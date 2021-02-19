import copy
import asyncio



def setup(bot):
    global config
    global db
    db = bot.db
    config = bot.config
 

class ExperienceAccount:
    def __init__(self, id):
        self.id = id
    
    async def init(self):
        if not await ExperienceAccount.is_exp_account(self.id):
            await ExperienceAccount.init_exp_acount(self.id)
        
    @staticmethod
    async def init_exp_acount(id): 
        default = copy.copy(config['default-xp'])
        default["id"] = id
        await db.insert(default)
    
    @staticmethod
    async def is_exp_account(id):
        return bool(await db.get(type="xp", id=id))

    @property
    async def json(self):
        return await db.get(type="xp", id=self.id)[0]

    async def add_xp(self, type: str, amount: int):
        curr_xp = (await self.json)["xp"]
        curr_xp[type] += amount
        await db.update({"xp": curr_xp}, type="xp", id=self.id)

    async def get_xp(self, type: str):
        return (await self.json)["xp"][type]
