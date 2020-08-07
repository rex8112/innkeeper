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
        main_embed = discord.Embed(title='Inventory', colour=ac.Colour.activeColour,
            description=f'Inventory {len(adv.inventory)}/{adv.inventoryCapacity}')
        main_embed.set_author(name=adv.name, icon_url=ctx.author.avatar_url)
        main_embed.set_footer(text='Follow up message: <examine #/compare # #/store #>')

        for count, e in enumerate(adv.inventory, start=1):
            main_embed.add_field(name=f'------- Slot {count:02} -------', value=e.getInfo(compare_equipment=adv.get_equipment_from_slot(e.slot)))

        main_message = await ctx.send(embed=main_embed)
        try:
            value_message = await self.bot.wait_for('message', timeout=30.0, check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)
        except asyncio.TimeoutError:
            main_embed.set_footer(text='')
            main_embed.colour = ac.Colour.infoColour
            await main_message.edit(embed=main_embed)
            return
        
        content = value_message.content.split(' ')
        delete = False
        try:
            if content[0].lower() == 'examine':
                slot = int(content[1])
                examined_item = adv.inventory[slot - 1]
                equipped_item = adv.get_equipment_from_slot(examined_item.slot)
                main_embed.clear_fields()
                main_embed.colour = ac.Colour.get_rarity_colour(examined_item.getRarity())
                main_embed.set_footer(text='')

                main_embed.add_field(name=f'Slot {slot}', value=examined_item.getInfo(compare_equipment=equipped_item))
                main_embed.add_field(name=f'Equipped {equipped_item.slot}', value=equipped_item.getInfo(compare_equipment=examined_item))
                await main_message.edit(embed=main_embed)
                delete = True
            elif content[0].lower() == 'compare':
                slot_1 = int(content[1])
                slot_2 = int(content[2])
                compare_1 = adv.inventory[slot_1 - 1]
                compare_2 = adv.inventory[slot_2 - 1]
                main_embed.clear_fields()
                main_embed.colour = ac.Colour.get_rarity_colour(compare_1.getRarity())
                main_embed.set_footer(text='')

                main_embed.add_field(name=f'Slot {slot_1}', value=compare_1.getInfo(compare_equipment=compare_2))
                main_embed.add_field(name=f'Slot {slot_2}', value=compare_2.getInfo(compare_equipment=compare_1))
                await main_message.edit(embed=main_embed)
                delete = True
            elif content[0].lower() == 'store':
                if adv.available:
                    storage = ac.Storage(adv)
                    slot = int(content[1])
                    if len(storage.inventory) < storage.slots:
                        item = adv.remInv(slot-1)
                        storage.add_item(item)
                        embed = discord.Embed(title='Success', colour=ac.Colour.successColour, description='Item stored.')
                        await main_message.edit(embed=embed)
                        adv.save()
                        storage.save()
                    else:
                        main_embed.colour = ac.Colour.infoColour
                        main_embed.set_footer(text='Storage Full')
                        await main_message.edit(embed=main_embed)
                else:
                    main_embed.colour = ac.Colour.infoColour
                    main_embed.set_footer(text='Adventurer Busy')
                    await main_message.edit(embed=main_embed)
                delete = True
            else:
                main_embed.colour = ac.Colour.infoColour
                main_embed.set_footer(text='')
                await main_message.edit(embed=main_embed)
            if delete and not isinstance(main_message.channel, discord.DMChannel):
                await value_message.delete()

        except IndexError:
            main_embed.colour = ac.Colour.infoColour
            main_embed.set_footer(text='Invalid Slot #')
            await main_message.edit(embed=main_embed)
            await value_message.delete()

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

    @commands.command(aliases=['bank'])
    async def storage(self, ctx):
        """View your storage and move stuff in and out."""
        adv = ac.Player(ctx.author.id)
        storage = ac.Storage(adv)
        main_embed = discord.Embed(title='Storage', colour=ac.Colour.activeColour,
            description=f'Storage {len(storage.inventory)}/{storage.slots}')
        main_embed.set_author(name=adv.name, icon_url=ctx.author.avatar_url)
        main_embed.set_footer(text='Follow up message: <examine #/compare # #/retrieve #>')

        for count, e in enumerate(storage.inventory, start=1):
            main_embed.add_field(name=f'Slot {count}', value=e.getInfo(compare_equipment=adv.get_equipment_from_slot(e.slot)))

        main_message = await ctx.send(embed=main_embed)
        try:
            value_message = await self.bot.wait_for('message', timeout=30.0, check=lambda message: message.author.id == ctx.author.id and message.channel.id == ctx.channel.id)
        except asyncio.TimeoutError:
            main_embed.set_footer(text='')
            main_embed.colour = ac.Colour.infoColour
            await main_message.edit(embed=main_embed)
            return
        
        content = value_message.content.split(' ')
        delete = False
        try:
            if content[0].lower() == 'examine':
                slot = int(content[1])
                examined_item = storage.inventory[slot - 1]
                equipped_item = adv.get_equipment_from_slot(examined_item.slot)
                main_embed.clear_fields()
                main_embed.colour = ac.Colour.get_rarity_colour(examined_item.getRarity())
                main_embed.set_footer(text='')

                main_embed.add_field(name=f'Slot {slot}', value=examined_item.getInfo(compare_equipment=equipped_item))
                main_embed.add_field(name=f'Equipped {equipped_item.slot}', value=equipped_item.getInfo(compare_equipment=examined_item))
                await main_message.edit(embed=main_embed)
                delete = True
            elif content[0].lower() == 'compare':
                slot_1 = int(content[1])
                slot_2 = int(content[2])
                compare_1 = storage.inventory[slot_1 - 1]
                compare_2 = storage.inventory[slot_2 - 1]
                main_embed.clear_fields()
                main_embed.colour = ac.Colour.get_rarity_colour(compare_1.getRarity())
                main_embed.set_footer(text='')

                main_embed.add_field(name=f'Slot {slot_1}', value=compare_1.getInfo(compare_equipment=compare_2))
                main_embed.add_field(name=f'Slot {slot_2}', value=compare_2.getInfo(compare_equipment=compare_1))
                await main_message.edit(embed=main_embed)
                delete = True
            elif content[0].lower() == 'retrieve':
                if adv.available:
                    slot = int(content[1])
                    if len(adv.inventory) < adv.inventoryCapacity:
                        item = storage.remove_item(slot-1)
                        adv.addInv(item)
                        embed = discord.Embed(title='Success', colour=ac.Colour.successColour, description='Item retrieved.')
                        await main_message.edit(embed=embed)
                        adv.save()
                        storage.save()
                    else:
                        main_embed.colour = ac.Colour.infoColour
                        main_embed.set_footer(text='Inventory Full')
                        await main_message.edit(embed=main_embed)
                else:
                    main_embed.colour = ac.Colour.infoColour
                    main_embed.set_footer(text='Adventurer Busy')
                    await main_message.edit(embed=main_embed)
                delete = True
            else:
                main_embed.colour = ac.Colour.infoColour
                main_embed.set_footer(text='')
                await main_message.edit(embed=main_embed)
            if delete and not isinstance(main_message.channel, discord.DMChannel):
                await value_message.delete()

        except IndexError:
            main_embed.colour = ac.Colour.infoColour
            main_embed.set_footer(text='Invalid Slot #')
            await main_message.edit(embed=main_embed)
            await value_message.delete()

def setup(bot):
    bot.add_cog(Inventory(bot))