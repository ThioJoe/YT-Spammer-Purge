#!/bin/bash
py=$(python --version)
command -v python >/dev/null 2>&1 || { pacman -S python; dnf install python; apt install python; zypper install python3; emerge python;}
command -v pip >/dev/null 2>&1 || { pacman -S pip; dnf install pip; apt install pip; zypper install pip; emerge pip;}
curl https://codeload.github.com/ThioJoe/YouTube-Spammer-Purge/tar.gz/refs/tags/v2.2.5 -o yt-spammer.tar.gz
tar -xzvf yt-spammer.tar.gz
cd YouTube-Spammer-Purge-2.2.5/
pip install -r requirements.txt
echo "Dependencies installed!"
