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
            BackStab.name: BackStab
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
            dmg = float(user.mods.get('dmg', 0))
            min_dmg = dmg * 0.9
            max_dmg = dmg * 1.1
            dmg = round(random.uniform(min_dmg, max_dmg), 2)
            critChance = float(user.mods.get('critChance'))
            target_ac = target.mods.get('ac', 0)
            user_wc = user.mods.get('wc', 0)
            chanceToHit = float(1 + (user_wc - target_ac) /
                ((user_wc + target_ac) * 0.5))

            if random.uniform(1.0, 100.0) > user.mods.get('evasion', 0):  # Evasion Check
                # If random number is lower than the chance to hit, you hit
                if random.uniform(0.0, 1.0) <= chanceToHit:
                    if random.uniform(1.0, 100.0) <= critChance:
                        dmg = dmg * 2
                        self.log = '**{}** crit **{}** for **{}** Damage.'.format(user.name, target.name, dmg)
                    target.deal_physical_damage(dmg)
                    logger.debug('Character hit for {} DMG'.format(dmg))
                    self.log = '**{}** hit **{}** for **{}** Damage.'.format(user.name, target.name, dmg)
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
            dmg = float(user.mods.get('dmg', 0))
            min_dmg = dmg * 0.9
            max_dmg = dmg * 1.1
            dmg = round(random.uniform(min_dmg, max_dmg), 2)
            target_ac = target.mods.get('ac', 0)
            user_wc = user.mods.get('wc', 0)
            target_ac *= 0.9
            chanceToHit = float(1 + (user_wc - target_ac) /
                ((user_wc + target_ac) * 0.5))


            if random.uniform(1.0, 100.0) > user.mods.get('evasion', 0):  # Evasion Check
                # If random number is lower than the chance to hit, you hit
                if random.uniform(0.0, 1.0) <= chanceToHit:
                    dmg = dmg * 2
                    dealt_damage = target.deal_physical_damage(dmg)
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