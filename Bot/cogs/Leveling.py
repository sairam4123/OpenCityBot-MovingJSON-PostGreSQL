import random
import time
from typing import Optional

import discord
from discord.ext import commands, menus

from .utils.checks import is_guild_owner
from .utils.color_builder import color_dict_to_discord_color_list
from .utils.converters import bool1
from .utils.list_manipulation import insert_or_append, pop_or_remove, replace_or_set
from .utils.message_interpreter import MessageInterpreter
from .utils.numbers import make_ordinal
from .utils.permision_builder import permission_builder


class Leveling_Menu(menus.MenuPages):
    async def update(self, payload):
        if self._can_remove_reactions:
            if payload.event_type == 'REACTION_ADD':
                await self.bot.http.remove_reaction(
                    payload.channel_id, payload.message_id,
                    discord.Message._emoji_reaction(payload.emoji), payload.member.id
                )
            elif payload.event_type == 'REACTION_REMOVE':
                return
        await super().update(payload)


class LevelingMenuPages(menus.ListPageSource):

    async def write_page(self, menu, offset, fields=None):
        if fields is None:
            fields = []
        len_data = len(self.entries)

        embed = discord.Embed(title=f"Leaderboard for {menu.ctx.guild.name}",
                              colour=menu.ctx.author.colour)
        embed.set_thumbnail(url=menu.ctx.guild.icon_url)
        embed.set_footer(text=f"Requested by {menu.ctx.author}. {offset:,} - {min(len_data, offset + self.per_page - 1):,} of {len_data:,} members.")

        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)

        return embed

    async def format_page(self, menu, entries):
        offset = (menu.current_page * self.per_page) + 1

        fields = []
        table = ("\n".join(f"{idx + offset}. {member.mention} is in {make_ordinal(entry['level'])} level with {entry['xps']}xps"
                           for idx, entry in enumerate(entries) if (member := menu.ctx.bot.get_guild(menu.ctx.guild.id).get_member(entry['user_id']))))

        fields.append(("Ranks", table))

        return await self.write_page(menu, offset, fields)


class Leveling(commands.Cog):
    """
    Leveling commands, users can level up here. For now leveling is not configurable.

```py
To view the (level or xps):
    1. {prefix_1}(level|xps)
To view others (level or xps):
    2. {prefix_1}(level|xps) view <mentions_of_members> # It is not recommended to use this command with the mention of the bot.
For guild owners or people with admin permissions:
    To add (level or xps) for you or other persons:
        3. {prefix_1}(level|xps) [add|+] [member] [xps|level] # Adding (level or xps) yourself is deprecated. It will be removed soon.
    To remove (level or xps) for you or other persons:
        4. {prefix_1}(level|xps) [remove|-] [member] [xps|level] # Removing (level or xps) yourself is deprecated. It will be removed soon.
    To set (level or xps) for you or other persons:
        5. {prefix_1}(level|xps) set [member] [xps|level] # Setting (level or xps) yourself is deprecated. It will be removed soon.
```

    """

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.xps_level = [0, 195, 255, 365, 655, 965, 1225, 2565, 3655, 6585, 9665]

        self.leveling_prefix = ['Pl. ', 'New ', 'Very Tiny ', 'Tiny ', 'Small ', '', 'Big ', 'Huge ', 'Very Huge ', 'Old ', 'Fl. ']
        self.leveling_roles = {'admin': ['Administrators', []], 'mod': ['Moderators', []], 'citizen': ['OpenCitizens', []]}

        self.color_dict = {
            "red": ["#FF5757", "#850000"],
            "yellow": ["#FFFF70", "#757501"],
            "green": ["#73FF73", "#007800"]
        }
        self.perms_list = [[68608, 68608, 1117184, 3214336, 3230720, 3230720, 36785152, 36785152, 36785216, 36785728, 36785728],
                           [36785856, 36785856, 36785857, 103894721, 103898817, 103899073, 108093377, 116481985, 250699713, 1324441537, 1324441537],
                           [1861312449, 1861312449, 1861320641, 1861451713, 1861713857, 1861746625, 1861746627, 1861746631, 1878523847, 2146959303, 2146959303]
                           ]
        self.leveling_data = {}
        self.base_roles = [self.leveling_prefix[0] + self.leveling_roles[i][0] for i in self.leveling_roles]
        self.top_roles = [self.leveling_prefix[-1] + self.leveling_roles[i][0] for i in self.leveling_roles]

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

    async def update_data(self, member):
        user_data = await self.bot.pg_conn.fetchrow("""
        SELECT * FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)
        if not user_data:
            await self.bot.pg_conn.execute("""
            INSERT INTO leveling_data (guild_id, user_id, level, xps, last_message_time) 
            VALUES ($1, $2, 0, 0, 0)
            """, member.guild.id, member.id)

    async def get_destination_for_level_up_messages(self, message: discord.Message) -> Optional[discord.TextChannel]:
        destination_channel_id = await self.bot.pg_conn.fetchval("""
        SELECT channel_id FROM leveling_message_destination_data
        WHERE guild_id = $1 AND "enabled?" = TRUE
        """, message.guild.id)
        enabled = await self.bot.pg_conn.fetchval("""
        SELECT "enabled?" FROM leveling_message_destination_data
        WHERE guild_id = $1 AND channel_id = $2
        """, message.guild.id, destination_channel_id)
        if enabled:
            if not destination_channel_id:
                return message.channel
            destination = discord.utils.get(message.guild.text_channels, id=destination_channel_id)
            if not destination:
                return message.channel
            return destination
        else:
            return None

    async def get_level(self, member: discord.Member):
        return await self.bot.pg_conn.fetchval("""
        SELECT level FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)

    async def get_xps(self, member: discord.Member):
        return await self.bot.pg_conn.fetchval("""
        SELECT xps FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)

    async def set_level(self, member: discord.Member, level: int):
        await self.bot.pg_conn.execute("""
        UPDATE leveling_data
        SET level = $3
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id, level)

    async def set_xps(self, member: discord.Member, xps):
        await self.bot.pg_conn.execute("""
                UPDATE leveling_data
                SET xps = $3
                WHERE guild_id = $1 AND user_id = $2
                """, member.guild.id, member.id, xps)

    async def get_last_message_time(self, member: discord.Member):
        return await self.bot.pg_conn.fetchval("""
        SELECT last_message_time FROM leveling_data
        WHERE guild_id = $1 AND user_id = $2
        """, member.guild.id, member.id)

    async def update_level(self, member: discord.Member):
        old_user_level = await self.get_level(member)
        user_xps = await self.get_xps(member)
        new_user_level = 0
        if user_xps < self.xps_level[1]:
            new_user_level = 0
        elif self.xps_level[1] <= user_xps < self.xps_level[-1]:
            for i in range(1, len(self.xps_level) - 1):
                if self.xps_level[i] <= user_xps < self.xps_level[i + 1]:
                    new_user_level = i
                    break
        else:
            new_user_level = len(self.xps_level) - 1
        return old_user_level, new_user_level

    async def send_level_up_message(self, member: discord.Member, message: discord.Message, old_level, new_level):
        await self.bot.pg_conn.execute("""
                    UPDATE leveling_data
                    SET level = $3
                    WHERE guild_id = $1 AND user_id = $2
                    """, member.guild.id, member.id, new_level)
        if new_level > old_level:
            messages = await self.bot.pg_conn.fetchval("""
            SELECT level_up_messages FROM leveling_message_destination_data
            WHERE guild_id = $1
            """, member.guild.id)
            if messages is not None:
                level_up_message = MessageInterpreter(random.choice(messages)).interpret_message(member, **{'level': new_level})
            else:
                level_up_message = (f"{member.mention} "
                                    f"You've leveled up to level `{new_level}` hurray!"
                                    )
            level_up_message_destination = await self.get_destination_for_level_up_messages(message)
            if level_up_message_destination is not None:
                await level_up_message_destination.send(level_up_message)

    async def update_xps(self, member: discord.Member, message: discord.Message):
        if (int(time.time()) - int(await self.get_last_message_time(member))) > 30 and not str(message.content).startswith(tuple(await self.bot.get_prefix(message))):
            await self.bot.pg_conn.execute("""
            UPDATE leveling_data
            SET xps = $3,
            last_message_time = $4
            WHERE guild_id = $1 AND user_id = $2
            """, member.guild.id, member.id, int(int(await self.get_xps(member)) + int(random.randrange(5, 25, 5))), time.time())

    async def return_user_category(self, member: discord.Member):
        user_category = None
        for i in self.leveling_roles:
            if discord.utils.find(lambda r: r.name == self.leveling_prefix[0] + self.leveling_roles[i][0], member.guild.roles) in member.roles:
                user_category = i
                break
        if user_category is None:
            try:
                await member.add_roles(discord.utils.find(lambda r: r.name == self.leveling_prefix[0] + self.leveling_roles['citizen'][0], member.guild.roles))
            except AttributeError:
                user_category = None
            else:
                user_category = 'citizen'
        return user_category

    async def give_roles_according_to_level(self, user_category, member: discord.Member, old_level: int, new_level: int):
        if user_category is not None:
            if (new_level - old_level) >= 1:
                user_level = new_level
                if discord.utils.find(lambda r: r.name == self.leveling_prefix[user_level] + self.leveling_roles[user_category][0], member.guild.roles) not in member.roles:
                    await member.add_roles(
                        discord.utils.find(lambda r: r.name == self.leveling_prefix[user_level] + self.leveling_roles[user_category][0], member.guild.roles))
            elif (new_level - old_level) >= 0:
                pass
            else:
                for user_level_1 in range((new_level - old_level)):
                    if discord.utils.find(lambda r: r.name == self.leveling_prefix[user_level_1] + self.leveling_roles[user_category][0], member.guild.roles) not in member.roles:
                        await member.add_roles(
                            discord.utils.find(lambda r: r.name == self.leveling_prefix[user_level_1] + self.leveling_roles[user_category][0], member.guild.roles))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.type != discord.ChannelType.private:
            enabled = await self.bot.pg_conn.fetchval("""
             SELECT enabled FROM cogs_data
             WHERE guild_id = $1
             """, message.guild.id)
            if f"Bot.cogs.{self.qualified_name}" in enabled:
                if message.author == self.bot.user:
                    return
                if not isinstance(message.author, discord.User):
                    await self.update_data(message.author)
                    if discord.utils.find(lambda r: r.name == 'Respected People', message.guild.roles) not in message.author.roles and message.author.bot is False:
                        user_category_1 = await self.return_user_category(message.author)
                        await self.update_xps(message.author, message)
                        old_level, new_level = await self.update_level(message.author)
                        await self.give_roles_according_to_level(user_category_1, message.author, old_level, new_level)
                        await self.send_level_up_message(message.author, message, old_level, new_level)

    async def check_new_role(self, before, after):
        new_role = next(role for role in after.roles if role not in before.roles)
        if after.bot is True and new_role.name in [j + self.leveling_roles[i][0] for i in self.leveling_roles for j in self.leveling_prefix]:
            await after.remove_roles(new_role)
        elif new_role.name in self.base_roles:
            # set user xps to 0
            await self.set_level(after, 0)
            await self.set_xps(after, 0)
            role_category_1 = list(self.leveling_roles.keys())[self.base_roles.index(new_role.name)]
            await after.add_roles(discord.utils.find(lambda r: r.name == self.leveling_prefix[0] + self.leveling_roles[role_category_1][0], after.guild.roles))
            for i in self.base_roles:
                if discord.utils.find(lambda r: r.name == i, after.guild.roles) in after.roles and new_role.name != i:
                    await after.remove_roles(discord.utils.find(lambda r: r.name == i, after.guild.roles))

        return new_role

    async def check_respected_people_status(self, new_role, after):
        if new_role.name in self.top_roles:
            respected_people_status = True
            for i in self.leveling_roles:
                if discord.utils.find(lambda r: r.name == self.leveling_prefix[-1] + self.leveling_roles[i][0], after.guild.roles) not in after.roles:
                    respected_people_status = False
            if respected_people_status is True:
                # you can set member out of leveling system but it checks with role name "respected people"
                if discord.utils.get(after.guild.roles, name='Respected People'):
                    await after.add_roles(discord.utils.find(lambda r: r.name == 'Respected People', after.guild.roles))
                    await self.set_level(after, 0)
                    await self.set_xps(after, 0)
                for i in self.leveling_roles:
                    for j in self.leveling_prefix:
                        if discord.utils.get(after.guild.roles, name=j + self.leveling_roles[i][0]) in after.roles:
                            await after.remove_roles(discord.utils.find(lambda r: r.name == j + self.leveling_roles[i][0], after.guild.roles))

    async def check_for_removed_role(self, before, after):
        removed_role = next(role for role in before.roles if role not in after.roles)
        if removed_role.name in self.base_roles:
            role_category = list(self.leveling_roles.keys())[self.base_roles.index(removed_role.name)]
            for i in range(len(self.leveling_prefix)):
                required_role = discord.utils.get(after.guild.roles, name=self.leveling_prefix[i] + self.leveling_roles[role_category][0])
                if required_role and required_role in after.roles:
                    await after.remove_roles(required_role)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        enabled = await self.bot.pg_conn.fetchval("""
             SELECT enabled FROM cogs_data
             WHERE guild_id = $1
             """, after.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            if discord.utils.find(lambda r: r.name == 'Respected People', after.guild.roles) not in after.roles:
                if len(before.roles) < len(after.roles):
                    new_role_1 = await self.check_new_role(before, after)
                    await self.check_respected_people_status(new_role_1, after)
                elif len(before.roles) > len(after.roles):
                    await self.check_for_removed_role(before, after)

    @commands.command(help="Creates leveling roles for this server!", hidden=True)
    @commands.check_any(is_guild_owner(), commands.is_owner())
    @commands.cooldown(1, 6 * 60 * 60)
    async def create_roles(self, ctx: commands.Context):
        perms_list = list(reversed([list(reversed(perms_list_1)) for perms_list_1 in self.perms_list]))
        if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) not in ctx.guild.roles:
            await ctx.guild.create_role(name="Respected People", color=discord.Colour(0x8600ff), hoist=True, mentionable=True, permissions=discord.Permissions(2146959319))
        leveling_prefix_1 = list(reversed(self.leveling_prefix))
        list_of_discord_colors = color_dict_to_discord_color_list(self.color_dict)
        list_of_discord_perms = permission_builder(perms_list)
        for i, list_of_discord_color, list_of_discord_perms_1 in zip(self.leveling_roles, list_of_discord_colors, list_of_discord_perms):
            for (j, k), color_1, perms_1 in zip(enumerate(self.leveling_prefix), list_of_discord_color, list_of_discord_perms_1):
                if discord.utils.get(ctx.guild.roles, name=leveling_prefix_1[j] + self.leveling_roles[i][0]) not in ctx.guild.roles:
                    await ctx.guild.create_role(name=leveling_prefix_1[j] + self.leveling_roles[i][0], color=color_1, hoist=True, mentionable=True, permissions=perms_1)
        await ctx.send("Created All levelling roles")

    @commands.command(help="Deletes leveling roles for this server!", hidden=True)
    @commands.check_any(is_guild_owner(), commands.is_owner())
    @commands.cooldown(1, 6 * 60 * 60)
    async def delete_roles(self, ctx: commands.Context):
        if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) in ctx.guild.roles:
            await discord.utils.get(ctx.guild.roles, name="Respected People", color=discord.colour.Colour(0x8600ff), hoist=True, mentionable=True).delete()
        leveling_prefix_1 = list(reversed(self.leveling_prefix))
        list_of_discord_colors = color_dict_to_discord_color_list(self.color_dict)
        for i, list_of_discord_color in zip(self.leveling_roles, list_of_discord_colors):
            for (j, k), color_1 in zip(enumerate(self.leveling_prefix), list_of_discord_color):
                if discord.utils.get(ctx.guild.roles, name=leveling_prefix_1[j] + self.leveling_roles[i][0]) in ctx.guild.roles:
                    await discord.utils.get(ctx.guild.roles, name=leveling_prefix_1[j] + self.leveling_roles[i][0], color=color_1, hoist=True, mentionable=True).delete()
        await ctx.send("Deleted All levelling roles")

    @commands.command(help="Deletes all leveling roles incase of emergency!", hidden=True)
    @commands.is_owner()
    @commands.cooldown(1, 6 * 60 * 60)
    async def delete_all_roles(self, ctx: commands.Context):
        if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) in ctx.guild.roles:
            await discord.utils.get(ctx.guild.roles, name="Respected People").delete()
        leveling_prefix_1 = list(reversed(self.leveling_prefix))
        list_of_discord_colors = color_dict_to_discord_color_list(self.color_dict)
        for i, list_of_discord_color in zip(self.leveling_roles, list_of_discord_colors):
            for (j, k), color_1 in zip(enumerate(self.leveling_prefix), list_of_discord_color):
                if discord.utils.get(ctx.guild.roles, name=leveling_prefix_1[j] + self.leveling_roles[i][0]) in ctx.guild.roles:
                    await discord.utils.get(ctx.guild.roles, name=leveling_prefix_1[j] + self.leveling_roles[i][0]).delete()
        await ctx.send("Deleted All levelling roles")

    @commands.group(name="xps", help="Returns your xps!", invoke_without_command=True, aliases=['xp', 'experience'])
    async def xps(self, ctx: commands.Context):
        user_xps = await self.get_xps(ctx.author)
        if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) in ctx.author.roles:
            await ctx.send(f"{ctx.author.mention} you are a Respected People or you have finished leveling")
        else:
            await ctx.send(f"{ctx.author.mention} Good going! You current experience is: `{user_xps}`")

    @xps.command(name="view", help="View other persons xps", aliases=['get'])
    async def xps_view(self, ctx, member: Optional[discord.Member] = None):
        if member is None:
            await ctx.send(f'{ctx.author.mention} Please mention someone!')

        else:
            if len(ctx.message.mentions) > 0:
                msg = ''
                for user in ctx.message.mentions:
                    if not user.bot:
                        if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) in user.roles:

                            msg += f"{user.mention} is a respected person or have finished leveling.\n"

                        else:
                            await self.update_data(user)
                            user_xps = await self.get_xps(user)
                            msg += f"{user.mention} has {user_xps}xps.\n"
                    else:
                        msg += f"{user.mention} is a Bot.\n"
                await ctx.send(msg)

    @xps.command(name="set", help="Sets xps for a user", aliases=['='])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def xps_set(self, ctx: commands.Context, member: Optional[discord.Member] = None, xps=0):
        member = ctx.author if member is None else member
        await self.set_xps(member, xps)
        await ctx.send(f"Set xps {xps} to {member.mention}")

    @xps.command(name="add", help="Adds xps to a user!", aliases=['+'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def xps_add(self, ctx: commands.Context, member: Optional[discord.Member] = None, xps=0):
        member = ctx.author if member is None else member
        old_xps = await self.get_xps(member)
        await self.set_xps(member, int(old_xps) + int(xps))
        await ctx.send(f"Added xps {xps} to {member.mention}")

    @xps.command(name="remove", help="Removes xps from a user!", aliases=['-'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def xps_remove(self, ctx: commands.Context, member: Optional[discord.Member] = None, xps=0):
        member = ctx.author if member is None else member
        old_xps = await self.get_xps(member)
        await self.set_xps(member, int(old_xps) - int(xps))
        await ctx.send(f"Removed xps {xps} to {member.mention}")

    @commands.group(name="level", help="Returns your level", invoke_without_command=True, aliases=['lvl'])
    async def level(self, ctx: commands.Context):
        user_level = await self.get_level(ctx.author)
        if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) in ctx.author.roles:
            await ctx.send(f"{ctx.author.mention} you are a Respected People or you have finished leveling.")
        else:
            await ctx.send(f"{ctx.author.mention} You are level `{user_level}` now. Keep participating in the server to climb up in the leaderboard.")

    @level.command(name="view", help="View other persons levels", aliases=['get'])
    async def level_view(self, ctx, member: Optional[discord.Member] = None):
        if member is None:
            await ctx.send(f'{ctx.author.mention} Please mention someone!')
        else:
            if len(ctx.message.mentions) > 0:
                msg = ''
                for user in ctx.message.mentions:
                    if not user.bot:
                        if discord.utils.find(lambda r: r.name == 'Respected People', ctx.guild.roles) in user.roles:
                            msg += f"{user.mention} is a respected people or have finished leveling.\n"
                        else:
                            await self.update_data(user)
                            user_level = await self.get_level(user)
                            msg += f"{user.mention} is in {make_ordinal(user_level)} level.\n"
                    else:
                        msg += f"{user.mention} is a Bot.\n"
                await ctx.send(msg)

    @level.command(name="set", help="Sets level for a user!", aliases=['='])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def level_set(self, ctx: commands.Context, member: Optional[discord.Member] = None, level=0):
        member = ctx.author if member is None else member
        await self.set_level(member, int(level))
        await ctx.send(f"Set level {level} to {member.mention}")

    @level.command(name="add", help="Adds level to a user!", aliases=['+'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def level_add(self, ctx: commands.Context, member: Optional[discord.Member] = None, level=0):
        member = ctx.author if member is None else member
        old_level = await self.get_xps(member)
        await self.set_level(member, int(int(old_level) + int(level)))
        await ctx.send(f"Added level {level} to {member.mention}")

    @level.command(name="remove", help="Removes level from a user!", aliases=['-'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def level_remove(self, ctx: commands.Context, member: Optional[discord.Member] = None, level=0):
        member = ctx.author if member is None else member
        old_level = await self.get_level(member)
        await self.set_level(member, int(int(old_level) - int(level)))
        await ctx.send(f"Removed level {level} to {member.mention}")

    async def get_leader_board(self, guild_id):
        leader_board1 = await self.bot.pg_conn.fetch("""
        SELECT user_id, level, xps FROM leveling_data
        WHERE guild_id = $1
        ORDER BY xps DESC 
        """, guild_id)
        return leader_board1

    @commands.command(name="leaderboard", aliases=['lb'], help="Returns leaderboard.")
    async def leader_board(self, ctx):
        leaderboard = await self.get_leader_board(ctx.guild.id)
        new_entries = []
        index = 1
        for entry in leaderboard:
            if ctx.bot.get_guild(ctx.guild.id).get_member(entry['user_id']):
                new_entries.append(entry)
                index += 1
            else:
                print(f"user not found in index {index}")
        source = LevelingMenuPages(new_entries, per_page=5)
        pages = Leveling_Menu(source=source)
        await pages.start(ctx)

    @commands.command(help="Sets the level up message channel for level up messages.", aliases=["set_lvlup_channel", "slumc", "lvm"])
    async def set_level_up_message_channel(self, ctx, channel: discord.TextChannel):
        await self.bot.pg_conn.execute("""
        INSERT INTO leveling_message_destination_data
        VALUES ($1, $2)
        """, ctx.guild.id, channel.id)
        await ctx.send(f"Set the level up message channel to {channel.mention}")

    @commands.command(name="toggle_level_up_message_status", aliases=['tlum', 'slums', 'set_level_up_message_status'],
                      help="Toggles the enabling and disabling of level up messages.")
    async def toggle_level_up_message(self, ctx, status: bool1):
        if status:
            await self.bot.pg_conn.execute("""
                    UPDATE leveling_message_destination_data
                    SET "enabled?" = TRUE
                    WHERE guild_id = $1
                    """, ctx.guild.id)
            await ctx.send("I've enabled the level up message.")
        else:
            await self.bot.pg_conn.execute("""
                       UPDATE leveling_message_destination_data
                       SET "enabled?" = FALSE
                       WHERE guild_id = $1
                       """, ctx.guild.id)
            await ctx.send("I've disabled the level up message.")

    @commands.command(help="Returns the level up message status.", aliases=['lums', 'lvl_up_message_status'])
    async def level_up_message_status(self, ctx):
        enabled = await self.bot.pg_conn.fetchval("""
        SELECT "enabled?" FROM leveling_message_destination_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        if enabled:
            await ctx.send("The status of level up message is enabled.")
        if not enabled:
            await ctx.send("The status of level up message is disabled.")

    @commands.group(aliases=['lum', 'lvl_up_msg'], help="Returns all level up messages of this server.")
    async def level_up_message(self, ctx: commands.Context):
        messages = await self.bot.pg_conn.fetchval("""
        SELECT level_up_messages FROM leveling_message_destination_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        if not messages:
            await self.bot.pg_conn.execute("""
            INSERT INTO leveling_message_destination_data (guild_id)
            VALUES ($1)
            """, ctx.guild.id)
        embed = discord.Embed(title="Available level up messages.")
        msg = ""
        for index, message in enumerate(messages, start=1):
            msg += f"{index}. {message}\n"

        embed.description = msg
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @level_up_message.command(name="add", aliases=['+'], help="Adds a level up message to the last index if index not given else insert in the passed index.")
    async def level_up_message_add(self, ctx: commands.Context, message: str, index: Optional[int]):
        messages = await self.bot.pg_conn.fetchval("""
                SELECT level_up_messages FROM leveling_message_destination_data
                WHERE guild_id = $1
                """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = insert_or_append(messages, message, index)
        await self.bot.pg_conn.execute("""
        UPDATE leveling_message_destination_data
        SET level_up_messages = $2
        WHERE guild_id = $1
        """, ctx.guild.id, messages)
        await ctx.send(f"Added message {message}.")

    @level_up_message.command(name="remove", aliases=['-'], help="Removes a level up message from the last index if index not given else pop the passed index.")
    async def level_up_message_remove(self, ctx: commands.Context, message: str, index: Optional[int]):
        messages = await self.bot.pg_conn.fetchval("""
                        SELECT level_up_messages FROM leveling_message_destination_data
                        WHERE guild_id = $1
                        """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = pop_or_remove(messages, message, index)
        await self.bot.pg_conn.execute("""
                UPDATE leveling_message_destination_data
                SET level_up_messages = $2
                WHERE guild_id = $1
                """, ctx.guild.id, messages)
        await ctx.send(f"Removed message {message}")

    @level_up_message.command(name="set", aliases=['='], help="Sets the level up message to the new message specified index.")
    async def level_up_message_set(self, ctx: commands.Context, message: str, index: int):
        messages = await self.bot.pg_conn.fetchval("""
                        SELECT level_up_messages FROM leveling_message_destination_data
                        WHERE guild_id = $1
                        """, ctx.guild.id)
        if not messages:
            messages = []
        messages, message, index = replace_or_set(messages, message, index)
        await self.bot.pg_conn.execute("""
                UPDATE leveling_message_destination_data
                SET level_up_messages = $2
                WHERE guild_id = $1
                """, ctx.guild.id, messages)
        await ctx.send(f"Set message {message} to {index}")


def setup(bot):
    bot.add_cog(Leveling(bot))
