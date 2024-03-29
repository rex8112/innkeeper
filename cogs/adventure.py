import discord
import logging
import asyncio
import random

import adventureController as ac
import tools.database as db
from tools.colour import Colour

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
        self.bot.xpName = 'Souls'
        self.quest_check.start()
        self.activity_change.start()

    @commands.command()
    @commands.guild_only()
    async def begin(self, ctx):
        """Begin your adventure!
        Ultimately, the character creator."""
        adv = ac.Player(ctx.author.id, False)
        embed = discord.Embed(title='Adventurer Creator', colour=Colour.creationColour,
                              description='Welcome Adventurer!\nBefore you can start your adventurer, I am going to need some new info from you.')
        embed.add_field(name='Needed Information',
                        value='Name:\nStrength:\nDexterity:\nConstitution:\n~~Intelligence:\nWisdom:\nCharisma:~~[WIP:Currently Unused But Required]')
        embed.add_field(name='Next on the list:',
                        value='**Name**\nYour new adventurer is going to need a name. Type it below.')
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text='You have 3 minutes to type your response')
        controlMessage = await ctx.send(embed=embed)
        tout = discord.Embed(title='Timed Out', colour=Colour.errorColour)

        try:
            logger.debug('Waiting for name')
            valueMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: message.author == ctx.author and message.channel == ctx.message.channel)
        except asyncio.TimeoutError:
            await controlMessage.edit(embed=tout)
            logger.warning('Adventure Creator Timed Out')
        else:
            logger.debug('Adventure Creator acquired name!')
            name = valueMessage.content
            await valueMessage.delete()
            cont = False

            while not cont:

                embed = discord.Embed(title='Adventurer Creator', colour=Colour.creationColour,
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
                            await ctx.send(embed=discord.Embed(title='Total number over 5, try again', colour=Colour.errorColour), delete_after=3.0)
                        elif total < 5:
                            await ctx.send(embed=discord.Embed(title='Total number under 5, try again', colour=Colour.errorColour), delete_after=3.0)
                        else:
                            cont = True
                    finally:
                        await valueMessage.delete()

            if controlMessage == None:
                return
            embed = discord.Embed(title='Adventurer Creator', colour=Colour.creationColour,
                                  description='Welcome Adventurer!\nBefore you can start your adventurer, I am going to need some new info from you.')
            embed.add_field(name='Needed Information',
                            value='Name: {0}\nStrength: {1[0]}\nDexterity: {1[1]}\nConstitution: {1[2]}\n~~Intelligence: {1[3]}\nWisdom: {1[4]}\nCharisma: {1[5]}~~\n[WIP:Currently Unused But Required]'.format(name, attributes))
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
                    if adv.new(name, 'Adventurer', 'Human', attributes):
                        embed = discord.Embed(title='Adventurer Created!',
                                              colour=Colour.successColour, description='Welcome {}!'.format(name))
                    else:
                        embed = discord.Embed(title='Adventurer Already Created!', colour=Colour.errorColour,
                                              description='You can not make two!')
                else:
                    embed = discord.Embed(title='Adventurer Scrapped!', colour=Colour.errorColour,
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
            tout = discord.Embed(title='Timed Out', colour=Colour.errorColour)
            first = True
            escape = False

            if not adv.loaded:
                embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=Colour.errorColour,
                                    description='Please contact rex8112#1200 if this is not the case.')
                await ctx.send(embed=embed)
                return

            while adv.get_unspent_points() > 0 and escape == False:
                embed = discord.Embed(title='You have **{}** unspent attribute points'.format(adv.get_unspent_points()),
                                      colour=Colour.infoColour,
                                      description='What would you like to spend them on?\n'
                                      + '1. Strength\n'
                                      + '2. Dexterity\n'
                                      + '3. Constitution\n'
                                      + '4. Intelligence\n'
                                      + '5. Wisdom\n'
                                      + '6. Charisma')
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
            embed = discord.Embed(title='{}'.format(adv.name), colour=Colour.infoColour,
                                    description='Level **{0.level}** | **{0.race}** | **{0.cls}**\n**{0.xp}** XP'.format(adv))
            embed.set_author(name=ctx.author.display_name,
                                icon_url=ctx.author.avatar_url)
            embed.add_field(
                name='Attributes', value='STR: **{0.strength}**\nDEX: **{0.dexterity}**\nCON: **{0.constitution}**\nINT: **{0.intelligence}**\nWIS: **{0.wisdom}**\nCHA: **{0.charisma}**'.format(adv))
            embed.add_field(
                name='Stats', value='Max Health: **{0.maxHealth}**\nWeapon Class: **{0.wc}**\nArmor Class: **{0.ac}**\nDamage: **{0.dmg:.0f}**\nSpell Amp: **{0.spellAmp:.0%}**'.format(adv))
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

    @profile.command(aliases=['attributes'])
    async def stats(self, ctx):
        """Get a bit more detail about your current stats and attributes"""
        adv = ac.Player(ctx.author.id)
        if not adv.loaded:
            embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=Colour.errorColour,
                                  description='Please contact rex8112#1200 if this is not the case.')
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title=str(
            adv.name), colour=Colour.infoColour, description='Detailed Attributes and Stats')
        embed.add_field(name='Strength: {}'.format(
            adv.strength), value='Base Strength: {0.rawStrength}\nUnarmed Damage: {0.unarmDamage}\nInventory Slots: {0.inventoryCapacity}'.format(adv))
        embed.add_field(name='Dexterity: {}'.format(
            adv.dexterity), value='Base Dexterity: {0.rawDexterity}\nEvasion: {0.evasion:.1%}\nCrit Chance: {0.critChance:.1%}'.format(adv))
        embed.add_field(name='Constitution: {}'.format(adv.constitution),
                        value='Base Constitution: {0.rawConstitution}\nMax Health: {0.maxHealth}'.format(adv))
        embed.add_field(name='Intelligence: {}'.format(adv.intelligence),
                        value='Base Intelligence: {0.rawIntelligence}\nSpell Amplification: {0.spellAmp:.1%}'.format(adv))
        embed.add_field(name='Wisdom: {}'.format(adv.wisdom),
                        value='Base Wisdom: {0.rawWisdom}'.format(adv))
        embed.add_field(name='Charisma: {}'.format(adv.charisma),
                        value='Base Charisma: {0.rawCharisma}'.format(adv))
        embed.set_author(name=ctx.author.display_name,
                         icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def equipment(self, ctx):
        """Get your currently equipped gear and info"""
        adv = ac.Player(ctx.author.id)
        if not adv.loaded:
            embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=Colour.errorColour,
                                  description='Please contact rex8112#1200 if this is not the case.')
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title=str(
            adv.name), colour=Colour.infoColour, description='Detailed Equipment Statistics')
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

    @commands.group()
    async def inventory(self, ctx):
        """Command group to manage your inventory
        If ran with no subcommands, will get your current inventory."""
        if ctx.invoked_subcommand is None:
            adv = ac.Player(ctx.author.id)
            if not adv.loaded:
                embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=Colour.errorColour,
                                    description='Please contact rex8112#1200 if this is not the case.')
                await ctx.send(embed=embed)
                return
            count = 0
            embed = discord.Embed(title='{}\'s Inventory'.format(
                adv.name), colour=Colour.infoColour)
            embed.set_author(name=ctx.author.display_name,
                             icon_url=ctx.author.avatar_url)
            embed.set_footer(
                text='{} / {}'.format(len(adv.inventory), adv.inventoryCapacity))
            for i in adv.inventory:
                e = ac.Equipment(i)
                count += 1
                embed.add_field(
                    name='Slot **{}**'.format(count), value=e.getInfo())

            await ctx.send(embed=embed)

    @inventory.command()
    @is_available()
    async def equip(self, ctx, slot: int):
        """Equip a piece of equipment from your inventory
        Must give the number of the inventory slot the equipment resides in."""
        try:
            adv = ac.Player(ctx.author.id, False)
            adv.load(False)
            if not adv.loaded:
                embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=Colour.errorColour,
                                    description='Please contact rex8112#1200 if this is not the case.')
                await ctx.send(embed=embed)
                return
            if adv.equip(slot):
                adv.save()
                await ctx.message.add_reaction('✅')
            else:
                await ctx.message.add_reaction('⛔')
        except Exception as _:
            logger.warning('Equipping Failed', exc_info=True)
            await ctx.message.add_reaction('⛔')

    @commands.group()
    @commands.guild_only()
    async def quest(self, ctx):
        """Command group to manage quests
        If ran with no subcommands, will output current quest information."""
        if ctx.invoked_subcommand is None:
            rng = ac.RNGDungeon()
            if rng.loadActive(ctx.author.id):
                embed = discord.Embed(
                    title='**{}** Stage Quest'.format(rng.stages), colour=Colour.infoColour)
                embed.set_author(name=ctx.author.display_name,
                                 icon_url=ctx.author.avatar_url)
                embed.set_footer(text='ID = {}'.format(rng.id))
                embed.add_field(name='Current Progress', value='Current Stage: **{}**\nStages Completed: **{}**\nTotal Stages: **{}**'.format(
                    rng.stage, rng.stage - 1, rng.stages))

                enemies = ''
                for e in rng.enemies[rng.stage - 1]:
                    t = ac.Enemy(e)
                    t.load(False)
                    enemies += '**Lv {}** {}\n'.format(t.level, t.name)

                embed.add_field(name='Current Enemies', value=enemies)
            else:
                embed = discord.Embed(
                    title='No Active Quest', colour=Colour.errorColour,
                    description='To start a new quest, run `{}quest start difficulty`. Replace difficulty with either: `easy`, `medium`, or `hard`.'.format(self.bot.CP))
                embed.set_author(name=ctx.author.display_name,
                                 icon_url=ctx.author.avatar_url)

            await ctx.send(embed=embed)

    @quest.command()
    @is_available()
    # Generates a new dungeon based on the inputted difficulty
    async def start(self, ctx, difficulty: str):
        """Generates a new dungeon based on the given difficulty
        Available difficulties: easy, medium, and hard.

        Difficulty increases the amount of stages done in one round while also getting more difficult in the later stages."""
        rng = ac.RNGDungeon()
        rng.new(ctx.author.id, difficulty)

        embed = discord.Embed(title='{} QUEST GENERATED'.format(difficulty.upper(
        )), colour=Colour.creationColour, description='**{}** Stages'.format(rng.stages))
        embed.set_author(name=ctx.author.display_name,
                         icon_url=ctx.author.avatar_url)

        enemies = ''
        for e in rng.enemies[rng.stage - 1]:
            t = ac.Enemy(e)
            t.load(False)
            enemies += '**Lv {}**, {}\n'.format(t.level, t.name)

        embed.add_field(name='Current Enemies', value=enemies)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @is_available()
    async def shop(self, ctx):
        adv = ac.Player(ctx.author.id, False)
        adv.load(False)
        adv.available = False
        adv.save()
        shop = ac.Shop(adv)
        mainExit = False

        embed = discord.Embed(title='Generating Shop',
                              colour=Colour.creationColour)
        timeoutEmbed = discord.Embed(
            title='Timed Out', colour=Colour.errorColour)
        timeoutEmbed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        goodbyeEmbed = discord.Embed(title='Goodbye {}'.format(
            adv.name), colour=Colour.infoColour)
        goodbyeEmbed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        shopMessage = await ctx.send(embed=embed)
        while mainExit == False:
            embed = discord.Embed(title='The Innkeeper\'s Shop', colour=Colour.infoColour,
                                  description='Welcome {},\nWhat brings you here today?'.format(adv.name))
            embed.set_author(name=ctx.author.display_name,
                             icon_url=ctx.author.avatar_url)
            embed.add_field(name='1. Potion of Peritia',
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
                    embed = discord.Embed(title='Potion of Peritia', colour=Colour.infoColour,
                                          description='Interested in more power, {}? It will come with a cost.'.format(adv.name))
                    embed.set_author(name=ctx.author.display_name,
                                     icon_url=ctx.author.avatar_url)
                    embed.add_field(name='Cost to Purchase', value='{} {}'.format(
                        adv.getXPToLevel(), self.bot.xpName))
                    embed.add_field(name='Current {}'.format(
                        self.bot.xpName), value=str(adv.xp))
                    await shopMessage.edit(embed=embed)
                    await asyncio.sleep(0.26)
                    await shopMessage.clear_reactions()
                    await asyncio.sleep(0.26)

                    if adv.xp >= adv.getXPToLevel():
                        await shopMessage.add_reaction('✅')
                        await asyncio.sleep(0.26)

                    await shopMessage.add_reaction('🔙')
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
                                embed = discord.Embed(title='Level Up!', colour=Colour.successColour,
                                                      description='**Congratulations!**\nYou have achieved level **{}**!\nDo not forget to choose a skill point.'.format(adv.level))
                                embed.set_author(
                                    name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                                embed.set_footer(
                                    text='To spend your skill point, use the {}profile command'.format(self.bot.CP))
                            else:
                                embed = discord.Embed(title='Insufficient {}'.format(
                                    self.bot.xpName), colour=Colour.errorColour)
                                embed.set_author(
                                    name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

                            mainExit = True
                            await shopMessage.edit(embed=embed)
                            await asyncio.sleep(0.26)
                            await shopMessage.clear_reactions()

                        elif str(reaction) == '🔙':  # Go back
                            pass  # Pass to return to the main menu

                        else:  # Cancel
                            mainExit = True
                            await shopMessage.edit(embed=goodbyeEmbed)
                            await asyncio.sleep(0.26)
                            await shopMessage.clear_reactions()

                elif str(reaction) == '2️⃣':  # Purchase Equipment
                    buy_embed = discord.Embed(title='Buying Equipment', colour=Colour.infoColour,
                                          description='Due to limitation, you will have to respond, in a message, with the item you wish to buy. Use `0` to go back.')
                    number = 0
                    for i in shop.inventory:
                        number += 1
                        e = ac.Equipment(i)
                        buy_embed.add_field(name='{}. {} {}'.format(number, e.getRarity(
                        ), e.name), value='Buying Cost: **{}** {}'.format(e.price, self.bot.xpName))

                    buyExit = False
                    while buyExit == False:
                        await shopMessage.edit(embed=buy_embed)
                        await asyncio.sleep(0.26)
                        await shopMessage.clear_reactions()
                        try:
                            vMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
                        except asyncio.TimeoutError:
                            await shopMessage.edit(embed=timeoutEmbed)
                            await asyncio.sleep(0.26)
                            await shopMessage.clear_reactions()
                        else:
                            try:
                                if int(vMessage.content) < 1:
                                    raise(InterruptedError)
                                index = int(vMessage.content) - 1
                                num = shop.inventory[index]
                            except (ValueError, IndexError) as e:
                                pass
                            except InterruptedError:
                                buyExit = True
                            else:
                                e = ac.Equipment(num)
                                embed = discord.Embed(title='{} {}'.format(e.getRarity(), e.name),
                                                      colour=Colour.infoColour, 
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
                                        shop.buy(index)
                                        shop.save()
                                        buyExit = True
                            finally:
                                await vMessage.delete()
                                
                elif str(reaction) == '3️⃣': # Buyback Equipment
                    buy_embed = discord.Embed(title='Buying Equipment', colour=Colour.infoColour,
                                          description='Due to limitation, you will have to respond, in a message, with the item you wish to buy. Use `0` to go back.')
                    number = 0
                    for i in shop.buyback:
                        number += 1
                        e = ac.Equipment(i)
                        buy_embed.add_field(name='{}. {} {}'.format(number, e.getRarity(
                        ), e.name), value='Buying Cost: **{}** {}'.format(e.price, self.bot.xpName))

                    buyExit = False
                    while buyExit == False:
                        await shopMessage.edit(embed=buy_embed)
                        await asyncio.sleep(0.26)
                        await shopMessage.clear_reactions()
                        try:
                            vMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
                        except asyncio.TimeoutError:
                            await shopMessage.edit(embed=timeoutEmbed)
                            await asyncio.sleep(0.26)
                            await shopMessage.clear_reactions()
                        else:
                            try:
                                if int(vMessage.content) < 1:
                                    raise(InterruptedError)
                                index = int(vMessage.content) - 1
                                num = shop.buyback[index]
                            except (ValueError, IndexError) as e:
                                pass
                            except InterruptedError:
                                buyExit = True
                            else:
                                e = ac.Equipment(num)
                                embed = discord.Embed(title='{} {}'.format(e.getRarity(), e.name),
                                                      colour=Colour.infoColour, 
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
                    embed = discord.Embed(title='Selling Equipment', colour=Colour.infoColour,
                                          description='Due to limitation, you will have to respond, in a message, with the item you wish to sell. You must use `0` to go cancel.')
                    await asyncio.sleep(0.26)
                    await shopMessage.clear_reactions()

                    sellExit = False
                    while sellExit == False:
                        embed.clear_fields()
                        number = 0
                        for i in adv.inventory:
                            number += 1
                            e = ac.Equipment(i)
                            if not e.mods.get('unsellable', False):
                                embed.add_field(name='{}. {} {}'.format(number, e.getRarity(
                                ), e.name), value='Selling Cost: **{}** {}'.format(e.price, self.bot.xpName))
                        await shopMessage.edit(embed=embed)
                        try:
                            vMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
                        except asyncio.TimeoutError:
                            await shopMessage.edit(embed=timeoutEmbed)
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
                                if not e.mods.get('unsellable', False):
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
    async def raid(self, ctx):
        """Host a raid for you and multiple adventurers to partake in."""
        if ctx.invoked_subcommand == False:
            embed = discord.Embed(colour=Colour.infoColour, description='Please use `{}raid host`'.format(self.bot.CP))
            await ctx.send(embed=embed)

    @raid.command(aliases=['start'])
    @is_available()
    async def host(self, ctx):
        timeoutEmbed = discord.Embed(
            title='Timed Out', colour=Colour.errorColour)
        timeoutEmbed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        raids = db.get_raids()
        embed = discord.Embed(title='Available Raids', colour=Colour.infoColour,
                              description='There are no restrictions, choose wisely or death is certain.')
        embed.set_footer(text='Send the *index* number of the raid you wish to do.')
        count = 0
        for raid in raids:
            count += 1
            embed.add_field(name='Index: **{}**'.format(count), value='__**{}**__\nLevel {}\n{}'.format(raid[1],raid[2],raid[3]))
        raid_message = await ctx.send(embed=embed)
        try:
            vMessage = await self.bot.wait_for('message', timeout=180.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
        except asyncio.TimeoutError:
            return
        await vMessage.delete()
        num = int(vMessage.content) - 1
        if num > -1:
            selected_raid = raids[num]
        else:
            return
        adventurer = ac.Player(ctx.author.id)
        players = [adventurer]
        joinable = True

        await raid_message.add_reaction('✅')
        while joinable:
            players_string = ''
            for adv in players:
                players_string += '**{0.name}**, Level: {0.level}\n'.format(adv)

            embed = discord.Embed(title='Raid: {}'.format(selected_raid[1]), colour=Colour.infoColour,
                                description='Level **{0[2]}**\n{0[3]}'.format(selected_raid))
            embed.add_field(name='Raid is Joinable', value='Join by reacting below with ✅.\nOnce you join, you can not leave.\nRaid will close 15 seconds after the last join.')
            embed.add_field(name='Current Adventurers', value=players_string)
            await raid_message.edit(embed=embed)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0,
                                                            check = lambda reaction, user: reaction.message.id == raid_message.id and str(reaction) == '✅')
            except asyncio.TimeoutError:
                joinable = False
            else:
                tmp = ac.Player(user.id)
                valid = True
                for p in players:
                    if tmp.id == p.id and tmp.available:
                        valid = False
                if valid and tmp.loaded:
                    players.append(tmp)
                    if len(players) >= 5:
                        joinable = False
                await reaction.remove(user)
        embed.clear_fields()
        embed.add_field(name='Raid is now closed', value='To begin the raid, the host must react with ✅ to begin or ❌ to cancel.')
        embed.add_field(name='Current Adventurers', value=players_string)
        await raid_message.edit(embed=embed)
        await raid_message.add_reaction('❌')
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=180.0,
                                                        check = lambda reaction, user: reaction.message.id == raid_message.id and user.id == ctx.author.id)
        except asyncio.TimeoutError:
            await raid_message.edit(embed=timeoutEmbed)
            await asyncio.sleep(0.26)
            await raid_message.clear_reactions()
            return
        else:
            if str(reaction) == '✅':
                try:
                    for p in players:
                        p.load()
                        p.available = False
                        p.save()
                    raid = ac.Raid(players, selected_raid[0])
                    raid.build_encounter()
                    await asyncio.sleep(0.26)
                    await raid_message.clear_reactions()
                    winner = await raid.encounter.run_combat(self.bot, raid_message)
                    if winner == 1: # 1 signifies player wins
                        await raid_message.add_reaction('✅')
                        for loot in raid.loot:
                            loot_rolls = {}
                            embed = discord.Embed(title='Loot', colour=Colour.infoColour, description='\n'.join(list(map(lambda x: x.name, raid.loot))))
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
                                        loot_rolls[user.id] = random.randint(1, 100)
                                finally:
                                    await reaction.remove(user)
                            sorted_rolls = sorted(loot_rolls, key=loot_rolls.__getitem__, reverse=True)
                            try:
                                loot_winner = next(x for x in raid.players if x.id == sorted_rolls[0])
                                loot_winner.addInv(loot.id)
                            except IndexError:
                                pass
                        raid.finish_encounter(True)
                    else:
                        raid.finish_encounter(False)
                    embed = discord.Embed(title='Raid Over', colour=Colour.errorColour)
                    await raid_message.edit(embed=embed)
                except:
                    logger.error('Error in Raid Host', exc_info=True)
                finally:
                    for p in players:
                        p.available = True
                        p.save()

    @commands.command()
    @commands.guild_only()
    async def talk(self, ctx):
        """Source of various information"""
        adv = ac.Player(ctx.author.id)
        timeoutEmbed = discord.Embed(
            title='Timed Out', colour=Colour.errorColour)
        timeoutEmbed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed = discord.Embed(title='The Innkeeper', colour=Colour.infoColour,
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
            information = """Quests is the main idle component that I offer. Quests are structured in stages, \
                each stage consists of a group of enemies that the adventurer must overcome to progress and get loot.
                
                Each stage takes **{}** seconds to complete. Every minute the time on your quest is checked and progressed.""".format(ac.RNGDungeon.stageTime)
        elif str(reaction) == '2️⃣':
            name = 'Raids'
            information = """Raids, at the moment, are the only active content that I can offer. \
                Upon hosting a raid, other adventurers have up to fifteen seconds to join your raid \
                    and assist you in defeating the boss. At the end, the loot will be cycled through \
                    and adventurers can opt to roll for the loot and the highest roll will get the item."""
        elif str(reaction) == '3️⃣':
            name = 'Combat'
            information = """Combat is turn-based with an order that relies on behind-the-scenes initiative rolls. \
                Adventurers will be confronted with a list of their skills and cooldowns that they may use. \
                All forms of skill usage should be formatted as `skill #` where `skill` is the listed \
                name of the skill and `#` is the index of the target -All this information is listed in the combat screen.\
                It is important to note how your skills are targetted, if your skill should be cast on an enemy then the \
                index must match that of the enemy. If it targets an ally, then the index must match your ally. In the event \
                of a self-cast ability, no target is necessary."""
        elif str(reaction) == '4️⃣':
            name = 'Armor and Weapon Class'
            information = """Armor Class and Weapon Class is used to determine hit chances based on the percent difference. \
                In an average scenerio, Weapon Class should be lower and that difference is used for hit chance; however, \
                if Weapon Class is higher than the armor class, the percent difference is then used for crit chance as a hit \
                is already guaranteed."""
        elif str(reaction) == '5️⃣':
            name = 'Roadmap'
            information = """
            Listed by priority.
            **1. Complete Equipment Overhaul**
            2. Storage and Player Trading
            3. Class and Races
            4. Status Effects
            5. Dungeons
            6. Property Ownership
            7. Slavery
            More to come."""
        else:
            name = 'Not an option'
            information = "I'm not in that big of a mood to talk."
        embed = discord.Embed(title=name, colour=Colour.infoColour, description=information)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await talk_message.edit(embed=embed)
        await asyncio.sleep(0.26)
        await talk_message.clear_reactions()


    @tasks.loop(minutes=1)
    async def quest_check(self):
        quest_to_update = db.getTimeRNG()
        for q in quest_to_update:
            rng = ac.RNGDungeon()
            if rng.loadActive(q[1]):  # If quest loaded successfully
                limiter = 200
                # While enemies or the player exists
                while len(rng.encounter.enemies) > 0 and len(rng.encounter.players) > 0 and limiter > 0:
                    rng.encounter.automatic_turn()
                    limiter -= 1

                rng.nextStage()
                rng.save()
                if not rng.active:  # Check if the quest is done
                    mem = self.bot.get_user(rng.adv.id)
                    if rng.stage > rng.stages:
                        embed = discord.Embed(title='Quest Completed', colour=Colour.successColour,
                                              description='{} stage quest completed successfully!\nXP: **{}**'.format(rng.stages, rng.xp))
                        lootStr = ''
                        for l in rng.loot:
                            tmp = ac.Equipment(l)
                            lootStr += 'Level {0.level} {1} {0.name}\n'.format(tmp, tmp.getRarity())
                        embed.add_field(name='Loot', value=lootStr)
                    else:
                        embed = discord.Embed(title='Quest Failed', colour=Colour.errorColour,
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
        activities = [
            discord.Activity(name='an Adventure', type=discord.ActivityType.watching),
            discord.Activity(name='{}help'.format(self.bot.CP), type=discord.ActivityType.listening),
            discord.Activity(name='with Drinks', type=discord.ActivityType.playing),
            discord.Activity(name='the Bard', type=discord.ActivityType.listening)
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
