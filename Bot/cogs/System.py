from typing import Union

import discord
from discord.ext import commands

from .utils.list_manipulation import insert_or_append, pop_or_remove


class System(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    @commands.is_owner()
    async def blacklist(self, ctx: commands.Context, member_or_user: Union[discord.User, discord.Member], *, reason: str):
        black_listed_users = await self.bot.pg_conn.fetchval("""
        SELECT black_listed_users FROM black_listed_users_data
        """)
        if not black_listed_users:
            await self.bot.pg_conn.execute("""
            INSERT INTO black_listed_users_data
            VALUES ($1, 1)
            """, [])
        black_listed_users, member_or_user_id, index = insert_or_append(black_listed_users, member_or_user.id)
        await self.bot.pg_conn.execute("""
        UPDATE black_listed_users_data
        SET black_listed_users = $1
        WHERE row_id = 1
        """, black_listed_users)
        reason = reason.strip('"')
        await ctx.send(f"I have blacklisted **{member_or_user.display_name}#{member_or_user.discriminator}** because of {reason}")

    @commands.command()
    @commands.is_owner()
    async def unblacklist(self, ctx: commands.Context, member_or_user: Union[discord.User, discord.Member], *, reason: str):
        black_listed_users = await self.bot.pg_conn.fetchval("""
            SELECT black_listed_users FROM black_listed_users_data
            """)
        if not black_listed_users:
            await self.bot.pg_conn.execute("""
                INSERT INTO black_listed_users_data
                VALUES ($1, 1)
                """, [])
        black_listed_users, member_or_user_id, index = pop_or_remove(black_listed_users, member_or_user.id)
        await self.bot.pg_conn.execute("""
            UPDATE black_listed_users_data
            SET black_listed_users = $1
            WHERE row_id = 1
            """, black_listed_users)
        reason = reason.strip('"')
        await ctx.send(f"I have unblacklisted **{member_or_user.display_name}#{member_or_user.discriminator}** because of \"{reason}\".")


def setup(bot):
    bot.add_cog(System(bot))
