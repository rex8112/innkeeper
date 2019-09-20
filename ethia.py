import discord
import logging

from discord.ext import commands
from tools.configLoader import settings

startup_extensions = []
logging.basicConfig(level=logging.INFO)

game = discord.Activity(name='An Adventure', type=discord.ActivityType.watching)
bot = commands.Bot(description='A Wonderful Adventure', command_prefix=',', owner_id=int(settings.owner), activity=game)

logger = logging.getLogger('core')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

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

if __name__ == "__main__":
  for extension in startup_extensions:
    try:
      bot.load_extension(extension)
    except Exception as e:
      exc = '{}: {}'.format(type(e).__name__, e)
      print('Failed to load extension {}\n{}'.format(extension, exc))
      logger.critical('Failed to load extension {}\n{}'.format(extension, exc))

bot.run(settings.token)