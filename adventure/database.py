from adventure.exceptions import NotFound
from typing import Tuple
import mariadb
import sys

from tools.configLoader import settings

class Database:
    conn = None
    blueprint_conn = None
    connections = 0

    #Initialize database connections
    def __init__(self):
        self.connected = False
        self.blueprint_connected = False
        if Database.conn:
            self.conn = Database.conn
        else:
            for i in range(1, 5):
                try:
                    self.conn = mariadb.connect(
                        user=settings.dbuser,
                        password=settings.dbpass,
                        host=settings.dbhost,
                        port=settings.dbport,
                        database=settings.dbname
                    )
                    self.connected = True
                    Database.conn = self.conn
                    break
                except mariadb.Error as e:
                    print(f'Attempt: {i}. Error connecting to MariaDB Platform: {e}\nTry running the included .sql if the database is not found.')
        if Database.blueprint_conn:
            self.blueprint_conn = Database.blueprint_conn
        else:
            for i in range(1, 5):
                try:
                    self.blueprint_conn = mariadb.connect(
                        user=settings.blueprintuser,
                        password=settings.blueprintpass,
                        host=settings.blueprinthost,
                        port=settings.blueprintport,
                        database=settings.blueprintname
                    )
                    self.blueprint_connected = True
                    Database.blueprint_conn = self.blueprint_conn
                    break
                except mariadb.Error as e:
                    print(f'Attempt: {i}. Error connecting to MariaDB Platform: {e}')

        self.cur = self.conn.cursor(dictionary=True)
        self.blueprint_cur = self.blueprint_conn.cursor(dictionary=True)
        Database.connections += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    #Close all connections
    def close(self):
        self.cur.close()
        self.blueprint_cur.close()
        Database.connections -= 1
        if Database.connections == 0:
            self.conn.close()
            self.blueprint_conn.close()
            Database.conn = None
            Database.blueprint_conn = None

    #Execute SQL
    def _execute_sql(self, sql, data: Tuple = None, commit: bool = True):
        try:
            self.cur.execute(sql, data)
            if commit:
                self.conn.commit()
        except mariadb.Error as e:
            print(f'Error executing SQL: {type(e)}: {e}')
            self.conn.rollback()

    #Execute SQL for blueprint database
    def _execute_static_sql(self, sql, data: Tuple = None, commit: bool = True):
        try:
            self.blueprint_cur.execute(sql, data)
            if commit:
                self.blueprint_conn.commit()
        except mariadb.Error as e:
            print(f'Error executing static SQL: {type(e)}: {e}')
            self.blueprint_conn.rollback()

    def fetchone(self, iterable):
        if not iterable:
            raise NotFound(f'No results found')
        one = iterable[0]
        return one

    #DATABASE FUNCTIONS
    def insert_adventurer(self, id, name, cls, race, attributes, home):
        sql = 'INSERT INTO adventurers(userID, name, class, race, attributes, home) VALUES(?, ?, ?, ?, ?, ?)'
        data = (id, name, cls, race, attributes, home)
        self._execute_sql(sql, data)
    
    def delete_adventurer(self, id):
        sql = "DELETE FROM adventurers WHERE userID=?"
        data = (id,)
        self._execute_sql(sql, data)

    def get_adventurer(self, **kwargs):
        sql = 'SELECT * FROM adventurers WHERE '
        for key, value in kwargs.items():
            sql += f'{key}=? AND '
        sql = sql[:-4]
        data = tuple(kwargs.values())
        self._execute_sql(sql, data, False)
        return self.cur.fetchall()

    def update_adventurer(self, id, **kwargs):
        sql = 'UPDATE adventurers SET '
        data = []
        for key, value in kwargs.items():
            sql += f'{key}=?, '
            data.append(value)
        sql = sql[:-2]
        sql += ' WHERE userID=?'
        data = tuple(data + [id])
        self._execute_sql(sql, data)

    def get_equipment(self, **kwargs):
        sql = 'SELECT * FROM equipment WHERE '
        data = []
        for key, value in kwargs.items():
            sql += f'{key}=? AND '
            data.append(value)
        sql = sql[:-4]
        data = tuple(data)
        self._execute_sql(sql, data, False)
        return self.cur.fetchall()

    def insert_equipment(self, blueprint, level, rarity, startingMods, randomMods):
        sql = 'INSERT INTO equipment(blueprint, level, rarity, startingMods, randomMods) VALUES(?, ?, ?, ?, ?)'
        data = (blueprint, level, rarity, startingMods, randomMods)
        self._execute_sql(sql, data)
        return self.cur.lastrowid

    def update_equipment(self, id, **kwargs):
        sql = 'UPDATE equipment SET '
        data = []
        for key, value in kwargs.items():
            sql += f'{key}=?, '
            data.append(value)
        sql = sql[:-2]
        sql += ' WHERE indx=?'
        data = tuple(data + [id])
        self._execute_sql(sql, data)

    def delete_equipment(self, id):
        sql = 'DELETE FROM equipment WHERE id=?'
        data = (id,)
        self._execute_sql(sql, data)

    # BLUEPRINT FUNCTIONS
    def get_modifier(self, **kwargs):
        sql = 'SELECT * FROM modifiers WHERE '
        data = []
        for key, value in kwargs.items():
            sql += f'{key}=? AND '
            data.append(value)
        sql = sql[:-4]
        data = tuple(data)
        self._execute_static_sql(sql, data, False)
        return self.blueprint_cur.fetchall()

    def get_base_equipment(self, **kwargs):
        sql = 'SELECT * FROM baseequipment WHERE '
        data = []
        for key, value in kwargs.items():
            sql += f'{key}=? AND '
            data.append(value)
        sql = sql[:-4]
        data = tuple(data)
        self._execute_static_sql(sql, data, False)
        return self.blueprint_cur.fetchall()

    def get_base_equipment_lvl(self, lvl: int, rarity: int, **kwargs):
        sql = 'SELECT * FROM baseequipment WHERE minLevel <= ? AND maxLevel >= ? AND maxRarity >= ? AND startingRarity <= ? AND '
        data = [lvl, lvl, rarity, rarity]
        for key, value in kwargs.items():
            sql += f'{key}=? AND '
            data.append(value)
        sql = sql[:-4]
        data = tuple(data)
        self._execute_static_sql(sql, data, False)
        return self.blueprint_cur.fetchall()

    def get_base_enemy(self, **kwargs):
        sql = 'SELECT * FROM baseenemies WHERE '
        data = []
        for key, value in kwargs.items():
            sql += f'{key}=? AND '
            data.append(value)
        sql = sql[:-4]
        data = tuple(data)
        self._execute_static_sql(sql, data, False)
        return self.blueprint_cur.fetchall()

    def get_base_enemy_lvl(self, lvl: int, **kwargs):
        sql = 'SELECT * FROM baseenemies WHERE minLevel <= ? AND maxLevel >= ? AND '
        data = [lvl, lvl]
        for key, value in kwargs.items():
            if key == 'combatRank':
                sql += f'{key}<? AND '
            else:
                sql += f'{key}=? AND '
            data.append(value)
        sql = sql[:-4]
        data = tuple(data)
        self._execute_static_sql(sql, data, False)
        return self.blueprint_cur.fetchall()

    def insert_quest(self, adventurer, stages, time, **kwargs):
        sql = 'INSERT INTO quests(adventurer, stages, time, '
        data = [adventurer, stages, time]
        for key, value in kwargs.items():
            sql += f'{key}, '
            data.append(value)
        sql = sql[:-2]
        sql += ') VALUES(?, ?, ?, '
        sql += ', '.join(['?'] * len(data)) + ')'
        data = tuple(data)
        self._execute_sql(sql, data)
        return self.cur.lastrowid

    def update_quest(self, id, **kwargs):
        sql = 'UPDATE quests SET '
        data = []
        for key, value in kwargs.items():
            sql += f'{key}=?, '
            data.append(value)
        sql = sql[:-2]
        sql += ' WHERE id=?'
        data = tuple(data + [id])
        self._execute_sql(sql, data)

    def get_quest(self, **kwargs):
        sql = 'SELECT * FROM quests WHERE '
        data = []
        for key, value in kwargs.items():
            sql += f'{key}=? AND '
            data.append(value)
        sql = sql[:-4]
        data = tuple(data)
        self._execute_sql(sql, data, False)
        return self.cur.fetchall()