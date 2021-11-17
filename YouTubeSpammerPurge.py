#!/usr/bin/env python3
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
version = "1.5.0-Testing"
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

import os
from datetime import datetime
import traceback
import re

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

# First prepared comments into groups of 50 to be submitted to API simultaneously
# Then uses print_prepared_comments() to print / log the comments
def print_comments(check_video_id_localprint, comments, logMode):
  j = 0 # Index when going through comments all comment groups
  if len(comments) > 50:
    remainder = len(comments) % 50
    numDivisions = int((len(comments)-remainder)/50)
    for i in range(numDivisions):
      j = print_prepared_comments(check_video_id_localprint,comments[i*50:i*50+50], j, logMode)
    if remainder > 0:
      j = print_prepared_comments(check_video_id_localprint,comments[numDivisions*50:len(comments)],j, logMode)
  else:
    j = print_prepared_comments(check_video_id_localprint,comments, j, logMode)

# Uses comments.list YouTube API Request to get text and author of specific set of comments, based on comment ID
def print_prepared_comments(check_video_id_localprep, comments, j, logMode):
  results = youtube.comments().list(
    part="snippet",
    id=comments,  # The API request can take an entire comma separated list of comment IDs (in "id" field) to return info about
    maxResults=100, # 100 is the max per page, but multiple pages will be scanned
    fields="items/snippet/authorDisplayName,items/snippet/textDisplay",
    textFormat="plainText"
  ).execute()

  # Prints author and comment text for each comment
  i = 0 # Index when going through comments
  for item in results["items"]:
    text = item["snippet"]["textDisplay"]
    author = item["snippet"]["authorDisplayName"]

    # Retrieve video ID from object using comment ID
    videoID = convert_comment_id_to_video_id(comments[i])

    # Prints comment info to console
    print(str(j+1) + ". " + author + ":  " + text)

    if check_video_id_localprep is None:  # Only print video title if searching entire channel
      title = get_video_title(videoID) # Get Video Title
      print("     > Video: " + title)
    print("     > Direct Link: " + "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comments[i] + "\n")

    # If logging enabled, also prints to log file
    if logMode == True:
      logFile.write(str(j+1) + ". " + author + ":  " + text + "\n")
      if check_video_id_localprep is None:  # Only print video title if searching entire channel
        title = get_video_title(videoID) # Get Video Title
        logFile.write("     > Video: " + title + "\n")
      logFile.write("     > Direct Link: " + "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comments[i] + "\n\n")

    i += 1
    j +=1

  return j


##########################################################################################
############################## GET COMMENT THREADS #######################################
##########################################################################################

# Call the API's commentThreads.list method to list the existing comments.
def get_comments(youtube, filterMode, check_video_id=None, check_channel_id=None, nextPageToken=None, inputtedSpammerChannelID=None, inputtedUsernameFilter=None, inputtedCommentTextFilter=None, regexPattern=None):  # None are set as default if no parameters passed into function
  global scannedCommentsCount
  # Initialize some variables
  authorChannelName = None
  commentText = None

  if filterMode == 1: # User entered spammer IDs -- Get Extra Info: None
    fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value"
  if filterMode == 2 or filterMode == 4: # Filter char by Username / Auto Regex non-ascii username -- Get Extra Info: Author Display Name
    fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/authorDisplayName"
  if filterMode == 3: # Filter char by Comment text -- Get Extra Info: Comment Text
    fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/textDisplay"


  # Gets all comment threads for a specific video
  if check_video_id is not None:
    results = youtube.commentThreads().list(
      part="snippet",
      videoId=check_video_id, 
      maxResults=100, # 100 is the max per page allowed by YouTube, but multiple pages will be scanned
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()
  
  # Get all comment threads across the whole channel
  elif check_video_id is None:
    results = youtube.commentThreads().list(
      part="snippet",
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
  # Also goes through each thread and execuites get_replies() to get reply content and matches
  for item in results["items"]:
    comment = item["snippet"]["topLevelComment"]
    videoID = comment["snippet"]["videoId"] # Only enable if NOT checking specific video
    parent_id = item["snippet"]["topLevelComment"]["id"]
    numReplies = item["snippet"]["totalReplyCount"]
    try: 
      authorChannelID = comment["snippet"]["authorChannelId"]["value"]
    except KeyError:
      authorChannelID = "[Deleted Channel]"

    # Need to be able to catch exceptions because sometimes the API will return a comment from non-existent / deleted channel
    # Need individual tries because not all are fetched for each mode
    if filterMode == 2 or filterMode == 4:
      try:
        authorChannelName = comment["snippet"]["authorDisplayName"]
      except KeyError:
        authorChannelName = "[Deleted Channel]"
    if filterMode == 3:
      try:
        commentText = comment["snippet"]["textDisplay"]
      except KeyError:
        commentText = "[Deleted/Missing Comment]"
    
    # Runs check against comment info for whichever filter data is relevant
    check_against_filter(filterMode, parent_id, videoID, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, authorChannelID, authorChannelName, commentText, regexPattern)
    scannedCommentsCount += 1  # Counts number of comments scanned, add to global count

    if numReplies > 0:
      get_replies(filterMode, parent_id, videoID, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, regexPattern)
    else:
      print_count_stats(final=False)  # Updates displayed stats if no replies
  
  return RetrievedNextPageToken


##########################################################################################
##################################### GET REPLIES ########################################
##########################################################################################

# Call the API's comments.list method to list the existing comment replies.
def get_replies(filterMode, parent_id, videoID, inputtedSpammerChannelID=None, inputtedUsernameFilter=None, inputtedCommentTextFilter=None, regexPattern=None):
  global scannedRepliesCount
  # Initialize some variables
  authorChannelName = None
  commentText = None
  
  if filterMode == 1: # User entered spammer IDs -- Get Extra Info: None
    fieldsToFetch = "items/snippet/authorChannelId/value,items/id"
  elif filterMode == 2 or filterMode == 4: # Filter by Username -- Get Extra Info: Author Display Name
    fieldsToFetch = "items/snippet/authorChannelId/value,items/id,items/snippet/authorDisplayName"
  elif filterMode == 3: # Filter by comment text -- Get Extra Info: Comment Text
    fieldsToFetch = "items/snippet/authorChannelId/value,items/id,items/snippet/textDisplay"

  results = youtube.comments().list(
    part="snippet",
    parentId=parent_id,
    maxResults=100, # 100 is the max per page, but multiple pages will be scanned
    fields=fieldsToFetch,
    textFormat="plainText"
  ).execute()
 
  # Iterates through items in results
  # Need to be able to catch exceptions because sometimes the API will return a comment from non-existent / deleted channel
  # Need individual tries because not all are fetched for each mode
  for item in results["items"]:  
    replyID = item["id"]
    try:
      authorChannelID = item["snippet"]["authorChannelId"]["value"]
    except KeyError:
      authorChannelID = "[Deleted Channel]"

    if filterMode == 2 or filterMode == 4: 
      try:
        authorChannelName = item["snippet"]["authorDisplayName"]
      except KeyError:
        authorChannelName = "[Deleted Channel]"  
    
    if filterMode == 3:
      try:
        commentText = item["snippet"]["textDisplay"]
      except KeyError:
        commentText = "[Deleted/Missing Comment]"

    # Runs check against comment info for whichever filter data is relevant
    check_against_filter(filterMode, replyID, videoID, inputtedSpammerChannelID, inputtedUsernameFilter, inputtedCommentTextFilter, authorChannelID, authorChannelName, commentText, regexPattern)

    # Update latest stats
    scannedRepliesCount += 1  # Count number of replies scanned, add to global count
    print_count_stats(final=False) # Prints out current count stats

  return True

############################## CHECK AGAINST FILTER ######################################
# The basic logic that actually checks each comment against filter criteria
def check_against_filter(filterMode, commentID, videoID, inputtedSpammerChannelID=None, inputtedUsernameFilter=None, inputtedCommentTextFilter=None, authorChannelID=None, authorChannelName=None, commentText=None, regexPattern=None):
  global vidIdDict
  global spamCommentsID
    # If the comment matches criteria based on mode, add to list of spam comment IDs
    # Also add key-value pair of comment ID and video ID to dictionary

  # Checks author of either parent comment or reply (both passed in as commentID) against channel ID inputted by user
  if filterMode == 1:
    if any(authorChannelID == x for x in inputtedSpammerChannelID):
      spamCommentsID += [commentID]
      vidIdDict[commentID] = videoID

  # Check if author channel name contains any characters entered by user
  elif filterMode == 2:
    authorChannelName = make_char_set(str(authorChannelName))
    if any(x in inputtedUsernameFilter for x in authorChannelName):
      spamCommentsID += [commentID]
      vidIdDict[commentID] = videoID

  # Check if comment text contains any characters entered by user
  elif filterMode == 3:
    commentText = make_char_set(str(commentText))
    if any(x in inputtedCommentTextFilter for x in commentText):
      spamCommentsID += [commentID]
      vidIdDict[commentID] = videoID

  # Check if author name contains non-ascii characters with Regex, sensitivity based on user selection
  elif filterMode == 4:
    if re.search(str(regexPattern), authorChannelName):
      spamCommentsID += [commentID]
      vidIdDict[commentID] = videoID

##########################################################################################
################################ DELETE COMMENTS #########################################
########################################################################################## 

# Takes in dictionary of comment IDs to delete, breaks them into 50-comment chunks, and deletes them in groups
def delete_found_comments(commentsDictionary,banChoice):

    # Deletes specified comment IDs
    def delete(commentIDs):
        youtube.comments().setModerationStatus(id=commentIDs, moderationStatus="rejected", banAuthor=banChoice).execute()

    commentsList = list(commentsDictionary.keys())  # Takes comment IDs out of dictionary and into list
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

# Takes in dictionary of comment IDs and video IDs, and checks if comments still exist individually
def check_deleted_comments(commentsDictionary):
    i = 0 # Count number of remaining comments
    j = 1 # Count number of checked
    total = len(commentsDictionary)
    for key, value in commentsDictionary.items():
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
            print("Possible Issue Deleting Comment: " + str(key) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(value) + "&lc=" + str(key))
            i += 1

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
# Get video title from video ID using YouTube API request
def get_video_title(video_id):
  results = youtube.videos().list(
    part="snippet",
    id=video_id,
    fields="items/snippet/title",
    maxResults=1
  ).execute()
  
  title = results["items"][0]["snippet"]["title"]

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
    print("Top Level Comments Scanned: " + str(scannedCommentsCount) + " | Replies Scanned: " + str(scannedRepliesCount) + " | Matches Found So Far: " +  str(len(spamCommentsID)) + "\n")
  else:
    print("Top Level Comments Scanned: " + str(scannedCommentsCount) + " | Replies Scanned: " + str(scannedRepliesCount) + " | Matches Found So Far: " +  str(len(spamCommentsID)), end = "\r")
  
  return None

##################################### VALIDATE VIDEO ID #####################################
# Checks if video ID is correct length, and if so, gets the title of the video
def validate_video_id(inputted_video):
  isolatedVideoID = "Invalid" # Default value
  # Get id from long video link
  if "/watch?" in inputted_video:
    startIndex = 0
    endIndex = 0
    
    if "?v=" in inputted_video:
      startIndex = inputted_video.index("?v=") + 3
    elif "&v=" in inputted_video:
      startIndex = inputted_video.index("&v=") + 3

    if "&" in inputted_video:
      endIndex = inputted_video.index("&")
    else:
      endIndex = len(inputted_video)
  
    if startIndex != 0 and endIndex != 0 and startIndex < endIndex and endIndex <= len(inputted_video):
      isolatedVideoID = inputted_video[startIndex:endIndex]

  # Get id from short video link
  elif "/youtu.be/" in inputted_video:
    startIndex = inputted_video.index(".be/") + 4
    endIndex = len(inputted_video)

    if "?" in inputted_video:
      endIndex = inputted_video.index("?")

    if endIndex != 0 and startIndex < endIndex and endIndex <= len(inputted_video):
      isolatedVideoID = inputted_video[startIndex:endIndex]

  else: 
    isolatedVideoID = inputted_video

  if len(isolatedVideoID) != 11:
    print("\nInvalid Video link or ID! Video IDs are 11 characters long.")
    return False, None

  else:
    return True, isolatedVideoID

##################################### VALIDATE CHANNEL ID ##################################
# Checks if channel ID is correct length and in correct format - if so returns True
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
    print("\nInvalid Channel link or ID! Channel IDs are 24 characters long and begin with 'UC'.")
    return False, None
  
############################### User Choice #################################
# User inputs Y/N for choice, returns True or False
# Takes in message to display

def choice(message=""):
  # While loop until valid input
  valid = False
  while valid == False:
    response = input("\n" + message + " (y/n): ")
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
      print("Invalid Channel ID or Link: " + str(inputList[i]) + "\n")
      return False, None
  
  return True, IDList
      
############################ Process Input Spammer IDs ###############################
# Opens log file to be able to be written
def open_log_file(name):
  global logFile
  logFile = open(name, "a", encoding="utf-8") # Opens log file in write mode


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
    inputtedSpammerChannelID = input("Enter the Channel link(s) or ID(s) of the spammer (comma separated): ")
    processResult = process_spammer_ids(inputtedSpammerChannelID)
    if processResult[0] == True:
      inputtedSpammerChannelID = processResult[1] # After processing, if valid, inputtedSpammerChannelID is a list of channel IDs
  print("\n")

  # Check if spammer ID and user's channel ID are the same, and warn
  # If using channel-wide scanning mode, program will not run for safety purposes
  if any(currentUserID == i for i in inputtedSpammerChannelID) and scanMode == 2:
    print("WARNING - You are scanning for your own channel ID!")
    print("For safety purposes, this program's delete functionality is disabled when scanning for yourself across your entire channel.")
    print("If you want to delete your own comments for testing purposes, you can instead scan an individual video.")
    confirmation = choice("Continue?")
    if confirmation == False:
      input("Ok, Cancelled. Press Enter to Exit...")
      exit()
  elif any(currentUserID == i for i in inputtedSpammerChannelID) and scanMode == 1:
    print("WARNING: You are scanning for your own channel ID! This would delete all of your comments on the video!")
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

# 2
# For Filter mode 2, user inputs characters in username to filter
def prepare_filter_mode_username(currentUser, deletionEnabledLocal, scanMode):
  # Create set of characters from users's channel name
  currentUserName = currentUser[1]
  channelChars = make_char_set(currentUserName) # Converts channel name to set of characters to compare with entered filter characters

  print("\nInput ONLY any special characters / emojis you want to search for in usernames. Do not include commas or spaces!")
  print("Note: Letters and numbers will not be included for safety purposes, even if you enter them.")
  print("Example: 👋🔥✔️✨")
  validEntry = False
  while validEntry == False:
    inputChars = input("Input the characters to search (no commas or spaces): ")
    inputChars = make_char_set(inputChars, stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=False)

    if any(x in inputChars for x in channelChars):
      print("WARNING! Character(s) you entered are within your own username, ' " + currentUserName + " '! : " + str(inputChars & channelChars))
      if scanMode == 1:
        print("Are you SURE you want to search your own comments? (You WILL still get a confirmation before deleting)")
        if choice("Choose") == True:
          deletionEnabledLocal = "HalfTrue"
          validEntry = True
      elif scanMode == 2:
        print("For safety purposes, this program's delete functionality is disabled when scanning for yourself across your entire channel.")
        print("Choose 'N' to choose different characters. Choose 'Y' to continue  (But you will get an error when trying to delete!)\n")
        if choice("Continue?") == True:
          validEntry = True
    else:
      print("Usernames will be scanned for ANY of these individual characters: " + str(inputChars))
      if choice("Begin scanning? ") == True:
        validEntry = True
        deletionEnabledLocal = "HalfTrue"
        inputtedCommentTextFilter = inputChars

  return deletionEnabledLocal, inputtedCommentTextFilter

# 3
# For Filter mode 3, user inputs characters in comment text to filter
def prepare_filter_mode_comment_text(currentUser, deletionEnabledLocal, scanMode):
  print("\nInput ONLY any special characters / emojis you want to search for in all comments. Do not include commas or spaces!")
  print("Note: Letters, numbers, and punctuation will not be included for safety purposes, even if you enter them.")
  print("Example: 👋🔥✔️✨")
  validEntry = False
  while validEntry == False:
    inputChars = input("Input the characters to search (no commas or spaces): ")
    inputChars = make_char_set(inputChars, stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=True)

    print("Comment text will be scanned for ANY of these individual characters: " + str(inputChars))
    if choice("Begin scanning? ") == True:
      validEntry = True
      deletionEnabledLocal = "HalfTrue"
      inputtedCommentTextFilter = inputChars

  return deletionEnabledLocal, inputtedCommentTextFilter


# 4
# For Filter mode 4, user inputs nothing, program scans for non-ascii
def prepare_filter_mode_non_ascii(currentUser, deletionEnabledLocal, scanMode):
  print("\n-------------------------------------------------------")
  print("~~~ This mode automatically searches for usernames that contain special characters (aka not letters/numbers) ~~~\n")
  print("Choose the sensitivity level of the filter. You will be shown examples after you choose.")
  print("   1. Allow Extended ASCII:       Filter rare unicode & Emojis only")
  print("   2. Allow Standard ASCII only:  Also filter semi-common foreign characters")
  print("   3. NUKE Mode (╯°□°)╯︵ ┻━┻:    Allow ONLY numbers, letters, and spaces")
  print("")
  # Get user input for mode selection, 
  confirmation = False
  while confirmation == False:
    selection = input("Choose Mode: ")
    try: selection = int(selection) # If not number entered, will get caught later as invalid
    except: pass

    if selection == 1:
      print("Filters/Deletes usernames with emojis, unicode symbols, and rare foreign characters such as: ✔️ ☝️ 🡆 ▲ π Ɲ Œ")
      if choice("Choose this mode?") == True:
        regexPattern = r"[^\x00-\xFF]"
        confirmation = True
    elif selection == 2:
      print("Filters/Deletes usernames with anything EXCEPT the following: Letters, numbers, punctuation, and special characters you can usually type with your keyboard like: % * & () + ")
      if choice("Choose this mode?") == True:
        regexPattern = r"[^\x00-\x7F]"
        confirmation = True
    elif selection == 3:
      print("Filters/Deletes usernames with anything EXCEPT letters, numbers, and spaces -- Likely to cause collateral damage!")
      if choice("Choose this mode?") == True:
        regexPattern = r"[^a-zA-Z0-9 ]"
        confirmation = True
    else:
      print("Invalid input. Please try again.")

    if re.search(regexPattern, currentUser[1]):
      confirmation = False
      print("!! WARNING !! This search mode would detect your own username!")
      if scanMode == 1:
        if choice("Are you REALLY sure you want to use this filter sensitivity?") == True:
          deletionEnabledLocal = "HalfTrue"
          confirmation = True
      elif scanMode == 2:
        print("For safety purposes, this program's delete functionality is disabled when scanning for yourself across your entire channel.")
        print("Choose 'N' to choose a different filter sensitivity. Choose 'Y' to continue  (But you will get an error when trying to delete!)\n")
        if choice("Continue?") == True:
          confirmation = True

  if selection == 1:
    autoModeName = "Allow Extended ASCII"
  elif selection == 2:
    autoModeName = "Allow Standard ASCII only"
  elif selection == 3:
    autoModeName = "NUKE Mode (╯°□°)╯︵ ┻━┻ - Allow only letters, numbers, and spaces"

  if confirmation == True:
    deletionEnabledLocal = "HalfTrue"
    return deletionEnabledLocal, regexPattern, autoModeName
  else:
    input("How did you get here? Something very strange went wrong. Press Enter to Exit...")
    exit()

##########################################################################################
##########################################################################################
###################################### MAIN ##############################################
##########################################################################################
##########################################################################################

def main():
  # Declare Global Variables
  global youtube  
  global spamCommentsID
  global vidIdDict
  global scannedRepliesCount
  global scannedCommentsCount

  # Default values for global variables
  spamCommentsID = []
  vidIdDict = {}
  scannedRepliesCount = 0
  scannedCommentsCount = 0
  regexPattern = ""
  
  # Declare Default Variables
  maxScanNumber = 999999999
  deletionEnabled = "False" # Disables deletion functionality, which is default until later - String is used instead of boolean to prevent flipped bits
  check_video_id = None
  nextPageToken = "start"
  logMode = False

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
  print("\n============ YOUTUBE SPAMMER PURGE v" + version + " ============")
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
    print("\n    >  Currently logged in user: " + str(currentUser[1]) + " (Channel ID: " + str(currentUser[0]) + " )")
    if choice("       Continue as this user?") == True:
      check_channel_id = currentUser[0]
      confirmedCorrectLogin = True
    else:
      os.remove(TOKEN_FILE_NAME)
      youtube = get_authenticated_service()
  
  # User selects scanning mode,  while Loop to get scanning mode, so if invalid input, it will keep asking until valid input
  print("\n-----------------------------------------------------------------")
  print("~~ Do you want to scan a single video, or your entire channel? ~~")
  print("      1. Scan Single Video")
  print("      2. Scan Entire Channel")

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
      check_video_id = input("Enter Video link or ID to scan: ")
      validVideoID = validate_video_id(check_video_id) # Sends link or video ID for isolation and validation
      
      if validVideoID[0] == True:  #validVideoID now contains True/False and video ID
        check_video_id = str(validVideoID[1])
        title = get_video_title(check_video_id)
        print("\nChosen Video:  " + title)
        confirm = choice("Is this correct?")
        if currentUser[0] != get_channel_id(check_video_id) and confirm == True:
          print("\n   >>> WARNING It is not possible to delete comments on someone elses video! Who do you think you are!? <<<")
          input("\n   Press Enter to continue for testing purposes...  (But you will get an error when trying to delete!)\n")

  # If chooses to scan entire channel - Validate Channel ID
  elif scanMode == 2:
    # While loop to get max scan number, not an integer, asks again
    validInteger = False
    while validInteger == False:
      try:
        maxScanNumber = int(input("Enter the maximum number of comments to scan: "))
        if maxScanNumber > 0:
          validInteger = True # If it gets here, it's an integer, otherwise goes to exception
        else:
          print("\nInvalid Input! Number must be greater than zero.")
      except:
        print("\nInvalid Input! - Must be a whole number.")
          
 
  # User inputs filtering mode
  print("\n-------------------------------------------------------")
  print("~~~~~~~ Choose how to identify spammers ~~~~~~~")
  print(" 1. Enter Spammer's channel ID(s) or link(s)")
  print(" 2. Scan usernames for certain individual characters you choose")
  print(" 3. Scan comment text for certain individual characters you choose") 
  print(" 4. Auto Mode: Scan usernames for ANY non-ASCII special characters (May cause collateral damage!)")
  
  # Make sure input is valid, if not ask again
  validFilterMode = False
  while validFilterMode == False:
    filterMode = input("\nChoice (1-4): ")
    try: filterMode = int(filterMode) # If not number entered, will get caught later as invalid
    except: pass

    if filterMode == 1 or filterMode == 2 or filterMode == 3 or filterMode == 4:
      validFilterMode = True
    else:
      print("\nInvalid choice! - Enter either 1, 2, 3 or 4. ")

  ### Prepare Filtering Modes ###
  # Default values for filter criteria
  inputtedSpammerChannelID = None
  inputtedUsernameFilter = None
  inputtedCommentTextFilter = None

  if filterMode == 1:
    filterSettings = prepare_filter_mode_ID(currentUser, deletionEnabled, scanMode)
    inputtedSpammerChannelID = filterSettings[1]
  elif filterMode == 2:
    filterSettings = prepare_filter_mode_username(currentUser, deletionEnabled, scanMode)
    inputtedUsernameFilter = filterSettings[1]
  elif filterMode == 3:
    filterSettings = prepare_filter_mode_comment_text(currentUser, deletionEnabled, scanMode)
    inputtedCommentTextFilter = filterSettings[1]
  elif filterMode == 4:
    filterSettings = prepare_filter_mode_non_ascii(currentUser, deletionEnabled, scanMode)
    regexPattern = filterSettings[1]
  deletionEnabled = filterSettings[0]

  ##################### START SCANNING #####################
  try:
    # Goes to get comments for first page
    print("Scanning... \n")
    nextPageToken = get_comments(youtube, filterMode, check_video_id, check_channel_id, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, regexPattern=regexPattern)
    print_count_stats(final=False)  # Prints comment scan stats, updates on same line

    # After getting first page, if there are more pages, goes to get comments for next page
    while nextPageToken != "End" and scannedCommentsCount < maxScanNumber:
      nextPageToken = get_comments(youtube, filterMode, check_video_id, check_channel_id, nextPageToken, inputtedSpammerChannelID=inputtedSpammerChannelID, inputtedUsernameFilter=inputtedUsernameFilter, inputtedCommentTextFilter=inputtedCommentTextFilter, regexPattern=regexPattern)
    print_count_stats(final=True)  # Prints comment scan stats, finalizes
  ##########################################################

    # Counts number of found spam comments and prints list
    spam_count = len(spamCommentsID)
    if spam_count == 0: # If no spam comments found, exits
      print("No spam comments found!\n")
      print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      input("\nPress Enter to exit...")
      exit()
    print("Number of Spammer Comments Found: " + str(len(spamCommentsID)))

    # Asks user if they want to save list of spam comments to a file
    if choice("Spam comments ready to display. Also save the list to a text file?") == True:
      logMode = True
      logFileName = "Spam_Log_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S" + ".txt")
      print("Log file will be called " + logFileName + "\n")
      input("Press Enter to display comments...")

      # Write heading info to log file
      open_log_file(logFileName)
      logFile.write("----------- YouTube Spammer Purge Log File ----------- \n\n")
      if filterMode == 1:
        logFile.write("Channel IDs of spammer searched: " + str(inputtedSpammerChannelID) + "\n\n")
      elif filterMode == 2:
        logFile.write("Characters searched in Usernames: " + str(inputtedUsernameFilter) + "\n\n")
      elif filterMode == 3:
        logFile.write("Characters searched in Comment Text: " + str(inputtedCommentTextFilter) + "\n\n")
      elif filterMode == 4:
        logFile.write("Automatic Search Mode: " + str(filterSettings[2]))
      logFile.write("Number of Spammer Comments Found: " + str(len(spamCommentsID)) + "\n\n")
      logFile.write("IDs of Spammer Comments: " + "\n" + str(spamCommentsID) + "\n\n\n")
      
    else:
      print("Ok, continuing... \n")

    # Prints list of spam comments
    print("\n\nComments by the selected user: \n")
    print_comments(check_video_id,spamCommentsID, logMode)
    if logMode == True: logFile.close()
      
    
    # Get confirmation to delete spam comments
    confirmDelete = None
    print("\n")
    print("Check that all comments listed above are indeed spam.")

    if deletionEnabled == "HalfTrue": # Check if deletion functionality is eligible to be enabled
      confirmDelete = input("Do you want to delete ALL of the above comments? Type 'YES' exactly, in all caps! \n") 
      if confirmDelete != "YES":  # Deletion functionality enabled via confirmation, or not
        input("\nDeletion CANCELLED. Press Enter to exit...")
        exit()
      elif confirmDelete == "YES":
        deletionEnabled = "True"
    elif deletionEnabled == "False" and inputtedSpammerChannelID == currentUser[0] and scanMode == 2:
      print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      input("\nDeletion functionality disabled for this scanning mode because you scanned your own channel. Press Enter to exit...")
      exit()
    else:
      print("\nThe deletion functionality was not enabled. Cannot delete comments.")
      print("Possible Causes: You're trying to scan someone elses video, or your search criteria matched your own channel in channel-wide scan mode.")
      print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
      input("Press Enter to exit...")
      exit()
      

    if confirmDelete == "YES" and deletionEnabled == "True":  # Only proceed if deletion functionality is enabled, and user has confirmed deletion
      # Ask if they want to also ban spammer
      banChoice = choice("Also ban the spammer(s) ?")
      if logMode == True:
        open_log_file(logFileName)
        logFile.write("\n\nSpammers Banned: " + str(banChoice)) # Write whether or not spammer is banned to log file
        logFile.close()
      print("\n")
      delete_found_comments(vidIdDict,banChoice) # Deletes spam comments
      check_deleted_comments(vidIdDict) #Verifies if comments were deleted
      input("\nDeletion Complete. Press Enter to Exit...")
    else:
      input("\nDeletion Cancelled. Press Enter to exit...")
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
          print("\n !! Processing Error - Sometimes this error fixes itself. Try just running the program again. !!")
          print("(This also occurs if you try deleting comments on someone elses video, which is not possible.)")
      input("\n Press Enter to Exit...")
    else:
      print("Unknown Error occurred. If this keeps happening, consider posting a bug report on the GitHub issues page, and include the above error info.")
      input("\n Press Enter to Exit...")
  else:
    print("\nFinished Executing.")

# Runs the program
if __name__ == "__main__":
  main()

