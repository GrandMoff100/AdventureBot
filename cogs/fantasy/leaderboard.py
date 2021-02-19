from .dbwrappers import UserAccs, setup as user_setup
from discord.ext.commands import Cog, command

import discord


def setup(bot):
    user_setup(bot)
    global db
    db = bot.db
    bot.add_cog(Leaderboard(bot))
    

class Leaderboard(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @command('leaderboard', aliases=['l'])
    async def leaderboard(self, ctx, type: str = 'net-worth'):  # Why not use amount in bank? Yeah that would be faster
        users = UserAccs.user_ids()
        
        if type == 'net-worth':
            amounts = {id:(user := UserAccs(id)).acc.pursecoins + user.acc.bankcoins for id in users}
        elif type == 'xp':
            amounts = {id: sum(UserAccs(id).xp.json['xp'].values()) for id in users}
        elif type == 'rarest-items':
            pass
        else:
            embed = discord.Embed(
                title="Invalid User Sorting Method",
                color=0xffa500
            )
            return await ctx.send(embed=embed)
        
        amounts = list(amounts.items())
        amounts.sort(key=lambda x: x[1], reverse=True)
        embed = await self.leaderboard_embed(type, amounts)
        await ctx.send(embed=embed)

    async def leaderboard_embed(self, type, amounts):
        embed = discord.Embed(
            title="Leaderboard for ``{}``".format(type.upper()),
            color=0xffa500,
            description="```\n{}\n```".format(
                "\n\n".join(['%s.  %s • %i' % (i + 1, amounts[i][0], amounts[i][1]) for i in range(len(amounts))])
            )
        )
        return embed

        




