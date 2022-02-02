# yt-spam-purge

[![ci](https://github.com/dekoza/yt-spam-purge/workflows/ci/badge.svg)](https://github.com/dekoza/yt-spam-purge/actions?query=workflow%3Aci)
[![documentation](https://img.shields.io/badge/docs-mkdocs%20material-blue.svg?style=flat)](https://dekoza.github.io/yt-spam-purge/)
[![pypi version](https://img.shields.io/pypi/v/yt-spam-purge.svg)](https://pypi.org/project/yt-spam-purge/)
[![gitter](https://badges.gitter.im/join%20chat.svg)](https://gitter.im/yt-spam-purge/community)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Easily scan for and delete scam comments on your YouTube channel.

## Requirements

yt-spam-purge requires Python 3.10 or above.

<details>
<summary>To install Python 3.10, I recommend using <a href="https://github.com/pyenv/pyenv"><code>pyenv</code></a>.</summary>

```bash
# install pyenv
git clone https://github.com/pyenv/pyenv ~/.pyenv

# setup pyenv (you should also put these three lines in .bashrc or similar)
export PATH="${HOME}/.pyenv/bin:${PATH}"
export PYENV_ROOT="${HOME}/.pyenv"
eval "$(pyenv init -)"

# install Python 3.10
pyenv install 3.10.0

# make it available globally
pyenv global system 3.10.0
```
</details>

## Installation

With `pip`:
```bash
python3.10 -m pip install yt-spam-purge
```

With [`pipx`](https://github.com/pipxproject/pipx):
```bash
python3.10 -m pip install --user pipx

pipx install --python python3.10 yt-spam-purge
```
