import datetime
import json
import os
# os.chdir("..")
import random
from itertools import cycle

import asyncpg
import discord
from discord.ext import commands, tasks
# from quart import Quart

from development.Bot.cogs.utils.timeformat_bot import format_duration

# TOKEN = os.getenv('DISCORD_TOKEN')
# CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')

# BOT_IS_READY = False
# PREFIX = os.getenv('DEFAULT_PREFIX')
# DELIMITER = os.getenv('DEFAULT_DELIMITER_FOR_ENV')
# IP_ADDRESS = os.getenv('IP_ADDRESS')
# PORT_NUMBER = os.getenv('PORT_NUMBER')
# DATABASE_URL = os.getenv('DATABASE_URL')

# bot = commands.AutoShardedBot(command_prefix=get_prefix)
# app = Quart(__name__)


# @app.route("/")
# def hello():
#     return "Hello from {}".format(bot.user.name)

# bot.ticket_emoji_default = TICKET_EMOJI.split(DELIMITER)

# @bot.event
# async def on_ready():
#     global BOT_IS_READY
#     BOT_IS_READY = True

#
# @tasks.loop(seconds=10)
# async def add_guild_to_db():
#     await bot.wait_until_ready()
#     if BOT_IS_READY:
#         for guild in bot.guilds:
#             guild_data = await bot.pg_conn.fetchrow("""
#             SELECT * FROM cogs_data
#             WHERE guild_id = $1
#             """, guild.id)
#             if not guild_data:
#                 await bot.pg_conn.execute("""
#                 INSERT INTO cogs_data (guild_id, enabled, disabled)
#                 VALUES ($1, $2, $3)
#                 """, guild.id, bot.init_cogs, ["None"])


# dispatcher = "Bot.cogs.utils.dispatcher"
# bot.load_extension(dispatcher)
# print('loaded dispatcher successfully')

# @add_guild_to_db.error
# async def add_guild_to_db_error(error):
#     raise error
#

# @blacklist_check.error
# async def blacklist_check_error(ctx, error):
#     if isinstance(error, commands.CheckFailure):
#         await ctx.send("You're blacklisted from using this bot completely. You can appeal for unblacklisting by DMing my owner.")


# bot.loop.create_task(app.run_task(host=IP_ADDRESS, port=int(PORT_NUMBER)))
# my_presence_per_day.start()
# add_guild_to_db.start()
# update_count_data_according_to_guild.start()
#
# bot.run(TOKEN)

# async def main():
#     asyncio.get_running_loop().create_task(app.run_task(host=IP_ADDRESS, port=int(PORT_NUMBER)))
#     asyncio.get_running_loop().create_task(await bot.start(TOKEN))
#     # asyncio.get_running_loop().create_task(await bot.login(TOKEN))
#
# asyncio.run(main())


class MyBot(commands.AutoShardedBot):
    def __init__(self, database_url, default_prefix):
        super().__init__(command_prefix=self.get_prefix)
        # env variables
        self.DATABASE_URL = database_url
        self.DEFAULT_PREFIX = default_prefix

        # normal variables
        self.pg_conn = None
        self.str_text = "OpenCity • Type {}help to get started"
        self.ACTIVITIES = cycle([discord.Game(name=self.str_text),
                                 discord.Streaming(name=self.str_text, url="https://www.twitch.tv/opencitybotdiscord"),
                                 discord.Activity(type=discord.ActivityType.listening, name=self.str_text),
                                 discord.Activity(type=discord.ActivityType.watching, name=self.str_text)
                                 ])
        self.STATUSES = cycle([discord.Status.online, discord.Status.idle, discord.Status.do_not_disturb])
        self.init_cogs = [f'Bot.cogs.{filename[:-3]}' for filename in os.listdir('Bot/cogs') if filename.endswith('.py')]
        self.invite_url = ""
        self.start_time = datetime.datetime.utcnow()
        self.credits = ['NameKhan72', 'SQWiperYT', 'Wizard BINAY', 'Sairam']
        self.prefix_default = json.loads(self.DEFAULT_PREFIX)
        self.start_number = 1000000000000000
        self.BOT_READY = False

        for filename in os.listdir('Bot/cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                self.load_extension(f'Bot.cogs.{filename[:-3]}')

        dispatcher = "Bot.cogs.utils.dispatcher"
        self.load_extension(dispatcher)
        print('loaded dispatcher successfully')

        # adding checks
        self.add_check(self.blacklist_check)

        # starting tasks
        self.add_guild_to_db.start()
        self.my_presence_per_day.start()
        self.update_count_data_according_to_guild.start()

    async def get_prefix(self, message):
        if message.channel.type == discord.ChannelType.private:
            return commands.when_mentioned_or(*self.prefix_default)(self, message)
        prefixes = await self.pg_conn.fetchval("""
        SELECT prefixes FROM prefix_data
        WHERE guild_id = $1
        """, message.guild.id)
        if not prefixes:
            await self.pg_conn.execute("""
            INSERT INTO prefix_data (guild_id, prefixes)
            VALUES ($1, $2)
            """, message.guild.id, self.prefix_default)
            return commands.when_mentioned_or(*self.prefix_default)(self, message)
        return commands.when_mentioned_or(*prefixes)(self, message)

    async def connection_for_pg(self):
        self.pg_conn = await asyncpg.create_pool(self.DATABASE_URL)

    async def get_invite_url(self):
        application = await self.application_info()
        self.invite_url = discord.utils.oauth_url(client_id=application.id, permissions=discord.Permissions(8))

    async def on_ready(self):
        await self.get_invite_url()
        random_user = random.choice(self.users)
        await self.is_owner(random_user)
        print(f'\n\n{self.user} (id: {self.user.id}) is connected to the following guilds:\n', end="")
        for guild_index, guild in enumerate(self.guilds):
            print(
                f' - {guild.name} (id: {guild.id})'
            )
        print("\n")
        for guild_index, guild in enumerate(self.guilds):
            members = '\n - '.join([f"{member} (id: {member.id})" for member in guild.members])
            print(f'{guild.name} (id: {guild.id})')
            print(f'Guild Members of {guild.name} are:\n - {members}')
            print(f"The above server has {guild.member_count} members")
            if guild_index != (len(self.guilds) - 1):
                print('\n\n\n', end="")

        print(f"\n\nI can view {len(self.users)} members in {len(self.guilds)} guilds.")
        print()
        print()
        for command in self.walk_commands():
            print(f"{command.qualified_name} -> {command.help} -> {command.cog_name}")

    def run(self, *args, **kwargs):
        self.loop.run_until_complete(self.connection_for_pg())
        super().run(*args, **kwargs)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
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

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"You missing this required argument: {error.param}")

        else:
            raise error

    async def blacklist_check(self, ctx: commands.Context):
        if await self.is_owner(ctx.author):
            return True
        black_listed_users = await self.pg_conn.fetchval("""
        SELECT black_listed_users FROM black_listed_users_data
        """)
        if not black_listed_users:
            return True
        if ctx.author.id not in black_listed_users:
            return True
        else:
            await ctx.send("You're blacklisted from using this bot completely. You can appeal for unblacklisting by DMing my owner.")
            return False

    @tasks.loop(hours=1)
    async def my_presence_per_day(self):
        await self.wait_until_ready()
        prefix = next(cycle(self.prefix_default))
        status = next(self.STATUSES)
        activity = next(self.ACTIVITIES)
        activity.name = activity.name.format(prefix)
        await self.change_presence(status=status, activity=activity)

    @tasks.loop(seconds=10)
    async def add_guild_to_db(self):
        await self.wait_until_ready()
        if self.BOT_READY:
            for guild in self.guilds:
                guild_data = await self.pg_conn.fetchrow("""
                SELECT * FROM cogs_data
                WHERE guild_id = $1
                """, guild.id)
                if not guild_data:
                    await self.pg_conn.execute("""
                    INSERT INTO cogs_data (guild_id, enabled, disabled)
                    VALUES ($1, $2, $3)
                    """, guild.id, self.init_cogs, ["None"])

    @tasks.loop(seconds=10)
    async def update_count_data_according_to_guild(self):
        await self.wait_until_ready()
        if self.BOT_READY:
            for guild in self.guilds:
                count_data = await self.pg_conn.fetchrow("""
                SELECT * FROM count_data
                WHERE guild_id = $1
                """, guild.id)
                id_data = await self.pg_conn.fetchrow("""
                SELECT * FROM id_data
                WHERE row_id = 1
                """)
                if not count_data:
                    await self.pg_conn.execute("""
                    INSERT INTO count_data 
                    VALUES ($1, 1, 1, 1, 1)
                    """, guild.id)
                if not id_data:
                    await self.pg_conn.execute("""
                    INSERT INTO id_data
                    VALUES ($1, $1, $1, $1, 1)
                    """, self.start_number)
