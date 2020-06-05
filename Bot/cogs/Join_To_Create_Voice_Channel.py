import discord
from discord.ext import commands


class Join_To_Create_Voice_Channel(commands.Cog):

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
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.voice:
            if member.voice.channel.name == "Join to Create":
                voice_channel = await member.guild.create_voice_channel(name=f"{member.display_name}'s channel", user_limit=3)
                await member.move_to(voice_channel)
        if before.channel and not after.channel:
            voice_channel1 = discord.utils.get(member.guild.voice_channels, name=f"{member.display_name}'s channel")
            await voice_channel1.delete()


def setup(bot):
    bot.add_cog(Join_To_Create_Voice_Channel(bot))
