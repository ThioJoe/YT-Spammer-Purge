#!/bin/bash

clear
# Clear screen before running any commands


install_debian () {
    sudo apt install python3 python3-tk python3-pip git
}

install_fedora () {
	sudo dnf install python3 python3-tkinter python3-pip git
}


install_centos () {
	sudo yum install -y python3
	rpm -q epel-release &> /dev/null || EPEL=0
	sudo yum install -y python3-tkinter epel-release python3-pip git
	# Honestly not sure why it's installing epel and then uninstalling
    [[ $EPEL -eq 0 ]] && sudo yum remove -y epel-release
}

install_arch () {
	sudo pacman -S --needed python3 tk git
}

install_python_requirements () {
    python3 -m ensurepip && \
        python3 -m pip install -r requirements.txt --user && \
        echo "Python requirements installed" || \
        echo "Python requirements did not install successfully"
}

install_os_requirements () {
    # Check for known OS's
    INSTALLED=0
    [[ -e /etc/debian_version ]] && install_debian && INSTALLED=1
    [[ -e /etc/fedora-release ]] && install_fedora && INSTALLED=1
    [[ -e  /etc/centos-release ]] && install_centos && INSTALLED=1
    [[ -e /etc/arch-release ]] && install_arch && INSTALLED=1
    [[ $INSTALLED -eq 0 ]] && printf "You are on an unknown system. You will have to install the required packages manually.\nContributions are welcome to add support for your system:\nhttps://github.com/ThioJoe/YT-Spammer-Purge" && exit 1
}

install_MAIN () {
    clear
    # Check what OS we're running on
    echo "YT-Spammer-Purge has a few requirements that you will need to install."

    install_os_requirements

    # If we've gotten python3 installed:

    install_python_requirements

    # Done!

    printf "Dependencies and Program installed!\nNow follow these instructions to get a client_secrets.json file!\nhttps://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key\n"
}

update () {
    echo "update here"
}

if ! command -v git &> /dev/null
then
    echo "You are missing some required packages."
    install_os_requirements
fi

git remote get-url origin > /dev/null && update || install_MAIN


