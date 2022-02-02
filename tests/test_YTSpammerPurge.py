#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest


def test_main():
    import YTSpammerPurge as ytspp
    with pytest.raises(OSError):
        ytspp.main()
