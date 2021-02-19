import copy
import time
import asyncio



def setup(bot):
    global config
    global db
    db = bot.db
    config = bot.config


class Auction:
    async def __init__(self, id, *args):
        self.id = id
    
    async def init(self, *args):
        if not await Auction.is_auction(self.id):
            await Auction.init_auction(self.id, *args)
        

    @staticmethod
    async def is_auction(id):
        return bool(await db.get(type="auction", id=id))

    @staticmethod
    async def init_auction(id, item, user_id, duration, start_bid):
        default = copy.copy(config["default-auction"])
        default["id"] = id
        default["item"] = item
        default["owner"] = user_id
        default["end"] = duration + time.time()
        default["start-bid"] = start_bid
        default["top_bidder"] = user_id
        await db.insert(default)

    @property
    async def json(self):
        return await db.get(type="auction", id=self.id)[0]

    @property
    async def item(self):
        json = await self.json
        return json["item"]

    @property
    async def bids(self):
        json = await self.json
        return json["bids"]

    @property
    async def top_bid(self):
        json = await self.json
        return json["bids"][-1]["coins"] if json["bids"] else json["start-bid"]
    
    @property
    async def next_bid(self):
        return int(await self.top_bid * 1.15 + 10)

    @property
    async def top_bidder(self):
        json = await self.json
        return json["bids"][-1]["bidder"] if json["bids"] else json["owner"]

    @property
    async def time_remaining(self):
        json = await self.json
        return json["end"] - time.time()


    async def bid(self, bidder, bid):
        bid_json = {"bidder": bidder, "coins": bid}
        json = await self.json()
        bids = json["bids"]
        bids.append(bid_json)
        await db.update({"bids": bids, "top_bidder": str(bidder)}, type="auction", id=self.id)

