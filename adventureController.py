import discord
import logging
import random
import math
import numpy as np
import datetime
import asyncio

from discord.ext import commands
import tools.skills as Skills
import tools.database as db
from tools.colour import Colour

logger = logging.getLogger('adventureController')
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

db.initDB()


class PerLevel:
    unarm_damage = 1.5  # Flat increase
    inventory_cap = 5  # Amount of strength to gain one inventory slot
    evasion = 0.004  # Evasion Chance
    softcap_evasion = 0.0023  # Evasion Chance after soft cap
    crit_chance = 0.0025
    softcap_crit_chance = 0.0016
    health = 10
    spell_amp = 0.01


class Character:
    baseXP = 25
    xpRate = 0.035
    pc = False

    def __init__(self, ID, load = True):
        self.id = ID
        self.name = 'Unloaded'
        self.loaded = False
        if load:
            self.load()

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
        self.mainhand = Equipment(1)
        self.offhand = Equipment(1)
        self.helmet = Equipment(1)
        self.armor = Equipment(1)
        self.gloves = Equipment(1)
        self.boots = Equipment(1)
        self.trinket = Equipment(1)

        self.inventory = []
        self.loaded = True

    def load(self):
        pass

    def equip(self, e: int):
        try:
            eq = Equipment(self.inventory[e-1])
            self.remInv(e)
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

            if not uneq.mods.get('empty', False):
                self.inventory.append(uneq.id)
            self.calculate()
            return True
        except IndexError:
            return False

    def unequip(self, slot: str):
        eq = Equipment(1)
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

        if not uneq.mods.get('empty', False):
            self.inventory.append(uneq.id)
        self.calculate()

    def addInv(self, id: int):
        try:
            if len(self.inventory) < self.inventoryCapacity:
                self.inventory.append(id)
                logger.debug('Adding {} to Inventory'.format(id))
                return True
            else:
                return False
        except AttributeError:
            self.calculate()
            return self.addInv(id)

    def remInv(self, e: int):
        try:
            self.inventory.pop(e-1)
            return True
        except ValueError:
            return False

    def addXP(self, count: int):
        self.xp += count
        return True

    def remXP(self, count: int, force=False):
        if self.xp - count >= 0:
            self.xp -= count
            return True
        else:
            if force:
                self.xp = 0
                return True
            else:
                return False

    def getXPToLevel(self):
        if self.level < 5:
            reqXP = self.baseXP * math.exp(self.xpRate * (self.level - 1))
        else:
            reqXP = 999999999
        return int(reqXP)

    def get_unspent_points(self):
        total_points = (self.rawStrength
                        + self.rawDexterity
                        + self.rawConstitution
                        + self.rawIntelligence
                        + self.rawWisdom
                        + self.rawCharisma)
        unspent_points = (self.level - 1) - (total_points - 65)
        return unspent_points

    def get_skill(self, skill_name: str):
        try:
            for skill in self.skills:
                if skill.name.lower() == skill_name.lower():
                    return skill
            return None
        except AttributeError:
            return None

    def roll_initiative(self):
        return random.randint(1, 20) + self.level

    def addLevel(self, count=1, force=False):
        xpToTake = 0
        levelToAdd = 0
        if not force:
            for _ in range(0, count):
                reqXP = self.getXPToLevel()
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
    
    def calculate(self):
        # Checks Race/Class for attribute changes
        self.strength = self.rawStrength
        self.dexterity = self.rawDexterity
        self.constitution = self.rawConstitution
        self.intelligence = self.rawIntelligence
        self.wisdom = self.rawWisdom
        self.charisma = self.rawCharisma
        self.maxHealth = 0
        self.wc = 3
        self.ac = 4
        self.dmg = 0
        self.strdmg = 0
        self.dexdmg = 0

        # TIME FOR EQUIPMENT CALCULATIONS
        for equip in [self.mainhand, self.offhand, self.helmet, self.armor, self.gloves, self.boots, self.trinket]:
            if equip == None:
                equip = Equipment(1)
            self.wc += int(equip.mods.get('wc', 0))
            self.ac += int(equip.mods.get('ac', 0))
            self.maxHealth += int(equip.mods.get('health', 0))

            self.strength += int(equip.mods.get('strength', 0))
            self.dexterity += int(equip.mods.get('dexterity', 0))
            self.constitution += int(equip.mods.get('constitution', 0))
            self.intelligence += int(equip.mods.get('intelligence', 0))
            self.wisdom += int(equip.mods.get('wisdom', 0))
            self.charisma += int(equip.mods.get('charisma', 0))

            self.dmg += int(equip.mods.get('dmg', 0))
            self.strdmg += int(equip.mods.get('strdmg', 0))
            self.dexdmg += int(equip.mods.get('dexdmg', 0))

        # Strength Related Stats First
        self.unarmDamage = float(self.strength) * PerLevel.unarm_damage
        logger.debug(
            '{0.name} Unarmed Damage calculated to: {0.unarmDamage}'.format(self))

        self.inventoryCapacity = self.strength // PerLevel.inventory_cap + \
            (10 - (10 // PerLevel.inventory_cap))
        logger.debug(
            '{0.name} Inventory Capacity calculated to: {0.inventoryCapacity}'.format(self))

        # Dexterity related stats second
        if self.dexterity <= 40:  # Dexterity below 40
            self.evasion = float(self.dexterity) * PerLevel.evasion
            self.critChance = float(self.dexterity) * PerLevel.evasion

        elif self.dexterity > 40 and self.dexterity <= 100:  # Dexterity between 40 and 100
            self.evasion = PerLevel.softcap_evasion * \
                (float(self.dexterity) - 40.0) + 40.0 * PerLevel.evasion
            self.critChance = PerLevel.softcap_crit_chance * \
                (float(self.dexterity) - 40.0) + 40.0 * PerLevel.crit_chance

        else:  # Dexterity above 100
            self.evasion = PerLevel.softcap_evasion * \
                (100.0 - 40.0) + 40.0 * PerLevel.evasion
            self.critChance = PerLevel.softcap_crit_chance * \
                (100.0 - 40.0) + 40.0 * PerLevel.crit_chance

        logger.debug(
            '{0.name} Evasion calculated to: {0.evasion}'.format(self))
        logger.debug(
            '{0.name} Crit Chance calculated to: {0.critChance}'.format(self))

        # Constitution related stats third
        self.maxHealth += PerLevel.health * self.constitution + 100
        logger.debug(
            '{0.name} Max health calculated to: {0.maxHealth}'.format(self))

        # Intelligence related stats fourth
        self.spellAmp = PerLevel.spell_amp * float(self.intelligence)
        logger.debug(
            '{0.name} Spell Amp calculated to: {0.spellAmp}'.format(self))

        # Wisdom related stats fifth
        self.secretChance = 0

        # Charisma related stats sixth
        self.discount = 0

        # Fill in Skills
        self.skills = []
        for skill in self.raw_skills:
            s = Skills.Skill.get_skill(skill)
            if s:
                self.skills.append(s())

        # Set values to their maximum
        self.dmg += self.strdmg * self.strength + self.dexdmg * self.dexterity
        if self.dmg == 0:
            self.dmg = self.unarmDamage

        if self.maxHealth < self.health:
            self.health = self.maxHealth

        logger.debug('{0.name} Calculation complete'.format(self))

    def rest(self):  # Reset anything that needs to on rest
        self.health = self.maxHealth

    def increment_cooldowns(self, amount = 1):
        for skill in self.skills:
            if skill.cooldown > 0:
                skill.cooldown -= 1


class Player(Character):
    baseXP = 100
    xpRate = 0.1
    pc = True

    def __eq__(self, value):
        if isinstance(value, Player):
            return self.id == value.id
        elif isinstance(value, int):
            return self.id == value
        else:
            return NotImplemented

    def __ne__(self, value):
        return not self.__eq__(value)

    def new(self, name, cls, race, rawAttributes):
        self.name = name
        self.cls = cls
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
        self.mainhand = Equipment(1)
        self.offhand = Equipment(1)
        self.helmet = Equipment(1)
        self.armor = Equipment(1)
        self.gloves = Equipment(1)
        self.boots = Equipment(1)
        self.trinket = Equipment(1)

        self.inventory = []
        if db.addAdventurer(self.id, name, cls, race, ','.join(str(e) for e in rawAttributes)):
            self.rest()
            self.calculate()
            self.rest()
            self.save()
            logger.info('{}:{} Created Successfully'.format(
                self.id, self.name))
            return True
        else:
            return False

    def delete(self):
        db.deleteAdventurer(self.id)
        logger.warning('{}:{} Deleted'.format(self.id, self.name))

    def load(self, calculate=True):
        try:
            raw = db.getAdventurer(self.id)
            self.name = raw[2]
            self.cls = raw[3]
            self.level = raw[4]
            self.xp = raw[5]
            self.race = raw[6]

            rawAttributes = raw[7].split(',')  # Get a list of the attributes
            self.rawStrength = int(rawAttributes[0])
            self.rawDexterity = int(rawAttributes[1])
            self.rawConstitution = int(rawAttributes[2])
            self.rawIntelligence = int(rawAttributes[3])
            self.rawWisdom = int(rawAttributes[4])
            self.rawCharisma = int(rawAttributes[5])

            try:
                self.raw_skills = raw[8].split(',')  # Get a list of skills
            except AttributeError:
                self.raw_skills = []

            equipment = raw[9].split(',')  # Get a list of equipped items
            self.mainhand = Equipment(equipment[0])
            self.offhand = Equipment(equipment[1])
            self.helmet = Equipment(equipment[2])
            self.armor = Equipment(equipment[3])
            self.gloves = Equipment(equipment[4])
            self.boots = Equipment(equipment[5])
            self.trinket = Equipment(equipment[6])

            self.inventory = raw[10].split(',')
            try:
                self.inventory.remove('')
            except:
                pass
            self.available = bool(raw[11])
            self.health = int(raw[12])

            if calculate:
                self.calculate()
            logger.debug('{}:{} Loaded Successfully'.format(
                self.id, self.name))
            self.loaded = True
        except Exception:
            logger.error('{} Failed to Load Player'.format(
                self.id), exc_info=True)
        finally:
            return self.loaded

    def save(self):
        rawAttributes = [self.rawStrength, self.rawDexterity, self.rawConstitution, self.rawIntelligence,
                         self.rawWisdom, self.rawCharisma]  # Bundles Attributes into a string to be stored
        rawAttributes = ','.join(str(e) for e in rawAttributes)
        # Does the same for skills, though skills aren't currently used
        skills = ','.join(self.raw_skills)
        equipment = ','.join(str(e) for e in [self.mainhand.id, self.offhand.id,
                                              self.helmet.id, self.armor.id, self.gloves.id, self.boots.id, self.trinket.id])
        inventory = ','.join(str(e) for e in self.inventory)

        save = [self.id, self.name, self.cls, self.level, int(
            self.xp), self.race, rawAttributes, skills, equipment, inventory, int(self.available), self.health]
        logger.debug('{}:{} Saved Successfully'.format(self.id, self.name))
        return db.saveAdventurer(save)


class Enemy(Character):
    def new(self, name, cls, race, rawAttributes, skills, rng):
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
        self.mainhand = Equipment(1)
        self.offhand = Equipment(1)
        self.helmet = Equipment(1)
        self.armor = Equipment(1)
        self.gloves = Equipment(1)
        self.boots = Equipment(1)
        self.trinket = Equipment(1)

        self.inventory = []
        self.id = db.addEnemy(name, cls, race, ','.join(
            str(e) for e in rawAttributes), ','.join(str(e) for e in skills), int(rng))
        logger.info('{}:{} Created Successfully'.format(self.id, self.name))

    def delete(self):
        db.deleteEnemy(self.id)
        logger.warning('{}:{} Deleted'.format(self.id, self.name))

    def calculate(self):
        self.health = 0
        Character.calculate(self)
        self.rest()

    def load(self, calculate=True):
        try:
            raw = db.getEnemy(self.id)
            self.name = raw[1]
            self.cls = raw[2]
            self.level = raw[3]
            self.xp = raw[4]
            self.race = raw[5]

            rawAttributes = raw[6].split(',')  # Get a list of the attributes
            self.rawStrength = int(rawAttributes[0])
            self.rawDexterity = int(rawAttributes[1])
            self.rawConstitution = int(rawAttributes[2])
            self.rawIntelligence = int(rawAttributes[3])
            self.rawWisdom = int(rawAttributes[4])
            self.rawCharisma = int(rawAttributes[5])

            self.raw_skills = raw[7].split(',')  # Get a list of skills

            equipment = raw[8].split(',')  # Get a list of equipped items
            self.mainhand = Equipment(equipment[0])
            self.offhand = Equipment(equipment[1])
            self.helmet = Equipment(equipment[2])
            self.armor = Equipment(equipment[3])
            self.gloves = Equipment(equipment[4])
            self.boots = Equipment(equipment[5])
            self.trinket = Equipment(equipment[6])

            self.inventory = raw[9].split(',')
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

    def save(self):
        rawAttributes = [self.rawStrength, self.rawDexterity, self.rawConstitution,
                         self.rawIntelligence, self.rawWisdom, self.rawCharisma]
        rawAttributes = ','.join(str(e) for e in rawAttributes)
        skills = ','.join(self.raw_skills)
        equipment = ','.join(str(e) for e in [self.mainhand.id, self.offhand.id,
                                              self.helmet.id, self.armor.id, self.gloves.id, self.boots.id, self.trinket.id])
        inventory = ','.join(self.inventory)

        save = [self.id, self.name, self.cls, self.level, self.xp,
                self.race, rawAttributes, skills, equipment, inventory]
        logger.debug('{}:{} Saved Successfully'.format(self.id, self.name))
        return db.saveEnemy(save)


class RaidBoss(Character):
    def __init__(self, boss_id):
        self.id = boss_id
        self.loaded = False
        if self.id > 0:
            self.load()

    def get_loot(self, rarity: int):
        loot = []
        for L in self.inventory:
            if L.rarity == rarity:
                loot.append(L)
        if len(loot) > 0:
            return random.choice(loot)

    def load(self):
        try:
            data = db.get_raid_boss(self.id)
            self.name = data[1]
            self.level = data[2]
            self.flavor = data[3]
            
            raw_attributes = data[4].split(',')  # Get a list of the attributes
            self.rawStrength = int(raw_attributes[0])
            self.rawDexterity = int(raw_attributes[1])
            self.rawConstitution = int(raw_attributes[2])
            self.rawIntelligence = int(raw_attributes[3])
            self.rawWisdom = int(raw_attributes[4])
            self.rawCharisma = int(raw_attributes[5])

            self.raw_skills = data[5].split(',')
            self.maxHealth = int(data[6])
            self.health = self.maxHealth

            self.inventory = []
            for L in data[7].split(','):
                self.inventory.append(Equipment(L))

            self.mainhand = None
            self.offhand = None
            self.helmet = None
            self.armor = None
            self.gloves = None
            self.boots = None
            self.trinket = Equipment(0)
            self.trinket.new('RaidBossModifierTrinket', 'Not much', 4, data[8], 'trinket', 0, save=False)

            self.calculate()
            self.loaded = True
            return True
        except Exception:
            logger.error('{} Failed to Load Raid Boss'.format(
                self.id), exc_info=True)
            return False


class Modifier:
    def __eq__(self, other):
        if isinstance(other, Modifier):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, Modifier):
            return self.value < other.value
        elif isinstance(other, int):
            return self.value < other
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, Modifier):
            return self.value <= other.value
        elif isinstance(other, int):
            return self.value <= other
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Modifier):
            return self.value > other.value
        elif isinstance(other, int):
            return self.value > other
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Modifier):
            return self.value >= other.value
        elif isinstance(other, int):
            return self.value >= other
        else:
            return NotImplemented

    def __init__(self, ID: str, value: int):
        self.id = ID
        self.value = value
        self.load()
    
    def load(self):
        data = db.get_modifier(self.id)
        if data:
            if data[2]:
                self.display_name = data[2]
            else:
                self.display_name = self.id
            if data[3]:
                self.title = data[3]
            else:
                self.title = None
        else:
            self.display_name = self.id
            self.title = None


class BaseEquipment:
    def __init__(self, ID = 0):
        self.id = ID
        if self.id != 0:
            self.load(self.id)

    def load(self, ID):
        if isinstance(ID, int):
            data = db.get_base_equipment(ID)
        else:
            data = ID
        self.id = str(data[0])
        self.name = str(data[1])
        self.flavor = str(data[2])
        self.slot = str(data[3])
        self.min_level = int(data[4])
        self.max_level = int(data[5])
        self.starting_rarity = int(data[6])
        self.starting_mod_string = str(data[7])
        self.random_mod_string = str(data[8])
        self.requirement_string = str(data[9])
        self.rng = bool(data[10])

    def new(self, lvl: int, RNG = True):
        if RNG:
            data = db.get_base_equipment_lvl_rng(lvl)
        else:
            data = db.get_base_equipment_lvl(lvl)
        chosen_data = random.choice(data)
        self.load(chosen_data)
        

class Equipment:
    def __init__(self, id):
        self.id = id
        if id == 0:
            pass
        else:  # Search for equipment in the database
            self.load()

    @staticmethod
    def calculate_drop_rarity():
        result = 0
        if random.random() <= 0.05:
            result = 4
        elif random.random() <= 0.10:
            result = 3
        elif random.random() <= 0.25:
            result = 2
        elif random.random() <= 0.40:
            result = 1

        return result
            

    @staticmethod
    def calculateWeight(loot: list):
        weight = []
        tmp = []
        total = 0
        for l in loot:
            e = Equipment(l)
            r = e.rarity

            if r == 0:
                r = 5
            elif r == 1:
                r = 4
            elif r == 2:
                r = 3
            elif r == 3:
                r = 2
            elif r == 4:
                r = 1

            tmp.append(r)
        for l in tmp:
            total += l
        for l in tmp:
            weight.append(l / total)
        return weight

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

    def getInfo(self):
        if self.name == 'Empty':
            info = '{}'.format(self.name)
        else:
            info = '***{}*\n{}**\n{}\n\nLv: **{}**\nID: **{}**\nPrice: **{}**\n'.format(
                self.getRarity(), self.name, self.flavor, self.level, self.id, self.price)
            for key, mod in self.mods.items():
                info += str(key).upper() + ': **' + str(mod) + '**\n'
        return info

    def process_mod_string(self, mod_string: str): # May be moved to Equipment
        mods = {}
        mod_string_list = mod_string.split('|')
        for mod in mod_string_list:
            key, value_string = tuple(mod.split(':'))
            min_string, max_string = tuple(value_string.split('/'))
            min_value, min_per_level = tuple(min_string.split('+'))
            max_value, max_per_level = tuple(max_string.split('+'))
            final_min_volume = int(min_value) + math.floor(float(min_per_level) * self.level)
            final_max_volume = int(max_value) + math.floor(float(max_per_level) * self.level)
            final_mod = Modifier(key, random.randint(final_min_volume, final_max_volume))
            if mods.get(key, False): # Determine if this modifier is already in the dictionary
                final_mod.value += mods.get(key).value
            mods[key] = final_mod
        return mods

    def process_requirement_string(self, requirement_string: str):
        requirements = {}
        requirement_string_list = requirement_string.split('|')
        for requirement in requirement_string_list:
            key, value_string = tuple(requirement.split(':'))
            value, per_level = tuple(value_string.split('+'))
            final_value = int(value) + math.floor(float(per_level) * self.level)
            final_requirement = Modifier(key, final_value)
            requirements[key] = final_requirement
        return requirements

    def generate_new_rng(self, lvl: int, rarity: int):
        self.base_equipment = BaseEquipment()
        self.base_equipment.new(lvl)

        self.name = self.base_equipment.name
        self.level = lvl
        self.flavor = self.base_equipment.flavor
        if rarity < self.base_equipment.starting_rarity:
            self.rarity = self.base_equipment.starting_rarity
        else:
            self.rarity = rarity
        self.slot = self.base_equipment.slot
        self.mods = self.process_mod_string(self.base_equipment.starting_mod_string)

        if self.rarity > 0 and self.base_equipment.random_mod_string: # Determine if new mods are needed
            potential_mods = self.process_mod_string(self.base_equipment.random_mod_string)
            new_mods = random.sample(potential_mods, self.rarity) # Grab an amount based on rarity
            for mod in new_mods: # Add new mods
                if self.mods.get(mod.id, False):
                    self.mods[mod.id].value += mod.value
                else:
                    self.mods[mod.id] = mod

            highest_mod = next(sorted(new_mods, reverse=True)) # Set title
            if highest_mod.title:
                self.name += ' {}'.format(highest_mod.title)

        if self.base_equipment.requirement_string:
            self.requirements = self.process_requirement_string(self.base_equipment.requirement_string)
        else:
            self.requirements = {}
        self.calculate_price()
        return True

    def load(self):
        try:
            raw = db.getEquipment(self.id)
            self.loaded = True
            self.name = raw[1]
            self.level = raw[2]
            self.flavor = raw[3]
            self.rarity = raw[4]
            self.slot = raw[6]
            self.price = raw[7]
            rawMod = raw[5].split(',')
            mods = []
            for mod in rawMod:
                mods.append(tuple(mod.split(':')))
            self.mods = dict(mods)
            logger.debug('{}:{} Loaded Successfully'.format(
                self.id, self.name))

            self.loaded = True
            return True
        except Exception:
            logger.error('{} Failed to Load'.format(
                self.id), exc_info=True)

            self.loaded = False
            return False

    def save(self):
        rawMod = []
        for mod in self.mods:
            rawMod.append('{}:{}'.format(mod, self.mods[mod]))

        save = [self.id, self.name, self.flavor, self.rarity,
                ','.join(rawMod), self.slot, self.price]
        return db.saveEquipment(save)

    def new(self, name, flavor, rarity: int, mods, slot, price, save=True):
        self.name = name
        self.flavor = flavor
        self.rarity = rarity
        self.slot = slot
        self.price = price
        rawMod = []
        for mod in mods.split(','):
            rawMod.append(tuple(mod.split(':')))
        self.mods = dict(rawMod)
        if (save):
            self.id = self.save()
        logger.info('{}:{} Created Successfully'.format(self.id, self.name))

    def delete(self):
        db.deleteEquipment(self.id)
        logger.warning('{}:{} Deleted'.format(self.id, self.name))


class Encounter:
    def __init__(self, players: list, enemies: list, pve=True):
        self.players = players
        self.enemies = enemies
        self.deadPlayers = []
        self.deadEnemies = []
        self.turn_order = []
        self.winner = 0
        for L in [self.players, self.enemies]:
            for c in L:
                self.turn_order.append(c)
        self.turn_order.sort(key=lambda character: character.roll_initiative())
        self.current_turn = 0

    def get_status(self, embed: discord.Embed):
        active_player = self.turn_order[self.current_turn]
        if active_player.pc:
            available_skills = 'Available Actions\n'
            for skill in active_player.skills:
                available_skills += '`{}` **Cooldown: {}**\n'.format(
                    skill.name, skill.cooldown if skill.cooldown > 0 else 'Ready')
        else:
            available_skills = 'Information Unknown'
        embed.add_field(name='Current Turn: {}'.format(active_player.name),
                        value=available_skills)

        enemy_string = ''
        for enemy in self.enemies:
            if enemy not in self.deadEnemies:
                enemy_string += '{}. Level **{}** {}\n'.format(
                    self.enemies.index(enemy) + 1, enemy.level, enemy.name)
            else:
                enemy_string += '~~{}. Level **{}** {}~~\n'.format(
                    self.enemies.index(enemy) + 1, enemy.level, enemy.name)

        player_string = ''
        for player in self.players:
            if player not in self.deadPlayers:
                player_string += '{}. Level **{}** {}\n'.format(
                    self.players.index(player) + 1, player.level, player.name)
            else:
                player_string += '~~{}. Level **{}** {}~~\n'.format(
                    self.players.index(player) + 1, player.level, player.name)

        turn_order_string = ''
        for character in self.turn_order:
            if character not in self.deadPlayers and character not in self.deadEnemies:
                turn_order_string += 'Level **{}** {}\n'.format(
                    character.level, character.name)
            else:
                turn_order_string += '~~Level **{}** {}~~\n'.format(
                    character.level, character.name)

        embed.add_field(name='Player List', value=player_string)
        embed.add_field(name='Enemy List', value=enemy_string)
        embed.add_field(name='Turn Order', value=turn_order_string)

    def use_skill(self, user, skill_id: str, target_int: int):
        skill = user.get_skill(skill_id)

        if user in self.players:
            friendly_team = self.players
            enemy_team = self.enemies
        else:
            friendly_team = self.enemies
            enemy_team = self.players

        result = False
        if skill:
            if skill.targetable == 0:
                target_group = self.players
                target = user
            elif skill.targetable == 1:
                target_group = friendly_team
                target = target_group[target_int - 1]
            else:
                target_group = enemy_team
                target = target_group[target_int - 1]

            info, result = skill.use(user, target, target_group)
        else:
            info = '`{}` not found in your skills.'.format(skill_id)
        return info, result
                

    def next_turn(self):
        check = self.turn_order[self.current_turn]
        if check.health <= 0:
            if check in self.players:
                self.deadPlayers.append(check)
            elif check in self.enemies:
                self.deadEnemies.append(check)

        if len(self.players) <= len(self.deadPlayers):
            print('Enemy wins')
            self.winner = 2
            return True
        elif len(self.enemies) <= len(self.deadEnemies):
            print('Player wins')
            self.winner = 1
            return True

        if self.current_turn + 1 < len(self.turn_order):
            self.current_turn += 1
        else:
            self.current_turn = 0
        check = self.turn_order[self.current_turn]

        if check.health <= 0:
            if check in self.players:
                    self.deadPlayers.append(check)
            elif check in self.enemies:
                self.deadEnemies.append(check)

        if check in self.deadEnemies or check in self.deadPlayers:
            return self.next_turn()
        else:
            check.increment_cooldowns()
        return False


    def automatic_turn(self):
        for player in self.players:
            if self.enemies[-1:]:
                logger.debug('Living Enemy detected')
                skill = Skills.Skill.get_skill('attack')
                skill().use(player, self.enemies[-1], self.enemies)

                # If the enemy is dead, remove him from active enemies
                if self.enemies[-1].health <= 0:
                    self.deadEnemies.append(self.enemies[-1])
                    self.enemies.pop()

        for enemy in self.enemies:
            if self.players[-1:]:
                logger.debug('Living Player detected')
                skill = Skills.Skill.get_skill('attack')
                skill().use(enemy, self.players[-1], self.players)

                # If the player is dead, remove him from active players
                if self.players[-1].health <= 0:
                    self.deadPlayers.append(self.players[-1])
                    self.players.pop()

    async def run_combat(self, bot, encounter_message: discord.Message):
        escape = False
        combat_log = ''
        while escape == False:
            if combat_log != '':
                tmp = combat_log.split('\n')
                if len(tmp) > 6:
                    tmp.pop(0)
                    combat_log = '\n'.join(tmp)

            active_turn = self.turn_order[self.current_turn]
            combat_embed = discord.Embed(title='Combat', colour=Colour.combatColour, description=combat_log)
            combat_embed.set_footer(text='You have 60 seconds to do your turn, otherwise your turn will be skipped.')
            self.get_status(combat_embed)
            await encounter_message.edit(embed=combat_embed)
            if active_turn.pc:
                try:
                    vMessage = await bot.wait_for('message', timeout=60.0, check=lambda message: message.channel.id == encounter_message.channel.id and message.author.id == active_turn.id)
                except asyncio.TimeoutError:
                    self.next_turn()
                else:
                    content = vMessage.content.split(' ')
                    try:
                        info, result = self.use_skill(active_turn, content[0].lower(), int(content[1]))
                    except IndexError:
                        result = False
                        info = 'Invalid Target'
                    except ValueError:
                        result = False
                        info = 'Target must be an integer'
                    combat_log += info + '\n'
                    if result:
                        escape = self.next_turn()
                finally:
                    try:
                        await vMessage.delete()
                    except discord.NotFound:
                        logger.debug('No message to delete')
            else:
                await asyncio.sleep(2)
                if active_turn in self.players:
                    friendly_team = self.players
                    enemy_team = self.enemies
                else:
                    friendly_team = self.enemies
                    enemy_team = self.players
                for skill in active_turn.skills:
                    if skill.cooldown <= 0:
                        if skill.targetable == 0:
                            info, result = self.use_skill(active_turn, skill.name, 0) #Target int doesn't matter for self cast
                        elif skill.targetable == 1:
                            info, result = self.use_skill(active_turn, skill.name, random.randint(1, len(friendly_team)))
                        else:
                            info, result = self.use_skill(active_turn, skill.name, random.randint(1, len(enemy_team)))
                        break
                combat_log += info + '\n'
                escape = self.next_turn()

        embed = discord.Embed(title='Combat Over', colour=Colour.combatColour)
        survivors_string = ''
        for player in self.players:
            if player not in self.deadPlayers:
                survivors_string += '{}\n'.format(player.name)
        embed.add_field(name='Survivors', value=survivors_string if survivors_string != '' else 'No one')
        embed.add_field(name='Combat Log', value=combat_log)
        await encounter_message.edit(embed=embed)
        await asyncio.sleep(5)
        return self.winner

    def getLoot(self):
        rawLoot = []
        for enemy in self.deadEnemies:
            for loot in enemy.inventory:
                if loot:
                    rawLoot.append(loot)
        return rawLoot

    def getExp(self):
        totalXP = 0
        for e in self.deadEnemies:
            totalXP += e.baseXP * math.exp(e.xpRate * e.level)
        return totalXP

    def end(self):
        if len(self.players) > 0 and len(self.enemies) :
            return True
        else:
            return False


class RNGDungeon:
    stageTime = 10  # Time it takes for each stage, in seconds

    def __init__(self, dID=0):
        self.id = dID
        self.combat_log = []

    def new(self, aID: int, difficulty: str):
        self.adv = Player(aID)
        self.adv.available = False
        self.adv.save()
        self.stage = 1
        self.active = True
        self.xp = 0
        self.calculateTime(RNGDungeon.stageTime)

        if difficulty == 'easy':
            self.stages = 2
        elif difficulty == 'medium':
            self.stages = 5
        elif difficulty == 'hard':
            self.stages = 9
        else:
            self.stages = 1

        self.enemies = []
        for i in range(1, self.stages + 1):
            if i > 6:
                bossToAdd = random.choice(
                    db.getEnemyRNG(self.adv.level, 2, 0))[0]
            elif i > 2:
                bossToAdd = random.choice(
                    db.getEnemyRNG(self.adv.level, 1, 0))[0]
            else:
                bossToAdd = None

            if bossToAdd:
                stageEnemies = [bossToAdd]
            else:
                stageEnemies = []

            pool = db.getEnemyRNG(self.adv.level)
            randMax = random.randint(1, 3)
            for _ in range(1, randMax + 1):
                stageEnemies.append(random.choice(pool)[0])

            self.enemies.append(stageEnemies)

        self.loot = []
        if difficulty == 'easy':
            self.lootInt = 2
        elif difficulty == 'medium':
            self.lootInt = 3
        elif difficulty == 'hard':
            self.lootInt = 4
        else:
            self.lootInt = 0

        lPool = db.getEquipmentRNG(self.adv.level)
        weights = np.asarray(Equipment.calculateWeight(lPool))
        try:
            for _ in range(1, self.lootInt + 1):
                self.loot.append(np.random.choice(lPool, p=weights))
        except Exception:
            logger.error('RNG Loot Failed to Load with weights: {}'.format(
                weights), exc_info=True)

        self.encounter = self.buildEncounter(
            [self.adv], self.enemies[self.stage - 1])

        self.save()

    def save(self):
        loot = ','.join(str(e) for e in self.loot)
        tmp = []
        for stage in self.enemies:
            tmp.append(','.join(str(e) for e in stage))
        enemies = ';'.join(tmp)
        save = [self.id, self.adv.id, int(self.active), self.stage, self.stages,
                enemies, loot, self.time.strftime('%Y-%m-%d %H:%M:%S'), self.xp, '|'.join(self.combat_log)]
        self.id = db.saveRNG(save)

    def loadActive(self, aID):
        try:
            save = db.getActiveRNG(aID)
            self.loot = save[6].split(',')

            self.enemies = []
            tmp = save[5].split(';')
            for stage in tmp:
                self.enemies.append(stage.split(','))

            self.id = save[0]
            self.adv = Player(save[1], False)
            self.active = bool(save[2])
            self.stage = save[3]
            self.stages = save[4]
            self.time = datetime.datetime.strptime(
                save[7], '%Y-%m-%d %H:%M:%S')
            self.xp = int(save[8])
            self.combat_log = save[9].split('|')
            self.encounter = self.buildEncounter(
                [self.adv], self.enemies[self.stage - 1])
            return True
        except Exception as e:
            logger.error('Failed to load quest {}\n{}:{}:{}'.format(
                self.id, type(self).__name__, type(e).__name__, e))
            return False

    def calculateTime(self, time: int):
        timeToAdd = datetime.timedelta(days=0, seconds=time)
        self.time = datetime.datetime.now() + timeToAdd
        logger.debug('Time calculated to {}'.format(
            self.time.strftime('%Y-%m-%d %H:%M:%S')))

    def buildEncounter(self, players: list, enemies: list):
        bPlayers = []
        bEnemies = []
        for player in players:
            if player is int:
                tmp = Player(player)
            else:
                tmp = player
                tmp.load()
            bPlayers.append(tmp)

        for enemy in enemies:
            tmp = Enemy(enemy)
            tmp.load()
            bEnemies.append(tmp)
        return Encounter(bPlayers, bEnemies)

    def nextStage(self):
        info = '**{0}**: {0.health}/{0.maxHealth}'.format(self.adv)
        info += '\n__*Enemies*__'
        for e in self.encounter.enemies:
            info += '\n*Lv {0.level}* **{0.name}**: {0.health}/{0.maxHealth}'.format(e)
        for e in self.encounter.deadEnemies:
            info += '\n*Lv {0.level}* **{0.name}**: {0.health}/{0.maxHealth}'.format(e)
        info += '\n'
        self.combat_log.append(info)
        if self.adv.health > 0:
            self.stage += 1
            self.xp += int(self.encounter.getExp())
            self.loot += self.encounter.getLoot()
            if self.stage > self.stages:
                self.end(True)
            else:
                self.adv.load()
                self.adv.rest()
                self.adv.save()
                self.encounter = self.buildEncounter(
                    [self.adv], self.enemies[self.stage - 1])
                self.calculateTime(RNGDungeon.stageTime)
        else:
            self.end(False)

    def end(self, result: bool):
        self.adv.load()
        self.active = False

        if result == True:
            self.adv.available = True
            self.adv.rest()
            self.adv.addXP(self.xp)
            for l in self.loot:
                self.adv.addInv(l)
        else:
            self.adv.available = True  # TEMPORARY UNTIL RECOVERY IS CODED
            self.adv.rest()

        self.adv.save()
        self.save()


class Shop():
    def __init__(self, adv, load=True):
        self.id = 0
        self.adv = adv
        self.adv.load()
        self.inventory = []
        self.buyback = []
        self.refresh = datetime.datetime.now()
        if load:
            self.loadActive()
        else:
            self.new()
            self.save()

    def new(self):
        equipment = db.getEquipmentRNG(self.adv.level)
        for _ in range(10):
            self.inventory.append(random.choice(equipment))
        self.refresh = datetime.datetime.now() + datetime.timedelta(hours=12)

    def save(self):
        if len(self.inventory) > 0:
            equipment_string = '|'.join(str(e) for e in self.inventory)
        else:
            equipment_string = None
        if len(self.buyback) > 0:
            buyback_string = '|'.join(str(e) for e in self.buyback)
        else:
            buyback_string = None
        refresh_string = self.refresh.strftime('%Y-%m-%d %H:%M:%S')
        save = [self.id, self.adv.id, equipment_string, buyback_string, refresh_string]
        self.id = db.SaveShop(save)

    def loadActive(self):
        save = db.GetActiveShop(self.adv.id)
        if save:
            self.id = save[0]
            tmp = save[2].split('|')
            equipment = list(map(lambda x: int(x), tmp))
            try:
                buypack = list(map(lambda x: int(x), save[3].split('|')))
            except AttributeError:
                buypack = []
            self.inventory = equipment
            self.buyback = buypack
            self.refresh = datetime.datetime.strptime(save[4], '%Y-%m-%d %H:%M:%S')
        else:
            self.new()
            self.save()


    def buy(self, index: int): # Index has to be the index in list
        index = int(index)
        equipment = Equipment(self.inventory[index])
        if self.adv.addInv(equipment.id):
            self.adv.remXP(equipment.price)
            self.inventory.pop(index)
            return True
        else:
            return False

    def buyB(self, index: int): # Index has to be the index in list
        index = int(index)
        equipment = Equipment(self.buyback[index])
        if self.adv.addInv(equipment.id):
            self.adv.remXP(equipment.price)
            self.buyback.pop(index)
            return True
        else:
            return False

    def sell(self, index: int):
        index = int(index)
        equipment = Equipment(self.adv.inventory[index])
        if self.adv.remInv(index + 1):
            self.buyback.append(index)
            self.adv.addXP(equipment.price)
            return True
        else:
            return False


class Raid():
    def __init__(self, players, boss = 0):
        self.id = 0
        self.boss = None
        self.players = []
        self.loot = []
        if boss == 0:
            pass
        else:
            self.new(players, boss)
    
    def new(self, players, boss):
        self.boss = RaidBoss(boss)
        if self.boss.loaded == False:
            return False
        self.players = players
        
        player_ids = []
        count = 0
        total = 0
        for player in self.players:
            count += 1
            total += player.level
            player_ids.append(str(player.id))
        self.loot = []
        loot_ids = []
        for _ in range(5):
            loot = self.boss.get_loot(Equipment.calculate_drop_rarity())
            if loot:
                self.loot.append(loot) # Need to get based on rarity
                loot_ids.append(str(loot.id))
        
        self.id = db.add_raid(','.join(player_ids), self.boss.id, ','.join(loot_ids))

    def build_encounter(self):
        self.encounter = Encounter(self.players, [self.boss])

    def finish_encounter(self, win: bool):
        totalXP = self.encounter.getExp() * 2 # Temporary
        for p in self.players:
            if win:
                p.addXP(totalXP)
            p.rest() # TEMPORARY UNTIL RECOVERY CODED
            p.save()
