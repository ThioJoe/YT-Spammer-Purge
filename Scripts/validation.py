#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Scripts.shared_imports import *
import Scripts.auth as auth

from urllib.parse import urlparse
from Scripts.community_downloader import get_post_channel_url

##################################### VALIDATE VIDEO ID #####################################
# Regex matches putting video id into a match group. Then queries youtube API to verify it exists - If so returns true and isolated video ID
def validate_video_id(video_url_or_id, silent=False, pass_exception=False):
    youtube_video_link_regex = r"^\s*(?P<video_url>(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube\.com|youtu.be)(?:\/(?:[\w\-]+\?v=|embed\/|v\/)?))?(?P<video_id>[\w\-]{11})(?:(?(video_url)\S+|$))?\s*$"
    match = re.match(youtube_video_link_regex, video_url_or_id)
    if match == None:
      if silent == False:
        print(f"\n{B.RED}{F.BLACK}Invalid Video link or ID!{S.R} Video IDs are 11 characters long.")
      return False, None, None, None, None
    else:
      try:
        possibleVideoID = match.group('video_id')
        result = auth.YOUTUBE.videos().list(
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
      response = auth.YOUTUBE.search().list(part="snippet",q=customURL, maxResults=1).execute()
      if response.get("items"):
        isolatedChannelID = response.get("items")[0]["snippet"]["channelId"] # Get channel ID from custom channel URL username
  
  # Handle legacy style custom URL (no /c/ for custom URL)
  elif not any(x in inputted_channel for x in notChannelList) and (inputted_channel.lower().startswith("youtube.com/") or str(urlparse(inputted_channel).hostname).lower() == "youtube.com"):
    startIndex = inputted_channel.rindex("/") + 1
    endIndex = len(inputted_channel)

    if startIndex < endIndex and endIndex <= len(inputted_channel):
      customURL = inputted_channel[startIndex:endIndex]
      # First check if actually video ID (video ID regex expression from: https://webapps.stackexchange.com/a/101153)
      if re.match(r'[0-9A-Za-z_-]{10}[048AEIMQUYcgkosw]', customURL):
        print(f"{F.LIGHTRED_EX}Invalid Channel ID / Link!{S.R} Did you enter a video ID / link by mistake?")
        return False, None, None

      response = auth.YOUTUBE.search().list(part="snippet",q=customURL, maxResults=1).execute()
      if response.get("items"):
        isolatedChannelID = response.get("items")[0]["snippet"]["channelId"] # Get channel ID from custom channel URL username

  # Channel ID regex expression from: https://webapps.stackexchange.com/a/101153
  elif re.match(r'UC[0-9A-Za-z_-]{21}[AQgw]', inputted_channel):
    isolatedChannelID = inputted_channel

  else:
    print(f"\n{B.RED}{F.BLACK}Error:{S.R} Invalid Channel link or ID!")
    return False, None, None

  if len(isolatedChannelID) == 24 and isolatedChannelID[0:2] == "UC":
    response = auth.YOUTUBE.channels().list(part="snippet", id=isolatedChannelID).execute()
    if response['items']:
      channelTitle = response['items'][0]['snippet']['title']
      return True, isolatedChannelID, channelTitle
    else:
      print(f"{F.LIGHTRED}Error{S.R}: Unable to Get Channel Title. Please check the channel ID.")
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