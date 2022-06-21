#!/usr/bin/env bash

clear
# Clear screen before running any commands

REQUIREMENTS_INSTALLED=0
# Implemented in install_MAIN
DEPS_ONLY=0
# Implemented at bottom of file
PDEPS_ONLY=0
# Implemented at bottom of file
ASSUME_YES=0
# Implemented in confirm function

print_usage() {
   # Display Usage
   echo "Usage: $0 [-y] [-d] [-c] [-p] [-h]"
   echo
   echo "Installer script for The YouTube Spammer Purge application."
   echo
   echo "Options:"
   echo "    -y     Assume yes: Skip confirmation prompts."
   echo "    -d     Only install OS-Specific dependencies."
   echo "    -c     Skip installing OS-Specific dependencies."
   echo "           This could be useful to those who have unsupported systems"
   echo "    -p     Only install Python dependencies"
   echo "    -h     Print this Help."
   echo
}

# Get the options
while getopts ":hdcyp" option; do
	case $option in
		h)  # display Help
			print_usage
			exit;;
		d)  # Install dependencies only
			DEPS_ONLY=1;;
		c)  # Skip installing dependencies
			REQUIREMENTS_INSTALLED=1;;
		p)  # Install Python dependencies only
			PDEPS_ONLY=1;;
		y)  # Assume YES
			ASSUME_YES=1;;
		\?) # Invalid option
			echo "Error: Invalid option. See option -h for help."
			exit 1 ;;
	esac
done

# Credit to https://stackoverflow.com/questions/29436275/how-to-prompt-for-yes-or-no-in-bash
# Slightly edited
confirm() {
    [[ $ASSUME_YES -eq 1 ]] && echo "Assuming YES." && return 0
    while true; do
        read -r -p "$* [y/n]: " yn

        if [[ "$yn" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
            return 0
        fi

        if [[ "$yn" =~ ^([nN][oO]|[nN])+$ ]]; then
            return 1
        fi

    done
}

install_fail () {
    echo "Install Failed."
    exit 1
}

install_debian () {
    sudo apt-get install python3 python3-dev python3-tk python3-pip git || install_fail
}

install_fedora () {
    sudo dnf install python3 python3-tkinter python3-pip git python3-devel || install_fail
}

install_centos () {
    sudo yum install -y python3 || install_fail
    rpm -q epel-release &> /dev/null || EPEL=0
    sudo yum install -y python3-tkinter epel-release python3-pip git || install_fail
    # Honestly not sure why it's installing epel and then uninstalling
    [[ $EPEL -eq 0 ]] && sudo yum remove -y epel-release
}

install_arch () {
    sudo pacman -S --needed python3 tk git && python3 -m ensurepip || install_fail
}

install_macos() {
    echo "This script will install Homebrew, along with YT-Spammer-Purge's requirements."
    echo "Continue installation?"
    confirm && echo "Ok, installing requirements." || install_fail
    if test ! "$(which brew)"; then
        #Install homebrew
        echo "Installing homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    # Install python3.10 & git or fail out
    brew install python@3.10 && \
    brew install tcl-tk && \
    brew install python-tk && \
    brew install git || \
        install_fail
}

install_python_requirements () {
    python3 -m pip install -q -r requirements.txt --user && \
        echo "Python requirements installed." || exit 1
    # Pip should give an error if it fails.
}

install_os_requirements () {
    echo "YT-Spammer-Purge has a few OS-Specific requirements that you will need to install."

    # Check for known OS's
    INSTALLED=0

    case "$(uname -s)" in
        Darwin*) install_macos && INSTALLED=1 || install_fail;;
        # Mac
        #CYGWIN*) do_something;;
        # Cygwin Emulator -- Unimplemented
        #MINGW*) do_something;;
        # MINGW Emulator -- Unimplemented
    esac

    [[ -e /etc/debian_version ]] && install_debian && INSTALLED=1

    [[ -e /etc/fedora-release ]] && install_fedora && INSTALLED=1

    [[ -e  /etc/centos-release ]] && install_centos && INSTALLED=1

    [[ -e /etc/arch-release ]] && install_arch && INSTALLED=1

    [[ $INSTALLED -eq 0 ]] && printf "You are on an unknown system. You will have to install the required packages manually.\nAfter installing your requirements, you can run install.sh -c to skip this step of the installation.\nContributions are welcome to add support for your system:\nhttps://github.com/ThioJoe/YT-Spammer-Purge" && exit 1

    return 0
}

install_latest_release () {
    echo "We are now going to download the code for YT-Spammer-Purge."
    git clone https://github.com/ThioJoe/YT-Spammer-Purge
    cd YT-Spammer-Purge || exit 5
    # Use non-1 exit code for debugging
    git checkout -q -m "$(git describe --abbrev=0 --tags)"
    # Go to latest release
}

install_MAIN () {
    clear
    echo "We will now install YT-Spammer-Purge."
    echo "Continue?"
    confirm || install_fail
    echo "Installing."
    # Check what OS we're running on

    # Check if we already installed the requirements -- git is needed to check for which mode to run.
    [[ $REQUIREMENTS_INSTALLED -eq 0 ]] && install_os_requirements

    echo "--------------------------"

    install_latest_release
    # install_latest_release cd's into YT-Spammer-Purge

    # Since we've gotten python3 installed:

    echo "--------------------------"
    install_python_requirements

    # Done!

    printf "Dependencies and Program installed into .\YT-Spammer-Purge!\nNow follow these instructions to get a client_secrets.json file!\nhttps://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key\n\nYou may run this script again inside your installation to update.\n"
    exit 0
}

check_python_requirements () {
    # This assumes we are in the YT-Spammer-Purge directory
    echo "Checking installed requirements"
    python3 -c "import pkg_resources; pkg_resources.require(open('requirements.txt',mode='r'))" &>/dev/null || install_python_requirements
}

update () {
    # This assumes we are in the YT-Spammer-Purge directory
    check_python_requirements
    clear
    echo "We will now attempt to update YT-Spammer-Purge."
    echo "Current version is $(git describe --abbrev=0 --tags)"
    echo "Continue?"
    confirm || exit 1
    echo "Updating..."


    git fetch origin
    echo "Latest version is $(git describe origin --abbrev=0 --tags)"
    echo "Updating to this version."
    git checkout -q -m "$(git describe origin --abbrev=0 --tags)"
    install_python_requirements
    # In case requirements are updated

    echo "--------------------------"
    echo "Updated!"
    echo "Report any bugs to TJoe.io/bug-report"
    exit 0
}

check_git_missing () {
    [[ $(git remote get-url origin) == *"YT-Spammer-Purge"* ]] && return 0
    # If this is a valid YT-Spammer-Purge install, return 0
    # If this is a fork, with a name different than YT-Spammer-Purge, this check will fail.
    # If you are running this on a fork, please replace every instance of 'YT-Spammer-Purge' with your fork name.
    clear
    echo "It looks like you downloaded a .zip of YT-Spammer-Purge"
    echo "Automated updates do not work on these versions, but you may download the latest version of YT-Spammer-Purge using this script."
    echo "If you choose to re-download the latest verion of YT-Spammer-Purge using this script, automated updates will be re-enabled."
    echo "The latest YT-Spammer-Purge with automated updates will be downloaded to a sub-directory of the same name."
    echo "Would you like to re-install YT-Spammer-Purge?"
    confirm && echo "OK, installing." || exit 1
    install_MAIN
    exit 0
}


# Start running commands to choose what to do next.

[[ $DEPS_ONLY -eq 1 ]] && install_os_requirements && exit 0

[[ $PDEPS_ONLY -eq 1 ]] && install_python_requirements && exit 0

# Check if any of these commands are missing/failing:
# -  git
# -  python3
# -  python3 -c "import tkinter"
#
if ( ! command -v git &> /dev/null ) | ( ! command -v python3 &> /dev/null ) | ( ! python3 -c "import tkinter" &>/dev/null )
then
    echo "You are missing some required packages."
    install_os_requirements
    REQUIREMENTS_INSTALLED=1
fi

[[ -e YTSpammerPurge.py ]] && check_git_missing && update
# If YTSpammerPurge.py exists in the dir, check if it is a valid YT-Spammer-Purge install, and either re-install or update
# These will exit when they succeed

install_MAIN
# If get-url succeeds, update, else install
# Will exit if succeed

# Script should not reach this point, error if it does
exit 1
