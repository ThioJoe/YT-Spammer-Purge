import json
from unicodedata import normalize
import string
import os
from config import CUSTOM_CONFUSABLE_PATH, CONFUSABLES_PATH, CONFUSABLE_MAPPING_PATH, MAX_SIMILARITY_DEPTH

def _asciify(char):
    return normalize('NFD',char).encode('ascii', 'ignore').decode('ascii')

def _get_accented_characters(char):
    return [u for u in (chr(i) for i in range(137928)) if u != char and _asciify(u) == char]

def _get_confusable_chars(character, unicode_confusable_map, depth):
    mapped_chars = unicode_confusable_map[character]

    group = set([character])
    if depth <= MAX_SIMILARITY_DEPTH:
        for mapped_char in mapped_chars:
            group.update(_get_confusable_chars(mapped_char, unicode_confusable_map, depth + 1))
    return group

def parse_new_mapping_file():
    unicode_confusable_map = {}

    with open(os.path.join(os.path.dirname(__file__), CONFUSABLES_PATH), "r", encoding = 'utf-8') as unicode_mappings:
        with open(os.path.join(os.path.dirname(__file__), CUSTOM_CONFUSABLE_PATH), "r", encoding = 'utf-8') as custom_mappings:
            mappings = unicode_mappings.readlines()
            mappings.extend(custom_mappings)

            numOfMappings = len(mappings)
            i = 0
            for mapping_line in mappings:
                i = i+1
                print(f"{i}/{numOfMappings} Mappings Checked", end = "\r")
                if not mapping_line.strip() or mapping_line[0] == '#' or mapping_line[1] == '#':
                    continue

                mapping = mapping_line.split(";")[:2]
                str1 = chr(int(mapping[0].strip(), 16))
                mapping[1] = mapping[1].strip().split(" ")
                mapping[1] = [chr(int(x, 16)) for x in mapping[1]]
                str2 = "".join(mapping[1])

                if unicode_confusable_map.get(str1):
                    unicode_confusable_map[str1].add(str2)
                else:
                    unicode_confusable_map[str1] = set([str2])

                if unicode_confusable_map.get(str2):
                    unicode_confusable_map[str2].add(str1)
                else:
                    unicode_confusable_map[str2] = set([str1])

                if len(str1) == 1:
                    case_change = str1.lower() if str1.isupper() else str1.upper()
                    if case_change != str1:
                        unicode_confusable_map[str1].add(case_change)
                        if unicode_confusable_map.get(case_change) is not None:
                            unicode_confusable_map[case_change].add(str1)
                        else:
                            unicode_confusable_map[case_change] = set([str1])

                if len(str2) == 1:
                    case_change = str2.lower() if str2.isupper() else str2.upper()
                    if case_change != str2:
                        unicode_confusable_map[str2].add(case_change)
                        if unicode_confusable_map.get(case_change) is not None:
                            unicode_confusable_map[case_change].add(str2)
                        else:
                            unicode_confusable_map[case_change] = set([str2])
            print("                                                                 ")

    for char in string.ascii_lowercase:
        accented = _get_accented_characters(char)
        unicode_confusable_map[char].update(accented)
        for accent in accented:
            if unicode_confusable_map.get(accent):
                unicode_confusable_map[accent].add(char)
            else:
                unicode_confusable_map[accent] = set([char])

    for char in string.ascii_uppercase:
        accented = _get_accented_characters(char)
        unicode_confusable_map[char].update(accented)
        for accent in accented:
            if unicode_confusable_map.get(accent):
                unicode_confusable_map[accent].add(char)
            else:
                unicode_confusable_map[accent] = set([char])

    CONFUSABLE_MAP = {}
    characters_to_map = list(unicode_confusable_map.keys())
    numOfCharsToMap = len(characters_to_map)
    charMapProgress = 0
    for character in characters_to_map:
        charMapProgress = charMapProgress +1
        print(f"{charMapProgress}/{numOfCharsToMap} Characters Processed", end = "\r")
        char_group = _get_confusable_chars(character, unicode_confusable_map, 0)
        CONFUSABLE_MAP[character] = list(char_group)
    print("                                                                 ")    

    mapping_file = open(os.path.join(os.path.dirname(__file__), CONFUSABLE_MAPPING_PATH), "w")
    mapping_file.write(json.dumps(CONFUSABLE_MAP))
    mapping_file.close()

parse_new_mapping_file()