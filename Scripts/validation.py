#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Scripts.shared_imports import *
import Scripts.auth as auth
import Scripts.utils as utils

from urllib.parse import urlparse
from Scripts.community_downloader import get_post_channel_url

import codecs

##################################### VALIDATE VIDEO ID #####################################
# Regex matches putting video id into a match group. Then queries youtube API to verify it exists - If so returns true and isolated video ID
def validate_video_id(video_url_or_id, silent=False, pass_exception=False, basicCheck=False):
    youtube_video_link_regex = r"^\s*(?P<video_url>(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube\.com|youtu.be)(?:\/(?:[\w\-]+\?v=|embed\/|v\/)?))?(?P<video_id>[\w\-]{11})(?:(?(video_url)\S+|$))?\s*$"
    match = re.match(youtube_video_link_regex, video_url_or_id)
    if match == None:
      if basicCheck == True:
        return False
      if silent == False:
        if ("youtube.com" in video_url_or_id or "youtu.be" in video_url_or_id) and "?v=" not in video_url_or_id:
          print(f"\n{B.RED}{F.BLACK}Invalid Video link!{S.R} Did you accidentally enter a channel link (or something else) instead of a video link?")
        elif ("youtube.com" in video_url_or_id or "youtu.be" in video_url_or_id):
          print(f"\n{B.RED}{F.BLACK}Invalid Video link!{S.R} Check that you copied it correctly. It should look something like \"youtube.com/watch?v=whatever-ID\" where 'whatever-ID' is 11 characters long.")
        else:
          print(f"\n{B.RED}{F.BLACK}Invalid Video link or ID!{S.R} Video IDs are 11 characters long.")
      return False, None, None, None, None
    elif basicCheck == True:
      possibleVideoID = match.group('video_id')
      if len(possibleVideoID) == 11:
        return True
    else:
      try:
        possibleVideoID = match.group('video_id')
        result = auth.YOUTUBE.videos().list(
          part="snippet,id,statistics",
          id=possibleVideoID,
          fields='items/id,items/snippet/channelId,items/snippet/channelTitle,items/statistics/commentCount,items/snippet/title',
          ).execute()

        # Checks if video exists but is unavailable
        if result['items'] == []:
          print(f"\n{B.RED}{F.WHITE} ERROR: {S.R} {F.RED}No info returned for ID: {S.R} {possibleVideoID} {F.LIGHTRED_EX} - Video may be unavailable or deleted.{S.R}")
          return False, None, None, None, None

        if possibleVideoID == result['items'][0]['id']:
          channelID = result['items'][0]['snippet']['channelId']
          channelTitle = result["items"][0]["snippet"]["channelTitle"]
          videoTitle = result["items"][0]["snippet"]["title"]
          # When comments are disabled, the commentCount is not included in the response, requires catching KeyError
          try:
            commentCount = result['items'][0]['statistics']['commentCount']
          except KeyError:
            if pass_exception == True:
              # If the video has comments disabled, the commentCount is not included in the response, but the video is still valid
              return True, possibleVideoID, videoTitle, "0", channelID, channelTitle

            traceback.print_exc()
            print("--------------------------------------")
            print(f"\n{B.RED}{F.WHITE} ERROR: {S.R} {F.RED}Unable to get comment count for video: {S.R} {possibleVideoID}  |  {videoTitle}")
            print(f"\n{F.YELLOW}Are comments disabled on this video?{S.R} If not, please report the bug and include the error info above.")
            print(f"                    Bug Report Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
            input("\nPress Enter to return to the main menu...")
            return "MainMenu", "MainMenu", "MainMenu", "MainMenu", "MainMenu"
            

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
      response = auth.YOUTUBE.search().list(part="snippet",q=customURL, maxResults=1, type="channel").execute()
      if response.get("items"):
        isolatedChannelID = response.get("items")[0]["snippet"]["channelId"] # Get channel ID from custom channel URL username
      else:
        print(f"\n{F.LIGHTRED_EX}No Channel Found!{S.R} YouTube returned no results for that channel. Try entering the @handle instead.")
        return False, None, None
  
  # Handle legacy style custom URL (no /c/ for custom URL)
  elif not any(x in inputted_channel for x in notChannelList) and (inputted_channel.lower().startswith("youtube.com/") or str(urlparse(inputted_channel).hostname).lower() in ["youtube.com", "www.youtube.com"]):
    startIndex = inputted_channel.rindex("/") + 1
    endIndex = len(inputted_channel)

    if startIndex < endIndex and endIndex <= len(inputted_channel):
      customURL = inputted_channel[startIndex:endIndex]
      # First check if actually video ID (video ID regex expression from: https://webapps.stackexchange.com/a/101153)
      if re.match(r'[0-9A-Za-z_-]{10}[048AEIMQUYcgkosw]', customURL):
        print(f"{F.LIGHTRED_EX}Invalid Channel ID / Link!{S.R} Did you enter a video ID / link by mistake?")
        return False, None, None

      response = auth.YOUTUBE.search().list(part="snippet",q=customURL, maxResults=1, type="channel").execute()
      if response.get("items"):
        isolatedChannelID = response.get("items")[0]["snippet"]["channelId"] # Get channel ID from custom channel URL username
      else:
        print(f"\n{F.LIGHTRED_EX}No Channel Found!{S.R} YouTube returned no results for that channel. Try entering the @handle instead.")
        return False, None, None
  
  # Check if new "handle" identifier is used
  elif inputted_channel.lower().startswith("@"):
    # Check for handle validity: Only letters and numbers, periods, underscores, and hyphens, and between 3 and 30 characters
    if re.match(r'^[a-zA-Z0-9._-]{3,30}$', inputted_channel[1:]):
      # Does a search for the handle and gets the channel ID from first response
      response = auth.YOUTUBE.search().list(part="snippet",q=inputted_channel, maxResults=1, type="channel").execute()
      if response.get("items"):
        isolatedChannelID = response.get("items")[0]["snippet"]["channelId"]
      else:
        print(f"\n{F.LIGHTRED_EX}No Channel Found!{S.R} YouTube returned no results for that channel. Double check it is correct, or try entering the Channel ID.")
        return False, None, None
    else:
      print(f"\n{B.RED}{F.BLACK}Error:{S.R} You appear to have entered an invalid handle! It must be between 3 and 30 characters long and only contain letters, numbers, periods, underscores, and hyphens.")
      return False, None, None


  # Channel ID regex expression from: https://webapps.stackexchange.com/a/101153
  elif re.match(r'UC[0-9A-Za-z_-]{21}[AQgw]', inputted_channel):
    isolatedChannelID = inputted_channel

  else:
    print(f"\n{B.RED}{F.BLACK}Error:{S.R} Invalid Channel link or ID!")
    return False, None, None

  if len(isolatedChannelID) == 24 and isolatedChannelID[0:2] == "UC":
    response = auth.YOUTUBE.channels().list(part="snippet", id=isolatedChannelID).execute()
    if response.get('items'):
      channelTitle = response['items'][0]['snippet']['title']
      return True, isolatedChannelID, channelTitle
    else:
      print(f"{F.LIGHTRED_EX}Error{S.R}: Unable to Get Channel Title. Please check the channel ID.")
      return False, None, None

  else:
    print(f"\n{B.RED}{F.BLACK}Invalid Channel link or ID!{S.R} Channel IDs are 24 characters long and begin with 'UC'.")
    return False, None, None

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


############################# VALIDATE CONFIG SETTINGS #############################
def validate_config_settings(config):

  print("\nValidating Config Settings...")
  print("-----------------------------------------------------\n")

  # Helper Functions
  def print_quit_and_report():
    print(f"\nIf you think this is a bug or can't figure it out, report it on the GitHub page:  {F.YELLOW}TJoe.io/bug-report{S.R}")
    input("\nPress Enter to exit...")
    sys.exit()

  def print_int_fail(setting, value):
    print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting '{setting}': {str(value)}")
    print("It must be a whole number greater than zero, or another possible value listed in the config for that setting.")
    print_quit_and_report()

  # Validation Functions
  # --------------------------------------------------------------------------------------
  def simple_settings_check(setting, value):
    if setting in validSettingsDict:
      # A None value means it can be any string
      if validSettingsDict[setting] == None:
        return True

      # For settings that accept more than one value, check each
      elif isinstance(value, str) and "," in str(value):
        try:
          settingList = utils.string_to_list(value)
          for settingValue in settingList:
            if settingValue not in validSettingsDict[setting]:
              print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting '{setting}': {str(value)}")
              print(f"It looks like you tried to enter a list. Check if that setting accepts multiple values or if you entered an invalid value.")
              print_quit_and_report()
          return True
        except:
          print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting '{setting}': {str(value)}")
          print("It looks like you tried to enter a list. Check if that setting accepts multiple values or if you entered an invalid value.")
          print_quit_and_report()

      elif value in validSettingsDict[setting]:
        return True
      else:
        print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting '{setting}': {str(value)}")
        print("Check the config file to see valid possible values for that setting.")
        print_quit_and_report()
    else:
      return None

  def validate_levenshtein(value, *args):
    try:
      value = float(value)
      if value >= 0.0 and value <= 1.0:
        return True
      else:
        print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting 'levenshtein_distance': {str(value)}")
        print("It must be a number from 0 to 1!")
        print_quit_and_report()
    except:  
      print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting 'levenshtein_distance': {str(value)}")
      print("It must be a number from 0 to 1!")
      print_quit_and_report()

  def validate_directory(path, settingName):
    if settingName == 'log_path' and path == 'logs':
      return True
    elif settingName == 'configs_path' and path == 'configs':
      return True
    elif os.path.isdir(path):
      return True
    else:
      print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting '{settingName}': {str(path)}")
      print("Make sure the folder exists!")
      print_quit_and_report()
  
  def validate_encoding(value, *args):
    try:
      codecs.lookup(value)
      return True
    except LookupError:
      print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting 'json_encoding': {str(value)}")
      print("Make sure the encoding is valid!")
      print_quit_and_report()

  def validate_videos_to_scan(value, *args):
    if value == 'ask':
      return True
    else:
      try:
        videoList = utils.string_to_list(value)
      except:
        print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting 'videos_to_scan': {str(value)}")
        print("Make sure it is either a single video ID / Link, or a comma separated list of them!")
        print_quit_and_report()
      if len(videoList) > 0:
        for video in videoList:
          if not validate_video_id(video, basicCheck=True):
            print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} There appears to be an invalid video ID or Link in setting 'videos_to_scan': {str(value)}")
            print_quit_and_report()
        return True
      else:
        print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting 'videos_to_scan' (it may be empty!): {str(value)}")
        print("Make sure it is either a single video ID / Link, or a comma separated list of them!")
        print_quit_and_report()

  def validate_channel_to_scan(value, *args):
    if value == 'ask' or value == 'mine':
      return True
    else:
      result, channelID, channelName = validate_channel_id(value)
      if result == False:
        print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Config setting for 'channel_to_scan' appears invalid: {str(value)}")
        print("Make sure it is either a single channel ID or channel link.  If it's a link, try using the channel ID instead.")
        print_quit_and_report()
      else:
        return True

  def validate_channel_ids_to_filter(value, *args):
    if value == 'ask':
      return True
    else:
      try:
        channelList = utils.string_to_list(value)
      except:
        print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting 'channel_ids_to_filter': {str(value)}")
        print("Make sure it is either a single channel ID / Link, or a comma separated list of them!")
        print_quit_and_report()
      for channel in channelList:
        if len(channel) != 24 or channel[0:2] != "UC":
          print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} There appears to be an invalid channel ID in setting 'channel_ids_to_filter': {str(value)}")
          print("A channel ID must be 24 characters long and begin with 'UC'!")
          print_quit_and_report()
      return True
  
  def validate_chars(value, *args):
    if value == 'ask':
      return True
    result = utils.make_char_set(value, stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=True)
    if result:
      return True
    else:
      print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting 'characters_to_filter': {str(value)}")
      print("For this mode, numbers, letters, and punctuation are removed. But there were no characters left to search!")
      print_quit_and_report()

  def validate_strings(value, *args):
    if value == 'ask':
      return True
    try:
      result = utils.string_to_list(value)
      if len(result) > 0:
        return True
      else:
        print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting 'strings_to_filter': {str(value)}")
        print("The list appears empty! Make sure it is either a single string, or a comma separated list of them!")
        print_quit_and_report()
    except:
      print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} Invalid value for config setting 'strings_to_filter': {str(value)}")
      print("Make sure it is either a single string, or a comma separated list of them!")
      print_quit_and_report()
  
  def validate_regex_setting(value, *args):
    if value == 'ask':
      return True
    isValid, expression = validate_regex(value)
    if isValid:
      return True
    else:
      print(f"\n{B.RED}{F.WHITE} ERROR! {S.R}The config setting 'regex_to_filter' does not appear to be valid: {str(value)}")
      print("Make sure it is a valid regular expression! Example:  [^\x00-\xFF]")
      print("You can test them out on websites like regex101.com")
      print_quit_and_report()
            
  # --------------------------------------------------------------------------------------      

  validSettingsDict = {
    'use_this_config': (True, False, 'ask'),
    'this_config_description': None,
    #'configs_path': None
    'your_channel_id': None, # None because will be checked right away anyway
    'auto_check_update': (True, False),
    'release_channel': ('all', 'stable'),
    'skip_confirm_video': (True, False),
    'moderator_mode': (True, False),
    'auto_close': (True, False),
    'colors_enabled': (True, False),
    'scan_mode': ('ask', 'chosenvideos', 'recentvideos', 'entirechannel', 'communitypost', 'recentcommunityposts'),
    'max_comments': ('ask'), #
    #'videos_to_scan': None,
    #'channel_to_scan': None,
    'recent_videos_amount': ('ask'), #
    'filter_mode': ('ask', 'id', 'username', 'text', 'nameandtext', 'autoascii', 'autosmart', 'sensitivesmart'),
    'filter_submode': ('ask', 'characters', 'strings', 'regex'),
    #'channel_ids_to_filter': None,
    'autoascii_sensitivity': ('ask', '1', '2', '3'),
    #'characters_to_filter': None,
    #'strings_to_filter': None,
    #'regex_to_filter': None,
    'detect_link_spam': (True, False),
    'detect_sub_challenge_spam': (True, False),
    'detect_spam_threads': (True, False),
    'duplicate_check_modes': ('none', 'id', 'username', 'text', 'nameandtext', 'autoascii', 'autosmart', 'sensitivesmart'),
    'stolen_comments_check_modes': ('none', 'id', 'username', 'text', 'nameandtext', 'autoascii', 'autosmart', 'sensitivesmart'),
    #'levenshtein_distance': (),
    #'minimum_duplicates': None,
    #'minimum_duplicate_length'
    'fuzzy_stolen_comment_detection': (True, False),
    'skip_deletion': (True, False),
    'delete_without_reviewing': (True, False),
    'enable_ban': ('ask', False),
    'remove_all_author_comments': ('ask', True, False),
    'removal_type': ('rejected', 'heldforreview', 'reportspam'),
    'whitelist_excluded': ('ask', True, False),
    'check_deletion_success':(True, False),
    'enable_logging': ('ask', True, False),
    #'log_path': None,
    'log_mode': ('rtf', 'plaintext'),
    'json_log': (True, False),
    #'json_encoding': None,
    'json_extra_data': (True, False),
    'json_log_all_comments': (True, False),
    'json_profile_picture': (False, 'default', 'medium', 'high'),
    #'quota_limit': (),
    #'config_version': (),
  }

  # Settings that can or must contain an integer
  integerSettings = ['max_comments', 'recent_videos_amount', 'minimum_duplicates', 'quota_limit', 'config_version', 'stolen_minimum_text_length', 'minimum_duplicate_length']

  # Dictionary of settings requiring specific checks, and the functions to validate them
  specialCheck = {
    'levenshtein_distance': validate_levenshtein,
    'log_path': validate_directory,
    'configs_path': validate_directory,
    'json_encoding': validate_encoding,
    'videos_to_scan': validate_videos_to_scan,
    'channel_to_scan': validate_channel_to_scan,
    'channel_ids_to_filter': validate_channel_ids_to_filter,
    'characters_to_filter': validate_chars,
    'strings_to_filter': validate_strings,
    'regex_to_filter': validate_regex_setting
    }

  # Checks all settings in the config file to ensure they are valid
  for settingName, settingValue in config.items():
    if settingValue == None or settingValue == '':
      print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} The config setting '{settingName}' appears empty!")
      print("Please go and add a valid setting value!")
      print_quit_and_report()

    # Check integer value settings
    if settingName in integerSettings:
      if settingValue != 'ask':
        try:
          int(settingValue)
        except ValueError:
          # Check if there is another valid value besides an integer
          if simple_settings_check(settingName, settingValue) == True:
            continue
          else:
            print_int_fail(settingName, settingValue)
        if int(settingValue) <= 0:
          print_int_fail(settingName, settingValue)
      else:
        # Check if 'ask' is a valid value
        if simple_settings_check(settingName, settingValue) == True:
          continue
        else:
          print_int_fail(settingName, settingValue)

    elif settingName in specialCheck:
      if specialCheck[settingName](settingValue, settingName) == True:
        continue

    # Check simple value settings
    else:
      result = simple_settings_check(settingName, settingValue)
      if result == True:
        continue
      elif result == None:
        print(f"\n{B.RED}{F.WHITE} WARNING! {S.R} An unknown setting was found:  '{settingName}': {str(settingValue)}")
        print(f"If you didn't add or change this setting in the config file, a validation check was probably forgotten to be created!")
        print(f"Consider reporting it: {F.YELLOW}TJoe.io/bug-report{S.R}")
        input(f"\n It might not cause an issue, so press Enter to Continue anyway...")
        continue
  

  # Checks to see if any settings are missing from the config file
  allSettingsDict = []
  allSettingsDict.extend(validSettingsDict.keys())
  allSettingsDict.extend(specialCheck.keys())
  allSettingsDict.extend(integerSettings)

  for settingName in allSettingsDict:
    if settingName not in list(config.keys()):
      print(f"\n{B.RED}{F.WHITE} ERROR! {S.R} The config setting '{settingName}' is missing from the config file!")
      print(" > Did you remove it or are you using an old config file? (It should have auto-updated)")
      print(" > You may need to delete and regenerate the config file.")
      print_quit_and_report()
