import datetime
import sqlite3
import discord
import logging


db = sqlite3.connect('ethiaData.db')
cursor = db.cursor()
logger = logging.getLogger('database')


def initDB():   #initialize the database
  cursor.execute( """CREATE TABLE IF NOT EXISTS adventurers( indx INTEGER PRIMARY KEY, id INTEGER UNIQUE, name TEXT, class TEXT, level INTEGER, xp INTEGER DEFAULT 0, race TEXT, attributes TEXT, skills TEXT, equipment TEXT, inventory TEXT)""" )
  cursor.execute( """CREATE TABLE IF NOT EXISTS enemies( indx INTEGER PRIMARY KEY, name TEXT, class TEXT, level INTEGER, xp INTEGER DEFAULT 0, race TEXT, attributes TEXT, skills TEXT, equipment TEXT, inventory TEXT)""" )
  cursor.execute( """CREATE TABLE IF NOT EXISTS equipment(indx INTEGER PRIMARY KEY, name TEXT, flavor TEXT, rarity TEXT, modifier TEXT, slot TEXT, price INTEGER)""" )

  cursor.execute( """SELECT * FROM equipment WHERE indx = 1""" )
  if not cursor.fetchone():
    cursor.execute( """INSERT INTO equipment(name, flavor, rarity, modifier, slot, price) VALUES(?, ?, ?, ?, ?, ?)""", ('Empty', 'Nothing is equipped', 'Common', 'unsellable:1,empty:1', 'all', 0))
  db.commit()
  
def addAdventurer(id, name, cls, race, attributes, skills):
  cursor.execute( """INSERT INTO adventurers(id, name, class, level, xp, race, attributes, skills) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""", (id, name, cls, 1, 0, race, attributes, skills))
  db.commit()

def deleteAdventurer(id):
  cursor.execute( """DELETE FROM adventurers WHERE id = ?""", (id,))
  db.commit()

def getAdventurer(id):
  cursor.execute( """SELECT * FROM adventurers WHERE id = ?""", (id,) )
  return cursor.fetchone()

def saveAdventurer(save):
  cursor.execute( """UPDATE adventurers SET name = ?, class = ?, level = ?, xp = ?, race = ?, attributes = ?, skills = ?, equipment = ?, inventory = ? WHERE id = ?""", (save[1], save[2], save[3], save[4], save[5], save[6], save[7], save[8], save[9], save[0]))
  db.commit()
  return save[0]

def getEquipment(id):
  cursor.execute( """SELECT * FROM equipment WHERE indx = ?""", (id,) )
  return cursor.fetchone()

def saveEquipment(save):
  if save[0] > 0:
    cursor.execute( """UPDATE equipment SET name = ?, flavor = ?, rarity = ?, modifier = ?, slot = ?, price = ? WHERE indx = ?""", (save[1],save[2],save[3],save[4],save[5],save[6], save[0]))
    id = save[0]
  else:
    cursor.execute( """INSERT INTO equipment(name, flavor, rarity, modifier, slot, price) VALUES(?, ?, ?, ?, ?, ?)""", (save[1],save[2],save[3],save[4],save[5],save[6]))
    id = cursor.lastrowid
  db.commit()
  return id

def deleteEquipment(id):
  cursor.execute( """DELETE FROM equipment WHERE indx = ?""", (id,))
  db.commit()

def addEnemy(name, cls, race, attributes, skills):
  cursor.execute( """INSERT INTO enemies(name, class, level, xp, race, attributes, skills) VALUES(?, ?, ?, ?, ?, ?, ?)""", (name, cls, 1, 0, race, attributes, skills))
  db.commit()
  idToSend = cursor.lastrowid
  return idToSend

def deleteEnemy(id):
  cursor.execute( """DELETE FROM enemies WHERE indx = ?""", (id,))
  db.commit()

def getEnemy(id):
  cursor.execute( """SELECT * FROM enemies WHERE indx = ?""", (id,) )
  return cursor.fetchone()

def saveEnemy(save):
  cursor.execute( """UPDATE enemies SET name = ?, class = ?, level = ?, xp = ?, race = ?, attributes = ?, skills = ?, equipment = ?, inventory = ? WHERE indx = ?""", (save[1], save[2], save[3], save[4], save[5], save[6], save[7], save[8], save[9], save[0]))
  db.commit()
  return save[0]