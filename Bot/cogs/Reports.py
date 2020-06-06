from typing import Optional, Union

import discord
from Bot.cogs.utils.timeformat_bot import indian_standard_time_now
from discord.ext import commands


class Reports(commands.Cog):

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

    @commands.group(help="Report something!", invoke_without_command=True)
    async def report(self, ctx: commands.Context, reported_user: Union[discord.Member, discord.User], *, reason: str):
        report_id = await self.bot.pg_conn.fetchval("""
            SELECT report_id FROM id_data
            """)
        report_number = await self.bot.pg_conn.fetchval("""
            SELECT report_number FROM count_data
            WHERE guild_id = $1
            """, ctx.guild.id)
        if not report_id:
            await self.bot.pg_conn.execute("""
                INSERT INTO id_data (report_id)
                VALUES ($1)
                """, self.bot.start_number)
        if not report_number:
            await self.bot.pg_conn.execute("""
                UPDATE count_data
                SET report_number = $1
                WHERE guild_id = $2
                """, 1, ctx.guild.id)
        title = f"Report #{report_number}"
        embed = discord.Embed(
            title=title,
            description=(
                f"**Report for**: {reported_user.mention}\n"
                f"**Report by**: {ctx.author.mention}\n"
                f"**Report reason**: {reason}"
            ),
            color=discord.Colour.blurple()
        ).set_footer(text=f"ReportID: {report_id} | {indian_standard_time_now()[1]}")
        embed.set_author(name=f"{ctx.author.name}", icon_url=f"{ctx.author.avatar_url}")
        message_sent = await ctx.send(embed=embed)
        await message_sent.add_reaction(f":_tick:705003237174018179")
        await message_sent.add_reaction(f":_neutral:705003236687609936")
        await message_sent.add_reaction(f":_cross:705003237174018158")
        await self.bot.pg_conn.execute("""
            INSERT INTO report_data
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, report_id, message_sent.id, title, reason, f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})", indian_standard_time_now()[1],
                                       message_sent.channel.id, message_sent.guild.id, "waiting",
                                       f"{reported_user.name}#{reported_user.discriminator} ({reported_user.id})", "Null")
        await self.bot.pg_conn.execute("""
            UPDATE id_data
            SET report_id = $1
            WHERE row_id = 1
            """, int(int(report_id) + int(1)))
        await self.bot.pg_conn.execute("""
            UPDATE count_data
            SET report_number = $1
            WHERE guild_id = $2
            """, int(report_number) + 1, ctx.guild.id)
        await ctx.author.send("Your report is sent!, This is how your report look like!", embed=embed)

    @report.command(name="accept", help="Accepts a report.")
    async def report_accept(self, ctx: commands.Context, report_id: int, *, reason: Optional[str] = None):
        report = await self.bot.pg_conn.fetchrow("""
            SELECT * FROM report_data
            WHERE "reportID" = $1
            """, report_id)
        embed = discord.Embed()
        author = ctx.guild.get_member(int(report['reportAuthor'].split(' ')[-1].strip('( )')))
        reported_user = ctx.guild.get_member(int(report['reportUser'].split(' ')[-1].strip('( )')))
        report_moderator = f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        embed.title = report['reportTitle'] + " Accepted"
        embed.description = (
            f"**Report for**: {reported_user.mention}\n"
            f"**Report by**: {ctx.author.mention}\n"
            f"**Report reason**: {report['reportReason']}"
        )
        if reason:
            embed.add_field(name=f"Reason by {f'{ctx.author.name}#{ctx.author.discriminator}'}", value=reason)
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.colour = discord.Colour.dark_green()
        embed.set_footer(text=f"ReportID: {report['reportID']} | {report['reportTime']}")
        report_guild = self.bot.get_guild(report['reportGuildID'])
        report_channel = report_guild.get_channel(report['reportChannelID'])
        report_message = await report_channel.fetch_message(report["reportMessageID"])
        await report_message.edit(embed=embed)
        await self.bot.pg_conn.execute("""
            UPDATE report_data 
            SET "reportStatus" = $2, 
            "reportModerator" = $3
            WHERE "reportID" = $1
            """, report_id, "accepted", report_moderator)
        await ctx.send(f"Accepted report {report_id} because of {reason}")

    @report.command(name="decline", help="Declines a report.")
    async def report_decline(self, ctx: commands.Context, report_id: int, *, reason: Optional[str] = None):
        report = await self.bot.pg_conn.fetchrow("""
                SELECT * FROM report_data
                WHERE "reportID" = $1
                """, report_id)
        embed = discord.Embed()
        author = ctx.guild.get_member(int(report['reportAuthor'].split(' ')[-1].strip('( )')))
        reported_user = ctx.guild.get_member(int(report['reportUser'].split(' ')[-1].strip('( )')))
        report_moderator = f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        embed.title = report['reportTitle'] + " Declined"
        embed.description = (
            f"**Report for**: {reported_user.mention}\n"
            f"**Report by**: {ctx.author.mention}\n"
            f"**Report reason**: {report['reportReason']}"
        )
        if reason:
            embed.add_field(name=f"Reason by {f'{ctx.author.name}#{ctx.author.discriminator}'}", value=reason)
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.colour = discord.Colour.dark_green()
        embed.set_footer(text=f"ReportID: {report['reportID']} | {report['reportTime']}")
        report_guild = self.bot.get_guild(report['reportGuildID'])
        report_channel = report_guild.get_channel(report['reportChannelID'])
        report_message = await report_channel.fetch_message(report["reportMessageID"])
        await report_message.edit(embed=embed)
        await self.bot.pg_conn.execute("""
                UPDATE report_data 
                SET "reportStatus" = $2, 
                "reportModerator" = $3
                WHERE "reportID" = $1
                """, report_id, "declined", report_moderator)
        await ctx.send(f"Declined report {report_id} because of {reason}")

    @report.command(name="fake", help="Marks a report as fake.")
    async def report_fake(self, ctx: commands.Context, report_id: int, *, reason: Optional[str] = None):
        report = await self.bot.pg_conn.fetchrow("""
            SELECT * FROM report_data
            WHERE "reportID" = $1
            """, report_id)
        embed = discord.Embed()
        author = ctx.guild.get_member(int(report['reportAuthor'].split(' ')[-1].strip('( )')))
        reported_user = ctx.guild.get_member(int(report['reportUser'].split(' ')[-1].strip('( )')))
        report_moderator = f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        embed.title = report['reportTitle'] + " Fake"
        embed.description = (
            f"**Report for**: {reported_user.mention}\n"
            f"**Report by**: {ctx.author.mention}\n"
            f"**Report reason**: {report['reportReason']}"
        )
        if reason:
            embed.add_field(name=f"Reason by {f'{ctx.author.name}#{ctx.author.discriminator}'}", value=reason)
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.colour = discord.Colour.dark_green()
        embed.set_footer(text=f"ReportID: {report['reportID']} | {report['reportTime']}")
        report_guild = self.bot.get_guild(report['reportGuildID'])
        report_channel = report_guild.get_channel(report['reportChannelID'])
        report_message = await report_channel.fetch_message(report["reportMessageID"])
        await report_message.edit(embed=embed)
        await self.bot.pg_conn.execute("""
            UPDATE report_data 
            SET "reportStatus" = $2, 
            "reportModerator" = $3
            WHERE "reportID" = $1
            """, report_id, "fake", report_moderator)
        await ctx.send(f"Marked report {report_id} as fake because of {reason}")


def setup(bot):
    bot.add_cog(Reports(bot))
