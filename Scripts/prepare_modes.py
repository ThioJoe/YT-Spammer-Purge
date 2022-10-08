#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Scripts.shared_imports import *
from Scripts.gui import *
from Scripts.utils import choice, make_char_set
import Scripts.utils as utils
import Scripts.validation as validation
import Scripts.auth as auth
import Scripts.operations as operations
import Scripts.files as files
import Scripts.filter_variables as filter

from Scripts.confusablesCustom import confusable_regex, normalize
from base64 import b85decode as b64decode
import pathlib

##########################################################################################
################################## FILTERING MODES #######################################
##########################################################################################

# For scanning for individual chars
def prepare_filter_mode_chars(scanMode, filterMode, config):
  if filterMode == "Username":
    whatToScanMsg = "Usernames"
  elif filterMode == "Text":
    whatToScanMsg = "Comment Text"
  elif filterMode == "NameAndText":
    whatToScanMsg = "Usernames and Comment Text"

  if config['characters_to_filter'] != "ask":
    print("Characters to filter obtained from config file.")
    pass
  else:
    print(f"\nNext, you will input {FOREGROUND_TEXT_COLOR.YELLOW}ONLY{TEXT_STYLE.RESET_ALL} any special characters / emojis you want to search for in all {whatToScanMsg}. Do not include commas or spaces!")
    print("          Note: Letters, numbers, and basic punctuation will not be included for safety purposes, even if you enter them.")
    print("          Example: 👋🔥✔️✨")
    input(f"\nPress {FOREGROUND_TEXT_COLOR.LIGHTGREEN_EX}Enter{TEXT_STYLE.RESET_ALL} to open the {FOREGROUND_TEXT_COLOR.LIGHTGREEN_EX}text entry window{TEXT_STYLE.RESET_ALL}...")
    print("-------------------------------------------")

  confirm = False
  validConfigSetting = True
  while confirm == False:
    if validConfigSetting == True and config and config['characters_to_filter'] != "ask":
      inputChars = make_char_set(config['characters_to_filter'], stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=True)
      bypass = True
    else:
      bypass = False
      print(f"\nWaiting for input Window. Press {FOREGROUND_TEXT_COLOR.MAGENTA}'Execute'{TEXT_STYLE.RESET_ALL} after entering valid characters to continue...", end="\r")
      try:
        # Takes in user input of characters, returns 'set' of characters stripped of specified characters
        inputChars = take_input_gui(mode="chars", stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=True)
      except NameError: # Catch if user closes GUI window, exit program.
        print("                                                                                          ") # Clears the line because of \r on previous print
        print("\nError Code G-1: Something went wrong with the input, or you closed the window improperly.")
        print("If this keeps happening inexplicably, consider filing a bug report here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
        input("Press Enter to exit...")
        sys.exit()

    print(f"     {whatToScanMsg} will be scanned for {FOREGROUND_TEXT_COLOR.MAGENTA}ANY{TEXT_STYLE.RESET_ALL} of the characters you entered in the previous window.")
    userChoice = choice("Begin Scanning? ", bypass)
    if userChoice == True:
      confirm = True
    elif userChoice == False:
      confirm = False
      validConfigSetting = False
    elif userChoice == None:
      return "MainMenu", None

  return inputChars, None

# For scanning for strings
def prepare_filter_mode_strings(scanMode, filterMode, config):
  if filterMode == "Username":
    whatToScanMsg = "Usernames"
  elif filterMode == "Text":
    whatToScanMsg = "Comment Text"
  elif filterMode == "NameAndText":
    whatToScanMsg = "Usernames and Comment Text"

  if config['strings_to_filter'] != "ask":
    print("Strings to filter obtained from config file.")
    pass
  else:
    print(f"\nPaste or type in a list of any {FOREGROUND_TEXT_COLOR.YELLOW}comma separated strings{TEXT_STYLE.RESET_ALL} you want to search for in {whatToScanMsg}. (Not case sensitive)")
    print("   >Note: If the text you paste includes special characters or emojis, they might not display correctly here, but it WILL still search them fine.")
    print("          Example Input: whatsapp, whatever multiple words, investment")

  validEntry = False
  validConfigSetting = True
  while validEntry == False:
    if validConfigSetting == True and config and config['strings_to_filter'] != "ask":
      inputString = config['strings_to_filter']
      bypass = True
    else:
      bypass = False
      inputString = input("Input Here: ")
      if str(inputString).lower() == "x":
        return "MainMenu", None

    # Convert comma separated string into list with function, then check against current user's name
    filterStringList = utils.string_to_list(inputString, lower=True)
    if len(filterStringList) > 0:
      validEntry = True
    else:
      validConfigSetting = False

    if validEntry == True:
      if config['strings_to_filter'] != "ask":
        pass
      else:
        print(f"     {whatToScanMsg} will be scanned for {FOREGROUND_TEXT_COLOR.MAGENTA}ANY{TEXT_STYLE.RESET_ALL} of the following strings:")
        print(filterStringList)
      userChoice = choice("Begin scanning? ", bypass)
      if userChoice == True:
        validEntry = True
      elif userChoice == False:
        validEntry = False
      elif userChoice == None:
        return "MainMenu", None

  return filterStringList, None

# For scanning for regex expression
def prepare_filter_mode_regex(scanMode, filterMode, config):
  if filterMode == "Username":
    whatToScanMsg = "Usernames"
  elif filterMode == "Text":
    whatToScanMsg = "Comment Text"
  elif filterMode == "NameAndText":
    whatToScanMsg = "Usernames and Comment Text"

  if config['regex_to_filter'] != "ask":
    print("Regex expression obtained from config file.")
    validConfigSetting = True
  else:
    print(f"Enter any {FOREGROUND_TEXT_COLOR.YELLOW}regex expression{TEXT_STYLE.RESET_ALL} to search within {whatToScanMsg}.")
    print(r"          Example Input:  [^\x00-\xFF]")
    validConfigSetting = False
  validExpression = False

  while validExpression == False:
    if validConfigSetting == True and config and config['regex_to_filter'] != "ask":
      inputtedExpression = config['regex_to_filter']
      bypass = True
    else:
      inputtedExpression = input("Input Expression Here:  ")
      if str(inputtedExpression).lower() == "x":
        return "MainMenu", None
      bypass = False

    validationResults = validation.validate_regex(inputtedExpression) # Returns tuple of valid, and processed expression
    validExpression = validationResults[0]

    if validExpression == True:
      processedExpression = validationResults[1]
      print(f"     The expression appears to be {FOREGROUND_TEXT_COLOR.GREEN}valid{TEXT_STYLE.RESET_ALL}!")

      if validExpression == True:
        userChoice = choice("Begin scanning? ", bypass)
        if userChoice == True:
          pass
        elif userChoice == False:
          validExpression = False
          validConfigSetting = False
        elif userChoice == None:
          return "MainMenu", None
    else:
      print(f"     {FOREGROUND_TEXT_COLOR.RED}Error{TEXT_STYLE.RESET_ALL}: The expression appears to be {FOREGROUND_TEXT_COLOR.RED}invalid{TEXT_STYLE.RESET_ALL}!")
      validConfigSetting = False

  return processedExpression, None

# Filter Mode: User manually enters ID
# Returns inputtedSpammerChannelID
def prepare_filter_mode_ID(scanMode, config):
  processResult = (False, None) #Tuple, first element is status of validity of channel ID, second element is channel ID
  validConfigSetting = True
  while processResult[0] == False:
    if validConfigSetting == True and config and config['channel_ids_to_filter'] != "ask":
      inputtedSpammerChannelID = config['channel_ids_to_filter']
      bypass = True
    else:
      bypass = False
      inputtedSpammerChannelID = input(f"Enter the {FOREGROUND_TEXT_COLOR.LIGHTRED_EX} Channel link(s) or ID(s){TEXT_STYLE.RESET_ALL} of the spammer (comma separated): ")
      if str(inputtedSpammerChannelID).lower() == "x":
        return "MainMenu", None

    processResult = utils.process_spammer_ids(inputtedSpammerChannelID)
    if processResult[0] == True:
      inputtedSpammerChannelID = processResult[1] # After processing, if valid, inputtedSpammerChannelID is a list of channel IDs
    else:
      validConfigSetting = False
  print("\n")

  # Check if spammer ID and user's channel ID are the same, and warn
  # If using channel-wide scanning mode, program will just ignore those comments
  if any(auth.CURRENTUSER.id == i for i in inputtedSpammerChannelID):
    print(f"{BACKGROUND_TEXT_COLOR.RED}{FOREGROUND_TEXT_COLOR.WHITE} WARNING: {TEXT_STYLE.RESET_ALL} - You entered your own channel ID!")
    print(f"For safety purposes, this program always {FOREGROUND_TEXT_COLOR.YELLOW}ignores{TEXT_STYLE.RESET_ALL} your own comments.")

    if config['channel_ids_to_filter'] != "ask":
      pass
    else:
      input("\nPress Enter to continue...")

  return inputtedSpammerChannelID, None

# For Filter mode auto-ascii, user inputs nothing, program scans for non-ascii
def prepare_filter_mode_non_ascii(scanMode, config):

  print("\n-------------------------------------------------- ASCII Mode--------------------------------------------------")
  print("~~~ This mode automatically searches for usernames that contain special characters (aka not letters/numbers) ~~~\n")
  print("Choose the sensitivity level of the filter. You will be shown examples after you choose.")
  print(f"   1. Allow {FOREGROUND_TEXT_COLOR.LIGHTMAGENTA_EX}Standard + Extended ASCII{TEXT_STYLE.RESET_ALL}:    Filter rare unicode & Emojis only")
  print(f"   2. Allow {FOREGROUND_TEXT_COLOR.LIGHTMAGENTA_EX}Standard ASCII only{TEXT_STYLE.RESET_ALL}:  Also filter semi-common foreign characters")
  print(f"   3. {FOREGROUND_TEXT_COLOR.LIGHTRED_EX}NUKE Mode (┘°□°)┘≈ ┴──┴ :    Allow ONLY numbers, letters, and spaces{TEXT_STYLE.RESET_ALL}")
  print("")

  # Get user input for mode selection,
  confirmation = False
  validConfigSetting = True
  while confirmation == False:
    if validConfigSetting == True and config and config['autoascii_sensitivity'] != "ask":
      selection = config['autoascii_sensitivity']
      bypass = True
    else:
      bypass = False
      selection = input("Choose Mode: ")
      if str(selection).lower() == "x":
        return "MainMenu", None
    if selection == "1":
      print(f"Searches for {FOREGROUND_TEXT_COLOR.YELLOW}usernames with emojis, unicode symbols, and rare foreign characters{TEXT_STYLE.RESET_ALL} such as: ✔️ ☝️ 🡆 ▲ π Ɲ Œ")
      userChoice = choice("Choose this mode?", bypass)
      if userChoice == True:
        regexPattern = r"[^\x00-\xFF]"
        confirmation = True
      elif userChoice == None:
        return "MainMenu", None
    elif selection == "2":
      print(f"Searches for {FOREGROUND_TEXT_COLOR.YELLOW}usernames with anything EXCEPT{TEXT_STYLE.RESET_ALL} the following: {FOREGROUND_TEXT_COLOR.YELLOW}Letters, numbers, punctuation, and common special characters{TEXT_STYLE.RESET_ALL} you can type with your keyboard like: % * & () + ")
      userChoice = choice("Choose this mode?", bypass)
      if userChoice == True:
        regexPattern = r"[^\x00-\x7F]"
        confirmation = True
      elif userChoice == None:
        return "MainMenu", None
    elif selection == "3":
      print(f"Searches for {FOREGROUND_TEXT_COLOR.YELLOW}usernames with anything EXCEPT letters, numbers, and spaces{TEXT_STYLE.RESET_ALL} - {BACKGROUND_TEXT_COLOR.RED}{FOREGROUND_TEXT_COLOR.WHITE} EXTREMELY LIKELY to cause collateral damage!{TEXT_STYLE.RESET_ALL} Recommended to just use to manually gather list of spammer IDs, then use a different mode to delete.")
      userChoice = choice("Choose this mode?", bypass)
      if userChoice == True:
        regexPattern = r"[^a-zA-Z0-9 ]"
        confirmation = True
      elif userChoice == None:
        return "MainMenu", None
    else:
      print(f"Invalid input: {selection} - Must be 1, 2, or 3.")
      validConfigSetting = False

  if selection == "1":
    autoModeName = "Allow Standard + Extended ASCII"
  elif selection == "2":
    autoModeName = "Allow Standard ASCII only"
  elif selection == "3":
    autoModeName = "NUKE Mode (┘°□°)┘≈ ┴──┴ - Allow only letters, numbers, and spaces"

  if confirmation == True:
    return regexPattern, autoModeName
  else:
    input("How did you get here? Something very strange went wrong. Press Enter to Exit...")
    sys.exit()

# Auto smart mode
def prepare_filter_mode_smart(scanMode, config, miscData, sensitive=False):
  rootDomainList = miscData.resources['rootDomainList']
  spamDomainsList = miscData.spamLists['spamDomainsList'] # List of domains from crowd sourced list
  #spamThreadsList = miscData.spamLists['spamThreadsList'] # List of filters associated with spam threads from crowd sourced list
  spamAccountsList = miscData.spamLists['spamAccountsList'] # List of mentioned instagram/telegram scam accounts from crowd sourced list
  utf_16 = "utf-8"
  if config['filter_mode'] == "autosmart":
    pass
  else:
    if sensitive:
      print("\n----------------------------------------------- Sensitive-Smart Mode -----------------------------------------------")
    else: # if not sensitive
      print("\n----------------------------------------------- Auto-Smart Mode -----------------------------------------------")
    print(f"~~~ This mode is a {FOREGROUND_TEXT_COLOR.LIGHTCYAN_EX}spammer's worst nightmare{TEXT_STYLE.RESET_ALL}. It automatically scans for multiple spammer techniques ~~~\n")
    print(" > Extremely low (near 0%) false positives")
    print(" > Detects whatsapp scammers and '18+ spam' bots")
    print(" > Easily cuts through look-alike characters and obfuscations, including impersonating usernames")
    if sensitive == False:
      print(f" > {FOREGROUND_TEXT_COLOR.LIGHTRED_EX}NOTE:{TEXT_STYLE.RESET_ALL} This mode prioritizes a {FOREGROUND_TEXT_COLOR.LIGHTGREEN_EX}VERY low false positive rate{TEXT_STYLE.RESET_ALL}, at the cost of occasionally missing some spammers.\n")
    elif sensitive == True:
      print(f" > {FOREGROUND_TEXT_COLOR.LIGHTRED_EX}NOTE:{TEXT_STYLE.RESET_ALL} In sensitive mode, {FOREGROUND_TEXT_COLOR.LIGHTRED_EX}expect more false positives{TEXT_STYLE.RESET_ALL}. Recommended to run this AFTER regular Auto Smart Mode.\n")
    input("Press Enter to Begin Scanning...")
    print ("\033[A                                     \033[A") # Erases previous line
  print("  Loading Filters  [                              ]", end="\r")

  # Create Variables
  compiledRegexDict = {
    'usernameBlackWords': filter.usernameBlackWordsCompiled,
    'usernameNovidBlackWords': filter.usernameNovidBlackWordsCompiled,
    'blackAdWords': filter.blackAdWordsCompiled,
    'redAdWords': filter.redAdWordsCompiled,
    'yellowAdWords': filter.yellowAdWordsCompiled,
    'usernameRedWords': filter.usernameRedWordsCompiled,
    'textBlackWords': filter.textBlackWordsCompiled,
    'doubledSusWords': filter.doubledSusWordsCompiled,
  }

  preciseRegexDict = {
    'textExactBlackWords': re.compile(filter.textExactBlackWords),
    'textUpLowBlackWords': re.compile(filter.textUpLowBlackWords),
    'exactRedAdWords': re.compile(filter.exactRedAdWords),
  }

  compiledObfuRegexDict = {
    'textObfuBlackWords': filter.textObfuBlackWordsCompiledPairs,
    'usernameObfuBlackWords': filter.usernameObfuBlackWordsCompiledPairs
  }

  # General Settings
  unicodeCategoriesStrip = ["Mn", "Cc", "Cf", "Cs", "Co", "Cn", "Sk"] # Categories of unicode characters to strip during normalization

  # Create General Lists
  spamGenEmojiSet = make_char_set(filter.spamGeneralEmoji)
  lowAlSet = make_char_set('abcdefghijklmnopqrstuvwxyz')

  # Type 1 Spammer Criteria
  minNumbersMatchCount = 6 # Choice of minimum number of matches from spamNums before considered spam

  x = filter.spamNums
  y = filter.spamPlus
  z = filter.spamOne

  # Prepare Filters for Type 1 Spammers
  spammerNumbersSet = make_char_set(x)
  regexTest1 = f"[{y}] ? ?[1]"
  regexTest2 = f"[+] ? ?[{z}]"
  regexTest3 = f"[{y}] ? ?[{z}]"
  compiledNumRegex = re.compile(f"({regexTest1}|{regexTest2}|{regexTest3})")
  compiledAllNumRegex = re.compile("|".join(list(filter.spamNums)))
  phoneRegexCompiled = re.compile(filter.phoneRegex)
  bigNumCheckRegexCompiled = re.compile(filter.bigNumCheckRegex)

  # Prepare Filters for Type 2 Spammers
  redAdEmojiSet = make_char_set(filter.redAdEmoji)
  yellowAdEmojiSet = make_char_set(filter.yellowAdEmoji)
  hrtSet = make_char_set(filter.hrt)

  # Prepare Regex to detect nothing but video link in comment
  onlyVideoLinkRegex = re.compile(r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$")
  compiledRegexDict['onlyVideoLinkRegex'] = onlyVideoLinkRegex

  # Compile Thread Detection Regex
  nameRegex = re.compile(rf'\b{filter.salutationRegex}\s+([a-zA-Z]+\.?)\s+([a-zA-Z]+)')
  nakedNameRegex = re.compile(rf'\b{filter.nakedNamePreRegex}\s+([a-zA-Z]+\.?)\s+([a-zA-Z]+)')
  cashRegex = re.compile(r"((\$|£|€)((\d*( ?k))|((\d{3,})|(\d{1,3}((,|\.)\d{3}){1,}))))|(((\d*( ?k))|(((\d{3,})|(\d{1,3}(,|\.\d{3})))))(\$|£|€| ?u\.?s\.?d\.?| ?eur| ?btc| ?u.?s.? dollar))")

  threadFiltersDict = {
    'threadWordsRegex': re.compile(filter.threadWordsRegex),
    'threadPhrasesRegex': re.compile(filter.threadPhrasesRegex),
    'monetWordsRegex': re.compile(filter.monetWordsRegex),
    'salutationRegex': re.compile(r"\b" + filter.salutationRegex),
    'nameRegex': nameRegex,
    'nakedNameRegex': nakedNameRegex,
    'cashRegex': cashRegex,
  }

  print("  Loading Filters  [======                        ]", end="\r")

  # Compile regex with upper case, otherwise many false positive character matches
  bufferChars = r"*_~|`[]()'-.•,"
  compiledRegexDict['bufferChars'] = bufferChars
  bufferMatch, addBuffers = "\\*_~|`\\-\\.", re.escape(bufferChars) # Add 'buffer' chars
  usernameConfuseRegex = re.compile(confusable_regex(miscData.channelOwnerName))
  m = bufferMatch
  a = addBuffers
  

  print("  Loading Filters  [==============                ]", end="\r")

  # Prepare All-domain Regex Expression
  prepString = "\.("
  first = True
  for extension in rootDomainList:
    if first == True:
        prepString += extension
        first = False
    else:
        prepString = prepString + "|" + extension
  sensitivePrepString = prepString + ")"
  prepString = prepString + ")\/"
  rootDomainRegex = re.compile(prepString)
  sensitiveRootDomainRegex = re.compile(sensitivePrepString)
  print("  Loading Filters  [===================           ]", end="\r")

  spamListExpressionsList = []
  # Prepare spam domain regex
  for domain in spamDomainsList:
    spamListExpressionsList.append(confusable_regex(domain.upper().replace(".", "⚫"), include_character_padding=False).replace("(?:⚫)", "(?:[^a-zA-Z0-9 ]{1,2})"))
  for account in spamAccountsList:
    spamListExpressionsList.append(confusable_regex(account.upper(), include_character_padding=True).replace(m, a))
  # for thread in spamThreadsList:
  #   spamListExpressionsList.append(confusable_regex(thread.upper(), include_character_padding=True).replace(m, a))
  print("  Loading Filters  [======================        ]", end="\r")
  spamListCombinedRegex = re.compile('|'.join(spamListExpressionsList))

  # Prepare Multi Language Detection
  turkish = 'ÇçŞşĞğİ'
  germanic = 'ẞßÄä'
  cyrillic = "гджзклмнпрстфхцчшщыэюяъь"
  japanese = 'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヷヸヹヺーヽヾヿぁあぃいぅうぇえぉおかがきぎぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞゟ'
  languages = [['turkish', turkish, []], ['germanic', germanic, []], ['cyrillic', cyrillic, []], ['japanese', japanese, []]]
  for item in languages:
    item[2] = make_char_set(item[1])
  print("  Loading Filters  [============================  ]", end="\r")


  filterSettings = {
    'spammerNumbersSet': spammerNumbersSet,
    'compiledNumRegex': compiledNumRegex,
    'compiledAllNumRegex': compiledAllNumRegex,
    'minNumbersMatchCount': minNumbersMatchCount,
    'phoneRegexCompiled': phoneRegexCompiled,
    'bigNumCheckRegexCompiled': bigNumCheckRegexCompiled,
    #'usernameBlackCharsSet': usernameBlackCharsSet,
    'spamGenEmojiSet': spamGenEmojiSet,
    'redAdEmojiSet': redAdEmojiSet,
    'yellowAdEmojiSet': yellowAdEmojiSet,
    'hrtSet': hrtSet,
    'lowAlSet': lowAlSet,
    'rootDomainRegex': rootDomainRegex,
    'compiledRegexDict': compiledRegexDict,
    'compiledObfuRegexDict': compiledObfuRegexDict,
    'preciseRegexDict': preciseRegexDict,
    'usernameConfuseRegex': usernameConfuseRegex,
    'languages': languages,
    'sensitive': sensitive,
    'sensitiveRootDomainRegex': sensitiveRootDomainRegex,
    'unicodeCategoriesStrip': unicodeCategoriesStrip,
    'spamListCombinedRegex': spamListCombinedRegex,
    'threadFiltersDict': threadFiltersDict
    }
  print("                                                                 ") # Erases line that says "loading filters"

  return filterSettings, None



##########################################################################################
################################# LIST MODES  ############################################
##########################################################################################


################################ RECOVERY MODE ###########################################
def recover_deleted_comments(config):
  print(f"\n\n-------------------- {FOREGROUND_TEXT_COLOR.LIGHTGREEN_EX}Comment Recovery Mode{TEXT_STYLE.RESET_ALL} --------------------\n")
  print("> Believe it or not, the YouTube API actually allows you to re-instate \"deleted\" comments.")
  print(f"> This is {FOREGROUND_TEXT_COLOR.YELLOW}only possible if you have stored the comment IDs{TEXT_STYLE.RESET_ALL} of the deleted comments, \n   such as {FOREGROUND_TEXT_COLOR.YELLOW}having kept the log file{TEXT_STYLE.RESET_ALL} of that session.")
  print("> If you don't have the comment IDs you can't recover the comments, and there is no way to find them. \n")

  recoveryList, listFileName = files.parse_comment_list(config, recovery=True)
  if recoveryList == "MainMenu":
    return "MainMenu"

  operations.delete_found_comments(commentsList=recoveryList, banChoice=False, deletionMode="published", recoveryMode=True)
  operations.check_recovered_comments(commentsList=recoveryList)

################################ DELETE COMMENT LIST ###########################################
def delete_comment_list(config):
  progressDict = dict()
  progressFileFolder = os.path.join(RESOURCES_FOLDER_NAME, "Removal_List_Progress")
  print(f"\n\n-------------------- {FOREGROUND_TEXT_COLOR.LIGHTRED_EX}Delete Using a List / Log{TEXT_STYLE.RESET_ALL} --------------------")
  while True:
    print("\nUse new comment list, or continue where you left off with another list?")
    print(f"  1. Use {FOREGROUND_TEXT_COLOR.LIGHTCYAN_EX}New List{TEXT_STYLE.RESET_ALL}")
    print(f"  2. {FOREGROUND_TEXT_COLOR.LIGHTMAGENTA_EX}Continue With{TEXT_STYLE.RESET_ALL} a List")
    listChoice = input("\nSelection (1 or 2): ")
    if listChoice == "1" or listChoice == "2":
      break
    else:
      print(f"\n{FOREGROUND_TEXT_COLOR.LIGHTRED_EX}Invalid selection!{TEXT_STYLE.RESET_ALL} Please try again.")

  if listChoice == "1":
    continued = False
    previousRemovedComments=set()
    remainingCommentsSet = set()
    previousFailedComments = list()
    sessionNum = 1

    removalList, listFileNameBase = files.parse_comment_list(config, removal=True, returnFileName=True)
    if removalList == "MainMenu":
      return "MainMenu"

    progressFileName = listFileNameBase + "_removal_progress.save"

  if listChoice == "2":
    continued = True
    valid = False

    # Use existing save if available
    existingSavesList = files.check_existing_save()
    if len(existingSavesList) > 0:
      if len(existingSavesList) == 1:
        saveChoice = existingSavesList[0]
        print(f"\n{FOREGROUND_TEXT_COLOR.LIGHTGREEN_EX}Using existing save: {TEXT_STYLE.RESET_ALL}{saveChoice}")
      elif len(existingSavesList) > 1:
        print("\nWhich save file would you like to use?")
        for i, save in enumerate(existingSavesList):
          print(f"  {i+1}. {save[:-22]}")
        # Take and Validate Input
        while valid == False:
          saveChoice = input(f"\nSelection (1-{len(existingSavesList)}): ")
          if saveChoice.isdigit() and int(saveChoice) > 0 and int(saveChoice) <= len(existingSavesList):
            saveChoice = existingSavesList[int(saveChoice)-1]
            valid = True
          elif saveChoice.lower() == "x":
            return "MainMenu"
          else:
            print(f"\n{FOREGROUND_TEXT_COLOR.RED}Invalid Selectionp{TEXT_STYLE.RESET_ALL}. Please try again.")
      progressFileName = saveChoice
      progressFileNameWithPath = os.path.join(progressFileFolder, progressFileName)
      progressDict = files.read_dict_pickle_file(progressFileName, progressFileFolder)
      valid = True
      removalList = "Loaded"

    else:
      print(f"\n{FOREGROUND_TEXT_COLOR.RED}No previous saves found!{TEXT_STYLE.RESET_ALL}")
      input("\nPress Enter to return to Main Menu...")
      return "MainMenu"


    while valid == False:
      input(f"\nNext, follow the process by loading {FOREGROUND_TEXT_COLOR.YELLOW}the same comment list/log you used before{TEXT_STYLE.RESET_ALL}. Press Enter to continue...")
      removalList, listFileNameBase = files.parse_comment_list(config, removal=True, returnFileName=True)
      if removalList == "MainMenu":
        return "MainMenu"

      # Read pickle into dictionary of deleted and non-deleted files from last time
      print("\nChecking for saved progress file...")
      progressFileName = listFileNameBase + "_removal_progress.save"
      progressFileNameWithPath = os.path.join(progressFileFolder, progressFileName)
      if os.path.isfile(progressFileNameWithPath):
        progressDict = files.read_dict_pickle_file(progressFileName, progressFileFolder)
        valid = True
      else:
        print(f"\n{FOREGROUND_TEXT_COLOR.LIGHTRED_EX}Error:{TEXT_STYLE.RESET_ALL} No progress file found for that log file. Try again.")

    # Get data from list
    lastSessionNum = int(len(progressDict))
    previousRemovedComments = set(progressDict[lastSessionNum]['removed'])
    remainingCommentsSet = set(progressDict[lastSessionNum]['notRemoved'])
    previousFailedComments = progressDict[lastSessionNum]['failedCommentsList']
    sessionNum = int(len(progressDict))+1

    if removalList == "Loaded" or (len(remainingCommentsSet) + len(previousRemovedComments) + len(previousFailedComments)) == len(removalList):
      pass
    else:
      print(f"{FOREGROUND_TEXT_COLOR.LIGHTRED_EX}Error:{TEXT_STYLE.RESET_ALL} The length of the comment list you loaded doesn't match the comment list you saved last time.")
      if choice(f"{FOREGROUND_TEXT_COLOR.YELLOW}Continue anyway?{TEXT_STYLE.RESET_ALL} (Will use previous save and ignore the file you just loaded)") != True:
        return "MainMenu"

    # Display status of loaded file
    prevRemovedNum = len(previousRemovedComments)
    prevNotRemovedNum = len(remainingCommentsSet)
    prevFailedNum = len(previousFailedComments)

    print(f"\n {FOREGROUND_TEXT_COLOR.LIGHTCYAN_EX}----------------------- Loaded Saved Comment List Status -----------------------{TEXT_STYLE.RESET_ALL}")
    print(f" {FOREGROUND_TEXT_COLOR.LIGHTGREEN_EX}{prevRemovedNum} removed{TEXT_STYLE.RESET_ALL}  |  {FOREGROUND_TEXT_COLOR.YELLOW}{prevNotRemovedNum} not removed yet{TEXT_STYLE.RESET_ALL}  |  {FOREGROUND_TEXT_COLOR.LIGHTRED_EX}{prevFailedNum} failed to be removed{TEXT_STYLE.RESET_ALL}")
    input("\n Press Enter to continue...")

    # Set removal list based on previous save
    removalList = list(remainingCommentsSet)
    if len(previousFailedComments)>0:
      print(f"{FOREGROUND_TEXT_COLOR.LIGHTRED_EX}NOTE:{TEXT_STYLE.RESET_ALL} During previous sessions, {FOREGROUND_TEXT_COLOR.LIGHTRED_EX}{len(previousFailedComments)} comments{TEXT_STYLE.RESET_ALL} failed to be deleted.")
      failChoice = choice(f"\n{FOREGROUND_TEXT_COLOR.YELLOW}Add these back into the list{TEXT_STYLE.RESET_ALL} to try again? (Otherwise will skip them for later) ")
      if failChoice == True:
        removalList = removalList + list(previousFailedComments)
        previousFailedComments = list()
      else:
        removalList = list(remainingCommentsSet)

    print(f"\n Loaded {FOREGROUND_TEXT_COLOR.YELLOW}{len(removalList)} Remaining Comments{TEXT_STYLE.RESET_ALL}")

  # --- Begin removal process using list ------
  print("\nWhat do you want to do with the comments in the list?")
  print(f"1. {FOREGROUND_TEXT_COLOR.LIGHTRED_EX}Delete{TEXT_STYLE.RESET_ALL} them")
  print(f"2. {FOREGROUND_TEXT_COLOR.LIGHTMAGENTA_EX}Hide{TEXT_STYLE.RESET_ALL} them for review")

  validInput = False
  while validInput == False:
    userChoice = input("\nSelection (1 or 2): ")
    if userChoice == "1":
      removalMode = "rejected"
      validInput = True
    elif userChoice == "2":
      removalMode = "heldForReview"
      validInput = True
      banChoice = False
    elif userChoice == "99": # For Testing
      removalMode = "reportSpam"
      banChoice = False
      validInput = True
    elif userChoice.lower() == "x":
      return "MainMenu"
    else:
      print(f"{FOREGROUND_TEXT_COLOR.RED}Invalid input, try again.{TEXT_STYLE.RESET_ALL}")
  if removalMode == "rejected":
    banChoice = choice(f"Also {FOREGROUND_TEXT_COLOR.RED}ban{TEXT_STYLE.RESET_ALL} the commenters?")
    if str(banChoice).lower() == "x":
      return "MainMenu"

  # Set limit based on quota
  quotaLimit = int(config['quota_limit'])-100

  validInput = False
  while validInput == False:
    print(f"\n{FOREGROUND_TEXT_COLOR.YELLOW}How many comments{TEXT_STYLE.RESET_ALL} (out of {len(removalList)}) do you want to remove this session? (Input '0' or 'all' to do them all)")
    countChoice = input(f"\nNumber of comments (1-{str(quotaLimit)}): ")
    if countChoice.lower() == "all" or countChoice == "0":
        countChoice = len(removalList)
    try:
        countChoice = int(countChoice)
        if countChoice > 0 and countChoice <= quotaLimit:
          validInput = True
        elif countChoice >= quotaLimit:
          print(f"\n{FOREGROUND_TEXT_COLOR.LIGHTRED_EX}Error:{TEXT_STYLE.RESET_ALL} {countChoice} is too many comments, you'll run out of API Quota. Read Here: {FOREGROUND_TEXT_COLOR.YELLOW}TJoe.io/api-limit-info{TEXT_STYLE.RESET_ALL}")
        else:
          print(f"Invalid input, must be 'all' or a whole number from 1 to {str(quotaLimit)}.")
    except:
      print(f"{FOREGROUND_TEXT_COLOR.RED}Invalid input, must be a whole number.{TEXT_STYLE.RESET_ALL} Try again.")

  # Extract selected amount of comment IDs from list
  if countChoice >= len(removalList):
    partial = False
  else:
    partial = True

  if partial == True:
    selectedRemovalList = removalList[:countChoice]
    notRemovedList = removalList[countChoice:]
  else:
    selectedRemovalList = removalList
    notRemovedList = list()

  input(f"\nPress {FOREGROUND_TEXT_COLOR.YELLOW}Enter{TEXT_STYLE.RESET_ALL} to Begin Removal...")
  failedCommentsList = operations.delete_found_comments(commentsList=selectedRemovalList, banChoice=banChoice, deletionMode=removalMode)

  ### Handle Results ###
  if len(failedCommentsList) > 0:
    print(f"\n{FOREGROUND_TEXT_COLOR.LIGHTRED_EX}Warning!{TEXT_STYLE.RESET_ALL} {len(failedCommentsList)} comments apparently failed to be removed. They'll be saved to be tried later.")
    input("\nPress Enter to continue...")
    failedCommentsSet = set(failedCommentsList)
  else:
    failedCommentsSet = set()

  selectedRemovalSet = set(selectedRemovalList)
  remainingCommentsSet = set(notRemovedList)

  # Calculating final results for save progress file
  if len(failedCommentsSet) > 0:
    partial = True
    finalRemovedSet = selectedRemovalSet - failedCommentsSet
  else:
    finalRemovedSet = selectedRemovalSet

  if partial == True or continued == True:
    print("\nSaving progress...")
    # Initialize progress dictionary
    if continued == True:
      progressDict[sessionNum] = {'removed': previousRemovedComments.union(finalRemovedSet), 'notRemoved': remainingCommentsSet, 'failedCommentsList': failedCommentsList+previousFailedComments}
    else:
      progressDict[sessionNum] = {'removed': finalRemovedSet, 'notRemoved': remainingCommentsSet, 'failedCommentsList': failedCommentsList+previousFailedComments}


  if not progressDict or (len(progressDict[sessionNum]['notRemoved']) == 0 and len(progressDict[sessionNum]['failedCommentsList']) == 0):
    if continued == True:
      print(f"\n{FOREGROUND_TEXT_COLOR.LIGHTGREEN_EX}Success!{TEXT_STYLE.RESET_ALL} All comments should be removed. {FOREGROUND_TEXT_COLOR.YELLOW}Will now remove{TEXT_STYLE.RESET_ALL} finished progress file. (Log file will remain)")
      files.try_remove_file(progressFileNameWithPath)
    else:
      print(f"\n{FOREGROUND_TEXT_COLOR.LIGHTGREEN_EX}Success!{TEXT_STYLE.RESET_ALL} All comments should be removed.")
  else:
    #progressFileName = listFileNameBase + "_removal_progress.save"
    result = files.write_dict_pickle_file(progressDict, progressFileName, progressFileFolder, forceOverwrite=True)
    if result == True:
      print(f"Progress file saved.")
    removed = len(progressDict[sessionNum]['removed'])
    notRemoved = len(progressDict[sessionNum]['notRemoved'])
    failed = len(progressDict[sessionNum]['failedCommentsList'])

    print(f"\n {FOREGROUND_TEXT_COLOR.LIGHTCYAN_EX}----------------------- Comment List Status -----------------------{TEXT_STYLE.RESET_ALL}")
    print(f" {FOREGROUND_TEXT_COLOR.LIGHTGREEN_EX}{removed} removed{TEXT_STYLE.RESET_ALL}  |  {FOREGROUND_TEXT_COLOR.YELLOW}{notRemoved} not removed yet{TEXT_STYLE.RESET_ALL}  |  {FOREGROUND_TEXT_COLOR.LIGHTRED_EX}{failed} failed to be removed{TEXT_STYLE.RESET_ALL}")
    print(f"\n You will be able to {FOREGROUND_TEXT_COLOR.YELLOW}continue later{TEXT_STYLE.RESET_ALL} using the {FOREGROUND_TEXT_COLOR.YELLOW}same log file{TEXT_STYLE.RESET_ALL}.")

  input(f"\nPress {FOREGROUND_TEXT_COLOR.YELLOW}Enter{TEXT_STYLE.RESET_ALL} to return to Main Menu...")
  return "MainMenu"
