import random
import logging

from .modifiers import Modifier
from .exceptions import NotFound

logger = logging.getLogger('skills')
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


class Skill():
    name = None # Identification
    targetable = None # 0 = Self Cast, 1 = Ally Cast, 2 = Enemy Cast
    max_cooldown = None
    start_cooldown = None
    damage_type = 'physical'
    hit_chance_modifier = 1.0
    damage_modifier = 1.0
    secondary_damage_modifier = 0.3 # For attacks that do not hit the main target i.e. Cleave
    requirements = {}
    flags = {}

    @staticmethod
    def get_skill(name: str):
        skill_list = {
            Attack.name: Attack,
            BackStab.name: BackStab,
            Cleave.name: Cleave,
            TripleStrike.name: TripleStrike
        }
        if name == 'all':
            return skill_list.copy()
        else:
            return skill_list.get(name, None)

    def __init__(self, adv, **kwargs):
        if isinstance(self, Skill):
            skill_str = kwargs.get('skill', '')
            if skill_str:
                found_skill = self.get_skill(skill_str)
                self = found_skill(adv)
            else:
                raise NotFound(f'{skill_str} skill not available.')
        else:
            self.log = ''
            self.user = adv
            self.ac = int(adv.mods.get('ac', 0))
            self.penetration = int(adv.mods.get('penetration', 0))
            self.critical = False

            if self.start_cooldown:
                self.cooldown = self.start_cooldown
            else:
                self.cooldown = self.max_cooldown

    def get_targets(self, target, target_group: list):
        if 'cleave' in self.flags:
            target_int = target_group.index(target)
            cleave_1_int = target_int - 1
            cleave_2_int = target_int + 1
            if cleave_1_int < 0:
                cleave_1 = target_group[-1]
            else:
                cleave_1 = target_group[cleave_1_int]
            if cleave_2_int >= len(target_group):
                cleave_2 = target_group[0]
            else:
                cleave_2 = target_group[cleave_2_int]
            if len(target_group) >= 3:
                return [target, cleave_1, cleave_2]
            elif len(target_group) == 2:
                return [target, cleave_1]
            else:
                return [target]
        else:
            return [target]

    def apply_status_effects(self, target):
        pass

    def get_damage(self, dmg: float):
        return round(random.uniform((dmg * 0.9), (dmg * 1.1)), 2)

    def deal_damage(self, target, dmg: float):
        if self.damage_type == 'physical':
            target.deal_physical_damage(dmg, self.penetration)
        elif self.damage_type == 'magical':
            target.deal_magical_damage(dmg, self.penetration)
    
    def get_hit_chance(self, target):
        wc = int(target.mods.get('wc', 0))
        chance_to_hit = float(1 + (wc - self.ac) / ((wc + self.ac) * 0.5)) - 0.2
        return chance_to_hit

    def test_hit_chance(self, hit_chance):
        if 'never_miss' in self.flags:
            return True
        else:
            if random.uniform(0.0, 1.0) <= hit_chance:
                return True
            else:
                return False

    def use(self, target, target_group: list):
        targets = self.get_targets(target, target_group)
        if self.test_hit_chance(self.get_hit_chance(target[0])):
            self.deal_damage(target[0], self.get_damage(self.user.mods.get('dmg', 0)))
        if len(targets) > 1:
            for t in targets[1:]:
                if self.test_hit_chance(self.get_hit_chance(t)):
                    self.deal_damage(t, self.get_damage(self.user.mods.get('dmg', 0)) * self.secondary_damage_modifier)
        result = True
        info = 'Invalid Skill'
        return info, result


class Attack(Skill):
    """Normal attack with your mainhand weapon"""
    name = 'attack'
    targetable = 2
    max_cooldown = 0

    def use(self, user, target, targetGroup: list):
        if self.cooldown <= 0:
            self.log = ''
            dmg = self.get_damage(float(user.mods.get('dmg', 0)))
            critChance = float(user.mods.get('critChance'))
            target_ac = float(target.mods.get('ac', 0))
            user_wc = float(user.mods.get('wc', 0))
            chanceToHit = float(1 + (user_wc - target_ac) /
                ((user_wc + target_ac) * 0.5)) - 0.2

            if random.uniform(1.0, 100.0) > user.mods.get('evasion', 0):  # Evasion Check
                # If random number is lower than the chance to hit, you hit
                if random.uniform(0.0, 1.0) <= chanceToHit:
                    if random.uniform(1.0, 100.0) <= critChance:
                        dmg = dmg * 2
                    dealt_damage = target.deal_physical_damage(dmg, user.mods.get('penetration', Modifier('penetration', 0)).value)
                    logger.debug('Character hit for {} DMG'.format(dealt_damage))
                    self.log = '**{}** hit **{}** for **{}** Damage.'.format(user.name, target.name, dealt_damage)
                    self.cooldown = self.max_cooldown
                else:  # You miss
                    logger.debug(
                        'Missed with chanceToHit: {:.1%}'.format(chanceToHit))
                    self.log = '**{}** missed trying to hit **{}**.'.format(user.name, target.name)
            else:  # You evaded
                logger.debug('Player Evaded')
                self.log = '**{1}** evaded **{0}**\'s backstab.'.format(user.name, target.name)
            return self.log, True
        else:
            self.log = '**{}** on cooldown for **{}** more turns.'.format(self.name.capitalize(), self.cooldown)
            return self.log, False

class BackStab(Skill):
    """Sneak up behind your target and strike them in the back.
    
    `Ignores 10% of AC`
    `Deals Double Damage`"""
    name = 'backstab'
    targetable = 2
    max_cooldown = 4
    requirements = {
        'dexterity': Modifier('dexterity', 13)
    }

    def use(self, user, target, targetGroup: list):
        if self.cooldown <= 0:
            self.log = ''
            dmg = self.get_damage(float(user.mods.get('dmg', 0)))
            target_ac = float(target.mods.get('ac', 0))
            user_wc = float(user.mods.get('wc', 0))
            target_ac *= 0.9
            chanceToHit = float(1 + (user_wc - target_ac) /
                ((user_wc + target_ac) * 0.5)) - 0.2


            if random.uniform(1.0, 100.0) > user.mods.get('evasion', 0):  # Evasion Check
                # If random number is lower than the chance to hit, you hit
                if random.uniform(0.0, 1.0) <= chanceToHit:
                    dmg = dmg * 2
                    dealt_damage = target.deal_physical_damage(dmg, user.mods.get('penetration', 0))
                    self.log = '**{}** snuck up behind **{}** and backstabbed them for **{}** Damage.'.format(user.name, target.name, dealt_damage)
                else:  # You miss
                    self.log = '**{}** missed trying to backstab **{}**.'.format(user.name, target.name)
            else:  # You evaded
                self.log = '**{1}** evaded **{0}**\'s backstab.'.format(user.name, target.name)
                self.cooldown = self.max_cooldown
            return self.log, True
        else:
            self.log = '**{}** on cooldown for **{}** more turns.'.format(self.name.capitalize(), self.cooldown)
            return self.log, False

class TripleStrike(Skill):
    """Unleash three quick strikes that are less likely to hit.
    
    `80% WC`
    `80% Damage`"""
    name = 'triplestrike'
    targetable = 2
    max_cooldown = 4
    requirements = {
        'dexterity': Modifier('dexterity', 13)
    }

    def use(self, user, target, targetGroup: list):
        if self.cooldown <= 0:
            self.log = '{} Unleashed three strikes towards {}: '.format(user.name, target.name)
            raw_dmg = float(user.mods.get('dmg', 0)) * 0.8
            pen = user.mods.get('penetration', 0)
            critChance = float(user.mods.get('critChance', 0))
            target_ac = float(target.mods.get('ac', 0))
            user_wc = float(user.mods.get('wc', 0))
            user_wc *= 0.8

            for _ in range(3):
                dmg = self.get_damage(raw_dmg)
                chanceToHit = float(1 + (user_wc - target_ac) /
                    ((user_wc + target_ac) * 0.5)) - 0.2
                if random.uniform(1.0, 100.0) > user.mods.get('evasion', 0):  # Evasion Check
                    # If random number is lower than the chance to hit, you hit
                    if random.uniform(0.0, 1.0) <= chanceToHit:
                        if random.uniform(1.0, 100.0) <= critChance:
                            dmg = dmg * 2
                            self.log += '**CRIT** '
                        dealt_damage = target.deal_physical_damage(dmg, pen)
                        logger.debug('Character hit for {} DMG'.format(dealt_damage))
                        self.log += '**{}**, '.format(dealt_damage)
                        self.cooldown = self.max_cooldown
                    else:  # You miss
                        logger.debug(
                            'Missed with chanceToHit: {:.1%}'.format(chanceToHit))
                        self.log += '**MISSED**, '
                else: # Evaded
                    self.log += '**EVADED**, '
            return self.log[:-2], True
        else:
            self.log = '**{}** on cooldown for **{}** more turns.'.format(self.name.capitalize(), self.cooldown)
            return self.log, False

class Cleave(Skill):
    """A wide swinging attack that strikes neighboring targets.
    
    `30% Cleave`"""
    name = 'cleave'
    targetable = 2
    max_cooldown = 3

    def use(self, user, target, targetGroup: list):
        if self.cooldown <= 0:
            self.log = ''
            position = targetGroup.index(target)
            dmg = self.get_damage(float(user.mods.get('dmg', 0)))
            pen = user.mods.get('penetration', 0)
            cleave_damage = dmg * .3
            cleave1 = None
            cleave2 = None
            critChance = float(user.mods.get('critChance'))
            target_ac = float(target.mods.get('ac', 0))
            user_wc = float(user.mods.get('wc', 0))
            chanceToHit = float(1 + (user_wc - target_ac) /
                ((user_wc + target_ac) * 0.5)) - 0.2

            if random.uniform(1.0, 100.0) > user.mods.get('evasion', 0):  # Evasion Check
                # If random number is lower than the chance to hit, you hit
                if random.uniform(0.0, 1.0) <= chanceToHit:
                    if random.uniform(1.0, 100.0) <= critChance:
                        dmg = dmg * 2

                    try:
                        cleave1 = targetGroup[position-1].deal_physical_damage(cleave_damage, pen)
                    except IndexError:
                        pass
                    try:
                        cleave2 = targetGroup[position+1].deal_physical_damage(cleave_damage, pen)
                    except IndexError:
                        pass

                    dealt_damage = target.deal_physical_damage(dmg, pen)
                    logger.debug('Character hit for {} DMG'.format(dealt_damage))
                    self.log = '**{}** cleaved through **{}** for **{}** damage and hit '.format(user.name, target.name, dealt_damage)
                    if cleave1 and cleave2:
                        self.log += '**{}** and **{}** for **{}** and **{}** damage.'.format(targetGroup[position-1].name, targetGroup[position+1].name, cleave1, cleave2)
                    elif cleave1:
                        self.log += '**{}** for **{}** damage.'.format(targetGroup[position-1].name, cleave1)
                    elif cleave2:
                        self.log += '**{}** for **{}** damage.'.format(targetGroup[position+1].name, cleave2)
                    else:
                        self.log += 'no one else.'
                    self.cooldown = self.max_cooldown
                else:  # You miss
                    logger.debug(
                        'Missed with chanceToHit: {:.1%}'.format(chanceToHit))
                    self.log = '**{}** missed trying to hit **{}**.'.format(user.name, target.name)
            else:  # You evaded
                logger.debug('Player Evaded')
                self.log = '**{1}** evaded **{0}**\'s backstab.'.format(user.name, target.name)
            return self.log, True
        else:
            self.log = '**{}** on cooldown for **{}** more turns.'.format(self.name.capitalize(), self.cooldown)
            return self.log, False


class MagicMissile(Skill):
    """A shot of pure magic.
    
    `60% Damage`
    `Never Misses`"""
    name = 'magicmissile'
    targetable = 2
    max_cooldown = 0

    def use(self, user, target, targetGroup: list):
        if self.cooldown <= 0:
            self.log = ''
            dmg = self.get_damage(float(user.mods.get('spellDamage', 0))) * 0.6
            
            dealt_damage = target.deal_magical_damage(dmg, user.mods.get('penetration', 0))
            self.log = '**{}** shot a magic missile at **{}**, dealing **{}** Magic Damage'.format(user.name, target.name, dealt_damage)
            
            return self.log, True
        else:
            self.log = '**{}** on cooldown for **{}** more turns.'.format(self.name.capitalize(), self.cooldown)
            return self.log, False


class HealingTouch(Skill):
    """A gentle touch that heals the wounds of the target."""
    name = 'healingtouch'
    targetable = 1
    max_cooldown = 3
    
    def use(self, user, target, targetGroup: list):
        if self.cooldown <= 0:
            self.log = ''
            heal = self.get_damage(float(user.mods.get('spellHeal', 0)))
            heal_amount = target.heal(heal)
            self.log = '**{}** placed their hands upon **{}** and healed them by **{}** HP'.format(user.name, target.name, heal_amount)
            return self.log, True
        else:
            self.log = '**{}** on cooldown for **{}** more turns.'.format(self.name.capitalize(), self.cooldown)
            return self.log, False