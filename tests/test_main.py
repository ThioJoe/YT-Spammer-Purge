#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize(
    "mod, func, func_args, err, exp_retval",
    (
        ("files", "check_for_update", (MagicMock(),), TypeError, None),
        ("files", "load_config_file", None, OSError, None),
        (
            "files",
            "check_update_config_file",
            (MagicMock(), MagicMock(), MagicMock()),
            OSError,
            None,
        ),
        ("files", "list_config_files", None, None, []),
        ("files", "choose_config_file", (MagicMock(), MagicMock()), OSError, None),
        ("files", "ingest_asset_file", (MagicMock(),), FileNotFoundError, None),
        (
            "files",
            "copy_asset_file",
            (MagicMock(), MagicMock()),
            FileNotFoundError,
            None,
        ),
        ("files", "ingest_list_file", (MagicMock(),), IndexError, None),
        ("files", "get_list_file_version", (MagicMock(),), UnboundLocalError, None),
        ("files", "create_config_file", None, OSError, None),
        ("files", "write_dict_pickle_file", (MagicMock(), MagicMock()), OSError, None),
        ("files", "try_remove_file", (MagicMock(),), OSError, None),
        ("files", "check_existing_save", None, None, []),
        ("auth", "get_authenticated_service", None, OSError, None),
        ("auth", "first_authentication", None, OSError, None),
        ("auth", "get_current_user", (MagicMock(),), AttributeError, None),
        ("auth", "remove_token", None, FileNotFoundError, None),
        (
            "community_downloader",
            "regex_search",
            (MagicMock(), MagicMock()),
            TypeError,
            None,
        ),
        ("community_downloader", "regex_search", ("", ""), IndexError, None),
        ("community_downloader", "regex_search", ("a", "."), IndexError, None),
        (
            "community_downloader",
            "get_post_channel_url",
            (MagicMock(),),
            json.decoder.JSONDecodeError,
            None,
        ),
        (
            "community_downloader",
            "fetch_recent_community_posts",
            (MagicMock(),),
            json.decoder.JSONDecodeError,
            None,
        ),
        ("community_downloader", "main", None, ValueError, None),
        ("community_downloader", "regex_search", ("a", "(.)"), None, "a"),
        (
            "logging",
            "print_comments",
            (
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
            ),
            None,
            None,
        ),
        (
            "logging",
            "print_prepared_comments",
            (
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
            ),
            None,
            None,
        ),
        ("logging", "make_rtf_compatible", (MagicMock(),), None, None),
        ("logging", "write_rtf", (MagicMock(),), TypeError, None),
        ("logging", "write_plaintext_log", (MagicMock(),), TypeError, None),
        ("logging", "write_json_log", (MagicMock(), MagicMock()), TypeError, None),
        (
            "logging",
            "get_extra_json_data",
            (MagicMock(), MagicMock()),
            AttributeError,
            None,
        ),
        (
            "logging",
            "download_profile_pictures",
            (MagicMock(), MagicMock()),
            None,
            None,
        ),
        (
            "logging",
            "prepare_logFile_settings",
            (
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
            ),
            FileNotFoundError,
            None,
        ),
    ),
)
def test_files_func(mod, func, func_args, err, exp_retval):
    import Scripts

    mod_func = getattr(getattr(Scripts, mod), func)
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


@pytest.mark.parametrize(
    "mod, func, func_args",
    (
        (
            "logging",
            "add_sample",
            (MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()),
        ),
        (
            "logging",
            "write_log_heading",
            (
                MagicMock(),
                MagicMock(),
                MagicMock(),
            ),
        ),
        (
            "logging",
            "write_log_completion_summary",
            (
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
            ),
        ),
        ("logging", "rewrite_log_file", (MagicMock(), MagicMock())),
    ),
)
def test_func_return_none(mod, func, func_args):
    import Scripts

    mod_func = getattr(getattr(Scripts, mod), func)
    if func_args:
        assert mod_func(*func_args) is None
    else:
        assert mod_func() is None
