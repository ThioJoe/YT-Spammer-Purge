#!/bin/bash
command -v jq >/dev/null 2>&1 || { JQ=0; }
#install python
if ! command -v python3 &> /dev/null; then
	if [[ -e /etc/debian_version ]]; then
		sudo apt install python3
	elif [[ -e /etc/fedora-release ]]; then
		sudo dnf install python3
	elif [[ -e /etc/centos-release ]]; then
		sudo yum install -y python3
	elif [[ -e /etc/arch-release ]]; then
		sudo pacman -Sy python3
	else
		echo "Looks like you aren't running this installer on a Debian, Ubuntu, Fedora, CentOS, or Arch Linux system."
		exit 1
	fi
else
	echo "Skipping installing python, as python is preinstalled"
fi
#install tkinter, a dependency
#install jq, needed to get version number
if [[ -e /etc/debian_version ]]; then
	sudo apt install python3-tk jq
elif [[ -e /etc/fedora-release ]]; then
	sudo dnf install python3-tkinter jq
elif [[ -e /etc/centos-release ]]; then
	sudo yum install -y tkinter epel-release jq
elif [[ -e /etc/arch-release ]]; then
	sudo pacman -Sy tk jq
fi
command -v pip >/dev/null 2>&1 || { curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py; python3 get-pip.py --no-warn-script-location; rm get-pip.py; }
TAG=$(curl https://api.github.com/repos/ThioJoe/YT-Spammer-Purge/releases/latest -s | jq .name -r)
if  [[ $JQ -ne 0 ]]; then
	if [[ -e /etc/debian_version ]]; then
		apt purge jq
	elif [[ -e /etc/fedora-release ]]; then
		dnf remove jq
	elif [[ -e /etc/centos-release ]]; then
		yum remove jq epel-release
	elif [[ -e /etc/arch-release ]]; then
		pacman -Rs jq
	fi
else
	echo "Did not unistall jq as it was preinstalled before running this script."
fi
# Uncomment if running this script alone, to also install the files for Youtube-Spammer-Purge
curl https://codeload.github.com/ThioJoe/YT-Spammer-Purge/tar.gz/refs/tags/v${TAG} -o yt-spammer.tar.gz
tar -xzf yt-spammer.tar.gz
rm yt-spammer.tar.gz
cd YouTube-Spammer-Purge-${TAG}/
bash -c "pip install -r requirements.txt"
printf "Dependencies and Program installed!\nNow follow these instructions to get a client_secrets.json file!\nhttps://github.com/ThioJoe/YouTube-Spammer-Purge#instructions---obtaining-youtube-api-key\n"
