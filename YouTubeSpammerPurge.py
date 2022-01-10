#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#######################################################################################################
################################# YOUTUBE SPAM COMMENT DELETER ########################################
#######################################################################################################
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
###
### Function: Allows you to scan for spam comments with multiple methods, and delete them all at once
###
### Purpose:  Recently, there has been a massive infestation of spam on YouTube where fake impersonator
###           accounts leave spam/scam replies to hundreds of users on a creator's videos.
###           
###           For some god-forsaken reason, YouTube offers no way to delete all comments by a specific
###           user at once, meaning you must delete them one by one BY HAND.
###
###           YouTube offers a functionality to ban a user, but it does NOT delete previous comments.
###           Therefore I created this script to allow you to instantly purge their spam comments.
###
### NOTES:    1. To use this script, you will need to obtain your own API credentials file by making
###				       a project via the Google Developers Console (aka 'Google Cloud Platform').
###              The credential file should be re-named 'client_secret.json' and be placed in the 
###              same directory as this script.
###				            >>> See the Readme for instructions on this.
###
###           2. I suck at programming so if something doesn't work I'll try to fix it but might not
###              even know how, so don't expect too much.
###
### Author:   ThioJoe - YouTube.com/ThioJoe
###                     Twitter.com/ThioJoe
###
### GitHub:   https://github.com/ThioJoe/YT-Spammer-Purge/
###
### License:  GPL-3.0
###
### IMPORTANT:  I OFFER NO WARRANTY OR GUARANTEE FOR THIS SCRIPT. USE AT YOUR OWN RISK.
###             I tested it on my own and implemented some failsafes as best as I could,
###             but there could always be some kind of bug. You should inspect the code yourself.
version = "2.10.0-Beta1"
configVersion = 17
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# GUI Related
from gui import *

# Standard Libraries
import io
import os
import re
import sys
import time
import ast
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from collections import namedtuple
import traceback
import platform
import requests
import json
from base64 import b85decode as b64decode
from configparser import ConfigParser
from pkg_resources import parse_version
import unicodedata
import hashlib
from itertools import islice
import zipfile
from shutil import copyfile
from random import randrange

# Non Standard Modules
import rtfunicode
from colorama import init, Fore as F, Back as B, Style as S
from confusables import confusable_regex, normalize

# Local Non Standard Modules
from community_downloader import main as get_community_comments #Args = post's ID, comment limit
from community_downloader import get_post_channel_url

# Google Authentication Modules
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


##########################################################################################
################################## AUTHORIZATION #########################################
##########################################################################################
# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets

# Authorize the request and store authorization credentials.
def get_authenticated_service():
  global TOKEN_FILE_NAME
  TOKEN_FILE_NAME = 'token.pickle'
  CLIENT_SECRETS_FILE = 'client_secrets.json'
  YOUTUBE_READ_WRITE_SSL_SCOPE = ['https://www.googleapis.com/auth/youtube.force-ssl']
  API_SERVICE_NAME = 'youtube'
  API_VERSION = 'v3'
  DISCOVERY_SERVICE_URL = "https://youtube.googleapis.com/$discovery/rest?version=v3" # If don't specify discovery URL for build, works in python but fails when running as EXE

  # Check if client_secrets.json file exists, if not give error
  if not os.path.exists(CLIENT_SECRETS_FILE):
    print(f"\n         ----- {F.WHITE}{B.RED}[!] Error:{S.R} client_secrets.json file not found -----")
    print(f" ----- Did you create a {F.YELLOW}Google Cloud Platform Project{S.R} to access the API? ----- ")
    print(f"  > For instructions on how to get an API key, visit: {F.YELLOW}www.TJoe.io/api-setup{S.R}")
    print(f"\n  > (Non-shortened Link: https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key)")
    input("\nPress Enter to Exit...")
    sys.exit()

  creds = None
  # The file token.pickle stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first time.
  if os.path.exists(TOKEN_FILE_NAME):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE_NAME, scopes=YOUTUBE_READ_WRITE_SSL_SCOPE)

  # If there are no (valid) credentials available, make the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      print(f"\nPlease {F.YELLOW}login using the browser window{S.R} that opened just now.\n")
      flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=YOUTUBE_READ_WRITE_SSL_SCOPE)
      creds = flow.run_local_server(port=0, authorization_prompt_message="Waiting for authorization. See message above.")
      print(f"{F.GREEN}[OK] Authorization Complete.{S.R}")
      # Save the credentials for the next run
    with open(TOKEN_FILE_NAME, 'w') as token:
      token.write(creds.to_json())
  return build(API_SERVICE_NAME, API_VERSION, credentials=creds, discoveryServiceUrl=DISCOVERY_SERVICE_URL)


############################ EXCEPTION MESSAGES ##########################################
def print_exception_reason(reason):
  print("    Reason: " + str(reason))
  if reason == "processingFailure":
    print(f"\n {F.LIGHTRED_EX}[!!] Processing Error{S.R} - Sometimes this error fixes itself. Try just running the program again. !!")
    print("This issue is often on YouTube's side, so if it keeps happening try again later.")
    print("(This also occurs if you try deleting comments on someone elses video, which is not possible.)")
  elif reason == "commentsDisabled":
    print(f"\n{F.LIGHTRED_EX}[!] Error:{S.R} Comments are disabled on this video. This error can also occur if scanning a live stream.")
  elif reason == "quotaExceeded":
    print(f"\n{F.LIGHTRED_EX}Error:{S.R} You have exceeded the YouTube API quota. To do more scanning you must wait until the quota resets.")
    print(" > There is a daily limit of 10,000 units/day, which works out to around reporting 10,000 comments/day.")
    print(" > You can check your quota by searching 'quota' in the google cloud console.")
    print(f"{F.YELLOW}Solutions: Either wait until tomorrow, or create additional projects in the cloud console.{S.R}")
    print(f"  > Read more about the quota limits for this app here: {F.YELLOW}TJoe.io/api-limit-info{S.R}")
    input("\n Press Enter to Exit...")

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
      title = get_video_title(current, videoID) # Get Video Title
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


##########################################################################################
############################## GET COMMENT THREADS #######################################
##########################################################################################

# Call the API's commentThreads.list method to list the existing comments.
def get_comments(current, filtersDict, miscData, config, scanVideoID=None, nextPageToken=None, videosToScan=None):  # None are set as default if no parameters passed into function
  # Initialize some variables
  authorChannelName = None
  commentText = None
  parentAuthorChannelID = None

  fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/replies/comments,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/authorDisplayName,items/snippet/topLevelComment/snippet/textDisplay"

  # Gets all comment threads for a specific video
  if scanVideoID is not None:
    results = YOUTUBE.commentThreads().list(
      part="snippet, replies",
      videoId=scanVideoID, 
      maxResults=100,
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()
  
  # Get all comment threads across the whole channel
  elif scanVideoID is None:
    results = YOUTUBE.commentThreads().list(
      part="snippet, replies",
      allThreadsRelatedToChannelId=CURRENTUSER.id,
      maxResults=100,
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()  
    
  # Get token for next page. If no token, sets to 'End'
  RetrievedNextPageToken = results.get("nextPageToken", "End")
  
  # After getting all comments threads for page, extracts data for each and stores matches in current.matchedCommentsDict
  # Also goes through each thread and executes get_replies() to get reply content and matches
  for item in results["items"]:
    comment = item["snippet"]["topLevelComment"]
    videoID = comment["snippet"]["videoId"] # Only enable if NOT checking specific video
    parent_id = item["snippet"]["topLevelComment"]["id"]
    numReplies = item["snippet"]["totalReplyCount"]

    # On rare occasions a comment will be there but the channel name will be empty, so this allows placeholders
    try:
      limitedRepliesList = item["replies"]["comments"] # API will return a limited number of replies (~5), but to get all, need to make separate call
    except KeyError:
      limitedRepliesList = []
      pass
    try: 
      parentAuthorChannelID = comment["snippet"]["authorChannelId"]["value"]
    except KeyError:
      parentAuthorChannelID = "[Deleted Channel]"

    # Need to be able to catch exceptions because sometimes the API will return a comment from non-existent / deleted channel
    try:
      authorChannelName = comment["snippet"]["authorDisplayName"].replace("\r", " ")
    except KeyError:
      authorChannelName = "[Deleted Channel]"
    try:
      commentText = comment["snippet"]["textDisplay"].replace("\r","") # Remove Return carriages
    except KeyError:
      commentText = "[Deleted/Missing Comment]"
    
    # Runs check against comment info for whichever filter data is relevant
    currentCommentDict = {
      'authorChannelID':parentAuthorChannelID, 
      'parentAuthorChannelID':None, 
      'authorChannelName':authorChannelName, 
      'commentText':commentText,
      'commentID':parent_id,
      }
    check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID)
    current.scannedCommentsCount += 1
    
    if numReplies > 0 and len(limitedRepliesList) < numReplies:
      get_replies(current, filtersDict, miscData, config, parent_id, videoID, parentAuthorChannelID, videosToScan)
    elif numReplies > 0 and len(limitedRepliesList) == numReplies: # limitedRepliesList can never be more than numReplies
      get_replies(current, filtersDict, miscData, config, parent_id, videoID, parentAuthorChannelID, videosToScan, repliesList=limitedRepliesList)
    else:
      print_count_stats(current, miscData, videosToScan, final=False)  # Updates displayed stats if no replies

  return RetrievedNextPageToken


##########################################################################################
##################################### GET REPLIES ########################################
##########################################################################################

# Call the API's comments.list method to list the existing comment replies.
def get_replies(current, filtersDict, miscData, config, parent_id, videoID, parentAuthorChannelID, videosToScan, repliesList=None):
  # Initialize some variables
  authorChannelName = None
  commentText = None
  
  if repliesList == None:
    fieldsToFetch = "items/snippet/authorChannelId/value,items/id,items/snippet/authorDisplayName,items/snippet/textDisplay"

    results = YOUTUBE.comments().list(
      part="snippet",
      parentId=parent_id,
      maxResults=100,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()

    replies = results["items"]
  else:
    replies = repliesList
 
  # Create list of author names in current thread, add into list - Only necessary when scanning comment text
  allThreadAuthorNames = []

  # Iterates through items in results
  # Need to be able to catch exceptions because sometimes the API will return a comment from non-existent / deleted channel
  # Need individual tries because not all are fetched for each mode
  for reply in replies:  
    replyID = reply["id"]
    try:
      authorChannelID = reply["snippet"]["authorChannelId"]["value"]
    except KeyError:
      authorChannelID = "[Deleted Channel]"

    # Get author display name
    try:
      authorChannelName = reply["snippet"]["authorDisplayName"]
      if filtersDict['filterMode'] == "Username" or filtersDict['filterMode'] == "AutoASCII" or filtersDict['filterMode'] == "AutoSmart" or filtersDict['filterMode'] == "NameAndText":
        allThreadAuthorNames.append(authorChannelName)
    except KeyError:
      authorChannelName = "[Deleted Channel]"
    
    # Comment Text
    try:
      commentText = reply["snippet"]["textDisplay"] # Remove Return carriages
    except KeyError:
      commentText = "[Deleted/Missing Comment]"

    # Runs check against comment info for whichever filter data is relevant
    currentCommentDict = {
      'authorChannelID':authorChannelID, 
      'parentAuthorChannelID':parentAuthorChannelID, 
      'authorChannelName':authorChannelName, 
      'commentText':commentText,
      'commentID':replyID,
      }
    check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID, allThreadAuthorNames=allThreadAuthorNames)

    # Update latest stats
    current.scannedRepliesCount += 1 
    print_count_stats(current, miscData, videosToScan, final=False)

  return True

############################## CHECK AGAINST FILTER ######################################
# The basic logic that actually checks each comment against filter criteria
def check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID, allThreadAuthorNames=None):
  # Retrieve Data from currentCommentDict
  commentID = currentCommentDict['commentID']
  authorChannelName = currentCommentDict['authorChannelName']
  authorChannelID = currentCommentDict['authorChannelID']
  parentAuthorChannelID = currentCommentDict['parentAuthorChannelID']
  commentTextRaw = str(currentCommentDict['commentText']) # Use str() to ensure not pointing to same place in memory
  commentText = str(currentCommentDict['commentText']).replace("\r", "")

  debugSingleComment = False #Debug usage
  if debugSingleComment == True:
    authorChannelName = input("Channel Name: ")
    commentText = input("Comment Text: ")
    authorChannelID = "x"

  # Do not even check comment if: Author is Current User, Author is Channel Owner, or Author is in whitelist
  if CURRENTUSER.id != authorChannelID and miscData['channelOwnerID'] != authorChannelID and authorChannelID not in miscData['Resources']['Whitelist']['WhitelistContents']:
    if "@" in commentText:
      # Logic to avoid false positives from replies to spammers
      if allThreadAuthorNames and (filtersDict['filterMode'] == "AutoSmart" or filtersDict['filterMode'] == "NameAndText"):
        for name in allThreadAuthorNames:
          if "@"+str(name) in commentText:
            commentText = commentText.replace("@"+str(name), "")
      # Extra logic to detect false positive if spammer's comment already deleted, but someone replied
      if current.matchedCommentsDict and filtersDict['filterMode'] == "AutoSmart":
        for key, value in current.matchedCommentsDict.items():
          if "@"+str(value['authorName']) in commentText:
            remove = True
            for key2,value2 in current.matchedCommentsDict.items():
              if value2['authorID'] == authorChannelID:
                remove = False
            if remove == True:
              commentText = commentText.replace("@"+str(value['authorName']), "")

    # If the comment/username matches criteria based on mode, add key/value pair of comment ID and author ID to current.matchedCommentsDict
    # Also add key-value pair of comment ID and video ID to dictionary
    # Also count how many spam comments for each author
    def add_spam(commentID, videoID):
      current.matchedCommentsDict[commentID] = {'text':commentText, 'textUnsanitized':commentTextRaw, 'authorName':authorChannelName, 'authorID':authorChannelID, 'videoID':videoID}
      current.vidIdDict[commentID] = videoID # Probably remove this later, but still being used for now
      if authorChannelID in current.authorMatchCountDict:
        current.authorMatchCountDict[authorChannelID] += 1
      else:
        current.authorMatchCountDict[authorChannelID] = 1
      if config and config['json_log'] == True and config['json_extra_data'] == True:
        current.matchedCommentsDict[commentID]['uploaderChannelID'] = miscData['channelOwnerID']
        current.matchedCommentsDict[commentID]['uploaderChannelName'] = miscData['channelOwnerName']
        current.matchedCommentsDict[commentID]['videoTitle'] = get_video_title(current, videoID)
        
      if debugSingleComment == True: 
        input("--- Yes, Matched -----")

    # Checks author of either parent comment or reply (both passed in as commentID) against channel ID inputted by user
    if filtersDict['filterMode'] == "ID":
      if any(authorChannelID == x for x in filtersDict['CustomChannelIdFilter']):
        add_spam(commentID, videoID)

    # Check Modes: Username
    elif filtersDict['filterMode'] == "Username":
      if filtersDict['filterSubMode'] == "chars":
        authorChannelName = make_char_set(str(authorChannelName))
        if any(x in filtersDict['CustomUsernameFilter'] for x in authorChannelName):
          add_spam(commentID, videoID)
      elif filtersDict['filterSubMode'] == "string":
        if check_list_against_string(listInput=filtersDict['CustomUsernameFilter'], stringInput=authorChannelName, caseSensitive=False):
          add_spam(commentID, videoID)
      elif filtersDict['filterSubMode'] == "regex":
        if re.search(str(filtersDict['CustomRegexPattern']), authorChannelName):
          add_spam(commentID, videoID)

    # Check Modes: Comment Text
    elif filtersDict['filterMode'] == "Text":
      if filtersDict['filterSubMode'] == "chars":
        commentText = make_char_set(str(commentText))
        if any(x in filtersDict['CustomCommentTextFilter'] for x in commentText):
          add_spam(commentID, videoID)
      elif filtersDict['filterSubMode'] == "string":
        if check_list_against_string(listInput=filtersDict['CustomCommentTextFilter'], stringInput=commentText, caseSensitive=False):
          add_spam(commentID, videoID)
      elif filtersDict['filterSubMode'] == "regex":
        if re.search(str(filtersDict['CustomRegexPattern']), commentText):
          add_spam(commentID, videoID)

    # Check Modes: Name and Text
    elif filtersDict['filterMode'] == "NameAndText":
      if filtersDict['filterSubMode'] == "chars":
        authorChannelName = make_char_set(str(authorChannelName))
        commentText = make_char_set(str(commentText))
        if any(x in filtersDict['CustomUsernameFilter'] for x in authorChannelName):
          add_spam(commentID, videoID)
        elif any(x in filtersDict['CustomCommentTextFilter'] for x in commentText):
          add_spam(commentID, videoID)
      elif filtersDict['filterSubMode'] == "string":
        if check_list_against_string(listInput=filtersDict['CustomUsernameFilter'], stringInput=authorChannelName, caseSensitive=False):
          add_spam(commentID, videoID)
        elif check_list_against_string(listInput=filtersDict['CustomCommentTextFilter'], stringInput=commentText, caseSensitive=False):
          add_spam(commentID, videoID)
      elif filtersDict['filterSubMode'] == "regex":
        if re.search(str(filtersDict['CustomRegexPattern']), authorChannelName):
          add_spam(commentID, videoID)
        elif re.search(str(filtersDict['CustomRegexPattern']), commentText):
          add_spam(commentID, videoID)

    # Check Modes: Auto ASCII (in username)
    elif filtersDict['filterMode'] == "AutoASCII":
      if re.search(str(filtersDict['CustomRegexPattern']), authorChannelName):
        add_spam(commentID, videoID)

    # Check Modes: Auto Smart (in username or comment text)
    # Here inputtedComment/Author Filters are tuples of, where 2nd element is list of char-sets to check against
    ## Also Check if reply author ID is same as parent comment author ID, if so, ignore (to account for users who reply to spammers)
    elif filtersDict['filterMode'] == "AutoSmart" or filtersDict['filterMode'] == "SensitiveSmart":
      smartFilter = filtersDict['CustomCommentTextFilter']
      # Receive Variables
      compiledRegexDict = smartFilter['compiledRegexDict']
      numberFilterSet = smartFilter['spammerNumbersSet']
      compiledRegex = smartFilter['compiledRegex']
      minNumbersMatchCount = smartFilter['minNumbersMatchCount']
      #usernameBlackCharsSet = smartFilter['usernameBlackCharsSet']
      spamGenEmojiSet = smartFilter['spamGenEmojiSet']
      redAdEmojiSet = smartFilter['redAdEmojiSet']
      yellowAdEmojiSet = smartFilter['yellowAdEmojiSet']
      hrtSet = smartFilter['hrtSet']
      languages = smartFilter['languages']
      sensitive =  smartFilter['sensitive']
      rootDomainRegex = smartFilter['rootDomainRegex']
      # Spam Lists
      spamDomainsRegex = smartFilter['spamListsRegex']['spamDomainsRegex']
      spamAccountsRegex = smartFilter['spamListsRegex']['spamAccountsRegex']
      spamThreadsRegex = smartFilter['spamListsRegex']['spamThreadsRegex']
      

      if debugSingleComment == True: 
        if input("Sensitive True/False: ").lower() == 'true': sensitive = True
        else: sensitive = False

      # Check for sensitive smart mode  
      if sensitive == True:
        rootDomainRegex = smartFilter['sensitiveRootDomainRegex']

      # Processed Variables
      combinedString = authorChannelName + commentText
      combinedSet = make_char_set(combinedString, stripLettersNumbers=True, stripPunctuation=True)
      usernameSet = make_char_set(authorChannelName)

      # Functions --------------------------------------------------------------
      def findOnlyObfuscated(regexExpression, originalWord, stringToSearch):
        # Confusable thinks s and f look similar, have to compensate to avoid false positive
        ignoredConfusablesConverter = {ord('f'):ord('s'),ord('s'):ord('f')} 
        result = re.findall(regexExpression, stringToSearch.lower())  
        if result == None:
          return False
        else:
          for match in result:
            lowerWord = originalWord.lower()
            if match.lower() != lowerWord and match.lower() != lowerWord.translate(ignoredConfusablesConverter):
              return True

      def remove_unicode_categories(string):
        return "".join(char for char in string if unicodedata.category(char) not in smartFilter['unicodeCategoriesStrip'])
      
      def check_if_only_a_link(string):
        result = re.match(compiledRegexDict['onlyVideoLinkRegex'], string)
        if result == None:
          return False
        elif result.group(0) and len(result.group(0)) == len(string):
          return True
        else:
          return False

      # Check all spam lists
      def check_spam_lists(spamDomainsRegex, spamAccountsRegex, spamThreadsRegex):
        if any(re.search(expression, combinedString) for expression in spamDomainsRegex):
          return True
        elif any(re.search(expression, combinedString) for expression in spamAccountsRegex):
          return True
        elif any(re.search(expression, combinedString) for expression in spamThreadsRegex):
          return True
        else:
          return False

      # ------------------------------------------------------------------------

      # Normalize usernames and text, remove multiple whitespace and invisible chars
      combinedString = re.sub(' +', ' ',combinedString)
      combinedString = remove_unicode_categories(combinedString)
      authorChannelName = re.sub(' +', ' ', authorChannelName)
      authorChannelName = remove_unicode_categories(authorChannelName)
      commentText = re.sub(' +', ' ', commentText)
      commentText = remove_unicode_categories(commentText)

      # Run Checks
      if authorChannelID == parentAuthorChannelID:
        pass
      elif len(numberFilterSet.intersection(combinedSet)) >= minNumbersMatchCount:
        add_spam(commentID, videoID)
      elif compiledRegex.search(combinedString):
        add_spam(commentID, videoID)
      # Black Tests
        #elif usernameBlackCharsSet.intersection(usernameSet):
        #  add_spam(commentID, videoID)
      elif any(re.search(expression[1], authorChannelName) for expression in compiledRegexDict['usernameBlackWords']):
        add_spam(commentID, videoID)
      elif any(findOnlyObfuscated(expression[1], expression[0], combinedString) for expression in compiledRegexDict['blackAdWords']):
        add_spam(commentID, videoID)
      elif any(findOnlyObfuscated(expression[1], expression[0], commentText) for expression in compiledRegexDict['textObfuBlackWords']):
        add_spam(commentID, videoID)
      elif any(findOnlyObfuscated(expression[1], expression[0], authorChannelName) for expression in compiledRegexDict['usernameObfuBlackWords']):
        add_spam(commentID, videoID)
      elif check_spam_lists(spamDomainsRegex, spamAccountsRegex, spamThreadsRegex) == True:
        add_spam(commentID, videoID)
      elif check_if_only_a_link(commentText.strip()):
        add_spam(commentID, videoID)
      elif sensitive == True and re.search(smartFilter['usernameConfuseRegex'], authorChannelName):
        add_spam(commentID, videoID)
      elif sensitive == False and findOnlyObfuscated(smartFilter['usernameConfuseRegex'], miscData['channelOwnerName'], authorChannelName):
        add_spam(commentID, videoID)
      # Multi Criteria Tests
      else:
        # Defaults
        yellowCount = 0
        redCount = 0
        
        languageCount = 0
        for language in languages:
          if language[2].intersection(combinedSet):
            languageCount += 1

        # Yellow Tests
        if any(findOnlyObfuscated(expression[1], expression[0], combinedString) for expression in compiledRegexDict['yellowAdWords']):
          yellowCount += 1

        hrtTest = len(hrtSet.intersection(combinedSet))
        if hrtTest >= 2:
          if sensitive == False:
            yellowCount += 1
          if sensitive == True:
            redCount += 1
        elif hrtTest >= 1 and sensitive == True:
          yellowCount += 1

        if yellowAdEmojiSet.intersection(combinedSet):
          yellowCount += 1

        if spamGenEmojiSet.intersection(combinedSet) and sensitive == False:
          yellowCount += 1

        if combinedString.count('#') >= 5:
          yellowCount += 1

        if combinedString.count('\n') >= 10:
          yellowCount += 1

        if languageCount >= 2:
          yellowCount += 1
          
        if re.search(rootDomainRegex, combinedString.lower()):
          yellowCount += 1

        # Red Tests
        #if any(foundObfuscated(re.findall(expression[1], combinedString), expression[0]) for expression in compiledRegexDict['redAdWords']):
        if any(findOnlyObfuscated(expression[1], expression[0], combinedString) for expression in compiledRegexDict['redAdWords']):
          redCount += 1

        if any(re.search(expression[1], combinedString) for expression in compiledRegexDict['exactRedAdWords']):
          redCount += 1

        if redAdEmojiSet.intersection(combinedSet):
          redCount += 1
        
        if spamGenEmojiSet.intersection(combinedSet) and sensitive == True:
          redCount += 1

        if any(re.search(expression[1], authorChannelName) for expression in compiledRegexDict['usernameRedWords']):
          redCount += 1

        # Calculate Score
        if yellowCount >= 3:
          add_spam(commentID, videoID)
        elif redCount >= 2:
          add_spam(commentID, videoID)
        elif redCount >= 1 and yellowCount >= 1:
          add_spam(commentID, videoID)
        elif redCount >= 1 and sensitive == True:
          add_spam(commentID, videoID)
  else:
    pass

##########################################################################################
################################ DELETE COMMENTS #########################################
########################################################################################## 

# Takes in list of comment IDs to delete, breaks them into 50-comment chunks, and deletes them in groups
def delete_found_comments(commentsList, banChoice, deletionMode, recoveryMode=False):
  print("\n")
  if deletionMode == "rejected":
    actionPresent = "Deleting"
    actionPast = "Deleted"
  elif deletionMode == "heldForReview":
    actionPresent = "Hiding"
    actionPast = "Hidden"
  elif deletionMode == "reportSpam":
    actionPresent = "Reporting"
    actionPast = "Reported"
  else:
    actionPresent = "Processing"
    actionPast = "Processed"

  # Local Functions 
  def setStatus(commentIDs): #Does the actual deletion
    if deletionMode == "reportSpam":
      result = YOUTUBE.comments().markAsSpam(id=commentIDs).execute()
      if len(result) > 0:
        print("\nSomething may gone wrong when reporting the comments.")    
    elif deletionMode == "heldForReview" or deletionMode == "rejected" or deletionMode == "published":
      YOUTUBE.comments().setModerationStatus(id=commentIDs, moderationStatus=deletionMode, banAuthor=banChoice).execute()
    else:
      print("Invalid deletion mode. This is definitely a bug, please report it here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
      print("Deletion Mode Is: " + deletionMode)
      input("Press Enter to Exit...")
      sys.exit()


  def print_progress(d, t, recoveryMode=False): 
    if recoveryMode == False:
      print(actionPresent +" Comments... - Progress: [" + str(d) + " / " + str(t) + "] (In Groups of 50)", end="\r")
    elif recoveryMode == True:
      print("Recovering Comments... - Progress: [" + str(d) + " / " + str(t) + "] (In Groups of 50)", end="\r")

  total = len(commentsList)
  deletedCounter = 0  
  print_progress(deletedCounter, total, recoveryMode)

  if total > 50:                                  # If more than 50 comments, break into chunks of 50
    remainder = total % 50                      # Gets how many left over after dividing into chunks of 50
    numDivisions = int((total-remainder)/50)    # Gets how many full chunks of 50 there are
    for i in range(numDivisions):               # Loops through each full chunk of 50
      setStatus(commentsList[i*50:i*50+50])
      deletedCounter += 50
      print_progress(deletedCounter, total, recoveryMode)
    if remainder > 0:
      setStatus(commentsList[numDivisions*50:total]) # Handles any leftover comments range after last full chunk
      deletedCounter += remainder
      print_progress(deletedCounter, total, recoveryMode)
  else:
      setStatus(commentsList)
      print_progress(deletedCounter, total, recoveryMode)
  if deletionMode == "reportSpam":
    print(f"{F.YELLOW}Comments Reported!{S.R} If no error messages were displayed, then everything was successful.")
  elif recoveryMode == False:
    print("Comments " + actionPast + "! Will now verify each is gone.                          \n")
  elif recoveryMode == True:
    print("Comments Recovered! Will now verify each is back.                          \n")

# Class for custom exception to throw if a comment is found to remain
class CommentFoundError(Exception):
    pass

# Takes in list of comment IDs and video IDs, and checks if comments still exist individually
def check_deleted_comments(checkDict):
    i = 0 # Count number of remaining comments
    j = 1 # Count number of checked
    total = len(checkDict)
    unsuccessfulResults = []

    # Wait 2 seconds so YouTube API has time to update comment status
    print("Preparing...", end="\r")
    time.sleep(1)
    print("                               ")
    print("    (Note: You can disable deletion success checking in the config file, to save time and API quota)\n")
    for commentID, metadata in checkDict.items():
      try:
        results = YOUTUBE.comments().list(
          part="snippet",
          id=commentID,  
          maxResults=1,
          fields="items",
          textFormat="plainText"
        ).execute()

        print("Verifying Deleted Comments: [" + str(j) + " / " + str(total) + "]", end="\r")
        j += 1

        if results["items"]:  # Check if the items result is empty
          raise CommentFoundError

      # If comment is found and possibly not deleted, print out video ID and comment ID
      except CommentFoundError:
        print("Possible Issue Deleting Comment: " + str(commentID) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(metadata['videoID']) + "&lc=" + str(commentID))
        i += 1
        unsuccessfulResults.append(results)
        pass
      except Exception:
        print("Unhandled Exception While Deleting Comment: " + str(commentID) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(metadata['videoID']) + "&lc=" + str(commentID))
        i += 1
        unsuccessfulResults.append(results)
        pass

    if i == 0:
      print("\n\nSuccess: All comments should be gone.")
    elif i > 0:
      print("\n\nWarning: " + str(i) + " comments may remain. Check links above or try running the program again. An error log file has been created: 'Deletion_Error_Log.txt'")
      # Write error log
      f = open("Deletion_Error_Log.txt", "a")
      f.write("----- YT Spammer Purge Error Log: Possible Issue Deleting Comments ------\n\n")
      f.write(str(unsuccessfulResults))
      f.write("\n\n")
      f.close()
    else:
      print("\n\nSomething strange happened... The comments may or may have not been deleted.")

    return None

# Class for custom exception to throw if a comment is found to remain
class CommentNotFoundError(Exception):
  pass

def check_recovered_comments(commentsList):
  i = 0 # Count number of remaining comments
  j = 1 # Count number of checked
  total = len(commentsList)
  unsuccessfulResults = []

  for comment in commentsList:
    try:
      results = YOUTUBE.comments().list(
        part="snippet",
        id=comment,  
        maxResults=1,
        fields="items",
        textFormat="plainText"
      ).execute()
      print("Verifying Deleted Comments: [" + str(j) + " / " + str(total) + "]", end="\r")
      j += 1

      if not results["items"]:  # Check if the items result is empty
        raise CommentNotFoundError

    except CommentNotFoundError:
      #print("Possible Issue Deleting Comment: " + str(key) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(value) + "&lc=" + str(key))
      print("Possible Issue Restoring Comment: " + str(comment))
      i += 1
      unsuccessfulResults.append(comment)
  
  if i == 0:
      print(f"\n\n{F.LIGHTGREEN_EX}Success: All spam comments should be restored!{S.R}")
      print("You can view them by using the links to them in the same log file you used.")

  elif i > 0:
    print("\n\nWarning: " + str(i) + " comments may have not been restored. See above list.")
    print("Use the links to the comments from the log file you used, to verify if they are back or not.")

  input("\nRecovery process finished. Press Enter to return to main menu...")
  return True

# Removes comments by user-selected authors from list of comments to delete
def exclude_authors(current, inputtedString, miscData):
  expression = r"(?<=exclude ).*" # Match everything after 'exclude '
  result = str(re.search(expression, inputtedString).group(0))
  result = result.replace(" ", "")
  SampleIDsToExclude = result.split(",")
  authorIDsToExclude = []
  displayString = ""
  excludedCommentsDict = {}
  rtfFormattedExcludes = ""
  plaintextFormattedExcludes = ""
  commentIDExcludeList = []

  # Get authorIDs for selected sample comments
  for authorID, info in current.matchSamplesDict.items():
    if str(info['index']) in SampleIDsToExclude:
      authorIDsToExclude += [authorID]

  # Get comment IDs to be excluded
  for comment, metadata in current.matchedCommentsDict.items():
    if metadata['authorID'] in authorIDsToExclude:
      commentIDExcludeList.append(comment)
  # Remove all comments by selected authors from dictionary of comments
  for comment in commentIDExcludeList:
    if comment in current.matchedCommentsDict.keys():
      excludedCommentsDict[comment] = current.matchedCommentsDict.pop(comment)

  # Create strings that can be used in log files
  rtfFormattedExcludes += f"Comments Excluded From Deletion: \\line \n"
  rtfFormattedExcludes += f"(Values = Comment ID | Author ID | Author Name | Comment Text) \\line \n"
  plaintextFormattedExcludes += f"Comments Excluded From Deletion:\n"
  plaintextFormattedExcludes += f"(Values = Comment ID | Author ID | Author Name | Comment Text)\n"
  for commentID, meta in excludedCommentsDict.items():
    rtfFormattedExcludes += f"{str(commentID)}  |  {str(excludedCommentsDict[commentID]['authorID'])}  |  {str(excludedCommentsDict[commentID]['authorName'])}  |   {str(excludedCommentsDict[commentID]['text'])} \\line \n"
  for commentID, meta in excludedCommentsDict.items():
    plaintextFormattedExcludes += f"{str(commentID)}  |  {str(excludedCommentsDict[commentID]['authorID'])}  |  {str(excludedCommentsDict[commentID]['authorName'])}  |   {str(excludedCommentsDict[commentID]['text'])}\n"

  # Verify removal
  for comment in current.matchedCommentsDict.keys():
    if comment in commentIDExcludeList:
      print(f"{F.LIGHTRED_EX}FATAL ERROR{S.R}: Something went wrong while trying to exclude comments. No comments have been deleted.")
      print(f"You should {F.YELLOW}DEFINITELY{S.R} report this bug here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
      print("Provide the error code: X-1")
      input("Press Enter to Exit...")
      sys.exit()
  
  # Get author names and IDs from dictionary, and display them
  for author in authorIDsToExclude:
    displayString += f"    User ID: {author}   |   User Name: {current.matchSamplesDict[author]['authorName']}\n"
    with open(miscData['Resources']['Whitelist']['PathWithName'], "a", encoding="utf-8") as f:
      f.write(f"# [Excluded]  Channel Name: {current.matchSamplesDict[author]['authorName']}  |  Channel ID: " + "\n")
      f.write(f"{author}\n")

  print(f"\n{F.CYAN}All {len(excludedCommentsDict)} comments{S.R} from the {F.CYAN}following {len(authorIDsToExclude)} users{S.R} are now {F.LIGHTGREEN_EX}excluded{S.R} from deletion:")
  print(displayString+"\n")
  input("Press Enter to decide what to do with the rest...")
  
  return excludedCommentsDict, rtfFormattedExcludes, plaintextFormattedExcludes # May use excludedCommentsDict later for printing them to log file

  

##########################################################################################
############################## UTILITY FUNCTIONS #########################################
########################################################################################## 

################################### GET VIDEO TITLE ###############################################
# Check if video title is in dictionary, if not get video title from video ID using YouTube API request, then return title
def get_video_title(current, video_id):
  if video_id in current.vidTitleDict.keys():
    title = current.vidTitleDict[video_id]
  else:
    results = YOUTUBE.videos().list(
      part="snippet",
      id=video_id,
      fields="items/snippet/title",
      maxResults=1
    ).execute()
    title = results["items"][0]["snippet"]["title"]
    current.vidTitleDict[video_id] = title

  return title

############################# GET CURRENTLY LOGGED IN USER #####################################
# Class for custom exception to throw if a comment if invalid channel ID returned
class ChannelIDError(Exception):
    pass
# Get channel ID and channel title of the currently authorized user
def get_current_user(config:dict) -> tuple[str, str, bool]:

  #Define fetch function so it can be re-used if issue and need to re-run it
  def fetch_user():
    results = YOUTUBE.channels().list(
      part="snippet", #Can also add "contentDetails" or "statistics"
      mine=True,
      fields="items/id,items/snippet/title"
    ).execute()
    return results
  results = fetch_user()

  # Fetch the channel ID and title from the API response
  # Catch exceptions if problems getting info
  if len(results) == 0: # Check if results are empty
    print("\n----------------------------------------------------------------------------------------")
    print(f"{F.YELLOW}Error Getting Current User{S.R}: The YouTube API responded, but did not provide a Channel ID.")
    print(f"{F.CYAN}Known Possible Causes:{S.R}")
    print("> The client_secrets file does not match user authorized with token.pickle file.")
    print("> You are logging in with a Google account that does not have a YouTube channel created yet.")
    print("> When choosing the account to log into, you selected the option showing the Google Account's email address, which might not have a channel attached to it.")
    input("\nPress Enter to try logging in again...")
    os.remove(TOKEN_FILE_NAME)

    global YOUTUBE
    YOUTUBE = get_authenticated_service()
    results = fetch_user() # Try again

  try:
    channelID = results["items"][0]["id"]
    IDCheck = validate_channel_id(channelID)
    if IDCheck[0] == False:
      raise ChannelIDError
    try:
      channelTitle = results["items"][0]["snippet"]["title"] # If channel ID was found, but not channel title/name
    except KeyError:
      print("Error Getting Current User: Channel ID was found, but channel title was not retrieved. If this occurs again, try deleting 'token.pickle' file and re-running. If that doesn't work, consider filing a bug report on the GitHub project 'issues' page.")
      print("> NOTE: The program may still work - You can try continuing. Just check the channel ID is correct: " + str(channelID))
      channelTitle = ""
      input("Press Enter to Continue...")
      pass
  except ChannelIDError:
    traceback.print_exc()
    print("\nError: Still unable to get channel info. Big Bruh Moment. Try deleting token.pickle. The info above might help if you want to report a bug.")
    print("Note: A channel ID was retrieved but is invalid: " + str(channelID))
    input("\nPress Enter to Exit...")
    sys.exit()
  except KeyError:
    traceback.print_exc()
    print("\nError: Still unable to get channel info. Big Bruh Moment. Try deleting token.pickle. The info above might help if you want to report a bug.")
    input("\nPress Enter to Exit...")
    sys.exit()
  
  if config == None:
    configMatch = None # Used only if channel ID is set in the config
  elif config and config['your_channel_id'] == "ask":
    configMatch = None
  elif validate_channel_id(config['your_channel_id'])[0] == True:
    if config['your_channel_id'] == channelID:
      configMatch = True
    else:
      print("Error: The channel ID in the config file appears to be valid, but does not match the channel ID of the currently logged in user.")
      input("Please check the config file. Press Enter to Exit...")
      sys.exit()
  else:
    print("Error: The channel ID in the config file appears to be invalid.")
    input("Please check the config file. Press Enter to Exit...")
    sys.exit()

  return channelID, channelTitle, configMatch

################################# Get Most Recent Videos #####################################
# Returns a list of lists
def get_recent_videos(channel_id, numVideosTotal):
  def get_block_of_videos(nextPageToken, j, numVideosBlock=5):
    result = YOUTUBE.search().list(
      part="snippet",
      channelId=channel_id,
      type='video',
      order='date',
      pageToken=nextPageToken,
      fields='nextPageToken,items/id/videoId,items/snippet/title',
      maxResults=numVideosBlock,
      ).execute()

    for item in result['items']:
      recentVideos.append({})
      videoID = str(item['id']['videoId'])
      videoTitle = str(item['snippet']['title']).replace("&quot;", "\"").replace("&#39;", "'")
      recentVideos[j]['videoID'] = videoID
      recentVideos[j]['videoTitle'] = videoTitle
      commentCount = validate_video_id(videoID)[3]
      if str(commentCount)=="MainMenu":
        return "MainMenu", None
      recentVideos[j]['commentCount'] = commentCount
      j+=1

    # Get token for next page
    try:
      nextPageToken = result['nextPageToken']
    except KeyError:
      nextPageToken = "End"
    
    return nextPageToken, j
    #----------------------------------------------------------------
  
  nextPageToken = None
  recentVideos = [] #List of dictionaries
  i = 0
  if numVideosTotal <=5:
    result = get_block_of_videos(None, j=i, numVideosBlock=numVideosTotal)
    if result[0] == "MainMenu":
      return "MainMenu"
  else:
    while nextPageToken != "End" and len(recentVideos) < numVideosTotal and str(nextPageToken[0]) != "MainMenu":
      print("Retrieved " + str(len(recentVideos)) + "/" + str(numVideosTotal) + " videos.", end="\r")
      remainingVideos = numVideosTotal - len(recentVideos)
      if remainingVideos <= 5:
        nextPageToken, i = get_block_of_videos(nextPageToken, j=i, numVideosBlock = remainingVideos)
      else:
        nextPageToken, i = get_block_of_videos(nextPageToken, j=i, numVideosBlock = 5)
      if str(nextPageToken[0]) == "MainMenu":
        return "MainMenu"
  print("                                          ")
  return recentVideos

##################################### PRINT STATS ##########################################

# Prints Scanning Statistics, can be version that overwrites itself or one that finalizes and moves to next line
def print_count_stats(current, miscData, videosToScan, final):
  # Use videosToScan (list of dictionaries) to retrieve total number of comments
  if videosToScan:
    totalComments = miscData['totalCommentCount']
    totalScanned = current.scannedRepliesCount + current.scannedCommentsCount
    percent = ((totalScanned / totalComments) * 100)
    progress = f"Total: [{str(totalScanned)}/{str(totalComments)}] ({percent:.0f}%) ".ljust(27, " ") + "|" #Formats percentage to 0 decimal places
  else:
    progress = ""
  
  comScanned = str(current.scannedCommentsCount)
  repScanned = str(current.scannedRepliesCount)
  matchCount = str(len(current.matchedCommentsDict))

  if final == True:
    print(f" {progress} Comments Scanned: {F.YELLOW}{comScanned}{S.R} | Replies Scanned: {F.YELLOW}{repScanned}{S.R} | Matches Found So Far: {F.LIGHTRED_EX}{matchCount}{S.R}\n")
  else:
    print(f" {progress} Comments Scanned: {F.YELLOW}{comScanned}{S.R} | Replies Scanned: {F.YELLOW}{repScanned}{S.R} | Matches Found So Far: {F.LIGHTRED_EX}{matchCount}{S.R}", end = "\r")
  
  return None

##################################### VALIDATE VIDEO ID #####################################
# Regex matches putting video id into a match group. Then queries youtube API to verify it exists - If so returns true and isolated video ID
def validate_video_id(video_url_or_id, silent=False):
    youtube_video_link_regex = r"^\s*(?P<video_url>(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube\.com|youtu.be)(?:\/(?:[\w\-]+\?v=|embed\/|v\/)?))?(?P<video_id>[\w\-]{11})(?:(?(video_url)\S+|$))?\s*$"
    match = re.match(youtube_video_link_regex, video_url_or_id)
    if match == None:
      if silent == False:
        print(f"\n{B.RED}{F.BLACK}Invalid Video link or ID!{S.R} Video IDs are 11 characters long.")
      return False, None, None, None, None
    else:
      try:
        possibleVideoID = match.group('video_id')
        result = YOUTUBE.videos().list(
          part="snippet,id,statistics",
          id=possibleVideoID,
          fields='items/id,items/snippet/channelId,items/snippet/channelTitle,items/statistics/commentCount,items/snippet/title',
          ).execute()
        if possibleVideoID == result['items'][0]['id']:
          channelID = result['items'][0]['snippet']['channelId']
          channelTitle = result["items"][0]["snippet"]["channelTitle"]
          videoTitle = result["items"][0]["snippet"]["title"]
          # When comments are disabled, the commentCount is not included in the response, requires catching KeyError
          try:
            commentCount = result['items'][0]['statistics']['commentCount']
          except KeyError:
            traceback.print_exc()
            print("--------------------------------------")
            print(f"\n{B.RED}{F.WHITE} ERROR: {S.R} {F.RED}Unable to get comment count for video: {S.R} {possibleVideoID}  |  {videoTitle}")
            print(f"\n{F.YELLOW}Are comments disabled on this video?{S.R} If not, please report the bug and include the error info above.")
            print(f"                    Bug Report Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
            input("\nPress Enter to return to the main menu...")
            return "MainMenu"

          return True, possibleVideoID, videoTitle, commentCount, channelID, channelTitle
        else:
          if silent == False:
            print("Something very odd happened. YouTube returned a video ID, but it is not equal to what was queried!")
          return False, None, None, None, None
      except AttributeError:
        if silent == False:
          print(f"\n{B.RED}{F.BLACK}Invalid Video link or ID!{S.R} Video IDs are 11 characters long.")
        return False, None, None, None, None
      except IndexError:
        if silent == False:
          print(f"\n{B.RED}{F.BLACK}Invalid Video link or ID!{S.R} Video IDs are 11 characters long.")
        return False, None, None, None, None
    

############################### VALIDATE COMMUNITY POST ID #################################
def validate_post_id(post_url):
  if "/post/" in post_url:
    startIndex = post_url.rindex("/") + 1
    endIndex = len(post_url)
  elif "/channel/" in post_url and "/community?" in post_url and "lb=" in post_url:
    startIndex = post_url.rindex("lb=") + 3
    endIndex = len(post_url)
  else:
    isolatedPostId = post_url
  try:
    if startIndex < endIndex and endIndex <= len(post_url):
      isolatedPostID = post_url[startIndex:endIndex]
  except:
    return False, None, None, None, None

  # Post IDs used to be shorter, but apparently now have a longer format
  if len(isolatedPostID) == 26 or len(isolatedPostID) == 36:
    if isolatedPostID[0:2] == "Ug":
      validatedPostUrl = "https://www.youtube.com/post/" + isolatedPostID
      postOwnerURL = get_post_channel_url(isolatedPostID)
      valid, postOwnerID, postOwnerUsername = validate_channel_id(postOwnerURL)

      return valid, isolatedPostID, validatedPostUrl, postOwnerID, postOwnerUsername

  else:
    return False, None, None, None, None
  

##################################### VALIDATE CHANNEL ID ##################################
# Checks if channel ID / Channel Link is correct length and in correct format - If so returns true and isolated channel ID
def validate_channel_id(inputted_channel):
  isolatedChannelID = "Invalid" # Default value
  inputted_channel = inputted_channel.strip()
  notChannelList = ['?v', 'v=', '/embed/', '/vi/', '?feature=', '/v/', '/e/']

  # Check if link is actually a video link / ID
  isVideo = validate_video_id(inputted_channel, silent=True)
  if isVideo[0] == True:
    print(f"\n{F.BLACK}{B.LIGHTRED_EX} Invalid Channel ID / Link! {S.R} Looks like you entered a Video ID / Link by mistake.")
    return False, None, None

  # Get id from channel link
  if "/channel/" in inputted_channel:
    startIndex = inputted_channel.rindex("/") + 1
    endIndex = len(inputted_channel)
    
    if "?" in inputted_channel:
      endIndex = inputted_channel.rindex("?")

    if startIndex < endIndex and endIndex <= len(inputted_channel):
      isolatedChannelID = inputted_channel[startIndex:endIndex]

  elif "/c/" in inputted_channel or "/user/" in inputted_channel:
    if "/c/" in inputted_channel:
      startIndex = inputted_channel.rindex("/c/") + 3 #Start index at at character after /c/
    elif "/user/" in inputted_channel:
      startIndex = inputted_channel.rindex("/user/") + 6

    endIndex = len(inputted_channel)

    # If there is a / after the username scoot the endIndex over
    if startIndex != inputted_channel.rindex("/") + 1:
      endIndex = inputted_channel.rindex("/") # endIndex is now at the last /

    if startIndex < endIndex and endIndex <= len(inputted_channel):
      customURL = inputted_channel[startIndex:endIndex]
      response = YOUTUBE.search().list(part="snippet",q=customURL, maxResults=1).execute()
      if response.get("items"):
        isolatedChannelID = response.get("items")[0]["snippet"]["channelId"] # Get channel ID from custom channel URL username
  
  # Handle legacy style custom URL (no /c/ for custom URL)
  elif "youtube.com" in inputted_channel and not any(x in inputted_channel for x in notChannelList):
    startIndex = inputted_channel.rindex("/") + 1
    endIndex = len(inputted_channel)

    if startIndex < endIndex and endIndex <= len(inputted_channel):
      customURL = inputted_channel[startIndex:endIndex]
      # First check if actually video ID (video ID regex expression from: https://webapps.stackexchange.com/a/101153)
      if re.match(r'[0-9A-Za-z_-]{10}[048AEIMQUYcgkosw]', customURL):
        print(f"{F.LIGHTRED_EX}Invalid Channel ID / Link!{S.R} Did you enter a video ID / link by mistake?")
        return False, None, None

      response = YOUTUBE.search().list(part="snippet",q=customURL, maxResults=1).execute()
      if response.get("items"):
        isolatedChannelID = response.get("items")[0]["snippet"]["channelId"] # Get channel ID from custom channel URL username

  # Channel ID regex expression from: https://webapps.stackexchange.com/a/101153
  elif re.match(r'UC[0-9A-Za-z_-]{21}[AQgw]', inputted_channel):
    isolatedChannelID = inputted_channel

  else:
    print(f"\n{B.RED}{F.BLACK}Error:{S.R} Invalid Channel link or ID!")
    return False, None, None

  if len(isolatedChannelID) == 24 and isolatedChannelID[0:2] == "UC":
    response = YOUTUBE.channels().list(part="snippet", id=isolatedChannelID).execute()
    if response['items']:
      channelTitle = response['items'][0]['snippet']['title']
      return True, isolatedChannelID, channelTitle
    else:
      print(f"{F.LIGHTRED}Error{S.R}: Unable to Get Channel Title. Please check the channel ID.")
      return False, None, None

  else:
    print(f"\n{B.RED}{F.BLACK}Invalid Channel link or ID!{S.R} Channel IDs are 24 characters long and begin with 'UC'.")
    return False, None, None
  
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
    valid, IDList[i], channelTitle = validate_channel_id(inputList[i])
    if valid == False:
      print(f"{B.RED}{F.BLACK}Invalid{S.R} Channel ID or Link: " + str(inputList[i]) + "\n")
      return False, None
  
  return True, IDList

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
    fieldsToFetch += ",items/snippet/thumbnails/default/url,items/id"

  def fetch_data(channelIdGroup):
    try:
      response = YOUTUBE.channels().list(part="snippet,statistics", id=channelIdGroup, fields=fieldsToFetch).execute()
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
      print("Error occurred when extra json data.")
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
  response = YOUTUBE.channels().list(part="snippet,statistics", id=channelOwnerID, fields=fieldsToFetch).execute()
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

############################ Validate Regex Input #############################
# Checks if regex expression is valid, tries to add escapes if necessary
# From: https://stackoverflow.com/a/51782559/17312053

def validate_regex(regex_from_user: str):
  try: 
    re.compile(regex_from_user)
    is_valid = True
    processedExpression = regex_from_user
  except re.error: 
    try:
      re.compile(re.escape(regex_from_user))
      is_valid = True
      processedExpression = re.escape(regex_from_user)
    except re.error:
      print("Failed")
      is_valid = False
      processedExpression = None

  return is_valid, processedExpression
      
############################ RTF & File Handling ###############################

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


  
############################# Check For App Update ##############################
def check_for_update(currentVersion, updateReleaseChannel, silentCheck=False):
  isUpdateAvailable = False
  print("\nGetting info about latest updates...")

  try:
    if updateReleaseChannel == "stable":
      response = requests.get("https://api.github.com/repos/ThioJoe/YT-Spammer-Purge/releases/latest")
    elif updateReleaseChannel == "all":
      response = requests.get("https://api.github.com/repos/ThioJoe/YT-Spammer-Purge/releases")

    if response.status_code != 200:
      if response.status_code == 403:
        if silentCheck == False:
          print(f"\n{B.RED}{F.WHITE}Error [U-4]:{S.R} Got an 403 (ratelimit_reached) when attempting to check for update.")
          print(f"This means you have been {F.YELLOW}rate limited by github.com{S.R}. Please try again in a while.\n")
          return False
        else:
          return False
      else:
        if silentCheck == False:
          print(f"{B.RED}{F.WHITE}Error [U-3]:{S.R} Got non 200 status code (got: {response.status_code}) when attempting to check for update.\n")
          print(f"If this keeps happening, you may want to report the issue here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
          if silentCheck == False:
            return False
        else:
          return False
    else:
      # assume 200 response
      if updateReleaseChannel == "stable":
        latestVersion = response.json()["name"]
        isBeta = False
      elif updateReleaseChannel == "all":
        latestVersion = response.json()[0]["name"]
        isBeta = response.json()[0]["prerelease"]
      
  except Exception as e:
    if silentCheck == False:
      print(e + "\n")
      print(f"{B.RED}{F.WHITE}Error [Code U-1]:{S.R} Problem while checking for updates. See above error for more details.\n")
      print("If this keeps happening, you may want to report the issue here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
      return False
    elif silentCheck == True:
      return False

  if parse_version(latestVersion) > parse_version(currentVersion):
    isUpdateAvailable = True
    if silentCheck == False:
      print("------------------------------------------------------------------------------------------")
      if isBeta == True:
        print(f" {F.YELLOW}A new {F.LIGHTGREEN_EX}beta{F.YELLOW} version{S.R} is available!")
      else:
        print(f" A {F.LIGHTGREEN_EX}new version{S.R} is available!")
      print(f" > Current Version: {currentVersion}")
      print(f" > Latest Version: {F.LIGHTGREEN_EX}{latestVersion}{S.R}")
      print("(To stop receiving beta releases, change the 'release_channel' setting in the config file)")
      print("------------------------------------------------------------------------------------------")
      userChoice = choice("Update Now?")
      if userChoice == True:
        if sys.platform == 'win32' or sys.platform == 'win64':
          print(f"\n> {F.LIGHTCYAN_EX} Downloading Latest Version...{S.R}")
          if updateReleaseChannel == "stable":
            jsondata = json.dumps(response.json()["assets"])
          elif updateReleaseChannel == "all":
            jsondata = json.dumps(response.json()[0]["assets"])
          dict_json = json.loads(jsondata)

          # Get files in release, get exe and hash info
          i,j,k = 0,0,0 # i = index of all, j = index of exe, k = index of hash
          for asset in dict_json:
            i+=1
            name = str(asset['name'])
            if '.exe' in name.lower():
              filedownload = requests.get(dict_json[0]['browser_download_url'], stream=True)
              j+=1 # Count number of exe files in release, in case future has multiple exe's, can cause warning
            if '.sha256' in name.lower():
              #First removes .sha256 file extension, then removes all non-alphanumeric characters
              downloadHashSHA256 = re.sub(r'[^a-zA-Z0-9]', '', name.lower().replace('.sha256', ''))
              k += 1

          ignoreHash = False
          # Validate Retrieved Info    
          if j > 1: # More than one exe file in release
            print(f"{S.YELLOW}Warning!{S.R} Multiple exe files found in release. You must be updating from the future when that was not anticipated.")
            print("You should instead manually download the latest version from: https://github.com/ThioJoe/YT-Spammer-Purge/releases")
            print("You can try continuing anyway, but it might not be successful, or might download the wrong exe file.")
            input("\nPress enter to continue...")
          elif j == 0: # No exe file in release
            print(f"{S.LIGHTRED_EX}Warning!{S.R} No exe file found in release. You'll have to manually download the latest version from:")
            print("https://github.com/ThioJoe/YT-Spammer-Purge/releases")
            return False
          if k == 0: # No hash file in release
            print(f"{S.YELLOW}Warning!{S.R} No verification sha256 hash found in release. If download fails, you can manually download latest version here:")
            print("https://github.com/ThioJoe/YT-Spammer-Purge/releases")
            input("\nPress Enter to try to continue...")
            ignoreHash = True
          elif k>0 and k!=j:
            print(f"{S.YELLOW}Warning!{S.R} Too many or too few sha256 files found in release. If download fails, you should manually download latest version here:")
            print("https://github.com/ThioJoe/YT-Spammer-Purge/releases")
            input("\nPress Enter to try to continue...")


          # Get and Set Download Info
          total_size_in_bytes= int(filedownload.headers.get('content-length', 0))
          block_size =  1048576 #1 MiB in bytes
          downloadFileName = dict_json[0]['name']

          # Check if file exists already, ask to overwrite if it does
          if os.path.exists(downloadFileName):
            print(f"\n{B.RED}{F.WHITE} WARNING! {S.R} '{F.YELLOW}{downloadFileName}{S.R}' file already exists. This would overwrite the existing file.")
            confirm = choice("Overwrite this existing file?")
            if confirm == True:
              try:
                os.remove(downloadFileName)
              except:
                traceback.print_exc()
                print(f"\n{F.LIGHTRED_EX}Error F-6:{S.R} Problem deleting existing existing file! Check if it's gone, or delete it yourself, then try again.")
                print("The info above may help if it's a bug, which you can report here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
                input("Press enter to Exit...")
                sys.exit()
            elif confirm == False or confirm == None:
              return False

          # Download File
          with open(downloadFileName, 'wb') as file:
            numProgressBars = 30
            for data in filedownload.iter_content(block_size):
              progress = os.stat(downloadFileName).st_size/total_size_in_bytes * numProgressBars
              print(f"{F.LIGHTGREEN_EX}<[{F.LIGHTCYAN_EX}" + '='*round(progress) + ' '*(numProgressBars-round(progress)) + f"{F.LIGHTGREEN_EX}]>{S.R}\r", end="") #Print Progress bar
              file.write(data)
          print(f"\n>  {F.LIGHTCYAN_EX}Verifying Download Integrity...{S.R}                       ")

          # Verify Download Size
          if os.stat(downloadFileName).st_size == total_size_in_bytes:
            pass
          elif total_size_in_bytes != 0 and os.stat(downloadFileName).st_size != total_size_in_bytes:
            os.remove(downloadFileName)
            print(f"\n> {F.RED} File did not fully download. Please try again later.")
            return False
          elif total_size_in_bytes == 0:
            print("Something is wrong with the download on the remote end. You should manually download latest version here:")
            print("https://github.com/ThioJoe/YT-Spammer-Purge/releases")

          # Verify hash
          if ignoreHash == False:
            if downloadHashSHA256 == hashlib.sha256(open(downloadFileName, 'rb').read()).hexdigest().lower():
              pass
            else:
              os.remove(downloadFileName)
              print(f"\n> {F.RED} Hash did not match. Please try again later.")
              print("Or download the latest version manually from here: https://github.com/ThioJoe/YT-Spammer-Purge/releases")
              return False

          # Print Success
          print(f"\n >  Download Completed: {F.LIGHTGREEN_EX}{downloadFileName}{S.R}")
          if isBeta == False:
            print("\nYou can now delete the old version. (Or keep it around in case you encounter any issues with the new version)")
          else:
            print(f"\n{F.LIGHTYELLOW_EX}NOTE:{S.R} Because this is a {F.CYAN}beta release{S.R}, you should keep the old version around in case you encounter any issues")
            print(f" > And don't forget to report any problems you encounter here: {F.YELLOW}TJoe.io/bug-report{S.R}")
          input("\nPress Enter to Exit...")
          sys.exit()

        else:
          # We do this because we pull the .exe for windows, but maybe we could use os.system('git pull')? Because this is a GIT repo, unlike the windows version
          print(f"> {F.RED} Error:{S.R} You are using an unsupported os for the autoupdater (macos/linux). \n This updater only supports Windows (right now) Feel free to get the files from github: https://github.com/ThioJoe/YT-Spammer-Purge")
          return False
      elif userChoice == "False" or userChoice == None:
        return False
    elif silentCheck == True:
      isUpdateAvailable = True
      return isUpdateAvailable

  elif parse_version(latestVersion) == parse_version(currentVersion):
    if silentCheck == False:
      print(f"\nYou have the {F.LIGHTGREEN_EX}latest{S.R} version: {F.LIGHTGREEN_EX}" + currentVersion)
      return False
  else:
    if silentCheck == False:
      print("\nNo newer release available - Your Version: " + currentVersion + "  --  Latest Version: " + latestVersion)
      return False
    elif silentCheck == True:
      return isUpdateAvailable

######################### Try To Get Remote File ##########################
def getRemoteFile(url, stream, silent=False, headers=None):
  try:
    if stream == False:
      response = requests.get(url, headers=headers)
    elif stream == True:
      response = requests.get(url, headers=headers, stream=True)
    if response.status_code != 200:
      if silent == False:
        print("Error fetching remote file or resource: " + url)
        print("Response Code: " + str(response.status_code))
    else:
      return response

  except Exception as e:
    if silent == False:
      print(e + "\n")
      print(f"{B.RED}{F.WHITE} Error {S.R} While Fetching Remote File or Resource: " + url)
      print("See above messages for details.\n")
      print("If this keeps happening, you may want to report the issue here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
    return None

########################### Check Lists Updates ###########################
def check_lists_update(spamListDict, silentCheck = False):
  SpamListFolder = spamListDict['Meta']['SpamListFolder']
  currentListVersion = spamListDict['Meta']['VersionInfo']['LatestLocalVersion']
  
  def update_last_checked():
    currentDate = datetime.today().strftime('%Y.%m.%d.%H.%M')
    #Update Dictionary with latest release gotten from API
    spamListDict['Meta']['VersionInfo'].update({'LatestLocalVersion': latestRelease})
    spamListDict['Meta']['VersionInfo'].update({'LastChecked': currentDate})

    # Prepare data for json file update, so only have to check once a day automatically
    newJsonContents = json.dumps({'LatestRelease': latestRelease, 'LastChecked' : currentDate})
    with open(spamListDict['Meta']['VersionInfo']['Path'], 'w', encoding="utf-8") as file:
      json.dump(newJsonContents, file, indent=4)

  if silentCheck == False:
    print("\nChecking for updates to spam lists...")

  if os.path.isdir(SpamListFolder):
    pass
  else:
    try:
      os.mkdir(SpamListFolder)
    except:
      print("Error: Could not create folder. Try creating a folder called 'spam_lists' to update the spam lists.")

  try:
    response = requests.get("https://api.github.com/repos/ThioJoe/YT-Spam-Domains-List/releases/latest")
    if response.status_code != 200:
      if response.status_code == 403:
        if silentCheck == False:
          print(f"\n{B.RED}{F.WHITE}Error [U-4L]:{S.R} Got an 403 (ratelimit_reached) when attempting to check for spam list update.")
          print(f"This means you have been {F.YELLOW}rate limited by github.com{S.R}. Please try again in a while.\n")
          return False
        else:
          return spamListDict
      else:
        if silentCheck == False:
          print(f"{B.RED}{F.WHITE}Error [U-3L]:{S.R} Got non 200 status code (got: {response.status_code}) when attempting to check for spam list update.\n")
          print(f"If this keeps happening, you may want to report the issue here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
          if silentCheck == False:
            return False
        else:
          return spamListDict
    latestRelease = response.json()["tag_name"]
  except:
    if silentCheck == True:
      return spamListDict
    else:
      print("Error: Could not get latest release info from GitHub. Please try again later.")
      return False

  # If update available
  if currentListVersion == None or (parse_version(latestRelease) > parse_version(currentListVersion)):
    print("\n>  A new spam list update is available. Downloading...")
    fileName = response.json()["assets"][0]['name']
    total_size_in_bytes = response.json()["assets"][0]['size']
    downloadFilePath = SpamListFolder + fileName
    downloadURL = response.json()["assets"][0]['browser_download_url']
    filedownload = getRemoteFile(downloadURL, stream=True) # These headers required to get correct file size
    block_size =  1048576 #1 MiB in bytes

    with open(downloadFilePath, 'wb') as file:
      for data in filedownload.iter_content(block_size):
        file.write(data)
  
    if os.stat(downloadFilePath).st_size == total_size_in_bytes:
      # Unzip files into folder and delete zip file
      attempts = 0
      print("Extracting updated lists...")
      while True:
        try:
          attempts += 1
          time.sleep(0.5)
          with zipfile.ZipFile(downloadFilePath,"r") as zip_ref:
            zip_ref.extractall(SpamListFolder)
          os.remove(downloadFilePath)
        except PermissionError as e:
          if attempts <= 10:
            continue
          else:
            traceback.print_exc()
            print(f"\n> {F.RED}Error:{S.R} The zip file containing the spam lists was downloaded, but there was a problem extracting the files because of a permission error. ")
            print(f"This can happen if an antivirus takes a while to scan the file. You may need to manually extract the zip file.")
            input("\nPress enter to Continue anyway...")
            break
        # This means success, the zip file was deleted after extracting
        except FileNotFoundError:
          update_last_checked()
          return spamListDict

    elif total_size_in_bytes != 0 and os.stat(downloadFilePath).st_size != total_size_in_bytes:
      os.remove(downloadFilePath)
      print(f" > {F.RED} File did not fully download. Please try again later.\n")
      return spamListDict
  else:
    update_last_checked()
    return spamListDict

############################# Ingest Other Files ##############################
def ingest_asset_file(fileName):
  def assetFilesPath(relative_path):
    if hasattr(sys, '_MEIPASS'): # If running as a pyinstaller bundle
      return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("assets"), relative_path) # If running as script, specifies resource folder as /assets
  
  # Open list of root zone domain extensions
  with open(assetFilesPath(fileName), 'r', encoding="utf-8") as file:
    data = file.readlines()
  dataList = []
  for line in data:
    if not line.strip().startswith('#'):
      line = line.strip()
      dataList.append(line.lower())
  return dataList

def copy_asset_file(fileName, destination):
  def assetFilesPath(relative_path):
    if hasattr(sys, '_MEIPASS'): # If running as a pyinstaller bundle
      return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("assets"), relative_path) # If running as script, specifies resource folder as /assets
  copyfile(assetFilesPath(fileName), os.path.abspath(destination))

def ingest_list_file(relativeFilePath, keepCase = True):
  if os.path.exists(relativeFilePath):
    with open(relativeFilePath, 'r', encoding="utf-8") as listFile:
      # If file doesn't end with newline, add one
      listData = listFile.readlines()
      lastline = listData[-1]
      
    with open(relativeFilePath, 'a', encoding="utf-8") as listFile:
      if not lastline.endswith('\n'):
        listFile.write('\n')

    processedList = []
    for line in listData:
      line = line.strip()
      if not line.startswith('#') and line !="":
        if keepCase == False:
          processedList.append(line.lower())
        else: 
          processedList.append(line)
    return processedList
  else:
    return None

def get_list_file_version(relativeFilePath):
  if os.path.exists(relativeFilePath):
    matchBetweenBrackets = '(?<=\[)(.*?)(?=\])' # Matches text between first set of two square brackets
    with open(relativeFilePath, 'r', encoding="utf-8") as file:
      for line in islice(file, 0, 5):
        try:
          listVersion = str(re.search(matchBetweenBrackets, line).group(0))
        except AttributeError:
          pass
      return listVersion
  else:
    return None

############################# CONFIG FILE FUNCTIONS ##############################
def create_config_file(updating=False, dontWarn=False):
  def config_path(relative_path):
    if hasattr(sys, '_MEIPASS'): # If running as a pyinstaller bundle
        #print("Test1") # For Debugging
        #print(os.path.join(sys._MEIPASS, relative_path)) # For Debugging
        return os.path.join(sys._MEIPASS, relative_path)
    #print("Test2") # for Debugging
    #print(os.path.join(os.path.abspath("assets"), relative_path)) # For debugging
    return os.path.join(os.path.abspath("assets"), relative_path) # If running as script, specifies resource folder as /assets

  configFileName = "SpamPurgeConfig.ini"
  confirm = True
  if os.path.exists(configFileName):
    if updating == False and dontWarn == False:
      print(f"{B.RED}{F.WHITE} WARNING! {S.R} {F.YELLOW}SpamPurgeConfig.ini{S.R} file already exists. This would overwrite the existing file.")
      confirm = choice("Create new empty config file and overwrite existing?")
    else:
      confirm = True

    if confirm == True:
      try:
        os.remove(configFileName)
      except:
        traceback.print_exc()
        print("Error Code F-1: Problem deleting existing existing file! Check if it's gone. The info above may help if it's a bug.")
        print("If this keeps happening, you may want to report the issue here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
        input("Press enter to Exit...")
        sys.exit()
    elif confirm == False or confirm == None:
      return "MainMenu"

  if confirm == True:
    # Get default config file contents
    try:
      with open(config_path('default_config.ini'), 'r', encoding="utf-8") as defaultConfigFile:
        data = defaultConfigFile.read()
      defaultConfigFile.close()
    except:
      traceback.print_exc()
      print(f"{B.RED}{F.WHITE}Error Code: F-2{S.R} - Problem reading default config file! The info above may help if it's a bug.")
      input("Press enter to Exit...")
      sys.exit()

    # Create config file
    try:
      configFile = open(configFileName, "w", encoding="utf-8")
      configFile.write(data)
      configFile.close()
    except:
      traceback.print_exc()
      print(f"{B.RED}{F.WHITE}Error Code: F-3{S.R} Problem creating config file! The info above may help if it's a bug.")
      input("Press enter to Exit...")
      sys.exit()

    if os.path.exists(configFileName):
      parser = ConfigParser()
      try:
        parser.read("SpamPurgeConfig.ini", encoding="utf-8")
        if parser.get("info", "config_version"):
          if updating == False:
            print(f"\n{B.GREEN}{F.BLACK} SUCCESS! {S.R} {F.YELLOW} SpamPurgeConfig.ini{S.R} file created successfully.")
            print("\nYou can now edit the file to your liking.\n")
            input("Press enter to Exit...")
            sys.exit()
          else:
            return True
        else:
          print("Something might have gone wrong. Check if SpamPurgeConfig.ini file exists and has contents.")
          input("Press enter to Exit...")
          sys.exit()
      except SystemExit:
        sys.exit()
      except:
        traceback.print_exc()
        print("Something went wrong when checking the created file. Check if SpamPurgeConfig.ini exists and has text. The info above may help if it's a bug.")
        input("Press enter to Exit...")
        sys.exit()
  else:
    input("Press Enter to return to the main menu...")
    return "MainMenu"

# -------------------------------------------------------------------
# Put config settings into dictionary
def load_config_file(forceDefault = False):
  configFileName = "SpamPurgeConfig.ini"
  configDict = {}

  # If user config file exists, keep path. Otherwise use default config file path
  if os.path.exists(configFileName) and forceDefault == False:
    default = False

  else:
    def default_config_path(relative_path):
      if hasattr(sys, '_MEIPASS'): # If running as a pyinstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
      return os.path.join(os.path.abspath("assets"), relative_path) # If running as script, specifies resource folder as /assets

    configFileName = default_config_path("default_config.ini")
    default = True

  # Load Contents of config file
  try:
    with open(configFileName, 'r', encoding="utf-8") as configFile:
      configData = configFile.read()
      configFile.close()
  except:
    traceback.print_exc()
    print(f"{B.RED}{F.WHITE}Error Code: F-4{S.R} - Config file found, but there was a problem loading it! The info above may help if it's a bug.")
    print("\nYou can manually delete SpamPurgeConfig.ini and use the program to create a new default config.")
    input("Press enter to Exit...")
    sys.exit()

  # Sanitize config Data by removing quotes
  configData = configData.replace("\'", "")
  configData = configData.replace("\"", "")

  # Converts string from config file, wraps it to make it behave like file so it can be read by parser
  # Must use .read_file, .read doesn't work
  wrappedConfigData = io.StringIO(configData)
  parser = ConfigParser()
  parser.read_file(wrappedConfigData)
 
  # Convert raw config dictionary into easier to use dictionary
  settingsToKeepCase = ["your_channel_id", "videos_to_scan", "channel_ids_to_filter", "regex_to_filter", "channel_to_scan", "log_path"]
  validWordVars = ['ask', 'mine', 'default']
  for section in parser.sections():
    for setting in parser.items(section):
      # Setting[0] is name of the setting, Setting[1] is the value of the setting
      if setting[0] in settingsToKeepCase and setting[1].lower() not in validWordVars:
        configDict[setting[0]] = setting[1]
      else:
        # Take values out of raw dictionary structure and put into easy dictionary with processed values
        configDict[setting[0]] = setting[1].lower()
        if setting[1].lower() == "false":
          configDict[setting[0]] = False
        elif setting[1].lower() == "true":
          configDict[setting[0]] = True

  # Prevent prompt about config file if it's the default config file
  if default == True:
    configDict['use_this_config'] = True

  return configDict

# -------------------------------------------------------------------
def update_config_file(oldVersion, newVersion, oldConfig):
  configFileName = "SpamPurgeConfig.ini"

  # If user config file exists, keep path. Otherwise use default config file path
  if os.path.exists(configFileName):
    pass
  else:
    print("No existing config file found!")
    return False

  # Load data of old config file
  with open(configFileName, 'r', encoding="utf-8") as oldFile:
    oldConfigData = oldFile.readlines()
    oldFile.close()

  # Rename config to backup
  backupConfigFileName = f"{configFileName}.backup_v{oldVersion}"
  if os.path.exists(backupConfigFileName):
    print("Existing backup config file found. Random number will be added to new backup file name.")
    while os.path.exists(backupConfigFileName):
      backupConfigFileName = backupConfigFileName + "_" + str(randrange(999))

  os.rename(configFileName, backupConfigFileName)
  print(f"\nOld config file renamed to {F.CYAN}{backupConfigFileName}{S.R}")

  # Creates new config file from default
  create_config_file(updating=True)

  try:
    with open(configFileName, 'r', encoding="utf-8") as newFile:
      newConfigData = newFile.readlines()

    newDataList = []
    # Go through all new config lines
    for newLine in newConfigData:
      if not newLine.strip().startswith('#') and not newLine.strip()=="" and "version" not in newLine:
        for setting in oldConfig.keys():
          # Check if any old settings are in new config file
          if newLine.startswith(setting):
            for oldLine in oldConfigData:
              if not oldLine.strip().startswith('#') and not oldLine.strip()=="" and "version" not in oldLine:
                # Sets new line to be the old line
                if oldLine.startswith(setting):
                  newLine = oldLine
                  break
            break
      # The new config file writes itself again, but with the modified newLine's
      newDataList.append(newLine)

    with open(configFileName, "w", encoding="utf-8") as newFile:
      newFile.writelines(newDataList)
  except:
    traceback.print_exc()
    print("--------------------------------------------------------------------------------")
    print("Something went wrong when copying your config settings. You'll have to manually copy them from backup.")
    input("\nPress Enter to exit...")
    sys.exit()
  
  print("\nConfig Updated! Please restart the program...")
  input("\nPress enter to Exit...")
  sys.exit()

################################ RECOVERY MODE ###########################################
def recover_deleted_comments():
  print(f"\n\n-------------------- {F.LIGHTGREEN_EX}Comment Recovery Mode{S.R} --------------------\n")
  print("Believe it or not, the YouTube API actually allows you to re-instate \"deleted\" comments.")
  print(f"This is {F.YELLOW}only possible if you have stored the comment IDs{S.R} of the deleted comments, such as {F.YELLOW}having kept the log file{S.R} of that session.")
  print("If you don't have the comment IDs you can't recover the comments, and there is no way to find them. \n")

  validFile = False
  manuallyEnter = False
  while validFile == False and manuallyEnter == False:
    print("Enter the name of the log file containing the comments to recover (you could rename it to something easier like \'log.rtf\')")
    print("     > (Or, just hit Enter to manually paste in the list of IDs next)")
    recoveryFileName = input("\nLog File Name (Example: \"log.rtf\" or \"log\"):  ")
    if str(recoveryFileName).lower() == "x":
      return "MainMenu"

    if len(recoveryFileName) > 0:
      if os.path.exists(recoveryFileName):
        pass
      elif os.path.exists(recoveryFileName+".rtf"):
        recoveryFileName = recoveryFileName + ".rtf"

      # Get file path
      if os.path.exists(recoveryFileName):
        try:
          with open(recoveryFileName, 'r', encoding="utf-8") as recoveryFile:
            data = recoveryFile.read()
          recoveryFile.close()
          validFile = True
        except:
          print("Error Code F-5: Log File was found but there was a problem reading it.")
      else:
        print(f"\n{F.LIGHTRED_EX}Error: File not found.{S.R} Make sure it is in the same folder as the program.\n")
        print("Enter 'Y' to try again, or 'N' to manually paste in the comment IDs.")
        userChoice = choice("Try entering file name again?")
        if userChoice == True:
          pass
        elif userChoice == False:
          manuallyEnter = True
        elif userChoice == None:
          return "MainMenu"
    else: 
      manuallyEnter = True

  if manuallyEnter == True:
    print("\n\n--- Manual Comment ID Entry Instructions ---")
    print("1. Open the log file and look for where it shows the list of \"IDs of Matched Comments\".")
    print("2. Copy that list, and paste it below (In windows console try pasting by right clicking).")
    print("3. If not using a log file, instead enter the ID list in this format: FirstID, SecondID, ThirdID, ... \n")
    data = str(input("Paste the list here, then hit Enter: "))
    if str(data).lower() == "x":
      return "MainMenu"
    print("\n")

  # Parse data into list
  if manuallyEnter == False and '[' in data and ']' in data:
    matchBetweenBrackets = '(?<=\[)(.*?)(?=\])' # Matches text between first set of two square brackets
    #matchIncludeBracktes = '\[(.*?)\]' # Matches between square brackets, including brackets
    result = str(re.search(matchBetweenBrackets, data).group(0))
  else: result = data
  result = result.replace("\'", "")
  result = result.replace("[", "")
  result = result.replace("]", "")
  result = result.replace(" ", "")
  result = result.split(",")

  if len(result) == 0:
    print("Error Code R-1: No comment IDs detected, try entering them manually and make sure they are formatted correctly.")
    input("Press Enter to return to main menu...")
    return "MainMenu"

  # Check for valid comment IDs
  validCount = 0
  notValidCount = 0
  notValidList = []
  for id in result:
    if id[0:2] == "Ug":
      validCount += 1
    else:
      notValidCount += 1
      notValidList.append(id)

  if notValidCount > 0:
    print(f"{F.YELLOW}Possibly Invalid Comment IDs:{S.R} " + str(notValidList)+ "\n")

  if notValidCount == 0:
    print("\nLoaded all " + str(validCount) + " comment IDs successfully!")
    input("\nPress Enter to begin recovery... ")
  elif validCount > 0 and notValidCount > 0:
    print(f"\{F.RED}Warning!{S.R} {str(validCount)} valid comment IDs loaded successfully, but {str(notValidCount)} may be invalid. See them above.")
    input("\nPress Enter to try recovering anyway...\n")
  elif validCount == 0 and notValidCount > 0:
    print(f"\n{F.RED}Warning!{S.R} All loaded comment IDs appear to be invalid. See them above.")
    input("Press Enter to try recovering anyway...\n")
  print("\n")

  delete_found_comments(commentsList=result, banChoice=False, deletionMode="published", recoveryMode=True)
  check_recovered_comments(commentsList=result)


##########################################################################################
################################## FILTERING MODES #######################################
##########################################################################################

# For scanning for individual chars
def prepare_filter_mode_chars(scanMode, filterMode, config):
  if filterMode == "Username":
    whatToScanMsg = "Usernames"
  elif filterMode == "Text":
    whatToScanMsg = "Comment Text"
  elif filterMode == "NameAndText":
    whatToScanMsg = "Usernames and Comment Text"

  if config and config['characters_to_filter'] != "ask":
    print("Characters to filter obtained from config file.")
    pass
  else:
    print(f"\nNext, you will input {F.YELLOW}ONLY{S.R} any special characters / emojis you want to search for in all {whatToScanMsg}. Do not include commas or spaces!")
    print("          Note: Letters, numbers, and basic punctuation will not be included for safety purposes, even if you enter them.")
    print("          Example: 👋🔥✔️✨")
    input(f"\nPress {F.LIGHTGREEN_EX}Enter{S.R} to open the {F.LIGHTGREEN_EX}text entry window{S.R}...")
    print("-------------------------------------------")

  confirm = False
  validConfigSetting = True
  while confirm == False:
    if validConfigSetting == True and config and config['characters_to_filter'] != "ask":
      inputChars = make_char_set(config['characters_to_filter'], stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=True)
      bypass = True
    else:
      bypass = False
      print(f"\nWaiting for input Window. Press {F.MAGENTA}'Execute'{S.R} after entering valid characters to continue...", end="\r")
      try:
        # Takes in user input of characters, returns 'set' of characters stripped of specified characters
        inputChars = take_input_gui(mode="chars", stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=True)
      except NameError: # Catch if user closes GUI window, exit program.
        print("                                                                                          ") # Clears the line because of \r on previous print
        print("\nError Code G-1: Something went wrong with the input, or you closed the window improperly.")
        print("If this keeps happening inexplicably, consider filing a bug report here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
        input("Press Enter to exit...")
        sys.exit()

    print(f"     {whatToScanMsg} will be scanned for {F.MAGENTA}ANY{S.R} of the characters you entered in the previous window.")
    userChoice = choice("Begin Scanning? ", bypass)
    if userChoice == True:
      confirm = True
    elif userChoice == False:
      confirm = False
      validConfigSetting = False
    elif userChoice == None:
      return "MainMenu", None

  return inputChars, None

# For scanning for strings
def prepare_filter_mode_strings(scanMode, filterMode, config):
  if filterMode == "Username":
    whatToScanMsg = "Usernames"
  elif filterMode == "Text":
    whatToScanMsg = "Comment Text"
  elif filterMode == "NameAndText":
    whatToScanMsg = "Usernames and Comment Text"

  if config and config['strings_to_filter'] != "ask":
    print("Strings to filter obtained from config file.")
    pass
  else:
    print(f"\nPaste or type in a list of any {F.YELLOW}comma separated strings{S.R} you want to search for in {whatToScanMsg}. (Not case sensitive)")
    print("   >Note: If the text you paste includes special characters or emojis, they might not display correctly here, but it WILL still search them fine.")
    print("          Example Input: whatsapp, whatever multiple words, investment")

  validEntry = False
  validConfigSetting = True
  while validEntry == False:
    if validConfigSetting == True and config and config['strings_to_filter'] != "ask":
      inputString = config['strings_to_filter']
      bypass = True
    else:
      bypass = False
      inputString = input("Input Here: ")
      if str(inputString).lower() == "x":
        return "MainMenu", None

    # Convert comma separated string into list with function, then check against current user's name
    filterStringList = string_to_list(inputString, lower=True)
    if len(filterStringList) > 0:
      validEntry = True
    else:
      validConfigSetting = False

    if validEntry == True:
      if config and config['strings_to_filter'] != "ask":
        pass
      else:
        print(f"     {whatToScanMsg} will be scanned for {F.MAGENTA}ANY{S.R} of the following strings:")
        print(filterStringList)
      userChoice = choice("Begin scanning? ", bypass)
      if userChoice == True:
        validEntry = True
      elif userChoice == False:
        validEntry = False
      elif userChoice == None:
        return "MainMenu", None

  return filterStringList, None

# For scanning for regex expression
def prepare_filter_mode_regex(scanMode, filterMode, config):
  if filterMode == "Username":
    whatToScanMsg = "Usernames"
  elif filterMode == "Text":
    whatToScanMsg = "Comment Text"
  elif filterMode == "NameAndText":
    whatToScanMsg = "Usernames and Comment Text"

  if config and config['regex_to_filter'] != "ask":
    print("Regex expression obtained from config file.")
    validConfigSetting = True
  else:
    print(f"Enter any {F.YELLOW}regex expression{S.R} to search within {whatToScanMsg}.")
    print(r"          Example Input:  [^\x00-\xFF]")
    validConfigSetting = False
  validExpression = False

  while validExpression == False:
    if validConfigSetting == True and config and config['regex_to_filter'] != "ask":
      inputtedExpression = config['regex_to_filter']
      bypass = True
    else:
      inputtedExpression = input("Input Expression Here:  ")
      if str(inputtedExpression).lower() == "x":
        return "MainMenu", None
      bypass = False

    validationResults = validate_regex(inputtedExpression) # Returns tuple of valid, and processed expression
    validExpression = validationResults[0]

    if validExpression == True:
      processedExpression = validationResults[1]
      print(f"     The expression appears to be {F.GREEN}valid{S.R}!")

      if validExpression == True:
        userChoice = choice("Begin scanning? ", bypass)
        if userChoice == True:
          pass
        elif userChoice == False:
          validExpression = False
          validConfigSetting = False
        elif userChoice == None:
          return "MainMenu", None
    else:
      print(f"     {F.RED}Error{S.R}: The expression appears to be {F.RED}invalid{S.R}!")
      validConfigSetting = False

  return processedExpression, None

# Filter Mode: User manually enters ID
# Returns inputtedSpammerChannelID
def prepare_filter_mode_ID(scanMode, config):
  processResult = (False, None) #Tuple, first element is status of validity of channel ID, second element is channel ID
  validConfigSetting = True
  while processResult[0] == False:
    if validConfigSetting == True and config and config['channel_ids_to_filter'] != "ask":
      inputtedSpammerChannelID = config['channel_ids_to_filter']
      bypass = True
    else:
      bypass = False
      inputtedSpammerChannelID = input(f"Enter the {F.LIGHTRED_EX} Channel link(s) or ID(s){S.R} of the spammer (comma separated): ")
      if str(inputtedSpammerChannelID).lower() == "x":
        return "MainMenu", None

    processResult = process_spammer_ids(inputtedSpammerChannelID)
    if processResult[0] == True:
      inputtedSpammerChannelID = processResult[1] # After processing, if valid, inputtedSpammerChannelID is a list of channel IDs
    else:
      validConfigSetting = False
  print("\n")

  # Check if spammer ID and user's channel ID are the same, and warn
  # If using channel-wide scanning mode, program will just ignore those comments
  if any(CURRENTUSER.id == i for i in inputtedSpammerChannelID):
    print(f"{B.RED}{F.WHITE} WARNING: {S.R} - You entered your own channel ID!")
    print(f"For safety purposes, this program always {F.YELLOW}ignores{S.R} your own comments.")

    if config and config['channel_ids_to_filter'] != "ask":
      pass
    else:
      input("\nPress Enter to continue...")
  
  return inputtedSpammerChannelID, None

# For Filter mode auto-ascii, user inputs nothing, program scans for non-ascii
def prepare_filter_mode_non_ascii(scanMode, config):

  print("\n--------------------------------------------------------------------------------------------------------------")
  print("~~~ This mode automatically searches for usernames that contain special characters (aka not letters/numbers) ~~~\n")
  print("Choose the sensitivity level of the filter. You will be shown examples after you choose.")
  print(f"   1. Allow {F.LIGHTMAGENTA_EX}Standard + Extended ASCII{S.R}:    Filter rare unicode & Emojis only")
  print(f"   2. Allow {F.LIGHTMAGENTA_EX}Standard ASCII only{S.R}:  Also filter semi-common foreign characters")
  print(f"   3. {F.LIGHTRED_EX}NUKE Mode (┘°□°)┘≈ ┴──┴ :    Allow ONLY numbers, letters, and spaces{S.R}")
  print("")

  # Get user input for mode selection, 
  confirmation = False
  validConfigSetting = True
  while confirmation == False:
    if validConfigSetting == True and config and config['autoascii_sensitivity'] != "ask":
      selection = config['autoascii_sensitivity']
      bypass = True
    else:
      bypass = False
      selection = input("Choose Mode: ")
      if str(selection).lower() == "x":
        return "MainMenu", None
    if selection == "1":
      print(f"Searches for {F.YELLOW}usernames with emojis, unicode symbols, and rare foreign characters{S.R} such as: ✔️ ☝️ 🡆 ▲ π Ɲ Œ")
      userChoice = choice("Choose this mode?", bypass)
      if userChoice == True:
        regexPattern = r"[^\x00-\xFF]"
        confirmation = True
      elif userChoice == None:
        return "MainMenu", None
    elif selection == "2":
      print(f"Searches for {F.YELLOW}usernames with anything EXCEPT{S.R} the following: {F.YELLOW}Letters, numbers, punctuation, and common special characters{S.R} you can type with your keyboard like: % * & () + ")
      userChoice = choice("Choose this mode?", bypass)
      if userChoice == True:
        regexPattern = r"[^\x00-\x7F]"
        confirmation = True
      elif userChoice == None:
        return "MainMenu", None
    elif selection == "3":
      print(f"Searches for {F.YELLOW}usernames with anything EXCEPT letters, numbers, and spaces{S.R} - {B.RED}{F.WHITE} EXTREMELY LIKELY to cause collateral damage!{S.R} Recommended to just use to manually gather list of spammer IDs, then use a different mode to delete.")
      userChoice = choice("Choose this mode?", bypass)
      if userChoice == True:
        regexPattern = r"[^a-zA-Z0-9 ]"
        confirmation = True
      elif userChoice == None:
        return "MainMenu", None
    else:
      print(f"Invalid input: {selection} - Must be 1, 2, or 3.")
      validConfigSetting = False
    
  if selection == "1":
    autoModeName = "Allow Standard + Extended ASCII"
  elif selection == "2":
    autoModeName = "Allow Standard ASCII only"
  elif selection == "3":
    autoModeName = "NUKE Mode (┘°□°)┘≈ ┴──┴ - Allow only letters, numbers, and spaces"

  if confirmation == True:
    return regexPattern, autoModeName
  else:
    input("How did you get here? Something very strange went wrong. Press Enter to Exit...")
    sys.exit()

# Auto smart mode
def prepare_filter_mode_smart(scanMode, config, miscData, sensitive=False):
  rootDomainList = miscData['rootDomainList']
  spamDomainsList = miscData['SpamLists']['spamDomainsList'] # List of domains from crowd sourced list
  spamThreadsList = miscData['SpamLists']['spamThreadsList'] # List of filters associated with spam threads from crowd sourced list
  spamAccountsList = miscData['SpamLists']['spamAccountsList'] # List of mentioned instagram/telegram scam accounts from crowd sourced list
  utf_16 = "utf-8"
  if config and config['filter_mode'] == "autosmart":
    pass
  else:
    print("\n--------------------------------------------------------------------------------------------------------------")
    print(f"~~~ This mode is a {F.LIGHTCYAN_EX}spammer's worst nightmare{S.R}. It automatically scans for multiple spammer techniques ~~~\n")
    print(" > Extremely low (near 0%) false positives")
    print(" > Detects whatsapp scammers and '18+ spam' bots")
    print(" > Easily cuts through look-alike characters and obfuscations, including impersonating usernames")
    if sensitive == False:
      print(f" > {F.LIGHTRED_EX}NOTE:{S.R} This mode prioritizes a {F.LIGHTGREEN_EX}VERY low false positive rate{S.R}, at the cost of occasionally missing some spammers.\n")
    elif sensitive == True:
      print(f" > {F.LIGHTRED_EX}NOTE:{S.R} In sensitive mode, {F.LIGHTRED_EX}expect more false positives{S.R}. Recommended to run this AFTER regular Auto Smart Mode.\n")
    input("Press Enter to Begin Scanning...")
    print ("\033[A                                     \033[A") # Erases previous line
    print(" Loading Filters...              ", end="\r")

  # Create Variables
  blackAdWords, redAdWords, yellowAdWords, exactRedAdWords, usernameBlackWords = [], [], [], [], []
  usernameBlackWords, usernameObfuBlackWords = [], []
  spamDomainsRegex, spamAccountsRegex, spamThreadsRegex = [], [], []
  compiledRegexDict = {
    'usernameBlackWords': [],
    'blackAdWords': [],
    'redAdWords': [],
    'yellowAdWords': [],
    'exactRedAdWords': [],
    'usernameRedWords': [],
    'textObfuBlackWords': [],
    'usernameObfuBlackWords': [],
  }

  # General Spammer Criteria
  #usernameBlackChars = ""
  spamGenEmoji_Raw = b'@Sl-~@Sl-};+UQApOJ|0pOJ~;q_yw3kMN(AyyBUh'
  usernameBlackWords_Raw = [b'aA|ICWn^M`', b'aA|ICWn>^?c>', b'Z*CxTWo%_<a$#)', b'c4=WCbY*O1XL4a}', b'Z*CxIZgX^DXL4a}', b'Z*CxIX8', b'V`yb#YanfTAY*7@', b'b7f^9ZFwMLXkh', b'c4>2IbRcbcAY*7@', b'cWHEJATS_yX=D', b'cWHEJAZ~9Uc4=e', b'cWHEJZ*_DaVQzUKc4=e']
  usernameObfuBlackWords_Raw = [b'c4Bp7YjX', b'b|7MPV{3B']
  usernameRedWords = ["whatsapp", "telegram"]
  textObfuBlackWords = ['telegram']
  
  # General Settings
  unicodeCategoriesStrip = ["Mn", "Cc", "Cf", "Cs", "Co", "Cn"] # Categories of unicode characters to strip during normalization

  # Create General Lists
  spamGenEmojiSet = make_char_set(b64decode(spamGenEmoji_Raw).decode(utf_16))
    #usernameBlackCharsSet = make_char_set(usernameBlackChars)
  for x in usernameBlackWords_Raw: usernameBlackWords.append(b64decode(x).decode(utf_16))
  for x in usernameObfuBlackWords_Raw: usernameObfuBlackWords.append(b64decode(x).decode(utf_16))

  # Type 1 Spammer Criteria
  minNumbersMatchCount = 3 # Choice of minimum number of matches from spamNums before considered spam
  spamNums = b'@4S%jypiv`lJC5e@4S@nyp`{~mhZfm@4T4ryqWL3kng;a@4S-lyp!*|l<&Ni@4S}pyqE91nD4xq-+|(hpyH9V;*yBsleOZVw&I?E;+~4|pM-+ovAy7_sN#{K;*quDl8NGzw&I<);+}!xo{R9GgoEI*sp65M;*qxEl8WM!x8j|+;+}%yo{aFHgoNO$sp65N;*q!Fl8fS#xZ<6;;+})zo{jLIgoWafq~ejd;*yNwleyxZy5gRM;+~G;o`m9_j_{v^hT@T>;*q)Hl8xe%y5gO?;+}=#o{#XKgoomhrs9#h;*yTyle^-byyBjQ;+~N3k%YbQpM;3vf|%lwr{a;j;*yWzlf2@cz2csS;+~Q4pM;6xk*MO4yyB9O;*-7Noxb9ph~l1-@SlW=;*+Z4lfUqvgp2T>gpBZ?gn{s%gn;m!pN{aIpP2BSpQ7-cpRDkmpO5gJpPBHTpRMqnpQG@dpSJLwpOEmKpPKNUpRVwopQP}epSSRxpONsLpPTTVpRe$ppQZ4fpSbXypOWyMpPcZWpRn+qpQiAgpSkdzpOf&NpPlfXpRw?rpQrGhpStj!pOo;OpPulYpR(|spQ!MipS$p#pOx^PpP%rZpR@3tpQ-SjpS<v$pO)~QpP=xapS19upQ`YkpS|#%pO^5RpP}%bpSAFvpR4elpT6*&pT7'
  spamPlus = b';+&e|oSEXDmBO*hmf?`8;(@y2f{NmZlj4Y!;)<2xik{-1wBo0_;-|afsDa|BgyN{8;;5tIsHEbkrQ)cj;;5(MsHozot>UPz;;6aesj=dzvf`|=@42Gyyo=$Rt>S^4;+U!8n5g2IrsA2f;+e7Ho2cTPnc|$9;+&h}oSfpEo#LFH;+&u2oS^EOn(CUH@Sl}{@Sl}|@Sl}}@Sl~2@Sl~3@Sl~4@SmQc@SmQd@SmQe@SmQf@SmQg@SmQh@SmQi'
  spamOne = b'@4S)lou7~Jou8TTou8xdou94nou9Yjl8EAywc?$&;+}xwo{I3Fgo59J;*p@@k+c'
  x = b64decode(spamNums).decode(utf_16)
  y = b64decode(spamPlus).decode(utf_16)
  z = b64decode(spamOne).decode(utf_16)

  # Prepare Filters for Type 1 Spammers
  spammerNumbersSet = make_char_set(x)
  regexTest1 = f"[{y}] ?[1]"
  regexTest2 = f"[+] ?[{z}]"
  regexTest3 = f"[{y}] ?[{z}]"
  compiledRegex = re.compile(f"({regexTest1}|{regexTest2}|{regexTest3})")

  # Type 2 Spammer Criteria
  blackAdWords_Raw = [b'V`yb#YanfTAaHVTW@&5', b'Z*XO9AZ>XdaB^>EX>0', b'b7f^9ZFwMYa&Km7Yy', b'V`yb#YanfTAa-eFWp4', b'V`yb#YanoPZ)Rz1', b'V`yb#Yan)MWMyv', b'bYXBHZ*CxMc>', b'Z*CxMc_46UV{~<LWd']
  redAdWords_Raw = [b'W_4q0', b'b7gn', b'WNBk-', b'WFcc~', b'W-4QA', b'W-2OUYX', b'Zgpg3', b'b1HZ', b'F*qv', b'aBp&M']
  yellowAdWords_Raw = [b'Y;SgD', b'Vr5}<bZKUFYy', b'VsB)5', b'XK8Y5a{', b'O~a&QV`yb=', b'Xk}@`pJf', b'Xm4}']
  exactRedAdWords_Raw = [b'EiElAEiElAEiElAEiElAEiElAEiElAEiElAEiElAEiElAEiElAEiC', b'Wq4s@bZmJbcW7aBAZZ|OWo2Y#WB']
  redAdEmoji = b64decode(b'@Sl{P').decode(utf_16)
  yellowAdEmoji = b64decode(b'@Sl-|@Sm8N@Sm8C@Sl>4@Sl;H@Sly0').decode(utf_16)
  hrt = b64decode(b';+duJpOTpHpOTjFpOTmGpOTaCpOTsIpOTvJpOTyKpOT#LpQoYlpOT&MpO&QJouu%el9lkElAZ').decode(utf_16)
  
  # Create Type 2 Lists
  for x in blackAdWords_Raw: blackAdWords.append(b64decode(x).decode(utf_16))
  for x in redAdWords_Raw: redAdWords.append(b64decode(x).decode(utf_16))
  for x in yellowAdWords_Raw: yellowAdWords.append(b64decode(x).decode(utf_16))
  for x in exactRedAdWords_Raw: exactRedAdWords.append(b64decode(x).decode(utf_16))
  

  # Prepare Filters for Type 2 Spammers
  redAdEmojiSet = make_char_set(redAdEmoji)
  yellowAdEmojiSet = make_char_set(yellowAdEmoji)
  hrtSet = make_char_set(hrt)
  
  # Prepare Regex to detect nothing but video link in comment
  onlyVideoLinkRegex = re.compile(r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$")
  compiledRegexDict['onlyVideoLinkRegex'] = onlyVideoLinkRegex

  # Compile regex with upper case, otherwise many false positive character matches
  bufferMatch, addBuffers = "*_~|`", "*_~|`\[\]\(\)'" # Add 'buffer' chars to compensate for obfuscation
  usernameConfuseRegex = re.compile(confusable_regex(miscData['channelOwnerName']))
  m = bufferMatch
  a = addBuffers
  for word in usernameBlackWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['usernameBlackWords'].append([word, value])
  for word in blackAdWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['blackAdWords'].append([word, value])
  for word in redAdWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['redAdWords'].append([word, value])
  for word in yellowAdWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['yellowAdWords'].append([word, value])
  for word in exactRedAdWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=False))
    compiledRegexDict['exactRedAdWords'].append([word, value])
  for word in usernameRedWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['usernameRedWords'].append([word, value])
  for word in textObfuBlackWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['textObfuBlackWords'].append([word, value])
  for word in usernameObfuBlackWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['usernameObfuBlackWords'].append([word, value])

  # Prepare All-domain Regex Expression
  prepString = "\.("
  first = True
  for extension in rootDomainList:
    if first == True:
        prepString += extension
        first = False
    else:
        prepString = prepString + "|" + extension
  sensitivePrepString = prepString + ")"
  prepString = prepString + ")\/"
  rootDomainRegex = re.compile(prepString)
  sensitiveRootDomainRegex = re.compile(sensitivePrepString)

  # Prepare spam domain regex
  for domain in spamDomainsList:
    expression = re.compile(confusable_regex(domain.upper(), include_character_padding=False))
    spamDomainsRegex.append(expression)
  for account in spamAccountsList:
    expression = re.compile(confusable_regex(account.upper(), include_character_padding=True))
    spamAccountsRegex.append(expression)
  for thread in spamThreadsList:
    expression = re.compile(confusable_regex(thread.upper(), include_character_padding=True))
    spamThreadsRegex.append(expression)

  # Prepare Multi Language Detection
  turkish = 'ÇçŞşĞğİ'
  germanic = 'ẞßÄä'
  cyrillic = "гджзклмнпрстфхцчшщыэюяъь"
  japanese = 'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヷヸヹヺーヽヾヿぁあぃいぅうぇえぉおかがきぎぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞゟ'
  languages = [['turkish', turkish, []], ['germanic', germanic, []], ['cyrillic', cyrillic, []], ['japanese', japanese, []]]
  for item in languages:
    item[2] = make_char_set(item[1])

  filterSettings = {
    'spammerNumbersSet': spammerNumbersSet, 
    'compiledRegex': compiledRegex, 
    'minNumbersMatchCount': minNumbersMatchCount, 
    'blackAdWords': blackAdWords, 
    'redAdWords': redAdWords, 
    'yellowAdWords': yellowAdWords, 
    #'usernameBlackCharsSet': usernameBlackCharsSet, 
    'spamGenEmojiSet': spamGenEmojiSet,
    'usernameBlackWords': usernameBlackWords,
    'redAdEmojiSet': redAdEmojiSet,
    'yellowAdEmojiSet': yellowAdEmojiSet,
    'hrtSet': hrtSet,
    'rootDomainRegex': rootDomainRegex,
    'compiledRegexDict': compiledRegexDict,
    'usernameConfuseRegex': usernameConfuseRegex,
    'languages': languages,
    'sensitive': sensitive,
    'sensitiveRootDomainRegex': sensitiveRootDomainRegex,
    'unicodeCategoriesStrip': unicodeCategoriesStrip,
    'spamListsRegex': {
        'spamDomainsRegex':spamDomainsRegex, 
        'spamAccountsRegex':spamAccountsRegex,
        'spamThreadsRegex':spamThreadsRegex
        },
    'spamDomainsRegex': spamDomainsRegex,
    }
  print("                                ") # Erases line that says "loading filters"  
  return filterSettings, None



##########################################################################################
##########################################################################################
###################################### MAIN ##############################################
##########################################################################################
##########################################################################################

def main():
  # Run check on python version, must be 3.6 or higher because of f strings
  if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    print("Error Code U-2: This program requires running python 3.6 or higher! You are running" + str(sys.version_info[0]) + "." + str(sys.version_info[1]))
    input("Press Enter to exit...")
    sys.exit()

  # Declare Global Variables
  global YOUTUBE
  global CURRENTUSER
  User = namedtuple('User', 'id name configMatch')
 
  # Checks system platform to set correct console clear command
  # Clears console otherwise the windows terminal doesn't work with colorama for some reason  
  clear_command = "cls" if platform.system() == "Windows" else "clear"
  os.system(clear_command)

  # Initiates colorama and creates shorthand variables for resetting colors
  init(autoreset=True)
  S.R = S.RESET_ALL
  F.R = F.RESET
  B.R = B.RESET

  print("\nLoading YT Spammer Purge @ " + str(version) + "...")

  # Authenticate with the Google API - If token expired and invalid, deletes and re-authenticates
  
  try:
    YOUTUBE = get_authenticated_service() # Create authentication object
  except Exception as e:
    if "invalid_grant" in str(e):
      print(f"{F.YELLOW}[!] Invalid token{S.R} - Requires Re-Authentication")
      os.remove(TOKEN_FILE_NAME)
      YOUTUBE = get_authenticated_service()
    else:
      print('\n')
      traceback.print_exc() # Prints traceback
      print("----------------")
      print(f"{F.RED}[!!!] Error: {S.R}" + str(e))
      print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
      input(f"\nError Code A-1: {F.RED}Something went wrong during authentication.{S.R} {F.YELLOW}Try deleting the token.pickle file.{S.R} \nPress Enter to exit...")
      sys.exit()

  # Check for config file, load into dictionary 'config'. If no config found, loads data from default config in assets folder
  config = load_config_file()
  if config:
    try:
      configFileVersion = int(config['config_version'])
      if configFileVersion < configVersion:
        configOutOfDate = True
      else:
        configOutOfDate = False
    except:
      configOutOfDate = True
  else:
    configOutOfDate = False
  
  os.system(clear_command)

  if config['use_this_config'] == 'ask' or config['use_this_config'] == True:
    if configOutOfDate == True:
      print(f"{F.YELLOW} WARNING! {S.R} Your config file is {F.YELLOW}out of date{S.R}. If you don't update it or a new one, you might get errors")
      print(f"\n  {F.LIGHTGREEN_EX}> Update it now?{S.R} (Program will {F.CYAN}back up the old file{S.R}, and also attempt to {F.CYAN}copy the settings over{S.R})")
      updateChoice = choice("Update Config File?")
      if updateChoice == True:
        update_config_file(oldVersion=int(config['config_version']), newVersion=configVersion, oldConfig=config)
    if choice(f"\nFound {F.YELLOW}config file{S.R}, use those settings?") == False:
      config = load_config_file(forceDefault = True)
    os.system(clear_command)
  elif config['use_this_config'] == False:
    config = load_config_file(forceDefault = True)
  elif config['use_this_config'] == True:
    pass
  else:
    print("Error C-1: Invalid value in config file for setting 'use_this_config' - Must be 'True', 'False', or 'Ask'")
    input("Press Enter to exit...")
    sys.exit()

           #### Prepare Resources ####
  resourceFolder = "SpamPurge_Resources"
  whitelistPathWithName = os.path.join(resourceFolder, "whitelist.txt")
  spamListFolder = os.path.join(resourceFolder, "Spam_Lists")
  spamListDict = {
      'Lists': {
        'Domains':  {'FileName': "SpamDomainsList.txt"},
        'Accounts': {'FileName': "SpamAccountsList.txt"},
        'Threads':  {'FileName': "SpamThreadsList.txt"}
      },
      'Meta': {
        'VersionInfo': {'FileName': "SpamVersionInfo.json"},
        'SpamListFolder': spamListFolder
        #'LatestLocalVersion': {}
      }
  }
  resourcesDict = {
    'Whitelist': {
      'PathWithName': whitelistPathWithName,
      'FileName': "whitelist.txt",
    }
  }

  print("Checking for updates to program and spam lists...")
  # Check if resources and spam list folders exist, and create them
  if not os.path.isdir(resourceFolder):
    try:
      os.mkdir(resourceFolder)
      # Create readme
      with open(os.path.join(resourceFolder, "_What_Is_This_Folder.txt"), "w") as f:
        f.write("# This Resources folder is used to store resources required for the YT Spammer Purge program.\n")
        f.write("# Note: If you had a previous spam_lists folder that was created in the same folder as \n")
        f.write("# the .exe file, you can delete that old spam_lists folder. The resources folder is the \n")
        f.write("# new location they will be stored.\n")
                
    except:
      print("\nError: Could not create folder. To update the spam lists, try creating a folder called 'SpamPurge_Resources',")
      print("       then inside that, create another folder called 'Spam_Lists'.")

  if os.path.isdir(resourceFolder) and not os.path.isdir(spamListFolder):
    try:
      os.mkdir(spamListFolder)
    except:
      print("\nError: Could not create folder. To update the spam lists, go into the 'SpamPurge_Resources' folder,")
      print("       then inside that, create another folder called 'Spam_Lists'.")

  # Prepare to check and ingest spammer list files
  # Iterate and get paths of each list
  for x,spamList in spamListDict['Lists'].items():
    spamList['Path'] = os.path.join(spamListFolder, spamList['FileName'])
  spamListDict['Meta']['VersionInfo']['Path'] = os.path.join(spamListFolder, spamListDict['Meta']['VersionInfo']['FileName']) # Path to version included in packaged assets folder

  # Check if each spam list exists, if not copy from assets, then get local version number, calculate latest version number
  latestLocalSpamListVersion = "1900.12.31"
  for x, spamList in spamListDict['Lists'].items():
    if not os.path.exists(spamList['Path']):
      copy_asset_file(spamList['FileName'], spamList['Path'])

    listVersion = get_list_file_version(spamList['Path'])
    spamList['Version'] = listVersion
    if parse_version(listVersion) > parse_version(latestLocalSpamListVersion):
      latestLocalSpamListVersion = listVersion

  spamListDict['Meta']['VersionInfo']['LatestLocalVersion'] = latestLocalSpamListVersion

  # Check for version info file, if it doesn't exist, get from assets folder
  if not os.path.exists(spamListDict['Meta']['VersionInfo']['Path']):
    copy_asset_file(spamListDict['Meta']['VersionInfo']['FileName'], spamListDict['Meta']['VersionInfo']['Path'])

  # Get stored spam list version data from json file
  jsonData = open(spamListDict['Meta']['VersionInfo']['Path'], 'r', encoding="utf-8")
  versionInfoJson = str(json.load(jsonData)) # Parses json file into a string
  versionInfo = ast.literal_eval(versionInfoJson) # Parses json string into a dictionary
  spamListDict['Meta']['VersionInfo']['LatestRelease'] = versionInfo['LatestRelease']
  spamListDict['Meta']['VersionInfo']['LastChecked'] = versionInfo['LastChecked']

  # Check for program and list updates if auto updates enabled in config
  try:
    if not config or config['release_channel'] == "all":
      updateReleaseChannel = "all"
    elif config['release_channel'] == "stable":
      updateReleaseChannel = "stable"
    else:
      print("Invalid value for 'release_channel' in config file. Must be 'All' or 'Stable'")
      print("Defaulting to 'All'")
      input("Press Enter to continue...")
      updateReleaseChannel = "all"
  except KeyError:
    print("\nYour version of the config file does not specify a release channel. Defaulting to 'All'")
    print(f"{F.YELLOW}Re-create your config{S.R} to get the latest version.")
    input("\nPress Enter to continue...")
    updateReleaseChannel = "all"

  if not config or config['auto_check_update'] == True:
    try:
      updateAvailable = check_for_update(version, updateReleaseChannel, silentCheck=True, )
    except Exception as e:
      print(f"{F.LIGHTRED_EX}Error Code U-3 occurred while checking for updates. (Checking can be disabled using the config file setting) Continuing...{S.R}\n")      
      updateAvailable = False
    
    # Check if today or tomorrow's date is later than the last update date (add day to account for time zones)
    if datetime.today()+timedelta(days=1) >= datetime.strptime(spamListDict['Meta']['VersionInfo']['LatestLocalVersion'], '%Y.%m.%d'):
      # Only check for updates until the next day
      if datetime.today() > datetime.strptime(spamListDict['Meta']['VersionInfo']['LastChecked'], '%Y.%m.%d.%H.%M')+timedelta(days=1):
        spamListDict = check_lists_update(spamListDict, silentCheck=True)

  else:
    updateAvailable = False

  # In all scenarios, load spam lists into memory  
  for x, spamList in spamListDict['Lists'].items():
    spamList['FilterContents'] = ingest_list_file(spamList['Path'], keepCase=False)
  
  ####### Load Other Data into MiscData #######
  print("\nLoading other assets..\n")
  miscData = {
    'Resources': {},
    'SpamLists':{}
  }
  rootDomainListAssetFile = "rootZoneDomainList.txt"
  rootDomainList = ingest_asset_file(rootDomainListAssetFile)
  miscData['rootDomainList'] = rootDomainList
  miscData['SpamLists']['spamDomainsList'] = spamListDict['Lists']['Domains']['FilterContents']
  miscData['SpamLists']['spamAccountsList'] = spamListDict['Lists']['Accounts']['FilterContents']
  miscData['SpamLists']['spamThreadsList'] = spamListDict['Lists']['Threads']['FilterContents']
  miscData['Resources'] = resourcesDict

  # Create Whitelist if it doesn't exist, 
  if not os.path.exists(whitelistPathWithName):
    with open(whitelistPathWithName, "a") as f:
      f.write("# Commenters whose channel IDs are in this list will always be ignored. You can add or remove IDs (one per line) from this list as you wish.\n")
      f.write("# Channel IDs for a channel can be found in the URL after clicking a channel's name while on the watch page or where they've left a comment.\n")
      f.write("# - Channels that were 'excluded' will also appear in this list.\n")
      f.write("# - Lines beginning with a '#' are comments and aren't read by the program. (But do not put a '#' on the same line as actual data)\n\n")
    miscData['Resources']['Whitelist']['WhitelistContents'] = []
  else:
    miscData['Resources']['Whitelist']['WhitelistContents'] = ingest_list_file(whitelistPathWithName, keepCase=True)

  if config:
    moderator_mode = config['moderator_mode']
  else:
    moderator_mode = False

  os.system(clear_command)
  #----------------------------------- Begin Showing Program ---------------------------------
  print(f"{F.LIGHTYELLOW_EX}\n===================== YOUTUBE SPAMMER PURGE v" + version + f" ====================={S.R}")
  print("=========== https://github.com/ThioJoe/YT-Spammer-Purge ===========")
  print("================= Author: ThioJoe - YouTube.com/ThioJoe ================ \n")

  # Instructions
  print("Purpose: Lets you scan for spam comments and mass-delete them all at once \n")
  print("NOTE: It's probably better to scan individual videos, because you can scan all those comments,")
  print("      but scanning your entire channel must be limited and might miss older spam comments.")
  print("You will be shown the comments to confirm before they are deleted.")

  # While loop until user confirms they are logged into the correct account
  confirmedCorrectLogin = False
  while confirmedCorrectLogin == False:
    # Get channel ID and title of current user, confirm with user
    userInfo = get_current_user(config)
    CURRENTUSER = User(id=userInfo[0], name=userInfo[1], configMatch=userInfo[2]) # Returns [channelID, channelTitle, configmatch]
    print("\n    >  Currently logged in user: " + f"{F.LIGHTGREEN_EX}" + str(CURRENTUSER.name) + f"{S.R} (Channel ID: {F.LIGHTGREEN_EX}" + str(CURRENTUSER.id) + f"{S.R} )")
    if choice("       Continue as this user?", CURRENTUSER.configMatch) == True:
      confirmedCorrectLogin = True
      os.system(clear_command)
    else:
      os.remove(TOKEN_FILE_NAME)
      os.system(clear_command)
      YOUTUBE = get_authenticated_service()

  @dataclass
  class ScanInstance:
    matchedCommentsDict: dict
    vidIdDict: dict
    vidTitleDict: dict
    matchSamplesDict: dict
    authorMatchCountDict: dict
    scannedRepliesCount: int
    scannedCommentsCount: int
    logTime: str
    logFileName: str  

  ##############################################
  ######### PRIMARY INSTANCE FUNCTION ##########
  ##############################################
  ## Allows Re-running Program From Main Menu ##
  ##############################################
  def primaryInstance(miscData):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Instantiate class for primary instance
    current = ScanInstance(
      matchedCommentsDict={}, 
      vidIdDict={}, 
      vidTitleDict={}, 
      matchSamplesDict={}, 
      authorMatchCountDict={}, 
      scannedRepliesCount=0, 
      scannedCommentsCount=0,
      logTime = timestamp, 
      logFileName = None,
      )

    # Declare Default Variables
    maxScanNumber:int = 999999999
    scanVideoID:str = None
    videosToScan:list = []
    nextPageToken:str = "start"
    loggingEnabled:bool = False
    userNotChannelOwner:bool = False

    os.system(clear_command)
    # User selects scanning mode,  while Loop to get scanning mode, so if invalid input, it will keep asking until valid input
    print(f"   [At any prompt, you can enter 'X' to return to this menu]")
    print(f"\n----------------------- {F.YELLOW}Scanning Options{S.R} -----------------------")
    print(f"      1. Scan {F.LIGHTBLUE_EX}specific videos{S.R}")
    print(f"      2. Scan {F.LIGHTCYAN_EX}recent videos{S.R} for a channel")
    print(f"      3. Scan recent comments across your {F.LIGHTMAGENTA_EX}Entire Channel{S.R}")
    print(f"      4. Scan a {F.LIGHTMAGENTA_EX}community post{S.R} (Experimental)")
    print(f"------------------------ {F.LIGHTRED_EX}Other Options{S.R} -------------------------")
    print(f"      5. Create your own config file to quickly run the program with pre-set settings")
    print(f"      6. Recover deleted comments using log file")
    print(f"      7. Check For Updates\n")
    
    # Check for updates silently
    if updateAvailable == True:
      if updateReleaseChannel == "stable":
        print(f"{F.LIGHTGREEN_EX}Notice: A new version is available! Choose 'Check For Updates' option for details.{S.R}\n")
      else:
        print(f"{F.LIGHTGREEN_EX}Notice: A new {F.CYAN}beta{F.LIGHTGREEN_EX} version is available! Choose 'Check For Updates' option for details.{S.R}\n")

    if config and configOutOfDate == True:
      print(f"{F.LIGHTRED_EX}Notice: Your config file is out of date! Choose 'Create your own config file' to generate a new one.{S.R}\n")

    # Make sure input is valid, if not ask again
    validMode = False
    validConfigSetting = True
    while validMode == False:
      if validConfigSetting == True and config and config['scan_mode'] != 'ask':
        scanMode = config['scan_mode']
      else:
        scanMode = input("Choice (1-7): ")

      # Set scanMode Variable Names
      validModeValues = ['1', '2', '3', '4', '5', '6', '7', 'chosenvideos', 'recentvideos', 'entirechannel', 'communitypost']
      if scanMode in validModeValues:
        validMode = True
        if scanMode == "1" or scanMode == "chosenvideos":
          scanMode = "chosenVideos"
        elif scanMode == "2" or scanMode == "recentvideos":
          scanMode = "recentVideos"
        elif scanMode == "3" or scanMode == "entirechannel":
          scanMode = "entireChannel"
        elif scanMode == "4" or scanMode == "communitypost":
          scanMode = "communityPost"
        elif scanMode == "5":
          scanMode = "makeConfig"
        elif scanMode == "6":
          scanMode = "recoverMode"
        elif scanMode == "7":
          scanMode = "checkUpdates"
      else:
        print(f"\nInvalid choice: {scanMode} - Enter either 1, 2, 3, 4, 5, 6, or 7. ")
        validConfigSetting = False

    # If chooses to scan single video - Validate Video ID, get title, and confirm with user
    if scanMode == "chosenVideos":  
      # While loop to get video ID and if invalid ask again
      confirm = False
      validConfigSetting = True
      while confirm == False:
        numVideos = 1
        allVideosMatchBool = True
        miscData['totalCommentCount'] = 0

        # Checks if input list is empty and if contains only valid video IDs
        listNotEmpty = False
        validVideoIDs = False # False just to get into the loop
        while listNotEmpty == False or validVideoIDs == False:
          if validConfigSetting == True and config and config['videos_to_scan'] != 'ask':
            enteredVideosList = string_to_list(config['videos_to_scan'])
            if len(enteredVideosList) == 0:
              validConfigSetting = False
              listNotEmpty = False
              print(f"{F.LIGHTRED_EX}\nError: Video list is empty!{S.R}")
            else:
              listNotEmpty = True
          else:
            print(f"\nEnter a list of {F.YELLOW}Video Links{S.R} or {F.YELLOW}Video IDs{S.R} to scan, separated by commas.")
            print(" > Note: All videos must be from the same channel.")
            enteredVideosList = string_to_list(input("Enter here: "))
            if str(enteredVideosList).lower() == "['x']":
              return True # Return to main menu
            validConfigSetting = False
            if len(enteredVideosList) == 0:
              listNotEmpty = False
              print(f"{F.LIGHTRED_EX}\nError: Video list is empty!{S.R}")
            else:
              listNotEmpty = True

          # Validates all video IDs/Links, gets necessary info about them
          validVideoIDs = True
          videosToScan = []
          videoListResult = [] # True/False, video ID, videoTitle, commentCount, channelID, channelTitle
          for i in range(len(enteredVideosList)):
            videoListResult.append([])
            videosToScan.append({})
            videoListResult[i] = validate_video_id(enteredVideosList[i]) # Sends link or video ID for isolation and validation
            if videoListResult[i][0] == False:
              validVideoIDs = False
              confirm = False
              break

        for i in range(len(videoListResult)): # Change this
          if videoListResult[i][0] == True:
            videosToScan[i]['videoID'] = str(videoListResult[i][1])
            videosToScan[i]['videoTitle'] = str(videoListResult[i][2])
            videosToScan[i]['commentCount'] = int(videoListResult[i][3])
            videosToScan[i]['channelOwnerID'] = str(videoListResult[i][4])
            videosToScan[i]['channelOwnerName'] = str(videoListResult[i][5])
            miscData['totalCommentCount'] += int(videoListResult[i][3])
          else:
            print(f"\nInvalid Video: {enteredVideosList[i]}  |  Video ID = {videoListResult[1]}")
            validConfigSetting = False
            break
          
          # Check each video against first to ensure all on same channel
          if allVideosMatchBool == True:
            misMatchVidIndex = 0
          if videosToScan[0]['channelOwnerID'] != videosToScan[i]['channelOwnerID']:
            misMatchVidIndex += 1
            if allVideosMatchBool == True:
              print(f"\n {F.LIGHTRED_EX}ERROR: Videos scanned together all must be from the same channel.{S.R}")
              print("  The following videos do not match the channel owner of the first video in the list: ")
            if misMatchVidIndex == 11 and len(enteredVideosList) > 10:
              remainingCount = str(len(enteredVideosList) - 10)
              userChoice = choice(f"There are {remainingCount} more mis-matched videos, do you want to see the rest?")
              if userChoice == False:
                break
              elif userChoice == None:
                return True # Return to main menu
            print(f"  {misMatchVidIndex}. {str(videosToScan[i]['videoTitle'])}")
            validConfigSetting = False
            allVideosMatchBool = False

        # If videos not from same channel, skip and re-prompt    
        if allVideosMatchBool == True:       
          # Print video titles, if there are many, ask user to see all if more than 5
          i = 0
          print(f"\n{F.BLUE}Chosen Videos:{S.R}")
          for video in videosToScan:
            i += 1
            if i==6 and len(enteredVideosList) > 5:
              remainingCount = str(len(enteredVideosList) - 5)
              userChoice = choice(f"You have entered many videos, do you need to see the rest (x{remainingCount})?")
              if userChoice == False:
                break
              elif userChoice == None:
                return True # Return to main menu
            print(f" {i}. {video['videoTitle']}")
          print("")
          
          if CURRENTUSER.id != videosToScan[0]['channelOwnerID']:
            userNotChannelOwner = True

          miscData['channelOwnerID'] = videosToScan[0]['channelOwnerID']
          miscData['channelOwnerName'] = videosToScan[0]['channelOwnerName']
          
          # Ask if correct videos, or skip if config
          if config and config['skip_confirm_video'] == True:
            confirm = True
          else:
            if userNotChannelOwner == True and moderator_mode == False:
              print(f"{F.LIGHTRED_EX}NOTE: This is not your video. Enabling '{F.YELLOW}Not Your Channel Mode{F.LIGHTRED_EX}'. You can report spam comments, but not delete them.{S.R}")
            elif userNotChannelOwner == True and moderator_mode == True:
              print(f"{F.LIGHTRED_EX}NOTE: {F.YELLOW}Moderator Mode is enabled{F.LIGHTRED_EX}. You can hold comments for review when using certain modes{S.R}")
            print("Total number of comments to scan: " + str(miscData['totalCommentCount']))
            if miscData['totalCommentCount'] >= 100000:
              print(f"\n{B.YELLOW}{F.BLACK} WARNING: {S.R} You have chosen to scan a large amount of comments. The default API quota limit ends up")
              print(f" around {F.YELLOW}10,000 comment deletions per day{S.R}. If you find more spam than that you will go over the limit.")
              print(f"        > Read more about the quota limits for this app here: {F.YELLOW}TJoe.io/api-limit-info{S.R}")
              if userNotChannelOwner == True or moderator_mode == True:
                print(f"{F.LIGHTCYAN_EX}> Note:{S.R} You may want to disable 'check_deletion_success' in the config, as this doubles the API cost! (So a 5K limit)")
            confirm = choice("Is this video list correct?", bypass=validConfigSetting)
            if confirm == None:
              return True # Return to main menu

    elif scanMode == "recentVideos":
      confirm = False
      validEntry = False
      validChannel = False
      
      while validChannel == False:
        # Get and verify config setting for channel ID
        if config and config['channel_to_scan'] != 'ask':
          if config['channel_to_scan'] == 'mine':
            channelID = CURRENTUSER.id
            channelTitle = CURRENTUSER.name
            validChannel = True
            break
          else:
            validChannel, channelID, channelTitle = validate_channel_id(config['channel_to_scan'])
            if validChannel == True:
              break
            else:
              print("Invalid Channel ID or Link in config file!")

        print(f"\nEnter a {F.YELLOW}channel ID or Link{S.R} to scan {F.LIGHTCYAN_EX}recent videos{S.R} from")
        print(f"   > If scanning {F.YELLOW}your own channel{S.R}, just hit {F.LIGHTGREEN_EX}Enter{S.R}")
        inputtedChannel = input("\nEnter Here: ")
        if inputtedChannel == "":
          channelID = CURRENTUSER.id
          channelTitle = CURRENTUSER.name
          validChannel = True
        elif str(inputtedChannel).lower() == "x":
          return True # Return to main menu
        else:
          validChannel, channelID, channelTitle = validate_channel_id(inputtedChannel)

      if CURRENTUSER.id != channelID:
        userNotChannelOwner = True

      print(f"\nChosen Channel: {F.LIGHTCYAN_EX}{channelTitle}{S.R}")
      
      # Get number of recent videos to scan, either from config or user input, and validate
      while validEntry == False or confirm == False:
        videosToScan=[]
        validConfigSetting = True
        if config and config['recent_videos_amount'] != 'ask' and validConfigSetting == True:
          numVideos = config['recent_videos_amount']
          try:
            numVideos = int(numVideos)
          except:
            validConfigSetting = False
            print("Invalid number entered in config file for recent_videos_amount")
            numVideos = None
        else:
          print(f"\nEnter the {F.YELLOW}number most recent videos{S.R} to scan back-to-back:")
          numVideos = input("\nNumber of Recent Videos: ")
          if str(numVideos).lower() == "x":
            return True # Return to main menu
        try:
          numVideos = int(numVideos)
          if numVideos > 0 and numVideos <= 500:
            validEntry = True
            validConfigSetting = True
          else:
            print("Error: Entry must be from 1 to 500 (the YouTube API Limit)")
            validEntry = False
            validConfigSetting = False
        except ValueError:
          print(f"{F.LIGHTRED_EX}Error:{S.R} Entry must be a whole number greater than zero.")
        
        if validEntry == True and numVideos >= 100:
          print(f"\n{B.YELLOW}{F.BLACK} WARNING: {S.R} You have chosen to scan a large amount of videos. With the default API quota limit,")
          print(f" every 100 videos will use up 20% of the quota {F.YELLOW}just from listing the videos alone, before any comment scanning.{S.R}")
          print(f"        > Read more about the quota limits for this app here: {F.YELLOW}TJoe.io/api-limit-info{S.R}")

        if validEntry == True:
          # Fetch recent videos and print titles to user for confirmation
          videosToScan = get_recent_videos(channelID, numVideos)
          if str(videosToScan) == "MainMenu":
            return True # Return to main menu
          # Get total comment count
          miscData['totalCommentCount'] = 0
          for video in videosToScan:
            miscData['totalCommentCount'] += int(video['commentCount'])

          if len(videosToScan) < numVideos:
            print(f"\n{F.YELLOW} WARNING:{S.R} Only {len(videosToScan)} videos found.")
          print("\nRecent Videos To Be Scanned:")
          for i in range(len(videosToScan)):
            if i == 10 and len(videosToScan) > 11:
              remainingCount = str(len(videosToScan) - 10)
              userChoice = choice(f"There are {remainingCount} more recent videos, do you want to see the rest?")
              if userChoice == False:
                break 
              elif userChoice == None:
                return True # Return to main menu         
            print(f"  {i+1}. {videosToScan[i]['videoTitle']}")

          if config and (config['skip_confirm_video'] == True and validConfigSetting == True):
            confirm = True
          else:
            if userNotChannelOwner == True and moderator_mode == False:
              print(f"{F.LIGHTRED_EX}NOTE: These aren't your videos. Enabling '{F.YELLOW}Not Your Channel Mode{F.LIGHTRED_EX}'. You can report spam comments, but not delete them.{S.R}")
            elif userNotChannelOwner == True and moderator_mode == True:
              print(f"{F.LIGHTRED_EX}NOTE: {F.YELLOW}Moderator Mode is enabled{F.LIGHTRED_EX}. You can hold comments for review when using certain modes{S.R}")
            print("\nTotal number of comments to scan: " + str(miscData['totalCommentCount']))
            if miscData['totalCommentCount'] >= 100000:
              print(f"\n{B.YELLOW}{F.BLACK} WARNING: {S.R} You have chosen to scan a large amount of comments. The default API quota limit ends up")
              print(f" around {F.YELLOW}10,000 comment deletions per day{S.R}. If you find more spam than that you will go over the limit.")
              print(f"        > Read more about the quota limits for this app here: {F.YELLOW}TJoe.io/api-limit-info{S.R}")
              if userNotChannelOwner == True or moderator_mode == True:
                print(f"{F.LIGHTCYAN_EX}> Note:{S.R} You may want to disable 'check_deletion_success' in the config, as this doubles the API cost! (So a 5K limit)")
            confirm = choice("Is everything correct?", bypass=config['skip_confirm_video'])
            if confirm == None:
              return True # Return to main menu

      miscData['channelOwnerID'] = channelID
      miscData['channelOwnerName'] = channelTitle

    # If chooses to scan entire channel - Validate Channel ID
    elif scanMode == "entireChannel":
      numVideos = 1 # Using this variable to indicate only one loop of scanning done later
      # While loop to get max scan number, not an integer, asks again
      validInteger = False
      if config: validConfigSetting = True
      while validInteger == False:
        try:
          if validConfigSetting == True and config and config['max_comments'] != 'ask':
            maxScanNumber = int(config['max_comments'])
          else:
            maxScanNumber = input(f"Enter the maximum {F.YELLOW}number of comments{S.R} to scan: ")
            if str(maxScanNumber).lower() == "x":
              return True # Return to main menu
            maxScanNumber = int(maxScanNumber)

            if maxScanNumber >= 100000:
              print(f"\n{B.YELLOW}{F.BLACK} WARNING: {S.R} You have chosen to scan a large amount of comments. The default API quota limit ends up")
              print(f" around {F.YELLOW}10,000 comment deletions per day{S.R}. If you find more spam than that you will go over the limit.")
              print(f"        > Read more about the quota limits for this app here: {F.YELLOW}TJoe.io/api-limit-info{S.R}")
              if userNotChannelOwner == True or moderator_mode == True:
                print(f"{F.LIGHTCYAN_EX}> Note:{S.R} You may want to disable 'check_deletion_success' in the config, as this doubles the API cost! (So a 5K limit)")
              userChoice = choice("Do you still want to continue?")
              if userChoice == False:
                validInteger == False
              elif userChoice == None:
                return True # Return to main menu

          if maxScanNumber > 0:
            validInteger = True # If it gets here, it's an integer, otherwise goes to exception
          else:
            print("\nInvalid Input! Number must be greater than zero.")
            validConfigSetting = False
        except:
          print("\nInvalid Input! - Must be a whole number.")
          validConfigSetting = False

      miscData['channelOwnerID'] = CURRENTUSER.id
      miscData['channelOwnerName'] = CURRENTUSER.name

    elif scanMode == 'communityPost':
      print(f"\nNOTES: This mode is {F.YELLOW}experimental{S.R}, and not as polished as other features. Expect some janky-ness.")
      print("   > It is also much slower to retrieve comments, because it does not use the API")
      print(f"   > You should only scan {F.YELLOW}your own{S.R} community posts, or things might not work right")
      confirm = False
      while confirm == False:
        communityPostInput = input("\nEnter the ID or link of the community post: ")
        if str(communityPostInput).lower() == "x":
          return True # Return to main menu
        # Validate post ID or link, get additional info about owner, and useable link
        isValid, communityPostID, postURL, postOwnerID, postOwnerUsername = validate_post_id(communityPostInput)
        if isValid == True:
          print("\nCommunity Post By: " + postOwnerUsername)
          if postOwnerID != CURRENTUSER.id:
            userNotChannelOwner = True
            print("\nWarning: You are scanning someone elses post. 'Not Your Channel Mode' Enabled.")
          confirm = choice("Continue?")
          if confirm == None:
            return True # Return to main menu
        else:
          print("Problem interpreting the post information, please check the link or ID.")
      miscData['channelOwnerID'] = postOwnerID
      miscData['channelOwnerName'] = postOwnerUsername 

      # Checking config for max comments in config
      if config and config['max_comments'] != 'ask':
        validInteger = False 
        try:
          maxScanNumber = int(config['max_comments'])
          if maxScanNumber > 0:
            validInteger = True
          else:
            pass
        except:
          pass

        if validInteger == False:
          print("\nInvalid max_comments setting in config! Number must a whole number be greater than zero.")
        while validInteger == False:
          maxScanInput = input(f"\nEnter the maximum {F.YELLOW}number of comments{S.R} to scan: ")
          if str(maxScanInput).lower() == "x":
            return True # Return to main menu
          try:
            maxScanNumber = int(maxScanInput)
            if maxScanNumber > 0:
              validInteger = True # If it gets here, it's an integer, otherwise goes to exception
            else:
              print("\nInvalid Input! Number must a whole number be greater than zero.")
          except:
            print("\nInvalid Input! - Must be a whole number greater than zero.")
        
    # Create config file
    elif scanMode == "makeConfig":
      if configOutOfDate == False:
        print(f"\n{F.LIGHTGREEN_EX}Config file already up to date!{S.R}")
        print(f"\nDo you want to {F.YELLOW}restore the default{S.R} config settings? (Overwrites current config file)")
        confirm = choice("Overwrite config and restore defaults?")
        if confirm == True:
          result = create_config_file(dontWarn=True)
        elif confirm == False or confirm == None:
          input("Press Enter to Return to main menu...")
          return True
        input("Press Enter to Return to main menu...")
        return True
      else:
        result = create_config_file()
        if str(result) == "MainMenu":
          return True

    # Check for latest version
    elif scanMode == "checkUpdates":
      check_lists_update(spamListDict)
      check_for_update(version, updateReleaseChannel)
      input("\nPress Enter to return to main menu...")
      return True

    # Recove deleted comments mode
    elif scanMode == "recoverMode":
      result = recover_deleted_comments()
      if str(result) == "MainMenu":
        return True

    # User inputs filtering mode
    print("\n-------------------------------------------------------")
    print(f"~~~~~~~~~~~ Choose how to identify spammers ~~~~~~~~~~~")
    print("-------------------------------------------------------")
    print(f" 1. {F.BLACK}{B.LIGHTGREEN_EX}(RECOMMENDED):{S.R} {F.YELLOW}Auto-Smart Mode{S.R}: Automatically detects multiple spammer techniques")
    print(f" 2. {F.YELLOW}Sensitive-Smart Mode{S.R}: Much more likely to catch all spammers, but with significantly more false positives")  
    print(f" 3. Enter Spammer's {F.LIGHTRED_EX}channel ID(s) or link(s){S.R}")
    print(f" 4. Scan {F.LIGHTBLUE_EX}usernames{S.R} for criteria you choose")
    print(f" 5. Scan {F.CYAN}comment text{S.R} for criteria you choose")
    print(f" 6. Scan both {F.LIGHTBLUE_EX}usernames{S.R} and {F.CYAN}comment text{S.R} for criteria you choose")
    print(f" 7. ASCII Mode: Scan usernames for {F.LIGHTMAGENTA_EX}ANY non-ASCII special characters{S.R} (May cause collateral damage!)")


    if userNotChannelOwner == True and moderator_mode == False:
      print(f" {F.LIGHTRED_EX}Note: With 'Not Your Channel Mode' enabled, you can only report matched comments while using 'Auto-Smart Mode'.{S.R}") # Based on filterModesAllowedforNonOwners
    elif userNotChannelOwner == True and moderator_mode == True:
      print(f" {F.LIGHTRED_EX}Note: With 'Moderator Mode', you can hold for review using: 'Auto-Smart', 'Sensitive-Smart', and Channel ID modes.{S.R}")
    # Make sure input is valid, if not ask again
    validFilterMode = False
    validFilterSubMode = False
    filterSubMode = None
    validConfigSetting = True

    validConfigSetting = True
    while validFilterMode == False:
      if validConfigSetting == True and config and config['filter_mode'] != 'ask':
        filterChoice = config['filter_mode']
      else:
        filterChoice = input("\nChoice (1-7): ")
      
      if str(filterChoice).lower() == "x":
        return True # Return to main menu

      validChoices = ['1', '2', '3', '4', '5', '6', '7', 'id', 'username', 'text', 'nameandtext', 'autoascii', 'autosmart', 'sensitivesmart']
      if filterChoice in validChoices:
        validFilterMode = True
        # Set string variable names for filtering modes
        if filterChoice == "1" or filterChoice == "autosmart":
          filterMode = "AutoSmart"
        elif filterChoice == "2" or filterChoice == "sensitivesmart":
          filterMode = "SensitiveSmart"      
        elif filterChoice == "3" or filterChoice == "id":
          filterMode = "ID"
        elif filterChoice == "4" or filterChoice == "username":
          filterMode = "Username"
        elif filterChoice == "5" or filterChoice == "text":
          filterMode = "Text"
        elif filterChoice == "6" or filterChoice == "nameandtext":
          filterMode = "NameAndText"
        elif filterChoice == "7" or filterChoice == "autoascii":
          filterMode = "AutoASCII"

      else:
        print(f"\nInvalid Filter Mode: {filterChoice} - Enter either 1, 2, 3, 4, 5, 6, or 7")
        validConfigSetting = False

    ## Get filter sub-mode to decide if searching characters or string
    validConfigSetting = None
    if config and config['filter_submode'] != 'ask':
      filterSubMode = config['filter_submode']
      validConfigSetting = True
    else:
      validConfigSetting = False

    if filterMode == "Username" or filterMode == "Text" or filterMode == "NameAndText":
      print("\n--------------------------------------------------------------")
      if filterMode == "Username":
        print("~~~ What do you want to scan usernames for specifically? ~~~")
      elif filterMode == "Text":
        print("~~~ What do you want to scan comment text for specifically? ~~~")
      elif filterMode == "NameAndText":
        print("~~~ What do you want to scan names and comments for specifically? ~~~")
      print(f" 1. A {F.CYAN}certain special character{S.R}, or set of multiple characters")
      print(f" 2. An {F.LIGHTMAGENTA_EX}entire string{S.R}, or multiple strings")
      print(f" 3. Advanced: A custom {F.YELLOW}Regex pattern{S.R} you'll enter")

      while validFilterSubMode == False:
        if validConfigSetting == True:
          pass
        else:
          filterSubMode = input("\nChoice (1, 2, or 3): ")
        if str(filterSubMode).lower() == "x":
          return True # Return to main menu

        validFilterSubModes = ["1", "2", "3", "characters", "strings", "regex"]
        if filterSubMode in validFilterSubModes:
          validFilterSubMode = True
          validConfigSetting = True
          if filterSubMode == "1" or filterSubMode == "characters":
            filterSubMode = "chars"
          elif filterSubMode == "2" or filterSubMode == "strings":
            filterSubMode = "string"
          elif filterSubMode == "3" or filterSubMode == "regex":
            filterSubMode = "regex"
        else:
          print(f"\nInvalid choice: {filterSubMode} - Enter 1, 2 or 3")
          validConfigSetting = False


    ### Prepare Filtering Modes ###
    # Default values for filter criteria
    inputtedSpammerChannelID = None
    inputtedUsernameFilter = None
    inputtedCommentTextFilter = None
    regexPattern = ""

    if filterMode == "ID":
      filterSettings = prepare_filter_mode_ID(scanMode, config)
      inputtedSpammerChannelID = filterSettings[0]

    elif filterMode == "AutoASCII":
      filterSettings = prepare_filter_mode_non_ascii(scanMode, config)
      regexPattern = filterSettings[0]

    elif filterMode == "AutoSmart":
      filterSettings = prepare_filter_mode_smart(scanMode, config, miscData)
      inputtedUsernameFilter = filterSettings[0]
      inputtedCommentTextFilter = filterSettings[0]
    elif filterMode == "SensitiveSmart":
      filterSettings = prepare_filter_mode_smart(scanMode, config, miscData, sensitive=True)
      inputtedUsernameFilter = filterSettings[0]
      inputtedCommentTextFilter = filterSettings[0]

    elif filterSubMode == "chars":
      filterSettings = prepare_filter_mode_chars(scanMode, filterMode, config)
    elif filterSubMode == "string":
      filterSettings = prepare_filter_mode_strings(scanMode, filterMode, config)
    elif filterSubMode == "regex":
      filterSettings = prepare_filter_mode_regex(scanMode, filterMode, config)
      regexPattern = filterSettings[1]

    if filterSettings[0] == "MainMenu":
      return True

    if filterSubMode != "regex":
      if filterMode == "Username":
        inputtedUsernameFilter = filterSettings[0]
      elif filterMode == "Text":
        inputtedCommentTextFilter = filterSettings[0]
      elif filterMode == "NameAndText":
        inputtedUsernameFilter = filterSettings[0]
        inputtedCommentTextFilter = filterSettings[0]

    ##################### START SCANNING #####################

    if scanMode == "communityPost":
      def scan_community_post(communityPostID, limit):
        allCommunityCommentsDict = get_community_comments(communityPostID=communityPostID, limit=limit)
        for key, value in allCommunityCommentsDict.items():
          currentCommentDict = {
            'authorChannelID':value['authorChannelID'], 
            'parentAuthorChannelID':None, 
            'authorChannelName':value['authorName'], 
            'commentText':value['commentText'],
            'commentID':key,
            }
          check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID=communityPostID)
      scan_community_post(communityPostID, maxScanNumber)

    else:
      # Goes to get comments for first page
      print("\n------------------------------------------------------------------------------")
      print("(Note: If the program appears to freeze, try right clicking within the window)\n")
      print("                          --- Scanning --- \n")

      filtersDict = { 'filterMode': filterMode,
                      'filterSubMode': filterSubMode,
                      'CustomChannelIdFilter': inputtedSpammerChannelID,
                      'CustomUsernameFilter': inputtedUsernameFilter,
                      'CustomCommentTextFilter': inputtedCommentTextFilter,
                      'CustomRegexPattern': regexPattern 
                      }
      
      # ----------------------------------------------------------------------------------------------------------------------
      def scan_video(miscData, config, filtersDict, scanVideoID, videosToScan=None, videoTitle=None, showTitle=False, i=1):
        nextPageToken = get_comments(current, filtersDict, miscData, config, scanVideoID, videosToScan=videosToScan)
        if showTitle == True and len(videosToScan) > 0:
          # Prints video title, progress count, adds enough spaces to cover up previous stat print line
          offset = 95 - len(videoTitle)
          if offset > 0:
            spacesStr = " " * offset
          else:
            spacesStr = ""
          print(f"Scanning {i}/{len(videosToScan)}: " + videoTitle + spacesStr + "\n")

        print_count_stats(current, miscData, videosToScan, final=False)  # Prints comment scan stats, updates on same line
        # After getting first page, if there are more pages, goes to get comments for next page
        while nextPageToken != "End" and current.scannedCommentsCount < maxScanNumber:
          nextPageToken = get_comments(current, filtersDict, miscData, config, scanVideoID, nextPageToken, videosToScan=videosToScan)
      # ----------------------------------------------------------------------------------------------------------------------

      if scanMode == "entireChannel":
        scan_video(miscData, config, filtersDict, scanVideoID)
      elif scanMode == "recentVideos" or scanMode == "chosenVideos":
        i = 1
        for video in videosToScan:
          scanVideoID = str(video['videoID'])
          videoTitle = str(video['videoTitle'])
          scan_video(miscData, config, filtersDict, scanVideoID, videosToScan=videosToScan, videoTitle=videoTitle, showTitle=True, i=i)
          i += 1
      print_count_stats(current, miscData, videosToScan, final=True)  # Prints comment scan stats, finalizes
    
    ##########################################################
    bypass = False
    if config and config['enable_logging'] != 'ask':
      logSetting = config['enable_logging']
      if logSetting == True:
        loggingEnabled = True
        bypass = True
      elif logSetting == False:
        loggingEnabled = False
        bypass = True
      elif logSetting == "ask":
        bypass = False
      else:
        bypass = False
        print("Error Code C-2: Invalid value for 'enable_logging' in config file:  " + logSetting)

    # Counts number of found spam comments and prints list
    spam_count = len(current.matchedCommentsDict)
    if spam_count == 0: # If no spam comments found, exits
      print(f"{B.RED}{F.BLACK} No matched comments or users found! {F.R}{B.R}{S.R}\n")
      print(f"If you see missed spam or false positives, you can submit a filter suggestion here: {F.YELLOW}TJoe.io/filter-feedback{S.R}")
      if bypass == False:
        input("\nPress Enter to return to main menu...")
        return True
      elif bypass == True:
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit()
    print(f"Number of Matched Comments Found: {B.RED}{F.WHITE} {str(len(current.matchedCommentsDict))} {F.R}{B.R}{S.R}")

    if bypass == False:
      # Asks user if they want to save list of spam comments to a file
      print(f"\nSpam comments ready to display. Also {F.LIGHTGREEN_EX}save a log file?{S.R} {B.GREEN}{F.BLACK} Highly Recommended! {F.R}{B.R}{S.R}")
      print(f"        (It even allows you to {F.LIGHTGREEN_EX}restore{S.R} deleted comments later)")
      loggingEnabled = choice(f"Save Log File (Recommended)?")
      if loggingEnabled == None:
        return True # Return to main menu
      print("")

    # Prepare logging
    logMode = None
    logFileType = None
    jsonSettingsDict = {}
    jsonLogging = False
    if loggingEnabled == True:
      if config and config['log_mode']:
        logMode = config['log_mode']
        if logMode == "rtf":
          logFileType = ".rtf"
        elif logMode == "plaintext":
          logFileType = ".txt"
        else:
          print("Invalid value for 'log_mode' in config file:  " + logMode)
          print("Defaulting to .rtf file")
          logMode = "rtf"
      else:
        logMode =  "rtf"
        logFileType = ".rtf"

      # Prepare log file names
      fileNameBase = "Spam_Log_" + current.logTime
      fileName = fileNameBase + logFileType

      if config:
        try:
          # Get json logging settings
          if config['json_log'] == True:
            jsonLogging = True
            jsonLogFileName = fileNameBase + ".json"
            jsonSettingsDict['channelOwnerID'] = miscData['channelOwnerID']
            jsonSettingsDict['channelOwnerName'] = miscData['channelOwnerName']

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
      else:
        jsonLogging = False
      

      # Set where to put log files      
      defaultLogPath = "logs"
      if config and config['log_path']:
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
      def write_func(logFileName, string, logMode, numLines):
        rtfLineEnd = ("\\line"*numLines) + " "
        newLines = "\n"*numLines
        if logMode == "rtf":
          write_rtf(logFileName, make_rtf_compatible(string) + rtfLineEnd)
        elif logMode == "plaintext":
          write_plaintext_log(logFileName, string + newLines)

      # Creates log file and writes first line
      if logMode == "rtf":
        write_rtf(current.logFileName, firstWrite=True)
        write_func(current.logFileName, "\\par----------- YouTube Spammer Purge Log File -----------", logMode, 2)
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
        write_func(current.logFileName, "Characters searched in Usernames and Comment Text: " + ", ".join(filterSettings[1]), logMode, 2)
      elif filterMode == "AutoASCII":
        write_func(current.logFileName, "Automatic Search Mode: " + str(filterSettings[1]), logMode, 2)
      elif filterMode == "AutoSmart":
        write_func(current.logFileName, "Automatic Search Mode: Smart Mode ", logMode, 2)
      elif filterMode == "SensitiveSmart":
        write_func(current.logFileName, "Automatic Search Mode: Sensitive Smart ", logMode, 2)
      write_func(current.logFileName, "Number of Matched Comments Found: " + str(len(current.matchedCommentsDict)), logMode, 2)
      write_func(current.logFileName, f"IDs of Matched Comments: \n[ {', '.join(current.matchedCommentsDict)} ] ", logMode, 3)
    else:
      print("Continuing without logging... \n")

    jsonSettingsDict['jsonLogging'] = jsonLogging

    # Prints list of spam comments
    if scanMode == "communityPost":
      scanVideoID = communityPostID
    print("\n\nAll Matched Comments: \n")

    print_comments(current, scanVideoID, list(current.matchedCommentsDict.keys()), loggingEnabled, scanMode, logMode)

    try:
      if jsonSettingsDict['jsonLogging']:
        if config['json_extra_data'] == True:
          jsonDataDict = get_extra_json_data(list(current.matchSamplesDict.keys()), jsonSettingsDict)
          jsonDataDict['Comments'] = current.matchedCommentsDict
          write_json_log(jsonSettingsDict, jsonDataDict, firstWrite=True)
        else:
          write_json_log(jsonSettingsDict, current.matchedCommentsDict, firstWrite=True)
    except KeyError:
      print("Problem getting json config settings. Is your config file up to date / correct?")

    print(f"\n{F.WHITE}{B.RED} NOTE: {S.R} Check that all comments listed above are indeed spam.")
    print(f" > If you see missed spam or false positives, you can submit a filter suggestion here: {F.YELLOW}TJoe.io/filter-feedback{S.R}")

    print()

    ### ---------------- Decide whether to skip deletion ----------------
    # Defaults
    deletionEnabled = False
    deletionMode = None # Should be changed later, but if missed it will default to heldForReview
    confirmDelete = None # If None, will later cause user to be asked to delete
    if moderator_mode == False:
      filterModesAllowedforNonOwners = ["AutoSmart"]
    elif moderator_mode == True:
      filterModesAllowedforNonOwners = ["AutoSmart", "SensitiveSmart", 'ID']
    
    # If user isn't channel owner and not using allowed filter mode, skip deletion
    if userNotChannelOwner == True and filterMode not in filterModesAllowedforNonOwners:
      confirmDelete = False
      deletionEnabled = False
    elif not config:
      deletionEnabled = "Allowed" # If no config, no need to use all the below, skip right to prompt how to process

    # Test skip_deletion preference - If passes both, will either delete or ask user to delete
    elif config['skip_deletion'] == True:
      return True
    elif config['skip_deletion'] != False:
      print("Error Code C-3: Invalid value for 'skip_deletion' in config file. Must be 'True' or 'False':  " + str(config['skip_deletion']))
      input("\nPress Enter to exit...")
      sys.exit()
    ### ----------------------------------------------------------------  

    ### ------------- Decide whether to ask before deleting -------------
    # Using config to determine deletion type, block invalid settings
    elif config['delete_without_reviewing'] == False:
      deletionEnabled = "Allowed"
      if config['removal_type'] == "reportspam" or userNotChannelOwner == True:
        deletionMode = "reportSpam"
      elif config['removal_type'] == "heldforreview":
        deletionMode = "heldForReview"
      elif config['removal_type'] == "rejected":
        deletionMode = "rejected"
      else:
        print("Error Code C-4: Invalid value for 'removal_type' in config file. Must be 'heldforreview', 'rejected', or 'reportSpam':  " + config['removal_type'])
        input("\nPress Enter to exit...")
        sys.exit()

    # User wants to automatically delete with no user intervention
    elif config['delete_without_reviewing'] == True:
      if userNotChannelOwner == True:
          confirmDelete = "REPORT"
          deletionMode = "reportSpam"
          deletionEnabled = True
      elif config['removal_type'] == "reportspam" or config['removal_type'] == "heldforreview":
        if filterMode == "AutoSmart" or filterMode == "ID":
          deletionEnabled = True
          if config['removal_type'] == "reportspam":
            deletionMode = "reportSpam"
            confirmDelete = "REPORT"
          elif config['removal_type'] == "heldforreview":
            deletionMode = "heldForReview"
            confirmDelete = "DELETE"
        else:
          # If non-permitted filter mode with delete_without_reviewing, will allow deletion, but now warns and requires usual confirmation prompt
          print("Error Code C-5: 'delete_without_reviewing' is set to 'True' in config file. So only filter mode 'AutoSmart' allowed..\n")
          print("Next time use one of those filter modes, or set 'delete_without_reviewing' to 'False'.")
          print("    > For this run, you will be asked to confirm removal of spam comments.")
          input("\nPress Enter to continue...")
          confirmDelete = None
          deletionEnabled = "Allowed"
      else:
        print("Error Code C-6: 'delete_without_reviewing' is set to 'True' in config file. So 'removal_type' must be either 'heldForReview' or 'reportSpam'.\n")
        print("Next time, either set one of those removal types, or set 'delete_without_reviewing' to 'False'.")
        print("    > For this run, you will be asked to confirm removal of spam comments.")
        input("\nPress Enter to continue...")
        confirmDelete = None
        deletionEnabled = "Allowed"
    else:
      # Catch Invalid value    
      print("Error C-7: Invalid value for 'delete_without_reviewing' in config file. Must be 'True' or 'False':  " + config['delete_without_reviewing'])
      input("\nPress Enter to exit...")
      sys.exit()

    
    # Check if deletion is enabled, otherwise block and quit
    if deletionEnabled != "Allowed" and deletionEnabled != True:
        print("\nThe deletion functionality was not enabled. Cannot delete or report comments.")
        print("Possible Cause: You're scanning someone elses video with a non-supported filter mode.\n")
        print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
        input("\nPress Enter to return to main menu...")
        return True


    ### ---------------- Set Up How To Handle Comments  ----------------
    # If not skipped by config, ask user what to do
    if confirmDelete == None:
      exclude = False
      # Menu for deletion mode
      while confirmDelete != "DELETE" and confirmDelete != "REPORT" and confirmDelete != "HOLD":
        # Title
        if exclude == False:
          print(f"{F.YELLOW}How do you want to handle the matched comments above?{S.R}")
        elif exclude == True:
          print(f"{F.YELLOW}How do you want to handle the rest of the comments (not ones you {F.LIGHTGREEN_EX}excluded{F.YELLOW})?{S.R}")
        if userNotChannelOwner == True and moderator_mode == False:
          print(f"{F.GREEN}~~ Not Your Channel Mode: Only Reporting is Possible ~~{S.R}")
        if userNotChannelOwner == True and moderator_mode == True:
          print(f"{F.GREEN}~~ Moderator Mode: Reporting and Holding for Review is possible ~~{S.R}")

        # Exclude
        if exclude == False:
          print(f" > To {F.LIGHTGREEN_EX}exclude certain authors{S.R}: Type \'{F.LIGHTGREEN_EX}exclude{S.R}\' followed by a list of the numbers {F.LIGHTMAGENTA_EX}in the sample list{S.R} next to those authors")
          print("      > Example:  exclude 1, 12, 9")

        # Delete Instructions
        if exclude == False:
          if userNotChannelOwner == False:
            print(f" > To {F.LIGHTRED_EX}delete ALL of the above comments{S.R}: Type ' {F.LIGHTRED_EX}DELETE{S.R} ' exactly (in all caps), then hit Enter.")
          if userNotChannelOwner == False or moderator_mode == True:
            print(f" > To {F.LIGHTRED_EX}move ALL comments above to 'Held For Review' in YT Studio{S.R}: Type ' {F.LIGHTRED_EX}HOLD{S.R} ' exactly (in all caps), then hit Enter.")
        elif exclude == True:
          if userNotChannelOwner == False:
            print(f" > To {F.LIGHTRED_EX}delete the rest of the comments{S.R}: Type ' {F.LIGHTRED_EX}DELETE{S.R} ' exactly (in all caps), then hit Enter.")
          if userNotChannelOwner == False or moderator_mode == True:
            print(f" > To {F.LIGHTRED_EX}move rest of comments above to 'Held For Review' in YT Studio{S.R}: Type ' {F.LIGHTRED_EX}HOLD{S.R} ' exactly (in all caps), then hit Enter.")
        
        # Report Instructions
        print(f" > To {F.LIGHTCYAN_EX}just report the comments for spam{S.R}, type ' {F.LIGHTCYAN_EX}REPORT{S.R} '. (Can be done even if you're not the channel owner)")
        if config and config['json_extra_data'] == True:
          print(f"\n{F.WHITE}{B.BLUE} JSON NOTE: {S.R} At this time, excluding comments will {F.RED}NOT{S.R} remove them from the JSON log file.")
        confirmDelete = input("\nInput: ")
        if confirmDelete == "DELETE" and userNotChannelOwner == False:
          deletionEnabled = True
          deletionMode = "rejected"
        elif confirmDelete == "HOLD" and (userNotChannelOwner == False or moderator_mode == True):
          deletionEnabled = True
          deletionMode = "heldForReview"
        elif confirmDelete == "REPORT":
          deletionEnabled = True
          deletionMode = "reportSpam" 
        elif "exclude" in confirmDelete.lower():
          excludedDict, rtfExclude, plaintextExclude = exclude_authors(current, inputtedString=confirmDelete, miscData=miscData)
          exclude = True
        else:
          input(f"\nDeletion {F.YELLOW}CANCELLED{S.R} (Because no matching option entered). Press Enter to return to main menu...")
          return True

    
    # Set deletion mode friendly name
    if deletionMode == "rejected":
      deletionModeFriendlyName = "Removed"
    elif deletionMode == "heldForReview":
      deletionModeFriendlyName = "Moved to 'Held for Review' Section"
    elif deletionMode == "reportSpam":
      deletionModeFriendlyName = "Reported for spam"

    # Set or choose ban mode, check if valid based on deletion mode
    if (confirmDelete == "DELETE" or confirmDelete == "REPORT" or confirmDelete == "HOLD") and deletionEnabled == True:  
      banChoice = False
      if config and config['enable_ban'] != "ask":
        if config['enable_ban'] == False:
          pass
        elif config['enable_ban'] == True:
          print("Error Code C-8: 'enable_ban' is set to 'True' in config file. Only possible config options are 'ask' or 'False' when using config.\n")
          input("Press Enter to continue...")
        else:
          print("Error Code C-9: 'enable_ban' is set to an invalid value in config file. Only possible config options are 'ask' or 'False' when using config.\n")
          input("Press Enter to continue...")
      elif deletionMode == "rejected":
        banChoice = choice(f"Also {F.YELLOW}ban{S.R} the spammer(s) ?")
        if banChoice == None:
          return True # Return to main menu

      elif deletionMode == "heldForReview":
        pass
      elif deletionMode == "reportSpam":
        pass
      
      ### ---------------- Reporting / Deletion Begins  ----------------
      delete_found_comments(list(current.matchedCommentsDict), banChoice, deletionMode)
      if deletionMode != "reportSpam":
        if not config or config and config['check_deletion_success'] == True:
          check_deleted_comments(current.matchedCommentsDict)
        elif config and config['check_deletion_success'] == False:
          print("\nSkipped checking if deletion was successful.\n")

      if loggingEnabled == True:
        if logMode == "rtf":
          write_rtf(current.logFileName, "\n\n \\line\\line Spammers Banned: " + str(banChoice)) # Write whether or not spammer is banned to log file
          write_rtf(current.logFileName, "\n\n \\line\\line Action Taken on Comments: " + str(deletionModeFriendlyName) + " \\line\\line \n\n")
          if exclude == True:
            write_rtf(current.logFileName, str(rtfExclude))
        elif logMode == "plaintext":
          write_plaintext_log(current.logFileName, "\n\n Spammers Banned: " + str(banChoice) + "\n\n") # Write whether or not spammer is banned to log file
          write_plaintext_log(current.logFileName, "Action Taken on Comments: " + str(deletionModeFriendlyName) + "\n\n")
          if exclude == True:
            write_plaintext_log(current.logFileName, str(plaintextExclude))

      input(f"\nProgram {F.LIGHTGREEN_EX}Complete{S.R}. Press Enter to to return to main menu...")
      return True

    elif config['deletion_enabled'] == False:
      input(f"\nDeletion is disabled in config file. Press Enter to to return to main menu...")
      return True
    else:
      input(f"\nDeletion {F.LIGHTRED_EX}Cancelled{S.R}. Press Enter to to return to main menu...")
      return True

  continueRunning = True
  while continueRunning == True:
    continueRunning = primaryInstance(miscData)


# Runs the program
if __name__ == "__main__":
  #For speed testing

  # import cProfile
  # cProfile.run('main()', "output.dat")
  # import pstats
  # from pstats import SortKey
  # with open("output_time.txt", "w") as f:
  #   p = pstats.Stats("output.dat", stream=f)
  #   p.sort_stats("time").print_stats()
  # with open("output_calls.txt", "w") as f:
  #   p = pstats.Stats("output.dat", stream=f)
  #   p.sort_stats("calls").print_stats()
  try:
    main()
  except SystemExit:
    sys.exit()

  except HttpError as hx:
    traceback.print_exc()
    print("------------------------------------------------")
    print("Error Message: " + str(hx))
    if hx.status_code:
      print("Status Code: " + str(hx.status_code))
      if hx.error_details[0]["reason"]: # If error reason is available, print it
          reason = str(hx.error_details[0]["reason"])
          print_exception_reason(reason)
      print(f"\nAn {F.LIGHTRED_EX}'HttpError'{S.R} was raised. This is sometimes caused by a remote server error. See the error info above.")
      print(f"If this keeps happening, consider posting a bug report on the GitHub issues page, and include the above error info.")
      print(f"Short Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
      input("\nPress Enter to Exit...")
    else:
      print(f"{F.LIGHTRED_EX}Unknown Error - Code: Z-1{S.R} occurred. If this keeps happening, consider posting a bug report on the GitHub issues page, and include the above error info.")
      print(f"Short Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
      input("\n Press Enter to Exit...")
  except UnboundLocalError as ux:
    traceback.print_exc()
    print("------------------------------------------------")
    print("Error Message: " + str(ux))
    if "referenced before assignment" in str(ux):
      print(f"\n{F.LIGHTRED_EX}Error - Code: X-2{S.R} occurred. This is almost definitely {F.YELLOW}my fault and requires patching{S.R} (big bruh moment)")
      print(f"Please post a bug report on the GitHub issues page, and include the above error info.")
      print(f"Short Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
      print("    (In the mean time, try using a previous release of the program.)")
      input("\n Press Enter to Exit...")
    else:
      traceback.print_exc()
      print("------------------------------------------------")
      print(f"\n{F.LIGHTRED_EX}Unknown Error - Code: Z-2{S.R} occurred. If this keeps happening,")
      print("consider posting a bug report on the GitHub issues page, and include the above error info.")
      print(f"Short Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
      input("\n Press Enter to Exit...")
  except KeyError as kx:
    traceback.print_exc()
    print("------------------------------------------------")
    if "config" in str(kx):
      print(f"{F.LIGHTRED_EX}Unknown Error - Code: X-3{S.R}")
      print("Are you using an outdated version of the config file? Try re-creating the config file to get the latest version.")
      print(f"{F.LIGHTYELLOW_EX}If that doesn't work{S.R}, consider posting a {F.LIGHTYELLOW_EX}bug report{S.R} on the GitHub issues page, and include the above error info.")
    else:
      print(f"{F.RED}Unknown Error - Code: X-4{S.R} occurred. This is {F.YELLOW}probably my fault{S.R},")
      print(f"please a {F.LIGHTYELLOW_EX}bug report{S.R} on the GitHub issues page, and include the above error info.")
    print(f"Short Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
    input("\n Press Enter to Exit...")
  except Exception as x:
    traceback.print_exc()
    print("------------------------------------------------")
    print("Error Message: " + str(x))
    print(f"\n{F.LIGHTRED_EX}Unknown Error - Code: Z-3{S.R} occurred. If this keeps happening, consider posting a bug report")
    print("on the GitHub issues page, and include the above error info.")
    print(f"Short Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
    input("\n Press Enter to Exit...")
  else:
    print("\nFinished Executing.")
	

