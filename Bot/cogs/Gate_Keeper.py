import random
from typing import Optional, Union

import discord
from discord.ext import commands

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

    @commands.group(name="gate_keeper", aliases=['gk', 'announcer', 'ann'])
    async def gate_keeper(self, ctx: commands.Context):
        check = await self.bot.pg_conn.fetchval("""
        SELECT * FROM gate_keeper_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        if not check:
            await self.bot.pg_conn.execute("""
            INSERT INTO gate_keeper_data (guild_id)
            VALUES ($1)
            """, ctx.guild.id)

    @gate_keeper.group(name="welcome_message", aliases=['wm'], invoke_without_command=True)
    async def welcome_message(self, ctx: commands.Context):
        pass

    @gate_keeper.group(name="leave_message", aliases=['lm'], invoke_without_command=True)
    async def leave_message(self, ctx: commands.Context):
        pass

    @gate_keeper.group(name="ban_message", aliases=['bm'], invoke_without_command=True)
    async def ban_message(self, ctx: commands.Context):
        pass

    @welcome_message.command(name="channel", aliases=['c'])
    async def welcome_message_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.pg_conn.execute("""
                UPDATE gate_keeper_data
                SET welcome_message_channel_id = $2
                WHERE guild_id = $1
        """, ctx.guild.id, channel.id)
        await ctx.send(f"Set welcome message channel to {channel.mention}")

    @leave_message.command(name="channel", aliases=['c'])
    async def leave_message_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.pg_conn.execute("""
                UPDATE gate_keeper_data
                SET leave_message_channel_id = $2
                WHERE guild_id = $1
                """, ctx.guild.id, channel.id)
        await ctx.send(f"Set leave message channel to {channel.mention}")

    @ban_message.command(name="channel", aliases=['c'])
    async def ban_message_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.pg_conn.execute("""
                UPDATE gate_keeper_data
                SET ban_message_channel_id = $2
                WHERE guild_id = $1
                """, ctx.guild.id, channel.id)
        await ctx.send(f"Set ban message channel to {channel.mention}")

    @welcome_message.group(name="message", aliases=['m'], invoke_without_command=True)
    async def welcome_message_message(self, ctx: commands.Context):
        messages = await self.bot.pg_conn.fetchval("""
        SELECT welcome_message FROM gate_keeper_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        embed = discord.Embed()
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        msg = ""
        for index, message in enumerate(messages):
            msg += f"{index}. {message}\n"
        embed.description = msg
        await ctx.send(embed=embed)

    @leave_message.group(name="message", aliases=['m'], invoke_without_command=True)
    async def leave_message_message(self, ctx: commands.Context):
        messages = await self.bot.pg_conn.fetchval("""
        SELECT leave_message FROM gate_keeper_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        embed = discord.Embed()
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        msg = ""
        for index, message in enumerate(messages):
            msg += f"{index}. {message}\n"
        embed.description = msg
        await ctx.send(embed=embed)

    @ban_message.group(name="message", aliases=['m'], invoke_without_command=True)
    async def ban_message_message(self, ctx: commands.Context):
        messages = await self.bot.pg_conn.fetchval("""
        SELECT ban_message FROM gate_keeper_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        embed = discord.Embed()
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        msg = ""
        for index, message in enumerate(messages):
            msg += f"{index}. {message}\n"
        embed.description = msg
        await ctx.send(embed=embed)

    @ban_message_message.command(name="add")
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

    @ban_message_message.command(name="remove")
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

    @ban_message_message.command(name="set")
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

    @welcome_message_message.command(name="add")
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

    @welcome_message_message.command(name="remove")
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

    @welcome_message_message.command(name="set")
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

    @leave_message_message.command(name="add")
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

    @leave_message_message.command(name="remove")
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

    @leave_message_message.command(name="set")
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

    @welcome_message.command(name="test_message", aliases=['t', 'tm', 'test'])
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

    @leave_message.command(name="test_message", aliases=['t', 'tm', 'test'])
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

    @ban_message.command(name="test_message", aliases=['t', 'tm', 'test'])
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


def setup(bot):
    bot.add_cog(Gate_Keeper(bot))
