#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#######################################################################################################
############################## YOUTUBE REPLY-SPAM COMMENT DELETER #####################################
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
###           Therefore I created this script to allow you to instantly purge their spam replies.
###
### NOTES:    1. Because of its limited purpose, the script ONLY deletes replies, not top-level comments.
###              That functinality may be added later if needed.
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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


import httplib2
import urllib
import os
import sys

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport import Request

#### DEFAULT VARIABLES ####
check_video_id = None
check_channel_id = None
maxScanNumber = 999999999
deletionEnabled = "False" # Disables deletion functionality, which is default until later - String is used instead of boolean to prevent flipped bits

########################
spamCommentsID = []
spamVidID = []
vidIdDict = {}
nextPageToken = "start"
scannedThreadsCount = 0
scannedRepliesCount = 0
scannedCommentsCount = 0
########################

##########################################################################################
################################## AUTHORIZATION #########################################
##########################################################################################
# Note: Most of everything in this section was copy-pasted from Google's API examples
# I don't fully understand how it works so it might be wonky
# If the credentials expire, just delete token.pickle and run the program again


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
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = 'token.pickle'

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:
   %s
with information from the APIs Console
https://console.developers.google.com

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# Authorize the request and store authorization credentials.
def get_authenticated_service():
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first time.
  if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, scopes=YOUTUBE_READ_WRITE_SSL_SCOPE)
  # If there are no (valid) credentials available, make the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      if creds.expired:
        print("\n ------------- Credentials Expired! Delete token.pickle file, and run again to re-authenticate ------------- \n")
      creds.refresh(Request())
      
    else:
      flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=YOUTUBE_READ_WRITE_SSL_SCOPE)
      creds = flow.run_local_server(port=0)
      # Save the credentials for the next run
    with open(TOKEN_FILE, 'w') as token:
      token.write(creds.to_json())

  return build(API_SERVICE_NAME, API_VERSION, credentials=creds)


##########################################################################################
##################################### GET REPLIES ########################################
##########################################################################################

# Call the API's comments.list method to list the existing comment replies.
def get_replies(parent_id, video_id):
  global spamCommentsID
  global scannedRepliesCount

  results = youtube.comments().list(
    part="snippet",
    parentId=parent_id,
    maxResults=100, # 100 is the max per page, but multiple pages will be scanned
    fields="items/snippet/authorDisplayName,items/snippet/authorChannelId/value,items/snippet/textDisplay,items/id",
    textFormat="plainText"
  ).execute()

  index = 0 # Index to use for object attributes

  # Iterates through items in results
  for item in results["items"]:  
    author = item["snippet"]["authorDisplayName"]
    authorChannelID = item["snippet"]["authorChannelId"]["value"]
    text = item["snippet"]["textDisplay"]
    replyID = item["id"]

    scannedRepliesCount += 1  # Count number of comment threads scanned, add to global count

    # If the comment is from the spammer channel, add to list of spam comment IDs
    # Also add key-value pair of comment ID and video ID to dictionary
    if authorChannelID == spammer_channel_id:
      spamCommentsID += [replyID]
      vidIdDict[replyID] = video_id
      index+=1

  return results["items"]

##########################################################################################
############################### PRINT SPECIFIC COMMENTS ##################################
##########################################################################################

# Uses comments.list YouTube API Request to get text and author of specific set of comments, based on comment ID
def print_specific_comments(comments):
  global check_video_id

  results = youtube.comments().list(
    part="snippet",
    id=comments,  # The API request can take an entire comma separated list of comment IDs (in "id" field) to return info about
    maxResults=100, # 100 is the max per page, but multiple pages will be scanned
    fields="items/snippet/authorDisplayName,items/snippet/textDisplay",
    textFormat="plainText"
  ).execute()

  # Prints author and comment text for each comment
  print("\n")
  i = 0 # Index when going through comments
  for item in results["items"]:
    text = item["snippet"]["textDisplay"]
    author = item["snippet"]["authorDisplayName"]

    # Retrieve video ID from object using comment ID
    videoID = convert_comment_id_to_video_id(comments[i])

    # Get video title
    title = get_video_title(videoID)
    print(str(i+1) + ". " + author + ":  " + text)
    if check_video_id is None:  # Only print video title if searching entire channel
      print("     > Video: " + title)
    print("     > Direct Link: " + "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comments[i] + "\n")
    i += 1

  return None


##########################################################################################
############################## GET COMMENT THREADS #######################################
##########################################################################################

# Call the API's commentThreads.list method to list the existing comments.
def get_comments(youtube, check_video_id=None, check_channel_id=None, nextPageToken=None):
  global scannedThreadsCount
  global scannedCommentsCount
  fieldsToFetch = "nextPageToken,items/id,items/snippet/topLevelComment/id,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/authorDisplayName,items/snippet/topLevelComment/snippet/textDisplay,items/snippet/topLevelComment/snippet/videoId"

  # Gets comment threads for a specific video
  if check_channel_id is None and check_video_id is not None:
    results = youtube.commentThreads().list(
      part="snippet",
      videoId=check_video_id, 
      maxResults=100, # 100 is the max per page allowed by YouTube, but multiple pages will be scanned
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()
  
  # Get comment threads across the whole channel
  if check_channel_id is not None and check_video_id is None:
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
 
  # After getting comments threads for page, goes through each thread and gets replies
  for item in results["items"]:
    comment = item["snippet"]["topLevelComment"]
    #author = comment["snippet"]["authorDisplayName"]  # If need to retrieve author name
    #text = comment["snippet"]["textDisplay"]  # If need to retrieve comment text
    videoID = comment["snippet"]["videoId"] # Only enable if NOT checking specific video
    parent_id = item["snippet"]["topLevelComment"]["id"]
    numReplies = item["snippet"]["totalReplyCount"]
    scannedCommentsCount += 1  # Counts number of comments scanned, add to global count

    if numReplies > 0:
      reply_results = get_replies(parent_id=parent_id, video_id=videoID)
      scannedThreadsCount += 1  # Counts number of comment threads with at least one reply, adds to counter
  
  return RetrievedNextPageToken


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


################################# VIDEO ID LOOKUP ##############################################
# Using comment ID, get corresponding video ID from dictionary variable
def convert_comment_id_to_video_id(comment_id):
  video_id = vidIdDict[comment_id]
  return video_id

##################################### PRINT STATS ##########################################

# Prints Scanning Statistics, can be version that overwrites itself or one that finalizes and moves to next line
def print_count_stats(final):
  if final == True:
    print("Top Level Comments Scanned: " + str(scannedCommentsCount) + " | Comment Threads Scanned: " + str(scannedThreadsCount) + " | Replies Scanned: " + str(scannedRepliesCount) + "\n")
  else:
    print("Top Level Comments Scanned: " + str(scannedCommentsCount) + " | Comment Threads Scanned: " + str(scannedThreadsCount) + " | Replies Scanned: " + str(scannedRepliesCount), end = "\r")
  
  return None

##################################### VALIDATE VIDEO ID #####################################
# Checks if video ID is correct length, and if so, gets the title of the video
def validate_video_id(video_id):
  if len(video_id) != 11:
    print("Invalid Video ID! Video IDs are 11 characters long.")
    exit()
  else:
    title = get_video_title(video_id)
    return title

##################################### VALIDATE CHANNEL ID ##################################
# Checks if channel ID is correct length and in correct format - if so returns True
def validate_channel_id(channel_id):
  if len(channel_id) == 24 and channel_id[0:2] == "UC":
    return True
  else:
    print("Invalid Channel ID! Channel IDs are 24 characters long and begin with 'UC'.")
    exit()
  
############################### Confirmation to continue #################################
# User inputs Y/N confirmation to continue, and exits if not yes
# Takes in message to display

def confirm_continue(message=None):
  response = input("\n" + message +" (Y/N): ")
  if response == "Y" or response == "y":
    print("Ok, Continuing... \n")
    return True
  elif response == "N" or response == "n":
    print("Ok, Exiting...")
    exit()
  else:
    print("Invalid Input - Exiting...")
    exit()  

##########################################################################################
###################################### MAIN ##############################################
##########################################################################################

if __name__ == "__main__":
  # Authenticate with the Google API
  # If get error about instantiation or creds expired, just delete token.pickle and run again
  youtube = get_authenticated_service()
  
  # Intro message
  print("====== YOUTUBE SPAMMER MASS-DELETER ======")
  print("Lets you scan and mass delete all comment replies (and ONLY replies) by a specific user at once \n")
  print("NOTE: It's probably better to scan a single video, because you can scan all those comments,")
  print("      but scanning your entire channel must be limited and might miss older spam comments.")
  print("You WILL be shown the comments to confirm before they are deleted. \n")

  # User selects scanning mode
  print("~~ Do you want to scan a single video, or your entire channel? ~~")
  print("      1. Scan Single Video")
  print("      2. Scan Entire Channel")
  mode = str(input("Choice: "))

  # If chooses to scan single video - Validate Video ID, get title, and confirm with user - otherwise exits
  if mode == "1":
    check_video_id = input("Enter Video ID to scan: ")
    title = validate_video_id(check_video_id)
    print("Chosen Video:  " + title)
    confirm_continue("Is this correct?")
    userChannelID = get_channel_id(check_video_id)

  # If chooses to scan entire channel - Validate Channel ID, otherwise exit
  elif mode == "2":
    check_channel_id = input("Enter YOUR Channel ID: ")
    if validate_channel_id(check_channel_id) == True:
      print("\n")
      userChannelID = check_channel_id
      maxScanNumber = int(input("Enter the maximum number of comments to scan: "))
    else:
      print("Invalid Channel ID - Exiting...")
      exit()
  else:
    print("Invalid choice, exiting...")
    exit()

  # User inputs channel ID of the spammer
  spammer_channel_id = input("Enter the Channel ID of the spammer: ")
  if validate_channel_id(spammer_channel_id) == True:
    print("\n")
  else:
    exit()

  # Check if spammer ID and user's channel ID are the same, and warn
  # If using channel-wide scanning mode, program will not run for safety purposes
  if spammer_channel_id == userChannelID and mode == "2":
    print("WARNING - You are scanning for your own channel ID!")
    print("For safety purposes, this program's delete functionality is disabled when scanning for yourself across your entire channel (Mode 2).")
    print("If you want to delete your own comments for testing purposes, you can instead scan an individual video (Mode 1).")
    confirmation = confirm_continue("Continue?")
  elif spammer_channel_id == userChannelID and mode == "1":
    print("WARNING: You are scanning for your own channel ID! This would delete all of your reply comments on the video!")
    print("     (You WILL still be asked to confirm before actually deleting anything)")
    print("If you are testing and want to scan and/or delete your own comments, enter 'Y' to continue, otherwise enter 'N' to exit.")
    confirmation = confirm_continue("Continue?")
    if confirmation == True:  # After confirmation, deletion functionality is elegible to be enabled later
      deletionEnabled = "HalfTrue"
  else: 
    deletionEnabled = "HalfTrue" # If no matching problem found, deletion functionality is elegible to be enabled later

  ##################### START SCANNING #####################
  try:
    # Goes to get comments for first page
    if nextPageToken == "start":
      print("Starting Scan...")
      nextPageToken = get_comments(youtube, check_video_id=check_video_id, check_channel_id=check_channel_id)
      print_count_stats(final=False)  # Prints comment scan stats, updates on same line


    # After getting first page, if there are more pages, goes to get comments for next page
    while nextPageToken != "End" and scannedCommentsCount < maxScanNumber:
      nextPageToken = get_comments(youtube, check_video_id=check_video_id, check_channel_id=check_channel_id, nextPageToken=nextPageToken)
      print_count_stats(final=False)  # Prints comment scan stats, updates on same line

    print_count_stats(final=True)  # Prints comment scan stats, finalizes

    # Counts number of spam comments and prints list
    spam_count = len(spamCommentsID)
    if spam_count == 0: # If no spam comments found, exits
      print("No spam comments found!\n")
      input("Press Enter to exit...")
      exit()
    print("Number of Spammer Replies Found: " + str(len(spamCommentsID)))
    print("IDs of Spammer Replies: " + str(spamCommentsID))
    print("\n")

    # Prints list of spam comments
    print("Reply Comments by the selected user:")
    print_specific_comments(spamCommentsID)


    # Get confirmation to delete spam comments
    confirmDelete = None
    print("\n")
    print("Check that all comments listed above are indeed spam.")

    if deletionEnabled == "HalfTrue": # Check if deletion functionality is elegible to be enabled
      confirmDelete = input("Do you want to delete ALL of the above comments? Type 'YES' exactly! \n") 
      if confirmDelete != "YES":  # Deletion functionality enabled via confirmation, or not
        print("Deletion CANCELLED. Press Enter to exit...")
        exit()
      elif confirmDelete == "YES":
        deletionEnabled = "True"
    elif deletionEnabled == "False" and spammer_channel_id == userChannelID and mode == "2":
      input("Deletion functionality disabled for this mode because you scanned your own channel. Press Enter to exit...")
      exit()
    else:
      input("FAILSAFE: For an unknown reason, the deletion functionality was not enabled. Cannot delete comments. Press Enter to exit...")
      exit()
      

    if confirmDelete == "YES" and deletionEnabled == "True":  # Only proceed if deletion functionality is enabled, and user has confirmed deletion
      print("\n")
      # Deletes spam comment replies
      for key, value in vidIdDict.items():  # Iterates through dictionary vidIdDict, to ensure comments deleted are same as those displayed to user
        youtube.comments().delete(id=key).execute()
        if check_channel_id is not None:
          print("Deleted Comment ID: " + str(key) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(value) + "&lc=" + str(key)) # If searching whole channel
        if check_video_id is not None:
          print("Deleted Comment ID: " + str(key) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(check_video_id) + "&lc=" + str(key)) # If searching specific video
      print("Deletion Complete")
    else:
      input("Deletion Cancelled. Press Enter to exit...")
      exit()

  #except HttpError, e:
  except urllib.error.HTTPError as e:
    print("Error")
  else:
    print("\n Finished Executing.")