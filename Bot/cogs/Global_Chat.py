import discord
from discord.ext import commands


class Global_Chat(commands.Cog):

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
        if message.channel.name == "global_-_chat":
            if message.author == self.bot.user:
                return
            if message.author.bot:
                return await message.delete()
            message_1 = message
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    if channel.name == "global_-_chat":
                        embed = discord.Embed(
                            color=message_1.author.color,
                            title=f"Sender: {message_1.author.display_name}#{message_1.author.discriminator}",
                            description=message_1.content
                        ).set_footer(text=f"From: {message_1.guild.name} | Author ID: {message_1.author.id}").set_thumbnail(url=message_1.author.avatar_url) \
                            .set_author(name=message_1.author.display_name, icon_url=message_1.author.avatar_url)
                        await channel.send(embed=embed)
            await message.delete()


def setup(bot):
    bot.add_cog(Global_Chat(bot))
