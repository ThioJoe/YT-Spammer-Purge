#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from unittest.mock import MagicMock

import pytest

from Scripts import community_downloader as cd


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
