#!/usr/bin/env bash
set -e

PYTHON_VERSIONS="${PYTHON_VERSIONS-3.6 3.7 3.8 3.9 3.10}"

if [ -n "${PYTHON_VERSIONS}" ]; then
    for python_version in ${PYTHON_VERSIONS}; do
        if output=$(poetry env use "${python_version}" 2>&1); then
            if echo "${output}" | grep -q ^Creating; then
                echo "> Environment for Python ${python_version} not created, skipping" >&2
                poetry env remove "${python_version}" &>/dev/null || true
            else
                echo "> poetry run $@ (Python ${python_version})"
                poetry run "$@"
            fi
        else
            echo "> poetry env use ${python_version}: Python version not available?" >&2
        fi
    done
else
    poetry run "$@"
fi
