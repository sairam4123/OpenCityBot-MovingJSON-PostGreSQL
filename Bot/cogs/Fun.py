import discord
from discord.ext import commands
import asyncio
import random
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
        try:
            db = await self.bot.pg_conn.fetch("SELECT * FROM jokes_data")

            if question:
                await ctx.send("Good. Now enter the answer")

                def check(m):
                    return m.author == ctx.author

                ans = await self.bot.wait_for('message', check=check, timeout=30)
                if ans:

                    await ctx.send("Added the question :thumbsup:")
                else:
                    await ctx.send("Please enter the answer")
            else:
                await ctx.send("Please enter the question")
            await self.bot.pg_conn.execute("INSERT INTO jokes_data(questions,answers) VALUES($1,$2)", question, ans.content)

        except asyncio.TimeoutError:
            await ctx.send("Oops, time up!:clock: Try again if you want to add your question")

        else:
            raise

    @joke_add.error
    async def jokeadd_error(self,ctx, e):
        if isinstance(e, commands.MissingRequiredArgument):
            await ctx.send("Please enter the question along with the command like **$joke_add Yo Mama ...**")
        else:
            raise

    @commands.command()
    async def jokes(self,ctx):
        already = []
        db = await self.bot.pg_conn.fetch("SELECT questions,answers FROM jokes_data")
        jok = random.choice(db)
        ques = jok['questions']
        answ = jok['answers']
        while ques in  already:
            jok = random.choice(db)
            ques = jok['questions']
            answ = jok['answers']
        already.append(ques)
        jk = discord.Embed(title = "J:laughing:ke",description = ques,color = 0x0E2FE5)
        await ctx.send(embed = jk)
        await asyncio.sleep(5)
        ans = discord.Embed(description = answ,color = 0x0E2FE5)
        await ctx.send(embed = ans)
def setup(bot):
    bot.add_cog(Fun(bot))
