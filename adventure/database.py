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

        self.cur = self.conn.cursor()
        self.blueprint_cur = self.blueprint_conn.cursor()

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
            else:
                self.conn.rollback()
        except mariadb.Error as e:
            print(f'Error executing SQL: {e}')
            self.conn.rollback()

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
        self.cur.execute(sql, data, False)
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