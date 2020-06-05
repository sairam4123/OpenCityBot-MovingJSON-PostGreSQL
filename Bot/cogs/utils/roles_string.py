from typing import List

import discord


def role_string(list_of_roles: List[discord.Role]) -> str:
    value_char = 0
    role_mention_str = ""
    for role_index, role in enumerate(list_of_roles):
        if not value_char >= 1000:
            value_char += len(role.mention)
            role_mention_str += f"{role.mention}"
        else:
            role_mention_str += f" (+{len(list_of_roles[role_index:])} Roles)"
            break
    return role_mention_str
