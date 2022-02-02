"""Development tasks."""

import inspect
import os
import re
import sys
from pathlib import Path
from shutil import which
from typing import List, Optional, Pattern

import httpx
from duty import duty
from git_changelog.build import Changelog, Version
from jinja2.sandbox import SandboxedEnvironment

PY_SRC_PATHS = (Path(_) for _ in ("src", "tests", "duties.py", "docs/macros.py"))
PY_SRC_LIST = tuple(str(_) for _ in PY_SRC_PATHS)
PY_SRC = " ".join(PY_SRC_LIST)
TESTING = os.environ.get("TESTING", "0") in {"1", "true"}
CI = os.environ.get("CI", "0") in {"1", "true", "yes", ""}
WINDOWS = os.name == "nt"
PTY = not WINDOWS and not CI


def latest(lines: List[str], regex: Pattern) -> Optional[str]:
    """
    Return the last released version.

    Arguments:
        lines: Lines of the changelog file.
        regex: A compiled regex to find version numbers.

    Returns:
        The last version.
    """
    for line in lines:
        match = regex.search(line)
        if match:
            return match.groupdict()["version"]
    return None


def unreleased(versions: List[Version], last_release: str) -> List[Version]:
    """
    Return the most recent versions down to latest release.

    Arguments:
        versions: All the versions (released and unreleased).
        last_release: The latest release.

    Returns:
        A list of versions.
    """
    for index, version in enumerate(versions):
        if version.tag == last_release:
            return versions[:index]
    return versions


def read_changelog(filepath: str) -> List[str]:
    """
    Read the changelog file.

    Arguments:
        filepath: The path to the changelog file.

    Returns:
        The changelog lines.
    """
    with open(filepath, "r") as changelog_file:
        return changelog_file.read().splitlines()


def write_changelog(filepath: str, lines: List[str]) -> None:
    """
    Write the changelog file.

    Arguments:
        filepath: The path to the changelog file.
        lines: The lines to write to the file.
    """
    with open(filepath, "w") as changelog_file:
        changelog_file.write("\n".join(lines).rstrip("\n") + "\n")


def update_changelog(
    inplace_file: str,
    marker: str,
    version_regex: str,
    template_url: str,
    commit_style: str,
) -> None:
    """
    Update the given changelog file in place.

    Arguments:
        inplace_file: The file to update in-place.
        marker: The line after which to insert new contents.
        version_regex: A regular expression to find currently documented versions in the file.
        template_url: The URL to the Jinja template used to render contents.
        commit_style: The style of commit messages to parse.
    """
    env = SandboxedEnvironment(autoescape=False)
    template = env.from_string(httpx.get(template_url).text)
    changelog = Changelog(".", style=commit_style)

    if len(changelog.versions_list) == 1:
        last_version = changelog.versions_list[0]
        if last_version.planned_tag is None:
            planned_tag = "0.1.0"
            last_version.tag = planned_tag
            last_version.url += planned_tag
            last_version.compare_url = last_version.compare_url.replace("HEAD", planned_tag)

    lines = read_changelog(inplace_file)
    last_released = latest(lines, re.compile(version_regex))
    if last_released:
        changelog.versions_list = unreleased(changelog.versions_list, last_released)
    rendered = template.render(changelog=changelog, inplace=True)
    lines[lines.index(marker)] = rendered
    write_changelog(inplace_file, lines)


@duty
def changelog(ctx):
    """
    Update the changelog in-place with latest commits.

    Arguments:
        ctx: The context instance (passed automatically).
    """
    ctx.run(
        update_changelog,
        kwargs={
            "inplace_file": "CHANGELOG.md",
            "marker": "<!-- insertion marker -->",
            "version_regex": r"^## \[v?(?P<version>[^\]]+)",
            "template_url": "https://raw.githubusercontent.com/pawamoy/jinja-templates/master/keepachangelog.md",
            "commit_style": "angular",
        },
        title="Updating changelog",
        pty=PTY,
    )


@duty(pre=["check_code_quality", "check_types", "check_docs", "check_dependencies"])
def check(ctx):
    """
    Check it all!

    Arguments:
        ctx: The context instance (passed automatically).
    """


@duty
def check_code_quality(ctx, files=PY_SRC):
    """
    Check the code quality.

    Arguments:
        ctx: The context instance (passed automatically).
        files: The files to check.
    """
    ctx.run(f"flake8 --config=config/flake8.ini {files}", title="Checking code quality", pty=PTY)


@duty
def check_dependencies(ctx):
    """
    Check for vulnerabilities in dependencies.

    Arguments:
        ctx: The context instance (passed automatically).
    """
    nofail = False
    safety = which("safety")
    if not safety:
        pipx = which("pipx")
        if pipx:
            safety = f"{pipx} run safety"
        else:

            def safety_not_available():  # noqa: WPS430
                print(
                    inspect.cleandoc(  # noqa: WPS462
                        """
                        Please install safety or pipx to run this task:

                        pip install --user safety
                        # or
                        pip install --user pipx
                        # and potentially
                        pipx install safety

                        See https://github.com/advisories/GHSA-7q25-qrjw-6fg2
                        """
                    )  # noqa: WPS355
                )
                return 1

            ctx.run(safety_not_available, title="Checking dependencies", nofail=True)
            return
    ctx.run(
        f"poetry export -f requirements.txt --without-hashes | {safety} check --stdin --full-report",
        title="Checking dependencies",
        pty=PTY,
        nofail=nofail,
    )


@duty
def check_docs(ctx):
    """
    Check if the documentation builds correctly.

    Arguments:
        ctx: The context instance (passed automatically).
    """
    Path("build/coverage").mkdir(parents=True, exist_ok=True)
    Path("build/coverage/index.html").touch(exist_ok=True)
    ctx.run("mkdocs build -s", title="Building documentation", pty=PTY)


@duty
def check_types(ctx):
    """
    Check that the code is correctly typed.

    Arguments:
        ctx: The context instance (passed automatically).
    """
    ctx.run(f"mypy --config-file config/mypy.ini {PY_SRC}", title="Type-checking", pty=PTY)


@duty(silent=True)
def clean(ctx):
    """
    Delete temporary files.

    Arguments:
        ctx: The context instance (passed automatically).
    """
    ctx.run("rm -rf .coverage*")
    ctx.run("rm -rf .mypy_cache")
    ctx.run("rm -rf .pytest_cache")
    ctx.run("rm -rf tests/.pytest_cache")
    ctx.run("rm -rf build")
    ctx.run("rm -rf dist")
    ctx.run("rm -rf pip-wheel-metadata")
    ctx.run("rm -rf site")
    ctx.run("find . -type d -name __pycache__ | xargs rm -rf")
    ctx.run("find . -name '*.rej' -delete")


@duty
def docs(ctx):
    """
    Build the documentation locally.

    Arguments:
        ctx: The context instance (passed automatically).
    """
    ctx.run("mkdocs build", title="Building documentation")


@duty
def docs_serve(ctx, host="127.0.0.1", port=8000):
    """
    Serve the documentation (localhost:8000).

    Arguments:
        ctx: The context instance (passed automatically).
        host: The host to serve the docs from.
        port: The port to serve the docs on.
    """
    ctx.run(f"mkdocs serve -a {host}:{port}", title="Serving documentation", capture=False)


@duty
def docs_deploy(ctx):
    """
    Deploy the documentation on GitHub pages.

    Arguments:
        ctx: The context instance (passed automatically).
    """
    ctx.run("mkdocs gh-deploy", title="Deploying documentation")


@duty
def format(ctx):
    """
    Run formatting tools on the code.

    Arguments:
        ctx: The context instance (passed automatically).
    """
    ctx.run(
        f"autoflake -ir --exclude tests/fixtures --remove-all-unused-imports {PY_SRC}",
        title="Removing unused imports",
        pty=PTY,
    )
    ctx.run(f"isort {PY_SRC}", title="Ordering imports", pty=PTY)
    ctx.run(f"black {PY_SRC}", title="Formatting code", pty=PTY)


@duty
def release(ctx, version):
    """
    Release a new Python package.

    Arguments:
        ctx: The context instance (passed automatically).
        version: The new version number to use.
    """
    ctx.run(f"poetry version {version}", title=f"Bumping version in pyproject.toml to {version}", pty=PTY)
    ctx.run("git add pyproject.toml CHANGELOG.md", title="Staging files", pty=PTY)
    ctx.run(["git", "commit", "-m", f"chore: Prepare release {version}"], title="Committing changes", pty=PTY)
    ctx.run(f"git tag {version}", title="Tagging commit", pty=PTY)
    if not TESTING:
        ctx.run("git push", title="Pushing commits", pty=False)
        ctx.run("git push --tags", title="Pushing tags", pty=False)
        ctx.run("poetry build", title="Building dist/wheel", pty=PTY)
        ctx.run("poetry publish", title="Publishing version", pty=PTY)
        docs_deploy.run()  # type: ignore


@duty(silent=True)
def coverage(ctx):
    """
    Report coverage as text and HTML.

    Arguments:
        ctx: The context instance (passed automatically).
    """
    ctx.run("coverage combine .coverage-*", nofail=True)
    ctx.run("coverage report --rcfile=config/coverage.ini", capture=False)
    ctx.run("coverage html --rcfile=config/coverage.ini")


@duty
def test(ctx, match: str = ""):
    """
    Run the test suite.

    Arguments:
        ctx: The context instance (passed automatically).
        match: A pytest expression to filter selected tests.
    """
    py_version = f"{sys.version_info.major}{sys.version_info.minor}"
    os.environ["COVERAGE_FILE"] = f".coverage-{py_version}"
    ctx.run(
        ["pytest", "-c", "config/pytest.ini", "-n", "auto", "-k", match, "tests"],
        title="Running tests",
        pty=PTY,
    )
