#!/bin/bash
#install python and tkinter, a dependency
if [[ -e /etc/debian_version ]]; then
	sudo apt install python3 python3-tk python3-pip
elif [[ -e /etc/fedora-release ]]; then
	sudo dnf install python3 python3-tkinter python3-pip
elif [[ -e /etc/centos-release ]]; then
	sudo yum install -y python3 python3-tkinter python3-pip
elif [[ -e /etc/arch-release ]]; then
	sudo pacman -S python3 tk python-pip
else
	echo "Looks like you aren't running this installer on a Debian, Ubuntu, Fedora, CentOS, Arch Linux system."
	exit 1
fi
# Uncomment if running this script alone, to also install the files for YT-Spammer-Purge
 curl https://codeload.github.com/ThioJoe/YT-Spammer-Purge/tar.gz/refs/tags/v2.7.3 -o yt-spammer.tar.gz
 tar -xzf yt-spammer.tar.gz
 rm yt-spammer.tar.gz
 cd YT-Spammer-Purge-2.7.3/
 pip3 install -r requirements.txt --user
printf "Dependencies and Program installed!\nNow follow these instructions to get a client_secrets.json file!\nhttps://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key\n"
