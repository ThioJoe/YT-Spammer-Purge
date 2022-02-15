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

  if config['strings_to_filter'] != "ask":
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
      if config['strings_to_filter'] != "ask":
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

  if config['regex_to_filter'] != "ask":
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
  print("  Loading Filters  [                              ]", end="\r")

  # Create Variables
  blackAdWords, redAdWords, yellowAdWords, exactRedAdWords, = [], [], [], []
  usernameBlackWords, usernameNovidBlackWords, usernameObfuBlackWords, textExactBlackWords, textUpLowBlackWords = [], [], [], [], []
  threadWords, threadPhrases, monetWords, monetStrings, salutations, nakedNamePre = [], [], [], [], [], []
  compiledRegexDict = {
    'usernameBlackWords': [],
    'usernameNovidBlackWords': [],
    'blackAdWords': [],
    'redAdWords': [],
    'yellowAdWords': [],
    'exactRedAdWords': [],
    'usernameRedWords': [],
    'textObfuBlackWords': [],
    'usernameObfuBlackWords': [],
    'textExactBlackWords': [],
    'textUpLowBlackWords': [],
  }

  # General Spammer Criteria
  #usernameBlackChars = ""
  spamGenEmoji_Raw = b'@Sl-~@Sl-};+UQApOJ|0pOJ~;q_yw3kMN(AyyC2e@3@cRnVj&SlB@'
  usernameBlackWords_Raw = [b'aA|ICWn^M`', b'aA|ICWn>^?c>', b'Z*CxTWo%_<a$#)', b'c4=WCbY*O1XL4a}', b'Z*CxIZgX^DXL4a}', b'Z*CxIX8', b'V`yb#YanfTAY*7@', b'b7f^9ZFwMLXkh', b'c4>2IbRcbcAY*7@', b'X>N0LVP|q-Z8`', b'Z*CxIZgX^D', b'Z*CxIZgX^DAZK!6Z2', b'c4=WCX>N0LVP|q-Z2', b'b9G`gb9G_', b'b9G`MG$3<zVg', b'Z*CxMc_3qGVE', b'XKx^MZy;@XAY*7@', b'X(w$UY-ML@bRcteVq$4-X8', b'W^!d^AZKZ2bN', b'WN&UKbRcqNVPqg}c>', b'Kxb`XX>2ZIZ*2']
  usernameNovidBlackWords_Raw = [b'cWHEJATS_yX=D', b'cWHEJAZ~9Uc4=e', b'cWHEJZ*_DaVQzUKc4=e']
  usernameObfuBlackWords_Raw = [b'c4Bp7YjX', b'b|7MPV{3B', b'a&KaFcm', b'a&KaFV{3B']
  usernameRedWords = ["whatsapp", "telegram"]
  textObfuBlackWords = ['telegram']
  textExactBlackWords_Raw = [b'Z*6BRAZ2)AV{~kJAa`hCbRcOUZe?X;Wn=', b'Z*6BRAZ2)AV{~kJAa`hCbRc<ebs%nKWn^V!', b'Z*6BRAZ2)AV{~kJAa`hCbRckLZ*Xj7AZ}%4WMyO', b'ZDnU+ZaN?$Xm50MWpW|', b'M`3zpIv^rJZDD$4WFi', b'X>%ZSa$$35EFf)pAY*TCbY*UIAZc>', b'X>%ZFVRB+&XJsrPZFwMLZ*FvDZge1Na{', b'Z*CwVX8']
  textUpLowBlackWords_Raw = [b'O<5pAPfk=tPE;UCQv', b'Ngz!@OGO}8L0KR|MO0KpQXoT5PE<usQ~', b'O<5pTNkm0YQy@W7MF', b'Qbj>TAWc~yP*P7uNlZl', b'Z*CwVM*']

  # General Settings
  unicodeCategoriesStrip = ["Mn", "Cc", "Cf", "Cs", "Co", "Cn"] # Categories of unicode characters to strip during normalization
  lowAl = b'VPa!sWoBn+X=-b1ZEkOHadLBXb#`}nd3p'

  # Create General Lists
  spamGenEmojiSet = make_char_set(b64decode(spamGenEmoji_Raw).decode(utf_16))
  lowAlSet = make_char_set(b64decode(lowAl).decode(utf_16))
    #usernameBlackCharsSet = make_char_set(usernameBlackChars)
  for x in usernameBlackWords_Raw: usernameBlackWords.append(b64decode(x).decode(utf_16))
  for x in usernameNovidBlackWords_Raw: usernameNovidBlackWords.append(b64decode(x).decode(utf_16))
  for x in usernameObfuBlackWords_Raw: usernameObfuBlackWords.append(b64decode(x).decode(utf_16))
  for x in textExactBlackWords_Raw: textExactBlackWords.append(b64decode(x).decode(utf_16))
  for x in textUpLowBlackWords_Raw: textUpLowBlackWords.append(b64decode(x).decode(utf_16))

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
  yellowAdWords_Raw = [b'Y;SgD', b'Vr5}<bZKUFYy', b'VsB)5', b'XK8Y5', b'O~a&QV`yb=', b'Xk}@`pJf', b'Xm4}', b'aCLKYc>']
  exactRedAdWords_Raw = [b'EiElAEiElAEiElAEiElAEiElAEiElAEiElAEiElAEiElAEiElAEiC', b'Wq4s@bZmJbcW7aBAZZ|OWo2Y#WB']
  redAdEmoji = b64decode(b'@Sl{P').decode(utf_16)
  yellowAdEmoji = b64decode(b'@Sl-|@Sm8N@Sm8C@Sl>4@Sl;H@Sly0').decode(utf_16)
  hrt = b64decode(b';+duJpOTpHpOTjFpOTmGpOTaCpOTsIpOTvJpOTyKpOT#LpQoYlpOT&MpO&QJouu%el9lkElAZ').decode(utf_16)

  # Create Type 2 Lists
  for x in blackAdWords_Raw: blackAdWords.append(b64decode(x).decode(utf_16))
  for x in redAdWords_Raw: redAdWords.append(b64decode(x).decode(utf_16))
  for x in yellowAdWords_Raw: yellowAdWords.append(b64decode(x).decode(utf_16))
  for x in exactRedAdWords_Raw: exactRedAdWords.append(b64decode(x).decode(utf_16))
  print("  Loading Filters  [===                           ]", end="\r")

  # Prepare Filters for Type 2 Spammers
  redAdEmojiSet = make_char_set(redAdEmoji)
  yellowAdEmojiSet = make_char_set(yellowAdEmoji)
  hrtSet = make_char_set(hrt)

  # Prepare Regex to detect nothing but video link in comment
  onlyVideoLinkRegex = re.compile(r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$")
  compiledRegexDict['onlyVideoLinkRegex'] = onlyVideoLinkRegex

  # Spam Thread Detection
  threadWords_raw = [b'aB^>EX><', b'V{&<LbZ-', b'Vsv8', b'Vrg_^Z)t7', b'baG*2X>Ml', b'baG*2Wd', b'X>N99b94', b'b7^O8VQc', b'Wq5F9a&!', b'aB^>EWpi_BZ*F01', b'b98cHbY*9G', b'ZDn+5Z)5', b'W^Zz3cm', b'b9G~5Wpi@', b'Wnpq|', b'AZ>C', b'AZ>DU', b'Z*XvLa&&cWX>@r', b'X>Mb0ZDj', b'aBp&SW^Zh1Zv', b'aB^>EX><', b'ZEtR6c>', b'b7f<4Wpn', b'cV%I0bZ7', b'Wnpq|']
  threadPhrases_raw = [b'cWHEJAZ2)PWpZ=', b'Wq5F9a&#bVas', b'Wq5F9a&#bVa&r', b'V{dMBVPkY4ZE^', b'V{dMBVPkY4ZE|w', b'V{dMBVPkY4XlZQ', b'V{dMBVPkY4Xk~H', b'cXDZTWguv2Z2', b'cXDZTWguu}as', b'bY*ySAZTfA', b'bY*ySAZTTB']
  monetWords_raw = [b'aB^>EX><', b'Wnpq|', b'X&`N3WMu', b'ZDC|(AZ=v']
  monetStrings_raw = [b'b#r6', b'Wp#3I', b'Bm', b'!lM', b';)1L', b'Vsv8']
  salutations_raw = [b'ZE^', b'ZE|w', b'ZE{>L', b'ZE|y5E&', b'ZF2', b'ZF4R', b'Wq5F9a&!']
  nakedNamePre_raw = [b'cWHEJ', b'VsdY5WpV']

  # Make Spam Thread Lists
  for x in threadWords_raw: threadWords.append(b64decode(x).decode(utf_16))
  for x in threadPhrases_raw: threadPhrases.append(b64decode(x).decode(utf_16))
  for x in monetWords_raw: monetWords.append(b64decode(x).decode(utf_16))
  for x in monetStrings_raw: monetStrings.append(b64decode(x).decode(utf_16))
  for x in salutations_raw: salutations.append(b64decode(x).decode(utf_16))
  for x in nakedNamePre_raw: nakedNamePre.append(b64decode(x).decode(utf_16))

  # Compile Thread Detection Regex
  salutationString = '|'.join(salutations)
  nakedNameString = '|'.join(nakedNamePre)
  nameRegex = re.compile(f'\\b({salutationString})\s+([a-zA-Z]+\.?)\s+([a-zA-Z]+)')
  nakedNameRegex = re.compile(f'\\b({nakedNameString})\s+([a-zA-Z]+\.?)\s+([a-zA-Z]+)')
  cashRegex = re.compile(r"^(\$|£|€)?(\d+|\d{1,3}(,\d{3})*)(\.\d+)?(\$|£|€|k| ?usd| ?eur| ?btc)?$")

  print("  Loading Filters  [======                        ]", end="\r")

  # Compile regex with upper case, otherwise many false positive character matches
  bufferChars = r"*_~|`[]()'-.•,"
  compiledRegexDict['bufferChars'] = bufferChars
  bufferMatch, addBuffers = "\\*_~|`\\-\\._", re.escape(bufferChars) # Add 'buffer' chars
  usernameConfuseRegex = re.compile(confusable_regex(miscData.channelOwnerName))
  m = bufferMatch
  a = addBuffers
  for word in usernameBlackWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['usernameBlackWords'].append([word, value])
  for word in usernameNovidBlackWords:
    value = re.compile(confusable_regex(word.upper(), include_character_padding=True).replace(m, a))
    compiledRegexDict['usernameNovidBlackWords'].append([word, value])
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
  print("  Loading Filters  [========                      ]", end="\r") 
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
    compiledRegexDict['textExactBlackWords'].append(word)
  for word in textUpLowBlackWords:
      compiledRegexDict['textUpLowBlackWords'].append(word)
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



  threadFiltersDict = {
    'threadWords':threadWords,
    'threadPhrases':threadPhrases,
    'monetWords':monetWords,
    'monetStrings':monetStrings,
    'nameRegex':nameRegex,
    'nakedNameRegex':nakedNameRegex,
    'cashRegex':cashRegex
  }

  filterSettings = {
    'spammerNumbersSet': spammerNumbersSet,
    'compiledNumRegex': compiledNumRegex,
    'minNumbersMatchCount': minNumbersMatchCount,
    #'usernameBlackCharsSet': usernameBlackCharsSet,
    'spamGenEmojiSet': spamGenEmojiSet,
    'redAdEmojiSet': redAdEmojiSet,
    'yellowAdEmojiSet': yellowAdEmojiSet,
    'hrtSet': hrtSet,
    'lowAlSet': lowAlSet,
    'rootDomainRegex': rootDomainRegex,
    'compiledRegexDict': compiledRegexDict,
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
  print(f"\n\n-------------------- {F.LIGHTGREEN_EX}Comment Recovery Mode{S.R} --------------------\n")
  print("> Believe it or not, the YouTube API actually allows you to re-instate \"deleted\" comments.")
  print(f"> This is {F.YELLOW}only possible if you have stored the comment IDs{S.R} of the deleted comments, \n   such as {F.YELLOW}having kept the log file{S.R} of that session.")
  print("> If you don't have the comment IDs you can't recover the comments, and there is no way to find them. \n")

  recoveryList = files.parse_comment_list(config, recovery=True)
  if recoveryList == "MainMenu":
    return "MainMenu"

  operations.delete_found_comments(commentsList=recoveryList, banChoice=False, deletionMode="published", recoveryMode=True)
  operations.check_recovered_comments(commentsList=recoveryList)

################################ DELETE COMMENT LIST ###########################################
def delete_comment_list(config):
  progressFileFolder = os.path.join(RESOURCES_FOLDER_NAME, "Removal_List_Progress")
  print(f"\n\n-------------------- {F.LIGHTRED_EX}Delete Using a List / Log{S.R} --------------------")
  while True:
    print("\nUse new comment list, or continue where you left off with another list?")
    print(f"  1. Use {F.LIGHTCYAN_EX}New List{S.R}")
    print(f"  2. {F.LIGHTMAGENTA_EX}Continue With{S.R} a List")
    listChoice = input("\nSelection (1 or 2): ")
    if listChoice == "1" or listChoice == "2":
      break
    else:
      print(f"\n{F.LIGHTRED_EX}Invalid selection!{S.R} Please try again.")

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
        print(f"\n{F.LIGHTGREEN_EX}Using existing save: {S.R}{saveChoice}")
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
            print(f"\n{F.RED}Invalid Selectionp{S.R}. Please try again.")
      progressFileName = saveChoice
      progressFileNameWithPath = os.path.join(progressFileFolder, progressFileName)
      progressDict = files.read_dict_pickle_file(progressFileName, progressFileFolder)
      valid = True
      removalList = "Loaded"

    else:
      print(f"\n{F.RED}No previous saves found!{S.R}")
      input("\nPress Enter to return to Main Menu...")
      return "MainMenu"


    while valid == False:
      input(F"\nNext, follow the process by loading {F.YELLOW}the same comment list/log you used before{S.R}. Press Enter to continue...")
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
        print(f"\n{F.LIGHTRED_EX}Error:{S.R} No progress file found for that log file. Try again.")

    # Get data from list
    lastSessionNum = int(len(progressDict))
    previousRemovedComments = set(progressDict[lastSessionNum]['removed'])
    remainingCommentsSet = set(progressDict[lastSessionNum]['notRemoved'])
    previousFailedComments = progressDict[lastSessionNum]['failedCommentsList']
    sessionNum = int(len(progressDict))+1

    if removalList == "Loaded" or (len(remainingCommentsSet) + len(previousRemovedComments) + len(previousFailedComments)) == len(removalList):
      pass
    else:
      print(f"{F.LIGHTRED_EX}Error:{S.R} The length of the comment list you loaded doesn't match the comment list you saved last time.")
      if choice(f"{F.YELLOW}Continue anyway?{S.R} (Will use previous save and ignore the file you just loaded)") != True:
        return "MainMenu"

    # Display status of loaded file
    prevRemovedNum = len(previousRemovedComments)
    prevNotRemovedNum = len(remainingCommentsSet)
    prevFailedNum = len(previousFailedComments)

    print(f"\n {F.LIGHTCYAN_EX}----------------------- Loaded Saved Comment List Status -----------------------{S.R}")
    print(f" {F.LIGHTGREEN_EX}{prevRemovedNum} removed{S.R}  |  {F.YELLOW}{prevNotRemovedNum} not removed yet{S.R}  |  {F.LIGHTRED_EX}{prevFailedNum} failed to be removed{S.R}")
    input("\n Press Enter to continue...")

    # Set removal list based on previous save
    removalList = list(remainingCommentsSet)
    if len(previousFailedComments)>0:
      print(f"{F.LIGHTRED_EX}NOTE:{S.R} During previous sessions, {F.LIGHTRED_EX}{len(previousFailedComments)} comments{S.R} failed to be deleted.")
      failChoice = choice(f"\n{F.YELLOW}Add these back into the list{S.R} to try again? (Otherwise will skip them for later) ")
      if failChoice == True:
        removalList = removalList + list(previousFailedComments)
        previousFailedComments = list()
      else:
        removalList = list(remainingCommentsSet)

    print(f"\n Loaded {F.YELLOW}{len(removalList)} Remaining Comments{S.R}")

  # --- Begin removal process using list ------
  print("\nWhat do you want to do with the comments in the list?")
  print(f"1. {F.LIGHTRED_EX}Delete{S.R} them")
  print(f"2. {F.LIGHTMAGENTA_EX}Hide{S.R} them for review")

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
      print(f"{F.RED}Invalid input, try again.{S.R}")
  if removalMode == "rejected":
    banChoice = choice(F"Also {F.RED}ban{S.R} the commenters?")
    if str(banChoice).lower() == "x":
      return "MainMenu"

  # Set limit based on quota
  quotaLimit = int(config['quota_limit'])-100

  validInput = False
  while validInput == False:
    print(f"\n{F.YELLOW}How many comments{S.R} (out of {len(removalList)}) do you want to remove this session? (Input '0' or 'all' to do them all)")
    countChoice = input(f"\nNumber of comments (1-{str(quotaLimit)}): ")
    if countChoice.lower() == "all" or countChoice == "0":
        countChoice = len(removalList)
    try:
        countChoice = int(countChoice)
        if countChoice > 0 and countChoice <= quotaLimit:
          validInput = True
        elif countChoice >= quotaLimit:
          print(f"\n{F.LIGHTRED_EX}Error:{S.R} {countChoice} is too many comments, you'll run out of API Quota. Read Here: {F.YELLOW}TJoe.io/api-limit-info{S.R}")
        else:
          print(f"Invalid input, must be 'all' or a whole number from 1 to {str(quotaLimit)}.")
    except:
      print(f"{F.RED}Invalid input, must be a whole number.{S.R} Try again.")

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

  input(f"\nPress {F.YELLOW}Enter{S.R} to Begin Removal...")
  failedCommentsList = operations.delete_found_comments(commentsList=selectedRemovalList, banChoice=banChoice, deletionMode=removalMode)

  ### Handle Results ###
  if len(failedCommentsList) > 0:
    print(f"\n{F.LIGHTRED_EX}Warning!{S.R} {len(failedCommentsList)} comments apparently failed to be removed. They'll be saved to be tried later.")
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
      progressDict = dict()
      progressDict[sessionNum] = {'removed': finalRemovedSet, 'notRemoved': remainingCommentsSet, 'failedCommentsList': failedCommentsList+previousFailedComments}


  if len(progressDict[sessionNum]['notRemoved']) == 0 and len(progressDict[sessionNum]['failedCommentsList']) == 0:
    if continued == True:
      print(f"\n{F.LIGHTGREEN_EX}Success!{S.R} All comments should be removed. {F.YELLOW}Will now remove{S.R} finished progress file. (Log file will remain)")
      files.try_remove_file(progressFileNameWithPath)
    else:
      print(f"\n{F.LIGHTGREEN_EX}Success!{S.R} All comments should be removed.")
  else:
    #progressFileName = listFileNameBase + "_removal_progress.save"
    result = files.write_dict_pickle_file(progressDict, progressFileName, progressFileFolder, forceOverwrite=True)
    if result == True:
      print(f"Progress file saved.")
    removed = len(progressDict[sessionNum]['removed'])
    notRemoved = len(progressDict[sessionNum]['notRemoved'])
    failed = len(progressDict[sessionNum]['failedCommentsList'])

    print(f"\n {F.LIGHTCYAN_EX}----------------------- Comment List Status -----------------------{S.R}")
    print(f" {F.LIGHTGREEN_EX}{removed} removed{S.R}  |  {F.YELLOW}{notRemoved} not removed yet{S.R}  |  {F.LIGHTRED_EX}{failed} failed to be removed{S.R}")
    print(f"\n You will be able to {F.YELLOW}continue later{S.R} using the {F.YELLOW}same log file{S.R}.")

  input(f"\nPress {F.YELLOW}Enter{S.R} to return to Main Menu...")
  return "MainMenu"
