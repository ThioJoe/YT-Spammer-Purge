# Contributing

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

## Contributing Guidelines

- If you'd like to make a pull request to contribute, please ***keep it simple***. If you use some higher level techniques I don't understand, I'm not going to approve it because I won't be able to maintain it.

- *Please* ensure all code has been formatted by [Black](https://pypi.org/project/black/) ([Usage Guide](https://black.readthedocs.io/en/stable/getting_started.html#basic-usage)). This helps to maintain code readability and keep a consistent style across all files. This is optional for you to do.

- **Avoid** adding new non-standard libraries if ***at all possible***. If you have an idea that would require one, please suggest it as an issue first instead of going through all the work and submitting a pull request.

- ***DO NOT*** modify SpamAccountsList.txt, SpamDomainsList.txt & SpamThreadsList.txt in the assets folder. There is a dedicated repo for these, for which you can submit additions via issues - https://github.com/ThioJoe/YT-Spam-Domains-List

- MAKE SURE IT RUNS


## Setting up your Environment

- Fork the repository [(How?)](https://docs.github.com/en/get-started/quickstart/fork-a-repo)
- Download your fork to your computer, either by:
- - Clone your repository using the `git` CLI. [(How?)](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
or by
- - Download as a ZIP and extract [(How?)](https://www.cloudsavvyit.com/p/uploads/2021/11/e8bb2301.png)
- Optional: Setup a virtual environment [(How?)](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment)

From here, you can either install dependencies with `pip`, or `poetry` [(How do I install poetry?)](https://python-poetry.org/docs/#installation)
- With `pip`:
- Download dependencies: `pip3 install -r requirements.txt`
- Optional: Download devlopment utilities
- - Black: 
- - - Run `pip3 install black`
- - - Use `python3 -m black` to run [(How do I use Black?)](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html)
- - Pre-Commit:
- - - Run `pip3 install pre-commit`
- - - Run `python3 -m pre-commit install`
- With `poetry`
- - Run `poetry install`
- - To install Pre-Commit, Run `poetry run pre-commit install`
