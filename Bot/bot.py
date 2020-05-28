import os

import asyncpg
import discord
from discord.ext import commands, tasks


TOKEN = os.getenv('DISCORD_TOKEN')
BOT_IS_READY = False


async def get_prefix(bot_1, message):
    if message.channel.type == discord.ChannelType.private:
        return commands.when_mentioned_or(['i!', 'i?'])(bot_1, message)
    prefixes = await bot_1.pg_conn.fetchrow("""
    SELECT prefixes FROM prefix_data
    WHERE guild_id = $1
    """, message.guild.id)
    if not prefixes:
        await bot_1.pg_conn.execute("""
        INSERT INTO prefix_data (guild_id, prefixes)
        VALUES ($1, $2)
        """, message.guild.id, ["i!", "i?"])
        return commands.when_mentioned_or(*['i!', 'i?'])(bot_1, message)
    return commands.when_mentioned_or(*prefixes[0])(bot_1, message)


bot = commands.Bot(command_prefix=get_prefix)
init_cogs = [f'Bot.cogs.{filename[:-3]}' for filename in os.listdir('Bot/cogs') if filename.endswith('.py')]


async def connection_for_pg():
    bot.pg_conn = await asyncpg.connect(password="1234", port="5858", host="localhost", user="postgres", database="postgres")


@bot.event
async def on_ready():
    global BOT_IS_READY
    await connection_for_pg()
    for guild_index, guild in enumerate(bot.guilds):
        print(
            f'{bot.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )

        members = '\n - '.join([member.name for member in guild.members])
        print(f'Guild Members of {guild.name} are:\n - {members}')
        if guild_index != (len(bot.guilds) - 1):
            print('\n\n\n', end="")
        BOT_IS_READY = True


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

for filename in os.listdir('Bot/cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'Bot.cogs.{filename[:-3]}')


@tasks.loop(seconds=10)
async def add_guild_to_db():
    await bot.wait_until_ready()
    if BOT_IS_READY:
        for guild in bot.guilds:
            guild_data = await bot.pg_conn.fetchrow("""
            SELECT * FROM cogs_data
            WHERE guild_id = $1
            """, guild.id)
            if not guild_data:
                await bot.pg_conn.execute("""
                INSERT INTO cogs_data (guild_id, enabled, disabled)
                VALUES ($1, $2, $3)
                """, guild.id, init_cogs, ["None"])


# @add_guild_to_db.error
# async def add_guild_to_db_error(error):
#     raise error


add_guild_to_db.start()

bot.run(TOKEN)
