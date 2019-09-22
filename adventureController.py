import discord
import logging

from discord.ext import commands
import tools.database as db

logger = logging.getLogger('adventureController')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
handler2 = logging.FileHandler(filename='latest.log', encoding='utf-8', mode='w')
handler2.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
logger.addHandler(handler2)

db.initDB()

class Player:
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
    db.addAdventurer(self.id, name, cls, race, ','.join(str(e) for e in rawAttributes), ','.join(str(e) for e in skills))
    logger.info('{}:{} Created Successfully'.format(self.id, self.name))

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
      self.rawStrength = rawAttributes[0]
      self.rawDexterity = rawAttributes[1]
      self.rawConstitution = rawAttributes[2]
      self.rawIntelligence = rawAttributes[3]
      self.rawWisdom = rawAttributes[4]
      self.rawCharisma = rawAttributes[5]

      self.skills = raw[8].split(',') #Get a list of skills

      equipment = raw[9].split(',') #Get a list of equipped items
      self.mainhand = Equipment(equipment[0])
      self.offhand = Equipment(equipment[1])
      self.helmet = Equipment(equipment[2])
      self.armor = Equipment(equipment[3])
      self.gloves = Equipment(equipment[4])
      self.boots = Equipment(equipment[5])

      self.inventory = raw[10].split(',')
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
    return db.saveAdventurer(save)

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