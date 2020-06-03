from typing import Optional

import discord
from discord.ext import commands


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.channel.type == discord.ChannelType.private:
            return True
        enabled = await self.bot.pg_conn.fetchval("""
            SELECT enabled FROM cogs_data
            WHERE guild_id = $1
            """, ctx.guild.id)
        print(enabled)
        print(f"")
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            print(f"{self.qualified_name}")
            return True
        return False

    @commands.command()
    async def slowmode(self, ctx, channel: Optional[discord.TextChannel], secs: int):
        channel = ctx.channel if not channel else channel
        await channel.edit(slowmode_delay=secs)
        await ctx.send(f"Added slowmode of `{secs}` to {channel.mention}")


def setup(bot):
    bot.add_cog(Moderation(bot))
