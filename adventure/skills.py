import random
import logging

from .modifiers import Modifier

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
    requirements = {}
    log = ''

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

    def __init__(self):
        if self.start_cooldown:
            self.cooldown = self.start_cooldown
        else:
            self.cooldown = self.max_cooldown 
        self.log = ''

    def get_damage(self, dmg: float):
        return round(random.uniform((dmg * 0.9), (dmg * 1.1)), 2)
    
    def use(self, user, target, targetGroup: list):
        result = False
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