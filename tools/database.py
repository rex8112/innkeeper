import datetime
import sqlite3
import discord
import logging
import numpy as np


db = sqlite3.connect('ethiaData.db')
db2 = sqlite3.connect('persistentData.db')
cursor = db.cursor()
cursor2 = db2.cursor()
logger = logging.getLogger('database')


def initDB():  # initialize the database
    cursor.execute("""CREATE TABLE IF NOT EXISTS adventurers( indx INTEGER PRIMARY KEY, id INTEGER UNIQUE, name TEXT, class TEXT, level INTEGER, xp INTEGER DEFAULT 0, race TEXT, attributes TEXT, skills TEXT, equipment TEXT, inventory TEXT, available INTEGER DEFAULT 1, health INTEGER)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS rngdungeons( indx INTEGER PRIMARY KEY, adv INTEGER, active INTEGER, stage INTEGER, stages INTEGER, enemies TEXT, loot TEXT, time TEXT, xp INTEGER DEFAULT 0)""")
    cursor2.execute("""CREATE TABLE IF NOT EXISTS enemies( indx INTEGER PRIMARY KEY, name TEXT, class TEXT, level INTEGER, xp INTEGER DEFAULT 0, race TEXT, attributes TEXT, skills TEXT, equipment TEXT, inventory TEXT, rng INTEGER)""")
    cursor2.execute("""CREATE TABLE IF NOT EXISTS equipment(indx INTEGER PRIMARY KEY, name TEXT, level INTEGER, flavor TEXT, rarity INTEGER, modifier TEXT, slot TEXT, price INTEGER, rng INTEGER)""")

    cursor2.execute("""SELECT * FROM equipment WHERE indx = 1""")
    if not cursor2.fetchone():
        cursor2.execute("""INSERT INTO equipment(name, level, flavor, rarity, modifier, slot, price, rng) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                        ('Empty', 0, 'Nothing is equipped', 0, 'unsellable:1,empty:1', 'all', 0, 0))

    cursor.execute("""DELETE FROM rngdungeons WHERE adv IS NULL""")
    db.commit()
    db2.commit()


def addAdventurer(id, name, cls, race, attributes):
    try:
        cursor.execute("""INSERT INTO adventurers(id, name, class, level, xp, race, attributes) VALUES(?, ?, ?, ?, ?, ?, ?)""",
                       (id, name, cls, 1, 0, race, attributes))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def deleteAdventurer(id):
    cursor.execute("""DELETE FROM adventurers WHERE id = ?""", (id,))
    db.commit()


def getAdventurer(id):
    cursor.execute("""SELECT * FROM adventurers WHERE id = ?""", (id,))
    return cursor.fetchone()


def saveAdventurer(save):
    cursor.execute("""UPDATE adventurers SET name = ?, class = ?, level = ?, xp = ?, race = ?, attributes = ?, skills = ?, equipment = ?, inventory = ?, available = ?, health = ? WHERE id = ?""",
                   (save[1], save[2], save[3], save[4], save[5], save[6], save[7], save[8], save[9], save[10], save[11], save[0]))
    db.commit()
    return save[0]


def statusAdventurer(id, available: bool):
    cursor.execute(
        """UPDATE adventurers SET available = ? WHERE id = ?""", (int(available), id))
    db.commit()


def getEquipment(id):
    cursor2.execute("""SELECT * FROM equipment WHERE indx = ?""", (id,))
    return cursor2.fetchone()


def getEquipmentRNG(lvl: int, offset=1, rnge=1):
    maximum = lvl + offset
    minimum = maximum - rnge
    cursor2.execute(
        """SELECT * FROM equipment WHERE rng = 1 AND level BETWEEN ? AND ?""", (minimum, maximum))
    equipment = cursor2.fetchall()
    tmp = []
    for e in equipment:
        tmp.append(e[0])
    return tmp


def saveEquipment(save):
    if save[0] > 0:
        cursor2.execute("""UPDATE equipment SET name = ?, flavor = ?, rarity = ?, modifier = ?, slot = ?, price = ? WHERE indx = ?""",
                        (save[1], save[2], save[3], save[4], save[5], save[6], save[0]))
        id = save[0]
    else:
        cursor2.execute("""INSERT INTO equipment(name, flavor, rarity, modifier, slot, price) VALUES(?, ?, ?, ?, ?, ?)""",
                        (save[1], save[2], save[3], save[4], save[5], save[6]))
        id = cursor2.lastrowid
    db2.commit()
    return id


def deleteEquipment(id):
    cursor2.execute("""DELETE FROM equipment WHERE indx = ?""", (id,))
    db2.commit()


def addEnemy(name, cls, race, attributes, skills, rng):
    cursor2.execute("""INSERT INTO enemies(name, class, level, xp, race, attributes, skills, rng) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                    (name, cls, 1, 0, race, attributes, skills, rng))
    db2.commit()
    idToSend = cursor2.lastrowid
    return idToSend


def deleteEnemy(id):
    cursor2.execute("""DELETE FROM enemies WHERE indx = ?""", (id,))
    db2.commit()


def getEnemy(id):
    cursor2.execute("""SELECT * FROM enemies WHERE indx = ?""", (id,))
    return cursor2.fetchone()


def getEnemyRNG(lvl: int, offset=0, rnge=3):
    maximum = lvl + offset
    minimum = maximum - rnge
    cursor2.execute(
        """SELECT * FROM enemies WHERE rng = 1 AND level BETWEEN ? AND ?""", (minimum, maximum))
    return cursor2.fetchall()


def saveEnemy(save):
    cursor2.execute("""UPDATE enemies SET name = ?, class = ?, level = ?, xp = ?, race = ?, attributes = ?, skills = ?, equipment = ?, inventory = ? WHERE indx = ?""",
                    (save[1], save[2], save[3], save[4], save[5], save[6], save[7], save[8], save[9], save[0]))
    db2.commit()
    return save[0]


def addRNG():
    cursor.execute("""INSERT INTO rngdungeons DEFAULT VALUES""")
    db.commit()
    return cursor.lastrowid


def saveRNG(save):
    if save[0] == 0:
        save[0] = addRNG()
    cursor.execute("""UPDATE rngdungeons SET adv = ?, active = ?, stage = ?, stages = ?, enemies = ?, loot = ?, time = ?, xp = ? WHERE indx = ?""",
                   (save[1], save[2], save[3], save[4], save[5], save[6], save[7], save[8], save[0]))
    db.commit()
    return save[0]


def getRNG(id):
    cursor.execute("""SELECT * FROM rngdungeons WHERE indx = ?""", (id,))
    return cursor.fetchone()


def getActiveRNG(aID):
    cursor.execute(
        """SELECT * FROM rngdungeons WHERE active = 1 AND adv = ?""", (aID,))
    return cursor.fetchone()


def getTimeRNG():
    cursor.execute(
        """SELECT * FROM rngdungeons WHERE active = 1 AND time <= datetime('now', 'localtime')""")
    return cursor.fetchall()
