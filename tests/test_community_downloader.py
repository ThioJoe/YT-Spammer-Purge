#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from unittest.mock import MagicMock

import pytest

from Scripts import community_downloader as cd


@pytest.mark.parametrize(
    "func, err, args",
    (
        ("regex_search", TypeError, (MagicMock(), MagicMock())),
        ("regex_search", IndexError, ("", "")),
        ("regex_search", IndexError, ("a", ".")),
        ("get_post_channel_url", json.decoder.JSONDecodeError, (MagicMock(),)),
        ("fetch_recent_community_posts", json.decoder.JSONDecodeError, (MagicMock(),)),
        ("main", ValueError, ()),
    ),
)
def test_auth_func(func, err, args):
    with pytest.raises(err):
        getattr(cd, func)(*args)


def test_regex_search_with_string():
    assert cd.regex_search("a", "(.)") == "a"


def test_ajax_request():
    if True:
        pytest.skip("run forever")
    cd.ajax_request(MagicMock(), MagicMock(), MagicMock())


def test_download_comments():
    res = cd.download_comments(MagicMock())
    assert res
    with pytest.raises(json.decoder.JSONDecodeError):
        list(res)


def test_search_dict():
    res = cd.search_dict(MagicMock(), MagicMock())
    assert res
    assert not list(res)
