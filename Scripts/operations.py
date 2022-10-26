#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from Scripts.shared_imports import *
import Scripts.utils as utils
import Scripts.auth as auth
import Scripts.validation as validation
from Scripts.utils import choice

import unicodedata
import time
import itertools
from datetime import datetime
from rapidfuzz import fuzz
from googleapiclient.errors import HttpError

##########################################################################################
############################## GET COMMENT THREADS #######################################
##########################################################################################

# Call the API's commentThreads.list method to list the existing comments.
def get_comments(current, filtersDict, miscData, config, allVideoCommentsDict, scanVideoID=None, nextPageToken=None, videosToScan=None):  # None are set as default if no parameters passed into function
  # Initialize some variables
  authorChannelName = None
  commentText = None
  parentAuthorChannelID = None

  fieldsToFetch = "nextPageToken,items/snippet/topLevelComment/id,items/replies/comments,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/videoId,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/authorDisplayName,items/snippet/topLevelComment/snippet/textDisplay,items/snippet/topLevelComment/snippet/publishedAt"

  try:
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
  except HttpError as hx:
    traceback.print_exc()
    utils.print_http_error_during_scan(hx)
    current.errorOccurred = True
    return "Error", None
  except Exception as ex:
    traceback.print_exc()
    utils.print_exception_during_scan(ex)
    current.errorOccurred = True
    return "Error", None
    
  # Get token for next page. If no token, sets to 'End'
  RetrievedNextPageToken = results.get("nextPageToken", "End")
  
  # After getting all comments threads for page, extracts data for each and stores matches in current.matchedCommentsDict
  # Also goes through each thread and executes get_replies() to get reply content and matches
  for item in results["items"]:
    comment = item["snippet"]["topLevelComment"]
    videoID = comment["snippet"]["videoId"]
    parent_id = item["snippet"]["topLevelComment"]["id"]
    numReplies = item["snippet"]["totalReplyCount"]
    timestamp = item["snippet"]["topLevelComment"]["snippet"]["publishedAt"]

    # In case there are no replies
    if 'replies' in item and 'comments' in item["replies"]:
      limitedRepliesList = item["replies"]["comments"] # API will return a limited number of replies (~5), but to get all, need to make separate call
    else:
      limitedRepliesList = []

    # On rare occasions a comment will be there but the channel name will be empty, so this allows placeholders
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
      'videoID': videoID,
      'timestamp':timestamp,
      'originalCommentID': None
      }
    if config['json_log_all_comments'] == True:
      currentCommentDict['uploaderChannelID'] = miscData.channelOwnerID
      currentCommentDict['uploaderChannelName'] = miscData.channelOwnerName
      currentCommentDict['textUnsanitized'] = str(commentText)
      currentCommentDict['videoTitle'] = utils.get_video_title(current, videoID)
      currentCommentDict['matchReason'] = None
      currentCommentDict['isSpam'] = 'False'


    check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID)
    current.scannedCommentsCount += 1

    #Log All Comments
    try:
      if parentAuthorChannelID in allVideoCommentsDict:
        allVideoCommentsDict[parentAuthorChannelID].append(currentCommentDict)
      else:
        allVideoCommentsDict[parentAuthorChannelID] = [currentCommentDict]
    except TypeError: # This might not be necessary, might remove later if not
      pass
    
    if numReplies > 0 and (filtersDict['filterMode'] == "AutoSmart" or filtersDict['filterMode'] == "SensitiveSmart") and config['detect_spam_threads'] == True:
        parentCommentDict = currentCommentDict
    else:
      parentCommentDict = None

    # If there are more replies than in the limited list
    if numReplies > 0 and len(limitedRepliesList) < numReplies:
      allVideoCommentsDict = get_replies(current, filtersDict, miscData, config, parent_id, videoID, parentAuthorChannelID, videosToScan, allVideoCommentsDict, parentCommentDict=parentCommentDict)
      if allVideoCommentsDict == "Error":
        return "Error", None

    # If all the replies are in the limited list
    elif numReplies > 0 and len(limitedRepliesList) == numReplies: # limitedRepliesList can never be more than numReplies
      allVideoCommentsDict = get_replies(current, filtersDict, miscData, config, parent_id, videoID, parentAuthorChannelID, videosToScan, allVideoCommentsDict, repliesList=limitedRepliesList, parentCommentDict=parentCommentDict)
      if allVideoCommentsDict == "Error":
        return "Error", None
    else:
      print_count_stats(current, miscData, videosToScan, final=False)  # Updates displayed stats if no replies

  # Runs after all comments scanned
  if RetrievedNextPageToken == "End" and allVideoCommentsDict and scanVideoID is not None:
    dupeCheckModes = utils.string_to_list(config['duplicate_check_modes'])
    if filtersDict['filterMode'].lower() in dupeCheckModes:
      print(" Analyzing For Duplicates                                                                                        ", end="\r")
      check_duplicates(current, config, miscData, allVideoCommentsDict, scanVideoID)
      print("                                                                                                                       ")
    repostCheckModes = utils.string_to_list(config['stolen_comments_check_modes'])
    if filtersDict['filterMode'].lower() in repostCheckModes:
      print(" Analyzing For Reposts                                                                                           ", end="\r")
      check_reposts(current, config, miscData, allVideoCommentsDict, scanVideoID)
      print("                                                                                                                       ")

  current.allScannedCommentsDict.update(allVideoCommentsDict)
  return RetrievedNextPageToken, allVideoCommentsDict


##########################################################################################
##################################### GET REPLIES ########################################
##########################################################################################

# Call the API's comments.list method to list the existing comment replies.
def get_replies(current, filtersDict, miscData, config, parent_id, videoID, parentAuthorChannelID, videosToScan, allVideoCommentsDict, parentCommentDict=None, repliesList=None):
  # Initialize some variables
  authorChannelName = None
  commentText = None
  threadDict = {}
  
  if repliesList == None:
    fieldsToFetch = "nextPageToken,items/snippet/authorChannelId/value,items/id,items/snippet/authorDisplayName,items/snippet/textDisplay,items/snippet/publishedAt"
    replies = []
    replyPageToken = None

    while replyPageToken != "End":
      try:
        results = auth.YOUTUBE.comments().list(
          part="snippet",
          parentId=parent_id,
          pageToken=replyPageToken,
          maxResults=100,
          fields=fieldsToFetch,
          textFormat="plainText"
        ).execute()
      except HttpError as hx:
        traceback.print_exc()
        utils.print_http_error_during_scan(hx)
        current.errorOccurred = True
        return "Error"
      except Exception as ex:
        traceback.print_exc()
        utils.print_exception_during_scan(ex)
        current.errorOccurred = True
        return "Error"

      replies.extend(results["items"])

      # Get token for next page
      if "nextPageToken" in results:
        replyPageToken = results["nextPageToken"]
      else:
        replyPageToken = "End"

  else:
    replies = repliesList
 
  # Create list of author names in current thread, add into list - Only necessary when scanning comment text
  allThreadAuthorNames = []

  # Iterates through items in results
  # Need to be able to catch exceptions because sometimes the API will return a comment from non-existent / deleted channel
  # Need individual tries because not all are fetched for each mode
  for reply in replies:  
    replyID = reply["id"]
    timestamp = reply["snippet"]["publishedAt"]
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
      'videoID': videoID,
      'timestamp':timestamp,
      'originalCommentID': None
      }
    if config['json_log_all_comments'] == True:
      currentCommentDict['uploaderChannelID'] = miscData.channelOwnerID
      currentCommentDict['uploaderChannelName'] = miscData.channelOwnerName
      currentCommentDict['textUnsanitized'] = str(commentText)
      currentCommentDict['videoTitle'] = utils.get_video_title(current, videoID)
      currentCommentDict['matchReason'] = None
      currentCommentDict['isSpam'] = 'False'

    if parentCommentDict:
      threadDict[replyID] = currentCommentDict

    check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID, allThreadAuthorNames=allThreadAuthorNames)

    #Log All Comments
    try:
      if authorChannelID in allVideoCommentsDict:
        allVideoCommentsDict[authorChannelID].append(currentCommentDict)
      else:
        allVideoCommentsDict[authorChannelID] = [currentCommentDict]
    except TypeError: # Again, might not be necessary, might remove later
      pass

    # Update latest stats
    current.scannedRepliesCount += 1 
    print_count_stats(current, miscData, videosToScan, final=False)
  
  # This won't exist if spam thread detection isn't enabled, because of check in get_comments function
  if parentCommentDict:
    current = check_spam_threads(current, filtersDict, miscData, config, parentCommentDict, threadDict)

  return allVideoCommentsDict


#####################################################################################################
def check_spam_threads(current, filtersDict, miscData, config, parentCommentDict, threadDict):
  # Note For Debugging: Parent Comment Author ID = parentCommentDict['authorChannelID']
  threadWordsRegex = filtersDict['CustomCommentTextFilter']['threadFiltersDict']['threadWordsRegex']
  threadPhrasesRegex = filtersDict['CustomCommentTextFilter']['threadFiltersDict']['threadPhrasesRegex']
  monetWordsRegex = filtersDict['CustomCommentTextFilter']['threadFiltersDict']['monetWordsRegex']
  nameRegex = filtersDict['CustomCommentTextFilter']['threadFiltersDict']['nameRegex']
  nakedNameRegex = filtersDict['CustomCommentTextFilter']['threadFiltersDict']['nakedNameRegex']
  cashRegex = filtersDict['CustomCommentTextFilter']['threadFiltersDict']['cashRegex']
  salutationRegex = filtersDict['CustomCommentTextFilter']['threadFiltersDict']['salutationRegex']
  ignoreList = ['earn', 'trade', 'invest', 'signal', 'crypto', ' is', ' she', ' he']
  spam = False
  threadAnalysisDict = {}
  preliminaryCount, redCount, yellowCount, nameCount, fullNameCount, partialNameCount, susMentionCount = 0, 0, 0, 0, 0, 0, 0
  nameList, partialNameList, fullNameList =[] , [], []
  name, partialName, fullName = "", "", ""
  minReplies = 5

  if any(item in parentCommentDict['commentText'].lower() for item in miscData.spamLists['spamThreadsList']):
    add_spam(current, config, miscData, parentCommentDict, parentCommentDict['videoID'], matchReason="Spam Bot Thread")
    return current
  # Preliminary Analysis
  if not threadDict or len(threadDict) < minReplies:
    return current
  matchCount = threadWordsRegex.findall(parentCommentDict['commentText'].lower())
  if matchCount:
      preliminaryCount += len(matchCount)
  if salutationRegex.search(parentCommentDict['commentText'].lower()):
    preliminaryCount += 1
  if preliminaryCount < 2:
    return current

  # Shoves all comments by each author into one each. Each author ID is key, combined comments text is value
  for _, data in threadDict.items():
    if data['authorChannelID'] in threadAnalysisDict:
      threadAnalysisDict[data['authorChannelID']] = threadAnalysisDict[data['authorChannelID']] + " " + re.sub(' +', ' ', data['commentText']).replace("\n", " ").replace("\r", " ").lower()
    else:
      threadAnalysisDict[data['authorChannelID']] = re.sub(' +', ' ', data['commentText']).replace("\n", " ").replace("\r", " ").lower()

  # When all authors have one combined comment text, put each into list
  threadAnalysisList = list(threadAnalysisDict.values())
  
  # -------------------------------------------------------------------------------
  def processResult(regResult, naked):
    if naked:
      g1 = 1
      g2 = 20
      g3 = 21
    else:
      g1 = 1
      g2 = 11
      g3 = 12

    len1 = len(regResult.group(g1))
    len2 = len(regResult.group(g2))
    len3 = len(regResult.group(g3))

    if (not naked and len3 > 3) or (naked and len2 >= 4 and len3 >= 5):
      name = regResult.group(g2).strip() + " " + regResult.group(g3).strip()
      name = re.sub(' +', ' ', name)
    else:
      name = ""

    if not naked:
      partialName = regResult.group(1).strip() + " " + regResult.group(g2).strip()
      partialName = re.sub(' +', ' ', partialName)
    else:
      partialName = ""

    if not naked:
      fullName = regResult.group(0)
    else:
      fullName = ""

    return name, partialName, fullName
  # -------------------------------------------------------------------------------
  def regexSearchNames(regex, name, partialName, fullName, naked=False):
    # Get Potential Names
    for comment in threadAnalysisList:
      regResult = re.search(regex, comment)
      if regResult:
        x, y, z = processResult(regResult, naked)
        # Strip empty
        name.append(x)
        partialName.append(y)
        fullName.append(z)

    regResult = re.search(regex, parentCommentDict['commentText'].lower())
    if regResult:
      x, y, z = processResult(regResult, naked)
      if x:
        name.append(x)
      if y:
        partialName.append(y)
      if z:
        fullName.append(z)
    return name, partialName, fullName
  # -------------------------------------------------------------------------------
  def remove_ignore(nameList):
    removeList = []
    for n in nameList:
      for word in ignoreList:
        if word in n:
          removeList.append(n)
    if removeList:
      for item in removeList:
        if item in nameList:
          nameList.remove(item)
    return nameList
  # -------------------------------------------------------------------------------

  nameList, partialNameList, fullNameList = regexSearchNames(nameRegex, nameList, partialNameList, fullNameList)
  if not nameList:
    nameList, partialNameList, fullNameList = regexSearchNames(nakedNameRegex, nameList, partialNameList, fullNameList,naked=True)
    partialNameList = []
    fullNameList = []

  while "" in nameList:
    nameList.remove("")
  while "" in partialNameList:
    partialNameList.remove("")
  while "" in fullNameList:
    fullNameList.remove("")
  
  # Determine most common names
  if nameList:
    name = max(set(nameList), key = nameList.count)
    if nameList.count(name) == 1:
      nameList = remove_ignore(nameList)
      if nameList:
        name = max(set(nameList), key = nameList.count)
      else:
        name = ""

  if partialNameList:
    partialName = max(set(partialNameList), key = partialNameList.count)
    if partialNameList.count(partialName) == 1:
      partialNameList = remove_ignore(partialNameList)
      if partialNameList:
        partialName = max(set(partialNameList), key = partialNameList.count)
      else:
        partialName = ""

  if fullNameList:
    fullName = max(set(fullNameList), key = fullNameList.count)
    if fullNameList.count(fullName) == 1:
      fullNameList = remove_ignore(fullNameList)
      if fullNameList:
        fullName = max(set(fullNameList), key = fullNameList.count)
      else:
        fullName = ""
  
  # Analyze Thread
  for comment in threadAnalysisList:
    if name:
      if fullName and fullName in comment:
        fullNameCount += 1
      elif name and name in comment:
        nameCount += 1
      elif partialName and partialName in comment:
        partialNameCount += 1
    susMention = False
    if threadWordsRegex.search(comment):
      yellowCount += 1
      susMention = True
    if threadPhrasesRegex.search(comment):
      redCount += 1
      susMention = True
    if cashRegex.search(comment):
      if monetWordsRegex.search(comment):
        redCount += 1
      else:
        yellowCount += 1
      susMention = True
    if susMention:
      susMentionCount += 1

  if fullName in parentCommentDict['commentText'].lower() or name in parentCommentDict['commentText'].lower():
    fullNameCount += 1
    redCount += 1

  susRatio = susMentionCount / len(threadAnalysisList) # Number of people, not replies
  allNameCount = nameCount + partialNameCount + fullNameCount

  if susRatio > 0.7:
    if filtersDict['filterMode'] == "SensitiveSmart":
      add_spam(current, config, miscData, parentCommentDict, parentCommentDict['videoID'], matchReason="Spam Bot Thread")
      return current
    elif len(threadAnalysisList) >= 10:
      redCount += 2
    else:
      redCount += 1
  elif susRatio < 0.3:
    return current

  # Score
  if redCount >= 1 and yellowCount >= 5 and (susRatio > 0.75 or (allNameCount >= 4 or fullNameCount >= 2)):
    spam = True
  elif redCount > 2 and yellowCount >= 3 and (susRatio > 0.70 or (allNameCount >= 4 or fullNameCount >= 2)):
    spam = True
  elif redCount >= 2 and (allNameCount >= 5 or fullNameCount >= 3) and susRatio > 0.6:
    spam = True
  elif redCount >= 5 and susRatio > 0.5:
    spam = True
  elif yellowCount >= 10 and susRatio > 0.65:
    spam = True

  if spam == True:
    add_spam(current, config, miscData, parentCommentDict, parentCommentDict['videoID'], matchReason="Spam Bot Thread")

  return current

  
###################################### Community Post Thread Dict Maker #####################################################
def make_community_thread_dict(commentID, allCommunityCommentsDict):
  threadDict = {}
  if "." not in commentID: # Checks if is top level comment or reply
    for id in allCommunityCommentsDict.keys():
      if commentID in id and commentID != id:
        threadDict[id] = allCommunityCommentsDict[id]

  return threadDict
  

###################################### ADD SPAM #####################################################

# If the comment/username matches criteria based on mode, add key/value pair of comment ID and author ID to current.matchedCommentsDict
# Also add key-value pair of comment ID and video ID to dictionary
# Also count how many spam comments for each author
def add_spam(current, config, miscData, currentCommentDict, videoID, matchReason="Filter Match"):
  if matchReason == "Filter Match":
    dictToUse = current.matchedCommentsDict
  elif matchReason == "Duplicate":
    dictToUse = current.duplicateCommentsDict
  elif matchReason == "Also By Matched Author":
    dictToUse = current.otherCommentsByMatchedAuthorsDict
  elif matchReason == "Spam Bot Thread":
    dictToUse = current.spamThreadsDict
  elif matchReason == "Repost":
    dictToUse = current.repostedCommentsDict

  commentID = currentCommentDict['commentID']
  authorChannelName = currentCommentDict['authorChannelName']
  authorChannelID = currentCommentDict['authorChannelID']
  commentTextRaw = str(currentCommentDict['commentText']) # Use str() to ensure not pointing to same place in memory
  commentText = str(currentCommentDict['commentText']).replace("\r", "")

  if 'originalCommentID' in currentCommentDict:
    originalCommentID = currentCommentDict['originalCommentID']
  else:
    originalCommentID = "Unavailable or N/A"
  
  if 'timestamp' in currentCommentDict:
    timestamp = currentCommentDict['timestamp']
  else:
    timestamp = "Unavailable"

  dictToUse[commentID] = {'text':commentText, 'textUnsanitized':commentTextRaw, 'authorName':authorChannelName, 'authorID':authorChannelID, 'videoID':videoID, 'matchReason':matchReason, 'originalCommentID':originalCommentID, 'timestamp':timestamp}
  current.vidIdDict[commentID] = videoID # Probably remove this later, but still being used for now

  # Count of comments per author
  if authorChannelID in current.authorMatchCountDict:
    current.authorMatchCountDict[authorChannelID] += 1
  else:
    current.authorMatchCountDict[authorChannelID] = 1


  # If json_log_all_comments is enabled, this is not needed because this info is logged for all comments
  if config['json_log'] == True and config['json_log_all_comments'] == False:
    dictToUse[commentID]['uploaderChannelID'] = miscData.channelOwnerID
    dictToUse[commentID]['uploaderChannelName'] = miscData.channelOwnerName
    dictToUse[commentID]['videoTitle'] = utils.get_video_title(current, videoID)

def get_all_author_comments(current, config, miscData, allCommentsDict):
  # Make set of all matched author IDs
  print(" Finding all other comments by authors...", end="\r")
  totalCommentsAmount = len(allCommentsDict)
  scannedCount = 0
  matchedAuthorIDSet = set()
  for _, commentData in current.matchedCommentsDict.items():
    matchedAuthorIDSet.add(commentData['authorID'])

  # Go through all comments
  for authorID, authorCommentsListofDicts in allCommentsDict.items():
    if authorID in matchedAuthorIDSet:
      for commentDict in authorCommentsListofDicts:
        scannedCount += 1
        print(f" Finding all other comments by authors: [ {scannedCount/totalCommentsAmount*100:.2f}% ]".ljust(40, " "), end="\r")
        if commentDict['commentID'] not in current.matchedCommentsDict:
          add_spam(current, config, miscData, commentDict, commentDict['videoID'], matchReason="Also By Matched Author")
  print("".ljust(55, " "))

  return current


############################## Check Duplicates ######################################
def check_duplicates(current, config, miscData, allVideoCommentsDict, videoID):
  domainList =  miscData.resources['rootDomainList']

  # Get Lenvenshtein Distance Setting - Does not need to be validated here, because that happens at beginning of program
  levenshtein = float(config['levenshtein_distance'])
  
  # Get duplicate count setting - Does not need to be validated as int here, because that happens at beginning of program
  minimum_duplicates = int(config['minimum_duplicates'])
  if minimum_duplicates < 2:
    minimum_duplicates = 4
    print("\nError: minimum_duplicates config setting must be greater than 1. Defaulting to 8.")
    input("\nPress Enter to Continue...")
  
  # Get minimum duplicate length setting - Does not need to be validated as int here, because that happens at beginning of program
  minimum_duplicate_length = int(config['minimum_duplicate_length'])
  
  # Calculate number of authors to check, for progress
  authorCount = len(allVideoCommentsDict)
  scannedCount = 0

  # Run the actual duplicate checking
  for authorID, authorCommentsList in allVideoCommentsDict.items():
    # Don't scan channel owner, current user, or any user in whitelist. Also don't bother if author is already in matchedCommentsDict
    if auth.CURRENTUSER.id == authorID or miscData.channelOwnerID == authorID or authorID in miscData.resources['Whitelist']['WhitelistContents'] or any(authorID == value['authorID'] for key,value in current.matchedCommentsDict.items()):
      scannedCount +=1
      print(f" Analyzing For Duplicates: [ {scannedCount/authorCount*100:.2f}% ]   (Can be Disabled & Customized With Config File)".ljust(75, " "), end="\r")
    else:
      numDupes = 0
      commentTextList = []
      matchedIndexes = []
      for commentDict in authorCommentsList:
        # Adding to use as lower case, because levenshtein is case sensitive. Also, root domain list is ingested as lower case, so necessary to compare
        commentTextList.append(commentDict['commentText'].lower())

      # Count number of comments that are similar to at least one other comment
      if len(commentTextList) > 1:
        for i,x in enumerate(commentTextList):
          # Check length of comment against minimum, but override if a domain is detected
          if len(x) >= minimum_duplicate_length or (len(x) >= 6 and any(f".{domain}" in x for domain in domainList)):
            for j in range(i+1,len(commentTextList)):
              y = commentTextList[j]
              # If Levenshtein distance is 1.0, then only check if comment text is exactly the same
              if levenshtein == 1.0 and x == y: 
                matchedIndexes.append(i)
                matchedIndexes.append(j)
                break
              # If Levenshtein distance is 0, don't check at all, just count number of comments by user
              elif levenshtein == 0.0:
                matchedIndexes.append(i)
                matchedIndexes.append(j)
                break
              elif fuzz.ratio(x,y) / 100 > levenshtein:
                # List the indexes of the matched comments in the list
                matchedIndexes.append(i)
                matchedIndexes.append(j)
                break
          else:
            break
        
        # Only count each comment once by counting number of unique indexes in matchedIndexes
        uniqueMatches = len(set(matchedIndexes))
        if uniqueMatches >= minimum_duplicates:
          numDupes += uniqueMatches
      if numDupes > 0:
        for commentDict in authorCommentsList:
          add_spam(current, config, miscData, commentDict, videoID, matchReason="Duplicate")
      scannedCount +=1
      print(f" Analyzing For Duplicates: [ {scannedCount/authorCount*100:.2f}% ]   (Can be Disabled & Customized With Config File)".ljust(75, " "), end="\r")

  print("".ljust(110, " ")) # Erase line


############################# Check Text Reposts #####################################
def check_reposts(current, config, miscData, allVideoCommentsDict, videoID):
  # Get Lenvenshtein Distance Setting
  if config['fuzzy_stolen_comment_detection'] == True:
    try:
      levenshtein = float(config['levenshtein_distance'])
      if levenshtein < 0 or levenshtein > 1:
        print("\nError: Levenshtein_distance config setting must be between 0 and 1. Defaulting to 0.9")
        input("\nPress Enter to Continue...")
        levenshtein = 0.9
    except ValueError:
      print("\nError: Levenshtein_distance config setting must be a number between 0 and 1. Defaulting to 0.9")
      input("\nPress Enter to Continue...")
      levenshtein = 0.9
    fuzzy = True
  else:
    fuzzy = False

  # Get duplicate count setting
  try:
    minLength = int(config['stolen_minimum_text_length'])
    if minLength < 1:
      minLength = 25
      print("\nError: stolen_minimum_text_length config setting must be greater than 0. Defaulting to 25.")
      input("\nPress Enter to Continue...")
  except ValueError:
    minLength = 25
    print("\nError: stolen_minimum_text_length config setting is invalid. Defaulting to 25.")
    input("\nPress Enter to Continue...")

  flatCommentList = []

  # Calculate number of authors to check, for progress
  scannedCount = 0

  # Create time-sorted list of all comments
  for authorID, authorCommentsList in allVideoCommentsDict.items():
    for commentDict in authorCommentsList:
      if not commentDict['parentAuthorChannelID']:  # Only bother checking top level comments
        flatCommentList.append(commentDict)

  flatCommentList.sort(key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%dT%H:%M:%SZ'))
  totalComments = len(flatCommentList)

  # Run Duplicate Check
  for i,x in enumerate(flatCommentList[1:], start=1): # x is comment dictionary. Enumerate starting with second comment (1:), because nothing came before it. Use start=1 so i-1 refers to correct index in flatCommentList
    scrutinizedText = x['commentText']
    scrutinizedAuthorID = x['authorChannelID']
    if scrutinizedAuthorID == auth.CURRENTUSER.id or scrutinizedAuthorID == miscData.channelOwnerID or scrutinizedAuthorID == miscData.resources['Whitelist']['WhitelistContents']:
      pass
    else:
      for j in range(0,i-1): # Only need to check against comments that came before it, so have index less than current
        olderCommentText = flatCommentList[j]['commentText']
        if len(scrutinizedText) >= minLength and flatCommentList[j]['authorChannelID'] != scrutinizedAuthorID and x['commentID'] not in current.matchedCommentsDict and x['commentID'] not in current.duplicateCommentsDict:
          if (not fuzzy and scrutinizedText == olderCommentText) or (fuzzy and fuzz.ratio(scrutinizedText, olderCommentText) / 100 > levenshtein):
            # List the indexes of the matched comments in the list
            x['originalCommentID'] = flatCommentList[j]['commentID']
            add_spam(current, config, miscData, x, videoID, matchReason="Repost")
            break
    scannedCount += 1
    print(f" Analyzing For Stolen / Reposted Comments: [ {scannedCount/totalComments*100:.2f}% ]   (Can be Disabled & Customized With Config File)".ljust(75, " "), end="\r")

  print("".ljust(110, " ")) # Erase line
    

##########################################################################################
############################## CHECK AGAINST FILTER ######################################
##########################################################################################

# The basic logic that actually checks each comment against filter criteria
def check_against_filter(current, filtersDict, miscData, config, currentCommentDict, videoID, allThreadAuthorNames=None):
  # Retrieve Data from currentCommentDict
  commentID = currentCommentDict['commentID']
  authorChannelName = currentCommentDict['authorChannelName']
  authorChannelID = currentCommentDict['authorChannelID']
  parentAuthorChannelID = currentCommentDict['parentAuthorChannelID']
  commentTextRaw = str(currentCommentDict['commentText']) # Use str() to ensure not pointing to same place in memory
  commentText = str(currentCommentDict['commentText']).replace("\r", "")

  # #Debugging
  # print(f"{F.LIGHTRED_EX}DEBUG MODE{S.R} - If you see this, I forgot to disable it before release, oops. \n Please report here: {F.YELLOW}TJoe.io/bug-report{S.R}")
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
      compiledObfuRegexDict = smartFilter['compiledObfuRegexDict']
      preciseRegexDict = smartFilter['preciseRegexDict']
      numberFilterSet = smartFilter['spammerNumbersSet']
      compiledNumRegex = smartFilter['compiledNumRegex']
      compiledAllNumRegex = smartFilter['compiledAllNumRegex']
      phoneRegexCompiled = smartFilter['phoneRegexCompiled']
      bigNumCheckRegexCompiled = smartFilter['bigNumCheckRegexCompiled']
      minNumbersMatchCount = smartFilter['minNumbersMatchCount']
      bufferChars = compiledRegexDict['bufferChars']
      #usernameBlackCharsSet = smartFilter['usernameBlackCharsSet']
      spamGenEmojiSet = smartFilter['spamGenEmojiSet']
      redAdEmojiSet = smartFilter['redAdEmojiSet']
      yellowAdEmojiSet = smartFilter['yellowAdEmojiSet']
      hrtSet = smartFilter['hrtSet']
      lowAlSet = smartFilter['lowAlSet']
      languages = smartFilter['languages']
      sensitive =  smartFilter['sensitive']
      rootDomainRegex = smartFilter['rootDomainRegex']
      accompanyingLinkSpamDict = smartFilter['accompanyingLinkSpamDict']
      comboDict = smartFilter['comboDict']

      # Spam Lists
      spamListCombinedRegex = smartFilter['spamListCombinedRegex']
      spamThreadsRegex = smartFilter['spamThreadsRegex']

      # if debugSingleComment == True: 
      #   if input("Sensitive True/False: ").lower() == 'true': sensitive = True
      #   else: sensitive = False

      # Check for sensitive smart mode  
      if sensitive:
        rootDomainRegex = smartFilter['sensitiveRootDomainRegex']

      # Functions --------------------------------------------------------------
      def findObf(expression, chars, stringToSearch, findall=True, phone=False):
        # Confusable thinks s and f look similar, have to compensate to avoid false positive
        ignoredConfusablesConverter = {ord('f'):ord('s'),ord('s'):ord('f')}
        if findall:
          result = expression.findall(stringToSearch.lower())
        else:
          result = expression.search(stringToSearch.lower())
        if not result:
          return False
        else:
          for match in result:
            if match != '':
              if not phone or (phone and not bigNumCheckRegexCompiled.search(match)):
                lowerChars = chars.lower()
                # Strips off buffer characters and specified unicode categories
                while match[0] in compiledRegexDict['bufferChars'] or match[-1] in compiledRegexDict['bufferChars']:
                  for bufferChar in compiledRegexDict['bufferChars']:
                    match = match.strip(bufferChar)
                while unicodedata.category(match[0]) in smartFilter['unicodeCategoriesStrip']:
                  match = match[1:]
                while unicodedata.category(match[-1]) in smartFilter['unicodeCategoriesStrip']:
                  match = match[:-1]
                if any(char not in lowerChars for char in match) and any(char not in lowerChars.translate(ignoredConfusablesConverter) for char in match):
                  return True

      def remove_unicode_categories(string):
        return "".join(char for char in string if unicodedata.category(char) not in smartFilter['unicodeCategoriesStrip'])

      def check_if_only_link(string):
        result = re.match(compiledRegexDict['onlyVideoLinkRegex'], string)
        if not result:
          return False
        elif result.group(0) and len(result.group(0)) == len(string):
          return True
        else:
          return False

      def find_accompanying_link_spam(string):
        linkResult = re.search(accompanyingLinkSpamDict['videoLinkRegex'], string)
        if not linkResult:
          return False
        else:
          phrasesList = accompanyingLinkSpamDict['accompanyingLinkSpamPhrasesList']
          notSpecialChars = accompanyingLinkSpamDict['notSpecial']
          nonLinkString = string.replace(linkResult.group(0), '')
          for char in notSpecialChars:
            nonLinkString = nonLinkString.replace(char, '').replace('\n', '')
          if any(phrase.lower().replace(' ', '') == nonLinkString for phrase in phrasesList):
            return True
          else:
            return False

      def multiVarDetect(text, username):
        multiUsernameAllList = comboDict['multiUsernameAllList']
        for checkList in multiUsernameAllList:
          if all(word in username for word in checkList):
            return True

      # ------------------------------------------------------------------------

      # Normalize usernames and text, remove multiple whitespace and invisible chars
      commentText = re.sub(' +', ' ', commentText)
      # https://stackoverflow.com/a/49695605/17312053
      commentText = "".join(k if k in bufferChars else "".join(v) for k,v in itertools.groupby(commentText, lambda c: c))
      commentTextNormalized = remove_unicode_categories(commentText)

      authorChannelName = re.sub(' +', ' ', authorChannelName)
      authorChannelName = remove_unicode_categories(authorChannelName)

      # Processed Variables
      combinedString = authorChannelName + commentText
      combinedStringNormalized = authorChannelName + commentTextNormalized
      combinedSet = utils.make_char_set(combinedString, stripLettersNumbers=True, stripPunctuation=True)
      # UpLow Text Set
      index = commentText.lower().rfind(miscData.channelOwnerName.lower())
      if index != -1:
        processedText = commentText.replace(commentText[index:index+len(miscData.channelOwnerName)], "")
      else:
        processedText = commentText
      upLowTextSet = set(processedText)

      # Run Spam Thread specific check first
      if spamThreadsRegex.search(commentTextNormalized.lower()):
        add_spam(current, config, miscData, currentCommentDict, videoID)

      # Run Checks
      if authorChannelID == parentAuthorChannelID:
        pass
      elif len(compiledAllNumRegex.findall(combinedString)) >= minNumbersMatchCount:
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif sensitive and findObf(phoneRegexCompiled, '0123456789+-() ', combinedString, phone=True):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif not sensitive and compiledRegexDict['doubledSusWords'].search(combinedStringNormalized) and findObf(phoneRegexCompiled, '0123456789+-() ', combinedString, phone=True):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif compiledNumRegex.search(combinedString):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      # Black Tests
        #elif usernameBlackCharsSet.intersection(usernameSet):
        #  add_spam(current, config, miscData, currentCommentDict, videoID)
      elif compiledRegexDict['usernameBlackWords'].search(authorChannelName):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif config['detect_sub_challenge_spam'] and compiledRegexDict['usernameNovidBlackWords'].search(authorChannelName):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif compiledRegexDict['blackAdWords'].search(authorChannelName):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif compiledRegexDict['textBlackWords'].search(commentTextNormalized):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif any(findObf(expressionPair[0], expressionPair[1], commentText) for expressionPair in compiledObfuRegexDict['textObfuBlackWords']):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif preciseRegexDict['textExactBlackWords'].search(commentTextNormalized.lower()):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif preciseRegexDict['textUpLowBlackWords'].search(commentTextNormalized) and not upLowTextSet.intersection(lowAlSet):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif any(findObf(expressionPair[0], expressionPair[1], authorChannelName) for expressionPair in compiledObfuRegexDict['usernameObfuBlackWords']):  
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif spamListCombinedRegex.search(combinedStringNormalized.lower()):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif config['detect_link_spam'] and check_if_only_link(commentTextNormalized.strip()):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif find_accompanying_link_spam(commentTextNormalized.lower()):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif multiVarDetect(commentTextNormalized.lower(), authorChannelName.lower()):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif sensitive and re.search(smartFilter['usernameConfuseRegex'], authorChannelName):
        add_spam(current, config, miscData, currentCommentDict, videoID)
      elif not sensitive and (findObf(smartFilter['usernameConfuseRegex'], miscData.channelOwnerName, authorChannelName) or authorChannelName == miscData.channelOwnerName):
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
        if compiledRegexDict['yellowAdWords'].search(combinedStringNormalized):
          yellowCount += 1

        hrtTest = len(hrtSet.intersection(combinedSet))
        if hrtTest >= 2:
          if not sensitive:
            yellowCount += 1
          else:
            redCount += 1
        elif sensitive and hrtTest >= 1:
          yellowCount += 1

        if yellowAdEmojiSet.intersection(combinedSet):
          yellowCount += 1

        if not sensitive and any(emoji in commentTextNormalized for emoji in spamGenEmojiSet):
          yellowCount += 1

        if not sensitive and any(emoji in authorChannelName for emoji in spamGenEmojiSet):
          redCount += 1

        if commentTextRaw.count('#') >= 5:
          yellowCount += 1

        if commentTextRaw.count('\n') >= 10:
          yellowCount += 1

        if languageCount >= 2:
          yellowCount += 1

        if rootDomainRegex.search(combinedStringNormalized.lower()):
          yellowCount += 1

        # Red Tests
        #if any(foundObfuscated(re.findall(expression[1], combinedString), expression[0]) for expression in compiledRegexDict['redAdWords']):
        if compiledRegexDict['redAdWords'].search(combinedStringNormalized):
          redCount += 1

        if preciseRegexDict['exactRedAdWords'].search(combinedStringNormalized.lower()):
          redCount += 1

        if redAdEmojiSet.intersection(combinedSet):
          redCount += 1

        if sensitive and spamGenEmojiSet.intersection(combinedSet):
          redCount += 1

        if compiledRegexDict['usernameRedWords'].search(authorChannelName.lower()):
          redCount += 1

        # Calculate Score
        if yellowCount >= 3:
          add_spam(current, config, miscData, currentCommentDict, videoID)
        elif redCount >= 2:
          add_spam(current, config, miscData, currentCommentDict, videoID)
        elif redCount >= 1 and yellowCount >= 2:
          add_spam(current, config, miscData, currentCommentDict, videoID)
        elif sensitive and redCount >= 1:
          add_spam(current, config, miscData, currentCommentDict, videoID)
  else:
    pass


##########################################################################################
################################ DELETE COMMENTS #########################################
########################################################################################## 

# Takes in list of comment IDs to delete, breaks them into 50-comment chunks, and deletes them in groups
def delete_found_comments(commentsList, banChoice, deletionMode, recoveryMode=False, skipCheck = False):
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

  failedComments = []
  # Local Functions 
  def setStatus(commentIDs, failedComments): #Does the actual deletion
    if deletionMode == "reportSpam":
      result = auth.YOUTUBE.comments().markAsSpam(id=commentIDs).execute()
      if len(result) > 0:
        print("\nSomething may have gone wrong when reporting the comments.")
        failedComments += commentIDs
    elif deletionMode == "heldForReview" or deletionMode == "rejected" or deletionMode == "published":
      try:
        response = auth.YOUTUBE.comments().setModerationStatus(id=commentIDs, moderationStatus=deletionMode, banAuthor=banChoice).execute()
        if len(response) > 0:
          failedComments += commentIDs
      except HttpError:
        print("\nSomething has gone wrong when removing some comments...")
        failedComments += commentIDs

    else:
      print("Invalid deletion mode. This is definitely a bug, please report it here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
      print("Deletion Mode Is: " + deletionMode)
      input("Press Enter to Exit...")
      sys.exit()
    return failedComments


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
      failedComments = setStatus(commentsList[i*50:i*50+50], failedComments)
      deletedCounter += 50
      print_progress(deletedCounter, total, recoveryMode)
    if remainder > 0:
      failedComments = setStatus(commentsList[numDivisions*50:total], failedComments) # Handles any leftover comments range after last full chunk
      deletedCounter += remainder
      print_progress(deletedCounter, total, recoveryMode)
  else:
      failedComments = setStatus(commentsList, failedComments)
      print_progress(deletedCounter, total, recoveryMode)
  if deletionMode == "reportSpam":
    print(f"{F.YELLOW}Comments Reported!{S.R} If no error messages were displayed, then everything was successful.")
    return failedComments
  elif recoveryMode == False and skipCheck == False:
    print("Comments " + actionPast + "! Will now verify each is gone.                          \n")
  elif recoveryMode == False and skipCheck == True:
    print("Comments " + actionPast + "!                                                   \n")
  elif recoveryMode == True:
    print("Comments Recovered! Will now verify each is back.                          \n")

  return failedComments

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
    print(" Preparing to check deletion status...", end="\r")
    time.sleep(1)
    print("                                                      ")
    print("    (Note: You can disable deletion success checking in the config file to save time and API quota)\n")
    for commentID in commentList:
      try:
        results = auth.YOUTUBE.comments().list(
          part="snippet",
          id=commentID,  
          #maxResults=1, #Cannot be used with 'id' parameter
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
        pass
      except HttpError as hx:
        try:
          reason = str(hx.error_details[0]["reason"])
        except:
          reason = "Not Given"
        if type(commentInput) == dict:
          print(f"HttpError '{reason}' While Deleting Comment: " + str(commentID) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(commentInput[commentID]['videoID']) + "&lc=" + str(commentID))
        elif type(commentInput) == list:
          print(f"HttpError '{reason}' While Deleting Comment: " + str(commentID))
        i += 1
        pass
      except Exception:
        if type(commentInput) == dict:
          print("Unhandled Exception While Deleting Comment: " + str(commentID) + " |  Check Here: " + "https://www.youtube.com/watch?v=" + str(commentInput[commentID]['videoID']) + "&lc=" + str(commentID))
        elif type(commentInput) == list:
          print("Unhandled Exception While Deleting Comment: " + str(commentID))
        i += 1
        pass

    if i == 0:
      print("\n\nSuccess: All comments should be gone.")
    elif i > 0:
      print("\n\nWarning: " + str(i) + " comments may remain. Check links above or try running the program again. An error log file has been created: 'Deletion_Error_Log.txt'")
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
        #maxResults=1, # Cannot be used with 'id' parameter
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
    print("Use the links to the comments from the log file you used to verify if they are back or not.")

  input("\nRecovery process finished. Press Enter to return to main menu...")
  return True

# Removes comments by user-selected authors from list of comments to delete
def exclude_authors(current, config, miscData, excludedCommentsDict, authorsToExcludeSet, commentIDExcludeSet, displayString, inputtedString, logInfo=None, only=False):
  plaintextFormattedExcludes = ""
  rtfFormattedExcludes = ""

  valid = False
  while valid == False:
    if "exclude" in inputtedString.lower() or "only" in inputtedString.lower():
      try:
        if "exclude" in inputtedString.lower(): # Account for if user is trying again
          isolateExpression = r"(?<=exclude ).*" # Matches everything after 'exclude'
          result = str(re.search(isolateExpression, inputtedString.lower()).group(0))
        elif "only" in inputtedString.lower():
          isolateExpression = r"(?<=only ).*" # Matches everything after 'exclude'
          result = str(re.search(isolateExpression, inputtedString.lower()).group(0))
      # User didn't enter any numbers or they're not right
      except AttributeError:
        result = "ThisStringCausesErrorNext"
    else:
      #Take new input from further down
      result = inputtedString

    result = result.replace(" ", "")
    validInputExpression = r'^[0-9,-]+$' # Ensures only digits, commas, and dashes are used
    if re.match(validInputExpression, result) == None:
      print(f"\n{F.LIGHTRED_EX}Invalid input!{S.R} Must be a comma separated list of numbers and/or range of numbers. Please try again.")
      if only == False:
        inputtedString = input("\nEnter the list of authors to exclude from deletion: ")
      elif only == True:
        inputtedString = input("\nEnter the list of only authors to delete: ")
      
    else:
      result = result.strip(',') # Remove leading/trailing comma
      result = utils.expand_ranges(result) # Expands ranges of numbers into a list of numbers
      chosenSampleIndexes = result.split(",")
      valid = True
      for num in chosenSampleIndexes: # Check if any numbers outside max range
        if int(num) > len(current.matchSamplesDict) or int(num)<1:
          print(f"\n{F.LIGHTRED_EX}Invalid input!{S.R} Number is outside the range of samples: {num} --  Please try again.")
          valid = False
          break
      if valid == False:
        if only == False:
          inputtedString = input("\nEnter the comma separated list of numbers and/or ranges to exclude: ")
        elif only == True:
          inputtedString = input("\nEnter the comma separated list of numbers and/or ranges to delete: ")

  # Go through all the sample numbers, check if they are on the list given by user
  for authorID, info in current.matchSamplesDict.items():
    if only == False:
      if str(info['index']) in chosenSampleIndexes:
        authorsToExcludeSet.add(authorID)
    elif only == True:
      if str(info['index']) not in chosenSampleIndexes:
        authorsToExcludeSet.add(authorID)

  # Get comment IDs to be excluded
  for comment, metadata in current.matchedCommentsDict.items():
    if metadata['authorID'] in authorsToExcludeSet:
      commentIDExcludeSet.add(comment)
  for comment, metadata in current.duplicateCommentsDict.items():
    if metadata['authorID'] in authorsToExcludeSet:
      commentIDExcludeSet.add(comment)
  for comment, metadata in current.otherCommentsByMatchedAuthorsDict.items():
    if metadata['authorID'] in authorsToExcludeSet:
      commentIDExcludeSet.add(comment)
  for comment, metadata in current.spamThreadsDict.items():
    if metadata['authorID'] in authorsToExcludeSet:
      commentIDExcludeSet.add(comment)
  for comment, metadata in current.repostedCommentsDict.items():
    if metadata['authorID'] in authorsToExcludeSet:
      commentIDExcludeSet.add(comment)

  # Remove all comments by selected authors from dictionary of comments
  for comment in commentIDExcludeSet:
    if comment in current.matchedCommentsDict.keys():
      excludedCommentsDict[comment] = current.matchedCommentsDict.pop(comment)
    if comment in current.duplicateCommentsDict.keys():
      excludedCommentsDict[comment] = current.duplicateCommentsDict.pop(comment)
    if comment in current.otherCommentsByMatchedAuthorsDict.keys():
      excludedCommentsDict[comment] = current.otherCommentsByMatchedAuthorsDict.pop(comment)
    if comment in current.spamThreadsDict.keys():
      excludedCommentsDict[comment] = current.spamThreadsDict.pop(comment)
    if comment in current.repostedCommentsDict.keys():
      excludedCommentsDict[comment] = current.repostedCommentsDict.pop(comment)  

  # Create strings that can be used in log files
  
  rtfFormattedExcludes += f"\\line \n Comments Excluded From Deletion: \\line \n"
  rtfFormattedExcludes += f"(Values = Comment ID | Author ID | Author Name | Comment Text) \\line \n"
  plaintextFormattedExcludes += f"\nComments Excluded From Deletion:\n"
  plaintextFormattedExcludes += f"(Values = Comment ID | Author ID | Author Name | Comment Text)\n"
  for commentID, meta in excludedCommentsDict.items():
    sanitizedText = str(excludedCommentsDict[commentID]['text']).replace("\n", " ").replace("\r", " ")
    rtfFormattedExcludes += f"{str(commentID)}  |  {str(excludedCommentsDict[commentID]['authorID'])}  |  {str(excludedCommentsDict[commentID]['authorName'])}  |   {sanitizedText} \\line \n"
  for commentID, meta in excludedCommentsDict.items():
    sanitizedText = str(excludedCommentsDict[commentID]['text']).replace("\n", " ").replace("\r", " ")
    plaintextFormattedExcludes += f"{str(commentID)}  |  {str(excludedCommentsDict[commentID]['authorID'])}  |  {str(excludedCommentsDict[commentID]['authorName'])}  |   {sanitizedText} \n"

  # Verify removal
  for comment in current.matchedCommentsDict.keys():
    if comment in commentIDExcludeSet:
      print(f"{F.LIGHTRED_EX}FATAL ERROR{S.R}: Something went wrong while trying to exclude comments. No comments have been deleted.")
      print(f"You should {F.YELLOW}DEFINITELY{S.R} report this bug here: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
      print("Provide the error code: X-1")
      input("Press Enter to Exit...")
      sys.exit()

  # Get author names and IDs from dictionary, and display them
  for author in authorsToExcludeSet:
    displayString += f"    User ID: {author}   |   User Name: {current.matchSamplesDict[author]['authorName']}\n"


  print(f"\n{F.CYAN}All {len(excludedCommentsDict)} comments{S.R} from the {F.CYAN}following users{S.R} are now {F.LIGHTGREEN_EX}excluded{S.R} from deletion:")
  print(displayString)

  if config['whitelist_excluded'] == 'ask':
    print(f"\nAdd these {F.LIGHTGREEN_EX}excluded{S.R} users to the {F.LIGHTGREEN_EX}whitelist{S.R} for future scans?")
    addWhitelist = choice("Whitelist Users?")
  elif config['whitelist_excluded'] == True:
    addWhitelist = True
  elif config['whitelist_excluded'] == False:
    addWhitelist = False

  if addWhitelist == True:
    with open(miscData.resources['Whitelist']['PathWithName'], "a+", encoding="utf-8") as f:
      f.seek(0)
      currentWhitelist = f.read()
      for author in authorsToExcludeSet:
        if not author in currentWhitelist:
          f.write(f"\n# [Excluded]  Channel Name: {current.matchSamplesDict[author]['authorName']}  |  Channel ID: " + "\n")
          f.write(f"{author}\n")
  
  input("\nPress Enter to decide what to do with the rest...")
  
  return current, excludedCommentsDict, authorsToExcludeSet, commentIDExcludeSet, rtfFormattedExcludes, plaintextFormattedExcludes # May use excludedCommentsDict later for printing them to log file


################################# Get Most Recent Videos #####################################
# Returns a list of lists
def get_recent_videos(current, channel_id, numVideosTotal):
  def get_block_of_videos(nextPageToken, j, k, numVideosBlock = 50):
    #fetch the channel resource
    channel = auth.YOUTUBE.channels().list(
      part="contentDetails",
      id=channel_id).execute()
    
    #get the "uploads" playlist
    uploadplaylistId = channel['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    #fetch videos in the playlist
    result = auth.YOUTUBE.playlistItems().list(
      part="snippet",
      playlistId=uploadplaylistId,
      pageToken=nextPageToken,
      maxResults=numVideosBlock,
      ).execute()

    for item in result['items']:
      videoID = str(item['snippet']['resourceId']['videoId'])
      videoTitle = str(item['snippet']['title']).replace("&quot;", "\"").replace("&#39;", "'")
      commentCount = validation.validate_video_id(videoID, pass_exception = True)[3]
      #Skips over video if comment count is zero, or comments disabled / is live stream
      if str(commentCount) == '0' or commentCount == None:
        if str(commentCount) == '0':
          print(f"{B.YELLOW}{F.BLACK} Skipping {S.R} {F.LIGHTRED_EX}Video with no comments:{S.R} " + str(item['snippet']['title']))
        if commentCount == None:
          print(f"{B.YELLOW}{F.BLACK} Skipping {S.R} {F.LIGHTRED_EX}Invalid Video, or video may have comments disabled:{S.R} " + str(item['snippet']['title']))
        k+=1
        continue
      
      if videoID not in current.vidTitleDict:
        current.vidTitleDict[videoID] = videoTitle

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
      if remainingVideos <= 50:
        nextPageToken, j, k, abortCheck = get_block_of_videos(nextPageToken, j, k, numVideosBlock = remainingVideos)
      else:
        nextPageToken, j, k, abortCheck = get_block_of_videos(nextPageToken, j, k, numVideosBlock = 50)
      if str(nextPageToken[0]) == "MainMenu":
        return "MainMenu"
  print("                                          ")
  return recentVideos

##################################### PRINT STATS ##########################################

# Prints Scanning Statistics, can be version that overwrites itself or one that finalizes and moves to next line
def print_count_stats(current, miscData, videosToScan, final):
  # Use videosToScan (list of dictionaries) to retrieve total number of comments
  if videosToScan and miscData.totalCommentCount > 0:
    totalComments = miscData.totalCommentCount
    totalScanned = current.scannedRepliesCount + current.scannedCommentsCount
    percent = ((totalScanned / totalComments) * 100)
    progress = f"Total: [{str(totalScanned)}/{str(totalComments)}] ({percent:.0f}%) ".ljust(27, " ") + "|" #Formats percentage to 0 decimal places
  else:
    progress = ""
  
  comScanned = str(current.scannedCommentsCount)
  repScanned = str(current.scannedRepliesCount)
  matchCount = str(len(current.matchedCommentsDict) + len(current.spamThreadsDict))

  if final == True:
    print(f" {progress} Comments Scanned: {F.YELLOW}{comScanned}{S.R} | Replies Scanned: {F.YELLOW}{repScanned}{S.R} | Matches Found So Far: {F.LIGHTRED_EX}{matchCount}{S.R}\n")
  else:
    print(f" {progress} Comments Scanned: {F.YELLOW}{comScanned}{S.R} | Replies Scanned: {F.YELLOW}{repScanned}{S.R} | Matches Found So Far: {F.LIGHTRED_EX}{matchCount}{S.R}", end = "\r")
  
  return None
