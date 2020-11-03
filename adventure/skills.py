import random
import logging

from .modifiers import Modifier
from .exceptions import NotFound
from .statusEffects import StatusEffect

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


def get_skill(adv, name: str):
    skills = {
        Attack.name: Attack,
        Backstab.name: Backstab,
        TripleStrike.name: TripleStrike,
        Cleave.name: Cleave
    }
    skill = skills.get(name)
    if skill:
        return skill(adv)
    else:
        raise NotFound(f'"{name}" not an available skill.')


class Skill():
    name = 'no_skill_loaded'
    targetable = 2
    max_cooldown = 0
    start_cooldown = 0
    damage_type = 'physical'
    damage_percentage = 1.0
    status_effects = {}
    requirements = {}
    def __init__(self, adv):
        self.log = ''
        self.user = adv
        self.crit_chance_additive = 0.0
        self.wc = int(adv.mods.get('wc', 0))
        self.penetration = int(adv.mods.get('penetration', 0))
        self.critical = False
        self.cooldown = self.start_cooldown

    def get_description(self):
        description = (
            'Unloaded skill. If you see this you broke something.'
        )
        return description

    def apply_status_effects(self, target):
        for s, p in self.status_effects.items():
            target.add_status_effect(StatusEffect(s, p))

    def get_damage(self, dmg: float, type='dmg'):
        damage = round(random.uniform((dmg * 0.9), (dmg * 1.1)), 2)
        return damage

    def deal_damage(self, target, dmg: float, ignore_crit=False):
        if self.critical and not ignore_crit:
            dmg *= 2
        if self.damage_type == 'physical':
            return target.deal_physical_damage(dmg, self.penetration)
        elif self.damage_type == 'magical':
            return target.deal_magical_damage(dmg, self.penetration)
    
    def get_hit_chance(self, target):
        ac = int(target.mods.get('ac', 0))
        chance_to_hit = float(1 + (self.wc - ac) / ((self.wc + ac) * 0.5)) - 0.2
        if chance_to_hit > 1:
            self.crit_chance_additive = chance_to_hit - 1.0
        return chance_to_hit

    def get_crit_chance(self, target):
        crit_chance = target.mods.get('crit_chance', Modifier('crit_chance'))
        crit_chance += self.crit_chance_additive
        return crit_chance

    def test_chance(self, chance):
        if random.uniform(0.0, 1.0) <= chance:
            return True
        else:
            return False

    def use(self, target, target_group: list):
        return 'ERROR: Unloaded Skill. You should never see this.', False

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

class Attack(Skill):
    """A normal attack with your mainhand weapon"""
    name = 'attack'
    targetable = 2
    max_cooldown = 0
    damage_type = 'physical'

    def get_description(self):
        description = (
            'A normal attack with your mainhand weapon.'
        )
        return description

    def use(self, target, target_group: list):
        if self.cooldown <= 0:
            if self.test_chance(self.get_hit_chance(target)):
                if self.test_chance(self.get_crit_chance(self.user)):
                    self.critical = True
                damage_dealt = self.deal_damage(target, self.user.get_damage())
                info = f'**{self.user}** attacks **{target}** and deals **{damage_dealt}** damage.'
            else:
                info = f'**{self.user}** attacks **{target}** and **misses**.'
            self.cooldown = self.max_cooldown
            return info, True
        else:
            info = f'`{self.name}` is on cooldown for `{self.cooldown}` more turns.'
            return info, False

class Backstab(Skill):
    """A guaranteed critical striek with a slightly higher chance to hit."""
    name = 'backstab'
    targetable = 2
    max_cooldown = 4
    damage_type = 'physical'
    hit_chance_additive = 0.1
    damage_percentage = 2.0
    requirements = {
        'dexterity': Modifier('dexterity', 13)
    }

    def get_description(self):
        description = (
            'A guaranteed critical strike with a slightly higher chance to hit.'
            '\n\n'
            f'`+{self.hit_chance_additive:.2%} Hit Chance`\n'
            f'`{self.damage_percentage:.2%} Damage`'
        )
        return description

    def use(self, target, target_group: list):
        if self.cooldown <= 0:
            if self.test_chance(self.get_hit_chance(target) + self.hit_chance_additive):
                damage_dealt = self.deal_damage(target, self.user.get_damage() * self.damage_percentage)
                info = f'**{self.user}** backstabs **{target}** and deals **{damage_dealt}** damage.'
            else:
                info = f'**{self.user}** tries to backstab **{target}** and **misses**.'
            self.cooldown = self.max_cooldown
            return info, True
        else:
            info = f'`{self.name}` is on cooldown for `{self.cooldown}` more turns.'
            return info, False

class TripleStrike(Skill):
    name = 'triplestrike'
    targetable = 2
    max_cooldown = 4
    damage_type = 'physical'
    hit_chance_additive = -0.2
    hit_count = 3
    requirements = {
        'dexterity': Modifier('dexterity', 13)
    }

    def get_description(self):
        description = (
            'A fury of three simultaneous strikes against the target.'
            '\n\n'
            f'`{self.hit_chance_additive:0.2%} Hit Chance`\n'
            f'`{self.hit_count} Hits`'
        )
        return description

    def use(self, target, target_group: list):
        if self.cooldown <= 0:
            hits = []
            miss = 0
            for _ in range(self.hit_count):
                if self.test_chance(self.get_hit_chance(target) + self.hit_chance_additive):
                    hits.append(self.deal_damage(target, self.user.get_damage()))
                else:
                    hits.append('miss')
                    miss += 1
            info = f'**{self.user}** attacks **{target}** with a flurry of strikes, dealing **{", ".join(hits)}** damage.'
            return info, True
        else:
            info = f'`{self.name}` is on cooldown for `{self.cooldown}` more turns.'
            return info, False

class Cleave(Skill):
    name = 'cleave'
    targetable = 2
    max_cooldown = 3
    damage_type = 'physical'
    cleave_damage = 0.3
    requirements = {
        'strength': Modifier('strength', 13)
    }

    def get_description(self):
        description = (
            'A heavy swing hitting surrounding enemies.'
            '\n\n'
            f'`{self.cleave_damage:0.2%} Cleave Damage`'
        )
        return description

    def use(self, target, target_group: list):
        if self.cooldown <= 0:
            target_index = target_group.index(target)
            cleave_targets = []
            if target_index > 0:
                cleave_targets.append(target_group[target_index-1])
            if len(target_group) - 1 > target_index:
                cleave_targets.append(target_group[target_index+1])
            hits = []
            if self.test_chance(self.get_hit_chance(target) + self.hit_chance_additive):
                main_damage = self.deal_damage(target, self.user.get_damage())
                for t in cleave_targets:
                    hits.append(self.deal_damage(t, self.user.get_damage() * self.cleave_damage))
                info = (
                    f'**{self.user}** attacks **{target}** with a cleaving strike, dealing **{main_damage}** damage '
                    f'and cleaving **{", ".join(cleave_targets)}** for **{", ".join(hits)}** damage.'
                )
            else:
                info = f'**{self.user}** attacks **{target}** with a cleaving strike and **misses**.'
            return info, True
        else:
            info = f'`{self.name}` is on cooldown for `{self.cooldown}` more turns.'
            return info, False

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
            self.log = '**{}** placed their hands upon **{}** and healed them by **{}** HP'.format(user.name, target, heal_amount)
            return self.log, True
        else:
            self.log = '**{}** on cooldown for **{}** more turns.'.format(self.name.capitalize(), self.cooldown)
            return self.log, False