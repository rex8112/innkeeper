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
        embed.add_field(name='Options', value='1️⃣: Create your own.\n2️⃣: Use a pre-existing one.')
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
                embed.title = 'Setup Progress 1/1'
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
                commandChannel = await category.create_text_channel(name='actions',
                                                                    reason=reason,
                                                                    topic='All commands for The Innkeeper goes here.')
            # elif str(reaction) == '2️⃣':
            #     embed.title = 'Setup Progress 2/4'
            #     embed.description = 'I am now going to need the appropriate IDs from you.'
            #     embed.clear_fields()
            #     embed.add_field(name='Information Needed', value='**Category ID**\nAnnouncement Channel ID\nGeneral')

            categoryID = category.id
            announcementID = announcementChannel.id
            generalID = generalChannel.id
            commandID = commandChannel.id
            db.add_server(guildID, guild.name, author.id, categoryID, announcementID, generalID, commandID)
            await ctx.message.add_reaction('✅')

            announceEmbed = discord.Embed(title='Hello Citizens of {}!'.format(guild.name), colour=Colour.infoColour,
                description='I have arrived to answer a plea for power, power that I can offer. You may call me, **The Innkeeper**.\nMy Inn will always be open to everyone, no matter their alignment.\n\n***(Bot is heavily still in early alpha and has a hard limitation at this moment until a few things are reworked. Think of this as more of a preview for what is to come.)***')
            announceEmbed.add_field(name='How to get started',
                                    value='To begin your adventure, run the `{}begin` command in {}. You will then be walked through a multi-step process to go from becoming a citizen to an adventurer.'.format(self.bot.CP, commandChannel.mention))
            announceEmbed.add_field(name='Current Alpha Limitations',
                                    value='Max level: 5\nVery Limited Equipment\nOne Raid\n\nThese limitations will be lifted once equipment is reworked.')
            print('About to send')
            await announcementChannel.send(embed=announceEmbed)
            print('Sending')


def setup(bot):
    bot.add_cog(Admin(bot))
