#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#######################################################################################################
################################# YOUTUBE SPAM COMMENT DELETER ########################################
#######################################################################################################
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
###
### Function: Allows you to mass-delete delete all comment replies by a particular user all at once.
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
### NOTES:    1. The script also scans top level comments from the spammer
###
###           2. To use this script, you will need to obtain your own API credentials file by making
###				       a project via the Google Developers Console (aka 'Google Cloud Platform').
###              The credential file should be re-named 'client_secret.json' and be placed in the 
###              same directory as this script.
###				            >>> See the Readme for instructions on this.
###
###           3. I suck at programming so if something doesn't work I'll try to fix it but might not
###              even know how, so don't expect too much.
###
###
### Author:   ThioJoe - YouTube.com/ThioJoe
###                     Twitter.com/ThioJoe
###
### IMPORTANT:  I OFFER NO WARRANTY OR GUARANTEE FOR THIS SCRIPT. USE AT YOUR OWN RISK.
###             I tested it on my own and implemented some failsafes as best as I could,
###             but there could always be some kind of bug. You should inspect the code yourself.
version = "1.7.0"
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

from gui import *

import os
import re
import sys
from datetime import datetime
import traceback
import platform
import rtfunicode

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from colorama import init, Fore as F, Back as B, Style as S

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
    print("\n ------------- ERROR: "+CLIENT_SECRETS_FILE+" file not found! ------------- ")
    print(" Make sure it is placed in the same folder as the program, and is spelled as above \n")
    print(" ----- Or: Did you create a Google Cloud Platform Project to access the API? ----- ")
    print(" ------ See section with instructions on obtaining an API Key at this page: ------- ")
    print(" ---------- https://github.com/ThioJoe/YouTube-Spammer-Purge/ ---------- ")
    input("\n Press Enter to Exit...")
    exit()

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
      flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=YOUTUBE_READ_WRITE_SSL_SCOPE)
      creds = flow.run_local_server(port=0, authorization_prompt_message="Log in using the browser window.")
      # Save the credentials for the next run
    with open(TOKEN_FILE_NAME, 'w') as token:
      token.write(creds.to_json())
  return build(API_SERVICE_NAME, API_VERSION, credentials=creds, discoveryServiceUrl=DISCOVERY_SERVICE_URL)


##########################################################################################
############################### PRINT SPECIFIC COMMENTS ##################################
##########################################################################################

# First prepared comments into segments of 50 to be submitted to API simultaneously
# Then uses print_prepared_comments() to print / log the comments
def print_comments(check_video_id_localprint, comments, logMode):
  j = 0 # Counting index when going through comments all comment segments
  correctly_ordered_comments_list =[] # Holds new list correctly ordered matched comments, same order as returned by API and presented to user - will be 

  if len(comments) > 50:
    remainder = len(comments) % 50
    numDivisions = int((len(comments)-remainder)/50)
    for i in range(numDivisions):
      j, k = print_prepared_comments(check_video_id_localprint,comments[i*50:i*50+50], j, logMode)
      correctly_ordered_comments_list.extend(k)
    if remainder > 0:
      j, k = print_prepared_comments(check_video_id_localprint,comments[numDivisions*50:len(comments)],j, logMode)
      correctly_ordered_comments_list.extend(k)
  else:
    j, k = print_prepared_comments(check_video_id_localprint,comments, j, logMode)
    correctly_ordered_comments_list.extend(k)

  # Print Sample Match List
  print(f"{F.LIGHTMAGENTA_EX}---------------------------- Match Samples: One comment per matched-comment author ----------------------------{S.R}")
  if logMode == True:
      write_rtf(logFileName, "-------------------- Match Samples: One comment per matched-comment author -------------------- \\line\\line \n")
  for value in matchSamplesDict.values():
    print(value)
    if logMode == True:
      write_rtf(logFileName, make_rtf_compatible(value) + " \\line \n")
  print("---------------------------------------------------------------------------------------------------------------")

  return correctly_ordered_comments_list

# Uses comments.list YouTube API Request to get text and author of specific set of comments, based on comment ID
def print_prepared_comments(check_video_id_localprep, comments, j, logMode):

  results = youtube.comments().list(
    part="snippet",
    id=comments,  # The API request can take an entire comma separated list of comment IDs (in "id" field) to return info about
    maxResults=100, # 100 is the max per page, but multiple pages will be scanned
    fields="items/snippet/authorDisplayName,items/snippet/textDisplay,items/id,items/snippet/authorChannelId/value",
    textFormat="plainText"
  ).execute()

  # Prints author and comment text for each comment
  i = 0 # Index when going through comments
  comments_segment_list = [] # Holds list of comments for each segment

  for item in results["items"]:
    text = item["snippet"]["textDisplay"]
    author = item["snippet"]["authorDisplayName"]
    author_id_local = item["snippet"]["authorChannelId"]["value"]
    comment_id_local = item["id"]

    # Retrieve video ID from object using comment ID
    videoID = convert_comment_id_to_video_id(comment_id_local)

    # Truncates very long comments, and removes excessive multiple lines
    if len(text) > 1500:
      text = text[0:1500] + "...\n[YT Spammer Purge Note: Long Comment Truncated - Visit Link to See Full Comment]"
    if text.count("\n") > 0:
      text = text.replace("\n", " ") + "\n[YT Spammer Purge Note: Comment converted from multiple lines to single line]"

    # Add one sample from each matching author to matchSamplesDict, containing author ID, name, and text
    if author_id_local not in matchSamplesDict:
      add_sample(author_id_local, author, text)

    # Prints comment info to console
    print(str(j+1) + f". {F.LIGHTCYAN_EX}" + author + f"{S.R}:  {F.YELLOW}" + text + f"{S.R}")
    print("—————————————————————————————————————————————————————————————————————————————————————————————")
    if check_video_id_localprep is None:  # Only print video title if searching entire channel
      title = get_video_title(videoID) # Get Video Title
      print("     > Video: " + title)
    print("     > Direct Link: " + "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comment_id_local)
    print(f"     > Author Channel ID: {F.LIGHTBLUE_EX}" + author_id_local + f"{S.R}")
    print("=============================================================================================\n")


    # If logging enabled, also prints to log file 
    if logMode == True:

      # Only print video title info if searching entire channel
      if check_video_id_localprep is None:  
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
        + "     > Direct Link: " + "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comment_id_local + "\\line "+ "\n"
        + "     > Author Channel ID: \cf6" + author_id_local + r"\cf1 \line "+ "\n"
        + "=============================================================================================\\line\\line\\line" + "\n\n\n"
      )
      write_rtf(logFileName, commentInfo)

    # Appends comment ID to new list of comments so it's in the correct order going forward, as provided by API and presented to user
    # Must use append here, not extend, or else it would add each character separately
    comments_segment_list.append(comment_id_local)
    i += 1
    j += 1

  return j, comments_segment_list

# Adds a sample to matchSamplesDict and preps formatting
def add_sample(authorID, authorName, commentText):
  global matchSamplesDict

  # Left Justify Author Name and Comment Text
  if len(authorName) > 30:
    authorName = authorName[0:27] + "..."
  authorName = authorName[0:30].ljust(30)+": "

  if len(commentText) > 85:
    commentText = commentText[0:82] + "..."
  commentText = commentText[0:85].ljust(85)

  # Add sample to matchSamplesDict
  matchSamplesDict[authorID] = (authorName + commentText)


##########################################################################################
############################## GET COMMENT THREADS #######################################
##########################################################################################

# Call the API's commentThreads.list method to list the existing comments.
def get_comments(youtube, filterMode, filterSubMode, check_video_id=None, check_channel_id=None, nextPageToken=None, inputtedSpammerChannelID=None, inputtedUsernameFilter=None, inputtedCommentTextFilter=None, regexPattern=None):  # None are set as default if no parameters passed into function
  global scannedCommentsCount
  # Initialize some variables
  authorChannelName = None
  commentText = None
  parentAuthorChannelID = None

  if filterMode == "ID": # User entered spammer IDs -- Get Extra Info: None
    fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/replies/comments,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value"
  elif filterMode == "Username" or filterMode == "AutoASCII": # Filter char by Username / Auto Regex non-ascii username -- Get Extra Info: Author Display Name
    fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/replies/comments,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/authorDisplayName"
  elif filterMode == "Text": # Filter char by Comment text -- Get Extra Info: Comment Text
    fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/replies/comments,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/textDisplay"
  elif filterMode == "AutoSmart": # Filter with smart auto mode - Get Extra Info: Author Display Name, Comment Text
    fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/replies/comments,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/authorDisplayName,items/snippet/topLevelComment/snippet/textDisplay"

  # Gets all comment threads for a specific video
  if check_video_id is not None:
    results = youtube.commentThreads().list(
      part="snippet, replies",
      videoId=check_video_id, 
      maxResults=100, # 100 is the max per page allowed by YouTube, but multiple pages will be scanned
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()
  
  # Get all comment threads across the whole channel
  elif check_video_id is None:
    results = youtube.commentThreads().list(
      part="snippet, replies",
      allThreadsRelatedToChannelId=check_channel_id,
      maxResults=100, # 100 is the max per page allowed by YouTube, but multiple pages will be scanned
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()  

  # Get token for next page
  try:
    RetrievedNextPageToken = results["nextPageToken"]
  except KeyError:
    RetrievedNextPageToken = "End"  
 
  # After getting all comments threads for page, extracts data for each and stores matches in spamCommentsID
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
    # Need individual tries because not all are fetched for each mode
    if filterMode == "Username" or filterMode == "AutoASCII" or filterMode == "AutoSmart":
      try:
        authorChannelName = comment["snippet"]["authorDisplayName"]
      except KeyError:
        authorChannelName = "[Deleted Channel]"
    if filterMode == "Text" or filterMode == "AutoSmart":
      try:
        commentText = comment["snippet"]["textDisplay"]
      except KeyError:
        commentText = "[Deleted/Missing Comment]"
    
    # Runs check against comment info for whichever filter data is relevant
    check_against_filter(filterMode=filterMode, filterSubMode=filterSubMode, commentID=parent_id, videoID=videoID, parentAuthorChannelID=None, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, authorChannelID=parentAuthorChannelID, authorChannelName=authorChannelName, commentText=commentText, regexPattern=regexPattern)
    scannedCommentsCount += 1  # Counts number of comments scanned, add to global count

    if numReplies > 0 and len(limitedRepliesList) < numReplies:
      get_replies(filterMode, filterSubMode, parent_id, videoID, parentAuthorChannelID, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, regexPattern)
    elif numReplies > 0 and len(limitedRepliesList) <= numReplies:
      get_replies(filterMode, filterSubMode, parent_id, videoID, parentAuthorChannelID, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, regexPattern, limitedRepliesList)
    else:
      print_count_stats(final=False)  # Updates displayed stats if no replies
  
  return RetrievedNextPageToken


##########################################################################################
##################################### GET REPLIES ########################################
##########################################################################################

# Call the API's comments.list method to list the existing comment replies.
def get_replies(filterMode, filterSubMode, parent_id, videoID, parentAuthorChannelID, inputtedSpammerChannelID=None, inputtedUsernameFilter=None, inputtedCommentTextFilter=None, regexPattern=None, repliesList=None):
  global scannedRepliesCount
  # Initialize some variables
  authorChannelName = None
  commentText = None
  
  if repliesList == None:

    if filterMode == "ID": # User entered spammer IDs -- Get Extra Info: None
      fieldsToFetch = "items/snippet/authorChannelId/value,items/id"
    elif filterMode == "Username" or filterMode == "AutoASCII": # Filter by Username -- Get Extra Info: Author Display Name
      fieldsToFetch = "items/snippet/authorChannelId/value,items/id,items/snippet/authorDisplayName"
    elif filterMode == "Text": # Filter by comment text -- Get Extra Info: Comment Text
      fieldsToFetch = "items/snippet/authorChannelId/value,items/id,items/snippet/textDisplay"
    elif filterMode == "AutoSmart": # Auto smart Mode: Get Extra Info: Author Display Name, Comment Text
      fieldsToFetch = "items/snippet/authorChannelId/value,items/id,items/snippet/authorDisplayName,items/snippet/textDisplay"


    results = youtube.comments().list(
      part="snippet",
      parentId=parent_id,
      maxResults=100, # 100 is the max per page, but multiple pages will be scanned
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()

    replies = results["items"]

  else:
    replies = repliesList
 
  # Iterates through items in results
  # Need to be able to catch exceptions because sometimes the API will return a comment from non-existent / deleted channel
  # Need individual tries because not all are fetched for each mode
  for reply in replies:  
    replyID = reply["id"]
    try:
      authorChannelID = reply["snippet"]["authorChannelId"]["value"]
    except KeyError:
      authorChannelID = "[Deleted Channel]"

    if filterMode == "Username" or filterMode == "AutoASCII" or filterMode == "AutoSmart": 
      try:
        authorChannelName = reply["snippet"]["authorDisplayName"]
      except KeyError:
        authorChannelName = "[Deleted Channel]"  
    
    if filterMode == "Text" or filterMode == "AutoSmart":
      try:
        commentText = reply["snippet"]["textDisplay"]
      except KeyError:
        commentText = "[Deleted/Missing Comment]"

    # Runs check against comment info for whichever filter data is relevant
    check_against_filter(filterMode=filterMode, filterSubMode=filterSubMode, commentID=replyID, videoID=videoID, parentAuthorChannelID=parentAuthorChannelID, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, authorChannelID=authorChannelID, authorChannelName=authorChannelName, commentText=commentText, regexPattern=regexPattern)

    # Update latest stats
    scannedRepliesCount += 1  # Count number of replies scanned, add to global count
    print_count_stats(final=False) # Prints out current count stats

  return True

############################## CHECK AGAINST FILTER ######################################
# The basic logic that actually checks each comment against filter criteria
def check_against_filter(filterMode, filterSubMode, commentID, videoID, parentAuthorChannelID=None, inputtedSpammerChannelID=None, inputtedUsernameFilter=None, inputtedCommentTextFilter=None, authorChannelID=None, authorChannelName=None, commentText=None, regexPattern=None):
  global vidIdDict
  global spamCommentsID

  # If the comment/username matches criteria based on mode, add to list of spam comment IDs
  # Also add key-value pair of comment ID and video ID to dictionary
  def add_spam(commentID, videoID):
    global spamCommentsID
    spamCommentsID += [commentID]
    vidIdDict[commentID] = videoID

  # Checks author of either parent comment or reply (both passed in as commentID) against channel ID inputted by user
  if filterMode == "ID":
    if any(authorChannelID == x for x in inputtedSpammerChannelID):
      add_spam(commentID, videoID)

  # Check usernames modes
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

  # Check comment text modes
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

  # Check if author name contains non-ascii characters with Regex, sensitivity based on user selection
  elif filterMode == "AutoASCII":
    if re.search(str(regexPattern), authorChannelName):
      add_spam(commentID, videoID)

  # Auto Smart Mode: Check author name and text for spammer-used characters
  # Check if reply author ID is same as parent comment author ID, if so, ignore (to account for users who reply to spammers)
  elif filterMode == "AutoSmart":
    authorChannelName = make_char_set(str(authorChannelName))
    commentText = make_char_set(str(commentText))
    if any(x in inputtedUsernameFilter for x in authorChannelName):
      add_spam(commentID, videoID)
    elif any(x in inputtedCommentTextFilter for x in commentText):
      if authorChannelID != parentAuthorChannelID:
        add_spam(commentID, videoID)

##########################################################################################
################################ DELETE COMMENTS #########################################
########################################################################################## 

# Takes in list of comment IDs to delete, breaks them into 50-comment chunks, and deletes them in groups
def delete_found_comments(commentsList,banChoice):

    # Deletes specified comment IDs
    def delete(commentIDs):
        youtube.comments().setModerationStatus(id=commentIDs, moderationStatus="rejected", banAuthor=banChoice).execute()

    total = len(commentsList)
    deletedCounter = 0  
    def print_progress(d, t): print("Deleting Comments... - Progress: [" + str(d) + " / " + str(t) + "] (In Groups of 50)", end="\r") # Prints progress of deletion
    print_progress(deletedCounter, total)

    if total > 50:                                  # If more than 50 comments, break into chunks of 50
        remainder = total % 50                      # Gets how many left over after dividing into chunks of 50
        numDivisions = int((total-remainder)/50)    # Gets how many full chunks of 50 there are
        for i in range(numDivisions):               # Loops through each full chunk of 50
            delete(commentsList[i*50:i*50+50])
            deletedCounter += 50
            print_progress(deletedCounter, total)
        if remainder > 0:
            delete(commentsList[numDivisions*50:total]) # Deletes any leftover comments range after last full chunk
            deletedCounter += remainder
            print_progress(deletedCounter, total)
    else:
        delete(commentsList)
        print_progress(deletedCounter, total)
    print("Comments Deleted! Will now verify each is gone.                          \n")

# Class for custom exception to throw if a comment is found to remain
class CommentFoundError(Exception):
    pass

# Takes in list of comment IDs and video IDs, and checks if comments still exist individually
def check_deleted_comments(commentsVideoDictionary):
    i = 0 # Count number of remaining comments
    j = 1 # Count number of checked
    total = len(commentsVideoDictionary)
    for key, value in commentsVideoDictionary.items():
        try:
          results = youtube.comments().list(
              part="snippet",
              id=key,  
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
          print("Possible Issue Deleting Comment: " + str(key) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(value) + "&lc=" + str(key))
          i += 1
          pass
        except Exception:
          print("Unhandled Exception While Deleting Comment: " + str(key) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(value) + "&lc=" + str(key))
          i += 1
          pass

    if i == 0:
        print("\n\nSuccess: All spam comments should be gone.")
    elif i > 0:
        print("\n\nWarning: " + str(i) + " spam comments may remain. Check links above or try running the program again.")
    else:
        print("\n\nSomething strange happened... The comments may or may have not been deleted.")

    return None



##########################################################################################
############################### LESSER FUNCTIONS #########################################
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

############################# GET CHANNEL ID FROM VIDEO ID #####################################
# Get channel ID from video ID using YouTube API request
def get_channel_id(video_id):
  results = youtube.videos().list(
    part="snippet",
    id=video_id,
    fields="items/snippet/channelId",
    maxResults=1
  ).execute()
  
  channel_id = results["items"][0]["snippet"]["channelId"]

  return channel_id

############################# GET CURRENTLY LOGGED IN USER #####################################
# Get channel ID and channel title of the currently authorized user
def get_current_user():
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
    print("\nError Getting Current User: Channel ID was not retrieved. Sometimes this happens if client_secrets file does not match user authorized with token.pickle file.")
    input("\nPress Enter to try logging in again...")
    os.remove(TOKEN_FILE_NAME)
    youtube = get_authenticated_service()
    results = fetch() # Try again

  try:
    channelID = results["items"][0]["id"]
    try:
      channelTitle = results["items"][0]["snippet"]["title"] # If channel ID was found, but not channel title/name
    except KeyError:
      print("Error Getting Current User: Channel ID was found, but channel title was not retrieved. If this occurs again, try deleting 'token.pickle' file and re-running. If that doesn't work, consider filing a bug report on the GitHub project 'issues' page.")
      print("    > NOTE: The program may still work - You can try continuing. Just check the channel ID is correct: " + str(channelID))
      channelTitle = ""
      input("Press Enter to Continue...")
      pass
  except KeyError:
    traceback.print_exc()
    print("\nError: Still unable to get channel info. Big Bruh Moment. Try deleting token.pickle. The info above might help if you want to report a bug.")
    input("\nPress Enter to Exit...")
    

  return channelID, channelTitle

################################# VIDEO ID LOOKUP ##############################################
# Using comment ID, get corresponding video ID from dictionary variable
def convert_comment_id_to_video_id(comment_id):
  video_id = vidIdDict[comment_id]
  return video_id

##################################### PRINT STATS ##########################################

# Prints Scanning Statistics, can be version that overwrites itself or one that finalizes and moves to next line
def print_count_stats(final):
  if final == True:
    print(f"Top Level Comments Scanned: {F.YELLOW}" + str(scannedCommentsCount) + f"{S.R} | Replies Scanned: {F.YELLOW}" + str(scannedRepliesCount) + f"{S.R} | Matches Found So Far: {F.LIGHTRED_EX}" +  str(len(spamCommentsID)) + f"{S.R}\n")
  else:
    print(f"Top Level Comments Scanned: {F.YELLOW}" + str(scannedCommentsCount) + f"{S.R} | Replies Scanned: {F.YELLOW}" + str(scannedRepliesCount) + f"{S.R} | Matches Found So Far: {F.LIGHTRED_EX}" +  str(len(spamCommentsID)) + f"{S.R}", end = "\r")
  
  return None

##################################### VALIDATE VIDEO ID #####################################
# Checks if video ID / video Link is correct length and in correct format - If so returns true and isolated video ID
def validate_video_id(video_url):
    youtube_video_link_regex = r"^\s*(?P<video_url>(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube\.com|youtu.be)(?:\/(?:[\w\-]+\?v=|embed\/|v\/)?))?(?P<video_id>[\w\-]{11})(?:(?(video_url)\S+|$))?\s*$"
    match = re.match(youtube_video_link_regex, video_url)
    if match == None:
        print(f"\n{B.RED}{F.BLACK}Invalid Video link or ID!{S.R} Video IDs are 11 characters long.")
        return False, None
    return True, match.group('video_id')

##################################### VALIDATE CHANNEL ID ##################################
# Checks if channel ID / Channel Link is correct length and in correct format - If so returns true and isolated channel ID
def validate_channel_id(inputted_channel):
  isolatedChannelID = "Invalid" # Default value

  # Get id from channel link
  if "/channel/" in inputted_channel:
    startIndex = inputted_channel.rindex("/") + 1
    endIndex = len(inputted_channel)
    
    if "?" in inputted_channel:
      endIndex = inputted_channel.rindex("?")

    if startIndex < endIndex and endIndex <= len(inputted_channel):
      isolatedChannelID = inputted_channel[startIndex:endIndex]

  elif "/c/" in inputted_channel:
    startIndex = inputted_channel.rindex("/c/") + 3 #Start index at at character after /c/
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
  elif ("youtube.com" in inputted_channel) and ("/c/" and "/channel/" not in inputted_channel):
    startIndex = inputted_channel.rindex("/") + 1
    endIndex = len(inputted_channel)

    if startIndex < endIndex and endIndex <= len(inputted_channel):
      customURL = inputted_channel[startIndex:endIndex]
      response = youtube.search().list(part="snippet",q=customURL, maxResults=1).execute()
      if response.get("items"):
          isolatedChannelID = response.get("items")[0]["snippet"]["channelId"] # Get channel ID from custom channel URL username

  else:
    isolatedChannelID = inputted_channel

  if len(isolatedChannelID) == 24 and isolatedChannelID[0:2] == "UC":
    return True, isolatedChannelID
  else:
    print(f"\n{B.RED}{F.BLACK}Invalid Channel link or ID!{S.R} Channel IDs are 24 characters long and begin with 'UC'.")
    return False, None
  
############################### User Choice #################################
# User inputs Y/N for choice, returns True or False
# Takes in message to display

def choice(message=""):
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
    valid, IDList[i] = validate_channel_id(inputList[i])
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
    file.write(r"{\colortbl;\red0\green0\blue0;\red255\green0\blue0;\red0\green255\blue0;\red0\green0\blue255;\red226\green129\blue0;\red102\green0\blue214;}"+"\n\n")
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
    punctuationChars = ("!?\".,;:'-/()")
    numbersLettersChars = ("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    keyboardSpecialChars = ("!@#$%^&*()_+-=[]\{\}|;':,./<>?`~")

    listedInput = list(stringInput)
    for i in range(len(listedInput)):
        listedInput[i] =  listedInput[i].strip()
        if stripLettersNumbers == True:
            listedInput[i] = listedInput[i].strip(numbersLettersChars)
        if stripKeyboardSpecialChars == True:
            listedInput[i] = listedInput[i].strip(keyboardSpecialChars)
        if stripPunctuation == True:
            listedInput[i] = listedInput[i].strip(punctuationChars)
        listedInput[i] = listedInput[i].strip('\ufe0f') # Strips invisible varation selector for emojis
    listedInput = list(filter(None, listedInput))
    
    
    return listedInput

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
def safety_check_username_against_filter(currentUserName, scanMode, filterCharsSet=None, filterStringList=None, regexPattern=None):
  currentUsernameChars = make_char_set(currentUserName)
  deletionEnabledLocal = "False"
  proceed = False

  if filterCharsSet:
    if any(x in filterCharsSet for x in currentUsernameChars):
      print(f"\n{B.LIGHTRED_EX}{F.BLACK}WARNING!{S.R} Character(s) you entered are within {F.LIGHTRED_EX}your own username{S.R}, ' " + currentUserName + " '! : " + str(filterCharsSet & currentUsernameChars))
      print("    (Some symbols above may not show in windows console, copy+paste them into a word processor to see the symbols)")
      if scanMode == 1:
        print("Are you SURE you want to search your own comments? (You WILL still get a confirmation before deleting)")
        if choice("Choose") == True:
          deletionEnabledLocal = "HalfTrue"
          proceed=True
      elif scanMode == 2:
        print(f"For safety purposes, this program's delete functionality is {F.LIGHTGREEN_EX}disabled{S.R} when scanning for yourself across your entire channel.")
        print(f"Choose {F.LIGHTRED_EX}'N'{S.R} to choose different characters. Choose {F.GREEN}'Y'{S.R} to continue  (But you will get an error when trying to delete!)\n")
        if choice("Continue?") == True:
          proceed = True
    else:
      proceed = True
      deletionEnabledLocal = "HalfTrue"
  
  elif filterStringList:
    #if filterString in currentUserName:
    if check_list_against_string(listInput=filterStringList, stringInput=currentUserName, caseSensitive=False):
      print(f"\n{B.LIGHTRED_EX}{F.BLACK}WARNING!{S.R} A string you entered is within {F.LIGHTRED_EX}your own username{S.R}!")
      if scanMode == 1:
        print("Are you SURE you want to search your own comments? (You WILL still get a confirmation before deleting)")
        if choice("Choose") == True:
          deletionEnabledLocal = "HalfTrue"
          proceed=True
      elif scanMode == 2:
        print(f"For safety purposes, this program's delete functionality is {F.LIGHTGREEN_EX}disabled{S.R} when scanning for yourself across your entire channel.")
        print(f"Choose {F.LIGHTRED_EX}'N'{S.R} to choose different characters. Choose {F.GREEN}'Y'{S.R} to continue  (But you will get an error when trying to delete!)\n")
        if choice("Continue?") == True:
          proceed = True
    else:
      proceed = True
      deletionEnabledLocal = "HalfTrue"

  elif regexPattern:
    if re.search(regexPattern, currentUserName):
      print(f"{B.RED}{F.WHITE}!! WARNING !!{S.R} This search mode / pattern would detect {F.LIGHTRED_EX}your own username{S.R}!")
      if scanMode == 1:
        if choice("Are you REALLY sure you want to continue?") == True:
          deletionEnabledLocal = "HalfTrue"
          proceed = True
      elif scanMode == 2:
        print(f"For safety purposes, this program's delete functionality is {F.GREEN}disabled{S.R} when scanning for yourself across your entire channel.")
        print("Choose 'N' to choose a different filter sensitivity. Choose 'Y' to continue  (But you will get an error when trying to delete!)\n")
        if choice("Continue?") == True:
          proceed = True
    else:
      proceed = True
      deletionEnabledLocal = "HalfTrue"

  

  return proceed, deletionEnabledLocal

##########################################################################################
################################## FILTERING MODES #######################################
##########################################################################################

# 1
# For if user chooses filter mode 1, to enter channel ID/Link
# Returns new deletionEnabled value, and inputtedSpammerChannelID
def prepare_filter_mode_ID(currentUser, deletionEnabledLocal, scanMode):
  currentUserID = currentUser[0]
  # Filter scanMode 1: User inputs spammer channel ID(s) or link(s)
  # User inputs channel ID of the spammer, while loop repeats until valid input
  processResult = (False, None) #Tuple, first element is status of validity of channel ID, second element is channel ID
  while processResult[0] == False:
    inputtedSpammerChannelID = input(f"Enter the {F.LIGHTRED_EX} Channel link(s) or ID(s){S.R} of the spammer (comma separated): ")
    processResult = process_spammer_ids(inputtedSpammerChannelID)
    if processResult[0] == True:
      inputtedSpammerChannelID = processResult[1] # After processing, if valid, inputtedSpammerChannelID is a list of channel IDs
  print("\n")

  # Check if spammer ID and user's channel ID are the same, and warn
  # If using channel-wide scanning mode, program will not run for safety purposes
  if any(currentUserID == i for i in inputtedSpammerChannelID) and scanMode == 2:
    print(f"{B.RED}{F.WHITE} WARNING: {S.R} - You are scanning for your own channel ID!")
    print("For safety purposes, this program's delete functionality is disabled when scanning for yourself across your entire channel.")
    print("If you want to delete your own comments for testing purposes, you can instead scan an individual video.")
    confirmation = choice("Continue?")
    if confirmation == False:
      input("Ok, Cancelled. Press Enter to Exit...")
      exit()
  elif any(currentUserID == i for i in inputtedSpammerChannelID) and scanMode == 1:
    print(f"{B.RED}{F.WHITE} WARNING: {S.R} You are scanning for your own channel ID! This would delete all of your comments on the video!")
    print("     (You WILL still be asked to confirm before actually deleting anything)")
    print("If you are testing and want to scan and/or delete your own comments, enter 'Y' to continue, otherwise enter 'N' to exit.")
    confirmation = choice("Continue?")
    if confirmation == True:  # After confirmation, deletion functionality is eligible to be enabled later
      deletionEnabledLocal = "HalfTrue"
    elif confirmation == False:
      input("Ok, Cancelled. Press Enter to Exit...")
      exit()
  else: 
    deletionEnabledLocal = "HalfTrue" # If no matching problem found, deletion functionality is eligible to be enabled later

  return deletionEnabledLocal, inputtedSpammerChannelID

# 2-1 - Username - Individual Characters
# For Filter mode 2, user inputs characters in username to filter
def prepare_filter_mode_username_chars(currentUser, deletionEnabledLocal, scanMode):
  # Create set of characters from users's channel name
  currentUserName = currentUser[1]
  
  print(f"\nNext, you will input {F.YELLOW}ONLY{S.R} any special characters / emojis you want to search for in usernames. Don't include commas or spaces!")
  print("          Note: Letters and numbers will not be included for safety purposes, even if you enter them.")
  print("          Example: 👋🔥✔️✨")
  input(f"\nPress {F.LIGHTGREEN_EX}Enter{S.R} to open the {F.LIGHTGREEN_EX}text entry window{S.R}...")
  print("-------------------------------------------")

  validEntry = False
  while validEntry == False:
    print(f"\nWaiting for input Window. Press {F.MAGENTA}'Execute'{S.R} after entering valid characters to continue...", end="\r")
    try:
      # Takes in user input of characters, returns 'set' of characters stripped of specified characters
      inputChars = take_input_gui(mode="chars", stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=False)
    except NameError: # Catch if user closes GUI window, exit program.
      print("                                                                                          ") # Clears the line because of \r on previous print
      print("\nSomething went wrong with the input, or you closed the window improperly.")
      input("Press Enter to exit...")
      exit()

    validEntry, deletionEnabledLocal = safety_check_username_against_filter(currentUserName, scanMode, filterCharsSet=inputChars)

    if validEntry == True:
      print(f"     Usernames will be scanned for {F.MAGENTA}ANY{S.R} of the characters you entered in the previous window.")
      if choice("Begin scanning? ") == True:
        validEntry = True
      else:
        validEntry = False

  return deletionEnabledLocal, inputChars


# 2-2 - Username - Entire String
# For Filter mode 2, user inputs a string or strings in username to filter
def prepare_filter_mode_username_string(currentUser, deletionEnabledLocal, scanMode):
  # Create set of characters from users's channel name
  currentUserName = currentUser[1]
  
  print(f"\nPaste or type in a list of any {F.YELLOW}comma separated strings{S.R} you want to search for in usernames. (Not case sensitive)")
  print("   >Note: If the text you paste includes special characters or emojis, they might not display correctly here, but it WILL still search them fine.")
  print("          Example Input: whatsapp, whatever multiple words, investment")

  validEntry = False
  while validEntry == False:
    inputString = input("Input Here: ")

    # Convert comma separated string into list with function, then check against current user's name
    filterStringList = string_to_list(inputString, lower=True)
    if len(filterStringList > 0):
      validEntry, deletionEnabledLocal = safety_check_username_against_filter(currentUserName.lower(), scanMode, filterStringList=filterStringList)

    if validEntry == True:
      print(f"     Usernames will be scanned for {F.MAGENTA}ANY{S.R} of the following strings:")
      print(filterStringList)
      if choice("Begin scanning? ") == True:
        validEntry = True
      else:
        validEntry = False

  return deletionEnabledLocal, filterStringList

# 2-3 Username - Regex
def prepare_filter_mode_username_regex (currentUser, deletionEnabledLocal, scanMode):
  currentUserName = currentUser[1]
  print(f"Enter any {F.YELLOW}regex expression{S.R} to search within usernames.")
  print(r"          Example Input:  [^\x00-\xFF]")
  validExpression = False

  while validExpression == False:
    inputtedExpression = input("Input Expression Here:  ")
    validationResults = validate_regex(inputtedExpression) # Returns tuple of valid, and processed expression
    validExpression = validationResults[0]

    if validExpression == True:
      processedExpression = validationResults[1]
      print(f"     The expression appears to be {F.GREEN}valid{S.R}!")
      validExpression, deletionEnabledLocal = safety_check_username_against_filter(currentUserName, scanMode, regexPattern=processedExpression)

      if validExpression == True and choice("Begin scanning? ") == True:
       return deletionEnabledLocal, processedExpression

    else: print(f"     {F.RED}Error{S.R}: The expression appears to be {F.RED}invalid{S.R}!")


# 3-1: Comment Text - Individual Characters
# For Filter mode 3, user inputs characters in comment text to filter
def prepare_filter_mode_comment_text_chars(currentUser, deletionEnabledLocal, scanMode):
  print(f"\nNext, you will input {F.YELLOW}ONLY{S.R} any special characters / emojis you want to search for in all comments. Do not include commas or spaces!")
  print("          Note: Letters, numbers, and punctuation will not be included for safety purposes, even if you enter them.")
  print("          Example: 👋🔥✔️✨")
  input(f"\nPress {F.LIGHTGREEN_EX}Enter{S.R} to open the {F.LIGHTGREEN_EX}text entry window{S.R}...")
  print("-------------------------------------------")

  validEntry = False
  while validEntry == False:
    print(f"\nWaiting for input Window. Press {F.MAGENTA}'Execute'{S.R} after entering valid characters to continue...", end="\r")

    try:
      inputChars = take_input_gui(mode="chars", stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=True)
    except NameError: # Catch if user closes GUI window, exit program.
      print("                                                                                          ") # Clears the line
      print("\nSomething went wrong with the input, or you closed the window improperly.")
      input("Press Enter to exit...")
      exit()

    print(f"     Comment text will be scanned for {F.MAGENTA}ANY{S.R} of the characters shown in the previous window.")
    if choice("Begin scanning? ") == True:
      validEntry = True
      deletionEnabledLocal = "HalfTrue"
      inputtedCommentTextFilter = inputChars

  return deletionEnabledLocal, inputtedCommentTextFilter


# 3-2 - Comment Text - Entire String
# For Filter mode 2, user inputs a string or strings in comment text to filter
def prepare_filter_mode_comment_text_string(currentUser, deletionEnabledLocal, scanMode):
  print(f"\nPaste or type in a list of any {F.YELLOW}comma separated strings{S.R} you want to search for in comments. (Not case sensitive)")
  print("   >Note: If the text you paste includes special characters or emojis, they might not display correctly here, but it WILL still search them fine.")
  print("          Example Input: whatsapp, whatever multiple words, investment")

  validEntry = False
  while validEntry == False:
    inputString = input("Input Here: ")

    # Convert comma separated string into list with function
    filterStringList = string_to_list(inputString, lower=True)
    if len(filterStringList) > 0:
      validEntry = True

    if validEntry == True:
      print(f"     Comment Text will be scanned for {F.MAGENTA}ANY{S.R} of the following strings:")
      print(filterStringList)
      if choice("Begin scanning? ") == True:
        validEntry = True
        deletionEnabledLocal = "HalfTrue"
      else:
        validEntry = False

  return deletionEnabledLocal, filterStringList

# 3-3 Comment Text - Regex
def prepare_filter_mode_comment_text_regex (currentUser, deletionEnabledLocal, scanMode):
  print(f"Enter any {F.YELLOW}regex expression{S.R} to search within comment text.")
  print(r"          Example Input:  [^\x00-\xFF]")
  validExpression = False

  while validExpression == False:
    inputtedExpression = input("Input Expression Here:  ")
    validationResults = validate_regex(inputtedExpression) # Returns tuple of valid, and processed expression
    validExpression = validationResults[0]

    if validExpression == True:
      print(f"     The expression appears to be {F.GREEN}valid{S.R}!")
      if choice("Begin scanning? ") == True:
        deletionEnabledLocal = "HalfTrue"
        processedExpression = validationResults[1]
    else:
      print(f"     {F.RED}Error{S.R}: The expression appears to be {F.RED}invalid{S.R}!")

  return deletionEnabledLocal, processedExpression

# 4
# For Filter mode 4, user inputs nothing, program scans for non-ascii
def prepare_filter_mode_non_ascii(currentUser, deletionEnabledLocal, scanMode):
  print("\n--------------------------------------------------------------------------------------------------------------")
  print("~~~ This mode automatically searches for usernames that contain special characters (aka not letters/numbers) ~~~\n")
  print("Choose the sensitivity level of the filter. You will be shown examples after you choose.")
  print(f"   1. Allow {F.LIGHTMAGENTA_EX}Standard + Extended ASCII{S.R}:    Filter rare unicode & Emojis only")
  print(f"   2. Allow {F.LIGHTMAGENTA_EX}Standard ASCII only{S.R}:  Also filter semi-common foreign characters")
  print(f"   3. {F.LIGHTRED_EX}NUKE Mode (┘°□°)┘≈ ┴──┴ :    Allow ONLY numbers, letters, and spaces{S.R}")
  print("")
  # Get user input for mode selection, 
  confirmation = False
  while confirmation == False:
    deletionEnabledLocal = "False"
    selection = input("Choose Mode: ")
    try: selection = int(selection) # If not number entered, will get caught later as invalid
    except: pass

    if selection == 1:
      print(f"Searches for {F.YELLOW}usernames with emojis, unicode symbols, and rare foreign characters{S.R} such as: ✔️ ☝️ 🡆 ▲ π Ɲ Œ")
      if choice("Choose this mode?") == True:
        regexPattern = r"[^\x00-\xFF]"
        confirmation = True
    elif selection == 2:
      print(f"Searches for {F.YELLOW}usernames with anything EXCEPT{S.R} the following: {F.YELLOW}Letters, numbers, punctuation, and common special characters{S.R} you can type with your keyboard like: % * & () + ")
      if choice("Choose this mode?") == True:
        regexPattern = r"[^\x00-\x7F]"
        confirmation = True
    elif selection == 3:
      print(f"Searches for {F.YELLOW}usernames with anything EXCEPT letters, numbers, and spaces{S.R} - {B.RED}{F.WHITE} EXTREMELY LIKELY to cause collateral damage!{S.R} Recommended to just use to manually gather list of spammer IDs, then use a different mode to delete.")
      if choice("Choose this mode?") == True:
        regexPattern = r"[^a-zA-Z0-9 ]"
        confirmation = True
    else:
      print("Invalid input. Please try again.")
    
    if confirmation == True:
      confirmation, deletionEnabledLocal = safety_check_username_against_filter(currentUser[1], scanMode=scanMode, regexPattern=regexPattern)

  if selection == 1:
    autoModeName = "Allow Standard + Extended ASCII"
  elif selection == 2:
    autoModeName = "Allow Standard ASCII only"
  elif selection == 3:
    autoModeName = "NUKE Mode (┘°□°)┘≈ ┴──┴ - Allow only letters, numbers, and spaces"

  if confirmation == True:
    return deletionEnabledLocal, regexPattern, autoModeName
  else:
    input("How did you get here? Something very strange went wrong. Press Enter to Exit...")
    exit()

# 5
# Auto filter for pre-made list of common spammer-used characters in usernames
def prepare_filter_mode_smart_chars(currentUser, deletionEnabledLocal, scanMode):
  currentUserName = currentUser[1]
  currentUsernameChars = make_char_set(currentUserName)

  print("\n--------------------------------------------------------------------------------------------------------------")
  print("~~~ This mode is pre-programmed to search usernames for special characters almost exclusively used by spammers ~~~\n")
  print(" > Specifically, unicode characters that look like numbers\n")
  input("Press Enter to continue...")

  spammerUsernameCharString = "０１２３４５６７８９０１２３４５６７８９߁①⑴⒈⓵❶➀➊🄂౽੨②⑵⒉⓶❷➁➋🄃౩③⑶⒊⓷❸➂➌🄄૩④⑷⒋⓸❹➃➍🄅⑤⑸⒌⓹❺➄➎➄➎🄆⑥⑹⒍⓺❻➅➏🄇⑦⑺⒎⓻❼➆➐𑄽🄈႘⑧⑻⒏⓼❽➇➑🄉⑨⑼⒐⓽❾➈➒🄊⓪⓿🄋🄌🄁🄀𝟎𝟘𝟢𝟬𝟏𝟙𝟭𝟣𝟶𝟐𝟚𝟮𝟤𝟷𝟑𝟛𝟯𝟥𝟸𝟒𝟜𝟰𝟦𝟹𝟓𝟝𝟱𝟧𝟺𝟔𝟞𝟲𝟨𝟻𝟕𝟟𝟳𝟩𝟼𝟖𝟠𝟴𝟪𝟽𝟗𝟡𝟵𝟫𝟾𝟿"
  filterCharsSet = make_char_set(spammerUsernameCharString, stripLettersNumbers=False, stripKeyboardSpecialChars=False, stripPunctuation=False)

  proceed, deletionEnabledLocal = safety_check_username_against_filter(currentUserName, filterCharsSet=filterCharsSet, scanMode=scanMode)

  if proceed == True:
    return deletionEnabledLocal, filterCharsSet
  else:
    input("Ok, cancelled. Press Enter to exit...")
    exit()

##########################################################################################
##########################################################################################
###################################### MAIN ##############################################
##########################################################################################
##########################################################################################

def main():
  # Run check on python version, must be 3.6 or higher because of f strings
  if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    print("Error: This program requires running python 3.6 or higher! You are running" + str(sys.version_info[0]) + "." + str(sys.version_info[1]))
    input("Press Enter to exit...")
    sys.exit()

  # Declare Global Variables
  global youtube  
  global spamCommentsID
  global vidIdDict
  global vidTitleDict
  global scannedRepliesCount
  global scannedCommentsCount
  global matchSamplesDict

  # Default values for global variables
  spamCommentsID = []
  vidIdDict = {}
  vidTitleDict = {}
  matchSamplesDict = {}
  scannedRepliesCount = 0
  scannedCommentsCount = 0
  regexPattern = ""
  
  # Declare Default Variables
  maxScanNumber = 999999999
  deletionEnabled = "False" # Disables deletion functionality, which is default until later - String is used instead of boolean to prevent flipped bits
  check_video_id = None
  nextPageToken = "start"
  logMode = False

  # Checks system platform to set correct console clear command
  # Clears console otherwise the windows terminal doesn't work with colorama for some reason  
  clear_command = "cls" if platform.system() == "Windows" else "clear"
  os.system(clear_command)

  # Initiates colorama and creates shorthand variables for resetting colors
  init(autoreset=True)
  S.R = S.RESET_ALL
  F.R = F.RESET
  B.R = B.RESET

  # Authenticate with the Google API - If token expired and invalid, deletes and re-authenticates
  try:
    youtube = get_authenticated_service() # Set easier name for API function
  except Exception as e:
    if "invalid_grant" in str(e):
      print("Invalid token - Requires Re-Authentication")
      os.remove(TOKEN_FILE_NAME)
      youtube = get_authenticated_service()
    else:
      traceback.print_exc() # Prints traceback
      print("----------------")
      print("\nError: " + str(e))
      print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      input("\nSomething went wrong during authentication. Try deleting token.pickle file. Press Enter to exit...")
      exit()
  
  # Intro message
  print(f"{F.YELLOW}\n============ YOUTUBE SPAMMER PURGE v" + version + f" ============{S.R}")
  print("== https://github.com/ThioJoe/YouTube-Spammer-Purge ==")
  print("======== Author: ThioJoe - YouTube.com/ThioJoe ======= \n")

  print("Purpose: Lets you scan and mass delete all comments from a specific user at once \n")
  print("NOTE: It's probably better to scan a single video, because you can scan all those comments,")
  print("      but scanning your entire channel must be limited and might miss older spam comments.")
  print("You WILL be shown the comments to confirm before they are deleted.")

  # While loop until user confirms they are logged into the correct account
  confirmedCorrectLogin = False
  while confirmedCorrectLogin == False:
    # Get channel ID and title of current user, confirm with user
    currentUser = get_current_user() # Returns [channelID, channelTitle]
    print("\n    >  Currently logged in user: " + f"{F.LIGHTGREEN_EX}" + str(currentUser[1]) + f"{S.R} (Channel ID: {F.LIGHTGREEN_EX}" + str(currentUser[0]) + f"{S.R} )")
    if choice("       Continue as this user?") == True:
      check_channel_id = currentUser[0]
      confirmedCorrectLogin = True
    else:
      os.remove(TOKEN_FILE_NAME)
      youtube = get_authenticated_service()
  
  # User selects scanning mode,  while Loop to get scanning mode, so if invalid input, it will keep asking until valid input
  print("\n-----------------------------------------------------------------")
  print(f"~~ Do you want to scan a single video, or your entire channel? ~~")
  print(f"      1. Scan a {F.LIGHTBLUE_EX}Single Video{S.R} (Recommended)")
  print(f"      2. Scan your {F.LIGHTMAGENTA_EX}Entire Channel{S.R}\n")

  # Make sure input is valid, if not ask again
  validMode = False
  while validMode == False:
    scanMode = input("Choice (1 or 2): ")
    try: scanMode = int(scanMode) # If not number entered, will get caught later as invalid
    except: pass

    if scanMode == 1 or scanMode == 2:
      validMode = True
    else:
      print("\nInvalid choice! - Enter either 1 or 2. ")

  # If chooses to scan single video - Validate Video ID, get title, and confirm with user - otherwise exits
  if scanMode == 1:  
    #While loop to get video ID and if invalid ask again
    validVideoID = (False, None) # Tuple, first element is status of validity of video ID, second element is video ID
    confirm = False
    while validVideoID[0] == False or confirm == False:
      check_video_id = input(F"Enter {F.YELLOW}Video Link{S.R} or {F.YELLOW}Video ID{S.R} to scan: ")
      validVideoID = validate_video_id(check_video_id) # Sends link or video ID for isolation and validation
      
      if validVideoID[0] == True:  #validVideoID now contains True/False and video ID
        check_video_id = str(validVideoID[1])
        title = get_video_title(check_video_id)
        print("\nChosen Video:  " + title)
        confirm = choice("Is this correct?")
        if currentUser[0] != get_channel_id(check_video_id) and confirm == True:
          print(f"\n   >>> {B.RED}{F.WHITE} WARNING {S.R} It is not possible to delete comments on someone elses video! Who do you think you are!? <<<")
          input("\n   Press Enter to continue for testing purposes...  (But you will get an error when trying to delete!)\n")

  # If chooses to scan entire channel - Validate Channel ID
  elif scanMode == 2:
    # While loop to get max scan number, not an integer, asks again
    validInteger = False
    while validInteger == False:
      try:
        maxScanNumber = int(input(f"Enter the maximum {F.YELLOW}number of comments{S.R} to scan: "))
        if maxScanNumber > 0:
          validInteger = True # If it gets here, it's an integer, otherwise goes to exception
        else:
          print("\nInvalid Input! Number must be greater than zero.")
      except:
        print("\nInvalid Input! - Must be a whole number.")

 
  # User inputs filtering mode
  print("\n-------------------------------------------------------")
  print(f"~~~~~~~ Choose how to identify spammers ~~~~~~~")
  print(f" 1. Enter Spammer's {F.LIGHTRED_EX}channel ID(s) or link(s){S.R}")
  print(f" 2. Scan {F.LIGHTGREEN_EX}usernames{S.R} for criteria you choose")
  print(f" 3. Scan {F.CYAN}comment text{S.R} for criteria you choose")
  print(f" 4. Auto Mode: Scan usernames for {F.LIGHTMAGENTA_EX}ANY non-ASCII special characters{S.R} (May cause collateral damage!)")
  print(f" 5. Auto Smart-Mode: Scan usernames and comments for {F.YELLOW}characters often used by scammers{S.R}")
  
  # Make sure input is valid, if not ask again
  validFilterMode = False
  validFilterSubMode = False
  filterSubMode = None

  while validFilterMode == False:
    filterChoice = input("\nChoice (1-5): ")
    if filterChoice == "1" or filterChoice == "2" or filterChoice == "3" or filterChoice == "4" or filterChoice == "5":
      validFilterMode = True

      # Set string variable names for filtering modes
      if filterChoice == "1":
        filterMode = "ID"
      elif filterChoice == "2":
        filterMode = "Username"
      elif filterChoice == "3":
        filterMode = "Text"
      elif filterChoice == "4":
        filterMode = "AutoASCII"
      elif filterChoice == "5":
        filterMode = "AutoSmart"
    else:
      print("\nInvalid choice! - Enter either 1, 2, 3, 4, or 5. ")

    ## Get filter sub-mode to decide if searching characters or string
    if filterMode == "Username" or filterMode == "Text":
      print("\n--------------------------------------------------------------")
      if filterMode == "Username":
        print("~~~ What do you want to scan usernames for specifically? ~~~")
      elif filterMode == "Text":
        print("~~~ What do you want to scan comment text for specifically? ~~~")
      print(f" 1. An {F.CYAN}individual special character{S.R}, or any of a set of characters")
      print(f" 2. An {F.LIGHTMAGENTA_EX}entire string{S.R}, or any of a set of strings")
      print(f" 3. Advanced: A custom {F.YELLOW}Regex pattern{S.R} you'll enter")

      while validFilterSubMode == False:
        filterSubMode = input("\nChoice (1, 2, or 3): ")
        if filterSubMode == "1" or filterSubMode == "2" or filterSubMode == "3":
          if filterSubMode == "1":
            filterSubMode = "chars"
            validFilterSubMode = True
          elif filterSubMode == "2":
            filterSubMode = "string"
            validFilterSubMode = True
          elif filterSubMode == "3":
            filterSubMode = "regex"
            validFilterSubMode = True
        else:
          print("\nInvalid choice! - Enter 1, 2 or 3")

  ### Prepare Filtering Modes ###
  # Default values for filter criteria
  inputtedSpammerChannelID = None
  inputtedUsernameFilter = None
  inputtedCommentTextFilter = None

  if filterMode == "ID":
    filterSettings = prepare_filter_mode_ID(currentUser, deletionEnabled, scanMode)
    inputtedSpammerChannelID = filterSettings[1]

  elif filterMode == "Username":
    if filterSubMode == "chars":
      filterSettings = prepare_filter_mode_username_chars(currentUser, deletionEnabled, scanMode)
      inputtedUsernameFilter = filterSettings[1]
    elif filterSubMode == "string":
      filterSettings = prepare_filter_mode_username_string(currentUser, deletionEnabled, scanMode)
      inputtedUsernameFilter = filterSettings[1]
    elif filterSubMode == "regex":
      filterSettings = prepare_filter_mode_username_regex(currentUser, deletionEnabled, scanMode)
      regexPattern = filterSettings[1]

  elif filterMode == "Text":
    if filterSubMode == "chars":
      filterSettings = prepare_filter_mode_comment_text_chars(currentUser, deletionEnabled, scanMode)
      inputtedCommentTextFilter = filterSettings[1]
    elif filterSubMode == "string":
      filterSettings = prepare_filter_mode_comment_text_string(currentUser, deletionEnabled, scanMode)
      inputtedCommentTextFilter = filterSettings[1]
    elif filterSubMode == "regex":
      filterSettings = prepare_filter_mode_comment_text_regex(currentUser, deletionEnabled, scanMode)
      regexPattern = filterSettings[1]

  elif filterMode == "AutoASCII":
    filterSettings = prepare_filter_mode_non_ascii(currentUser, deletionEnabled, scanMode)
    regexPattern = filterSettings[1]

  elif filterMode == "AutoSmart":
    filterSettings = prepare_filter_mode_smart_chars(currentUser, deletionEnabled, scanMode)
    inputtedUsernameFilter = filterSettings[1]
    inputtedCommentTextFilter = filterSettings[1]

  deletionEnabled = filterSettings[0]

  ##################### START SCANNING #####################
  try:
    # Goes to get comments for first page
    print("Scanning... \n")
    nextPageToken = get_comments(youtube, filterMode, filterSubMode, check_video_id, check_channel_id, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, regexPattern=regexPattern)
    print_count_stats(final=False)  # Prints comment scan stats, updates on same line

    # After getting first page, if there are more pages, goes to get comments for next page
    while nextPageToken != "End" and scannedCommentsCount < maxScanNumber:
      nextPageToken = get_comments(youtube, filterMode, filterSubMode, check_video_id, check_channel_id, nextPageToken, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, regexPattern=regexPattern)
    print_count_stats(final=True)  # Prints comment scan stats, finalizes
  ##########################################################

    # Counts number of found spam comments and prints list
    spam_count = len(spamCommentsID)
    if spam_count == 0: # If no spam comments found, exits
      print(f"{B.RED}{F.BLACK}No matched comments or users found!{S.R}\n")
      print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      input("\nPress Enter to exit...")
      exit()
    print(f"Number of Matched Comments Found: {B.RED}{F.WHITE} " + str(len(spamCommentsID)) + f" {S.R}")

    # Asks user if they want to save list of spam comments to a file
    if choice(f"Spam comments ready to display. Also {F.LIGHTGREEN_EX}save the list to a text file?{S.R}") == True:
      logMode = True
      global logFileName
      logFileName = "Spam_Log_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S" + ".rtf")
      print(f"Log file will be called {F.YELLOW}" + logFileName + f"{S.R}\n")
      input(f"Press {F.YELLOW}Enter{S.R} to display comments...")

      # Write heading info to log file
      write_rtf(logFileName, firstWrite=True)
      write_rtf(logFileName, "\\par----------- YouTube Spammer Purge Log File -----------\\line\\line " + "\n\n")
      if filterMode == "ID":
        write_rtf(logFileName, "Channel IDs of spammer searched: " + str(inputtedSpammerChannelID) + "\\line\\line " + "\n\n")
      elif filterMode == "Username":
        write_rtf(logFileName, "Characters searched in Usernames: " + make_rtf_compatible(str(inputtedUsernameFilter)) + "\\line\\line " + "\n\n")
      elif filterMode == "Text":
       write_rtf(logFileName, "Characters searched in Comment Text: " + make_rtf_compatible(str(inputtedCommentTextFilter)) + "\\line\\line " + "\n\n")
      elif filterMode == "AutoASCII":
        write_rtf(logFileName, "Automatic Search Mode: " + make_rtf_compatible(str(filterSettings[2])) + "\\line\\line " + "\n\n")
      elif filterMode == "AutoSmart":
        write_rtf(logFileName, "Automatic Search Mode: Smart Mode \\line\\line " + "\n\n")
      write_rtf(logFileName, "Number of Matched Comments Found: " + str(len(spamCommentsID)) + "\\line\\line " + "\n\n")
      write_rtf(logFileName, "IDs of Matched Comments: " + "\n" + str(spamCommentsID) + "\\line\\line\\line " + "\n\n\n")
      
    else:
      print("Ok, continuing... \n")

    # Prints list of spam comments
    print("\n\nAll Matched Comments: \n")
    reorderedSpamCommentsID = print_comments(check_video_id, spamCommentsID, logMode)
      
    
    # Get confirmation to delete spam comments
    confirmDelete = None
    print("\n")
    print(f"{F.WHITE}{B.RED} NOTE: {S.R} Check that all comments listed above are indeed spam.")

    if deletionEnabled == "HalfTrue": # Check if deletion functionality is eligible to be enabled
      confirmDelete = input(f"Do you want to {F.RED}delete ALL of the above comments{S.R}? Type ' {F.YELLOW}YES{S.R} ' exactly, in all caps to be sure! \n") 
      if confirmDelete != "YES":  # Deletion functionality enabled via confirmation, or not
        input(f"\nDeletion {F.YELLOW}CANCELLED{S.R}. Press Enter to exit...")
        exit()
      elif confirmDelete == "YES":
        deletionEnabled = "True"
    elif deletionEnabled == "False" and inputtedSpammerChannelID == currentUser[0] and scanMode == 2:
      print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      input(f"\n{F.LIGHTGREEN_EX}Deletion functionality disabled for this scanning mode because you scanned your own channel.{S.R} Press Enter to exit...")
      exit()
    else:
      print("\nThe deletion functionality was not enabled. Cannot delete comments.")
      print("Possible Causes: You're trying to scan someone elses video, or your search criteria matched your own channel in channel-wide scan mode.")
      print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      input("Press Enter to exit...")
      exit()
      

    if confirmDelete == "YES" and deletionEnabled == "True":  # Only proceed if deletion functionality is enabled, and user has confirmed deletion
      # Ask if they want to also ban spammer
      banChoice = choice(f"Also {F.YELLOW}ban{S.R} the spammer(s) ?")
      if logMode == True:
        write_rtf(logFileName, "\n\n"+ "\\line\\line Spammers Banned: " + str(banChoice)) # Write whether or not spammer is banned to log file
      print("\n")
      delete_found_comments(reorderedSpamCommentsID,banChoice) # Deletes spam comments
      check_deleted_comments(vidIdDict) #Verifies if comments were deleted
      input(f"\nDeletion {F.LIGHTGREEN_EX}Complete{S.R}. Press Enter to Exit...")
    else:
      input(f"\nDeletion {F.LIGHTRED_EX}Cancelled{S.R}. Press Enter to exit...")
      exit()

  # Catches exception errors and prints error info
  # If possible transient error, tells user to try again
  except HttpError as e:
    traceback.print_exc()
    print("------------------------------------------------")
    print("Error Message: ")
    print(e)
    if e.status_code: # If error code is available, print it
      print("\nError Info:")
      print("    Code: "+ str(e.status_code))
      if e.error_details[0]["reason"]: # If error reason is available, print it
        reason = str(e.error_details[0]["reason"])
        print("    Reason: " + reason)
        if reason == "processingFailure":
          print(f"\n !! {F.RED}Processing Error{S.R} - Sometimes this error fixes itself. Try just running the program again. !!")
          print("This issue is often on YouTube's side, so if it keeps happening try again later.")
          print("(This also occurs if you try deleting comments on someone elses video, which is not possible.)")
      input("\n Press Enter to Exit...")
    else:
      print(f"{F.RED}Unknown Error{S.R} occurred. If this keeps happening, consider posting a bug report on the GitHub issues page, and include the above error info.")
      input("\n Press Enter to Exit...")
  else:
    print("\nFinished Executing.")

# Runs the program
if __name__ == "__main__":
  main()


