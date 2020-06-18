from discord.ext import commands


class bool1(commands.Converter):
    async def convert(self, ctx, argument):
        lowered = argument.lower()
        if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on', 'enabled'):
            return True
        elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off', 'disabled'):
            return False


class TicketConverter(commands.Converter):
    async def convert(self, ctx, argument):
        argument_ = argument if not argument else "0"
        try:
            print(f"{argument_=}")
            id_ = int(argument_)
            print(f"{argument_=}")
            ticket = await ctx.bot.pg_conn.fetchrow("""
            SELECT * FROM ticket_data
            WHERE "ticketID" = $1 OR "ticketChannelID" = $2
            """, id_, ctx.channel.id)
            return ticket
        except (TypeError, ValueError):
            raise commands.BadArgument("Bad argument id given please try again with correct id")
