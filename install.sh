#!/bin/bash

READY_TO_RUN_PIP=0

debian_install () {
    echo "YT-Spammer-Purge has a few requirements for Debian/Ubuntu-based systems."
    sudo apt install python3 python3-tk python3-pip

    READY_TO_RUN_PIP=1
}

fedora_install () {
	sudo dnf install python3 python3-tkinter python3-pip
    READY_TO_RUN_PIP=1
}

centos_install () {
	sudo yum install -y python3
	rpm -q epel-release &> /dev/null || EPEL=0
	sudo yum install -y python3-tkinter epel-release python3-pip
	# Honestly not sure why it's installing epel and then uninstalling
    [[ $EPEL -eq 0 ]] && sudo yum remove -y epel-release
    READY_TO_RUN_PIP=1
}

arch_install () {
	sudo pacman -S --needed python3 tk
    READY_TO_RUN_PIP=1
}

install_python_requirements () {
    python3 -m ensurepip && \
        python3 -m pip install -r requirements.txt --user && \
        echo "Python requirements installed" || \
        echo "Python requirements did not install successfully"
}



# Check what OS we're running on

[[ -e /etc/debian_version ]] && debian_install || \
    [[ -e /etc/fedora-release ]] && fedora_install || \
    [[ -e  /etc/centos-release ]] && centos_install || \
    [[ -e /etc/arch-release ]] && arch_install || \
    echo "Unknown system."

if [[ $READY_TO_RUN_PIP -eq 0 ]];
then
    echo "Looks like you aren't running this installer on a supported system."
    echo "Contributions are welcome to add support for your system:"
    echo "https://github.com/ThioJoe/YT-Spammer-Purge"
	exit 1
fi

# If we've gotten python3 installed:

install_python_requirements

# Done!

printf "Dependencies and Program installed!\nNow follow these instructions to get a client_secrets.json file!\nhttps://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key\n"
