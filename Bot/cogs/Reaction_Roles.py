from typing import Optional, Union

import discord
from discord.ext import commands

from .utils.converters import bool1


class Reaction_Roles(commands.Cog):
    Emoji = Union[discord.Emoji, discord.PartialEmoji, str]

    def __init__(self, bot: commands.Bot):
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        channel: discord.TextChannel = guild.get_channel(payload.channel_id)
        message: discord.Message = await channel.fetch_message(payload.message_id)
        reactions = [str(reaction.emoji) for reaction in message.reactions if reaction.me]
        if str(payload.emoji) in reactions:
            user: discord.Member = guild.get_member(payload.user_id)
            role_id = await self.bot.pg_conn.fetchval("""
            SELECT role_id FROM reaction_roles_data
            WHERE guild_id = $1 AND message_id = $2 AND reaction = $3
            """, payload.guild_id, payload.message_id, str(payload.emoji))
            role = guild.get_role(role_id)
            if role:
                await user.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        channel: discord.TextChannel = guild.get_channel(payload.channel_id)
        message: discord.Message = await channel.fetch_message(payload.message_id)
        reactions = [str(reaction.emoji) for reaction in message.reactions if reaction.me]
        if str(payload.emoji) in reactions:
            user: discord.Member = guild.get_member(payload.user_id)
            role_id = await self.bot.pg_conn.fetchval("""
                    SELECT role_id FROM reaction_roles_data
                    WHERE guild_id = $1 AND message_id = $2 AND reaction = $3
                    """, payload.guild_id, payload.message_id, str(payload.emoji))
            role = guild.get_role(role_id)
            if role:
                await user.remove_roles(role)

    @commands.group(aliases=['rr'], help="Does nothing when invoked without subcommand!", invoke_without_command=True)
    async def reaction_roles(self, ctx, message_id: int):
        embed = discord.Embed()
        embed.title = f"Available reaction roles for message id {message_id}!"
        msg = ''
        reaction_roles_2 = await self.bot.pg_conn.fetch("""
        SELECT * FROM reaction_roles_data
        WHERE guild_id = $1 AND message_id = $2
        """, ctx.guild.id, message_id)
        emojis = [reaction['reaction'] for reaction in reaction_roles_2]
        roles = [reaction['role_id'] for reaction in reaction_roles_2]
        for index, (emoji, role) in enumerate(zip(emojis, roles)):
            index += 1
            discord_role = discord.utils.get(ctx.guild.roles, id=role)
            msg += f"{index}. {emoji} -> {discord_role.mention}\n"
        embed.description = msg
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    @reaction_roles.command(name="create", help="Creates a reaction role.", aliases=['*'])
    async def rr_create(self, ctx, channel: Optional[discord.TextChannel], title: str, description: str, *, bulk: str):
        embed = discord.Embed()
        embed.title = title
        channel = ctx.channel if not channel else channel
        embed.description = description
        message = await channel.send(embed=embed)
        await ctx.send("I am adding the reaction roles.")
        await ctx.send("Please wait!")
        for emoji, role in [reaction_role.strip().split(' ') for reaction_role in bulk.split('\n')]:
            role = await commands.RoleConverter().convert(ctx, role)
            await message.add_reaction(emoji)
            await self.bot.pg_conn.execute("""
            INSERT INTO reaction_roles_data
            VALUES ($1, $2, $3, $4, $5)
            """, ctx.guild.id, message.id, str(emoji), role.id, "Normal")
        await ctx.send("I've added reaction role.")

    @reaction_roles.command(name="add", help="Adds a reaction role to a message.", aliases=['+'])
    async def rr_add(self, ctx: commands.Context, message_id: int, emoji: Emoji, role: discord.Role):
        await ctx.send("I am adding the reaction roles.")
        await ctx.send("Please wait!")
        message = None
        for channel in ctx.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                continue
        await message.add_reaction(emoji)
        await self.bot.pg_conn.execute("""
                INSERT INTO reaction_roles_data
                VALUES ($1, $2, $3, $4, $5)
                """, ctx.guild.id, message_id, str(emoji), role.id, "Normal")
        await ctx.send("I've added reaction role.")

    @rr_add.error
    async def rr_add_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"You have missed this argument. {str(error)}")

    @reaction_roles.command(name="remove", help="Removes a reaction role from message.", aliases=['-'])
    async def rr_remove(self, ctx, message_id: int, emoji: Emoji, role: discord.Role):
        await ctx.send("I am deleting the reaction role.")
        await ctx.send("Please wait!")
        message = None
        for channel in ctx.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                continue
        await message.remove_reaction(emoji, ctx.me)
        await self.bot.pg_conn.execute("""
                DELETE FROM reaction_roles_data
                WHERE guild_id = $1 AND message_id = $2 AND reaction = $3 AND role_id = $4
                """, ctx.guild.id, message_id, str(emoji), role.id)
        await ctx.send("I've removed the reaction role.")

    @reaction_roles.command(name="delete", help="Deletes all the reaction roles in a specific message and also deletes the specified message. If delete_message is True.",
                            aliases=['/'])
    async def rr_delete(self, ctx, message_id: int, delete_message: bool1 = True):
        await ctx.send("I am deleting the reaction role.")
        await ctx.send("Please wait!")
        message = None
        for channel in ctx.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                continue
        await message.clear_reactions()
        await self.bot.pg_conn.execute("""
                        DELETE FROM reaction_roles_data
                        WHERE guild_id = $1 AND message_id = $2
                        """, ctx.guild.id, message_id)
        if delete_message:
            await message.delete()
            await ctx.send("I've removed all reaction roles and deleted the message.")
        else:
            await ctx.send("I've removed all reaction roles but I haven't deleted the message.")


def setup(bot):
    bot.add_cog(Reaction_Roles(bot))
