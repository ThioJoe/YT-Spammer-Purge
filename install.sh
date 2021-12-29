#!/bin/bash
#checks for python; if not installed will install it 
command -v python >/dev/null 2>&1 || { py_installed = false;}
if [ "$py_installed" = false ] ; then
	if [[ -e /etc/debian_version ]]; then
    		apt install python3
	elif [[ -e /etc/fedora-release ]]; then
    		dnf install python3
  	elif [[ -e /etc/centos-release ]]; then
		yum install tkinter
	elif [[ -e /etc/arch-release ]]; then
		pacman -Syu python3
	else
		echo "Looks like you aren't running this installer on a Debian, Ubuntu, Fedora, CentOS, Arch Linux system."
		exit 1
	fi
fi
#install tkinter, a dependency
if [[ -e /etc/debian_version ]]; then
	apt-get install python3-tk
elif [[ -e /etc/fedora-release ]]; then
	dnf install python3
elif [[ -e /etc/centos-release ]]; then
	yum install tkinter
elif [[ -e /etc/arch-release ]]; then
	pacman -Syu python3
fi
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
# Uncomment if running this script alone, to also install the files for Youtube-Spammer-Purge
: 'curl https://codeload.github.com/ThioJoe/YouTube-Spammer-Purge/tar.gz/refs/tags/v2.2.5 -o yt-spammer.tar.gz
tar -xzf yt-spammer.tar.gz
rm yt-spammer.tar.gz
cd YouTube-Spammer-Purge-2.2.5/'
rm get-pip.py
pip install -r requirements.txt
printf "Dependencies and Program installed!\nNow follow these instructions to get a client_secrets.json file!\nhttps://github.com/ThioJoe/YouTube-Spammer-Purge#instructions---obtaining-youtube-api-key"
