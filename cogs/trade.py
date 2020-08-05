import discord
import logging
import asyncio

import adventure as ac
from discord.ext import commands

logger = logging.getLogger('tradeCog')
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

class Trade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def trade(self, ctx):
        adv = ac.Player(ctx.author.id)
        if not adv.loaded:
            raise ac.InvalidAdventurer('Could not load adventurer')
        trades = []
        message = None
        response = None
        stage = 'menu'
        arguments = [None]
        while stage != 'cancel':
            if stage == 'menu': # Display the top menu
                if response:
                    await response.delete()
                menu_embed = discord.Embed(
                    title='Trades',
                    colour=ac.Colour.activeColour,
                    description=f'To create a new trade, run `{self.bot.CP}trade new <player>`'
                )
                menu_embed.set_author(name=adv.name, icon_url=ctx.author.avatar_url)
                trade_ids = adv.get_trades()
                trades.clear()
                if trade_ids:
                    for i, indx in enumerate(trade_ids, start=1):
                        trade = ac.Trade()
                        trade.load(indx)
                        trades.append(trade)
                        name = f'**{i}.** {trade.player_1.name} -> {trade.player_2.name}'
                        value = f'Waiting on: {trade.waiting_on.name}'
                        menu_embed.add_field(name=name, value=value)
                menu_embed.set_footer(text='Follow up: new/view <index>')
                if not message:
                    message = await ctx.send(embed=menu_embed)
                else:
                    await message.edit(embed=menu_embed)
            elif stage == 'view': # View a trade
                if response:
                    await response.delete()
                    response = None
                try:
                    trade = trades[int(arguments[0]) - 1]
                except IndexError:
                    menu_embed.colour = ac.Colour.errorColour
                    menu_embed.set_footer(text='Error: Trade does not exist')
                    await message.edit(embed=menu_embed)
                    return
                except TypeError:
                    menu_embed.colour = ac.Colour.errorColour
                    menu_embed.set_footer(text='Error: Index missing')
                    await message.edit(embed=menu_embed)
                    return
                menu_embed = discord.Embed(
                    title=f'{trade.player_1.name} -> {trade.player_2.name}',
                    colour=ac.Colour.activeColour,
                    description=f'Waiting on: {trade.waiting_on.name}'
                )
                if trade.inventory_1:
                    inv1 = ''
                    for c, i in enumerate(trade.inventory_1, start=1):
                        inv1 += f'**{c}.** {i.get_name()}\n'
                else:
                    inv1 = 'Nothing'
                if trade.inventory_2:
                    inv2 = ''
                    for c, i in enumerate(trade.inventory_2, start=1):
                        inv2 += f'**{c}.** {i.get_name()}\n'
                else:
                    inv2 = 'Nothing'

                menu_embed.add_field(
                    name=f'{trade.player_1.name}\'s Offer',
                    value=inv1
                )
                menu_embed.add_field(
                    name=f'{trade.player_2.name}\'s Offer',
                    value=inv2
                )
                if trade.waiting_on == adv:
                    menu_embed.set_footer(text='Follow up: add/remove/send/cancel')
                    allow = True
                else:
                    menu_embed.set_footer(text='Follow up: cancel')
                    allow = False
                await message.edit(embed=menu_embed)

                try:
                    trade_response = await self.bot.wait_for('message', timeout=60.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
                except asyncio.TimeoutError:
                    stage = 'cancel'
                    continue
                content = trade_response.content.split(' ')
                action = content[0]
                try:
                    await trade_response.delete()
                except discord.Forbidden:
                    pass
                if action == 'add' and allow: # Add items to trade
                    escape = False
                    footer = ''
                    while escape == False:
                        items_string = ''
                        for c, i in enumerate(adv.inventory, start=1):
                            items_string += f'**{c}.** {i.get_name()}'
                        inv_embed = discord.Embed(
                            title='Add item to trade',
                            colour=ac.Colour.activeColour,
                            description=f'Respond with index number, like the shop.\n\n{items_string}'
                        )
                        inv_embed.set_footer(text=footer)
                        await message.edit(embed=inv_embed)
                        item_response = await self.bot.wait_for('message', timeout=60.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
                        try:
                            index = int(item_response.content)
                            try:
                                await item_response.delete()
                            except discord.Forbidden:
                                pass
                        except ValueError:
                            footer = 'Error: Not a number'
                            continue
                        if index == 0:
                            escape = True
                        else:
                            item = adv.remInv(index-1)
                            if not trade.add_item(adv, item):
                                adv.addInv(item)
                                footer = 'Error: Items in trade can not exceed 10'
                            else:
                                footer = ''
                    continue
                elif action == 'remove' and allow:
                    pass
                elif action == 'send' and allow:
                    pass
                else:
                    stage = 'cancel'
                    continue
            try:
                response = await self.bot.wait_for('message', timeout=60.0, check=lambda message: ctx.author == message.author and ctx.message.channel.id == message.channel.id)
            except asyncio.TimeoutError:
                stage = 'cancel'
            else:
                raw = response.content.split(' ')
                stage = raw[0]
                if len(raw) > 1:
                    arguments = raw[1:]
                else:
                    arguments = [None]
        menu_embed.colour = ac.Colour.infoColour
        menu_embed.set_footer(text='')
        await message.edit(embed=menu_embed)
        trade.save()
        adv.save()


def setup(bot):
    bot.add_cog(Trade(bot))