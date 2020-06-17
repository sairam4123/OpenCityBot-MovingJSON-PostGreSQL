import asyncio
from typing import List, Union

import discord


async def add_emojis_to_message(list_of_emojis: List[Union[discord.Emoji, discord.PartialEmoji, str]], message: discord.Message):
    for emoji in list_of_emojis:
        await message.add_reaction(emoji)
        await asyncio.sleep(0.25)
    return None
