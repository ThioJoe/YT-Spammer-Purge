#!/usr/bin/env python
# -*- coding: utf-8 -*-
def test_initialize():
    from Scripts import auth

    assert auth.initialize() is None
