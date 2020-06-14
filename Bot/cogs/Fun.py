import asyncio
import random

import discord
from discord.ext import commands


class Fun(commands.Cog):

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

    @commands.command()
    async def joke_add(self, ctx, *, question):
        if question:
            await ctx.send("Good. Now enter the answer")

            def check(m):
                return m.author == ctx.author

            try:
                ans = await self.bot.wait_for('message', check=check, timeout=30)
                if ans:
                    await ctx.send("Added the question :thumbsup:")
                    await self.bot.pg_conn.execute("INSERT INTO jokes_data(questions,answers) VALUES($1,$2)", question, ans.content)
                else:
                    await ctx.send("Please enter the answer")
                # await self.bot.pg_conn.execute("INSERT INTO jokes_data(questions,answers) VALUES($1,$2)", question, ans.content)
            except asyncio.TimeoutError:
                await ctx.send("Oops, time up!:clock: Try again if you want to add your question")
        else:
            await ctx.send("Please enter the question")

    @joke_add.error
    async def joke_add_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter the question along with the command like **$joke_add Yo Mama ...**")
        else:
            raise

    def random_between_cycle_and_random(self, list_1):
        pass

    @commands.command()
    async def jokes(self, ctx):
        jokes_data = await self.bot.pg_conn.fetch("""
        SELECT questions, answers FROM jokes_data
        """)
        joke = random.choice(jokes_data)
        question = joke['questions']
        answer = joke['answers']
        joke_embed = discord.Embed(title="J:laughing:ke", description=question, color=0x0E2FE5)
        await ctx.send(embed=joke_embed)
        await asyncio.sleep(5)
        ans = discord.Embed(description=answer, color=0x0E2FE5)
        await ctx.send(embed=ans)


def setup(bot):
    bot.add_cog(Fun(bot))
