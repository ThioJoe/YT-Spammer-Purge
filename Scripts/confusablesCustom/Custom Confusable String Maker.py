#-*- coding: UTF-8 -*-

# Script Purpose: Automatically generates additional entries for 'custom_confusables.txt', for confusable character combinations that are not included by default. 
#                 Remember: After adding all the characters you want, you must then still run parse.py to generate the new 'confusable_mapping.json' file

# ------------------------------------ Only Change This Section ------------------------------------

# THESE TWO VARIABLES ARE THE ONLY THINGS YOU NEED TO CHANGE
# Ensure the spammified phrases and real phrases line up exactly, as each character will be compared to it's counterpart in the other variable
spammifiedPhrase = "ＦＲＥＥ ＲＯＢＵＸ on мy proғιle"
realPhrase = "FREE ROBUX ON MY PROFILE"


# ---------------------------------------------------------------------------------------------------
import sys
import os
import json

# Note: Only uncomment and change the following two lines if running this script from somewhere else other than confusables directory, then comment out the other code in this section that's taken from __init__.py
#sys.path.insert(1, 'C:\\Some\\Other\\Directory\\YTSpammerPurge') # Set this path to the directory containing the main YTSpammerPurge.py script, otherwise it won't know where to import the customConfusables scripts from
#from Scripts.confusablesCustom import confusable_regex, normalize, confusable_characters

# Code in this section taken from __init__.py
from config import CONFUSABLE_MAPPING_PATH
# read confusable mappings from file, build 2-way map of the pairs
with open(os.path.join(os.path.dirname(__file__), CONFUSABLE_MAPPING_PATH), "r") as mappings:
    CONFUSABLE_MAP = json.loads(mappings.readline())
def confusable_characters(char):
    mapped_chars = CONFUSABLE_MAP.get(char)
    if mapped_chars:
        return mapped_chars
    if len(char) <= 1:
        return [char]
    return None
# ---------------------------------------------------------------------------------------------------
# Following code by ThioJoe
def check_char(realLetterLower, letterInSpam):
    realLetterUpper = realLetterLower.upper()
    if realLetterLower == letterInSpam or realLetterUpper == letterInSpam:
        print(f"{letterInSpam} is Normal Letter")
    else:
        confuseChars = confusable_characters(realLetterLower)
        confuseCharsUpper = confusable_characters(realLetterUpper)

        if letterInSpam in confuseChars:
            print(f"Confusable Combo {realLetterLower}:{letterInSpam} Already Included in Confusables")
        else:
            makeStringList.append({realLetterLower:letterInSpam})

        if letterInSpam in confuseCharsUpper:
            print(f"Confusable Combo {realLetterUpper}:{letterInSpam} Already Included in Confusables")
        else:
            makeStringList.append({realLetterUpper:letterInSpam})

def make_string(realLetter, letterInSpam):
    tab = ' '
    spamHex = format(ord(letterInSpam), 'x')
    spamHexFormatted = spamHex.rjust(4, str(0)).upper()

    letterHex = format(ord(realLetter), 'x')
    letterHexFormatted = letterHex.rjust(4, str(0)).upper()

    finalString = f"{letterHexFormatted}{tab};{tab}{spamHexFormatted}{tab};{tab}#{tab}{realLetter}{tab}→{tab}{letterInSpam}"
    print(finalString)


spammifiedPhrase = spammifiedPhrase.replace(" ", "")
realPhrase = realPhrase.replace(" ", "").lower()

makeStringList = []
alreadyCheckedCharList = []

for i in range(len(spammifiedPhrase)):
    if spammifiedPhrase[i] in alreadyCheckedCharList:
        continue
    else:
        alreadyCheckedCharList.append(spammifiedPhrase[i])
        check_char(realPhrase[i], spammifiedPhrase[i])


if makeStringList:
    print("------------------------------------------------------------------")
    print("-------------------------- Pairs to Add --------------------------")
    print("------------------------------------------------------------------")
else:
    print("------------------------------------------------------------------\n")
    print("All pairs are either normal characters or are already included in the confusables mapping.\n")
    input("Press Enter to Exit")
    sys.exit()

for charDict in makeStringList:
    make_string(list(charDict.keys())[0], list(charDict.values())[0])

print("\n------------------------------------------------------------------\n")
input("Entries Generated Above. Press Enter to Exit")
sys.exit()
