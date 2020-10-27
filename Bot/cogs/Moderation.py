import re
from typing import Optional

import discord
from better_profanity import profanity
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

    @commands.command(help="Adds a slowmode to a channel. If channel not passed it will be user.")
    async def slowmode(self, ctx, channel: Optional[discord.TextChannel], secs: int):
        channel = ctx.channel if not channel else channel
        await channel.edit(slowmode_delay=secs)
        await ctx.send(f"Added slowmode of `{secs}` to {channel.mention}")

    @commands.command(help='Bans the given user')
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, members: commands.Greedy[discord.Member], *, reason="No reason provided"):
        pass

    @commands.command(help='Kicks the given user')
    @commands.has_guild_permissions(kick_members=True)
    @commands.bot_has_guild_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason="No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name='Kicked Members')
        await member.add_roles(role, reason=reason)
        await ctx.send(f'{member} is kicked because of {reason}.')

    @commands.command(help="Mutes the given user")
    @commands.has_guild_permissions(manage_roles=True, manage_guild=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, *, reason="No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name='Muted Members')
        # self.bot.dispatch('member_mute', member)
        await member.add_roles(role, reason=reason)
        await ctx.send(f"{member} is muted because of {reason}.")

    @commands.command(help="Unmutes the given user")
    @commands.has_guild_permissions(manage_roles=True, manage_guild=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason="No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name='Muted Members')
        await member.remove_roles(role, reason=reason)
        await ctx.send(f"{member} is unmuted because of {reason}.")

    @commands.command(help='Unbans the given user')
    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, member: discord.Member, *, reason="No reason provided"):
        role = discord.utils.get(ctx.guild.roles, name='Banned Members')
        await member.remove_roles(role, reason=reason)
        await ctx.send(f'{member} is unbanned because of {reason}.')

    @commands.command(help="Purges the given amount of messages", aliases=['clear'])
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount_of_messages: Optional[int] = 12524, author: Optional[discord.Member] = None):
        await ctx.channel.purge(limit=amount_of_messages + 1, check=lambda m: True if author is None else m.author == author)

    @commands.command(help="Get the status!")
    async def status(self, ctx: commands.Context, member: discord.Member):
        await ctx.send(member.activity)

    @commands.Cog.listener()
    async def on_message_create(self, message: discord.Message):
        enabled = await self.bot.pg_conn.fetchval("""
        SELECT enabled FROM cogs_data
        WHERE guild_id = $1
        """, message.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            print(
                f"\"{message.content}\" in (#{message.channel} (ID: {message.channel.id}))  by ({message.author} (ID: {message.author.id})) in server ({message.guild.name} (ID: {message.guild.id}))")

            if not message.author.bot:
                # profanity.add_censor_words(['idiot', 'stupid', 'fool', 'rascal'])
                # print(discord.utils.escape_markdown(message.content))
                _MARKDOWN_ESCAPE_SUBREGEX = '|'.join(r'\{0}(?=([\s\S]*((?<!\{0})\{0})))'.format(c)
                                                     for c in ('*', '`', '_', '~', '|'))
                uppercase = re.findall(r'[A-Z]', message.content)
                print(uppercase)

                _MARKDOWN_ESCAPE_REGEX = re.compile(r'(?P<markdown>%s)' % _MARKDOWN_ESCAPE_SUBREGEX)
                regex = r'(?P<markdown>[_\\~|\*`]|>(?:>>)?\s)'
                print(((len(uppercase) / (len(message.content)))*100))
                print(((len(uppercase) / (len(message.content)))*100) <= 70)
                print(((len(uppercase) / (len(message.content))) * 100) >= 70)
                if profanity.contains_profanity(re.sub(regex, '', message.content)):
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} No swearing, over swearing will get you muted!", delete_after=5.0)
                elif int(((len(uppercase) / (len(message.content))) * 100)) >= 65:
                    await message.delete()
                    await message.channel.send(
                        f"{message.author.mention} Overuse of Uppercase is denied in this server, overuse of uppercase letters again and again will get you muted!", delete_after=5.0)


def setup(bot):
    bot.add_cog(Moderation(bot))
