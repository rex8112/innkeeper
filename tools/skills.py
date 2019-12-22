import random
import logging

import adventureController as ac


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
    name = None # In Turns
    targetable = None # 0 = Self Cast, 1 = Ally Cast, 2 = Enemy Cast
    cleave = None # 0 = No, 1 = Surrounding, 2 = All
    max_cooldown = None

    @staticmethod
    def get_skill(name: str):
        skill_list = [AttackSkill]
        for i in skill_list:
            if i.name == name:
                return i
            else:
                return None

    def __init__(self):
        self.cooldown = self.max_cooldown 
        self.log = ''
    
    def use(self, user, target, targetGroup: list):
        return False


class AttackSkill(Skill):
    name = 'attack'
    targetable = 2
    cleave = 0
    max_cooldown = 0

    def use(self, user, target, targetGroup: list):
        if self.cooldown <= 0:
            dmg = user.dmg
            critChance = user.critChance
            chanceToHit = 1 + (user.wc - target.ac) / \
                ((user.wc + target.ac) * 0.5)

            if chanceToHit > 1:  # If you have a chance to hit higher than 100% convert overflow into crit chance
                critChance += chanceToHit - 1.0
                logger.debug(
                    'Player Crit Chance set to: {}'.format(critChance))

            if random.uniform(0.0, 1.0) > user.evasion:  # Evasion Check
                # If random number is lower than the chance to hit, you hit
                if random.uniform(0.0, 1.0) <= chanceToHit:
                    if random.uniform(0.0, 1.0) <= critChance:
                        dmg = dmg * 2
                        self.log = '**{}** crit **{}** for **{}** Damage'.format(user.name, target.name, dmg)
                    target.health -= dmg
                    logger.debug('Character hit for {} DMG'.format(dmg))
                    self.log = '**{}** hit **{}** for **{}** Damage'.format(user.name, target.name, dmg)
                    self.cooldown = self.max_cooldown
                else:  # You miss
                    logger.debug(
                        'Missed with chanceToHit: {:.1%}'.format(chanceToHit))
                    self.log = '{} missed trying to hit {}'.format(user.name, target.name)
            else:  # You evaded
                logger.debug('Player Evaded')
                self.log = '{1} evaded attack from {0}'.format(user.name, target.name)
            return self.log
        else:
         self.cooldown -= 1
