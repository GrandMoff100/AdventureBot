import json
import asyncio
import discord
import random
from .dbwrappers import UserAccs, setup as user_setup
from .dbwrappers.inventory import Item

from ..error import Errors
from discord.ext.commands import Cog, command, has_permissions, is_owner
from discord.utils import get



def setup(bot):
    user_setup(bot)
    global db
    global config
    global store
    store = bot.store
    db = bot.db
    config = bot.config
    bot.add_cog(Items(bot))


class Items(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_servers = set()
        self.item_msgs = {}

    @command(name='inventory', aliases=['inv', 'i', 'I'])
    async def inventory(self, ctx, user: discord.User = None):
        """View yours or another player's inventory."""
        if user is None:
            user = ctx.author
        id = str(user.id)
        useracc = UserAccs(id)
        await useracc.init()
        
        embed = await self.inventory_embed(user, useracc.inv)
        await ctx.send(embed=embed)


    async def inventory_embed(self, user, inv):
        embed = discord.Embed(
            title=f":card_box: {user.display_name}'s Stuff",
            color=0x964B00,
        )
        embed.set_thumbnail(url=user.avatar_url)
        invjson = await inv.json
        items = {}
        for item, count in invjson['items'].items():
            if count > 0:
                rarity = Item(item).rarity.capitalize()
                items['%ix %s' % (count, item)] ='*%s*' % rarity
        if len(items.keys()) == 0:
            items['No items'] = ":frowning2:"
        for field, value in items.items():
            embed.add_field(name=field, value=value, inline=False)
        return embed

    @command(name="set-artifact-channel", aliases=['artifacts-here','sach'])
    @has_permissions(administrator=True)
    async def set_item_channel(self, ctx):
        """Set channel for items to be spawned in."""
        if db.get(type="item-channel", server=str(ctx.guild.id)) != []:
            db.update({"id": str(ctx.channel.id)}, type="item-channel", server=str(ctx.guild.id))
        else:
            db.insert({"type": "item-channel", "server": str(ctx.guild.id), "id": str(ctx.channel.id)})
        
        embed = discord.Embed(
            title=f"Set item channel to `{ctx.channel.name}`.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


    @Cog.listener('on_message')
    async def message_counter(self, message):
        if message.guild and not message.author.bot:
            if message.guild not in self.active_servers:
                self.active_servers.add(message.guild)

    @Cog.listener('on_ready')
    async def spawn_items(self):
        while self.bot.online:
            await asyncio.sleep(90/(len(self.active_servers) + (0 if self.active_servers else 0.5)))
            #await asyncio.sleep(1)
            servers = list(self.active_servers)

            if len(servers) == 0:
                continue

            target = random.choices(servers, [server.member_count for server in servers], k=1)[0]
            
            channel = await db.get(type="item-channel", server=str(target.id))
            if not channel:
                continue
            else:
                channel = channel[0]["id"]

            item = random.choices(
                [item for item in list(store['items'].keys()) if store['items'][item]['rarity']],                
                [store['items'][item]["rarity"] for item in store["items"] if store['items'][item]['rarity']],                k=1
            )[0]

            msg = await self.item_embed(target, item, channel)
            self.active_servers = set()

            self.item_msgs[msg] = item
            await msg.add_reaction('✅')


    async def item_embed(self, guild, item: str, channel: str):
        embed = discord.Embed(
            title=f"A wild {item} appeared!",
            description="React with :white_check_mark: to claim it.",
            color=discord.Color.green()
        )
        channel = await self.bot.fetch_channel(int(channel))
        return await channel.send(embed=embed)


    @Cog.listener("on_reaction_add")
    async def item_reaction(self, reaction, user):
        message = reaction.message
        if message in self.item_msgs and user.id != self.bot.user.id:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            useracc = UserAccs(str(user.id))
            await useracc.init()
        
            await useracc.inv.add_item(self.item_msgs[message], 1)
            self.item_msgs.pop(message)


    @command(name='add-artifact', aliases=['ai', 'add-item'], hidden=True)
    @is_owner()
    async def add_item(self, ctx, name: str, *args):
        args = [None if arg == 'None' else arg for arg in args]
        args = [int(args) if arg.isdecimal() else arg for arg in args]
        for arg, i in zip(args, range(len(args))):
            try:
                d = json.loads('{"recipe": {"weapon": true}}')
            except json.decoder.JSONDecodeError as exc:
                embed = discord.Embed(
                    title=f'Generic Error: {exc.__class__.__name__}', # Generic error, Uncommon error, Rare error, Legendary error, MYTHICAL ERROR
                    color=0x0000ff,
                    description=str(exc)
                )
                await ctx.send(embed=embed)
                return
            if type(d) in [list, dict]:
                args[i] = d
        await UserAccs.Inventory.create_item(name, *args)
        embed = await self.item_add_success(name, *args)
        await ctx.author.send(embed=embed)


    async def item_add_success(self, name, rarity, cost):
        embed = discord.Embed(
            title=f"You successfully added {name}",
            description=f"It's rarity is now `{rarity}` and it costs `{cost}`",
            color=0x00ff00
        )
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        return embed

