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
  infoColour = discord.Colour(0xFFA41C)


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
          try:
            attributes = list(map(int, valueMessage.content.split(' ')))
          except ValueError:
            logger.warning('Invalid Response passed to attributes')
          else:
            total = 0
            if len(attributes) > 6:
              del attributes[6:]
            elif len(attributes) < 6:
              for i in range(6 - len(attributes)):
                attributes.append(0)

            for att in attributes:
              total += att

            attributes[:] = [x + 10 for x in attributes]
            print(attributes)

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
                      value='Name: {0}\nStrength: {1[0]}\nDexterity: {1[1]}\nConstitution: {1[2]}\nIntelligence: {1[3]}\nWisdom: {1[4]}\nCharisma: {1[5]}[WIP:Currently Unused But Required]'.format(name, attributes))
      embed.add_field(name='Next on the list:',
                      value='**ALL DONE!**\nTake a look at the information, is it all to your liking?')
      embed.set_author(name=ctx.author.display_name,
                       icon_url=ctx.author.avatar_url)
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
          async with controlMessage.channel.typing():
            if adv.new(name, 'Adventurer', 'Human', attributes):
              embed = discord.Embed(title='Adventurer Created!',
                                    colour=Colour.successColour, description='Welcome {}!'.format(name))
            else:
              embed = discord.Embed(title='Adventurer Already Created!', colour=Colour.errorColour,
                                    description='You can not make two!')
        else:
          embed = discord.Embed(title='Adventurer Scrapped!', colour=Colour.errorColour,
                                description='Rerun the command to try again')
        await controlMessage.clear_reactions()
        await controlMessage.edit(embed=embed)

  @commands.command()
  @commands.guild_only()
  async def adventurer(self, ctx):
    """Get information on your Adventurer"""
    adv = ac.Player(ctx.author.id)
    if not adv.load():
      embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=Colour.errorColour,
                            description='Please contact rex8112#1200 if this is not the case.')
      await ctx.send(embed=embed)
      return
    else:
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

      invStr = '\n'.join(adv.inventory)
      if not invStr:
        invStr = 'Nothing'

      embed.add_field(name='Inventory', value=invStr)
      await ctx.send(embed=embed)


def setup(bot):
  bot.add_cog(Adventure(bot))
