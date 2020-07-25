import discord
import logging
import asyncio
import random
import math
import re

import adventure as ac

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

def is_available():
    async def predicate(ctx):
        adv = ac.Player(ctx.author.id, False)
        adv.load(False)
        if adv.loaded:
            return adv.available
        else:
            return False
    return commands.check(predicate)


class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['i','inv'])
    async def inventory(self, ctx, slot = 0):
        """Command to view your inventory
        If slot is provided, will show a more detailed view of the item in that slot."""
        adv = ac.Player(ctx.author.id)
        if not adv.loaded:
            embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=ac.Colour.errorColour,
                                description='Please contact rex8112#1200 if this is not the case.')
            await ctx.send(embed=embed)
            return
        if slot == 0:
            embed = discord.Embed(title='{}\'s Inventory'.format(
                adv.name), colour=ac.Colour.infoColour)
            embed.set_author(name=ctx.author.display_name,
                                icon_url=ctx.author.avatar_url)
            embed.set_footer(
                text='Inventory Capacity: {} / {}'.format(len(adv.inventory), adv.inventoryCapacity))
            for count, i in enumerate(adv.inventory, start=1):
                e = ac.Equipment(i)
                embed.add_field(
                    name='Slot **{}**'.format(count), value=e.getInfo(compare_equipment=adv.get_equipment_from_slot(e.slot)))
        else:
            try:
                e = ac.Equipment(adv.inventory[slot-1])
                embed = discord.Embed(title=e.name, colour=ac.Colour.get_rarity_colour(e.rarity), description=e.getInfo(title=False))
            except IndexError:
                embed = discord.Embed(title='Slot Empty', colour=ac.Colour.errorColour, description='Slot {} has no items.'.format(slot))
        await ctx.send(embed=embed)

    @commands.command()
    @is_available()
    async def equip(self, ctx, slot: int):
        """Equip a piece of equipment from your inventory
        Must give the number of the inventory slot the equipment resides in."""
        try:
            adv = ac.Player(ctx.author.id, False)
            adv.load(False)
            if not adv.loaded:
                embed = discord.Embed(title='Failed to Load Adventurer. Do you have one?', colour=ac.Colour.errorColour,
                                    description='Please contact rex8112#1200 if this is not the case.')
                await ctx.send(embed=embed)
                return
            if adv.equip(slot-1):
                adv.save()
                await ctx.message.add_reaction('✅')
            else:
                await ctx.message.add_reaction('⛔')
        except (ac.InvalidLevel, ac.InvalidRequirements) as e:
            error_embed = discord.Embed(title='{}'.format(type(e).__name__), colour=ac.Colour.errorColour, description='{}'.format(e))
            await ctx.message.add_reaction('⛔')
            await ctx.send(embed=error_embed)
        except Exception:
            logger.warning('Equipping Failed', exc_info=True)
            await ctx.message.add_reaction('⛔')

def setup(bot):
    bot.add_cog(Inventory(bot))