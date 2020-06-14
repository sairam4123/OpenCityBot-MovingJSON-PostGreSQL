from typing import Optional

import discord

from .numbers import make_ordinal


class MessageInterpreter:
    """
    Message Interpreter.

    Interprets the messages given, using correct attributes.
    """

    def __init__(self, message):
        self.message = message

    def interpret_message(self, member: discord.Member, /, *, guild: Optional[discord.Guild] = None, **ops) -> str:
        """
        Interprets the given messages using correct values.

        Parameters
        ----------
        member : discord.Member
        guild : discord.Guild

        Returns
        -------
        The formatted message.

        Return Type
        -----------
        str

        """
        # print(self.message)
        user_level = 0
        user_xps = 0
        try:
            user_level = ops['level']
            user_xps = ops['xps']
        except KeyError:
            pass
        message = self.message
        server_to_guild_message = message.replace('server', 'guild')
        if "{member.join_count}" in self.message:
            index_of_member = make_ordinal(sorted(member.guild.members, key=lambda m: m.joined_at).index(member) + 1)
            server_to_guild_message = server_to_guild_message.replace("{member.join_count}", index_of_member)
        if "{member.level}" in self.message:
            server_to_guild_message = server_to_guild_message.replace('{member.level}', user_level)
        if "{member.xps}" in self.message:
            server_to_guild_message = server_to_guild_message.replace('{member.xps}', user_xps)
        formatted_message_1 = server_to_guild_message.format(guild=(member.guild if isinstance(member, discord.Member) else guild), member=member)

        return formatted_message_1
