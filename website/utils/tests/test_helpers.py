"""Testing module for :py:mod:`utils.helpers` module."""

import json
import logging
import os
from copy import deepcopy
from unittest import mock

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms import ValidationError

from utils.constants.core import (
    ASASTATS_SLOGANS,
    DEFAULT_SLEEP_INTERVAL,
    INVALID_ADDRESS_TEXT,
    MISSING_ENVIRONMENT_VARIABLE_ERROR,
)
from utils.helpers import (
    base64_to_utf,
    bundle_from_addresses,
    check_algorand_address,
    check_bundle_addresses,
    create_bundle,
    create_multiprocess_logger,
    get_env_variable,
    load_transparency_reports,
    message_for_app_code_in_values,
    parse_export_limits,
    pause,
    random_slogan,
    read_json,
    weighted_randomized_banner,
)
from utils.tests.fixtures import (
    TEST_ADDRESS,
    TEST_ADDRESS2,
    TEST_ADDRESS3,
    TEST_BANNERS,
    TESTING_VALUES_SMALL,
)


class TestUtilsHelpersFunctions:
    """Testing class for :py:mod:`utils.helpers` functions."""

    # # base64_to_utf
    def test_utils_helpers_base64_to_utf_returns_empty_string_for_no_value(self):
        assert base64_to_utf("") == ""

    def test_utils_helpers_base64_to_utf_returns_empty_string_for_wrong_value(self):
        value = "1Z1fxplupLIoTgnub0NOoKH33eRixM7CdHrNfmCnZSM="
        assert base64_to_utf(value) == ""

    def test_utils_helpers_base64_to_utf_returns_empty_string_for_error(self, mocker):
        base64_message = mocker.MagicMock()
        base64_message.encode.side_effect = UnicodeDecodeError("", bytes(), 0, 0, "")
        assert base64_to_utf(base64_message) == ""

    def test_utils_helpers_base64_to_utf_returns_string(self):
        base64_message = "eyJhc3NldElkIjozMTU2NjcwNH0="
        assert base64_to_utf(base64_message) == '{"assetId":31566704}'

    # check_algorand_address
    def test_utils_helpers_check_address_returns_address_if_it_is_valid(self, mocker):
        mocked_algod = mocker.patch("utils.helpers.algod_instance")
        mocked_is_valid = mocker.patch(
            "utils.helpers.is_valid_address", return_value=True
        )
        entry = "valid-address"
        mocked_name = mocker.patch("utils.helpers.check_name", return_value=entry)
        returned = check_algorand_address(entry)
        assert returned == entry
        mocked_name.assert_called_once_with(entry, mocked_algod.return_value)
        mocked_algod.assert_called_once_with()
        mocked_is_valid.assert_called_once_with(entry)

    def test_utils_helpers_check_address_returns_addresses_for_valid_name(self, mocker):
        mocked_algod = mocker.patch("utils.helpers.algod_instance")
        mocked_is_valid = mocker.patch(
            "utils.helpers.is_valid_address", return_value=True
        )
        entry = "somename.algo"
        address1, address2 = "valid-address1", "valid-address2"
        addresses = f"{address1} {address2}"
        mocked_name = mocker.patch("utils.helpers.check_name", return_value=addresses)
        returned = check_algorand_address(entry)
        assert returned == addresses
        mocked_name.assert_called_once_with(entry, mocked_algod.return_value)
        mocked_algod.assert_called_once_with()
        calls = [
            mocker.call(address1),
            mocker.call(address2),
        ]
        mocked_is_valid.assert_has_calls(calls, any_order=False)
        assert mocked_is_valid.call_count == 2

    def test_utils_helpers_check_address_returns_empty_string_for_invalid_address(
        self, mocker
    ):
        mocked_algod = mocker.patch("utils.helpers.algod_instance")
        mocked_name = mocker.patch("utils.helpers.check_name", return_value="address1")
        mocked_is_valid = mocker.patch(
            "utils.helpers.is_valid_address", return_value=False
        )
        entry = mocker.MagicMock()
        assert check_algorand_address(entry) == ""
        mocked_name.assert_called_once_with(entry, mocked_algod.return_value)
        mocked_is_valid.assert_called_once_with(mocked_name.return_value)

    def test_utils_helpers_check_address_returns_empty_string_for_invalid_name(
        self, mocker
    ):
        mocker.patch("utils.helpers.algod_instance")
        mocker.patch("utils.helpers.is_valid_address", side_effect=[True, False])
        entry = "somename.algo"
        address1, address2 = "valid-address1", "valid-address2"
        addresses = f"{address1} {address2}"
        mocker.patch("utils.helpers.check_name", return_value=addresses)
        returned = check_algorand_address(entry)
        assert returned == ""

    def test_utils_helpers_check_address_raises_validationerror_for_raise_true(
        self, mocker
    ):
        mocker.patch("utils.helpers.check_name", return_value="address1 address2")
        mocker.patch("utils.helpers.algod_instance")
        mocker.patch("utils.helpers.is_valid_address", return_value=False)
        with pytest.raises(ValidationError) as exception:
            check_algorand_address(mocker.MagicMock(), raise_error=True)
        assert exception.value.message == INVALID_ADDRESS_TEXT

    # # create_multiprocess_logger
    def test_utils_helpers_create_multiprocess_logger_returns_multiprocessing_logger(
        self, mocker
    ):
        mocker.patch("utils.helpers.logging.FileHandler")
        mocker.patch("utils.helpers.logging.Formatter")
        mocker.patch("utils.helpers.multiprocessing.current_process")
        mocked = mocker.patch("utils.helpers.multiprocessing.get_logger")
        returned = create_multiprocess_logger("identifier")
        assert returned == mocked.return_value
        mocked.assert_called_once_with()

    def test_utils_helpers_create_multiprocess_logger_sets_level_to_info(self, mocker):
        mocker.patch("utils.helpers.logging.FileHandler")
        mocker.patch("utils.helpers.logging.Formatter")
        mocker.patch("utils.helpers.multiprocessing.current_process")
        mocked = mocker.patch("utils.helpers.multiprocessing.get_logger")
        create_multiprocess_logger("identifier")
        mocked.return_value.setLevel.assert_called_once_with(logging.INFO)

    def test_utils_helpers_create_multiprocess_logger_sets_level_to_provided(
        self, mocker
    ):
        mocker.patch("utils.helpers.logging.FileHandler")
        mocker.patch("utils.helpers.logging.Formatter")
        mocker.patch("utils.helpers.multiprocessing.current_process")
        mocked = mocker.patch("utils.helpers.multiprocessing.get_logger")
        create_multiprocess_logger("identifier", level=logging.WARNING)
        mocked.return_value.setLevel.assert_called_once_with(logging.WARNING)

    def test_utils_helpers_create_multiprocess_logger_initalizes_filehandler_default(
        self, mocker
    ):
        mocker.patch("utils.helpers.multiprocessing.get_logger")
        mocker.patch("utils.helpers.logging.Formatter")
        process = mocker.MagicMock()
        name = "NAME"
        process.name = name
        mocked_current = mocker.patch(
            "utils.helpers.multiprocessing.current_process", return_value=process
        )
        mocked = mocker.patch("utils.helpers.logging.FileHandler")
        identifier = "identifier"
        create_multiprocess_logger(identifier)
        mocked.assert_called_once_with(
            settings.DATA_PATH / "logs" / f"process_{name}_{identifier}.log"
        )
        mocked_current.assert_called_once_with()

    def test_utils_helpers_create_multiprocess_logger_initalizes_filehandler_prefix(
        self, mocker
    ):
        mocker.patch("utils.helpers.multiprocessing.get_logger")
        mocker.patch("utils.helpers.logging.Formatter")
        process = mocker.MagicMock()
        name = "NAME"
        process.name = name
        mocked_current = mocker.patch(
            "utils.helpers.multiprocessing.current_process", return_value=process
        )
        mocked = mocker.patch("utils.helpers.logging.FileHandler")
        identifier = "identifier"
        prefix = "prefix"
        create_multiprocess_logger(identifier, prefix=prefix)
        mocked.assert_called_once_with(
            settings.DATA_PATH / "logs" / f"{prefix}_{name}_{identifier}.log"
        )
        mocked_current.assert_called_once_with()

    def test_utils_helpers_create_multiprocess_logger_initalizes_formatter(
        self, mocker
    ):
        mocker.patch("utils.helpers.multiprocessing.get_logger")
        mocker.patch("utils.helpers.logging.FileHandler")
        process = mocker.MagicMock()
        name = "NAME"
        process.name = name
        mocker.patch(
            "utils.helpers.multiprocessing.current_process", return_value=process
        )
        mocked = mocker.patch("utils.helpers.logging.Formatter")
        create_multiprocess_logger("identifier")
        mocked.assert_called_once_with("%(asctime)s - %(levelname)s - %(message)s")

    def test_utils_helpers_create_multiprocess_logger_sets_handler_level_to_provided(
        self, mocker
    ):
        mocker.patch("utils.helpers.logging.FileHandler")
        mocker.patch("utils.helpers.logging.Formatter")
        mocker.patch("utils.helpers.multiprocessing.current_process")
        mocked = mocker.patch("utils.helpers.multiprocessing.get_logger")
        create_multiprocess_logger("identifier", level=logging.WARNING)
        mocked.return_value.setLevel.assert_called_once_with(logging.WARNING)

    def test_utils_helpers_create_multiprocess_logger_sets_formatter_and_adds_handler(
        self, mocker
    ):
        mocked_logger = mocker.patch("utils.helpers.multiprocessing.get_logger")
        mocked_handler = mocker.patch("utils.helpers.logging.FileHandler")
        process = mocker.MagicMock()
        name = "NAME"
        process.name = name
        mocker.patch(
            "utils.helpers.multiprocessing.current_process", return_value=process
        )
        mocked_formatter = mocker.patch("utils.helpers.logging.Formatter")
        returned = create_multiprocess_logger("identifier")
        assert returned == mocked_logger.return_value
        mocked_handler.return_value.setFormatter.assert_called_once_with(
            mocked_formatter.return_value
        )
        mocked_logger.return_value.addHandler.assert_called_once_with(
            mocked_handler.return_value
        )
        mocked_handler.return_value.setLevel.assert_called_once_with(logging.INFO)

    def test_utils_helpers_create_multiprocess_logger_formatter_and_handler_level(
        self, mocker
    ):
        mocked_logger = mocker.patch("utils.helpers.multiprocessing.get_logger")
        mocked_handler = mocker.patch("utils.helpers.logging.FileHandler")
        process = mocker.MagicMock()
        name = "NAME"
        process.name = name
        mocker.patch(
            "utils.helpers.multiprocessing.current_process", return_value=process
        )
        mocked_formatter = mocker.patch("utils.helpers.logging.Formatter")
        returned = create_multiprocess_logger("identifier", level=logging.WARNING)
        assert returned == mocked_logger.return_value
        mocked_handler.return_value.setFormatter.assert_called_once_with(
            mocked_formatter.return_value
        )
        mocked_logger.return_value.addHandler.assert_called_once_with(
            mocked_handler.return_value
        )
        mocked_handler.return_value.setLevel.assert_called_once_with(logging.WARNING)

    # # get_env_variable
    def test_utils_helpers_get_env_variable_access_and_returns_os_environ_key(self):
        var_name = "SECRET_KEY"
        old_value = os.environ[var_name]
        value = "some value"
        os.environ[var_name] = value
        returned = get_env_variable(var_name)
        os.environ[var_name] = old_value
        assert returned == value

    def test_utils_helpers_get_env_variable_raises_for_wrong_variable(self):
        name = "NON_EXISTING_VARIABLE_NAME"
        with pytest.raises(ImproperlyConfigured) as exception:
            get_env_variable(name)
        assert str(exception.value) == "{} {}!".format(
            name, MISSING_ENVIRONMENT_VARIABLE_ERROR
        )

    def test_utils_helpers_get_env_variable_returns_default(self):
        name = "NON_EXISTING_VARIABLE_NAME"
        default = "default"
        assert get_env_variable(name, default) == default

    def test_utils_helpers_get_env_variable_functionality(self):
        assert "settings" in get_env_variable("DJANGO_SETTINGS_MODULE")

    # # message_for_app_code_in_values
    def test_utils_helpers_message_for_app_code_in_values_returns_empty_string(
        self, mocker
    ):
        values = deepcopy(TESTING_VALUES_SMALL)
        app_codes = ["ff"]
        assert (
            message_for_app_code_in_values(values, app_codes, mocker.MagicMock()) == ""
        )

    def test_utils_helpers_message_for_app_code_in_values_returns_empty_string_empty(
        self, mocker
    ):
        values = [
            [100.0, 520602904, 1, {}, 405.2525, "ABCDE"],
            [1, 520602904, 1, {}, 405.2525, ""],
        ]
        app_codes = ["ff", "foo"]
        assert (
            message_for_app_code_in_values(values, app_codes, mocker.MagicMock()) == ""
        )

    def test_utils_helpers_message_for_app_code_in_values_returns_message(self, mocker):
        values = deepcopy(TESTING_VALUES_SMALL)
        app_codes = ["foo", "ff", "e"]
        msg = mocker.MagicMock()
        assert message_for_app_code_in_values(values, app_codes, msg) == msg

    # # parse_export_limits
    def test_utils_helpers_parse_export_limits_returns_valid_dictionary(self):
        raw = "free: 5, Intro:6, Asastatser : 7"
        assert parse_export_limits(raw) == {"free": 5, "Intro": 6, "Asastatser": 7}

    def test_utils_helpers_parse_export_limits_skips_missing_key_or_separator(self):
        # ":6" has no key; "Asastatser7" has no separator
        raw = "free:5, :6, Asastatser7"
        assert parse_export_limits(raw) == {"free": 5}

    def test_utils_helpers_parse_export_limits_skips_invalid_integers(self):
        # "abc" cannot be cast to int
        raw = "free:5, Intro:abc"
        assert parse_export_limits(raw) == {"free": 5}

    def test_utils_helpers_parse_export_limits_handles_empty_string(self):
        assert parse_export_limits("") == {}

    # # pause
    def test_utils_helpers_pause_functionality_for_provided_argument(self):
        seconds = 10
        with mock.patch("utils.helpers.time.sleep") as mocked_sleep:
            pause(seconds)
            mocked_sleep.assert_called_once_with(seconds)

    def test_utils_helpers_pause_default_functionality(self):
        with mock.patch("utils.helpers.time.sleep") as mocked_sleep:
            pause()
            mocked_sleep.assert_called_once_with(DEFAULT_SLEEP_INTERVAL)

    # # read_json
    def test_utils_helpers_read_json_returns_empty_dict_for_no_file(self, mocker):
        path = mocker.MagicMock()
        with (
            mock.patch(
                "utils.helpers.os.path.exists", return_value=False
            ) as mocked_exist,
            mock.patch("utils.helpers.open") as mocked_open,
        ):
            assert read_json(path) == {}
            mocked_exist.assert_called_once_with(path)
            mocked_open.assert_not_called()

    def test_utils_helpers_read_json_returns_empty_dict_for_exception(self, mocker):
        with (
            mock.patch("utils.helpers.os.path.exists", return_value=True),
            mock.patch("utils.helpers.open"),
            mock.patch(
                "utils.helpers.json.load", side_effect=json.JSONDecodeError("", "", 0)
            ),
        ):
            assert read_json(mocker.MagicMock()) == {}

    def test_utils_helpers_read_json_returns_json_file_content(self, mocker):
        path = mocker.MagicMock()
        with (
            mock.patch("utils.helpers.os.path.exists", return_value=True),
            mock.patch("utils.helpers.open") as mocked_open,
            mock.patch("utils.helpers.json.load") as mocked_load,
        ):
            assert read_json(path) == mocked_load.return_value
            mocked_open.assert_called_once_with(path, "r")
            mocked_load.assert_called_once_with(
                mocked_open.return_value.__enter__.return_value
            )


class TestUtilsHelpersGeneralPublicFunctions:
    """Testing class for :py:mod:`utils.helpers` general public functions."""

    # # bundle_from_addresses
    def test_utils_helpers_bundle_from_addresses_instantiates_sha1(self):
        addresses = "foo bar"
        with mock.patch("utils.helpers.hashlib.sha1") as mocked:
            returned = bundle_from_addresses(addresses)
            assert (
                returned
                == mocked.return_value.hexdigest.return_value.upper.return_value
            )
            mocked.assert_called_once_with(b"bar foo")
            mocked.return_value.hexdigest.assert_called_once_with()

    def test_utils_helpers_bundle_from_addresses_uses_addresses_for_hash(self):
        addresses = "foo bar"
        with mock.patch("utils.helpers.hashlib.sha1") as mocked:
            bundle_from_addresses(addresses)
            mocked.return_value.hexdigest.assert_called_once_with()
            mocked.return_value.hexdigest.return_value.upper.assert_called_once_with()

    @pytest.mark.parametrize(
        "addresses,result",
        [
            (
                f"{TEST_ADDRESS} {TEST_ADDRESS2}",
                "65B4307A047B8276EEA9F184EE78975A5F47ACA1",
            ),
            (
                f"{TEST_ADDRESS2} {TEST_ADDRESS2} {TEST_ADDRESS3}",
                "540A5D8CEC896E073F9170AF0A962503E69147CF",
            ),
            (
                f"{TEST_ADDRESS} {TEST_ADDRESS3}",
                "8C6405F9FC1E9CD5078C4B0CEA15C7CBCF484800",
            ),
            (
                f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
                "540A5D8CEC896E073F9170AF0A962503E69147CF",
            ),
            (
                f"{TEST_ADDRESS} {TEST_ADDRESS2} {TEST_ADDRESS3}",
                "8F509823948F7595D6138602C80E5DF8CAFD3A70",
            ),
        ],
    )
    def test_utils_helpers_bundle_from_addresses_functionality(self, addresses, result):
        assert bundle_from_addresses(addresses) == result

    # # check_bundle_addresses
    def test_utils_helpers_check_bundle_addresses_returns_addresses(self, mocker):
        bundle = "foobar"
        addresses = "foo bar"
        mocked_cache = mocker.patch("utils.helpers.redis_instance")
        mocked = mocker.patch("utils.helpers.cached_bundle", return_value=addresses)
        returned = check_bundle_addresses(bundle)
        assert returned == addresses
        mocked.assert_called_once_with(bundle, mocked_cache.return_value)
        mocked_cache.assert_called_once_with()

    def test_utils_helpers_check_bundle_addresses_returns_empty_string_if_not_exists(
        self, mocker
    ):
        bundle = "foobar"
        mocker.patch("utils.helpers.redis_instance")
        mocker.patch("utils.helpers.cached_bundle", return_value=False)
        returned = check_bundle_addresses(bundle)
        assert returned == ""

    # # create_bundle
    def test_utils_helpers_create_bundle_doesnt_update_cache_if_it_exist(self, mocker):
        addresses = "foo bar"
        mocked_bundle = mocker.patch("utils.helpers.bundle_from_addresses")
        mocked_redis = mocker.patch("utils.helpers.redis_instance")
        mocked_cached = mocker.patch("utils.helpers.cached_bundle")
        mocked_cupdate = mocker.patch("utils.helpers.cupdate_bundle")
        create_bundle(addresses)
        mocked_bundle.assert_called_once_with(addresses)
        mocked_cached.assert_called_once_with(
            mocked_bundle.return_value,
            mocked_redis.return_value,
        )
        mocked_redis.assert_called_once_with()
        mocked_cupdate.assert_not_called()

    def test_utils_helpers_create_bundle_updates_cache(self, mocker):
        addresses = "foo bar"
        mocked_bundle = mocker.patch("utils.helpers.bundle_from_addresses")
        mocked_redis = mocker.patch("utils.helpers.redis_instance")
        mocker.patch("utils.helpers.cached_bundle", return_value=False)
        mocked_cupdate = mocker.patch("utils.helpers.cupdate_bundle")
        create_bundle(addresses)
        mocked_bundle.assert_called_once_with(addresses)
        mocked_cupdate.assert_called_once_with(
            mocked_bundle.return_value,
            addresses,
            mocked_redis.return_value,
        )
        mocked_redis.assert_called_once_with()

    # # load_transparency_reports
    def test_utils_helpers_load_transparency_reports_parsing_and_sorting(self, mocker):
        mocker.patch("os.path.exists", return_value=True)
        # Mocking directory contents: mixing valid PDFs, invalid files, and out of order dates
        mock_files = [
            "asastats-logo.png",
            "asastats-transparency-report-2024-05.pdf",
            "asastats-transparency-report-2026-01.pdf",
            "asastats-transparency-report-2024-12.pdf",
            "asastats-whitepaper.pdf",
        ]
        mocker.patch("os.listdir", return_value=mock_files)
        reports = load_transparency_reports()
        # Check grouping and sorting (2026 should be first, then 2024. 2025 doesn't exist)
        assert len(reports) == 2
        assert reports[0]["year"] == 2026
        assert reports[1]["year"] == 2024
        # Check 2026 contents
        assert len(reports[0]["months"]) == 1
        assert reports[0]["months"][0]["month"] == "01"
        assert reports[0]["months"][0]["month_name"] == "January"
        # Check 2024 contents and sorting (12 should be before 05)
        assert len(reports[1]["months"]) == 2
        assert reports[1]["months"][0]["month"] == "12"
        assert reports[1]["months"][0]["month_name"] == "December"
        assert reports[1]["months"][1]["month"] == "05"
        assert reports[1]["months"][1]["short_year"] == "24"

    def test_utils_helpers_load_transparency_reports_directory_missing(self, mocker):
        mocker.patch("os.path.exists", return_value=False)
        reports = load_transparency_reports()
        assert reports == []

    # # random_slogan
    def test_utils_helpers_random_slogan_calls_random_choice(self):
        with mock.patch("utils.helpers.random.choice") as mocked:
            random_slogan()
            mocked.assert_called_once_with(ASASTATS_SLOGANS)

    def test_utils_helpers_random_slogan_returns_from_slogans_collection(self):
        returned = random_slogan()
        assert isinstance(returned, str)
        assert returned in ASASTATS_SLOGANS

    # # weighted_randomized_banner
    def test_utils_helpers_weighted_randomized_banner(self):
        """
        Ensure the function returns a banner from the provided list and that it
        is unwrapped from the list returned by random.choices.
        """
        result = weighted_randomized_banner(TEST_BANNERS)
        assert result in TEST_BANNERS

    def test_utils_helpers_weighted_randomized_banner_passes_correct_weights(self):
        # We patch 'random.choices' where it is imported/used in your module.
        # Assuming the function is defined in a module where 'import random' is used:
        with mock.patch("random.choices") as mock_choices:
            # random.choices returns a list, so we mock it to return a list containing one banner
            mock_choices.return_value = [TEST_BANNERS[0]]
            result = weighted_randomized_banner(TEST_BANNERS)
            # Verify it was called with the exact weights we expect: [4, 2, 1]
            mock_choices.assert_called_once_with(TEST_BANNERS, weights=[4, 2, 1], k=1)
            # Verify the function correctly returns the unwrapped single dictionary
            assert result == TEST_BANNERS[0]

    def test_utils_helpers_weighted_randomized_banner_handles_missing_weights(self):
        banners_missing_weights = [
            {"image": "img/1.jpg", "weight": 5},
            {"image": "img/2.jpg"},  # Missing weight key
        ]
        with mock.patch("random.choices") as mock_choices:
            mock_choices.return_value = [banners_missing_weights[0]]
            weighted_randomized_banner(banners_missing_weights)
            # Verify the missing weight was defaulted to 1
            mock_choices.assert_called_once_with(
                banners_missing_weights, weights=[5, 1], k=1
            )

    def test_utils_helpers_weighted_randomized_banner_empty_list(self):
        returned = weighted_randomized_banner([])
        assert returned == {}
