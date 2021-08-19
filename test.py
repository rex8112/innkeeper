from adventure.race import Race
from adventure.character_class import CharacterClass
import adventure

a = adventure.Player(123, False)
a.new('Erika', CharacterClass.get_class('warrior'), Race.get_race('human'), [1,2,3,4,5,6], 456)

e = adventure.Equipment()
e.generate_new(5, 3)
print(e.save())
e = adventure.Equipment(3)
print(e.name)