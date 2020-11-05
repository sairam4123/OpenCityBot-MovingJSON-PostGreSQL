import asyncio
from typing import Optional

import discord
from discord.ext import commands

from .utils.list_manipulation import insert_or_append, pop_or_remove


class Applications(commands.Cog):
    """
    Application related commands.

    To apply:
        1. `{prefix_1}apply <application_name>`
    """

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
    
    async def get_destination_for_applications(self, guild: discord.Guild):
        application_channel_id = await self.bot.pg_conn.fetch("""
        SELECT channel_id FROM application_config_data
        WHERE guild_id = $1
        """, guild.id)
        if not application_channel_id:
            return None
        return discord.utils.get(guild.channels, id=application_channel_id)

    @commands.group(aliases=['app', 'a'], invoke_without_command=True, help="Lists all applications")
    async def applications(self, ctx: commands.Context):
        application_data = await self.bot.pg_conn.fetch("""
        SELECT application_name FROM application_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        embed = discord.Embed()
        embed.title = "Available applications for this server!"
        msg = ''
        for index, key in enumerate(application_data, start=1):
            msg += f"{index}. {key['application_name']}\n"
        embed.description = msg
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    @applications.command(help="Applies a applications")
    async def apply(self, ctx, application_name):
        list_of_questions = await self.bot.pg_conn.fetchval("""
        SELECT questions FROM application_data
        WHERE guild_id = $1 AND application_name = $2
        """, ctx.guild.id, application_name)
        if not list_of_questions:
            await ctx.send("The application name you sent is not available in this server!")
            return
        # application_names = [application['application_name'] for application in application_data]
        # if application_name not in application_names:
        #     await ctx.send("The application name you sent is not available in this server!")
        #     return
        # list_of_questions = application_data[str(ctx.guild.id)][application_name]

        await ctx.author.send(f'You\'ve applied for {application_name} application!')
        await ctx.author.send('This is the first question!')

        def check(message: discord.Message) -> bool:
            return message.author == ctx.author

        list_of_answers = []
        for index, question in enumerate(list_of_questions, start=1):
            await ctx.author.send(f"{index}. {str(question).capitalize()}")
            try:
                response_by_user = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send(f"You took to long to respond {ctx.author.mention}")
                break
            else:
                if response_by_user.content in ['close', 'exit', 'cancel']:
                    await ctx.author.send("Okay, exiting!")
                    break
                list_of_answers.append(response_by_user)
        await ctx.author.send('You\'ve successfully answered all of my questions!')
        await ctx.author.send('Thank you for your time!')
        embed = discord.Embed()
        embed.title = f"{ctx.author}"
        for index, (question, answer) in enumerate(zip(list_of_questions, list_of_answers), start=1):
            embed.add_field(name=f"{index}. {question}", value=f"{answer.content}", inline=False)
        await ctx.send(embed=embed)

    @applications.group(invoke_without_command=True, help="Lists all questions of a application.")
    async def questions(self, ctx, application_name):
        list_of_questions = await self.bot.pg_conn.fetchval("""
        SELECT questions FROM application_data
        WHERE guild_id = $1 AND application_name = $2
        """, ctx.guild.id, application_name)
        if not list_of_questions:
            await ctx.send("The application name you sent is not available in this server!")
            return
        embed = discord.Embed()
        embed.title = "Available questions for this application on this server!"
        msg = ''
        for index, key in enumerate(list_of_questions, start=1):
            msg += f"{index}. {key}\n"
        embed.description = msg
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)
        await ctx.send(embed=embed)
        # json.dump(application_data, open(self.bot.applications_json, "w"), indent='\t')

    @questions.command(name="add", help="Adds a question to a application", aliases=['+'])
    async def question_add(self, ctx, application_name, question, index: Optional[int] = None):
        list_of_questions = await self.bot.pg_conn.fetchval("""
        SELECT questions FROM application_data
        WHERE guild_id = $1 AND application_name = $2
        """, ctx.guild.id, application_name)
        if not list_of_questions:
            await ctx.send("The application name you sent is not available in this server!")
            return
        try:
            list_of_questions, question, index = insert_or_append(list_of_questions, question, index)
        except IndexError as ie:
            await ctx.send(ie)
        await self.bot.pg_conn("""
        UPDATE application_data
        SET questions = $3
        WHERE guild_id = $1 AND application_name = $2
        """, ctx.guild.id, application_name, list_of_questions)
        await ctx.send(f"Added your question {question} at {index}")
        # json.dump(application_data, open(self.bot.applications_json, "w"), indent='\t')

    @questions.command(name="remove", help="Removes a question from a application", aliases=['-'])
    async def question_remove(self, ctx, application_name, question, index: Optional[int] = None):
        list_of_questions = await self.bot.pg_conn.fetchval("""
        SELECT questions FROM application_data
        WHERE guild_id = $1 AND application_name = $2
        """, ctx.guild.id, application_name)
        if not list_of_questions:
            await ctx.send("The application name you sent is not available in this server!")
            return
        try:
            list_of_questions, question, index = pop_or_remove(list_of_questions, question, index)
        except IndexError as ie:
            await ctx.send(str(ie))
        await self.bot.pg_conn("""
                UPDATE application_data
                SET questions = $3
                WHERE guild_id = $1 AND application_name = $2
                """, ctx.guild.id, application_name, list_of_questions)
        await ctx.send(f"Removed your question {question} at {index}")
        # json.dump(application_data, open(self.bot.applications_json, "w"), indent='\t')

    @applications.command(name='add', help='Adds a application to a server.', aliases=['+'])
    async def application_add(self, ctx: commands.Context, application_name):
        application_data = await self.bot.pg_conn.fetch("""
        SELECT * FROM application_data
        WHERE guild_id = $1 AND application_name = $2
        """, ctx.guild.id, application_name)
        if application_data:
            await ctx.send(f"Application already available, if you want to add extra question see the below help.")
            question_command = self.bot.get_command('applications questions add')
            await ctx.send_help(question_command)

        await ctx.send("Application added")
        await ctx.send("Please say the amount of question you would like to enter?")

        def int_check(message: discord.Message) -> bool:
            return message.author == ctx.author and type(int(message.content)) == int

        def question_check(message: discord.Message) -> bool:
            return message.author == ctx.author and message.content.endswith('?')

        count = await self.bot.wait_for('message', check=int_check)
        questions = []
        for i in range(int(count.content)):
            await ctx.send("Please say the question")
            question = await self.bot.wait_for('message', check=question_check)
            questions.append(question.content)

        await self.bot.pg_conn.execute("""
        INSERT INTO application_data
        VALUES ($1, $2, $3)
        """, ctx.guild.id, application_name, questions)
        await ctx.send("Questions added successfully")
        await ctx.send("To add extra questions or remove unnecessary questions, see the below embed.")
        add_questions_command = self.bot.get_command('applications questions add')
        remove_questions_command = self.bot.get_command('applications questions remove')
        await ctx.send_help(add_questions_command)
        await ctx.send_help(remove_questions_command)

    @applications.command(name='remove', help="Removes a application from a server.", aliases=['-'])
    async def application_remove(self, ctx, application_name):
        application_data = await self.bot.pg_conn.fetch("""
               SELECT * FROM application_data
               WHERE guild_id = $1 AND application_name = $2
               """, ctx.guild.id, application_name)
        if not application_data:
            await ctx.send(f"Application not available")
        self.bot.pg_conn.execute("""
        DELETE FROM application_data
        WHERE guild_id = $1 AND application_name = $2
        """, ctx.guild.id, application_name)
        await ctx.send("Removed application successfully")
    
    @applications.group(name='config', help="Configures the application channel")
    async def application_config(self, ctx):
        pass
    
    @application_config.command(name='set_application_channel', help="Sets the application channel", aliases=['sac'])
    async def application_config_set_application_channel(self, ctx, channel: discord.TextChannel):
        application_channel_id = await self.bot.pg_conn.fetch("""
        SELECT channel_id FROM application_config_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        if not application_channel_id:
            await self.bot.pg_conn.execute("""
            INSERT INTO application_config_data
            VALUES ($1, $2)
            """, ctx.guild.id, channel.id)
            await ctx.send(f"Set application channel to {channel.mention}")
        else:
            await self.bot.pg_conn.execute("""
            UPDATE application_config_data
            SET channel_id = $2
            WHERE guild_id = $1
            """, ctx.guild.id, channel.id)
            await ctx.send(f"Updated application channel to {channel.mention}")
    
def setup(bot):
    bot.add_cog(Applications(bot))
