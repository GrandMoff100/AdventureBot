import discord
from .dbwrappers.inventory import Item
from .dbwrappers import UserAccs, setup as user_setup
from discord.ext.commands import command, Cog, UserInputError



def setup(bot):
    user_setup(bot)
    global store
    global config
    config = bot.config
    store = bot.store
    bot.add_cog(Market(bot))

    


class Market(Cog):
    def __init__(self, bot):
        self.bot = bot
        # Button stuff:
        self.market_msgs = {}

    @command(name="market", aliases=['m', 'shop', 'store'])
    async def store(self, ctx, page: int = 1, page_size: int = 12):
        items = [item for item in store['items'] if store['items'][item]['cost']]
        pages = []
        async for embed in self.market_embeds(items, page_size):
            pages.append(embed)
        
        title_page, *pages = pages
        title_msg = await ctx.send(embed=title_page)
        msg = await ctx.send(embed=pages[(page - 1) % len(pages)])
        
        # Button stuff:
        await msg.add_reaction('⬅️')
        await msg.add_reaction('➡️')
        await msg.add_reaction('🗑️')

        if ctx.channel.id in self.market_msgs:
            for x in self.market_msgs[ctx.channel.id][1:]:
                await x.delete()

        self.market_msgs[ctx.channel.id] = [[page, page_size], title_msg, msg]


    async def market_embeds(self, items, page_size, i=0):
        embed = discord.Embed(
            title="Buy an artifact!",
            color=0xd0a000,
            description='Welcome to the markets! This is where you can view items to buy and sell as well as check their prices.'
        )
        url = 'http://wiki.dominionstrategy.com/images/c/cc/Grand_MarketArt.jpg'
        embed.set_image(url=url)
        yield embed
        embed = discord.Embed(title="Page None:", color=0xd0a000)
        for item in items:
            if i % page_size == 0:
                page = int((i-i%page_size)/page_size) + 1
                if i != 0:
                    yield embed
                embed = embed = discord.Embed(title=f"Page {page}:", color=0xd0a000)
            price = Item(item).cost
            rarity = Item(item).rarity.capitalize()
            value = "*%s*\n**Price:** $%i" % (rarity, price)
            embed.add_field(
                name=item,
                value=value,
                inline=True
            )
            i += 1
        yield embed

    # Button stuff:
    @Cog.listener("on_reaction_add")
    async def market_paginator(self, reaction, user):
        message = reaction.message
        if user != self.bot.user and message.channel.id in self.market_msgs:
            if message in [x[2] for x in self.market_msgs.values()]:

                if reaction.emoji == '🗑️':
                    for x in self.market_msgs[message.channel.id][1:]:
                        await x.delete()
                    del self.market_msgs[message.channel.id]

                elif reaction.emoji in ('➡️', '⬅️'):
                    items = [item for item in store['items'] if store['items'][item]['cost']]
                    page, page_size = self.market_msgs[message.channel.id][0]

                    page += 1 if reaction.emoji == '➡️' else -1

                    pages = []
                    async for embed in self.market_embeds(items, page_size):
                        pages.append(embed)

                    title_page, *pages = pages
                    await self.market_msgs[message.channel.id][2].edit(embed=pages[(page - 1) % len(pages)])
                    await reaction.remove(user)

                    self.market_msgs[message.channel.id][0][0] = page

    @command(name='buy-artifact', aliases=['buy','bi'])
    async def buy_item(self, ctx, quantity: int, *item: str):
        name = ' '.join(item)
        id = str(ctx.author.id)
        useracc = UserAccs(id)
        await useracc.init()
        

        try:
            price = Item(name).cost
        except KeyError:
            embed = await self.item_not_exist_embed(name)
            await ctx.send(embed=embed)
            return
        price *= quantity

        if quantity < 1:
            raise UserInputError("You can't buy that amount of this item.")

        useracc.acc.add_to_purse(-price)
        useracc.inv.add_item(name, quantity)

        embed = await self.buy_item_embed(name, quantity)
        await ctx.send(embed=embed)


    async def buy_item_embed(self, name, quantity):
        embed = discord.Embed(
            title="You successfully bought %sx *%s*!" % (str(quantity), name),
            color=0x00ff00,
        )
        return embed


    async def item_not_exist_embed(self, item):
        embed = discord.Embed(
            title='That item does not exist!',
            color=0x00ff00,
            description=f'``{item}`` does not exist.'
        )
        return embed

    @command(name='sell-artifact', aliases=['sell', 'si'])
    async def sell_item(self, ctx, quantity: str, *item: str):
        name = ' '.join(item)
        id = str(ctx.author.id)
        useracc = UserAccs(id)
        await useracc.init()
        

        contents = useracc.inv._contents

        if quantity == 'all':
            quantity = contents[name]

        quantity = int(quantity)
        
        try:
            price = Item(name).cost
            
        except KeyError:
            embed = await self.item_not_exist_embed(name)
            await ctx.send(embed=embed)
            return
    
        print(quantity)
        price *= quantity
        price *= 0.9
        price = int(price - price % 1 + 1)

        if quantity < 1 or quantity > contents[name]:
            raise UserInputError("You can't sell that amount of this item.")

        useracc.acc.add_to_purse(price)
        useracc.inv.add_item(name, -quantity)

        embed = await self.sell_item_embed(name, quantity)
        await ctx.send(embed=embed)
    
    async def sell_item_embed(self, name, quantity):
        embed = discord.Embed(
            title="You sold %ix *%s%s*!" % (quantity, name, "'s" if quantity > 1 else ''),
            color=0x00ff00
        )
        return embed
