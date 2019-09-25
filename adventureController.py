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
    self.available = True
    self.dead = False
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
      self.save()
      logger.info('{}:{} Created Successfully'.format(self.id, self.name))
      return True

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

      self.skills = raw[8].split(',') #Get a list of skills

      equipment = raw[9].split(',') #Get a list of equipped items
      self.mainhand = Equipment(equipment[0])
      self.offhand = Equipment(equipment[1])
      self.helmet = Equipment(equipment[2])
      self.armor = Equipment(equipment[3])
      self.gloves = Equipment(equipment[4])
      self.boots = Equipment(equipment[5])
      self.trinket = Equipment(equipment[6])

      self.inventory = raw[10].split(',')
      self.available = bool(raw[11])
      self.dead = bool(raw[12])

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
    inventory = ','.join(self.inventory)

    save = [self.id, self.name, self.cls, self.level, self.xp, self.race, rawAttributes, skills, equipment, inventory, int(self.available), int(self.dead)]
    logger.debug('{}:{} Saved Successfully'.format(self.id, self.name))
    return db.saveAdventurer(save)

  def calculate(self):
    #Checks Race/Class for attribute changes
    self.strength = self.rawStrength
    self.dexterity = self.rawDexterity
    self.constitution = self.rawConstitution
    self.intelligence = self.rawIntelligence
    self.wisdom = self.rawWisdom
    self.charisma = self.rawCharisma
    self.maxHealth = 0
    self.wc = 0
    self.ac = 0
    self.dmg = 0
    self.strdmg = 0
    self.dexdmg = 0
    self.attackSpeed = 2 #Turns per attack

    #TIME FOR EQUIPMENT CALCULATIONS
    for equip in [self.mainhand, self.offhand, self.helmet, self.armor, self.gloves, self.boots, self.trinket]:
      self.wc += equip.mods.get('wc', 0)
      self.ac += equip.mods.get('ac', 0)
      self.maxHealth += equip.mods.get('health', 0)

      self.strength += equip.mods.get('strength', 0)
      self.dexterity += equip.mods.get('dexterity', 0)
      self.constitution += equip.mods.get('constitution', 0)
      self.intelligence += equip.mods.get('intelligence', 0)
      self.wisdom += equip.mods.get('wisdom', 0)
      self.charisma += equip.mods.get('charisma', 0)

      self.dmg += equip.mods.get('dmg', 0)
      self.strdmg += equip.mods.get('strdmg', 0)
      self.dexdmg += equip.mods.get('dexdmg', 0)
      self.attackSpeed += equip.mods.get('as', 0)

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
    if not self.dead:
      self.health = self.maxHealth
    else:
      self.health = 0

    self.dmg += self.strdmg * self.strength + self.dexdmg * self.dexterity
    if self.dmg == 0:
      self.dmg = self.unarmDamage

    logger.debug('{0.name} Calculation complete'.format(self))


class Enemy:
  def __init__(self, id):
    self.id = id

  def new(self, name, cls, race, rawAttributes, skills):
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

    self.inventory = []
    self.id = db.addEnemy(name, cls, race, ','.join(str(e) for e in rawAttributes), ','.join(str(e) for e in skills))
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
      self.rawStrength = rawAttributes[0]
      self.rawDexterity = rawAttributes[1]
      self.rawConstitution = rawAttributes[2]
      self.rawIntelligence = rawAttributes[3]
      self.rawWisdom = rawAttributes[4]
      self.rawCharisma = rawAttributes[5]

      self.skills = raw[7].split(',') #Get a list of skills

      equipment = raw[8].split(',') #Get a list of equipped items
      self.mainhand = Equipment(equipment[0])
      self.offhand = Equipment(equipment[1])
      self.helmet = Equipment(equipment[2])
      self.armor = Equipment(equipment[3])
      self.gloves = Equipment(equipment[4])
      self.boots = Equipment(equipment[5])

      self.inventory = raw[9].split(',')
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
    equipment = ','.join(str(e) for e in [self.mainhand.id, self.offhand.id, self.helmet.id, self.armor.id, self.gloves.id, self.boots.id])
    inventory = ','.join(self.inventory)

    save = [self.id, self.name, self.cls, self.level, self.xp, self.race, rawAttributes, skills, equipment, inventory]
    logger.debug('{}:{} Saved Successfully'.format(self.id, self.name))
    return db.saveEnemy(save)


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
      self.flavor = raw[2]
      self.rarity = raw[3]
      self.slot = raw[5]
      self.price = raw[6]
      rawMod = raw[4].split(',')
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

    self.rawLoot = []
    for enemy in self.enemies:
      self.rawLoot += enemy.inventory

  def nextTurn(self):
    for player in self.players:
      if self.enemies[-1:]:
        if player.attackCooldown <= 0:
          dmg = player.dmg
          critChance = player.critChance
          chanceToHit = 1 + (player.wc - self.enemies[-1].ac) / ((player.wc + self.enemies[-1].ac) * 0.5)

          if chanceToHit <= 1: #If you have a chance to hit higher than 100% convert overflow into crit chance
            critChance += chanceToHit - 1.0

          if random.random(0.0, 1.0) <= chanceToHit: #If random number is lower than the chance to hit, you hit
            if random.random(0.0, 1.0) <= critChance:
              dmg = dmg * 2
            self.enemies[-1].health -= dmg
            player.attackCooldown = player.attackSpeed
          else: #You miss
            pass

          if self.enemies[-1].health <= 0: #If the enemy is dead, remove him from active enemies
            self.deadEnemies.append(self.enemies[-1])
            self.enemies.pop()
        else:
          player.attackCooldown -= 1

    for enemy in self.enemies:
      if self.players[-1:]:
        if enemy.attackCooldown <= 0:
          dmg = enemy.dmg
          critChance = enemy.critChance
          chanceToHit = 1 + (enemy.wc - self.players[-1].ac) / ((enemy.wc + self.players[-1].ac) * 0.5)

          if chanceToHit <= 1: #If you have a chance to hit higher than 100% convert overflow into crit chance
            critChance += chanceToHit - 1.0

          if random.random(0.0, 1.0) <= chanceToHit: #If random number is lower than the chance to hit, you hit
            if random.random(0.0, 1.0) <= critChance:
              dmg = dmg * 2
            self.players[-1].health -= dmg
            enemy.attackCooldown = enemy.attackSpeed
          else: #You miss
            pass

          if self.players[-1].health <= 0: #If the enemy is dead, remove him from active enemies
            self.deadPlayers.append(self.players[-1])
            self.players.pop()
        else:
          enemy.attackCooldown -= 1