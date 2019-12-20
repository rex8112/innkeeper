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

def attack_skill(self, adventurer, target, targetGroup): # Unfinished, CopyPasta-ed from adventureController.py
    if attacker.attackCooldown <= 0:
        dmg = attacker.dmg
        critChance = attacker.critChance
        chanceToHit = 1 + (attacker.wc - defender.ac) / \
            ((attacker.wc + defender.ac) * 0.5)

        if chanceToHit > 1:  # If you have a chance to hit higher than 100% convert overflow into crit chance
            critChance += chanceToHit - 1.0
            logger.debug(
                'Player Crit Chance set to: {}'.format(critChance))

        if random.uniform(0.0, 1.0) > attacker.evasion:  # Evasion Check
            # If random number is lower than the chance to hit, you hit
            if random.uniform(0.0, 1.0) <= chanceToHit:
                if random.uniform(0.0, 1.0) <= critChance:
                    dmg = dmg * 2
                defender.health -= dmg
                logger.debug('Character hit for {} DMG'.format(dmg))
                attacker.attackCooldown = attacker.attackSpeed
            else:  # You miss
                logger.debug(
                    'Missed with chanceToHit: {:.1%}'.format(chanceToHit))
        else:  # You evaded
            logger.debug('Player Evaded')

    else:
        attacker.attackCooldown -= 1

attack = ac.Skill('attack')
attack.type = 2
attack.cleave = 0
attack.use = attack_skill