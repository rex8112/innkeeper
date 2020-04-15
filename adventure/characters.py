import logging
import math
import random

from.per_level import PerLevel
from .skills import Skill
from .exceptions import InvalidLevel, InvalidRequirements, InvalidModString
from .equipment import Equipment
from .modifiers import Modifier, EliteModifier
from .database import db

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

    def __init__(self, ID, load = True):
        self.id = ID
        self.name = 'Unloaded'
        self.mods = {}
        self.raw_mods = {}
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
            eq = Equipment(self.inventory[e])

            if self.level < eq.level:
                raise InvalidLevel('{} is too low level to equip level {} {}'.format(self.name, eq.level, eq.name))
            elif self.rawStrength < eq.requirements.get('strength', 0):
                raise InvalidRequirements('{} does not have enough strength to equip {}'.format(self.name, eq.name))
            elif self.rawDexterity < eq.requirements.get('dexterity', 0):
                raise InvalidRequirements('{} does not have enough dexterity to equip {}'.format(self.name, eq.name))
            elif self.rawConstitution < eq.requirements.get('constitution', 0):
                raise InvalidRequirements('{} does not have enough constitution to equip {}'.format(self.name, eq.name))
            elif self.rawIntelligence < eq.requirements.get('intelligence', 0):
                raise InvalidRequirements('{} does not have enough intelligence to equip {}'.format(self.name, eq.name))
            elif self.rawWisdom < eq.requirements.get('wisdom', 0):
                raise InvalidRequirements('{} does not have enough wisdom to equip {}'.format(self.name, eq.name))
            elif self.rawCharisma < eq.requirements.get('charisma', 0):
                raise InvalidRequirements('{} does not have enough charisma to equip {}'.format(self.name, eq.name))

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

            if not uneq.requirements.get('empty', False):
                self.inventory.append(uneq.save())
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

        if not uneq.mods.get('empty', False):
            self.inventory.append(uneq.save())
        self.calculate()

    def addInv(self, ID):
        try:
            if len(self.inventory) < self.inventoryCapacity:
                self.inventory.append(ID)
                logger.debug('Adding {} to Inventory'.format(ID))
                return True
            else:
                return False
        except AttributeError:
            self.calculate()
            return self.addInv(ID)

    def remInv(self, e: int):
        try:
            self.inventory.pop(e)
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

    def roll_initiative(self):
        return random.randint(1, 20) + self.level

    def deal_physical_damage(self, value: float, penetration = 0):
        parmor = self.mods.get('parmor', 0) - penetration
        if parmor > 100:
            parmor = 100
        elif parmor < 0:
            parmor = 0
        damage = value * ((100 - parmor) / 100)
        self.health -= damage
        return damage

    def deal_magical_damage(self, value: float, penetration = 0):
        marmor = self.mods.get('marmor', 0) - penetration
        if marmor > 100:
            marmor = 100
        elif marmor < 0:
            marmor = 0
        damage = value * ((100 - marmor) / 100)
        self.health -= damage
        return damage

    def heal(self, value: float):
        self.health += value
        if self.health > self.maxHealth:
            value -= self.health - self.maxHealth
            self.health = self.maxHealth
        return value

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
        self.mods['wc'] = Modifier('wc', 3)
        self.mods['ac'] = Modifier('ac', 4)
        self.mods['dmg'] = Modifier('dmg', 0)
        self.mods['strdmg'] = Modifier('strdmg', 0)
        self.mods['dexdmg'] = Modifier('dexdmg', 0)

        for mod in self.raw_mods.values():
            if self.mods.get(mod.id, False):
                self.mods[mod.id].value += mod.value
            else:
                self.mods[mod.id] = mod

        # TIME FOR EQUIPMENT CALCULATIONS
        for equip in [self.mainhand, self.offhand, self.helmet, self.armor, self.gloves, self.boots, self.trinket]:
            if equip == None:
                equip = Equipment('empty')

            for key, mod in equip.starting_mods.items():
                if self.mods.get(key, False):
                    self.mods.get(key).value += mod.value
                else:
                    self.mods[key] = mod
            for key, mod in equip.random_mods.items():
                if self.mods.get(key, False):
                    self.mods.get(key).value += mod.value
                else:
                    self.mods[key] = mod
        self.maxHealth += int(self.mods.get('health', 0))

        self.strength += int(self.mods.get('strength', 0))
        self.dexterity += int(self.mods.get('dexterity', 0))
        self.constitution += int(self.mods.get('constitution', 0))
        self.intelligence += int(self.mods.get('intelligence', 0))
        self.wisdom += int(self.mods.get('wisdom', 0))
        self.charisma += int(self.mods.get('charisma', 0))

        # Strength Related Stats First
        self.mods['unarmDamage'] = Modifier('unarmDamage', float(self.strength) * PerLevel.unarm_damage)
        logger.debug(
            '{0.name} Unarmed Damage calculated to: {1}'.format(self, self.mods['unarmDamage']))

        self.inventoryCapacity = (self.rawStrength // PerLevel.inventory_cap + 
            (10 - (10 // PerLevel.inventory_cap)))
        logger.debug(
            '{0.name} Inventory Capacity calculated to: {0.inventoryCapacity}'.format(self))

        # Dexterity related stats second
        dex = self.dexterity - 10
        if dex <= 40:  # Dexterity below 40
            evasion = Modifier('evasion', float(dex) * PerLevel.evasion)
            crit = Modifier('critChance', float(dex) * PerLevel.evasion)

        elif dex > 40 and dex <= 100:  # Dexterity between 40 and 100
            evasion = Modifier('evasion', (PerLevel.softcap_evasion * (float(dex) - 40.0) + 40.0 * PerLevel.evasion))
            crit = Modifier('critChance', (PerLevel.softcap_crit_chance * (float(dex) - 40.0) + 40.0 * PerLevel.crit_chance))

        else:  # Dexterity above 100
            evasion = Modifier('evasion', (PerLevel.softcap_evasion * (100.0 - 40.0) + 40.0 * PerLevel.evasion))
            crit = Modifier('critChance', (PerLevel.softcap_crit_chance * (100.0 - 40.0) + 40.0 * PerLevel.crit_chance))
        
        if self.mods.get(evasion.id, False):
            self.mods[evasion.id].value += evasion.value
        else:
            self.mods[evasion.id] = evasion
        if self.mods.get(crit.id, False):
            self.mods[crit.id].value += crit.value
        else:
            self.mods[crit.id] = crit

        logger.debug(
            '{0.name} Evasion calculated to: {1}'.format(self, self.mods['evasion']))
        logger.debug(
            '{0.name} Crit Chance calculated to: {1}'.format(self, self.mods['critChance']))

        # Constitution related stats third
        self.maxHealth += PerLevel.health * self.constitution + 100
        logger.debug(
            '{0.name} Max health calculated to: {0.maxHealth}'.format(self))

        # Intelligence related stats fourth
        spellAmp = Modifier('spellAmp', (PerLevel.spell_amp * float(self.intelligence - 10)))
        if self.mods.get(spellAmp.id, False):
            self.mods[spellAmp.id].value += spellAmp.value
        else:
            self.mods[spellAmp.id] = spellAmp
        logger.debug(
            '{0.name} Spell Amp calculated to: {1}'.format(self, self.mods['spellAmp']))
        spell_damage = Modifier('spellDamage', (PerLevel.spell_damage * float(self.intelligence - 10)))
        if self.mods.get(spell_damage.id, False):
            self.mods[spell_damage.id].value += spell_damage.value
        else:
            self.mods[spell_damage.id] = spell_damage

        # Wisdom related stats fifth
        out_heal_amp = Modifier('healAmp', (PerLevel.out_heal_amp * float(self.wisdom - 10)))
        if self.mods.get(out_heal_amp.id, False):
            self.mods[out_heal_amp.id].value += out_heal_amp.value
        else:
            self.mods[out_heal_amp.id] = out_heal_amp
        spell_heal = Modifier('spellHeal', (PerLevel.spell_heal * float(self.wisdom - 10)))
        if self.mods.get(spell_heal.id, False):
            self.mods[spell_heal.id].value += spell_heal.value
        else:
            self.mods[spell_heal.id] = spell_heal

        # Charisma related stats sixth
        # self.discount = 0

        # Fill in Skills
        self.skills = []
        for skill in self.raw_skills:
            s = Skill.get_skill(skill)
            if s:
                self.skills.append(s())

        # Set values to their maximum
        self.mods['dmg'].value += self.mods['strdmg'].value * self.strength + self.mods['dexdmg'].value * self.dexterity

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

    def load(self, calculate=True):
        try:
            raw = db.getAdventurer(self.id)
            self.name = raw['name']
            self.cls = raw['class']
            self.level = raw['level']
            self.xp = raw['xp']
            self.race = raw['race']

            rawAttributes = raw['attributes'].split(',')  # Get a list of the attributes
            self.rawStrength = int(rawAttributes[0])
            self.rawDexterity = int(rawAttributes[1])
            self.rawConstitution = int(rawAttributes[2])
            self.rawIntelligence = int(rawAttributes[3])
            self.rawWisdom = int(rawAttributes[4])
            self.rawCharisma = int(rawAttributes[5])

            try:
                self.raw_skills = raw['skills'].split(',')  # Get a list of skills
            except AttributeError:
                self.raw_skills = []

            equipment = raw['equipment'].split('/')  # Get a list of equipped items
            self.mainhand = Equipment(equipment[0])
            self.offhand = Equipment(equipment[1])
            self.helmet = Equipment(equipment[2])
            self.armor = Equipment(equipment[3])
            self.gloves = Equipment(equipment[4])
            self.boots = Equipment(equipment[5])
            self.trinket = Equipment(equipment[6])

            self.inventory = raw['inventory'].split('/')
            try:
                self.inventory.remove('')
            except:
                pass
            self.available = bool(raw['available'])
            self.health = int(raw['health'])

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
        equipment = '/'.join(str(e) for e in [self.mainhand.save(), self.offhand.save(),
                                              self.helmet.save(), self.armor.save(),
                                              self.gloves.save(), self.boots.save(),
                                              self.trinket.save()])
        inventory = '/'.join(str(e) for e in self.inventory)

        save = [self.id, self.name, self.cls, self.level, int(
            self.xp), self.race, rawAttributes, skills, equipment, inventory, int(self.available), self.health]
        logger.debug('{}:{} Saved Successfully'.format(self.id, self.name))
        return db.saveAdventurer(save)

    def delete(self):
        """IRREVERSIBLE deletion of an adventurer"""
        for e in [self.mainhand, self.offhand,
                  self.helmet, self.armor,
                  self.gloves, self.boots,
                  self.trinket]:
            e.delete()

        for raw_e in self.inventory:
            e = Equipment(raw_e)
            e.delete()

        db.deleteAdventurer(self.id)
        logger.warning('{}:{} Deleted'.format(self.id, self.name))


class Enemy(Character):
    def __init__(self, raw_data = ''):
        self.name = 'Unloaded'
        self.mods = {}
        self.raw_mods = {}
        self.loaded = False

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

    def generate_new(self, lvl: int, rng = True, index = 0):
        if index == 0:
            data_pool = db.get_base_enemy(lvl, rng=rng)
            data = random.choice(data_pool)
        else:
            data = db.get_base_enemy_indx(index)
        
        self.id = int(data[0])
        self.name = str(data[1])
        # minLevel = int(data[2])
        # maxLevel = int(data[3])
        self.potential_elites = data[4].split('|')
        attributes_string = data[5]
        modifiers_string = data[6]
        self.raw_skills = data[7].split('|')
        self.level = lvl
        self.process_attributes_string(attributes_string)
        self.raw_mods = self.process_mod_string(modifiers_string)

    def generate_new_elite(self, lvl: int, rng = True, index = 0):
        self.generate_new(lvl, rng=rng, index=index)
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

    def calculate(self):
        self.health = 0
        self.mainhand = Equipment('empty')
        self.offhand = Equipment('empty')
        self.helmet = Equipment('empty')
        self.armor = Equipment('empty')
        self.gloves = Equipment('empty')
        self.boots = Equipment('empty')
        self.trinket = Equipment('empty')
        Character.calculate(self)
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


class RaidBoss(Character):
    def __init__(self, boss_id):
        self.id = boss_id
        self.raw_mods = {}
        self.mods = {}
        self.loaded = False
        if self.id > 0:
            self.load()

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
                try:
                    self.inventory.append(int(L))
                except (AttributeError, ValueError):
                    logger.error('{} can not be converted to int in {} RaidBoss generation'.format(L, self.id), exc_info=True)

            self.mainhand = None
            self.offhand = None
            self.helmet = None
            self.armor = None
            self.gloves = None
            self.boots = None
            self.trinket = None

            for mod_string in data[8].split('|'):
                mod_tmp = mod_string.split(':')
                mod = Modifier(mod_tmp[0], int(mod_tmp[1]))
                self.raw_mods[mod.id] = mod

            self.calculate()
            self.loaded = True
            return True
        except Exception:
            logger.error('{} Failed to Load Raid Boss'.format(
                self.id), exc_info=True)
            return False