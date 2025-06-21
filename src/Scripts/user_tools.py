#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Scripts.shared_imports import *
import Scripts.auth as auth
import Scripts.validation as validation
import Scripts.utils as utils

################################ USER TOOLS MENU ###########################################
def user_tools_menu(config):
  print(f"\n\n-------------------- {F.LIGHTGREEN_EX}Helpful Tools{S.R} --------------------")
  print(f"      1. Get Channel ID from Video URL")
  print("")
  
  validMode:bool = False
  while not validMode:
    toolChoice = input("Choice: ")

    # Check if user wants to go back
    if toolChoice == "x":
      return "MainMenu"
    
    # Check if valid choice
    validChoices = ['1']
    if toolChoice in validChoices:
      validMode = True

      # Call the appropriate function
      if toolChoice == "1":
        result = video_to_channel_id()
        
      #--------------------------------------------
      # Check if user wants to go back
      if str(result) == "MainMenu":
        return "MainMenu"
    
    else:
      print(f"{F.LIGHTRED_EX}Invalid Choice! Must be a number from the selections above.\n{S.R}")
      if len(validChoices) == 1:
        print(f"(Note: For now there is currently only one option available, so enter \"1\".)\n")


################################ VIDEO URL TO CHANNEL ID ###########################################
def video_to_channel_id():
  print(f"\n\n-------------------- Video URL to Channel ID --------------------")
  print(f"{F.YELLOW}How To Use:{S.R} Enter a video URL and this tool will return the channel ID of the uploader.")
  print("")
  
  validChoice = False
  while not validChoice:
    urlInput = input("Video URL: ")

    # Check if user wants to go back
    if urlInput == "x":
      return "MainMenu"

    # Validate video URL and get info about video and channel
    videoInfo = validation.validate_video_id(urlInput, pass_exception=True)
    if videoInfo[0] == True:
      validChoice = True

      videoID = videoInfo[1]
      videoTitle = videoInfo[2]
      commentCount = videoInfo[3]
      channelID = videoInfo[4]
      channelTitle = videoInfo[5]

      print("\nResults:")
      print(f"  - {F.BLUE}Video Title{S.R}: {videoTitle}")
      print(f"  - {F.BLUE}Channel Name{S.R}: {channelTitle}")
      print(f"  - {F.BLUE}Channel ID{S.R}: {B.YELLOW}{F.BLACK} {channelID} {S.R}")

      input("\nPress Enter to return to main menu...")
      return "MainMenu"
