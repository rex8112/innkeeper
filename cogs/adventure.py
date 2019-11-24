import discord
import logging
import asyncio
import adventureController as ac
import tools.database as db

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


class Colour:
  creationColour = discord.Colour(0x00DBEB)
  errorColour = discord.Colour(0xFF0000)
  successColour = discord.Colour(0x0DFF00)
  infoColour = discord.Colour(0xFFA41C)


def is_available():
  def predicate(ctx):
    adv = ac.Player(ctx.author.id)
    adv.load(False)
    return adv.available
  return commands.check(predicate)

class Adventure(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.questCheck.start()


  @commands.command()
  @commands.guild_only()
  async def begin(self, ctx):
    """Begin your adventure!
    Ultimately, the character creator."""
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
          #async with controlMessage.channel.typing():
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

  @commands.group(aliases=['character'])
  @commands.guild_only()
  async def profile(self, ctx):
    """Get information on your Adventurer"""
    if ctx.invoked_subcommand is None:
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

        invStr = ''
        for i in adv.inventory:
          tmp = ac.Equipment(i)
          invStr += '**{}** {}, Level **{}**\n'.format(tmp.rarity, tmp.name, tmp.level)
        if invStr == '':
          invStr = 'Nothing'

        embed.add_field(name='Inventory', value=invStr)
        await ctx.send(embed=embed)

  @profile.command(aliases=['attributes'])
  async def stats(self, ctx):
    """Get a bit more detail about your current stats and attributes"""
    adv = ac.Player(ctx.author.id)
    if not adv.load():
      embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=Colour.errorColour,
                            description='Please contact rex8112#1200 if this is not the case.')
      await ctx.send(embed=embed)
      return

    embed = discord.Embed(title=str(adv.name), colour=Colour.infoColour, description='Detailed Attributes and Stats')
    embed.add_field(name='Strength: {}'.format(adv.strength), value='Base Strength: {0.rawStrength}\nUnarmed Damage: {0.unarmDamage}\nInventory Slots: {0.inventoryCapacity}'.format(adv))
    embed.add_field(name='Dexterity: {}'.format(adv.dexterity), value='Base Dexterity: {0.rawDexterity}\nEvasion: {0.evasion:.1%}\nCrit Chance: {0.critChance:.1%}'.format(adv))
    embed.add_field(name='Constitution: {}'.format(adv.constitution), value='Base Constitution: {0.rawConstitution}\nMax Health: {0.maxHealth}'.format(adv))
    embed.add_field(name='Intelligence: {}'.format(adv.intelligence), value='Base Intelligence: {0.rawIntelligence}\nSpell Amplification: {0.spellAmp:.1%}'.format(adv))
    embed.add_field(name='Wisdom: {}'.format(adv.wisdom), value='Base Wisdom: {0.rawWisdom}'.format(adv))
    embed.add_field(name='Charisma: {}'.format(adv.charisma), value='Base Charisma: {0.rawCharisma}'.format(adv))
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

  @commands.command()
  @commands.guild_only()
  async def equipment(self, ctx):
    """Get your currently equipped gear and info"""
    adv = ac.Player(ctx.author.id)
    adv.load()
    embed = discord.Embed(title=str(adv.name), colour=Colour.infoColour, description='Detailed Equipment Statistics')
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    
    embed.add_field(name='Mainhand', value=adv.mainhand.getInfo())
    embed.add_field(name='Offhand', value=adv.offhand.getInfo())
    embed.add_field(name='Helmet', value=adv.helmet.getInfo())
    embed.add_field(name='Armor', value=adv.armor.getInfo())
    embed.add_field(name='Gloves', value=adv.gloves.getInfo())
    embed.add_field(name='Boots', value=adv.boots.getInfo())
    embed.add_field(name='Trinket', value=adv.trinket.getInfo())

    await ctx.send(embed=embed)

  @commands.group()
  @commands.guild_only()
  async def inventory(self, ctx):
    """Command group to manage your inventory
    If ran with no subcommands, will get your current inventory."""
    if ctx.invoked_subcommand is None:
      adv = ac.Player(ctx.author.id)
      adv.load()
      count = 0
      embed = discord.Embed(title='{}\'s Inventory'.format(adv.name), colour=Colour.infoColour)
      embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
      embed.set_footer(text='{} / {}'.format(len(adv.inventory), adv.inventoryCapacity))
      for i in adv.inventory:
        e = ac.Equipment(i)
        count += 1
        embed.add_field(name='Slot **{}**'.format(count), value=e.getInfo())
        
      await ctx.send(embed=embed)

  @inventory.command()
  @is_available()
  async def equip(self, ctx, slot: int):
    """Equip a piece of equipment from your inventory
    Must give the number of the inventory slot the equipment resides in."""
    try:
      adv = ac.Player(ctx.author.id)
      adv.load(False)
      if adv.equip(slot):
        adv.save()
        await ctx.message.add_reaction('✅')
      else:
        await ctx.message.add_reaction('⛔')
    except Exception as e:
      logger.warning('Equipping Failed',exc_info=True)
      await ctx.message.add_reaction('⛔')

  @commands.group()
  @commands.guild_only()
  async def quest(self, ctx):
    """Command group to manage quests
    If ran with no subcommands, will output current quest information."""
    if ctx.invoked_subcommand is None:
      rng = ac.RNGDungeon()
      if rng.loadActive(ctx.author.id):
        embed = discord.Embed(title='**{}** Stage Quest'.format(rng.stages), colour=Colour.infoColour)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text='ID = {}'.format(rng.id))
        embed.add_field(name='Current Progress', value='Current Stage: **{}**\nStages Completed: **{}**\nTotal Stages: **{}**'.format(rng.stage, rng.stage - 1, rng.stages))
        
        enemies = ''
        for e in rng.enemies[rng.stage - 1]:
          t = ac.Enemy(e)
          t.load(False)
          enemies += '**Lv {}** {}\n'.format(t.level, t.name)

        embed.add_field(name='Current Enemies', value=enemies)
      else:
        embed = discord.Embed(title='No Active Quest', colour=Colour.errorColour)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

      await ctx.send(embed=embed)

  @quest.command()
  @is_available()
  async def start(self, ctx, difficulty: str): #Generates a new dungeon based on the inputted difficulty
    """Generates a new dungeon based on the given difficulty
    Available difficulties: easy, medium, and hard.
    
    Difficulty increases the amount of stages done in one round while also getting more difficult in the later stages."""
    rng = ac.RNGDungeon()
    rng.new(ctx.author.id, difficulty)

    embed = discord.Embed(title='{} QUEST GENERATED'.format(difficulty.upper()), colour=Colour.creationColour, description='**{}** Stages'.format(rng.stages))
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    enemies = ''
    for e in rng.enemies[rng.stage - 1]:
      t = ac.Enemy(e)
      t.load(False)
      enemies += '**Lv {}**, {}\n'.format(t.level, t.name)

    embed.add_field(name='Current Enemies', value=enemies)
    await ctx.send(embed=embed)

  @commands.command()
  @commands.guild_only()
  async def shop(self, ctx):
    pass

  @tasks.loop(minutes=1)
  async def questCheck(self):
    qtu = db.getTimeRNG()
    for q in qtu:
      rng = ac.RNGDungeon()
      if rng.loadActive(q[1]): #If quest loaded successfully
        limiter = 200
        while len(rng.encounter.enemies) > 0 and len(rng.encounter.players) > 0 and limiter > 0: #While enemies or the player exists
          rng.encounter.nextTurn()
          limiter -= 1
        
        rng.nextStage()
        rng.save()
        if not rng.active: #Check if the quest is done
          mem = self.bot.get_user(rng.adv.id)
          if rng.stage > rng.stages:
            embed = discord.Embed(title='Quest Completed', colour=Colour.successColour, description='{} stage quest completed successfully!\nXP: **{}**'.format(rng.stages, rng.xp))
            lootStr = ''
            for l in rng.loot:
              tmp = ac.Equipment(l)
              lootStr += 'Level {0.level} {0.rarity} {0.name}\n'.format(tmp)
            embed.add_field(name='Loot', value=lootStr)
            await mem.send(embed=embed)
          else:
            embed = discord.Embed(title='Quest Failed', colour=Colour.errorColour, description='{} died on stage {}'.format(rng.adv.name, rng.stage))
            await mem.send(embed=embed)

  @questCheck.before_loop
  async def before_questCheck(self):
    await self.bot.wait_until_ready()


def setup(bot):
  bot.add_cog(Adventure(bot))
