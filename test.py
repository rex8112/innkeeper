from adventure.database import Database

db = Database()
db.insert_adventurer(123, 'Erika', 'adventurer', 'human', '[1,2,3,4,5]', 5634)
db.delete_adventurer(123)