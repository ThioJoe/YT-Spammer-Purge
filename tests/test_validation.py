#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest.mock import patch

import pytest


def test_validate_channel_id():
    ic = "https://www.youtube.com/channel/UCzb9_b2UY29xuY-S8BsmpOg"
    from Scripts.validation import validate_channel_id

    with pytest.raises(AttributeError):
        validate_channel_id(ic)


def test_validate_channel_id_w_mock_youtube():
    channel_id = "UCzb9_b2UY29xuY-S8BsmpOg"
    ic = f"https://www.youtube.com/channel/{channel_id}"
    with patch("Scripts.validation.auth.YOUTUBE", spec=True) as m_youtube:
        from Scripts import validation

        res = validation.validate_channel_id(ic)
        assert res == (
            True,
            channel_id,
            m_youtube.channels.return_value.list.return_value.execute.return_value[
                "items"
            ][0]["snippet"]["title"],
        )
