from adventure.tools.json_manager import dumps
import json
import logging
import math
import random
from typing import List

from discord import Member, User, Embed
from .data import PerLevel, TestData
from .skills import get_skill
from .statusEffects import PassiveEffect
from .exceptions import InvalidLevel, InvalidRequirements, InvalidModString
from .equipment import Equipment
from .modifiers import Modifier, EliteModifier, ModifierDict
from .database import Database
from .character_class import CharacterClass
from .race import Race

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

class Character:
    baseXP = 25
    xpRate = 0.035
    pc = False

    def __init__(self, ID):
        self.id = ID
        self.name = 'Unloaded'
        self.mods = ModifierDict()
        self.raw_mods = ModifierDict()
        self.total_ac = []
        self.total_wc = []
        self.effects = {}
        self.status_effects = {}
        self.passive_effects = {}
        self.loaded = False

    def __str__(self):
        return self.name

    def __index__(self):
        return self.id

    def __int__(self):
        return self.id

    def new(self, name, cls, race, rawAttributes, skills, rng): # This should be overridden
        self.name = name
        self.cls = cls
        self.race = race
        self.level = 1
        self.xp = 0
        # Attributes
        self.rawStrength = rawAttributes[0]
        self.rawDexterity = rawAttributes[1]
        self.rawConstitution = rawAttributes[2]
        self.rawIntelligence = rawAttributes[3]
        self.rawWisdom = rawAttributes[4]
        self.rawCharisma = rawAttributes[5]
        # Skills
        self.raw_skills = ['attack'] + skills
        # Equipment
        self.mainhand = Equipment('empty')
        self.offhand = Equipment('empty')
        self.helmet = Equipment('empty')
        self.armor = Equipment('empty')
        self.gloves = Equipment('empty')
        self.boots = Equipment('empty')
        self.trinket = Equipment('empty')

        self.inventory = []
        self.loaded = True

    def load(self):
        pass

    def equip(self, e: int):
        try:
            eq = self.inventory[e]

            if self.level < eq.level:
                raise InvalidLevel('{} is too low level to equip level {} {}'.format(self.name, eq.level, eq.name))
            elif self.strength < eq.requirements.get('strength', 0):
                raise InvalidRequirements('{} does not have enough strength to equip {}'.format(self.name, eq.name))
            elif self.dexterity < eq.requirements.get('dexterity', 0):
                raise InvalidRequirements('{} does not have enough dexterity to equip {}'.format(self.name, eq.name))
            elif self.constitution < eq.requirements.get('constitution', 0):
                raise InvalidRequirements('{} does not have enough constitution to equip {}'.format(self.name, eq.name))
            elif self.intelligence < eq.requirements.get('intelligence', 0):
                raise InvalidRequirements('{} does not have enough intelligence to equip {}'.format(self.name, eq.name))
            elif self.wisdom < eq.requirements.get('wisdom', 0):
                raise InvalidRequirements('{} does not have enough wisdom to equip {}'.format(self.name, eq.name))
            elif self.charisma < eq.requirements.get('charisma', 0):
                raise InvalidRequirements('{} does not have enough charisma to equip {}'.format(self.name, eq.name))

            self.rem_item(e)
            if eq.slot == 'mainhand':
                uneq = self.mainhand
                self.mainhand = eq
            elif eq.slot == 'offhand':
                uneq = self.offhand
                self.offhand = eq
            elif eq.slot == 'helmet':
                uneq = self.helmet
                self.helmet = eq
            elif eq.slot == 'armor':
                uneq = self.armor
                self.armor = eq
            elif eq.slot == 'gloves':
                uneq = self.gloves
                self.gloves = eq
            elif eq.slot == 'boots':
                uneq = self.boots
                self.boots = eq
            elif eq.slot == 'trinket':
                uneq = self.trinket
                self.trinket = eq
            else:
                return

            if not uneq.requirements.get('empty', False):
                self.inventory.append(uneq)
            self.calculate()
            return True
        except IndexError:
            return False

    def unequip(self, slot: str):
        eq = Equipment('empty')
        if slot == 'mainhand':
            uneq = self.mainhand
            self.mainhand = eq
        elif slot == 'offhand':
            uneq = self.offhand
            self.offhand = eq
        elif slot == 'helmet':
            uneq = self.helmet
            self.helmet = eq
        elif slot == 'armor':
            uneq = self.armor
            self.armor = eq
        elif slot == 'gloves':
            uneq = self.gloves
            self.gloves = eq
        elif slot == 'boots':
            uneq = self.boots
            self.boots = eq
        elif slot == 'trinket':
            uneq = self.trinket
            self.trinket = eq
        else:
            return

        if not uneq.mods.get('empty', False):
            self.inventory.append(uneq)
        self.calculate()

    def add_item(self, item):
        """Adds item to inventory
        Returns success in bool"""
        try:
            if len(self.inventory) < self.inventoryCapacity:
                self.inventory.append(item)
                logger.debug('Adding {} to Inventory'.format(item))
                return True
            else:
                return False
        except AttributeError:
            self.calculate()
            return self.add_item(item)

    def rem_item(self, index: int):
        """Remove indexed item from inventory.
        Returns item removed or None"""
        try:
            item = self.inventory[index]
            self.inventory.pop(index)
            return item
        except ValueError:
            return None

    def add_xp(self, count: int):
        amount_to_add = count * self.mods['xp_rate'].get_total()
        self.xp += amount_to_add
        return amount_to_add

    def rem_xp(self, count: int, force=False):
        if self.xp - count >= 0:
            self.xp -= count
            return True
        else:
            if force:
                self.xp = 0
                return True
            else:
                return False

    def get_xp_to_level(self):
        if self.level < PerLevel.level_cap:
            reqXP = self.baseXP * math.exp(self.xpRate * (self.level - 1))
        else:
            return math.inf
        return int(reqXP)

    def get_unspent_points(self):
        total_points = (self.rawStrength
                        + self.rawDexterity
                        + self.rawConstitution
                        + self.rawIntelligence
                        + self.rawWisdom
                        + self.rawCharisma)
        unspent_points = (self.level - 1) - (total_points - 5)
        return unspent_points

    def get_skill(self, skill_name: str):
        try:
            for skill in self.skills:
                if skill.name.lower() == skill_name.lower():
                    return skill
            return None
        except AttributeError:
            return None

    def get_equipment_from_slot(self, slot: str):
        if slot == 'mainhand':
            return self.mainhand
        elif slot == 'offhand':
            return self.offhand
        elif slot == 'helmet':
            return self.helmet
        elif slot == 'armor':
            return self.armor
        elif slot == 'gloves':
            return self.gloves
        elif slot == 'boots':
            return self.boots
        elif slot == 'trinket':
            return self.trinket
        else:
            raise ValueError('Incorrect Slot Passed')

    def fill_inventory_embed(self, embed: Embed):
        for count, e in enumerate(self.inventory, start=1):
            embed.add_field(name=f'------- Slot {count:02} -------', value=e.getInfo(compare_equipment=self.get_equipment_from_slot(e.slot)))

    def roll_initiative(self):
        return random.randint(1, 20) + self.level

    def deal_physical_damage(self, value: float, penetration = 0, multiplicative = False):
        parmor = self.mods.get('parmor') - float(penetration)
        if multiplicative:
            value = self.health * value
        if parmor > 100:
            parmor = 100
        elif parmor < 0:
            parmor = 0
        damage = round(value * ((100 - float(parmor)) / 100))
        if not isinstance(damage, (int, float)):
            raise ValueError('Dealt Damage returned NaN. This is not supposed to happen.')
        self.health -= damage
        return damage

    def deal_magical_damage(self, value: float, penetration = 0, multiplicative = False):
        marmor = self.mods.get('marmor') - float(penetration)
        if multiplicative:
            value = self.health * value
        if marmor > 100:
            marmor = 100
        elif marmor < 0:
            marmor = 0
        damage = round(value * ((100 - float(marmor)) / 100))
        if not isinstance(damage, (int, float)):
            raise ValueError('Dealt Damage returned NaN. This is not supposed to happen.')
        self.health -= damage
        return damage

    def deal_status_damage(self, value: float, penetration = 0, multiplicative = False):
        if multiplicative:
            value = self.health * value
        self.health -= value
        return value

    def heal(self, value: float, multiplicative = False):
        if multiplicative:
            value = self.health * value
        self.health += value
        if self.health > self.max_health:
            value -= self.health - self.max_health
            self.health = self.max_health
        return value

    def add_level(self, count=1, force=False):
        xpToTake = 0
        levelToAdd = 0
        if not force:
            for _ in range(0, count):
                reqXP = self.get_xp_to_level()
                if self.xp - xpToTake >= reqXP:
                    xpToTake += reqXP
                    levelToAdd += 1

            if levelToAdd == count:
                self.level += levelToAdd
                self.xp -= xpToTake
                return True
            else:
                return False
        else:
            self.level += count
            return True

    def process_per_round(self, round_count=1):
        for _ in range(round_count):
            effect_list = [x for x in self.status_effects.values()]
            for s in effect_list:
                if s.full_effect:
                    for e in s.round_effects:
                        self.process_round_effect(e)
                if s.process_lifespan():
                    self.del_status_effect(s)

    def process_round_effect(self, effect):
        multiplicative = True if effect.effect_type == 1 else False
        if effect.modifier_id == 'health':
            if effect.value > 0:
                self.heal(effect.value, multiplicative)
            else:
                self.deal_status_damage(value=effect.value * -1, multiplicative=multiplicative)

    def add_status_effect(self, status_effect):
        s = self.status_effects.get(status_effect.id)
        if s:
            if s.add_potency(status_effect):
                status_effect.apply_effects(self.mods)
        else:
            self.status_effects[status_effect.id] = status_effect
            if status_effect.full_effect:
                status_effect.apply_effects(self.mods)

    def del_status_effect(self, status_effect):
        if self.status_effects.get(status_effect.id):
            status_effect.remove_effects(self.mods)
            del self.status_effects[status_effect.id]

    def add_mod(self, mod: Modifier):
        if mod.id == 'ac':
            self.total_ac.append(mod.value)
        elif mod.id == 'wc':
            self.total_wc.append(mod.value)
        else:
            self.mods.add(mod)

    def add_equipment_mod(self, mod: Modifier):
        if mod.id == 'ac':
            self.total_ac.append(mod.value)
        elif mod.id == 'wc':
            self.total_wc.append(mod.value)
        else:
            self.equipment_mods.add(mod)

    def add_base_mod(self, mod: Modifier):
        if mod.id == 'ac':
            self.total_ac.append(mod.value)
        elif mod.id == 'wc':
            self.total_wc.append(mod.value)
        else:
            self.base_mods.add(mod)

    def get_damage(self, type='dmg'):
        return self.mainhand.damage.get(type).get_total()

    def calculate(self):
        # Checks Race/Class for attribute changes
        self.strength = int((self.rawStrength + 10) * self.cls.attribute_bonuses[0])
        self.dexterity = int((self.rawDexterity + 10) * self.cls.attribute_bonuses[1])
        self.constitution = int((self.rawConstitution + 10) * self.cls.attribute_bonuses[2])
        self.intelligence = int((self.rawIntelligence + 10) * self.cls.attribute_bonuses[3])
        self.wisdom = int((self.rawWisdom + 10) * self.cls.attribute_bonuses[4])
        self.charisma = int((self.rawCharisma + 10) * self.cls.attribute_bonuses[5])
        self.max_health = 0
        self.total_ac.clear()
        self.total_wc.clear()
        self.mods.clear()
        self.equipment_mods = ModifierDict()
        self.base_mods = ModifierDict()
        self.skills = []

        # TIME FOR EQUIPMENT CALCULATIONS
        for equip in [self.mainhand, self.offhand, self.helmet, self.armor, self.gloves, self.boots, self.trinket]:
            if equip == None:
                equip = Equipment('empty')

            for _, mod in equip.starting_mods.items():
                self.add_equipment_mod(mod)
            for _, mod in equip.random_mods.items():
                self.add_equipment_mod(mod)
            for skill in equip.skills:
                self.skills.append(get_skill(self, skill))
            equip.generate_damage(self)

        self.max_health = int(self.mods.get('max_health'))

        # Strength Related Stats First
        self.inventoryCapacity = (self.strength // PerLevel.inventory_cap + 
            (10 - (10 // PerLevel.inventory_cap)))

        # Dexterity related stats second
        dex = self.dexterity - 10
        if dex <= 40:  # Dexterity below 40
            evasion = Modifier('evasion', float(dex) * PerLevel.evasion)
        elif dex > 40 and dex <= 100:  # Dexterity between 40 and 100
            evasion = Modifier('evasion', (PerLevel.softcap_evasion * (float(dex) - 40.0) + 40.0 * PerLevel.evasion))
        else:  # Dexterity above 100
            evasion = Modifier('evasion', (PerLevel.softcap_evasion * (100.0 - 40.0) + 40.0 * PerLevel.evasion))
        self.add_base_mod(evasion)

        # Constitution related stats third
        self.max_health += PerLevel.health * (self.constitution - 10) + 100

        # Intelligence related stats fourth
        spellAmp = Modifier('spellAmp', (PerLevel.spell_amp * float(self.intelligence - 10)))
        self.add_base_mod(spellAmp)

        # Wisdom related stats fifth
        out_heal_amp = Modifier('healAmp', (PerLevel.out_heal_amp * float(self.wisdom - 10)))
        self.add_base_mod(out_heal_amp)

        # Charisma related stats sixth
        # self.discount = 0

        # Set final values
        for mod in self.raw_mods.values():
            self.add_base_mod(mod)
        for mod in self.base_mods.values():
            self.add_mod(mod)
        for mod in self.equipment_mods.values():
            self.add_mod(mod)

        self.mods.set(Modifier('ac', sum(self.total_ac) / len(self.total_ac)))
        self.mods.set(Modifier('wc', sum(self.total_wc) / len(self.total_wc)))

        # Fill in Skills
        for skill in self.raw_skills:
            s = get_skill(self, skill)
            self.skills.append(s)

        if isinstance(self.race.passive_effect, PassiveEffect):
            self.race.passive_effect.apply_effects(self.mods) #Apply Race Effect

        try:
            if self.max_health < self.health:
                self.health = self.max_health
        except AttributeError:
            self.health = self.max_health

        logger.debug('{0.name} Calculation complete'.format(self))

    def rest(self):  # Reset anything that needs to on rest
        self.health = self.max_health
        try:
            for skill in self.skills:
                skill.cooldown = skill.start_cooldown
        except AttributeError:
            pass

    def increment_cooldowns(self, amount = 1):
        for skill in self.skills:
            if skill.cooldown > 0:
                skill.cooldown -= 1


class Player(Character):
    baseXP = 100
    xpRate = 0.15
    pc = True

    def __eq__(self, value):
        if isinstance(value, (Player, Member, User)):
            return self.id == value.id
        elif isinstance(value, int):
            return self.id == value
        else:
            return NotImplemented

    def __ne__(self, value):
        return not self.__eq__(value)

    def __init__(self, id, load = True):
        super().__init__(id)
        if load:
            self.load()

    def new(self, name: str, clss: CharacterClass, race: Race, rawAttributes: List[int], home_id: int, save: bool = True) -> bool:
        self.name = name
        self.cls = clss
        self.race = race
        self.level = 1
        self.xp = 0
        self.maxHealth = 100
        self.available = True
        # Attributes
        self.rawStrength = rawAttributes[0]
        self.rawDexterity = rawAttributes[1]
        self.rawConstitution = rawAttributes[2]
        self.rawIntelligence = rawAttributes[3]
        self.rawWisdom = rawAttributes[4]
        self.rawCharisma = rawAttributes[5]
        # Skills
        self.raw_skills = ['attack']
        # Equipment
        self.mainhand = Equipment(0)
        self.mainhand.generate_new(1, 0, index=5)
        self.offhand = Equipment('empty')
        self.helmet = Equipment(0)
        self.helmet.generate_new(1, 0, index=1)
        self.armor = Equipment(0)
        self.armor.generate_new(1, 0, index=2)
        self.gloves = Equipment(0)
        self.gloves.generate_new(1, 0, index=3)
        self.boots = Equipment(0)
        self.boots.generate_new(1, 0, index=4)
        self.trinket = Equipment('empty')

        self.inventory = []
        if save:
            with Database() as db:
                db.insert_adventurer(self.id, name, clss.id, race.id, json.dumps(rawAttributes), home_id)
                self.calculate()
                self.rest()
                self.save()
                logger.debug('{}:{} Created Successfully'.format(
                    self.id, self.name))
                return True
        else:
            self.calculate()
            self.rest()
            return False

    def load(self, calculate=True):
        try:
            if self.id in TestData.active_test_players:
                self.id = TestData.active_test_players[self.id]
            with Database() as db:
                raw = db.fetchone(db.get_adventurer(userID=self.id))
            self.name = raw['name']
            self.cls = CharacterClass.get_class(raw['class'])
            self.level = raw['level']
            self.xp = raw['xp']
            self.race = Race.get_race(raw['race'])
            rawAttributes = json.loads(raw['attributes'])  # Get a list of the attributes
            self.rawStrength = int(rawAttributes[0])
            self.rawDexterity = int(rawAttributes[1])
            self.rawConstitution = int(rawAttributes[2])
            self.rawIntelligence = int(rawAttributes[3])
            self.rawWisdom = int(rawAttributes[4])
            self.rawCharisma = int(rawAttributes[5])

            try:
                self.raw_skills = json.loads(raw['skills'])  # Get a list of skills
            except (AttributeError, TypeError):
                self.raw_skills = []

            equipment = json.loads(raw['equipment'])  # Get a list of equipped items
            self.mainhand = Equipment(equipment[0])
            self.offhand = Equipment(equipment[1])
            self.helmet = Equipment(equipment[2])
            self.armor = Equipment(equipment[3])
            self.gloves = Equipment(equipment[4])
            self.boots = Equipment(equipment[5])
            self.trinket = Equipment(equipment[6])

            self.inventory = []
            temp_inventory = json.loads(raw['inventory'])
            try:
                temp_inventory.remove('')
            except:
                pass
            for e in temp_inventory:
                self.inventory.append(Equipment(e))
            self.available = bool(raw['available'])
            self.health = int(raw['health'])

            if calculate:
                self.calculate()
            logger.debug('{}:{} Loaded Successfully'.format(
                self.id, self.name))
            self.loaded = True
        except Exception:
            logger.debug('{} Failed to Load Player'.format(
                self.id), exc_info=True)
        finally:
            return self.loaded

    def save(self):
        rawAttributes = [self.rawStrength, self.rawDexterity, self.rawConstitution, self.rawIntelligence,
                         self.rawWisdom, self.rawCharisma]
        equipment = [self.mainhand, self.offhand,
                        self.helmet, self.armor,
                        self.gloves, self.boots,
                        self.trinket]
        temp_inventory = []
        for e in self.inventory:
            temp_inventory.append(e.save(database=True))

        save = {
            'name': self.name,
            'class': self.cls.id,
            'level': self.level,
            'xp': int(self.xp),
            'race': self.race.id,
            'attributes': dumps(rawAttributes),
            'skills': dumps(self.raw_skills),
            'equipment': dumps(equipment),
            'inventory': dumps(temp_inventory),
            'available': bool(self.available),
            'health': self.health}
        logger.debug('{}:{} Saved Successfully'.format(self.id, self.name))
        with Database() as db:
            db.update_adventurer(self.id, **save)

    def delete(self) -> None:
        """IRREVERSIBLE deletion of an adventurer"""
        for e in [self.mainhand, self.offhand,
                  self.helmet, self.armor,
                  self.gloves, self.boots,
                  self.trinket]:
            e.delete()

        for e in self.inventory:
            e.delete()

        with Database() as db:
            db.delete_adventurer(self.id)
        logger.warning('{}:{} Deleted'.format(self.id, self.name))


class Enemy(Character):
    def __init__(self, raw_data = ''):
        super().__init__(0)
        if raw_data:
            self.load(raw_data)

    def process_attributes_string(self, attributes_string: str):
        attributes_list = attributes_string.split('|')
        final_list = []
        for a in attributes_list:
            base_value, per_level = tuple(a.split('+'))
            final_value = math.floor(float(base_value) + (float(per_level) * self.level))
            final_list.append(final_value)
        self.rawStrength = 0
        self.rawDexterity = 0
        self.rawConstitution = 0
        self.rawIntelligence = 0
        self.rawWisdom = 0
        self.rawCharisma = 0
        try:
            self.rawStrength = final_list[0]
            self.rawDexterity = final_list[1]
            self.rawConstitution = final_list[2]
            self.rawIntelligence = final_list[3]
            self.rawWisdom = final_list[4]
            self.rawCharisma = final_list[5]
        except IndexError:
            pass

    def process_mod_string(self, mod_string: str):
        mods = {}
        mod_string_list = mod_string.split('|')
        try:
            for mod in mod_string_list:
                key, value = tuple(mod.split(':'))
                base_value, per_level = tuple(value.split('+'))
                mods[key] = Modifier(key, math.floor(float(base_value) + (float(per_level) * self.level)))
            return mods
        except ValueError as e:
            raise InvalidModString('Invalid Mod String: `{}` {}'.format(mod_string, e))

    def generate_new(self, lvl: int, rng = True, index = 0, max_combat_rank = 1, calculate = True):
        with Database() as db:
            if index == 0:
                data_pool = db.get_base_enemy_lvl(lvl, rng=rng, combatRank=max_combat_rank)
                data = random.choice(data_pool)
            else:
                data = db.get_base_enemy(indx = index)
                data = db.fetchone(data)

        self.id = int(data['indx'])
        self.name = str(data['name'])
        self.minLevel = int(data['minLevel'])
        self.maxLevel = int(data['maxLevel'])
        self.potential_elites = data['elite']
        attributes_string = data['attributes']
        modifiers_string = data['modifiers']
        self.raw_skills = json.loads(data['skills'])
        self.combat_rank = float(data['combatRank'])
        self.level = lvl
        self.process_attributes_string(attributes_string)
        self.raw_mods = self.process_mod_string(modifiers_string)
        if calculate:
            self.calculate()

    def generate_new_elite(self, lvl: int, rng = True, index = 0, max_combat_rank = 1, calculate = True):
        self.generate_new(lvl, rng=rng, index=index, max_combat_rank=max_combat_rank, calculate=False)
        elite = random.choice(self.potential_elites)
        try:
            elite = int(elite)
        except ValueError:
            pass
        self.elite = EliteModifier(elite)
        self.raw_skills += self.elite.skills
        if self.elite.title:
            if self.elite.title[0] == ' ':
                self.name = '{}{}'.format(self.name, self.elite.title)
            else:
                self.name = '{}{}'.format(self.elite.title, self.name)
        length = len(self.elite.attributes)
        for indx, attribute in enumerate([self.rawStrength, self.rawDexterity, self.rawConstitution, self.rawIntelligence, self.rawWisdom, self.rawCharisma]):
            if indx + 1 <= length:
                attribute *= self.elite.attributes[indx]

        for mod in self.elite.modifiers.values():
            if self.raw_mods.get(mod.id, False):
                tmp = self.raw_mods.get(mod.id).value * mod.value
                self.raw_mods.get(mod.id).value = int(tmp)

        for skill in self.elite.skills:
            self.raw_skills.append(skill)
        if calculate:
            self.calculate()

    def calculate(self):
        race = Race()
        race.id = 'enemy'
        race.name = 'Enemy'
        race.description = 'You should not see this'
        race.passive_effect = 'Nothing'
        clss = CharacterClass()
        clss.id = 'enemy'
        clss.name = 'Enemy'
        clss.description = 'You should not see this'
        clss.attribute_bonuses = [1, 1, 1, 1, 1, 1]

        self.health = 0
        self.mainhand = Equipment('empty')
        self.offhand = Equipment('empty')
        self.helmet = Equipment('empty')
        self.armor = Equipment('empty')
        self.gloves = Equipment('empty')
        self.boots = Equipment('empty')
        self.trinket = Equipment('empty')
        self.race = race
        self.cls = clss
        super().calculate()
        self.max_health -= 100
        self.rest()

    def load(self, raw_data, calculate=True):
        try:
            data = raw_data.split('|')
            self.id = int(data[0])
            self.name = data[1]
            self.level = int(data[2])

            rawAttributes = data[3].split(';')  # Get a list of the attributes
            self.rawStrength = int(rawAttributes[0])
            self.rawDexterity = int(rawAttributes[1])
            self.rawConstitution = int(rawAttributes[2])
            self.rawIntelligence = int(rawAttributes[3])
            self.rawWisdom = int(rawAttributes[4])
            self.rawCharisma = int(rawAttributes[5])

            self.raw_skills = data[5].split(';')  # Get a list of skills

            raw_mods = data[4].split(';')
            self.raw_mods.clear()
            for mod_string in raw_mods:
                key, value = tuple(mod_string.split(':'))
                self.raw_mods[key] = Modifier(key, int(value))

            if calculate:
                self.calculate()
            
            logger.debug('{}:{} Loaded Successfully'.format(
                self.id, self.name))
            self.loaded = True
        except Exception:
            logger.error('{} Failed to Load Enemy'.format(
                self.id), exc_info=True)
        finally:
            return self.loaded

    def serialize(self):
        return self.save()

    def save(self):
        rawAttributes = [self.rawStrength, self.rawDexterity, self.rawConstitution,
                         self.rawIntelligence, self.rawWisdom, self.rawCharisma]
        rawAttributes = ';'.join(str(e) for e in rawAttributes)
        skills = ';'.join(self.raw_skills)
        tmp_mods = []
        for mod in self.raw_mods.values():
            tmp_mods.append('{}:{}'.format(mod.id, mod.value))
        mods = ';'.join(tmp_mods)

        save = '|'.join([str(self.id), self.name, str(self.level), rawAttributes, mods, skills])
        logger.debug('{}:{} Saved Successfully'.format(self.id, self.name))
        return save


# class RaidBoss(Character):
#     def __init__(self, boss_id):
#         super().__init__(boss_id)
#         if self.id > 0:
#             self.load()

#     def load(self):
#         try:
#             data = db.get_raid_boss(self.id)
#             self.name = data[1]
#             self.level = data[2]
#             self.flavor = data[3]
#             race = Race()
#             race.id = 'enemy'
#             race.name = 'Enemy'
#             race.description = 'You should not see this'
#             race.passive_effect = 'Nothing'
#             clss = CharacterClass()
#             clss.id = 'enemy'
#             clss.name = 'Enemy'
#             clss.description = 'You should not see this'
#             clss.attribute_bonuses = [1, 1, 1, 1, 1, 1]
#             self.cls = clss
#             self.race = race
            
#             raw_attributes = data[4].split('|')  # Get a list of the attributes
#             self.rawStrength = int(raw_attributes[0])
#             self.rawDexterity = int(raw_attributes[1])
#             self.rawConstitution = int(raw_attributes[2])
#             self.rawIntelligence = int(raw_attributes[3])
#             self.rawWisdom = int(raw_attributes[4])
#             self.rawCharisma = int(raw_attributes[5])

#             self.raw_skills = data[5].split(',')

#             self.inventory = []
#             for L in data[7].split(','):
#                 try:
#                     self.inventory.append(int(L))
#                 except (AttributeError, ValueError):
#                     logger.error('{} can not be converted to int in {} RaidBoss generation'.format(L, self.id), exc_info=True)

#             self.mainhand = None
#             self.offhand = None
#             self.helmet = None
#             self.armor = None
#             self.gloves = None
#             self.boots = None
#             self.trinket = None

#             for mod_string in data[8].split('|'):
#                 mod_tmp = mod_string.split(':')
#                 mod = Modifier(mod_tmp[0], int(mod_tmp[1]))
#                 self.raw_mods[mod.id] = mod

#             self.calculate()
#             self.maxHealth = int(data[6])
#             self.health = self.maxHealth
#             self.loaded = True
#             return True
#         except Exception:
#             logger.error('{} Failed to Load Raid Boss'.format(
#                 self.id), exc_info=True)
#             return False


# test_players = []
# for i in range(1, 11):
#     adv = Player(i)
#     if not adv.loaded:
#         adv = None
#     test_players.append(adv)
