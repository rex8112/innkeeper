import mariadb
import sys

from tools.configLoader import settings

class Database:
    def __init__(self):
        try:
            self.conn = mariadb.connect(
                user=settings.dbuser,
                password=settings.dbpass,
                host=settings.dbhost,
                port=settings.dbport,
                database=settings.dbname
            )
        except mariadb.Error as e:
            print(f'Error connecting to MariaDB Platform: {e}\nTry running the included .sql if the database is not found.')
            sys.exit(1)
        self.cur = self.conn.cursor()