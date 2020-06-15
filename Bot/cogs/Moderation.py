from typing import Optional

import discord
from discord.ext import commands


class Moderation(commands.Cog):

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

    @commands.command()
    async def slowmode(self, ctx, channel: Optional[discord.TextChannel], secs: int):
        channel = ctx.channel if not channel else channel
        await channel.edit(slowmode_delay=secs)
        await ctx.send(f"Added slowmode of `{secs}` to {channel.mention}")

    @commands.command(help='Bans the given user')
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx: discord.ext.commands.context.Context, member: discord.Member, *, reason="No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name='Banned Members')
        await member.add_roles(role, reason=reason)
        await ctx.send(f'{member} is banned because of {reason}.')

    @commands.command(help='Kicks the given user')
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx: discord.ext.commands.context.Context, member: discord.Member, *, reason="No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name='Kicked Members')
        await member.add_roles(role, reason=reason)
        await ctx.send(f'{member} is kicked because of {reason}.')

    @commands.command(help="Mutes the given user")
    @commands.has_guild_permissions(manage_roles=True)
    async def mute(self, ctx: discord.ext.commands.context.Context, member: discord.Member, *, reason="No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name='Muted Members')
        # self.bot.dispatch('member_mute', member)
        await member.add_roles(role, reason=reason)
        await ctx.send(f"{member} is muted because of {reason}.")

    @commands.command(help="Unmutes the given user")
    @commands.has_guild_permissions(manage_roles=True)
    async def unmute(self, ctx: discord.ext.commands.context.Context, member: discord.Member, *, reason="No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name='Muted Members')
        await member.remove_roles(role, reason=reason)
        await ctx.send(f"{member} is unmuted because of {reason}.")

    @commands.command(help='Unbans the given user')
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx: discord.ext.commands.context.Context, member: discord.Member, *, reason="No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name='Banned Members')
        await member.remove_roles(role, reason=reason)
        await ctx.send(f'{member} is unbanned because of {reason}.')

    @commands.command(help='Unkicks the given user')
    @commands.has_guild_permissions(kick_members=True)
    async def unkick(self, ctx: discord.ext.commands.context.Context, member: discord.Member, *, reason="No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name='Kicked Members')
        await member.remove_roles(role, reason=reason)
        await ctx.send(f'{member} is unkicked because of {reason}.')

    @commands.command(help="Purges the given amount of messages", aliases=['clear'])
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx: discord.ext.commands.context.Context, amount_of_messages=11110, author: Optional[discord.Member] = None):
        await ctx.channel.purge(limit=amount_of_messages, check=lambda m: True if author is None else m.author == author)

    @commands.command(help="Get the status!")
    async def status(self, ctx: commands.Context, member: discord.Member):
        await ctx.send(member.activity)


def setup(bot):
    bot.add_cog(Moderation(bot))
