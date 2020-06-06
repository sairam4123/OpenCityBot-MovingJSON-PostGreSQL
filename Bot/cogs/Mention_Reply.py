import random

import discord
from discord.ext import commands


class Mention_Reply(commands.Cog):

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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        prefix = random.choice(await self.bot.command_prefix(self.bot, message))
        enabled = await self.bot.pg_conn.fetchval("""
                        SELECT enabled FROM cogs_data
                        WHERE guild_id = $1
                        """, message.guild.id)
        if message.channel.type == discord.ChannelType.private or f"Bot.cogs.{self.qualified_name}" in enabled:
            if message.content.startswith('<@') and message.content.endswith('>'):
                for mention in message.mentions:
                    if mention == self.bot.user:
                        await message.channel.send(f"I am {self.bot.user.name}. To see my prefix do `{prefix}prefix`. ")
                        return


def setup(bot):
    bot.add_cog(Mention_Reply(bot))
