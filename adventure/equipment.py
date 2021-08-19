import json
import random
import logging
import math

from .modifiers import Modifier, Effect
from .skills import Skill
from .database import Database
from .exceptions import InvalidBaseEquipment, InvalidModString
from .formatting import Formatting
from .tools.json_manager import dumps

logger = logging.getLogger('characters')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
handler2 = logging.FileHandler(
    filename='latest.log', encoding='utf-8', mode='a')
handler2.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
logger.addHandler(handler2)

class BaseEquipment:
    def __init__(self, ID = 0):
        try:
            self.id = int(ID)
        except ValueError:
            self.id = ID
        if self.id == 'empty':
            self.load(
                {
                    'indx': 'empty',
                    'name': 'Empty',
                    'flavor': 'Nothing is equipped',
                    'slot': 'all',
                    'minLevel': 1,
                    'maxLevel': 1000,
                    'startingRarity': 0,
                    'maxRarity': 0,
                    'startingModString': None,
                    'randomModString': '',
                    'requirementString': None,
                    'flags': 'empty|unsellable',
                    'damageString': None,
                    'skills': None,
                    'rng': 0
                }
            )
        elif self.id != 0:
            self.load(self.id)

    def load(self, ID):
        if isinstance(ID, int):
            with Database() as db:
                data = db.get_base_equipment(indx=ID)
                if data:
                    data = data[0]
        else:
            data = ID
        self.id = str(data['indx'])
        self.name = str(data['name'])
        self.flavor = str(data['flavor'])
        self.slot = str(data['slot'])
        self.min_level = int(data['minLevel'])
        self.max_level = int(data['maxLevel'])
        self.starting_rarity = int(data['startingRarity'])
        self.max_rarity = int(data['maxRarity'])

        if data['startingModString']:
            self.starting_mod_string = str(data['startingModString']) + f'|{self.get_class()}'
        else:
            self.starting_mod_string = self.get_class()
        self.random_mod_string = str(data['randomModString'])
        self.damage_string = str(data['damageString'])
        self.flags = str(data['flags'])
        if data['requirementString']:
            self.requirement_string = str(data['requirementString'])
        else:
            self.requirement_string = None
        if data['skills']:
            self.skills_string = str(data['skills'])
        else:
            self.skills_string = None
        self.rng = bool(data['rng'])

    def new(self, lvl: int, rarity: int, RNG = True):
        with Database() as db:
            data = db.get_base_equipment_lvl(lvl=lvl, rarity=rarity, rng=RNG)
        if not data:
            raise InvalidBaseEquipment
        chosen_data = random.choice(data)
        self.load(chosen_data)

    def get_class(self):
        base_min = 9
        min_increase = 12
        base_max = 36
        max_increase = 14
        current_min = base_min + min_increase * (self.min_level)
        current_max = base_max + max_increase * (self.min_level)
        value_string = f'{current_min}+{min_increase}/{current_max}+{max_increase}'
        if self.slot == 'mainhand' or self.slot == 'offhand':
            class_string = 'wc'
        else:
            class_string = 'ac'
        return f'{class_string}:{value_string}'

        

class Equipment:
    def __init__(self, ID=0):
        self.loaded = False
        try:
            self.id = int(ID)
        except (ValueError, TypeError):
            self.id = ID
        if self.id == 'empty' or self.id == 'None':
            data_list = ['empty', 'empty', 1, 0, '', '']
            self.load(data_list=data_list)
        elif isinstance(self.id, (list, tuple)):
            self.load(data_list=self.id)
        elif isinstance(self.id, str):
            self.load(data_list=self.id.split(','))
        elif self.id != 0:
            self.load()

    @staticmethod
    def calculate_drop_rarity():
        result = 0
        if random.random() <= 0.01:
            result = 4
        elif random.random() <= 0.10:
            result = 3
        elif random.random() <= 0.25:
            result = 2
        elif random.random() <= 0.40:
            result = 1

        return result

    def getRarity(self):
        if self.name == 'Empty':
            return ''
        elif self.rarity == 0:
            return 'Common'
        elif self.rarity == 1:
            return 'Uncommon'
        elif self.rarity == 2:
            return 'Rare'
        elif self.rarity == 3:
            return 'Epic'
        elif self.rarity == 4:
            return 'Legendary'

    def getInfo(self, compare_equipment = None, title = True):
        if self.name == 'Empty':
            info = '{}'.format(self.name)
        else:
            if title:
                info = f'{self.get_name(level=False)}\nLevel: **{self.level}**\n\nPrice: **{self.price}** (**{self.sell_price}**)\n'
            else:
                info = f'{self.flavor}\n\nLevel: **{self.level}**\nPrice (Sell): **{self.price}** (**{self.sell_price}**)\n'

            info += '\n__Item Modifiers__\n'
            for mod in self.starting_mods.values():
                if compare_equipment:
                    other = compare_equipment.starting_mods.get(mod.id, Modifier(mod.id, 0))
                    compare = mod.value - other.value
                    info += f'{str(mod).capitalize()}: **{int(mod)}** *({int(compare)})*{Formatting.get_difference_emoji(compare)}\n'
                else:
                    info += f'{str(mod).capitalize()}: **{int(mod)}**\n'

            if len(self.random_mods) > 0:
                info += '\n__Rarity Modifiers__\n'
            for mod in self.random_mods.values():
                if compare_equipment:
                    other = compare_equipment.random_mods.get(mod.id, Modifier(mod.id, 0))
                    compare = mod.value - other.value
                    info += f'{str(mod).capitalize()}: **{int(mod)}** *({int(compare)})*{Formatting.get_difference_emoji(compare)}\n'
                else:
                    info += f'{str(mod).capitalize()}: **{int(mod)}**\n'
            
            if len(self.requirements) > 0:
                info += '\n__Requirements__\n'
            for mod in self.requirements.values():
                info += f'{str(mod).capitalize()}: **{int(mod)}**\n'
            info += f'\nIdentification: **{self.id}**'
        return info

    def get_name(self, rarity=True, level=True, discord=True):
        name = self.name
        if level and discord:
            name = f'**Lv. {self.level}** {name}'
        elif level:
            name = f'Lv. {self.level} {name}'
        if rarity:
            name = f'{Formatting.get_rarity_emoji(self.rarity)} {name}'
        return name

    def process_mod_string_min_max(self, mod_string: str):
        min_mods = {}
        max_mods = {}
        level = self.level - self.base_equipment.min_level
        mod_string_list = mod_string.split('|')
        try:
            for mod in mod_string_list:
                key, value_string = tuple(mod.split(':'))
                min_string, max_string = tuple(value_string.split('/'))
                min_value, min_per_level = tuple(min_string.split('+'))
                max_value, max_per_level = tuple(max_string.split('+'))
                final_min_volume = float(min_value) + (float(min_per_level) * level)
                final_max_volume = float(max_value) + (float(max_per_level) * level)
                min_mods[key] = Modifier(key, round(final_min_volume, 1))
                max_mods[key] = Modifier(key, round(final_max_volume, 1))
            return min_mods, max_mods
        except ValueError as e:
            raise InvalidModString('Invalid Mod String: `{}` {}'.format(mod_string, e))

    def process_mod_string(self, mod_string: str): # May be moved to Equipment
        mods = {}
        level = self.level - self.base_equipment.min_level
        mod_string_list = mod_string.split('|')
        try:
            for mod in mod_string_list:
                key, value_string = tuple(mod.split(':'))
                min_string, max_string = tuple(value_string.split('/'))
                min_value, min_per_level = tuple(min_string.split('+'))
                max_value, max_per_level = tuple(max_string.split('+'))
                final_min_volume = float(min_value) + (float(min_per_level) * level)
                final_max_volume = float(max_value) + (float(max_per_level) * level)
                final_mod = Modifier(key, round(random.uniform(final_min_volume, final_max_volume), 1))
                if mods.get(key, False): # Determine if this modifier is already in the dictionary
                    final_mod.value += mods.get(key).value
                mods[key] = final_mod
            return mods
        except ValueError as e:
            raise InvalidModString('Invalid Mod String: `{}` {}'.format(mod_string, e))

    def process_requirement_string(self, requirement_string: str):
        requirements = {}
        level = self.level - self.base_equipment.min_level
        requirement_string_list = requirement_string.split('|')
        for requirement in requirement_string_list:
            key, value_string = tuple(requirement.split(':'))
            value, per_level = tuple(value_string.split('+'))
            final_value = int(value) + math.floor(float(per_level) * level)
            final_requirement = Modifier(key, final_value)
            requirements[key] = final_requirement
        return requirements

    def process_skills_string(self, skills_string: str):
        skills = skills_string.split('|')
        return skills

    def process_damage_string(self, damage_string: str):
        # 'dmg:20+5,str_scale.1,dex_scale.1|...'
        damage = {}
        if not damage_string or damage_string == 'None':
            return damage
        damage_list = damage_string.split('|')
        for d in damage_list:
            scalars = {}
            damage_type, values = tuple(d.split(':'))
            values_list = values.split(',')
            base, per_level = values_list[0].split('+')
            base_damage = int(base) + (self.level - self.base_equipment.min_level) * int(per_level)
            if len(values_list) > 1:
                scales = values_list[1:]
                for s in scales:
                    attribute, amount = tuple(s.split('.'))
                    scalars[attribute] = int(amount)
            damage[damage_type] = (Modifier(damage_type, value=base_damage), scalars)
        return damage

    def generate_damage(self, adv):
        self.damage = {}
        for key, value in self.raw_damage.items():
            mod, scalars = value
            for attribute, amount in scalars.items():
                if attribute == 'str_scale':
                    a = adv.strength
                elif attribute == 'dex_scale':
                    a = adv.dexterity
                elif attribute == 'con_scale':
                    a = adv.constitution
                elif attribute == 'int_scale':
                    a = adv.intelligence
                elif attribute == 'wis_scale':
                    a = adv.wisdom
                elif attribute == 'cha_scale':
                    a = adv.charisma
                amount_to_add = ((a * amount) / 200) * mod.value
                e = Effect(attribute, key, amount_to_add)
                mod.add_effect(e)
            self.damage[key] = mod

    def calculate_price(self):
        base_price = 10
        price_per_mod = 100
        price_per_level = 10 * math.ceil(self.level / 10)
        rarity_coefficient = 1 + (self.rarity * 0.5)
        self.price = int((base_price + (price_per_level * self.level) + (price_per_mod * (len(self.starting_mods) + len(self.random_mods)))) * rarity_coefficient)
        self.sell_price = int(self.price * 0.5)

    def generate_new(self, lvl: int, rarity: int, index = 0):
        if index == 0:
            self.base_equipment = BaseEquipment()
            self.base_equipment.new(lvl, rarity)
        else:
            self.base_equipment = BaseEquipment(index)

        self.id = None
        self.name = self.base_equipment.name
        self.level = lvl
        self.flavor = self.base_equipment.flavor
        if rarity < self.base_equipment.starting_rarity:
            self.rarity = self.base_equipment.starting_rarity
        else:
            self.rarity = rarity
        self.slot = self.base_equipment.slot
        self.raw_damage = self.process_damage_string(self.base_equipment.damage_string)
        self.damage = {}
        self.flags = self.base_equipment.flags.split('|')
        self.starting_mods = self.process_mod_string(self.base_equipment.starting_mod_string)
        self.random_mods = {}
        if self.rarity > 0 and self.base_equipment.random_mod_string: # Determine if new mods are needed
            potential_mods = self.process_mod_string(self.base_equipment.random_mod_string)
            new_mods = random.sample(list(potential_mods.values()), self.rarity) # Grab an amount based on rarity
            for mod in new_mods: # Add new mods
                if self.random_mods.get(mod.id, False):
                    self.random_mods[mod.id].value += mod.value
                else:
                    self.random_mods[mod.id] = mod

            highest_mod = max(new_mods) # Set title
            if highest_mod.title:
                self.name += ' {}'.format(highest_mod.title)

        # for key, value in self.starting_mods.items(): # Put starting_mods and random_mods together
        #     if self.mods.get(key, False):
        #         self.mods[key] += value
        #     else:
        #         self.mods[key] = value

        # for key, value in self.random_mods.items():
        #     if self.mods.get(key, False):
        #         self.mods[key] += value
        #     else:
        #         self.mods[key] = value

        if self.base_equipment.requirement_string:
            self.requirements = self.process_requirement_string(self.base_equipment.requirement_string)
        else:
            self.requirements = {}

        if self.base_equipment.skills_string:
            self.skills = self.process_skills_string(self.base_equipment.skills_string)
        else:
            self.skills = []
        self.calculate_price()
        self.loaded = True
        return True

    def load(self, data_list = None):
        try:
            if data_list:
                if isinstance(data_list, (list, tuple)):
                    data = data_list
                elif isinstance(data_list, str):
                    data = data_list.split(',')
            else:
                with Database() as db:
                    data = db.get_equipment(indx=self.id)
                    if data:
                        data = data[0]
            if data['indx'] == 'None':
                self.id = None
            else:
                self.id = data['indx']
            self.base_equipment = BaseEquipment(data['blueprint'])
            self.level = int(data['level'])
            self.rarity = int(data['rarity'])
            self.starting_mods = {}
            self.random_mods = {}
            try:
                starting_mods = json.loads(data['startingMods'])
                random_mods = json.loads(data['randomMods'])
            except TypeError:
                starting_mods = data['startingMods']
                random_mods = data['randomMods']
            self.name = self.base_equipment.name
            self.flavor = self.base_equipment.flavor
            self.raw_damage = self.process_damage_string(self.base_equipment.damage_string)
            self.damage = {}
            self.slot = self.base_equipment.slot
            if self.base_equipment.requirement_string:
                self.requirements = self.process_requirement_string(self.base_equipment.requirement_string)
            else:
                self.requirements = {}
            if self.base_equipment.skills_string:
                self.skills = self.process_skills_string(self.base_equipment.skills_string)
            else:
                self.skills = []

            for mod_data in starting_mods.values():
                mod = Modifier.from_dict(mod_data)
                self.starting_mods[mod.id] = mod

            for mod_data in random_mods.value():
                mod = Modifier.from_dict(mod_data)
                if self.random_mods.get(mod.id, False):
                    self.random_mods[mod.id].value += mod.value
                else:
                    self.random_mods[mod.id] = mod
                    
            if len(self.random_mods) > 0:
                highest_mod = max(self.random_mods.values()) # Set title
                if highest_mod.title:
                    self.name += ' {}'.format(highest_mod.title)

            self.calculate_price()

            logger.debug('{}:{} Loaded Successfully'.format(
                self.id, self.name))
            self.loaded = True
            return True
        except Exception:
            logger.error('{} Failed to Load'.format(
                self.id), exc_info=True)

            self.loaded = False
            return False

    def save(self, database = False):
        starting_mods = dumps(self.starting_mods)
        random_mods = dumps(self.random_mods)

        save = {'blueprint': self.base_equipment.id, 'level': self.level, 'rarity': self.rarity, 'startingMods': starting_mods, 'randomMods': random_mods}
        if database and self.id is None:
            with Database() as db:
                self.id = db.insert_equipment(self.base_equipment.id, self.level, self.rarity, starting_mods, random_mods)
                save[0] = self.id
            return str(self.id)
        elif self.id:
            with Database() as db:
                db.update_equipment(self.id, save)
            return str(self.id)
        logger.debug('{}:{} Saved Successfully'.format(self.id, self.name))
        save['indx'] = self.id
        return dumps(save)

    def balance_check(self):
        changed = False
        if self.level > self.base_equipment.max_level:
            self.level = self.base_equipment.max_level
            changed = True
        elif self.level < self.base_equipment.min_level:
            self.level = self.base_equipment.min_level
            changed = True
            
        starting_min, starting_max = self.process_mod_string_min_max(self.base_equipment.starting_mod_string)
        random_min, random_max = self.process_mod_string_min_max(self.base_equipment.random_mod_string)
        starting_to_delete = []
        random_to_delete = []
        for mod in self.starting_mods.values(): # Check min/max of starting mods and also delete mods no longer listed.
            min_mod = starting_min.get(mod.id, None)
            max_mod = starting_max.get(mod.id, None)
            if min_mod:
                if mod < min_mod:
                    mod.value = min_mod.value
                    changed = True
                elif mod > max_mod:
                    mod.value = max_mod.value
                    changed = True
            else:
                starting_to_delete.append(mod.id)
                changed = True

        for ID in starting_to_delete:
            del self.starting_mods[ID]

        for min_mod in starting_min.values(): # Check if there are any new mods that are not listed in starting mods and random it
            mod = self.starting_mods.get(min_mod.id, None)
            if not mod:
                min_value = min_mod.value
                max_value = starting_max[min_mod.id].value
                self.starting_mods[min_mod.id] = Modifier(min_mod.id, round(random.uniform(min_value, max_value), 1))
                changed = True

        amount_to_add = 0
        for mod in self.random_mods.values(): # Check min/max of random mods and delete non-existing mods
            min_mod = random_min.get(mod.id, None)
            if min_mod:
                if mod < min_mod:
                    mod.value = min_mod.value
                    changed = True
                elif mod > random_max[min_mod.id]:
                    mod.value = random_max[min_mod.id].value
                    changed = True
            else:
                random_to_delete.append(mod.id)
                amount_to_add += 1
                changed = True

        for ID in random_to_delete:
            del self.random_mods[ID]

        if self.rarity > self.base_equipment.max_rarity:
            change = self.rarity - self.base_equipment.max_rarity
            self.rarity = self.base_equipment.max_rarity
            amount_to_add -= change
        elif self.rarity < self.base_equipment.starting_rarity:
            change = self.base_equipment.starting_rarity - self.rarity
            self.rarity = self.base_equipment.starting_rarity
            amount_to_add += change
        
        if amount_to_add > 0: # If existing random mods were removed, fill their void with new mods
            for min_mod in random_min.values():
                mod = self.random_mods.get(min_mod.id, None)
                if not mod: # Make sure that mod was never used before
                    min_value = min_mod.value
                    max_value = random_max[min_mod.id].value
                    self.random_mods[min_mod.id] = Modifier(min_mod.id, round(random.uniform(min_value, max_value), 1))
                    amount_to_add -= 1
                if amount_to_add <= 0:
                    break
        elif amount_to_add < 0:
            while amount_to_add < 0:
                mod_to_delete = random.choice(self.random_mods)
                del self.random_mods[mod_to_delete.id]
                amount_to_add += 1
        return changed

    def delete(self):
        if isinstance(self.id, int):
            db.delete_equipment(self.id)
        logger.debug('{}:{} Deleted'.format(self.id, self.name))
        self.id = None