import random

import discord
from discord.ext import commands

from .utils.message_interpreter import MessageInterpreter


class Gate_Keeper(commands.Cog):

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
        pass

    @gate_keeper.group(name="welcome_message", aliases=['wm'])
    async def welcome_message(self, ctx: commands.Context, message: str):
        pass

    @gate_keeper.group(name="leave_message", aliases=['lm'])
    async def leave_message(self, ctx: commands.Context, message: str):
        pass

    @gate_keeper.group(name="ban_message", aliases=['bm'])
    async def ban_message(self, ctx: commands.Context, message: str):
        pass

    @welcome_message.command(name="channel", aliases=['c'])
    async def welcome_message_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        pass

    @leave_message.command(name="channel", aliases=['c'])
    async def leave_message_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        pass

    @ban_message.command(name="channel", aliases=['c'])
    async def ban_message_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        pass

    @welcome_message.group(name="message", aliases=['m'])
    async def welcome_message_message(self, ctx: commands.Context):
        pass

    @leave_message.group(name="message", aliases=['m'])
    async def leave_message_message(self, ctx: commands.Context):
        pass

    @ban_message.group(name="message", aliases=['m'])
    async def ban_message_message(self, ctx: commands.Context):
        pass

    @ban_message_message.command(name="add")
    async def ban_message_message_add(self, ctx: commands.Context, message: str):
        pass

    @ban_message_message.command(name="remove")
    async def ban_message_message_remove(self, ctx: commands.Context, message: str):
        pass

    @ban_message_message.command(name="set")
    async def ban_message_message_set(self, ctx: commands.Context, message: str):
        pass

    @welcome_message_message.command(name="add")
    async def welcome_message_message_add(self, ctx: commands.Context, message: str):
        pass

    @welcome_message_message.command(name="remove")
    async def welcome_message_message_remove(self, ctx: commands.Context, message: str):
        pass

    @welcome_message_message.command(name="set")
    async def welcome_message_message_set(self, ctx: commands.Context, message: str):
        pass

    @leave_message_message.command(name="add")
    async def leave_message_message_add(self, ctx: commands.Context, message: str):
        pass

    @leave_message_message.command(name="remove")
    async def leave_message_message_remove(self, ctx: commands.Context, message: str):
        pass

    @leave_message_message.command(name="set")
    async def leave_message_message_set(self, ctx: commands.Context, message: str):
        pass

    @commands.command(name="test_message")
    async def test_message(self, ctx: commands.Context, message_type):
        formatted_message = ""
        if message_type == "join":
            join_message = await self.bot.pg_conn.fetchval("""
            SELECT welcome_message FROM gate_keeper_data
            WHERE guild_id = $1
            """, ctx.guild.id)
            if not join_message:
                return await ctx.send("You haven't set any message to join. Please try setting a message and try again.")
            formatted_message = MessageInterpreter(random.choice(join_message)).interpret_message(ctx.author)
        elif message_type == "leave":
            leave_message = await self.bot.pg_conn.fetchval("""
            SELECT leave_message FROM gate_keeper_data
            WHERE guild_id = $1
            """, ctx.guild.id)
            if not leave_message:
                return await ctx.send("You haven't set any message to join. Please try setting a message and try again.")
            formatted_message = MessageInterpreter(random.choice(leave_message)).interpret_message(ctx.author)
        elif message_type == "ban":
            ban_message = await self.bot.pg_conn.fetchval("""
            SELECT ban_message FROM gate_keeper_data
            WHERE guild_id = $1
            """, ctx.guild.id)
            if not ban_message:
                return await ctx.send("You haven't set any message to join. Please try setting a message and try again.")
            formatted_message = MessageInterpreter(random.choice(ban_message)).interpret_message(ctx.author)
        await ctx.send(formatted_message)


def setup(bot):
    bot.add_cog(Gate_Keeper(bot))
