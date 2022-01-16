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

from confusables import confusable_regex, normalize
from base64 import b85decode as b64decode

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

  if config and config['characters_to_filter'] != "ask":
    print("Characters to filter obtained from config file.")
    pass
  else:
    print(f"\nNext, you will input {F.YELLOW}ONLY{S.R} any special characters / emojis you want to search for in all {whatToScanMsg}. Do not include commas or spaces!")
    print("          Note: Letters, numbers, and basic punctuation will not be included for safety purposes, even if you enter them.")
    print("          Example: 👋🔥✔️✨")
    input(f"\nPress {F.LIGHTGREEN_EX}Enter{S.R} to open the {F.LIGHTGREEN_EX}text entry window{S.R}...")
    print("-------------------------------------------")

  confirm = False
  validConfigSetting = True
  while confirm == False:
    if validConfigSetting == True and config and config['characters_to_filter'] != "ask":
      inputChars = make_char_set(config['characters_to_filter'], stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=True)
      bypass = True
    else:
      bypass = False
      print(f"\nWaiting for input Window. Press {F.MAGENTA}'Execute'{S.R} after entering valid characters to continue...", end="\r")
      try:
        # Takes in user input of characters, returns 'set' of characters stripped of specified characters
        inputChars = take_input_gui(mode="chars", stripLettersNumbers=True, stripKeyboardSpecialChars=False, stripPunctuation=True)
      except NameError: # Catch if user closes GUI window, exit program.
        print("                                                                                          ") # Clears the line because of \r on previous print
        print("\nError Code G-1: Something went wrong with the input, or you closed the window improperly.")
        print("If this keeps happening inexplicably, consider filing a bug report here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
        input("Press Enter to exit...")
        sys.exit()

    print(f"     {whatToScanMsg} will be scanned for {F.MAGENTA}ANY{S.R} of the characters you entered in the previous window.")
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

  if config and config['strings_to_filter'] != "ask":
    print("Strings to filter obtained from config file.")
    pass
  else:
    print(f"\nPaste or type in a list of any {F.YELLOW}comma separated strings{S.R} you want to search for in {whatToScanMsg}. (Not case sensitive)")
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
      if config and config['strings_to_filter'] != "ask":
        pass
      else:
        print(f"     {whatToScanMsg} will be scanned for {F.MAGENTA}ANY{S.R} of the following strings:")
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

  if config and config['regex_to_filter'] != "ask":
    print("Regex expression obtained from config file.")
    validConfigSetting = True
  else:
    print(f"Enter any {F.YELLOW}regex expression{S.R} to search within {whatToScanMsg}.")
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
      print(f"     The expression appears to be {F.GREEN}valid{S.R}!")

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
      print(f"     {F.RED}Error{S.R}: The expression appears to be {F.RED}invalid{S.R}!")
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
      inputtedSpammerChannelID = input(f"Enter the {F.LIGHTRED_EX} Channel link(s) or ID(s){S.R} of the spammer (comma separated): ")
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
    print(f"{B.RED}{F.WHITE} WARNING: {S.R} - You entered your own channel ID!")
    print(f"For safety purposes, this program always {F.YELLOW}ignores{S.R} your own comments.")

    if config and config['channel_ids_to_filter'] != "ask":
      pass
    else:
      input("\nPress Enter to continue...")
  
  return inputtedSpammerChannelID, None

# For Filter mode auto-ascii, user inputs nothing, program scans for non-ascii
def prepare_filter_mode_non_ascii(scanMode, config):

  print("\n--------------------------------------------------------------------------------------------------------------")
  print("~~~ This mode automatically searches for usernames that contain special characters (aka not letters/numbers) ~~~\n")
  print("Choose the sensitivity level of the filter. You will be shown examples after you choose.")
  print(f"   1. Allow {F.LIGHTMAGENTA_EX}Standard + Extended ASCII{S.R}:    Filter rare unicode & Emojis only")
  print(f"   2. Allow {F.LIGHTMAGENTA_EX}Standard ASCII only{S.R}:  Also filter semi-common foreign characters")
  print(f"   3. {F.LIGHTRED_EX}NUKE Mode (┘°□°)┘≈ ┴──┴ :    Allow ONLY numbers, letters, and spaces{S.R}")
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
      print(f"Searches for {F.YELLOW}usernames with emojis, unicode symbols, and rare foreign characters{S.R} such as: ✔️ ☝️ 🡆 ▲ π Ɲ Œ")
      userChoice = choice("Choose this mode?", bypass)
      if userChoice == True:
        regexPattern = r"[^\x00-\xFF]"
        confirmation = True
      elif userChoice == None:
        return "MainMenu", None
    elif selection == "2":
      print(f"Searches for {F.YELLOW}usernames with anything EXCEPT{S.R} the following: {F.YELLOW}Letters, numbers, punctuation, and common special characters{S.R} you can type with your keyboard like: % * & () + ")
      userChoice = choice("Choose this mode?", bypass)
      if userChoice == True:
        regexPattern = r"[^\x00-\x7F]"
        confirmation = True
      elif userChoice == None:
        return "MainMenu", None
    elif selection == "3":
      print(f"Searches for {F.YELLOW}usernames with anything EXCEPT letters, numbers, and spaces{S.R} - {B.RED}{F.WHITE} EXTREMELY LIKELY to cause collateral damage!{S.R} Recommended to just use to manually gather list of spammer IDs, then use a different mode to delete.")
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
  rootDomainList = miscData.rootDomainsList
  spamDomainsList = miscData.spamLists['spamDomainsList'] # List of domains from crowd sourced list
  spamThreadsList = miscData.spamLists['spamThreadsList'] # List of filters associated with spam threads from crowd sourced list
  spamAccountsList = miscData.spamLists['spamAccountsList'] # List of mentioned instagram/telegram scam accounts from crowd sourced list
  utf_16 = "utf-8"
  if config and config['filter_mode'] == "autosmart":
    pass
  else:
    print("\n--------------------------------------------------------------------------------------------------------------")
    print(f"~~~ This mode is a {F.LIGHTCYAN_EX}spammer's worst nightmare{S.R}. It automatically scans for multiple spammer techniques ~~~\n")
    print(" > Extremely low (near 0%) false positives")
    print(" > Detects whatsapp scammers and '18+ spam' bots")
    print(" > Easily cuts through look-alike characters and obfuscations, including impersonating usernames")
    if sensitive == False:
      print(f" > {F.LIGHTRED_EX}NOTE:{S.R} This mode prioritizes a {F.LIGHTGREEN_EX}VERY low false positive rate{S.R}, at the cost of occasionally missing some spammers.\n")
    elif sensitive == True:
      print(f" > {F.LIGHTRED_EX}NOTE:{S.R} In sensitive mode, {F.LIGHTRED_EX}expect more false positives{S.R}. Recommended to run this AFTER regular Auto Smart Mode.\n")
    input("Press Enter to Begin Scanning...")
    print ("\033[A                                     \033[A") # Erases previous line
    print(" Loading Filters...              ", end="\r")

  # Create Variables
  blackAdWords, redAdWords, yellowAdWords, exactRedAdWords, usernameBlackWords = [], [], [], [], []
  usernameBlackWords, usernameObfuBlackWords, textExactBlackWords = [], [], []
  compiledRegexDict = {
    'usernameBlackWords': [],
    'blackAdWords': [],
    'redAdWords': [],
    'yellowAdWords': [],
    'exactRedAdWords': [],
    'usernameRedWords': [],
    'textObfuBlackWords': [],
    'usernameObfuBlackWords': [],
    'textExactBlackWords': [],
  }

  # General Spammer Criteria
  #usernameBlackChars = ""
  spamGenEmoji_Raw = b'@Sl-~@Sl-};+UQApOJ|0pOJ~;q_yw3kMN(AyyC2e@3@cRnVj&SlB@'
  usernameBlackWords_Raw = [b'aA|ICWn^M`', b'aA|ICWn>^?c>', b'Z*CxTWo%_<a$#)', b'c4=WCbY*O1XL4a}', b'Z*CxIZgX^DXL4a}', b'Z*CxIX8', b'V`yb#YanfTAY*7@', b'b7f^9ZFwMLXkh', b'c4>2IbRcbcAY*7@', b'cWHEJATS_yX=D', b'cWHEJAZ~9Uc4=e', b'cWHEJZ*_DaVQzUKc4=e', b'X>N0LVP|q-Z8`', b'Z*CxIZgX^D', b'Z*CxIZgX^DAZK!6Z2']
  usernameObfuBlackWords_Raw = [b'c4Bp7YjX', b'b|7MPV{3B']
  usernameRedWords = ["whatsapp", "telegram"]
  textObfuBlackWords = ['telegram']
  textExactBlackWords_Raw = [b'Z*6BRAZ2)AV{~kJAa`hCbRcOUZe?X;Wn=', b'Z*6BRAZ2)AV{~kJAa`hCbRc<ebs%nKWn^V!', b'Z*6BRAZ2)AV{~kJAa`hCbRckLZ*Xj7AZ}%4WMyO', b'ZDnU+ZaN?$Xm50MWpW|']
  
  # General Settings
  unicodeCategoriesStrip = ["Mn", "Cc", "Cf", "Cs", "Co", "Cn"] # Categories of unicode characters to strip during normalization

  # Create General Lists
  spamGenEmojiSet = make_char_set(b64decode(spamGenEmoji_Raw).decode(utf_16))
    #usernameBlackCharsSet = make_char_set(usernameBlackChars)
  for x in usernameBlackWords_Raw: usernameBlackWords.append(b64decode(x).decode(utf_16))
  for x in usernameObfuBlackWords_Raw: usernameObfuBlackWords.append(b64decode(x).decode(utf_16))
  for x in textExactBlackWords_Raw: textExactBlackWords.append(b64decode(x).decode(utf_16))

  # Type 1 Spammer Criteria
  minNumbersMatchCount = 6 # Choice of minimum number of matches from spamNums before considered spam
  spamNums = b'@4S%jypiv`lJC5e@4S@nyp`{~mhZfm@4T4ryqWL3kng;a@4S-lyp!*|l<&Ni@4S}pyqE91nD4xq-+|(hpyH9V;*yBsleOZVw&I?E;+~4|pM-+ovAy7_sN#{K;*quDl8NGzw&I<);+}!xo{R9GgoEI*sp65M;*qxEl8WM!x8j|+;+}%yo{aFHgoNO$sp65N;*q!Fl8fS#xZ<6;;+})zo{jLIgoWafq~ejd;*yNwleyxZy5gRM;+~G;o`m9_j_{v^hT@T>;*q)Hl8xe%y5gO?;+}=#o{#XKgoomhrs9#h;*yTyle^-byyBjQ;+~N3k%YbQpM;3vf|%lwr{a;j;*yWzlf2@cz2csS;+~Q4pM;6xk*MO4yyB9O;*-7Noxb9ph~l1-@SlW=;*+Z4lfUqvgp2T>gpBZ?gn{s%gn;m!pN{aIpP2BSpQ7-cpRDkmpO5gJpPBHTpRMqnpQG@dpSJLwpOEmKpPKNUpRVwopQP}epSSRxpONsLpPTTVpRe$ppQZ4fpSbXypOWyMpPcZWpRn+qpQiAgpSkdzpOf&NpPlfXpRw?rpQrGhpStj!pOo;OpPulYpR(|spQ!MipS$p#pOx^PpP%rZpR@3tpQ-SjpS<v$pO)~QpP=xapS19upQ`YkpS|#%pO^5RpP}%bpSAFvpR4elpT6*&pT7'
  spamPlus = b';+&e|oSEXDmBO*hmf?`8;(@y2f{NmZlj4Y!;)<2xik{-1wBo0_;-|afsDa|BgyN{8;;5tIsHEbkrQ)cj;;5(MsHozot>UPz;;6aesj=dzvf`|=@42Gyyo=$Rt>S^4;+U!8n5g2IrsA2f;+e7Ho2cTPnc|$9;+&h}oSfpEo#LFH;+&u2oS^EOn(CUH@Sl}{@Sl}|@Sl}}@Sl~2@Sl~3@Sl~4@SmQc@SmQd@SmQe@SmQf@SmQg@SmQh@SmQi'
  spamOne = b'@4S)lou7~Jou8TTou8xdou94nou9Yjl8EAywc?$&;+}xwo{I3Fgo59J;*p@@k+c'
  x = b64decode(spamNums).decode(utf_16)
  y = b64decode(spamPlus).decode(utf_16)
  z = b64decode(spamOne).decode(utf_16)

  # Prepare Filters for Type 1 Spammers
  spammerNumbersSet = make_char_set(x)
  regexTest1 = f"[{y}] ?[1]"
  regexTest2 = f"[+] ?[{z}]"
  regexTest3 = f"[{y}] ?[{z}]"
  compiledNumRegex = re.compile(f"({regexTest1}|{regexTest2}|{regexTest3})")

  # Type 2 Spammer Criteria
  blackAdWords_Raw = [b'V`yb#YanfTAaHVTW@&5', b'Z*XO9AZ>XdaB^>EX>0', b'b7f^9ZFwMYa&Km7Yy', b'V`yb#YanfTAa-eFWp4', b'V`yb#YanoPZ)Rz1', b'V`yb#Yan)MWMyv', b'bYXBHZ*CxMc>', b'Z*CxMc_46UV{~<LWd']
  redAdWords_Raw = [b'W_4q0', b'b7gn', b'WNBk-', b'WFcc~', b'W-4QA', b'W-2OUYX', b'Zgpg3', b'b1HZ', b'F*qv', b'aBp&M']
  yellowAdWords_Raw = [b'Y;SgD', b'Vr5}<bZKUFYy', b'VsB)5', b'XK8Y5a{', b'O~a&QV`yb=', b'Xk}@`pJf', b'Xm4}']
  exactRedAdWords_Raw = [b'EiElAEiElAEiElAEiElAEiElAEiElAEiElAEiElAEiElAEiElAEiC', b'Wq4s@bZmJbcW7aBAZZ|OWo2Y#WB']
  redAdEmoji = b64decode(b'@Sl{P').decode(utf_16)
  yellowAdEmoji = b64decode(b'@Sl-|@Sm8N@Sm8C@Sl>4@Sl;H@Sly0').decode(utf_16)
  hrt = b64decode(b';+duJpOTpHpOTjFpOTmGpOTaCpOTsIpOTvJpOTyKpOT#LpQoYlpOT&MpO&QJouu%el9lkElAZ').decode(utf_16)
  
  # Create Type 2 Lists
  for x in blackAdWords_Raw: blackAdWords.append(b64decode(x).decode(utf_16))
  for x in redAdWords_Raw: redAdWords.append(b64decode(x).decode(utf_16))
  for x in yellowAdWords_Raw: yellowAdWords.append(b64decode(x).decode(utf_16))
  for x in exactRedAdWords_Raw: exactRedAdWords.append(b64decode(x).decode(utf_16))
  

  # Prepare Filters for Type 2 Spammers
  redAdEmojiSet = make_char_set(redAdEmoji)
  yellowAdEmojiSet = make_char_set(yellowAdEmoji)
  hrtSet = make_char_set(hrt)
  
  # Prepare Regex to detect nothing but video link in comment
  onlyVideoLinkRegex = re.compile(r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$")
  compiledRegexDict['onlyVideoLinkRegex'] = onlyVideoLinkRegex

  # Compile regex with upper case, otherwise many false positive character matches
  bufferChars = r"*_~|`[]()'-.•"
  compiledRegexDict['bufferChars'] = bufferChars
  bufferMatch, addBuffers = "\\*_~|`\\-\\.", re.escape(bufferChars) # Add 'buffer' chars
  usernameConfuseRegex = re.compile(confusable_regex(miscData.channelOwnerName))
  m = bufferMatch
  a = addBuffers
  for word in usernameBlackWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['usernameBlackWords'].append([word, value])
  for word in blackAdWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['blackAdWords'].append([word, value])
  for word in redAdWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['redAdWords'].append([word, value])
  for word in yellowAdWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['yellowAdWords'].append([word, value])
  for word in exactRedAdWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=False))
    compiledRegexDict['exactRedAdWords'].append([word, value])
  for word in usernameRedWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['usernameRedWords'].append([word, value])
  for word in textObfuBlackWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['textObfuBlackWords'].append([word, value])
  for word in usernameObfuBlackWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['usernameObfuBlackWords'].append([word, value])
  for word in textExactBlackWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['textExactBlackWords'].append([word, value])

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

  spamListExpressionsList = []
  # Prepare spam domain regex
  for domain in spamDomainsList:
    spamListExpressionsList.append(confusable_regex(domain.upper(), include_character_padding=False).replace(m, a).replace("\.|", "\.|•|"))
  for account in spamAccountsList:
    spamListExpressionsList.append(confusable_regex(account.upper(), include_character_padding=True).replace(m, a))
  for thread in spamThreadsList:
    spamListExpressionsList.append(confusable_regex(thread.upper(), include_character_padding=True).replace(m, a))
  spamListCombinedRegex = re.compile('|'.join(spamListExpressionsList))

  # Prepare Multi Language Detection
  turkish = 'ÇçŞşĞğİ'
  germanic = 'ẞßÄä'
  cyrillic = "гджзклмнпрстфхцчшщыэюяъь"
  japanese = 'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヷヸヹヺーヽヾヿぁあぃいぅうぇえぉおかがきぎぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞゟ'
  languages = [['turkish', turkish, []], ['germanic', germanic, []], ['cyrillic', cyrillic, []], ['japanese', japanese, []]]
  for item in languages:
    item[2] = make_char_set(item[1])

  filterSettings = {
    'spammerNumbersSet': spammerNumbersSet, 
    'compiledNumRegex': compiledNumRegex, 
    'minNumbersMatchCount': minNumbersMatchCount, 
    #'usernameBlackCharsSet': usernameBlackCharsSet, 
    'spamGenEmojiSet': spamGenEmojiSet,
    'redAdEmojiSet': redAdEmojiSet,
    'yellowAdEmojiSet': yellowAdEmojiSet,
    'hrtSet': hrtSet,
    'rootDomainRegex': rootDomainRegex,
    'compiledRegexDict': compiledRegexDict,
    'usernameConfuseRegex': usernameConfuseRegex,
    'languages': languages,
    'sensitive': sensitive,
    'sensitiveRootDomainRegex': sensitiveRootDomainRegex,
    'unicodeCategoriesStrip': unicodeCategoriesStrip,
    'spamListCombinedRegex': spamListCombinedRegex,
    }
  print("                                ") # Erases line that says "loading filters"  
  return filterSettings, None



##########################################################################################
################################# LIST MODES  ############################################
##########################################################################################


################################ RECOVERY MODE ###########################################
def recover_deleted_comments():
  print(f"\n\n-------------------- {F.LIGHTGREEN_EX}Comment Recovery Mode{S.R} --------------------\n")
  print("Believe it or not, the YouTube API actually allows you to re-instate \"deleted\" comments.")
  print(f"This is {F.YELLOW}only possible if you have stored the comment IDs{S.R} of the deleted comments, such as {F.YELLOW}having kept the log file{S.R} of that session.")
  print("If you don't have the comment IDs you can't recover the comments, and there is no way to find them. \n")

  recoveryList = files.parse_comment_list(recovery=True)
  if recoveryList == "MainMenu":
    return "MainMenu"

  operations.delete_found_comments(commentsList=recoveryList, banChoice=False, deletionMode="published", recoveryMode=True)
  operations.check_recovered_comments(commentsList=recoveryList)

################################ RECOVERY MODE ###########################################
def delete_comment_list():
  print(f"\n\n-------------------- {F.LIGHTRED_EX}Delete Using a List / Log{S.R} --------------------\n")
  removalList = files.parse_comment_list(removal=True)
  if removalList == "MainMenu":
    return "MainMenu"
  print("\nWhat do you want to do with the comments in the list?")
  print("1. Delete them")
  print("2. Hide them for review")

  validInput = False
  while validInput == False:
    userChoice = input("\nSelection (1 or 2): ")
    if userChoice == "1":
      removalMode = "rejected"
      validInput = True
    elif userChoice == "2":
      removalMode = "heldForReview"
      validInput = True
    elif userChoice.lower() == "x":
      return "MainMenu"
    else:
      print("Invalid input, try again.")
    
  if removalMode == "rejected":
    banChoice = choice("Also ban the commenters?")

  input("\nPress Enter to Begin Removal...")
  operations.delete_found_comments(commentsList=removalList, banChoice=banChoice, deletionMode=removalMode)

  print("Check that the comments were deleted? (Warning: Costs 1 API quota unit each, default daily max is 10,000)")
  userChoice = choice("Check Deletion Success?")
  if userChoice == True:
    operations.check_deleted_comments(removalList)
  input("\nOperation Complete. Press Enter to return to main menu...")
  return "MainMenu"
