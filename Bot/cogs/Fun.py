import asyncio
import random
import re
from itertools import cycle
from typing import Optional

import aiohttp
import discord
import wikipedia
from aiowiki import Wiki
from asyncurban import UrbanDictionary
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
            formatted_joke = {'question': joke['questions'], "answer": joke['answers']}
            formatted_jokes.append(formatted_joke)
        self.cycled_jokes = cycle(formatted_jokes)
        self.normal_jokes = formatted_jokes

    @commands.command(help="Adds a joke to the db.")
    async def joke_add(self, ctx, *, question):
        if question:
            await ctx.send("Good. Now enter the answer")

            def check(m):
                return m.author == ctx.author

            try:
                ans = await self.bot.wait_for('message', check=check, timeout=30)
                if ans:
                    await ctx.send("Added the joke :thumbsup:")
                    await self.bot.pg_conn.execute("""
                        INSERT INTO jokes_data
                        VALUES($1,$2)
                    """, question, ans.content)
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

    @commands.command(help="Returns a random joke.")
    async def jokes(self, ctx):
        joke = next(self.random_between_cycle_and_random())
        question = joke['question']
        answer = joke['answer']
        joke_embed = discord.Embed(title="J:laughing:ke", description=question, color=0x0E2FE5)
        await ctx.send(embed=joke_embed)
        await asyncio.sleep(5)
        joke_answer = discord.Embed(description=answer, color=0x0E2FE5)
        await ctx.send(embed=joke_answer)

    @tasks.loop(seconds=5)
    async def jokes_update(self):
        await self.bot.wait_until_ready()
        jokes_data = await self.bot.pg_conn.fetch("""
                SELECT questions, answers FROM jokes_data
                """)
        formatted_jokes = []
        for joke in jokes_data:
            formatted_joke = {joke['questions']: joke['answers']}
            formatted_jokes.append(formatted_joke)
        self.cycled_jokes = cycle(formatted_jokes)
        self.normal_jokes = formatted_jokes

    @commands.command(name='99!', help='Gives a random brooklyn 99 quote!')
    async def _99(self, ctx: discord.ext.commands.context.Context):
        brooklyn_99_quotes = [
            'I\'m the human form of the 💯 emoji.',
            'Bingpot!',
            (
                'Cool. Cool cool cool cool cool cool cool, '
                'no doubt no doubt no doubt no doubt.'
            )
        ]
        response = random.choice(brooklyn_99_quotes)
        await ctx.send(response)

    @commands.command(name='8ball', help='Answers your questions! ;)')
    async def _8ball(self, ctx: discord.ext.commands.context.Context, *, question):
        replies = [
            "As I see it, yes.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don’t count on it.",
            "It is certain.",
            "It is decidedly so.",
            "Most likely.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Outlook good.",
            "Reply hazy, try again.",
            "Signs point to yes.",
            "Very doubtful.",
            "Without a doubt.",
            "Yes.",
            "Yes – definitely.",
            "You may rely on it."
        ]
        await ctx.send(
            f'Question: {question}\n'
            f'Answer: {random.choice(replies)}'
        )

    @commands.command(aliases=['announce'], usage='[content]')
    async def say(self, ctx, channel: Optional[discord.TextChannel] = None, *, message: str = None):
        """Say a message"""
        channel = ctx.channel if channel is None else channel
        emojis = re.findall(r':(.*?):', str(message))
        new_msg = str(message)
        for a in emojis:
            rep = f":{a}:"
            emoji = discord.utils.get(ctx.guild.emojis, name=a)
            if emoji is not None:
                if emoji.animated:
                    new_msg = (new_msg.replace(rep, f"<a:\_:{emoji.id}>"))
                else:
                    new_msg = (new_msg.replace(rep, f"<:\_:{emoji.id}>"))
            else:
                continue
        await channel.send(new_msg)
        await ctx.message.delete()

    # @say.error
    # async def error_say(self, ctx, error):
    # 	if isinstance(error, discord.HTTPException):
    # 		await ctx.send(f"Message is not filled. Please send the message to be sent. {ctx.author.mention}")

    @commands.command(name='spaceit!', help="Add a space between each letter!")
    async def space_it(self, ctx: commands.Context, *, message: str):
        await ctx.send(" ".join(message))

    @commands.command(name='randomizecase', help="Randomizes each letter into capital or small", aliases=['randomcase', 'caserandom'])
    async def randomize_case(self, ctx: commands.Context, *, message: str):
        await ctx.send("".join(random.choice((str1.upper(), str1.lower())) for str1 in message))

    @commands.command(name='flipthecoin!', help="Flips the coin!", aliases=['flip', 'coinflip'])
    async def flip_the_coin(self, ctx: commands.Context):
        await ctx.send(f"You got {str(random.choice(('Head', 'Tail'))).lower()}")

    @commands.command(name='voter!', help='Helps you to decide anything!', aliases=['vote', 'voteforme'])
    async def voter(self, ctx: commands.Context, *, messages: str):
        await ctx.send(
            f"Answer: {random.choice(messages.split(','))}"
        )

    @staticmethod
    def get_wikipedia_page_and_summary(search, results=2, sentences=2):
        result = wikipedia.search(search, results)
        print(result)
        page = None
        while True:
            try:
                result_ = random.choice(result)
                print(result_)
                page = wikipedia.page(result_)
                print(page)
            except (wikipedia.DisambiguationError, wikipedia.PageError):
                continue
            else:
                break
        print(page)
        return page, wikipedia.summary(page.title, sentences)

    @commands.command(name="wikipedia", help="Gives you the page in wikipedia", aliases=['wiki'])
    async def wikipedia(self, ctx, *, search: str):
        wiki = Wiki.wikipedia()
        result = await wiki.opensearch(search, limit=10)
        page = random.choice(result)
        summary = str(await page.summary())
        summary_2 = ""
        for line_index, line in enumerate(summary.split('. '), start=1):
            if line_index > 3:
                break
            else:
                summary_2 += line + "."
        image = random.choice(await page.media())
        embed = discord.Embed(title=page.title, description=summary_2)
        url = await page.urls()
        embed.add_field(name="Link", value=f"[Here it is]({url[0]})")
        embed.set_thumbnail(url=image)
        await wiki.close()
        await ctx.send(embed=embed)

    @commands.command(name="urban", help="Give you the page from urban dictionary", hidden=True)
    async def urban(self, ctx, *, search):
        urban = UrbanDictionary()
        terms = await urban.search(search, limit=2)
        word = random.choice(terms)
        embed = discord.Embed(title=f"Definition of {word.word}", description=word.definition)
        embed.add_field(name="Example", value=word.example, inline=False)
        embed.add_field(name="Link", value=word.permalink)
        await urban.close()
        await ctx.send(embed=embed)

    @commands.command(help="Says what you sent using tts!")
    async def echo(self, ctx, channel: Optional[discord.TextChannel] = None, *, message=None):
        if message is not None:
            if channel is None:
                await ctx.send(message, tts=True)
            else:
                await channel.send(message, tts=True)
                await ctx.send("Message sent")
        else:
            await ctx.send(f"Message is not filled. Please send the message to be sent. {ctx.author.mention}")

    @commands.group(name="convert_to", help="Converts a given string into a subcommand formatted string")
    async def _convert_to(self, ctx: commands.Context):
        pass

    @_convert_to.command(help="Gives you up-side down text!")
    async def up_down(self, ctx, *, string: str):
        input_table = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*()_+{}|:\"<>?[]\\;',./"
        output_table = "".join(reversed(list("/˙',؛\[]¿<>„:|{}+‾()*&^%$#@¡~0987654321ZʎXMΛ∩⊥SᴚὉԀONW˥ʞſIHƃℲƎᗡϽq∀zʎxʍʌnʇsɹbdouɯןʞɾıɥƃɟǝpɔqɐ")))
        translation = string.maketrans(input_table, output_table)

        output_string = string.translate(translation)
        output_reverse = "".join(reversed(list(output_string)))
        await ctx.send(output_reverse)

    @_convert_to.command(help="Gives you the reversed string!")
    async def reverse(self, ctx, *, string: str):
        output_reverse = "".join(reversed(list(string)))
        await ctx.send(output_reverse)

    @_convert_to.command(help="Gives you a formatted Small-Caps")
    async def small_caps(self, ctx, *, string):
        input_table = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*()_+{}|:\"<>?[]\;',./"
        output_table = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*()_+{}|:\"<>?[]\;',./"

        translation = string.maketrans(input_table, output_table)

        output_string = string.translate(translation)
        await ctx.send(output_string)

    @_convert_to.command(help="Gives you a vapour-waved string")
    async def vapour_wave(self, ctx, *, string):
        input_table = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*()_+{}|:\"<>?[]\;',./"
        output_table = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ１２３４５６７８９０～！＠＃＄％＾＆＊（）＿＋｛｝｜：＂＜＞？［］＼；＇，．／"

        translation = string.maketrans(input_table, output_table)

        output_string = string.translate(translation)
        await ctx.send(output_string)

    @_convert_to.command(help="Gives you a monospaced string")
    async def monospace(self, ctx, *, string):
        input_table = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*()_+{}|:\"<>?[]\;',./"
        output_table = "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿0~!@#$%^&*()_+{}|:\"<>?[]\;',./"

        translation = string.maketrans(input_table, output_table)

        output_string = string.translate(translation)
        await ctx.send(output_string)

    @_convert_to.command(help="Gives you a formatted string with cursive!")
    async def cursive_script(self, ctx, *, string):
        input_table = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*()_+{}|:\"<>?[]\;',./"
        output_table = "𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵1234567890~!@#$%^&*()_+{}|:\"<>?[]\;',./"

        translation = string.maketrans(input_table, output_table)

        output_string = string.translate(translation)
        await ctx.send(output_string)

    @_convert_to.command(help="Gives you a currency styled a format!")
    async def currency_styled_text(self, ctx, *, string):
        input_table = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*()_+{}|:\"<>?[]\;',./"
        output_table = "₳฿₵ĐɆ₣₲ⱧłJ₭Ⱡ₥₦Ø₱QⱤ₴₮ɄV₩ӾɎⱫ₳฿₵ĐɆ₣₲ⱧłJ₭Ⱡ₥₦Ø₱QⱤ₴₮ɄV₩ӾɎⱫ1234567890~!@#$%^&*()_+{}|:\"<>?[]\;',./"

        translation = string.maketrans(input_table, output_table)

        output_string = string.translate(translation)
        await ctx.send(output_string)

    @_convert_to.command(help="Gives you a formatted old_english_styled string!")
    async def old_english_style(self, ctx, *, string):
        input_table = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*()_+{}|:\"<>?[]\;',./"
        output_table = "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ1234567890~!@#$%^&*()_+{}|:\"<>?[]\;',./"

        translation = string.maketrans(input_table, output_table)

        output_string = string.translate(translation)
        await ctx.send(output_string)

    @commands.command(help="Returns a fact of a passed animal.")
    async def fact(self, ctx: commands.Context, animal: str):
        if animal.lower() in ('cat', 'dog', 'panda', 'fox', 'bird', 'koala'):
            fact_url = f"https://some-random-api.ml/facts/{animal}"
            image_url = f"https://some-random-api.ml/img/{'birb' if animal == 'bird' else animal}"
            async with aiohttp.ClientSession() as session:
                async with session.get(fact_url) as request, session.get(image_url) as image_request:
                    if request.status == 200 and image_request.status == 200:
                        data = await request.json()
                        image_data = await image_request.json()
                        image = image_data['link']
                        fact = data['fact']
                        embed = discord.Embed(title=f"{animal.capitalize()} fact", description=fact)
                        embed.set_image(url=image)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"Error code {request.status} and {image_request.status}: Error")


def setup(bot):
    bot.add_cog(Fun(bot))
