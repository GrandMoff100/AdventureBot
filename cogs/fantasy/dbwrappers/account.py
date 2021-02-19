import copy
import asyncio
from utils.errors import AmountError, BalanceError



def setup(bot):
    global config
    global bank
    bank = bot.db
    config = bot.config


class Account:
    def __init__(self, id: str):
        self.id = id
    
    async def init(self): # Ah yes
        if not await self.is_account(self.id):
            await self.init_account(self.id)


    @staticmethod
    async def is_account(id):
        return bool(await bank.get(id=id, type="monetary"))

    @staticmethod
    async def init_account(id):
        default = copy.copy(config["default-money"])
        default['id'] = id
        await bank.insert(default)

    @staticmethod
    async def remove_account(id):
        await bank.remove(id=id, type="monetary")

    @property
    async def json(self):
        return (await bank.get(id=self.id, type="monetary"))
    
    @property
    async def bankcoins(self):
        return (await self.json)[0]["bank"]["coins"]

    @property
    async def pursecoins(self):
        return (await self.json)[0]['purse']['coins']

    async def can_deposit(self, amount: int):
        return (await self.pursecoins) >= amount and amount >= 0

    async def can_withdraw(self, amount: int):
        return (await self.bankcoins) >= amount and amount >= 0

    async def _add_bank(self, amount):
        await bank.update({"bank": {"coins": self.bankcoins+amount}}, id=self.id, type="monetary")

    async def _add_purse(self, amount):
        await bank.update({"purse": {"coins": self.pursecoins+amount}}, id=self.id, type="monetary")

    async def _set_bank(self, amount):
        await bank.update({"bank": {"coins": amount}}, id=self.id, type="monetary")

    async def _set_purse(self, amount):
        await bank.update({"purse": {"coins": amount}}, id=self.id, type="monetary")


    async def deposit(self, amount: int):
        if await self.can_deposit(amount):
            await self._add_bank(amount)
            await self._add_purse(-amount)
        else:
            raise AmountError(amount)

    async def withdraw(self, amount: int):
        if await self.can_withdraw(amount):
            await self._add_bank(-amount)
            await self._add_purse(amount)
        else:
            raise AmountError(amount)
    
    async def add_to_bank(self, amount: int):
        if (await self.bankcoins) + amount >= 0:
            await self._add_bank(amount)
        else:
            raise BalanceError("You don't have enough coins to do that.")

    async def add_to_purse(self, amount: int):
        if (await self.pursecoins) + amount >= 0:
            await self._add_purse(amount)
        else:
            raise BalanceError("You don't have enough coins to do that.")
  
    @property
    async def salary(self):
        return (await bank.get(id=self.id, type="monetary"))[0]["salary"]

    async def set_salary(self, value: int):
        await bank.update({"salary": value}, id=self.id, type="monetary")

    @staticmethod
    async def all_accounts():
        return await bank.get(type="monetary")