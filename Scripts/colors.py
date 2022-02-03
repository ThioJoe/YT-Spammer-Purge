from colorama import init, Fore as F, Back as B, Style as S
from YTSpammerPurge import configVersion
from .files import load_config_file

class BlankFore:
    # If the user wants to disable colors, set all of them = nothing
    BLACK = BLUE = CYAN = GREEN = LIGHTBLACK_EX = LIGHTBLUE_EX = LIGHTCYAN_EX = LIGHTGREEN_EX = LIGHTMAGENTA_EX = LIGHTRED_EX = LIGHTWHITE_EX = LIGHTYELLOW_EX = MAGENTA = RED = RESET = WHITE = YELLOW = R = ''

class BlankBack:
    # If the user wants to disable colors, set all of them = nothing
    BLACK = BLUE = CYAN = GREEN = LIGHTBLACK_EX = LIGHTBLUE_EX = LIGHTCYAN_EX = LIGHTGREEN_EX = LIGHTMAGENTA_EX = LIGHTRED_EX = LIGHTWHITE_EX = LIGHTYELLOW_EX = MAGENTA = RED = RESET = WHITE = YELLOW = R = ''


class BlankStyle:
    # If the user wants to disable colors, set them all = nothing
    BRIGHT = DIM = NORMAL = RESET_ALL = R = ''


config = load_config_file(configVersion)

# Disable colors before they are used anywhere
try:
    if config['colors_enabled'] == False:
        S = BlankStyle
        F = BlankFore
        B = BlankBack
except Exception as e:
    print('`colors_enabled` is not set properly (?) -- ignoring')


__all__ = ['F', 'B', 'S', 'init']
