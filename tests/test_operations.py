#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest.mock import MagicMock


def test_exclude_authors(tmp_path):
    from Scripts.operations import exclude_authors

    miscData = MagicMock()
    output_txt = tmp_path / "output.txt"
    miscData.resources = {"Whitelist": {"PathWithName": str(output_txt)}}
    current = MagicMock()
    current.matchSamplesDict = {MagicMock(): MagicMock(), MagicMock(): MagicMock()}
    kwargs = dict(
        current=current,
        config=MagicMock(),
        miscData=miscData,
        excludedCommentsDict=MagicMock(),
        authorsToExcludeSet=MagicMock(),
        commentIDExcludeSet=MagicMock(),
        displayString=MagicMock(),
        inputtedString="exclude 1",
        logInfo=None,
        only=False,
    )
    exp_res = (
        kwargs["current"],
        kwargs["excludedCommentsDict"],
        kwargs["authorsToExcludeSet"],
        kwargs["commentIDExcludeSet"],
    )
    res = exclude_authors(**kwargs)  # type: ignore
    assert res == exp_res
    assert not output_txt.read_text()
