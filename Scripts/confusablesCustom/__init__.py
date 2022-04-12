import json
import re
import os
from itertools import product

from .config import CONFUSABLE_MAPPING_PATH, NON_NORMAL_ASCII_CHARS
from .utils import is_ascii


# read confusable mappings from file, build 2-way map of the pairs
with open(os.path.join(os.path.dirname(__file__), CONFUSABLE_MAPPING_PATH), "r") as mappings:
    CONFUSABLE_MAP = json.loads(mappings.readline())


def is_confusable(str1, str2):
    while str1 and str2:
        length1, length2 = 0, 0
        for index in range(len(str1), 0, -1):
            if str1[:index] in confusable_characters(str2[0]):
                length1 = index
                break
        for index in range(len(str2), 0, -1):
            if str2[:index] in confusable_characters(str1[0]):
                length2 = index
                break

        if not length1 and not length2:
            return False
        elif not length2 or length1 >= length2:
            str1 = str1[length1:]
            str2 = str2[1:]
        else:
            str1 = str1[1:]
            str2 = str2[length2:]
    return str1 == str2

def confusable_characters(char):
    mapped_chars = CONFUSABLE_MAP.get(char)
    if mapped_chars:
        return mapped_chars
    if len(char) <= 1:
        return [char]
    return None

def confusable_regex(string, include_character_padding=False):
    space_regex = "[\*_~|`\-\.]*" if include_character_padding else ''
    regex = space_regex
    for char in string:
        escaped_chars = [re.escape(c) for c in confusable_characters(char)]
        regex += "(?:" + "|".join(escaped_chars) + ")" + space_regex

    return regex

def normalize(string, prioritize_alpha=False):
    normal_forms = set([""])
    for char in string:
        normalized_chars = []
        confusable_chars = confusable_characters(char)
        if not is_ascii(char) or not char.isalpha():
            for confusable in confusable_chars:
                if prioritize_alpha:
                    if ((char.isalpha() and confusable.isalpha() and is_ascii(confusable)) or (not char.isalpha() and is_ascii(confusable))) and confusable not in NON_NORMAL_ASCII_CHARS:
                        normal = confusable
                        if len(confusable) > 1:
                            normal = normalize(confusable)[0]
                        normalized_chars.append(normal)
                else:
                    if is_ascii(confusable) and confusable not in NON_NORMAL_ASCII_CHARS:
                        normal = confusable
                        if len(confusable) > 1:
                            normal = normalize(confusable)[0]
                        normalized_chars.append(normal)
        else:
            normalized_chars = [char]

        if len(normalized_chars) == 0:
            normalized_chars = [char]
        normal_forms = set([x[0]+x[1].lower() for x in list(product(normal_forms, normalized_chars))])
    return sorted(list(normal_forms))
