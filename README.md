<h1 align="center">
<img src="/assets/icon.png" alt="Icon" width="100" height="100" </img>
<br>
YouTube Spammer Purge
<br>
</h1>


**What Is This?** - Allows you to filter and search for spammer comments on your channel and other's channel(s) in many different ways AND delete/report them all at once (see features below).

**How to Download:** Click the "[Releases](https://github.com/ThioJoe/YouTube-Spammer-Purge/releases)" link on the right, then on the latest release, under 'Assets' click to download "YTSpammerPurge.exe". (You might have to click "Assets" to view the files for the release)
> * [Linux Setup Instructions](https://github.com/ThioJoe/YouTube-Spammer-Purge/wiki/Linux-Installation-Instructions)
> * [MacOS Setup Instructions](https://github.com/ThioJoe/YouTube-Spammer-Purge/wiki/MacOS-Instructions)
> * (Windows installation not necessary if using exe file. But see how to set up required API key [on this page](https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key))

### **Detailed Info & Documentation →** Visit the wiki [(Click Here)](https://github.com/ThioJoe/YT-Spammer-Purge/wiki) for more detailed writeups on the program

## Features

* 15 Different Filtering Methods
  * **Auto-Smart Mode (Recommended)**: Automatically detects multiple spammer techniques
  * **Sensitive-Smart Mode**: More likely to catch elusive spammers, but with more false positives
  * **Scan by Channel ID**: Enter a known spammer's channel link or ID directly
  * **Scan Usernames** for: Individual special characters, individual strings, or using a custom Regex expression
  * **Scan Comment Text**: (Same 3 options as above)
  * **Scan Usernames and Comment Text** simultaneously: (Same 3 options as above)
  * **ASCII Mode**: Scan Usernames for non-ASCII special characters (three different sensitivities)
* 4 Different Scanning Modes
  * Scan a **single video**
  * Scan **Recent Videos** (Up to 5)
  * Scan recent comments across **entire channel** (all videos)
  * *Experimental*: Scan a **community post**
* Automatic deletion of all found comments (after confirmation), as well as the option to ban them
* Options to instead Report spam comments or 'Hold For Review'
* Ability to create config file to skip pre-set options
* Rich text log files
* 'Recovery Mode' option to re-instate previously deleted comments
* Displays "match samples" after printing comments list to easily spot false positives
* Ability to exclude selected authors before deletion / reporting

## Purpose

Recently, there has been a massive infestation of spam on YouTube where fake impersonator accounts leave spam/scam replies to hundreds of users on a creator's videos. For some god-forsaken reason, YouTube offers no way to delete all comments by a specific user at once, meaning you must delete them one by one BY HAND.

YouTube offers a functionality to ban a user, but it does NOT delete previous comments. Therefore I created this script to allow you to instantly purge their spam replies, and since then it has evolved into a fully featured spam scanner as well. **IT DOES NOT PREVENT SPAMMERS - It only makes it easier to delete them when they show up!** YouTube still must implement better native tools for dealing with spammers.

## 🤔 Pro-Tip If This Seems Sketchy: Limiting The App's Access 🤔

If you feel sketched out about giving the app the required high level permissions to your channel (very understandable), you could instead use the app in 'moderator mode' (set in the config file). First, some context: When you grant access to another channel to be a moderator for your channel, they are able to mark comments for 'held for review', and this permission works through the API as well. 

_Therefore,_ what you could do is create an _blank dummy-google-account_ with nothing on it except a empty new channel. Then you can grant _that_ channel permission to be a moderator, and use the app through _the dummy moderator account_. **This way, you know that the app will never have the ability to do more than mark comments as held for review** (which the app supports) on your main channel, and have no other access to your account's data. You just won't be able to ban the spammers through this app directly, but you can still remove/hide their comments instead of deleting them. Just make sure to create the google cloud API project on the dummy account instead.

Read some additional details about 'moderator mode' on the [wiki page here](https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Moderator-Mode-&-Limiting-Permissions).

## Usage Notes -READ THIS

1. To use this script, you will need to obtain your own API credentials file by making a project via the Google Developers Console (aka 'Google Cloud Platform'). The credential file should be re-named `client_secret.json` and be placed in the same directory as this script. [See Instructions Here](https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key).

2. **IF IT FREEZES** while scanning, it is probably because you clicked within the command prompt window and entered "selection mode" which pauses everything. **To unfreeze it, simply right click within the window, or press the Escape key.**

3. I'm a total amateur, so if something doesn't work I'll try to fix it but might not even know how, so don't expect too much. Therefore **I OFFER NO WARRANTY OR GUARANTEE FOR THIS SCRIPT. USE AT YOUR OWN RISK.** I tested it on my own and implemented some failsafes as best as I could, but there could always be some kind of unexpected bug. You should inspect the code yourself.

## Video: Project Demonstrations

<p align="center">Latest Demonstration Video: https://www.youtube.com/watch?v=2tRppXW_aKo</p>

[![Updated Demo Video Screenshot Link](https://user-images.githubusercontent.com/12518330/147130101-ff84cd0e-c1fb-43d9-a3be-4c9d4b95d7b0.png)
](https://www.youtube.com/watch?v=2tRppXW_aKo)

<p align="center">Original Demo for Context: https://www.youtube.com/watch?v=-vOakOgYLUI</p>

[![Demo 1 Video Screenshot Link](https://user-images.githubusercontent.com/12518330/140164510-7c886cd9-b9d4-4d6d-a466-fb58dd42ab48.jpg)](https://www.youtube.com/watch?v=-vOakOgYLUI)

(Takes you to YouTube, not embedded. See timestamps in video description.)

## Screenshots

<p align="center">Opening Menu:</p>
<p align="center"><img width="675" alt="Opening Menu" src="https://user-images.githubusercontent.com/93459510/147557851-6d517280-6e20-4dfd-ab78-1a2357f710a7.png"></p>
<p align="center">Filter Mode Selection:</p>
<p align="center"><img width="675" alt="Filter Mode Selection" src="https://user-images.githubusercontent.com/93459510/147558339-28dc9fec-a51b-48be-a1bb-4f8b9e6cb3f6.png"></p>
<p align="center">Scanning (Auto Smart Mode):</p>
<p align="center"><img width="675" alt="Scanning" src="https://user-images.githubusercontent.com/93459510/147558617-b097e342-40bb-48df-ab59-d6a985a2322a.png"></p>
<p align="center">Matched Comments List:</p>
<p align="center"><img width="675" alt="Matched Comments List" src="https://user-images.githubusercontent.com/93459510/147558790-881b4871-e3de-43fe-be02-2fce6a03304d.png"></p>
<p align="center">Match Samples and Deletion Menu:</p>
<p align="center"><img width="738" alt="Match Samples and Deletion Menu" src="https://user-images.githubusercontent.com/93459510/147559013-7b1f59c7-4433-4b19-8e2e-7988d5d29ee5.png"></p>

## Installation

If using the python script version (not the exe), there is a requirements.txt with necessary modules. Created with Python 3.9.7

Either way, you DO need to acquire your own API credentials file to access the YouTube API - [See Instructions Here](https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key).

**Operating System Specific Instructions:**

* [Linux Setup Instructions](https://github.com/ThioJoe/YouTube-Spammer-Purge/wiki/Linux-Installation-Instructions)
* [MacOS Setup Instructions](https://github.com/ThioJoe/YouTube-Spammer-Purge/wiki/MacOS-Instructions)



**Docker Instructions:**

Before running `docker-compose` you must run the `YTSpammerPurge.py` script at least once with your `client_secrets.json` file to confirm OAuth credentials and generate the config/token files.

The generated config files, token, and Spam Purge Resources will all be bound to the docker container via volumes.

Once you generated the token and config files you are ready to run the docker image.


Now you can run `docker-compose up` to start the container, or use the image to run on a Kubernetes cluster for example.
To build your own version you can run this command: `docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build`


## Instructions - Obtaining YouTube API Key
To use this script, you will need an "Oauth2" credential to access the scanning and deletion functions via YouTube's Data API. Otherwise this script won't work at all. 
* #### Instructions can be found on this page: [Instructions: Obtaining an API Key](https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key)
* #### **Or, follow a video WalkThrough Here: <https://www.youtube.com/watch?v=c6ebWvay8dE>**  
