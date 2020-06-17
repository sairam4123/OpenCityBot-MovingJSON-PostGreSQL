import datetime
import os
# os.chdir("..")
import random
from itertools import cycle

import asyncpg
import discord
from discord.ext import commands, tasks
from quart import Quart

from development.Bot.cogs.utils.timeformat_bot import format_duration

TOKEN = os.getenv('DISCORD_TOKEN')
CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')

BOT_IS_READY = False
PREFIX = os.getenv('DEFAULT_PREFIX')
DELIMITER = os.getenv('DEFAULT_DELIMITER_FOR_ENV')
IP_ADDRESS = os.getenv('IP_ADDRESS')
PORT_NUMBER = os.getenv('PORT_NUMBER')
DATABASE_URL = os.getenv('DATABASE_URL')


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


bot = commands.AutoShardedBot(command_prefix=get_prefix)
app = Quart(__name__)


@app.route("/")
def hello():
    return "Hello from {}".format(bot.user.name)


bot.oauth_url = discord.utils.oauth_url(client_id=CLIENT_ID, permissions=discord.Permissions(8))
bot.init_cogs = [f'Bot.cogs.{filename[:-3]}' for filename in os.listdir('Bot/cogs') if filename.endswith('.py')]
bot.invite_url = discord.utils.oauth_url(client_id=CLIENT_ID, permissions=discord.Permissions(8))
bot.start_time = datetime.datetime.utcnow()
bot.credits = ['NameKhan72', 'SQWiperYT', 'Wizard BINAY', 'Sairam']
bot.prefix_default = PREFIX.split(DELIMITER)
bot.start_number = 1000000000000000
# bot.ticket_emoji_default = TICKET_EMOJI.split(DELIMITER)

str_text = "OpenCity • Type {}help to get started"
ACTIVITIES = cycle([discord.Game(name=str_text),
                    discord.Streaming(name=str_text, url="https://www.twitch.tv/opencitybotdiscord"),
                    discord.Activity(type=discord.ActivityType.listening, name=str_text),
                    discord.Activity(type=discord.ActivityType.watching, name=str_text)
                    ])
STATUSES = cycle([discord.Status.online, discord.Status.idle, discord.Status.do_not_disturb])


async def connection_for_pg():
    bot.pg_conn = await asyncpg.create_pool(DATABASE_URL)


@bot.event
async def on_ready():
    global BOT_IS_READY
    random_user = random.choice(bot.users)
    await bot.is_owner(random_user)
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


for filename in os.listdir('Bot/cogs'):
    if filename.endswith('.py') and not filename.startswith('_'):
        bot.load_extension(f'development.Bot.cogs.{filename[:-3]}')


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if hasattr(ctx.command, 'on_error'):
        return

    try:
        if ctx.cog_handler:
            return
    except AttributeError:
        pass

    error = getattr(error, "original", error)

    if isinstance(error, commands.CommandNotFound):
        await ctx.send("I am not able to find the command, you asked me, in my registered commands list.")

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Sorry, I think you need to ask your server owner or people with role higher than you to give the needed permission.\n"
                       "These permissions are needed to run the command:\n\n {}".
                       format('\n'.join([f"{index}. {permission.replace('guild', 'server').replace('_', ' ').title()}"
                                         for index, permission in enumerate(error.missing_perms, start=1)])))

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
        await ctx.send(f"The command you send is on cooldown! Try again after {format_duration(int(error.retry_after))}.")

    elif isinstance(error, discord.Forbidden):
        await ctx.send(error.text)

    else:
        raise error


@bot.command()
@commands.is_owner()
async def reload_all_extensions(ctx):
    for filename1 in os.listdir('Bot/cogs'):
        if filename1.endswith('.py'):
            bot.unload_extension(f'development.Bot.cogs.{filename1[:-3]}')
            bot.load_extension(f'development.Bot.cogs.{filename1[:-3]}')
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


@tasks.loop(seconds=10)
async def update_count_data_according_to_guild():
    await bot.wait_until_ready()
    if BOT_IS_READY:
        for guild in bot.guilds:
            count_data = await bot.pg_conn.fetchrow("""
            SELECT * FROM count_data
            WHERE guild_id = $1
            """, guild.id)
            id_data = await bot.pg_conn.fetchrow("""
            SELECT * FROM id_data
            WHERE row_id = 1
            """)
            if not count_data:
                await bot.pg_conn.execute("""
                INSERT INTO count_data 
                VALUES ($1, 1, 1, 1, 1)
                """, guild.id)
            if not id_data:
                await bot.pg_conn.execute("""
                INSERT INTO id_data
                VALUES ($1, $1, $1, $1, 1)
                """, bot.start_number)


dispatcher = "development.Bot.cogs.utils.dispatcher"
bot.load_extension(dispatcher)
print('loaded dispatcher successfully')


@tasks.loop(hours=1)
async def my_presence_per_day():
    await bot.wait_until_ready()
    prefix = next(cycle(bot.prefix_default))
    status = next(STATUSES)
    activity = next(ACTIVITIES)
    activity.name = activity.name.format(prefix)
    await bot.change_presence(status=status, activity=activity)


# @add_guild_to_db.error
# async def add_guild_to_db_error(error):
#     raise error
#
@bot.check
async def blacklist_check(ctx: commands.Context):
    if await bot.is_owner(ctx.author):
        return True
    black_listed_users = await bot.pg_conn.fetchval("""
    SELECT black_listed_users FROM black_listed_users_data
    """)
    if not black_listed_users:
        return True
    if ctx.author.id not in black_listed_users:
        return True
    else:
        await ctx.send("You're blacklisted from using this bot completely. You can appeal for unblacklisting by DMing my owner.")
        return False


# @blacklist_check.error
# async def blacklist_check_error(ctx, error):
#     if isinstance(error, commands.CheckFailure):
#         await ctx.send("You're blacklisted from using this bot completely. You can appeal for unblacklisting by DMing my owner.")


bot.loop.run_until_complete(connection_for_pg())
bot.loop.create_task(app.run_task(host=IP_ADDRESS, port=int(PORT_NUMBER)))
my_presence_per_day.start()
add_guild_to_db.start()
update_count_data_according_to_guild.start()

bot.run(TOKEN)

# async def main():
#     asyncio.get_running_loop().create_task(app.run_task(host=IP_ADDRESS, port=int(PORT_NUMBER)))
#     asyncio.get_running_loop().create_task(await bot.start(TOKEN))
#     # asyncio.get_running_loop().create_task(await bot.login(TOKEN))
#
# asyncio.run(main())
