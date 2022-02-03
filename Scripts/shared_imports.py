import os
import sys
import traceback
import re

from colorama import init, Fore as F, Back as B, Style as S


class BlankFore:
    # If the user wants to disable colors, set all of them = nothing
    BLACK = BLUE = CYAN = GREEN = LIGHTBLACK_EX = LIGHTBLUE_EX = LIGHTCYAN_EX = LIGHTGREEN_EX = LIGHTMAGENTA_EX = LIGHTRED_EX = LIGHTWHITE_EX = LIGHTYELLOW_EX = MAGENTA = RED = RESET = WHITE = YELLOW = R = ''

class BlankBack:
    # If the user wants to disable colors, set all of them = nothing
    BLACK = BLUE = CYAN = GREEN = LIGHTBLACK_EX = LIGHTBLUE_EX = LIGHTCYAN_EX = LIGHTGREEN_EX = LIGHTMAGENTA_EX = LIGHTRED_EX = LIGHTWHITE_EX = LIGHTYELLOW_EX = MAGENTA = RED = RESET = WHITE = YELLOW = R = ''


class BlankStyle:
    # If the user wants to disable colors, set them all = nothing
    BRIGHT = DIM = NORMAL = RESET_ALL = R = ''



# Global Hardcoded Constants
RESOURCES_FOLDER_NAME = "SpamPurge_Resources"

__all__ = ['os', 'sys', 're', 'traceback', 'F', 'B', 'S', 'init', 'RESOURCES_FOLDER_NAME', 'BlankFore', 'BlankBack', 'BlankStyle']
