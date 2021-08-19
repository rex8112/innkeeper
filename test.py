import adventure

with adventure.Database() as db:
    db.insert_adventurer(123, 'Erika', 'adventurer', 'human', '[1,2,3,4,5]', 5634)
    db.delete_adventurer(123)

e = adventure.Equipment()
e.generate_new(5, 3)
print(e.save())
e = adventure.Equipment(3)
print(e.name)