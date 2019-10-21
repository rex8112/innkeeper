import discord
import logging
import random

from discord.ext import commands
import tools.database as db

logger = logging.getLogger('adventureController')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
handler2 = logging.FileHandler(filename='latest.log', encoding='utf-8', mode='a')
handler2.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
logger.addHandler(handler2)

db.initDB()


class PerLevel:
  unarmDamage = 3.5 #Flat increase
  invCap = 5 #Amount of strength to gain one inventory slot
  evasion = 0.004 #Evasion Chance
  softCapEvasion = 0.0023 #Evasion Chance after soft cap
  critChance = 0.0025
  softCapCritChance = 0.0016
  health = 10
  spellAmp = 0.01


class Player:
  def __init__(self, id):
    self.id = id

  def new(self, name, cls, race, rawAttributes):
    self.name = name
    self.cls = cls
    self.race = race
    self.level = 1
    self.xp = 0
    self.maxHealth = 100
    self.available = True
    #Attributes
    self.rawStrength = rawAttributes[0]
    self.rawDexterity = rawAttributes[1]
    self.rawConstitution = rawAttributes[2]
    self.rawIntelligence = rawAttributes[3]
    self.rawWisdom = rawAttributes[4]
    self.rawCharisma = rawAttributes[5]
    #Skills
    self.skills = []
    #Equipment
    self.mainhand = Equipment(1)
    self.offhand = Equipment(1)
    self.helmet = Equipment(1)
    self.armor = Equipment(1)
    self.gloves = Equipment(1)
    self.boots = Equipment(1)
    self.trinket = Equipment(1)

    self.inventory = []
    if db.addAdventurer(self.id, name, cls, race, ','.join(str(e) for e in rawAttributes)):
      self.rest()
      self.calculate()
      self.rest()
      self.save()
      logger.info('{}:{} Created Successfully'.format(self.id, self.name))
      return True
    else:
      return False

  def delete(self):
    db.deleteAdventurer(self.id)
    logger.warning('{}:{} Deleted'.format(self.id, self.name))

  def load(self):
    try:
      raw = db.getAdventurer(self.id)
      self.name = raw[2]
      self.cls = raw[3]
      self.level = raw[4]
      self.xp = raw[5]
      self.race = raw[6]

      rawAttributes = raw[7].split(',') #Get a list of the attributes
      self.rawStrength = int(rawAttributes[0])
      self.rawDexterity = int(rawAttributes[1])
      self.rawConstitution = int(rawAttributes[2])
      self.rawIntelligence = int(rawAttributes[3])
      self.rawWisdom = int(rawAttributes[4])
      self.rawCharisma = int(rawAttributes[5])

      try:
        self.skills = raw[8].split(',') #Get a list of skills
      except AttributeError:
        self.skills = []

      equipment = raw[9].split(',') #Get a list of equipped items
      self.mainhand = Equipment(equipment[0])
      self.offhand = Equipment(equipment[1])
      self.helmet = Equipment(equipment[2])
      self.armor = Equipment(equipment[3])
      self.gloves = Equipment(equipment[4])
      self.boots = Equipment(equipment[5])
      self.trinket = Equipment(equipment[6])

      self.inventory = raw[10].split(',')
      try:
        self.inventory.remove('')
      except:
        pass
      self.available = bool(raw[11])
      self.health = int(raw[12])

      self.calculate()
      logger.debug('{}:{} Loaded Successfully'.format(self.id, self.name))
      return True
    except Exception as e:
      exc = '{}: {}'.format(type(e).__name__, e)
      logger.error('{} Failed to Load\n{}:{}'.format(self.id, type(self).__name__, exc))
      return False

  def save(self):
    rawAttributes = [self.rawStrength, self.rawDexterity, self.rawConstitution, self.rawIntelligence, self.rawWisdom, self.rawCharisma] #Bundles Attributes into a string to be stored
    rawAttributes = ','.join(str(e) for e in rawAttributes)
    skills = ','.join(self.skills) #Does the same for skills, though skills aren't currently used
    equipment = ','.join(str(e) for e in [self.mainhand.id, self.offhand.id, self.helmet.id, self.armor.id, self.gloves.id, self.boots.id, self.trinket.id])
    inventory = ','.join(str(e) for e in self.inventory)

    save = [self.id, self.name, self.cls, self.level, self.xp, self.race, rawAttributes, skills, equipment, inventory, int(self.available), self.health]
    logger.debug('{}:{} Saved Successfully'.format(self.id, self.name))
    return db.saveAdventurer(save)

  def equip(self, e: int):
    eq = Equipment(e)
    if eq.slot == 'mainhand':
      uneq = self.mainhand
      self.mainhand = eq
    elif eq.slot == 'offhand':
      uneq = self.offhand
      self.offhand = eq
    elif eq.slot == 'helmet':
      uneq = self.helmet
      self.helmet = eq
    elif eq.slot == 'armor':
      uneq = self.armor
      self.armor = eq
    elif eq.slot == 'gloves':
      uneq = self.gloves
      self.gloves = eq
    elif eq.slot == 'boots':
      uneq = self.boots
      self.boots = eq
    elif eq.slot == 'trinket':
      uneq = self.trinket
      self.trinket = eq
    
    if not uneq.mods.get('empty', False):
      self.inventory.append(uneq.id)
    self.calculate()

  def unequip(self, slot: str):
    eq = Equipment(1)
    if slot == 'mainhand':
      uneq = self.mainhand
      self.mainhand = eq
    elif slot == 'offhand':
      uneq = self.offhand
      self.offhand = eq
    elif slot == 'helmet':
      uneq = self.helmet
      self.helmet = eq
    elif slot == 'armor':
      uneq = self.armor
      self.armor = eq
    elif slot == 'gloves':
      uneq = self.gloves
      self.gloves = eq
    elif slot == 'boots':
      uneq = self.boots
      self.boots = eq
    elif slot == 'trinket':
      uneq = self.trinket
      self.trinket = eq
    
    if not uneq.mods.get('empty', False):
      self.inventory.append(uneq.id)
    self.calculate()

  def calculate(self):
    #Checks Race/Class for attribute changes
    self.strength = self.rawStrength
    self.dexterity = self.rawDexterity
    self.constitution = self.rawConstitution
    self.intelligence = self.rawIntelligence
    self.wisdom = self.rawWisdom
    self.charisma = self.rawCharisma
    self.maxHealth = 0
    self.wc = 3
    self.ac = 4
    self.dmg = 0
    self.strdmg = 0
    self.dexdmg = 0
    self.attackSpeed = 2 #Turns per attack

    #TIME FOR EQUIPMENT CALCULATIONS
    for equip in [self.mainhand, self.offhand, self.helmet, self.armor, self.gloves, self.boots, self.trinket]:
      self.wc += int(equip.mods.get('wc', 0))
      self.ac += int(equip.mods.get('ac', 0))
      self.maxHealth += int(equip.mods.get('health', 0))

      self.strength += int(equip.mods.get('strength', 0))
      self.dexterity += int(equip.mods.get('dexterity', 0))
      self.constitution += int(equip.mods.get('constitution', 0))
      self.intelligence += int(equip.mods.get('intelligence', 0))
      self.wisdom += int(equip.mods.get('wisdom', 0))
      self.charisma += int(equip.mods.get('charisma', 0))

      self.dmg += int(equip.mods.get('dmg', 0))
      self.strdmg += int(equip.mods.get('strdmg', 0))
      self.dexdmg += int(equip.mods.get('dexdmg', 0))
      self.attackSpeed += int(equip.mods.get('as', 0))

    #Strength Related Stats First
    self.unarmDamage = float(self.strength) * PerLevel.unarmDamage
    logger.debug('{0.name} Unarmed Damage calculated to: {0.unarmDamage}'.format(self))

    self.inventoryCapacity = self.strength // PerLevel.invCap + (10 - (10 // PerLevel.invCap))
    logger.debug('{0.name} Inventory Capacity calculated to: {0.inventoryCapacity}'.format(self))

    #Dexterity related stats second
    if self.dexterity <= 40: #Dexterity below 40
      self.evasion = float(self.dexterity) * PerLevel.evasion
      self.critChance = float(self.dexterity) * PerLevel.evasion

    elif self.dexterity > 40 and self.dexterity <= 100: #Dexterity between 40 and 100
      self.evasion = PerLevel.softCapEvasion * (float(self.dexterity) - 40.0) + 40.0 * PerLevel.evasion
      self.critChance = PerLevel.softCapCritChance * (float(self.dexterity) - 40.0) + 40.0 * PerLevel.critChance

    else: #Dexterity above 100
      self.evasion = PerLevel.softCapEvasion * (100.0 - 40.0) + 40.0 * PerLevel.evasion
      self.critChance = PerLevel.softCapCritChance * (100.0 - 40.0) + 40.0 * PerLevel.critChance
      
    logger.debug('{0.name} Evasion calculated to: {0.evasion}'.format(self))
    logger.debug('{0.name} Crit Chance calculated to: {0.critChance}'.format(self))

    #Constitution related stats third
    self.maxHealth += PerLevel.health * self.constitution + 100
    logger.debug('{0.name} Max health calculated to: {0.maxHealth}'.format(self))

    #Intelligence related stats fourth
    self.spellAmp = PerLevel.spellAmp * float(self.intelligence)
    logger.debug('{0.name} Spell Amp calculated to: {0.spellAmp}'.format(self))

    #Wisdom related stats fifth
    self.secretChance = 0

    #Charisma related stats sixth
    self.discount = 0

    #Set values to their maximum
    self.attackCooldown = self.attackSpeed

    self.dmg += self.strdmg * self.strength + self.dexdmg * self.dexterity
    if self.dmg == 0:
      self.dmg = self.unarmDamage

    if self.maxHealth < self.health:
      self.health = self.maxHealth

    logger.debug('{0.name} Calculation complete'.format(self))
  
  def rest(self): #Reset anything that needs to on rest
    self.health = self.maxHealth


class Enemy:
  def __init__(self, id):
    self.id = id

  def new(self, name, cls, race, rawAttributes, skills, rng):
    self.name = name
    self.cls = cls
    self.race = race
    self.level = 1
    self.xp = 0
    #Attributes
    self.rawStrength = rawAttributes[0]
    self.rawDexterity = rawAttributes[1]
    self.rawConstitution = rawAttributes[2]
    self.rawIntelligence = rawAttributes[3]
    self.rawWisdom = rawAttributes[4]
    self.rawCharisma = rawAttributes[5]
    #Skills
    self.skills = skills
    #Equipment
    self.mainhand = Equipment(1)
    self.offhand = Equipment(1)
    self.helmet = Equipment(1)
    self.armor = Equipment(1)
    self.gloves = Equipment(1)
    self.boots = Equipment(1)
    self.trinket = Equipment(1)

    self.inventory = []
    self.id = db.addEnemy(name, cls, race, ','.join(str(e) for e in rawAttributes), ','.join(str(e) for e in skills), int(rng))
    logger.info('{}:{} Created Successfully'.format(self.id, self.name))

  def delete(self):
    db.deleteEnemy(self.id)
    logger.warning('{}:{} Deleted'.format(self.id, self.name))

  def load(self):
    try:
      raw = db.getEnemy(self.id)
      self.name = raw[1]
      self.cls = raw[2]
      self.level = raw[3]
      self.xp = raw[4]
      self.race = raw[5]

      rawAttributes = raw[6].split(',') #Get a list of the attributes
      self.rawStrength = int(rawAttributes[0])
      self.rawDexterity = int(rawAttributes[1])
      self.rawConstitution = int(rawAttributes[2])
      self.rawIntelligence = int(rawAttributes[3])
      self.rawWisdom = int(rawAttributes[4])
      self.rawCharisma = int(rawAttributes[5])

      self.skills = raw[7].split(',') #Get a list of skills

      equipment = raw[8].split(',') #Get a list of equipped items
      self.mainhand = Equipment(equipment[0])
      self.offhand = Equipment(equipment[1])
      self.helmet = Equipment(equipment[2])
      self.armor = Equipment(equipment[3])
      self.gloves = Equipment(equipment[4])
      self.boots = Equipment(equipment[5])
      self.trinket = Equipment(equipment[6])

      self.inventory = raw[9].split(',')
      self.calculate()
      logger.debug('{}:{} Loaded Successfully'.format(self.id, self.name))
      return True
    except Exception as e:
      exc = '{}: {}'.format(type(e).__name__, e)
      logger.error('{} Failed to Load\n{}:{}'.format(self.id, type(self).__name__, exc))
      return False

  def save(self):
    rawAttributes = [self.rawStrength, self.rawDexterity, self.rawConstitution, self.rawIntelligence, self.rawWisdom, self.rawCharisma]
    rawAttributes = ','.join(str(e) for e in rawAttributes)
    skills = ','.join(self.skills)
    equipment = ','.join(str(e) for e in [self.mainhand.id, self.offhand.id, self.helmet.id, self.armor.id, self.gloves.id, self.boots.id, self.trinket.id])
    inventory = ','.join(self.inventory)

    save = [self.id, self.name, self.cls, self.level, self.xp, self.race, rawAttributes, skills, equipment, inventory]
    logger.debug('{}:{} Saved Successfully'.format(self.id, self.name))
    return db.saveEnemy(save)

  def calculate(self):
    #Checks Race/Class for attribute changes
    self.strength = self.rawStrength
    self.dexterity = self.rawDexterity
    self.constitution = self.rawConstitution
    self.intelligence = self.rawIntelligence
    self.wisdom = self.rawWisdom
    self.charisma = self.rawCharisma
    self.maxHealth = 0
    self.wc = 3
    self.ac = 4
    self.dmg = 0
    self.strdmg = 0
    self.dexdmg = 0
    self.attackSpeed = 2 #Turns per attack

    #TIME FOR EQUIPMENT CALCULATIONS
    for equip in [self.mainhand, self.offhand, self.helmet, self.armor, self.gloves, self.boots, self.trinket]:
      self.wc += int(equip.mods.get('wc', 0))
      self.ac += int(equip.mods.get('ac', 0))
      self.maxHealth += int(equip.mods.get('health', 0))

      self.strength += int(equip.mods.get('strength', 0))
      self.dexterity += int(equip.mods.get('dexterity', 0))
      self.constitution += int(equip.mods.get('constitution', 0))
      self.intelligence += int(equip.mods.get('intelligence', 0))
      self.wisdom += int(equip.mods.get('wisdom', 0))
      self.charisma += int(equip.mods.get('charisma', 0))

      self.dmg += int(equip.mods.get('dmg', 0))
      self.strdmg += int(equip.mods.get('strdmg', 0))
      self.dexdmg += int(equip.mods.get('dexdmg', 0))
      self.attackSpeed += int(equip.mods.get('as', 0))

    #Strength Related Stats First
    self.unarmDamage = float(self.strength) * PerLevel.unarmDamage
    logger.debug('{0.name} Unarmed Damage calculated to: {0.unarmDamage}'.format(self))

    self.inventoryCapacity = self.strength // PerLevel.invCap + (10 - (10 // PerLevel.invCap))
    logger.debug('{0.name} Inventory Capacity calculated to: {0.inventoryCapacity}'.format(self))

    #Dexterity related stats second
    if self.dexterity <= 40: #Dexterity below 40
      self.evasion = float(self.dexterity) * PerLevel.evasion
      self.critChance = float(self.dexterity) * PerLevel.evasion

    elif self.dexterity > 40 and self.dexterity <= 100: #Dexterity between 40 and 100
      self.evasion = PerLevel.softCapEvasion * (float(self.dexterity) - 40.0) + 40.0 * PerLevel.evasion
      self.critChance = PerLevel.softCapCritChance * (float(self.dexterity) - 40.0) + 40.0 * PerLevel.critChance

    else: #Dexterity above 100
      self.evasion = PerLevel.softCapEvasion * (100.0 - 40.0) + 40.0 * PerLevel.evasion
      self.critChance = PerLevel.softCapCritChance * (100.0 - 40.0) + 40.0 * PerLevel.critChance
      
    logger.debug('{0.name} Evasion calculated to: {0.evasion}'.format(self))
    logger.debug('{0.name} Crit Chance calculated to: {0.critChance}'.format(self))

    #Constitution related stats third
    self.maxHealth += PerLevel.health * self.constitution + 100
    logger.debug('{0.name} Max health calculated to: {0.maxHealth}'.format(self))

    #Intelligence related stats fourth
    self.spellAmp = PerLevel.spellAmp * float(self.intelligence)
    logger.debug('{0.name} Spell Amp calculated to: {0.spellAmp}'.format(self))

    #Wisdom related stats fifth
    self.secretChance = 0

    #Charisma related stats sixth
    self.discount = 0

    #Set values to their maximum
    self.attackCooldown = self.attackSpeed
    self.health = self.maxHealth

    self.dmg += self.strdmg * self.strength + self.dexdmg * self.dexterity
    if self.dmg == 0:
      self.dmg = self.unarmDamage

    logger.debug('{0.name} Calculation complete'.format(self))


class Equipment:
  def __init__(self, id):
    self.id = id
    if id == 0:
      pass
    else: #Search for equipment in the database
      self.load()

  def load(self):
    try:
      raw = db.getEquipment(self.id)
      self.name = raw[1]
      self.level = raw[2]
      self.flavor = raw[3]
      self.rarity = raw[4]
      self.slot = raw[6]
      self.price = raw[7]
      rawMod = raw[5].split(',')
      mods = []
      for mod in rawMod:
        mods.append(tuple(mod.split(':')))
      self.mods = dict(mods)
      logger.debug('{}:{} Loaded Successfully'.format(self.id, self.name))
      return True
    except Exception as e:
      exc = '{}: {}'.format(type(e).__name__, e)
      logger.error('{} Failed to Load\n{}:{}'.format(self.id, type(self).__name__, exc))
      return False

  def save(self):
    rawMod = []
    for mod in self.mods:
      rawMod.append('{}:{}'.format(mod, self.mods[mod]))
    
    save = [self.id, self.name, self.flavor, self.rarity, ','.join(rawMod), self.slot, self.price]
    return db.saveEquipment(save)

  def new(self, name, flavor, rarity, mods, slot, price):
    self.name = name
    self.flavor = flavor
    self.rarity = rarity
    self.slot = slot
    self.price = price
    rawMod = []
    for mod in mods.split(','):
      rawMod.append(tuple(mod.split(':')))
    self.mods = dict(rawMod)
    self.id = self.save()
    logger.info('{}:{} Created Successfully'.format(self.id, self.name))

  def delete(self):
    db.deleteEquipment(self.id)
    logger.warning('{}:{} Deleted'.format(self.id, self.name))


class Encounter:
  def __init__(self, players: list, enemies: list, pve = True):
    self.players = players
    self.enemies = enemies
    self.deadPlayers = []
    self.deadEnemies = []

  def nextTurn(self):
    for player in self.players:
      if self.enemies[-1:]:
        logger.debug('Living Enemy detected')
        self.attack(player, self.enemies[-1])

        if self.enemies[-1].health <= 0: #If the enemy is dead, remove him from active enemies
          self.deadEnemies.append(self.enemies[-1])
          self.enemies.pop()

    for enemy in self.enemies:
      if self.players[-1:]:
        logger.debug('Living Player detected')
        self.attack(enemy, self.players[-1])

        if self.players[-1].health <= 0: #If the enemy is dead, remove him from active enemies
          self.deadPlayers.append(self.players[-1])
          self.players.pop()
        
    
  def attack(self, attacker, defender):
    if attacker.attackCooldown <= 0:
      dmg = attacker.dmg
      critChance = attacker.critChance
      chanceToHit = 1 + (attacker.wc - defender.ac) / ((attacker.wc + defender.ac) * 0.5)
      print (chanceToHit)

      if chanceToHit > 1: #If you have a chance to hit higher than 100% convert overflow into crit chance
        critChance += chanceToHit - 1.0
        logger.debug('Player Crit Chance set to: {}'.format(critChance))

      if random.uniform(0.0, 1.0) > attacker.evasion: #Evasion Check
        if random.uniform(0.0, 1.0) <= chanceToHit: #If random number is lower than the chance to hit, you hit
          if random.uniform(0.0, 1.0) <= critChance:
            dmg = dmg * 2
          defender.health -= dmg
          logger.debug('Character hit for {} DMG'.format(dmg))
          attacker.attackCooldown = attacker.attackSpeed
        else: #You miss
          logger.debug('Missed with chanceToHit: {:.1%}'.format(chanceToHit))
      else: #You evaded
        logger.debug('Player Evaded')

    else:
      attacker.attackCooldown -= 1

  def getLoot(self):
    rawLoot = []
    for enemy in self.deadEnemies:
      for loot in enemy.inventory:
        rawLoot.append(loot)
    return rawLoot

  def end(self):
    if self.players.count > 0:
      return True
    else:
      return False

class RNGDungeon:
  def __init__(self, dID = 0):
    self.id = dID

  def new(self, aID: int, level: int, difficulty: str):
    self.adv = Player(aID)

    if difficulty == 'easy':
      self.stages = 2
    elif difficulty == 'medium':
      self.stages = 5
    elif difficulty == 'hard':
      self.stages = 9
    else:
      self.stages = 1
    
    self.enemies = []
    for i in range(1, self.stages + 1):
      if i > 6:
        bossToAdd = random.choice(db.getEnemyRNG(level, 2, 0))[0]
      elif i > 2:
        bossToAdd = random.choice(db.getEnemyRNG(level, 1, 0))[0]
      else:
        bossToAdd = None

      if bossToAdd:
        stageEnemies = [bossToAdd]
      else:
        stageEnemies = []

      pool = db.getEnemyRNG(level)
      randMax = random.randint(1, 3)
      for _ in range(1, randMax + 1):
        stageEnemies.append(random.choice(pool)[0])
      
      self.enemies.append(stageEnemies)

    self.loot = []
    if difficulty == 'easy':
      self.lootInt = 2
    elif difficulty == 'medium':
      self.lootInt = 3
    elif difficulty == 'hard':
      self.lootInt = 4
    else:
      self.lootInt = 1

    lPool = db.getEquipmentRNG(level)
    for _ in range(1, self.lootInt + 1):
      self.loot.append(random.choice(lPool)[0])
      
    print(self.enemies)
    print(self.loot)

  def save(self):
    pass

  def load(self):
    pass

  def nextStage(self):
    pass
