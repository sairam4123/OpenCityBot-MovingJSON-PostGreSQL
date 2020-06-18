import datetime

import discord
from discord.ext import commands


class dispatcher(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick):
            if (datetime.datetime.utcnow() - entry.created_at).total_seconds() < 20:
                if entry.target == member:
                    self.bot.dispatch('member_kick', member)
                    return
        try:
            if await member.guild.fetch_ban(member):
                self.bot.dispatch('member_ban_1', member, member.guild)
                return
        except (discord.HTTPException, discord.Forbidden, discord.NotFound, AttributeError):
            self.bot.dispatch('member_leave', member)
        else:
            self.bot.dispatch('member_leave', member)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel and not after.channel:
            self.bot.dispatch('member_voice_channel_leave', member, before.channel)
        if after.channel and not before.channel:
            self.bot.dispatch('member_voice_channel_join', member, after.channel)
        if after.channel and before.channel:
            if not after.channel == before.channel:
                self.bot.dispatch('member_voice_channel_switch', member, before.channel, after.channel)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.bot.dispatch('message_create', message)


def setup(bot):
    bot.add_cog(dispatcher(bot))
