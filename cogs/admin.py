import discord
import logging
import asyncio
import random
import re

import adventure as ac

from discord.ext import tasks, commands

logger = logging.getLogger('adminCog')
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

def is_admin():
    def predicate(ctx):
        admins = [
            180067685986467840, # Rex8112
            216388852066156544  # Nub
        ]
        return ctx.author.id in admins
    return commands.check(predicate)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=['ap'])
    @is_admin()
    async def adminpanel(self, ctx):
        pass

    @adminpanel.command()
    async def set_available(self, ctx, member: discord.Member, value: bool):
        adv = ac.Player(member.id, False)
        adv.load(False)
        adv.available = value
        adv.save()
        await ctx.message.add_reaction('✅')

    @adminpanel.command()
    async def rest(self, ctx, member: discord.Member):
        adv = ac.Player(member.id)
        adv.rest()
        adv.save()
        await ctx.message.add_reaction('✅')

    @adminpanel.command()
    async def announce(self, ctx, *, content):
        """A bot-wide announcement, used for updates and the like.
        
        Format: Embed Title|Embed Description|Field Title|Field Value
        Fields are repeatable but need both a title and a value."""
        channels = []
        for g in ac.Server.server_cache.values():
            if g.announcement:
                channels.append(g.announcement)
        message = content.split('|')
        embed = discord.Embed(title=message[0], colour=ac.Colour.infoColour, description=message[1])
        for i, x in enumerate(message[2:]):
            if i % 2 != 1:
                try:
                    embed.add_field(name=x, value=message[2+i+1])
                except IndexError:
                    pass
        async with ctx.channel.typing():
            for channel in channels:
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass
            await ctx.message.add_reaction('✅')

    @adminpanel.command()
    async def test_characters(self, ctx):
        try:
            main_description = ''
            for count, a in enumerate(ac.test_players, start=1):
                if a:
                    main_description += '{}. Level {} {} {}, {}\n'.format(a.id, a.level, a.race, a.cls, a.name[6:])
                else:
                    main_description += '{}. None\n'.format(count)
            main_embed = discord.Embed(title='Test Characters', description=discord.utils.escape_markdown(main_description), colour=ac.Colour.activeColour)
            main_embed.set_footer(text='Follow up messages: <new/delete/activate/deactivate>')
            main_message = await ctx.send(embed=main_embed)
            try:
                value_message = await self.bot.wait_for('message', timeout=10.0, check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)
            except asyncio.TimeoutError:
                main_embed.colour = ac.Colour.infoColour
                main_embed.set_footer(text='')
                await main_message.edit(embed=main_embed)
                return
            await value_message.delete()
            if value_message.content.lower() == 'new':
                new_embed = main_embed.copy()
                new_description = new_embed.description
                new_description = '**What slot do you want to create the new adventurer?**\n\n{}'.format(new_description)
                new_embed.title = 'New Test Character'
                new_embed.description = new_description
                new_embed.set_footer(text='Follow up message: <Int: 1-10>')
                await main_message.edit(embed=new_embed)
                value_message = await self.bot.wait_for('message', timeout=30.0, check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)
                await value_message.delete()

                try:
                    slot = int(value_message.content)
                except ValueError:
                    raise discord.InvalidArgument('An integer must be provided')
                if slot > 10 or slot < 1:
                    raise discord.InvalidArgument('Integer must be between 1 and 10, inclusively.')

                new_embed.description = 'What name would you like to give to this test character?'
                new_embed.set_footer(text='Follow up message: <Str: 3-20 Characters>')
                await main_message.edit(embed=new_embed)
                value_message = await self.bot.wait_for('message', timeout=30.0, check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)
                await value_message.delete()

                name = re.sub('([^A-Za-z ]+|[ ]{2,})', ' ', value_message.content.strip())
                length = len(name)
                if length < 3 or length > 20:
                    raise discord.InvalidArgument('Name must be within 3 and 20 characters')
                name = 'test__' + name
                adv_info = 'Name: {}\n'.format(discord.utils.escape_markdown(name))
                new_embed.description = '**What level should this character be?**\n\n{}'.format(adv_info)
                new_embed.set_footer(text='Follow up message: <Int: >= 1>')
                await main_message.edit(embed=new_embed)
                value_message = await self.bot.wait_for('message', timeout=30.0, check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)
                await value_message.delete()
                try:
                    level = int(value_message.content)
                except ValueError:
                    raise discord.InvalidArgument('An integer must be provided')
                if level < 1:
                    raise discord.InvalidArgument('Integer must be greater than or equal to 1')

                old_adv = ac.test_players[slot-1]
                if isinstance(old_adv, ac.Player):
                    old_adv.delete()
                adv = ac.Player(slot, False)
                adv.new(name, 'Adventurer', 'Human', [10, 10, 10, 10, 10, 10], ctx.guild.id)
                adv.level = level
                adv.save()
                ac.test_players[slot-1] = adv
                new_embed.description = '**{}** Created Successfully'.format(discord.utils.escape_markdown(name))
                new_embed.set_footer(text='')
                new_embed.colour = ac.Colour.successColour
                await main_message.edit(embed=new_embed)
            elif value_message.content.lower() == 'delete':
                new_embed = main_embed.copy()
                new_description = new_embed.description
                new_description = '**What slot do you want to delete?**\n\n{}'.format(new_description)
                new_embed.title = 'Delete Test Character'
                new_embed.description = new_description
                new_embed.set_footer(text='Follow up message: <Int: 1-10>')
                await main_message.edit(embed=new_embed)
                value_message = await self.bot.wait_for('message', timeout=30.0, check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)
                await value_message.delete()
                try:
                    slot = int(value_message.content)
                except ValueError:
                    raise discord.InvalidArgument('An integer must be provided')
                if slot > 10 or slot < 1:
                    raise discord.InvalidArgument('Integer must be between 1 and 10, inclusively.')

                adv = ac.test_players[slot-1]
                adv.delete()
                ac.test_players[slot-1] = None

                new_embed.description = '**{}** Deleted Successfully'.format(discord.utils.escape_markdown(adv.name))
                new_embed.set_footer(text='')
                new_embed.colour = ac.Colour.successColour
                await main_message.edit(embed=new_embed)
            elif value_message.content.lower() == 'activate':
                new_embed = main_embed.copy()
                new_description = new_embed.description
                new_description = '**What slot do you want to activate?**\n\n{}'.format(new_description)
                new_embed.title = 'Activate Test Character'
                new_embed.description = new_description
                new_embed.set_footer(text='Follow up message: <Int: 1-10>')
                await main_message.edit(embed=new_embed)
                value_message = await self.bot.wait_for('message', timeout=30.0, check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)
                await value_message.delete()
                try:
                    slot = int(value_message.content)
                except ValueError:
                    raise discord.InvalidArgument('An integer must be provided')
                if slot > 10 or slot < 1:
                    raise discord.InvalidArgument('Integer must be between 1 and 10, inclusively.')
                ac.TestData.active_test_players[ctx.author.id] = slot
                adv = ac.Player(slot)
                new_embed.description = '**{}** Activated Successfully'.format(discord.utils.escape_markdown(adv.name))
                new_embed.set_footer(text='')
                new_embed.colour = ac.Colour.successColour
                await main_message.edit(embed=new_embed)
            elif value_message.content.lower() == 'deactivate':
                ac.TestData.active_test_players.pop(ctx.author.id, None)
                main_embed.title = 'Deactivation'
                main_embed.description = 'Deactivated Successfully'
                main_embed.set_footer(text='')
                main_embed.colour = ac.Colour.successColour
                await main_message.edit(embed=main_embed)
            else:
                main_embed.colour = ac.Colour.infoColour
                main_embed.set_footer(text='Invalid Follow Up')
                await main_message.edit(embed=main_embed)

        except (discord.InvalidArgument, asyncio.TimeoutError) as e:
            error_embed = main_message.embeds[0]
            error_embed.colour = ac.Colour.errorColour
            error_embed.set_footer(text='{}: {}'.format(type(e).__name__, e))
            await main_message.edit(embed=error_embed)




    @adminpanel.command()
    async def generate_equipment(self, ctx, target_id: int, lvl: int, rarity: int, index = 0):
        adv = ac.Player(target_id)
        if not adv.loaded:
            await ctx.message.add_reaction('⛔')
            return
        e = ac.Equipment(0)
        e.generate_new(lvl, rarity, index=index)
        embed = discord.Embed(title='Loot Generated: {}'.format(e.name), colour=ac.Colour.creationColour,
                              description=e.getInfo())
        message = await ctx.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=180.0, check=lambda reaction, user: user.id == ctx.author.id and reaction.message.id == message.id)
            if str(reaction) == '✅':
                adv.addInv(e)
                adv.save()
                await message.edit(embed=discord.Embed(title='Equipment Given', colour=ac.Colour.successColour))
        except asyncio.TimeoutError:
            pass
        finally:
            try:
                await message.clear_reactions()
            except discord.Forbidden:
                pass

    @adminpanel.command()
    async def show_base_equipment(self, ctx, ID: int):
        base = ac.BaseEquipment(ID)
        lowest = ac.Equipment(0)
        highest = ac.Equipment(0)
        lowest.generate_new(base.min_level, 0, ID)
        highest.generate_new(base.max_level, 0, ID)
        embed = discord.Embed(title='Lvl {} to {}, {}'.format(base.min_level, base.max_level, base.name), colour=ac.Colour.infoColour, description=base.flavor)
        embed.set_footer(text='ID: {}'.format(ID))
        embed.add_field(name='Rarity Info', value='Min Rarity: {}\nMax Rarity: {}'.format(base.starting_rarity, base.max_rarity))
        starting_string = ''
        
        low_min, low_max = lowest.process_mod_string_min_max(base.starting_mod_string)
        high_min, high_max = highest.process_mod_string_min_max(base.starting_mod_string)
        for mod in low_min.values():
            starting_string += '`{}: '.format(mod.id)
            starting_string += '{}-{} / {}-{}`\n'.format(
                mod.value,
                low_max[mod.id].value,
                high_min[mod.id].value,
                high_max[mod.id].value
            )
        embed.add_field(name='Item Mods', value=starting_string)

        random_string = ''
        ran_low_min, ran_low_max = lowest.process_mod_string_min_max(base.random_mod_string)
        ran_high_min, ran_high_max = highest.process_mod_string_min_max(base.random_mod_string)
        for mod in ran_low_min.values():
            random_string += '`{}: '.format(mod.id)
            random_string += '{}-{} / {}-{}`\n'.format(
                mod.value,
                ran_low_max[mod.id].value,
                ran_high_min[mod.id].value,
                ran_high_max[mod.id].value
            )
        embed.add_field(name='Rarity Mods', value=random_string)

        if base.requirement_string:
            requirement_string = ''
            req_low = lowest.process_requirement_string(base.requirement_string)
            req_high = highest.process_requirement_string(base.requirement_string)
            for req in req_low.values():
                requirement_string += '`{}: '.format(req.id)
                requirement_string += '{} / {}`\n'.format(
                    req.value,
                    req_high[req.id].value
                )
            embed.add_field(name='Requirements', value=requirement_string)
        await ctx.send(embed=embed)

    @adminpanel.command()
    async def list_all_equipment(self, ctx, page=1):
        offset = (page-1)*10
        all_data = ac.db.get_all_base_equipment()
        trimmed_data = all_data[offset:offset+9]
        embed = discord.Embed(title=f'Base Equipment {offset} - {offset+9}', colour=ac.Colour.infoColour)
        embed.set_author(name=ctx.author.display_name,
                         icon_url=ctx.author.avatar_url)
        for data in trimmed_data:
            title = f'**{data["indx"]}.** {data["name"]}'
            desc = (
                f'Level: `{data["minLevel"]}-{data["maxLevel"]}`\n'
                f'Slot: `{data["slot"]}`\n'
                f'Skills: `{data["skills"]}`\n'
                f'In Quests: `{bool(data["rng"])}`'
            )
            embed.add_field(name=title, value=desc, inline=False)
        await ctx.send(embed=embed)

    @adminpanel.command()
    async def test_hit_chance(self, ctx, wc: float, ac_: float):
        chanceToHit = float(1 + (wc - ac_) /
                ((wc + ac_) * 0.5)) - 0.2
        if random.uniform(0.0, 1.0) < chanceToHit:
            succeed = True
        else:
            succeed = False
        embed = discord.Embed(title='{} WC vs {} AC'.format(wc, ac_), colour=ac.Colour.infoColour, description='{:.2%} to hit\nWould succeed? `{}`'.format(chanceToHit, succeed))
        await ctx.send(embed=embed)

    @adminpanel.command()
    async def test_auto_combat(self, ctx, enemies_string, count=100):
        """
        Enemies_string: enemy_id|enemy_level|allow_elite,...
        """
        wins = 0
        losses = 0
        adv = ac.Player(ctx.author.id)
        async with ctx.channel.typing():
            for _ in range(count):
                adv.rest()
                enemies = []
                for e in enemies_string.split(','):
                    enemy_id, enemy_level, allow_elite = e.split('|')
                    enemy = ac.Enemy()
                    if bool(allow_elite):
                        enemy.generate_new_elite(int(enemy_level), True, int(enemy_id))
                    else:
                        enemy.generate_new(int(enemy_level), True, int(enemy_id))
                    enemy.calculate()
                    enemies.append(enemy)
                encounter = ac.Encounter([adv], enemies)

                escape = False
                log = ''
                limiter = 100
                while escape == False and limiter > 0:
                    limiter -= 1
                    escape = await encounter.automatic_turn()
                if encounter.winner == 1:
                    wins += 1
                elif encounter.winner == 2:
                    losses += 1
                else:
                    logger.warning('COMBAT LIMITED')
                if count == 1:
                    log = encounter.log
            if len(log) > 500:
                log = log[-500:]
            average_wins = round(wins/count, 3)
            embed = discord.Embed(title='Results', colour=ac.Colour.infoColour,
                                    description='{}/{}/{}'.format(wins,losses,count)
                                            +' **{}**'.format(average_wins))
            if log:
                embed.add_field(name='Combat Log', value=log)
            await ctx.send(embed=embed)

    @adminpanel.command()
    async def balance_all_equipment(self, ctx):
        all_data = ac.db.get_all_equipment()
        async with ctx.channel.typing():
            counter = 0
            for data in all_data:
                e = ac.Equipment(data['indx'])
                changed = e.balance_check()
                if changed:
                    e.save(database=True)
                    counter += 1
            embed = discord.Embed(title='Balance Check Complete', colour=ac.Colour.successColour,
                                    description='{} Pieces of Equipment Changed'.format(counter))
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.guild_only()
    async def set_action_channels(self, ctx, count: int):
        server = ac.Server(ctx.guild.id, self.bot)
        if count <= 0:
            return
        change = count - len(server.action_channels)
        if change < 0:
            change *= -1
            for _ in range(change):
                await server.delete_action_channel(reason=f'{str(ctx.author)}|Deleted via command')
        elif change > 0:
            for _ in range(change):
                await server.build_action_channel()
        server.save()
        await ctx.message.add_reaction('✅')

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def settings(self, ctx):
        tout = discord.Embed(title='Timed Out', colour=ac.Colour.errorColour)
        author = ctx.author
        guild = ctx.guild
        server = ac.Server.get_server(guild.id)
        settings_embed = discord.Embed(
            title=f'{guild.name} Settings',
            colour=ac.Colour.activeColour
        )
        settings_embed.set_author(name=author.display_name, icon_url=author.avatar_url)
        if server:
            category_string = server.category.mention if server.category else 'None'
            a_string = server.announcement.mention if server.announcement else 'None'
            g_string = server.general.mention if server.general else 'None'
            if server.action_channels:
                act_string = ', '.join(a.mention for a in server.action_channels)
            else:
                act_string = 'None'
            channels = (
                f'Category: {category_string}\n'
                f'Announcement Channel: {a_string}\n'
                f'General Chat Channel: {g_string}\n'
                f'Action Channels: {act_string}'
            )
            settings_embed.add_field(name='Linked Channels', value=channels)
            settings_embed.add_field(name='Other Settings', value=f'On Join Message: {server.on_join}')
            await ctx.send(embed=settings_embed)
        else:
            settings_embed.add_field(
                name='Server Setup',
                value=(
                    'You have two options for setting up the server. I can either make '
                    'the channels I need for you ~~or you can tell me what channels I am allowed '
                    'to run out of.~~'
                )
            )
            await ctx.send(embed=settings_embed)
            server = ac.Server(guild.id, self.bot, load=False)
            server.new()
            await server.build_category()
            await server.build_announcement_channel()
            await server.build_general_channel()
            await server.build_action_channel()
            await server.build_adventurer_role()
            server.on_join = True
            server.save()

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def leave_server(self, ctx):
        server = ac.Server(ctx.guild.id, self.bot)
        embed = discord.Embed(
            title='Are you sure you want me to leave?',
            colour=ac.Colour.errorColour,
            description='Leaving will result in my deleting all my channels (Not including current raid channels) and erasing server settings.'
        )
        pending_deletion = ''
        pending_deletion += f'{server.category}\n'
        pending_deletion += f'{server.announcement}\n'
        pending_deletion += f'{server.general}\n'
        for a in server.action_channels:
            pending_deletion += f'{a}\n'
        embed.add_field(
            name='Pending Deletion',
            value=pending_deletion
        )
        confirm_message = await ctx.send(embed=embed)
        await confirm_message.add_reaction('✅')
        await asyncio.sleep(0.26)
        await confirm_message.add_reaction('❌')
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=180.0, check=lambda reaction, user: reaction.message.id == confirm_message.id and user.id == ctx.author.id)
        except asyncio.TimeoutError:
            await confirm_message.clear_reactions()
        else:
            if str(reaction) == '✅':
                try:
                    await server.delete()
                    await ctx.guild.leave()
                except discord.Forbidden:
                    embed = discord.Embed(title='I do not have permission to clear up my channels.', colour=ac.Colour.errorColour)
                    await confirm_message.edit(embed=embed)
            else:
                await asyncio.sleep(0.26)
                await confirm_message.clear_reactions()


def setup(bot):
    bot.add_cog(Admin(bot))
