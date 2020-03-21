import discord
import random
import asyncio
import logging
import math

from .skills import Skill
from .colour import Colour

logger = logging.getLogger('encounter')
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
                if enemy.pc:
                    enemy_string += ' **HP: {:.1f}**\n'.format(enemy.health)
                else:
                    enemy_string += '\n'
            else:
                enemy_string += '~~{}. Level **{}** {}~~\n'.format(
                    self.enemies.index(enemy) + 1, enemy.level, enemy.name)

        player_string = ''
        for player in self.players:
            if player not in self.deadPlayers:
                player_string += '{}. Level **{}** {}'.format(
                    self.players.index(player) + 1, player.level, player.name)
                if player.pc:
                    player_string += ' **HP: {:.1f}**\n'.format(player.health)
                else:
                    player_string += '\n'
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
        else:
            check.increment_cooldowns()

        if len(self.players) <= len(self.deadPlayers):
            self.winner = 2
            return True
        elif len(self.enemies) <= len(self.deadEnemies):
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
        return False


    def automatic_turn(self):
        for player in self.players:
            if self.enemies[-1:]:
                logger.debug('Living Enemy detected')
                skill = Skill.get_skill('attack')
                skill().use(player, self.enemies[-1], self.enemies)

                # If the enemy is dead, remove him from active enemies
                if self.enemies[-1].health <= 0:
                    self.deadEnemies.append(self.enemies[-1])
                    self.enemies.pop()

        for enemy in self.enemies:
            if self.players[-1:]:
                logger.debug('Living Player detected')
                skill = Skill.get_skill('attack')
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
            try:
                for loot in enemy.inventory:
                    if loot:
                        rawLoot.append(loot)
            except AttributeError:
                pass
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