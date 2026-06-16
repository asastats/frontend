"""Testing module for :py:mod:`core.helpers` module."""

import types
from pathlib import Path
from unittest import mock

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

import core.helpers
from core.helpers import (
    BUNDLE_SEPARATION_CHARS,
    INVALID_ADDRESS_TEXT,
    MAX_BUNDLE_SIZE,
    _check_public_bundles_eligibility,
    _create_public_bundle_files,
    _delete_public_bundle_files,
    _normalize_collection,
    _parse_bundle,
    _public_bundle_filenames,
    _public_bundles_collection,
    _send_duration_messages,
    _send_enqueued_messages,
    _strip_address,
    addresses_from_raw,
    check_export_status,
    check_forbidden_addresses,
    check_public_bundles,
    context_with_consolidated_data,
    format_addresses_limit_help_text,
    prepare_tax_context,
    reset_export,
    start_export,
)
from core.templatetags.core_extras import short_address
from utils.constants.core import FORBIDDEN_ADDRESSES
from utils.constants.tax import TAX_DURATION_MESSAGE
from utils.constants.users import (
    BUNDLE_ADDRESSES_LIMIT_HELP_TEXT,
    PUBLIC_BUNDLE_ADDRESSES_LIMIT_HELP_TEXT,
    PUBLIC_BUNDLE_ADDRESSES_NOT_ALLOWED_HELP_TEXT,
)
from utils.tests.fixtures import TEST_ADDRESS, TEST_ADDRESS2, TEST_BUNDLE


class TestCoreHelpersParsingRawFunctions:
    """Testing class for :py:mod:`core.helpers` raw input parsing functions."""

    # # _normalize_collection
    def test_corehelpers_normalize_collection_functionality(self):
        address1, address2, address3, address4, address5 = (
            "address1",
            "address2",
            "address3",
            "address4",
            "address5",
        )
        collection = [address1, "", f"{address2} {address3} {address4}", address5]
        returned = _normalize_collection(collection)
        assert returned == [address1, address2, address3, address4, address5]

    def test_corehelpers_normalize_collection_functionality_for_greater_than_max_size(
        self,
    ):
        (
            address1,
            address2,
            address3,
            address4,
            address5,
            address6,
            address7,
        ) = (
            "address1",
            "address2",
            "address3",
            "address4",
            "address5",
            "address6",
            "address7",
        )
        collection = [
            address1,
            "",
            f"{address2} {address3} {address4}",
            f"{address5} {address6} {address7}",
        ]
        returned = _normalize_collection(collection)
        assert (
            returned
            == [address1, address2, address3, address4, address5, address6, address7][
                :MAX_BUNDLE_SIZE
            ]
        )

    def test_corehelpers_normalize_collection_functionality_for_provided_max_size(
        self,
    ):
        (
            address1,
            address2,
            address3,
            address4,
            address5,
            address6,
            address7,
        ) = (
            "address1",
            "address2",
            "address3",
            "address4",
            "address5",
            "address6",
            "address7",
        )
        collection = [
            address1,
            "",
            f"{address2} {address3} {address4}",
            f"{address5} {address6} {address7}",
        ]
        max_bundle_size = 4
        returned = _normalize_collection(collection, max_bundle_size=max_bundle_size)
        assert (
            returned
            == [address1, address2, address3, address4, address5, address6, address7][
                :max_bundle_size
            ]
        )

    # # _parse_bundle
    def test_corehelpers_parse_bundle_functionality(self, mocker):
        address1, address2, address3, address4, address5 = (
            "address1",
            "address2",
            "address3",
            "address4",
            "address5",
        )
        stripped = [address1, address2, address3, address4, address5]
        mocked_strip = mocker.patch("core.helpers._strip_address", side_effect=stripped)
        mocked_check = mocker.patch(
            "core.helpers.check_algorand_address", side_effect=stripped
        )
        data = f"{address1},{address2},{address3},{address4},{address5}"
        returned = _parse_bundle(data)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == stripped
        calls = [mocker.call(address) for address in stripped]
        mocked_strip.assert_has_calls(calls, any_order=True)
        assert mocked_strip.call_count == len(stripped)
        calls = [mocker.call(address) for address in stripped]
        mocked_check.assert_has_calls(calls, any_order=True)
        assert mocked_check.call_count == len(stripped)

    # # _strip_address
    @pytest.mark.parametrize(
        "char", [*[char for char in BUNDLE_SEPARATION_CHARS], "\n"]
    )
    def test_corehelpers_strip_address_functionality(self, char):
        returned = _strip_address(TEST_ADDRESS + char)
        assert returned == TEST_ADDRESS

    # # addresses_from_raw
    def test_corehelpers_addresses_from_raw_raises_validationerror_for_empty_provided(
        self,
    ):
        with pytest.raises(ValidationError) as exception:
            addresses_from_raw(None, None)
            assert str(exception.value) == INVALID_ADDRESS_TEXT

    def test_corehelpers_addresses_from_raw_returns_check_for_address_data_and_not_data(
        self, mocker
    ):
        mocked = mocker.patch("core.helpers.check_algorand_address")
        returned = addresses_from_raw(None, TEST_ADDRESS)
        assert returned == mocked.return_value
        mocked.assert_called_once_with(TEST_ADDRESS, raise_error=True)

    def test_corehelpers_addresses_from_raw_returns_addresses_for_valid_bundle(self):
        returned = addresses_from_raw(f"{TEST_ADDRESS},{TEST_ADDRESS2}")
        assert len(returned.split(" ")) == 2
        assert TEST_ADDRESS in returned
        assert TEST_ADDRESS2 in returned

    def test_corehelpers_addresses_from_raw_is_valid_for_valid_raw_of_names(
        self, mocker
    ):
        addresses1, addresses2 = "addresses1", "addresses2"
        mocker.patch(
            "core.helpers.check_algorand_address",
            side_effect=[addresses1, TEST_ADDRESS, addresses2, TEST_ADDRESS2],
        )
        returned = addresses_from_raw(
            f"name1.algo,{TEST_ADDRESS},name2.algo,{TEST_ADDRESS2}"
        )
        assert len(returned.split(" ")) == 4
        assert addresses1 in returned
        assert addresses2 in returned
        assert TEST_ADDRESS in returned
        assert TEST_ADDRESS2 in returned

    def test_corehelpers_addresses_from_for_provided_max_bundle_size(self, mocker):
        addresses1, addresses2 = "addresses1", "addresses2"
        mocker.patch(
            "core.helpers.check_algorand_address",
            side_effect=[addresses1, TEST_ADDRESS, addresses2, TEST_ADDRESS2],
        )
        returned = addresses_from_raw(
            f"name1.algo,{TEST_ADDRESS},name2.algo,{TEST_ADDRESS2}", max_bundle_size=3
        )
        assert len(returned.split(" ")) == 3
        assert addresses1 in returned
        assert addresses2 in returned
        assert TEST_ADDRESS in returned

    def test_corehelpers_addresses_from_raw_raises_validationerror_for_no_bundle(
        self, mocker
    ):
        mocked_parse = mocker.patch("core.helpers._parse_bundle")
        raw = "some.data"
        mocked_normalize = mocker.patch(
            "core.helpers._normalize_collection", return_value=False
        )
        with pytest.raises(ValidationError) as exception:
            returned = addresses_from_raw(raw)
            assert str(exception.value) == INVALID_ADDRESS_TEXT
            assert returned == mocked_normalize.return_value
        mocked_parse.assert_called_once_with(raw)
        mocked_normalize.assert_called_once_with(
            mocked_parse.return_value, max_bundle_size=MAX_BUNDLE_SIZE
        )

    # # check_forbidden_addresses
    def test_corehelpers_check_forbidden_addresses_raises_404(self):
        address = FORBIDDEN_ADDRESSES[0]
        with pytest.raises(Http404):
            check_forbidden_addresses(address)

    def test_corehelpers_check_forbidden_addresses_raises_404_for_multiple_addresses(
        self,
    ):
        addresses = f"ADDRESS1 {FORBIDDEN_ADDRESSES[0]}"
        with pytest.raises(Http404):
            check_forbidden_addresses(addresses)

    def test_corehelpers_check_forbidden_addresses_does_nothing_for_normal_address(
        self,
    ):
        address = "ADDRESS1"
        check_forbidden_addresses(address)

    # # context_with_consolidated_data
    def test_core_helpers_context_with_consolidated_data_functionality(self, mocker):
        asas, values, total, nft_colors = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        context = {
            "asas": asas,
            "values": values,
            "total": total,
            "nft_colors": nft_colors,
        }
        serialized_data = mocker.MagicMock()
        distchart, ratiochart, nftfloorchart, consolidated = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        mocked_prepare = mocker.patch(
            "core.helpers.prepare_consolidated_charts",
            return_value=(distchart, ratiochart, nftfloorchart, consolidated),
        )
        returned = context_with_consolidated_data(context, serialized_data)
        mocked_prepare.assert_called_once_with(
            serialized_data, asas, values, total, nft_colors
        )
        assert len(returned) == 8
        assert returned["asas"] == asas
        assert returned["distchart"] == distchart
        assert returned["ratiochart"] == ratiochart
        assert returned["nftfloorchart"] == nftfloorchart
        assert returned["consolidated"] == consolidated


# class MockedSession(dict):
#     modified = False


class TestCoreHelpersTaxClientSideFunctions:
    """Testing class for :py:mod:`core.helpers` client-side tax functions."""

    # # _send_duration_messages
    def test_core_helpers_send_duration_messages_functionality(self, mocker):
        request = mocker.MagicMock()
        mocked_success = mocker.patch("core.helpers.messages.success")
        _send_duration_messages(request)
        lines = TAX_DURATION_MESSAGE.split("\n")
        calls = [
            mocker.call(request, "-" * 5),
            *[mocker.call(request, line) for line in lines],
        ]
        mocked_success.assert_has_calls(calls, any_order=True)
        assert mocked_success.call_count == len(lines) * 2

    # # _send_enqueued_messages
    def test_core_helpers_send_enqueued_messages_for_single_address(self, mocker):
        request = mocker.MagicMock()
        addresses = TEST_ADDRESS
        mocked_success = mocker.patch("core.helpers.messages.success")
        _send_enqueued_messages(request, addresses)
        mocked_success.assert_called_once_with(
            request, f"{short_address(addresses)} enqueued for processing!"
        )

    def test_core_helpers_send_enqueued_messages_for_multiple_addresses(self, mocker):
        request = mocker.MagicMock()
        addresses = f"{TEST_ADDRESS} {TEST_ADDRESS2}"
        mocked_success = mocker.patch("core.helpers.messages.success")
        _send_enqueued_messages(request, addresses)
        calls = [
            mocker.call(
                request, f"{short_address(TEST_ADDRESS)} enqueued for processing!"
            ),
            mocker.call(
                request, f"{short_address(TEST_ADDRESS2)} enqueued for processing!"
            ),
        ]
        mocked_success.assert_has_calls(calls, any_order=True)
        assert mocked_success.call_count == 2

    # # check_export_status
    def test_core_helpers_check_export_status_functionality(self, mocker):
        url_value = TEST_ADDRESS
        mocked_export = mocker.patch("core.helpers.export_status")
        returned = check_export_status(url_value)
        assert returned == mocked_export.return_value
        mocked_export.assert_called_once_with(url_value)

    # # prepare_tax_context
    def test_core_helpers_prepare_tax_context_for_single_address(self, mocker):
        context = {}
        url_value = TEST_ADDRESS
        mocked_bundle = mocker.patch("core.helpers.check_bundle_addresses")
        returned = prepare_tax_context(context, url_value)
        assert returned == {"address": [TEST_ADDRESS], "url_value": TEST_ADDRESS}
        mocked_bundle.assert_not_called()

    def test_core_helpers_prepare_tax_context_for_bundle(self, mocker):
        context = {}
        url_value = TEST_BUNDLE
        mocked_bundle = mocker.patch(
            "core.helpers.check_bundle_addresses",
            return_value=f"{TEST_ADDRESS} {TEST_ADDRESS2}",
        )
        returned = prepare_tax_context(context, url_value)
        assert returned == {
            "bundle": [TEST_ADDRESS, TEST_ADDRESS2],
            "url_value": TEST_BUNDLE,
        }
        mocked_bundle.assert_called_once_with(url_value)

    # # reset_export
    def test_core_helpers_reset_export_functionality(self, mocker):
        mocked = mocker.patch("core.helpers._reset_export")
        returned = reset_export("foobar")
        assert returned == mocked.return_value
        mocked.assert_called_once_with("foobar")

    # # start_export
    def test_core_helpers_start_export_functionality(self, mocker):
        url_value = TEST_BUNDLE
        addresses = mocker.MagicMock()
        request = mocker.MagicMock()
        mocked_send = mocker.patch("core.helpers._send_enqueued_messages")
        mocked_start = mocker.patch("core.helpers._start_export")
        returned = start_export(url_value, addresses, request)
        assert returned == mocked_start.return_value
        mocked_send.assert_called_once_with(request, addresses)
        mocked_start.assert_called_once_with(url_value, addresses)


class TestCoreHelpersPublicBundlesFunctions:
    """Testing class for :py:mod:`core.helpers` public bundles' functions."""

    # # _check_public_bundles_eligibility
    def test_core_helpers_check_public_bundles_eligibility_for_no_bundlenames(
        self, mocker
    ):
        mocked_filter = mocker.patch(
            "core.helpers.BundleName.objects.filter", return_value=[]
        )
        returned = _check_public_bundles_eligibility()
        assert returned == []
        mocked_filter.assert_called_once_with(public=True)

    def test_core_helpers_check_public_bundles_eligibility_functionality(self, mocker):
        bundlename1, bundlename2, bundlename3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        bundlename1.is_eligible_public_bundlename.return_value = True
        bundlename2.is_eligible_public_bundlename.return_value = False
        bundlename3.is_eligible_public_bundlename.return_value = True
        mocked_filter = mocker.patch(
            "core.helpers.BundleName.objects.filter",
            return_value=[bundlename1, bundlename2, bundlename3],
        )
        returned = _check_public_bundles_eligibility()
        assert returned == [bundlename1, bundlename3]
        mocked_filter.assert_called_once_with(public=True)
        bundlename1.is_eligible_public_bundlename.assert_called_once_with()
        bundlename2.is_eligible_public_bundlename.assert_called_once_with()
        bundlename3.is_eligible_public_bundlename.assert_called_once_with()

    # # _create_public_bundle_files
    def test_core_helpers_create_public_bundle_files_functionality(self, mocker):
        hashes = ["bundle1_aaaaaaaaaa", "bundle2_bbbbbbbbbb", "bundle3_bbbbbbbbbb"]
        settings = mocker.MagicMock()
        with mock.patch.object(core.helpers, "settings", settings), mock.patch(
            "pathlib.Path.touch"
        ) as mocked_touch:
            settings.DATA_PATH = Path("foobar")
            _create_public_bundle_files(hashes)
            calls = [mocker.call()]
            mocked_touch.assert_has_calls(calls, any_order=True)
            assert mocked_touch.call_count == 3

    # # _delete_public_bundle_files
    def test_core_helpers_delete_public_bundle_files_functionality(self, mocker):
        hashes = ["bundle1_aaaaaaaaaa", "bundle2_bbbbbbbbbb", "bundle3_bbbbbbbbbb"]
        settings = mocker.MagicMock()
        with mock.patch.object(core.helpers, "settings", settings), mock.patch(
            "pathlib.Path.unlink"
        ) as mocked_touch:
            settings.DATA_PATH = Path("foobar")
            _delete_public_bundle_files(hashes)
            calls = [mocker.call()]
            mocked_touch.assert_has_calls(calls, any_order=True)
            assert mocked_touch.call_count == 3

    # # _public_bundle_filenames
    def test_core_helpers_public_bundle_filenames_functionality(self, mocker):
        glob = [
            Path("foobar") / "bundle1_aaaaaaaaaa",
            Path("foobar") / "bundle2_bbbbbbbbbb",
            Path("foobar") / "bundle4",
            Path("foobar") / "foobar",
            Path("foobar") / "bundle3_bbbbbbbbbb",
        ]
        settings = mocker.MagicMock()
        with mock.patch.object(core.helpers, "settings", settings), mock.patch(
            "pathlib.Path.glob", return_value=glob
        ) as mocked_glob:
            settings.DATA_PATH = Path("foobar")
            returned = _public_bundle_filenames()
            assert isinstance(returned, set)
            assert sorted(list(returned)) == [
                "bundle1_aaaaaaaaaa",
                "bundle2_bbbbbbbbbb",
                "bundle3_bbbbbbbbbb",
            ]
            mocked_glob.assert_called_once_with("*")

    # # _public_bundles_collection
    def test_core_helpers_public_bundles_collection_functionality(self, mocker):
        bundlename1, bundlename2, bundlename3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        bundlename1.name = "Name1"
        bundlename1.bundle = "bundle1"
        bundlename2.name = "name2"
        bundlename2.bundle = "bundle2"
        bundlename3.name = "Name3"
        bundlename3.bundle = "bundle3"
        mocked_check = mocker.patch(
            "core.helpers._check_public_bundles_eligibility",
            return_value=[bundlename1, bundlename2, bundlename3],
        )
        returned = _public_bundles_collection()
        assert returned == [
            ("name1_bundle1", bundlename1),
            ("name2_bundle2", bundlename2),
            ("name3_bundle3", bundlename3),
        ]
        mocked_check.assert_called_once_with()

    # # check_public_bundles
    def test_core_helpers_check_public_bundles_for_no_update(self, mocker):
        bundlename1, bundlename2, bundlename3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        bundlename1.name = "name1"
        bundlename1.bundle = "bundle1"
        bundlename2.name = "name2"
        bundlename2.bundle = "bundle2"
        bundlename3.name = "name3"
        bundlename3.bundle = "bundle3"
        mocked_collection = mocker.patch(
            "core.helpers._public_bundles_collection",
            return_value=[
                ("name1_bundle1", bundlename1),
                ("name2_bundle2", bundlename2),
                ("name3_bundle3", bundlename3),
            ],
        )
        mocked_filenames = mocker.patch(
            "core.helpers._public_bundle_filenames",
            return_value={"name1_bundle1", "name2_bundle2", "name3_bundle3"},
        )
        mocked_create = mocker.patch("core.helpers._create_public_bundle_files")
        mocked_delete = mocker.patch("core.helpers._delete_public_bundle_files")
        returned = check_public_bundles()
        assert returned == []
        mocked_collection.assert_called_once_with()
        mocked_filenames.assert_called_once_with()
        mocked_create.assert_not_called()
        mocked_delete.assert_not_called()

    def test_core_helpers_check_public_bundles_for_missing(self, mocker):
        bundlename1, bundlename2, bundlename3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        bundlename1.name = "name1"
        bundlename1.bundle = "bundle1"
        bundlename2.name = "name2"
        bundlename2.bundle = "bundle2"
        bundlename3.name = "name3"
        bundlename3.bundle = "bundle3"
        mocked_collection = mocker.patch(
            "core.helpers._public_bundles_collection",
            return_value=[
                ("name1_bundle1", bundlename1),
                ("name2_bundle2", bundlename2),
                ("name3_bundle3", bundlename3),
            ],
        )
        mocked_filenames = mocker.patch(
            "core.helpers._public_bundle_filenames",
            return_value={"name1_bundle1", "name3_bundle3"},
        )
        mocked_create = mocker.patch("core.helpers._create_public_bundle_files")
        mocked_delete = mocker.patch("core.helpers._delete_public_bundle_files")
        returned = check_public_bundles()
        assert returned == ["name2"]
        mocked_collection.assert_called_once_with()
        mocked_filenames.assert_called_once_with()
        mocked_create.assert_called_once_with({"name2_bundle2"})
        mocked_delete.assert_not_called()

    def test_core_helpers_check_public_bundles_for_obsolete(self, mocker):
        bundlename1, bundlename2, bundlename3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        bundlename1.name = "name1"
        bundlename1.bundle = "bundle1"
        bundlename2.name = "name2"
        bundlename2.bundle = "bundle2"
        bundlename3.name = "name3"
        bundlename3.bundle = "bundle3"
        mocked_collection = mocker.patch(
            "core.helpers._public_bundles_collection",
            return_value=[
                ("name1_bundle1", bundlename1),
                ("name2_bundle2", bundlename2),
            ],
        )
        mocked_filenames = mocker.patch(
            "core.helpers._public_bundle_filenames",
            return_value={"name1_bundle1", "name2_bundle2", "name3_bundle3"},
        )
        mocked_create = mocker.patch("core.helpers._create_public_bundle_files")
        mocked_delete = mocker.patch("core.helpers._delete_public_bundle_files")
        returned = check_public_bundles()
        assert returned == ["name3"]
        mocked_collection.assert_called_once_with()
        mocked_filenames.assert_called_once_with()
        mocked_delete.assert_called_once_with({"name3_bundle3"})
        mocked_create.assert_not_called()

    def test_core_helpers_check_public_bundles_functionality(self, mocker):
        bundlename1, bundlename2, bundlename3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        bundlename1.name = "name1"
        bundlename1.bundle = "bundle1"
        bundlename2.name = "name2"
        bundlename2.bundle = "bundle2"
        bundlename3.name = "name3"
        bundlename3.bundle = "bundle3"
        mocked_collection = mocker.patch(
            "core.helpers._public_bundles_collection",
            return_value=[
                ("name1_bundle1", bundlename1),
                ("name2_bundle2", bundlename2),
                ("name3_bundle3", bundlename3),
            ],
        )
        mocked_filenames = mocker.patch(
            "core.helpers._public_bundle_filenames",
            return_value={"name1_bundle1", "name4_bundle4"},
        )
        mocked_create = mocker.patch("core.helpers._create_public_bundle_files")
        mocked_delete = mocker.patch("core.helpers._delete_public_bundle_files")
        returned = check_public_bundles()
        assert sorted(returned) == ["name2", "name3", "name4"]
        mocked_collection.assert_called_once_with()
        mocked_filenames.assert_called_once_with()
        mocked_create.assert_called_once_with({"name2_bundle2", "name3_bundle3"})
        mocked_delete.assert_called_once_with({"name4_bundle4"})

    # # format_addresses_limit_help_text
    def test_core_helpers_format_addresses_limit_help_text_for_no_public(self, mocker):
        bundlename = mocker.MagicMock()
        limit = 10
        bundlename.profile.bundle_size_limit.return_value = limit
        bundlename.profile.bundle_size_limit_for_public.return_value = 0
        returned = format_addresses_limit_help_text(bundlename)
        assert (
            returned
            == BUNDLE_ADDRESSES_LIMIT_HELP_TEXT.format(limit)
            + PUBLIC_BUNDLE_ADDRESSES_NOT_ALLOWED_HELP_TEXT
        )
        bundlename.profile.bundle_size_limit.assert_called_once_with(bundlename)
        bundlename.profile.bundle_size_limit_for_public.assert_called_once_with()

    def test_core_helpers_format_addresses_limit_help_text_functionality(self, mocker):
        bundlename = mocker.MagicMock()
        limit = 15
        bundlename.profile.bundle_size_limit.return_value = limit
        limit_public = 10
        bundlename.profile.bundle_size_limit_for_public.return_value = limit_public
        returned = format_addresses_limit_help_text(bundlename)
        assert returned == BUNDLE_ADDRESSES_LIMIT_HELP_TEXT.format(
            limit
        ) + PUBLIC_BUNDLE_ADDRESSES_LIMIT_HELP_TEXT.format(limit_public)
        bundlename.profile.bundle_size_limit.assert_called_once_with(bundlename)
        bundlename.profile.bundle_size_limit_for_public.assert_called_once_with()
