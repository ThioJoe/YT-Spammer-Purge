BEGIN
{
  values = "\\s+#\\s+Default\\s+=\\s+"
  option = "[A-Za-z]"
  option_or_values = "^(" option "|" values ")"
}

$0 ~ option_or_values
{
  # Even it's applied for both strings: documentation and option one, it has effect just for the first one.
  cleaned_up_documentation = gensub(/Possible Values:|Possible:|Example Values:/, "", "g", gensub(/\[[A-Za-z0-9 ]+\]/, "", "g", gensub(/\s+=.*/, "", "1", gensub(values, "", "1"))))
  documentation = "--"

  if (cleaned_up_documentation !~ documentation)
    cleaned_up_documentation = gensub(/$/, "\n", "1", cleaned_up_documentation)
  
  print cleaned_up_documentation
}