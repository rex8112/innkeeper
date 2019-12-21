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


def get_skill(self, id: str):
    for i in skill_list:
        if i.id == id:
            return i
        else:
            return None

skill_list = []


class Skill():
    name = None # In Turns
    targetable = None # 0 = Self Cast, 1 = Ally Cast, 2 = Enemy Cast
    cleave = None # 0 = No, 1 = Surrounding, 2 = All
    max_cooldown = None

    def __init__(self):
        self.cooldown = self.max_cooldown 
    
    def use(self):
        return False


class AttackSkill(Skill):
    name = 'attack'
    targetable = 2
    cleave = 0
    max_cooldown = 1

    def use(self, user, target: int, targetGroup: list): # target is index in targetGroup
        if user.attackCooldown <= 0:
            dmg = user.dmg
            critChance = user.critChance
            chanceToHit = 1 + (user.wc - targetGroup[target].ac) / \
                ((user.wc + targetGroup[target].ac) * 0.5)

            if chanceToHit > 1:  # If you have a chance to hit higher than 100% convert overflow into crit chance
                critChance += chanceToHit - 1.0
                logger.debug(
                    'Player Crit Chance set to: {}'.format(critChance))

            if random.uniform(0.0, 1.0) > user.evasion:  # Evasion Check
                # If random number is lower than the chance to hit, you hit
                if random.uniform(0.0, 1.0) <= chanceToHit:
                    if random.uniform(0.0, 1.0) <= critChance:
                        dmg = dmg * 2
                    targetGroup[target].health -= dmg
                    logger.debug('Character hit for {} DMG'.format(dmg))
                    user.attackCooldown = user.attackSpeed
                else:  # You miss
                    logger.debug(
                        'Missed with chanceToHit: {:.1%}'.format(chanceToHit))
            else:  # You evaded
                logger.debug('Player Evaded')

        else:
         user.attackCooldown -= 1
