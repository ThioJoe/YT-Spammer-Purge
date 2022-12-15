#!/usr/bin/env bash

# Just leading spaces are removed and placeholders with square brackets.
# Entries are separated via empty blank lines.
# Anything else is being unthouched.
get_values_and_options() {
  declare config_path="$1"
  awk --file="./get_raw_property_representation.awk" "$config_path"
}

convert_to_json_properties() {
  declare raw_input="$1"
  awk --file="./get_json_property_representation.awk" <<< "$raw_input"
}

declare config_path="../assets/default_config.ini"
convert_to_json_properties "$(get_values_and_options "$config_path")"