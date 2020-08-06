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

def is_available():
    async def predicate(ctx):
        adv = ac.Player(ctx.author.id, False)
        adv.load(False)
        if adv.loaded:
            return adv.available
        else:
            return False
    return commands.check(predicate)

class Trade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @is_available()
    async def trade(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        adv = ac.Player(ctx.author.id)
        if not adv.loaded:
            raise ac.InvalidAdventurer('Could not load adventurer')
        trades = []
        message = None
        response = None
        stage = 'menu'
        save = False
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
                menu_embed.set_footer(text='Follow up: view <index>')
                if not message:
                    message = await ctx.send(embed=menu_embed)
                else:
                    await message.edit(embed=menu_embed)
            elif stage == 'view': # View a trade
                if response:
                    try:
                        await response.delete()
                    except discord.Forbidden:
                        pass
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
                except ValueError:
                    menu_embed.colour = ac.Colour.errorColour
                    menu_embed.set_footer(text='Error: NaN')
                    await message.edit(embed=menu_embed)
                    return
                menu_embed = discord.Embed(
                    title=f'{trade.player_1.name} -> {trade.player_2.name}',
                    colour=ac.Colour.activeColour,
                    description=f'Waiting on: {trade.waiting_on.name}'
                )
                menu_embed.set_author(name=adv.name, icon_url=ctx.author.avatar_url)
                if trade.inventory_1:
                    inv1 = f'Confirmed: {trade.confirm_1}\n\n'
                    for c, i in enumerate(trade.inventory_1, start=1):
                        inv1 += f'**{c}.** {i.get_name()}\n'
                else:
                    inv1 = f'Confirmed: {trade.confirm_1}\n\nNothing'
                if trade.inventory_2:
                    inv2 = f'Confirmed: {trade.confirm_2}\n\n'
                    for c, i in enumerate(trade.inventory_2, start=1):
                        inv2 += f'**{c}.** {i.get_name()}\n'
                else:
                    inv2 = f'Confirmed: {trade.confirm_2}\n\nNothing'

                menu_embed.add_field(
                    name=f'{trade.player_1.name}\'s Offer',
                    value=inv1
                )
                menu_embed.add_field(
                    name=f'{trade.player_2.name}\'s Offer',
                    value=inv2
                )
                if trade.waiting_on == adv:
                    menu_embed.set_footer(text='Follow up: add/remove <#>/send/confirm/cancel')
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
                if action.lower() == 'add' and allow: # Add items to trade
                    save = True
                    trade.set_confirm(trade.player_1, False)
                    trade.set_confirm(trade.player_2, False)
                    escape = False
                    footer = ''
                    while escape == False:
                        items_string = ''
                        for c, i in enumerate(trade.waiting_on.inventory, start=1):
                            items_string += f'**{c}.** {i.get_name()}\n'
                        inv_embed = discord.Embed(
                            title='Add item to trade',
                            colour=ac.Colour.activeColour,
                            description=f'Respond with index number, like the shop. Use `0` to cancel.\n\n{items_string}'
                        )
                        inv_embed.set_author(name=adv.name, icon_url=ctx.author.avatar_url)
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
                            if not trade.add_item(adv, index-1):
                                footer = 'Error: Items in trade can not exceed 10'
                            else:
                                footer = ''
                    continue
                elif action.lower() == 'remove' and allow:
                    save = True
                    trade.set_confirm(trade.player_1, False)
                    trade.set_confirm(trade.player_2, False)
                    try:
                        index = int(content[1])
                    except IndexError:
                        footer = 'Error: Missing index'
                        continue
                    except ValueError:
                        footer = 'Error: NaN'
                        continue
                    item = trade.del_item(adv, index-1)
                    if not adv.addInv(item):
                        trade.add_item(adv, item)
                        footer = 'Error: Inventory full'
                        continue
                    continue
                elif action.lower() == 'send' and allow:
                    save = True
                    trade.set_confirm(trade.player_1, False)
                    trade.set_confirm(trade.player_2, False)
                    sender = trade.waiting_on
                    trade.toggle_waiting_on()
                    send_embed = discord.Embed(
                        title='Trade Updated',
                        colour=ac.Colour.infoColour,
                        description=f'Your trade with **{sender.name}** has been updated.'
                    )
                    user = self.bot.get_user(trade.waiting_on.id)
                    if user:
                        try:
                            await user.send(embed=send_embed)
                        except discord.Forbidden:
                            pass
                    menu_embed = discord.Embed(
                        title='Trade Sent',
                        colour=ac.Colour.successColour
                    )
                    menu_embed.set_author(name=adv.name, icon_url=ctx.author.avatar_url)
                    await message.edit(embed=menu_embed)
                    stage = 'cancel'
                    continue
                elif action.lower() == 'confirm' and allow:
                    save = True
                    sender = trade.waiting_on
                    trade.set_confirm(adv, True)
                    trade.toggle_waiting_on()
                    if not trade.waiting_on.available:
                        trade.set_confirm(trade.waiting_on, False)
                    confirm_embed = discord.Embed(
                        title='Trade Confirmed',
                        colour=ac.Colour.infoColour,
                        description=f'**{sender.name}** has confirmed the trade with you.'
                    )
                    user = self.bot.get_user(trade.waiting_on.id)
                    if user:
                        try:
                            await user.send(embed=confirm_embed)
                        except discord.Forbidden:
                            pass
                    if trade.confirm_1 == True and trade.confirm_2 == True:
                        for i in trade.inventory_1:
                            if not trade.player_2.addInv(i):
                                storage = ac.Storage(trade.player_2)
                                storage.add_item(i, True)
                        for i in trade.inventory_2:
                            if not trade.player_1.addInv(i):
                                storage = ac.Storage(trade.player_1)
                                storage.add_item(i, True)
                        trade.active = False
                    menu_embed = discord.Embed(
                        title='Trade Confirmed',
                        colour=ac.Colour.successColour
                    )
                    await message.edit(embed=menu_embed)
                    stage = 'cancel'
                    continue
                else:
                    stage = 'cancel'
                    continue
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
        if save:
            trade.save()

    @trade.command()
    async def new(self, ctx, member: discord.Member):
        adv1 = ac.Player(ctx.author.id)
        adv2 = ac.Player(member.id)
        if not adv1.loaded:
            embed = discord.Embed(
                title='Adventurer not found',
                colour=ac.Colour.errorColour,
                description='You do not have an adventurer'
            )
            await ctx.send(embed=embed)
            return
        if not adv2.loaded:
            embed = discord.Embed(
                title='Adventurer not found',
                colour=ac.Colour.errorColour,
                description=f'{member.display_name} does not have an adventurer'
            )
            await ctx.send(embed=embed)
            return
        trade = ac.Trade()
        trade.new(adv1, adv2)
        trade.save()
        embed = discord.Embed(
            title='Trade created',
            colour=ac.Colour.successColour,
            description=f'Use `{self.bot.CP}trade` to interact with it.'
        )
        await ctx.send(embed=embed)
        embed = discord.Embed(
            title=f'{adv1.name} has created a trade with you.',
            colour=ac.Colour.infoColour
        )
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

def setup(bot):
    bot.add_cog(Trade(bot))