import copy
import time
import random
import asyncio

def setup(bot):
    global config
    global db
    global items
    db = bot.db
    config = bot.config
    items = bot.store


class Crop:
    def __init__(self, vals):
        self.name = vals[0]
        self.grow_time = vals[1]
        self.grow_drops = items["items"][self.name]["attrs"]["grow-drops"]

    def __repr__(self):
        return "<%s>" % self.name

    @staticmethod
    def init_json(crop_type):
        return (crop_type, time.time() + items["items"][crop_type]["attrs"]["grow-time"])

    @staticmethod
    def init(crop_type):
        return Crop(Crop.init_json(crop_type))

    @property
    def json(self):
        return (self.name, self.grow_time)

    @property
    def is_done(self):
        return self.grow_time <= time.time()

    @property
    def drops(self):
        drops = self.grow_drops["guaranteed"]
        rand_drops = self.grow_drops["rand"]

        for x, y in rand_drops:
            rand = random.randint(0, 100)
            if rand <= x:
                drops += y

        return drops


class Farm:
    def __init__(self, id):
        self.id = id

    async def init(self):
        if not await self.is_farm(self.id):
            await self.init_farm(self.id)

    @staticmethod
    async def is_farm(id):
        return bool(await db.get(type="farm", id=id))

    @staticmethod
    async def init_farm(id):
        farm = copy.copy(config["default-farm"])
        farm["id"] = id
        await db.insert(farm)

    @property
    async def json(self):
        return (await db.get(type="farm", id=self.id))[0]

    @property
    async def crops(self):
        crops = (await self.json)["growing"]
        return [Crop(crop) for crop in crops]


    async def plant_crop(self, crop_type):
        crops = await self.crops
        if len(crops) > (await self.json)["max-crops"]:
            return False

        crop = Crop.init(crop_type)
        new_crops = [c.json for c in crops] + [crop.json]

        await db.update({"growing": new_crops}, type="farm", id=self.id)

        return True


    async def remove_crop(self, crop):
        crops = (await self.json)['growing']
        if not isinstance(crop, Crop):
            crop = Crop(crop)
        crops.remove([crop.name, crop.grow_time])
        await db.update({"growing": crops}, type="farm", id=self.id)
