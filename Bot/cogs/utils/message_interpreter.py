import discord

from .numbers import make_ordinal


class MessageInterpreter:
    """
    Message Interpreter.

    Interprets the messages given, using correct attributes.
    """

    def __init__(self, message):
        self.message = message

    def interpret_message(self, member: discord.Member, **ops) -> str:
        """
        Interprets the given messages using correct values.

        :param member: discord.Member
        :return: The updated message
        :rtype: str
        """
        # print(self.message)
        try:
            user_level = ops['level']
        except KeyError:
            pass
        message = self.message
        server_to_guild_message = message.replace('server', 'guild')
        index_of_member = make_ordinal(sorted(member.guild.members, key=lambda m: m.joined_at).index(member) + 1)
        formatted_message = server_to_guild_message.replace("{member.join_count}", index_of_member)
        formatted_message_1 = formatted_message.format(guild=member.guild, member=member)

        return formatted_message_1
