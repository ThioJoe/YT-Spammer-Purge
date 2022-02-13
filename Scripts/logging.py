#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Scripts.shared_imports import *
import Scripts.utils as utils
import Scripts.auth as auth
from Scripts.utils import choice
from unicodedata import category as unicode_category

import rtfunicode
import os
import requests
import json


##########################################################################################
############################### PRINT SPECIFIC COMMENTS ##################################
##########################################################################################

# First prepared comments into segments of 50 to be submitted to API simultaneously
# Then uses print_prepared_comments() to print / log the comments
def print_comments(current, config, scanVideoID, loggingEnabled, scanMode, logMode=None, doWritePrint=True):
  j = 0 # Counting index when going through comments all comment segments
  commentsContents = ""

  # Print filter matched comments
  j, commentsContents = print_prepared_comments(current, commentsContents, scanVideoID, list(current.matchedCommentsDict.keys()), j, loggingEnabled, scanMode, logMode, doWritePrint, matchReason="Filter Match")
  # Print comments of other match types
  if current.spamThreadsDict:
    j, commentsContents = print_prepared_comments(current, commentsContents, scanVideoID, list(current.spamThreadsDict.keys()), j, loggingEnabled, scanMode, logMode, doWritePrint, matchReason="Spam Bot Thread")
  if current.otherCommentsByMatchedAuthorsDict:
    j, commentsContents = print_prepared_comments(current, commentsContents, scanVideoID, list(current.otherCommentsByMatchedAuthorsDict.keys()), j, loggingEnabled, scanMode, logMode, doWritePrint, matchReason="Also By Matched Author")
  if current.duplicateCommentsDict:
    j, commentsContents = print_prepared_comments(current, commentsContents, scanVideoID, list(current.duplicateCommentsDict.keys()), j, loggingEnabled, scanMode, logMode, doWritePrint, matchReason="Duplicate")

  # Writes everything to the log file
  if loggingEnabled == True and doWritePrint:
    print(" Writing to log file, please wait...", end="\r")
    if logMode == "rtf":
      write_rtf(current.logFileName, commentsContents)
    elif logMode == "plaintext":
      write_plaintext_log(current.logFileName, commentsContents)
    print("                                             ")

  # Print Sample Match List
  valuesPreparedToWrite = ""
  valuesPreparedToPrint = ""
  matchSamplesContent = ""
  spamThreadValuesPreparedToWrite = ""
  spamThreadValuesPreparedToPrint = ""
  spamThreadSamplesContent = ""
  duplicateValuesToWrite = ""
  duplicateValuesToPrint = ""
  duplicateSamplesContent = ""
  hasDuplicates = False
  hasSpamThreads = False
  

  def print_and_write(value, writeValues, printValues):
    if loggingEnabled == True and logMode == "rtf":
      writeValues = writeValues + value['iString'] + value['cString'] + f"{str(value['authorID'])} | {make_rtf_compatible(str(value['nameAndText']))} \\line \n"
    elif loggingEnabled == True and logMode == "plaintext":
      writeValues = writeValues + value['iString'] + value['cString'] + f"{str(value['authorID'])} | {str(value['nameAndText'])}\n"
    if doWritePrint:
      printValues = printValues + value['iString'] + value['cString'] + f"{str(value['nameAndText'])}\n"
    return writeValues, printValues

  if doWritePrint:
    print(f"{F.LIGHTMAGENTA_EX}============================ Match Samples: One comment per matched-comment author ============================{S.R}")
  for value in current.matchSamplesDict.values():
    if value['matchReason'] != "Duplicate" and value['matchReason'] != "Spam Bot Thread":
      valuesPreparedToWrite, valuesPreparedToPrint = print_and_write(value, valuesPreparedToWrite, valuesPreparedToPrint)
    # If there are duplicates, save those to print later, but get ready by calculating some duplicate info
    elif value['matchReason'] == "Duplicate":
      hasDuplicates = True
      similarity = str(round(float(config['levenshtein_distance'])*100))+"%"
      minDupes = str(config['minimum_duplicates'])
    elif value['matchReason'] == "Spam Bot Thread":
      hasSpamThreads = True
  if doWritePrint:
    print(valuesPreparedToPrint)

  # Print Spam Thread Match Samples
  if hasSpamThreads == True:
    if doWritePrint:
      print(f"{S.BRIGHT}{F.MAGENTA}============================ Match Samples: Spam Bot Threads ============================{S.R}")
  for value in current.matchSamplesDict.values():
    if value['matchReason'] == "Spam Bot Thread":
      spamThreadValuesPreparedToWrite, spamThreadValuesPreparedToPrint = print_and_write(value, spamThreadValuesPreparedToWrite, spamThreadValuesPreparedToPrint)
  if doWritePrint:
    print(spamThreadValuesPreparedToPrint)

  # Print Duplicates Match Samples
  if hasDuplicates == True:
    if doWritePrint:
      print(f"{F.LIGHTMAGENTA_EX}------------------------- {S.BRIGHT}{F.WHITE}{B.BLUE} Non-Matched {S.R}{F.LIGHTCYAN_EX} Commenters, But Who Wrote Many Similar Comments{F.LIGHTMAGENTA_EX} -------------------------{S.R}")
      print(f"{F.MAGENTA}---------------------------- ( {F.LIGHTBLUE_EX}Similarity Threshold: {similarity}  |  Minimum Duplicates: {minDupes}{F.MAGENTA} ) ----------------------------{S.R}")
  for value in current.matchSamplesDict.values():
    if value['matchReason'] == "Duplicate":
      duplicateValuesToWrite, duplicateValuesToPrint = print_and_write(value, duplicateValuesToWrite, duplicateValuesToPrint)
  if doWritePrint:
    print(duplicateValuesToPrint)

  # --------------------------------------------------

  # Write just match Samples to log, after header and comment contents already in place
  if loggingEnabled == True:

    if logMode == "rtf":
      matchSamplesContent = "==================== Match Samples: One comment per matched-comment author ==================== \\line\\line \n" + valuesPreparedToWrite
      if doWritePrint:
        write_rtf(current.logFileName, matchSamplesContent)
      if current.spamThreadsDict:
        spamThreadSamplesContent = " \n \\line\\line ============================ Match Samples: Spam Bot Threads ============================ \\line\\line \n" + spamThreadValuesPreparedToWrite
        if doWritePrint:
          write_rtf(current.logFileName, spamThreadSamplesContent)
      if hasDuplicates == True:
        duplicateSamplesContent = " \n \\line\\line -------------------- Non-Matched Commenters, but who wrote many similar comments -------------------- \\line \n" 
        duplicateSamplesContent += f"---------------------- ( Similarity Threshold: {similarity}  |  Minimum Duplicates: {minDupes} ) ---------------------- \\line\\line \n" + duplicateValuesToWrite
        if doWritePrint:
          write_rtf(current.logFileName, duplicateSamplesContent)

    elif logMode == "plaintext":
      matchSamplesContent = "==================== Match Samples: One comment per matched-comment author ====================\n" + valuesPreparedToWrite
      if doWritePrint:
        write_plaintext_log(current.logFileName, matchSamplesContent)
      if current.spamThreadsDict:
        spamThreadSamplesContent = "\n============================ Match Samples: Spam Bot Threads ============================\n" + spamThreadValuesPreparedToWrite
        if doWritePrint:
          write_plaintext_log(current.logFileName, spamThreadSamplesContent)
      if hasDuplicates == True:
        duplicateSamplesContent = "\n-------------------- Non-Matched Commenters, but who wrote many similar comments --------------------\n"
        duplicateSamplesContent += f"---------------------- ( Similarity Threshold: {similarity}  |  Minimum Duplicates: {minDupes} ) ----------------------\n" + duplicateValuesToWrite
        if doWritePrint:
          write_plaintext_log(current.logFileName, duplicateSamplesContent)

    # Entire Contents of Log File
    logFileContents = commentsContents + matchSamplesContent + spamThreadSamplesContent + duplicateSamplesContent
  else:
    logFileContents = None
    logMode = None
  if doWritePrint:
    print(f"{F.LIGHTMAGENTA_EX}==================== (See log file for channel IDs of matched authors above) ===================={S.R}")

  return logFileContents, logMode

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Uses comments.list YouTube API Request to get text and author of specific set of comments, based on comment ID
def print_prepared_comments(current, commentsContents, scanVideoID, comments, j, loggingEnabled, scanMode, logMode, doWritePrint, matchReason):

  if matchReason != "Filter Match":
    dividerString = "============================================================================================"
    if matchReason == "Also By Matched Author":
      reasonString = "======================== All Non-matched Comments by Authors Above ========================"
    elif matchReason == "Duplicate":
      reasonString = "=========================== Non-Matched, But Duplicate Comments ==========================="
    elif matchReason == "Spam Bot Thread":
      reasonString = "============================ Spam Bot Thread Top-Level Comments ==========================="
    
    # -------------------- Print Section Header --------------------
    # Print top divider
    if doWritePrint:
      print(f"\n\n{dividerString}")
    if logMode == "rtf":
      commentsContents = commentsContents + f"\\line\\line \n\n{dividerString}"
    elif logMode == "plaintext":
      commentsContents = commentsContents + f"\n\n{dividerString}"

    # Print header text
    if doWritePrint:
      print(f"{reasonString}")
    if logMode == "rtf":
      commentsContents = commentsContents + f"\\line \n{reasonString}"
    elif logMode == "plaintext":
       commentsContents = commentsContents + f"\n{reasonString}"
    
    # Print bottom divider
    if doWritePrint:
      print(f"{dividerString}\n")
    if logMode == "rtf":
      commentsContents = commentsContents + f"\\line \n{dividerString} \\line\\line \n\n"
    elif logMode == "plaintext":
      commentsContents = commentsContents + f"\n{dividerString}\n\n"
    # -----------------------------------------------------------------

  for comment in comments:
    if matchReason == "Filter Match":
      metadata = current.matchedCommentsDict[comment]
    elif matchReason == "Duplicate":
      metadata = current.duplicateCommentsDict[comment]
    elif matchReason == "Also By Matched Author":
      metadata = current.otherCommentsByMatchedAuthorsDict[comment]
    elif matchReason == "Spam Bot Thread":
      metadata = current.spamThreadsDict[comment]

    # For printing and regular logging
    text = metadata['text']
    author = metadata['authorName']
    author_id_local = metadata['authorID']
    comment_id_local = comment
    videoID = metadata['videoID']
    matchReason = metadata['matchReason']
   
    # Truncates very long comments, and removes excessive multiple lines
    if len(text) > 1500:
      text = text[0:1500] + "[Comment Truncated by YT SPammer Purge]"
    if text.count("\n") > 0:
      text = text.replace("\n", " ")

    # Add one sample from each matching author to current.matchSamplesDict, containing author ID, name, and text
    if matchReason != "Also By Matched Author" and author_id_local not in current.matchSamplesDict.keys():
      add_sample(current, author_id_local, author, text, matchReason)

    # Build comment direct link
    if scanMode == "communityPost" or scanMode == "recentCommunityPosts":
      directLink = "https://www.youtube.com/post/" + videoID + "?lc=" + comment_id_local
    else:
      directLink = "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comment_id_local

    # Prints comment info to console
    if doWritePrint:
      print(str(j+1) + f". {F.LIGHTCYAN_EX}" + author + f"{S.R}:  {F.YELLOW}" + text + f"{S.R}")
      print("—————————————————————————————————————————————————————————————————————————————————————————————")
      print("     > Reason: " + matchReason)
    if scanVideoID is None:  # Only print video title if searching entire channel
      title = utils.get_video_title(current, videoID) # Get Video Title
      if doWritePrint:
        print("     > Video: " + title)
    if doWritePrint:
      print("     > Direct Link: " + directLink)
      print(f"     > Author Channel ID: {F.LIGHTBLUE_EX}" + author_id_local + f"{S.R}")
      print("=============================================================================================\n")

    # If logging enabled, also prints to log file 
    if loggingEnabled == True:
      # Only print video title info if searching entire channel
      if scanVideoID is None:  
        if logMode == "rtf":
         titleInfoLine = "     > Video: " + title + "\\line " + "\n"
        elif logMode == "plaintext":
          titleInfoLine = "     > Video: " + title + "\n"
      else:
        titleInfoLine = ""

      if logMode == "rtf":
        commentInfo = (
          # Author Info
          str(j+1) + r". \cf4"
          + make_rtf_compatible(author)
          + r"\cf1 :  \cf5"
          + make_rtf_compatible(text)
          + r"\cf1 \line " + "\n"
          + "---------------------------------------------------------------------------------------------\\line " + "\n"
          # Rest of Comment Info
          + "     > Reason: " + matchReason + "\\line "+ "\n"
          + titleInfoLine
          + "     > Direct Link: " + directLink + " \\line "+ "\n"
          + "     > Author Channel ID: \cf6" + author_id_local + r"\cf1 \line "+ "\n"
          + "=============================================================================================\\line\\line\\line" + "\n\n\n"
        )
      elif logMode == "plaintext":
        commentInfo = (
          # Author Info
          str(j+1) + ". "
          + author
          + ":  "
          + text
          + "\n"
          + "---------------------------------------------------------------------------------------------\n"
          # Rest of Comment Info
          + "     > Reason: " + matchReason + "\n"
          + titleInfoLine
          + "     > Direct Link: " + directLink + "\n"
          + "     > Author Channel ID: " + author_id_local + "\n"
          + "=============================================================================================\n\n\n"
        )
      commentsContents = commentsContents + commentInfo

    # Appends comment ID to new list of comments so it's in the correct order going forward, as provided by API and presented to user
    # Must use append here, not extend, or else it would add each character separately
    j += 1

  return j, commentsContents


############################ RTF & Log File Handling ###############################

# Takes in a string that contains unicode, and returns a string with properly escaped unicode format for use in rtf files
# Uses 'rtfunicode' module to encode with proper rtf-compatible unicode escapes, then decode back to utf-8 so it can be written to file and read by wordpad or whatever
def make_rtf_compatible(text):
  try:
    return text.encode('rtfunicode').decode('utf-8')
  except:
    intermediate = "".join(char for char in text if unicode_category(char) not in ["Mn", "Cc", "Cf", "Cs", "Co", "Cn"])
    try:
      return intermediate.encode('rtfunicode').decode('utf-8')
    except:
      return intermediate

# Writes properly to rtf file, also can prepare with necessary header information and formatting settings
def write_rtf(fileName, newText=None, firstWrite=False, fullWrite=False):
  success = False
  attempts = 0
  if firstWrite == True or fullWrite == True:
    # If directory does not exist for desired log file path, create it
    logFolderPath = os.path.dirname(os.path.realpath(fileName))
    if not os.path.isdir(logFolderPath):
      try:
        os.mkdir(logFolderPath)
        # If relative path, make it absolute
        if not os.path.isabs(fileName):
          fileName = os.path.join(logFolderPath, os.path.basename(fileName))
      except:
        print(f"{F.LIGHTRED_EX}Error:{S.R} Could not create desired directory for log files. Will place them in current directory.")
        fileName = os.path.basename(fileName)
    while success == False:
      try:
        attempts += 1
        with open(fileName, 'w', encoding="utf-8") as file:
          # Some header information for RTF file, sets courier as font
          file.write(r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Courier;}}"+"\n")

          # Sets color table to be able to set colors for text, each color set with RGB values in raw string
          # To use color, use '\cf1 ' (with space) for black, cf2 = red, cf3 = green, cf4 = blue, cf5 = orange, cf6 = purple
          #                       cf1                cf2                  cf3                  cf4                  cf5                    cf6                 
          file.write(r"{\colortbl;\red0\green0\blue0;\red255\green0\blue0;\red0\green255\blue0;\red0\green0\blue255;\red143\green81\blue0;\red102\green0\blue214;}"+"\n\n")
          if fullWrite == True:
            file.write(newText)
          file.write(r"}")
          file.close()
        success = True
      except PermissionError:
        if attempts < 3:
          print(f"\n{F.YELLOW}\nERROR!{S.R} Cannot write to {F.LIGHTCYAN_EX}{fileName}{S.R}. Is it open? Try {F.YELLOW}closing the file{S.R} before continuing.")
          input("\n Press Enter to Try Again...")
        else:
          print(f"{F.LIGHTRED_EX}\nERROR! Still cannot write to {F.LIGHTCYAN_EX}{fileName}{F.LIGHTRED_EX}. {F.YELLOW}Try again?{S.R} (Y) or {F.YELLOW}Skip Writing Log?{S.R} (N)")
          if choice("Choice") == False:
            break

  # If the string might have unicode, use unicode mode to convert for rtf
  else:
    # Writes to line just before last, to preserve required ending bracket in rtf file
    # Slightly modified from: https://stackoverflow.com/a/50567967/17312053   
    while success == False:
      try:
        attempts += 1
        with open(fileName, 'r+', encoding="utf-8") as file:
          pos, text = 0, ''
          while True:
            # save last line value and cursor position
            prev_pos, pos = pos, file.tell()
            prev_text, text = text, file.readline()  
            if text == '': # Checks for last line with only ending bracket
              break
          file.seek(prev_pos, 0) # replace cursor to the last line
          for line in newText: # write new lines. If any brackets, add escape backslash
            line.replace("}", "\\}")
            line.replace("{", "\\{")
            file.write(line)
          file.write("\n}") # Re-write new line with ending bracket again. Could put prev_text in here if being dynamic
          file.close()
          success = True
      except PermissionError:
        if attempts < 3:
          print(f"\n{F.YELLOW}\nERROR!{S.R} Cannot write to {F.LIGHTCYAN_EX}{fileName}{S.R}. Is it open? Try {F.YELLOW}closing the file{S.R} before continuing.")
          input("\n Press Enter to Try Again...")
        else:
          print(f"{F.LIGHTRED_EX}\nERROR! Still cannot write to {F.LIGHTCYAN_EX}{fileName}{F.LIGHTRED_EX}. {F.YELLOW}Try again?{S.R} (Y) or {F.YELLOW}Skip Writing Log?{S.R} (N)")
          if choice("Choice") == False:
            break

############################ Plaintext Log & File Handling ###############################

def write_plaintext_log(fileName, newText=None, firstWrite=False, fullWrite=False):
  success = False
  attempts = 0
  if firstWrite == True or fullWrite == True:
    # If directory does not exist for desired log file path, create it
    logFolderPath = os.path.dirname(os.path.realpath(fileName))
    if not os.path.isdir(logFolderPath):
      try:
        os.mkdir(logFolderPath)
        # If relative path, make it absolute
        if not os.path.isabs(fileName):
          fileName = os.path.join(logFolderPath, os.path.basename(fileName))
      except:
        print(f"{F.LIGHTRED_EX}Error:{S.R} Could not create desired directory for log files. Will place them in current directory.")
        fileName = os.path.basename(fileName)
    while success == False:
      try:
        attempts += 1
        with open(fileName, "w", encoding="utf-8") as file:
          if fullWrite == True:
            file.write(newText)
          else:
            file.write("")
          file.close()
        success = True
      except PermissionError:
        if attempts < 3:
          print(f"\n{F.YELLOW}\nERROR!{S.R} Cannot write to {F.LIGHTCYAN_EX}{fileName}{S.R}. Is it open? Try {F.YELLOW}closing the file{S.R} before continuing.")
          input("\n Press Enter to Try Again...")
        else:
          print(f"{F.LIGHTRED_EX}\nERROR! Still cannot write to {F.LIGHTCYAN_EX}{fileName}{F.LIGHTRED_EX}. {F.YELLOW}Try again?{S.R} (Y) or {F.YELLOW}Skip Writing Log?{S.R} (N)")
          if choice("Choice") == False:
            break 

  else:
    while success == False:
      try:
        attempts += 1
        with open(fileName, 'a', encoding="utf-8") as file:
          for line in newText:
            file.write(line)
          file.close()
        success = True
      except PermissionError:
        if attempts < 3:
          print(f"\n{F.YELLOW}\nERROR!{S.R} Cannot write to {F.LIGHTCYAN_EX}{fileName}{S.R}. Is it open? Try {F.YELLOW}closing the file{S.R} before continuing.")
          input("\n Press Enter to Try Again...")
        else:
          print(f"{F.LIGHTRED_EX}\nERROR! Still cannot write to {F.LIGHTCYAN_EX}{fileName}{F.LIGHTRED_EX}. {F.YELLOW}Try again?{S.R} (Y) or {F.YELLOW}Skip Writing Log?{S.R} (N)")
          if choice("Choice") == False:
            break 

############################ JSON Log & File Handling ###############################
def write_json_log(jsonSettingsDict, commentsDict, jsonDataDict=None):
  success = False
  attempts = 0
  if jsonDataDict:
    jsonDataDict['Comments'] = commentsDict
    dictionaryToWrite = jsonDataDict
  else:
    dictionaryToWrite = commentsDict

  fileName = jsonSettingsDict['jsonLogFileName']
  jsonEncoding = jsonSettingsDict['encoding']

  # If directory does not exist for desired log file path, create it
  logFolderPath = os.path.dirname(os.path.realpath(fileName))
  if not os.path.isdir(logFolderPath):
    try:
      os.mkdir(logFolderPath)
      # If relative path, make it absolute
      if not os.path.isabs(fileName):
        fileName = os.path.join(logFolderPath, os.path.basename(fileName))
    except:
      print(f"{F.LIGHTRED_EX}Error:{S.R} Could not create desired directory for log files. Will place them in current directory.")
      fileName = os.path.basename(fileName)
  while success == False:
    try:
      attempts += 1
      with open(fileName, "w", encoding=jsonEncoding) as file:
        file.write(json.dumps(dictionaryToWrite, indent=4, ensure_ascii=False))
        file.close()
      success = True
    except PermissionError:
      if attempts < 3:
        print(f"\n{F.YELLOW}\nERROR!{S.R} Cannot write to {F.LIGHTCYAN_EX}{fileName}{S.R}. Is it open? Try {F.YELLOW}closing the file{S.R} before continuing.")
        input("\n Press Enter to Try Again...")
      else:
        print(f"{F.LIGHTRED_EX}\nERROR! Still cannot write to {F.LIGHTCYAN_EX}{fileName}{F.LIGHTRED_EX}. {F.YELLOW}Try again?{S.R} (Y) or {F.YELLOW}Skip Writing Log?{S.R} (N)")
        if choice("Choice") == False:
          break 

############################ Get Extra JSON Data and Profile Pictures ###############################

def get_extra_json_data(channelIDs, jsonSettingsDict):
  channelOwnerID = jsonSettingsDict['channelOwnerID']
  channelOwnerName = jsonSettingsDict['channelOwnerName']
  getPicsBool = False

  # Construct extra json data dictionary
  jsonExtraDataDict = {
    "Comments": {},
    "CommentAuthorInfo": {},
    "UploaderInfo": {}
  }

  if jsonSettingsDict['json_profile_picture'] != False:
      getPicsBool = True
      pictureUrlsDict = {}
      resolution = jsonSettingsDict['json_profile_picture']
      possibleResolutions = ['default', 'medium', 'high']
      if resolution not in possibleResolutions:
        print(f"{B.RED}{F.BLACK}Invalid Resolution!{S.R} Defaulting to 'default' (smallest)")
        resolution = 'default'

  total = len(channelIDs)
  fieldsToFetch=(
    "items/id,"
    "items/snippet/publishedAt,"
    "items/statistics")

  if jsonSettingsDict['json_profile_picture'] != False:
    fieldsToFetch += f",items/snippet/thumbnails/{resolution}/url,items/id"

  def fetch_data(channelIdGroup):
    try:
      response = auth.YOUTUBE.channels().list(part="snippet,statistics", id=channelIdGroup, fields=fieldsToFetch).execute()
      if response['items']:
        for j in range(len(channelIdGroup)):
          tempDict = {}
          channelID = response['items'][j]['id']
          tempDict['PublishedAt'] = response['items'][j]['snippet']['publishedAt']
          tempDict['Statistics'] = response['items'][j]['statistics']
          if getPicsBool == True:
            picURL = response['items'][j]['snippet']['thumbnails'][resolution]['url']
            pictureUrlsDict[channelID] = picURL
          jsonExtraDataDict['CommentAuthorInfo'][channelID] = tempDict
    except:
      traceback.print_exc()
      print("Error occurred when fetching extra json data.")
      return False

  # Get Extra Info About Commenters
  print("Fetching Extra JSON Data...")
  if total > 50:
    remainder = total % 50
    numDivisions = int((total-remainder)/50)
    for i in range(numDivisions):
      fetch_data(channelIDs[i*50:i*50+50])
    if remainder > 0:
      fetch_data(channelIDs[numDivisions*50:])
  else:
    fetch_data(channelIDs)
  
  # Get info about uploader
  response = auth.YOUTUBE.channels().list(part="snippet,statistics", id=channelOwnerID, fields=fieldsToFetch).execute()
  if response['items']:
    tempDict = {}
    tempDict['PublishedAt'] = response['items'][0]['snippet']['publishedAt']
    tempDict['Statistics'] = response['items'][0]['statistics']
    tempDict['ChannelID'] = channelOwnerID
    tempDict['ChannelName'] = channelOwnerName
    if getPicsBool == True:
      pictureUrlsDict[channelOwnerID] = response['items'][0]['snippet']['thumbnails'][resolution]['url']
    jsonExtraDataDict['UploaderInfo'] = tempDict

  if getPicsBool == True:
    download_profile_pictures(pictureUrlsDict, jsonSettingsDict)
  
  return jsonExtraDataDict

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def download_profile_pictures(pictureUrlsDict, jsonSettingsDict):
  fileName = jsonSettingsDict['jsonLogFileName']
  logtime = jsonSettingsDict['logTime'] # To have the same name as the log file

  imageFolderName = "ProfileImages_" + logtime
  logFolderPath = os.path.dirname(os.path.realpath(fileName))
  imageFolderPath = os.path.join(logFolderPath, imageFolderName)
  logtime = jsonSettingsDict['logTime'] # To have the same name as the log file

  block_size =  1048576 # 1 MiB
  if not os.path.isdir(imageFolderPath):
    try:
      os.mkdir(imageFolderPath)
    except:
      print(f"{F.LIGHTRED_EX}Error:{S.R} Unable to create image folder. Try creating a folder called 'ProfileImages' in the log file folder.")
      return False, None

  attempts = 0
  success = False
  print("\nFetching Profile Pictures...")
  # Download and save pictures
  while success == False:
    try:
      attempts += 1
      for channelID, pictureURL in pictureUrlsDict.items():
        filedownload = requests.get(pictureURL, stream=True)
        downloadFileName = channelID + ".jpg"
        # Make absolute path
        downloadFileName = os.path.join(imageFolderPath, channelID + ".jpg")
        with open(downloadFileName, 'wb') as file:
          for data in filedownload.iter_content(block_size):
            file.write(data)
      success = True
      print("Successfully downloaded profile pictures.")
    except PermissionError:
      if attempts < 3:
        print(f"\n{F.YELLOW}\nERROR!{S.R} Cannot write to {F.LIGHTCYAN_EX}{fileName}{S.R}. Is it open? Try {F.YELLOW}closing the file{S.R} before continuing.")
        input("\n Press Enter to Try Again...")
      else:
        print(f"{F.LIGHTRED_EX}\nERROR! Still cannot write to {F.LIGHTCYAN_EX}{fileName}{F.LIGHTRED_EX}. {F.YELLOW}Try again?{S.R} (Y) or {F.YELLOW}Skip Downloading Profile Pictures?{S.R} (N)")
        if choice("Choice") == False:
          break 

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Adds a sample to current.matchSamplesDict and preps formatting
def add_sample(current, authorID, authorNameRaw, commentText, matchReason):

  # Make index number and string formatted version
  index = len(current.matchSamplesDict) + 1
  iString = f"{str(index)}. ".ljust(4)
  authorNumComments = current.authorMatchCountDict[authorID]
  cString = f"[x{str(authorNumComments)}] ".ljust(7)

  # Left Justify Author Name and Comment Text
  if len(authorNameRaw) > 20:
    authorName = authorNameRaw[0:17] + "..."
    authorName = authorName[0:20].ljust(20)+": "
  else: 
    authorName = authorNameRaw[0:20].ljust(20)+": "

  commentText = str(commentText).replace("\n", " ").replace("\r", " ")
  if len(commentText) > 82:
    commentText = commentText[0:79] + "..."
  commentText = commentText[0:82].ljust(82)

  # Add comment sample, author ID, name, and counter
  current.matchSamplesDict[authorID] = {'index':index, 'cString':cString, 'iString':iString, 'count':authorNumComments, 'authorID':authorID, 'authorName':authorNameRaw, 'nameAndText':authorName + commentText, 'matchReason':matchReason}

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Determine log file and json log file locations and names
def prepare_logFile_settings(current, config, miscData, jsonSettingsDict, filtersDict, bypass):

  logMode = None
  logFileType = None
  jsonLogging = False

  logMode = config['log_mode']
  if logMode == "rtf":
    logFileType = ".rtf"
  elif logMode == "plaintext":
    logFileType = ".txt"
  else:
    print("Invalid value for 'log_mode' in config file:  " + logMode)
    print("Defaulting to .rtf file")
    logMode = "rtf"

  # Prepare log file names
  fileNameBase = "Spam_Log_" + current.logTime
  fileName = fileNameBase + logFileType

  try:
    # Get json logging settings
    if config['json_log'] == True:
      jsonLogging = True
      jsonLogFileName = fileNameBase + ".json"
      jsonSettingsDict['channelOwnerID'] = miscData.channelOwnerID
      jsonSettingsDict['channelOwnerName'] = miscData.channelOwnerName

      #Encoding
      allowedEncodingModes = ['utf-8', 'utf-16', 'utf-32', 'rtfunicode']
      if config['json_encoding'] in allowedEncodingModes:
        jsonSettingsDict['encoding'] = config['json_encoding']

    elif config['json_log'] == False:
      jsonLogging = False
    else:
      print("Invalid value for 'json_log' in config file:  " + config['json_log'])
      print("Defaulting to False (no json log file will be created)")
      jsonLogging = False

    if config['json_extra_data'] == True:
      jsonSettingsDict['json_extra_data'] = True
    elif config['json_extra_data'] == False:
      jsonSettingsDict['json_extra_data'] = False
    
    if config['json_profile_picture'] != False:
      jsonSettingsDict['json_profile_picture'] = config['json_profile_picture']
      jsonSettingsDict['logTime'] = current.logTime
    elif config['json_profile_picture'] == False:
      jsonSettingsDict['json_profile_picture'] = False

  except KeyError:
    print("Problem getting json settings, is your config file correct?")

  # Set where to put log files
  defaultLogPath = "logs"
  if config['log_path']:
    if config['log_path'] == "default": # For backwards compatibility, can remove later on
      logPath = defaultLogPath
    else:
      logPath = config['log_path']
    current.logFileName = os.path.normpath(logPath + "/" + fileName)
    print(f"Log file will be located at {F.YELLOW}" + current.logFileName + f"{S.R}\n")
    if jsonLogging == True:
      jsonLogFileName = os.path.normpath(logPath + "/" + jsonLogFileName)
      jsonSettingsDict['jsonLogFileName'] = jsonLogFileName
      print(f"JSON log file will be located at {F.YELLOW}" + jsonLogFileName + f"{S.R}\n")
  else:
    current.logFileName = os.path.normpath(defaultLogPath + "/" + fileName)
    print(f"Log file will be called {F.YELLOW}" + current.logFileName + f"{S.R}\n")

  if bypass == False:
    input(f"Press {F.YELLOW}Enter{S.R} to display comments...")

  # Write heading info to log file
  write_log_heading(current, logMode, filtersDict)

  jsonSettingsDict['jsonLogging'] = jsonLogging

  return current, logMode, jsonSettingsDict

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def write_log_heading(current, logMode, filtersDict, afterExclude=False, combinedCommentsDict=None):
  if combinedCommentsDict == None:
    combinedCommentsDict = dict(current.matchedCommentsDict)
    combinedCommentsDict.update(current.spamThreadsDict)
    combinedCommentsDict.update(current.duplicateCommentsDict)

  filterMode = filtersDict['filterMode']
  inputtedSpammerChannelID = filtersDict['CustomChannelIdFilter']
  inputtedUsernameFilter = filtersDict['CustomUsernameFilter']
  inputtedCommentTextFilter = filtersDict['CustomCommentTextFilter']
  filterSettings = filtersDict['filterSettings']

  def write_func(logFileName, string, logMode, numLines):
    rtfLineEnd = ("\\line"*numLines) + " "
    newLines = "\n"*numLines # Just the amount of new lines to put for this line
    if logMode == "rtf":
      write_rtf(logFileName, make_rtf_compatible(string) + rtfLineEnd)
    elif logMode == "plaintext":
      write_plaintext_log(logFileName, string + newLines)

  # Creates log file and writes first line
  if logMode == "rtf":
    write_rtf(current.logFileName, firstWrite=True)
    write_func(current.logFileName, "----------- YouTube Spammer Purge Log File -----------", logMode, 2)
  elif logMode == "plaintext":
    write_plaintext_log(current.logFileName, firstWrite=True)
    write_func(current.logFileName, "----------- YouTube Spammer Purge Log File -----------", logMode, 2)

  if filterMode == "ID":
    write_func(current.logFileName, "Channel IDs of spammer searched: " + ", ".join(inputtedSpammerChannelID), logMode, 2)
  elif filterMode == "Username":
    write_func(current.logFileName, "Characters searched in Usernames: " + ", ".join(inputtedUsernameFilter), logMode, 2)
  elif filterMode == "Text":
    write_func(current.logFileName, "Characters searched in Comment Text: " + ", ".join(inputtedCommentTextFilter), logMode, 2)
  elif filterMode == "NameAndText":
    write_func(current.logFileName, "Characters searched in Usernames and Comment Text: " + ", ".join(inputtedCommentTextFilter), logMode, 2)
  elif filterMode == "AutoASCII":
    write_func(current.logFileName, "Automatic Search Mode: " + str(filterSettings[1]), logMode, 2)
  elif filterMode == "AutoSmart":
    write_func(current.logFileName, "Automatic Search Mode: Smart Mode ", logMode, 2)
  elif filterMode == "SensitiveSmart":
    write_func(current.logFileName, "Automatic Search Mode: Sensitive Smart ", logMode, 2)
  
  # Write number of comments for each type
  write_func(current.logFileName, "Number of Matched Comments Found: " + str(len(current.matchedCommentsDict)), logMode, 2)
  write_func(current.logFileName, "Number of Spam Bot Threads Found: " + str(len(current.spamThreadsDict)), logMode, 2)
  write_func(current.logFileName, "Number of Non-Matched, but Duplicate Comments Found: " + str(len(current.duplicateCommentsDict)), logMode, 2)
  
  # How to label the comment ID list
  if current.duplicateCommentsDict:
    commentListLabel = "IDs of Matched & Duplicate Comments"
  else:
    commentListLabel = "IDs of Matched Comments"

  if afterExclude == True:
    excludeString = " (Excluded Comments Removed)"
  else:
    excludeString = ""
    
  write_func(current.logFileName, f"{commentListLabel}{excludeString}: \n[ {', '.join(combinedCommentsDict)} ] ", logMode, 3)
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def write_log_completion_summary(current, exclude, logMode, banChoice, deletionModeFriendlyName, removeOtherAuthorComments):
  if logMode == "rtf":
    write_rtf(current.logFileName, "\n\n\\line\\line Spammers Banned: " + str(banChoice))
    write_rtf(current.logFileName, "\n\n\\line\\line Action Taken on Comments: " + str(deletionModeFriendlyName) + " \\line\\line \n\n")
    write_rtf(current.logFileName, "\n\n\\line\\line Also Retrieved All Other Comments by Matched Authors: " + str(removeOtherAuthorComments) + " \\line\\line \n\n")

  elif logMode == "plaintext":
    write_plaintext_log(current.logFileName, "\n\nSpammers Banned: " + str(banChoice) + "\n\n")
    write_plaintext_log(current.logFileName, "Action Taken on Comments: " + str(deletionModeFriendlyName) + "\n\n")
    write_plaintext_log(current.logFileName, "Also Retrieved All Other Comments by Matched Authors: " + str(removeOtherAuthorComments) + "\n\n")

# Re-Writes Log Files if authors excluded
def rewrite_log_file(current, logInfo, combinedCommentsDict=None):
  logMode = logInfo['logMode']
  logFileContents = logInfo['logFileContents']
  #jsonSettingsDict = logInfo['jsonSettingsDict']
  filtersDict = logInfo['filtersDict']

  # Rewrites the heading, which includes list of matched Comment IDs
  write_log_heading(current, logMode, filtersDict, afterExclude=True, combinedCommentsDict=combinedCommentsDict)

  # Rewrites the rest of the log file contents after the heading
  if logMode == "rtf":
    write_rtf(current.logFileName, logFileContents)
  elif logMode == "plaintext":
    write_plaintext_log(current.logFileName, logFileContents)

