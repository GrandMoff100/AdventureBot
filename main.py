import discord
import os
from discord.ext.commands import Bot
from utils.util import Json, DBJson
from utils.events import register, on_event


class AdventureBot(Bot):
    exts = [
        'cogs.help', 'cogs.error', 'cogs.stats', 'cogs.admin',
        'cogs.fantasy.bank', 'cogs.fantasy.leaderboard', 'cogs.fantasy.items',
        'cogs.fantasy.auctionhub', 'cogs.fantasy.xp', 'cogs.fantasy.market',
        'cogs.fantasy.farming'
    ]

    def __init__(self, parent=True):
        config = Json('config.json')
        store = Json('items.json')

        db = DBJson()
        super().__init__(
            command_prefix=config['prefix'],
            help_command=None,
            description=config['description'],
            max_messages=config['max_messages'],
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name='Screams of the Devil',
            ),
            status=discord.Status.online,
            owner_ids=[
                config['owner-id'], 
                *config['admins']
            ]
        )

        self.config = config
        self.db = db
        self.store = store
        self.register = register
        self.on_event = on_event

        for ext in AdventureBot.exts:
            self.load_extension(ext)

        self.online = False

    async def on_ready(self):
        self.online = True
        print('Logged in as {} | ID: {}'.format(self.user, self.user.id))
        print(f"Using TinyDBWeb server at {os.getenv('TDBW_URL')}")


    async def on_message(self, message):
        if message.author != self.user:
            if message.content.startswith(self.command_prefix):
                async with message.channel.typing():
                    await self.process_commands(message)


    async def on_message_edit(self, old, message):
        if message.author != self.user:
            if message.content.startswith(self.command_prefix):
                async with message.channel.typing():
                    await self.process_commands(message)


bot = AdventureBot()
bot.run(os.getenv('ADVENTUREBOTTOKEN'))
