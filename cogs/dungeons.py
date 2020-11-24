import adventure
import discord

from discord.ext import tasks, commands

class Dungeons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test_dungeon(self, ctx, other_player: discord.Member):
        adv = adventure.Player(ctx.author.id)
        adv_2 = adventure.Player(other_player.id)
        dungeon = adventure.Dungeon([adv, adv_2])
        dungeon.build_dungeon()
        message = await ctx.send('Testing')
        while True:
            _action, message = await dungeon.run_turn(self.bot, message)

def setup(bot):
    bot.add_cog(Dungeons(bot))