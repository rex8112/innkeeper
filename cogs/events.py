import discord
import logging
import tools.database as db
from tools.colour import Colour

from discord.ext import commands

logger = logging.getLogger('eventsCog')
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

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        owner = guild.owner
        embed = discord.Embed(title='Hello {}'.format(owner.name), colour=Colour.infoColour, 
                              description='I appreciate you taking an interest in the adventures I can offer. However, for me to offer my services correctly, I am going to need some assistance setting up. If either you or an administrator of **{0}** could run the `{1}setup_server` \
                                  in any channel within **{0}**, we can get this process started.'.format(guild.name, self.bot.CP))
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        await owner.send(embed=embed)

def setup(bot):
    bot.add_cog(Events(bot))