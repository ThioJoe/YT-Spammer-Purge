#!/usr/bin/env bash

# Installer script for The YouTube Spammer Purge application

print_usage() {
   # Display Usage
   echo "Usage: $0 [-h] [-d]"
   echo
   echo "Installer script for The YouTube Spammer Purge application."
   echo
   echo "Options:"
   echo "    -d     Only install dependencies."
   echo "    -h     Print this Help."
   echo
}

DEPS_ONLY=0

# Get the options
while getopts ":hd" option; do
	case $option in
		h)  # display Help
			print_usage
			exit;;
		d)  # Install dependencies only
			DEPS_ONLY=1;;
		\?) # Invalid option
			echo "Error: Invalid option. See option -h for help."
			exit 1 ;;
	esac
done


# Running this installer is only supported on specific systems.
if ! { [[ -e /etc/debian_version ]] || [[ -e /etc/fedora-release ]] || [[ -e  /etc/centos-release ]] || [[ -e /etc/arch-release ]]; }; then
	echo "Looks like you aren't running this installer on a Debian, Ubuntu, Fedora, CentOS, or Arch Linux system."
	exit 1
fi

#install python
if ! command -v python3 &> /dev/null; then
	if [[ -e /etc/debian_version ]]; then
		sudo apt install python3
	elif [[ -e /etc/fedora-release ]]; then
		sudo dnf --assumeyes --quiet install python3
	elif [[ -e /etc/centos-release ]]; then
		sudo yum install -y python3
	elif [[ -e /etc/arch-release ]]; then
		sudo pacman -S python3
	fi
else
	echo "Skipping installing python, as python is preinstalled."
fi
#install tkinter, a dependency
#install GCC and Python3 headers on Fedora, since python-Levenshtein needs to be compiled there.
if [[ -e /etc/debian_version ]]; then
	sudo apt install python3-tk python3-pip
elif [[ -e /etc/fedora-release ]]; then
	sudo dnf --assumeyes --quiet install python3-tkinter python3-pip python3-devel gcc
elif [[ -e /etc/centos-release ]]; then
	rpm -q epel-release &> /dev/null || EPEL=0
	sudo yum install -y python3-tkinter epel-release python3-pip python3-devel gcc
	sudo yum install -y
	[[ $EPEL -eq 0 ]] && sudo yum remove -y epel-release
elif [[ -e /etc/arch-release ]]; then
	sudo pacman -S --needed tk
fi

if [[ DEPS_ONLY -eq 0 ]]; then
	TAG=$(curl https://api.github.com/repos/ThioJoe/YT-Spammer-Purge/releases/latest | grep -oP '(?<="tag_name": ")[^"]*')
	location=YT-Spammer-Purge-"${TAG}"
	curl https://codeload.github.com/ThioJoe/YT-Spammer-Purge/tar.gz/refs/tags/"${TAG}" | tar -xz -C "$location" --strip-components 1
	cd "$location" || exit
	bash -c "pip3 install -r requirements.txt --user"
	printf "Dependencies and Program installed!\nNow follow these instructions to get a client_secrets.json file!\nhttps://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key\n"
fi

exit 0
