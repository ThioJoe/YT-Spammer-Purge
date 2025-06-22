#!/usr/bin/env python3
import os
import sys
import traceback
from html import unescape
from typing import Any

import regex as re
from googleapiclient.errors import HttpError

from . import auth, validation
from .shared_imports import B, F, S
from .types import ScanInstance

##########################################################################################
############################## UTILITY FUNCTIONS #########################################
##########################################################################################


################################### GET VIDEO TITLE ###############################################
# Check if video title is in dictionary, if not get video title from video ID using YouTube API request, then return title
def get_video_title(current: ScanInstance, video_id: str):
    if video_id in current.vidTitleDict.keys():
        title = current.vidTitleDict[video_id]
    elif not current.errorOccurred:
        try:
            results = auth.YOUTUBE.videos().list(part="snippet", id=video_id, fields="items/snippet/title", maxResults=1).execute()
        except HttpError as hx:
            traceback.print_exc()
            print_http_error_during_scan(hx)
            print_error_title_fetch()
            current.errorOccurred = True
            return "[Unavailable]"

        except Exception as ex:
            traceback.print_exc()
            print_exception_during_scan(ex)
            print_error_title_fetch()
            current.errorOccurred = True
            return "[Unavailable]"

        if results['items']:
            title = unescape(results["items"][0]["snippet"]["title"])
            current.vidTitleDict[video_id] = title
        elif (len(video_id) == 26 or len(video_id) == 36) and video_id[0:2] == "Ug":
            title = "[Community Post - No Title]"
            current.vidTitleDict[video_id] = title
        else:
            title = "[Title Unavailable]"
            current.vidTitleDict[video_id] = title
    else:
        title = "[Title Unavailable]"

    return title


######################### Convert string to set of characters#########################
def make_char_set(stringInput: str, stripLettersNumbers: bool = False, stripKeyboardSpecialChars: bool = False, stripPunctuation: bool = False):
    # Optional lists of characters to strip from string
    translateDict: dict[int, Any] = {}
    charsToStrip = " "
    if stripLettersNumbers:
        numbersLettersChars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        charsToStrip += numbersLettersChars
    if stripKeyboardSpecialChars:
        keyboardSpecialChars = "!@#$%^&*()_+-=[]\{\}|;':,./<>?`~"
        charsToStrip += keyboardSpecialChars
    if stripPunctuation:
        punctuationChars = "!?\".,;:'-/()"
        charsToStrip += punctuationChars

    # Adds characters to dictionary to use with translate to remove these characters
    for c in charsToStrip:
        translateDict[ord(c)] = None
    translateDict[ord("\ufe0f")] = None  # Strips invisible varation selector for emojis

    # Removes charsToStrip from string
    stringInput = stringInput.translate(translateDict)
    listedInput = list(stringInput)

    return set(filter(None, listedInput))


######################### Check List Against String #########################
# Checks if any items in a list are a substring of a string
def check_list_against_string(listInput: list[str], stringInput: str, caseSensitive: bool = False):
    if not caseSensitive:
        stringInput = stringInput.lower()
        listInput = [item.lower() for item in listInput]
    return any(x in stringInput for x in listInput)


######################### Clear multiple previous lines #########################
def clear_lines(up: int, down: int = 0):
    LINE_UP = '\033[1A'
    LINE_CLEAR = '\x1b[2K'
    print(LINE_CLEAR, end="")
    for _ in range(up):
        print(LINE_UP, end=LINE_CLEAR)
    if down > 0:
        print("\n" * down, end="\r")


################### Process Comma-Separated String to List ####################
# Take in string, split by commas, remove whitespace and empty items, and return list
def string_to_list(rawString: str, lower: bool = False):
    if lower:
        rawString = rawString.lower()

    # Remove whitespace
    newList = rawString.split(",")
    newList = [item.strip() for item in newList]

    # Remove empty strings from list
    newList = list(filter(None, newList))
    return newList


############################ Process Input Spammer IDs ###############################
# Takes single or list of spammer IDs, splits and sanitizes each, converts to list of channel IDs
# Returns list of channel IDs
def process_spammer_ids(rawString: str):
    inputList = []  # For list of unvalidated inputted items
    IDList = []  # For list of validated channel IDs, converted from inputList of spammer IDs - Separate to allow printing original invalid input if necessary
    inputList = rawString.split(",")  # Split spammer IDs / Links by commas

    # Remove whitespace from each list item
    inputList = [item.strip() for item in inputList]
    inputList = list(filter(None, inputList))  # Remove empty strings from list
    IDList = list(inputList)  # Need to use list() instead of just setting equal so each list is separately affected, otherwise same pointer

    # Validate each ID in list
    for item, i in enumerate(inputList):  ## !!! THIS IS WRONG. ITEM AND I ARE SWAPPED. ENUMAERATE RETURNS (INDEX, VALUE) !!!
        valid, IDList[i], _ = validation.validate_channel_id(item)
        if valid is False:
            print(f"{B.RED}{F.BLACK}Invalid{S.R} Channel ID or Link: {inputList[i]}\n")
            return False, None

    return True, IDList


########################## Expand Number Ranges #############################
def expand_ranges(stringInput: str):
    return re.sub(r'(\d+)-(\d+)', lambda match: ','.join(str(i) for i in range(int(match.group(1)), int(match.group(2)) + 1)), stringInput)


############################### User Choice #################################
# User inputs Y/N for choice, returns True or False
# Takes in message to display


def choice(message: str = "", bypass: bool = False):
    if bypass:
        return True
    while True:
        user = input(f"\n{message} ({F.LIGHTCYAN_EX}y{S.R}/{F.LIGHTRED_EX}n{S.R}): ").strip().lower()
        match user:
            case "y" | "Y":
                return True
            case "n" | "N":
                return False
            case "x" | "X":
                return None
            case _:
                print("\nInvalid Input. Enter Y or N  --  Or enter X to return to main menu.")


############################### ERROR HANDLING MESSAGES #################################


def print_exception_reason(reason: str):
    print(f"    Reason: {reason}")
    if reason == "processingFailure":
        print(f"\n {F.LIGHTRED_EX}[!!] Processing Error{S.R} - Sometimes this error fixes itself. Try just running the program again. !!")
        print("This issue is often on YouTube's side, so if it keeps happening try again later.")
        print("(This also occurs if you try deleting comments on someone else's video, which is not possible.)")
    elif reason == "commentsDisabled":
        print(f"\n{F.LIGHTRED_EX}[!] Error:{S.R} Comments are disabled on this video. This error can also occur if scanning a live stream.")
    elif reason == "quotaExceeded":
        print(f"\n{F.LIGHTRED_EX}Error:{S.R} You have exceeded the YouTube API quota. To do more scanning you must wait until the quota resets.")
        print(" > There is a daily limit of 10,000 units/day, which works out to around reporting 10,000 comments/day.")
        print(" > You can check your quota by searching 'quota' in the Google Cloud console.")
        print(f"{F.YELLOW}Solutions: Either wait until tomorrow, or create additional projects in the cloud console.{S.R}")
        print(f"  > Read more about the quota limits for this app here: {F.YELLOW}TJoe.io/api-limit-info{S.R}")


def print_http_error_during_scan(hx: HttpError):
    print("------------------------------------------------")
    print(f"{B.RED}{F.WHITE} ERROR! {S.R}  Error Message: {hx}")
    if hx.status_code:
        print(f"Status Code: {hx.status_code}")
        if hx.error_details[0]["reason"]:  # If error reason is available, print it
            reason = str(hx.error_details[0]["reason"])
            print_exception_reason(reason)


def print_exception_during_scan(ex: Exception):
    print("-" * 48)
    print(f"{B.RED}{F.WHITE} ERROR! {S.R}  Error Message: {str(ex)}")


def print_break_finished(scanMode: str):
    print("-" * 48)
    print(f"\n{F.LIGHTRED_EX}[!] Fatal Error Occurred During Scan! {F.BLACK}{B.LIGHTRED_EX} Read the important info below! {S.R}")
    print(f"\nProgram must skip the rest of the scan. {F.LIGHTGREEN_EX}Comments already scanned can still be used to create a log file (if you choose){S.R}")
    print(f"  > You won't be able to delete/hide any comments like usual, but you can {F.LIGHTMAGENTA_EX}exclude users before saving the log file{S.R}")
    print(f"  > Then, you can {F.LIGHTGREEN_EX}delete the comments later{S.R} using the {F.YELLOW}mode that removes comments using a pre-existing list{S.R}")
    if scanMode == "entireChannel":
        print(f"{F.RED}NOTE: {S.R} Because of the scanning mode (entire channel) the log will be missing the video IDs and video names.")
    input("\n Press Enter to Continue...")


def print_error_title_fetch():
    print("-" * 122)
    print(f"\n{F.BLACK}{B.RED} ERROR OCCURRED {S.R} While Fetching Video Title... {F.BLACK}{B.LIGHTRED_EX} READ THE INFO BELOW {S.R}")
    print(f"Program will {F.LIGHTGREEN_EX}attempt to continue{S.R}, but the {F.YELLOW}video title may not be available{S.R} in the log file.")
    print(f"  > You won't be able to delete/hide any comments like usual, but you can {F.LIGHTMAGENTA_EX}exclude users before saving the log file{S.R}")
    print(f"  > Then, you can {F.LIGHTGREEN_EX}delete the comments later{S.R} using the {F.YELLOW}mode that removes comments using a pre-existing log file{S.R}")
    input("\n Press Enter to Continue...")


def clear_terminal():
    if sys.stdout.isatty():  # if in a terminal
        if sys.platform.startswith("win"):
            # For windows, use cls
            os.system("cls")
        else:
            # For MacOS / Linux, this should clear the screen
            sys.stdout.write("\033[2J\033[1;1H")
    # Not 100% sure if there are any cases where sys.stdout.isatty can raise an exception
