import argparse
import re
import shlex
from typing import NoReturn, Optional, Text

import discord
from discord.ext import commands

from .utils.checks import is_administrator_or_permission, is_guild_owner
from .utils.list_manipulation import insert_or_append, pop_or_remove, replace_or_set


class ArgParse(argparse.ArgumentParser):
    def error(self, message: Text) -> NoReturn:
        raise commands.BadArgument(message)


class Configuration(commands.Cog):
    """
     Configure bot for your server.
```py
To change, add, remove or get the prefix:
    1. {prefix_1}prefix add <prefix> [index] # To add a prefix, to insert one set index.
                                    (or)
    1. {prefix_1}prefix remove <prefix> [index] # To remove a prefix, to pop one set index.
                                    (or)
    1. {prefix_1}prefix set <prefix> <index> # To set a prefix, needs index to change the prefix correctly.
                                    (or)
    1. {prefix_1}prefix # This command gives the prefix of the server.

To disable or enable the enabled, disabled plugins:
    1. {prefix_1}plugin (enable|disable) <plugin_ext>
To get the list of (enabled|disabled of the server)|all plugins of the bot:
    1. {prefix_1}plugins ((--enabled|-e)|(--disabled|-d)|(--all|-a))
```

    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        try:
            return is_guild_owner() or await self.bot.is_owner(ctx.author) or ctx.author
        except AttributeError:
            return await self.bot.is_owner(ctx.author)

    # async def cog_command_error(self, ctx, error):
    #     ctx.cog_handler = True
    #     if isinstance(error, commands.MissingRequiredArgument):
    #         await ctx.send("You've sent a bad argument.")

    @commands.group(name="prefix", help="Gives you prefixes when sent without subcommands!", invoke_without_command=True)
    async def prefix(self, ctx: commands.Context):
        prefix_list = await self.bot.pg_conn.fetchval("""
        SELECT prefixes FROM prefix_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        embed = discord.Embed()
        embed.title = "Available prefixes for this server!"
        msg = ''
        try:
            for index, item in enumerate(prefix_list):
                index += 1
                msg += f"{index}. {item}\n"
        except AttributeError:
            for index, item in enumerate(self.bot.prefix_default):
                index += 1
                msg += f"{index}. {item}\n"
        embed.description = msg
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    @prefix.command(name="set", help="Sets the prefix for a guild!", aliases=['='])
    @commands.check_any(is_guild_owner(), commands.is_owner(), is_administrator_or_permission(administrator=True))
    async def prefix_set(self, ctx: commands.Context, prefix, index: Optional[int] = 0):
        prefix_list = await self.bot.pg_conn.fetchval("""
        SELECT prefixes FROM prefix_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        try:
            prefix_list, prefix, index = replace_or_set(prefix_list, prefix, index)
        except IndexError as ie:
            await ctx.send(str(ie))
        await self.bot.pg_conn.execute("""
        UPDATE prefix_data
        SET prefixes = $2
        WHERE guild_id = $1
        """, ctx.guild.id, prefix_list[0])
        await ctx.send(f"Set prefix to {prefix}")

    @prefix.command(name="add", help="Adds a prefix for a guild!", aliases=['+'])
    @commands.check_any(is_guild_owner(), commands.is_owner(), is_administrator_or_permission(administrator=True))
    async def prefix_add(self, ctx: commands.Context, prefix, index: Optional[int] = None):
        prefix_list = await self.bot.pg_conn.fetchval("""
        SELECT prefixes FROM prefix_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        try:
            prefix_list, prefix, index = insert_or_append(prefix_list, prefix, index)
            print(prefix_list)
        except IndexError as ie:
            await ctx.send(str(ie))
        await self.bot.pg_conn.execute("""
                UPDATE prefix_data
                SET prefixes = $2
                WHERE guild_id = $1
                """, ctx.guild.id, prefix_list)
        await ctx.send(f"Added prefix {prefix} to {index} index.")

    @prefix.command(name="remove", help="Removes the prefix for a guild with index value!", aliases=['-'])
    @commands.check_any(is_guild_owner(), commands.is_owner(), is_administrator_or_permission(administrator=True))
    async def prefix_remove(self, ctx: commands.Context, prefix, index: Optional[int] = None):
        prefix_list = await self.bot.pg_conn.fetchval("""
        SELECT prefixes FROM prefix_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        try:
            prefix_list, prefix, index = pop_or_remove(prefix_list, prefix, index)
        except IndexError as ie:
            await ctx.send(str(ie))
        await self.bot.pg_conn.execute("""
                UPDATE prefix_data
                SET prefixes = $2
                WHERE guild_id = $1
                """, ctx.guild.id, prefix_list)
        await ctx.send(f"Removed prefix {prefix}")

    @commands.group(name="plugin", help="Shows the enabled plugins for this server!", invoke_without_command=True, aliases=['plugins'])
    async def plugin(self, ctx: commands.Context, *, args):
        parser = ArgParse()
        parser.add_argument('--enabled', '-e', action='store_true')
        parser.add_argument('--disabled', '-d', action='store_true')
        parser.add_argument('--all', '-a', action='store_true')
        args = parser.parse_args(shlex.split(args))
        if (args.enabled + args.disabled) > 1:
            return await ctx.send("It is not possible to have --enabled and --disabled flags on the same command, use --all instead.")
        enabled = await self.bot.pg_conn.fetchval("""
         SELECT enabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        disabled = await self.bot.pg_conn.fetchval("""
         SELECT disabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        # print(enabled)
        embed = discord.Embed()
        embed.title = f"{'Enabled' if args.enabled else 'Disabled' if args.disabled else 'All'} plugins of this {'server' if not args.all else 'bot'}!"
        msg = ''
        for index, item in enumerate(enabled if args.enabled else disabled if args.disabled else self.bot.init_cogs):
            index += 1
            msg += f"{index}. {item.lstrip('Bot.').lstrip('cogs.')}\n"
        embed.description = msg
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    @plugin.command(name="enable", help="Enables given plugin!", aliases=['+'])
    @commands.check_any(is_guild_owner(), commands.is_owner(), is_administrator_or_permission(administrator=True))
    async def plugin_enable(self, ctx: commands.Context, *plugin_exts: str):
        enabled = await self.bot.pg_conn.fetchval("""
         SELECT enabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        disabled = await self.bot.pg_conn.fetchval("""
         SELECT disabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        plugin_not_found = []
        plugin_enabled_successfully = []
        plugin_already_enabled = []
        if plugin_exts[0] in ['all', 'All', 'ALL']:
            plugin_exts = self.bot.init_cogs
        for plugin_ext in plugin_exts:
            plugin_ext = plugin_ext.lstrip('Bot.').lstrip('cogs.')
            if re.match("([A-Za-z][^_]+)", plugin_ext):
                plugin_to_enable = f"Bot.cogs.{plugin_ext}"
            else:
                plugin_to_enable = f"Bot.cogs.{plugin_ext.replace('_', ' ').title().replace(' ', '_')}"
            if plugin_to_enable not in self.bot.init_cogs:
                plugin_not_found.append(plugin_ext)
            elif plugin_to_enable in enabled:
                plugin_already_enabled.append(plugin_ext)
            else:
                try:
                    disabled.remove(plugin_to_enable)
                except ValueError:
                    pass
                enabled.append(plugin_to_enable)
                # await ctx.send("Plugin enabled successfully")
                try:
                    if enabled:
                        enabled.remove("None")
                except ValueError:
                    pass
                try:
                    if not disabled:
                        disabled.append("None")
                except ValueError:
                    pass
                plugin_enabled_successfully.append(plugin_ext)

        await self.bot.pg_conn.execute("""
            UPDATE cogs_data 
            SET enabled = $2,
                disabled = $3
            WHERE guild_id = $1
        """, ctx.guild.id, enabled, disabled)
        for plugin_ext in plugin_enabled_successfully:
            await ctx.send(f"Plugin {plugin_ext} enabled successfully!")
        for plugin_ext in plugin_already_enabled:
            await ctx.send(f"Plugin {plugin_ext} already enabled!")
        for plugin_ext in plugin_not_found:
            await ctx.send(f"Plugin {plugin_ext} not found!")

    @plugin.command(name="disable", help="Disables given plugin or all plugins!", aliases=['-'])
    @commands.check_any(is_guild_owner(), commands.is_owner(), is_administrator_or_permission(administrator=True))
    async def plugin_disable(self, ctx: commands.Context, *plugin_exts: str):
        enabled = await self.bot.pg_conn.fetchval("""
             SELECT enabled FROM cogs_data
             WHERE guild_id = $1
             """, ctx.guild.id)
        disabled = await self.bot.pg_conn.fetchval("""
             SELECT disabled FROM cogs_data
             WHERE guild_id = $1
             """, ctx.guild.id)
        plugin_not_found = []
        plugin_disabled_successfully = []
        plugin_already_disabled = []
        if plugin_exts[0] in ['all', 'All', 'ALL']:
            plugin_exts = self.bot.init_cogs
        for plugin_ext in plugin_exts:
            plugin_ext = plugin_ext.lstrip('Bot.').lstrip('cogs.')
            if re.match("([A-Za-z][^_]+)", plugin_ext):
                plugin_to_disable = f"Bot.cogs.{plugin_ext}"
            else:
                plugin_to_disable = f"Bot.cogs.{plugin_ext.replace('_', ' ').title().replace(' ', '_')}"
            if plugin_to_disable not in self.bot.init_cogs:
                plugin_not_found.append(plugin_ext)
            elif plugin_to_disable in disabled:
                plugin_already_disabled.append(plugin_ext)
            else:
                try:
                    enabled.remove(plugin_to_disable)
                except ValueError:
                    pass
                disabled.append(plugin_to_disable)
                try:
                    if disabled:
                        disabled.remove("None")
                except ValueError:
                    pass
                try:
                    if not enabled:
                        enabled.append("None")
                except ValueError:
                    pass
                plugin_disabled_successfully.append(plugin_ext)

        await self.bot.pg_conn.execute("""
                UPDATE cogs_data 
                SET enabled = $2,
                    disabled = $3
                WHERE guild_id = $1
            """, ctx.guild.id, enabled, disabled)
        for plugin_ext in plugin_disabled_successfully:
            await ctx.send(f"Plugin {plugin_ext} disabled successfully!")
        for plugin_ext in plugin_already_disabled:
            await ctx.send(f"Plugin {plugin_ext} already disabled!")
        for plugin_ext in plugin_not_found:
            await ctx.send(f"Plugin {plugin_ext} not found!")


def setup(bot):
    bot.add_cog(Configuration(bot))
