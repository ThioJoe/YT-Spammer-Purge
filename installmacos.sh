#!/bin/zsh
echo "This script will install homebrew, python, git and pip (If not arleady installed!). It will also install all modules."

#If no homebrew is found
if test ! $(which brew); then
    #Install homebrew
    echo "Installing homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
#If no python is found
if test ! $(which python3); then
    #Install python
    echo "Installing python..."
    brew install python@3.10
fi
#If no git is found
if test ! $(which git); then
    #Install git
    echo "Installing git..."
    brew install git
fi

#Clone the repo
git clone https://github.com/ThioJoe/YT-Spammer-Purge.git
#Cd into it
cd YT-Spammer-Purge
#Install required pip modules
pip3 install -r requirements.txt

#Finish
echo "Shloud have installed everything! Now run python3 YTSpammerPurge.py, and follow the instructions on how to get a client secret.json"



