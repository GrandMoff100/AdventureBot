def setup(bot):
    global db
    global config
    db = bot.db
    config = bot.config
    


class Task:
    def __init__(self, name, user):
        self.name = name
        self.user = user

    async def run(self):
        """To be overwritten!"""
        ...


