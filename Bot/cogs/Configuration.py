from typing import Optional

import discord
from discord.ext import commands

from Bot.cogs.utils.checks import is_guild_owner


class Configuration(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        try:
            return is_guild_owner() or await self.bot.is_owner(ctx.author) or ctx.author
        except AttributeError:
            return await self.bot.is_owner(ctx.author)

    @commands.group(name="prefix", help="Gives you prefixes when sent without subcommands!", invoke_without_command=True)
    async def prefix(self, ctx: commands.Context):
        prefix_list = await self.bot.pg_conn.fetchrow("""
        SELECT prefixes FROM prefix_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        embed = discord.Embed()
        embed.title = "Available prefixes for this server!"
        msg = ''
        try:
            for index, item in enumerate(prefix_list[0]):
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
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def prefix_set(self, ctx: commands.Context, prefix, index: Optional[int] = 0):
        prefix_list = await self.bot.pg_conn.fetchrow("""
        SELECT prefixes FROM prefix_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        prefix_list[0][index] = prefix
        await self.bot.pg_conn.execute("""
        UPDATE prefix_data
        SET prefixes = $2
        WHERE guild_id = $1
        """, ctx.guild.id, prefix_list[0])
        await ctx.send(f"Set prefix to {prefix}")

    @prefix.command(name="add", help="Adds a prefix for a guild!", aliases=['+'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def prefix_add(self, ctx: commands.Context, prefix):
        prefix_list = await self.bot.pg_conn.fetchrow("""
        SELECT prefixes FROM prefix_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        prefix_list[0].append(prefix)
        await self.bot.pg_conn.execute("""
                UPDATE prefix_data
                SET prefixes = $2
                WHERE guild_id = $1
                """, ctx.guild.id, prefix_list[0])
        await ctx.send(f"Added prefix to {prefix}")

    @prefix.command(name="remove", help="Removes the prefix for a guild with index value!", aliases=['-'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def prefix_remove(self, ctx: commands.Context, prefix):
        prefix_list = await self.bot.pg_conn.fetchrow("""
        SELECT prefixes FROM prefix_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        prefix_list[0].remove(prefix)
        await self.bot.pg_conn.execute("""
                UPDATE prefix_data
                SET prefixes = $2
                WHERE guild_id = $1
                """, ctx.guild.id, prefix_list[0])
        await ctx.send(f"Removed prefix {prefix}")

    @commands.group(name="plugin", help="Shows the enabled plugins for this server!", invoke_without_command=True, aliases=['plugins'])
    async def plugin(self, ctx: commands.Context):
        enabled = await self.bot.pg_conn.fetchrow("""
         SELECT enabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        embed = discord.Embed()
        embed.title = "Enabled modules of this server!"
        msg = ''
        for index, item in enumerate(enabled[0]):
            index += 1
            msg += f"{index}. {item.lstrip('Bot.').lstrip('cogs.')}\n"
        embed.description = msg
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    @plugin.command(name="enable", help="Enables given plugin!", aliases=['+'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def plugin_enable(self, ctx: commands.Context, plugin_ext: str):
        enabled = await self.bot.pg_conn.fetchrow("""
         SELECT enabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        disabled = await self.bot.pg_conn.fetchrow("""
         SELECT disabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        plugin_to_enable = f"Bot.cogs.{plugin_ext.replace('_', ' ').title().replace(' ', '_')}"
        if plugin_to_enable in enabled[0]:
            await ctx.send("Plugin already enabled!")
        else:
            try:
                disabled[0].remove(plugin_to_enable)
            except ValueError:
                pass
            enabled[0].append(plugin_to_enable)
            await ctx.send("Plugin enabled successfully")
            try:
                if enabled[0]:
                    enabled[0].remove("None")
            except ValueError:
                pass
            try:
                if not disabled[0]:
                    disabled[0].append("None")
            except ValueError:
                pass

        await self.bot.pg_conn.execute("""
            UPDATE cogs_data 
            SET enabled = $2,
                disabled = $3
            WHERE guild_id = $1
        """, ctx.guild.id, enabled[0], disabled[0])

    @plugin.command(name="disable", help="Disables given plugin!", aliases=['-'])
    @commands.check_any(is_guild_owner(), commands.is_owner())
    async def plugin_disable(self, ctx: commands.Context, plugin_ext: str):
        enabled = await self.bot.pg_conn.fetchrow("""
         SELECT enabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        disabled = await self.bot.pg_conn.fetchrow("""
         SELECT disabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        plugin_to_disable = f"Bot.cogs.{plugin_ext.replace('_', ' ').title().replace(' ', '_')}"
        if plugin_to_disable in disabled[0]:
            await ctx.send("Plugin already disabled!")
        else:
            try:
                enabled[0].remove(plugin_to_disable)
            except ValueError:
                pass
            disabled[0].append(plugin_to_disable)
            await ctx.send("Plugin disabled successfully")
            try:
                if disabled[0]:
                    disabled[0].remove("None")
            except ValueError:
                pass
            try:
                if not enabled[0]:
                    enabled[0].append("None")
            except ValueError:
                pass

        await self.bot.pg_conn.execute("""
            UPDATE cogs_data 
            SET enabled = $2,
                disabled = $3
            WHERE guild_id = $1
            """, ctx.guild.id, enabled[0], disabled[0])


def setup(bot):
    bot.add_cog(Configuration(bot))
