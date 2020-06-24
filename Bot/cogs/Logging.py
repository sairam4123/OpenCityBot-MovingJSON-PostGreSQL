import datetime

import discord
from discord.ext import commands


class Logging(commands.Cog):

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
        print(f'{member.display_name} left server {member.guild.name}')

    @commands.Cog.listener()
    async def on_member_kick(self, member):
        async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick):
            if (datetime.datetime.utcnow() - entry.created_at).total_seconds() < 20:
                if entry.target == member:
                    print(f'{member} got kicked from {member.guild.name} by {entry.user} because of {entry.reason}')

    @commands.Cog.listener()
    async def on_member_voice_channel_join(self, member, channel):
        print(f'{member.display_name} joined voice channel {channel.name}')

    @commands.Cog.listener()
    async def on_member_voice_channel_leave(self, member, channel):
        print(f'{member.display_name} left voice channel {channel.name}')

    @commands.Cog.listener()
    async def on_member_voice_channel_switch(self, member, old_channel, new_channel):
        print(f'{member.display_name} switched voice channel from {old_channel.name} to {new_channel.name}')


def setup(bot):
    bot.add_cog(Logging(bot))
