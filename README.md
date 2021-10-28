# YouTube Spammer Purge

Allows you to purge all reply comments left by a user on a YouTube channel or video.

## Purpose
Recently, there has been a massive infestation of spam on YouTube where fake impersonator accounts leave spam/scam replies to hundreds of users on a creator's videos. For some god-forsaken reason, YouTube offers no way to delete all comments by a specific user at once, meaning you must delete them one by one BY HAND.

YouTube offers a functionality to ban a user, but it does NOT delete previous comments. Therefore I created this script to allow you to instantly purge their spam replies.

## Usage Notes

1. Because of its limited purpose, the script ONLY deletes replies, not top-level comments. That functionality may be added later if needed.

2. To use this script, you will need to obtain your own API credentials file by making a project via the Google Developers Console (aka 'Google Cloud Platform'). The credential file should be re-named 'client_secret.json' and be placed in the same directory as this script. See Instructions below.

3. I suck at programming so if something doesn't work I'll try to fix it but might not
   even know how, so don't expect too much.

## Screenshots
<img width="545" alt="Screenshot 1" src="https://user-images.githubusercontent.com/12518330/139163806-9cc7aa50-0bce-4113-afeb-707ee6689b5e.png">
<img width="722" alt="Screenshot 2" src="https://user-images.githubusercontent.com/12518330/139163816-18efe73e-1304-4187-b5da-b6d4b096e46d.png">


## Installation

The script file is standalone, but you DO need to acquire your own API credentials file to access the YouTube API - See instructions below.

## Instructions - Obtaining YouTube API Key

To use this script, you will need an "Oauth2" credential to access the scanning and deletion functions via YouTube's Data API. Otherwise this script won't work at all.

1. Log into Google Developer's Console with your Google account that has your YouTube channel:  https://console.cloud.google.com/apis/dashboard

2. On the top blue bar nex to where it says "Google Cloud Platform", click the dropdown to 'Select a Project'. (If you have existing projects, it may instead show the name of one)

3. In the "Select a Project" Window click "New Project"

4. Enter some project name, it doesn't really matter, then click 'Create'

5. Make sure the project you just created is active, with it showing at the top, then click "Library" on the left menu.

6. Scroll down and click the box that says "YouTube Data API v3"

7. Click "Enable" and wait for it to load. It will take you to another page.

8. Click "Create Credentials". 
(Note: If you don't see this page, open the left pop-out menu and click "APIs & Services" > "Dashboard". Then in the table/list on the page, look in the 'Name' column, and click "YouTube Data API v3")

9. In the dropdown, select "YouTube Data API v3", then select "User Data", and click Next

10. Under "Oauth Consent Screen", fill out the required fields with some name, select your email, and enter an email below too. It doesn't really matter what you put here. Then click "Save and Continue"

11. Click "Add or Remove Scopes", then find the one that says ".../auth/youtube.force-ssl", click the check box, then at the bottom click "Update". Then click "Save and Continue"

12. Under "Oauth Client ID", just select 'Desktop App'. You can set a name or not. Then click "create".

13. Now click "Download" to download the credentials json file. Rename it to "client_secrets.json" and save it into the same directory as the python script. Then click done.

14. Now you should be able to run the python script. It will ask you to log in, and the session will last about an hour before expiring.


