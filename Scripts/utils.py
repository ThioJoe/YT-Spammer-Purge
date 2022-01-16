#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Scripts.shared_imports import *
import Scripts.validation as validation
import Scripts.auth as auth


##########################################################################################
############################## UTILITY FUNCTIONS #########################################
########################################################################################## 

################################### GET VIDEO TITLE ###############################################
# Check if video title is in dictionary, if not get video title from video ID using YouTube API request, then return title
def get_video_title(current, video_id):
  if video_id in current.vidTitleDict.keys():
    title = current.vidTitleDict[video_id]
  else:
    results = auth.YOUTUBE.videos().list(
      part="snippet",
      id=video_id,
      fields="items/snippet/title",
      maxResults=1
    ).execute()
    title = results["items"][0]["snippet"]["title"]
    current.vidTitleDict[video_id] = title

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