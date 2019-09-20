import discord
import logging

from discord.ext import commands
import tools.database as db

logger = logging.getLogger('adventureController')

db.initDB()

class Character:
  def __init__(self, id):
    self.id = id

  def new(self, strength, dexterity, constitution, intelligence, wisdom, charisma):
    pass

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
    self.mainhand = equipment[0]
    self.offhand = equipment[1]
    self.helmet = equipment[2]
    self.armor = equipment[3]
    self.gloves = equipment[4]
    self.boots = equipment[5]

    self.inventory = raw[10].split(',')

  def save(self):
    rawAttributes = [self.rawStrength, self.rawDexterity, self.rawConstitution, self.rawIntelligence, self.rawWisdom, self.rawCharisma]
    rawAttributes = ','.join(str(e) for e in rawAttributes)
    skills = ','.join(self.skills)
    equipment = ','.join([self.mainhand, self.offhand, self.helmet, self.armor, self.gloves, self.boots])
    inventory = ','.join(self.inventory)

    save = [self.id, self.name, self.cls, self.level, self.xp, self.race, rawAttributes, skills, equipment, inventory]
    db.saveAdventurer(save)

class Equipment:
  def __init__(self, name):
    self.name = name

x = Character(8112)
x.load()
x.save()
x.load()

print ("{} is a level {} {} {} with {}STR {}DEX {}CON {}INT {}WIS {}CHA\n\
  Wearing: {}-MH {}-OH {}-HELM {}-ARM {}-GLV {}-BTS\n\
    Has: {}".format(x.name, x.level, x.race, x.cls, x.rawStrength, x.rawDexterity, x.rawConstitution, x.rawIntelligence, x.rawWisdom, x.rawCharisma, x.mainhand,\
      x.offhand, x.helmet, x.armor, x.gloves, x.boots, x.inventory))
