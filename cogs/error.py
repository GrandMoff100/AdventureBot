import discord
from discord.ext.commands import Cog, command
from utils.util import Json



def setup(bot):
    bot.add_cog(Errors(bot))


class Errors(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @Cog.listener("on_command_error")
    async def error_handler(self, ctx, error):
        errname = error.__class__.__name__
        errargs = error.args

        embed = discord.Embed(
            title=f'Generic Error: {errname}', # Generic error, Uncommon error, Rare error, Legendary error, MYTHICAL ERROR
            color=0x0000ff,
            description=str(error) if str(error) else "Unknown"
        )
        raise error
        await ctx.send(embed=embed)
