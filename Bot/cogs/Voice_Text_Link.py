import discord
from discord.ext import commands


class Voice_Text_Link(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.channel.type == discord.ChannelType.private:
            return True
        if await self.bot.is_owner(ctx.author):
            return True
        enabled = await self.bot.pg_conn.fetchval("""
        SELECT enabled FROM cogs_data
        WHERE guild_id = $1
        """, ctx.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            return True
        return False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        leave_overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False, read_message_history=False),
            member: discord.PermissionOverwrite(read_messages=False, send_messages=False, read_message_history=False)
        }
        enabled = await self.bot.pg_conn.fetchval("""
                SELECT enabled FROM cogs_data
                WHERE guild_id = $1
                """, member.guild.id)
        if f"Bot.cogs.{self.qualified_name}" in enabled:
            if after.channel and (not before.channel):
                after_text_channel_id, history_for_text = await self.bot.pg_conn.fetchval("""
                SELECT (text_channel_id, history_for_text) FROM voice_text_data
                WHERE guild_id = $1 AND voice_channel_id = $2
                """, member.guild.id, after.channel.id)
                channel: discord.TextChannel = discord.utils.get(member.guild.text_channels, id=after_text_channel_id)
                if channel:
                    print("history_for_text=", history_for_text)
                    join_overwrites = {
                        member.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False, read_message_history=False),
                        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=history_for_text)
                    }
                    await channel.edit(overwrites=join_overwrites)
            elif (not after.channel) and before.channel:
                before_text_channel_id = await self.bot.pg_conn.fetchval("""
                SELECT text_channel_id FROM voice_text_data
                WHERE guild_id = $1 AND voice_channel_id = $2
                """, member.guild.id, before.channel.id)
                channel: discord.TextChannel = discord.utils.get(member.guild.text_channels, id=before_text_channel_id)
                if channel:
                    await channel.edit(overwrites=leave_overwrites)
                    await channel.set_permissions(member, overwrite=None)
            elif after.channel and before.channel:
                if not after.channel == before.channel:
                    before_text_channel_id = await self.bot.pg_conn.fetchval("""
                    SELECT text_channel_id FROM voice_text_data
                    WHERE guild_id = $1 AND voice_channel_id = $2
                    """, member.guild.id, before.channel.id)
                    after_text_channel_id, history_for_text = await self.bot.pg_conn.fetchval("""
                    SELECT (text_channel_id, history_for_text) FROM voice_text_data
                    WHERE guild_id = $1 AND voice_channel_id = $2
                    """, member.guild.id, after.channel.id)
                    before_channel: discord.TextChannel = discord.utils.get(member.guild.text_channels, id=before_text_channel_id)
                    after_channel: discord.TextChannel = discord.utils.get(member.guild.text_channels, id=after_text_channel_id)
                    if before_channel:
                        await before_channel.edit(overwrites=leave_overwrites)
                        await before_channel.set_permissions(member, overwrite=None)
                    if after_channel:
                        join_overwrites = {
                            member.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False, read_message_history=False),
                            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=history_for_text)
                        }
                        await after_channel.edit(overwrites=join_overwrites)

    @commands.group(aliases=["voice_text_link", "voice_link"], invoke_without_command=True, help="Returns all Voice Text Links.")
    async def vtl(self, ctx):
        voice_text_data = await self.bot.pg_conn.fetch("""
                            SELECT * FROM voice_text_data
                            WHERE guild_id = $1
                            """, ctx.guild.id)
        embed = discord.Embed()
        embed.title = "Available voice text links!"
        msg = ''
        for index, voice_text_link1 in enumerate(voice_text_data, start=1):
            voice_channel = discord.utils.get(ctx.guild.voice_channels, id=voice_text_link1['voice_channel_id'])
            text_channel = discord.utils.get(ctx.guild.text_channels, id=voice_text_link1['text_channel_id'])
            history_for_text_channel = voice_text_link1['history_for_text']
            msg += f"{index}. {voice_channel.mention} -> {text_channel.mention} with history turned {'off' if not history_for_text_channel else 'on'}.\n"
        embed.description = msg
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    @vtl.command(name="add", help='Creates a new a voice text link', aliases=['+'])
    async def vtl_add(self, ctx, voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel, history_for_text_channel: bool = True):
        if not (voice_channel or text_channel):
            await ctx.send("You didn't send voice channel or text channel!")
        else:

            await self.bot.pg_conn.execute("""
                INSERT INTO voice_text_data (guild_id, voice_channel_id, text_channel_id, history_for_text)
                VALUES ($1, $2, $3, $4)
                """, ctx.guild.id, voice_channel.id, text_channel.id, history_for_text_channel)
            await ctx.send(f"Added the voice text link! {voice_channel.name} -> {text_channel.name} with history turned {'off' if not history_for_text_channel else 'on'}.")

    @vtl.command(name="remove", help="Deletes a existing voice text link", aliases=['-'])
    async def vtl_remove(self, ctx, voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel):
        if not (voice_channel or text_channel):
            await ctx.send("You didn't send voice channel or text channel!")
        else:
            history_for_text_channel = await self.bot.pg_conn.fetchrow("""
                DELETE FROM voice_text_data
                WHERE guild_id = $1 AND voice_channel_id = $2 AND text_channel_id = $3
                RETURNING history_for_text
                """, ctx.guild.id, voice_channel.id, text_channel.id)
            await ctx.send(f"Removed the voice text link! {voice_channel.name} -> {text_channel.name} with history turned history turned {'off' if not history_for_text_channel else 'on'}.")

    @vtl.command(name='history', help="Change the history of linked text channels.")
    async def vtl_history(self, ctx, on_or_off: bool, text_channels: commands.Greedy[discord.TextChannel]):
        list_of_linked_text_channel_ids = [record['text_channel_id'] for record in await self.bot.pg_conn.fetch("""
        SELECT text_channel_id FROM voice_text_data
        WHERE guild_id = $1
        """, ctx.guild.id)]
        print(f"{list_of_linked_text_channel_ids=}")
        for text_channel in text_channels:
            print(f"{on_or_off=}")
            if text_channel.id in list_of_linked_text_channel_ids:
                print(await self.bot.pg_conn.fetchrow("""
                UPDATE voice_text_data
                SET history_for_text = $3
                WHERE guild_id = $1 AND text_channel_id = $2
                RETURNING history_for_text
                """, ctx.guild.id, text_channel.id, on_or_off))
                print(text_channel)

        if on_or_off:
            await ctx.send("The history for the channel has been turned on. Users can see what they have sent.")
        if not on_or_off:
            await ctx.send("The history for the channel has been turned off. Users can't see what they have sent.")


def setup(bot):
    bot.add_cog(Voice_Text_Link(bot))
