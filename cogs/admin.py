import discord
from discord.ext.commands import Cog, command, is_owner


def setup(bot):
    global config
    config = bot.config
    bot.add_cog(Admin(bot))


class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot

    def success_embed(self, task: str):
        embed = discord.Embed(title=f':white_check_mark: {task}',
                              color=0x00ff00)
        return embed

    @command(name='activity', hidden=True)
    @is_owner()
    async def set_activity(self, ctx, type: str, name: str):
        """Set bot activity."""
        activity = discord.Activity(type=getattr(discord.ActivityType, type),
                                    name=name)
        await self.bot.change_presence(activity=activity)
        await ctx.send(
            embed=self.success_embed('Successfully changed presence.'))

    @command(name='status', hidden=True)
    @is_owner()
    async def set_status(self, ctx, type: str):
        """Set bot status."""
        await self.bot.change_presence(status=getattr(discord.Status, type))
        await ctx.send(embed=self.success_embed('Successfully changed status.')
                       )

    @command(name='quit', hidden=True)
    @is_owner()
    async def quit_bot(self, ctx):
        """Shut down bot."""
        await ctx.send(embed=self.success_embed('Disconnecting now.'))
        self.bot.online = False
        await self.bot.close()
        exit(3)

    @command(name='clean', hidden=True)
    @is_owner()
    async def clean(self, ctx, step: int = 20, limit: int = 1000):
        await ctx.message.delete()
        lines, count = [], 0

        for guild in self.bot.guilds:
            for channel in guild.channels:
                if str(channel.type) == 'text':
                    async for msg in channel.history(oldest_first=False,
                                                     limit=limit):
                        if msg.author == self.bot.user or msg.content.startswith(
                                self.bot.command_prefix):
                            try:
                                await msg.delete()
                                count += 1
                            except discord.ext.commands.MissingPermissions as exc:
                                await ctx.send(exc)
                                break

        lines, i = [' '.join(line) for line in lines], 0
        while True:
            sel = lines[i:i + step]
            if sel == []:
                break
            await ctx.author.send('```%s```' % "\n".join(sel))
            i += step
        embed = discord.Embed(
            title=f"I cleansed my servers of {count} uneeded and old messages.",
            color=0x00ff00,
        )
        await ctx.send(embed=embed)

    @command(name="set-balance", hidden=True)
    @is_owner()
    async def set_balance(self, ctx, amount: int):
        id = str(ctx.author.id)

        if amount > 50_000:
            return
        #useracc = UserAccs(id)
        #await useracc.init()

    @command('run-as', aliases=['ra'], hidden=True)
    @is_owner()
    async def run_as(self, ctx, user: discord.User, cmd: str):
        ctx.message.content = cmd
        ctx.message.author = user
        await self.bot.on_message(ctx.message)
