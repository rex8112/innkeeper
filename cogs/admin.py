import discord
import logging
import asyncio
import adventureController as ac
import tools.database as db

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


class Colour:
    creationColour = discord.Colour(0x00DBEB)
    errorColour = discord.Colour(0xFF0000)
    successColour = discord.Colour(0x0DFF00)
    infoColour = discord.Colour(0xFFA41C)


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
        adv = ac.Player(member.id)
        adv.load(False)
        adv.available = value
        adv.save()
        await ctx.message.add_reaction('✅')


def setup(bot):
    bot.add_cog(Admin(bot))