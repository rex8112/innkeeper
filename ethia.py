import discord
import logging
import sys

from discord.ext import commands
from tools.configLoader import settings
import tools.database as db
db.initDB()

commandPrefix = '-'
startup_extensions = ['cogs.adventure',
                        'cogs.admin',
                        'cogs.events']
logging.basicConfig(level=logging.INFO)

game = discord.Activity(
    name='An Adventure', type=discord.ActivityType.watching)
bot = commands.Bot(description='A Wonderful Adventure',
                   command_prefix=commandPrefix, owner_id=int(settings.owner))
bot.CP = commandPrefix

logger = logging.getLogger('core')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
handler2 = logging.FileHandler(
    filename='latest.log', encoding='utf-8', mode='w')
handler2.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
logger.addHandler(handler2)


@bot.event
async def on_ready():
    print('Logged in as')
    print('Name: {}'.format(bot.user.name))
    print('ID:   {}'.format(bot.user.id))
    print('----------')
    for guild in bot.guilds:
        print(guild.name)
        print(guild.id)
        print('---------')
    logger.info('----- Bot Ready -----')


@bot.command()
@commands.guild_only()
async def ping(ctx):
    await ctx.send('Pong!')


@bot.command(hidden=True)
@commands.is_owner()
async def shutdown(ctx):
    """Turns the bot off"""
    await bot.logout()
    sys.exit()


if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            logger.critical(
                'Failed to load extension {}\n{}'.format(extension, exc))

bot.run(settings.token)
