from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import BucketType

from .utils.list_manipulation import insert_or_append, pop_or_remove
from .utils.timeformat_bot import indian_standard_time_now
from .utils.transcriptor import message_history_into_transcript_file_object


class Ticket(commands.Cog):

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

    @commands.group(help="Does nothing when send without subcommands")
    async def ticket(self, ctx: commands.Context):
        pass

    @ticket.command(name="new", help="Creates a new ticket!")
    async def ticket_new(self, ctx: commands.Context, *, reason: Optional[str] = "No reason Provided"):
        ticket_id = await self.bot.pg_conn.fetchval("""
                SELECT ticket_id FROM id_data
                """)
        ticket_number = await self.bot.pg_conn.fetchval("""
                SELECT ticket_number FROM count_data
                WHERE guild_id = $1
                """, ctx.guild.id)
        support_role = discord.utils.find(lambda r: r.name == "Support", ctx.guild.roles)
        if support_role is None:
            await ctx.guild.create_role(name="Support")
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            ctx.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)

        }
        author = f"{ctx.author} ({ctx.author.id})"
        embed = discord.Embed(
            title=f"Thank you for creating a ticket! {ctx.author.name} This is Ticket #{ticket_number}",
            description=f"Thank you for creating a ticket! {ctx.author.mention}\nWe'll get back to you as soon as possible.",
        )
        embed.set_footer(text=f"TicketID: {ticket_id} | {indian_standard_time_now()[1]}")
        if not discord.utils.get(ctx.guild.categories, name="Support"):
            await ctx.guild.create_category(name="Support")
        channel = await ctx.guild.create_text_channel(name=f'{ctx.author.name}-{ctx.author.discriminator}', category=discord.utils.get(ctx.guild.categories, name="Support"),
                                                      overwrites=overwrites)
        await channel.edit(topic=f"Opened by {ctx.author.name} - All messages sent to this channel are being recorded.")
        await channel.send(embed=embed)
        await self.bot.pg_conn.execute("""
                INSERT INTO ticket_data
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, ticket_id, reason, author, indian_standard_time_now()[1], "Not closed till now.", ctx.guild.id, "Open", ["No user was added till now."], "Null", channel.id)
        await self.bot.pg_conn.execute("""
                UPDATE id_data
                SET ticket_id = ticket_id + 1
                WHERE row_id = 1
                """)
        await self.bot.pg_conn.execute("""
                UPDATE count_data
                SET ticket_number = ticket_number + 1
                WHERE guild_id = $1
                """, ctx.guild.id)

    @ticket.command(help="Close a active ticket!")
    async def close(self, ctx: commands.Context, ticket_id: Optional[int]):
        ticket = await self.bot.pg_conn.fetchrow("""
        SELECT * FROM ticket_data
        WHERE "ticketID" = $1 OR "ticketChannelID" = $2
        """, ticket_id, ctx.channel.id)
        ticket_owner = ctx.guild.get_member(int(ticket['ticketAuthor'].split(' ')[-1].strip('( )')))
        if (ctx.channel.id == int(ticket['ticketChannelID'])) or (discord.utils.get(ctx.guild.roles, name="Support") in ctx.author.roles) or (ctx.author == ctx.guild.owner):
            file = await message_history_into_transcript_file_object(ctx.channel, ticket_owner, ticket['ticketID'])
            await ticket_owner.send(file=file)
            moderator = f"{ctx.author} ({ctx.author.id})"
            await self.bot.pg_conn.execute("""
            UPDATE ticket_data
            SET "ticketClosedTime" = $2,
            "ticketStatus" = 'closed',
            "ticketModerator" = $3
            WHERE "ticketID" = $1
            """, ticket_id, indian_standard_time_now()[1], moderator)
            channel = discord.utils.get(ctx.guild.text_channels, id=int(ticket['ticketChannelID']))
            await channel.delete()

    @ticket.command(name="add_suffix", help="Adds a suffix to the ticket.")
    @commands.cooldown(2, 10, BucketType.guild)
    async def ticket_add_suffix(self, ctx: commands.Context, ticket_id: Optional[int], suffix: str):
        ticket = await self.bot.pg_conn.fetchrow("""
        SELECT * FROM ticket_data
        WHERE "ticketID" = $1 OR "ticketChannelID" = $2
        """, ticket_id, ctx.channel.id)
        channel: discord.TextChannel = ctx.guild.get_channel(int(ticket['ticketChannelID']))
        suffix_1 = suffix.replace('"', '')
        print(f"-{suffix_1.replace(' ', '-')}")
        name = channel.name + f"-{suffix_1.replace(' ', '-')}"
        print("lk")
        await channel.edit(name=name)
        print("something")
        await ctx.send(f"Added suffix to ticket {ticket['ticketID']}")

    @ticket.command(name="remove_suffix", help="Removes all suffix from ticket.")
    @commands.cooldown(2, 10)
    async def ticket_remove_suffix(self, ctx: commands.Context, ticket_id: Optional[int]):
        ticket = await self.bot.pg_conn.fetchrow("""
                SELECT * FROM ticket_data
                WHERE "ticketID" = $1 OR "ticketChannelID" = $2
                """, ticket_id, ctx.channel.id)
        channel: discord.TextChannel = ctx.guild.get_channel(int(ticket['ticketChannelID']))
        ticket_owner = ctx.guild.get_member(int(ticket['ticketAuthor'].split(' ')[-1].strip('( )')))
        name = f"{ticket_owner.name}-{ticket_owner.discriminator}"
        await channel.edit(name=name)
        await ctx.send(f"Removed suffix from ticket {ticket['ticketID']}")

    @ticket.command(name='transcript', help="Gets transcript of the ticket.")
    async def ticket_transcript(self, ctx: commands.Context, ticket_id: Optional[int]):
        ticket = await self.bot.pg_conn.fetchrow("""
                SELECT * FROM ticket_data
                WHERE "ticketID" = $1 OR "ticketChannelID" = $2
                """, ticket_id, ctx.channel.id)
        channel = ctx.guild.get_channel(int(ticket['ticketChannelID']))
        ticket_owner = ctx.guild.get_member(int(ticket['ticketAuthor'].split(' ')[-1].strip('( )')))
        file = await message_history_into_transcript_file_object(channel, ticket_owner, ticket['ticketID'])
        await ticket_owner.send(file=file)

    @ticket.group(name="users", invoke_without_command=True, help="Returns all users added to ticket.")
    async def ticket_users(self, ctx: commands.Context, ticket_id: Optional[int]):
        ticket = await self.bot.pg_conn.fetchrow("""
        SELECT * FROM ticket_data
        WHERE "ticketID" = $1 OR "ticketChannelID" = $2
        """, ticket_id, ctx.channel.id)
        embed = discord.Embed()
        msg = ""
        for user_index, user in enumerate(ticket['ticketUsers'], start=1):
            if user == "No user was added till now.":
                msg = user
            else:
                user = ctx.guild.get_member(int(user.split(' ')[-1].strip('( )')))
                msg += f"{user_index}. {user.mention}"
        embed.description = msg
        embed.title = "Here are the members who was added by the staff."
        await ctx.send(embed=embed)

    @ticket_users.command(name="add", aliases=['+'], help="Adds a users to the ticket.")
    async def ticket_users_add(self, ctx: commands.Context, ticket_id: Optional[int], user: Optional[discord.Member]):
        ticket = await self.bot.pg_conn.fetchrow("""
        SELECT * FROM ticket_data
        WHERE "ticketID" = $1 OR "ticketChannelID" = $2
        """, ticket_id, ctx.channel.id)
        ticket_users = ticket['ticketUsers']
        user_1 = f"{user} ({user.id})"
        ticket_users, user_1, index = insert_or_append(ticket_users, user_1)
        if ticket_users:
            ticket_users.remove("No user was added till now.")
        channel: discord.TextChannel = discord.utils.get(ctx.guild.text_channels, id=ticket['ticketChannelID'])
        if channel:
            overwrites = channel.overwrites
            overwrites[user] = discord.PermissionOverwrite(read_messages=False, send_messages=False, read_message_history=False)
            await channel.edit(overwrites=overwrites)
            await channel.set_permissions(user, overwrite=None)
        await self.bot.pg_conn.execute("""
        UPDATE ticket_data
        SET "ticketUsers" = $1
        WHERE "ticketID" = $2 OR "ticketChannelID" = $3
        """, ticket_users, ticket_id, ctx.channel.id)
        await ctx.send(f"User {user.mention} was successfully added to the ticket \"{ticket_id if ticket_id is not None else ticket['ticketID']}\"")

    @ticket_users.command(name="remove", aliases=['-'], help="Removes a user from the ticket.")
    async def ticket_users_remove(self, ctx: commands.Context, ticket_id: Optional[int], user: Optional[discord.Member]):
        ticket = await self.bot.pg_conn.fetchrow("""
               SELECT * FROM ticket_data
               WHERE "ticketID" = $1 OR "ticketChannelID" = $2
               """, ticket_id, ctx.channel.id)
        ticket_users = ticket['ticketUsers']
        user_1 = f"{user} ({user.id})"
        ticket_users, user_1, index = pop_or_remove(ticket_users, user_1)
        if not ticket_users:
            ticket_users.append("No user was added till now.")
        channel: discord.TextChannel = discord.utils.get(ctx.guild.text_channels, id=ticket['ticketChannelID'])
        if channel:
            overwrites = channel.overwrites
            overwrites[user] = discord.PermissionOverwrite(read_messages=False, send_messages=False, read_message_history=False)
            await channel.edit(overwrites=overwrites)
            await channel.set_permissions(user, overwrite=None)
        await self.bot.pg_conn.execute("""
               UPDATE ticket_data
               SET "ticketUsers" = $1
               WHERE "ticketID" = $2 OR "ticketChannelID" = $3
               """, ticket_users, ticket_id, ctx.channel.id)
        await ctx.send(f"User {user.mention} was successfully removed from the ticket \"{ticket_id if ticket_id is not None else ticket['ticketID']}\"")


def setup(bot):
    bot.add_cog(Ticket(bot))
