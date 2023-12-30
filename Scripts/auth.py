#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Scripts.shared_imports import *
import Scripts.validation as validation

# Google Authentication Modules
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from json import JSONDecodeError

TOKEN_FILE_NAME = 'token.pickle'

YOUTUBE = None
CURRENTUSER = None

def initialize():
  pass

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
  global YOUTUBE
  CLIENT_SECRETS_FILE = 'client_secrets.json'
  YOUTUBE_READ_WRITE_SSL_SCOPE = ['https://www.googleapis.com/auth/youtube.force-ssl']
  API_SERVICE_NAME = 'youtube'
  API_VERSION = 'v3'
  DISCOVERY_SERVICE_URL = "https://youtube.googleapis.com/$discovery/rest?version=v3" # If don't specify discovery URL for build, works in python but fails when running as EXE

  # Check if client_secrets.json file exists, if not give error
  if not os.path.exists(CLIENT_SECRETS_FILE):
    # In case people don't have file extension viewing enabled, they may add a redundant json extension
    if os.path.exists(f"{CLIENT_SECRETS_FILE}.json"):
      CLIENT_SECRETS_FILE = CLIENT_SECRETS_FILE + ".json"
    else:
      print(f"\n         ----- {F.WHITE}{B.RED}[!] Error:{S.R} client_secrets.json file not found -----")
      print(f" ----- Did you create a {F.YELLOW}Google Cloud Platform Project{S.R} to access the API? ----- ")
      print(f"  > For instructions on how to get an API key, visit: {F.YELLOW}TJoe.io/api-setup{S.R}")
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
  YOUTUBE = build(API_SERVICE_NAME, API_VERSION, credentials=creds, discoveryServiceUrl=DISCOVERY_SERVICE_URL, cache_discovery=False, cache=None)
  return YOUTUBE


def first_authentication():
  global YOUTUBE
  try:
    YOUTUBE = get_authenticated_service() # Create authentication object
  except JSONDecodeError as jx:
    print(f"{F.WHITE}{B.RED} [!!!] Error: {S.R}" + str(jx))
    print(f"\nDid you make the client_secrets.json file yourself by {F.LIGHTRED_EX}copying and pasting into it{S.R}, instead of {F.LIGHTGREEN_EX}downloading it{S.R}?")
    print(f"You need to {F.YELLOW}download the json file directly from the Google Cloud dashboard{S.R} as shown in the instructions.")
    print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
    input("Press Enter to Exit...")
    sys.exit()
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
      input(f"\nError Code A-1: {F.RED}Something went wrong during authentication.{S.R} {F.YELLOW}Try deleting the token.pickle file.{S.R} \nPress Enter to Exit...")
      sys.exit()
  return YOUTUBE


############################# GET CURRENTLY LOGGED IN USER #####################################
# Class for custom exception to throw if a comment if invalid channel ID returned
class ChannelIDError(Exception):
    pass
# Get channel ID and channel title of the currently authorized user
def get_current_user(config):

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
    print("> You are logging in with a Google Account that does not have a YouTube channel created yet.")
    print("> When choosing the account to log into, you selected the option showing the Google Account's email address, which might not have a channel attached to it.")
    input("\nPress Enter to try logging in again...")
    os.remove(TOKEN_FILE_NAME)

    global YOUTUBE
    YOUTUBE = get_authenticated_service()
    results = fetch_user() # Try again

  try:
    channelID = results["items"][0]["id"]
    IDCheck = validation.validate_channel_id(channelID)
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
  elif config['your_channel_id'] == "ask":
    configMatch = None
  elif validation.validate_channel_id(config['your_channel_id'])[0] == True:
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


def remove_token():
  os.remove(TOKEN_FILE_NAME)
