#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

ytsp = "YTSpammerPurge"
nav[("YTSpammerPurge",)] = Path(f"{ytsp}.md")
full_doc_path = Path("reference", f"{ytsp}.md")
with mkdocs_gen_files.open(full_doc_path, "w") as fd:
    print(f"::: {ytsp}", file=fd)
mkdocs_gen_files.set_edit_path(full_doc_path, f"{ytsp}.py")

for path in sorted(Path("Scripts").glob("*.py")):
    module_path = path.with_suffix("")
    doc_path = path.with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = list(module_path.parts)
    nav[parts] = doc_path

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(module_path.parts)
        print("::: " + ident, file=fd)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
