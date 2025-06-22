#!/usr/bin/env python3
from typing import Any

from . import validation
from .shared_imports import B, F, S


################################ USER TOOLS MENU ###########################################
def user_tools_menu(_config: Any):
    print(f"\n\n-------------------- {F.LIGHTGREEN_EX}Helpful Tools{S.R} --------------------")
    print("      1. Get Channel ID from Video URL")
    print("")

    while True:
        match input("Choice: "):
            case "1":
                result = video_to_channel_id()
                if result == "MainMenu":
                    return "MainMenu"
                break
            case "x":
                return "MainMenu"
            case _:
                print(f"{F.LIGHTRED_EX}Invalid Choice! Must be a number from the selections above.\n{S.R}")


################################ VIDEO URL TO CHANNEL ID ###########################################
def video_to_channel_id():
    print("\n\n-------------------- Video URL to Channel ID --------------------")
    print(f"{F.YELLOW}How To Use:{S.R} Enter a video URL and this tool will return the channel ID of the uploader.\n")

    while True:
        urlInput = input("Video URL: ")

        # Check if user wants to go back
        if urlInput == "x":
            return "MainMenu"

        # Validate video URL and get info about video and channel
        validate = validation.validate_video_id(urlInput, pass_exception=True)
        if not validate:
            print(f"{F.LIGHTRED_EX}Invalid URL! Please enter a valid YouTube video URL.{S.R}\n")
            continue

        (valid, _videoID, videoTitle, _commentCount, channelID, channelTitle) = validate
        if valid:
            print("\nResults:")
            print(f"  - {F.BLUE}Video Title{S.R}: {videoTitle}")
            print(f"  - {F.BLUE}Channel Name{S.R}: {channelTitle}")
            print(f"  - {F.BLUE}Channel ID{S.R}: {B.YELLOW}{F.BLACK} {channelID} {S.R}")

            input("\nPress Enter to return to main menu...")
            return "MainMenu"
