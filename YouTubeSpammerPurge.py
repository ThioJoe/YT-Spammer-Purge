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
version = "1.2.0"
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

import os
from datetime import datetime

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

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
logMode = False
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

# Check if client_secrets.json file exists, if not give error
if not os.path.exists(CLIENT_SECRETS_FILE):
  print("\n ------------- ERROR: client_secrets.json file not found! ------------- ")
  print(" Make sure it is placed in the same folder as the program, and is spelled as above \n")
  print(" ----- Or: Did you create a Google Cloud Platform Project to access the API? ----- ")
  print(" ------ See section with instructions on obtaining an API Key at this page: ------- ")
  print(" ---------- https://github.com/ThioJoe/YouTube-Spammer-Purge/ ---------- ")
  input("\n Press Enter to Exit...")
  exit()

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
YOUTUBE_READ_WRITE_SSL_SCOPE = ['https://www.googleapis.com/auth/youtube.force-ssl']
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
  # The file token.pickle stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first time.
  if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, scopes=YOUTUBE_READ_WRITE_SSL_SCOPE)

  # If there are no (valid) credentials available, make the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
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

  return results["items"]

##########################################################################################
############################### PRINT SPECIFIC COMMENTS ##################################
##########################################################################################

# First prepared comments into groups of 50 to be submitted to API simultaneously
# Then uses print_prepared_comments() to print / log the comments
def print_comments(comments, logMode):
  j = 0 # Index when going through comments all comment groups
  if len(comments) > 50:
    remainder = len(comments) % 50
    numDivisions = int((len(comments)-remainder)/50)
    for i in range(numDivisions):
      j = print_prepared_comments(comments[i*50:i*50+50], j, logMode)
    if remainder > 0:
      j = print_prepared_comments(comments[numDivisions*50:len(comments)],j, logMode)
  else:
    j = print_prepared_comments(comments, j, logMode)

# Uses comments.list YouTube API Request to get text and author of specific set of comments, based on comment ID
def print_prepared_comments(comments, j, logMode):
  global check_video_id
  global logFile

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

    # Get video title
    title = get_video_title(videoID)

    # Prints comment info to console
    print(str(j+1) + ". " + author + ":  " + text)
    if check_video_id is None:  # Only print video title if searching entire channel
      print("     > Video: " + title)
    print("     > Direct Link: " + "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comments[i] + "\n")

    # If logging enabled, also prints to log file
    if logMode == True:
      logFile.write(str(j+1) + ". " + author + ":  " + text + "\n")
      if check_video_id is None:  # Only print video title if searching entire channel
        logFile.write("     > Video: " + title + "\n")
      logFile.write("     > Direct Link: " + "https://www.youtube.com/watch?v=" + videoID + "&lc=" + comments[i] + "\n\n")

    i += 1
    j +=1

  return j


##########################################################################################
############################## GET COMMENT THREADS #######################################
##########################################################################################

# Call the API's commentThreads.list method to list the existing comments.
def get_comments(youtube, check_video_id=None, check_channel_id=None, nextPageToken=None):
  global scannedThreadsCount
  global scannedCommentsCount
  global spamCommentsID
  fieldsToFetch = "nextPageToken,items/id,items/snippet/topLevelComment/id,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/authorDisplayName,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/textDisplay,items/snippet/topLevelComment/snippet/videoId"

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
    author = comment["snippet"]["authorDisplayName"]  # If need to retrieve author name
    authorChannelID = item["snippet"]["topLevelComment"]["snippet"]["authorChannelId"]["value"]
    #text = comment["snippet"]["textDisplay"]  # If need to retrieve comment text
    videoID = comment["snippet"]["videoId"] # Only enable if NOT checking specific video
    parent_id = item["snippet"]["topLevelComment"]["id"]
    numReplies = item["snippet"]["totalReplyCount"]
    scannedCommentsCount += 1  # Counts number of comments scanned, add to global count

    if authorChannelID == spammer_channel_id:
      spamCommentsID += [parent_id]
      vidIdDict[parent_id] = videoID

    if numReplies > 0:
      reply_results = get_replies(parent_id=parent_id, video_id=videoID)
      scannedThreadsCount += 1  # Counts number of comment threads with at least one reply, adds to counter
  
  return RetrievedNextPageToken


##########################################################################################
################################ DELETE COMMENTS #########################################
########################################################################################## 

# Takes in dictionary of comment IDs to delete, breaks them into 50-comment chunks, and deletes them in groups
def delete_found_comments(commentsDictionary):

    # Deletes specified comment IDs
    def delete(commentIDs):
        youtube.comments().setModerationStatus(id=commentIDs, moderationStatus="rejected").execute()

    print("Deleting Comments. Please Wait...")
    commentsList = list(commentsDictionary.keys()) # Takes comment IDs out of dictionary and into list
    if len(commentsList) > 50:
        remainder = len(commentsList) % 50
        numDivisions = int((len(commentsList)-remainder)/50)
        for i in range(numDivisions):
            delete(commentsList[i*50:i*50+50])
        if remainder > 0:
            delete(commentsList[numDivisions*50:len(commentsList)])
    else:
        delete(commentsList)
    print("Comments Deleted! Will now verify each is gone.\n")

# Takes in dictionary of comment IDs and video IDs, and checks if comments still exist individually
def check_deleted_comments(commentsDictionary):
    i = 0 # Count number of remaining comments
    j = 1 # Count number of checked
    for key, value in commentsDictionary.items():
        results = youtube.comments().list(
            part="snippet",
            id=key,  
            maxResults=1,
            fields="items",
            textFormat="plainText"
        ).execute()
        print("Verifying Comments Deleted..." + "."*j, end="\r")
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


################################# VIDEO ID LOOKUP ##############################################
# Using comment ID, get corresponding video ID from dictionary variable
def convert_comment_id_to_video_id(comment_id):
  video_id = vidIdDict[comment_id]
  return video_id

##################################### PRINT STATS ##########################################

# Prints Scanning Statistics, can be version that overwrites itself or one that finalizes and moves to next line
def print_count_stats(final):
  if final == True:
    print("Top Level Comments Scanned: " + str(scannedCommentsCount) + " | Replies Scanned: " + str(scannedRepliesCount) + " | Spam Found So Far: " +  str(len(spamCommentsID)) + "\n")
  else:
    print("Top Level Comments Scanned: " + str(scannedCommentsCount) + " | Replies Scanned: " + str(scannedRepliesCount) + " | Spam Found So Far: " +  str(len(spamCommentsID)), end = "\r")
  
  return None

##################################### VALIDATE VIDEO ID #####################################
# Checks if video ID is correct length, and if so, gets the title of the video
def validate_video_id(video_id):
  if len(video_id) != 11:
    print("\nInvalid Video ID! Video IDs are 11 characters long.")
    return False
  else:
    return True

##################################### VALIDATE CHANNEL ID ##################################
# Checks if channel ID is correct length and in correct format - if so returns True
def validate_channel_id(channel_id):
  if len(channel_id) == 24 and channel_id[0:2] == "UC":
    return True
  else:
    print("\nInvalid Channel ID! Channel IDs are 24 characters long and begin with 'UC'.")
    return False
  
############################### Confirmation to continue #################################
# User inputs Y/N confirmation to continue, and exits if not yes
# Takes in message to display

def confirm_continue(message=""):
  # While loop until valid input
  valid = False
  while valid == False:
    response = input("\n" + message + " (Y/N): ")
    if response == "Y" or response == "y":
      return True
    elif response == "N" or response == "n":
      return False
    else:
      print("\nInvalid Input. Enter Y or N")


##########################################################################################
##########################################################################################
###################################### MAIN ##############################################
##########################################################################################
##########################################################################################

if __name__ == "__main__":
  # Authenticate with the Google API
  # If get error about instantiation or creds expired, just delete token.pickle and run again
  youtube = get_authenticated_service()
  
  # Intro message
  print("============ YOUTUBE SPAMMER PURGE v" + version + " ============")
  print("== https://github.com/ThioJoe/YouTube-Spammer-Purge ==")
  print("======== Author: ThioJoe - YouTube.com/ThioJoe ======= \n")

  print("Purpose: Lets you scan and mass delete all comments from a specific user at once \n")
  print("NOTE: It's probably better to scan a single video, because you can scan all those comments,")
  print("      but scanning your entire channel must be limited and might miss older spam comments.")
  print("You WILL be shown the comments to confirm before they are deleted. \n")

 
  
  # User selects scanning mode,  while Loop to get scanning mode, so if invalid input, it will keep asking until valid input
  print("~~ Do you want to scan a single video, or your entire channel? ~~")
  print("      1. Scan Single Video")
  print("      2. Scan Entire Channel")

  validMode = False
  while validMode == False:
    mode = str(input("Choice: "))
    # If chooses to scan single video - Validate Video ID, get title, and confirm with user - otherwise exits
    if mode == "1":
      validMode = True
      
      #While loop to get video ID and if invalid ask again
      validVideoID = False
      confirm = False
      while validVideoID == False or confirm == False:
        check_video_id = input("Enter Video ID to scan: ")
        validVideoID = validate_video_id(check_video_id)
        title = get_video_title(check_video_id)
        print("Chosen Video:  " + title)
        confirm = confirm_continue("Is this correct?")
      userChannelID = get_channel_id(check_video_id)

    # If chooses to scan entire channel - Validate Channel ID, otherwise exit
    elif mode == "2":
      validMode = True
      # While loop to get channel ID, if invalid, asks again
      validChannelID = False
      while validChannelID == False:
        check_channel_id = input("Enter YOUR Channel ID: ")
        if validate_channel_id(check_channel_id) == True:
          validChannelID = True
          userChannelID = check_channel_id
          print("\n")
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
      print("\nInvalid choice! - Enter either 1 or 2. ")

  # User inputs channel ID of the spammer, while loop repeats until valid input
  validChannelID = False
  while validChannelID == False:
    spammer_channel_id = input("Enter the Channel ID of the spammer: ")
    validChannelID = validate_channel_id(spammer_channel_id)
  print("\n")

  # Check if spammer ID and user's channel ID are the same, and warn
  # If using channel-wide scanning mode, program will not run for safety purposes
  if spammer_channel_id == userChannelID and mode == "2":
    print("WARNING - You are scanning for your own channel ID!")
    print("For safety purposes, this program's delete functionality is disabled when scanning for yourself across your entire channel (Mode 2).")
    print("If you want to delete your own comments for testing purposes, you can instead scan an individual video (Mode 1).")
    confirmation = confirm_continue("Continue?")
    if confirmation == False:
      input("Ok, Cancelled. Press Enter to Exit...")
      exit()
  elif spammer_channel_id == userChannelID and mode == "1":
    print("WARNING: You are scanning for your own channel ID! This would delete all of your comments on the video!")
    print("     (You WILL still be asked to confirm before actually deleting anything)")
    print("If you are testing and want to scan and/or delete your own comments, enter 'Y' to continue, otherwise enter 'N' to exit.")
    confirmation = confirm_continue("Continue?")
    if confirmation == True:  # After confirmation, deletion functionality is elegible to be enabled later
      deletionEnabled = "HalfTrue"
    elif confirmation == False:
      input("Ok, Cancelled. Press Enter to Exit...")
      exit()
  else: 
    deletionEnabled = "HalfTrue" # If no matching problem found, deletion functionality is elegible to be enabled later

  ##################### START SCANNING #####################
  try:
    # Goes to get comments for first page
    if nextPageToken == "start":
      print("Scanning... \n")
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
      input("\nPress Enter to exit...")
      exit()
    print("Number of Spammer Comments Found: " + str(len(spamCommentsID)))

    # Asks user if they want to save list of spam comments to a file
    if confirm_continue("Spam comments ready to display. Also save the list to a text file?") == True:
      logMode = True
      logFileName = "Spam_Log_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S" + ".txt")
      logFile = open(logFileName, "w") # Opens log file in write mode
      print("Log file will be called " + logFileName + "\n")
      input("Press Enter to display comments...")

      # Write heading info to log file
      logFile.write("----------- YouTube Spammer Purge Log File ----------- \n\n")
      logFile.write("Channel ID spammer searched: " + spammer_channel_id + "\n\n")
      logFile.write("Number of Spammer Comments Found: " + str(len(spamCommentsID)) + "\n\n")
      logFile.write("IDs of Spammer Comments: " + "\n" + str(spamCommentsID) + "\n\n\n")

    else:
      print("Ok, continuing... \n")

    # Prints list of spam comments
    print("\n\nComments by the selected user: \n")
    print_comments(spamCommentsID, logMode)
    if logMode == True:
      logFile.close()



    # Get confirmation to delete spam comments
    confirmDelete = None
    print("\n")
    print("Check that all comments listed above are indeed spam.")

    if deletionEnabled == "HalfTrue": # Check if deletion functionality is elegible to be enabled
      confirmDelete = input("Do you want to delete ALL of the above comments? Type 'YES' exactly! \n") 
      if confirmDelete != "YES":  # Deletion functionality enabled via confirmation, or not
        input("\nDeletion CANCELLED. Press Enter to exit...")
        exit()
      elif confirmDelete == "YES":
        deletionEnabled = "True"
    elif deletionEnabled == "False" and spammer_channel_id == userChannelID and mode == "2":
      input("\nDeletion functionality disabled for this mode because you scanned your own channel. Press Enter to exit...")
      exit()
    else:
      input("\nFAILSAFE: For an unknown reason, the deletion functionality was not enabled. Cannot delete comments. Press Enter to exit...")
      exit()
      

    if confirmDelete == "YES" and deletionEnabled == "True":  # Only proceed if deletion functionality is enabled, and user has confirmed deletion
      print("\n")
      delete_found_comments(vidIdDict) # Deletes spam comments
      check_deleted_comments(vidIdDict) #Verifies if comments were deleted
      input("\nDeletion Complete. Press Enter to Exit...")
    else:
      input("\nDeletion Cancelled. Press Enter to exit...")
      exit()

  except HttpError as err:
    print(err)

  else:
    print("\nFinished Executing.")