import discord
from discord.ext import commands


class dispatcher(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel and not after.channel:
            self.bot.dispatch('member_voice_channel_leave', member, before.channel)
        if after.channel and not before.channel:
            self.bot.dispatch('member_voice_channel_join', member, after.channel)
        if after.channel and before.channel:
            if not after.channel == before.channel:
                self.bot.dispatch('member_voice_channel_switch', member, before.channel, after.channel)


def setup(bot):
    bot.add_cog(dispatcher(bot))
