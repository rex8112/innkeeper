from adventure.quests import Quest
from adventure.tools.json_manager import dumps
from adventure.characters import Player
from adventure.race import Race
from adventure.character_class import CharacterClass
import adventure

a = adventure.Player(123, False)
a.new('Erika', CharacterClass.get_class('fighter'), Race.get_race('human'), [1,2,3,4,5,6], 456)
a = adventure.Player(123)

q = Quest()
q.new(123, 5)
q.start()
q.end(True)

a.delete()

e = adventure.Equipment()
e.generate_new(5, 3)
print(dumps(e.save()))