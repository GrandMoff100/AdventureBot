from discord.ext.commands import Cog, command, Context, errors
from discord import Embed
import time
import discord

from .dbwrappers.inventory import Item
from .dbwrappers import UserAccs, setup as user_setup


def setup(bot):
    user_setup(bot)
    global config
    global db
    global items
    db = bot.db
    config = bot.config
    items = bot.store
    bot.add_cog(Farms(bot))


class Farms(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command("crops", aliases=["farm", "c"])
    async def view_crops(self, ctx: Context):
        useracc = UserAccs(str(ctx.author.id))
        await useracc.init()
        
        farm = useracc.farm
        embed = await self.crop_embed(ctx, (await farm.crops))
        await ctx.send(embed=embed)

    @command("plant", aliases=['p'])
    async def plant_crop(self, ctx: Context, amount: int, *crop_type: str):
        crop_type = ' '.join([c.capitalize() for c in crop_type])
        id = str(ctx.author.id)

        if amount < 1:
            raise errors.UserInputError("Amount of crops must be greater than 0.")
        if not Item.item_exists(crop_type):
            raise errors.UserInputError("That item does not exist.")
        if not Item(crop_type).attrs.get('plantable', False):
            raise errors.UserInputError("That item is not plantable.")

        useracc = UserAccs(id)
        await useracc.init()
        
        inv, farm = useracc.inv, useracc.farm

        if (await inv._contents).get(crop_type, 0) < amount:
            raise errors.UserInputError("You do not have enough of this item.")

        planted = 0
        for x in range(amount):
            if not await farm.plant_crop(crop_type):
                raise errors.UserInputError(f"Your farm cannot hold any more crops. I have planted {planted} {crop_type}.")
            await inv.add_item(crop_type, -1)
            planted += 1
        
        embed = Embed(
            title=f"Planted {amount} {crop_type}",
            description=":sunflower: Use `.crops` to view your crops",
            color=0xc7a423
        )
        await ctx.send(embed=embed)

    @command("harvest")
    async def harvest_crops(self, ctx: Context):
        id = str(ctx.author.id)

        useracc = UserAccs(id)
        await useracc.init()
        
        inv, farm = useracc.inv, useracc.farm

        harvested = []
        for crop in filter(lambda crop: crop.is_done, (await farm.crops)):
            drops = crop.drops
            harvested += drops
            for x in drops:
                await inv.add_item(x, 1)
            await farm.remove_crop(crop)

        embed = await self.harvested_embed(harvested)
        await ctx.send(embed=embed)


    async def crop_embed(self, ctx, crops):
        embed = Embed(
            title=f"{ctx.author}'s Farm",
            color=0xc7a423
        )
        if not crops:
            embed.add_field(
                name="**:warning: You don't have any crops!**",
                value="Use `plant <seed>` to plant some! Seeds are items in your inventory."
            )
            embed.set_image(url='https://images-ext-1.discordapp.net/external/HB0Kr4sPFJU-HUFNho9FLTz1GpjXfpwaZ6teY1xfd8o/%3Fwidth%3D300%26height%3D200/https/images-ext-2.discordapp.net/external/77nfFuhRrOxats55ULbxIkwPl9NHRKdfE0PYDjXI6fA/https/thumbs.dreamstime.com/b/cartoon-color-dry-land-scene-concept-vector-flat-design-include-sun-desert-tree-illustration-172002417.jpg?width=270&height=180')
            return embed
        
        embed.set_image(url='https://images-ext-1.discordapp.net/external/PCPV6DFmXHgWAlpOB3ALMrKrU8wYSg7qY6Q2Y2cu2Pk/%3Fwidth%3D400%26height%3D200/https/images-ext-1.discordapp.net/external/wRRKC7zsyI6wwAZapgds_dJ1eAmOAybrwyMbDIiflUI/https/i.pinimg.com/originals/5c/6f/b4/5c6fb48945080b9a0d55b951cefc4218.jpg?width=360&height=180')
        for crop in crops:
            embed.add_field(
                name=crop.name,
                value=f"{round((crop.grow_time - time.time()) / 60)} minutes" if not crop.is_done else "**DONE**"
            )
        return embed


    async def harvested_embed(self, harvested):
        harvested = [crop.name if hasattr(crop, "name") else crop for crop in harvested]
        harvested = {crop: harvested.count(crop) for crop in harvested}
        embed = discord.Embed(
            title=":sunflower: You Harvested Some Crops!",
            color=0xf6a90f
        )
        embed.add_field(name='Havested', value='\n'.join(["**%s:** *%i*" % (crop, count) for crop, count in harvested.items()]))
        return embed
