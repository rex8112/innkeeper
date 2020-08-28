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
    def __init__(self, adv, skill_name: str):
            self.name = 'no_skill_loaded'
            self.targetable = 2
            self.max_cooldown = 0
            self.start_cooldown = 0
            self.damage_type = 'physical'
            self.hit_count = 1
            self.hit_chance_additive = 1.0
            self.damage_modifier = 1.0
            self.secondary_damage_modifier = 0.3 # For attacks that do not hit the main target i.e. Cleave
            self.requirements = {}
            self.flags = []

            self.log = ''
            self.user = adv
            self.wc = int(adv.mods.get('wc', 0))
            self.penetration = int(adv.mods.get('penetration', 0))
            self.critical = False

            self.load(skill_name)

            self.cooldown = self.start_cooldown

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
        damage = round(random.uniform((dmg * 0.9), (dmg * 1.1)), 2)
        damage *= self.damage_modifier
        return damage

    def get_secondary_damage(self, dmg: float):
        damage = round(random.uniform((dmg * 0.9), (dmg * 1.1)), 2)
        damage *= self.secondary_damage_modifier
        return damage

    def deal_damage(self, target, dmg: float):
        if self.damage_type == 'physical':
            return target.deal_physical_damage(dmg, self.penetration)
        elif self.damage_type == 'magical':
            return target.deal_magical_damage(dmg, self.penetration)
    
    def get_hit_chance(self, target):
        ac = int(target.mods.get('ac', 0))
        chance_to_hit = float(1 + (self.wc - ac) / ((self.wc + ac) * 0.5)) - 0.2
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
        if self.cooldown <= 0:
            info = f'{self.user.name} used `{self.name}` and dealt '
            targets = self.get_targets(target, target_group)
            damage_values = []
            for t in targets:
                damage_values.append([])
            for _ in range(self.hit_count):
                if self.test_hit_chance(self.get_hit_chance(targets[0])):
                    damage_values[0].append(self.deal_damage(targets[0], self.get_damage(float(self.user.mods.get('dmg', 0)))))
                    
                    if 'cleave' in self.flags:
                        if len(targets) > 1:
                            for index, t in enumerate(targets[1:], start=1):
                                damage_values[index].append(self.deal_damage(t, self.get_secondary_damage(float(self.user.mods.get('dmg', 0)))))
                else:
                    for l in damage_values:
                        l.append('X')
            for index, l in enumerate(damage_values):
                damages = ', '.join(str(d) for d in l)
                info += f'**{damages}** {self.damage_type} damage to {targets[index].name}. '
            result = True
            self.cooldown = self.max_cooldown
        else:
            info = f'`{self.name}` is on cooldown for `{self.cooldown}` more turns.'
            result = False
        return info, result

    def load(self, skill_name: str):
        if skill_name == 'attack':
            self.name = 'attack'
            self.targetable = 2
            self.max_cooldown = 0
        elif skill_name == 'backstab':
            self.name = 'backstab'
            self.targetable = 2
            self.max_cooldown = 4
            self.damage_modifier = 2.0
            self.hit_chance_additive = 0.1
            self.requirements = {
                'dexterity': Modifier('dexterity', 13)
            }
        elif skill_name == 'triplestrike':
            self.name = 'triplestrike'
            self.targetable = 2
            self.max_cooldown =  4
            self.hit_count = 3
            self.hit_chance_additive = -0.2
            self.requirements = {
                'dexterity': Modifier('dexterity', 13)
            }
        elif skill_name == 'cleave':
            self.name = 'cleave'
            self.targetable = 2
            self.max_cooldown = 3
            self.secondary_damage_modifier = 0.3
            self.flags = [
                'cleave'
            ]

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