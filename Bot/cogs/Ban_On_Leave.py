import discord
from discord.ext import commands


class Ban_On_Leave(commands.Cog):

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
    async def on_member_leave(self, member):
        enabled = await self.bot.pg_conn.fetchval("""
                    SELECT enabled FROM cogs_data
                    WHERE guild_id = $1
                    """, member.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            member.ban()


def setup(bot):
    bot.add_cog(Ban_On_Leave(bot))
