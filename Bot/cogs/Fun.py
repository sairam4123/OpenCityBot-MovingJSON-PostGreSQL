import asyncio
import random
from itertools import cycle

import discord
from discord.ext import commands, tasks


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.cycled_jokes = []
        self.normal_jokes = []
        self.jokes_update.start()

    def cog_unload(self):
        self.jokes_update.cancel()

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

    @commands.Cog.listener()
    async def on_ready(self):
        jokes_data = await self.bot.pg_conn.fetch("""
                        SELECT questions, answers FROM jokes_data
                        """)
        formatted_jokes = []
        for joke in jokes_data:
            print(joke)
            formatted_joke = {'question': joke['questions'], "answer": joke['answers']}
            formatted_jokes.append(formatted_joke)
        self.cycled_jokes = cycle(formatted_jokes)
        self.normal_jokes = formatted_jokes

    @commands.command()
    async def joke_add(self, ctx, *, question):
        if question:
            await ctx.send("Good. Now enter the answer")

            def check(m):
                return m.author == ctx.author

            try:
                ans = await self.bot.wait_for('message', check=check, timeout=30)
                if ans:
                    await ctx.send("Added the joke :thumbsup:")
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

    def random_between_cycle_and_random(self):
        while True:
            func = random.choice([random.choice, next])
            list1 = random.choice([self.cycled_jokes, self.normal_jokes])
            try:
                test = func(list1)
            except TypeError:
                continue
            else:
                yield test

    @commands.command()
    async def jokes(self, ctx):
        joke = next(self.random_between_cycle_and_random())
        question = joke['question']
        answer = joke['answer']
        joke_embed = discord.Embed(title="J:laughing:ke", description=question, color=0x0E2FE5)
        await ctx.send(embed=joke_embed)
        await asyncio.sleep(5)
        ans = discord.Embed(description=answer, color=0x0E2FE5)
        await ctx.send(embed=ans)

    @tasks.loop(seconds=1)
    async def jokes_update(self):
        jokes_data = await self.bot.pg_conn.fetch("""
                SELECT questions, answers FROM jokes_data
                """)
        formatted_jokes = []
        for joke in jokes_data:
            print(joke)
            formatted_joke = {joke['questions']: joke['answers']}
            formatted_jokes.append(formatted_joke)
        self.cycled_jokes = cycle(formatted_jokes)
        self.normal_jokes = formatted_jokes


def setup(bot):
    bot.add_cog(Fun(bot))
