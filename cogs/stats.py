import discord
from discord.ext.commands import Cog, command
from proj_stats import lines_of_code, find_files


def setup(bot):
    bot.add_cog(Stats(bot))


class Stats(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @command(name="lines-of-code", aliases=['loc', 'lol'], hidden=True)
    async def lines_of_code(self, ctx):
        count = lines_of_code()
        embed = discord.Embed(
            title=f"{count} Total Lines of Code",
            color=0xffff00,
            description=f"AdventureBot runs on {count} total lines of code. Be sure to congratulate the developers."
        )
        await ctx.send(embed=embed)
    
    @command(name="total-files", aliases=['tf'], hidden=True)
    async def total_files(self, ctx):
        count = len(list(find_files()))
        embed = discord.Embed(
            title=f"{count} Total Files",
            color=0xffff00,
            description=f"AdventureBot runs on {count} total files. Be sure to congratulate the developers."
        )
        await ctx.send(embed=embed)
    
    
