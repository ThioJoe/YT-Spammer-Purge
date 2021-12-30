#!/bin/bash
#install python
#install tkinter, a dependency
if [[ -e /etc/debian_version ]]; then
	apt install python3 python3-tk
elif [[ -e /etc/fedora-release ]]; then
	dnf install python3
	dnf install python3-tkinter
elif [[ -e /etc/centos-release ]]; then
	yum install -y python3
	yum install tkinter
elif [[ -e /etc/arch-release ]]; then
	pacman -Sy python3 tk
else
	echo "Looks like you aren't running this installer on a Debian, Ubuntu, Fedora, CentOS, Arch Linux system."
	exit 1
fi
sudo -u $USER curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo -u $USER python3 get-pip.py
# Uncomment if running this script alone, to also install the files for Youtube-Spammer-Purge
: 'sudo -u $USER curl https://codeload.github.com/ThioJoe/YouTube-Spammer-Purge/tar.gz/refs/tags/v2.2.5 -o yt-spammer.tar.gz
sudo -u $USER tar -xzf yt-spammer.tar.gz
sudo -u $USER rm yt-spammer.tar.gz
sudo -u $USER cd YouTube-Spammer-Purge-2.2.5/'
sudo -u $USER rm get-pip.py
sudo -u $USER pip -q install -r requirements.txt
printf "Dependencies and Program installed!\nNow follow these instructions to get a client_secrets.json file!\nhttps://github.com/ThioJoe/YouTube-Spammer-Purge#instructions---obtaining-youtube-api-key\n"