# YouTube Spammer Purge

**What Is This?** - Allows you to filter and search for spammer comments on your channel in many different ways AND delete them all at once (see features below).

**How to Download:** Click the "[Releases](https://github.com/ThioJoe/YouTube-Spammer-Purge/releases)" link on the right, then on the latest release, under 'Assets' click to download "YouTubeSpammerPurge.exe". NOTE: You may get a warning - See "[Download & Windows Warning](#download--windows-warning)" section below for details.
* [Linux Setup Instructions](https://github.com/ThioJoe/YouTube-Spammer-Purge/wiki/Linux-Installation-Instructions) 
* [MacOS Setup Instructions](https://github.com/ThioJoe/YouTube-Spammer-Purge/wiki/MacOS-Instructions)
* (Windows installation not necessary if using exe file. But read below for how to set up required API key)

## Features
* Scan comments on a **single video** or across your **entire channel**
* 11 Different Filtering Methods
   * **Scan by Channel ID**: Enter a known spammer's channel link or ID directly
   * **Scan Usernames** for: Individual special characters, individual strings, or using a custom Regex expression
   * **Scan Comment Text for**: Individual special characters, individual strings, or using a custom Regex expression
   * **Auto Mode**: Scan Usernames for non-ASCII special characters (three different sensitivities)
   * **Auto Smart-Mode**: Scan Usernames for special characters often used only by scammers
 * Automatic deletion of all found comments (after confirmation), as well as the option to ban them
 * Rich text log files

## Purpose
Recently, there has been a massive infestation of spam on YouTube where fake impersonator accounts leave spam/scam replies to hundreds of users on a creator's videos. For some god-forsaken reason, YouTube offers no way to delete all comments by a specific user at once, meaning you must delete them one by one BY HAND.

YouTube offers a functionality to ban a user, but it does NOT delete previous comments. Therefore I created this script to allow you to instantly purge their spam replies. **IT DOES NOT PREVENT SPAMMERS - It only makes it easier to delete them when they show up!** YouTube still must implement better native tools for dealing with spammers.

## Usage Notes -READ THIS

1. To use this script, you will need to obtain your own API credentials file by making a project via the Google Developers Console (aka 'Google Cloud Platform'). The credential file should be re-named `client_secret.json` and be placed in the same directory as this script. [See Instructions below](#instructions---obtaining-youtube-api-key).

2. **IF IT FREEZES** while scanning, it is probably because you clicked within the command prompt window and entered "selection mode" which pauses everything. **To unfreeze it, simply right click within the window, or press the Escape key.**

3. I'm a total amateur, so if something doesn't work I'll try to fix it but might not even know how, so don't expect too much. Therefore **I OFFER NO WARRANTY OR GUARANTEE FOR THIS SCRIPT. USE AT YOUR OWN RISK.** I tested it on my own and implemented some failsafes as best as I could, but there could always be some kind of unexpected bug. You should inspect the code yourself.

## Video: Project Explanation, Demonstration, and Setup Walkthrough
<p align="center">Regular Link: https://www.youtube.com/watch?v=-vOakOgYLUI</p>

[![Explanation Video Screenshot Link](https://user-images.githubusercontent.com/12518330/140164510-7c886cd9-b9d4-4d6d-a466-fb58dd42ab48.jpg)](https://www.youtube.com/watch?v=-vOakOgYLUI)
(Takes you to YouTube, not embedded. See timestamps in video description.)

## Screenshots
<p align="center"><img width="615" alt="Screenshot 1 5 2" src="https://user-images.githubusercontent.com/12518330/142356861-b95c3fce-d784-4a98-a732-1c41f8b1ebde.png"></p>
<p align="center"><img width="762" alt="Screenshot 2" src="https://user-images.githubusercontent.com/12518330/142356872-7720aa8d-3a34-4f74-b75a-e29d13c03d08.png"></p>
<p align="center"><img width="665" alt="Screenshot 3" src="https://user-images.githubusercontent.com/12518330/142356875-94af0784-4347-460e-8693-f89fc7c9f204.png"></p>



## Installation

If using the python script version (not the exe), there is a requirements.txt with necessary modules. Created with Python 3.9.7

Either way, you DO need to acquire your own API credentials file to access the YouTube API - [See instructions below](instructions---obtaining-youtube-api-key).

**Operating System Specific Instructions:** 
* [Linux Setup Instructions](https://github.com/ThioJoe/YouTube-Spammer-Purge/wiki/Linux-Installation-Instructions) 
* [MacOS Setup Instructions](https://github.com/ThioJoe/YouTube-Spammer-Purge/wiki/MacOS-Instructions)

## Download & Windows Warning

Because I haven't published software before, web browsers and Windows might block the exe from downloading / running as "unrecognized" until it builds a reputation as being safe. In the meantime, you can simply unblock the program by Right Clicking > Properties > Check 'Unblock' > Click Apply. You can confirm the download by selecting "keep". (If you see these warnings at all)

![Download Warnings](https://user-images.githubusercontent.com/12518330/139365793-75df4170-24d9-4724-b54a-43eddb64dd53.png)

<img width="814" alt="Unblock Warning" src="https://user-images.githubusercontent.com/12518330/139364886-f1ad4d80-f7f3-459c-a826-16379d5cf004.png">



## Instructions - Obtaining YouTube API Key

To use this script, you will need an "Oauth2" credential to access the scanning and deletion functions via YouTube's Data API. Otherwise this script won't work at all.  
**Video walking through these same steps here (Go to 11:33) https://youtu.be/-vOakOgYLUI?t=693**  

1. Log into [Google Developer's Console](https://console.cloud.google.com/apis/dashboard) with your Google account that has your YouTube channel.  

2. On the top blue bar nex to where it says "Google Cloud Platform", click the dropdown to 'Select a Project'. (If you have existing projects, it may instead show the name of one)
<p align="center"><img width="530" alt="2" src="https://user-images.githubusercontent.com/12518330/139733945-f80b9eed-9847-4459-bbe2-7f252707b20d.png"></p>

3. In the "Select a Project" Window click "New Project"
<p align="center"><img width="599" alt="3" src="https://user-images.githubusercontent.com/12518330/139733959-72cf691f-7332-4be6-8c61-adbe437b2386.png"></p>

4. Enter some project name, it doesn't really matter, then click 'Create'
<p align="center"><img width="440" alt="4" src="https://user-images.githubusercontent.com/12518330/139733967-e233a183-f9c3-4f5b-89de-606b08996848.png"></p>

5. Make sure the project you just created is active, with it showing at the top, then click "Library" on the left menu.
<p align="center"><img width="617" alt="5" src="https://user-images.githubusercontent.com/12518330/139733984-fd2163fd-5848-47bc-bb96-a7cde8534e6c.png"></p>

6. Scroll down and click the box that says "YouTube Data API v3"
<p align="center"><img width="635" alt="6" src="https://user-images.githubusercontent.com/12518330/139733998-b309d84b-e2ab-4af3-bd71-2e2c921a62bc.png"></p>

7. Click "Enable" and wait for it to load. It will take you to another page.
<p align="center"><img width="503" alt="7" src="https://user-images.githubusercontent.com/12518330/139734007-091f7402-cca4-468f-9f68-61b10dd5f510.png"></p>

8. Click "Create Credentials". 
(Note: If you don't see this page, open the left pop-out menu and click "APIs & Services" > "Dashboard". Then in the table/list on the page, look in the 'Name' column, and click "YouTube Data API v3")
<p align="center"><img width="759" alt="8" src="https://user-images.githubusercontent.com/12518330/139734018-cd85d035-2d21-4f3d-aa06-70aa2b2daa6f.png"></p>

9. In the dropdown, select "YouTube Data API v3", then select "User Data", and click Next
<p align="center"><img width="625" alt="9" src="https://user-images.githubusercontent.com/12518330/139734039-454c1a5d-8927-4a51-826f-84927b0e2148.png"></p>

10. Under "Oauth Consent Screen", fill out the required fields with some name, select your email, and enter an email below too. It doesn't really matter what you put here. Then click "Save and Continue"
<p align="center"><img width="461" alt="10" src="https://user-images.githubusercontent.com/12518330/139734052-6b5ab0b6-9a0d-41fd-a2fa-c36dfce599a3.png"></p>

11. Click "Add or Remove Scopes", then find the one that says ".../auth/youtube.force-ssl", click the check box, then at the bottom click "Update". Then click "Save and Continue"
<p align="center"><img width="422" alt="11 1" src="https://user-images.githubusercontent.com/12518330/139734064-221fedee-988f-4103-8718-f082eae9df12.png">
<img width="546" alt="11 2" src="https://user-images.githubusercontent.com/12518330/139734072-9be172a0-8b12-418a-ba8d-feab6e303058.png"></p>

12. Under "Oauth Client ID", just select 'Desktop App'. You can set a name or not. Then click "create".
<p align="center"><img width="452" alt="12" src="https://user-images.githubusercontent.com/12518330/139734091-2ee876c0-b4b2-4324-9f13-2f6f80d7e8bf.png"></p>

13. Now click "Download" to download the credentials json file. Rename it to `client_secrets.json` and save it into the same directory as the python script. Then click done.
<p align="center"><img width="462" alt="13" src="https://user-images.githubusercontent.com/12518330/139734114-95ce0476-fcf2-4618-8966-525734b2a3bb.png">
   <img width="354" alt="13 2" src="https://user-images.githubusercontent.com/12518330/139736335-ee5f3b95-2ed4-4f8e-971c-06d659018d4e.png"></p>

14. When trying to log in you may get a "403 Access_Denied" error. If so, you need to add yourself as an authorized user. On the left menu, go to APIs & Services > Oauth Consent Screen > Under Test Users, Click "Add Users". On the pop out window, type in your same Google/channel account email into the box and hit Save.
<p align="center"><img width="584" alt="14" src="https://user-images.githubusercontent.com/12518330/139734123-64eb4583-686a-4b5a-a4a1-54393f6b97f0.png"></p>
<p align="center"><img width="595" alt="14 2" src="https://user-images.githubusercontent.com/12518330/139734814-26d04eed-76b6-4b4f-9689-e6960f781faa.png"></p>

15. Now you should be able to run the python script, and it will ask you to log in.

<h1>Unsupported Devices/Android Users</h1>
<p> If you are unable to run the .exe file and the code files because your computer/phone doesn't support it please follow these instructions. </p>
<p> 1. Go to https://replit.com. If you are on android go into destop view </p>
<p> 2. Create a account/Login.</p>
<p>3. On the menu, click Create Repl, if it doesn't load click the menu icon.</p>
<p>4. Click, import from github and paste this repo's url, open the YouTubeSpammerPurger.py file.</p>
<p>5. It will open markdown, tap shell and type the following commands:</p>

<p>Command List for Shell:</p>
<p>pip install rtfunicode</p>
<p>pip install colorama</p>
<p>pip install google-api-python-client (make sure you put the dashes in between)</p>
<p>python3 YouTubeSpammerPurge.py (case sensitive)</p>

<p>Then, you need to do the following setup mentioned above, tap the add file button and add your client_secrets.json file.</p>
