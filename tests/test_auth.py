#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize('func', ( 'get_authenticated_service', 'first_authentication') )
def test_func_with_OSError(func):
    from Scripts import auth
    with pytest.raises(OSError):
        getattr(auth, func)()

def test_initialize():
    from Scripts import auth
    auth.initialize()


def test_get_current_user():
    from Scripts import auth
    with pytest.raises(AttributeError):
        auth.get_current_user(MagicMock())

def test_remove_token():
    from Scripts import auth
    with pytest.raises(FileNotFoundError):
        auth.remove_token()
