from dataclasses import dataclass

from colorama import init
from colorama.ansi import AnsiBack, AnsiFore, AnsiStyle


class Back(AnsiBack):
    R: str = AnsiBack.RESET


class Fore(AnsiFore):
    R: str = AnsiFore.RESET


class Style(AnsiStyle):
    R: str = AnsiStyle.RESET_ALL


S = Style()
F = Fore()
B = Back()


@dataclass
class ScanInstance:
    matchedCommentsDict: dict[str, str]  # Comments flagged by the filter
    duplicateCommentsDict: dict[str, str]  # Comments flagged as duplicates
    repostedCommentsDict: dict[str, str]  # Comments stolen from other users
    otherCommentsByMatchedAuthorsDict: dict[str, str]  # Comments not matched, but are by a matched author
    scannedThingsList: list[str]  # List of posts or videos that were scanned
    spamThreadsDict: dict[str, str]  # Comments flagged as parent of spam threads
    allScannedCommentsDict: dict[str, str]  # All comments scanned for this instance
    vidIdDict: dict[str, str]  # Contains the video ID on which each comment is found
    vidTitleDict: dict[str, str]  # Contains the titles of each video ID
    matchSamplesDict: dict[str, dict[str, str | None]]  # Contains sample info for every flagged comment of all types
    authorMatchCountDict: dict[str, str]  # The number of flagged comments per author
    scannedRepliesCount: int  # The current number of replies scanned so far
    scannedCommentsCount: int  # The current number of comments scanned so far
    logTime: str  # The time at which the scan was started
    logFileName: str | None  # Contains a string of the current date/time to be used as a log file name or anything else
    errorOccurred: bool  # True if an error occurred during the scan


# Global Hardcoded Constants
RESOURCES_FOLDER_NAME = "SpamPurge_Resources"

__all__ = [
    "F",
    "B",
    "S",
    "init",
    "RESOURCES_FOLDER_NAME",
    "ScanInstance",
]
