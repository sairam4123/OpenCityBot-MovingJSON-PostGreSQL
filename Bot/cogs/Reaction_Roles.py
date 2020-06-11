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
        # guild_data = json.load(open(self.bot.guilds_json))
        # enabled = guild_data[str(user.guild.id)]["enabled"]
        # if f"Bot.cogs.{self.qualified_name}" in enabled:
        # reaction_roles_data = json.load(open(self.bot.reaction_roles_json, encoding="utf-8"))
        # if str(guild.id) not in reaction_roles_data.keys():
        #     reaction_roles_data[str(guild.id)] = {}
        #     reaction_roles_data[str(guild.id)]['reaction_roles'] = {}
        # for emoji_2 in reaction_roles_data[str(guild.id)]['reaction_roles'].keys():
        # if str(emoji_1) == str(emoji_2):
        #     role = discord.utils.get(guild.roles, name=reaction_roles_data[str(guild.id)]['reaction_roles'][str(emoji_2)])
        #     if not role:
        #         await channel.send("Role not available")
        #         return
        #     await user.add_roles(role)
        #
        # json.dump(reaction_roles_data, open(self.bot.reaction_roles_json, 'w'), indent='\t')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        # emoji_1 = payload.emoji
        # channel: discord.TextChannel = guild.get_channel(payload.channel_id)
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

    #     user: discord.Member = guild.get_member(payload.user_id)
    #     guild_data = json.load(open(self.bot.guilds_json))
    #     enabled = guild_data[str(user.guild.id)]["enabled"]
    #     if f"Bot.cogs.{self.qualified_name}" in enabled:
    #         reaction_roles_data = json.load(open(self.bot.reaction_roles_json, encoding="utf-8"))
    #         if str(guild.id) not in reaction_roles_data.keys():
    #             reaction_roles_data[str(guild.id)] = {}
    #             reaction_roles_data[str(guild.id)]['reaction_roles'] = {}
    #         for emoji_2 in reaction_roles_data[str(guild.id)]['reaction_roles'].keys():
    #             if str(emoji_1) == str(emoji_2):
    #                 role = discord.utils.get(guild.roles, name=reaction_roles_data[str(guild.id)]['reaction_roles'][str(emoji_1)])
    #                 if not role:
    #                     await channel.send("Role not available")
    #                     return
    #                 await user.remove_roles(role)
    #         json.dump(reaction_roles_data, open(self.bot.reaction_roles_json, 'w'), indent='\t')

    @commands.group(aliases=['rr'], help="Does nothing when invoked without subcommand!", invoke_without_command=True)
    async def reaction_roles(self, ctx, message_id: int):

        # reaction_roles_data = json.load(open(self.bot.reaction_roles_json, encoding="utf-8"))
        # if str(ctx.guild.id) not in reaction_roles_data.keys():
        #     reaction_roles_data[str(ctx.guild.id)] = {}
        #     reaction_roles_data[str(ctx.guild.id)]['reaction_roles'] = {}
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
        # json.dump(reaction_roles_data, open(self.bot.reaction_roles_json, 'w'), indent='\t')

    @reaction_roles.command(name="create", help="Creates a reaction role.", aliases=['*'])
    async def rr_create(self, ctx, channel: Optional[discord.TextChannel], title: str, description: str, *, bulk: str):
        # role = discord.utils.get(ctx.guild.roles, name=role_1)
        # if not role:
        #     await ctx.send("Role not available")
        #     return
        # list_of_unicode_emojis = [key for key in emoji.EMOJI_UNICODE.values()]
        # list_of_guild_emojis = [f"<:{emoji_1.name}:{emoji_1.id}>" for emoji_1 in ctx.guild.emojis]
        # print([reaction_role.strip().split(' ') for reaction_role in bulk.split('\n')])
        # # This is original code
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

    # # this is not original code
    # if emoji_2 in list_of_unicode_emojis:
    #     for emoji_3 in list_of_unicode_emojis:
    #         if emoji_2 == emoji_3:
    #             reaction_roles_data[str(ctx.guild.id)]['reaction_roles'][str(emoji_2)] = role.name
    # if emoji_2 in list_of_guild_emojis:
    #     for emoji_3 in list_of_guild_emojis:
    #         if emoji_2 == emoji_3:
    #             reaction_roles_data[str(ctx.guild.id)]['reaction_roles'][str(emoji_2)] = role.name
    # json.dump(reaction_roles_data, open(self.bot.reaction_roles_json, 'w'), indent='\t')

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
    #     reaction_roles_data = json.load(open(self.bot.reaction_roles_json, encoding="utf-8"))
    #     if str(ctx.guild.id) not in reaction_roles_data.keys():
    #         reaction_roles_data[str(ctx.guild.id)] = {}
    #         reaction_roles_data[str(ctx.guild.id)]['reaction_roles'] = {}
    #     list_of_unicode_emojis = [key for key in emoji.EMOJI_UNICODE.values()]
    #     list_of_guild_emojis = [f"<:{emoji_1.name}:{emoji_1.id}>" for emoji_1 in ctx.guild.emojis]
    #     if emoji_2 in list_of_unicode_emojis:
    #         for emoji_3 in list_of_unicode_emojis:
    #             if emoji_2 == emoji_3:
    #                 reaction_roles_data[str(ctx.guild.id)]['reaction_roles'].pop(str(emoji_2))
    #     if emoji_2 in list_of_guild_emojis:
    #         for emoji_3 in list_of_guild_emojis:
    #             if emoji_2 == emoji_3:
    #                 reaction_roles_data[str(ctx.guild.id)]['reaction_roles'].pop(str(emoji_2))
    #     json.dump(reaction_roles_data, open(self.bot.reaction_roles_json, 'w'), indent='\t')


def setup(bot):
    bot.add_cog(Reaction_Roles(bot))
