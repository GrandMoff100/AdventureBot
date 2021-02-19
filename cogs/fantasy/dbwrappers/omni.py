from .xpacc import ExperienceAccount as XP, setup as xp
from .account import Account as Acc, setup as account
from .inventory import Inventory as Inv, setup as inventory
from .farms import Farm as F, setup as farm
from utils.util import Json


def setup(bot):
    inventory(bot)
    account(bot)
    farm(bot)
    xp(bot)
    global users
    users = Json('users.json')


class UserAccs:
    Account = Acc
    Inventory = Inv
    Farm = F
    ExperienceAccount = XP

    def __init__(self, id: str):
        users[id] = True
        users.save()
        self.id = id
    
    async def init(self):
        self.inv = Inv(self.id)
        await self.inv.init()
        self.farm = F(self.id)
        await self.farm.init()
        self.acc = Acc(self.id)
        await self.acc.init()
        self.xp = XP(self.id)
        await self.xp.init()
        
    @staticmethod
    def user_ids():
        return list(users)

