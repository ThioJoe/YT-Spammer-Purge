# Contributing

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.


## Contributing Guidelines

- If you'd like to make a pull request to contribute, please keep it simple. If you use some higher level techniques I don't understand, I'm not going to approve it because I won't be able to maintain it.

- Please don't make a pull request with a bunch of changes in syntax just for the sake of 'best practices' (ex: changing "if blah == False" to "if not blah"). Unless something makes a difference to performance frankly I don't care.

- Avoid adding new non-standard libraries if at all possible. If you have an idea that would require one, please suggest it as an issue first instead of going through all the work and submitting a pull request.

- Don't modify SpamAccountsList.txt, SpamDomainsList.txt & SpamThreadsList.txt in the assets folder. There is a dedicated repo for these, for which you can submit additions via issues - https://github.com/ThioJoe/YT-Spam-Domains-List

- MAKE SURE IT RUNS

## Environment setup

Nothing easier!

Fork and clone the repository, then:

```bash
cd yt-spam-purge
make setup
```

!!! note
    If it fails for some reason,
    you'll need to install
    [Poetry](https://github.com/python-poetry/poetry)
    manually.

    You can install it with:

    ```bash
    python3 -m pip install --user pipx
    pipx install poetry
    ```

    Now you can try running `make setup` again,
    or simply `poetry install`.

You now have the dependencies installed.

You can run the application with `poetry run ytsp [ARGS...]`.

Run `make help` to see all the available actions!

## Tasks

This project uses [duty](https://github.com/pawamoy/duty) to run tasks.
A Makefile is also provided. The Makefile will try to run certain tasks
on multiple Python versions. If for some reason you don't want to run the task
on multiple Python versions, you can do one of the following:

1. `export PYTHON_VERSIONS= `: this will run the task
   with only the current Python version
2. run the task directly with `poetry run duty TASK`,
   or `duty TASK` if the environment was already activated
   through `poetry shell`

The Makefile detects if the Poetry environment is activated,
so `make` will work the same with the virtualenv activated or not.

## Development

As usual:

1. create a new branch: `git checkout -b feature-or-bugfix-name`
1. edit the code and/or the documentation

If you updated the documentation or the project dependencies:

1. run `make docs-regen`
1. run `make docs-serve`,
   go to http://localhost:8000 and check that everything looks good

**Before committing:**

1. run `make format` to auto-format the code
1. run `make check` to check everything (fix any warning)
1. run `make test` to run the tests (fix any issue)
1. follow our [commit message convention](#commit-message-convention)

If you are unsure about how to fix or ignore a warning,
just let the continuous integration fail,
and we will help you during review.

Don't bother updating the changelog, we will take care of this.

## Commit message convention

Commits messages must follow the
[Angular style](https://gist.github.com/stephenparish/9941e89d80e2bc58a153#format-of-the-commit-message):

```
<type>[(scope)]: Subject

[Body]
```

Scope and body are optional. Type can be:

- `build`: About packaging, building wheels, etc.
- `chore`: About packaging or repo/files management.
- `ci`: About Continuous Integration.
- `docs`: About documentation.
- `feat`: New feature.
- `fix`: Bug fix.
- `perf`: About performance.
- `refactor`: Changes which are not features nor bug fixes.
- `style`: A change in code style/format.
- `tests`: About tests.

**Subject (and body) must be valid Markdown.**
If you write a body, please add issues references at the end:

```
Body.

References: #10, #11.
Fixes #15.
```

## Pull requests guidelines

Link to any related issue in the Pull Request message.

During review, we recommend using fixups:

```bash
# SHA is the SHA of the commit you want to fix
git commit --fixup=SHA
```

Once all the changes are approved, you can squash your commits:

```bash
git rebase -i --autosquash master
```

And force-push:

```bash
git push -f
```

If this seems all too complicated, you can push or force-push each new commit,
and we will squash them ourselves if needed, before merging.

