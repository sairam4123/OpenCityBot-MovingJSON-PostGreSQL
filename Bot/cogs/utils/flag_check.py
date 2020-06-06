def get_flag_and_voice_server_for_guild(voice_region: str) -> str:
    voice_region_dict = {'India': "IN", "Sydney": "AU", "Brazil": "BR", "Europe": "EU", "Japan": "JA", "US South": "US", "US Central": "US", "US East": "US", "US West": "US",
                         "Russia": "RU", "Singapore": "SG", "Dubai": "AE", "London": "GB", "Amsterdam": "NL", "Frankfurt": "DE", "EU West": "EU", "EU Central": "EU"}
    if "vip-" in voice_region:
        voice_region = voice_region.replace('vip-', '')
    if voice_region == "hongkong":
        flag = "HK"
    elif voice_region == "southafrica":
        flag = "ZA"
    elif len(voice_region.split('-')) > 1:
        voice_region1 = voice_region.replace('-', ' ').title().split(' ')[0].upper()
        voice_region = voice_region1 + " " + "".join(voice_region.replace('-', ' ').title().split(' ')[1:])
        flag = voice_region_dict.get(voice_region)
    else:
        voice_region = voice_region.capitalize()
        flag = voice_region_dict.get(voice_region)
    return f":flag_{flag.lower()}: `{voice_region}`"
