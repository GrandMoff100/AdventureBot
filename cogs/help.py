import discord
import random
import time
from .fantasy._messages import HELP_MESSAGES
from discord.ext.commands import command, Cog, cooldown, BucketType
import asyncio


def setup(bot):
    global config
    config = bot.config
    bot.add_cog(Helper(bot))


GREENS = [
    0x3cb043,
    0xaef359,
    0x74b72e,
    0x234f1e,
    0x597d35,
    0xB0fc38,
    0xfdbb63,
    0x566d1d,
    0x03c04a,
    0xb2d3c2,
    0x3a5311,
    0x98bf64,
    0x03ac13,
    0x99edc3,
    0x32612d,
    0x728c69,
    0x02a80f,
    0x3ded97,
    0x354a21,
    0x607d3b
]


class Helper(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @command(name='help', aliases=['h'])
    @cooldown(2, 10, type=BucketType.user)
    async def help_command(self, ctx, command: str = None):
        """Get help for commands."""
        embed = discord.Embed(
            title=random.choice(HELP_MESSAGES),
            color=random.choice(GREENS)
        )
        embed.set_author(
            name=self.bot.user,
            url=self.bot.user.avatar_url,
            icon_url=self.bot.user.avatar_url
        )
        if command is None:
            await self.all_help(ctx, embed)
        else:
            await self.command_help(ctx, embed, command)


    async def all_help(self, ctx, embed):
        for name, cog in self.bot.cogs.items():
            val = ""
            for cmd in cog.walk_commands():
                if not cmd.hidden:
                    val += f"{' -'*len(cmd.parents)} `{cmd.name}`: {cmd.help}\n"
            
            if bool(val):
                embed.add_field(
                    name=name,
                    value=val.strip(),
                    inline=False
                )
        await ctx.send(embed=embed)
    
    async def command_help(self, ctx, embed, *command: str):
        command = " ".join(command)
        for name, cog in self.bot.cogs.items():
            if command in [com.qualified_name for com in cog.walk_commands() if not com.hidden]:
                com = [com for com in cog.walk_commands() if com.qualified_name == command][0]
                embed.add_field(
                    name=f"`{command}` help.",
                    value=f"*{com.help}*",
                    inline=False
                )
                embed.add_field(
                    name="Aliases",
                    value=" | ".join(["`%s`" % name for name in [com.name, *com.aliases]]),
                    inline=False
                )
                embed.add_field(
                    name="Arguments",
                    value=f"`<>` means required, `[]` means optional.\n**`{com.name} {com.signature}`**",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
        await ctx.send("Sorry, but I couldn't find that command. Try again?")


    @Cog.listener('on_ready')
    async def dm_admin(self):
        ids = self.bot.owner_ids
        admins = []
        for id in ids:
            await asyncio.sleep(0.2)
            admin = await self.bot.fetch_user(id)
            admins.append(admin)
        for admin in admins:
            await admin.send(f'```\n\nBot started at {time.time()}s\n\n```')
