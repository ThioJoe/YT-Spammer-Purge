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
version = "1.4.1"
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
import os
import logging as log # Importing the logging dependence as log 
from datetime import datetime
import traceback

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
    log.critical(CLIENT_SECRETS_FILE  + " file not found!")
    print("\n ------------- ERROR: "+CLIENT_SECRETS_FILE+" file not found! ------------- ")
    print(" Make sure it is placed in the same folder as the program, and is spelled as above \n")
    print(" ----- Or: Did you create a Google Cloud Platform Project to access the API? ----- ")
    print(" ------ See section with instructions on obtaining an API Key at this page: ------- ")
    print(" ---------- https://github.com/ThioJoe/YouTube-Spammer-Purge/ ---------- ")
    input("\n Press Enter to Exit...")
    exit()

  log.debug("Authorizing...")
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
      log.debug("No valid " + TOKEN_FILE_NAME + " found. Requesting user consent...")
      flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=YOUTUBE_READ_WRITE_SSL_SCOPE)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(TOKEN_FILE_NAME, 'w') as token:
      token.write(creds.to_json())
  log.info("Successfully authorized")
  return build(API_SERVICE_NAME, API_VERSION, credentials=creds, discoveryServiceUrl=DISCOVERY_SERVICE_URL)

  

##########################################################################################
##################################### GET REPLIES ########################################
##########################################################################################

# Call the API's comments.list method to list the existing comment replies.
def get_replies(parent_id, video_id):
  global spamCommentsID
  global scannedRepliesCount

  log.info("Getting replies...")

  log.debug("Fetching replies...")
  results = youtube.comments().list(
    part="snippet",
    parentId=parent_id,
    maxResults=100, # 100 is the max per page, but multiple pages will be scanned
    #fields="items/snippet/authorDisplayName,items/snippet/authorChannelId/value,items/snippet/textDisplay,items/id", # If want to get author name and comment text
    fields="items/snippet/authorChannelId/value,items/id",
    textFormat="plainText"
  ).execute()
 
  log.debug("Analyzing replies information...") 
  # Iterates through items in results
  for item in results["items"]:  
    log.debug("Analyzing reply " + item["id"] +"'s information...")
    authorChannelID = item["snippet"]["authorChannelId"]["value"]
    replyID = item["id"]
    scannedRepliesCount += 1  # Count number of comment threads scanned, add to global count

    # If the comment is from the spammer channel, add to list of spam comment IDs
    # Also add key-value pair of comment ID and video ID to dictionary
    if any(authorChannelID == x for x in spammer_channel_id):
      spamCommentsID += [replyID]
      vidIdDict[replyID] = video_id

    print_count_stats(final=False) # Prints out current count stats

  return True

##########################################################################################
############################### PRINT SPECIFIC COMMENTS ##################################
##########################################################################################

# First prepared comments into groups of 50 to be submitted to API simultaneously
# Then uses print_prepared_comments() to print / log the comments
def print_comments(check_video_id_localprint, comments, logMode):
  log.info("Printing comments...")
  
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
  log.debug("Printing prepared comments...")
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
    log.debug("Printing comment from " + author + " ("+text+") ...")
    
    log.debug("Retriving video ID from object using comment ID")
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
      log.debug("Logging comments")
      logFile.write(str(j+1) + ". " + author + ":  " + text + "\n")
      log.info(str(j+1) + ". " + author + ":  " + text + "\n")
      if check_video_id_localprep is None:  # Only print video title if searching entire channel
        title = get_video_title(videoID) # Get Video Title
        logFile.write("     > Video: " + title + "\n")
        log.info("     > Video: " + title + "\n")
      logFile.write("     > Direct Link: " + "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comments[i] + "\n\n")
      log.info("     > Direct Link: " + "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comments[i] + "\n\n")

    i += 1
    j +=1

  return j


##########################################################################################
############################## GET COMMENT THREADS #######################################
##########################################################################################

# Call the API's commentThreads.list method to list the existing comments.
def get_comments(youtube, check_video_id=None, check_channel_id=None, nextPageToken=None):  # None are set as default if no parameters passed into function
  log.info("Getting comments...")
  global scannedThreadsCount
  global scannedCommentsCount
  global spamCommentsID
  #fieldsToFetch = "nextPageToken,items/id,items/snippet/topLevelComment/id,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/authorDisplayName,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/textDisplay,items/snippet/topLevelComment/snippet/videoId"
  fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/videoId"

  # Gets comment threads for a specific video
  if check_video_id is not None:
    log.debug("Fetching comment threads for video " + check_video_id + "...")
    
    results = youtube.commentThreads().list(
      part="snippet",
      videoId=check_video_id, 
      maxResults=100, # 100 is the max per page allowed by YouTube, but multiple pages will be scanned
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()
  
  # Get comment threads across the whole channel
  if check_video_id is None:
    log.debug("Fetching comment threads across the whole channel...")
    
    results = youtube.commentThreads().list(
      part="snippet",
      allThreadsRelatedToChannelId=check_channel_id,
      maxResults=100, # 100 is the max per page allowed by YouTube, but multiple pages will be scanned
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()  

  log.debug("Getting the token for the next page...")
  # Get token for next page
  try:
    RetrievedNextPageToken = results["nextPageToken"]
  except KeyError:
    RetrievedNextPageToken = "End"  
 
  # After getting comments threads for page, goes through each thread and gets replies
  for item in results["items"]:
    comment = item["snippet"]["topLevelComment"]
    #text = comment["snippet"]["textDisplay"]  # If need to retrieve comment text
    videoID = comment["snippet"]["videoId"] # Only enable if NOT checking specific video
    parent_id = item["snippet"]["topLevelComment"]["id"]
    numReplies = item["snippet"]["totalReplyCount"]
    log.debug("Getting thread from "+ parent_id+"...")

    log.debug("Analyzing thread's replies information...") 
    # Need to be able to catch exceptions because sometimes the API will return a comment from non-existent / deleted channel
    try:
      log.debug("The channel exists")
      authorChannelID = item["snippet"]["topLevelComment"]["snippet"]["authorChannelId"]["value"]
      #author = comment["snippet"]["authorDisplayName"]  # If need to retrieve author name
    except KeyError:
      log.debug("The channel NOT exists... Marking it as '[Deleted channel]'")
      authorChannelID = "[Deleted Channel]"
    scannedCommentsCount += 1  # Counts number of comments scanned, add to global count
    log.debug("Added 1 to scannedCommentsCount. Total: " + str(scannedCommentsCount))

    if any(authorChannelID == x for x in spammer_channel_id):
      log.debug("Comment from spammer channel")
      spamCommentsID += [parent_id]
      vidIdDict[parent_id] = videoID

    if numReplies > 0:
      log.debug("Found " + numReplies + "reply(es) in " + parent_id + "...")
      get_replies(parent_id=parent_id, video_id=videoID)
      scannedThreadsCount += 1  # Counts number of comment threads with at least one reply, adds to counter
      log.debug("Added 1 to scannedThreadsCount. Total: " + str(scannedThreadsCount))
    else:
      log.debug("No replies found in " + parent_id)
      print_count_stats(final=False)  # Updates displayed stats if no replies
  
  return RetrievedNextPageToken


##########################################################################################
################################ DELETE COMMENTS #########################################
########################################################################################## 

# Takes in dictionary of comment IDs to delete, breaks them into 50-comment chunks, and deletes them in groups
def delete_found_comments(commentsDictionary,banChoice):

    log.info("Deleting comments...")

    # Deletes specified comment IDs
    def delete(commentIDs):
        log.debug("Because of user's choices, the script deleting comments and banning the authors" if banChoice == True else "Deleting comments, but not banning authors")
        youtube.comments().setModerationStatus(id=commentIDs, moderationStatus="rejected", banAuthor=banChoice).execute()

    print("Deleting Comments. Please Wait...")
    commentsList = list(commentsDictionary.keys()) # Takes comment IDs out of dictionary and into list
    if len(commentsList) > 50:
        log.debug("The list of comments is longer than 50 comments. Deleting in groups of 50")
        remainder = len(commentsList) % 50
        numDivisions = int((len(commentsList)-remainder)/50)
        for i in range(numDivisions):
            delete(commentsList[i*50:i*50+50])
        if remainder > 0:
            delete(commentsList[numDivisions*50:len(commentsList)])
    else:
        log.debug("The list of comments is less than 50 comments. Deleting all in one")
        delete(commentsList)
    log.info("The comments have been deleted.")
    print("Comments Deleted! Will now verify each is gone.\n")

# Takes in dictionary of comment IDs and video IDs, and checks if comments still exist individually
def check_deleted_comments(commentsDictionary):
    i = 0 # Count number of remaining comments
    j = 1 # Count number of checked
    log.info("Verifying if all of them were deleted.")
    log.debug("Starting verification of comments deleted.")
    for key, value in commentsDictionary.items():
        log.debug("Fetching comment " + key + "...")
        results = youtube.comments().list(
            part="snippet",
            id=key,  
            maxResults=1,
            fields="items",
            textFormat="plainText"
        ).execute()
        print("Verifying Comments Deleted..." + "."*j, end="\r")
        j += 1
        log.debug("Increased 1 to j variable. j's value is " + str(j))

        log.debug("Checking if comment " + key + " still exists...")
        if results["items"]:  # Check if the items result is empty
            log.warning("Possible Issue Deleting Comment: " + str(key) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(value) + "&lc=" + str(key))
            print("Possible Issue Deleting Comment: " + str(key) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(value) + "&lc=" + str(key))
            i += 1

    if i == 0:
        log.info("All comments were deleted.")
        print("\n\nSuccess: All spam comments should be gone.")
    elif i > 0:
        log.warning("There are " + str(i) + " comments that were not deleted. Check links above to see these comments.")
        print("\n\nWarning: " + str(i) + " spam comments may remain. Check links above or try running the program again.")
    else:
        log.error("There was an error verifying if all comments were deleted. However it may worked anyway")
        print("\n\nSomething strange happened... The comments may or may have not been deleted.")

    return None



##########################################################################################
############################### LESSER FUNCTIONS #########################################
########################################################################################## 

################################### GET VIDEO TITLE ###############################################
# Get video title from video ID using YouTube API request
def get_video_title(video_id):
  log.debug("Getting video title from video ID...")
  results = youtube.videos().list(
    part="snippet",
    id=video_id,
    fields="items/snippet/title",
    maxResults=1
  ).execute()
  
  title = results["items"][0]["snippet"]["title"]
  log.debug("Retrieved video title ( " + title + " ) from video ID.")

  return title

############################# GET CHANNEL ID FROM VIDEO ID #####################################
# Get channel ID from video ID using YouTube API request
def get_channel_id(video_id):
  log.debug("Getting channel ID from video ID (" + video_id + ")...")
  results = youtube.videos().list(
    part="snippet",
    id=video_id,
    fields="items/snippet/channelId",
    maxResults=1
  ).execute()
  
  channel_id = results["items"][0]["snippet"]["channelId"]
  log.debug("Retrieved channel ID ( " + channel_id + " ) from video ID ( " + video_id + " ).")

  return channel_id

############################# GET CURRENTLY LOGGED IN USER #####################################
# Get channel ID and channel title of the currently authorized user
def get_current_user():
  global youtube

  log.debug("Getting current user's channel ID and title...")
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
  log.debug("Converting comment ID to video ID...")
  video_id = vidIdDict[comment_id]
  log.debug("Retrieved video ID ( " + video_id + " ) from comment ID ( " + comment_id + " ).")
  return video_id

##################################### PRINT STATS ##########################################

# Prints Scanning Statistics, can be version that overwrites itself or one that finalizes and moves to next line
def print_count_stats(final):
  log.debug("Printing status of the scanning")
  if final == True:
    log.debug("Top Level Comments Scanned: " + str(scannedCommentsCount) + " | Replies Scanned: " + str(scannedRepliesCount) + " | Spam Found So Far: " +  str(len(spamCommentsID)))
    print("Top Level Comments Scanned: " + str(scannedCommentsCount) + " | Replies Scanned: " + str(scannedRepliesCount) + " | Spam Found So Far: " +  str(len(spamCommentsID)) + "\n")
  else:
    log.debug("Top Level Comments Scanned: " + str(scannedCommentsCount) + " | Replies Scanned: " + str(scannedRepliesCount) + " | Spam Found So Far: " +  str(len(spamCommentsID)))
    print("Top Level Comments Scanned: " + str(scannedCommentsCount) + " | Replies Scanned: " + str(scannedRepliesCount) + " | Spam Found So Far: " +  str(len(spamCommentsID)), end = "\r")
  
  return None

##################################### VALIDATE VIDEO ID #####################################
# Checks if video ID is correct length, and if so, gets the title of the video
def validate_video_id(inputted_video):
  log.debug("Validating video ID...")
  isolatedVideoID = "Invalid" # Default value
  # Get id from long video link
  if "/watch?" in inputted_video:
    log.debug("Video link is in the long format. Retriving video ID from it...")
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
      log.debug("Video ID is "+ isolatedVideoID)

  # Get id from short video link
  elif "/youtu.be/" in inputted_video:
    log.debug("Video link is in the short format. Retriving video ID from it...")
    startIndex = inputted_video.index(".be/") + 4
    endIndex = len(inputted_video)

    if "?" in inputted_video:
      endIndex = inputted_video.index("?")

    if endIndex != 0 and startIndex < endIndex and endIndex <= len(inputted_video):
      isolatedVideoID = inputted_video[startIndex:endIndex]
      log.debug("Video ID is "+ isolatedVideoID)

  else: 
    isolatedVideoID = inputted_video
    log.debug("Video ID is "+ isolatedVideoID)

  if len(isolatedVideoID) != 11:
    print("\nInvalid Video link or ID! Video IDs are 11 characters long.")
    log.error("Invalid Video link or ID! Video IDs are 11 characters long.")
    return False, None

  else:
    log.debug("Video ID is valid. Returning it")
    return True, isolatedVideoID

##################################### VALIDATE CHANNEL ID ##################################
# Checks if channel ID is correct length and in correct format - if so returns True
def validate_channel_id(inputted_channel):
  log.debug("Validating channel ID...")
  isolatedChannelID = "Invalid" # Default value

  # Get id from channel link
  if "/channel/" in inputted_channel:
    log.debug("Channel link is in the long format. Retriving channel ID from it...")
    startIndex = inputted_channel.rindex("/") + 1
    endIndex = len(inputted_channel)
    
    if "?" in inputted_channel:
      endIndex = inputted_channel.rindex("?")

    if startIndex < endIndex and endIndex <= len(inputted_channel):
      isolatedChannelID = inputted_channel[startIndex:endIndex]
      log.debug("Channel ID is "+ isolatedChannelID)

  elif "/c/" in inputted_channel:
    log.debug("Channel link is in the short format. Retriving channel ID from it...")
    startIndex = inputted_channel.rindex("/c/") + 3 #Start index at at character after /c/
    endIndex = len(inputted_channel)

    # If there is a / after the username scoot the endIndex over
    if startIndex != inputted_channel.rindex("/") + 1:
      endIndex = inputted_channel.rindex("/") # endIndex is now at the last /

    if startIndex < endIndex and endIndex <= len(inputted_channel):
      customURL = inputted_channel[startIndex:endIndex]
      log.debug("Because this is a short link, the channel ID is not explicit, so retriving it form YouTube's API")
      response = youtube.search().list(part="snippet",q=customURL, maxResults=1).execute()
      if response.get("items"):
          isolatedChannelID = response.get("items")[0]["snippet"]["channelId"] # Get channel ID from custom channel URL username
          log.debug("Channel ID is "+ isolatedChannelID)
  
  # Handle legacy style custom URL (no /c/ for custom URL)
  elif ("youtube.com" in inputted_channel) and ("/c/" and "/channel/" not in inputted_channel):
    log.debug("Channel link is in the legacy format. Retriving channel ID from it...")
    startIndex = inputted_channel.rindex("/") + 1
    endIndex = len(inputted_channel)

    if startIndex < endIndex and endIndex <= len(inputted_channel):
      customURL = inputted_channel[startIndex:endIndex]
      log.debug("Because this is a legacy link, the channel ID is not explicit, so retriving it form YouTube's API")
      response = youtube.search().list(part="snippet",q=customURL, maxResults=1).execute()
      if response.get("items"):
          isolatedChannelID = response.get("items")[0]["snippet"]["channelId"] # Get channel ID from custom channel URL username
          log.debug("Channel ID is "+ isolatedChannelID)

  else:
    isolatedChannelID = inputted_channel
    log.debug("Channel ID is "+ isolatedChannelID)

  if len(isolatedChannelID) == 24 and isolatedChannelID[0:2] == "UC":
    log.debug("Channel ID is valid. Returning it")
    return True, isolatedChannelID
  else:
    log.error("Invalid Channel link or ID! Channel IDs are 24 characters long and start with 'UC'.")
    print("\nInvalid Channel link or ID! Channel IDs are 24 characters long and begin with 'UC'.")
    return False, None
  
############################### User Choice #################################
# User inputs Y/N for choice, returns True or False
# Takes in message to display

def choice(message=""):
  log.debug("Waiting for user's choice")
  # While loop until valid input
  valid = False
  while valid == False:
    response = input("\n" + message + " (y/n): ")
    if response == "Y" or response == "y":
      log.debug("User chose 'yes'. Returning True")
      return True
    elif response == "N" or response == "n":
      log.debug("User chose 'no'. Returning False")
      return False
    else:
      log.warning("Incorrect input by user")
      print("\nInvalid Input. Enter Y or N")


############################ Process Input Spammer IDs ###############################
# Takes single or list of spammer IDs, splits and sanitizes each, converts to list of channel IDs
# Returns list of channel IDs
def process_spammer_ids(rawString):
  log.debug("Processing spammer IDs...")
  inputList = [] # For list of unvalidated inputted items
  IDList = [] # For list of validated channel IDs, converted from inputList of spammer IDs - Separate to allow printing original invalid input if necessary
  inputList = rawString.split(",") # Split spammer IDs / Links by commas
  
  log.debug("Variables: inputList=" + str(inputList) + " IDList=" + str(IDList) + " rawString=" + str(rawString))

  # Remove whitespace from each list item
  for i in range(len(inputList)):
     inputList[i] =  inputList[i].strip()
  log.debug("Final result: " + str(inputList))
  
  IDList = list(inputList)  # Need to use list() so each list is separately affected, otherwise same pointer
  
  log.debug("Updating IDList to " + str(IDList))

  log.debug("Updating IDList to " + str(IDList))
  # Validate each ID in list
  for i in range(len(inputList)):
    log.debug("Validating spammer ID " + str(i) + ": " + str(inputList[i]))
    valid, IDList[i] = validate_channel_id(inputList[i])
    if valid == False:
      log.warn("Invalid spammer ID: " + str(inputList[i]))
      log.debug("Validated (as False) spammer ID " + str(i) + ": " + str(inputList[i]))
      print("Invalid Channel ID or Link: " + str(inputList[i]) + "\n")
      return False, None
  
  log.debug("All spammer's IDs should be right. Returning validated spammer IDs: " + str(IDList))
  return True, IDList
      
############################ Process Input Spammer IDs ###############################
# Opens log file to be able to be written
def open_log_file(name):
  log.debug("Opening log file...")
  global logFile
  logFile = open(name, "a", encoding="utf-8") # Opens log file in write mode

##################################### SET UP THE LOG ###########################################
# Note: I'm putting this here for it to cover all functions, from the error that the client_secrets.json file is not found, to the end of the program 

already_setted_up = False

# Logging variables for debugging and testing purposes
def logVariables(youtube,  spamCommentsID, vidIdDict, scannedThreadsCount, scannedRepliesCount, scannedCommentsCount, maxScanNumber, deletionEnabled, check_video_id, nextPageToken, logMode):
  variablesNames = ["youtube", "spamCommentsID", "vidIdDict", "scannedThreadsCount", "scannedRepliesCount", "scannedCommentsCount", "maxScanNumber", "deletionEnabled", "check_video_id", "nextPageToken", "logMode"] # List of variables names to log
  variablesValues = [youtube,  spamCommentsID, vidIdDict, scannedThreadsCount, scannedRepliesCount, scannedCommentsCount, maxScanNumber, deletionEnabled, check_video_id, nextPageToken, logMode] # List of variables values to log
  for i in range(len(variablesNames)):
    log.debug("Variable "+variablesNames[i] + ": " + str(variablesValues[i]))

def set_up_log(logName="Spam_Log_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S" + ".txt")):
  if logName == "": # If the script don't want to log, do nothing
    return False
  ######## Note: if you want to debug, change the "level" to "log.DEBUG", or name the file "debug"
  level = log.INFO # Default log level
  if logName == "debug": # If the user want to log in debug mode, set log level to DEBUG
    level = log.DEBUG
  log.basicConfig(filename=logName + ".log", level=level, filemode="w" , format='%(asctime)s %(levelname)s: %(message)s') # Setting up the logging config. "format" attribute is for formatting the log message to: "(now's date) (level: like CRITICAL or INFO): (message of the log)"
  print("Log file will be called " + logName + ".log \n") # Informing the user what is the file name
  log.info("Logging started") # Log 'Logging started'
  log.info("============ YOUTUBE SPAMMER PURGE v" + version + " ============") # Log intro
  return True


##########################################################################################
##########################################################################################
###################################### MAIN ##############################################
##########################################################################################
##########################################################################################

def main():
  # Declare Global Variables
  global youtube  
  global spammer_channel_id
  global spamCommentsID
  global vidIdDict
  global scannedThreadsCount
  global scannedRepliesCount
  global scannedCommentsCount

  # Default values for global variables
  # Spammer_channel_id doesn't need to be initialized because gets assigned in this function
  spamCommentsID = []
  vidIdDict = {}
  scannedThreadsCount = 0
  scannedRepliesCount = 0
  scannedCommentsCount = 0
  
  # Declare Default Variables
  maxScanNumber = 999999999
  deletionEnabled = "False" # Disables deletion functionality, which is default until later - String is used instead of boolean to prevent flipped bits
  check_video_id = None
  nextPageToken = "start"
  logMode = False

  ############################################## LOGGING TRIGGER ##############################################

  # Ask if the user want to keep the log
  keepLog = input("Do you want to log the activities? (Y/N) ")
  if keepLog == "Y" or keepLog == "y":
    logName = input("\nEnter the name of the log file (Nothing to auto generate the name and 'debug' to debug level. Debug level is specially useful if something is going wrong or you want to report some error): ") # Warn the user about the mess it will generate
  if logName == "": # If the user didn't enter a name, the script will generate one for him
      set_up_log()
  else: # If the user entered a name, the script will use it
    if logName == "debug": # If the user inputted 'debug' as the file name, the script will set up the log with the debug level
      print("Be clare, the output file WILL be a mess. Don't understanding some stuff is normal. However, this mess can be very useful for error reporting, testing and/or debugging.")
    if os.path.exists(logName + ".log"): # Check if the file already exists
      overwrite = input("\nThe log file " + logName + ".log already exists. Do you want to overwrite it? (Y/N) ") # If so, ask if the user wants to overwrite it or not
      if overwrite == "Y" or overwrite == "y": # If the user wants to overwrite the file
        print("Ok, continuing...") # Warn the user that the script will overwrite the file
        already_setted_up = True # The script will set this variable to True to not execute the set_up_log function again
        set_up_log(logName) # The script will set up the log with this name anyway
      else: # If the user doesn't want to overwrite the file
        print("Ok, generating a file with the name specified and now's date...") # Warn the user that the script will generate the file with the name specified and now's date
        already_setted_up = True # The script will set this variable to True to not execute the set_up_log function again
        set_up_log(logName + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")) # The script will set up the log with this name and now's date
    else: # If the file doesn't exist
      already_setted_up = True # The script will set this variable to True to not execute the set_up_log function again
      set_up_log(logName) # The script will set up the log with this name
    if not already_setted_up: # If the script didn't set up the log yet #### Note: I THINK this is not necessary, and is only a safeguard.
      set_up_log(logName) # It will do it now ############################## If you are sure this is not necessary, you can make a pull request and take these lines out


  # Authenticate with the Google API
  youtube = get_authenticated_service()

  logVariables(youtube, spamCommentsID, vidIdDict, scannedThreadsCount, scannedRepliesCount, scannedCommentsCount, maxScanNumber, deletionEnabled, check_video_id, nextPageToken, logMode) # Log variables
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
  log.debug("Waiting for user to confirm the logged  in account...")

  confirmedCorrectLogin = False
  log.debug("Variable confirmedCorrect: " + str(confirmedCorrectLogin))
  while confirmedCorrectLogin == False:
    # Get channel ID and title of current user, confirm with user
    log.debug("Getting current user")
    currentUser = get_current_user() # Returns [channelID, channelTitle]
    log.debug("Current user: "+ str(currentUser))
    print("\n    >  Currently logged in user: " + str(currentUser[1]) + " (Channel ID: " + str(currentUser[0]) + " )")
    if choice("       Continue as this user?") == True:
      log.debug("User accepted current user logged in. Continuing the program...")
      check_channel_id = currentUser[0]
      confirmedCorrectLogin = True
    else:
      log.debug("User declined current user logged in. Asking for log in again...")
      os.remove(TOKEN_FILE_NAME)
      log.debug("Token file removed.")
      youtube = get_authenticated_service()
  
  # User selects scanning mode,  while Loop to get scanning mode, so if invalid input, it will keep asking until valid input
  print("\n-----------------------------------------------------------------")
  print("~~ Do you want to scan a single video, or your entire channel? ~~")
  print("      1. Scan Single Video")
  print("      2. Scan Entire Channel")

  log.debug("Getting scanning mode")
  validMode = False
  while validMode == False:
    mode = str(input("Choice: "))
    log.debug("The user input was " + mode)
    # If chooses to scan single video - Validate Video ID, get title, and confirm with user - otherwise exits
    if mode == "1":
      validMode = True
      #While loop to get video ID and if invalid ask again
      validVideoID = (False, None) # Tuple, first element is status of validity of video ID, second element is video ID
      log.debug("User chose to scan a single video. Waiting for video link/ID")
      confirm = False
      while validVideoID[0] == False or confirm == False:
        check_video_id = input("Enter Video link or ID to scan: ")
        validVideoID = validate_video_id(check_video_id) # Sends link or video ID for isolation and validation
        
        if validVideoID[0] == True:  #validVideoID now contains True/False and video ID
          log.debug("Video ID is valid. Continuing...")
          check_video_id = str(validVideoID[1])
          log.debug("Video ID is " + check_video_id)
          title = get_video_title(check_video_id)
          log.debug("Video title is " + title)
          print("Chosen Video:  " + title)
          confirm = choice("Is this correct?")
          log.debug("User confirmed video title. Continuing...")
          if currentUser[0] != get_channel_id(check_video_id):
            log.warning(">>> It is not possible to delete comments on someone elses video! Who do you think you are!? <<<")
            print("\n   >>> WARNING It is not possible to delete comments on someone elses video! Who do you think you are!? <<<")
            input("\n   Press Enter to continue for testing purposes...  (But you will get an error when trying to delete!)\n")
            log.info("User confirmed that they are not trying to delete someone elses comments. Continuing...")

    # If chooses to scan entire channel - Validate Channel ID
    elif mode == "2":
      log.debug("User chose to scan the entire channel. Waiting for max scan number")
      validMode = True
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
          
    else:
      log.warning("User invalid choice")
      print("\nInvalid choice! - Enter either 1 or 2. ")

  # User inputs channel ID of the spammer, while loop repeats until valid input
  processResult = (False, None) #Tuple, first element is status of validity of channel ID, second element is channel ID
  while processResult[0] == False:
    log.debug("Waiting for channel link(s)/ID(s)")
    spammer_channel_id = input("Enter the Channel link(s) or ID(s) of the spammer (comma separated): ")
    processResult = process_spammer_ids(spammer_channel_id)
    log.debug("Processed spammer channel ID(s): " + str(processResult[1]) + " (Array of link(s)/ID(s): " + str(spammer_channel_id) + ")")
    if processResult[0] == True:
      spammer_channel_id = processResult[1] # After processing, if valid, spammer_channel_id is a list of channel IDs
  print("\n")

  # Check if spammer ID and user's channel ID are the same, and warn
  # If using channel-wide scanning mode, program will not run for safety purposes
  if any(currentUser[0] == i for i in spammer_channel_id) and mode == "2":
    log.warning("Mode: "+ mode +" | User is scanning for himself's channel. For safety purposes, this program's delete functionality is disabled when scanning for yourself across your entire channel (Mode 2). \n To do this use mode 1 (Single video scan)")
    print("WARNING - You are scanning for your own channel ID!")
    print("For safety purposes, this program's delete functionality is disabled when scanning for yourself across your entire channel (Mode 2).")
    print("If you want to delete your own comments for testing purposes, you can instead scan an individual video (Mode 1).")
    confirmation = choice("Continue?")
    if confirmation == False:
      input("Ok, Cancelled. Press Enter to Exit...")
      log.info("\n\nUser exited. End of the log")
      exit()
  elif any(currentUser[0] == i for i in spammer_channel_id) and mode == "1":
    log.warning("Mode: "+ mode +" | User is scanning for himself's channel. Asking if user is sure about that")
    print("WARNING: You are scanning for your own channel ID! This would delete all of your comments on the video!")
    print("     (You WILL still be asked to confirm before actually deleting anything)")
    print("If you are testing and want to scan and/or delete your own comments, enter 'Y' to continue, otherwise enter 'N' to exit.")
    confirmation = choice("Continue?")
    if confirmation == True:  # After confirmation, deletion functionality is eligible to be enabled later
      deletionEnabled = "HalfTrue"
    elif confirmation == False:
      input("Ok, Cancelled. Press Enter to Exit...")
      log.info("\n\nUser exited. End of the log")
      exit()
  else: 
    deletionEnabled = "HalfTrue" # If no matching problem found, deletion functionality is eligible to be enabled later
    log.debug("No matching problem found. Continuing with variable 'deletionEnabled' as " + str(deletionEnabled))

  ##################### START SCANNING #####################
  try:
    # Goes to get comments for first page
    if nextPageToken == "start":
      log.info("\nScanning...")
      log.debug("Getting comments for first page")
      print("Scanning... \n")
      nextPageToken = get_comments(youtube, check_video_id=check_video_id, check_channel_id=check_channel_id)
      log.debug("Comments for the first page: " + str(nextPageToken))
      print_count_stats(final=False)  # Prints comment scan stats, updates on same line

    # After getting first page, if there are more pages, goes to get comments for next page
    while nextPageToken != "End" and scannedCommentsCount < maxScanNumber:
      nextPageToken = get_comments(youtube, check_video_id=check_video_id, check_channel_id=check_channel_id, nextPageToken=nextPageToken)
      log.debug("Comments for the next page: " + str(nextPageToken))

    print_count_stats(final=True)  # Prints comment scan stats, finalizes
    log.info("\nScanning complete!")

    # Counts number of spam comments and prints list
    spam_count = len(spamCommentsID)
    log.debug("Spammers: " + str(spam_count))
    if spam_count == 0: # If no spam comments found, exits
      print("No spam comments found!\n")
      log.info("No spam comments found!")
      input("\nPress Enter to exit...")
      log.info("\n\nUser exited. End of the log")
      exit()
    print("Number of Spammer Comments Found: " + str(len(spamCommentsID)))

    # Asks user if they want to save list of spam comments to a file
    if choice("Spam comments ready to display. Also save the list to a text file (If you say no, the comments wouldn't be on the previous log file)?") == True:
      logMode = True
      logFileName = "Spam_Log_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S" + ".txt")
      print("Log file will be called " + logFileName + "\n")
      input("Press Enter to display comments...")

      # Write heading info to log file
      open_log_file(logFileName)
      log.info("Log file created: " + logFileName)
      logFile.write("----------- YouTube Spammer Purge Log File ----------- \n\n")
      log.info("----------- YouTube Spammer Purge Log File output ----------- \n\n")
      logFile.write("Channel IDs of spammer searched: " + str(spammer_channel_id) + "\n\n")
      log.info("Channel IDs of spammer searched: " + str(spammer_channel_id) + "\n\n")
      logFile.write("Number of Spammer Comments Found: " + str(len(spamCommentsID)) + "\n\n")
      log.info("Number of Spammer Comments Found: " + str(len(spamCommentsID)) + "\n\n")
      logFile.write("IDs of Spammer Comments: " + "\n" + str(spamCommentsID) + "\n\n\n")
      log.info("IDs of Spammer Comments: " + "\n" + str(spamCommentsID) + "\n\n\n")
      
    else:
      log.info("User didn't want to log.")
      print("Ok, continuing... \n")

    # Prints list of spam comments
    log.debug("Showing comments...")
    print("\n\nComments by the selected user: \n")
    print_comments(check_video_id,spamCommentsID, logMode)
    if logMode == True: logFile.close() and log.debug("Closed log file")
      
    
    # Get confirmation to delete spam comments
    confirmDelete = None
    print("\n")
    print("Check that all comments listed above are indeed spam.")
    log.info("Waiting for user's consent")

    if deletionEnabled == "HalfTrue": # Check if deletion functionality is eligible to be enabled
      confirmDelete = input("Do you want to delete ALL of the above comments? Type 'YES' exactly, in all caps! \n") 
      if confirmDelete != "YES":  # Deletion functionality enabled via confirmation, or not
        log.warn("User didn't want to delete comments. The script will NOT delete the comments.")
        input("\nDeletion CANCELLED. Press Enter to exit...")
        log.info("\n\nUser exited. End of the log")
        exit()
      elif confirmDelete == "YES":
        log.info("User accepted deleting comments")
        deletionEnabled = "True"
        log.debug("Because the user accepted delete the comments, 'deletionEnabled' is now " + deletionEnabled)
    elif deletionEnabled == "False" and spammer_channel_id == currentUser[0] and mode == "2":
      log.info("Because user is running on mode " + mode + ", the script will NOT delete the comments.")
      input("\nDeletion functionality disabled for this mode because you scanned your own channel. Press Enter to exit...")
      log.info("\n\nUser rejected deletion. Exiting program... \n End of the log")
      exit()
    else:
      input("\nFAILSAFE: For an unknown reason, the deletion functionality was not enabled. Cannot delete comments. Press Enter to exit...")
      log.error("FAILSAFE: For an unknown reason, the deletion functionality was not enabled. Cannot delete comments. Press Enter to exit...")
      log.inf("\n\nFailsafe occurred. Exiting program... \n End of the log")
      exit()
      

    if confirmDelete == "YES" and deletionEnabled == "True":  # Only proceed if deletion functionality is enabled, and user has confirmed deletion
      log.info("Because user accepted deleting the comments, asking to also ban the spammer(s)")
      # Ask if they want to also ban spammer
      banChoice = choice("Also ban the spammer(s) ?")
      if logMode == True:
        open_log_file(logFileName)
        log.debug("Because logMode is " + str(logMode) + ", writing user's choice.")
        logFile.write("\n\nSpammers Banned: " + str(banChoice)) # Write whether or not spammer is banned to log file
        log.info("\n\nSpammers Banned: " + str(banChoice)) # Write whether or not spammer is banned to log file
        logFile.close()
      print("\n")
      log.info("Deleting comments...")
      delete_found_comments(vidIdDict,banChoice) # Deletes spam comments
      log.info("Verifying if comments are gone...")
      check_deleted_comments(vidIdDict) #Verifies if comments were deleted
      
      input("\nDeletion Complete. Press Enter to Exit...")
      log.info("\n\nDeletion complete. Exiting program... \n End of the log")

    else:
      input("\nDeletion Cancelled. Press Enter to exit...")
      log.info("\n\nDeletion cancelled. Exiting program... \n End of the log")
      exit()

  # Catches exception errors and prints error info
  # If possible transient error, tells user to try again
  except HttpError as e:
    traceback.print_exc()
    print("------------------------------------------------")
    print("Error Message: ")
    print(e)
    log.error("------------------------------------------------")
    log.error("Error Message: ")
    log.error(e)
    if e.status_code: # If error code is available, print it
      print("\nError Info:")
      print("    Code: "+ str(e.status_code))
      log.error("\nError Info:")
      log.error("    Code: "+ str(e.status_code)) 
      if e.error_details[0]["reason"]: # If error reason is available, print it
        reason = str(e.error_details[0]["reason"])
        log.error("    Reason: " + reason)
        print("    Reason: " + reason)
        if reason == "processingFailure":
          print("\n !! Processing Error - Sometimes this error fixes itself. Try just running the program again. !!")
          print("(This also occurs if you try deleting comments on someone elses video, which is not possible.)")
          log.error("\n !! Processing Error - Sometimes this error fixes itself. Try just running the program again. !!")
          log.error("(This also occurs if you try deleting comments on someone elses video, which is not possible.)")
      input("\n Press Enter to Exit...")
    else:
      print("Unknown Error occurred. If this keeps happening, consider posting a bug report on the GitHub issues page, and include the above error info.")
      input("\n Press Enter to Exit...")
  else:
    print("\nFinished Executing.")
    log.info("Program finished successfully. Exiting program... \n End of the log")

# Runs the program
if __name__ == "__main__":
  main()
