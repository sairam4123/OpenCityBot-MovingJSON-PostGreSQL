import os
from contextlib import suppress
from typing import Union

import discord
from discord.ext import commands

from .utils.list_manipulation import insert_or_append, pop_or_remove


class System(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(help='Blacklists a member from using the bot.')
    @commands.is_owner()
    async def blacklist(self, ctx: commands.Context, member_or_user: Union[discord.User, discord.Member], *, reason: str):
        black_listed_users = await self.bot.pg_conn.fetchval("""
        SELECT black_listed_users FROM black_listed_users_data
        """)
        if not black_listed_users:
            await self.bot.pg_conn.execute("""
            INSERT INTO black_listed_users_data
            VALUES ($1, 1)
            """, [])
        black_listed_users, member_or_user_id, index = insert_or_append(black_listed_users, member_or_user.id)
        await self.bot.pg_conn.execute("""
        UPDATE black_listed_users_data
        SET black_listed_users = $1
        WHERE row_id = 1
        """, black_listed_users)
        reason = reason.strip('"')
        await ctx.send(f"I have blacklisted **{member_or_user}** because of {reason}")

    @commands.command(help='Unblacklists a member from using the bot.')
    @commands.is_owner()
    async def unblacklist(self, ctx: commands.Context, member_or_user: Union[discord.User, discord.Member], *, reason: str):
        black_listed_users = await self.bot.pg_conn.fetchval("""
            SELECT black_listed_users FROM black_listed_users_data
            """)
        if not black_listed_users:
            await self.bot.pg_conn.execute("""
                INSERT INTO black_listed_users_data
                VALUES ($1, 1)
                """, [])
        black_listed_users, member_or_user_id, index = pop_or_remove(black_listed_users, member_or_user.id)
        await self.bot.pg_conn.execute("""
            UPDATE black_listed_users_data
            SET black_listed_users = $1
            WHERE row_id = 1
            """, black_listed_users)
        reason = reason.strip('"')
        await ctx.send(f"I have unblacklisted **{member_or_user}** because of \"{reason}\".")

    @commands.command(help="Reloads all cogs.")
    @commands.is_owner()
    async def reload_all_extensions(self, ctx):
        original_dir = os.getcwd()
        os.chdir('..')
        for filename1 in os.listdir('Bot/cogs'):
            if filename1.endswith('.py') and not (filename1.startswith('__') or filename1.startswith('_')):
                self.bot.unload_extension(f'Bot.cogs.{filename1[:-3]}')
                self.bot.load_extension(f'Bot.cogs.{filename1[:-3]}')
        await ctx.send("Reloaded all extensions!")
        os.chdir(original_dir)

    @commands.command(name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command()
    async def repl(self, ctx):
        """Launches an interactive REPL session."""
        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': ctx.message,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            '_': None,
        }

        if ctx.channel.id in self.sessions:
            await ctx.send('Already running a REPL session in this channel. Exit it with `quit`.')
            return

        self.sessions.add(ctx.channel.id)
        await ctx.send('Enter code to execute or evaluate. `exit()` or `quit` to exit.')

        def check(m):
            return m.author.id == ctx.author.id and \
                   m.channel.id == ctx.channel.id and \
                   m.content.startswith('`')

        while True:
            try:
                response = await self.bot.wait_for('message', check=check, timeout=10.0 * 60.0)
            except asyncio.TimeoutError:
                await ctx.send('Exiting REPL session.')
                self.sessions.remove(ctx.channel.id)
                break

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await ctx.send('Exiting.')
                self.sessions.remove(ctx.channel.id)
                return

            executor = exec
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as e:
                    await ctx.send(self.get_syntax_error(e))
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception as e:
                value = stdout.getvalue()
                fmt = f'```py\n{value}{traceback.format_exc()}\n```'
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = f'```py\n{value}{result}\n```'
                    variables['_'] = result
                elif value:
                    fmt = f'```py\n{value}\n```'

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        await ctx.send('Content too big to be printed.')
                    else:
                        await ctx.send(fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send(f'Unexpected error: `{e}`')



def setup(bot):
    bot.add_cog(System(bot))
