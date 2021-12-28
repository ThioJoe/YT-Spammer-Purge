#!/bin/bash
#checks for python; if not installed will install it
command -v python >/dev/null 2>&1 || { pacman -S python; dnf install python3; apt install python3; zypper install python3; emerge python;}
#install tkinter, a dependency
apt-get install python3-tk; pacman -Syu tk; dnf install python3-tkinter; zypper install python3-tk
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
# Uncomment if running this script alone, to also install the files for Youtube-Spammer-Purge
curl https://codeload.github.com/ThioJoe/YouTube-Spammer-Purge/tar.gz/refs/tags/v2.2.5 -o yt-spammer.tar.gz
tar -xzf yt-spammer.tar.gz
rm yt-spammer.tar.gz
cd YouTube-Spammer-Purge-2.2.5/
rm get-pip.py
pip install -r requirements.txt
printf "Dependencies and Program installed!\nNow follow these instructions to get a client_secrets.json file!\nhttps://github.com/ThioJoe/YouTube-Spammer-Purge#instructions---obtaining-youtube-api-key"
