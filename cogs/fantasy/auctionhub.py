import random
import time
from .dbwrappers import UserAccs, setup as user_setup
from .dbwrappers.auction import Auction, setup as ah_setup
from discord import Embed, Color, User
from discord.ext.commands import command, Cog, errors, group, cooldown, BucketType
from utils.errors import BalanceError



def setup(bot):
    ah_setup(bot)
    user_setup(bot)
    global config
    global db
    db = bot.db
    config = bot.config
    bot.add_cog(AuctionHub(bot))


class AuctionHub(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command("auction", aliases=["ah"])
    async def auction_create(self, ctx, duration: int, starting_bid: int, *item: str):
        """Create an auction for an item"""
        item = ' '.join(item)
        
        id = str(ctx.author.id)

        useracc = UserAccs(id)
        await useracc.init()

        if item not in (await useracc.inv.json)["items"]:
            raise errors.UserInputError("You do not have that item.")
        
        await useracc.inv.add_item(item, -1)

        auction = Auction(
            str(random.randint(0, 1000000)),
            item,
            str(ctx.author.id),
            duration * 60,
            starting_bid
        )
        await self.auction_embed(ctx, auction)


    async def auction_embed(self, ctx, auction: Auction):
        embed = Embed(
            title=f"Auction for a {await auction.item}. Auction #{auction.ah_id}",
            description="React with :arrow_up: to bid.",
            color=0x000000
        )
        embed.add_field(
            name="Top Bid",
            value=f"${await auction.top_bid} by {await self.bot.fetch_user(int(auction.top_bidder))}"
        )
        embed.add_field(
            name="Next Bid",
            value=f"${await auction.next_bid}"
        )
        embed.add_field(
            name="Total bids",
            value=len(await auction.bids)
        )
        remaining = await auction.time_remaining
        hours = round(remaining / (60*60), 1)
        minutes = round(remaining / 60, 1)
        embed.add_field(
            name="Time remaining",
            value=f"{minutes} minutes | {hours} hours" if minutes > 0 else "**DONE**"
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('⬆️')


    def get_embed_id(self, embed):
        title = embed.title
        return int(title[title.rfind("#")+1:])

    @Cog.listener("on_reaction_add")
    async def bid_detect(self, reaction, user):
        message = reaction.message

        bidding = False
        if message.author == self.bot.user and user != self.bot.user:
            if message.embeds:
                if message.embeds[0].title.startswith("Auction for a"):
                    bidding = True
        if not bidding:
            return

        ah_id = self.get_embed_id(message.embeds[0])
        auction = Auction(str(ah_id))
        await auction.init()
        
        useracc = UserAccs(str(user.id))
        await useracc.init()
        
        
        if await auction.time_remaining <= 0:
            return

        next_bid = await auction.next_bid

        bids = await auction.bids
        refund = bids[-1]["coins"] if bids and bids[-1]["bidder"] == str(user.id) else 0

        if (await useracc.acc.pursecoins) + refund < next_bid:
            raise BalanceError("Not enough coins in purse to afford this auction.")

        if bids:
            prev_bid = bids[-1]
            await UserAccs(prev_bid["bidder"]).acc.add_to_purse(prev_bid["coins"])

        await useracc.acc.add_to_purse(-next_bid)
        await auction.bid(str(user.id), next_bid)

        await message.delete()
        await self.auction_embed(message.channel, auction)


    @command("collect", aliases=["col", "co", "c-ah"])
    async def collect(self, ctx):
        """Collect the auctions you made / were the highest bidder."""

        id = str(ctx.author.id)
        
        auctions = (await db.op([("end", "<=", time.time())], type="auction", owner=id))\
                 + (await db.op([("end", "<=", time.time())], type="auction", top_bidder=id))

        collected_coins = 0
        collected_items = []

        for auction in auctions:
            top_bidder = auction["top_bidder"] if auction["top_bidder"] else auction["owner"]
            if top_bidder == id and not auction["collected"][1]:
                collected_items.append(auction["item"])

                collected = auction["collected"]
                collected[1] = True
                await db.update({"collected": collected}, type="auction", id=auction["id"])

            elif auction["owner"] == id and not auction["collected"][0]:
                collected_coins += auction["bids"][-1]["coins"] if auction["bids"] else 0

                collected = auction["collected"]
                collected[0] = True
                await db.update({"collected": collected}, type="auction", id=auction["id"])

            if auction["collected"][1] and auction["collected"][0]:
                await db.remove(type="auction", id=auction["id"])

        useracc = UserAccs(id)
        await useracc.init()
        

        for i in collected_items:
            await useracc.inv.add_item(i, 1)
        await useracc.acc.add_to_purse(collected_coins)

        embed = Embed(
            title="Collected your auctions.",
            color=Color.green()
        )
        embed.add_field(name="Coins Collected", value=collected_coins)
        val = "\n".join(["**%s**" % x for x in collected_items])
        embed.add_field(
            name="Items collected",
            value=val if val else "None"
        )
        await ctx.send(embed=embed)


    @group("search", aliases=["srch"], invoke_without_command=True)
    async def search(self, ctx):
        """Search for auctions."""
        embed = Embed(
            title="Auction search methods",
            description="Use `search {search type} [arguments...]` to search for auctions.",
            color=Color.dark_green()
        )
        for com in self.search.walk_commands():
            embed.add_field(
                name=com.name,
                value=f"*{com.help}*\n`{com.qualified_name} {com.signature}`"
            )
        await ctx.send(embed=embed)

    @search.command("ending", aliases=["e"])
    @cooldown(1, 4, type=BucketType.user)
    async def search_by_time(self, ctx, results: int = 5):
        """Search for auctions ending soon."""
        if not 0 < results < 10:
            raise errors.UserInputError("results must be greater than 1 and less than 10")

        counter = 0
        ahs = await db.op([("end", ">", time.time()), ("end", "<", time.time()+60*10)], type="auction")

        if len(ahs) == 0:
            await ctx.send(embed=Embed(title=":warning: Couldn't find any auctions ending soon.",
                                       color=Color.red()))
        
        for auction in ahs:
            if counter >= results:
                break
            await self.auction_embed(ctx, Auction(auction["id"]))
            counter += 1

    @search.command("owner", aliases=["o"])
    @cooldown(1, 4, type=BucketType.user)
    async def search_owner(self, ctx, user: User = None, results: int = 5):
        """Search your/a user's auctions."""
        if user is None:
            user = ctx.author

        if not 0 < results < 10:
            raise errors.UserInputError("results must be greater than 1 and less than 10")

        counter = 0
        ahs = await db.get(type="auction", owner=str(user.id))

        if len(ahs) == 0:
            await ctx.send(embed=Embed(title=f":warning: Couldn't find any auctions created by {user}.",
                                       color=Color.red()))

        for auction in ahs:
            if counter >= results:
                break
            await self.auction_embed(ctx, Auction(auction["id"]))
            counter += 1

    @search.command("item", aliases=["i"])
    @cooldown(1, 4, type=BucketType.user)
    async def search_by_item(self, ctx, item: str, results: int = 5):
        """Search for item by it's name/part of it's name"""
        ahs = await db.find(item, "item", type="auction")
        counter = 0

        if len(ahs) == 0:
            await ctx.send(embed=Embed(title=f":warning: Couldn't find any auctions for {item}.",
                                       color=Color.red()))

        for auction in ahs:
            if counter >= results:
                break
            await self.auction_embed(ctx, Auction(auction["id"]))
            counter += 1
