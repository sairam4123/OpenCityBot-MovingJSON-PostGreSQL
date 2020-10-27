import os

from Bot.bot import MyBot

TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
DEFAULT_PREFIX = os.getenv('DEFAULT_PREFIX').replace("'", '"')

bot = MyBot(DATABASE_URL, DEFAULT_PREFIX)

bot.run(TOKEN)
