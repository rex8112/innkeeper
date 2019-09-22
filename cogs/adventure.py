import discord
import logging
import asyncio
import adventureController as ac
import tools.database as db

from discord.ext import commands

logger = logging.getLogger('adventureCog')
logger.setLevel(logging.DEBUG)
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


class Adventure(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  @commands.guild_only()
  async def begin(self, ctx):
    """Begin your adventure!"""
    adv = ac.Player(ctx.author.id)
    embed = discord.Embed(title='Adventurer Creator', colour=Colour.creationColour,
                          description='Welcome Adventurer!\nBefore you can start your adventurer, I am going to need some new info from you.')
    embed.add_field(name='Needed Information',
                    value='Name:\nStrength:\nDexterity:\nConstitution:\nIntelligence:\nWisdom:\nCharisma:[WIP:Currently Unused But Required]')
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
                        value='Name: {}\nStrength:\nDexterity:\nConstitution:\nIntelligence:\nWisdom:\nCharisma:[WIP:Currently Unused But Required]'.format(name))
        embed.add_field(name='Next on the list:',
                        value='**Attributes**\nBy default, you have 10 in every attribute but we are going to change that. You have **5** points to spend. \
                          You will gain a point per level up, do not worry.\n**Formatting**\nFor this information, I am going to need you to put the points \
                            you want in the format listed below, the order matters and is the same as listed above.\n`1 2 2 0 0 0`')
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text='You have 3 minutes to type your response')
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
          attributes = valueMessage.content.split(' ')
          await valueMessage.delete()
          total = 0
          if len(attributes) > 6:
            del attributes[6:]
          elif len(attributes) < 6:
            for i in range(6 - len(attributes)):
              attributes.append(0)

          for att in attributes:
            total += int(att)

          if total > 5:
            await ctx.send(embed=discord.Embed(title='Total number over 5, try again', colour=Colour.errorColour), delete_after=3.0)
          elif total < 5:
            await ctx.send(embed=discord.Embed(title='Total number under 5, try again', colour=Colour.errorColour), delete_after=3.0)
          else:
            cont = True

      if controlMessage == None:
        return
      embed = discord.Embed(title='Adventurer Creator', colour=Colour.creationColour,
                            description='Welcome Adventurer!\nBefore you can start your adventurer, I am going to need some new info from you.')
      embed.add_field(name='Needed Information',
                      value='Name: {0}\nStrength: {1[0]}\nDexterity: {1[1]}\nConstitution: {1[2]}\nIntelligence: {1[3]}\nWisdom: {1[4]}\nCharisma: {1[5]}[WIP:Currently Unused But Required]'.format(name, attributes))
      embed.add_field(name='Next on the list:',
                      value='**ALL DONE!**\nTake a look at the information, is it all to your liking?')
      embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
      embed.set_footer(text='You have 3 minutes to react your response')
      await controlMessage.edit(embed=embed)
      await controlMessage.add_reaction('✅')
      await controlMessage.add_reaction('❌')

      try:
        logger.debug('Waiting for confirmation')
        reaction, user = await self.bot.wait_for('reaction_add', timeout=180.0, check=lambda reaction, user: user == ctx.message.author and controlMessage.id == reaction.message.id)
      except asyncio.TimeoutError:
        await controlMessage.edit(embed=tout)
        await controlMessage.clear_reactions()
        logger.warning('Adventure Creator Timed Out')
      else:
        if str(reaction) == '✅':
          embed = discord.Embed(title='Adventurer Created!',
                                colour=Colour.successColour, description='Welcome {}!'.format(name))
        else:
          embed = discord.Embed(title='Adventurer Scrapped!', colour=Colour.errorColour,
                                description='Rerun the command to try again')
        await controlMessage.clear_reactions()
        await controlMessage.edit(embed=embed)


def setup(bot):
  bot.add_cog(Adventure(bot))


#message = await ctx.send('Test, react with ✅ or ❌')
#await message.add_reaction('✅')
#await message.add_reaction('❌')
#def check(reaction, user):
#    return user == ctx.message.author and message.id == reaction.message.id
#try:
#    reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=10.0)
#except asyncio.TimeoutError:
#    await ctx.send('Timeout')
#else:
#    await ctx.send('So far so good!')
