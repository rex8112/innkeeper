import copy

from .exceptions import NotFound

class CharacterClass:
    class_dict = {}
    def __init__(self, class_id = ''):
        self.id = 'nothing'
        self.name = 'Nothing'
        self.description = 'No Description'
        self.attribute_bonuses = [1, 1, 1, 1, 1, 1]
        if class_id:
            self = CharacterClass.get_class(class_id)

    @staticmethod
    def get_class(id: str):
        c = CharacterClass.class_dict.get(id, None)
        if c:
            return copy.deepcopy(c)
        else:
            raise NotFound(f'{id} class does not exist')

fighter = CharacterClass()
fighter.id = 'fighter'
fighter.name = 'Fighter'
fighter.description = 'Description Coming Soon'
fighter.attribute_bonuses = [2, 1, 1.5, 1, 1, 1]
CharacterClass.class_dict[fighter.id] = fighter

rogue = CharacterClass()
rogue.id = 'rogue'
rogue.name = 'Rogue'
rogue.description = 'Description Coming Soon'
rogue.attribute_bonuses = [1, 2, 1, 1.5, 1, 1]

bard = CharacterClass()
bard.id = 'bard'
bard.name = 'Bard'
bard.description = 'Description Coming Soon'
bard.attribute_bonuses = [1, 1.5, 1, 1, 1, 2]
CharacterClass.class_dict[bard.id] = bard

cleric = CharacterClass()
cleric.id = 'cleric'
cleric.name = 'Cleric'
cleric.description = 'Description Coming Soon'
cleric.attribute_bonuses = [1, 1, 1, 1, 2, 1.5]
CharacterClass.class_dict[cleric.id] = cleric

wizard = CharacterClass()
wizard.id = 'wizard'
wizard.name = 'Wizard'
wizard.description = 'Description Coming Soon'
wizard.attribute_bonuses = [1, 1, 1, 2, 1.5, 1]
CharacterClass.class_dict[wizard.id] = wizard
