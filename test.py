from adventure.quests import Quest
from adventure.tools.json_manager import dumps
from adventure.characters import Player
from adventure.race import Race
from adventure.character_class import CharacterClass
import adventure

print('Creating Adventurer')
a = adventure.Player(123, False)
a.new('Erika', CharacterClass.get_class('fighter'), Race.get_race('human'), [1,2,3,4,5,6], 456)
a = adventure.Player(123)
print('DONE')
print('Creating Quest')
q = Quest()
q.new(123, 5)
print('Starting Quest')
q.start()
q.end(True)
print('DONE')

a.delete()

e = adventure.Equipment()
e.generate_new(5, 3)
print(dumps(e.save()))