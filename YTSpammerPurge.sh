#!/usr/bin/env bash

ScriptDir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
$ScriptDir/venv/bin/python3 $ScriptDir/YTSpammerPurge.py
