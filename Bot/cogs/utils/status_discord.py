import random

import discord


def get_status_of(member: discord.Member) -> str:
    if member.status == discord.Status.idle:
        status = random.choice(["<:idle:713029270976331797> Idle", "<a:idle1:718510652616081408> Idle"])
    elif member.status == discord.Status.do_not_disturb:
        status = random.choice(["<:dnd:713029270489792533> Do Not Disturb", "<a:dnd1:718510652670607360> Do Not Disturb"])
    elif member.status == discord.Status.online:
        status = random.choice(["<:online:713029272125833337> Online", "<a:online1:718510653186244636> Online"])
    elif member.status == discord.Status.offline:
        status = random.choice(["<:invisible:713029271391830109> Offline", "<a:invisible1:718510652674801675> Offline"])
    else:
        status = random.choice(["<:invisible:713029271391830109> Invisible", "<a:invisible1:718510652674801675> Invisible"])
    return status
