import datetime
import platform
import sys
from typing import List, Mapping, Optional, Union

import discord
import psutil
from discord.ext import commands, menus

from .utils.flag_check import get_flag_and_voice_server_for_guild
from .utils.roles_string import role_string
from .utils.sizer import get_size
from .utils.status_discord import get_status_of
from .utils.timeformat_bot import convert_utc_into_ist, datetime_to_seconds, format_duration


class MyMenuClass(menus.GroupByPageSource):
    def __init__(self, entries, key):
        super(MyMenuClass, self).__init__(entries, key=key, per_page=4)

    def format_page(self, menu, entry):
        pass


class MyHelpCommand(commands.HelpCommand):
    def __init__(self, **options):
        super().__init__(**options)

    async def send_command_help(self, command: commands.Command):
        if (not command.hidden) or await self.context.bot.is_owner(self.context.author) or (
                command in await self.filter_commands(command.root_parent.commands if command.root_parent else command.cog.get_commands())):
            embed = discord.Embed()
            embed.title = f"{self.context.prefix}{command.name}"
            embed.colour = discord.Colour.dark_green()
            embed.set_author(name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar_url)
            embed.add_field(name="Usage", value=f"`{self.get_command_signature(command)}`")
            embed.add_field(name="Aliases", value=" | ".join([f"`{alias}`" for alias in command.aliases]) if command.aliases else f"`{command.name}`")
            embed.add_field(name="Module", value=f"{str(command.cog.qualified_name)}")
            embed.description = command.help
            await self.context.send(embed=embed)
        else:
            if command.parent is None:
                await self.context.send(self.command_not_found(command.qualified_name))
            else:
                await self.context.send(self.subcommand_not_found(command.parent, command.name))

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]):
        embed = discord.Embed()
        embed.colour = discord.Colour.dark_blue()
        embed.title = f"Need some help, right? Get it here! " + str(len(self.context.bot.commands))
        embed.set_author(name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar_url)
        for cogs in mapping.keys():
            if cogs is not None:
                if len(await self.filter_commands(cogs.get_commands())) != 0:
                    embed.add_field(name=cogs.qualified_name, value=", ".join([
                        f"`{self.clean_prefix}{command}`" for command in await self.filter_commands(cogs.get_commands()) if
                        not command.hidden or await self.context.bot.is_owner(self.context.author)]),
                                    inline=False)
        # for field in embed.fields:
        #     if not field.value:
        #         # embed.remove_field()
        #         print(embed.fields)
        #         embed.fields.index(field)

        await self.context.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        if cog.qualified_name != "System":
            embed = discord.Embed()
            embed.colour = discord.Colour.dark_gold()
            embed.title = cog.qualified_name
            embed.description = cog.__doc__.format(prefix_1=self.clean_prefix) if cog.__doc__ else "Information about this module not available. Owner has forgot to add " \
                                                                                                   "information to this cog or he may be adding information to the cog."
            embed.set_author(name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar_url)
            for command in cog.get_commands():
                if command is not None and command in await self.filter_commands(cog.get_commands()):
                    embed.add_field(name=f"`{self.clean_prefix}{command.name}`", value=command.help, inline=False)
            await self.context.send(embed=embed)
        else:
            await self.context.send("There is no cog named System!")

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed()
        embed.colour = discord.Colour.dark_orange()
        embed.title = group.qualified_name
        embed.description = f"Usage: `{self.get_command_signature(group)}`\nAliases: " \
                            f"{' | '.join([f'`{alias}`' for alias in group.aliases]) if group.aliases else f'`{group.name}`'}" \
                            f"\nHelp: {group.help}"
        embed.set_author(name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar_url)
        for command in group.commands:
            if command in await self.filter_commands(group.commands):
                embed.add_field(name=command.name, value=command.help)
        await self.context.send(embed=embed)

    # def get_command_signature(self, command):
    #     return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)


class MyBriefCommand(commands.HelpCommand):
    def __init__(self, **options):
        super().__init__(**options)

    async def send_command_help(self, command: commands.Command):
        if (not command.hidden) or await self.context.bot.is_owner(self.context.author) or (
                command in await self.filter_commands(command.root_parent.commands if command.root_parent else command.cog.get_commands())):
            embed = discord.Embed()
            embed.title = f"{self.context.prefix}{command.name}"
            embed.colour = discord.Colour.lighter_grey()
            embed.set_author(name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar_url)
            embed.add_field(name="Usage", value=f"`{self.get_command_signature(command)}`")
            embed.add_field(name="Aliases", value=" | ".join([f"`{alias}`" for alias in command.aliases]) if command.aliases else f"`{command.name}`")
            embed.add_field(name="Module", value=f"{str(command.cog.qualified_name)}")
            embed.description = command.brief if command.brief else command.help
            await self.context.send(embed=embed)
        else:
            if command.parent is None:
                await self.context.send(self.command_not_found(command.qualified_name))
            else:
                await self.context.send(self.subcommand_not_found(command.parent, command.name))

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]):
        embed = discord.Embed()
        embed.colour = discord.Colour.dark_magenta()
        embed.title = f"Need some brief help, right? Get it here! " + str(len(self.context.bot.commands))
        embed.set_author(name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar_url)
        for cogs in mapping.keys():
            if cogs is not None:
                # print(len(await self.filter_commands((cogs.get_commands()))))
                if len(await self.filter_commands(cogs.get_commands())) != 0:
                    embed.add_field(name=cogs.qualified_name, value=", ".join([
                        f"`{self.context.prefix}{command}`" for command in await self.filter_commands(cogs.get_commands()) if
                        not command.hidden or await self.context.bot.is_owner(self.context.author)]),
                                    inline=False)
        # for field in embed.fields:
        #     if not field.value:
        #         # embed.remove_field()
        #         print(embed.fields)
        #         embed.fields.index(field)

        await self.context.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        if cog.qualified_name != "System":
            embed = discord.Embed()
            embed.colour = discord.Colour.dark_teal()
            embed.title = cog.qualified_name
            embed.set_author(name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar_url)
            for command in cog.get_commands():
                if command is not None and command in await self.filter_commands(cog.get_commands()):
                    embed.add_field(name=command.name, value=command.brief if command.brief else command.help, inline=False)
            await self.context.send(embed=embed)
        else:
            await self.context.send("There is no cog named System!")

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed()
        embed.colour = discord.Colour.teal()
        embed.title = group.qualified_name
        embed.description = f"Usage: `{self.get_command_signature(group)}`\nAliases: " \
                            f"{' | '.join([f'`{alias}`' for alias in group.aliases]) if group.aliases else f'`{group.name}`'}\nHelp: {group.help}"
        embed.set_author(name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar_url)
        for command in group.commands:
            if command in await self.filter_commands(group.commands):
                embed.add_field(name=command.name, value=command.brief)
        await self.context.send(embed=embed)

    # def get_command_signature(self, command):
    #     return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)


class Information(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand()
        bot.help_command.cog = self
        self.brief_command = MyBriefCommand()

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

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

    @commands.command(help='Pings the bot and gives latency')
    @commands.cooldown(2, 10)
    async def ping(self, ctx: discord.ext.commands.context.Context):
        time_before = datetime.datetime.utcnow()
        message = await ctx.send(f'Pong! `{round(self.bot.latency * 1000)}ms\\` latency')
        time_after = datetime.datetime.utcnow() - time_before
        await message.edit(content=f"Pong! `{round(self.bot.latency * 1000)}ms\\{round(time_after.total_seconds() * 1000)}ms` latency")

    @commands.command(help="Gives you invite for this bot!")
    async def invite(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Invite Me!",
            color=discord.Colour.gold(),
            description=f"This is my invite link. You can use this link to add me to your server!\nLink can be found [here]({self.bot.invite_url})."
        )
        await ctx.send(embed=embed)

    @commands.group(name="brief", help='gives the brief for the commands or cogs.')
    async def brief_(self, ctx: commands.Context, *, argument=None):
        self.brief_command.context = ctx
        await self.brief_command.command_callback(ctx, command=argument)

    @commands.command(help="Gives you the bot's uptime!")
    async def uptime(self, ctx: commands.Context):
        delta_uptime = datetime.datetime.utcnow() - self.bot.start_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        await ctx.send(f"Uptime: {days}d, {hours}h, {minutes}m, {seconds}s")

    @commands.group(help="Gives you info of the thing you want.", aliases=['i'])
    async def info(self, ctx):
        pass

    @info.command(help="Gives the info of a user.", name="user", aliases=['u'])
    async def info_user(self, ctx: commands.Context, member: Optional[Union[discord.Member, discord.User]]):
        member = ctx.author if member is None else member

        device = "<:android:718485581142687774> Phone" if member.is_on_mobile() else "<:windows:718485580819726366> Desktop"
        status = get_status_of(member)

        embed = discord.Embed()
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.title = f"Info of {member.display_name}"
        embed.add_field(name="Name", value=member.display_name)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Created at", value=f"{convert_utc_into_ist(member.created_at)[1]} \n {format_duration(datetime_to_seconds(member.created_at))} ago", inline=False)
        embed.add_field(name="Joined at", value=f"{convert_utc_into_ist(member.joined_at)[1]} \n {format_duration(datetime_to_seconds(member.joined_at))} ago")
        embed.add_field(name="Roles", value=role_string(list(reversed(member.roles[1:]))) if role_string(list(reversed(member.roles[1:]))) else "This man has no roles",
                        inline=False)
        embed.add_field(name="Avatar URL", value=f"[Avatar URL]({member.avatar_url})")
        embed.add_field(name="Device", value=f"{device}")
        embed.add_field(name="Status", value=f"{status}")
        embed.set_thumbnail(url=member.avatar_url)

        await ctx.send(embed=embed)

    @info.command(help="Gives the info of bot.", name="bot", aliases=['b'])
    async def info_bot(self, ctx):
        appinfo = await self.bot.application_info()

        bot_owners = ""
        if appinfo.team is None:
            bot_owner = await self.bot.fetch_user(self.bot.owner_id)
            bot_owners = f"`{bot_owner}`"
        else:
            for bot_owner_id in self.bot.owner_ids:
                bot_owner = await self.bot.fetch_user(bot_owner_id)
                bot_owners += f" `{bot_owner}`"

        embed = discord.Embed()
        embed.set_author(name=ctx.me.display_name, icon_url=ctx.me.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.title = f"My Info"
        embed.add_field(name="Python version", value=sys.version.split(' ')[0])
        embed.add_field(name="Discord.py version", value=discord.__version__)
        embed.add_field(name="Servers count", value=f"{len(self.bot.guilds)}")
        embed.add_field(name="Users count", value=f"{len(self.bot.users)}")
        embed.add_field(name="Channels count", value=f"{len([channel for channel in self.bot.get_all_channels()])}")
        embed.add_field(name="Bot Owner(s)", value=bot_owners, inline=False)
        embed.add_field(name="CPU Usage", value=f"`{psutil.cpu_percent()}%`")
        embed.add_field(name="Created at", value=f"{convert_utc_into_ist(self.bot.user.created_at)[1]} \n {format_duration(datetime_to_seconds(self.bot.user.created_at))} ago")
        embed.add_field(name="Memory or RAM Usage", value=f"`{psutil.virtual_memory().percent}%`")
        embed.add_field(name="Network Sent", value=f"`{get_size(psutil.net_io_counters().bytes_sent)}`")
        embed.add_field(name="Network Received", value=f"`{get_size(psutil.net_io_counters().bytes_recv)}`")
        embed.add_field(name="Operating System", value=f"`{platform.uname().system} {platform.uname().version}`")

        await ctx.send(embed=embed)
        # embed.add_field(name="Avatar URL", value=f"[Avatar URL]({member.avatar_url})")
        # embed.set_thumbnail(url=member.avatar_url)

    @info.command(help="Gives the info of a guild.", name="guild", aliases=['g', 's', 'server'])
    async def info_guild(self, ctx: commands.Context):
        online_members = 0
        offline_members = 0
        idle_members = 0
        dnd_members = 0
        bots = 0
        humans = 0

        store_channels = 0
        news_channels = 0
        nsfw_channels = 0
        category_channels = 0

        guild: discord.Guild = ctx.guild
        for member in guild.members:
            if member.status is discord.Status.online:
                online_members += 1
            if member.status is discord.Status.offline:
                offline_members += 1
            if member.status is discord.Status.idle:
                idle_members += 1
            if member.status is discord.Status.dnd:
                dnd_members += 1
            if member.bot:
                bots += 1
            if not member.bot:
                humans += 1
        for channel in guild.channels:
            if isinstance(channel, discord.StoreChannel):
                store_channels += 1
            if isinstance(channel, discord.TextChannel):
                if channel.is_news():
                    news_channels += 1
                if channel.is_nsfw():
                    nsfw_channels += 1
            if isinstance(channel, discord.CategoryChannel):
                category_channels += 1

        role_mention_str = role_string(guild.roles[1:])
        embed = discord.Embed()
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.title = f"Info of {guild.name}"
        embed.add_field(name="Name", value=guild.name)
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Created at", value=f"{convert_utc_into_ist(guild.created_at)[1]} \n {format_duration(datetime_to_seconds(guild.created_at))} ago", inline=False)
        embed.add_field(name="Channels available",
                        value=f"<:channel:713041608379203687> {len(guild.text_channels)} \t <:voice:713041608312094731> {len(guild.voice_channels)}\n <:news:713041608559427624> "
                              f"{news_channels} \t <:store_tag1:716660817487200338> {store_channels} \n "
                              f"<:nsfw:716664108392644708> {nsfw_channels} \t <:category1:714347844307517514> "
                              f"{category_channels} \n \n Total: {len(guild.channels)}")
        embed.add_field(name="Members count with status",
                        value=f"<:online:713029272125833337> {online_members} \t <:invisible:713029271391830109> {offline_members} \n "
                              f"<:idle:713029270976331797> {idle_members} \t "
                              f"<:dnd:713029270489792533> {dnd_members} \n \n :robot: {bots} \t <:members:716546232570347560> {humans} \n \n Total: {len(guild.members)}")
        embed.add_field(name="Roles", value=role_mention_str, inline=False)
        embed.add_field(name="Guild Icon URL", value="This server has no icon url" if not bool(guild.icon_url) else f"[Guild Icon URL]({guild.icon_url})")
        embed.add_field(name="Voice Region", value=get_flag_and_voice_server_for_guild(str(guild.region)))
        embed.add_field(name="Ban Count", value=f"<:ban:714168539975778324> {len(await guild.bans())}")
        embed.set_thumbnail(url=guild.icon_url)
        await ctx.send(embed=embed)

    @info.command(help="Gives the info of a role.", name="role", aliases=['r'])
    async def info_role(self, ctx, role: discord.Role):
        online_members = 0
        offline_members = 0
        idle_members = 0
        dnd_members = 0
        bots = 0
        humans = 0

        for member in role.members:
            if member.status is discord.Status.online:
                online_members += 1
            if member.status is discord.Status.offline:
                offline_members += 1
            if member.status is discord.Status.idle:
                idle_members += 1
            if member.status is discord.Status.dnd:
                dnd_members += 1
            if member.bot:
                bots += 1
            if not member.bot:
                humans += 1

        embed = discord.Embed()
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.title = f"Info of {role.name}"
        embed.add_field(name="Name", value=role.name)
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Created at", value=f"{convert_utc_into_ist(role.created_at)[1]} \n {format_duration(datetime_to_seconds(role.created_at))} ago", inline=False)
        embed.add_field(name="Hoisted",
                        value=role.hoist)
        embed.add_field(name="Mentionable",
                        value=role.mentionable)
        embed.add_field(name="Members count with status",
                        value=f"<:online:713029272125833337> {online_members} \t "
                              f"<:invisible:713029271391830109> {offline_members} \n <:idle:713029270976331797> {idle_members} \t "
                              f"<:dnd:713029270489792533> {dnd_members} \n \n :robot: {bots} \t <:members:716546232570347560> {humans} \n \n Total: {len(role.members)}")
        embed.add_field(name="Colour", value=f"{role.colour}", inline=False)
        embed.add_field(name="Mention", value=role.mention)
        embed.add_field(name="Position (from top) (with uncategorized category)", value=f"{list(reversed(ctx.guild.roles)).index(role) + 1}")
        embed.add_field(name="Position (from bottom)", value=f"{ctx.guild.roles.index(role) + 1}")
        await ctx.send(embed=embed)

    @info.command(help="Gives the info of a channel.", name="channel", aliases=['c'])
    async def info_channel(self, ctx, channel: Optional[Union[discord.TextChannel, discord.VoiceChannel, discord.StoreChannel]]):
        channel = ctx.channel if channel is None else channel

        type_1 = ("None"
                  if channel is None else "<:channel:713041608379203687> Text"
        if channel.type == discord.ChannelType.text else "<:voice:713041608312094731> Voice"
        if channel.type == discord.ChannelType.voice else "<:news:713041608559427624> News"
        if channel.type == discord.ChannelType.news else "<:store_tag1:716660817487200338> Store"
        if channel.type == discord.ChannelType.store else "<:category1:714347844307517514> Category"
                  )
        embed = discord.Embed()
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.title = f"Info of {channel.name}"
        embed.add_field(name="Name", value=channel.name)
        embed.add_field(name="ID", value=channel.id)
        embed.add_field(name="Created at", value=f"{convert_utc_into_ist(channel.created_at)[1]} \n {format_duration(datetime_to_seconds(channel.created_at))} ago", inline=False)
        if channel.type == discord.ChannelType.text:
            embed.add_field(name="NSFW", value=channel.nsfw)
        embed.add_field(name="Type",
                        value=type_1)
        embed.add_field(name="Parent", value=f"{channel.category}", inline=False)
        embed.add_field(name="Mention", value=channel.mention)
        embed.add_field(name="Position (from top)", value=f"{list(reversed(ctx.guild.channels)).index(channel) + 1}")
        embed.add_field(name="Position (from bottom)", value=f"{ctx.guild.channels.index(channel) + 1}")
        embed.add_field(name="Slowmode", value=channel.slowmode_delay)
        embed.add_field(name="Channel Topic", value="Channel topic not available." if not channel.topic else channel.topic)
        await ctx.send(embed=embed)

    @info.command(name="emoji", aliases=['e'], help="Gives the info the given emoji.")
    async def info_emoji(self, ctx, emoji: discord.Emoji):
        guild: discord.Guild = await self.bot.fetch_guild(ctx.guild.id)
        emoji = await guild.fetch_emoji(emoji.id)
        embed = discord.Embed(title=f"Info of {emoji}")
        embed.add_field(name="Emoji name", value=f"{emoji.name}")
        embed.add_field(name="ID", value=f"{emoji.id}")
        embed.add_field(name="Created at", value=f"{convert_utc_into_ist(emoji.created_at)[1]} \n {format_duration(datetime_to_seconds(emoji.created_at))} ago")
        embed.add_field(name="Is animated?", value=emoji.animated)
        embed.add_field(name="Is managed?", value=emoji.managed)
        embed.add_field(name="URL", value=f"{f'[URL]({emoji.url})' if emoji.url else 'None'}")
        embed.add_field(name="Uploaded by", value=f"{emoji.user}")
        await ctx.send(embed=embed)

    @info_emoji.error
    async def info_emoji_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("I can't give info for unicode symbols.")

    @commands.command(help="Gives the credits.")
    async def credits(self, ctx: commands.Context):
        await ctx.send("I have been made by these people." + "\n".join([f"{index}. {member}#{member}" for index, member in enumerate(self.bot.credits)]))


def setup(bot):
    bot.add_cog(Information(bot))
