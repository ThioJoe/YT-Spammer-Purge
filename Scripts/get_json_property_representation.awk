BEGIN {
  RS = ""
  FS = "\n"

  print "{"
}

function join(array, start, end, sep,    result, i) {
    if (sep == "")
       sep = " "
    else if (sep == SUBSEP) # magic value
       sep = ""
    result = array[start]
    for (i = start + 1; i <= end; i++)
        result = result sep array[i]
    return result
}

function get_internal_value_type(value) {
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

function get_json_value_type(internal_value_type) {
  switch (internal_value_type)
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

function is_value_in_array(array, value,    i) {
  for (i = 1; i <= length(array); i++)
    if (array[i] == value)
      return 1
  return 0
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
    split(option_values, option_values_array, " ")

    # In JSON schema all keys will have lower case.
    for (key in option_values_array)
      option_values_array[key] = tolower(option_values_array[key])

    default_option_value = option_values_array[1]
    option_types_array[1] = "\"" get_json_value_type(get_internal_value_type(default_option_value)) "\""
    default_option_value_type = option_types_array[1]
    
    option_type_index = 2

    option_has_range_value = 0
    range_constraints_json = ""

    split("", option_example_values)
    option_example_values_index = 1
    option_examples_json = ""

    for (i = 2; i <= length(option_values_array); i++) {
      internal_type_to_add = get_internal_value_type(option_values_array[i])
      type_to_add = "\"" get_json_value_type(internal_type_to_add) "\""

      if (internal_type_to_add ~ /range/ && !option_has_range_value) {
        option_has_range_value = 1 # Just first range is preserved

        range_constraints_json = ", "
        range = gensub(/\[|\]/, "", "g", option_values_array[i])
        split(range, range_array, "-")

        switch (internal_type_to_add) {
          case /closed_integer_range|closed_float_range/:
            range_constraints_json = range_constraints_json "\"minimum\": " range_array[1] ", \"maximum\": " range_array[2]
            break
          case /closed_open_integer_range|closed_open_float_range/:
            range_constraints_json = range_constraints_json "\"minimum\": " range_array[1]
            break
        }
      }

      if (option_values_array[i] ~ /^<.*>$/) {
        option_example_value = gensub(/<|>/, "", "g", option_values_array[i])
        if (type_to_add == "\"string\"")
          option_example_value = "\"" option_example_value "\""

        if (!is_value_in_array(option_example_values, option_example_value)) {
          option_example_values[option_example_values_index] = option_example_value
          option_example_values_index++
        }
      }

      if (!is_value_in_array(option_types_array, type_to_add)) {
        option_types_array[option_type_index] = type_to_add
        option_type_index++
      }
    }

    if (length(option_example_values))
      option_examples_json = ", \"examples\": [" join(option_example_values, 1, length(option_example_values), ", ") "]"

    if (option_types_array[1] == "\"string\"")
      default_option_value = "\"" default_option_value "\""
    if (length(option_types_array) == 1)
      print "{ \"" option_name "\": { \"type\": " default_option_value_type ", \"default\": " default_option_value range_constraints_json option_examples_json " } },"
    else {
      types = "[" join(option_types_array, 1, option_type_index - 1, ", ") "]"
      print "{ \"" option_name "\": { \"type\": " types ", \"default\": " default_option_value range_constraints_json option_examples_json " } },"
    }

    delete option_values_array
    delete option_types_array
    delete option_example_values
  }
}

END {
  print "{}\n}" # Add dummy trailing empty object to make JSON syntax correct
}