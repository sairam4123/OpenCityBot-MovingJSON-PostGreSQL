from discord.ext import commands


class bool1(commands.Converter):
    async def convert(self, ctx, argument):
        lowered = argument.lower()
        if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
            return True
        elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
            return False
