import datetime
import sqlite3
import mariadb
import sys
import discord
import logging
import semantic_version
import numpy as np
import shutil

logger = logging.getLogger('database')

class Database:
    def __init__(self):
        self.db = sqlite3.connect('innkeeperData.db')
        self.db2 = sqlite3.connect('staticData.db')
        self.db.row_factory = sqlite3.Row
        self.db2.row_factory = sqlite3.Row
        self.initDB()

    def initDB(self):  # initialize the database
        logger.info('Initializing Database')
        cursor = self.db.cursor()
        cursor2 = self.db2.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS adventurers( indx INTEGER PRIMARY KEY, id INTEGER UNIQUE, name TEXT, class TEXT, level INTEGER, xp INTEGER DEFAULT 0, race TEXT, attributes TEXT, skills TEXT, equipment TEXT, inventory TEXT, available INTEGER DEFAULT 1, health INTEGER, home INTEGER)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS rngdungeons( indx INTEGER PRIMARY KEY, adv INTEGER, active INTEGER, stage INTEGER, stages INTEGER, enemies TEXT, loot TEXT, time TEXT, xp INTEGER DEFAULT 0, combatInfo TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS shop( indx INTEGER PRIMARY KEY, adv INTEGER, inventory TEXT, buyback TEXT, refresh TEXT )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS raid( indx INTEGER PRIMARY KEY, adventurers TEXT, boss INTEGER, loot TEXT, completed INTEGER)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS servers( indx INTEGER PRIMARY KEY, name TEXT, id INTEGER NOT NULL UNIQUE, ownerID INTEGER NOT NULL, type TEXT NOT NULL, category INTEGER, announcement INTEGER, general INTEGER, command TEXT, adventureRole INTEGER, travelRole INTEGER, onjoin INTEGER DEFAULT 0)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS equipment( indx INTEGER PRIMARY KEY, baseID INTEGER NOT NULL, level INTEGER NOT NULL, rarity INTEGER NOT NULL, startingMods TEXT NOT NULL, randomMods TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS raidChannels(indx INTEGER PRIMARY KEY, channelID INTEGER NOT NULL, guildID INTEGER NOT NULL, advIDs TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS storage(indx INTEGER PRIMARY KEY UNIQUE, adv INTEGER NOT NULL UNIQUE, slots INTEGER DEFAULT 20, inventory TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS trade(indx INTEGER PRIMARY KEY UNIQUE, adv1 INTEGER NOT NULL, adv2 INTEGER NOT NULL, money1 INTEGER, money2 INTEGER, inventory1 TEXT, inventory2 TEXT, confirm1 INTEGER NOT NULL DEFAULT 0, confirm2 INTEGER NOT NULL DEFAULT 0, waitingOn INTEGER NOT NULL DEFAULT 1, active INTEGER NOT NULL DEFAULT 1)""")

        cursor2.execute("""CREATE TABLE IF NOT EXISTS baseEnemies( indx INTEGER PRIMARY KEY, name TEXT NOT NULL, minLevel INTEGER NOT NULL DEFAULT 1, maxLevel INTEGER NOT NULL DEFAULT 1000, elite TEXT, attributes TEXT NOT NULL, modifiers TEXT NOT NULL, skills TEXT NOT NULL DEFAULT attack, rng INTEGER NOT NULL DEFAULT 1)""")
        cursor2.execute("""CREATE TABLE IF NOT EXISTS baseEquipment(indx INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL, flavor TEXT NOT NULL, slot TEXT NOT NULL, minLevel INTEGER NOT NULL DEFAULT 1, maxLevel INTEGER NOT NULL DEFAULT 1000, startingRarity INTEGER NOT NULL DEFAULT 0, maxRarity INTEGER NOT NULL DEFAULT 4, damageString TEXT, startingModString TEXT NOT NULL, randomModString TEXT NOT NULL, requirementString TEXT, skills TEXT, flags TEXT, rng INTEGER NOT NULL)""")
        cursor2.execute("""CREATE TABLE IF NOT EXISTS raid(indx INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL, level INTEGER NOT NULL, flavor TEXT NOT NULL, attributes TEXT NOT NULL, skills TEXT NOT NULL, health INTEGER NOT NULL, loot TEXT NOT NULL, modifiers TEXT NOT NULL, available INTEGER NOT NULL DEFAULT 0)""")
        cursor2.execute("""CREATE TABLE IF NOT EXISTS modifiers(indx INTEGER PRIMARY KEY NOT NULL, id TEXT UNIQUE NOT NULL, displayName TEXT, titleName TEXT, description TEXT, defaultValue INTEGER NOT NULL DEFAULT 0)""")
        cursor2.execute("""CREATE TABLE IF NOT EXISTS eliteModifiers(indx INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, title TEXT, attributes TEXT, modifiers TEXT, skills TEXT)""")

        cursor.execute("""DELETE FROM rngdungeons WHERE adv IS NULL""")
        cursor.close()
        cursor2.close()
        self.db.commit()
        self.db2.commit()

    def addAdventurer(self, id, name, cls, race, attributes, home):
        cursor = self.db.cursor()
        try:
            cursor.execute("""INSERT INTO adventurers(id, name, class, level, xp, race, attributes, home) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                        (id, name, cls, 1, 0, race, attributes, home))
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            cursor.close()
            self.db.commit()

    def deleteAdventurer(self, id):
        cursor = self.db.cursor()
        cursor.execute("""DELETE FROM adventurers WHERE id = ?""", (id,))
        cursor.close()
        self.db.commit()


    def getAdventurer(self, id):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * FROM adventurers WHERE id = ?""", (id,))
        fetch = cursor.fetchone()
        cursor.close()
        return fetch

    def get_all_adventurers(self):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * FROM adventurers""")
        fetch = cursor.fetchall()
        cursor.close()
        return fetch

    def saveAdventurer(self, save):
        cursor = self.db.cursor()
        cursor.execute("""UPDATE adventurers SET name = ?, class = ?, level = ?, xp = ?, race = ?, attributes = ?, skills = ?, equipment = ?, inventory = ?, available = ?, health = ? WHERE id = ?""",
                    (save[1], save[2], save[3], save[4], save[5], save[6], save[7], save[8], save[9], save[10], save[11], save[0]))
        cursor.close()
        self.db.commit()
        return save[0]

    def statusAdventurer(self, id, available: bool):
        cursor = self.db.cursor()
        cursor.execute(
            """UPDATE adventurers SET available = ? WHERE id = ?""", (int(available), id))
        cursor.close()
        self.db.commit()

    def get_base_equipment(self, ID = None, lvl = None, rarity = None, rng = True):
        cursor = self.db2.cursor()
        if ID:
            cursor.execute(
                """SELECT * FROM baseEquipment WHERE indx = ?""",
                (ID,)
            )
            fetch = cursor.fetchone()
        elif rng and lvl and rarity is not None:
            cursor.execute(
                """SELECT * FROM baseEquipment WHERE rng = 1 AND minLevel <= ? AND maxLevel >= ? AND startingRarity <= ? AND maxRarity >= ?""",
                (lvl, lvl, rarity, rarity)
            )
            fetch = cursor.fetchall()
        elif lvl and rarity is not None:
            cursor.execute(
                """SELECT * FROM baseEquipment WHERE minLevel <= ? AND maxLevel >= ? AND startingRarity <= ? AND maxRarity >= ?""",
                (lvl, lvl, rarity, rarity)
            )
            fetch = cursor.fetchall()
        elif lvl:
            cursor.execute(
                """SELECT * FROM baseEquipment WHERE minLevel <= ? AND maxLevel >= ?""",
                (lvl, lvl)
            )
            fetch = cursor.fetchall()
        elif rarity is not None:
            cursor.execute(
                """SELECT * FROM baseEquipment WHERE startingRarity <= ? AND maxRarity >= ?""",
                (rarity, rarity)
            )
            fetch = cursor.fetchall()
        else:
            cursor.close()
            return None

        cursor.close()
        return fetch

    def get_all_base_equipment(self):
        cursor = self.db2.cursor()
        cursor.execute(
            """SELECT * FROM baseEquipment"""
        )
        fetch = cursor.fetchall()
        cursor.close()
        return fetch

    def get_base_equipment_lvl(self, lvl: int):
        cursor = self.db2.cursor()
        cursor.execute(
            """SELECT * FROM baseEquipment WHERE minLevel <= ? AND maxLevel >= ?""", (lvl, lvl)
        )
        fetch = cursor.fetchall()
        cursor.close()
        return fetch


    def get_base_equipment_lvl_rng(self, lvl: int):
        cursor = self.db2.cursor()
        cursor.execute(
            """SELECT * FROM baseEquipment WHERE rng = 1 AND minLevel <= ? AND maxLevel >= ?""", (lvl, lvl)
        )
        fetch = cursor.fetchall()
        cursor.close()
        return fetch


    def get_equipment(self, id):
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT * FROM equipment WHERE indx = ?""",
            (id,)
        )
        fetch = cursor.fetchone()
        cursor.close()
        return fetch

    def get_all_equipment(self):
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT * FROM equipment"""
        )
        fetch = cursor.fetchall()
        cursor.close()
        return fetch

    def save_equipment(self, save):
        cursor = self.db.cursor()
        if save[0] == None:
            cursor.execute(
                """INSERT INTO equipment(baseID, level, rarity, startingMods, randomMods) VALUES(?, ?, ?, ?, ?)""",
                (save[1], save[2], save[3], save[4], save[5])
            )
            lastrowid = cursor.lastrowid
        else:
            cursor.execute(
                """UPDATE equipment SET baseID = ?, level = ?, rarity = ?, startingMods = ?, randomMods = ? WHERE indx = ?""",
                (save[1], save[2], save[3], save[4], save[5], save[0])
            )
            lastrowid = save[0]
        cursor.close()
        self.db.commit()
        return lastrowid


    def delete_equipment(self, id):
        cursor = self.db.cursor()
        cursor.execute("""DELETE FROM equipment WHERE indx = ?""", (id,))
        cursor.close()
        self.db.commit()


    # def addEnemy(name, cls, race, attributes, skills, rng):
    #     cursor.execute("""INSERT INTO enemies(name, class, level, xp, race, attributes, skills, rng) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
    #                     (name, cls, 1, 0, race, attributes, skills, rng))
    #     db2.commit()
    #     idToSend = cursor.lastrowid
    #     return idToSend


    # def deleteEnemy(indx):
    #     cursor.execute("""DELETE FROM enemies WHERE indx = ?""", (indx,))
    #     db2.commit()


    def get_base_enemy_indx(self, indx: int):
        cursor = self.db2.cursor()
        cursor.execute("""SELECT * FROM baseEnemies WHERE indx = ?""", (indx,))
        fetch = cursor.fetchone()
        cursor.close()
        return fetch


    def get_base_enemy(self, lvl: int, combat_rank = 1, rng = True):
        cursor = self.db2.cursor()
        if rng:
            cursor.execute(
                """SELECT * FROM baseEnemies WHERE rng = 1 AND minLevel <= ? AND maxLevel >= ? AND combatRank <= ?""",
                (lvl, lvl, combat_rank)
            )
        else:
            cursor.execute(
                """SELECT * FROM baseEnemies WHERE minLevel <= ? AND maxLevel >= ? AND combatRank <= ?""",
                (lvl, lvl, combat_rank)
            )
        fetch = cursor.fetchall()
        cursor.close()
        return fetch


    # def saveEnemy(save):
    #     cursor.execute("""UPDATE enemies SET name = ?, class = ?, level = ?, xp = ?, race = ?, attributes = ?, skills = ?, equipment = ?, inventory = ? WHERE indx = ?""",
    #                     (save[1], save[2], save[3], save[4], save[5], save[6], save[7], save[8], save[9], save[0]))
    #     db2.commit()
    #     return save[0]


    def addRNG(self):
        cursor = self.db.cursor()
        cursor.execute("""INSERT INTO rngdungeons DEFAULT VALUES""")
        lastrowid = cursor.lastrowid
        cursor.close()
        self.db.commit()
        return lastrowid


    def saveRNG(self, save):
        cursor = self.db.cursor()
        if save[0] == 0:
            save[0] = self.addRNG()
        cursor.execute("""UPDATE rngdungeons SET adv = ?, active = ?, stage = ?, stages = ?, enemies = ?, loot = ?, time = ?, xp = ?, combatInfo = ? WHERE indx = ?""",
                    (save[1], save[2], save[3], save[4], save[5], save[6], save[7], save[8], save[9], save[0]))
        cursor.close()
        self.db.commit()
        return save[0]


    def getRNG(self, id):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * FROM rngdungeons WHERE indx = ?""", (id,))
        fetch = cursor.fetchone()
        cursor.close()
        return fetch


    def getActiveRNG(self, aID):
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT * FROM rngdungeons WHERE active = 1 AND adv = ?""", (aID,))
        fetch = cursor.fetchone()
        cursor.close()
        return fetch


    def getTimeRNG(self):
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT * FROM rngdungeons WHERE active = 1 AND time <= datetime('now', 'localtime')""")
        fetch = cursor.fetchall()
        cursor.close()
        return fetch

    def AddShop(self):
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO shop DEFAULT VALUES""")
        lastrowid = cursor.lastrowid
        cursor.close()
        self.db.commit()
        return lastrowid

    def SaveShop(self, save):
        cursor = self.db.cursor()
        if save[0] == 0:
            save[0] = self.AddShop()
        cursor.execute(
            """UPDATE shop SET adv = ?, inventory = ?, buyback = ?, refresh = ? WHERE indx = ?""",
            (save[1], save[2], save[3], save[4], save[0])
        )
        cursor.close()
        self.db.commit()
        return save[0]

    def GetActiveShop(self, id):
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT * FROM shop WHERE adv = ? AND refresh > datetime('now', 'localtime')""",
            (id,)
        )
        fetch = cursor.fetchone()
        cursor.close()
        return fetch

    def get_raid_boss(self, indx: int):
        cursor = self.db2.cursor()
        cursor.execute(
            """SELECT * FROM raid WHERE indx = ?""",
            (indx,)
        )
        fetch = cursor.fetchone()
        cursor.close()
        return fetch

    def get_raids(self):
        cursor = self.db2.cursor()
        cursor.execute(
            """SELECT indx, name, level, flavor FROM raid WHERE available = 1"""
        )
        fetch = cursor.fetchall()
        cursor.close()
        return fetch

    def add_raid(self, players: str, boss: int, loot: str):
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO raid(adventurers, boss, loot, completed) VALUES(?, ?, ?, 0)""",
            (players, boss, loot)
        )
        lastrowid = cursor.lastrowid
        cursor.close()
        self.db.commit()
        return lastrowid

    def complete_raid(self, indx: int, result = 1):
        cursor = self.db.cursor()
        cursor.execute(
            """UPDATE raid SET completed = ? WHERE indx = ?""",
            (result, indx)
        )
        cursor.close()
        self.db.commit()

    def add_server(self, ID: int, name: str, ownerID: int, type_: str):
        cursor = self.db.cursor()
        try:
            cursor.execute(
                """INSERT INTO servers(name, id, ownerID, type) VALUES(?, ?, ?, ?)""",
                (name, ID, ownerID, type_)
            )
        except sqlite3.IntegrityError as e:
            self.db.rollback()
            raise e
        else:
            self.db.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    def update_server(self, ID: int, name: str, ownerID: int, type_: str, categoryID: int, announcementID: int, generalID: int, commandID: str, adventureRole: int, travelRole: int, onjoin: int):
        cursor = self.db.cursor()
        cursor.execute(
            """UPDATE servers SET name = ?, ownerID = ?, type = ?, category = ?, announcement = ?, general = ?, command = ?, adventureRole = ?, travelRole = ?, onjoin = ? WHERE id = ?""",
            (name, ownerID, type_, categoryID, announcementID, generalID, commandID, adventureRole, travelRole, onjoin, ID)
        )
        cursor.close()
        self.db.commit()
        return ID

    def del_server(self, ID: int):
        cursor = self.db.cursor()
        cursor.execute(
            """DELETE FROM servers WHERE id = ?""",
            (ID,)
        )
        cursor.close()
        self.db.commit()

    def get_server(self, ID: int):
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT * FROM servers WHERE id = ?""",
            (ID,)
        )
        fetch = cursor.fetchone()
        cursor.close()
        return fetch

    def get_all_servers(self):
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT * FROM servers"""
        )
        fetch = cursor.fetchall()
        cursor.close()
        return fetch

    def add_raid_channel(self, cID: int, gID: int, advIDs: str):
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO raidChannels(channelID, guildID, advIDs) VALUES(?, ?, ?)""",
            (cID, gID, advIDs)
        )
        cursor.close()
        self.db.commit()

    def del_raid_channel(self, cID: int):
        cursor = self.db.cursor()
        cursor.execute(
            """DELETE FROM raidChannels WHERE channelID = ?""",
            (cID,)
        )
        cursor.close()
        self.db.commit()

    def get_modifier(self, ID: str):
        cursor = self.db2.cursor()
        cursor.execute(
            """SELECT * FROM modifiers WHERE id = ?""",
            (ID,)
        )
        fetch = cursor.fetchone()
        cursor.close()
        return fetch

    def get_elite_modifier(self, ID):
        cursor = self.db2.cursor()
        if isinstance(ID, int):
            cursor.execute(
                """SELECT * FROM eliteModifiers WHERE indx = ?""",
                (ID,)
            )
        elif isinstance(ID, str):
            cursor.execute(
                """SELECT * FROM eliteModifiers WHERE name = ?""",
                (ID,)
            )
        fetch = cursor.fetchone()
        cursor.close()
        return fetch

    def get_storage(self, ID):
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT * FROM storage WHERE adv = ?""",
            (ID,)
        )
        fetch = cursor.fetchone()
        cursor.close()
        return fetch

    def add_storage(self, ID):
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO storage(adv) VALUES(?)""",
            (ID,)
        )
        lastrowid = cursor.lastrowid
        cursor.close()
        self.db.commit()
        return lastrowid

    def update_storage(self, ID, slot, inventory):
        cursor = self.db.cursor()
        cursor.execute(
            """UPDATE storage SET slots = ?, inventory = ? where adv = ?""",
            (slot, inventory, ID)
        )
        cursor.close()
        self.db.commit()
    
    def delete_storage(self, ID):
        cursor = self.db.cursor()
        cursor.execute(
            """DELETE FROM storage WHERE adv = ?""",
            (ID)
        )
        cursor.close()
        self.db.commit()

    def add_trade(self, adv1: int, adv2: int):
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO trade(adv1, adv2) VALUES(?, ?)""",
            (adv1, adv2)
        )
        lastrowid = cursor.lastrowid
        cursor.close()
        self.db.commit()
        return lastrowid

    def update_trade(self, money1: int, money2: int, inventory1: str, inventory2: str, confirm1: int, confirm2: int, waiting_on: int, active: int, indx: int):
        cursor = self.db.cursor()
        cursor.execute(
            """UPDATE trade SET money1 = ?, money2 = ?, inventory1 = ?, inventory2 = ?, confirm1 = ?, confirm2 = ?, waitingOn = ?, active = ? where indx = ?""",
            (money1, money2, inventory1, inventory2, confirm1, confirm2, waiting_on, active, indx)
        )
        cursor.close()
        self.db.commit()

    def get_trade(self, adv: int, active = True, indx = 0):
        cursor = self.db.cursor()
        if indx:
            cursor.execute(
                """SELECT * FROM trade WHERE indx = ?""",
                (indx,)
            )
            fetch = cursor.fetchone()
        elif active:
            cursor.execute(
                """SELECT * FROM trade WHERE adv1 = ? AND active = 1 OR adv2 = ? AND active = 1""",
                (adv, adv)
            )
            fetch = cursor.fetchall()
        else:
            cursor.execute(
                """SELECT * FROM trade WHERE adv1 = ? OR adv2 = ?""",
                (adv, adv)
            )
            fetch = cursor.fetchall()
        cursor.close()
        return fetch

db = Database()