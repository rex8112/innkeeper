import copy

from .exceptions import NotFound

class Race:
    race_dict = {}
    def __init__(self):
        self.id = 'nonrace'
        self.name = 'NonRace'
        self.description = 'No Description'
        self.passive_effect = ''

    @staticmethod
    def get_race(id: str):
        r = Race.race_dict.get(id, None)
        if r:
            return copy.deepcopy(r)
        else:
            raise NotFound(f'{id} class does not exist')

human = Race()
human.id = 'human'
human.name = 'Human'
human.description = 'Humans are known for their tenacity.'
human.passive_effect = 'Debuff Resistance'
Race.race_dict[human.id] = human

elf = Race()
elf.id = 'elf'
elf.name = 'Elf'
elf.description = 'Elves are a rather nimble race and more likely to hit weakpoints.'
elf.passive_effect = 'Critical Hit Buff'
Race.race_dict[elf.id] = elf

dwarf = Race()
dwarf.id = 'dwarf'
dwarf.name = 'Dwarf'
dwarf.description = 'Dwarves have a hearty metabolism for their size.'
dwarf.passive_effect = 'Health Regen'
Race.race_dict[dwarf.id] = dwarf

goblin = Race()
goblin.id = 'goblin'
goblin.name = 'Goblin'
goblin.description = 'Goblins are greedy little bastards'
goblin.passive_effect = 'Essense and Gold gain increase'
Race.race_dict[goblin.id] = goblin
