from discord.ext import commands


def is_guild_owner():
    async def predicate(ctx):
        try:
            return ctx.author == ctx.guild.owner
        except AttributeError:
            return False
    return commands.check(predicate)
