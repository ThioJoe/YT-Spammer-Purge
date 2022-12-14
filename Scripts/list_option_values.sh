#!/usr/bin/env bash

# Just leading spaces are remvoed and placeholders with square brackets.
# Entries are separated via empty blank lines.
# Anything else is being unthouched.
get_values_and_options() {
  declare config_path="$1"

  awk 'BEGIN {
  values = "\\s+#\\s+Default\\s+=\\s+"
  option_or_values = "^(\\w" "|" values ")"

}

$0 ~ option_or_values {
  result = gensub(/\[[A-Za-z0-9 ]+\]/, "", "g", gensub(/\s+=.*/, "", "1", gensub(values, "", "1")))
  if (result !~ /--/)
    result = gensub(/$/, "\n\n", "1", result)
  
  print result
}' "$config_path"
}

declare config_path="../assets/default_config.ini"
declare values_and_options="$(get_values_and_options "$config_path")"
echo "$values_and_options"