import asyncio
import discord
import math
import random
import time

from ._messages import (
    FAVOR_MESSAGES,
    WORK_MESSAGES,
    PROMOTED_MESSAGES,
    STEAL_FAIL_MESSAGES,
    STEAL_SUCCESS_MESSAGES,
    EMPTY_STEAL_MESSAGES,
    GIVE_MESSAGES
)

from .dbwrappers import UserAccs, setup as user_setup
from discord.ext.commands import Cog, command, cooldown, BucketType, UserInputError



def setup(bot):
    user_setup(bot)
    global config
    global bank
    bank = bot.db
    config = bot.config
    bot.add_cog(Money(bot))

class Money(Cog):
    def __init__(self, bot):
        self.bot = bot
        self._interest_rate = config['interest-rate']
        self._interest_wait = config['interest-wait']

    @command(name='balance', aliases=['bal', 'b', 'bank'])
    async def balance(self, ctx, user: discord.User = None):
        """View your or another player's bank, purse, and salary."""
        if not user:
            user = ctx.author
        id = str(user.id)

        embed = await self.bank_embed(id, url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    async def bank_embed(self, id, url):
        user = await self.bot.fetch_user(int(id))
        embed = discord.Embed(
            title=":money_with_wings: %s's Money" % user.display_name,
            color=0x000000
        )
        embed.set_thumbnail(url=url)

        useracc = UserAccs(id)
        await useracc.init()

        b_coins = await useracc.acc.bankcoins
        p_coins = await useracc.acc.pursecoins
        if float(int(b_coins)) != b_coins:
            await useracc.acc._set_bank(int(b_coins))
        if float(int(p_coins)) != p_coins:
            await useracc.acc._set_purse(int(p_coins))

        fields = {
            'Bank :bank:': '$%s' % str(int(b_coins)),
            'Purse :moneybag:': '$%s' % str(int(p_coins)),
        }

        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
        
        embed.add_field(
            name='Salary per Work',
            value='$%s' % str(await useracc.acc.salary),
            inline=False
        )
        embed.set_thumbnail(url=str(user.avatar_url))

        return embed

    @command(name='work', aliases=['w', 'labor'])
    @cooldown(rate=1, per=60*60, type=BucketType.user)
    async def work(self, ctx):
        """Work to make money."""
        embed = await self.work_embed(str(ctx.author.id))
        await ctx.send(embed=embed)

        if random.choice([False]*99+[True]):
            embed = await self.promoted_embed(str(ctx.author.id))
            await ctx.send(embed=embed)


    async def work_embed(self, id):
        useracc = UserAccs(id)
        await useracc.init()

        sal = await useracc.acc.salary

        await useracc.acc.add_to_purse(sal)
        embed = discord.Embed(
            title="You worked!",
            color=0x00ff00,
            description=random.choice(WORK_MESSAGES)
        )

        embed.add_field(
            name='You Earned...',
            value='$'+str(sal)
        )

        embed.set_thumbnail(
            url='https://cdn.iconscout.com/icon/free/png-256/office-building-working-place-infrastructure-real-estate-emoj-symbol-30755.png'
        )
        return embed
    
    async def promoted_embed(self, id):
        embed = discord.Embed(
            title="You got promoted!",
            color=0x00ff00,
            description=random.choice(PROMOTED_MESSAGES)
        )
        useracc = UserAccs(id)
        await useracc.init()
        
        amount = int(await useracc.acc.salary * 1.2)
        useracc.acc.set_salary(amount)

        embed.add_field(
            name="New Salary...",
            value='$'+str(amount)
        )
        embed.set_thumbnail(url='https://thumbs.dreamstime.com/b/grunge-red-promoted-word-round-rubber-seal-stamp-white-background-grunge-red-promoted-word-round-rubber-seal-stamp-white-149415841.jpg')
        return embed


    @command(name='favor', aliases=['f'])
    @cooldown(rate=1, per=60*60, type=BucketType.user)
    async def favor(self, ctx):
        """Do a small favor."""
        embed = await self.favor_embed(str(ctx.author.id))
        await ctx.send(embed=embed)

    async def favor_embed(self, id):
        useracc = UserAccs(id)
        await useracc.init()
        
        amount = random.randint(1, int(await useracc.acc.salary/3))
        await useracc.acc.add_to_purse(amount)
        embed = discord.Embed(
            title='You did someone a favor!',
            color=0x00ff00,
            description=random.choice(FAVOR_MESSAGES) % str(amount)
        )
        embed.add_field(
            name='You Earned...',
            value='$'+str(amount)
        )
        embed.set_thumbnail(url='https://cdn.iconscout.com/icon/free/png-256/office-building-working-place-infrastructure-real-estate-emoj-symbol-30755.png')
        return embed

    @command(name='deposit', aliases=['dep', 'd'])
    async def dep(self, ctx, amount: str):
        """Deposit coins in purse into the bank (to prevent stealing)."""
        id = str(ctx.author.id)

        useracc = UserAccs(id)
        await useracc.init()
        
        if amount == 'all':
            amount = (await useracc.acc.pursecoins)
        amount = int(amount)
        await useracc.acc.deposit(amount)
        embed = await self.deposit_embed(amount, useracc.acc)
        await ctx.send(embed=embed)


    async def deposit_embed(self, amount, acc):
        embed = discord.Embed(
            title="You deposited $%i" % amount,
            color=0x00ff00
        )
        fields = {
            'Bank :bank:': '$%s' % str(await acc.bankcoins),
            'Purse :moneybag:': '$%s' % str(await acc.pursecoins),
        }
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
        embed.set_thumbnail(url="https://lh3.googleusercontent.com/proxy/Dht1YmQ2y75hIJrtJkbyynnQmQK0y-m9FtcldLHIieJ2Ywt1q8uaqiEQqSU1oosWN3YVks5yDb6r8V1MVkYa9TiyxjxSKWPI")
        return embed

    @command(name='withdraw', aliases=['wd'])
    async def withdraw(self, ctx, amount: str):
        """Withdraw coins from bank and put into purse."""
        id = str(ctx.author.id)
        useracc = UserAccs(id)
        await useracc.init()
        
        if amount == 'all':
            amount = (await useracc.acc.bankcoins)
        amount = int(await useracc.amount)
        await useracc.acc.withdraw(amount)
        embed = await self.withdraw_embed(amount, useracc.acc)
        await ctx.send(embed=embed)


    async def withdraw_embed(self, amount, acc):
        embed = discord.Embed(
            title="You withdrew $%i" % amount,
            color=0x00ff00
        )
        fields = {
            'Bank :bank:': '$%s' % str(await acc.bankcoins),
            'Purse :moneybag:': '$%s' % str(await acc.pursecoins),
        }
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
        embed.set_thumbnail(url="https://lh3.googleusercontent.com/proxy/Dht1YmQ2y75hIJrtJkbyynnQmQK0y-m9FtcldLHIieJ2Ywt1q8uaqiEQqSU1oosWN3YVks5yDb6r8V1MVkYa9TiyxjxSKWPI")
        return embed

    @command(name='steal', aliases=['s'])
    @cooldown(rate=1, per=60*60, type=BucketType.user)
    async def steal(self, ctx, user: discord.User):
        """Try to steal from someone."""
        id = str(ctx.author.id)
        target_id = str(user.id)
        
        useracc = UserAccs(id)
        await useracc.init()
        
        target = UserAccs(target_id)
        await target.init()
        

        b = await target.acc.pursecoins
        a = await useracc.acc.pursecoins

        if b == 0:
            embed = await self.empty_steal_embed()
            await ctx.send(embed=embed)
            return

        chance = int(math.floor(100*(b-a)/(b+a)))
        if chance < 0:
            chance = 0

        if random.choice([True]*chance+[False]*(100-chance)):
            embed = await self.steal_success_embed(useracc.acc, target.acc, a, b, chance/100)
        else:
            embed = await self.steal_fail_embed(ctx, user)
        await ctx.send(embed=embed)


    async def steal_success_embed(self, acc, target, a, b, chance):
        embed = discord.Embed(
            title="Success!",
            description=random.choice(STEAL_SUCCESS_MESSAGES),
            color=0x00ff00
        )
        amount = int(b * (1+chance)/8 + a/2)
        acc.add_to_purse(amount)
        target.add_to_purse(-amount)
        embed.add_field(
            name="You stole...",
            value="$"+str(amount),
            inline=True
        )
        embed.add_field(
            name="Your coins...",
            value="$"+str(await acc.pursecoins),
            inline=True
        )
        return embed


    async def steal_fail_embed(self, ctx, user):
        embed = discord.Embed(
            title=f"You failed to steal from {user}! :frowning2:",
            description=random.choice(STEAL_FAIL_MESSAGES),
            color=0xff0000
        )
        return embed
    
    async def empty_steal_embed(self):
        embed = discord.Embed(
            title='There was nothing to steal.',
            color=0xff0000,
            description=random.choice(EMPTY_STEAL_MESSAGES)
        )
        embed.set_thumbnail(url='https://external-preview.redd.it/5WPmHdiR4ELHbFJbme7_Lppq7iFuDCeOG3rYvJTh5kk.jpg?auto=webp&s=7efde69aa4e7b7c0291e8b7a3a6e7f88a5d23ef2')
        return embed
    
    @command(name='give', aliases=['g'])
    async def give(self, ctx, user: discord.User, amount: str):
        """Give away coins to a player."""
        id = str(ctx.author.id)
        useracc = UserAccs(id)
        await useracc.init()
        
        target_id = str(user.id)
        target = UserAccs(target_id)
        await target.init()
        
        
        if amount == 'all':
            amount = (await useracc.acc.pursecoins)
        amount = int(amount)
        if amount < 0:
            raise UserInputError("You can't give negative coins.")
         
        await useracc.acc.add_to_purse(-amount)
        target.acc.add_to_purse(amount)
        

        embed = await self.give_embed(user, amount)
        await ctx.send(embed=embed)
    
    async def give_embed(self, user, amount):
        embed = discord.Embed(
            title=f'You gave {user.display_name} ${amount}!',
            color=0x00ff00,
            description=random.choice(GIVE_MESSAGES)
        )
        embed.set_thumbnail(url='https://thumbs.dreamstime.com/b/black-isolated-outline-icon-gift-box-open-hands-white-background-line-two-give-make-present-143784239.jpg')
        return embed
    
    @Cog.listener("on_ready")
    async def bank_interest(self):
        while self.bot.online:
            await asyncio.sleep(self._interest_wait)
            for acc in UserAccs.Account.all_accounts():
                useracc = UserAccs(acc['id'])
                await useracc.init()
                await useracc.acc.add_to_bank(int(await acc.bankcoins * self._interest_rate))
            
