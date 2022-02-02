#!/usr/bin/env bash
set -e

PYTHON_VERSIONS="${PYTHON_VERSIONS-3.6 3.7 3.8 3.9 3.10}"

install_with_pipx() {
    if ! command -v "$1" &>/dev/null; then
        if ! command -v pipx &>/dev/null; then
            python3 -m pip install --user pipx
        fi
        pipx install "$1"
    fi
}

install_with_pipx poetry

if [ -n "${PYTHON_VERSIONS}" ]; then
    for python_version in ${PYTHON_VERSIONS}; do
        if output=$(poetry env use "${python_version}" 2>&1); then
            if echo "${output}" | grep -q ^Creating; then
                echo "> Created environment for Python ${python_version}"
            else
                echo "> Using Python ${python_version} environment"
            fi
            poetry install
        else
            echo "> poetry env use ${python_version}: Python version not available?" >&2
        fi
    done
else
    poetry install
fi
