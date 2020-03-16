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
        if isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(title='No Private Message', colour=Colour.errorColour, description='Sorry. This command is not allow in private messages. Run {}help to see what is supported in DMs'.format(self.bot.CP))
        elif isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.CheckFailure):
            embed = discord.Embed(title='Check Failure', colour=Colour.errorColour, description='{}\nCould your adventurer be busy?'.format(str(error)))
        elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            embed = discord.Embed(title='Incomplete Arguments', colour=Colour.errorColour, description='{}: {}'.format(type(error).__name__, str(error)))
        else:
            logger.error('{}: {}'.format(type(error).__name__, error))
            embed = discord.Embed(title="Unknown Error Detected", colour=Colour.errorColour, description='**Error Details**```{}: {}```'.format(type(error).__name__, str(error)))
            embed.set_footer(text='I have already notified the programmer.')
            owner_embed = discord.Embed(title='Error In Command: {}'.format(ctx.command.name), colour=Colour.errorColour, description='```{}: {}```'.format(type(error).__name__, str(error)))
            owner_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            owner = self.bot.get_user(self.bot.owner_id)
            await owner.send(embed=owner_embed)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

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