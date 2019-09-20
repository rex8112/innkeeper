import discord
import logging

from discord.ext import commands
import tools.database as db

logger = logging.getLogger('adventureController')

db.initDB()

class Character:
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
    self.mainhand = Equipment('empty')
    self.offhand = Equipment('empty')
    self.helmet = Equipment('empty')
    self.armor = Equipment('empty')
    self.gloves = Equipment('empty')
    self.boots = Equipment('empty')

    self.inventory = []
    db.addAdventurer(self.id, name, cls, race, ','.join(str(e) for e in rawAttributes), ','.join(skills))

  def delete(self):
    db.removeAdventurer(self.id)

  def load(self):
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
    logger.info('{} Loaded Successfully'.format(self.name))

  def save(self):
    rawAttributes = [self.rawStrength, self.rawDexterity, self.rawConstitution, self.rawIntelligence, self.rawWisdom, self.rawCharisma]
    rawAttributes = ','.join(str(e) for e in rawAttributes)
    skills = ','.join(self.skills)
    equipment = ','.join([self.mainhand.name, self.offhand.name, self.helmet.name, self.armor.name, self.gloves.name, self.boots.name])
    inventory = ','.join(self.inventory)

    save = [self.id, self.name, self.cls, self.level, self.xp, self.race, rawAttributes, skills, equipment, inventory]
    db.saveAdventurer(save)

class Equipment:
  def __init__(self, name):
    self.name = name
    if name == 'new':
      pass
    elif name != 'empty': #Search for equipment in the database
      pass
    else:
      self.name = 'Empty'
