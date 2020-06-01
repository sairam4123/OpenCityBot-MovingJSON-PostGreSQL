import datetime
import os
from itertools import cycle

import asyncpg
import discord
import click
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


bot = commands.Bot(command_prefix=get_prefix)
app = Quart(__name__)


@app.route("/")
def hello():
    return "Hello from {}".format(bot.user.name)


bot.oauth_url = discord.utils.oauth_url(client_id=CLIENT_ID, permissions=discord.Permissions(8))
bot.init_cogs = [f'Bot.cogs.{filename[:-3]}' for filename in os.listdir('Bot/cogs') if filename.endswith('.py')]
bot.invite_url = discord.utils.oauth_url(client_id=CLIENT_ID, permissions=discord.Permissions(8))
bot.start_time = datetime.datetime.utcnow()
bot.prefix_default = PREFIX.split(DELIMITER)
bot.start_number = 1000000000000000
bot.ticket_emoji_default = TICKET_EMOJI.split(DELIMITER)


async def connection_for_pg():
    bot.pg_conn = await asyncpg.create_pool(DATABASE_URL)


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


@click.command()
async def create_tables():
    await bot.pg_conn.execute("""
    CREATE TABLE public.application_data
(
    guild_id bigint,
    application_name text COLLATE pg_catalog."default",
    questions text[] COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE public.application_data
    OWNER to postgres;
    """)
    await bot.pg_conn.execute("""
    CREATE TABLE public.bank_data
(
    guild_id bigint,
    bank_name text COLLATE pg_catalog."default",
    currency_symbol text COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE public.bank_data
    OWNER to postgres;
    """)
    await bot.pg_conn.execute("""
    CREATE TABLE public.cogs_data
(
    guild_id bigint NOT NULL,
    enabled text[] COLLATE pg_catalog."default",
    disabled text[] COLLATE pg_catalog."default",
    CONSTRAINT cogs_data_pk PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE public.cogs_data
    OWNER to postgres;
-- Index: cogs_data_guild_id_uindex

-- DROP INDEX public.cogs_data_guild_id_uindex;

CREATE UNIQUE INDEX cogs_data_guild_id_uindex
    ON public.cogs_data USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
    """)
    await bot.pg_conn.execute("""
    CREATE TABLE public.count_data
(
    guild_id bigint NOT NULL,
    suggestion_number integer DEFAULT 0,
    report_number integer DEFAULT 0,
    ticket_number integer DEFAULT 0,
    tunnel_number integer DEFAULT 0,
    CONSTRAINT count_data_pk PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE public.count_data
    OWNER to postgres;

CREATE UNIQUE INDEX count_data_guild_id_uindex
    ON public.count_data USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
    """)

    await bot.pg_conn.execute("""
    CREATE TABLE public.economy_data
(
    guild_id bigint,
    user_id bigint,
    amount bigint DEFAULT 2000
)

TABLESPACE pg_default;

ALTER TABLE public.economy_data
    OWNER to postgres;
    """)

    await bot.pg_conn.execute("""
    CREATE TABLE public.id_data
(
    suggestion_id bigint,
    report_id bigint,
    ticket_id bigint,
    tunnel_id bigint,
    row_id integer DEFAULT 0
)

TABLESPACE pg_default;

ALTER TABLE public.id_data
    OWNER to postgres;

CREATE UNIQUE INDEX id_data_report_id_uindex
    ON public.id_data USING btree
    (report_id ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX id_data_suggestion_id_uindex
    ON public.id_data USING btree
    (suggestion_id ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX id_data_ticket_id_uindex
    ON public.id_data USING btree
    (ticket_id ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX id_data_tunnel_id_uindex
    ON public.id_data USING btree
    (tunnel_id ASC NULLS LAST)
    TABLESPACE pg_default;
    """)

    await bot.pg_conn.execute("""
    CREATE TABLE public.join_to_create_data
(
    channel_id bigint,
    user_id bigint
)

TABLESPACE pg_default;

ALTER TABLE public.join_to_create_data
    OWNER to postgres;    
    """)

    await bot.pg_conn.execute("""
    CREATE TABLE public.leveling_data
(
    guild_id bigint,
    user_id bigint,
    xps integer,
    level integer,
    last_message_time bigint
)

TABLESPACE pg_default;

ALTER TABLE public.leveling_data
    OWNER to postgres;
    """)

    await bot.pg_conn.execute("""
    CREATE TABLE public.prefix_data
(
    guild_id bigint NOT NULL,
    prefixes character varying[] COLLATE pg_catalog."default",
    CONSTRAINT prefix_data_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE public.prefix_data
    OWNER to postgres;
    """)

    await bot.pg_conn.execute("""
    CREATE TABLE public.reaction_roles_data
(
    guild_id bigint,
    message_id bigint,
    reaction text COLLATE pg_catalog."default",
    role_id bigint,
    message_type text COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE public.reaction_roles_data
    OWNER to postgres;
    """)
    await bot.pg_conn.execute("""
    CREATE TABLE public.report_data
(
    "reportID" bigint NOT NULL,
    "reportMessageID" bigint,
    "reportTitle" text COLLATE pg_catalog."default",
    "reportReason" text COLLATE pg_catalog."default",
    "reportAuthor" text COLLATE pg_catalog."default",
    "reportTime" text COLLATE pg_catalog."default",
    "reportChannelID" bigint,
    "reportGuildID" bigint,
    "reportStatus" text COLLATE pg_catalog."default",
    "reportUser" text COLLATE pg_catalog."default",
    "reportModerator" text COLLATE pg_catalog."default",
    CONSTRAINT report_data_pk PRIMARY KEY ("reportID")
)

TABLESPACE pg_default;

ALTER TABLE public.report_data
    OWNER to postgres;

CREATE UNIQUE INDEX report_data_reportid_uindex
    ON public.report_data USING btree
    ("reportID" ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX report_data_reportmessageid_uindex
    ON public.report_data USING btree
    ("reportMessageID" ASC NULLS LAST)
    TABLESPACE pg_default;  
    """)

    await bot.pg_conn.execute("""
    CREATE TABLE public.suggestion_data
(
    "suggestionID" bigint NOT NULL,
    "suggestionMessageID" bigint,
    "suggestionTitle" text COLLATE pg_catalog."default",
    "suggestionContent" text COLLATE pg_catalog."default",
    "suggestionAuthor" text COLLATE pg_catalog."default",
    "suggestionTime" text COLLATE pg_catalog."default",
    "suggestionChannelID" bigint,
    "suggestionGuildID" bigint,
    "suggestionType" text COLLATE pg_catalog."default",
    "suggestionStatus" text COLLATE pg_catalog."default",
    "suggestionModerator" text COLLATE pg_catalog."default",
    CONSTRAINT suggestion_data_pk PRIMARY KEY ("suggestionID")
)

TABLESPACE pg_default;

ALTER TABLE public.suggestion_data
    OWNER to postgres;

CREATE UNIQUE INDEX suggestion_data_suggestionid_uindex
    ON public.suggestion_data USING btree
    ("suggestionID" ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX suggestion_data_suggestionmessageid_uindex
    ON public.suggestion_data USING btree
    ("suggestionMessageID" ASC NULLS LAST)
    TABLESPACE pg_default;
    """)
    await bot.pg_conn.execute("""
    CREATE TABLE public.tunnel_data
(
    "tunnelID" bigint NOT NULL,
    "tunnelReason" text COLLATE pg_catalog."default",
    "tunnelAuthor" text COLLATE pg_catalog."default",
    "tunnelOpenedTime" text COLLATE pg_catalog."default",
    "tunnelClosedTime" text COLLATE pg_catalog."default",
    "tunnelGuildID" text COLLATE pg_catalog."default",
    "tunnelStatus" text COLLATE pg_catalog."default",
    "tunnelUser" text COLLATE pg_catalog."default",
    CONSTRAINT tunnel_data_pk PRIMARY KEY ("tunnelID")
)

TABLESPACE pg_default;

ALTER TABLE public.tunnel_data
    OWNER to postgres;

CREATE UNIQUE INDEX tunnel_data_tunnelid_uindex
    ON public.tunnel_data USING btree
    ("tunnelID" ASC NULLS LAST)
    TABLESPACE pg_default;
    """)
    await bot.pg_conn.execute("""
    CREATE TABLE public.ticket_data
(
    "ticketID" bigint NOT NULL,
    "ticketReason" text COLLATE pg_catalog."default",
    "ticketAuthor" text COLLATE pg_catalog."default",
    "ticketOpenedTime" text COLLATE pg_catalog."default",
    "ticketClosedTime" text COLLATE pg_catalog."default",
    "ticketGuildID" text COLLATE pg_catalog."default",
    "ticketStatus" text COLLATE pg_catalog."default",
    "ticketUser" text COLLATE pg_catalog."default",
    CONSTRAINT ticket_data_pk PRIMARY KEY ("ticketID")
)

TABLESPACE pg_default;

ALTER TABLE public.ticket_data
    OWNER to postgres;

CREATE UNIQUE INDEX ticket_data_ticketid_uindex
    ON public.ticket_data USING btree
    ("ticketID" ASC NULLS LAST)
    TABLESPACE pg_default;
    """)

    await bot.pg_conn.execute("""
    CREATE TABLE public.tunnel_data
(
    "tunnelID" bigint NOT NULL,
    "tunnelReason" text COLLATE pg_catalog."default",
    "tunnelAuthor" text COLLATE pg_catalog."default",
    "tunnelOpenedTime" text COLLATE pg_catalog."default",
    "tunnelClosedTime" text COLLATE pg_catalog."default",
    "tunnelGuildID" text COLLATE pg_catalog."default",
    "tunnelStatus" text COLLATE pg_catalog."default",
    "tunnelUser" text COLLATE pg_catalog."default",
    CONSTRAINT tunnel_data_pk PRIMARY KEY ("tunnelID")
)

TABLESPACE pg_default;

ALTER TABLE public.tunnel_data
    OWNER to postgres;

CREATE UNIQUE INDEX tunnel_data_tunnelid_uindex
    ON public.tunnel_data USING btree
    ("tunnelID" ASC NULLS LAST)
    TABLESPACE pg_default;
    """)

    await bot.pg_conn.execute("""
    CREATE TABLE public.voice_text_data
(
    guild_id bigint,
    voice_channel_id bigint,
    text_channel_id bigint
)

TABLESPACE pg_default;

ALTER TABLE public.voice_text_data
    OWNER to postgres;
    """)


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
