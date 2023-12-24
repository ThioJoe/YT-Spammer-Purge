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
version = "2.17.1"
configVersion = 32
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print("Importing Script Modules...")
# Import other module files
from Scripts.shared_imports import *
import Scripts.auth as auth
import Scripts.validation as validation
import Scripts.utils as utils
import Scripts.files as files
import Scripts.logging as logging
import Scripts.operations as operations
import Scripts.user_tools as user_tools
from Scripts.community_downloader import main as get_community_comments #Args = post's ID, comment limit
import Scripts.community_downloader as community_downloader
from Scripts.utils import choice

print("Importing Standard Libraries...")
# Standard Libraries
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import namedtuple
import json, ast
from pkg_resources import parse_version

print("Importing Third-Party Modules...")
# Other Libraries
from googleapiclient.errors import HttpError



##########################################################################################
##########################################################################################
###################################### MAIN ##############################################
##########################################################################################
##########################################################################################


def main():
  global S
  global B
  global F
  # These variables are from shared_imports.py
  # S - Style
  # B - Background
  # F - Foreground

  # Run check on python version, must be 3.6 or higher because of f strings
  if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    print("Error Code U-2: This program requires running python 3.6 or higher! You are running" + str(sys.version_info[0]) + "." + str(sys.version_info[1]))
    input("Press Enter to Exit...")
    sys.exit()

  # Declare Global Variables
  global YOUTUBE
  global CURRENTUSER
  User = namedtuple('User', 'id name configMatch')

  # Some Typehints
  scanMode: str
  config: dict
  jsonData: dict
  versionInfoJson: dict

  utils.clear_terminal()

  print("\nLoading YT Spammer Purge @ " + str(version) + "...")

  # Authenticate with the Google API - If token expired and invalid, deletes and re-authenticates
  YOUTUBE = auth.first_authentication()

           #### Prepare Resources ####
  resourceFolder = RESOURCES_FOLDER_NAME
  whitelistPathWithName = os.path.join(resourceFolder, "whitelist.txt")
  spamListFolder = os.path.join(resourceFolder, "Spam_Lists")
  filtersFolder = os.path.join(resourceFolder, "Filters")
  filterFileName = "filter_variables.py"
  spamListDict = {
      'Lists': {
        'Domains':  {'FileName': "SpamDomainsList.txt"},
        'Accounts': {'FileName': "SpamAccountsList.txt"},
        'Threads':  {'FileName': "SpamThreadsList.txt"}
      },
      'Meta': {
        'VersionInfo': {'FileName': "SpamVersionInfo.json"},
        'SpamListFolder': spamListFolder
        #'LatestLocalVersion': {} # Gets added later during check, this line here for reference
      }
  }
  filterListDict = {
    'Files': {
      'FilterVariables': {'FileName': filterFileName}
    },
    'ResourcePath': filtersFolder
    #'LocalVersion': {} # Gets added later during check, this line here for reference
  }

  resourcesDict = {
    'Whitelist': {
      'PathWithName': whitelistPathWithName,
      'FileName': "whitelist.txt",
    }
  }

  print("Checking for updates to program and spam lists...")
  # Check if resources, spam list, and filters folders exist, and create them
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
      input("Press Enter to Continue...")

  if os.path.isdir(resourceFolder) and not os.path.isdir(spamListFolder):
    try:
      os.mkdir(spamListFolder)
    except:
      print("\nError: Could not create folder. To update the spam lists, go into the 'SpamPurge_Resources' folder,")
      print("       then inside that, create another folder called 'Spam_Lists'.")

  if os.path.isdir(resourceFolder) and not os.path.isdir(filtersFolder):
      try:
        os.mkdir(filtersFolder)
      except:
        print("\nError: Could not create folder. To update the spam lists, go into the 'SpamPurge_Resources' folder,")
        print("       then inside that, create another folder called 'Filters'.")

  # Prepare to check and ingest spammer list files
  # Iterate and get paths of each list. Also gets path of filter_variables.py
  # This for loops might not actually do anything?
  for x,spamList in spamListDict['Lists'].items():
    spamList['Path'] = os.path.join(spamListFolder, spamList['FileName'])

  spamListDict['Meta']['VersionInfo']['Path'] = os.path.join(spamListFolder, spamListDict['Meta']['VersionInfo']['FileName']) # Path to version included in packaged assets folder

  # Check if each spam list exists, if not copy from assets, then get local version number, calculate latest version number
  latestLocalSpamListVersion = "1900.12.31"
  for x, spamList in spamListDict['Lists'].items():
    if not os.path.exists(spamList['Path']):
      files.copy_asset_file(spamList['FileName'], spamList['Path'])

    listVersion = files.get_list_file_version(spamList['Path'])
    spamList['Version'] = listVersion
    if listVersion and parse_version(listVersion) > parse_version(latestLocalSpamListVersion):
      latestLocalSpamListVersion = listVersion

  spamListDict['Meta']['VersionInfo']['LatestLocalVersion'] = latestLocalSpamListVersion

  # Check for version info file, if it doesn't exist, get from assets folder
  if not os.path.exists(spamListDict['Meta']['VersionInfo']['Path']):
    files.copy_asset_file(spamListDict['Meta']['VersionInfo']['FileName'], spamListDict['Meta']['VersionInfo']['Path'])

  # Check if filter_variables.py is in Spampurge_Resources, if not copy from temp folder or scripts, depending if using pyinstaller
  filterFilePath = os.path.join(filtersFolder, filterFileName)
  if not os.path.exists(filterFilePath):
    files.copy_scripts_file(filterFileName, filterFilePath)

  # Get stored spam list version data from json file
  jsonData = open(spamListDict['Meta']['VersionInfo']['Path'], 'r', encoding="utf-8")
  versionInfoJson = str(json.load(jsonData)) # Parses json file into a string
  versionInfo = ast.literal_eval(versionInfoJson) # Parses json string into a dictionary
  spamListDict['Meta']['VersionInfo']['LatestRelease'] = versionInfo['LatestRelease']
  spamListDict['Meta']['VersionInfo']['LastChecked'] = versionInfo['LastChecked']

  # Get current version of filter_variables.py that is in the SpamPurge_Resources/Filters folder
  filterVersion = files.get_current_filter_version(filterListDict)
  filterListDict['LocalVersion'] = filterVersion

  # Check for primary config file, load into dictionary 'config'. If no config found, loads data from default config in assets folder
  utils.clear_terminal()
  config = files.load_config_file(configVersion)
  validation.validate_config_settings(config)
  utils.clear_terminal()

  # Disable colors before they are used anywhere
  if config['colors_enabled'] == False:
    # Disables colors entirely
    init(autoreset=True, strip=True, convert=False)
  else:
    # Initiates colorama and creates shorthand variables for resetting colors
    init(autoreset=True)

  # Check for program and list updates if auto updates enabled in config
  try:
    if config['release_channel'] == "all":
      updateReleaseChannel = "all"
    elif config['release_channel'] == "stable":
      updateReleaseChannel = "stable"
    else:
      print("Invalid value for 'release_channel' in config file. Must be 'All' or 'Stable'")
      print("Defaulting to 'All'")
      input("Press Enter to Continue...")
      updateReleaseChannel = "all"
  except KeyError:
    print("\nYour version of the config file does not specify a release channel. Defaulting to 'All'")
    print(f"{F.YELLOW}Re-create your config{S.R} to get the latest version.")
    input("\nPress Enter to Continue...")
    updateReleaseChannel = "all"

  if config['auto_check_update'] == True:
    try:
      updateAvailable = files.check_for_update(version, updateReleaseChannel, silentCheck=True, )
    except Exception as e:
      print(f"{F.LIGHTRED_EX}Error Code U-3 occurred while checking for updates. (Checking can be disabled using the config file setting) Continuing...{S.R}\n")
      updateAvailable = None

    # Only check for updates once a day, compare current date to last checked date
    if datetime.today() > datetime.strptime(spamListDict['Meta']['VersionInfo']['LastChecked'], '%Y.%m.%d.%H.%M')+timedelta(days=1):
      # Check for update to filter variables file
      files.check_for_filter_update(filterListDict, silentCheck=True)
      # Check spam lists if today or tomorrow's date is later than the last update date (add day to account for time zones)
      if datetime.today()+timedelta(days=1) >= datetime.strptime(spamListDict['Meta']['VersionInfo']['LatestLocalVersion'], '%Y.%m.%d'):
        spamListDict = files.check_lists_update(spamListDict, silentCheck=True)        

  else:
    updateAvailable = False

  # In all scenarios, load spam lists into memory
  for x, spamList in spamListDict['Lists'].items():
    spamList['FilterContents'] = files.ingest_list_file(spamList['Path'], keepCase=False)

  # In all scenarios, load filter variables into memory. Must import prepare_modes after filter_variables has been updated and placed in SpamPurge_Resources
  print("Loading filter file...\n")
  import Scripts.prepare_modes as modes

  ####### Load Other Data into MiscData #######
  print("\nLoading other assets..\n")
  @dataclass
  class MiscDataStore:
    resources:dict
    spamLists:dict
    totalCommentCount:int
    channelOwnerID:str
    channelOwnerName:str

  miscData = MiscDataStore(
    resources = {},
    spamLists = {},
    totalCommentCount = 0,
    channelOwnerID = "",
    channelOwnerName = "",
    )

  miscData.resources = resourcesDict
  rootDomainListAssetFile = "rootZoneDomainList.txt"
  rootDomainList = files.ingest_asset_file(rootDomainListAssetFile)
  miscData.resources['rootDomainList'] = rootDomainList
  miscData.spamLists['spamDomainsList'] = spamListDict['Lists']['Domains']['FilterContents']
  miscData.spamLists['spamAccountsList'] = spamListDict['Lists']['Accounts']['FilterContents']
  miscData.spamLists['spamThreadsList'] = spamListDict['Lists']['Threads']['FilterContents']


  # Create Whitelist if it doesn't exist,
  if not os.path.exists(whitelistPathWithName):
    with open(whitelistPathWithName, "a") as f:
      f.write("# Commenters whose channel IDs are in this list will always be ignored. You can add or remove IDs (one per line) from this list as you wish.\n")
      f.write("# Channel IDs for a channel can be found in the URL after clicking a channel's name while on the watch page or where they've left a comment.\n")
      f.write("# - Channels that were 'excluded' will also appear in this list.\n")
      f.write("# - Lines beginning with a '#' are comments and aren't read by the program. (But do not put a '#' on the same line as actual data)\n\n")
    miscData.resources['Whitelist']['WhitelistContents'] = []
  else:
    miscData.resources['Whitelist']['WhitelistContents'] = files.ingest_list_file(whitelistPathWithName, keepCase=True)

  if config:
    moderator_mode = config['moderator_mode']
  else:
    moderator_mode = False

  utils.clear_terminal()



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
    userInfo = auth.get_current_user(config)
    CURRENTUSER = User(id=userInfo[0], name=userInfo[1], configMatch=userInfo[2]) # Returns [channelID, channelTitle, configmatch]
    auth.CURRENTUSER = CURRENTUSER
    print("\n    >  Currently logged in user: " + f"{F.LIGHTGREEN_EX}" + str(CURRENTUSER.name) + f"{S.R} (Channel ID: {F.LIGHTGREEN_EX}" + str(CURRENTUSER.id) + f"{S.R} )")
    if choice("       Continue as this user?", CURRENTUSER.configMatch) == True:
      confirmedCorrectLogin = True
      utils.clear_terminal()
    else:
      auth.remove_token()
      utils.clear_terminal()
      YOUTUBE = auth.get_authenticated_service()

  # Declare Classes
  @dataclass
  class ScanInstance:
    matchedCommentsDict: dict         #Comments flagged by the filter
    duplicateCommentsDict: dict       #Comments flagged as duplicates
    repostedCommentsDict: dict          #Comments stolen from other users
    otherCommentsByMatchedAuthorsDict: dict #Comments not matched, but are by a matched author
    scannedThingsList: list           #List of posts or videos that were scanned
    spamThreadsDict: dict             #Comments flagged as parent of spam threads
    allScannedCommentsDict: dict      #All comments scanned for this instance
    vidIdDict: dict                   #Contains the video ID on which each comment is found
    vidTitleDict: dict                #Contains the titles of each video ID
    matchSamplesDict: dict            #Contains sample info for every flagged comment of all types
    authorMatchCountDict: dict        #The number of flagged comments per author
    scannedRepliesCount: int          #The current number of replies scanned so far
    scannedCommentsCount: int         #The current number of comments scanned so far
    logTime: str                      #The time at which the scan was started
    logFileName: str                  #Contains a string of the current date/time to be used as a log file name or anything else
    errorOccurred:bool                #True if an error occurred during the scan


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
      duplicateCommentsDict={},
      repostedCommentsDict={},
      otherCommentsByMatchedAuthorsDict={},
      scannedThingsList=[],
      spamThreadsDict = {},
      allScannedCommentsDict={},
      vidIdDict={},
      vidTitleDict={},
      matchSamplesDict={},
      authorMatchCountDict={},
      scannedRepliesCount=0,
      scannedCommentsCount=0,
      logTime = timestamp,
      logFileName = None,
      errorOccurred = False,
      )

    # Declare Default Variables
    maxScanNumber = 999999999
    scanVideoID = None
    videosToScan = []
    recentPostsListofDicts = []
    postURL = ""
    loggingEnabled = False
    userNotChannelOwner = False

    utils.clear_terminal()

    # -----------------------------------------------------------------------------------------------------------------------------
    if updateAvailable != False:
      updateStringLabel = "Update Available: "
      if updateAvailable == True: # Stable update available
        updateString = f"{B.LIGHTGREEN_EX}{F.BLACK} Yes {S.R}"

      elif updateAvailable == "beta": # Beta Update Available
        if updateReleaseChannel == "stable":
          updateStringLabel = ""
          updateString = ""
        else:
          updateString = f"{B.LIGHTCYAN_EX}{F.BLACK} Beta {S.R}"
      elif updateAvailable == None:
        updateString = f"{F.LIGHTRED_EX}Error{S.R}"
        print("> Note: Error during check for updates. Select 'Check For Updates' for details.")

    else:
      if config['auto_check_update'] == False:
        updateStringLabel = "Update Checking: "
        updateString = "Off"
      else:
        updateStringLabel = ""
        updateString = ""

    # User selects scanning mode,  while Loop to get scanning mode, so if invalid input, it will keep asking until valid input
    print("\n{:<59}{:<18}{:>7}".format("> At any prompt, enter 'X' to return here", updateStringLabel, updateString))
    print("> Enter 'Q' now to quit")

    print(f"\n\n-------------------------------- {F.YELLOW}Scanning Options{S.R} --------------------------------")
    print(f"      1. Scan {F.LIGHTCYAN_EX}specific videos{S.R}")
    print(f"      2. Scan {F.LIGHTCYAN_EX}recent videos{S.R} for a channel")
    print(f"      3. Scan recent comments across your {F.LIGHTBLUE_EX}Entire Channel{S.R}")
    print(f"      4. Scan a specific {F.LIGHTMAGENTA_EX}community post{S.R} (Experimental)")
    print(f"      5. Scan {F.LIGHTMAGENTA_EX}recent community posts{S.R} for a channel (Experimental)")
    print(f"\n--------------------------------- {F.YELLOW}Other Options{S.R} ----------------------------------")
    print(f"      6. Create your own {F.LIGHTGREEN_EX}config file(s){S.R} to run the program with pre-set settings")
    print(f"      7. Remove comments using a {F.LIGHTRED_EX}pre-existing list{S.R} or log file")
    print(f"      8. Recover deleted comments using log file")
    print(f"      9. Check & Download {F.LIGHTCYAN_EX}Updates{S.R}")
    print(f"      10. {F.BLACK}{B.LIGHTGREEN_EX} NEW! {S.R} Helpful Tools")
    print("")



    # Make sure input is valid, if not ask again
    validMode:bool = False
    validConfigSetting:bool = True
    while validMode == False:
      if validConfigSetting == True and config and config['scan_mode'] != 'ask':
        scanMode = config['scan_mode']
      else:
        scanMode = input("Choice (1-10): ")
      if scanMode.lower() == "q":
        sys.exit()

      # Set scanMode Variable Names
      validModeValues = ['1', '2', '3', '4', '5', '6', '7', '8', '9','10', 'chosenvideos', 'recentvideos', 'entirechannel', 'communitypost', 'commentlist', 'recentcommunityposts']
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
        elif scanMode == "5" or scanMode == "recentcommunityposts":
          scanMode = "recentCommunityPosts"
        elif scanMode == "6":
          scanMode = "makeConfig"
        elif scanMode == "7" or scanMode == "commentlist":
          scanMode = "commentList"
        elif scanMode == "8":
          scanMode = "recoverMode"
        elif scanMode == "9":
          scanMode = "checkUpdates"
        elif scanMode == "10":
          scanMode = "tools"
      else:
        print(f"\nInvalid choice: {scanMode} - Enter a number from 1 to 10")
        validConfigSetting = False

# ================================================================================= CHOSEN VIDEOS ======================================================================================================

    # If chooses to scan single video - Validate Video ID, get title, and confirm with user
    if scanMode == "chosenVideos":
      # While loop to get video ID and if invalid ask again
      confirm:bool = False
      validConfigSetting = True
      while confirm == False:
        numVideos = 1
        allVideosMatchBool = True
        miscData.totalCommentCount = 0

        # Checks if input list is empty and if contains only valid video IDs
        listNotEmpty:bool = False
        validVideoIDs = False # False just to get into the loop
        while listNotEmpty == False or validVideoIDs == False:
          if validConfigSetting == True and config and config['videos_to_scan'] != 'ask':
            enteredVideosList = utils.string_to_list(config['videos_to_scan'])
            if len(enteredVideosList) == 0:
              validConfigSetting = False
              listNotEmpty = False
              print(f"{F.LIGHTRED_EX}\nError: Video list is empty!{S.R}")
            else:
              listNotEmpty = True
          else:
            print(f"\nEnter a list of {F.YELLOW}Video Links{S.R} or {F.YELLOW}Video IDs{S.R} to scan, separated by commas.")
            print(" > Note: All videos must be from the same channel.")
            enteredVideosList = utils.string_to_list(input("\nEnter here: "))
            if str(enteredVideosList).lower() == "['x']":
              return True # Return to main menu
            validConfigSetting = False
            if len(enteredVideosList) == 0:
              listNotEmpty = False
              print(f"{F.LIGHTRED_EX}\nError: Video list is empty!{S.R}")
            else:
              listNotEmpty = True

          # Validates all video IDs/Links, gets necessary info about them
          validVideoIDs:bool = True
          videosToScan = []
          videoListResult = [] # True/False, video ID, videoTitle, commentCount, channelID, channelTitle
          for i in range(len(enteredVideosList)):
            videoListResult.append([])
            videosToScan.append({})
            videoListResult[i] = validation.validate_video_id(enteredVideosList[i]) # Sends link or video ID for isolation and validation
            if videoListResult[i][0] == False:
              validVideoIDs = False
              validConfigSetting = False
              confirm = False
              break

        for i in range(len(videoListResult)): # Change this
          if videoListResult[i][0] == True:
            videosToScan[i]['videoID'] = str(videoListResult[i][1])
            videosToScan[i]['videoTitle'] = str(videoListResult[i][2])
            videosToScan[i]['commentCount'] = int(videoListResult[i][3])
            videosToScan[i]['channelOwnerID'] = str(videoListResult[i][4])
            videosToScan[i]['channelOwnerName'] = str(videoListResult[i][5])
            miscData.totalCommentCount += int(videoListResult[i][3])
            if str(videoListResult[i][1]) not in current.vidTitleDict:
              current.vidTitleDict[videoListResult[i][1]] = str(videoListResult[i][2])
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
              if config['skip_confirm_video'] == False:
                userChoice = choice(f"You have entered many videos, do you need to see the rest (x{remainingCount})?")
                if userChoice == False:
                  break
                elif userChoice == None:
                  return True # Return to main menu
            print(f" {i}. {video['videoTitle']}")
          print("")

          if CURRENTUSER.id != videosToScan[0]['channelOwnerID']:
            userNotChannelOwner = True

          miscData.channelOwnerID = videosToScan[0]['channelOwnerID']
          miscData.channelOwnerName = videosToScan[0]['channelOwnerName']

          # Ask if correct videos, or skip if config
          if config['skip_confirm_video'] == True:
            confirm = True
          else:
            if userNotChannelOwner == True and moderator_mode == False:
              print(f"{F.LIGHTRED_EX}NOTE: This is not your video. Enabling '{F.YELLOW}Not Your Channel Mode{F.LIGHTRED_EX}'. You can report spam comments, but not delete them.{S.R}")
            elif userNotChannelOwner == True and moderator_mode == True:
              print(f"{F.LIGHTRED_EX}NOTE: {F.YELLOW}Moderator Mode is enabled{F.LIGHTRED_EX}. You can hold comments for review when using certain modes{S.R}")
            print("Total number of comments to scan: " + str(miscData.totalCommentCount))
            if miscData.totalCommentCount >= 100000:
              print(f"\n{B.YELLOW}{F.BLACK} WARNING: {S.R} You have chosen to scan a large amount of comments. The default API quota limit ends up")
              print(f" around {F.YELLOW}10,000 comment deletions per day{S.R}. If you find more spam than that you will go over the limit.")
              print(f"        > Read more about the quota limits for this app here: {F.YELLOW}TJoe.io/api-limit-info{S.R}")
              if userNotChannelOwner == False or moderator_mode == True:
                print(f"{F.LIGHTCYAN_EX}> Note:{S.R} You may want to disable 'check_deletion_success' in the config, as this doubles the API cost! (So a 5K limit)")
            confirm = choice("Is this video list correct?", bypass=validConfigSetting)
            if confirm == None:
              return True # Return to main menu

# ============================================================================ RECENT VIDEOS ==========================================================================================================

    elif scanMode == "recentVideos":
      confirm = False
      validEntry = False
      validChannel = False

      while validChannel == False:
        # Get and verify config setting for channel ID
        if config['channel_to_scan'] != 'ask':
          if config['channel_to_scan'] == 'mine':
            channelID = CURRENTUSER.id
            channelTitle = CURRENTUSER.name
            validChannel = True
            break
          else:
            validChannel, channelID, channelTitle = validation.validate_channel_id(config['channel_to_scan'])
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
          validChannel, channelID, channelTitle = validation.validate_channel_id(inputtedChannel)

      if CURRENTUSER.id != channelID:
        userNotChannelOwner = True

      print(f"\nChosen Channel: {F.LIGHTCYAN_EX}{channelTitle}{S.R}")

      # Get number of recent videos to scan, either from config or user input, and validate
      while validEntry == False or confirm == False:
        videosToScan=[]
        validConfigSetting = True
        if config['recent_videos_amount'] != 'ask' and validConfigSetting == True:
          numVideos = config['recent_videos_amount']
          try:
            numVideos = int(numVideos)
          except:
            validConfigSetting = False
            print("Invalid number entered in config file for recent_videos_amount")
            numVideos = None
        else:
          print(f"\nEnter the {F.YELLOW}number of most recent videos{S.R} to scan back-to-back:")
          numVideos = input("\nNumber of Recent Videos: ")
          print("")
          if str(numVideos).lower() == "x":
            return True # Return to main menu
        try:
          numVideos = int(numVideos)
          if numVideos > 0 and numVideos <= 5000:
            validEntry = True
            validConfigSetting = True
          else:
            print("Error: Entry must be from 1 to 5000 (the YouTube API Limit)")
            validEntry = False
            validConfigSetting = False
        except ValueError:
          print(f"{F.LIGHTRED_EX}Error:{S.R} Entry must be a whole number greater than zero.")
          validEntry = False
        if validEntry == True and numVideos >= 1000:
          print(f"\n{B.YELLOW}{F.BLACK} WARNING: {S.R} You have chosen to scan a large amount of videos. With the default API quota limit,")
          print(f" every 1000 videos will use up 20% of the quota {F.YELLOW}just from listing the videos alone, before any comment scanning.{S.R}")
          print(f"        > Read more about the quota limits for this app here: {F.YELLOW}TJoe.io/api-limit-info{S.R}")

        if validEntry == True:
          # Fetch recent videos and print titles to user for confirmation
          videosToScan = operations.get_recent_videos(current, channelID, numVideos)
          if str(videosToScan) == "MainMenu":
            return True # Return to main menu
          if len(videosToScan) == 0:
            print(f"\n{F.LIGHTRED_EX}Error:{S.R} No scannable videos found in selected range!  They all may have no comments and/or are live streams.")
            if config['auto_close'] == True:
              print("Auto-close enabled in config. Exiting in 5 seconds...")
              time.sleep(5)
              sys.exit()
            else:
              input("\nPress Enter to return to main menu...")
              return True

          # Get total comment count
          miscData.totalCommentCount = 0
          for video in videosToScan:
            miscData.totalCommentCount += int(video['commentCount'])

          if len(videosToScan) < numVideos:
            print(f"\n{F.YELLOW} WARNING:{S.R} Only {len(videosToScan)} videos found. Videos may be skipped if there are no comments.")
          print("\nRecent Videos To Be Scanned:")
          for i in range(len(videosToScan)):
            if config['skip_confirm_video'] == False:
              if i == 10 and len(videosToScan) > 11:
                remainingCount = str(len(videosToScan) - 10)
                userChoice = choice(f"There are {remainingCount} more recent videos, do you want to see the rest?")
                if userChoice == False:
                  break
                elif userChoice == None:
                  return True # Return to main menu
            print(f"  {i+1}. {videosToScan[i]['videoTitle']}")

          if config['skip_confirm_video'] == True and validConfigSetting == True:
            confirm = True
          else:
            if userNotChannelOwner == True and moderator_mode == False:
              print(f"{F.LIGHTRED_EX}NOTE: These aren't your videos. Enabling '{F.YELLOW}Not Your Channel Mode{F.LIGHTRED_EX}'. You can report spam comments, but not delete them.{S.R}")
            elif userNotChannelOwner == True and moderator_mode == True:
              print(f"{F.LIGHTRED_EX}NOTE: {F.YELLOW}Moderator Mode is enabled{F.LIGHTRED_EX}. You can hold comments for review when using certain modes{S.R}")
            print("\nTotal number of comments to scan: " + str(miscData.totalCommentCount))
            if miscData.totalCommentCount >= 100000:
              print(f"\n{B.YELLOW}{F.BLACK} WARNING: {S.R} You have chosen to scan a large amount of comments. The default API quota limit ends up")
              print(f" around {F.YELLOW}10,000 comment deletions per day{S.R}. If you find more spam than that you will go over the limit.")
              print(f"        > Read more about the quota limits for this app here: {F.YELLOW}TJoe.io/api-limit-info{S.R}")
              if userNotChannelOwner == True or moderator_mode == True:
                print(f"{F.LIGHTCYAN_EX}> Note:{S.R} You may want to disable 'check_deletion_success' in the config, as this doubles the API cost! (So a 5K limit)")
            confirm = choice("Is everything correct?", bypass=config['skip_confirm_video'])
            if confirm == None:
              return True # Return to main menu

      miscData.channelOwnerID = channelID
      miscData.channelOwnerName = channelTitle

# ============================================================================= ENTIRE CHANNEL ============================================================================================================

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
              if userChoice == None:
                return True # Return to main menu

          if maxScanNumber > 0:
            validInteger = True # If it gets here, it's an integer, otherwise goes to exception
          else:
            print("\nInvalid Input! Number must be greater than zero.")
            validConfigSetting = False
        except:
          print("\nInvalid Input! - Must be a whole number.")
          validConfigSetting = False

      miscData.channelOwnerID = CURRENTUSER.id
      miscData.channelOwnerName = CURRENTUSER.name

# ================================================================================ COMMUNITY POST =====================================================================================================

    elif scanMode == 'communityPost':
      print(f"\nNOTES: This mode is {F.YELLOW}experimental{S.R}, and not as polished as other features. Expect some janky-ness.")
      print("   > It is also much slower to retrieve comments, because it does not use the API")
      confirm = False
      while confirm == False:
        communityPostInput = input("\nEnter the ID or link of the community post: ")
        if str(communityPostInput).lower() == "x":
          return True # Return to main menu
        # Validate post ID or link, get additional info about owner, and useable link
        isValid, communityPostID, postURL, postOwnerID, postOwnerUsername = validation.validate_post_id(communityPostInput)
        if isValid == True:
          print("\nCommunity Post By: " + postOwnerUsername)
          if postOwnerID != CURRENTUSER.id:
            userNotChannelOwner = True
            print(f"\n{F.YELLOW}Warning:{S.R} You are scanning someone else's post. '{F.LIGHTRED_EX}Not Your Channel Mode{S.R}' Enabled.")
          confirm = choice("Continue?")
          if confirm == None:
            return True # Return to main menu
        else:
          print("Problem interpreting the post information, please check the link or ID.")
      miscData.channelOwnerID = postOwnerID
      miscData.channelOwnerName = postOwnerUsername

      # Checking config for max comments in config
      if config['max_comments'] != 'ask':
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
          print("\nInvalid max_comments setting in config! Number must be a whole number greater than zero.")
        while validInteger == False:
          maxScanInput = input(f"\nEnter the maximum {F.YELLOW}number of comments{S.R} to scan: ")
          if str(maxScanInput).lower() == "x":
            return True # Return to main menu
          try:
            maxScanNumber = int(maxScanInput)
            if maxScanNumber > 0:
              validInteger = True # If it gets here, it's an integer, otherwise goes to exception
            else:
              print("\nInvalid Input! Number must be a whole number greater than zero.")
          except:
            print("\nInvalid Input! - Must be a whole number greater than zero.")

# ==================================================================== RECENT COMMUNITY POSTS =============================================================================================================

    # Recent Community Posts
    elif scanMode == 'recentCommunityPosts':
      print(f"\nNOTES: This mode is {F.YELLOW}experimental{S.R}, and not as polished as other features. Expect some janky-ness.")
      print("   > It is also much slower to retrieve comments, because it does not use the API")

      confirm = False
      validEntry = False
      validChannel = False

      while validChannel == False:
        # Get and verify config setting for channel ID
        if config['channel_to_scan'] != 'ask':
          if config['channel_to_scan'] == 'mine':
            channelID = CURRENTUSER.id
            channelTitle = CURRENTUSER.name
            validChannel = True
            break
          else:
            validChannel, channelID, channelTitle = validation.validate_channel_id(config['channel_to_scan'])
            if validChannel == True:
              break
            else:
              print("Invalid Channel ID or Link in config file!")

        print(f"\nEnter a {F.YELLOW}channel ID or Link{S.R} to scan {F.LIGHTCYAN_EX}recent community posts{S.R} from")
        print(f"   > If scanning {F.YELLOW}your own channel{S.R}, just hit {F.LIGHTGREEN_EX}Enter{S.R}")
        inputtedChannel = input("\nEnter Here: ")
        if inputtedChannel == "":
          channelID = CURRENTUSER.id
          channelTitle = CURRENTUSER.name
          validChannel = True
        elif str(inputtedChannel).lower() == "x":
          return True # Return to main menu
        else:
          validChannel, channelID, channelTitle = validation.validate_channel_id(inputtedChannel)

      if CURRENTUSER.id != channelID:
        userNotChannelOwner = True

      # Get and print community posts
      recentPostsListofDicts = community_downloader.fetch_recent_community_posts(channelID)

      print("\n------------------------------------------------------------")
      print(f"Retrieved {F.YELLOW}{len(recentPostsListofDicts)} recent posts{S.R} from {F.LIGHTCYAN_EX}{channelTitle}{S.R}")
      print(f"\n  Post Content Samples:")
      for i in range(len(recentPostsListofDicts)):
        # recentPostsListofDicts = {post id : post text} - Below prints sample of post text
        print(f"    {i+1}.".ljust(9, " ") + f"{list(recentPostsListofDicts[i].values())[0][0:50]}")

      if userNotChannelOwner == True:
              print(f"\n > {F.LIGHTRED_EX}Warning:{S.R} You are scanning someone else's post. {F.LIGHTRED_EX}'Not Your Channel Mode'{S.R} Enabled.")

      print(f"\n{F.YELLOW}How many{S.R} of the most recent posts do you want to scan?")

      inputStr = ""
      while True:
        if config['recent_videos_amount'] != 'ask' and inputStr == "":
          inputStr = config['recent_videos_amount']
        else:
          inputStr = input("\nNumber of Recent Posts: ")
          if str(inputStr).lower() == "x":
            return True

        try:
          numRecentPosts = int(inputStr)
          if numRecentPosts > len(recentPostsListofDicts):
            print("Number entered is more than posts available. Will just scan all posts available.")
            numRecentPosts = len(recentPostsListofDicts)
            break
          elif numRecentPosts <= 0:
            print("Please enter a whole number greater than zero.")
          else:
            break
        except ValueError:
          print("Invalid Input! - Must be a whole number.")

      miscData.channelOwnerID = channelID
      miscData.channelOwnerName = channelTitle

# =============================================================================== OTHER MENU OPTIONS =============================================================================================

    # Create config file
    elif scanMode == "makeConfig":
      result = files.create_config_file(configDict=config)
      if str(result) == "MainMenu":
        return True

    # Check for latest version
    elif scanMode == "checkUpdates":
      files.check_lists_update(spamListDict)
      files.check_for_update(version, updateReleaseChannel)
      files.check_for_filter_update(filterListDict, silentCheck=True)
      input("\nPress Enter to return to main menu...")
      return True

    # Recove deleted comments mode
    elif scanMode == "recoverMode":
      result = modes.recover_deleted_comments(config)
      if str(result) == "MainMenu":
        return True

    elif scanMode == "commentList":
      result = modes.delete_comment_list(config)
      if str(result) == "MainMenu":
        return True

    elif scanMode == "tools":
      result = user_tools.user_tools_menu(config)
      if str(result) == "MainMenu":
        return True

# ====================================================================================================================================================================================================
# ====================================================================================================================================================================================================

    # Set Menu Colors
    autoSmartColor = F.YELLOW
    sensitiveColor = F.YELLOW
    IDColor = F.LIGHTRED_EX
    usernameColor = F.LIGHTBLUE_EX
    textColor = F.CYAN
    usernameTextColor = F.LIGHTBLUE_EX
    asciiColor = F.LIGHTMAGENTA_EX
    styleID = S.BRIGHT
    styleOther = S.BRIGHT
    a1 = ""
    a2 = ""

    # Change menu display & colors of some options depending on privileges
    if userNotChannelOwner:
      styleOther = S.DIM
      a2 = f"{F.LIGHTRED_EX}*{S.R}" # a = asterisk

    if not moderator_mode and userNotChannelOwner:
      styleID = S.DIM
      a1 = f"{F.LIGHTRED_EX}*{S.R}"

    # User inputs filtering mode
    print("\n-------------------------------------------------------")
    print(f"~~~~~~~~~~~ Choose how to identify spammers ~~~~~~~~~~~")
    print("-------------------------------------------------------")
    print(f"{S.BRIGHT} 1. {S.R}{F.BLACK}{B.LIGHTGREEN_EX}(RECOMMENDED):{S.R} {S.BRIGHT}{autoSmartColor}Auto-Smart Mode{F.R}: Automatically detects multiple spammer techniques{S.R}")
    print(f"{S.BRIGHT} 2. {sensitiveColor}Sensitive-Smart Mode{F.R}: Much more likely to catch all spammers, but with significantly more false positives{S.R}")
    print(f"{a1}{styleID} 3. Enter Spammer's {IDColor}channel ID(s) or link(s){F.R}{S.R}")
    print(f"{a2}{styleOther} 4. Scan {usernameColor}usernames{F.R} for criteria you choose{S.R}")
    print(f"{a2}{styleOther} 5. Scan {textColor}comment text{F.R} for criteria you choose{S.R}")
    print(f"{a2}{styleOther} 6. Scan both {usernameTextColor}usernames{F.R} and {textColor}comment text{F.R} for criteria you choose{S.R}")
    print(f"{a2}{styleOther} 7. ASCII Mode: Scan usernames for {asciiColor}ANY non-ASCII special characters{F.R} (May cause collateral damage!){S.R}")


    if userNotChannelOwner == True and moderator_mode == False:
      print(f" {F.LIGHTRED_EX}*Note: With 'Not Your Channel Mode' enabled, you can only report matched comments while using 'Auto-Smart Mode' \n        or 'Sensitive-Smart Mode'.{S.R}") # Based on filterModesAllowedforNonOwners
    elif userNotChannelOwner == True and moderator_mode == True:
      print(f" {F.LIGHTRED_EX}*Note: With 'Moderator Mode', you can Hold and/or Report using: 'Auto-Smart', 'Sensitive-Smart', and Channel ID modes.{S.R}")
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
        print(f"\nInvalid Filter Mode: {filterChoice} - Enter a whole number from 1-7")
        validConfigSetting = False

    ## Get filter sub-mode to decide if searching characters or string
    if config['filter_submode'] != 'ask':
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
      filterSettings = modes.prepare_filter_mode_ID(scanMode, config)
      inputtedSpammerChannelID = filterSettings[0]

    elif filterMode == "AutoASCII":
      filterSettings = modes.prepare_filter_mode_non_ascii(scanMode, config)
      regexPattern = filterSettings[0]

    elif filterMode == "AutoSmart":
      filterSettings = modes.prepare_filter_mode_smart(scanMode, config, miscData)
      inputtedUsernameFilter = filterSettings[0]
      inputtedCommentTextFilter = filterSettings[0]
    elif filterMode == "SensitiveSmart":
      filterSettings = modes.prepare_filter_mode_smart(scanMode, config, miscData, sensitive=True)
      inputtedUsernameFilter = filterSettings[0]
      inputtedCommentTextFilter = filterSettings[0]

    elif filterSubMode == "chars":
      filterSettings = modes.prepare_filter_mode_chars(scanMode, filterMode, config)
    elif filterSubMode == "string":
      filterSettings = modes.prepare_filter_mode_strings(scanMode, filterMode, config)
    elif filterSubMode == "regex":
      filterSettings = modes.prepare_filter_mode_regex(scanMode, filterMode, config)
      regexPattern = filterSettings[0]

    if filterSettings[0] == "MainMenu":
      return True

    if filterMode == "Username":
      inputtedUsernameFilter = filterSettings[0]
    elif filterMode == "Text":
      inputtedCommentTextFilter = filterSettings[0]
    elif filterMode == "NameAndText":
      inputtedUsernameFilter = filterSettings[0]
      inputtedCommentTextFilter = filterSettings[0]

    # Prepare scan mode info dictionary
    if videosToScan:
      current.scannedThingsList = list(item['videoID'] for item in videosToScan)
    elif recentPostsListofDicts:
     current.scannedThingsList = list(list(post.keys())[0] for post in recentPostsListofDicts)[0:numRecentPosts]
    elif postURL:
      current.scannedThingsList = [postURL]
    else:
      current.scannedThingsList = []

    ##################### START SCANNING #####################
    filtersDict = {
      'filterSettings': filterSettings,
      'filterMode': filterMode,
      'filterSubMode': filterSubMode,
      'CustomChannelIdFilter': inputtedSpammerChannelID,
      'CustomUsernameFilter': inputtedUsernameFilter,
      'CustomCommentTextFilter': inputtedCommentTextFilter,
      'CustomRegexPattern': regexPattern
      }

    if scanMode == "communityPost" or scanMode == "recentCommunityPosts":
      def scan_community_post(current, config, communityPostID, limit, postScanProgressDict=None, postText=None):
        authorKeyAllCommentsDict = {}
        allCommunityCommentsDict = get_community_comments(communityPostID=communityPostID, limit=limit, postScanProgressDict=postScanProgressDict, postText=postText)
        retrievedCount = len(allCommunityCommentsDict)
        print(f"\nRetrieved {retrievedCount} comments from post.\n")
        scannedCount = 0
        threadDict = {}

        # Analyze and store comments
        for key, value in allCommunityCommentsDict.items():
          currentCommentDict = {
            'authorChannelID':value['authorChannelID'],
            'parentAuthorChannelID':None,
            'authorChannelName':value['authorName'],
            'commentText':value['commentText'],
            'commentID':key,
            #'originalCommentID': None
            }
          try:
            if value['authorChannelID'] in authorKeyAllCommentsDict:
              authorKeyAllCommentsDict[value['authorChannelID']].append(currentCommentDict)
            else:
              authorKeyAllCommentsDict[value['authorChannelID']] = [currentCommentDict]
          except TypeError: # Try/Except might not be necessary, might remove later
            pass
          operations.check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID=communityPostID)

          # Scam for spam threads
          if (filtersDict['filterMode'] == "AutoSmart" or filtersDict['filterMode'] == "SensitiveSmart") and config['detect_spam_threads'] == True:
            threadDict = operations.make_community_thread_dict(key, allCommunityCommentsDict)
            if threadDict and len(threadDict) > 7: # Only if more than 7 replies
              parentCommentDict = dict(currentCommentDict)
              parentCommentDict['videoID'] = communityPostID
              current = operations.check_spam_threads(current, filtersDict, miscData, config, parentCommentDict, threadDict)
          scannedCount += 1

          # Print Progress
          percent = ((scannedCount / retrievedCount) * 100)
          progressStats = f"[ {str(scannedCount)} / {str(retrievedCount)} ]".ljust(15, " ") + f" ({percent:.2f}%)"
          print(f'  {progressStats}  -  Analyzing Comments For Spam ', end='\r')
        print("                                                                                        ")

        dupeCheckModes = utils.string_to_list(config['duplicate_check_modes'])
        if filtersDict['filterMode'].lower() in dupeCheckModes:
          operations.check_duplicates(current, config, miscData, authorKeyAllCommentsDict, communityPostID)
        # repostCheckModes = utils.string_to_list(config['stolen_comments_check_modes'])
        # if filtersDict['filterMode'].lower() in repostCheckModes:
        #   operations.check_reposts(current, config, miscData, allCommunityCommentsDict, communityPostID)
          print("                                                                                                                       ")

      if scanMode == "communityPost":
        scan_community_post(current, config, communityPostID, maxScanNumber)

      elif scanMode == "recentCommunityPosts":
        postScanProgressDict = {'scanned':0, 'total':numRecentPosts}

        for post in recentPostsListofDicts:
          postScanProgressDict['scanned'] += 1
          id = list(post.keys())[0] # Each dict only has one key/value pair, so makes list of length 1, so id is in index 0
          postText = list(post.values())[0] # Same as above but applies to values
          current.vidTitleDict[id] = f"[Community Post]: {postText}"

          scan_community_post(current, config, id, maxScanNumber, postScanProgressDict=postScanProgressDict, postText=postText)
          if postScanProgressDict['scanned'] == numRecentPosts:
            break

    else:
      # Goes to get comments for first page
      print("\n------------------------------------------------------------------------------")
      print("(Note: If the program appears to freeze, try right clicking within the window)\n")
      print("                          --- Scanning --- \n")

      # ----------------------------------------------------------------------------------------------------------------------
      def scan_video(miscData, config, filtersDict, scanVideoID, videosToScan=None, currentVideoDict=None, videoTitle=None, showTitle=False, i=1):
        if currentVideoDict is None:
          currentVideoDict = {}
        nextPageToken, currentVideoDict = operations.get_comments(current, filtersDict, miscData, config, currentVideoDict, scanVideoID, videosToScan=videosToScan)
        if nextPageToken == "Error":
            return "Error"

        if showTitle == True and len(videosToScan) > 0:
          # Prints video title, progress count, adds enough spaces to cover up previous stat print line
          offset = 95 - len(videoTitle)
          if offset > 0:
            spacesStr = " " * offset
          else:
            spacesStr = ""
          print(f"Scanning {i}/{len(videosToScan)}: " + videoTitle + spacesStr + "\n")

        operations.print_count_stats(current, miscData, videosToScan, final=False)  # Prints comment scan stats, updates on same line
        # After getting first page, if there are more pages, goes to get comments for next page
        while nextPageToken != "End" and current.scannedCommentsCount < maxScanNumber:
          nextPageToken, currentVideoDict = operations.get_comments(current, filtersDict, miscData, config, currentVideoDict, scanVideoID, nextPageToken, videosToScan=videosToScan)
          if nextPageToken == "Error":
            return "Error"
        return "OK"
      # ----------------------------------------------------------------------------------------------------------------------

      if scanMode == "entireChannel":
        status = scan_video(miscData, config, filtersDict, scanVideoID)
        if status == "Error":
          pass

      elif scanMode == "recentVideos" or scanMode == "chosenVideos":
        i = 1
        for video in videosToScan:
          currentVideoDict = {}
          scanVideoID = str(video['videoID'])
          videoTitle = str(video['videoTitle'])
          status = scan_video(miscData, config, filtersDict, scanVideoID, videosToScan=videosToScan, currentVideoDict=currentVideoDict, videoTitle=videoTitle, showTitle=True, i=i)
          if status == "Error":
            break
          i += 1

      if current.errorOccurred == False:
        operations.print_count_stats(current, miscData, videosToScan, final=True)  # Prints comment scan stats, finalizes
      else:
        utils.print_break_finished(scanMode)
    ##########################################################
    bypass = False
    if config['enable_logging'] != 'ask':
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
    if not current.matchedCommentsDict and not current.duplicateCommentsDict and not current.spamThreadsDict and not current.repostedCommentsDict: # If no spam comments found, exits
      print(f"{B.RED}{F.BLACK} No matched comments or users found! {F.R}{B.R}{S.R}\n")
      print(f"If you see missed spam or false positives, you can submit a filter suggestion here: {F.YELLOW}TJoe.io/filter-feedback{S.R}")

      # Can still log to json even though no comments
      if config['json_log_all_comments'] and config['json_log'] and config['enable_logging'] != False:
        print(f"Because you enabled '{F.LIGHTCYAN_EX}json_log_all_comments{S.R}' in config, {F.LIGHTCYAN_EX}continuing on to log anyway{S.R}.")
        jsonSettingsDict = {}
        current, logMode, jsonSettingsDict = logging.prepare_logFile_settings(current, config, miscData, jsonSettingsDict, filtersDict, bypass)
        jsonDataDict = logging.get_extra_json_data([], jsonSettingsDict)
        logging.write_json_log(current, config, jsonSettingsDict, {}, jsonDataDict)

      if config['auto_close'] == False:
        input("\nPress Enter to return to main menu...")
        return True
      elif config['auto_close'] == True:
        print("\nAuto-close enabled in config. Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit()
    print(f"Number of {S.BRIGHT}{F.LIGHTRED_EX}Matched{S.R} Comments Found: {B.RED}{F.WHITE} {str(len(current.matchedCommentsDict))} {F.R}{B.R}{S.R}")
    if current.spamThreadsDict:
      print(f"\nNumber of {S.BRIGHT}{F.RED}Spam Bot Threads{S.R} Found: {S.BRIGHT}{B.RED}{F.WHITE} {str(len(current.spamThreadsDict))} {F.R}{B.R}{S.R}")
    if current.duplicateCommentsDict:
      print(f"\nNumber of {S.BRIGHT}{F.LIGHTBLUE_EX}Non-Matched But Duplicate{S.R} Comments Found: {S.BRIGHT}{F.WHITE}{B.BLUE} {str(len(current.duplicateCommentsDict))} {F.R}{B.R}{S.R}")
    if current.repostedCommentsDict:
      print(f"\nNumber of {S.BRIGHT}{F.LIGHTBLUE_EX}Non-Matched But Stolen & Reposted{S.R} Comments Found: {S.BRIGHT}{F.WHITE}{B.BLUE} {str(len(current.repostedCommentsDict))} {F.R}{B.R}{S.R}")

    # If spam comments were found, continue
    if bypass == False:
      # Asks user if they want to save list of spam comments to a file
      print(f"\nComments ready to display. Also {F.LIGHTGREEN_EX}save a log file?{S.R} {B.GREEN}{F.BLACK} Highly Recommended! {F.R}{B.R}{S.R}")
      print(f"        (It even allows you to {F.LIGHTGREEN_EX}restore{S.R} deleted comments later)")
      loggingEnabled = choice(f"Save Log File (Recommended)?")
      if loggingEnabled == None:
        return True # Return to main menu
      print("")

    # Prepare log file and json log file settings - Location and names
    jsonSettingsDict = {}
    if loggingEnabled == True:
      current, logMode, jsonSettingsDict = logging.prepare_logFile_settings(current, config, miscData, jsonSettingsDict, filtersDict, bypass)
      print("\n-----------------------------------------------------------------------------------------------------------------\n")
    else:
      print("Continuing without logging... \n")
      logMode = None
      jsonSettingsDict['jsonLogging'] = False

    # Prints list of spam comments
    if scanMode == "communityPost":
      scanVideoID = communityPostID

    # Print comments  and write to log files
    logFileContents, logMode = logging.print_comments(current, config, scanVideoID, loggingEnabled, scanMode, logMode)

    print(f"\n{F.WHITE}{B.RED} NOTE: {S.R} Check that all comments listed above are indeed spam.")
    print(f" > If you see missed spam or false positives, you can submit a filter suggestion here: {F.YELLOW}TJoe.io/filter-feedback{S.R}")
    print()

    ### ---------------- Decide whether to skip deletion ----------------
    returnToMenu = False

    # Defaults
    deletionEnabled = False
    deletionMode = None # Should be changed later, but if missed it will default to heldForReview
    confirmDelete = None # If None, will later cause user to be asked to delete
    if moderator_mode == False:
      filterModesAllowedforNonOwners = ["AutoSmart", "SensitiveSmart"]
    elif moderator_mode == True:
      filterModesAllowedforNonOwners = ["AutoSmart", "SensitiveSmart", 'ID']

    # If user isn't channel owner and not using allowed filter mode, skip deletion
    if userNotChannelOwner == True and filterMode not in filterModesAllowedforNonOwners:
      confirmDelete = False
      deletionEnabled = False
      print(f"{F.LIGHTRED_EX}Error:{S.R}To prevent abuse, even in moderator mode, you can only use filter modes: Auto Smart, Sensitive Smart, and ID")
      response = input("Press Enter to Continue, or type 'x' to return to Main Menu...")
      if response.lower() == 'x':
        return True

    # Test skip_deletion preference - If passes both, will either delete or ask user to delete
    if config['skip_deletion'] == True:
      print("\nConfig setting skip_deletion enabled.")
      returnToMenu = True

    elif config['skip_deletion'] != False:
      print("Error Code C-3: Invalid value for 'skip_deletion' in config file. Must be 'True' or 'False'. Current Value:  " + str(config['skip_deletion']))
      print(f"Defaulting to '{F.YELLOW}False{S.R}'")
      input("\nPress Enter to Continue...")

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
        input("\nPress Enter to Exit...")
        sys.exit()

    # User wants to automatically delete with no user intervention
    elif config['delete_without_reviewing'] == True:
      if userNotChannelOwner == True:
          confirmDelete = "report"
          deletionMode = "reportSpam"
          deletionEnabled = True
      elif config['removal_type'] == "reportspam" or config['removal_type'] == "heldforreview":
        if filterMode == "AutoSmart" or filterMode == "ID":
          deletionEnabled = True
          if config['removal_type'] == "reportspam":
            deletionMode = "reportSpam"
            confirmDelete = "report"
          elif config['removal_type'] == "heldforreview":
            deletionMode = "heldForReview"
            confirmDelete = "hold"
        else:
          # If non-permitted filter mode with delete_without_reviewing, will allow deletion, but now warns and requires usual confirmation prompt
          print("Error Code C-5: 'delete_without_reviewing' is set to 'True' in config file. So only filter mode 'AutoSmart' allowed..\n")
          print("Next time use one of those filter modes, or set 'delete_without_reviewing' to 'False'.")
          print("    > For this run, you will be asked to confirm removal of spam comments.")
          input("\nPress Enter to Continue...")
          confirmDelete = None
          deletionEnabled = "Allowed"
      else:
        print("Error Code C-6: 'delete_without_reviewing' is set to 'True' in config file. So 'removal_type' must be either 'heldForReview' or 'reportSpam'.\n")
        print("Next time, either set one of those removal types, or set 'delete_without_reviewing' to 'False'.")
        print("    > For this run, you will be asked to confirm removal of spam comments.")
        input("\nPress Enter to Continue...")
        confirmDelete = None
        deletionEnabled = "Allowed"
    else:
      # Catch Invalid value
      print("Error C-7: Invalid value for 'delete_without_reviewing' in config file. Must be 'True' or 'False':  " + config['delete_without_reviewing'])
      input("\nPress Enter to Exit...")
      sys.exit()

    # Check if deletion is enabled, otherwise block and quit
    if returnToMenu == False and deletionEnabled != "Allowed" and deletionEnabled != True:
        print("\nThe deletion functionality was not enabled. Cannot delete or report comments.")
        print("Possible Cause: You're scanning someone else's video with a non-supported filter mode.\n")
        print(f"If you think this is a bug, you may report it on this project's GitHub page: {F.YELLOW}TJoe.io/bug-report{S.R}")
        if config['auto_close'] == True:
          print("\nAuto-close enabled in config. Exiting in 5 seconds...")
          time.sleep(5)
          sys.exit()
        else:
          input("\nPress Enter to return to main menu...")
          return True

    ### ---------------- Set Up How To Handle Comments  ----------------
    rtfExclude = None
    plaintextExclude = None
    authorsToExcludeSet = set()
    commentIDExcludeSet = set()
    exclude = False
    excludedCommentsDict = {}
    excludeDisplayString = ""
    # If not skipped by config, ask user what to do
    if confirmDelete == None and returnToMenu == False:
      # Menu for deletion mode
      validResponses = ['delete', 'report', 'hold', 'none']
      while confirmDelete == None or confirmDelete.lower() not in validResponses:
        # Title
        if current.errorOccurred == True:
          print(f"\n--- {F.WHITE}{B.RED} NOTE: {S.R} Options limited due to error during scanning ---")
        if exclude == False:
          print(f"{F.YELLOW}How do you want to handle {F.BLACK}{B.YELLOW} ALL {S.R}{F.YELLOW} the listed comments above?{S.R} (Including Non-Matched Duplicates)")
        elif exclude == True:
          print(f"{F.YELLOW}How do you want to handle the rest of the comments (not ones you {F.LIGHTGREEN_EX}excluded{F.YELLOW})?{S.R}")
        if userNotChannelOwner == True and moderator_mode == False:
          print(f"{F.GREEN}~~ Not Your Channel Mode: Only Reporting is Possible ~~{S.R}")
        if userNotChannelOwner == True and moderator_mode == True:
          print(f"{F.GREEN}~~ Moderator Mode: Reporting and Holding for Review is possible ~~{S.R}")

        # Exclude
        if exclude == False:
          print(f" > To {F.LIGHTGREEN_EX}exclude certain authors{S.R}: Type \'{F.LIGHTGREEN_EX}exclude{S.R}\' followed by a list of the numbers (or ranges of #'s) {F.LIGHTMAGENTA_EX}from the sample list{S.R}")
          print("      > Example:  exclude 1, 3-5, 7, 12-15")
          print(f" > To {F.LIGHTGREEN_EX}only process certain authors{S.R}: Type \'{F.LIGHTGREEN_EX}only{S.R}\' followed by a list of the numbers (or ranges of #s) {F.LIGHTMAGENTA_EX}from the sample list{S.R}")
          print("      > Example:  only 1, 3-5, 7, 12-15  --  (Will effectively exclude the 'inverse' of the 'only' selected authors)")

        # Delete & Hold
        if exclude == False:
          if userNotChannelOwner == False and current.errorOccurred == False:
            print(f" > To {F.LIGHTRED_EX}delete ALL of the above comments{S.R}: Type '{F.LIGHTRED_EX}DELETE{S.R}', then hit Enter.")
          if (userNotChannelOwner == False or moderator_mode == True) and current.errorOccurred == False:
            print(f" > To {F.LIGHTRED_EX}move ALL comments above to 'Held For Review' in YT Studio{S.R}: Type '{F.LIGHTRED_EX}HOLD{S.R}', then hit Enter.")
        elif exclude == True:
          if userNotChannelOwner == False and current.errorOccurred == False:
            print(f" > To {F.LIGHTRED_EX}delete the rest of the comments{S.R}: Type '{F.LIGHTRED_EX}DELETE{S.R}', then hit Enter.")
          if (userNotChannelOwner == False or moderator_mode == True) and current.errorOccurred == False:
            print(f" > To {F.LIGHTRED_EX}move rest of comments above to 'Held For Review' in YT Studio{S.R}: Type '{F.LIGHTRED_EX}HOLD{S.R}', then hit Enter.")

        # Report & None
        if current.errorOccurred == False:
          print(f" > To {F.LIGHTCYAN_EX}report the comments for spam{S.R}, type '{F.LIGHTCYAN_EX}REPORT{S.R}'.")
        if loggingEnabled:
          print(f" > To do nothing and {F.YELLOW}only log{S.R}, type '{F.YELLOW}NONE{S.R}'")
        else:
          print(f" > To do {F.YELLOW}nothing{S.R}, type '{F.YELLOW}NONE{S.R}'")

        if config['json_log'] == True and config['json_extra_data'] == True and loggingEnabled:
          print(f"\n{F.WHITE}{B.BLUE} JSON NOTE: {S.R} You must proceed to write the JSON log file, even if you choose nothing")

        # Take Entry
        confirmDelete = input("\n (Not Case Sensitive) Input: ")

        # Process Entry
        if confirmDelete.lower() == "delete" and userNotChannelOwner == False:
          deletionEnabled = True
          deletionMode = "rejected"

        elif confirmDelete.lower() == "hold" and (userNotChannelOwner == False or moderator_mode == True):
          deletionEnabled = True
          deletionMode = "heldForReview"

        elif confirmDelete.lower() == "report":
          deletionEnabled = True
          deletionMode = "reportSpam"

        elif "exclude" in confirmDelete.lower() or "only" in confirmDelete.lower():
          if "exclude" in confirmDelete.lower():
            onlyBool = False

          elif "only" in confirmDelete.lower():
            onlyBool = True

          if loggingEnabled:
            logInfo = {
              'logMode': logMode,
              'logFileContents': logFileContents,
              'jsonSettingsDict': jsonSettingsDict,
              'filtersDict': filtersDict
              }
          else:
            logInfo = None

          # This is very messy for now, will later consolidate the parameters
          current, excludedCommentsDict, authorsToExcludeSet, commentIDExcludeSet, rtfFormattedExcludes, plaintextFormattedExcludes = operations.exclude_authors(current, config, miscData, excludedCommentsDict, authorsToExcludeSet, commentIDExcludeSet, excludeDisplayString, inputtedString=confirmDelete, logInfo=logInfo, only=onlyBool)
          miscData.resources['Whitelist']['WhitelistContents'] = files.ingest_list_file(whitelistPathWithName, keepCase=True)
          exclude = True

          # Check that remaining comments list to remove is not empty
          if not current.matchedCommentsDict and not current.duplicateCommentsDict and not current.spamThreadsDict and not current.repostedCommentsDict:
            print(f"\n{F.YELLOW}All authors excluded, no comments left to remove!{S.R}")
            input("\nPress Enter to log and/or return to main menu...")
            returnToMenu = True
            break

        elif confirmDelete.lower() == "none":
          returnToMenu = True

        else:
          print(f"\n{F.LIGHTRED_EX}ERROR:{S.R} This entry was invalid or not allowed with current settings: {confirmDelete}")
          input("\nPress Enter to try again...")
          print("\n")

    # Combine commentIDs from different match type dicts
    combinedCommentDict = dict(current.matchedCommentsDict)
    combinedCommentDict.update(current.duplicateCommentsDict)
    combinedCommentDict.update(current.spamThreadsDict)
    combinedCommentDict.update(current.repostedCommentsDict)
    includeOtherAuthorComments = False

    banChoice = False
    if returnToMenu == False:
      # Set deletion mode friendly name
      if deletionMode == "rejected":
        deletionModeFriendlyName = "Removed"
      elif deletionMode == "heldForReview":
        deletionModeFriendlyName = "Moved to 'Held for Review' Section"
      elif deletionMode == "reportSpam":
        deletionModeFriendlyName = "Reported for spam"

      # Set or choose ban mode, check if valid based on deletion mode
      if (deletionMode == "rejected" or deletionMode == "reportSpam" or deletionMode == "heldForReview") and deletionEnabled == True and current.errorOccurred == False:
        proceedWithDeletion = True
        if config['enable_ban'] != "ask":
          if config['enable_ban'] == False:
            pass
          elif config['enable_ban'] == True:
            print("Error Code C-8: 'enable_ban' is set to 'True' in config file. Only possible config options are 'ask' or 'False' when using config.\n")
            input("Press Enter to Continue...")
          else:
            print("Error Code C-9: 'enable_ban' is set to an invalid value in config file. Only possible config options are 'ask' or 'False' when using config.\n")
            input("Press Enter to Continue...")
        elif deletionMode == "rejected":
          print("\nAlso ban the spammer(s)?")
          banChoice = choice(f"{F.YELLOW}Ban{S.R} the spammer(s) ?")
          if banChoice == None:
            banChoice = False
            returnToMenu = True
            includeOtherAuthorComments = False

        if deletionMode == "rejected" or deletionMode == "heldForReview":
          if config['remove_all_author_comments'] != 'ask':
            includeOtherAuthorComments = config['remove_all_author_comments']
          else:
            print(f"\nAlso remove {F.YELLOW}all other comments{S.R} from the selected authors, even if their other comments weren't matched?")
            includeOtherAuthorComments = choice("Choose:")
        else:
          includeOtherAuthorComments = False

      else:
        proceedWithDeletion = False
        deletionModeFriendlyName="Nothing (Log Only)"
    else:
      proceedWithDeletion = False
      deletionModeFriendlyName="Nothing (Log Only)"

    # Print Final Logs
    if includeOtherAuthorComments == True:
      current = operations.get_all_author_comments(current, config, miscData, current.allScannedCommentsDict)
      combinedCommentDict.update(current.otherCommentsByMatchedAuthorsDict)

    if loggingEnabled == True:
      # Rewrites the contents of entire file, but now without the excluded comments in the list of comment IDs
      # Also if other non-matched comments by matched authors were added
      if exclude == True or current.otherCommentsByMatchedAuthorsDict:
        # This is just to redo the logFileContents to write later, not to actually write to log file
        logFileContents, logMode = logging.print_comments(current, config, scanVideoID, loggingEnabled, scanMode, logMode, doWritePrint=False)

        # Update logFile Contents after updating them
        logInfo = {
          'logMode': logMode,
          'logFileContents': logFileContents,
          'jsonSettingsDict': jsonSettingsDict,
          'filtersDict': filtersDict 
          }
        logging.rewrite_log_file(current, logInfo, combinedCommentDict)
      print("Updating log file, please wait...", end="\r")

      # Appends the excluded comment info to the log file that was just re-written
      if exclude == True:
        if logInfo['logMode'] == "rtf":
          logging.write_rtf(current.logFileName, str(rtfFormattedExcludes))
        elif logInfo['logMode'] == "plaintext":
          logging.write_plaintext_log(current.logFileName, str(plaintextFormattedExcludes))
      print("                                          ")

      print(" Finishing Log File...", end="\r")
      logging.write_log_completion_summary(current, exclude, logMode, banChoice, deletionModeFriendlyName, includeOtherAuthorComments)
      print("                               ")

      # Write Json Log File
      if config['json_log'] == True and loggingEnabled and (current.matchedCommentsDict or current.duplicateCommentsDict or current.spamThreadsDict or current.repostedCommentsDict):
        print("\nWriting JSON log file...")
        if config['json_extra_data'] == True:
          if current.errorOccurred == False:
            jsonDataDict = logging.get_extra_json_data(list(current.matchSamplesDict.keys()), jsonSettingsDict)
            logging.write_json_log(current, config, jsonSettingsDict, combinedCommentDict, jsonDataDict)
          else:
            print(f"\n{F.LIGHTRED_EX}NOTE:{S.R} Extra JSON data collection disabled due to error during scanning")
        else:
          logging.write_json_log(current, config, jsonSettingsDict, combinedCommentDict)
        if returnToMenu == True:
          print("\nJSON Operation Finished.")
    ### ---------------- Reporting / Deletion Begin  ----------------
    if returnToMenu == False:
      if proceedWithDeletion == True:
        operations.delete_found_comments(list(combinedCommentDict), banChoice, deletionMode)
        if deletionMode != "reportSpam":
          if config['check_deletion_success'] == True:
            operations.check_deleted_comments(list(combinedCommentDict))
          elif config['check_deletion_success'] == False:
            print("\nSkipped checking if deletion was successful.\n")

      if config['auto_close'] == True:
        print("\nProgram Complete.")
        print("Auto-close enabled in config. Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit()
      else:
        input(f"\nProgram {F.LIGHTGREEN_EX}Complete{S.R}. Press Enter to return to main menu...")
        return True
    elif current.errorOccurred == True:
      if config['auto_close'] == True:
        print("Deletion disabled due to error during scanning. Auto-close enabled in config. Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit()
      else:
        input(f"\nDeletion disabled due to error during scanning. Press Enter to return to main menu...")
        return True

    elif config['skip_deletion'] == True:
      if config['auto_close'] == True:
        print("\nDeletion disabled in config file.")
        print("Auto-close enabled in config. Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit()
      else:
        if confirmDelete != None and str(confirmDelete.lower()) == "none":
          input(f"\nDeletion {F.LIGHTCYAN_EX}Declined{S.R}. Press Enter to return to main menu...")
        else:
          input(f"\nDeletion {F.LIGHTRED_EX}Cancelled{S.R}. Press Enter to return to main menu...")
        return True
    else:
      if config['auto_close'] == True:
        print("Deletion Cancelled. Auto-close enabled in config. Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit()
      else:
        input(f"\nDeletion {F.LIGHTRED_EX}Cancelled{S.R}. Press Enter to return to main menu...")
        return True
  # -------------------------------------------------------------------------------------------------------------------------------------------------
  # ------------------------------------------------END PRIMARY INSTANCE-----------------------------------------------------------------------------
  # -------------------------------------------------------------------------------------------------------------------------------------------------

  # Loops Entire Program to Main Menu
  continueRunning = True
  while continueRunning == True:
    continueRunning = primaryInstance(miscData)


# Runs the program
if __name__ == "__main__":
#   #For speed testing

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


# -------------------------------------------------------------------------------------------------------------------------------------------------
  print("Running Main Program...")
  try:
    #remind()
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
          utils.print_exception_reason(reason)
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
      print(f"please post a {F.LIGHTYELLOW_EX}bug report{S.R} on the GitHub issues page, and include the above error info.")
    print(f"Short Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
    input("\n Press Enter to Exit...")
  except TypeError:
    traceback.print_exc()
    print("------------------------------------------------")
    print(f"{F.RED}Unknown Error - Code: X-5{S.R} occurred. This is {F.YELLOW}probably my fault{S.R},")
    print(f"please post a {F.LIGHTYELLOW_EX}bug report{S.R} on the GitHub issues page, and include the above error info.")
    print(f"Short Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
    input("\n Press Enter to Exit...")
  except KeyboardInterrupt:
    print("\n\nProcess Cancelled via Keyboard Shortcut")
    sys.exit()
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
