import discord
import logging

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

    @commands.command()
    async def trade(self, ctx):
        adv = ac.Player(ctx.author.id)
        if not adv.loaded:
            raise ac.InvalidAdventurer('Could not load adventurer')
        trades = []
        stage = 'menu'
        while stage != 'cancel':
            if stage == 'menu':
                menu_embed = discord.Embed(
                    title='Trades',
                    colour=ac.Colour.activeColour)
                menu_embed.set_author(name=adv.name, icon_url=ctx.author.avatar_url)
                description = ''
                trade_ids = adv.get_trades()
                trades.clear()
                if trade_ids:
                    for i, indx in enumerate(trade_ids, start=1):
                        trade = ac.Trade()
                        trade.load(indx)
                        trades.append(trade)
                        name = f'**{c}.** {trade.player_1.name} -> {trade.player_2.name}'
                        value = f'Waiting on: {trade.waiting_on.name}'

def setup(bot):
    bot.add_cog(Trade(bot))