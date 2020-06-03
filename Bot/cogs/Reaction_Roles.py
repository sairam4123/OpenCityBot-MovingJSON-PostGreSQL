import discord
import emoji
from discord.ext import commands


class Reaction_Roles(commands.Cog):

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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        emoji_1 = payload.emoji
        channel: discord.TextChannel = guild.get_channel(payload.channel_id)
        user: discord.Member = guild.get_member(payload.user_id)
        # guild_data = json.load(open(self.bot.guilds_json))
        # enabled = guild_data[str(user.guild.id)]["enabled"]
        # if f"Bot.cogs.{self.qualified_name}" in enabled:
        reaction_roles_data = json.load(open(self.bot.reaction_roles_json, encoding="utf-8"))
        if str(guild.id) not in reaction_roles_data.keys():
            reaction_roles_data[str(guild.id)] = {}
            reaction_roles_data[str(guild.id)]['reaction_roles'] = {}
        for emoji_2 in reaction_roles_data[str(guild.id)]['reaction_roles'].keys():
            if str(emoji_1) == str(emoji_2):
                role = discord.utils.get(guild.roles, name=reaction_roles_data[str(guild.id)]['reaction_roles'][str(emoji_2)])
                if not role:
                    await channel.send("Role not available")
                    return
                await user.add_roles(role)

        json.dump(reaction_roles_data, open(self.bot.reaction_roles_json, 'w'), indent='\t')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        emoji_1 = payload.emoji
        channel: discord.TextChannel = guild.get_channel(payload.channel_id)
        user: discord.Member = guild.get_member(payload.user_id)
        guild_data = json.load(open(self.bot.guilds_json))
        enabled = guild_data[str(user.guild.id)]["enabled"]
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            reaction_roles_data = json.load(open(self.bot.reaction_roles_json, encoding="utf-8"))
            if str(guild.id) not in reaction_roles_data.keys():
                reaction_roles_data[str(guild.id)] = {}
                reaction_roles_data[str(guild.id)]['reaction_roles'] = {}
            for emoji_2 in reaction_roles_data[str(guild.id)]['reaction_roles'].keys():
                if str(emoji_1) == str(emoji_2):
                    role = discord.utils.get(guild.roles, name=reaction_roles_data[str(guild.id)]['reaction_roles'][str(emoji_1)])
                    if not role:
                        await channel.send("Role not available")
                        return
                    await user.remove_roles(role)
            json.dump(reaction_roles_data, open(self.bot.reaction_roles_json, 'w'), indent='\t')

    @commands.group(aliases=['rr'], help="Shows the reaction roles.")
    async def reaction_roles(self, ctx):
        reaction_roles_data = json.load(open(self.bot.reaction_roles_json, encoding="utf-8"))
        if str(ctx.guild.id) not in reaction_roles_data.keys():
            reaction_roles_data[str(ctx.guild.id)] = {}
            reaction_roles_data[str(ctx.guild.id)]['reaction_roles'] = {}
        embed = discord.Embed()
        embed.title = "Available reaction roles!"
        msg = ''
        for index, (key, value) in enumerate(reaction_roles_data[str(ctx.guild.id)]["reaction_roles"].items()):
            index += 1
            msg += f"{index}. {key} -> {value}\n"
        embed.description = msg
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)
        await ctx.send(embed=embed)
        json.dump(reaction_roles_data, open(self.bot.reaction_roles_json, 'w'), indent='\t')

    @reaction_roles.command(name="add", usage="<emoji> <role>", help="Creates a reaction role.", aliases=['+'])
    async def rr_add(self, ctx, emoji_2, role_1):
        reaction_roles_data = json.load(open(self.bot.reaction_roles_json, encoding="utf-8"))
        if str(ctx.guild.id) not in reaction_roles_data.keys():
            reaction_roles_data[str(ctx.guild.id)] = {}
            reaction_roles_data[str(ctx.guild.id)]['reaction_roles'] = {}
        role = discord.utils.get(ctx.guild.roles, name=role_1)
        if not role:
            await ctx.send("Role not available")
            return
        list_of_unicode_emojis = [key for key in emoji.EMOJI_UNICODE.values()]
        list_of_guild_emojis = [f"<:{emoji_1.name}:{emoji_1.id}>" for emoji_1 in ctx.guild.emojis]
        if emoji_2 in list_of_unicode_emojis:
            for emoji_3 in list_of_unicode_emojis:
                if emoji_2 == emoji_3:
                    reaction_roles_data[str(ctx.guild.id)]['reaction_roles'][str(emoji_2)] = role.name
        if emoji_2 in list_of_guild_emojis:
            for emoji_3 in list_of_guild_emojis:
                if emoji_2 == emoji_3:
                    reaction_roles_data[str(ctx.guild.id)]['reaction_roles'][str(emoji_2)] = role.name
        json.dump(reaction_roles_data, open(self.bot.reaction_roles_json, 'w'), indent='\t')

    @reaction_roles.command(name="remove", usage="<emoji> <role>", help="Deletes a reaction role.", aliases=['-'])
    async def rr_remove(self, ctx, emoji_2):
        reaction_roles_data = json.load(open(self.bot.reaction_roles_json, encoding="utf-8"))
        if str(ctx.guild.id) not in reaction_roles_data.keys():
            reaction_roles_data[str(ctx.guild.id)] = {}
            reaction_roles_data[str(ctx.guild.id)]['reaction_roles'] = {}
        list_of_unicode_emojis = [key for key in emoji.EMOJI_UNICODE.values()]
        list_of_guild_emojis = [f"<:{emoji_1.name}:{emoji_1.id}>" for emoji_1 in ctx.guild.emojis]
        if emoji_2 in list_of_unicode_emojis:
            for emoji_3 in list_of_unicode_emojis:
                if emoji_2 == emoji_3:
                    reaction_roles_data[str(ctx.guild.id)]['reaction_roles'].pop(str(emoji_2))
        if emoji_2 in list_of_guild_emojis:
            for emoji_3 in list_of_guild_emojis:
                if emoji_2 == emoji_3:
                    reaction_roles_data[str(ctx.guild.id)]['reaction_roles'].pop(str(emoji_2))
        json.dump(reaction_roles_data, open(self.bot.reaction_roles_json, 'w'), indent='\t')


def setup(bot):
    bot.add_cog(Reaction_Roles(bot))
