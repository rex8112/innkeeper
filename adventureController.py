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

    skills = raw[8].split(',') #Get a list of skills

    equipment = raw[9].split(',') #Get a list of equipped items
    self.mainhand = equipment[0]
    self.offhand = equipment[1]
    self.helmet = equipment[2]
    self.armor = equipment[3]
    self.gloves = equipment[4]
    self.boots = equipment[5]

    self.inventory = raw[10].split(',')

class Attribute:
  def __init__(self, name, value):
    self.name = name
    self.set(value)

  def set(self, value):
    self.value = value
    self.mod = value // 2 - 5

class Equipment:
  def __init__(self, name):
    self.name = name

x = Character(8112)
x.load()

print ("{} is {} with {}STR {}DEX {}CON {}INT {}WIS {}CHA\n\
  Wearing: {}-MH {}-OH {}-HELM {}-ARM {}-GLV {}-BTS\n\
    Has: {}".format(x.name, x.level, x.rawStrength, x.rawDexterity, x.rawConstitution, x.rawIntelligence, x.rawWisdom, x.rawCharisma, x.mainhand,\
      x.offhand, x.helmet, x.armor, x.gloves, x.boots, x.inventory))
