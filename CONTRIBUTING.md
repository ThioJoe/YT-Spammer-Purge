## Contributing Guidelines

- If you'd like to make a pull request to contribute, please keep it simple. If you use some higher level techniques I don't understand, I'm not going to approve it because I won't be able to maintain it.

- Please ensure all code has been formatted by [Black](https://pypi.org/project/black/) ([Usage Guide](https://black.readthedocs.io/en/stable/getting_started.html#basic-usage)). This helps to maintain code readability and keep a consistent style across all files.

- Please don't make a pull request with a bunch of changes in syntax just for the sake of 'best practices' (ex: changing "if blah == False" to "if not blah"). Unless something makes a difference to performance frankly I don't care.

- Avoid adding new non-standard libraries if at all possible. If you have an idea that would require one, please suggest it as an issue first instead of going through all the work and submitting a pull request.

- Don't modify SpamAccountsList.txt, SpamDomainsList.txt & SpamThreadsList.txt in the assets folder. There is a dedicated repo for these, for which you can submit additions via issues - https://github.com/ThioJoe/YT-Spam-Domains-List

- MAKE SURE IT RUNS
