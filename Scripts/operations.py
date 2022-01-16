#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from Scripts.shared_imports import *
import Scripts.utils as utils
import Scripts.auth as auth
import Scripts.validation as validation
import Scripts.logging as logging

import unicodedata
import time
import itertools
#from collections import Counter
from Levenshtein import ratio

##########################################################################################
############################## GET COMMENT THREADS #######################################
##########################################################################################

# Call the API's commentThreads.list method to list the existing comments.
def get_comments(current, filtersDict, miscData, config, currentVideoDict, scanVideoID=None, nextPageToken=None, videosToScan=None):  # None are set as default if no parameters passed into function
  # Initialize some variables
  authorChannelName = None
  commentText = None
  parentAuthorChannelID = None
  allCommentsDict = currentVideoDict

  fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/replies/comments,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/authorDisplayName,items/snippet/topLevelComment/snippet/textDisplay"

  # Gets all comment threads for a specific video
  if scanVideoID is not None:
    results = auth.YOUTUBE.commentThreads().list(
      part="snippet, replies",
      videoId=scanVideoID, 
      maxResults=100,
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()
  
  # Get all comment threads across the whole channel
  elif scanVideoID is None:
    results = auth.YOUTUBE.commentThreads().list(
      part="snippet, replies",
      allThreadsRelatedToChannelId=auth.CURRENTUSER.id,
      maxResults=100,
      pageToken=nextPageToken,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()
    
  # Get token for next page. If no token, sets to 'End'
  RetrievedNextPageToken = results.get("nextPageToken", "End")
  
  # After getting all comments threads for page, extracts data for each and stores matches in current.matchedCommentsDict
  # Also goes through each thread and executes get_replies() to get reply content and matches
  for item in results["items"]:
    comment = item["snippet"]["topLevelComment"]
    videoID = comment["snippet"]["videoId"] # Only enable if NOT checking specific video
    parent_id = item["snippet"]["topLevelComment"]["id"]
    numReplies = item["snippet"]["totalReplyCount"]

    # On rare occasions a comment will be there but the channel name will be empty, so this allows placeholders
    try:
      limitedRepliesList = item["replies"]["comments"] # API will return a limited number of replies (~5), but to get all, need to make separate call
    except KeyError:
      limitedRepliesList = []
      pass
    try: 
      parentAuthorChannelID = comment["snippet"]["authorChannelId"]["value"]
    except KeyError:
      parentAuthorChannelID = "[Deleted Channel]"

    # Need to be able to catch exceptions because sometimes the API will return a comment from non-existent / deleted channel
    try:
      authorChannelName = comment["snippet"]["authorDisplayName"]
    except KeyError:
      authorChannelName = "[Deleted Channel]"
    try:
      commentText = comment["snippet"]["textDisplay"] # Remove Return carriages
    except KeyError:
      commentText = "[Deleted/Missing Comment]"

    # Runs check against comment info for whichever filter data is relevant
    currentCommentDict = {
      'authorChannelID':parentAuthorChannelID, 
      'parentAuthorChannelID':None, 
      'authorChannelName':authorChannelName, 
      'commentText':commentText,
      'commentID':parent_id,
      }
    check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID)
    current.scannedCommentsCount += 1

    #Log All Comments
    try:
      allCommentsDict[parentAuthorChannelID].append(currentCommentDict)
    except KeyError:
      allCommentsDict[parentAuthorChannelID] = [currentCommentDict]
    except TypeError:
      pass
    
    if numReplies > 0 and len(limitedRepliesList) < numReplies:
      allCommentsDict = get_replies(current, filtersDict, miscData, config, parent_id, videoID, parentAuthorChannelID, videosToScan, allCommentsDict)
    elif numReplies > 0 and len(limitedRepliesList) == numReplies: # limitedRepliesList can never be more than numReplies
      allCommentsDict = get_replies(current, filtersDict, miscData, config, parent_id, videoID, parentAuthorChannelID, videosToScan, allCommentsDict, repliesList=limitedRepliesList)
    else:
      print_count_stats(current, miscData, videosToScan, final=False)  # Updates displayed stats if no replies

  # Runs after all comments scanned
  if RetrievedNextPageToken == "End" and allCommentsDict != None:
    dupeCheckModes = utils.string_to_list(config['duplicate_check_modes'])
    if filtersDict['filterMode'].lower() in dupeCheckModes:
      print(" Scanning For Duplicates                                                                                 ", end="\r")
      check_duplicates(current, config, miscData, allCommentsDict, videoID)
      print("                                                                                                                  ")

  return RetrievedNextPageToken, allCommentsDict


##########################################################################################
##################################### GET REPLIES ########################################
##########################################################################################

# Call the API's comments.list method to list the existing comment replies.
def get_replies(current, filtersDict, miscData, config, parent_id, videoID, parentAuthorChannelID, videosToScan, allCommentsDict, repliesList=None):
  # Initialize some variables
  authorChannelName = None
  commentText = None
  
  if repliesList == None:
    fieldsToFetch = "items/snippet/authorChannelId/value,items/id,items/snippet/authorDisplayName,items/snippet/textDisplay"

    results = auth.YOUTUBE.comments().list(
      part="snippet",
      parentId=parent_id,
      maxResults=100,
      fields=fieldsToFetch,
      textFormat="plainText"
    ).execute()

    replies = results["items"]
  else:
    replies = repliesList
 
  # Create list of author names in current thread, add into list - Only necessary when scanning comment text
  allThreadAuthorNames = []

  # Iterates through items in results
  # Need to be able to catch exceptions because sometimes the API will return a comment from non-existent / deleted channel
  # Need individual tries because not all are fetched for each mode
  for reply in replies:  
    replyID = reply["id"]
    try:
      authorChannelID = reply["snippet"]["authorChannelId"]["value"]
    except KeyError:
      authorChannelID = "[Deleted Channel]"

    # Get author display name
    try:
      authorChannelName = reply["snippet"]["authorDisplayName"]
      if filtersDict['filterMode'] == "Username" or filtersDict['filterMode'] == "AutoASCII" or filtersDict['filterMode'] == "AutoSmart" or filtersDict['filterMode'] == "NameAndText":
        allThreadAuthorNames.append(authorChannelName)
    except KeyError:
      authorChannelName = "[Deleted Channel]"
    
    # Comment Text
    try:
      commentText = reply["snippet"]["textDisplay"] # Remove Return carriages
    except KeyError:
      commentText = "[Deleted/Missing Comment]"

    # Runs check against comment info for whichever filter data is relevant
    currentCommentDict = {
      'authorChannelID':authorChannelID, 
      'parentAuthorChannelID':parentAuthorChannelID, 
      'authorChannelName':authorChannelName, 
      'commentText':commentText,
      'commentID':replyID,
      }
    check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID, allThreadAuthorNames=allThreadAuthorNames)

    #Log All Comments
    try:
      allCommentsDict[authorChannelID].append(currentCommentDict)
    except KeyError:
      allCommentsDict[authorChannelID] = [currentCommentDict]
    except TypeError:
      pass

    # Update latest stats
    current.scannedRepliesCount += 1 
    print_count_stats(current, miscData, videosToScan, final=False)

  return allCommentsDict


# If the comment/username matches criteria based on mode, add key/value pair of comment ID and author ID to current.matchedCommentsDict
# Also add key-value pair of comment ID and video ID to dictionary
# Also count how many spam comments for each author
def add_spam(current, config, miscData, currentCommentDict, videoID, matchReason="Generic/Unspecified"):
  commentID = currentCommentDict['commentID']
  authorChannelName = currentCommentDict['authorChannelName']
  authorChannelID = currentCommentDict['authorChannelID']
  commentTextRaw = str(currentCommentDict['commentText']) # Use str() to ensure not pointing to same place in memory
  commentText = str(currentCommentDict['commentText']).replace("\r", "")

  current.matchedCommentsDict[commentID] = {'text':commentText, 'textUnsanitized':commentTextRaw, 'authorName':authorChannelName, 'authorID':authorChannelID, 'videoID':videoID, 'matchReason':matchReason}
  current.vidIdDict[commentID] = videoID # Probably remove this later, but still being used for now
  if authorChannelID in current.authorMatchCountDict:
    current.authorMatchCountDict[authorChannelID] += 1
  else:
    current.authorMatchCountDict[authorChannelID] = 1
  if config and config['json_log'] == True and config['json_extra_data'] == True:
    current.matchedCommentsDict[commentID]['uploaderChannelID'] = miscData.channelOwnerID
    current.matchedCommentsDict[commentID]['uploaderChannelName'] = miscData.channelOwnerName
    current.matchedCommentsDict[commentID]['videoTitle'] = utils.get_video_title(current, videoID)

  # if debugSingleComment == True: 
  #   input("--- Yes, Matched -----")

############################## Check Duplicats ######################################
def check_duplicates(current, config, miscData, allCommentsDict, videoID):
  # Get Lenvenshtein Distance Setting
  try:
    levenshtein = float(config['levenshtein_distance'])
    if levenshtein < 0 or levenshtein > 1:
      print("\nError: Levenshtein_distance config setting must be between 0 and 1. Defaulting to 0.9")
      input("\nPress Enter to continue...")
      levenshtein = 0.9
  except ValueError:
    print("\nError: Levenshtein_distance config setting must be a number between 0 and 1. Defaulting to 0.9")
    input("\nPress Enter to continue...")
    levenshtein = 0.9

  # Get dupliate count setting
  try:
    minimum_duplicates = int(config['minimum_duplicates'])
    if minimum_duplicates < 2:
      minimum_duplicates = 5
      print("\nError: Minimum_Duplicates config setting must be greater than 1. Defaulting to 5.")
      input("\nPress Enter to continue...")
  except ValueError:
    minimum_duplicates = 5
    print("\nError: Minimum_Duplicates config setting is invalid. Defaulting to 5.")
    input("\nPress Enter to continue...")
  
  # Calculate number of authors to check, for progress
  authorCount = len(allCommentsDict)
  scannedCount = 0

  # Run the actual duplicate checking
  for authorID, authorCommentsList in allCommentsDict.items():
    # Don't bother if author is already in matchedCommentsDict
    if any(authorID == value['authorID'] for key,value in current.matchedCommentsDict.items()):
      scannedCount +=1
      print(f" Scanning For Duplicates - Progress: [ {scannedCount/authorCount*100:.2f}% ]".ljust(75, " "), end="\r")
    else:
      numDupes = 0
      commentTextList = []
      matchedIndexes = []
      for commentDict in authorCommentsList:
        commentTextList.append(commentDict['commentText'])

      # Count number of comments that are similar to at least one other comment
      if len(commentTextList) > 1:
        for i,x in enumerate(commentTextList):
          for j in range(i+1,len(commentTextList)):
            y = commentTextList[j]
            if ratio(x,y) > levenshtein:
              # List the indexes of the matched comments in the list
              matchedIndexes.append(i)
              matchedIndexes.append(j)
              break
        
        # Only count each comment once by counting number of unique indexes in matchedIndexes
        uniqueMatches = len(set(matchedIndexes))    
        if uniqueMatches >= minimum_duplicates:
          numDupes += uniqueMatches
      if numDupes > 0:
        for commentDict in authorCommentsList:
          add_spam(current, config, miscData, commentDict, videoID, matchReason="Duplicates")
      scannedCount +=1
      print(f" Scanning For Duplicates - Progress: [ {scannedCount/authorCount*100:.2f}% ]".ljust(75, " "), end="\r")


############################## CHECK AGAINST FILTER ######################################
# The basic logic that actually checks each comment against filter criteria
def check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID, allThreadAuthorNames=None):
  # Retrieve Data from currentCommentDict
  commentID = currentCommentDict['commentID']
  authorChannelName = currentCommentDict['authorChannelName']
  authorChannelID = currentCommentDict['authorChannelID']
  parentAuthorChannelID = currentCommentDict['parentAuthorChannelID']
  commentTextRaw = str(currentCommentDict['commentText']) # Use str() to ensure not pointing to same place in memory
  commentText = str(currentCommentDict['commentText']).replace("\r", "")

  ##Debugging
  # print("Comment ID: " + commentID)
  # debugSingleComment = True #Debug usage
  # if debugSingleComment == True:
  #   authorChannelName = input("Channel Name: ")
  #   commentText = input("Comment Text: ")
  #   authorChannelID = "x"
  
  # Do not even check comment if: Author is Current User, Author is Channel Owner, or Author is in whitelist
  if auth.CURRENTUSER.id != authorChannelID and miscData.channelOwnerID != authorChannelID and authorChannelID not in miscData.resources['Whitelist']['WhitelistContents']:
    if "@" in commentText:
      # Logic to avoid false positives from replies to spammers
      if allThreadAuthorNames and (filtersDict['filterMode'] == "AutoSmart" or filtersDict['filterMode'] == "NameAndText"):
        for name in allThreadAuthorNames:
          if "@"+str(name) in commentText:
            commentText = commentText.replace("@"+str(name), "")
      # Extra logic to detect false positive if spammer's comment already deleted, but someone replied
      if current.matchedCommentsDict and filtersDict['filterMode'] == "AutoSmart":
        for key, value in current.matchedCommentsDict.items():
          if "@"+str(value['authorName']) in commentText:
            remove = True
            for key2,value2 in current.matchedCommentsDict.items():
              if value2['authorID'] == authorChannelID:
                remove = False
            if remove == True:
              commentText = commentText.replace("@"+str(value['authorName']), "")



    # Checks author of either parent comment or reply (both passed in as commentID) against channel ID inputted by user
    if filtersDict['filterMode'] == "ID":
      if any(authorChannelID == x for x in filtersDict['CustomChannelIdFilter']):
        add_spam(current, config, miscData, currentCommentDict, videoID)

    # Check Modes: Username
    elif filtersDict['filterMode'] == "Username":
      if filtersDict['filterSubMode'] == "chars":
        authorChannelName = utils.make_char_set(str(authorChannelName))
        if any(x in filtersDict['CustomUsernameFilter'] for x in authorChannelName):
          add_spam(current, config, miscData, currentCommentDict, videoID)
      elif filtersDict['filterSubMode'] == "string":
        if utils.check_list_against_string(listInput=filtersDict['CustomUsernameFilter'], stringInput=authorChannelName, caseSensitive=False):
          add_spam(current, config, miscData, currentCommentDict, videoID)
      elif filtersDict['filterSubMode'] == "regex":
        if re.search(str(filtersDict['CustomRegexPattern']), authorChannelName):
          add_spam(current, config, miscData, currentCommentDict, videoID)

    # Check Modes: Comment Text
    elif filtersDict['filterMode'] == "Text":
      if filtersDict['filterSubMode'] == "chars":
        commentText = utils.make_char_set(str(commentText))
        if any(x in filtersDict['CustomCommentTextFilter'] for x in commentText):
          add_spam(current, config, miscData, currentCommentDict, videoID)
      elif filtersDict['filterSubMode'] == "string":
        if utils.check_list_against_string(listInput=filtersDict['CustomCommentTextFilter'], stringInput=commentText, caseSensitive=False):
          add_spam(current, config, miscData, currentCommentDict, videoID)
      elif filtersDict['filterSubMode'] == "regex":
        if re.search(str(filtersDict['CustomRegexPattern']), commentText):
          add_spam(current, config, miscData, currentCommentDict, videoID)

    # Check Modes: Name and Text
    elif filtersDict['filterMode'] == "NameAndText":
      if filtersDict['filterSubMode'] == "chars":
        authorChannelName = utils.make_char_set(str(authorChannelName))
        commentText = utils.make_char_set(str(commentText))
        if any(x in filtersDict['CustomUsernameFilter'] for x in authorChannelName):
          add_spam(current, config, miscData, currentCommentDict, videoID)
        elif any(x in filtersDict['CustomCommentTextFilter'] for x in commentText):
          add_spam(current, config, miscData, currentCommentDict, videoID)
      elif filtersDict['filterSubMode'] == "string":
        if utils.check_list_against_string(listInput=filtersDict['CustomUsernameFilter'], stringInput=authorChannelName, caseSensitive=False):
          add_spam(current, config, miscData, currentCommentDict, videoID)
        elif utils.check_list_against_string(listInput=filtersDict['CustomCommentTextFilter'], stringInput=commentText, caseSensitive=False):
          add_spam(current, config, miscData, currentCommentDict, videoID)
      elif filtersDict['filterSubMode'] == "regex":
        if re.search(str(filtersDict['CustomRegexPattern']), authorChannelName):
          add_spam(current, config, miscData, currentCommentDict, videoID)
        elif re.search(str(filtersDict['CustomRegexPattern']), commentText):
          add_spam(current, config, miscData, currentCommentDict, videoID)

    # Check Modes: Auto ASCII (in username)
    elif filtersDict['filterMode'] == "AutoASCII":
      if re.search(str(filtersDict['CustomRegexPattern']), authorChannelName):
        add_spam(current, config, miscData, currentCommentDict, videoID)

    # Check Modes: Auto Smart (in username or comment text)
    # Here inputtedComment/Author Filters are tuples of, where 2nd element is list of char-sets to check against
    ## Also Check if reply author ID is same as parent comment author ID, if so, ignore (to account for users who reply to spammers)
    elif filtersDict['filterMode'] == "AutoSmart" or filtersDict['filterMode'] == "SensitiveSmart":
      smartFilter = filtersDict['CustomCommentTextFilter']
      # Receive Variables
      compiledRegexDict = smartFilter['compiledRegexDict']
      numberFilterSet = smartFilter['spammerNumbersSet']
      compiledNumRegex = smartFilter['compiledNumRegex']
      minNumbersMatchCount = smartFilter['minNumbersMatchCount']
      bufferChars = compiledRegexDict['bufferChars']
      #usernameBlackCharsSet = smartFilter['usernameBlackCharsSet']
      spamGenEmojiSet = smartFilter['spamGenEmojiSet']
      redAdEmojiSet = smartFilter['redAdEmojiSet']
      yellowAdEmojiSet = smartFilter['yellowAdEmojiSet']
      hrtSet = smartFilter['hrtSet']
      languages = smartFilter['languages']
      sensitive =  smartFilter['sensitive']
      rootDomainRegex = smartFilter['rootDomainRegex']
      # Spam Lists
      spamListCombinedRegex = smartFilter['spamListCombinedRegex']
      

      # if debugSingleComment == True: 
      #   if input("Sensitive True/False: ").lower() == 'true': sensitive = True
      #   else: sensitive = False

      # Check for sensitive smart mode  
      if sensitive == True:
        rootDomainRegex = smartFilter['sensitiveRootDomainRegex']

      # Functions --------------------------------------------------------------
      def findOnlyObfuscated(regexExpression, originalWord, stringToSearch):
        # Confusable thinks s and f look similar, have to compensate to avoid false positive
        ignoredConfusablesConverter = {ord('f'):ord('s'),ord('s'):ord('f')} 
        result = re.findall(regexExpression, stringToSearch.lower())  
        if result == None:
          return False
        else:
          for match in result:
            lowerWord = originalWord.lower()
            for char in compiledRegexDict['bufferChars']:
              match = match.strip(char)
            if match.lower() != lowerWord and match.lower() != lowerWord.translate(ignoredConfusablesConverter):
              return True

      def remove_unicode_categories(string):
        return "".join(char for char in string if unicodedata.category(char) not in smartFilter['unicodeCategoriesStrip'])

      def check_if_only_a_link(string):
        result = re.match(compiledRegexDict['onlyVideoLinkRegex'], string)
        if result == None:
          return False
        elif result.group(0) and len(result.group(0)) == len(string):
          return True
        else:
          return False

      # ------------------------------------------------------------------------

      # Normalize usernames and text, remove multiple whitespace and invisible chars
      commentText = re.sub(' +', ' ', commentText)
      # https://stackoverflow.com/a/49695605/17312053
      commentText = "".join(k if k in bufferChars else "".join(v) for k,v in itertools.groupby(commentText, lambda c: c))
      commentText = remove_unicode_categories(commentText)

      authorChannelName = re.sub(' +', ' ', authorChannelName)
      authorChannelName = remove_unicode_categories(authorChannelName)

      # Processed Variables
      combinedString = authorChannelName + commentText
      combinedSet = utils.make_char_set(combinedString, stripLettersNumbers=True, stripPunctuation=True)
      #usernameSet = utils.make_char_set(authorChannelName)

      # Run Checks
      if authorChannelID == parentAuthorChannelID:
        pass
      elif len(numberFilterSet.intersection(combinedSet)) >= minNumbersMatchCount:
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif compiledNumRegex.search(combinedString):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      # Black Tests
        #elif usernameBlackCharsSet.intersection(usernameSet):
        #  add_spam(current, config, miscData, currentCommentDict, videoID)
      elif any(re.search(expression[1], authorChannelName) for expression in compiledRegexDict['usernameBlackWords']):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif any(findOnlyObfuscated(expression[1], expression[0], combinedString) for expression in compiledRegexDict['blackAdWords']):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif any(findOnlyObfuscated(expression[1], expression[0], commentText) for expression in compiledRegexDict['textObfuBlackWords']):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif any(re.search(expression[1], commentText) for expression in compiledRegexDict['textExactBlackWords']):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif any(findOnlyObfuscated(expression[1], expression[0], authorChannelName) for expression in compiledRegexDict['usernameObfuBlackWords']):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif re.search(spamListCombinedRegex, combinedString):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif check_if_only_a_link(commentText.strip()):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif sensitive == True and re.search(smartFilter['usernameConfuseRegex'], authorChannelName):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif sensitive == False and findOnlyObfuscated(smartFilter['usernameConfuseRegex'], miscData.channelOwnerName, authorChannelName):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      # Multi Criteria Tests
      else:
        # Defaults
        yellowCount = 0
        redCount = 0

        languageCount = 0
        for language in languages:
          if language[2].intersection(combinedSet):
            languageCount += 1

        # Yellow Tests
        if any(findOnlyObfuscated(expression[1], expression[0], combinedString) for expression in compiledRegexDict['yellowAdWords']):
          yellowCount += 1

        hrtTest = len(hrtSet.intersection(combinedSet))
        if hrtTest >= 2:
          if sensitive == False:
            yellowCount += 1
          if sensitive == True:
            redCount += 1
        elif hrtTest >= 1 and sensitive == True:
          yellowCount += 1

        if yellowAdEmojiSet.intersection(combinedSet):
          yellowCount += 1

        if spamGenEmojiSet.intersection(combinedSet) and sensitive == False:
          yellowCount += 1

        if combinedString.count('#') >= 5:
          yellowCount += 1

        if combinedString.count('\n') >= 10:
          yellowCount += 1

        if languageCount >= 2:
          yellowCount += 1

        if re.search(rootDomainRegex, combinedString.lower()):
          yellowCount += 1

        # Red Tests
        #if any(foundObfuscated(re.findall(expression[1], combinedString), expression[0]) for expression in compiledRegexDict['redAdWords']):
        if any(findOnlyObfuscated(expression[1], expression[0], combinedString) for expression in compiledRegexDict['redAdWords']):
          redCount += 1

        if any(re.search(expression[1], combinedString) for expression in compiledRegexDict['exactRedAdWords']):
          redCount += 1

        if redAdEmojiSet.intersection(combinedSet):
          redCount += 1

        if spamGenEmojiSet.intersection(combinedSet) and sensitive == True:
          redCount += 1

        if any(re.search(expression[1], authorChannelName) for expression in compiledRegexDict['usernameRedWords']):
          redCount += 1

        # Calculate Score
        if yellowCount >= 3:
          add_spam(current, config, miscData, currentCommentDict, videoID)
        elif redCount >= 2:
          add_spam(current, config, miscData, currentCommentDict, videoID)
        elif redCount >= 1 and yellowCount >= 1:
          add_spam(current, config, miscData, currentCommentDict, videoID)
        elif redCount >= 1 and sensitive == True:
          add_spam(current, config, miscData, currentCommentDict, videoID)
  else:
    pass

##########################################################################################
################################ DELETE COMMENTS #########################################
########################################################################################## 

# Takes in list of comment IDs to delete, breaks them into 50-comment chunks, and deletes them in groups
def delete_found_comments(commentsList, banChoice, deletionMode, recoveryMode=False):
  print("\n")
  if deletionMode == "rejected":
    actionPresent = "Deleting"
    actionPast = "Deleted"
  elif deletionMode == "heldForReview":
    actionPresent = "Hiding"
    actionPast = "Hidden"
  elif deletionMode == "reportSpam":
    actionPresent = "Reporting"
    actionPast = "Reported"
  else:
    actionPresent = "Processing"
    actionPast = "Processed"

  # Local Functions 
  def setStatus(commentIDs): #Does the actual deletion
    if deletionMode == "reportSpam":
      result = auth.YOUTUBE.comments().markAsSpam(id=commentIDs).execute()
      if len(result) > 0:
        print("\nSomething may gone wrong when reporting the comments.")    
    elif deletionMode == "heldForReview" or deletionMode == "rejected" or deletionMode == "published":
      auth.YOUTUBE.comments().setModerationStatus(id=commentIDs, moderationStatus=deletionMode, banAuthor=banChoice).execute()
    else:
      print("Invalid deletion mode. This is definitely a bug, please report it here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
      print("Deletion Mode Is: " + deletionMode)
      input("Press Enter to Exit...")
      sys.exit()


  def print_progress(d, t, recoveryMode=False): 
    if recoveryMode == False:
      print(actionPresent +" Comments... - Progress: [" + str(d) + " / " + str(t) + "] (In Groups of 50)", end="\r")
    elif recoveryMode == True:
      print("Recovering Comments... - Progress: [" + str(d) + " / " + str(t) + "] (In Groups of 50)", end="\r")

  total = len(commentsList)
  deletedCounter = 0  
  print_progress(deletedCounter, total, recoveryMode)

  if total > 50:                                  # If more than 50 comments, break into chunks of 50
    remainder = total % 50                      # Gets how many left over after dividing into chunks of 50
    numDivisions = int((total-remainder)/50)    # Gets how many full chunks of 50 there are
    for i in range(numDivisions):               # Loops through each full chunk of 50
      setStatus(commentsList[i*50:i*50+50])
      deletedCounter += 50
      print_progress(deletedCounter, total, recoveryMode)
    if remainder > 0:
      setStatus(commentsList[numDivisions*50:total]) # Handles any leftover comments range after last full chunk
      deletedCounter += remainder
      print_progress(deletedCounter, total, recoveryMode)
  else:
      setStatus(commentsList)
      print_progress(deletedCounter, total, recoveryMode)
  if deletionMode == "reportSpam":
    print(f"{F.YELLOW}Comments Reported!{S.R} If no error messages were displayed, then everything was successful.")
  elif recoveryMode == False:
    print("Comments " + actionPast + "! Will now verify each is gone.                          \n")
  elif recoveryMode == True:
    print("Comments Recovered! Will now verify each is back.                          \n")

# Class for custom exception to throw if a comment is found to remain
class CommentFoundError(Exception):
    pass

# Takes in list of comment IDs and video IDs, and checks if comments still exist individually
def check_deleted_comments(commentInput):
    i = 0 # Count number of remaining comments
    j = 1 # Count number of checked
    total = len(commentInput)
    unsuccessfulResults = []
    commentList = []

    if type(commentInput) == list:
      commentList = commentInput
    elif type(commentInput) == dict:
      commentList = list(commentInput.keys())
      
    # Wait 2 seconds so YouTube API has time to update comment status
    print("Preparing...", end="\r")
    time.sleep(1)
    print("                               ")
    print("    (Note: You can disable deletion success checking in the config file, to save time and API quota)\n")
    for commentID in commentList:
      try:
        results = auth.YOUTUBE.comments().list(
          part="snippet",
          id=commentID,  
          maxResults=1,
          fields="items",
          textFormat="plainText"
        ).execute()

        print("Verifying Deleted Comments: [" + str(j) + " / " + str(total) + "]", end="\r")
        j += 1

        if results["items"]:  # Check if the items result is empty
          raise CommentFoundError

      # If comment is found and possibly not deleted, print out video ID and comment ID
      except CommentFoundError:
        if type(commentInput) == dict:
          print("Possible Issue Deleting Comment: " + str(commentID) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(commentInput[commentID]['videoID']) + "&lc=" + str(commentID))
        elif type(commentInput) == list:
          print("Possible Issue Deleting Comment: " + str(commentID))
        i += 1
        unsuccessfulResults.append(results)
        pass
      except Exception:
        if type(commentInput) == dict:
          print("Unhandled Exception While Deleting Comment: " + str(commentID) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(commentInput[commentID]['videoID']) + "&lc=" + str(commentID))
        elif type(commentInput) == list:
          print("Unhandled Exception While Deleting Comment: " + str(commentID))
        i += 1
        unsuccessfulResults.append(results)
        pass

    if i == 0:
      print("\n\nSuccess: All comments should be gone.")
    elif i > 0:
      print("\n\nWarning: " + str(i) + " comments may remain. Check links above or try running the program again. An error log file has been created: 'Deletion_Error_Log.txt'")
      # Write error log
      f = open("Deletion_Error_Log.txt", "a")
      f.write("----- YT Spammer Purge Error Log: Possible Issue Deleting Comments ------\n\n")
      f.write(str(unsuccessfulResults))
      f.write("\n\n")
      f.close()
    else:
      print("\n\nSomething strange happened... The comments may or may have not been deleted.")

    return None

# Class for custom exception to throw if a comment is found to remain
class CommentNotFoundError(Exception):
  pass

def check_recovered_comments(commentsList):
  i = 0 # Count number of remaining comments
  j = 1 # Count number of checked
  total = len(commentsList)
  unsuccessfulResults = []

  for comment in commentsList:
    try:
      results = auth.YOUTUBE.comments().list(
        part="snippet",
        id=comment,  
        maxResults=1,
        fields="items",
        textFormat="plainText"
      ).execute()
      print("Verifying Deleted Comments: [" + str(j) + " / " + str(total) + "]", end="\r")
      j += 1

      if not results["items"]:  # Check if the items result is empty
        raise CommentNotFoundError

    except CommentNotFoundError:
      #print("Possible Issue Deleting Comment: " + str(key) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(value) + "&lc=" + str(key))
      print("Possible Issue Restoring Comment: " + str(comment))
      i += 1
      unsuccessfulResults.append(comment)
  
  if i == 0:
      print(f"\n\n{F.LIGHTGREEN_EX}Success: All spam comments should be restored!{S.R}")
      print("You can view them by using the links to them in the same log file you used.")

  elif i > 0:
    print("\n\nWarning: " + str(i) + " comments may have not been restored. See above list.")
    print("Use the links to the comments from the log file you used, to verify if they are back or not.")

  input("\nRecovery process finished. Press Enter to return to main menu...")
  return True

# Removes comments by user-selected authors from list of comments to delete
def exclude_authors(current, miscData, inputtedString, logInfo=None):
  expression = r"(?<=exclude ).*" # Match everything after 'exclude '
  result = str(re.search(expression, inputtedString).group(0))
  result = result.replace(" ", "")
  SampleIDsToExclude = result.split(",")
  authorIDsToExclude = []
  displayString = ""
  excludedCommentsDict = {}
  rtfFormattedExcludes = ""
  plaintextFormattedExcludes = ""
  commentIDExcludeList = []

  # Get authorIDs for selected sample comments
  for authorID, info in current.matchSamplesDict.items():
    if str(info['index']) in SampleIDsToExclude:
      authorIDsToExclude += [authorID]

  # Get comment IDs to be excluded
  for comment, metadata in current.matchedCommentsDict.items():
    if metadata['authorID'] in authorIDsToExclude:
      commentIDExcludeList.append(comment)
  # Remove all comments by selected authors from dictionary of comments
  for comment in commentIDExcludeList:
    if comment in current.matchedCommentsDict.keys():
      excludedCommentsDict[comment] = current.matchedCommentsDict.pop(comment)

  # Create strings that can be used in log files
  rtfFormattedExcludes += f"\\line \n Comments Excluded From Deletion: \\line \n"
  rtfFormattedExcludes += f"(Values = Comment ID | Author ID | Author Name | Comment Text) \\line \n"
  plaintextFormattedExcludes += f"\nComments Excluded From Deletion:\n"
  plaintextFormattedExcludes += f"(Values = Comment ID | Author ID | Author Name | Comment Text)\n"
  for commentID, meta in excludedCommentsDict.items():
    rtfFormattedExcludes += f"{str(commentID)}  |  {str(excludedCommentsDict[commentID]['authorID'])}  |  {str(excludedCommentsDict[commentID]['authorName'])}  |   {str(excludedCommentsDict[commentID]['text'])} \\line \n"
  for commentID, meta in excludedCommentsDict.items():
    plaintextFormattedExcludes += f"{str(commentID)}  |  {str(excludedCommentsDict[commentID]['authorID'])}  |  {str(excludedCommentsDict[commentID]['authorName'])}  |   {str(excludedCommentsDict[commentID]['text'])}\n"

  # Verify removal
  for comment in current.matchedCommentsDict.keys():
    if comment in commentIDExcludeList:
      print(f"{F.LIGHTRED_EX}FATAL ERROR{S.R}: Something went wrong while trying to exclude comments. No comments have been deleted.")
      print(f"You should {F.YELLOW}DEFINITELY{S.R} report this bug here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
      print("Provide the error code: X-1")
      input("Press Enter to Exit...")
      sys.exit()

  # Get author names and IDs from dictionary, and display them
  for author in authorIDsToExclude:
    displayString += f"    User ID: {author}   |   User Name: {current.matchSamplesDict[author]['authorName']}\n"
    with open(miscData.resources['Whitelist']['PathWithName'], "a", encoding="utf-8") as f:
      f.write(f"# [Excluded]  Channel Name: {current.matchSamplesDict[author]['authorName']}  |  Channel ID: " + "\n")
      f.write(f"{author}\n")

  print(f"\n{F.CYAN}All {len(excludedCommentsDict)} comments{S.R} from the {F.CYAN}following {len(authorIDsToExclude)} users{S.R} are now {F.LIGHTGREEN_EX}excluded{S.R} from deletion:")
  print(displayString)

  # Re-Write Log File
  if logInfo:
    print("Updating log file, please wait...", end="\r")
    logging.rewrite_log_file(current, logInfo)
    if logInfo['logMode'] == "rtf":
      logging.write_rtf(current.logFileName, str(rtfFormattedExcludes))
    elif logInfo['logMode'] == "plaintext":
      logging.write_plaintext_log(current.logFileName, str(plaintextFormattedExcludes))
    print("                                          ")
  
  input("\nPress Enter to decide what to do with the rest...")
  
  return current, excludedCommentsDict, rtfFormattedExcludes, plaintextFormattedExcludes # May use excludedCommentsDict later for printing them to log file


################################# Get Most Recent Videos #####################################
# Returns a list of lists
def get_recent_videos(channel_id, numVideosTotal):
  def get_block_of_videos(nextPageToken, j, k, numVideosBlock = 5):
    result = auth.YOUTUBE.search().list(
      part="snippet",
      channelId=channel_id,
      type='video',
      order='date',
      pageToken=nextPageToken,
      #fields='nextPageToken,items/id/videoId,items/snippet/title',
      maxResults=numVideosBlock,
      ).execute()

    for item in result['items']:
      videoID = str(item['id']['videoId'])
      videoTitle = str(item['snippet']['title']).replace("&quot;", "\"").replace("&#39;", "'")
      commentCount = validation.validate_video_id(videoID, pass_exception = True)[3]
      #Skips over video if comment count is zero, or comments disabled / is live stream
      if str(commentCount) == '0':
        print(f"{B.YELLOW}{F.BLACK} Skipping {S.R} {F.LIGHTRED_EX}Video with no comments:{S.R} " + str(item['snippet']['title']))
        k+=1
        continue

      recentVideos.append({})
      recentVideos[j]['videoID'] = videoID
      recentVideos[j]['videoTitle'] = videoTitle
      if str(commentCount)=="MainMenu":
        return None, None, "MainMenu"
      recentVideos[j]['commentCount'] = commentCount
      j+=1
      k+=1

    # Get token for next page
    try:
      nextPageToken = result['nextPageToken']
    except KeyError:
      nextPageToken = "End"

    #      0              1  2  3
    return nextPageToken, j, k, ""
    #----------------------------------------------------------------
  
  nextPageToken = None
  recentVideos = [] #List of dictionaries
  abortCheck = "" # Used to receive "MainMenu" if user wants to exit, when entering 
  j,k = 0,0 # i = number of videos added to list, k = number of videos checked (different only if one video skipped because no comments)
  if numVideosTotal <=5:
    result = get_block_of_videos(None, j, k, numVideosBlock=numVideosTotal)
    if result[3] == "MainMenu":
      return "MainMenu"
  else:
    while nextPageToken != "End" and k < numVideosTotal and str(abortCheck) != "MainMenu":
      print("Retrieved " + str(len(recentVideos)) + "/" + str(numVideosTotal) + " videos.", end="\r")
      remainingVideos = numVideosTotal - k
      if remainingVideos <= 5:
        nextPageToken, j, k, abortCheck = get_block_of_videos(nextPageToken, j, k, numVideosBlock = remainingVideos)
      else:
        nextPageToken, j, k, abortCheck = get_block_of_videos(nextPageToken, j, k, numVideosBlock = 5)
      if str(nextPageToken[0]) == "MainMenu":
        return "MainMenu"
  print("                                          ")
  return recentVideos

##################################### PRINT STATS ##########################################

# Prints Scanning Statistics, can be version that overwrites itself or one that finalizes and moves to next line
def print_count_stats(current, miscData, videosToScan, final):
  # Use videosToScan (list of dictionaries) to retrieve total number of comments
  if videosToScan:
    totalComments = miscData.totalCommentCount
    totalScanned = current.scannedRepliesCount + current.scannedCommentsCount
    percent = ((totalScanned / totalComments) * 100)
    progress = f"Total: [{str(totalScanned)}/{str(totalComments)}] ({percent:.0f}%) ".ljust(27, " ") + "|" #Formats percentage to 0 decimal places
  else:
    progress = ""
  
  comScanned = str(current.scannedCommentsCount)
  repScanned = str(current.scannedRepliesCount)
  matchCount = str(len(current.matchedCommentsDict))

  if final == True:
    print(f" {progress} Comments Scanned: {F.YELLOW}{comScanned}{S.R} | Replies Scanned: {F.YELLOW}{repScanned}{S.R} | Matches Found So Far: {F.LIGHTRED_EX}{matchCount}{S.R}\n")
  else:
    print(f" {progress} Comments Scanned: {F.YELLOW}{comScanned}{S.R} | Replies Scanned: {F.YELLOW}{repScanned}{S.R} | Matches Found So Far: {F.LIGHTRED_EX}{matchCount}{S.R}", end = "\r")
  
  return None