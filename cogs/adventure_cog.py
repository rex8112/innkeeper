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

    @commands.command()
    @commands.guild_only()
    async def begin(self, ctx):
        """Begin your adventure!
        Ultimately, the character creator."""
        adv = ac.Player(ctx.author.id, False)
        embed = discord.Embed(title='Adventurer Creator', colour=ac.Colour.creationColour,
                              description='Welcome Adventurer!\nBefore you can start your adventurer, I am going to need some new info from you.')
        embed.add_field(name='Needed Information',
                        value='Name:\nStrength:\nDexterity:\nConstitution:\nIntelligence:\nWisdom:\nCharisma:[WIP:Not currently implemented]')
        embed.add_field(name='Next on the list:',
                        value='**Name**\nYour new adventurer is going to need a name. Type it below.')
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text='You have 3 minutes to type your response')
        controlMessage = await ctx.send(embed=embed)
        tout = discord.Embed(title='Timed Out', colour=ac.Colour.errorColour)

        try:
            logger.debug('Waiting for name')
            valueMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: message.author == ctx.author and message.channel == ctx.message.channel)
        except asyncio.TimeoutError:
            await controlMessage.edit(embed=tout)
            logger.warning('Adventure Creator Timed Out')
        else:
            logger.debug('Adventure Creator acquired name!')
            name = re.sub('[ ]{2,}', ' ', valueMessage.content)
            name = re.sub('[^A-Za-z ]+', '', name)
            name = name.strip()
            length = len(name)
            if length < 3 or length > 20:
                embed = discord.Embed(title='Name must be 3-20 characters long.',
                                      colour=ac.Colour.errorColour)
                await controlMessage.edit(embed=embed)
                return

            await valueMessage.delete()
            cont = False

            while not cont:

                embed = discord.Embed(title='Adventurer Creator', colour=ac.Colour.creationColour,
                                      description='Welcome Adventurer!\nBefore you can start your adventurer, I am going to need some new info from you.')
                embed.add_field(name='Needed Information',
                                value='Name: {}\nStrength:\nDexterity:\nConstitution:\n~~Intelligence:\nWisdom:\nCharisma:\n~~[WIP:Currently Unused But Required]'.format(name))
                embed.add_field(name='Next on the list:',
                                value='**Attributes**\nBy default, you have 10 in every attribute but we are going to change that. You have **5** points to spend. \
                          You will gain a point per level up, do not worry.\n**Formatting**\nFor this information, I am going to need you to put the points \
                            you want in the format listed below, the order matters and is the same as listed above.\n`1 2 2 0 0 0`')
                embed.set_author(name=ctx.author.name,
                                 icon_url=ctx.author.avatar_url)
                embed.set_footer(
                    text='You have 3 minutes to type your response')
                await controlMessage.edit(embed=embed)

                try:
                    logger.debug('Waiting for attributes')
                    valueMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: message.author == ctx.author and message.channel == ctx.channel)
                except asyncio.TimeoutError:
                    cont = True
                    await controlMessage.edit(embed=tout)
                    controlMessage = None
                    logger.warning('Adventure Creator Timed Out')
                else:
                    try:
                        attributes = list(
                            map(int, valueMessage.content.split(' ')))
                    except ValueError:
                        logger.warning('Invalid Response passed to attributes')
                    else:
                        total = 0
                        if len(attributes) > 6:
                            del attributes[6:]
                        elif len(attributes) < 6:
                            for _ in range(6 - len(attributes)):
                                attributes.append(0)

                        for att in attributes:
                            total += att

                        attributes[:] = [x + 10 for x in attributes]

                        if total > 5:
                            await ctx.send(embed=discord.Embed(title='Total number over 5, try again', colour=ac.Colour.errorColour), delete_after=3.0)
                        elif total < 5:
                            await ctx.send(embed=discord.Embed(title='Total number under 5, try again', colour=ac.Colour.errorColour), delete_after=3.0)
                        else:
                            cont = True
                    finally:
                        await valueMessage.delete()

            if controlMessage == None:
                return
            embed = discord.Embed(title='Adventurer Creator', colour=ac.Colour.creationColour,
                                  description='Welcome Adventurer!\nBefore you can start your adventurer, I am going to need some new info from you.')
            embed.add_field(name='Needed Information',
                            value='Name: {0}\nStrength: {1[0]}\nDexterity: {1[1]}\nConstitution: {1[2]}\nIntelligence: {1[3]}\nWisdom: {1[4]}\n~~Charisma: {1[5]}~~\n[WIP:Currently Unused But Required]'.format(name, attributes))
            embed.add_field(name='Next on the list:',
                            value='**ALL DONE!**\nTake a look at the information, is it all to your liking?')
            embed.set_author(name=ctx.author.display_name,
                             icon_url=ctx.author.avatar_url)
            embed.set_footer(text='You have 3 minutes to react your response')
            await controlMessage.edit(embed=embed)
            await controlMessage.add_reaction('✅')
            await asyncio.sleep(0.26)
            await controlMessage.add_reaction('❌')

            try:
                logger.debug('Waiting for confirmation')
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=180.0, check=lambda reaction, user: user == ctx.message.author and controlMessage.id == reaction.message.id)
            except asyncio.TimeoutError:
                await controlMessage.edit(embed=tout)
                await asyncio.sleep(0.26)
                await controlMessage.clear_reactions()
                logger.warning('Adventure Creator Timed Out')
            else:
                if str(reaction) == '✅':
                    # async with controlMessage.channel.typing():
                    if adv.new(name, 'Adventurer', 'Human', attributes, ctx.guild.id):
                        embed = discord.Embed(title='Adventurer Created!',
                                              colour=ac.Colour.successColour, description='Welcome {}!'.format(name))
                        embed.add_field(name='What to do next?', value='To start getting to work, run `{0}quest` to begin your first journey. Use `{0}talk` for various information.'.format(self.bot.CP))
                    else:
                        embed = discord.Embed(title='Adventurer Already Created!', colour=ac.Colour.errorColour,
                                              description='You can not make two!')
                else:
                    embed = discord.Embed(title='Adventurer Scrapped!', colour=ac.Colour.errorColour,
                                          description='Rerun the command to try again')
                await asyncio.sleep(0.26)
                await controlMessage.clear_reactions()
                await controlMessage.edit(embed=embed)

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

            if isinstance(ctx.channel, discord.DMChannel):
                escape = True
            while adv.get_unspent_points() > 0 and escape == False:
                embed = discord.Embed(title='You have **{}** unspent attribute points'.format(adv.get_unspent_points()),
                                      colour=ac.Colour.infoColour,
                                      description='What would you like to spend them on?\n'
                                      + f'1. Strength ({adv.rawStrength})\n'
                                      + f'2. Dexterity ({adv.rawDexterity})\n'
                                      + f'3. Constitution ({adv.rawConstitution})\n'
                                      + f'4. Intelligence ({adv.rawIntelligence})\n'
                                      + f'5. Wisdom ({adv.rawWisdom})\n'
                                      + f'6. Charisma ({adv.rawCharisma})')
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
                                    description='Level **{0.level}** | **{0.race}** | **{0.cls}**\n**{0.xp}** XP'.format(adv))
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
            for i in adv.inventory:
                tmp = ac.Equipment(i)
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

    @commands.command(aliases=['i','inv'])
    async def inventory(self, ctx, slot = 0):
        """Command to view your inventory
        If slot is provided, will show a more detailed view of the item in that slot."""
        adv = ac.Player(ctx.author.id)
        if not adv.loaded:
            embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=ac.Colour.errorColour,
                                description='Please contact rex8112#1200 if this is not the case.')
            await ctx.send(embed=embed)
            return
        if slot == 0:
            embed = discord.Embed(title='{}\'s Inventory'.format(
                adv.name), colour=ac.Colour.infoColour)
            embed.set_author(name=ctx.author.display_name,
                                icon_url=ctx.author.avatar_url)
            embed.set_footer(
                text='Inventory Capacity: {} / {}'.format(len(adv.inventory), adv.inventoryCapacity))
            for count, i in enumerate(adv.inventory, start=1):
                e = ac.Equipment(i)
                embed.add_field(
                    name='Slot **{}**'.format(count), value=e.getInfo(compare_equipment=adv.get_equipment_from_slot(e.slot)))
        else:
            try:
                e = ac.Equipment(adv.inventory[slot-1])
                embed = discord.Embed(title=e.name, colour=ac.Colour.get_rarity_colour(e.rarity), description=e.getInfo(title=False))
            except IndexError:
                embed = discord.Embed(title='Slot Empty', colour=ac.Colour.errorColour, description='Slot {} has no items.'.format(slot))
        await ctx.send(embed=embed)

    @commands.command()
    @is_available()
    async def equip(self, ctx, slot: int):
        """Equip a piece of equipment from your inventory
        Must give the number of the inventory slot the equipment resides in."""
        try:
            adv = ac.Player(ctx.author.id, False)
            adv.load(False)
            if not adv.loaded:
                embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=ac.Colour.errorColour,
                                    description='Please contact rex8112#1200 if this is not the case.')
                await ctx.send(embed=embed)
                return
            if adv.equip(slot-1):
                adv.save()
                await ctx.message.add_reaction('✅')
            else:
                await ctx.message.add_reaction('⛔')
        except (ac.InvalidLevel, ac.InvalidRequirements) as e:
            error_embed = discord.Embed(title='{}'.format(type(e).__name__), colour=ac.Colour.errorColour, description='{}'.format(e))
            await ctx.message.add_reaction('⛔')
            await ctx.send(embed=error_embed)
        except Exception:
            logger.warning('Equipping Failed', exc_info=True)
            await ctx.message.add_reaction('⛔')

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
            if int(stages) > 10:
                stages = 10
            elif int(stages) < 2:
                stages = 2
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
            embed = discord.Embed(title='The Innkeeper\'s Shop', colour=ac.Colour.infoColour,
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
                        buy_embed.add_field(name='{}. {} {}'.format(number, i.getRarity(
                        ), i.name), value='Buying Cost: **{}** {}'.format(i.price, self.bot.xpName))

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
                            except (ValueError, IndexError) as e:
                                pass
                            except InterruptedError:
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
                                        buyExit = True
                            finally:
                                await vMessage.delete()
                                
                elif str(reaction) == '3️⃣': # Buyback Equipment
                    buy_embed = discord.Embed(title='Buying Equipment', colour=ac.Colour.activeColour,
                                          description='Due to limitation, you will have to respond, in a message, with the item you wish to buy. Use `0` to go back.')
                    buy_embed.set_footer(text='You have 3 minutes to respond.')
                    for number, i in enumerate(shop.buyback, start=1):
                        buy_embed.add_field(name='{}. {} {}'.format(number, i.getRarity(),
                            i.name), value='Buying Cost: **{}** {}'.format(i.price, self.bot.xpName))

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
                            except (ValueError, IndexError) as e:
                                pass
                            except InterruptedError:
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
                                        buyExit = True
                            finally:
                                await vMessage.delete()

                elif str(reaction) == '4️⃣':  # Sell Equipment
                    embed = discord.Embed(title='Selling Equipment', colour=ac.Colour.activeColour,
                                          description='Due to limitation, you will have to respond, in a message, with the item you wish to sell. You must use `0` to go cancel.')
                    embed.set_footer(text='You have 3 minutes to respond.')
                    await asyncio.sleep(0.26)
                    await shopMessage.clear_reactions()

                    sellExit = False
                    while sellExit == False:
                        embed.clear_fields()
                        for number, i in enumerate(adv.inventory, start=1):
                            e = ac.Equipment(i)
                            if not e.requirements.get('unsellable', False):
                                embed.add_field(name='{}. {} {}'.format(number, e.getRarity(
                                ), e.name), value='Selling Cost: **{}** {}'.format(e.price, self.bot.xpName))
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
                            except (ValueError, IndexError) as e:
                                pass
                            except InterruptedError:
                                sellExit = True
                            else:
                                # In case they type in a number that wasn't listed, which happens to be one of their equipments
                                if not e.requirements.get('unsellable', False):
                                    shop.sell(num)
                                    shop.save()
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
                    raw_server_data = ac.db.get_server(ctx.guild.id)
                    channel = ctx.guild.get_channel(next(int(e) for e in raw_server_data[7].split('|')))
                    if channel:
                        category = channel.category
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
                    if channel:
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
                                    loot_list += '***{1}* {0.name}**\n'.format(l, l.getRarity())
                                else:
                                    loot_list += '*{1}* {0.name}\n'.format(l, l.getRarity())
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
                                if not loot_winner.addInv(loot.save(database=True)):
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
                'In an average scenerio, Weapon Class should be lower and that difference is used for hit chance; however, '
                'if Weapon Class is higher than the armor class, the percent difference is then used for crit chance as a hit '
                'is already guaranteed.')
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
