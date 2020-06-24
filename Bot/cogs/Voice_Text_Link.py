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
        join_overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False, read_message_history=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)
        }
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
                after_text_channel_id = await self.bot.pg_conn.fetchval("""
                SELECT text_channel_id FROM voice_text_data
                WHERE guild_id = $1 AND voice_channel_id = $2
                """, member.guild.id, after.channel.id)
                channel: discord.TextChannel = discord.utils.get(member.guild.text_channels, id=after_text_channel_id)
                if channel:
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
                    after_text_channel_id = await self.bot.pg_conn.fetchval("""
                    SELECT text_channel_id FROM voice_text_data
                    WHERE guild_id = $1 AND voice_channel_id = $2
                    """, member.guild.id, after.channel.id)
                    before_channel: discord.TextChannel = discord.utils.get(member.guild.text_channels, id=before_text_channel_id)
                    after_channel: discord.TextChannel = discord.utils.get(member.guild.text_channels, id=after_text_channel_id)
                    if before_channel:
                        await before_channel.edit(overwrites=leave_overwrites)
                    if after_channel:
                        await after_channel.edit(overwrites=join_overwrites)

    @commands.group(aliases=["vtl", "voice_link"], invoke_without_command=True, help="Returns all Voice Text Links.")
    async def voice_text_link(self, ctx):
        voice_text_data = await self.bot.pg_conn.fetch("""
                            SELECT * FROM voice_text_data
                            WHERE guild_id = $1
                            """, ctx.guild.id)
        embed = discord.Embed()
        embed.title = "Available voice text links!"
        msg = ''
        for index, voice_text_link1 in enumerate(voice_text_data):
            index += 1
            voice_channel = discord.utils.get(ctx.guild.voice_channels, id=voice_text_link1['voice_channel_id'])
            text_channel = discord.utils.get(ctx.guild.text_channels, id=voice_text_link1['text_channel_id'])
            msg += f"{index}. {voice_channel.mention} -> {text_channel.mention}\n"
        embed.description = msg
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    @voice_text_link.command(name="add", help='Creates a new a voice text link', aliases=['+'])
    async def vtl_add(self, ctx, voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel):
        if (voice_channel or text_channel) is None:
            await ctx.send("You didn't send voice channel or text channel!")
        else:

            await self.bot.pg_conn.execute("""
                INSERT INTO voice_text_data (guild_id, voice_channel_id, text_channel_id)
                VALUES ($1, $2, $3)
                """, ctx.guild.id, voice_channel.id, text_channel.id)
            await ctx.send(f"Added the voice text link! {voice_channel.name} -> {text_channel.name}")

    @voice_text_link.command(name="remove", help="Deletes a existing voice text link", aliases=['-'])
    async def vtl_remove(self, ctx, voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel):
        if voice_channel is None or text_channel is None:
            await ctx.send("You didn't send voice channel or text channel!")
        else:
            await self.bot.pg_conn.execute("""
                DELETE FROM voice_text_data
                WHERE guild_id = $1 AND voice_channel_id = $2 AND text_channel_id = $3
                """, ctx.guild.id, voice_channel.id, text_channel.id)
            await ctx.send(f"Removed the voice text link! {voice_channel.name} -> {text_channel.name}")


def setup(bot):
    bot.add_cog(Voice_Text_Link(bot))
