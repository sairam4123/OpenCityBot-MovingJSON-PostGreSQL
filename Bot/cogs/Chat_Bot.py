import aiohttp
import discord
from discord.ext import commands


class Chat_Bot(commands.Cog):

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
        print(message.channel)
        if message.channel.name == 'open-city-bot-chat':
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://some-random-api.ml/chatbot?message={message.content}') as response:
                    print(response)
                    json_data = await response.json()
                    await message.channel.send(f"`{message.author.mention}`: {json_data['response']}")


def setup(bot):
    bot.add_cog(Chat_Bot(bot))
