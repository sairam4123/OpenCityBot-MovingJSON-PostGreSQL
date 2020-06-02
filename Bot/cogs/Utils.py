import binascii
import os
from typing import Optional

import aiohttp
from discord.ext import commands


class Utils(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # async def cog_check(self, ctx):
    #     if ctx.channel.type == discord.ChannelType.private:
    #         return True
    #     enabled = await self.bot.pg_conn.fetchrow("""
    #         SELECT enabled FROM cogs_data
    #         WHERE guild_id = $1
    #         """, ctx.guild.id)
    #     if f"Bot.cogs.{self.qualified_name}" in enabled:
    #         return True
    #     return False

    @staticmethod
    def random_color():
        print(binascii.b2a_hex(os.urandom(3)).decode('ascii'))
        return binascii.b2a_hex(os.urandom(3)).decode('ascii')

    @commands.command()
    async def color(self, ctx, color: Optional[str]):
        color = color if color else self.random_color()
        header = {'Application': "text/json"}
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.color-hex.com/color/' + f'{color}') as request:
                json = await request.json()
                print(json)


def setup(bot):
    bot.add_cog(Utils(bot))
