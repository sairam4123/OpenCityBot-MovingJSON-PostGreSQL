import datetime
import os
from itertools import cycle

import asyncpg
import discord
from discord.ext import commands, tasks
from quart import Quart


TOKEN = os.getenv('DISCORD_TOKEN')
CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')

BOT_IS_READY = False
PREFIX = os.getenv('DEFAULT_PREFIX')
DELIMITER = os.getenv('DEFAULT_DELIMITER_FOR_ENV')
TICKET_EMOJI = os.getenv('DEFAULT_TICKET_EMOJI')
IP_ADDRESS = os.getenv('IP_ADDRESS')
PORT_NUMBER = os.getenv('PORT_NUMBER')


async def get_prefix(bot_1, message):
    if message.channel.type == discord.ChannelType.private:
        return commands.when_mentioned_or(*bot_1.prefix_default)(bot_1, message)
    prefixes = await bot_1.pg_conn.fetchval("""
    SELECT prefixes FROM prefix_data
    WHERE guild_id = $1
    """, message.guild.id)
    if not prefixes:
        await bot_1.pg_conn.execute("""
        INSERT INTO prefix_data (guild_id, prefixes)
        VALUES ($1, $2)
        """, message.guild.id, bot_1.prefix_default)
        return commands.when_mentioned_or(*bot_1.prefix_default)(bot_1, message)
    return commands.when_mentioned_or(*prefixes)(bot_1, message)


bot = commands.Bot(command_prefix=get_prefix)
app = Quart(__name__)


@app.route("/")
def hello():
    return "Hello from {}".format(bot.user.name)


bot.oauth_url = discord.utils.oauth_url(client_id=CLIENT_ID, permissions=discord.Permissions(8))
bot.init_cogs = [f'Bot.cogs.{filename[:-3]}' for filename in os.listdir('Bot/cogs') if filename.endswith('.py')]
bot.start_time = datetime.datetime.utcnow()
bot.prefix_default = PREFIX.split(DELIMITER)
bot.start_number = 1000000000000000
bot.ticket_emoji_default = TICKET_EMOJI.split(DELIMITER)


async def connection_for_pg():
    bot.pg_conn = await asyncpg.create_pool(password="1234", port="5858", host="localhost", user="postgres", database="postgres")


@bot.event
async def on_ready():
    global BOT_IS_READY
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
    if filename.endswith('.py') and not filename.startswith('_'):
        bot.load_extension(f'Bot.cogs.{filename[:-3]}')


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command Not found!")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have enough permissions.")
    elif isinstance(error, commands.CheckAnyFailure):
        await ctx.send("".join(error.args))
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("".join(error.args))
    elif isinstance(error, commands.PrivateMessageOnly):
        await ctx.send("You're only allowed to use this command in Direct or Private Message only!")
    elif isinstance(error, commands.NotOwner):
        await ctx.send("You're not a owner till now!")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("You can't send this commands here!")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send("The command you send is on cooldown!")
    else:
        raise error


@bot.command()
@commands.is_owner()
async def reload_all_extensions(ctx):
    for filename1 in os.listdir('Bot/cogs'):
        if filename1.endswith('.py'):
            bot.unload_extension(f'Bot.cogs.{filename1[:-3]}')
            bot.load_extension(f'Bot.cogs.{filename1[:-3]}')
    await ctx.send("Reloaded all extensions!")


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
                """, guild.id, bot.init_cogs, ["None"])

dispatcher = "Bot.cogs.utils.dispatcher"
bot.load_extension(dispatcher)
print('loaded dispatcher successfully')


@tasks.loop(hours=1)
async def my_presence_per_day():
    await bot.wait_until_ready()
    prefix = next(cycle(bot.prefix_default))
    status = next(cycle([discord.Status.do_not_disturb, discord.Status.online, discord.Status.idle, discord.Status.dnd]))
    activity = next(cycle([discord.Game(name=f"OpenCity • Type {prefix}help to get started"),
                           discord.Streaming(name=f"OpenCity • Type {prefix}help to get started", url="https://www.twitch.tv/opencitybotdiscord"),
                           discord.Activity(type=discord.ActivityType.listening, name=f"OpenCity • Type {prefix}help to get started"),
                           discord.Activity(type=discord.ActivityType.watching, name=f"OpenCity • Type {prefix}help to get started")
                           ]))
    await bot.change_presence(status=status, activity=activity)


# @add_guild_to_db.error
# async def add_guild_to_db_error(error):
#     raise error
#
bot.loop.run_until_complete(connection_for_pg())
bot.loop.create_task(app.run_task(host=IP_ADDRESS, port=int(PORT_NUMBER)))
my_presence_per_day.start()
add_guild_to_db.start()

bot.run(TOKEN)


# async def main():
#     asyncio.get_running_loop().create_task(app.run_task(host=IP_ADDRESS, port=int(PORT_NUMBER)))
#     asyncio.get_running_loop().create_task(await bot.start(TOKEN))
#     # asyncio.get_running_loop().create_task(await bot.login(TOKEN))
#
# asyncio.run(main())
