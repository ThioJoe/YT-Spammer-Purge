BEGIN {
  RS = ""
  FS = "\n"

  print "{"
}


function join(array, start, end, sep,    result, i)
{
    if (sep == "")
       sep = " "
    else if (sep == SUBSEP) # magic value
       sep = ""
    result = array[start]
    for (i = start + 1; i <= end; i++)
        result = result sep array[i]
    return result
}

function get_internal_value_type(value)
{
  switch (value)
  {
    case /^true|false$/:
      return "boolean"
    case /^[-+]?[0-9]+$/:
      return "integer"
    case /^[-+]?[0-9]+\.[0-9]+$/:
      return "float"
    case /^\[[-+]?[0-9]+-[-+]?[0-9]+\]$/:
      return "closed_integer_range"
    case /^\[[-+]?[0-9]+\.[0-9]+-[-+]?[0-9]+\.[0-9]+\]$/:
      return "closed_float_range"
    case /^\[[-+]?[0-9]+-infinity\]$/:
      return "closed_open_integer_range"
    case /^\[[-+]?[0-9]+\.[0-9]+-infinity\]$/:
      return "closed_open_float_range"
    default:
      return "string";
  }
}

function get_json_value_type(internal_value_type)
{
  switch (value)
  {
    case "boolean":
      return "boolean"
    case "integer":
      return "integer"
    case "float":
      return "number"
    case "closed_integer_range":
      return "integer"
    case "closed_float_range":
      return "number"
    case "closed_open_integer_range":
      return "integer"
    case "closed_open_float_range":
      return "number"
    default:
      return "string";
  }
}

{
  option_name = $2
  option_values = $1
  if (!$2) {
    option_name = $1
    option_values = ""
    print "{ \"" option_name "\": { \"type\": \"string\" } }," # We assume that if no value is present than it is string.
  } else {
    option_values = gensub(/\s+(--|\|)\s+/, " ", "g", option_values)
    option_value_count = split(option_values, option_values_array, " ")

    # In JSON schema all keys will have lower case.
    for (key in option_values_array)
      option_values_array[key] = tolower(option_values_array[key])

    default_option_value = option_values_array[1]
    
    if (default_option_value ~ /^true|false$/)
      option_types[1] = "\"boolean\""
    else if (default_option_value ~ /^[0-9]+$/)
      option_types[1] = "\"integer\""
    else if (default_option_value ~ /^[0-9]+\.[0-9]+$/)
      option_types[1] = "\"number\""
    else
      option_types[1] = "\"string\""
  
    option_type_index = 2

    for (i = 2; i <= option_value_count; i++) {
      if (option_values_array[i] ~ /^true|false$/)
        type_to_add = "\"boolean\""
      else if (option_values_array[i] ~ /^[0-9]+$/)
        type_to_add = "\"integer\""
      else if (option_values_array[i] ~ /^[0-9]+\.[0-9]+$/)
        type_to_add = "\"number\""
      else
        type_to_add = "\"string\""

      type_is_already_added = 0
      for (j = 1; j < option_type_index; j++)
        if (option_types[j] == type_to_add)
          type_is_already_added = 1

      if (type_is_already_added == 0) {
        option_types[option_type_index] = type_to_add
        option_type_index++
      }
    }

    if (option_types[1] == "\"string\"")
      default_option_value = "\"" default_option_value "\""
    if (option_type_index - 1 == 1)
      print "{ \"" option_name "\": { \"type\": " option_types[1] ", \"default\": " default_option_value " } },"
    else {
      types = "[" join(option_types, 1, option_type_index - 1, ", ") "]"
      print "{ \"" option_name "\": { \"type\": " types ", \"default\": " default_option_value " } },"
    }

    delete option_values_array
    delete option_types
  }
}

END {
  print "}"
}