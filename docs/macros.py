"""Macros and filters made available in Markdown pages."""

from itertools import chain
from pathlib import Path

import toml
from pip._internal.commands.show import search_packages_info  # noqa: WPS436 (no other way?)


def get_credits_data() -> dict:
    """
    Return data used to generate the credits file.

    Returns:
        Data required to render the credits template.
    """
    project_dir = Path(__file__).parent.parent
    metadata = toml.load(project_dir / "pyproject.toml")["tool"]["poetry"]
    lock_data = toml.load(project_dir / "poetry.lock")
    project_name = metadata["name"]

    direct_dependencies = set(metadata["dependencies"].keys())
    direct_dependencies.remove("python")
    dev_dependencies = set(metadata["dev-dependencies"].keys())
    poetry_dependencies = set(chain(direct_dependencies, dev_dependencies))
    indirect_dependencies = {
        pkg["name"].lower() for pkg in lock_data["package"] if pkg["name"].lower() not in poetry_dependencies
    }

    packages = {}
    all_pkgs = poetry_dependencies.copy()
    all_pkgs.update(indirect_dependencies)
    for pkg in search_packages_info(list(all_pkgs)):
        # NOTE walrus can be used
        name = pkg.name
        if name:
            packages[name.lower()] = {key: getattr(pkg, key) for key in dir(pkg) if not key.startswith("_")}

    # all packages might not be credited,
    # like the ones that are now part of the standard library
    # or the ones that are only used on other operating systems,
    # and therefore are not installed,
    # but it's not that important

    return {
        "project_name": project_name,
        "direct_dependencies": sorted(direct_dependencies),
        "dev_dependencies": sorted(dev_dependencies),
        "indirect_dependencies": sorted(indirect_dependencies),
        "package_info": packages,
    }


def define_env(env):
    """
    Add macros and filters into the Jinja2 environment.

    This hook is called by `mkdocs-macros-plugin`
    when building the documentation.

    Arguments:
        env: An object used to add macros and filters to the environment.
    """
    env.macro(get_credits_data, "get_credits_data")
