from discord.ext import commands


def is_guild_owner():
    async def predicate(ctx) -> bool:
        try:
            return ctx.author == ctx.guild.owner
        except AttributeError:
            return False

    return commands.check(predicate)


def is_administrator_or_permission(**perms):
    async def predicate(ctx) -> bool:
        try:
            return commands.has_role('Admin') or commands.has_permissions(**perms) or ctx.author == ctx.guild.owner
        except AttributeError:
            return False

    return commands.check(predicate)


def is_mod_or_permission(**perms):
    async def predicate(ctx) -> bool:
        try:
            return commands.has_role('Mod') or commands.has_permissions(**perms) or ctx.author == ctx.guild.owner
        except AttributeError:
            return False

    return commands.check(predicate)
