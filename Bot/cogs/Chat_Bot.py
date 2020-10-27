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
        if message.author.bot:
            return
        if message.channel.name == 'open-city-bot-chat':
            async with message.channel.typing():
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'https://some-random-api.ml/chatbot?message={message.content}') as response:
                        # print(response)
                        json_data = None
                        while True:
                            try:
                                json_data = await response.json()
                            except aiohttp.ContentTypeError:
                                continue
                            else:
                                break
                        print(response.status)
                        if response.status != 200:
                            if "error" in json_data:
                                await message.channel.send(f"Something went wrong, {json_data.get('error')}")
                        await message.channel.send(f"`@{message.author.display_name}`: {json_data.get('response')}")


def setup(bot):
    bot.add_cog(Chat_Bot(bot))
