import re

from colorama import init
from colorama.ansi import AnsiBack, AnsiFore, AnsiStyle


class Back(AnsiBack):
    R: str = AnsiBack.RESET


class Fore(AnsiFore):
    R: str = AnsiFore.RESET


class Style(AnsiStyle):
    R: str = AnsiStyle.RESET_ALL


S = Style()
F = Fore()
B = Back()


# Global Hardcoded Constants
RESOURCES_FOLDER_NAME = "SpamPurge_Resources"

__all__ = [
    "re",
    "F",
    "B",
    "S",
    "init",
    "RESOURCES_FOLDER_NAME",
]
