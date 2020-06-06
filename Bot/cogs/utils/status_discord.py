import discord


def get_status_of(member: discord.Member) -> str:
    if member.status == discord.Status.idle:
        status = "<:idle:713029270976331797> Idle"
    elif member.status == discord.Status.do_not_disturb:
        status = "<:dnd:713029270489792533> Do Not Disturb"
    elif member.status == discord.Status.online:
        status = "<:online:713029272125833337> Online"
    elif member.status == discord.Status.offline:
        status = "<:invisible:713029271391830109> Offline"
    else:
        status = "<:invisible:713029271391830109> Invisible"
    return status
