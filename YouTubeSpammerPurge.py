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
version = "2.5.4"
configVersion = 12
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# GUI Related
from gui import *

# Standard Libraries
import io
import os
import re
import sys
import time
from datetime import datetime, date, timedelta
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
    CURR_DIR = os.path.dirname(os.path.realpath(__file__)) #current directory
    LIST_DIR = os.listdir(CURR_DIR) #list current directory, array.
    for dir in LIST_DIR:
      if dir.endswith('.json'):
        print(f'{F.GREEN} RENAMING, \'{dir}\'')
        os.rename(dir, 'client_secrets.json') #rename if file with extension '.json' is found.
        break
    if os.path.exists(CLIENT_SECRETS_FILE):
      print('FILE [RENAMED]...')
    else:
      print(f"\n         ----- {F.WHITE}{B.RED}[!] Error:{S.R} client_secrets.json file not found -----")
      print(f" ----- Did you create a {F.YELLOW}Google Cloud Platform Project{S.R} to access the API? ----- ")
      print(f"  > For instructions on how to get an API key, visit: {F.YELLOW}www.TJoe.io/api-setup{S.R}")
      print(f"\n  > (Non-shortened Link: https://github.com/ThioJoe/YT-Spammer-Purge#instructions---obtaining-youtube-api-key)")
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
    input("\n Press Enter to Exit...")

##########################################################################################
############################### PRINT SPECIFIC COMMENTS ##################################
##########################################################################################

# First prepared comments into segments of 50 to be submitted to API simultaneously
# Then uses print_prepared_comments() to print / log the comments
def print_comments(scanVideoID_localprint, comments, logMode, scanMode):
  j = 0 # Counting index when going through comments all comment segments
  groupSize = 2500 # Number of comments to process per iteration

  if len(comments) > groupSize:
    remainder = len(comments) % groupSize
    numDivisions = int((len(comments)-remainder)/groupSize)
    for i in range(numDivisions):
      j = print_prepared_comments(scanVideoID_localprint,comments[i*groupSize:i*groupSize+groupSize], j, logMode, scanMode)
    if remainder > 0:
      j = print_prepared_comments(scanVideoID_localprint,comments[numDivisions*groupSize:len(comments)],j, logMode, scanMode)
  else:
    j = print_prepared_comments(scanVideoID_localprint,comments, j, logMode, scanMode)

  # Print Sample Match List
  valuesPreparedToWrite = ""
  valuesPreparedToPrint = ""
  print(f"{F.LIGHTMAGENTA_EX}---------------------------- Match Samples: One comment per matched-comment author ----------------------------{S.R}")
  for value in matchSamplesDict.values():
    valuesPreparedToWrite = valuesPreparedToWrite + value['iString'] + value['cString'] + f"{str(value['authorID'])} | {make_rtf_compatible(str(value['nameAndText']))} \\line \n"
    valuesPreparedToPrint = valuesPreparedToPrint + value['iString'] + value['cString'] + f"{str(value['nameAndText'])}\n"
  if logMode == True:
    write_rtf(logFileName, "-------------------- Match Samples: One comment per matched-comment author -------------------- \\line\\line \n")
    write_rtf(logFileName, valuesPreparedToWrite)
  print(valuesPreparedToPrint)
  print(f"{F.LIGHTMAGENTA_EX}---------------------------- (See log file for channel IDs of matched authors above) ---------------------------{S.R}")

  return None

# Uses comments.list YouTube API Request to get text and author of specific set of comments, based on comment ID
def print_prepared_comments(scanVideoID_localprep, comments, j, logMode, scanMode):

  # Prints author and comment text for each comment
  i = 0 # Index when going through comments
  dataPreparedToWrite = ""

  for comment in comments:
    metadata = matchedCommentsDict[comment]
    text = metadata['text']
    author = metadata['authorName']
    author_id_local = metadata['authorID']
    comment_id_local = comment
    videoID = metadata['videoID']

    # Truncates very long comments, and removes excessive multiple lines
    if len(text) > 1500:
      text = text[0:1500] + "  ...[YT Spammer Purge Note: Long Comment Truncated - Visit Link to See Full Comment]"
    if text.count("\n") > 0:
      text = text.replace("\n", " ") + "  ...[YT Spammer Purge Note: Comment converted from multiple lines to single line]"

    # Add one sample from each matching author to matchSamplesDict, containing author ID, name, and text
    if author_id_local not in matchSamplesDict.keys():
      add_sample(author_id_local, author, text)

    # Build comment direct link
    if scanMode == "communityPost":
      directLink = "https://www.youtube.com/post/" + videoID + "?lc=" + comment_id_local
    else:
      directLink = "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comment_id_local

    # Prints comment info to console
    print(str(j+1) + f". {F.LIGHTCYAN_EX}" + author + f"{S.R}:  {F.YELLOW}" + text + f"{S.R}")
    print("—————————————————————————————————————————————————————————————————————————————————————————————")
    if scanVideoID_localprep is None:  # Only print video title if searching entire channel
      title = get_video_title(videoID) # Get Video Title
      print("     > Video: " + title)
    print("     > Direct Link: " + directLink)
    print(f"     > Author Channel ID: {F.LIGHTBLUE_EX}" + author_id_local + f"{S.R}")
    print("=============================================================================================\n")

    # If logging enabled, also prints to log file 
    if logMode == True:
      # Only print video title info if searching entire channel
      if scanVideoID_localprep is None:  
         titleInfoLine = "     > Video: " + title + "\\line " + "\n"
      else:
        titleInfoLine = ""

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
      dataPreparedToWrite = dataPreparedToWrite + commentInfo

    # Appends comment ID to new list of comments so it's in the correct order going forward, as provided by API and presented to user
    # Must use append here, not extend, or else it would add each character separately
    i += 1
    j += 1

  if logMode == True:
    print(" Writing to log file, please wait...", end="\r")
    write_rtf(logFileName, dataPreparedToWrite)
    print("                                    ")

  return j

# Adds a sample to matchSamplesDict and preps formatting
def add_sample(authorID, authorNameRaw, commentText):
  global matchSamplesDict
  global authorMatchCountDict

  # Make index number and string formatted version
  index = len(matchSamplesDict) + 1
  iString = f"{str(index)}. ".ljust(4)
  authorNumComments = authorMatchCountDict[authorID]
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
  matchSamplesDict[authorID] = {'index':index, 'cString':cString, 'iString':iString, 'count':authorNumComments, 'authorID':authorID, 'authorName':authorNameRaw, 'nameAndText':authorName + commentText}


##########################################################################################
############################## GET COMMENT THREADS #######################################
##########################################################################################

# Call the API's commentThreads.list method to list the existing comments.
def get_comments(youtube, currentUser, miscData, filterMode, filterSubMode, scanVideoID=None, check_channel_id=None, nextPageToken=None, inputtedSpammerChannelID=None, inputtedUsernameFilter=None, inputtedCommentTextFilter=None, regexPattern=None, videosToScan=None):  # None are set as default if no parameters passed into function
  global scannedCommentsCount
  # Initialize some variables
  authorChannelName = None
  commentText = None
  parentAuthorChannelID = None

  fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/replies/comments,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/authorDisplayName,items/snippet/topLevelComment/snippet/textDisplay"

  # Gets all comment threads for a specific video
  if scanVideoID is not None:
    results = youtube.commentThreads().list(
      part="snippet, replies",
      videoId=scanVideoID, 
      maxResults=100,
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()
  
  # Get all comment threads across the whole channel
  elif scanVideoID is None:
    results = youtube.commentThreads().list(
      part="snippet, replies",
      allThreadsRelatedToChannelId=check_channel_id,
      maxResults=100,
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()  
    
  # Get token for next page
  try:
    RetrievedNextPageToken = results["nextPageToken"]
  except KeyError:
    RetrievedNextPageToken = "End"  
  
  # After getting all comments threads for page, extracts data for each and stores matches in matchedCommentsDict
  # Also goes through each thread and executes get_replies() to get reply content and matches
  for item in results["items"]:
    comment = item["snippet"]["topLevelComment"]
    videoID = comment["snippet"]["videoId"] # Only enable if NOT checking specific video
    parent_id = item["snippet"]["topLevelComment"]["id"]
    numReplies = item["snippet"]["totalReplyCount"]

    # Need to use try/except, because if no replies, will throw KeyError
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
      authorChannelName = comment["snippet"]["authorDisplayName"]
    except KeyError:
      authorChannelName = "[Deleted Channel]"
    try:
      commentText = comment["snippet"]["textDisplay"]
    except KeyError:
      commentText = "[Deleted/Missing Comment]"
    
    # Runs check against comment info for whichever filter data is relevant
    check_against_filter(currentUser, miscData, filterMode=filterMode, filterSubMode=filterSubMode, commentID=parent_id, videoID=videoID, authorChannelID=parentAuthorChannelID, parentAuthorChannelID=None, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, authorChannelName=authorChannelName, commentText=commentText, regexPattern=regexPattern)
    scannedCommentsCount += 1  # Counts number of comments scanned, add to global count
    
    if numReplies > 0 and len(limitedRepliesList) < numReplies:
      get_replies(youtube, currentUser, miscData, filterMode, filterSubMode, parent_id, videoID, parentAuthorChannelID, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, regexPattern, videosToScan)
    elif numReplies > 0 and len(limitedRepliesList) == numReplies: # limitedRepliesList can never be more than numReplies
      get_replies(youtube, currentUser, miscData, filterMode, filterSubMode, parent_id, videoID, parentAuthorChannelID, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, regexPattern, videosToScan, repliesList=limitedRepliesList)
    else:
      print_count_stats(miscData, videosToScan, final=False)  # Updates displayed stats if no replies

  return RetrievedNextPageToken


##########################################################################################
##################################### GET REPLIES ########################################
##########################################################################################

# Call the API's comments.list method to list the existing comment replies.
def get_replies(youtube, currentUser, miscData, filterMode, filterSubMode, parent_id, videoID, parentAuthorChannelID, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, regexPattern, videosToScan, repliesList=None, ):
  global scannedRepliesCount
  # Initialize some variables
  authorChannelName = None
  commentText = None
  
  if repliesList == None:
    fieldsToFetch = "items/snippet/authorChannelId/value,items/id,items/snippet/authorDisplayName,items/snippet/textDisplay"

    results = youtube.comments().list(
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
  if filterMode == "Username" or filterMode == "AutoASCII" or filterMode == "AutoSmart" or filterMode == "NameAndText":
    for reply in replies:
      try:
        authorChannelName = reply["snippet"]["authorDisplayName"]
      except KeyError:
        authorChannelName = "[Deleted Channel]"
      # Add authorchannelname to list
      allThreadAuthorNames.append(authorChannelName)

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
    except KeyError:
      authorChannelName = "[Deleted Channel]"
    
    # Comment Text
    try:
      commentText = reply["snippet"]["textDisplay"]
    except KeyError:
      commentText = "[Deleted/Missing Comment]"

    # Runs check against comment info for whichever filter data is relevant
    check_against_filter(currentUser, miscData, filterMode=filterMode, filterSubMode=filterSubMode, commentID=replyID, videoID=videoID, authorChannelID=authorChannelID, parentAuthorChannelID=parentAuthorChannelID, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, authorChannelName=authorChannelName, commentText=commentText, regexPattern=regexPattern, allThreadAuthorNames=allThreadAuthorNames)

    # Update latest stats
    scannedRepliesCount += 1  # Count number of replies scanned, add to global count
    print_count_stats(miscData, videosToScan, final=False) # Prints out current count stats

  return True

############################## CHECK AGAINST FILTER ######################################
# The basic logic that actually checks each comment against filter criteria
def check_against_filter(currentUser, miscData, filterMode, filterSubMode, commentID, videoID, authorChannelID, parentAuthorChannelID=None, inputtedSpammerChannelID=None, inputtedUsernameFilter=None, inputtedCommentTextFilter=None,  authorChannelName=None, commentText=None, regexPattern=None, allThreadAuthorNames=None):
  global vidIdDict
  global matchedCommentsDict
  commentTextOriginal = str(commentText)

  debugSingleComment = False #Debug usage
  if debugSingleComment == True:
    authorChannelName = input("Channel Name: ")
    commentText = input("Comment Text: ")
    authorChannelID = "x"

  # Do not even check comment if author ID matches currently logged in user's ID
  if currentUser[0] != authorChannelID and miscData['channelOwnerID'] != authorChannelID:
    if "@" in commentText:
      # Logic to avoid false positives from replies to spammers
      if allThreadAuthorNames and (filterMode == "AutoSmart" or filterMode == "NameAndText"):
        for name in allThreadAuthorNames:
          if "@"+str(name) in commentText:
            commentText = commentText.replace("@"+str(name), "")
      # Extra logic to detect false positive if spammer's comment already deleted, but someone replied
      if matchedCommentsDict and filterMode == "AutoSmart":
        for key, value in matchedCommentsDict.items():
          if "@"+str(value['authorName']) in commentText:
            remove = True
            for key2,value2 in matchedCommentsDict.items():
              if value2['authorID'] == authorChannelID:
                remove = False
            if remove == True:
              commentText = commentText.replace("@"+str(value['authorName']), "")

    # If the comment/username matches criteria based on mode, add key/value pair of comment ID and author ID to matchedCommentsDict
    # Also add key-value pair of comment ID and video ID to dictionary
    # Also count how many spam comments for each author
    def add_spam(commentID, videoID):
      global matchedCommentsDict
      global authorMatchCountDict
      matchedCommentsDict[commentID] = {'text':commentTextOriginal, 'authorName':authorChannelName, 'authorID':authorChannelID, 'videoID':videoID}
      vidIdDict[commentID] = videoID # Probably remove this later, but still being used for now
      if authorChannelID in authorMatchCountDict:
        authorMatchCountDict[authorChannelID] += 1
      else:
        authorMatchCountDict[authorChannelID] = 1
      if debugSingleComment == True: 
        input("--- Yes, Matched -----")

    # Checks author of either parent comment or reply (both passed in as commentID) against channel ID inputted by user
    if filterMode == "ID":
      if any(authorChannelID == x for x in inputtedSpammerChannelID):
        add_spam(commentID, videoID)

    # Check Modes: Username
    elif filterMode == "Username":
      if filterSubMode == "chars":
        authorChannelName = make_char_set(str(authorChannelName))
        if any(x in inputtedUsernameFilter for x in authorChannelName):
          add_spam(commentID, videoID)
      elif filterSubMode == "string":
        if check_list_against_string(listInput=inputtedUsernameFilter, stringInput=authorChannelName, caseSensitive=False):
          add_spam(commentID, videoID)
      elif filterSubMode == "regex":
        if re.search(str(regexPattern), authorChannelName):
          add_spam(commentID, videoID)

    # Check Modes: Comment Text
    elif filterMode == "Text":
      if filterSubMode == "chars":
        commentText = make_char_set(str(commentText))
        if any(x in inputtedCommentTextFilter for x in commentText):
          add_spam(commentID, videoID)
      elif filterSubMode == "string":
        if check_list_against_string(listInput=inputtedCommentTextFilter, stringInput=commentText, caseSensitive=False):
          add_spam(commentID, videoID)
      elif filterSubMode == "regex":
        if re.search(str(regexPattern), commentText):
          add_spam(commentID, videoID)

    # Check Modes: Name and Text
    elif filterMode == "NameAndText":
      if filterSubMode == "chars":
        authorChannelName = make_char_set(str(authorChannelName))
        commentText = make_char_set(str(commentText))
        if any(x in inputtedUsernameFilter for x in authorChannelName):
          add_spam(commentID, videoID)
        elif any(x in inputtedCommentTextFilter for x in commentText):
          add_spam(commentID, videoID)
      elif filterSubMode == "string":
        if check_list_against_string(listInput=inputtedUsernameFilter, stringInput=authorChannelName, caseSensitive=False):
          add_spam(commentID, videoID)
        elif check_list_against_string(listInput=inputtedCommentTextFilter, stringInput=commentText, caseSensitive=False):
          add_spam(commentID, videoID)
      elif filterSubMode == "regex":
        if re.search(str(regexPattern), authorChannelName):
          add_spam(commentID, videoID)
        elif re.search(str(regexPattern), commentText):
          add_spam(commentID, videoID)

    # Check Modes: Auto ASCII (in username)
    elif filterMode == "AutoASCII":
      if re.search(str(regexPattern), authorChannelName):
        add_spam(commentID, videoID)

    # Check Modes: Auto Smart (in username or comment text)
    # Here inputtedComment/Author Filters are tuples of, where 2nd element is list of char-sets to check against
    ## Also Check if reply author ID is same as parent comment author ID, if so, ignore (to account for users who reply to spammers)
    elif filterMode == "AutoSmart" or filterMode == "SensitiveSmart":
      smartFilter = inputtedUsernameFilter
      # Receive Variables
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
      spamDomainRegex = smartFilter['spamDomainRegex']
      compiledRegexDict = smartFilter['compiledRegexDict']

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
      elif any(re.search(expression, combinedString) for expression in spamDomainRegex):
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
      result = youtube.comments().markAsSpam(id=commentIDs).execute()
      if len(result) > 0:
        print("\nSomething may gone wrong when reporting the comments.")    
    elif deletionMode == "heldForReview" or deletionMode == "rejected" or deletionMode == "published":
      youtube.comments().setModerationStatus(id=commentIDs, moderationStatus=deletionMode, banAuthor=banChoice).execute()
    else:
      print("Invalid deletion mode. This is definitely a bug, please report it here: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
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
          setStatus(commentsList[numDivisions*50:total]) # Deletes any leftover comments range after last full chunk
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
    for commentID, metadata in checkDict.items():
      try:
        results = youtube.comments().list(
          part="snippet",
          id=commentID,  
          maxResults=1,
          fields="items",
          textFormat="plainText"
        ).execute()
        print("    (Note: You can disable deletion success checking in the config file, to save time and API quota)\n")
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
      results = youtube.comments().list(
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

  input("\nRecovery process finished. Press Enter to Exit...")
  sys.exit()

# Removes comments by user-selected authors from list of comments to delete
def exclude_authors(inputtedString):
  global matchSamplesDict

  expression = r"(?<=exclude ).*" # Match everything after 'exclude '
  result = str(re.search(expression, inputtedString).group(0))
  result = result.replace(" ", "")
  SampleIDsToExclude = result.split(",")
  authorIDsToExclude = []
  displayString = ""
  excludedCommentsDict = {}
  rtfFormattedExcludes = ""
  commentIDExcludeList = []

  # Get authorIDs for selected sample comments
  for authorID, info in matchSamplesDict.items():
    if str(info['index']) in SampleIDsToExclude:
      authorIDsToExclude += [authorID]

  # Get comment IDs to be excluded
  for comment, metadata in matchedCommentsDict.items():
    if metadata['authorID'] in authorIDsToExclude:
      commentIDExcludeList.append(comment)
  # Remove all comments by selected authors from dictionary of comments
  for comment in commentIDExcludeList:
    if comment in matchedCommentsDict.keys():
      excludedCommentsDict[comment] = matchedCommentsDict.pop(comment)

  rtfFormattedExcludes += f"Comments Excluded From Deletion: \\line \n"
  rtfFormattedExcludes += f"(Values = Comment ID | Author ID | Author Name | Comment Text) \\line \n"
  for commentID, meta in excludedCommentsDict.items():
    rtfFormattedExcludes += f"{str(commentID)}  |  {str(excludedCommentsDict[commentID]['authorID'])}  |  {str(excludedCommentsDict[commentID]['authorName'])}  |   {str(excludedCommentsDict[commentID]['text'])} \\line \n"

  # Verify removal
  for comment in matchedCommentsDict.keys():
    if comment in commentIDExcludeList:
      print("FATAL ERROR: Something went wrong while trying to exclude comments. No comments have been deleted.")
      print("You should report this bug here: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      print("Provide the error code: X-1")
      input("Press Enter to Exit...")
      sys.exit()
  
  # Get author names and IDs from dictionary, and display them
  for author in authorIDsToExclude:
    displayString += f"    User ID: {author}   |   User Name: {matchSamplesDict[author]['authorName']}\n"
  print(f"\n{F.CYAN}All {len(excludedCommentsDict)} comments{S.R} from the {F.CYAN}following {len(authorIDsToExclude)} users{S.R} are now {F.LIGHTGREEN_EX}excluded{S.R} from deletion:")
  print(displayString+"\n")
  input("Press Enter to decide what to do with the rest...")
  
  return excludedCommentsDict, rtfFormattedExcludes # May use excludedCommentsDict later for printing them to log file

  

##########################################################################################
############################## UTILITY FUNCTIONS #########################################
########################################################################################## 

################################### GET VIDEO TITLE ###############################################
# Check if video title is in dictionary, if not get video title from video ID using YouTube API request, then return title
def get_video_title(video_id):
  global vidTitleDict

  if video_id in vidTitleDict.keys():
    title = vidTitleDict[video_id]
  else:
    results = youtube.videos().list(
      part="snippet",
      id=video_id,
      fields="items/snippet/title",
      maxResults=1
    ).execute()
    title = results["items"][0]["snippet"]["title"]
    vidTitleDict[video_id] = title

  return title


def get_comment_count(video_id):
  result = youtube.videos().list(
    part="statistics",
    id=video_id,
    fields='items/statistics/commentCount',
    ).execute()
  return result['items'][0]['statistics']['commentCount']

############################# GET CHANNEL ID FROM VIDEO ID #####################################
# Get channel ID from video ID using YouTube API request
def get_channel_id(video_id):
  results = youtube.videos().list(
    part="snippet",
    id=video_id,
    fields="items/snippet/channelId,items/snippet/channelTitle",
    maxResults=1
  ).execute()
  
  channelID = results["items"][0]["snippet"]["channelId"]
  channelTitle = results["items"][0]["snippet"]["channelTitle"]

  return channelID, channelTitle

############################# GET CURRENTLY LOGGED IN USER #####################################
# Class for custom exception to throw if a comment if invalid channel ID returned
class ChannelIDError(Exception):
    pass
# Get channel ID and channel title of the currently authorized user
def get_current_user(config):
  global youtube

  #Define fetch function so it can be re-used if issue and need to re-run it
  def fetch():
    results = youtube.channels().list(
      part="snippet", #Can also add "contentDetails" or "statistics"
      mine=True,
      fields="items/id,items/snippet/title"
    ).execute()
    return results
  results = fetch()

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
    youtube = get_authenticated_service()
    results = fetch() # Try again

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
    configMatch = None
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

################################# VIDEO ID LOOKUP ##############################################
# Using comment ID, get corresponding video ID from dictionary variable
def convert_comment_id_to_video_id(comment_id):
  video_id = vidIdDict[comment_id]
  return video_id

################################# Get Most Recent 5 Videos #####################################
# Returns a list of lists: [Video ID, Video Title]
def get_recent_videos(channel_id, numVideos):
  result = youtube.search().list(
    part="snippet",
    channelId=channel_id,
    type='video',
    order='date',
    fields='items/id/videoId,items/snippet/title',
    maxResults=numVideos,
    ).execute()

  recentVideos = [] #List of dictionaries
  i=0
  for item in result['items']:
    recentVideos.append({})
    videoID = str(item['id']['videoId'])
    videoTitle = str(item['snippet']['title']).replace("&quot;", "\"")
    recentVideos[i]['videoID'] = videoID
    recentVideos[i]['videoTitle'] = videoTitle

    commentCount = get_comment_count(videoID)
    recentVideos[i]['commentCount'] = commentCount

    i+=1

  return recentVideos

##################################### PRINT STATS ##########################################

# Prints Scanning Statistics, can be version that overwrites itself or one that finalizes and moves to next line
def print_count_stats(miscData, videosToScan, final):
  # Use videosToScan (list of dictionaries) to retrieve total number of comments
  if videosToScan:
    totalComments = miscData['totalCommentCount']
    totalScanned = scannedRepliesCount + scannedCommentsCount
    percent = ((totalScanned / totalComments) * 100)
    progress = f"Total: [{str(totalScanned)}/{str(totalComments)}] ({percent:.0f}%) ".ljust(27, " ") + "|" #Formats percentage to 0 decimal places
  else:
    progress = ""
  
  comScanned = str(scannedCommentsCount)
  repScanned = str(scannedRepliesCount)
  matchCount = str(len(matchedCommentsDict))

  if final == True:
    print(f" {progress} Comments Scanned: {F.YELLOW}{comScanned}{S.R} | Replies Scanned: {F.YELLOW}{repScanned}{S.R} | Matches Found So Far: {F.LIGHTRED_EX}{matchCount}{S.R}\n")
  else:
    print(f" {progress} Comments Scanned: {F.YELLOW}{comScanned}{S.R} | Replies Scanned: {F.YELLOW}{repScanned}{S.R} | Matches Found So Far: {F.LIGHTRED_EX}{matchCount}{S.R}", end = "\r")
  
  return None

##################################### VALIDATE VIDEO ID #####################################
# Checks if video ID / video Link is correct length and in correct format - If so returns true and isolated video ID
def validate_video_id(video_url, silent=False):
    youtube_video_link_regex = r"^\s*(?P<video_url>(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube\.com|youtu.be)(?:\/(?:[\w\-]+\?v=|embed\/|v\/)?))?(?P<video_id>[\w\-]{11})(?:(?(video_url)\S+|$))?\s*$"
    match = re.match(youtube_video_link_regex, video_url)
    if match == None:
      if silent == False:
        print(f"\n{B.RED}{F.BLACK}Invalid Video link or ID!{S.R} Video IDs are 11 characters long.")
      return False, None
    return True, match.group('video_id')

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
      response = youtube.search().list(part="snippet",q=customURL, maxResults=1).execute()
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
        print(f"{F.LIGHTRED_EX}Invalid Channel ID / Link!{S.R} Looks like you entered a Video ID / Link by mistake.)")
        return False, None, None

      response = youtube.search().list(part="snippet",q=customURL, maxResults=1).execute()
      if response.get("items"):
        isolatedChannelID = response.get("items")[0]["snippet"]["channelId"] # Get channel ID from custom channel URL username

  # Channel ID regex expression from: https://webapps.stackexchange.com/a/101153
  elif re.match(r'UC[0-9A-Za-z_-]{21}[AQgw]', inputted_channel):
    isolatedChannelID = inputted_channel

  else:
    print(f"\n{B.RED}{F.BLACK}Error:{S.R} Invalid Channel link or ID!")
    return False, None, None

  if len(isolatedChannelID) == 24 and isolatedChannelID[0:2] == "UC":
    response = youtube.channels().list(part="snippet", id=isolatedChannelID).execute()
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
    response = input("\n" + message + f" ({F.LIGHTCYAN_EX}y{S.R}/{F.LIGHTRED_EX}n{S.R}): ")
    if response == "Y" or response == "y":
      return True
    elif response == "N" or response == "n":
      return False
    else:
      print("\nInvalid Input. Enter Y or N")


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

############################# Check Username Against Filter ##############################
# Check the own user's username against a filter, warn if it matches
# Note: Most uses of this function are obsolete after changing it so the program totally ignores current users's own comments
def safety_check_username_against_filter(currentUserName, scanMode, filterCharsSet=None, filterStringList=None, regexPattern=None, bypass = False):
  currentUsernameChars = make_char_set(currentUserName)
  proceed = False
  if bypass != True:
    if filterCharsSet:
      if any(x in filterCharsSet for x in currentUsernameChars):
        print(f"\n{B.LIGHTRED_EX}{F.BLACK}NOTE!{S.R} Character(s) you entered are within {F.LIGHTRED_EX}your own username{S.R}, ' " + currentUserName + " '! : " + str(filterCharsSet & currentUsernameChars))
        print("      (Some symbols above may not show in windows console)")
        print(f"\nThis program will {F.YELLOW}ignore{S.R} any comments made by you (by checking the author channel ID)")
        input("\nPress enter to continue...")    
    
    elif filterStringList:
      if check_list_against_string(listInput=filterStringList, stringInput=currentUserName, caseSensitive=False):
        print(f"\n{B.LIGHTRED_EX}{F.BLACK}NOTE!{S.R} A string you entered is within {F.LIGHTRED_EX}your own username{S.R}!")
        print(f"\nThis program will {F.YELLOW}ignore{S.R} any comments made by you (by checking the author channel ID)")
        input("\nPress enter to continue...")

    elif regexPattern:
      if re.search(regexPattern, currentUserName):
        print(f"{B.RED}{F.WHITE}NOTE!{S.R} This search mode / pattern would detect {F.LIGHTRED_EX}your own username{S.R}!")
        print(f"\nThis program will {F.YELLOW}ignore{S.R} any comments made by you (by checking the author channel ID)")
        input("\nPress enter to continue...")

  proceed = True

  return proceed
  
  
############################# Check For App Update ##############################
def check_for_update(currentVersion, silentCheck=False):
  isUpdateAvailable = False
  print("\nGetting info about latest updates...")

  try:
    response = requests.get("https://api.github.com/repos/ThioJoe/YouTube-Spammer-Purge/releases/latest")
    if response.status_code != 200:
      if response.status_code == 403:
        print(f"\n{B.RED}{F.WHITE}Error [U-4]:{S.R} Got an 403 (ratelimit_reached) when attempting to check for update.")
        print(f"This means you have been {F.YELLOW}rate limited by github.com{S.R}. Please try again in a while.\n")
        if silentCheck == False:
          input("\nPress enter to exit...")
          sys.exit()
      else:
        print(f"{B.RED}{F.WHITE}Error [U-3]:{S.R} Got non 200 status code (got: {response.status_code}) when attempting to check for update.\n")
        print(f"If this keeps happening, you may want to report the issue here: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
        if silentCheck == False:
          input("\nPress enter to exit...")
          sys.exit()
    else:
      # assume 200 response
      latestVersion = response.json()["name"]
  except Exception as e:
    if silentCheck == False:
      print(e + "\n")
      print(f"{B.RED}{F.WHITE}Error [Code U-1]:{S.R} Problem while checking for updates. See above error for more details.\n")
      print("If this keeps happening, you may want to report the issue here: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      input("Press enter to Exit...")
      sys.exit()
    elif silentCheck == True:
      return isUpdateAvailable

  if parse_version(latestVersion) > parse_version(currentVersion):
    isUpdateAvailable = True
    if silentCheck == False:
      print("--------------------------------------------------------------------------------")
      print(f" A {F.LIGHTGREEN_EX}new version{S.R} is available!")
      print(f" > Current Version: {currentVersion}")
      print(f" > Latest Version: {F.LIGHTGREEN_EX}{latestVersion}{S.R}")
      print("--------------------------------------------------------------------------------")
      if choice("Update Now?") == True:
        if sys.platform == 'win32' or sys.platform == 'win64':
          print(f"\n> {F.LIGHTCYAN_EX} Downloading Latest Version...{S.R}")
          jsondata = json.dumps(response.json()["assets"])
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
            input("\nPress Enter to Exit...")
            sys.exit()
          if k == 0: # No hash file in release
            print(f"{S.YELLOW}Warning!{S.R} No verification sha256 hash found in release. If download fails, you can manually download latest version here:")
            print("https://github.com/ThioJoe/YT-Spammer-Purge/releases")
            input("\nPress Enter to Exit...")
            ignoreHash = True
          elif k>0 and k!=j:
            print(f"{S.YELLOW}Warning!{S.R} Too many or too few sha256 files found in release. If download fails, you should manually download latest version here:")
            print("https://github.com/ThioJoe/YT-Spammer-Purge/releases")
            input("\nPress Enter to Exit...")
            sys.exit()

          # Get and Set Download Info
          total_size_in_bytes= int(filedownload.headers.get('content-length', 0))
          block_size =  1048576 #1 MiB in bytes
          downloadFileName = dict_json[0]['name']

          # Check if file exists already, ask to overwrite if it does
          if os.path.exists(downloadFileName):
            print(f"{B.RED}{F.WHITE}WARNING!{S.R} '{F.YELLOW}{downloadFileName}{S.R}' file already exists. This would overwrite the existing file.")
            confirm = choice("Overwrite this existing file?")
            if confirm == True:
              try:
                os.remove(downloadFileName)
              except:
                traceback.print_exc()
                print(f"\n{F.LIGHTRED_EX}Error F-6:{S.R} Problem deleting existing existing file! Check if it's gone, or delete it yourself, then try again.")
                print("The info above may help if it's a bug, which you can report here: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
                input("Press enter to Exit...")
                sys.exit()

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
            input("\nPress enter to Exit...")
            sys.exit()
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
              input("\nPress enter to Exit...")
              sys.exit()

          # Print Success
          print(f"\n>  Download Completed: {F.LIGHTGREEN_EX}{downloadFileName}{S.R}")
          print("You can now delete the old version. (Or keep it around in case you encounter any issues with the new version)")
          input("\nPress Enter to Exit...")
          sys.exit()

        else:
          # We do this because we pull the .exe for windows, but maybe we could use os.system('git pull')? Because this is a GIT repo, unlike the windows version
          print(f"> {F.RED} Error:{S.R} You are using an unsupported os for the autoupdater (macos/linux). \n This updater only supports Windows (right now) Feel free to get the files from github: https://github.com/ThioJoe/YouTube-Spammer-Purge")
          input("\nPress enter to Exit...")
          sys.exit()
      else:
        input("Aborted. Press Enter to Exit...")
        sys.exit()
    elif silentCheck == True:
      isUpdateAvailable = True
      return isUpdateAvailable

  elif parse_version(latestVersion) == parse_version(currentVersion):
    if silentCheck == False:
      print(f"\nYou have the {F.LIGHTGREEN_EX}latest{S.R} version: {F.LIGHTGREEN_EX}" + currentVersion)
      input("\nPress enter to Exit...")
      sys.exit()
  else:
    if silentCheck == False:
      print("\nNo newer release available - Your Version: " + currentVersion + "  --  Latest Version: " + latestVersion)
      input("\nPress enter to Exit...")
      sys.exit()
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
def check_lists_update(currentListVersion, silentCheck = False):
  isListUpdateAvailable = False
  #spamDomainListLatestCommit = 'https://api.github.com/repos/ThioJoe/YT-Spam-Domains-List/commits?path=SpamDomainsList.txt&page=1&per_page=1'
  #spamDomainListRawLink = 'https://raw.githubusercontent.com/ThioJoe/YT-Spam-Domains-List/main/SpamDomainsList.txt'
  #otherlink = 'https://api.github.com/repos/ThioJoe/YT-Spam-Domains-List/contents/SpamDomainsList.txt'
  #spamDomainHostedLocation = "https://cdn.jsdelivr.net/gh/thiojoe/YT-Spam-Domains-List/SpamDomainsList.txt"
  listDirectory = "spam_lists/"
  
  if silentCheck == False:
    print("\nChecking for updates to spam lists...")

  if os.path.isdir(listDirectory):
    pass
  else:
    try:
      os.mkdir(listDirectory)
    except:
      print("Error: Could not create folder. Try creating a folder called 'spam_lists' to update the spam lists.")

  if os.path.exists(listDirectory + "SpamDomainsList.txt"):
    currentListVersion = get_list_file_version(listDirectory + "SpamDomainsList.txt")
  else:
    currentListVersion = None
  
  # Get latest version based on release tag - In format: 2022.01.01 (YYYY.MM.DD)
  try:
    response = requests.get("https://api.github.com/repos/ThioJoe/YT-Spam-Domains-List/releases/latest")
    latestVersion = response.json()["tag_name"]

  except:
    if silentCheck == True:
      return isListUpdateAvailable
    else:
      print("Error: Could not get latest release info from GitHub. Please try again later.")
      input("\nPress enter to Exit...")
      sys.exit()

  if currentListVersion == None or (parse_version(latestVersion) > parse_version(currentListVersion)):
    fileName = response.json()["assets"][0]['name']
    total_size_in_bytes = response.json()["assets"][0]['size']
    downloadFilePath = listDirectory + fileName
    downloadURL = response.json()["assets"][0]['browser_download_url']
    filedownload = getRemoteFile(downloadURL, stream=True) # These headers required to get correct file size
    #total_size_in_bytes= int(filedownload.headers.get('content-length', 0))
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
            zip_ref.extractall(listDirectory)
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
        except FileNotFoundError:
          break

    elif total_size_in_bytes != 0 and os.stat(downloadFilePath).st_size != total_size_in_bytes:
      os.remove(downloadFilePath)
      print(f" > {F.RED} File did not fully download. Please try again later.\n")


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
    if not line.startswith('#'):
      line = line.strip()
      dataList.append(line.lower())
  return dataList

def ingest_list_file(relativeFilePath):
  if os.path.exists(relativeFilePath):
    with open(relativeFilePath, 'r', encoding="utf-8") as listFile:
      listData = listFile.readlines()
    processedList = []
    for line in listData:
      if not line.startswith('#'):
        line = line.strip()
        processedList.append(line.lower())
    return processedList
  else:
    return None

def get_list_file_version(relativeFilePath):
  if os.path.exists(relativeFilePath):
    matchBetweenBrackets = '(?<=\[)(.*?)(?=\])' # Matches text between first set of two square brackets
    with open(relativeFilePath, 'r', encoding="utf-8") as file:
      for line in islice(file, 0, 2):
        try:
          listVersion = str(re.search(matchBetweenBrackets, line).group(0))
        except AttributeError:
          pass
      return listVersion
  else:
    return None

############################# CONFIG FILE FUNCTIONS ##############################
def create_config_file():
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
    print(f"{B.RED}{F.WHITE}WARNING!{S.R} {F.YELLOW}SpamPurgeConfig.ini{S.R} file already exists. This would overwrite the existing file.")
    confirm = choice("Create new empty config file and overwrite existing?")
    if confirm == True:
      try:
        os.remove(configFileName)
      except:
        traceback.print_exc()
        print("Error Code F-1: Problem deleting existing existing file! Check if it's gone. The info above may help if it's a bug.")
        print("If this keeps happening, you may want to report the issue here: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
        input("Press enter to Exit...")
        sys.exit()
    else:
      return None

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
        if parser.get("general", "use_this_config").lower() == "ask":
          print(f"{B.GREEN}{F.BLACK}SUCCESS!{S.R} {F.YELLOW}SpamPurgeConfig.ini{S.R} file created successfully.")
          print("\nYou can now edit the file to your liking.\n")
          input("Press enter to Exit...")
          sys.exit()
        else:
          print("Something might have gone wrong. Check if SpamPurgeConfig.ini file exists and has text.")
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
    return None

# Put config settings into dictionary
def load_config_file():
  configFileName = "SpamPurgeConfig.ini"
  if os.path.exists(configFileName):
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
    #configDictRaw = {s:dict(parser.items(s)) for s in parser.sections()}

    # Convert raw config dictionary into easier to use dictionary
    settingsToKeepCase = ["your_channel_id", "video_to_scan", "channel_ids_to_filter", "regex_to_filter", "channel_to_scan", "log_path"]
    validWordVars = ['ask', 'mine', 'default']
    configDict = {}
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

    return configDict
  else:
    return None

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
        if choice("Try entering file name again?") == True:
          pass
        else:
          manuallyEnter = True
    else: 
      manuallyEnter = True

  if manuallyEnter == True:
    print("\n\n--- Manual Comment ID Entry Instructions ---")
    print("1. Open the log file and look for where it shows the list of \"IDs of Matched Comments\".")
    print("2. Copy that list, and paste it below (In windows console try pasting by right clicking).")
    print("3. If not using a log file, instead enter the ID list in this format: FirstID, SecondID, ThirdID, ... \n")
    data = str(input("Paste the list here, then hit Enter: "))
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
    input("Press enter to Exit...")
    sys.exit()

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
def prepare_filter_mode_chars(currentUser, scanMode, filterMode, config):
  currentUserName = currentUser[1]
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

  validEntry = False
  validConfigSetting = True
  while validEntry == False:
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
        print("If this keeps happening inexplicably, consider filing a bug report here: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
        input("Press Enter to exit...")
        sys.exit()

    if filterMode == "Username" or filterMode == "NameAndText":
      validEntry= safety_check_username_against_filter(currentUserName, scanMode, filterCharsSet=inputChars, bypass=bypass)
    elif filterMode == "Text":
      validEntry = True

    if validEntry == True:
      if validConfigSetting == True and config and config['characters_to_filter'] != "ask":
        pass
      else:
        print(f"     {whatToScanMsg} will be scanned for {F.MAGENTA}ANY{S.R} of the characters you entered in the previous window.")
      if choice("Begin Scanning? ", bypass) == True:
        validEntry = True
      else:
        validEntry = False
        validConfigSetting = False

  return inputChars, None

# For scanning for strings
def prepare_filter_mode_strings(currentUser, scanMode, filterMode, config):
  currentUserName = currentUser[1]
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

    # Convert comma separated string into list with function, then check against current user's name
    filterStringList = string_to_list(inputString, lower=True)
    if len(filterStringList) > 0:
      if filterMode == "Username" or filterMode == "NameAndText":
        validEntry = safety_check_username_against_filter(currentUserName.lower(), scanMode, filterStringList=filterStringList, bypass=bypass)
      elif filterMode == "Text":
        validEntry = True
    else:
      validConfigSetting = False

    if validEntry == True:
      if config and config['strings_to_filter'] != "ask":
        pass
      else:
        print(f"     {whatToScanMsg} will be scanned for {F.MAGENTA}ANY{S.R} of the following strings:")
        print(filterStringList)
      if choice("Begin scanning? ", bypass) == True:
        validEntry = True
      else:
        validEntry = False

  return filterStringList, None

# For scanning for regex expression
def prepare_filter_mode_regex(currentUser, scanMode, filterMode, config):
  currentUserName = currentUser[1]
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
      bypass = False

    validationResults = validate_regex(inputtedExpression) # Returns tuple of valid, and processed expression
    validExpression = validationResults[0]

    if validExpression == True:
      processedExpression = validationResults[1]
      print(f"     The expression appears to be {F.GREEN}valid{S.R}!")
      if filterMode == "Username" or filterMode == "NameAndText":
        validExpression = safety_check_username_against_filter(currentUserName, scanMode, regexPattern=processedExpression, bypass=bypass)

      if validExpression == True and choice("Begin scanning? ", bypass) == True:
        pass
      else:
        validExpression = False
        validConfigSetting = False
    else:
      print(f"     {F.RED}Error{S.R}: The expression appears to be {F.RED}invalid{S.R}!")
      validConfigSetting = False

  return processedExpression, None

# Filter Mode: User manually enters ID
# Returns inputtedSpammerChannelID
def prepare_filter_mode_ID(currentUser, scanMode, config):
  currentUserID = currentUser[0]
  processResult = (False, None) #Tuple, first element is status of validity of channel ID, second element is channel ID
  validConfigSetting = True
  while processResult[0] == False:
    if validConfigSetting == True and config and config['channel_ids_to_filter'] != "ask":
      inputtedSpammerChannelID = config['channel_ids_to_filter']
      bypass = True
    else:
      bypass = False
      inputtedSpammerChannelID = input(f"Enter the {F.LIGHTRED_EX} Channel link(s) or ID(s){S.R} of the spammer (comma separated): ")

    processResult = process_spammer_ids(inputtedSpammerChannelID)
    if processResult[0] == True:
      inputtedSpammerChannelID = processResult[1] # After processing, if valid, inputtedSpammerChannelID is a list of channel IDs
    else:
      validConfigSetting = False
  print("\n")

  # Check if spammer ID and user's channel ID are the same, and warn
  # If using channel-wide scanning mode, program will not run for safety purposes
  if any(currentUserID == i for i in inputtedSpammerChannelID):
    print(f"{B.RED}{F.WHITE} WARNING: {S.R} - You entered your own channel ID!")
    print(f"For safety purposes, this program always {F.YELLOW}ignores{S.R} your own comments.")

    if config and config['channel_ids_to_filter'] != "ask":
      pass
    else:
      input("\nPress Enter to continue...")
  
  return inputtedSpammerChannelID, None

# For Filter mode auto-ascii, user inputs nothing, program scans for non-ascii
def prepare_filter_mode_non_ascii(currentUser, scanMode, config):

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
    if selection == "1":
      print(f"Searches for {F.YELLOW}usernames with emojis, unicode symbols, and rare foreign characters{S.R} such as: ✔️ ☝️ 🡆 ▲ π Ɲ Œ")
      if choice("Choose this mode?", bypass) == True:
        regexPattern = r"[^\x00-\xFF]"
        confirmation = True
    elif selection == "2":
      print(f"Searches for {F.YELLOW}usernames with anything EXCEPT{S.R} the following: {F.YELLOW}Letters, numbers, punctuation, and common special characters{S.R} you can type with your keyboard like: % * & () + ")
      if choice("Choose this mode?", bypass) == True:
        regexPattern = r"[^\x00-\x7F]"
        confirmation = True
    elif selection == "3":
      print(f"Searches for {F.YELLOW}usernames with anything EXCEPT letters, numbers, and spaces{S.R} - {B.RED}{F.WHITE} EXTREMELY LIKELY to cause collateral damage!{S.R} Recommended to just use to manually gather list of spammer IDs, then use a different mode to delete.")
      if choice("Choose this mode?", bypass) == True:
        regexPattern = r"[^a-zA-Z0-9 ]"
        confirmation = True
    else:
      print(f"Invalid input: {selection} - Must be 1, 2, or 3.")
      validConfigSetting = False
    
    if confirmation == True:
      confirmation = safety_check_username_against_filter(currentUser[1], scanMode=scanMode, regexPattern=regexPattern, bypass=bypass)

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
def prepare_filter_mode_smart(currentUser, scanMode, config, miscData, sensitive=False):
  currentUserName = currentUser[1]
  rootDomainList = miscData['rootDomainList']
  spamDomainList = miscData['spamDomainList']
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

  # General Spammer Criteria
  #usernameBlackChars = ""
  spamGenEmoji_Raw = b'@Sl-~@Sl-};+UQApOJ|0pOJ~;q_yw3kMN(AyyBUh'
  usernameBlackWords_Raw = [b'aA|ICWn^M`', b'aA|ICWn>^?c>', b'Z*CxTWo%_<a$#)', b'c4=WCbY*O1XL4a}', b'Z*CxIZgX^DXL4a}', b'Z*CxIX8', b'V`yb#YanfTAY*7@Zf<34', b'b7f^9ZFwMLXkl({Wo!', b'c4>2IbRcbcAY*7@Zf<34', b'cWHEJATS_yX=G(@a{', b'cWHEJAZ~9Uc4=f~Z*u', b'cWHEJZ*_DaVQzUKc4=e']
  usernameObfuBlackWords_Raw = [b'c4Bp7YjX', b'b|7MPV{3B']
  usernameRedWords = ["whatsapp", "telegram"]
  textObfuBlackWords = ['telegram']
  
  # General Settings
  unicodeCategoriesStrip = ["Mn", "Cc", "Cf", "Cs", "Co", "Cn"] # Categories of unicode characters to strip during normalization

  # Create General Lists
  usernameBlackWords, usernameObfuBlackWords = [], []
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
  blackAdWords, redAdWords, yellowAdWords, exactRedAdWords, usernameBlackWords = [], [], [], [], []
  for x in blackAdWords_Raw: blackAdWords.append(b64decode(x).decode(utf_16))
  for x in redAdWords_Raw: redAdWords.append(b64decode(x).decode(utf_16))
  for x in yellowAdWords_Raw: yellowAdWords.append(b64decode(x).decode(utf_16))
  for x in exactRedAdWords_Raw: exactRedAdWords.append(b64decode(x).decode(utf_16))
  

  # Prepare Filters for Type 2 Spammers
  redAdEmojiSet = make_char_set(redAdEmoji)
  yellowAdEmojiSet = make_char_set(yellowAdEmoji)
  hrtSet = make_char_set(hrt)
  
  # Prepare Regex for Type 2 and General Spammers
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
  spamDomainRegex = []
  for domain in spamDomainList:
    expression = re.compile(confusable_regex(domain.upper(), include_character_padding=False))
    spamDomainRegex.append(expression)

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
    'spamDomainRegex': spamDomainRegex,
    }
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
  global youtube
  global matchedCommentsDict
  global vidIdDict
  global vidTitleDict
  global scannedRepliesCount
  global scannedCommentsCount
  global matchSamplesDict
  global authorMatchCountDict

  # Default values for global variables
  matchedCommentsDict = {}
  authorMatchCountDict = {}
  vidIdDict = {}
  vidTitleDict = {}
  matchSamplesDict = {}
  scannedRepliesCount = 0
  scannedCommentsCount = 0
  regexPattern = ""
  
  # Declare Default Variables
  maxScanNumber = 999999999
  scanVideoID = None
  videosToScan = []
  nextPageToken = "start"
  logMode = False
  userNotChannelOwner = False
  spamListPathsDict = {}
  
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
    youtube = get_authenticated_service() # Create authentication object
  except Exception as e:
    if "invalid_grant" in str(e):
      print(f"{F.YELLOW}[!] Invalid token{S.R} - Requires Re-Authentication")
      os.remove(TOKEN_FILE_NAME)
      youtube = get_authenticated_service()
    else:
      print('\n')
      traceback.print_exc() # Prints traceback
      print("----------------")
      print(f"{F.RED}[!!!] Error: {S.R}" + str(e))
      print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      input(f"\nError Code A-1: {F.RED}Something went wrong during authentication.{S.R} {F.YELLOW}Try deleting the token.pickle file.{S.R} \nPress Enter to exit...")
      sys.exit()

  # Check for config file, load into dictionary 'config'
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
  if config != None:
    if config['use_this_config'] == 'ask':
      if configOutOfDate == True:
        print(f"{F.LIGHTRED_EX}WARNING!{S.R} Your config file is out of date. If you don't generate a new one, you might get errors.")
      if choice(f"\nFound {F.YELLOW}config file{S.R}, use those settings?") == False:
        config = None
      os.system(clear_command)
    elif config['use_this_config'] == False:
      config = None
    elif config['use_this_config'] == True:
      pass
    else:
      print("Error C-1: Invalid value in config file for setting 'use_this_config' - Must be 'True', 'False', or 'Ask'")
      input("Press Enter to exit...")
      sys.exit()

  # Check for program and list updates
  print("Checking for updates to program and spam lists...")
  spamListFolder = "spam_lists"
  spamDomainListFileName = "SpamDomainsList.txt"
  spamDomainListPath = os.path.join(spamListFolder, spamDomainListFileName) # Path to version included in packaged assets folder
  spamListPathsDict['spamDomainListPath'] = spamDomainListPath
  if not config or config['auto_check_update'] == True:
    try:
      updateAvailable = check_for_update(version, silentCheck=True)
    except:
      print(f"{F.LIGHTRED_EX}Error Code U-3 occurred while checking for updates. (Checking can be disabled using the config file setting) Continuing...{S.R}\n")      
      updateAvailable = False
    
    # Check if spam list file exists, see if out of date based on today's date
    # Therefore should only need to use GitHub api once a day
    if os.path.exists(spamListPathsDict['spamDomainListPath']):
      spamDomainListVersion = get_list_file_version(spamListPathsDict['spamDomainListPath'])
    else:
      spamDomainListVersion = None

    # Check if today or tomorrow's date is later than the last update date (add day to account for time zones)
    if spamDomainListVersion and (datetime.today()+timedelta(days=1) >= datetime.strptime(spamDomainListVersion, '%Y.%m.%d')):
      spamDomainList = ingest_list_file(spamListPathsDict['spamDomainListPath'])
    else:
      try:
        check_lists_update(spamDomainListVersion, silentCheck=True)
        spamDomainList = ingest_list_file(spamListPathsDict['spamDomainListPath'])
      except Exception as e:
        # Get backup from asset folder
        spamDomainList = ingest_asset_file(spamDomainListFileName)

  else:
    spamDomainList = ingest_list_file(spamListPathsDict['spamDomainListPath'])
    if spamDomainList == None:
      spamDomainList = ingest_asset_file(spamDomainListFileName)
    updateAvailable = False
    spamDomainListVersion = get_list_file_version(spamListPathsDict['spamDomainListPath'])
  os.system(clear_command)

  # Load any other data
  print("Loading other assets..\n")
  rootDomainListAssetFile = "rootZoneDomainList.txt"
  miscData = {}
  rootDomainList = ingest_asset_file(rootDomainListAssetFile)
  miscData['rootDomainList'] = rootDomainList
  miscData['spamDomainList'] = spamDomainList
  os.system(clear_command)

  if config:
    moderator_mode = config['moderator_mode']
  else:
    moderator_mode = False

  #----------------------------------- Begin Showing Program ---------------------------------
  print(f"{F.LIGHTYELLOW_EX}\n===================== YOUTUBE SPAMMER PURGE v" + version + f" ====================={S.R}")
  print("=========== https://github.com/ThioJoe/YouTube-Spammer-Purge ===========")
  print("================= Author: ThioJoe - YouTube.com/ThioJoe ================ \n")

  # Instructions
  print("Purpose: Lets you scan for spam comments and mass-delete them all at once \n")
  print("NOTE: It's probably better to scan a single video, because you can scan all those comments,")
  print("      but scanning your entire channel must be limited and might miss older spam comments.")
  print("You will be shown the comments to confirm before they are deleted.")

  # While loop until user confirms they are logged into the correct account
  confirmedCorrectLogin = False
  while confirmedCorrectLogin == False:
    # Get channel ID and title of current user, confirm with user
    currentUser = get_current_user(config) # Returns [channelID, channelTitle]
    print("\n    >  Currently logged in user: " + f"{F.LIGHTGREEN_EX}" + str(currentUser[1]) + f"{S.R} (Channel ID: {F.LIGHTGREEN_EX}" + str(currentUser[0]) + f"{S.R} )")
    if choice("       Continue as this user?", currentUser[2]) == True:
      check_channel_id = currentUser[0]
      confirmedCorrectLogin = True
      os.system(clear_command)
    else:
      os.remove(TOKEN_FILE_NAME)
      os.system(clear_command)
      youtube = get_authenticated_service()
  
  # User selects scanning mode,  while Loop to get scanning mode, so if invalid input, it will keep asking until valid input
  print(f"\n---------- {F.YELLOW}Scanning Options{S.R} ----------")
  print(f"      1. Scan a {F.LIGHTBLUE_EX}Specific video{S.R}")
  print(f"      2. Scan {F.LIGHTCYAN_EX}recent videos{S.R} for a channel")
  print(f"      3. Scan recent comments across your {F.LIGHTMAGENTA_EX}Entire Channel{S.R}")
  print(f"      4. Scan a {F.LIGHTMAGENTA_EX}community post{S.R} (Experimental)")
  print(f"---------- {F.LIGHTRED_EX}Other Options{S.R} ----------")
  print(f"      5. Create your own config file to quickly run the program with pre-set settings")
  print(f"      6. Recover deleted comments using log file")
  print(f"      7. Check For Updates\n")
  
  # Check for updates silently
  
  if updateAvailable == True:
    print(f"{F.LIGHTGREEN_EX}Notice: A new version is available! Choose 'Check For Updates' option for details.{S.R}\n")
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
    validVideoIDResult = (False, None) # Tuple, first element is status of validity of video ID, second element is video ID
    confirm = False
    validConfigSetting = True
    numVideos = 1
    videosToScan = [{}]

    while validVideoIDResult[0] == False or confirm == False:
      if validConfigSetting == True and config and config['video_to_scan'] != 'ask':
        enteredVideos = config['video_to_scan']
      else:
        enteredVideos = input(F"Enter {F.YELLOW}Video Link{S.R} or {F.YELLOW}Video ID{S.R} to scan: ")
        validConfigSetting = False

      validVideoIDResult = validate_video_id(enteredVideos) # Sends link or video ID for isolation and validation
      
      if validVideoIDResult[0] == True:  #validVideoID now contains True/False and video ID
        videosToScan[0]['videoID'] = str(validVideoIDResult[1])
        videosToScan[0]['videoTitle'] = get_video_title(videosToScan[0]['videoID'])
        videosToScan[0]['commentCount'] = get_comment_count(videosToScan[0]['videoID'])

        # Add to comment overall comment count
        miscData['totalCommentCount'] = 0
        for video in videosToScan:
          miscData['totalCommentCount'] += int(video['commentCount'])

        print(f"\n{F.BLUE}Chosen Video:{S.R}  " + videosToScan[0]['videoTitle'])

        channelOwner = get_channel_id(videosToScan[0]['videoID'])
        if currentUser[0] != channelOwner[0]:
          userNotChannelOwner = True
        miscData['channelOwnerID'] = channelOwner[0]
        miscData['channelOwnerName'] = channelOwner[1]
        
        # Ask if correct video, or skip if config
        if config and config['skip_confirm_video'] == True:
          confirm = True
        else:
          if userNotChannelOwner == True and moderator_mode == False:
            print(f"{F.LIGHTRED_EX}NOTE: This is not your video. Enabling '{F.YELLOW}Not Your Channel Mode{F.LIGHTRED_EX}'. You can report spam comments, but not delete them.{S.R}")
          elif userNotChannelOwner == True and moderator_mode == True:
            print(f"{F.LIGHTRED_EX}NOTE: {F.YELLOW}Moderator Mode is enabled{F.LIGHTRED_EX}. You can hold comments for review when using certain modes{S.R}")
          confirm = choice("Is this video correct?", bypass=validConfigSetting)

      else:
        print("\nInvalid Video ID or Link: " + str(validVideoIDResult[1]))
        validConfigSetting = False

  elif scanMode == "recentVideos":
    confirm = False
    validEntry = False
    validChannel = False
    
    while validChannel == False:
      # Get and verify config setting for channel ID
      if config and config['channel_to_scan'] != 'ask':
        if config['channel_to_scan'] == 'mine':
          channelID = currentUser[0]
          channelTitle = currentUser[1]
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
        channelID = currentUser[0]
        channelTitle = currentUser[1]
        validChannel = True
      else:
        validChannel, channelID, channelTitle = validate_channel_id(inputtedChannel)

    if currentUser[0] != channelID:
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
        print(f"\nEnter the {F.YELLOW}number most recent videos{S.R} to scan back-to-back (up to 5):")
        numVideos = input("\nNumber of Recent Videos (1-5): ")
      try:
        numVideos = int(numVideos)
        if numVideos > 0 and numVideos <= 5:
          validEntry = True
          validConfigSetting = True
        else:
          print("Error: Entry must be from 1 to 5")
          validEntry = False
          validConfigSetting = False
      except ValueError:
        print(f"{F.LIGHTRED_EX}Error:{S.R} Entry must be a whole number, from 1 to 5.")

      if validEntry == True:
        # Fetch recent videos and print titles to user for confirmation
        videosToScan = get_recent_videos(channelID, numVideos)

        # Get total comment count
        miscData['totalCommentCount'] = 0
        for video in videosToScan:
          miscData['totalCommentCount'] += int(video['commentCount'])

        if len(videosToScan) < numVideos:
          print(f"\n{F.YELLOW}WARNING:{S.R} Only {len(videosToScan)} videos found.")
        print("\nRecent Videos To Be Scanned:")
        for i in range(len(videosToScan)):
          print(f"  {i+1}. {videosToScan[i]['videoTitle']}")

        if config and (config['skip_confirm_video'] == True or validConfigSetting == True):
          confirm = True
        else:
          if userNotChannelOwner == True and moderator_mode == False:
            print(f"{F.LIGHTRED_EX}NOTE: These aren't your videos. Enabling '{F.YELLOW}Not Your Channel Mode{F.LIGHTRED_EX}'. You can report spam comments, but not delete them.{S.R}")
          elif userNotChannelOwner == True and moderator_mode == True:
            print(f"{F.LIGHTRED_EX}NOTE: {F.YELLOW}Moderator Mode is enabled{F.LIGHTRED_EX}. You can hold comments for review when using certain modes{S.R}")
          confirm = choice("Is everything correct?", bypass=validConfigSetting)  

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
          maxScanNumber = int(input(f"Enter the maximum {F.YELLOW}number of comments{S.R} to scan: "))

        if maxScanNumber > 0:
          validInteger = True # If it gets here, it's an integer, otherwise goes to exception
        else:
          print("\nInvalid Input! Number must be greater than zero.")
          validConfigSetting = False
      except:
        print("\nInvalid Input! - Must be a whole number.")
        validConfigSetting = False
    miscData['channelOwnerID'] = currentUser[0]
    miscData['channelOwnerName'] = currentUser[1]

  elif scanMode == 'communityPost':
    print(f"\nNOTES: This mode is {F.YELLOW}experimental{S.R}, and not as polished as other features. Expect some janky-ness.")
    print("   > It is also much slower to retrieve comments, because it does not use the API")
    print(f"   > You should only scan {F.YELLOW}your own{S.R} community posts, or things might not work right")
    confirm = False
    while confirm == False:
      communityPostInput = input("\nEnter the ID or link of the community post: ")
      # Validate post ID or link, get additional info about owner, and useable link
      isValid, communityPostID, postURL, postOwnerID, postOwnerUsername = validate_post_id(communityPostInput)
      if isValid == True:
        print("\nCommunity Post By: " + postOwnerUsername)
        if postOwnerID != currentUser[0]:
          userNotChannelOwner = True
          print("\nWarning: You are scanning someone elses post. 'Not Your Channel Mode' Enabled.")
        confirm = choice("Continue?")
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
    create_config_file()
    print("\nConfig file created: SpamPurgeConfig.ini - Open file with text editor to read instructions and change settings.")

  # Check for latest version
  elif scanMode == "checkUpdates":
    check_lists_update(spamDomainListVersion)
    check_for_update(version)

  # Recove deleted comments mode
  elif scanMode == "recoverMode":
    recover_deleted_comments()

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

  if filterMode == "ID":
    filterSettings = prepare_filter_mode_ID(currentUser, scanMode, config)
    inputtedSpammerChannelID = filterSettings[0]

  elif filterMode == "AutoASCII":
    filterSettings = prepare_filter_mode_non_ascii(currentUser, scanMode, config)
    regexPattern = filterSettings[0]

  elif filterMode == "AutoSmart":
    filterSettings = prepare_filter_mode_smart(currentUser, scanMode, config, miscData)
    inputtedUsernameFilter = filterSettings[0]
    inputtedCommentTextFilter = filterSettings[0]
  elif filterMode == "SensitiveSmart":
    filterSettings = prepare_filter_mode_smart(currentUser, scanMode, config, miscData, sensitive=True)
    inputtedUsernameFilter = filterSettings[0]
    inputtedCommentTextFilter = filterSettings[0]

  elif filterSubMode == "chars":
    filterSettings = prepare_filter_mode_chars(currentUser, scanMode, filterMode, config)
  elif filterSubMode == "string":
    filterSettings = prepare_filter_mode_strings(currentUser, scanMode, filterMode, config)
  elif filterSubMode == "regex":
    filterSettings = prepare_filter_mode_regex(currentUser, scanMode, filterMode, config)
    regexPattern = filterSettings[1]

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
        commentID = key
        authorChannelID = value['authorChannelID']
        authorChannelName = value['authorName']
        commentText = value['commentText']
        check_against_filter(currentUser, miscData, filterMode=filterMode, filterSubMode=filterSubMode, commentID=commentID, videoID=communityPostID, authorChannelID=authorChannelID, parentAuthorChannelID=None, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, authorChannelName=authorChannelName, commentText=commentText, regexPattern=regexPattern)
    scan_community_post(communityPostID, maxScanNumber)

  else:
    # Goes to get comments for first page
    print("\n------------------------------------------------------------------------------")
    print("(Note: If the program appears to freeze, try right clicking within the window)\n")
    print("                          --- Scanning --- \n")
  
    def scan_video(youtube, miscData, currentUser, filterMode, filterSubMode, videoID, check_channel_id, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, regexPattern, videosToScan=None, videoTitle=None, showTitle=False, i=1):
      nextPageToken = get_comments(youtube, currentUser, miscData, filterMode, filterSubMode, videoID, check_channel_id, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, regexPattern=regexPattern, videosToScan=videosToScan)
      if showTitle == True and len(videosToScan) > 0:
        # Prints video title, progress count, adds enough spaces to cover up previous stat print line
        offset = 95 - len(videoTitle)
        if offset > 0:
          spacesStr = " " * offset
        else:
          spacesStr = ""
        print(f"Scanning {i}/{len(videosToScan)}: " + videoTitle + spacesStr + "\n")

      print_count_stats(miscData, videosToScan, final=False)  # Prints comment scan stats, updates on same line
      # After getting first page, if there are more pages, goes to get comments for next page
      while nextPageToken != "End" and scannedCommentsCount < maxScanNumber:
        nextPageToken = get_comments(youtube, currentUser, miscData, filterMode, filterSubMode, videoID, check_channel_id, nextPageToken, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, regexPattern=regexPattern, videosToScan=videosToScan)

    if scanMode == "entireChannel":
      scan_video(youtube, miscData, currentUser, filterMode, filterSubMode, scanVideoID, check_channel_id, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, regexPattern)
    elif scanMode == "recentVideos" or scanMode == "chosenVideos":
      i = 1
      for video in videosToScan:
        videoID = str(video['videoID'])
        videoTitle = str(video['videoTitle'])
        scan_video(youtube, miscData, currentUser, filterMode, filterSubMode, videoID, check_channel_id, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, regexPattern, videosToScan=videosToScan, videoTitle=videoTitle, showTitle=True, i=i)
        i += 1
    print_count_stats(miscData, videosToScan, final=True)  # Prints comment scan stats, finalizes
  
##########################################################
  bypass = False
  if config and config['enable_logging'] != 'ask':
    logSetting = config['enable_logging']
    if logSetting == True:
      logMode = True
      bypass = True
    elif logSetting == False:
      logMode = False
      bypass = True
    elif logSetting == "ask":
      bypass = False
    else:
      bypass = False
      print("Error Code C-2: Invalid value for 'enable_logging' in config file:  " + logSetting)

  # Counts number of found spam comments and prints list
  spam_count = len(matchedCommentsDict)
  if spam_count == 0: # If no spam comments found, exits
    print(f"{B.RED}{F.BLACK}No matched comments or users found!{S.R}\n")
    print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
    if bypass == False:
      input("\nPress Enter to exit...")
      sys.exit()
    elif bypass == True:
      print("Exiting in 5 seconds...")
      time.sleep(5)
      sys.exit()
  print(f"Number of Matched Comments Found: {B.RED}{F.WHITE} " + str(len(matchedCommentsDict)) + f" {S.R}")

  if bypass == False:
    # Asks user if they want to save list of spam comments to a file
    print(f"\nSpam comments ready to display. Also {F.LIGHTGREEN_EX}save a log file?{S.R} {B.GREEN}{F.BLACK} Highly Recommended! {S.R}")
    print(f"        (It even allows you to {F.LIGHTGREEN_EX}restore{S.R} deleted comments later)")
    logMode = choice(f"Save Log File (Recommended)?")

  if logMode == True:
    global logFileName
    fileName = "Spam_Log_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S" + ".rtf")
    if config and config['log_path'] and config['log_path'] != "default":
        logFileName = os.path.normpath(config['log_path'] + "/" + fileName)
        print(f"Log file will be located at {F.YELLOW}" + logFileName + f"{S.R}\n")
    else:
        logFileName = fileName
        print(f"Log file will be called {F.YELLOW}" + logFileName + f"{S.R}\n")
    
    if bypass == False:
      input(f"Press {F.YELLOW}Enter{S.R} to display comments...")

    # Write heading info to log file
    write_rtf(logFileName, firstWrite=True)
    write_rtf(logFileName, "\\par----------- YouTube Spammer Purge Log File -----------\\line\\line " + "\n\n")
    if filterMode == "ID":
      write_rtf(logFileName, "Channel IDs of spammer searched: " + ", ".join(inputtedSpammerChannelID) + "\\line\\line " + "\n\n")
    elif filterMode == "Username":
      write_rtf(logFileName, "Characters searched in Usernames: " + make_rtf_compatible(", ".join(inputtedUsernameFilter)) + "\\line\\line " + "\n\n")
    elif filterMode == "Text":
      write_rtf(logFileName, "Characters searched in Comment Text: " + make_rtf_compatible(", ".join(inputtedCommentTextFilter)) + "\\line\\line " + "\n\n")
    elif filterMode == "NameAndText":
      write_rtf(logFileName, "Characters searched in Usernames and Comment Text: " + make_rtf_compatible(", ".join(filterSettings[1])) + "\\line\\line " + "\n\n")
    elif filterMode == "AutoASCII":
      write_rtf(logFileName, "Automatic Search Mode: " + make_rtf_compatible(str(filterSettings[1])) + "\\line\\line " + "\n\n")
    elif filterMode == "AutoSmart":
      write_rtf(logFileName, "Automatic Search Mode: Smart Mode \\line\\line " + "\n\n")
    elif filterMode == "SensitiveSmart":
      write_rtf(logFileName, "Automatic Search Mode: Sensitive Smart \\line\\line " + "\n\n")
    write_rtf(logFileName, "Number of Matched Comments Found: " + str(len(matchedCommentsDict)) + "\\line\\line \n\n")
    write_rtf(logFileName, f"IDs of Matched Comments: \n[ {', '.join(matchedCommentsDict)} ] \\line\\line\\line \n\n\n")
  else:
    print("Continuing without logging... \n")

  # Prints list of spam comments
  if scanMode == "communityPost":
    scanVideoID = communityPostID
  print("\n\nAll Matched Comments: \n")
  print_comments(scanVideoID, list(matchedCommentsDict.keys()), logMode, scanMode)
  print(f"\n{F.WHITE}{B.RED} NOTE: {S.R} Check that all comments listed above are indeed spam.")
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
    sys.exit()
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
      print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      input("Press Enter to exit...")
      sys.exit()


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
        excludedDict, rtfExclude = exclude_authors(confirmDelete)
        exclude = True
      else:
        input(f"\nDeletion {F.YELLOW}CANCELLED{S.R} (Because no matching option entered). Press Enter to exit...")
        sys.exit()

  
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

    elif deletionMode == "heldForReview":
      pass
    elif deletionMode == "reportSpam":
      pass
    
    ### ---------------- Reporting / Deletion Begins  ----------------
    delete_found_comments(list(matchedCommentsDict), banChoice, deletionMode)
    if deletionMode != "reportSpam":
      if not config or config and config['check_deletion_success'] == True:
        check_deleted_comments(matchedCommentsDict)
      elif config and config['check_deletion_success'] == False:
        print("\nSkipped checking if deletion was successful.\n")

    if logMode == True:
      write_rtf(logFileName, "\n\n \\line\\line Spammers Banned: " + str(banChoice)) # Write whether or not spammer is banned to log file
      write_rtf(logFileName, "\n\n \\line\\line Action Taken on Comments: " + str(deletionModeFriendlyName) + "\n\n"+ "\\line\\line")
      if exclude == True:
        write_rtf(logFileName, str(rtfExclude))
    input(f"\nProgram {F.LIGHTGREEN_EX}Complete{S.R}. Press Enter to Exit...")

  elif config:
      sys.exit()
  else:
    input(f"\nDeletion {F.LIGHTRED_EX}Cancelled{S.R}. Press Enter to exit...")
    sys.exit()

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
  except HttpError as e:
    traceback.print_exc()
    print("------------------------------------------------")
    print("Error Message: " + str(e))
    if e.status_code:
      print("Status Code: " + str(e.status_code))
      if e.error_details[0]["reason"]: # If error reason is available, print it
          reason = str(e.error_details[0]["reason"])
          print_exception_reason(reason)
      input("\nPress Enter to Exit...")
    else:
      print(f"{F.RED}Unknown Error - Code: X-2{S.R} occurred. If this keeps happening, consider posting a bug report on the GitHub issues page, and include the above error info.")
      input("\n Press Enter to Exit...")
  except SystemExit:
    sys.exit()
  else:
    print("\nFinished Executing.")      

