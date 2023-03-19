#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Scripts.shared_imports import *
import Scripts.validation as validation
import Scripts.auth as auth
from googleapiclient.errors import HttpError

##########################################################################################
############################## UTILITY FUNCTIONS #########################################
########################################################################################## 

################################### GET VIDEO TITLE ###############################################
# Check if video title is in dictionary, if not get video title from video ID using YouTube API request, then return title
def get_video_title(current, video_id):
  if video_id in current.vidTitleDict.keys():
    title = current.vidTitleDict[video_id]
  elif current.errorOccurred == False:
    try:
      results = auth.YOUTUBE.videos().list(
        part="snippet",
        id=video_id,
        fields="items/snippet/title",
        maxResults=1
      ).execute()
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
      title = results["items"][0]["snippet"]["title"]
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
def make_char_set(stringInput, stripLettersNumbers=False, stripKeyboardSpecialChars=False, stripPunctuation=False):
    # Optional lists of characters to strip from string
    translateDict = {}
    charsToStrip = " "
    if stripLettersNumbers == True:
      numbersLettersChars = ("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
      charsToStrip += numbersLettersChars
    if stripKeyboardSpecialChars == True:
      keyboardSpecialChars = ("!@#$%^&*()_+-=[]\{\}|;':,./<>?`~")
      charsToStrip += keyboardSpecialChars
    if stripPunctuation == True:
      punctuationChars = ("!?\".,;:'-/()")
      charsToStrip += punctuationChars
    
    # Adds characters to dictionary to use with translate to remove these characters
    for c in charsToStrip:
      translateDict[ord(c)] = None
    translateDict[ord("\ufe0f")] = None # Strips invisible varation selector for emojis
    
    # Removes charsToStrip from string
    stringInput = stringInput.translate(translateDict)
    listedInput = list(stringInput)
    
    return set(filter(None, listedInput))

######################### Check List Against String #########################    
# Checks if any items in a list are a substring of a string
def check_list_against_string(listInput, stringInput, caseSensitive=False):
  if caseSensitive == False:
    stringInput = stringInput.lower()
    listInput = [item.lower() for item in listInput]
  if any(x in stringInput for x in listInput):
    return True
  else:
    return False


################### Process Comma-Separated String to List ####################
# Take in string, split by commas, remove whitespace and empty items, and return list
def string_to_list(rawString, lower=False):
  if lower == True:
    rawString = rawString.lower()
  
  # Remove whitespace
  newList = rawString.split(",")
  for i in range(len(newList)):
    newList[i] =  newList[i].strip()

  # Remove empty strings from list
  newList = list(filter(None, newList)) 
  return newList


############################ Process Input Spammer IDs ###############################
# Takes single or list of spammer IDs, splits and sanitizes each, converts to list of channel IDs
# Returns list of channel IDs
def process_spammer_ids(rawString):
  inputList = [] # For list of unvalidated inputted items
  IDList = [] # For list of validated channel IDs, converted from inputList of spammer IDs - Separate to allow printing original invalid input if necessary
  inputList = rawString.split(",") # Split spammer IDs / Links by commas

  # Remove whitespace from each list item
  for i in range(len(inputList)):
     inputList[i] =  inputList[i].strip()
  inputList = list(filter(None, inputList)) # Remove empty strings from list
  IDList = list(inputList)  # Need to use list() instead of just setting equal so each list is separately affected, otherwise same pointer

  # Validate each ID in list
  for i in range(len(inputList)):
    valid, IDList[i], channelTitle = validation.validate_channel_id(inputList[i])
    if valid == False:
      print(f"{B.RED}{F.BLACK}Invalid{S.R} Channel ID or Link: " + str(inputList[i]) + "\n")
      return False, None
  
  return True, IDList  


########################## Expand Number Ranges #############################
def expand_ranges(stringInput):
    return re.sub(
        r'(\d+)-(\d+)',
        lambda match: ','.join(
            str(i) for i in range(
                int(match.group(1)),
                int(match.group(2)) + 1
            )   
        ),  
        stringInput
    )



############################### User Choice #################################
# User inputs Y/N for choice, returns True or False
# Takes in message to display

def choice(message="", bypass=False):
  if bypass == True:
    return True

  # While loop until valid input
  valid = False
  while valid == False:
    response = input("\n" + message + f" ({F.LIGHTCYAN_EX}y{S.R}/{F.LIGHTRED_EX}n{S.R}): ").strip()
    if response == "Y" or response == "y":
      return True
    elif response == "N" or response == "n":
      return False
    elif response == "X" or response == "x":
      return None
    else:
      print("\nInvalid Input. Enter Y or N  --  Or enter X to return to main menu.")  


############################### ERROR HANDLING MESSAGES #################################

def print_exception_reason(reason):
  print("    Reason: " + str(reason))
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

def print_http_error_during_scan(hx):
  print("------------------------------------------------")
  print(f"{B.RED}{F.WHITE} ERROR! {S.R}  Error Message: " + str(hx))
  if hx.status_code:
    print("Status Code: " + str(hx.status_code))
    if hx.error_details[0]["reason"]: # If error reason is available, print it
        reason = str(hx.error_details[0]["reason"])
        print_exception_reason(reason)

def print_exception_during_scan(ex):
  print("------------------------------------------------")
  print(f"{B.RED}{F.WHITE} ERROR! {S.R}  Error Message: " + str(ex))

def print_break_finished(scanMode):
  print("------------------------------------------------")
  print(f"\n{F.LIGHTRED_EX}[!] Fatal Error Occurred During Scan! {F.BLACK}{B.LIGHTRED_EX} Read the important info below! {S.R}")
  print(f"\nProgram must skip the rest of the scan. {F.LIGHTGREEN_EX}Comments already scanned can still be used to create a log file (if you choose){S.R}")
  print(f"  > You won't be able to delete/hide any comments like usual, but you can {F.LIGHTMAGENTA_EX}exclude users before saving the log file{S.R}")
  print(f"  > Then, you can {F.LIGHTGREEN_EX}delete the comments later{S.R} using the {F.YELLOW}mode that removes comments using a pre-existing list{S.R}")
  if scanMode == "entireChannel":
    print(f"{F.RED}NOTE: {S.R} Because of the scanning mode (entire channel) the log will be missing the video IDs and video names.")
  input("\n Press Enter to Continue...")

def print_error_title_fetch():
  print("--------------------------------------------------------------------------------------------------------------------------")
  print(f"\n{F.BLACK}{B.RED} ERROR OCCURRED {S.R} While Fetching Video Title... {F.BLACK}{B.LIGHTRED_EX} READ THE INFO BELOW {S.R}")
  print(f"Program will {F.LIGHTGREEN_EX}attempt to continue{S.R}, but the {F.YELLOW}video title may not be available{S.R} in the log file.")
  print(f"  > You won't be able to delete/hide any comments like usual, but you can {F.LIGHTMAGENTA_EX}exclude users before saving the log file{S.R}")
  print(f"  > Then, you can {F.LIGHTGREEN_EX}delete the comments later{S.R} using the {F.YELLOW}mode that removes comments using a pre-existing log file{S.R}")
  input("\n Press Enter to Continue...")

def clear_terminal() -> None:
  if sys.stdout.isatty(): # if in a terminal
    if sys.platform.startswith("win"):
      # For windows, use cls
      os.system("cls")
    else:
      # For MacOS / Linux, this should clear the screen
      sys.stdout.write("\033[2J\033[1;1H")
  # Do nothing if not a terminal
  return
  # Not 100% sure if there are any cases where sys.stdout.isatty can raise an exception
