from adventure.quests import Quest
from adventure.tools.json_manager import dumps
from adventure.characters import Player
from adventure.race import Race
from adventure.character_class import CharacterClass
import adventure

d = {'test': 1, 'test2': 2}
print('Creating Adventurer')
a= adventure.Player.new(123, 'Erika', CharacterClass.get_class('fighter'), Race.get_race('human'), [1,2,3,4,5,6], 456)
a = adventure.Player(123)
print('DONE')

a.delete()

e = adventure.Equipment.generate_new(5, 3)
print(dumps(e.save()))