import discord
import logging
import asyncio
import random
import math
import re

import adventure as ac

from discord.ext import tasks, commands

logger = logging.getLogger('adventureCog')
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

def is_available():
    async def predicate(ctx):
        adv = ac.Player(ctx.author.id, False)
        adv.load(False)
        if adv.loaded:
            return adv.available
        else:
            return False
    return commands.check(predicate)


class Adventure(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.xpName = 'Essence'
        self.quest_check.start()
        self.activity_change.start()

    async def wait_for_message(self, check, timeout=30.0, delete=True):
        content = None
        try:
            v_message = await self.bot.wait_for('message', timeout=timeout, check=check)
            content = v_message.content
            await asyncio.sleep(0.1)
            await v_message.delete()
        except asyncio.TimeoutError:
            pass
        except discord.Forbidden:
            pass
        finally:
            return content

    async def wait_for_reaction(self, check, timeout=30.0, delete=True):
        emoji = None
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=timeout, check=check)
            emoji = reaction.emoji
            await asyncio.sleep(0.1)
            await reaction.remove(user)
        except asyncio.TimeoutError:
            pass
        except discord.Forbidden:
            pass
        finally:
            return emoji

    async def build_reaction_menu(self, message, reactions: list, clear=True, delete=True):
        try:
            if clear:
                await asyncio.sleep(0.26)
                await message.clear_reactions()
        except discord.Forbidden:
            pass
        for r in reactions:
            await asyncio.sleep(0.26)
            await message.add_reaction(r)

    @commands.command()
    @commands.guild_only()
    async def begin(self, ctx):
        """Begin your adventure!
        Ultimately, the character creator."""
        async def update_message(message):
            creator_embed = discord.Embed(
                title='Character Creator',
                colour=ac.Colour.creationColour,
                description=(
                    'Welcome to the character creator. I will be walking you through '
                    'a few steps to create a new character. At the end if you are not '
                    'pleased with your character, you can scrap them and start over.'
                )
            )
            creator_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            creator_embed.set_footer(text=footer)
            information = (
                f'Name : {name if name else ""}\n'
                f'Race : {race if race else ""}\n'
                f'Class: {clss if clss else ""}'
            )
            creator_embed.add_field(
                name='Current Information',
                value=information
            )
            creator_embed.add_field(
                name='Next Up',
                value=next_up
            )
            if not message:
                message = await ctx.send(embed=creator_embed)
            else:
                await message.edit(embed=creator_embed)
            return message
        server = ac.Server.get_server(ctx.guild.id)
        name = None
        race = None
        clss = None
        timeout_embed = discord.Embed(
            title='Timed Out',
            colour=ac.Colour.errorColour
        )
        in_progress = True
        embed_message = None
        attributes = [0, 0, 0, 0, 0, 0]
        next_up = 'Nothing'
        footer = ''
        while in_progress:
            while not name:
                next_up = (
                    '__**Character Name**__\n'
                    'To set your character name, send a message with your desired name.\n'
                    'Name must only contain alphanumeric characters but spaces are allowed.'
                )
                embed_message = await update_message(embed_message)
                footer = ''
                response = await self.wait_for_message(
                    check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id
                )
                if response:
                    name = re.sub('[ ]{2,}', ' ', response)
                    name = re.sub('[^A-Za-z ]+', '', name)
                    name = name.strip()
                    length = len(name)
                    if length < 3 or length > 20:
                        name = None
                        footer = 'Name must be within 3 and 20 characters'
                else:
                    in_progress = False
                    footer = 'Timed Out'
                    await embed_message.edit(embed=timeout_embed)

            while not race:
                next_up = (
                            '__**Race Selection**__\n'
                            'You will have to choose a race out of the '
                            'following selection below.'
                        )
                embed_message = await update_message(embed_message)
                available_races = ''
                chosen_race = None
                for key, r in ac.Race.race_dict.items():
                    available_races += f'`{key}`: {r}\n'

                race_embed = discord.Embed(
                    title='Available Races',
                    colour=ac.Colour.infoColour,
                    description=available_races
                )
                race_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                race_embed.set_footer(text='Respond with the race you would like to inspect')
                race_message = await ctx.send(embed=race_embed)

                response = await self.wait_for_message(
                    check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id
                )
                if response:
                    response = response.lower()
                    try:
                        chosen_race = ac.Race.get_race(response)
                    except ac.NotFound:
                        await race_message.delete()
                        continue
                else:
                    await race_message.delete()
                    await embed_message.edit(embed=timeout_embed)
                    return

                race_embed.clear_fields()
                race_embed.add_field(
                    name=chosen_race.name,
                    value=f'{chosen_race.description}\n\n__Passive Effect__\n{chosen_race.passive_effect}'
                )
                race_embed.set_footer(text='Press the appropriate reaction if you want this race.')
                await race_message.edit(embed=race_embed)
                await self.build_reaction_menu(race_message, ['✅', '❌'])
                emoji = await self.wait_for_reaction(check=lambda reaction, user: user == ctx.message.author and race_message.id == reaction.message.id)
                if emoji == '✅':
                    race = chosen_race
                await race_message.delete()

            while not clss:
                next_up = (
                            '__**Class Selection**__\n'
                            'You will have to choose a class out of the '
                            'following selection below.'
                        )
                embed_message = await update_message(embed_message)
                available_classes = ''
                chosen_class = None
                for key, c in ac.CharacterClass.class_dict.items():
                    available_classes += f'`{key}`: {c}\n'

                class_embed = discord.Embed(
                    title='Available Classes',
                    colour=ac.Colour.infoColour,
                    description=available_classes
                )

                class_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                class_embed.set_footer(text='Respond with the class you would like to inspect')
                class_message = await ctx.send(embed=class_embed)

                response = await self.wait_for_message(
                    check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id
                )
                if response:
                    try:
                        chosen_class = ac.CharacterClass.get_class(response)
                    except ac.NotFound:
                        await class_message.delete()
                        continue
                else:
                    await class_message.delete()
                    await embed_message.edit(embed=timeout_embed)
                    return

                modifiers_string = (
                    f'Strength: {chosen_class.attribute_bonuses[0]:3.0%}\n'
                    f'Dexterity: {chosen_class.attribute_bonuses[1]:3.0%}\n'
                    f'Constitution: {chosen_class.attribute_bonuses[2]:3.0%}\n'
                    f'Intelligence: {chosen_class.attribute_bonuses[3]:3.0%}\n'
                    f'Wisdom: {chosen_class.attribute_bonuses[4]:3.0%}\n'
                    f'Charisma: {chosen_class.attribute_bonuses[5]:3.0%}\n'
                )

                class_embed.clear_fields()
                class_embed.add_field(
                    name=chosen_class.name,
                    value=f'{chosen_class.description}\n\n__Attribute Modifiers__\n{modifiers_string}'
                )
                class_embed.set_footer(text='Press the appropriate reaction if you want this class.')
                await class_message.edit(embed=class_embed)
                await self.build_reaction_menu(class_message, ['✅', '❌'])
                emoji = await self.wait_for_reaction(check=lambda reaction, user: user == ctx.message.author and class_message.id == reaction.message.id)
                if emoji == '✅':
                    clss = chosen_class
                await class_message.delete()

            if name and race and clss:
                in_progress = False

        next_up = (
            '__**Happy with what you see?**__\n'
            'You will be able to apply 5 attribute points after this process '
            f'by running `{self.bot.CP}profile`.'
        )
        embed_message = await update_message(embed_message)
        await self.build_reaction_menu(embed_message, ['✅', '❌'])
        emoji = await self.wait_for_reaction(check=lambda reaction, user: user == ctx.message.author and embed_message.id == reaction.message.id)
        if emoji == '✅':
            adv = ac.Player(ctx.author.id, load=False)
            if adv.new(name, clss, race, attributes, ctx.guild.id):
                result_embed = discord.Embed(
                    title='Creation Succeeded!',
                    colour=ac.Colour.successColour
                )
                result_embed.set_author(name=adv.name, icon_url=ctx.author.avatar_url)
                result_embed.add_field(
                    name='Where to start',
                    value=(
                        f'You can spend your attribute points by using `{self.bot.CP}profile`. '
                        f'You should also check out `{self.bot.CP}inventory` and `{self.bot.CP}equip` '
                        f'when you get some equipment. As for your first activity, run `{self.bot.CP}quest` '
                        'to get started.'
                    )
                )
                await ctx.author.add_roles(server.adventurer_role, reason='Made an Adventurer')
            else:
                result_embed = discord.Embed(
                    title='You can not have more than one adventurer',
                    colour=ac.Colour.errorColour,
                    description=f'Run `{self.bot.CP}profile delete` to remove your existing character.'
                )
                result_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            await embed_message.edit(embed=result_embed)
        await asyncio.sleep(0.26)
        await embed_message.clear_reactions()

    @commands.group(aliases=['character'])
    async def profile(self, ctx):
        """Get information on your Adventurer"""
        if ctx.invoked_subcommand is None:
            adv = ac.Player(ctx.author.id)
            profile_message = None
            tout = discord.Embed(title='Timed Out', colour=ac.Colour.errorColour)
            first = True
            escape = False

            if not adv.loaded:
                embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=ac.Colour.errorColour,
                                    description='Please contact rex8112#1200 if this is not the case.')
                await ctx.send(embed=embed)
                return

            if isinstance(ctx.channel, discord.DMChannel) or not adv.available:
                escape = True
            while adv.get_unspent_points() > 0 and escape == False:
                embed = discord.Embed(title='You have **{}** unspent attribute points'.format(adv.get_unspent_points()),
                                      colour=ac.Colour.infoColour,
                                      description='What would you like to spend them on?\n'
                                      + f'1. Strength ({adv.strength})\n'
                                      + f'2. Dexterity ({adv.dexterity})\n'
                                      + f'3. Constitution ({adv.constitution})\n'
                                      + f'4. Intelligence ({adv.intelligence})\n'
                                      + f'5. Wisdom ({adv.wisdom})\n'
                                      + f'6. Charisma ({adv.charisma})')
                if profile_message:
                    await profile_message.edit(embed=embed)
                else:
                    profile_message = await ctx.send(embed=embed)
                if first:
                    await asyncio.sleep(0.26)
                    await profile_message.clear_reactions()
                    await asyncio.sleep(0.26)
                    await profile_message.add_reaction('1️⃣')
                    await asyncio.sleep(0.26)
                    await profile_message.add_reaction('2️⃣')
                    await asyncio.sleep(0.26)
                    await profile_message.add_reaction('3️⃣')
                    await asyncio.sleep(0.26)
                    await profile_message.add_reaction('4️⃣')
                    await asyncio.sleep(0.26)
                    await profile_message.add_reaction('5️⃣')
                    await asyncio.sleep(0.26)
                    await profile_message.add_reaction('6️⃣')
                    await asyncio.sleep(0.26)
                    await profile_message.add_reaction('❌')
                    first = False
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=180.0, check=lambda reaction, user: user == ctx.message.author and profile_message.id == reaction.message.id)
                    if str(reaction) == '1️⃣':
                        adv.rawStrength += 1
                    elif str(reaction) == '2️⃣':
                        adv.rawDexterity += 1
                    elif str(reaction) == '3️⃣':
                        adv.rawConstitution += 1
                    elif str(reaction) == '4️⃣':
                        adv.rawIntelligence += 1
                    elif str(reaction) == '5️⃣':
                        adv.rawWisdom += 1
                    elif str(reaction) == '6️⃣':
                        adv.rawCharisma += 1
                    else:
                        escape = True
                    adv.calculate()
                    await reaction.remove(user)
                except asyncio.TimeoutError:
                    await profile_message.edit(embed=tout)
                    await asyncio.sleep(0.26)
                    await profile_message.clear_reactions()
                    return
                finally:
                    adv.calculate()
                    adv.save()

            if profile_message:
                await asyncio.sleep(0.26)
                await profile_message.clear_reactions()
            equipment = []
            for e in [adv.mainhand, adv.offhand, adv.helmet, adv.armor, adv.gloves, adv.boots, adv.trinket]:
                equipment.append(e)
            skill_string = '**{}** Learned skills\nUse `{}skills` for more information.'.format(len(adv.skills), self.bot.CP)

            if adv.available:
                c = ac.Colour.infoColour
                t = '{}'.format(adv.name)
            else:
                c = ac.Colour.errorColour
                t = '{} (Busy)'.format(adv.name)
            embed = discord.Embed(title=t, colour=c,
                                    description='Level **{0.level}** | **{0.race.name}** | **{0.cls.name}**\n**{0.xp}** {1}'.format(adv, self.bot.xpName))
            embed.set_author(name=ctx.author.display_name,
                                icon_url=ctx.author.avatar_url)
            embed.add_field(
                name='Attributes', value='STR: **{0.strength}**\nDEX: **{0.dexterity}**\nCON: **{0.constitution}**\nINT: **{0.intelligence}**\nWIS: **{0.wisdom}**\nCHA: **{0.charisma}**'.format(adv))
            embed.add_field(
                name='Stats', value='Max Health: **{0.maxHealth}**\nWeapon Class: **{1.value}**\nArmor Class: **{2.value}**\nDamage: **{3.value:.0f}**\nUse `{4}profile stats` for more info.'\
                    .format(adv, adv.mods.get('wc'),
                            adv.mods.get('ac'),
                            adv.mods.get('dmg'),
                            self.bot.CP))
            embed.add_field(name='Skills', value=skill_string)
            embed.add_field(
                name='Equipment', value='Main Hand: **{0[0].name}**\nOff Hand: **{0[1].name}**\nHelmet: **{0[2].name}**\nArmor: **{0[3].name}**\nGloves: **{0[4].name}**\nBoots: **{0[5].name}**\nTrinket: **{0[6].name}**'.format(equipment))

            invStr = ''
            for tmp in adv.inventory:
                invStr += '**{}** {}, Level **{}**\n'.format(
                    tmp.getRarity(), tmp.name, tmp.level)
            if invStr == '':
                invStr = 'Nothing'

            embed.add_field(name='Inventory', value=invStr)
            if profile_message:
                await profile_message.edit(embed=embed)
            else:
                await ctx.send(embed=embed)

    @profile.command(name='stats', aliases=['attributes'])
    async def profile_stats(self, ctx):
        """Get a bit more detail about your current stats and attributes"""
        adv = ac.Player(ctx.author.id)
        if not adv.loaded:
            embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=ac.Colour.errorColour,
                                  description='Please contact rex8112#1200 if this is not the case.')
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title=str(
            adv.name), colour=ac.Colour.infoColour, description='Detailed Attributes and Stats')
        embed.add_field(name='Strength: {}'.format(
            adv.strength), value='Base Strength: **{0.rawStrength}**\nInventory Slots: **{0.inventoryCapacity}**'.format(adv))
        embed.add_field(name='Dexterity: {}'.format(
            adv.dexterity), value='Base Dexterity: **{0.rawDexterity}**\nEvasion: **{1:.1f}%**\nCrit Chance: **{2:.1f}%**'.format(
                                    adv, adv.mods.get('evasion', ac.Modifier('evasion', 0)).value,
                                    adv.mods.get('critChance', ac.Modifier('critChance', 0)).value))
        embed.add_field(name='Constitution: {}'.format(adv.constitution),
                        value='Base Constitution: {0.rawConstitution}\nMax Health: **{0.maxHealth}**'.format(adv))
        embed.add_field(name='Intelligence: {}'.format(adv.intelligence),
                        value='Base Intelligence: {0.rawIntelligence}\nSpell Amp: **{1:.1f}%**'.format(adv, adv.mods.get('spellAmp', ac.Modifier('spellAmp', 0)).value))
        embed.add_field(name='Wisdom: {}'.format(adv.wisdom),
                        value='Base Wisdom: {0.rawWisdom}\nOutgoing Heal Amp: **{1:.1f}%**'.format(adv, adv.mods.get('healAmp', ac.Modifier('healAmp', 0)).value))
        embed.add_field(name='Charisma: {}'.format(adv.charisma),
                        value='Base Charisma: {0.rawCharisma}'.format(adv))
        embed.set_author(name=ctx.author.display_name,
                         icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @profile.command(name='delete')
    async def profile_delete(self, ctx):
        """IRREVERSIBLY delete your adventurer"""
        adv = ac.Player(ctx.author.id)
        server = ac.Server.get_server(ctx.guild.id)
        embed = discord.Embed(title='ARE YOU SURE?', colour=ac.Colour.errorColour, description='Deleting your adventure is COMPLETELY irreversible, even for admins. To delete your adventurer, type `{}`'.format(adv.name.upper()))
        abort = discord.Embed(title='Deletion aborted', colour=ac.Colour.errorColour)
        d_message = await ctx.send(embed=embed)
        try:
            value_message = await self.bot.wait_for('message', timeout=30.0, check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)
        except asyncio.TimeoutError:
            await d_message.edit(embed=abort)
        else:
            if value_message.content == adv.name.upper():
                deleted = discord.Embed(title='{} Deleted'.format(adv.name), colour=ac.Colour.errorColour)
                adv.delete()
                await ctx.author.remove_roles(server.adventurer_role, reason='Adventurer Deleted')
                await d_message.edit(embed=deleted)
            else:
                await d_message.edit(embed=abort)

    @commands.command()
    async def equipment(self, ctx):
        """Get your currently equipped gear and info"""
        adv = ac.Player(ctx.author.id)
        if not adv.loaded:
            embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=ac.Colour.errorColour,
                                  description='Please contact rex8112#1200 if this is not the case.')
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title=str(
            adv.name), colour=ac.Colour.infoColour, description='Detailed Equipment Statistics')
        embed.set_author(name=ctx.author.display_name,
                         icon_url=ctx.author.avatar_url)

        embed.add_field(name='Mainhand', value=adv.mainhand.getInfo())
        embed.add_field(name='Offhand', value=adv.offhand.getInfo())
        embed.add_field(name='Helmet', value=adv.helmet.getInfo())
        embed.add_field(name='Armor', value=adv.armor.getInfo())
        embed.add_field(name='Gloves', value=adv.gloves.getInfo())
        embed.add_field(name='Boots', value=adv.boots.getInfo())
        embed.add_field(name='Trinket', value=adv.trinket.getInfo())

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def skills(self, ctx):
        adv = ac.Player(ctx.author.id)
        embed = discord.Embed(title='Skills', colour=ac.Colour.infoColour)
        embed.set_author(name=adv.name, icon_url=ctx.author.avatar_url)
        for s in adv.skills:
            r = ''
            for req in s.requirements.values():
                r += '`{0.display_name}: {0.value}`\n'.format(req)

            if s.targetable == 0:
                t = 'Self'
            elif s.targetable == 1:
                t = 'Allies'
            else:
                t = 'Enemies'

            d = '`Targets: {}`\n{}'.format(t, s.__doc__)
            if r:
                d += '\n**Requirements**\n{}'.format(r)
            embed.add_field(name='__**{}**__'.format(s.name), value=d)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def quest(self, ctx, stages = None):
        """Command to view or starts quests
        If stages is provided, will shortcut the creation process and allow customization in the quantity of stages."""
        rng = ac.Quest()
        if rng.loadActive(ctx.author.id):
            embed = discord.Embed(
                title='**{}** Stage Quest'.format(rng.stages), colour=ac.Colour.infoColour)
            embed.set_author(name=ctx.author.display_name,
                                icon_url=ctx.author.avatar_url)
            embed.set_footer(text='ID = {}'.format(rng.id))
            embed.add_field(name='Current Progress', value='Current Stage: **{}**\nStages Completed: **{}**\nTotal Stages: **{}**'.format(
                rng.stage, rng.stage - 1, rng.stages))

            enemies = ''
            for e in rng.enemies[rng.stage - 1]:
                t = ac.Enemy(e)
                enemies += '**Lv {}** {}\n'.format(t.level, t.name)

            embed.add_field(name='Current Enemies', value=enemies)
            await ctx.send(embed=embed)
        else:
            adv = ac.Player(ctx.author.id)
            if adv.available:
                embed = discord.Embed(
                    title='No Active Quest', colour=ac.Colour.errorColour,
                    description='What level of quest would you like to do?\n1️⃣ 2 Stage Quest\n2️⃣ 6 Stage Quest\n3️⃣ 10 Stage Quest')
            else:
                embed = discord.Embed(
                    title='No Active Quest', colour=ac.Colour.errorColour,
                    description='Can not start a new quest while **{}** is busy.'.format(adv.name))
            embed.set_author(name=ctx.author.display_name,
                                icon_url=ctx.author.avatar_url)
            quest_message = await ctx.send(embed=embed)
            if not adv.available:
                return
            if not stages:
                await quest_message.add_reaction('1️⃣')
                await asyncio.sleep(0.26)
                await quest_message.add_reaction('2️⃣')
                await asyncio.sleep(0.26)
                await quest_message.add_reaction('3️⃣')
                await asyncio.sleep(0.26)
                await quest_message.add_reaction('❌')
                try:
                    reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=lambda reaction, user: reaction.message.id == quest_message.id and user.id == ctx.author.id)
                except asyncio.TimeoutError:
                    await quest_message.clear_reactions()
                    return
                if str(reaction) == '1️⃣':
                    stages = 2
                elif str(reaction) == '2️⃣':
                    stages = 6
                elif str(reaction) == '3️⃣':
                    stages = 10
                else:
                    await asyncio.sleep(0.26)
                    await quest_message.clear_reactions()
                    return
            try:
                if int(stages) > 10:
                    stages = 10
                elif int(stages) < 2:
                    stages = 2
            except ValueError:
                embed = discord.Embed(title=f'{stages} is not a number.', colour=ac.Colour.errorColour)
                await ctx.send(embed=embed)
                return
            rng.new(ctx.author.id, int(stages))

            embed = discord.Embed(title='{} STAGE QUEST GENERATED'.format(stages),
                                    colour=ac.Colour.creationColour)
            embed.set_author(name=ctx.author.display_name,
                            icon_url=ctx.author.avatar_url)

            enemies = ''
            for e in rng.enemies[rng.stage - 1]:
                t = ac.Enemy(e)
                enemies += '**Lv {}**, {}\n'.format(t.level, t.name)

            embed.add_field(name='Current Enemies', value=enemies)
            await quest_message.edit(embed=embed)
            await asyncio.sleep(0.26)
            await quest_message.clear_reactions()

    @commands.command()
    @commands.guild_only()
    @is_available()
    async def shop(self, ctx):
        """Opens a shop menu"""
        adv = ac.Player(ctx.author.id)
        adv.available = False
        adv.save()
        shop = ac.Shop(adv)
        mainExit = False

        embed = discord.Embed(title='Generating Shop',
                              colour=ac.Colour.creationColour)
        timeoutEmbed = discord.Embed(
            title='Timed Out', colour=ac.Colour.errorColour)
        timeoutEmbed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        goodbyeEmbed = discord.Embed(title='Goodbye {}'.format(
            adv.name), colour=ac.Colour.infoColour)
        goodbyeEmbed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        shopMessage = await ctx.send(embed=embed)
        await asyncio.sleep(0.5)
        while mainExit == False:
            embed = discord.Embed(title='The Innkeeper\'s Shop', colour=ac.Colour.activeColour,
                                  description='Welcome {},\nWhat brings you here today?'.format(adv.name))
            embed.set_author(name=ctx.author.display_name,
                             icon_url=ctx.author.avatar_url)
            embed.add_field(name='1. Potion of Peritia (Level Up)',
                            value='A fine concoction, my own recipe in fact. It will permanently boost the magnitude of your abilities. Some might even call it, a level up, perhaps.')
            embed.add_field(name='2. Purchase Equipment',
                            value='Choose from a variety of my wares, at least, wares I find fitting for you.')
            embed.add_field(name='3. Buyback Equipment',
                            value='Accidentally sell something you did not want to sell? Buy it back here.')
            embed.add_field(name='4. Sell Equipment',
                            value='I will buy some equipment from you, if you no longer want it.')
            embed.set_footer(text='Shop Refresh at: {}'.format(shop.refresh.strftime('%H:%M')))
            await shopMessage.edit(embed=embed)
            await asyncio.sleep(0.26)
            await shopMessage.clear_reactions()
            await asyncio.sleep(0.26)
            await shopMessage.add_reaction('1️⃣')
            await asyncio.sleep(0.26)
            await shopMessage.add_reaction('2️⃣')
            await asyncio.sleep(0.26)
            await shopMessage.add_reaction('3️⃣')
            await asyncio.sleep(0.26)
            await shopMessage.add_reaction('4️⃣')
            await asyncio.sleep(0.26)
            await shopMessage.add_reaction('❌')
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=180.0, check=lambda reaction, user: user == ctx.message.author and shopMessage.id == reaction.message.id)

            except asyncio.TimeoutError:
                mainExit = True
                await shopMessage.edit(embed=timeoutEmbed)
                await asyncio.sleep(0.26)
                await shopMessage.clear_reactions()

            else:
                if str(reaction) == '1️⃣':  # Looking at a Potion of Peritia
                    xp_to_level = adv.getXPToLevel()
                    embed = discord.Embed(title='Potion of Peritia', colour=ac.Colour.infoColour,
                                          description='Interested in more power, {}? It will come with a cost.'.format(adv.name))
                    embed.set_author(name=ctx.author.display_name,
                                     icon_url=ctx.author.avatar_url)
                    if math.isinf(xp_to_level):
                        embed.add_field(name='Cost to Purchase', value='Infinite {}'.format(self.bot.xpName))
                    else:
                        embed.add_field(name='Cost to Purchase', value='{} {}'.format(
                            xp_to_level, self.bot.xpName))
                    embed.add_field(name='Current {}'.format(
                        self.bot.xpName), value=str(adv.xp))
                    await shopMessage.edit(embed=embed)
                    await asyncio.sleep(0.26)
                    await shopMessage.clear_reactions()
                    await asyncio.sleep(0.26)

                    if adv.xp >= xp_to_level:
                        await shopMessage.add_reaction('✅')
                        await asyncio.sleep(0.26)
                    await shopMessage.add_reaction('❌')

                    try:
                        reaction, _ = await self.bot.wait_for('reaction_add', timeout=180.0, check=lambda reaction, user: user == ctx.message.author and shopMessage.id == reaction.message.id)
                    except asyncio.TimeoutError:
                        mainExit = True
                        await shopMessage.edit(embed=timeoutEmbed)
                        await asyncio.sleep(0.26)
                        await shopMessage.clear_reactions()
                    else:
                        if str(reaction) == '✅':  # If purchase is accepted
                            if adv.addLevel():  # If adding a level was successful
                                embed = discord.Embed(title='Level Up!', colour=ac.Colour.successColour,
                                                      description='**Congratulations!**\nYou have achieved level **{}**!\nDo not forget to choose a skill point.'.format(adv.level))
                                embed.set_author(
                                    name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                                embed.set_footer(
                                    text='To spend your skill point, use the {}profile command'.format(self.bot.CP))
                            else:
                                embed = discord.Embed(title='Insufficient {}'.format(
                                    self.bot.xpName), colour=ac.Colour.errorColour)
                                embed.set_author(
                                    name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

                            await shopMessage.edit(embed=embed)
                            await asyncio.sleep(3)
                        else:  # Cancel
                            pass

                elif str(reaction) == '2️⃣':  # Purchase Equipment
                    buy_embed = discord.Embed(title='Buying Equipment', colour=ac.Colour.activeColour,
                                          description='Due to limitation, you will have to respond, in a message, with the item you wish to buy. Use `0` to go back.')
                    buy_embed.set_footer(text='You have 3 minutes to respond.')
                    for number, i in enumerate(shop.inventory, start=1):
                        buy_embed.add_field(name=f'**{number}.** {i.get_name()}', value='Buying Cost: **{}** {}'.format(i.price, self.bot.xpName))

                    buyExit = False
                    while buyExit == False:
                        await shopMessage.edit(embed=buy_embed)
                        await asyncio.sleep(0.26)
                        await shopMessage.clear_reactions()
                        try:
                            vMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
                        except asyncio.TimeoutError:
                            buyExit = True
                            mainExit = True
                            buy_embed.colour = ac.Colour.infoColour
                            buy_embed.set_footer(text='')
                            await shopMessage.edit(embed=buy_embed)
                            await asyncio.sleep(0.26)
                            await shopMessage.clear_reactions()
                        else:
                            try:
                                if int(vMessage.content) < 1:
                                    raise(InterruptedError)
                                index = int(vMessage.content) - 1
                                e = shop.inventory[index]
                            except IndexError as e:
                                pass
                            except (InterruptedError, ValueError):
                                buyExit = True
                            else:
                                embed = discord.Embed(title='{} {}'.format(e.getRarity(), e.name), 
                                                      colour=ac.Colour.infoColour, 
                                                      description=e.getInfo(compare_equipment=adv.get_equipment_from_slot(e.slot)))
                                await shopMessage.edit(embed=embed)
                                await asyncio.sleep(0.26)
                                await shopMessage.add_reaction('✅')
                                await asyncio.sleep(0.26)
                                await shopMessage.add_reaction('❌')
                                try:
                                    reaction, _ = await self.bot.wait_for('reaction_add', timeout=180.0, check=lambda reaction, user: user == ctx.message.author and shopMessage.id == reaction.message.id)
                                except asyncio.TimeoutError:
                                    mainExit = True
                                    buyExit = True
                                    await shopMessage.edit(embed=timeoutEmbed)
                                    await asyncio.sleep(0.26)
                                    await shopMessage.clear_reactions()
                                else:
                                    if str(reaction) == '✅':
                                        shop.buy(index)
                                        shop.save()
                                        adv.save()
                                        buyExit = True
                            finally:
                                await vMessage.delete()
                                
                elif str(reaction) == '3️⃣': # Buyback Equipment
                    buy_embed = discord.Embed(title='Buying Equipment', colour=ac.Colour.activeColour,
                                          description='Due to limitation, you will have to respond, in a message, with the item you wish to buy. Use `0` to go back.')
                    buy_embed.set_footer(text='You have 3 minutes to respond.')
                    for number, i in enumerate(shop.buyback, start=1):
                        buy_embed.add_field(name=f'**{number}.** {i.get_name()}', value='Buying Cost: **{}** {}'.format(i.price, self.bot.xpName))

                    buyExit = False
                    while buyExit == False:
                        await shopMessage.edit(embed=buy_embed)
                        await asyncio.sleep(0.26)
                        await shopMessage.clear_reactions()
                        try:
                            vMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
                        except asyncio.TimeoutError:
                            buyExit = True
                            mainExit = True
                            buy_embed.colour = ac.Colour.infoColour
                            buy_embed.set_footer(text='')
                            await shopMessage.edit(embed=buy_embed)
                            await asyncio.sleep(0.26)
                            await shopMessage.clear_reactions()
                        else:
                            try:
                                if int(vMessage.content) < 1:
                                    raise(InterruptedError)
                                index = int(vMessage.content) - 1
                                e = shop.buyback[index]
                            except IndexError as e:
                                pass
                            except (InterruptedError, ValueError):
                                buyExit = True
                            else:
                                embed = discord.Embed(title='{} {}'.format(e.getRarity(), e.name),
                                                      colour=ac.Colour.infoColour, 
                                                      description=e.getInfo())
                                await shopMessage.edit(embed=embed)
                                await shopMessage.add_reaction('✅')
                                await asyncio.sleep(0.26)
                                await shopMessage.add_reaction('❌')
                                try:
                                    reaction, _ = await self.bot.wait_for('reaction_add', timeout=180.0, check=lambda reaction, user: user == ctx.message.author and shopMessage.id == reaction.message.id)
                                except asyncio.TimeoutError:
                                    mainExit = True
                                    buyExit = True
                                    await shopMessage.edit(embed=timeoutEmbed)
                                    await asyncio.sleep(0.26)
                                    await shopMessage.clear_reactions()
                                else:
                                    if str(reaction) == '✅':
                                        shop.buyB(index)
                                        shop.save()
                                        adv.save()
                                        buyExit = True
                            finally:
                                await vMessage.delete()

                elif str(reaction) == '4️⃣':  # Sell Equipment
                    embed = discord.Embed(title='Selling Equipment', colour=ac.Colour.activeColour,
                                          description='Due to limitation, you will have to respond, in a message, with the item you wish to sell. You must use `0` to go back.')
                    embed.set_footer(text='You have 3 minutes to respond.')
                    await asyncio.sleep(0.26)
                    await shopMessage.clear_reactions()

                    sellExit = False
                    while sellExit == False:
                        embed.clear_fields()
                        for number, e in enumerate(adv.inventory, start=1):
                            if not e.requirements.get('unsellable', False):
                                embed.add_field(name=f'**{number}.** {e.get_name()}', value='Selling Cost: **{}** {}'.format(e.sell_price, self.bot.xpName))
                        await shopMessage.edit(embed=embed)
                        try:
                            vMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
                        except asyncio.TimeoutError:
                            sellExit = True
                            mainExit = True
                            embed.colour = ac.Colour.infoColour
                            embed.set_footer(text='')
                            await shopMessage.edit(embed=embed)
                            await asyncio.sleep(0.26)
                            await shopMessage.clear_reactions()
                        else:
                            try:
                                if int(vMessage.content) < 1:
                                    raise(InterruptedError)
                                num = int(vMessage.content) - 1
                            except IndexError as e:
                                pass
                            except (InterruptedError, ValueError):
                                sellExit = True
                            else:
                                # In case they type in a number that wasn't listed, which happens to be one of their equipments
                                if not e.requirements.get('unsellable', False):
                                    shop.sell(num)
                                    shop.save()
                                    adv.save()
                                    
                            finally:
                                await vMessage.delete()

                elif str(reaction) == '❌':
                    mainExit = True
                    await shopMessage.edit(embed=goodbyeEmbed)
                    await asyncio.sleep(0.26)
                    await shopMessage.clear_reactions()

            finally:  # No matter what, adventurer should be set available again and saved.
                adv.available = True
                adv.save()

    @commands.group()
    @commands.guild_only()
    @is_available()
    async def raid(self, ctx):
        """Host a raid"""
        timeoutEmbed = discord.Embed(
            title='Timed Out', colour=ac.Colour.errorColour)
        timeoutEmbed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        raids = ac.db.get_raids()
        server = ac.Server.get_server(ctx.guild.id)
        embed = discord.Embed(title='Available Raids', colour=ac.Colour.infoColour,
                              description='There are no restrictions, choose wisely or death is certain.')
        embed.set_footer(text='Send the *index* number of the raid you wish to do.')
        count = 0
        for raid in raids:
            count += 1
            embed.add_field(name='Index: **{}**'.format(count), value='__**{}**__\nLevel {}\n{}'.format(raid[1],raid[2],raid[3]))
        setup_message = await ctx.send(embed=embed)
        try:
            vMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
        except asyncio.TimeoutError:
            return
        await vMessage.delete()
        num = int(vMessage.content) - 1
        if num > -1:
            try:
                selected_raid = raids[num]
            except IndexError:
                embed.set_footer(text='')
                await setup_message.edit(embed=embed)
                return
        else:
            return
        adventurer = ac.Player(ctx.author.id)
        players = [adventurer]
        joinable = True

        await setup_message.add_reaction('✅')
        while joinable:
            players_string = ''
            for adv in players:
                players_string += '**{0.name}**, Level: {0.level}\n'.format(adv)

            embed = discord.Embed(title='Raid: {}'.format(selected_raid[1]), colour=ac.Colour.infoColour,
                                description='Level **{0[2]}**\n{0[3]}'.format(selected_raid))
            embed.add_field(name='Raid is Joinable', value='Join by reacting below with ✅.\nOnce you join, you can not leave.\nRaid will close 15 seconds after the last join.')
            embed.add_field(name='Current Adventurers', value=players_string)
            await setup_message.edit(embed=embed)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0,
                                                            check = lambda reaction, user: reaction.message.id == setup_message.id and str(reaction) == '✅')
            except asyncio.TimeoutError:
                joinable = False
            else:
                tmp = ac.Player(user.id)
                valid = True
                for p in players:
                    if tmp.id == p.id or not tmp.available:
                        valid = False
                if valid and tmp.loaded:
                    players.append(tmp)
                    if len(players) >= 5:
                        joinable = False
                await reaction.remove(user)
        embed.clear_fields()
        embed.add_field(name='Raid is now closed', value='To begin the raid, the host must react with ✅ to begin or ❌ to cancel.')
        embed.add_field(name='Current Adventurers', value=players_string)
        await setup_message.edit(embed=embed)
        await setup_message.add_reaction('❌')
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=180.0,
                                                        check = lambda reaction, user: reaction.message.id == setup_message.id and user.id == ctx.author.id)
        except asyncio.TimeoutError:
            await setup_message.edit(embed=timeoutEmbed)
            await asyncio.sleep(0.26)
            await setup_message.clear_reactions()
            return
        else:
            if str(reaction) == '✅':
                try:
                    category = server.category if server else None
                    name = 'Raid_'
                    mentions = ''
                    ids = []
                    overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False)}

                    for p in players:
                        p.load()
                        p.available = False
                        p.save()
                        name += p.name[0]
                        ids.append(p.id)
                        member = ctx.guild.get_member(p.id)
                        mentions += member.mention
                        overwrites[member] = discord.PermissionOverwrite(view_channel = True)

                    raid = ac.Raid(players, selected_raid[0])
                    raid.build_encounter()
                    await asyncio.sleep(0.26)
                    await setup_message.clear_reactions()
                    if category:
                        raid_channel = await category.create_text_channel(name, overwrites=overwrites, reason='For Raid')
                    else:
                        raid_channel = await ctx.guild.create_text_channel(name, overwrites=overwrites, reason='For Raid')
                    ac.db.add_raid_channel(raid_channel.id, raid_channel.guild.id, '|'.join(str(e) for e in ids))
                    raid_message = await raid_channel.send(content=mentions)
                    await setup_message.edit(embed = discord.Embed(title='{} Raid In Progress'.format(selected_raid[1]), description='[Raid Channel](https://discordapp.com/channels/{}/{})'.format(ctx.guild.id, raid_channel.id),
                                                                   colour=ac.Colour.infoColour))
                    winner = await raid.encounter.run_combat(self.bot, raid_message)
                    if winner == 1: # 1 signifies player wins
                        await raid_message.add_reaction('✅')
                        for loot in raid.loot:
                            loot_rolls = {}
                            loot_list = ''
                            for l in raid.loot:
                                if l is loot:
                                    loot_list += f'__{l.get_name()}__\n'
                                else:
                                    loot_list += f'{l.get_name()}\n'
                            embed = discord.Embed(title='Loot', colour=ac.Colour.get_rarity_colour(loot.rarity), description=loot_list)
                            embed.set_footer(text='If you roll a 0 then your inventory is full')
                            loot_escape = False
                            while loot_escape == False:
                                loot_rolls_string = ''
                                for key, value in loot_rolls.items():
                                    roller = next(x for x in raid.players if x.id == key)
                                    loot_rolls_string += '{}: {}\n'.format(roller.name, value)
                                if loot_rolls_string == '':
                                    loot_rolls_string = 'None'

                                embed.clear_fields()
                                embed.add_field(name='Loot Information', value=loot.getInfo())
                                embed.add_field(name='Loot Rolls', value=loot_rolls_string)
                                await raid_message.edit(embed=embed)
                                try:
                                    reaction, user = await self.bot.wait_for('reaction_add', timeout=10.0,
                                                                                check=lambda reaction, user: reaction.message.id == raid_message.id)
                                except asyncio.TimeoutError:
                                    loot_escape = True
                                else:
                                    if str(reaction) == '✅' and user.id in [int(x) for x in raid.players] and user.id not in loot_rolls:
                                        t = next(x for x in raid.players if x.id == user.id)
                                        if len(t.inventory) < t.inventoryCapacity:
                                            loot_rolls[user.id] = random.randint(1, 100)
                                        else:
                                            loot_rolls[user.id] = 0
                                finally:
                                    await reaction.remove(user)
                            sorted_rolls = sorted(loot_rolls, key=loot_rolls.__getitem__, reverse=True)
                            try:
                                loot_winner = next(x for x in raid.players if x.id == sorted_rolls[0])
                                if not loot_winner.addInv(loot):
                                    loot.delete()
                            except IndexError:
                                pass
                        raid.finish_encounter(True)
                    else:
                        raid.finish_encounter(False)
                    embed = discord.Embed(title='Raid Over', colour=ac.Colour.errorColour)
                    await raid_message.edit(embed=embed)
                    await setup_message.edit(embed=embed)
                except:
                    logger.error('Error in Raid Host', exc_info=True)
                finally:
                    try:
                        await raid_channel.delete(reason='Raid Finished')
                        ac.db.del_raid_channel(raid_channel.id)
                    except (discord.NotFound, UnboundLocalError):
                        pass
                    for p in players:
                        p.available = True
                        p.save()
            else:
                cancel_embed = discord.Embed(title='Raid Canceled', colour=ac.Colour.errorColour)
                await setup_message.edit(embed=cancel_embed)

    @commands.command()
    @commands.guild_only()
    async def talk(self, ctx):
        """Source of various information"""
        adv = ac.Player(ctx.author.id)
        timeoutEmbed = discord.Embed(
            title='Timed Out', colour=ac.Colour.errorColour)
        timeoutEmbed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed = discord.Embed(title='The Innkeeper', colour=ac.Colour.infoColour,
                              description='Hello {},\nHow may I help you today?'.format(adv.name))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.add_field(name='Information Options', value='1️⃣ Quests\n2️⃣ Raids\n3️⃣ Combat\n4️⃣ AC/WC\n5️⃣ Roadmap')
        talk_message = await ctx.send(embed=embed)
        await talk_message.add_reaction('1️⃣')
        await asyncio.sleep(0.26)
        await talk_message.add_reaction('2️⃣')
        await asyncio.sleep(0.26)
        await talk_message.add_reaction('3️⃣')
        await asyncio.sleep(0.26)
        await talk_message.add_reaction('4️⃣')
        await asyncio.sleep(0.26)
        await talk_message.add_reaction('5️⃣')
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=lambda reaction, user: reaction.message.id == talk_message.id and user.id == ctx.author.id)
        except asyncio.TimeoutError:
            await talk_message.edit(embed=timeoutEmbed)
            await asyncio.sleep(0.26)
            await talk_message.clear_reactions()
            return
        if str(reaction) == '1️⃣':
            name = 'Quests'
            information = ('Quests are the main idle component that I offer. Quests are structured in stages, '
                'each stage consists of a group of enemies that the adventurer must overcome to progress and get loot.\n\n'
                'Each stage takes **{}** seconds to complete. Every minute the time on your quest is checked and progressed.'.format(ac.Quest.stageTime))
        elif str(reaction) == '2️⃣':
            name = 'Raids'
            information = ('Raids, at the moment, are the only active content that I can offer. '
                'Upon hosting a raid, other adventurers have up to fifteen seconds to join your raid '
                'and assist you in defeating the boss. At the end, the loot will be cycled through '
                'and adventurers can opt to roll for the loot and the highest roll will get the item.')
        elif str(reaction) == '3️⃣':
            name = 'Combat'
            information = ('Combat is turn-based with an order that relies on behind-the-scenes initiative rolls. '
                'Adventurers will be confronted with a list of their skills and cooldowns that they may use. '
                'All forms of skill usage should be formatted as `skill #` where `skill` is the listed '
                'name of the skill and `#` is the index of the target -All this information is listed in the combat screen. '
                'It is important to note how your skills are targetted, if your skill should be cast on an enemy then the '
                'index must match that of the enemy. If it targets an ally, then the index must match your ally. In the event '
                'of a self-cast ability, no target is necessary.')
        elif str(reaction) == '4️⃣':
            name = 'Armor and Weapon Class'
            information = ('Armor Class and Weapon Class is used to determine hit chances based on the percent difference. '
                'In an average scenerio, both should be equal which will give you an 80 percent chance to hit with any percent '
                'difference causing that chance to hit to be changed accordingly.')
        elif str(reaction) == '5️⃣':
            name = 'Roadmap'
            information = (
            'Listed by priority.\n'
            '**1. Storage and Player Trading**\n'
            '2. Class and Races\n'
            '3. Status Effects\n'
            '4. Dungeons\n'
            'More to come.')
        else:
            name = 'Not an option'
            information = "I'm not in that big of a mood to talk."
        embed = discord.Embed(title=name, colour=ac.Colour.infoColour, description=information)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await talk_message.edit(embed=embed)
        await asyncio.sleep(0.26)
        await talk_message.clear_reactions()


    @tasks.loop(minutes=1)
    async def quest_check(self):
        await self.bot.wait_until_ready()
        quest_to_update = ac.db.getTimeRNG()
        for q in quest_to_update:
            rng = ac.Quest()
            if rng.loadActive(q[1]):  # If quest loaded successfully
                limiter = 200
                escape = False
                # While enemies or the player exists
                while escape == False and limiter > 0:
                    limiter -= 1
                    escape = await rng.encounter.automatic_turn()

                rng.nextStage()
                rng.save()
                if not rng.active:  # Check if the quest is done
                    mem = self.bot.get_user(rng.adv.id)
                    if rng.stage > rng.stages:
                        embed = discord.Embed(title='Quest Completed', colour=ac.Colour.successColour,
                                              description='{} stage quest completed successfully!\nXP: **{}**'.format(rng.stages, rng.xp))
                        lootStr = ''
                        for l in rng.loot:
                            lootStr += 'Level {0.level} {1} {0.name}\n'.format(l, l.getRarity())
                        if lootStr:
                            embed.add_field(name='Loot', value=lootStr)
                        else:
                            embed.add_field(name='Loot', value='None, try doing more stages at a time.')
                    else:
                        embed = discord.Embed(title='Quest Failed', colour=ac.Colour.errorColour,
                                              description='{} died on stage {}'.format(rng.adv.name, rng.stage))
                    count = 1
                    while '' in rng.combat_log: rng.combat_log.remove('')
                    for info in rng.combat_log:
                        embed.add_field(name='Stage {}'.format(count), value=info)
                        count += 1
                    embed.set_footer(text='DEBUG: Current Characters: {}'.format(len(embed)))
                    await mem.send(embed=embed)

    @quest_check.before_loop
    async def before_questCheck(self):
        await self.bot.wait_until_ready()

    current_activity = None
    @tasks.loop(minutes=5)
    async def activity_change(self):
        amt = len(ac.db.get_all_adventurers())
        activities = [
            discord.Activity(name='an Adventure', type=discord.ActivityType.watching),
            discord.Activity(name='{}help'.format(self.bot.CP), type=discord.ActivityType.listening),
            discord.Activity(name='with Drinks', type=discord.ActivityType.playing),
            discord.Activity(name='the Bard', type=discord.ActivityType.listening),
            discord.Activity(name='{} Brave Souls'.format(amt), type=discord.ActivityType.watching)
        ]
        old_activity = self.current_activity
        while old_activity == self.current_activity:
            self.current_activity = random.choice(activities)
        await self.bot.change_presence(activity=self.current_activity)

    @activity_change.before_loop
    async def before_activity_change(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Adventure(bot))
