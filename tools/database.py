import datetime
import sqlite3
import discord
import logging


db = sqlite3.connect('ethiaData.db')
cursor = db.cursor()
logger = logging.getLogger('database')


def initDB():   #initialize the database
  cursor.execute( """CREATE TABLE IF NOT EXISTS adventurers( indx INTEGER PRIMARY KEY, id INTEGER UNIQUE, name TEXT, class TEXT, level INTEGER, xp INTEGER DEFAULT 0, race TEXT, attributes TEXT, skills TEXT, equipment TEXT, inventory TEXT)""" )
  db.commit()
  
def addAdventurer(id, name, cls, race, attributes, skills):
  cursor.execute( """INSERT INTO adventurers(id, name, class, level, xp, race, attributes, skills) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""", (id, name, cls, 1, 0, race, attributes, skills))
  db.commit()

def removeAdventurer(id):
  cursor.execute( """DELETE FROM adventurers WHERE id = ?""", (id,))
  db.commit()

def getAdventurer(id):
  cursor.execute( """SELECT * FROM adventurers WHERE id = ?""", (id,) )
  return cursor.fetchone()

def saveAdventurer(save):
  cursor.execute( """UPDATE adventurers SET name = ?, class = ?, level = ?, xp = ?, race = ?, attributes = ?, skills = ?, equipment = ?, inventory = ? WHERE id = ?""", (save[1], save[2], save[3], save[4], save[5], save[6], save[7], save[8], save[9], save[0]))
  db.commit()