import asyncio
import binascii
import colorsys
import io
import os
import pathlib
import re
from typing import Optional, Union

import discord
from PIL import Image
from discord.ext import commands

from .utils.color_builder import rgb_tuple_to_rgb_int


class Utils(commands.Cog):

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

    @staticmethod
    def random_color():
        return "#" + binascii.b2a_hex(os.urandom(3)).decode('ascii')

    @commands.command(aliases=['color'], help="Returns a random color info if color not passed else info of the given color.")
    async def colour(self, ctx, color: Optional[str]):
        from colour import Color
        if re.match('([A-Fa-f0-9]{1,6})', color):
            color = ("#" + color.replace('#', ''))
        color_2 = color
        # print(3 <= len(color) <= 6 and color.startswith('#'))
        if 3 <= len(color) <= 6 and color.startswith('#'):
            for zero in range(len(color), 8):
                color += color_2[-1]
                if len(color) == 7:
                    break
        del color_2
        color_2 = color
        # print(1 <= len(color) <= 2 and color.startswith('#'))
        if 0 <= len(color) <= 3 and color.startswith('#'):
            for zero in range(len(color), 5):
                color += color_2[-1]
                if len(color) == 4:
                    break
        del color_2
        try:
            color_1 = Color(color)
        except ValueError as exc:
            return await ctx.send(exc)
        image = Image.new("RGB", (500, 500), tuple(map(int, map(lambda r: r*255, color_1.get_rgb()))))
        _file_ = io.BytesIO()
        image.save(_file_, "PNG")
        _file_.seek(0)
        embed = discord.Embed(title="Here's your requested color!",
                              description=f"Hex code: `{color_1.get_hex_l()}` \n RGB value: `{tuple(map(int, map(lambda r: r*255, color_1.get_rgb())))}` \n "
                                          f"Link: [color](https://www.color-hex.com/color/{color_1.get_hex().lstrip('#')}) \n"
                                          f"HLS Value: `{colorsys.rgb_to_hls(*tuple(map(int, map(lambda r: r*255, color_1.get_rgb()))))}` \n"
                                          f"HSV Value: `{colorsys.rgb_to_hsv(*tuple(map(int, map(lambda r: r*255, color_1.get_rgb()))))}` \n"
                                          f"YIQ Value: `{colorsys.rgb_to_yiq(*tuple(map(int, map(lambda r: r*255, color_1.get_rgb()))))}` \n"
                                          f"RGBInt: `{rgb_tuple_to_rgb_int(*tuple(map(int, map(lambda r: r*255, color_1.get_rgb()))))}`"
                              )
        embed.set_image(url=f"attachment://color.png")
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.colour = discord.Colour.from_rgb(*tuple(map(int, map(lambda r: r*255, color_1.get_rgb()))))
        await ctx.send(embed=embed, file=discord.File(_file_, "color.png"))

    @commands.command(help="Bookmarks a message. So you can read it later. ")
    async def bookmark(self, ctx, message_link: discord.Message):
        embed = discord.Embed()
        embed.title = "Bookmark"
        base_path = pathlib.Path(__file__).parent.resolve()
        print(base_path)
        file = open(base_path / r'images/654080405988966419.png', 'rb')
        embed.set_thumbnail(url="attachment://bookmark.png")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.description = message_link.content
        embed.add_field(name="Want to view that message?", value=f"[Here it is!]({message_link.jump_url})")
        await ctx.author.send(embed=embed, file=discord.File(file, 'bookmark.png'))

    @commands.command(help="Quotes the message.")
    async def quote(self, ctx, message_link: discord.Message):
        embed = discord.Embed()
        embed.title = "Quote"
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.description = message_link.content
        embed.add_field(name="Want to view that message?", value=f"[Here it is!]({message_link.jump_url})")
        await ctx.send(embed=embed)

    @commands.command(help="Gives the avatar.", name="avatar", aliases=['av'])
    async def avatar(self, ctx, member: Optional[Union[discord.Member, discord.User]]):
        member = ctx.author if not member else member
        embed = discord.Embed(title=f"Avatar for {member}")
        png = f"[png]({member.avatar_url_as(format='png')})"
        jpg = f"[jpg]({member.avatar_url_as(format='jpg')})"
        webp = f"[webp]({member.avatar_url_as(format='webp')})"
        jepg = f"[jepg]({member.avatar_url_as(format='jpeg')})"
        gif = f"[gif]({member.avatar_url_as(format='gif')})" if member.is_avatar_animated() else "|| gif not available ||"
        embed.add_field(name="Link as", value=f"{png} | {jpg} | {webp} | {gif} | {jepg}")
        embed.set_image(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(help="Pins all messages in a specific channel.", aliases=['pe', 'p_e', 'pin_all', 'pa', 'p_a'])
    async def pin_everything(self, ctx: commands.Context, channel: discord.TextChannel):
        count = 0
        async for message in channel.history():
            await message.pin()
            count += 1
            await asyncio.sleep(0.25)
        await channel.purge(limit=count)
        await ctx.send("Pinned all the messages in the channel. And deleted the pin message.")


def setup(bot):
    bot.add_cog(Utils(bot))
