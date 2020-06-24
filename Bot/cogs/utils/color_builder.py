from typing import Dict, List, Union

import discord


def hex_to_rgb(hex1: str) -> List[int]:
    """ "#FFFFFF" -> [255,255,255] """
    # Pass 16 to the integer function for change of base
    return [int(hex1[i:i + 2], 16) for i in range(1, 6, 2)]


def rgb_to_hex(rgb: List[int]) -> str:
    """ [255,255,255] -> "#FFFFFF" """
    # Components need to be integers for hex to make sense
    rgb = [int(x) for x in rgb]
    return "#" + "".join(["0{0:x}".format(v) if v < 16 else "{0:x}".format(v) for v in rgb])


def color_dict(gradient: List[List[int]]) -> Dict[str, List[Union[str, int]]]:
    """ Takes in a list of RGB sub-lists and returns dictionary of
    colors in RGB and hex form for use in a graphing function
    defined later on """
    return {"hex": [rgb_to_hex(RGB) for RGB in gradient],
            "r": [RGB[0] for RGB in gradient],
            "g": [RGB[1] for RGB in gradient],
            "b": [RGB[2] for RGB in gradient]}


# def convert_color_dict_to_rgb_tuple(start_hex, finish_hex="#FFFFFF", n=10):
# 	color_dict1 = linear_gradient(start_hex, finish_hex, n)
# 	r_s = [r for r in color_dict1["r"]]
# 	g_s = [g for g in color_dict1["g"]]
# 	b_s = [b for b in color_dict1["b"]]
# 	list_of_rgb_tuples = [(r, g, b) for r, g, b in zip(r_s, g_s, b_s)]
# 	return list_of_rgb_tuples


def linear_gradient(start_hex: str, finish_hex: str = "#FFFFFF", n: int = 11) -> color_dict:
    """ returns a gradient list of (n) colors between
    two hex colors. start_hex and finish_hex
    should be the full six-digit color string,
    including the number sign ("#FFFFFF") """
    # Starting and ending colors in RGB form
    s = hex_to_rgb(start_hex)
    f = hex_to_rgb(finish_hex)
    # Initialize a list of the output colors with the starting color
    rgb_list = [s]
    # Calculate a color at each evenly spaced value of t from 1 to n
    for t in range(1, n):
        # Interpolate RGB vector for color at the current value of t
        curr_vector = [
            int(s[j] + (float(t) / (n - 1)) * (f[j] - s[j]))
            for j in range(3)
        ]
        # Add it to our list of output colors
        rgb_list.append(curr_vector)

    return color_dict(rgb_list)


def color_dict_to_discord_color_list(color_dict1: Dict[str, List[str]]) -> List[List[discord.Colour]]:
    hexes_list = [linear_gradient(color_dict1[color][0], color_dict1[color][1])["hex"] for color in color_dict1]
    # print(hexes)
    rgb_list = [[hex_to_rgb(hex1) for hex1 in hexes] for hexes in hexes_list]
    # print(len(rgb_list))
    discord_color_list_1 = []
    for i in range(len(rgb_list)):
        rgb_list_1 = rgb_list[i]
        # print("rgb = ", rgb_list)
        rgbint_list = [(r * 256 ** 2 + g * 256 + b) for r, g, b in rgb_list_1]
        discord_color_list = [discord.Colour(rgbint) for rgbint in rgbint_list]
        discord_color_list_1.append(discord_color_list)

    return discord_color_list_1


def rgb_tuple_to_rgb_int(r: int, g: int, b: int) -> int:
    return r * 256 ** 2 + g * 256 + b


if __name__ == '__main__':
    colors = {
        "red": ["#DC143C", "#8B0000"],
        "yellow": ["#FFFF99", "#666600"],
        "green": ["#90EE90", "#006400"]
    }

    discord_color_list_2 = color_dict_to_discord_color_list(colors)
    print(len(discord_color_list_2[0]))
