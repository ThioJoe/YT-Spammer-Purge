#!/bin/bash

INSTALL_LEVEL=full
if [ -n "$1" ]; then
  INSTALL_LEVEL=$1
fi

#Piping output to awk allows us to split the string, basically equivalent str.split('=')[1] in python then pass thru tr to trim quotation marks
OS_RELEASE_FILTERED=$(grep -i -v VERSION /etc/os-release)
OS_ID=$(echo "${OS_RELEASE_FILTERED}" | grep -m 1 ID | awk -F '=' '{print $2}' | tr -d '"')

#We have a special installer for centos, but centos is a derivative of fedora
if [ centos != "${OS_ID}" ]; then
  OS_ID_LIKE=$(echo "${OS_RELEASE_FILTERED}" | grep -m 1 ID_LIKE  2>/dev/null | awk -F '=' '{print $2}')
fi

#This os is based on another os, like ubuntu is based on debian or amazonlinux is based on fedora.
if [ -n "${OS_ID_LIKE}" ]; then
  echo "${OS_ID} is based on ${OS_ID_LIKE}, will install as if this is ${OS_ID_LIKE}"
  OS_ID="${OS_ID_LIKE}"
fi

#Distro specific installer scripts, to avoid having to check which distro we were on again each statement
#Every installation pretty much has the same dependencies: python, python-dev, gcc, pip, jq, curl, tk
function install_debian() {
  sudo DEBIAN_FRONTEND=noninteractive apt-get -yqq update && sudo DEBIAN_FRONTEND=noninteractive apt-get -yq install python3 python3-tk jq python3-pip curl
  if  [[ $JQ -ne 0 ]]; then
    sudo apt purge -yq jq
  else
	  echo "Did not uninstall jq as it was preinstalled before running this script."
  fi
}

function install_fedora() {
  sudo dnf install -yq python3 python3-devel python3-tkinter jq python3-pip curl gcc
  if  [[ $JQ -ne 0 ]]; then
    sudo dnf remove -yq jq
  else
	  echo "Did not uninstall jq as it was preinstalled before running this script."
  fi
}

function install_centos() {
	rpm -q epel-release &> /dev/null || EPEL=0
	sudo yum install -y python3 python3-devel python3-tkinter epel-release python3-pip jq curl  curl gcc
	[[ $EPEL -eq 0 ]] && sudo yum remove -y epel-release
	if  [[ $JQ -ne 0 ]]; then
    sudo yum remove -y jq
  else
	  echo "Did not uninstall jq as it was preinstalled before running this script."
  fi
}

function install_arch() {
  sudo pacman -Sy --noconfirm --needed python3 python-pip tk jq curl gcc
  if  [[ $JQ -ne 0 ]]; then
    sudo pacman -Rs jq
  else
	  echo "Did not uninstall jq as it was preinstalled before running this script."
  fi
}

function install_alpine() {
    sudo apk add python3 python3-dev py3-pip python3-tkinter jq curl build-base
}

command -v jq >/dev/null 2>&1 && { JQ=0; }

case "${OS_ID}" in

  debian)
    install_debian
    ;;

  fedora)
    install_fedora
    ;;

  centos)
    install_centos
    ;;

  arch)
    install_arch
    ;;

  alpine)
    install_alpine
    ;;

  linux)
    echo "It seems to be impossible to determine the distribution of the linux system through reading /etc/os-release."
    echo "Currently only the following distributions are supported: Debian, Kali, Ubuntu, Fedora, CentOS, Arch Linux, or Alpine."
    exit 1
    ;;

  *) # the default case
    echo "Looks like you are running this installer on ${OS_ID}."
    echo "Currently only the following distributions are supported: Debian, Kali, Ubuntu, Fedora, CentOS, Arch Linux, or Alpine."
    exit 1
    ;;
esac

TAG=$(curl https://api.github.com/repos/ThioJoe/YT-Spammer-Purge/releases/latest -s | jq .name -r)

if [ "full" == "${INSTALL_LEVEL}" ]; then
  curl https://codeload.github.com/ThioJoe/YT-Spammer-Purge/tar.gz/refs/tags/v${TAG} -o yt-spammer.tar.gz
  tar -xzf yt-spammer.tar.gz
  rm yt-spammer.tar.gz
  cd YT-Spammer-Purge-${TAG}/
fi
bash -c "pip3 install -r requirements.txt --user -q"
printf "Dependencies and Program installed!\nNow follow these instructions to get a client_secrets.json file!\nhttps://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key\n"
