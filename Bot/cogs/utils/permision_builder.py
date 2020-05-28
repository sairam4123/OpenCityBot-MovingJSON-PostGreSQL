import discord

perms = [[68608, 68608, 1117184, 3214336, 3230720, 3230720, 36785152, 36785152, 36785216, 36785728, 36785728],
         [36785856, 36785856, 36785857, 103894721, 103898817, 103899073, 108093377, 116481985, 250699713, 1324441537, 1324441537],
         [1861312449, 1861312449, 1861320641, 1861451713, 1861713857, 1861713857, 1861713859, 1861713863, 1878491079, 2146926535, 2146926535]
         ]
list2 = [
    list(reversed(list3)) for list3 in perms
]


def permission_builder(perms_list):
    discord_perms_list_1 = []
    for i in range(len(perms_list)):
        perms_list_1 = perms_list[i]
        discord_perms_list = [discord.Permissions(value) for value in perms_list_1]
        discord_perms_list_1.append(discord_perms_list)

    return discord_perms_list_1


if __name__ == '__main__':
    print(len(permission_builder(list2)[0]))
