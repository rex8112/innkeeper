from typing import Tuple
import mariadb
import sys

from tools.configLoader import settings

class Database:
    #Initialize database connections
    def __init__(self):
        self.connected = False
        self.blueprint_connected = False
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
                break
            except mariadb.Error as e:
                print(f'Attempt: {i}. Error connecting to MariaDB Platform: {e}\nTry running the included .sql if the database is not found.')
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
                break
            except mariadb.Error as e:
                print(f'Attempt: {i}. Error connecting to MariaDB Platform: {e}')

        self.cur = self.conn.cursor(dictionary=True)
        self.blueprint_cur = self.blueprint_conn.cursor(dictionary=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    #Close all connections
    def close(self):
        self.cur.close()
        self.blueprint_cur.close()
        self.conn.close()
        self.blueprint_conn.close()

    def _execute_sql(self, sql, data: Tuple = None, commit: bool = True):
        try:
            self.cur.execute(sql, data)
            if commit:
                self.conn.commit()
        except mariadb.Error as e:
            print(f'Error executing SQL: {type(e)}: {e}')
            self.conn.rollback()

    def _execute_static_sql(self, sql, data: Tuple = None, commit: bool = True):
        try:
            self.blueprint_cur.execute(sql, data)
            if commit:
                self.blueprint_conn.commit()
        except mariadb.Error as e:
            print(f'Error executing SQL: {type(e)}: {e}')
            self.blueprint_conn.rollback()

    #Insert a new adventurer into the database
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

    def get_base_equipment_lvl(self, lvl: int, rarity: int, rng: bool):
        sql = 'SELECT * FROM baseequipment WHERE minLevel <= ? AND maxLevel >= ? AND maxRarity >= ? AND startingRarity <= ? AND rng = ?'
        data = (lvl, lvl, rarity, rarity, rng)
        self._execute_static_sql(sql, data, False)
        return self.blueprint_cur.fetchall()

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

    def insert_equipment(self, blueprint, level, startingMods, randomMods):
        sql = 'INSERT INTO equipment(blueprint, level, startingMods, randomMods) VALUES(?, ?, ?, ?)'
        data = (blueprint, level, startingMods, randomMods)
        self._execute_sql(sql, data)
        return self.cur.lastrowid

    def update_equipment(self, id, **kwargs):
        sql = 'UPDATE equipment SET '
        data = []
        for key, value in kwargs.items():
            sql += f'{key}=?, '
            data.append(value)
        sql = sql[:-2]
        sql += ' WHERE id=?'
        data = tuple(data + [id])
        self._execute_sql(sql, data)

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