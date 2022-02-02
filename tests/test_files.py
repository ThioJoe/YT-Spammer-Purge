#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

import pytest

from Scripts import files


@pytest.mark.parametrize(
    "func, func_args, err, exp_retval",
    (
        ("check_lists_update", (MagicMock(),), TypeError, None),
        ("check_for_update", (MagicMock(),), TypeError, None),
        ("load_config_file", None, OSError, None),
        (
            "check_update_config_file",
            (MagicMock(), MagicMock(), MagicMock()),
            OSError,
            None,
        ),
        ("list_config_files", None, None, []),
        ("choose_config_file", (MagicMock(), MagicMock()), OSError, None),
        ("ingest_asset_file", (MagicMock(),), FileNotFoundError, None),
        ("copy_asset_file", (MagicMock(), MagicMock()), FileNotFoundError, None),
        ("ingest_list_file", (MagicMock(),), IndexError, None),
        ("get_list_file_version", (MagicMock(),), UnboundLocalError, None),
        ("create_config_file", None, OSError, None),
        ("write_dict_pickle_file", (MagicMock(), MagicMock()), OSError, None),
        ("try_remove_file", (MagicMock(),), OSError, None),
        ("check_existing_save", None, None, []),
    ),
)
def test_files_func(func, func_args, err, exp_retval):
    mod_func = getattr(files, func)
    if err:
        with pytest.raises(err):
            if func_args:
                mod_func(*func_args)
            else:
                mod_func()
    elif func_args and exp_retval is None:
        assert mod_func(*func_args)
    elif func_args and exp_retval is not None:
        assert mod_func(*func_args) == exp_retval
    elif exp_retval is None:
        assert mod_func()
    else:
        assert mod_func() == exp_retval
