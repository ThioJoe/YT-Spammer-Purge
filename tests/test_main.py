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
            [MagicMock()] * 3,
            OSError,
            None,
        ),
        ("files", "list_config_files", None, None, []),
        ("files", "choose_config_file", [MagicMock()] * 2, OSError, None),
        ("files", "ingest_asset_file", (MagicMock(),), FileNotFoundError, None),
        (
            "files",
            "copy_asset_file",
            [MagicMock()] * 2,
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
            [MagicMock()] * 2,
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
            [MagicMock()] * 6,
            None,
            None,
        ),
        (
            "logging",
            "print_prepared_comments",
            [MagicMock()] * 7,
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
            [MagicMock()] * 2,
            AttributeError,
            None,
        ),
        (
            "logging",
            "download_profile_pictures",
            [MagicMock()] * 2,
            None,
            None,
        ),
        (
            "logging",
            "prepare_logFile_settings",
            [MagicMock()] * 6,
            FileNotFoundError,
            None,
        ),
        (
            "operations",
            "get_comments",
            [MagicMock()] * 5,
            None,
            None,
        ),
        (
            "operations",
            "get_replies",
            [MagicMock()] * 9,
            None,
            None,
        ),
        (
            "operations",
            "get_comments",
            [MagicMock()] * 5,
            None,
            None,
        ),
        (
            "operations",
            "check_duplicates",
            [MagicMock()] * 5,
            OSError,
            None,
        ),
        (
            "operations",
            "check_against_filter",
            [MagicMock()] * 6,
            AttributeError,
            None,
        ),
        (
            "operations",
            "delete_found_comments",
            [MagicMock()] * 3,
            OSError,
            None,
        ),
        ("operations", "check_recovered_comments", [MagicMock()] * 1, OSError, None),
        ("operations", "exclude_authors", [MagicMock()] * 4, TypeError, None),
        ("operations", "get_recent_videos", [MagicMock()] * 2, TypeError, None),
        ("operations", "print_count_stats", [MagicMock()] * 4, TypeError, None),
        (
            "prepare_modes",
            "prepare_filter_mode_chars",
            [MagicMock()] * 3,
            UnboundLocalError,
            None,
        ),
        (
            "prepare_modes",
            "prepare_filter_mode_strings",
            [MagicMock()] * 3,
            OSError,
            None,
        ),
        (
            "prepare_modes",
            "prepare_filter_mode_strings",
            [MagicMock()] * 3,
            OSError,
            None,
        ),
        (
            "prepare_modes",
            "prepare_filter_mode_regex",
            [MagicMock()] * 3,
            TypeError,
            None,
        ),
        ("prepare_modes", "prepare_filter_mode_ID", [MagicMock()] * 2, None, None),
        (
            "prepare_modes",
            "prepare_filter_mode_non_ascii",
            [MagicMock()] * 2,
            OSError,
            None,
        ),
        (
            "prepare_modes",
            "prepare_filter_mode_smart",
            [MagicMock()] * 3,
            OSError,
            None,
        ),
        ("prepare_modes", "recover_deleted_comments", [MagicMock()], OSError, None),
        ("prepare_modes", "delete_comment_list", [MagicMock()], OSError, None),
        ("utils", "get_video_title", [MagicMock()] * 2, None, None),
        ("utils", "make_char_set", [MagicMock()], None, set()),
        ("utils", "check_list_against_string", [MagicMock()] * 2, None, False),
        ("utils", "string_to_list", [MagicMock()], None, []),
        ("utils", "process_spammer_ids", [MagicMock()], None, None),
        ("utils", "expand_ranges", [MagicMock()], TypeError, None),
        ("utils", "choice", None, OSError, None),
        ("utils", "print_break_finished", [MagicMock()], OSError, None),
        ("utils", "print_error_title_fetch", None, OSError, None),
        ("validation", "validate_video_id", [MagicMock()], TypeError, None),
        ("validation", "validate_post_id", [MagicMock()], None, None),
        ("validation", "validate_channel_id", [MagicMock()], TypeError, None),
        ("validation", "validate_regex", [MagicMock()], TypeError, None),
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
            [MagicMock()] * 5,
        ),
        (
            "logging",
            "write_log_heading",
            [MagicMock()] * 3,
        ),
        (
            "logging",
            "write_log_completion_summary",
            [MagicMock()] * 4,
        ),
        ("logging", "rewrite_log_file", [MagicMock()] * 2),
        ("auth", "initialize", None),
        ("operations", "add_spam", [MagicMock()] * 5),
        (
            "operations",
            "check_deleted_comments",
            [MagicMock()] * 1,
        ),
        ("utils", "print_exception_reason", [MagicMock()]),
        ("utils", "print_http_error_during_scan", [MagicMock()]),
        ("utils", "print_exception_during_scan", [MagicMock()]),
    ),
)
def test_func_return_none(mod, func, func_args):
    import Scripts

    mod_func = getattr(getattr(Scripts, mod), func)
    if func_args:
        assert mod_func(*func_args) is None
    else:
        assert mod_func() is None
