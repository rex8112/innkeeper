import datetime
import sqlite3
import discord
import logging


db = sqlite3.connect('ethiaData.db')
cursor = db.cursor()
logger = logging.getLogger('database')


def initDB():   #initialize the database
  cursor.execute( """CREATE TABLE IF NOT EXISTS adventurers( indx INTEGER PRIMARY KEY, id INTEGER UNIQUE, name TEXT, class TEXT, level INTEGER, xp INTEGER, race TEXT, attributes TEXT, skills TEXT, equipment TEXT, inventory TEXT)""" )
  db.commit()
  
def addAdventurer(id, att):
  pass

def getAdventurer(id):
  cursor.execute( """SELECT * FROM adventurers WHERE id = ?""", (id,) )
  return cursor.fetchone()