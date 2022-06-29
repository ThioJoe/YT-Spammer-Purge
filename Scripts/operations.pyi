from Scripts.shared_imports import *
import typing as T
from typing import Any, Union

def get_comments(
    current,
    filtersDict,
    miscData,
    config,
    allVideoCommentsDict,
    scanVideoID: Union[Any, None] = ...,
    nextPageToken: Union[Any, None] = ...,
    videosToScan: Union[Any, None] = ...,
): ...
def get_replies(
    current,
    filtersDict,
    miscData,
    config,
    parent_id,
    videoID,
    parentAuthorChannelID,
    videosToScan,
    allVideoCommentsDict,
    parentCommentDict: Union[Any, None] = ...,
    repliesList: Union[Any, None] = ...,
): ...
def check_spam_threads(
    current, filtersDict, miscData, config, parentCommentDict, threadDict
) -> None: ...
def make_community_thread_dict(commentID, allCommunityCommentsDict) -> None: ...
def add_spam(
    current, config, miscData, currentCommentDict, videoID, matchReason: str = ...
) -> None: ...
def get_all_author_comments(current, config, miscData, allCommentsDict) -> None: ...
def check_duplicates(
    current, config, miscData, allVideoCommentsDict, videoID
) -> None: ...
def check_against_filter(
    current,
    filtersDict,
    miscData,
    config,
    currentCommentDict,
    videoID,
    allThreadAuthorNames: Union[Any, None] = ...,
): ...
def delete_found_comments(
    commentsList,
    banChoice,
    deletionMode,
    recoveryMode: bool = ...,
    skipCheck: bool = ...,
): ...

class CommentFoundError(Exception): ...

def check_deleted_comments(commentInput) -> None: ...

class CommentNotFoundError(Exception): ...

def check_recovered_comments(commentsList) -> None: ...
def exclude_authors(
    current: T.Any,
    config: T.Dict[str, T.Any],
    miscData: T.Any,
    excludedCommentsDict: T.Dict[str, T.Any],
    authorsToExcludeSet: T.Set[T.Any],
    commentIDExcludeSet: T.Set[T.Any],
    displayString: str,
    inputtedString: str,
    logInfo: T.Optional[T.Dict[str, T.Any]] = ...,
    only: bool = ...,
) -> T.Tuple[T.Any, T.Dict[str, T.Any], T.Set[T.Any], T.Set[T.Any]]: ...
def get_recent_videos(channel_id, numVideosTotal) -> None: ...
def print_count_stats(current, miscData, videosToScan, final) -> None: ...
