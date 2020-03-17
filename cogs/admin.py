import discord
import logging
import asyncio
import adventureController as ac
import tools.database as db
from tools.colour import Colour

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
        admins = [180067685986467840]
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
        raw_guilds = db.get_all_servers()
        channels = [self.bot.get_channel(x[5]) for x in raw_guilds]
        message = content.split('|')
        embed = discord.Embed(title=message[0], colour=Colour.infoColour, description=message[1])
        for i, x in enumerate(message[2:]):
            if i % 2 != 1:
                try:
                    embed.add_field(name=x, value=message[2+i+1])
                except IndexError:
                    pass
        for channel in channels:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass
        await ctx.message.add_reaction('✅')

    @adminpanel.command()
    async def generate_equipment(self, ctx, target: discord.Member, lvl: int, rarity: int, index = 0):
        adv = ac.Player(target.id)
        if not adv.loaded:
            await ctx.message.add_reaction('⛔')
            return
        e = ac.Equipment(0)
        e.generate_new(lvl, rarity, index=index)
        embed = discord.Embed(title='Loot Generated: {}'.format(e.name), colour=Colour.creationColour,
                              description=e.getInfo())
        message = await ctx.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=180.0, check=lambda reaction, user: user.id == ctx.author.id and reaction.message.id == message.id)
            if str(reaction) == '✅':
                adv.addInv(e.save(database=True))
                adv.save()
                await message.edit(embed=discord.Embed(title='Equipment Given', colour=Colour.successColour))
        except asyncio.TimeoutError:
            pass
        finally:
            try:
                await message.clear_reactions()
            except discord.Forbidden:
                pass

    @commands.command()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.guild_only()
    async def set_action_channels(self, ctx, count: int):
        raw_server_data = list(db.get_server(ctx.guild.id))
        guild = ctx.guild
        category = next(x for x in guild.categories if x.id == raw_server_data[4])
        action_channels = []
        for x in raw_server_data[7].split('|'):
            channel = guild.get_channel(int(x))
            if channel:
                action_channels.append(channel)
        if count <= 0:
            return
        change = count - len(action_channels)
        if change < 0:
            change *= -1
            for _ in range(change):
                await action_channels[-1].delete(reason='{}|Deleted via command'.format(str(ctx.author)))
                action_channels.pop()
        elif change > 0:
            for _ in range(change):
                c = await category.create_text_channel(name='actions_{}'.format(len(action_channels) + 1))
                action_channels.append(c)
        raw_server_data[7] = '|'.join(str(x.id) for x in action_channels)
        db.update_server(
            raw_server_data[2],
            raw_server_data[1],
            raw_server_data[3],
            raw_server_data[4],
            raw_server_data[5],
            raw_server_data[6],
            raw_server_data[7]
        )
        await ctx.message.add_reaction('✅')

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setup_server(self, ctx):
        tout = discord.Embed(title='Timed Out', colour=Colour.errorColour)

        author = ctx.author
        guild = ctx.guild
        guildID = guild.id
        embed = discord.Embed(title='Setup Progress 1/?', colour=Colour.infoColour, 
            description='For me to work as intended now and in the future I have to work out of a specific channel category. Would you like me to create my own or use a pre-existing one?')
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        embed.add_field(name='Options', value='1️⃣: Create your own.\n~~2️⃣: Use a pre-existing one.~~')
        try:
            mainMessage = await author.send(embed=embed)
        except discord.Forbidden:
            mainMessage = await ctx.send(embed=embed)
        await mainMessage.add_reaction('1️⃣')
        # await asyncio.sleep(0.26)
        # await mainMessage.add_reaction('2️⃣')
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=lambda reaction, user: reaction.message.id == mainMessage.id and author.id == user.id)
        except asyncio.TimeoutError:
            await mainMessage.edit(embed=tout)
        else:
            if isinstance(mainMessage.channel, discord.TextChannel):
                await mainMessage.clear_reactions()
            if str(reaction) == '1️⃣':
                embed.title = 'Setup Progress 1/2'
                embed.description = 'How many channels should I make that are designated for bot-related commands? This can be changed later.'
                embed.set_footer(text='Respond with the number')
                embed.clear_fields()
                await mainMessage.edit(embed=embed)
                try:
                    message_response = await self.bot.wait_for('message', timeout=180.0, check = lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.author.dm_channel.id)
                    action_count = int(message_response.content)
                except asyncio.TimeoutError:
                    await mainMessage.edit(embed=tout)
                    return
                except (ValueError, AttributeError):
                    action_count = 1
                embed.title = 'Setup Progress 2/2'
                embed.description = 'I will now create a new category and channels, you may edit the channels as you see fit but do not delete and recreate them.'
                embed.clear_fields()
                await mainMessage.edit(embed=embed)
                await mainMessage.add_reaction('✅')
                announcePerms = {
                    guild.default_role: discord.PermissionOverwrite(send_messages=False),
                    guild.me: discord.PermissionOverwrite(send_messages=True)
                }
                reason = 'Constructing The Inn'
                category = await guild.create_category(name='The Inn', reason=reason)
                announcementChannel = await category.create_text_channel(name='notice_board',
                                                                         overwrites=announcePerms,
                                                                         reason=reason,
                                                                         topic='Announcement Channel for The Innkeeper.')
                generalChannel = await category.create_text_channel(name='innkeepers_bar',
                                                                    reason=reason,
                                                                    topic='Discussion related to The Inn.')
                commandChannels = []
                for i in range(action_count):
                    commandChannels.append(
                        await category.create_text_channel(
                            name='actions_{}'.format(i+1),
                            reason=reason,
                            topic='All commands for The Innkeeper goes here.')
                    )
                commandChannel = commandChannels[0]
            # elif str(reaction) == '2️⃣':
            #     embed.title = 'Setup Progress 2/4'
            #     embed.description = 'I am now going to need the appropriate IDs from you.'
            #     embed.clear_fields()
            #     embed.add_field(name='Information Needed', value='**Category ID**\nAnnouncement Channel ID\nGeneral')

            categoryID = category.id
            announcementID = announcementChannel.id
            generalID = generalChannel.id
            commandID = '|'.join(str(x.id) for x in commandChannels)
            db.add_server(guildID, guild.name, author.id, categoryID, announcementID, generalID, commandID)
            await ctx.message.add_reaction('✅')

            announceEmbed = discord.Embed(title='Hello Citizens of {}!'.format(guild.name), colour=Colour.infoColour,
                description='I have arrived to answer a plea for adventure, and a plea for drinks. Both I can offer and both you can have, with a little work that is. You may call me, **The Innkeeper**.\nMy Inn will always be open to everyone, no matter their alignment.')
            announceEmbed.add_field(name='How to get started',
                                    value='To begin your adventure, run the `{}begin` command in {}. You will then be walked through a multi-step process to go from becoming a **citizen** to an **adventurer**.'.format(self.bot.CP, commandChannel.mention))
            await announcementChannel.send(embed=announceEmbed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def leave_server(self, ctx):
        embed = discord.Embed(title='Are you sure you want me to leave?', colour=Colour.errorColour,
                              description='Leaving will result in my deleting all my channels (Not including raid channels) and erasing server settings.')
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
                raw_server_data = db.get_server(ctx.guild.id)
                tmp = ctx.guild.get_channel(raw_server_data[5])
                ID = ctx.guild.id
                category = tmp.category
                try:
                    for channel in category.channels:
                        await channel.delete(reason='Cleaning up my mess before I go')
                    await category.delete(reason='Cleaning up my mess before I go')
                    await ctx.guild.leave()
                    db.del_server(ID)
                except discord.Forbidden:
                    embed = discord.Embed(title='I do not have permission to clear up my channels.', colour=Colour.errorColour)
                    await confirm_message.edit(embed=embed)
            else:
                await asyncio.sleep(0.26)
                await confirm_message.clear_reactions()


def setup(bot):
    bot.add_cog(Admin(bot))
