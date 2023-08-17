#!/usr/bin/env sh

in_restrictions="$1"

key="$(echo "$in_restrictions" | jq '.key')"
echo "$in_restrictions" | jq -r "del(.key) | to_entries[] | . = \"--arg \($key)_\(.key) \(.value)\""
