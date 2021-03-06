import random
from typing import Optional, Union

import discord
from discord.ext import commands, tasks

from .utils.converters import Converters
from .utils.list_manipulation import insert_or_append, pop_or_remove, replace_or_set
from .utils.message_interpreter import MessageInterpreter


class Gate_Keeper(commands.Cog):
    """
    Welcomes and goodbyes users who join and leave in a custom way you say!

```py
To add a (welcome, goodbye and ban) message:
    1. {prefix_1}gk (wm|lm|bm) m [add|+] <message> [index] # When setting index will make it work like insert.
To remove a (welcome, goodbye and ban) message:
    2. {prefix_1}gk (wm|lm|bm) m [remove|-] <message> [index] # When setting index will make it work like pop.
To set a (welcome, goodbye and ban) message:
    3. {prefix_1}gk (wm|lm|bm) m [set|=] <message> <index> # Index is needed for setting the message.
```

    """
    def __init__(self, bot):
        self.bot = bot
        self.add_guild_to_db_gk.start()

    async def cog_check(self, ctx):
        if ctx.channel.type == discord.ChannelType.private:
            return True
        enabled = await self.bot.pg_conn.fetchval("""
            SELECT enabled FROM cogs_data
            WHERE guild_id = $1
            """, ctx.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            return True
        return False

    async def cog_unload(self):
        self.add_guild_to_db_gk.cancel()

    @commands.group(name="gate_keeper", aliases=['gk', 'announcer', 'ann'], invoke_without_command=True, help="Returns the gate keeper settings.")
    async def gate_keeper(self, ctx: commands.Context):
        welcome_message_available = False
        leave_message_available = False
        ban_message_available = False
        gk_data = await self.bot.pg_conn.fetch("""
        SELECT * FROM gate_keeper_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        if not gk_data:
            await self.bot.pg_conn.execute("""
            INSERT INTO gate_keeper_data (guild_id)
            VALUES ($1)
            """, ctx.guild.id)
        welcome_channel = await Converters.channel_converter(ctx.guild, gk_data[0]['welcome_message_channel_id'])
        if welcome_channel:
            welcome_message_available = True
        leave_channel = await Converters.channel_converter(ctx.guild, gk_data[0]['leave_message_channel_id'])
        if leave_channel:
            leave_message_available = True
        ban_channel = await Converters.channel_converter(ctx.guild, gk_data[0]['ban_message_channel_id'])
        if ban_channel:
            ban_message_available = True
        embed = discord.Embed(title="Gate Keeper of this server.")
        desc = (f"Enabled gate keepers:\n \t\t1. Welcome Message: {welcome_message_available}\n"
                f" \t\t2. Leave Message: {leave_message_available}\n"
                f" \t\t3. Ban Message: {ban_message_available}\n\n\n")
        embed.add_field(name="Channels", value=(f"Welcome Channel: \t\t{welcome_channel.mention if welcome_channel else None}\n"
                                                f"Leave Channel: \t\t{leave_channel.mention if leave_channel else None}\n"
                                                f"Ban Channel: \t\t{ban_channel.mention if ban_channel else None}"), inline=False)
        embed.description = desc
        await ctx.send(embed=embed)

    @gate_keeper.group(name="welcome_message", aliases=['wm'], invoke_without_command=True, help="Returns the welcome message settings.")
    async def welcome_message(self, ctx: commands.Context):
        gk_data = await self.bot.pg_conn.fetch("""
                SELECT * FROM gate_keeper_data
                WHERE guild_id = $1
                """, ctx.guild.id)
        welcome_messages = [f"{index}. {MessageInterpreter(message).interpret_message(ctx.author)}" for index, message in
                            enumerate(gk_data[0]['welcome_message'] if gk_data[0]['welcome_message'] else [], start=1)]
        welcome_channel = await Converters.channel_converter(ctx.guild, gk_data[0]['welcome_message_channel_id'])
        embed = discord.Embed(title="Welcome Messages")
        desc = f"Welcome Channel: \t\t{welcome_channel.mention if welcome_channel else None}\n"
        embed.add_field(name="Messages:", value="\n".join(welcome_messages) if welcome_messages else "None", inline=False)
        embed.description = desc
        await ctx.send(embed=embed)

    @gate_keeper.group(name="leave_message", aliases=['lm'], invoke_without_command=True, help="Returns the leave message settings.")
    async def leave_message(self, ctx: commands.Context):
        gk_data = await self.bot.pg_conn.fetch("""
                        SELECT * FROM gate_keeper_data
                        WHERE guild_id = $1
                        """, ctx.guild.id)
        leave_messages = [f"{index}. {MessageInterpreter(message).interpret_message(ctx.author)}" for index, message in
                          enumerate(gk_data[0]['leave_message'] if gk_data[0]['leave_message'] else [], start=1)]
        leave_channel = await Converters.channel_converter(ctx.guild, gk_data[0]['leave_message_channel_id'])
        embed = discord.Embed(title="Leave Messages")
        desc = f"Leave Channel: \t\t{leave_channel.mention if leave_channel else None}\n"
        embed.add_field(name="Messages:", value="\n".join(leave_messages) if leave_messages else "None", inline=False)
        embed.description = desc
        await ctx.send(embed=embed)

    @gate_keeper.group(name="ban_message", aliases=['bm'], invoke_without_command=True, help="Returns the ban message settings.")
    async def ban_message(self, ctx: commands.Context):
        gk_data = await self.bot.pg_conn.fetch("""
                                SELECT * FROM gate_keeper_data
                                WHERE guild_id = $1
                                """, ctx.guild.id)
        ban_messages = [f"{index}. {MessageInterpreter(message).interpret_message(ctx.author)}" for index, message in
                        enumerate(gk_data[0]['ban_message'] if gk_data[0]['ban_message'] else [], start=1)]
        ban_channel = await Converters.channel_converter(ctx.guild, gk_data[0]['ban_message_channel_id'])
        embed = discord.Embed(title="Ban Messages")
        desc = f"Ban Channel: \t\t{ban_channel.mention if ban_channel else None}\n"
        embed.add_field(name="Messages:", value="\n".join(ban_messages) if ban_messages else "None", inline=False)
        embed.description = desc
        await ctx.send(embed=embed)

    @welcome_message.command(name="channel", aliases=['c'], help="Sets the welcome message channel.")
    async def welcome_message_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.pg_conn.execute("""
                UPDATE gate_keeper_data
                SET welcome_message_channel_id = $2
                WHERE guild_id = $1
        """, ctx.guild.id, channel.id)
        await ctx.send(f"Set welcome message channel to {channel.mention}")

    @leave_message.command(name="channel", aliases=['c'], help="Sets the leave message channel.")
    async def leave_message_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.pg_conn.execute("""
                UPDATE gate_keeper_data
                SET leave_message_channel_id = $2
                WHERE guild_id = $1
                """, ctx.guild.id, channel.id)
        await ctx.send(f"Set leave message channel to {channel.mention}")

    @ban_message.command(name="channel", aliases=['c'], help="Sets the ban message channel.")
    async def ban_message_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.pg_conn.execute("""
                UPDATE gate_keeper_data
                SET ban_message_channel_id = $2
                WHERE guild_id = $1
                """, ctx.guild.id, channel.id)
        await ctx.send(f"Set ban message channel to {channel.mention}")

    @welcome_message.group(name="message", aliases=['m'], invoke_without_command=True, help="Returns all the welcome messages.")
    async def welcome_message_message(self, ctx: commands.Context):
        messages = await self.bot.pg_conn.fetchval("""
        SELECT welcome_message FROM gate_keeper_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        embed = discord.Embed()
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        msg = ""
        for index, message in enumerate(messages if messages else []):
            msg += f"{index}. {message}\n"
        embed.description = msg if msg else "No messages found in this server."
        await ctx.send(embed=embed)

    @leave_message.group(name="message", aliases=['m'], invoke_without_command=True, help="Returns all the leave messages.")
    async def leave_message_message(self, ctx: commands.Context):
        messages = await self.bot.pg_conn.fetchval("""
        SELECT leave_message FROM gate_keeper_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        embed = discord.Embed()
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        msg = ""
        for index, message in enumerate(messages if messages else []):
            msg += f"{index}. {message}\n"
        embed.description = msg if msg else "No messages found in this server."
        await ctx.send(embed=embed)

    @ban_message.group(name="message", aliases=['m'], invoke_without_command=True, help="Returns all the ban messages.")
    async def ban_message_message(self, ctx: commands.Context):
        messages = await self.bot.pg_conn.fetchval("""
        SELECT ban_message FROM gate_keeper_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        embed = discord.Embed()
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        msg = ""
        for index, message in enumerate(messages if messages else []):
            msg += f"{index}. {message}\n"
        embed.description = msg if msg else "No messages found in this server."
        await ctx.send(embed=embed)

    @ban_message_message.command(name="add", help="Adds a ban message.")
    async def ban_message_message_add(self, ctx: commands.Context, message: str, index: Optional[int] = None):
        messages = await self.bot.pg_conn.fetchval("""
                SELECT ban_message FROM gate_keeper_data
                WHERE guild_id = $1
        """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = insert_or_append(messages, message, index)
        await self.bot.pg_conn.execute("""
                UPDATE gate_keeper_data
                SET ban_message = $2
                WHERE guild_id = $1
        """, ctx.guild.id, messages)
        await ctx.send(f"I've successfully added your new ban message. "
                       f"This is how it looks like when interpreted: {MessageInterpreter(message).interpret_message(ctx.author)} \n"
                       f"Here the member is you! It will be replaced with banned member name.")

    @ban_message_message.command(name="remove", help="Removes a ban message.")
    async def ban_message_message_remove(self, ctx: commands.Context, message: str, index: Optional[int] = None):
        messages = await self.bot.pg_conn.fetchval("""
                SELECT ban_message FROM gate_keeper_data
                WHERE guild_id = $1
                """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = pop_or_remove(messages, message, index)
        await self.bot.pg_conn.execute("""
                UPDATE gate_keeper_data
                SET ban_message = $2
                WHERE guild_id = $1
                """, ctx.guild.id, messages)
        await ctx.send(f"I've successfully removed your ban message which was in index {index}. ")

    @ban_message_message.command(name="set", help="Sets a ban message.")
    async def ban_message_message_set(self, ctx: commands.Context, message: str, index: int):
        messages = await self.bot.pg_conn.fetchval("""
                        SELECT ban_message FROM gate_keeper_data
                        WHERE guild_id = $1
                        """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = replace_or_set(messages, message, index)
        await self.bot.pg_conn.execute("""
                        UPDATE gate_keeper_data
                        SET ban_message = $2
                        WHERE guild_id = $1
                        """, ctx.guild.id, messages)
        await ctx.send(f"I've successfully set your old ban message which was in index {index} "
                       f"to new ban message. \n"
                       f"This is how it looks like when interpreted: {MessageInterpreter(message).interpret_message(ctx.author)} \n"
                       f"Here the member is you! It will be replaced with banned member name.")

    @welcome_message_message.command(name="add", help="Adds a welcome message.")
    async def welcome_message_message_add(self, ctx: commands.Context, message: str, index: Optional[int] = None):
        messages = await self.bot.pg_conn.fetchval("""
                        SELECT welcome_message FROM gate_keeper_data
                        WHERE guild_id = $1
                """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = insert_or_append(messages, message, index)
        await self.bot.pg_conn.execute("""
                        UPDATE gate_keeper_data
                        SET welcome_message = $2
                        WHERE guild_id = $1
                """, ctx.guild.id, messages)
        await ctx.send(f"I've successfully added your new welcome message. "
                       f"This is how it looks like when interpreted: {MessageInterpreter(message).interpret_message(ctx.author)} \n"
                       f"Here the member is you! It will be replaced with joined member name.")

    @welcome_message_message.command(name="remove", help="Removes a welcome message.")
    async def welcome_message_message_remove(self, ctx: commands.Context, message: str, index: Optional[int] = None):
        messages = await self.bot.pg_conn.fetchval("""
                        SELECT welcome_message FROM gate_keeper_data
                        WHERE guild_id = $1
                        """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = pop_or_remove(messages, message, index)
        await self.bot.pg_conn.execute("""
                        UPDATE gate_keeper_data
                        SET welcome_message = $2
                        WHERE guild_id = $1
                        """, ctx.guild.id, messages)
        await ctx.send(f"I've successfully removed your welcome message which was in index {index}. ")

    @welcome_message_message.command(name="set", help="Sets a welcome message.")
    async def welcome_message_message_set(self, ctx: commands.Context, message: str, index: int = None):
        messages = await self.bot.pg_conn.fetchval("""
                                SELECT welcome_message FROM gate_keeper_data
                                WHERE guild_id = $1
                                """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = replace_or_set(messages, message, index)
        await self.bot.pg_conn.execute("""
                                UPDATE gate_keeper_data
                                SET welcome_message = $2
                                WHERE guild_id = $1
                                """, ctx.guild.id, messages)
        await ctx.send(f"I've successfully set your old welcome message which was in index {index} "
                       f"to new welcome message. \n"
                       f"This is how it looks like when interpreted: {MessageInterpreter(message).interpret_message(ctx.author)} \n"
                       f"Here the member is you! It will be replaced with joined member name.")

    @leave_message_message.command(name="add", help="Adds a leave message.")
    async def leave_message_message_add(self, ctx: commands.Context, message: str, index: Optional[int] = None):
        messages = await self.bot.pg_conn.fetchval("""
                        SELECT leave_message FROM gate_keeper_data
                        WHERE guild_id = $1
                """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = insert_or_append(messages, message, index)
        await self.bot.pg_conn.execute("""
                        UPDATE gate_keeper_data
                        SET leave_message = $2
                        WHERE guild_id = $1
                """, ctx.guild.id, messages)
        await ctx.send(f"I've successfully added your new leave message. "
                       f"This is how it looks like when interpreted: {MessageInterpreter(message).interpret_message(ctx.author)} \n"
                       f"Here the member is you! It will be replaced with left member name.")

    @leave_message_message.command(name="remove", help="Removes a leave message.")
    async def leave_message_message_remove(self, ctx: commands.Context, message: str, index: Optional[int] = None):
        messages = await self.bot.pg_conn.fetchval("""
                                SELECT leave_message FROM gate_keeper_data
                                WHERE guild_id = $1
                                """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = pop_or_remove(messages, message, index)
        await self.bot.pg_conn.execute("""
                                UPDATE gate_keeper_data
                                SET leave_message = $2
                                WHERE guild_id = $1
                                """, ctx.guild.id, messages)
        await ctx.send(f"I've successfully removed your leave message which was in index {index}. ")

    @leave_message_message.command(name="set", help="Sets a leave message.")
    async def leave_message_message_set(self, ctx: commands.Context, message: str, index: int = None):
        messages = await self.bot.pg_conn.fetchval("""
                                SELECT leave_message FROM gate_keeper_data
                                WHERE guild_id = $1
                                """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = replace_or_set(messages, message, index)
        await self.bot.pg_conn.execute("""
                                UPDATE gate_keeper_data
                                SET leave_message = $2
                                WHERE guild_id = $1
                                """, ctx.guild.id, messages)
        await ctx.send(f"I've successfully set your old leave message which was in index {index} "
                       f"to new leave message. \n"
                       f"This is how it looks like when interpreted: {MessageInterpreter(message).interpret_message(ctx.author)} \n"
                       f"Here the member is you! It will be replaced with left member name.")

    @welcome_message.command(name="test_message", aliases=['t', 'tm', 'test'], help="Tests a welcome message.")
    async def welcome_message_test_message(self, ctx: commands.Context, index: Optional[int] = None):
        join_messages = await self.bot.pg_conn.fetchval("""
                    SELECT welcome_message FROM gate_keeper_data
                    WHERE guild_id = $1
                    """, ctx.guild.id)
        if not join_messages:
            return await ctx.send("You haven't set any message to join. Please try setting a message and try again.")
        if not index:
            join_message = random.choice(join_messages)
        else:
            try:
                join_message = join_messages[index]
            except (ValueError, IndexError):
                return await ctx.send("You sent an wrong index. Please try again with correct index or try again without index.")
        await ctx.send(str(MessageInterpreter(join_message).interpret_message(ctx.author)))

    @leave_message.command(name="test_message", aliases=['t', 'tm', 'test'], help="Tests a leave message.")
    async def leave_message_test_message(self, ctx: commands.Context, index: Optional[int] = None):
        leave_messages = await self.bot.pg_conn.fetchval("""
                    SELECT leave_message FROM gate_keeper_data
                    WHERE guild_id = $1
                    """, ctx.guild.id)
        if not leave_messages:
            return await ctx.send("You haven't set any message to join. Please try setting a message and try again.")
        if not index:
            join_message = random.choice(leave_messages)
        else:
            try:
                join_message = leave_messages[index]
            except (ValueError, IndexError):
                return await ctx.send("You sent an wrong index. Please try again with correct index or try again without index.")
        await ctx.send(str(MessageInterpreter(join_message).interpret_message(ctx.author)))

    @ban_message.command(name="test_message", aliases=['t', 'tm', 'test'], help="Tests a ban message.")
    async def ban_message_test_message(self, ctx: commands.Context, index: Optional[int] = None):
        ban_messages = await self.bot.pg_conn.fetchval("""
                    SELECT ban_message FROM gate_keeper_data
                    WHERE guild_id = $1
                    """, ctx.guild.id)
        if not ban_messages:
            return await ctx.send("You haven't set any message to join. Please try setting a message and try again.")
        if not index:
            join_message = random.choice(ban_messages)
        else:
            try:
                join_message = ban_messages[index]
            except (ValueError, IndexError):
                return await ctx.send("You sent an wrong index. Please try again with correct index or try again without index.")
        await ctx.send(str(MessageInterpreter(join_message).interpret_message(ctx.author)))

    @commands.Cog.listener()
    async def on_member_leave(self, member: discord.Member):
        goodbye_messages = await self.bot.pg_conn.fetchval("""
                                    SELECT leave_message FROM gate_keeper_data
                                    WHERE guild_id = $1
                                    """, member.guild.id)
        leave_channel_id = await self.bot.pg_conn.fetchval("""
                                    SELECT leave_message_channel_id FROM gate_keeper_data
                                    WHERE guild_id = $1
                                    """, member.guild.id)
        if not goodbye_messages:
            return
        goodbye_message = random.choice(goodbye_messages)
        leave_channel = member.guild.get_channel(leave_channel_id)
        await leave_channel.send(str(MessageInterpreter(goodbye_message).interpret_message(member)))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        join_messages = await self.bot.pg_conn.fetchval("""
                            SELECT welcome_message FROM gate_keeper_data
                            WHERE guild_id = $1
                            """, member.guild.id)
        welcome_channel_id = await self.bot.pg_conn.fetchval("""
                            SELECT welcome_message_channel_id FROM gate_keeper_data
                            WHERE guild_id = $1
                            """, member.guild.id)
        if not join_messages:
            return
        join_message = random.choice(join_messages)
        welcome_channel = member.guild.get_channel(welcome_channel_id)
        await welcome_channel.send(str(MessageInterpreter(join_message).interpret_message(member)))

    @commands.Cog.listener()
    async def on_member_ban_1(self, user: Union[discord.Member, discord.User], guild: discord.Guild):
        print("got the event")
        ban_messages = await self.bot.pg_conn.fetchval("""
                            SELECT ban_message FROM gate_keeper_data
                            WHERE guild_id = $1
                            """, guild.id)
        ban_channel_id = await self.bot.pg_conn.fetchval("""
                            SELECT ban_message_channel_id FROM gate_keeper_data
                            WHERE guild_id = $1
                            """, guild.id)
        if not ban_messages:
            return
        ban_message = random.choice(ban_messages)
        ban_channel = guild.get_channel(ban_channel_id)
        await ban_channel.send(str(MessageInterpreter(ban_message).interpret_message(user, guild=guild)))

    @tasks.loop(seconds=10)
    async def add_guild_to_db_gk(self):
        for guild in self.bot.guilds:
            gk_data = await self.bot.pg_conn.fetch("""
                    SELECT * FROM gate_keeper_data
                    WHERE guild_id = $1
                    """, guild.id)
            if not gk_data:
                await self.bot.pg_conn.execute("""
                        INSERT INTO gate_keeper_data (guild_id)
                        VALUES ($1)
                        """, guild.id)


def setup(bot):
    bot.add_cog(Gate_Keeper(bot))
