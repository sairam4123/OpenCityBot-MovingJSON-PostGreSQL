import binascii
import io
import os
from typing import Optional

import discord
from PIL import Image
from discord.ext import commands

from Bot.cogs.utils.color_builder import hex_to_rgb


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
        color_1 = color if color else self.random_color()
        image = Image.new("RGB", (500, 500), tuple(hex_to_rgb(color_1)))
        _file_ = io.BytesIO()
        image.save(_file_, "PNG")
        _file_.seek(0)
        embed = discord.Embed(title="Color", description=f"Hex code: `{color}`", image=f"attachment://color.png")
        await ctx.send(embed=embed, file=discord.File(_file_, "color.png"))


def setup(bot):
    bot.add_cog(Utils(bot))
