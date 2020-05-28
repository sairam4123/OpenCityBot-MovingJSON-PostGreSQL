import json

import discord
from discord.ext import commands

from Bot.cogs.utils.timeformat_bot import indian_standard_time_now


class Suggestions(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.channel.type == discord.ChannelType.private:
            return True
        enabled = self.bot.pg_conn.fetchrow("""
         SELECT enabled FROM cogs_data
         WHERE guild_id = $1
         """, ctx.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled[0]:
            return True
        return False

    @commands.group(help="Suggest something!", invoke_without_command=True, usage="<type_of_suggestion> <suggestion>")
    async def suggest(self, ctx: commands.Context, type1, *, suggestion):
        counts = await self.bot.pg_conn.fetch("""
        SELECT * FROM id_data
        """)
        if "suggestion_id" not in counts:
            counts["id"] = {}
        # if str(ctx.guild.id) not in counts.keys():
        #     counts[str(ctx.guild.id)] = {}
        # if "suggestion_id" not in counts["id"].keys():
        #     counts["id"]["suggestion_id"] = self.bot.start_number
        # if "suggestion_number" not in counts[str(ctx.guild.id)].keys():
        #     counts[str(ctx.guild.id)]["suggestion_number"] = 1
        # title = f"Suggestion #{counts[str(ctx.guild.id)]['suggestion_number']}"
        # embed = discord.Embed(
        #     title=title,
        #     description=(
        #         f"**Suggestion**: {suggestion}\n"
        #         f"**Suggestion by**: {ctx.author.mention}"
        #     ),
        #     color=discord.Colour.green()
        # ).set_footer(text=f"SuggestionID: {counts['id']['suggestion_id']} | {indian_standard_time_now()[1]}")
        # embed.set_author(name=f"{ctx.author.name}", icon_url=f"{ctx.author.avatar_url}")
        # message_sent = await ctx.send(embed=embed)
        # await message_sent.add_reaction(f":_tick:705003237174018179")
        # await message_sent.add_reaction(f":_neutral:705003236687609936")
        # await message_sent.add_reaction(f":_cross:705003237174018158")
        # await message_sent.add_reaction(f":_already_there:705003236897194004")
        # suggestions = json.load(open(self.bot.suggestions_json))
        # if "suggestions" not in suggestions.keys():
        #     suggestions["suggestions"] = []
        # suggestion_1 = {
        #     "suggestionID": counts['id']["suggestion_id"],
        #     "suggestionMessageID": message_sent.id,
        #     "suggestionTitle": title,
        #     "suggestionContent": suggestion,
        #     "suggestionAuthor": f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})",
        #     "suggestionTime": indian_standard_time_now()[1],
        #     "suggestionChannelID": message_sent.channel.id,
        #     "suggestionGuildID": message_sent.guild.id,
        #     "suggestionType": f"{type1}",
        #     "suggestionStatus": "waiting"
        # }
        # counts['id']["suggestion_id"] += 1
        # counts[str(ctx.guild.id)]["suggestion_number"] += 1
        # json.dump(counts, open(self.bot.counts_json, "w+"), indent='\t')
        # suggestions["suggestions"].append(suggestion_1)
        # json.dump(suggestions, open(self.bot.suggestions_json, "w+"), indent='\t')
        # await ctx.author.send("Your suggestion is sent!, This is how your suggestion look like!", embed=embed)


def setup(bot):
    bot.add_cog(Suggestions(bot))
