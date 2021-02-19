import copy
import asyncio


def setup(bot):
    global db
    global config
    global store
    store = bot.store
    db = bot.db
    config = bot.config

    global get_rarity
    def get_rarity(weight: int):
        for rarity, spectrum in config['rarity-table'].items():
            low,hi = spectrum
            if low <= weight <= hi:
                return rarity
        return None


class Item:
    def __init__(self, name):
        self.name = name
        try:
            self._data = self._get_data()
        except KeyError:
            print(name)
            raise type('ItemError', (BaseException,), {"args": ['That item does not exist.']})
        self.cost = self._data['cost']
        self.recipe = self._data['recipe']
        self.attrs = self._data['attrs']
        self.rarity_int = self._data['rarity']
        self.rarity = get_rarity(self.rarity_int)

    def item_exists(name):
        return name in store['items']

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return "<Item name=\"{}\" data={}>".format(self.name, str(self._data)[:12]+"... ")


    def _get_data(self):
        return copy.copy(store['items'][self.name])

    @staticmethod
    def all_items():
        return {name: Item(name) for name in store['items']}

    def __getattribute__(self, name):
        if name.startswith("is_"):
            return bool(self.attrs.get(name[2:]))
        else:
            return super().__getattribute__(name)


class Inventory:
    def __init__(self, id):
        self.id = id
    
    async def init(self):
        if not await Inventory.is_inv(self.id):
            await Inventory.init_inv(self.id)

    @staticmethod
    async def is_inv(id):
        res = await db.get(type="inventory", id=id)
        return bool(res)

    @staticmethod
    async def init_inv(id):
        default = copy.copy(config["default-inventory"])
        default["id"] = id
        await db.insert(default)

    @property
    async def json(self):
        return (await db.get(type="inventory", id=self.id))[0]

    @property
    async def _contents(self):
        return (await self.json)["items"]

    @property
    async def contents(self):
        contents = await self._contents
        return {name: Item(name) for name in contents}


    async def quantity(self, name):
        return (await self._contents)[name]


    async def add_item(self, item, quantity):
        contents = await self._contents
        if item in contents:
            contents[item] += quantity
        else:
            contents[item] = quantity
        await db.update({"items": contents}, type="inventory", id=self.id)

    @staticmethod
    def create_item(name: str, rarity: int, cost: int, recipe: dict, attrs: dict):
        store['items'][name] = {
            "rarity": rarity,
            "cost": cost,
            "recipe": recipe,
            "attrs": attrs
        }
        store.save()

    @staticmethod
    def remove_item(name: str):
        del store['items'][name]
        config.save()
    
    @staticmethod
    def existing_items():
        return store['items']

