#!/usr/bin/env bash

# Get the latest tagged version from the upstream repository
get_latest_version() {
    git remote add -f --tags upstream https://github.com/ThioJoe/YT-Spammer-Purge.git
    git checkout $(git describe --tags $(git rev-list --tags --max-count=1 --remotes=upstream))

}

install_uv() {
    # Check if UV is installed
    if ! command -v uv &> /dev/null; then
        echo "UV is not installed. Installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    else
        uv self update
    fi
}

# if the script is run with the argument "latest", get the latest version
if [ "$1" == "latest" ]; then
    get_latest_version
fi
git pull

install_uv

uv sync
uv lock
