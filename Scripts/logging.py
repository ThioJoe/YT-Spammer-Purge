#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Scripts.shared_imports import *
import Scripts.utils as utils
import Scripts.auth as auth

import rtfunicode
import os
import requests
import json


##########################################################################################
############################### PRINT SPECIFIC COMMENTS ##################################
##########################################################################################

# First prepared comments into segments of 50 to be submitted to API simultaneously
# Then uses print_prepared_comments() to print / log the comments
def print_comments(current, scanVideoID, comments, loggingEnabled, scanMode, logMode):
  j = 0 # Counting index when going through comments all comment segments
  groupSize = 2500 # Number of comments to process per iteration

  if len(comments) > groupSize:
    remainder = len(comments) % groupSize
    numDivisions = int((len(comments)-remainder)/groupSize)
    for i in range(numDivisions):
      j = print_prepared_comments(current, scanVideoID,comments[i*groupSize:i*groupSize+groupSize], j, loggingEnabled, scanMode, logMode)
    if remainder > 0:
      j = print_prepared_comments(current, scanVideoID,comments[numDivisions*groupSize:len(comments)],j, loggingEnabled, scanMode, logMode)
  else:
    j = print_prepared_comments(current, scanVideoID,comments, j, loggingEnabled, scanMode, logMode)

  # Print Sample Match List
  valuesPreparedToWrite = ""
  valuesPreparedToPrint = ""
  print(f"{F.LIGHTMAGENTA_EX}---------------------------- Match Samples: One comment per matched-comment author ----------------------------{S.R}")
  for value in current.matchSamplesDict.values():
    if loggingEnabled == True and logMode == "rtf":
      valuesPreparedToWrite = valuesPreparedToWrite + value['iString'] + value['cString'] + f"{str(value['authorID'])} | {make_rtf_compatible(str(value['nameAndText']))} \\line \n"
    elif loggingEnabled == True and logMode == "plaintext":
      valuesPreparedToWrite = valuesPreparedToWrite + value['iString'] + value['cString'] + f"{str(value['authorID'])} | {str(value['nameAndText'])}\n"
    valuesPreparedToPrint = valuesPreparedToPrint + value['iString'] + value['cString'] + f"{str(value['nameAndText'])}\n"
  
  if loggingEnabled == True:
    if logMode == "rtf":
      write_rtf(current.logFileName, "-------------------- Match Samples: One comment per matched-comment author -------------------- \\line\\line \n")
      write_rtf(current.logFileName, valuesPreparedToWrite)
    elif logMode == "plaintext":
      write_plaintext_log(current.logFileName, "-------------------- Match Samples: One comment per matched-comment author --------------------\n")
      write_plaintext_log(current.logFileName, valuesPreparedToWrite)
  print(valuesPreparedToPrint)
  print(f"{F.LIGHTMAGENTA_EX}---------------------------- (See log file for channel IDs of matched authors above) ---------------------------{S.R}")

  return None

# Uses comments.list YouTube API Request to get text and author of specific set of comments, based on comment ID
def print_prepared_comments(current, scanVideoID, comments, j, loggingEnabled, scanMode, logMode):

  # Prints author and comment text for each comment
  i = 0 # Index when going through comments
  dataPreparedToWrite = ""

  for comment in comments:
    metadata = current.matchedCommentsDict[comment]

    # For printing and regular logging
    text = metadata['text']
    author = metadata['authorName']
    author_id_local = metadata['authorID']
    comment_id_local = comment
    videoID = metadata['videoID']
   
    # Truncates very long comments, and removes excessive multiple lines
    if len(text) > 1500:
      text = text[0:1500] + "[Comment Truncated by YT SPammer Purge]"
    if text.count("\n") > 0:
      text = text.replace("\n", " ")

    # Add one sample from each matching author to current.matchSamplesDict, containing author ID, name, and text
    if author_id_local not in current.matchSamplesDict.keys():
      add_sample(current, author_id_local, author, text)

    # Build comment direct link
    if scanMode == "communityPost":
      directLink = "https://www.youtube.com/post/" + videoID + "?lc=" + comment_id_local
    else:
      directLink = "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comment_id_local

    # Prints comment info to console
    print(str(j+1) + f". {F.LIGHTCYAN_EX}" + author + f"{S.R}:  {F.YELLOW}" + text + f"{S.R}")
    print("—————————————————————————————————————————————————————————————————————————————————————————————")
    if scanVideoID is None:  # Only print video title if searching entire channel
      title = utils.get_video_title(current, videoID) # Get Video Title
      print("     > Video: " + title)
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
          + titleInfoLine
          + "     > Direct Link: " + directLink + "\\line "+ "\n"
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
          + titleInfoLine
          + "     > Direct Link: " + directLink + "\n"
          + "     > Author Channel ID: " + author_id_local + "\n"
          + "=============================================================================================\n\n\n"
        )
      dataPreparedToWrite = dataPreparedToWrite + commentInfo

    # Appends comment ID to new list of comments so it's in the correct order going forward, as provided by API and presented to user
    # Must use append here, not extend, or else it would add each character separately
    i += 1
    j += 1

  if loggingEnabled == True:
    print(" Writing to log file, please wait...", end="\r")
    if logMode == "rtf":
      write_rtf(current.logFileName, dataPreparedToWrite)
    elif logMode == "plaintext":
      write_plaintext_log(current.logFileName, dataPreparedToWrite)
    print("                                    ")

  return j


############################ RTF & Log File Handling ###############################

# Takes in a string that contains unicode, and returns a string with properly escaped unicode format for use in rtf files
# Uses 'rtfunicode' module to encode with proper rtf-compatible unicode escapes, then decode back to utf-8 so it can be written to file and read by wordpad or whatever
def make_rtf_compatible(text):
  return text.encode('rtfunicode').decode('utf-8')

# Writes properly to rtf file, also can prepare with necessary header information and formatting settings
def write_rtf(fileName, newText=None, firstWrite=False):
  if firstWrite == True:
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

    file = open(fileName, "w", encoding="utf-8") # Opens log file in write mode
    # Some header information for RTF file, sets courier as font
    file.write(r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Courier;}}"+"\n")

    # Sets color table to be able to set colors for text, each color set with RGB values in raw string
    # To use color, use '\cf1 ' (with space) for black, cf2 = red, cf3 = green, cf4 = blue, cf5 = orange, cf6 = purple
    #                       cf1                cf2                  cf3                  cf4                  cf5                    cf6                 
    file.write(r"{\colortbl;\red0\green0\blue0;\red255\green0\blue0;\red0\green255\blue0;\red0\green0\blue255;\red143\green81\blue0;\red102\green0\blue214;}"+"\n\n")
    file.write(r"}")
    file.close()

  # If the string might have unicode, use unicode mode to convert for rtf
  else:
    # Writes to line just before last, to preserve required ending bracket in rtf file
    # Slightly modified from: https://stackoverflow.com/a/50567967/17312053   
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

############################ Plaintext Log & File Handling ###############################

def write_plaintext_log(fileName, newText=None, firstWrite=False):
  if firstWrite == True:
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
    with open(fileName, "w", encoding="utf-8") as file:
      file.write("")
      file.close()
  else:
    with open(fileName, 'a', encoding="utf-8") as file:
      for line in newText:
        file.write(line)
      file.close()

############################ JSON Log & File Handling ###############################
def write_json_log(jsonSettingsDict, dictionaryToWrite, firstWrite=True):
  fileName = jsonSettingsDict['jsonLogFileName']
  jsonEncoding = jsonSettingsDict['encoding']
  if firstWrite == True:
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
    with open(fileName, "w", encoding=jsonEncoding) as file:
      file.write(json.dumps(dictionaryToWrite, indent=4, ensure_ascii=False))
      file.close()

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

  print("\nFetching Profile Pictures...")
  # Download and save pictures
  try:
    for channelID, pictureURL in pictureUrlsDict.items():
      filedownload = requests.get(pictureURL, stream=True)
      downloadFileName = channelID + ".jpg"
      # Make absolute path
      downloadFileName = os.path.join(imageFolderPath, channelID + ".jpg")
      with open(downloadFileName, 'wb') as file:
        for data in filedownload.iter_content(block_size):
          file.write(data)
    print("Successfully downloaded profile pictures.")
  except:
    return False



# Adds a sample to current.matchSamplesDict and preps formatting
def add_sample(current, authorID, authorNameRaw, commentText):

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

  if len(commentText) > 82:
    commentText = commentText[0:79] + "..."
  commentText = commentText[0:82].ljust(82)

  # Add comment sample, author ID, name, and counter
  current.matchSamplesDict[authorID] = {'index':index, 'cString':cString, 'iString':iString, 'count':authorNumComments, 'authorID':authorID, 'authorName':authorNameRaw, 'nameAndText':authorName + commentText}
