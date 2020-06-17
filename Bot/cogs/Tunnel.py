from typing import Optional

import discord
from discord.ext import commands

from .utils.list_manipulation import insert_or_append, pop_or_remove
from .utils.timeformat_bot import indian_standard_time_now
from .utils.transcriptor import message_history_into_transcript_file_object


class Tunnel(commands.Cog):

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
    async def tunnel(self, ctx: commands.Context):
        pass

    @tunnel.command(name="new", help="Creates a new tunnel!")
    async def tunnel_new(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = "No reason Provided"):
        tunnel_id = await self.bot.pg_conn.fetchval("""
                    SELECT tunnel_id FROM id_data
                    """)
        tunnel_number = await self.bot.pg_conn.fetchval("""
                    SELECT tunnel_number FROM count_data
                    WHERE guild_id = $1
                    """, ctx.guild.id)
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)
        }
        author = f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        embed = discord.Embed(
            title=f"Thank you for creating a tunnel! {ctx.author.name} This is Tunnel #{tunnel_number}",
            description=f"Thank you for creating a tunnel! {ctx.author.mention}\nWe'll get back to you as soon as possible.",
        )
        embed.set_footer(text=f"TunnelID: {tunnel_id} | {indian_standard_time_now()[1]}")
        member_ = f"{member.name}#{member.discriminator} ({member.id})"
        if not discord.utils.get(ctx.guild.categories, name="Tunnels"):
            await ctx.guild.create_category(name="Tunnels")
        channel = await ctx.guild.create_text_channel(name=f'{ctx.author.name}-{ctx.author.discriminator}-_-{member.name}-{member.discriminator}',
                                                      category=discord.utils.get(ctx.guild.categories, name="Tunnels"),
                                                      overwrites=overwrites)
        await channel.edit(topic=f"Opened by {ctx.author.name} - All messages sent to this channel are being recorded.")
        await channel.send(embed=embed)
        await self.bot.pg_conn.execute("""
                    INSERT INTO tunnel_data
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, tunnel_id, reason, author, indian_standard_time_now()[1], "Not closed till now.", ctx.guild.id, "Open", [member_], "Null", channel.id)
        await self.bot.pg_conn.execute("""
                    UPDATE id_data
                    SET tunnel_id = tunnel_id + 1
                    WHERE row_id = 1
                    """)
        await self.bot.pg_conn.execute("""
                    UPDATE count_data
                    SET tunnel_number = tunnel_number + 1
                    WHERE guild_id = $1
                    """, ctx.guild.id)

    @tunnel.command(help="Close a active tunnel!")
    async def close(self, ctx: commands.Context, tunnel_id: Optional[int]):
        tunnel = await self.bot.pg_conn.fetchrow("""
            SELECT * FROM tunnel_data
            WHERE "tunnelID" = $1 OR "tunnelChannelID" = $2
            """, tunnel_id, ctx.channel.id)
        tunnel_owner = ctx.guild.get_member(int(tunnel['tunnelAuthor'].split(' ')[-1].strip('( )')))
        if (ctx.channel.id == int(tunnel['tunnelChannelID'])) or (discord.utils.get(ctx.guild.roles, name="Support") in ctx.author.roles) or (ctx.author == ctx.guild.owner):
            file = await message_history_into_transcript_file_object(ctx.channel, tunnel_owner, tunnel['tunnelID'])
            await tunnel_owner.send(file=file)
            moderator = f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
            await self.bot.pg_conn.execute("""
                UPDATE tunnel_data
                SET "tunnelClosedTime" = $2,
                "tunnelStatus" = 'closed',
                "tunnelModerator" = $3
                WHERE "tunnelID" = $1
                """, tunnel_id, indian_standard_time_now()[1], moderator)
            channel = discord.utils.get(ctx.guild.text_channels, id=int(tunnel['tunnelChannelID']))
            await channel.delete()

    # @tunnel.command(name="add_suffix")
    # @commands.cooldown(2, 10, BucketType.guild)
    # async def tunnel_add_suffix(self, ctx: commands.Context, tunnel_id: Optional[int], suffix: str):
    #     tunnel = await self.bot.pg_conn.fetchrow("""
    #         SELECT * FROM tunnel_data
    #         WHERE "tunnelID" = $1 OR "tunnelChannelID" = $2
    #         """, tunnel_id, ctx.channel.id)
    #     channel: discord.TextChannel = ctx.guild.get_channel(int(tunnel['tunnelChannelID']))
    #     suffix_1 = suffix.replace('"', '')
    #     print(f"-{suffix_1.replace(' ', '-')}")
    #     name = channel.name + f"-{suffix_1.replace(' ', '-')}"
    #     print("lk")
    #     await channel.edit(name=name)
    #     print("something")
    #     await ctx.send(f"Added suffix to tunnel {tunnel['tunnelID']}")
    #
    # @tunnel.command(name="remove_suffix")
    # @commands.cooldown(2, 10)
    # async def tunnel_remove_suffix(self, ctx: commands.Context, tunnel_id: Optional[int]):
    #     tunnel = await self.bot.pg_conn.fetchrow("""
    #                 SELECT * FROM tunnel_data
    #                 WHERE "tunnelID" = $1 OR "tunnelChannelID" = $2
    #                 """, tunnel_id, ctx.channel.id)
    #     channel: discord.TextChannel = ctx.guild.get_channel(int(tunnel['tunnelChannelID']))
    #     tunnel_owner = ctx.guild.get_member(int(tunnel['tunnelAuthor'].split(' ')[-1].strip('( )')))
    #     name = f"{tunnel_owner.name}-{tunnel_owner.discriminator}"
    #     await channel.edit(name=name)
    #     await ctx.send(f"Removed suffix from tunnel {tunnel['tunnelID']}")

    @tunnel.command(name='transcript')
    async def tunnel_transcript(self, ctx: commands.Context, tunnel_id: Optional[int]):
        tunnel = await self.bot.pg_conn.fetchrow("""
                    SELECT * FROM tunnel_data
                    WHERE "tunnelID" = $1 OR "tunnelChannelID" = $2
                    """, tunnel_id, ctx.channel.id)
        channel = ctx.guild.get_channel(int(tunnel['tunnelChannelID']))
        tunnel_owner = ctx.guild.get_member(int(tunnel['tunnelAuthor'].split(' ')[-1].strip('( )')))
        file = await message_history_into_transcript_file_object(channel, tunnel_owner, tunnel['tunnelID'])
        await tunnel_owner.send(file=file)

    @tunnel.group(name="users", invoke_without_command=True)
    async def tunnel_users(self, ctx: commands.Context, tunnel_id: Optional[int]):
        tunnel = await self.bot.pg_conn.fetchrow("""
            SELECT * FROM tunnel_data
            WHERE "tunnelID" = $1 OR "tunnelChannelID" = $2
            """, tunnel_id, ctx.channel.id)
        embed = discord.Embed()
        msg = ""
        for user_index, user in enumerate(tunnel['tunnelUsers'], start=1):
            if user == "No user was added till now.":
                msg = user
            else:
                user = ctx.guild.get_member(int(user.split(' ')[-1].strip('( )')))
                msg += f"{user_index}. {user.mention}"
        embed.description = msg
        embed.title = "Here are the members who was added by the staff."
        await ctx.send(embed=embed)

    @tunnel_users.command(name="add", aliases=['+'])
    async def tunnel_users_add(self, ctx: commands.Context, tunnel_id: Optional[int], user: Optional[discord.Member]):
        tunnel = await self.bot.pg_conn.fetchrow("""
            SELECT * FROM tunnel_data
            WHERE "tunnelID" = $1 OR "tunnelChannelID" = $2
            """, tunnel_id, ctx.channel.id)
        tunnel_users = tunnel['tunnelUsers']
        user_1 = f"{user.name}#{user.discriminator} ({user.id})"
        tunnel_users, user_1, index = insert_or_append(tunnel_users, user_1)
        if tunnel_users:
            tunnel_users.remove("No user was added till now.")
        channel: discord.TextChannel = discord.utils.get(ctx.guild.text_channels, id=tunnel['tunnelChannelID'])
        if channel:
            overwrites = channel.overwrites
            overwrites[user] = discord.PermissionOverwrite(read_messages=False, send_messages=False, read_message_history=False)
            await channel.edit(overwrites=overwrites)
            await channel.set_permissions(user, overwrite=None)
        await self.bot.pg_conn.execute("""
            UPDATE tunnel_data
            SET "tunnelUsers" = $1
            WHERE "tunnelID" = $2 OR "tunnelChannelID" = $3
            """, tunnel_users, tunnel_id, ctx.channel.id)
        await ctx.send(f"User {user.mention} was successfully added to the tunnel \"{tunnel_id if tunnel_id is not None else tunnel['tunnelID']}\"")

    @tunnel_users.command(name="remove", aliases=['-'])
    async def tunnel_users_remove(self, ctx: commands.Context, tunnel_id: Optional[int], user: Optional[discord.Member]):
        tunnel = await self.bot.pg_conn.fetchrow("""
                   SELECT * FROM tunnel_data
                   WHERE "tunnelID" = $1 OR "tunnelChannelID" = $2
                   """, tunnel_id, ctx.channel.id)
        tunnel_users = tunnel['tunnelUsers']
        user_1 = f"{user.name}#{user.discriminator} ({user.id})"
        tunnel_users, user_1, index = pop_or_remove(tunnel_users, user_1)
        if not tunnel_users:
            tunnel_users.append("No user was added till now.")
        channel: discord.TextChannel = discord.utils.get(ctx.guild.text_channels, id=tunnel['tunnelChannelID'])
        if channel:
            overwrites = channel.overwrites
            overwrites[user] = discord.PermissionOverwrite(read_messages=False, send_messages=False, read_message_history=False)
            await channel.edit(overwrites=overwrites)
            await channel.set_permissions(user, overwrite=None)
        await self.bot.pg_conn.execute("""
                   UPDATE tunnel_data
                   SET "tunnelUsers" = $1
                   WHERE "tunnelID" = $2 OR "tunnelChannelID" = $3
                   """, tunnel_users, tunnel_id, ctx.channel.id)
        await ctx.send(f"User {user.mention} was successfully removed from the tunnel \"{tunnel_id if tunnel_id is not None else tunnel['tunnelID']}\"")


def setup(bot):
    bot.add_cog(Tunnel(bot))
