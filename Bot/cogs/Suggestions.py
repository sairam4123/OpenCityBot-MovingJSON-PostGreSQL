from typing import Optional

import discord
from discord.ext import commands

from .utils.emoji_adder import add_emojis_to_message
from .utils.timeformat_bot import indian_standard_time_now


class Suggestions(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.channel.type == discord.ChannelType.private:
            return True
        if await self.bot.is_owner(ctx.author):
            return True
        enabled = await self.bot.pg_conn.fetchval("""
         SELECT enabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            return True
        return False

    @commands.group(help="Does nothing when invoked without subcommand.")
    async def suggestion(self, ctx):
        pass

    @commands.group(help="Suggest something!", invoke_without_command=True, usage="<type_of_suggestion> <suggestion>")
    async def suggest(self, ctx: commands.Context, type1, *, suggestion: str):
        suggestion_id = await self.bot.pg_conn.fetchval("""
        SELECT suggestion_id FROM id_data
        """)
        suggestion_number = await self.bot.pg_conn.fetchval("""
        SELECT suggestion_number FROM count_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        title = f"Suggestion #{suggestion_number}"
        embed = discord.Embed(
            title=title,
            description=(
                f"**Suggestion**: {suggestion}\n"
                f"**Suggestion by**: {ctx.author.mention}"
            ),
            color=discord.Colour.green()
        ).set_footer(text=f"SuggestionID: {suggestion_id} | {indian_standard_time_now()[1]}")
        embed.set_author(name=f"{ctx.author.name}", icon_url=f"{ctx.author.avatar_url}")
        message_sent = await ctx.send(embed=embed)
        try:
            await add_emojis_to_message([":_tick:705003237174018179", ":_neutral:705003236687609936", ":_cross:705003237174018158", ":_already_there:705003236897194004"],
                                        message_sent)
        except (discord.Forbidden, discord.NotFound):
            pass
        await self.bot.pg_conn.execute("""
        INSERT INTO suggestion_data
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, suggestion_id, message_sent.id, title, suggestion, f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})", indian_standard_time_now()[1],
                                       message_sent.channel.id, message_sent.guild.id, type1, "waiting", "Null")
        await self.bot.pg_conn.execute("""
        UPDATE id_data
        SET suggestion_id = suggestion_id + 1
        WHERE row_id = 1
        """)
        await self.bot.pg_conn.execute("""
        UPDATE count_data
        SET suggestion_number = suggestion_number + 1
        WHERE guild_id = $1
        """, ctx.guild.id)
        await ctx.author.send("Your suggestion is sent!, This is how your suggestion look like!", embed=embed)

    @suggestion.command(name="approve", help="Approves a suggestion.")
    async def suggestion_approve(self, ctx: commands.Context, suggestion_id: int, *, reason: Optional[str] = None):
        suggestion = await self.bot.pg_conn.fetchrow("""
        SELECT * FROM suggestion_data
        WHERE "suggestionID" = $1
        """, suggestion_id)
        if not suggestion:
            return await ctx.send(f"{suggestion_id} is wrong")
        embed = discord.Embed()
        author = ctx.guild.get_member(int(suggestion['suggestionAuthor'].split(' ')[-1].strip('( )')))
        suggestion_moderator = f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        embed.title = suggestion['suggestionTitle'] + " Approved"
        embed.description = (
            f"**Suggestion**: {suggestion['suggestionContent']}\n"
            f"**Suggested by**: {author.mention}"
        )
        if reason:
            embed.add_field(name=f"Reason by {f'{ctx.author.name}#{ctx.author.discriminator}'}", value=reason)
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.colour = discord.Colour.dark_green()
        embed.set_footer(text=f"SuggestionID: {suggestion['suggestionID']} | {suggestion['suggestionTime']}")
        suggestion_guild = self.bot.get_guild(suggestion['suggestionGuildID'])
        suggestion_channel = suggestion_guild.get_channel(suggestion['suggestionChannelID'])
        suggestion_message = await suggestion_channel.fetch_message(suggestion["suggestionMessageID"])
        await suggestion_message.edit(embed=embed)
        await self.bot.pg_conn.execute("""
        UPDATE suggestion_data 
        SET "suggestionStatus" = $2, 
        "suggestionModerator" = $3
        WHERE "suggestionID" = $1
        """, suggestion_id, "approved", suggestion_moderator)
        await ctx.send(f"Approved suggestion {suggestion_id} because of {reason}")

    @suggestion.command(name="deny", help="Denies a suggestion.")
    async def suggestion_deny(self, ctx: commands.Context, suggestion_id: int, *, reason: Optional[str] = None):
        suggestion = self.bot.pg_conn.fetchrow("""
                SELECT * FROM suggestion_data
                WHERE "suggestionID" = $1
                """, suggestion_id)
        if not suggestion:
            return await ctx.send(f"{suggestion_id} is wrong")
        embed = discord.Embed()
        author = ctx.guild.get_member(int(suggestion['suggestionAuthor'].split(' ')[-1].strip('( )')))
        suggestion_moderator = f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        embed.title = suggestion['suggestionTitle'] + " Denied"
        embed.description = (
            f"**Suggestion**: {suggestion['suggestionContent']}\n"
            f"**Suggested by**: {author.mention}"
        )
        if reason:
            embed.add_field(name=f"Reason by {f'{ctx.author.name}#{ctx.author.discriminator}'}", value=reason)
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.colour = discord.Colour.blue()
        embed.set_footer(text=f"SuggestionID: {suggestion['suggestionID']} | {suggestion['suggestionTime']}")
        suggestion_guild = self.bot.get_guild(suggestion['suggestionGuildID'])
        suggestion_channel = suggestion_guild.get_channel(suggestion['suggestionChannelID'])
        suggestion_message = await suggestion_channel.fetch_message(suggestion["suggestionMessageID"])
        await suggestion_message.edit(embed=embed)
        await self.bot.pg_conn.execute("""
        UPDATE suggestion_data 
        SET "suggestionStatus" = $2, 
        "suggestionModerator" = $3
        WHERE "suggestionID" = $1
        """, suggestion_id, "denied", suggestion_moderator)
        await ctx.send(f"Denied suggestion {suggestion_id} because of {reason}")

    @suggestion.command(name="consider", help="Marks a suggestion as considered.")
    async def suggestion_consider(self, ctx: commands.Context, suggestion_id: int, *, reason: Optional[str] = None):
        suggestion = self.bot.pg_conn.fetchrow("""
                    SELECT * FROM suggestion_data
                    WHERE "suggestionID" = $1
                    """, suggestion_id)
        if not suggestion:
            return await ctx.send(f"{suggestion_id} is wrong")
        embed = discord.Embed()
        author = ctx.guild.get_member(int(suggestion['suggestionAuthor'].split(' ')[-1].strip('( )')))
        suggestion_moderator = f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        embed.title = suggestion[0]['suggestionTitle'] + " Considered"
        embed.description = (
            f"**Suggestion**: {suggestion['suggestionContent']}\n"
            f"**Suggested by**: {author.mention}"
        )
        if reason:
            embed.add_field(name=f"Reason by {f'{ctx.author.name}#{ctx.author.discriminator}'}", value=reason)
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.colour = discord.Colour.dark_red()
        embed.set_footer(text=f"SuggestionID: {suggestion['suggestionID']} | {suggestion[0]['suggestionTime']}")
        suggestion_guild = self.bot.get_guild(suggestion['suggestionGuildID'])
        suggestion_channel = suggestion_guild.get_channel(suggestion['suggestionChannelID'])
        suggestion_message = await suggestion_channel.fetch_message(suggestion["suggestionMessageID"])
        await suggestion_message.edit(embed=embed)
        await self.bot.pg_conn.execute("""
            UPDATE suggestion_data 
            SET "suggestionStatus" = $2, 
            "suggestionModerator" = $3
            WHERE "suggestionID" = $1
        """, suggestion_id, "considered", suggestion_moderator)
        await ctx.send(f"Marked suggestion {suggestion_id} as considered because of {reason}")

    @suggestion.command(name="implemented", help="Marks a suggestion as already implemented.")
    async def suggestion_implemented(self, ctx: commands.Context, suggestion_id: int, *, reason: Optional[str] = None):
        suggestion = await self.bot.pg_conn.fetchrow("""
               SELECT * FROM suggestion_data
               WHERE "suggestionID" = $1
               """, suggestion_id)
        if not suggestion:
            return await ctx.send(f"{suggestion_id} is wrong")
        embed = discord.Embed()
        author = ctx.guild.get_member(int(suggestion['suggestionAuthor'].split(' ')[-1].strip('( )')))
        suggestion_moderator = f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        embed.title = suggestion['suggestionTitle'] + " Implemented"
        embed.description = (
            f"**Suggestion**: {suggestion['suggestionContent']}\n"
            f"**Suggested by**: {author.mention}"
        )
        if reason:
            embed.add_field(name=f"Reason by {f'{ctx.author.name}#{ctx.author.discriminator}'}", value=reason)
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.colour = discord.Colour.dark_green()
        embed.set_footer(text=f"SuggestionID: {suggestion['suggestionID']} | {suggestion['suggestionTime']}")
        suggestion_guild = self.bot.get_guild(suggestion['suggestionGuildID'])
        suggestion_channel = suggestion_guild.get_channel(suggestion['suggestionChannelID'])
        suggestion_message = await suggestion_channel.fetch_message(suggestion["suggestionMessageID"])
        await suggestion_message.edit(embed=embed)
        await self.bot.pg_conn.execute("""
               UPDATE suggestion_data 
               SET "suggestionStatus" = $2, 
               "suggestionModerator" = $3
               WHERE "suggestionID" = $1
               """, suggestion_id, "implemented", suggestion_moderator)
        await ctx.send(f"Marked suggestion {suggestion_id} as already implemented because of {reason}")


def setup(bot):
    bot.add_cog(Suggestions(bot))
