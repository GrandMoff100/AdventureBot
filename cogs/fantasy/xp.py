import copy
import discord
import io

from .dbwrappers import UserAccs, setup as user_setup
from discord.ext.commands import Cog, command, Context
from io import BytesIO


def setup(bot):
    user_setup(bot)
    global config
    config = bot.config
    bot.add_cog(Experience(bot))



class Experience(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name='myxp', aliases=['xp', 'x'])
    async def xp(self, ctx: Context):
        id = str(ctx.author.id)

        useracc = UserAccs(id)
        await useracc.init()
        
        xp = {type: useracc.xp.get_xp(type) for type in config['default-xp']['xp']}
        
        embed = await self.xp_embed(xp)

        await ctx.send(embed=embed)


    async def xp_embed(self, xp):
        embed = discord.Embed(
            title="Your AdventureBot Skills",
            color=0x00aa00
        )
        for xptype, amount in xp.items():
            level, remains, target = self.get_level(amount)
            embed.add_field(
                name=xptype.capitalize(),
                value=f"Level: **{level + 1}**\n **{remains}** of **{target}**xp",
                inline=True
            )
        return embed

    def level_thresholds(self):
        for i in range(100):
            yield i, int(10 * config['xp-scale']**(i))


    def get_level(self, amount):
        for level, threshold in self.level_thresholds():
            if amount > threshold:
                amount -= threshold
            else:
                return amount, level, threshold
