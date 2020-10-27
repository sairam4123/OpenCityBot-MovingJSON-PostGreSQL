from io import BytesIO

import discord

from .timeformat_bot import convert_utc_into_ist


async def message_history_into_transcript_file_object(channel: discord.TextChannel, member: discord.Member, id_: int) -> discord.File:
    transcripts = None
    try:
        transcripts = list(reversed(await channel.history().flatten()))
    except discord.NotFound:
        pass
    transcript_temp = f"Transcript for {member} ({member.id}) \n"
    file1 = BytesIO(initial_bytes=bytes(transcript_temp + "\n".join(
        f"{convert_utc_into_ist(transcript.created_at)[1]}   {transcript.author} ({transcript.author.id}): {transcript.content}" for transcript in transcripts), encoding="utf-8"))
    return discord.File(file1, filename=f"{member.name}_{member.discriminator}_{id_}.txt")
