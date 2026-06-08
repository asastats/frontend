"""Testing module for :py:mod:`utils.userhelpers` module."""

import base64
import time
from datetime import UTC, datetime
from unittest import mock

import pytest
from algosdk.error import AlgodHTTPError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from permissiondapp.dapp.config import (
    SUBTOPIA_ASASTATSER_APP_ID,
    SUBTOPIA_CLUSTER_APP_ID,
    SUBTOPIA_INTRO_APP_ID,
    SUBTOPIA_PROFESSIONAL_APP_ID,
    SUBTOPIA_URL_PREFIX,
)

from core.models import Profile
from utils.constants.users import (
    ADDRESS_AND_ALGO_NAME_URL_PATH_ERROR,
    ADMPOOL_ADDRESS,
    ADMPOOL_AUTHORIZATION_MIN_ROUND,
    PERMISSION_APP_ID,
)
from utils.tests.fixtures import TEST_ADDRESS2
from utils.userhelpers import (
    _docs_positions_offset_and_length_pairs,
    _extract_uint,
    _format_days_diff_message,
    _format_tier_name_as_link,
    _starting_positions_offset_and_length_pairs,
    _values_offset_and_length_pairs,
    address_votes_and_permission_from_permission_dapp,
    box_name_from_address,
    check_authorization_transaction,
    decode_unique_hash,
    delete_deactivated,
    deserialize_values_data,
    deserialized_permission_dapp_box_value,
    formatted_subscription_timestamps,
    is_system_reserved_url_path,
    slugified_bundle_name,
    truncated_timestamp_and_address,
    unique_hash_from_number,
    user_display,
    validate_address_or_algo_name_url_path,
)


# # SUBSCRIPTIONS
class TestUserHelpersSUBSCRIPTIONSFunctions:
    """Testing class for :py:mod:`utils.userhelpers` subscriptions functions."""

    # # _format_days_diff_message
    @pytest.mark.parametrize(
        "date,result",
        [
            (datetime(2025, 1, 18, 0, 0, 0), "expires in 8 days"),
            (datetime(2025, 2, 9, 0, 0, 0), "expires in 30 days"),
            (datetime(2025, 1, 10, 0, 0, 0), "expires in 0 days"),
            (datetime(2025, 1, 9, 0, 0, 0), "EXPIRED"),
            (datetime(2024, 2, 10, 0, 0, 0), "EXPIRED"),
        ],
    )
    def test_utils_userhelpers_format_days_diff_message_functionality(
        self, date, result, mocker
    ):
        timestamp = mocker.MagicMock()
        with mock.patch("utils.userhelpers.datetime") as mocked_datetime:
            mocked_datetime.now.return_value = datetime(2025, 1, 10, 0, 0, 0)
            mocked_datetime.fromtimestamp.return_value = date
            returned = _format_days_diff_message(timestamp)
            assert returned == result
            mocked_datetime.now.assert_called_once()
            mocked_datetime.now.assert_called_with(UTC)
            mocked_datetime.fromtimestamp.assert_called_once()
            mocked_datetime.fromtimestamp.assert_called_with(timestamp, UTC)

    # # _format_tier_name_as_link
    @pytest.mark.parametrize(
        "tier_name,app_id",
        [
            ("Intro", SUBTOPIA_INTRO_APP_ID),
            ("Asastatser", SUBTOPIA_ASASTATSER_APP_ID),
            ("Professional", SUBTOPIA_PROFESSIONAL_APP_ID),
            ("Cluster", SUBTOPIA_CLUSTER_APP_ID),
        ],
    )
    def test_utils_userhelper_format_tier_name_as_link_functionality(
        self, tier_name, app_id
    ):
        returned = _format_tier_name_as_link(tier_name)
        assert returned == (
            f'<a href="{SUBTOPIA_URL_PREFIX}{app_id}" target="_blank" rel="noopener" '
            f'title="Open Subtopia.io subscription tier page">{tier_name} tier</a>'
        )

    # # formatted_subscription_timestamps
    def test_utils_userhelper_formatted_subscription_timestamps_functionality(
        self, mocker
    ):
        timestamp1, timestamp2, timestamp3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        subscriptions = {
            "Intro": timestamp1,
            "Professional": timestamp2,
            "Cluster": timestamp3,
        }
        with mock.patch("utils.userhelpers.datetime") as mocked_datetime:
            mocked_datetime.now.return_value = datetime(2025, 1, 10, 0, 0, 0)
            mocked_datetime.fromtimestamp.side_effect = [
                datetime(2025, 1, 15, 0, 0, 0),
                datetime(2025, 1, 1, 0, 0, 0),
                datetime(2025, 1, 10, 0, 0, 0),
            ]
            returned = formatted_subscription_timestamps(subscriptions)
            assert returned == {
                f'<a href="{SUBTOPIA_URL_PREFIX}{SUBTOPIA_INTRO_APP_ID}" target="_blank" rel="noopener" '
                f'title="Open Subtopia.io subscription tier page">Intro tier</a>': "expires in 5 days",
                f'<a href="{SUBTOPIA_URL_PREFIX}{SUBTOPIA_PROFESSIONAL_APP_ID}" target="_blank" rel="noopener" '
                f'title="Open Subtopia.io subscription tier page">Professional tier</a>': "EXPIRED",
                f'<a href="{SUBTOPIA_URL_PREFIX}{SUBTOPIA_CLUSTER_APP_ID}" target="_blank" rel="noopener" '
                f'title="Open Subtopia.io subscription tier page">Cluster tier</a>': "expires in 0 days",
            }


def _valid_boxes_values_and_data():
    return [
        (
            [1, 2, 3, 4, 5, 6],
            "AAAAAAAAAAEAAAAAAAAAAgAAAAAAAAADAAAAAAAAAAQAAAAAAAAABQAAAAAAAAAG",
        ),
        (
            [100, 200, 300, 400, 500, 600],
            "AAAAAAAAAGQAAAAAAAAAyAAAAAAAAAEsAAAAAAAAAZAAAAAAAAAB9AAAAAAAAAJY",
        ),
        (
            [
                10000000000,
                1000000000000,
                0,
                0,
                0,
                0,
                1000000000000,
                1,
            ],
            (
                "AAAAAlQL5AAAAADo1KUQAAAAAAAAAAAAAAAAAA"
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA6NSlEAAB"
            ),
        ),
        (
            [100, 200, 300, 400, 500, 600, 700, 5, 800, 6, 900, 7, 1000, 8],
            "AAAAAAAAAGQAAAAAAAAAyAAAAAAAAAEsAAAAAAAAAZAAAAAAAAAB9"
            "AAAAAAAAAJYAAAAAAAAArwFAAAAAAAAAyAGAAAAAAAAA4QHAAAAAAAAA+gI",
        ),
        (
            [
                10000000,
                200000000,
                0,
                0,
                2000500,
                2055200,
                1000,
                1,
                1100,
                2,
                1200,
                3,
                1300,
                4,
                1400,
                5,
                1500,
                6,
                1600,
                7,
                1700,
                8,
                1800,
                9,
                1900,
                10,
                2000,
                11,
                2010,
                12,
            ],
            "AAAAAACYloAAAAAAC+vCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB6GdAAAAAAAH1wgAAAAAAA"
            "AA+gBAAAAAAAABEwCAAAAAAAABLADAAAAAAAABRQEAAAAAAAABXgFAAAAAAAABdwGAAAAAA"
            "AABkAHAAAAAAAABqQIAAAAAAAABwgJAAAAAAAAB2wKAAAAAAAAB9ALAAAAAAAAB9oM",
        ),
    ]


# # VALUES
class TestUserHelpersValuesFunctions:
    """Testing class for :py:mod:`utils.userhelpers` values functions."""

    # # _docs_positions_offset_and_length_pairs
    @pytest.mark.parametrize(
        "size,result",
        [
            (0, []),
            (9, [(48, 8), (56, 1)]),
            (18, [(48, 8), (56, 1), (57, 8), (65, 1)]),
            (27, [(48, 8), (56, 1), (57, 8), (65, 1), (66, 8), (74, 1)]),
            (
                36,
                [
                    (48, 8),
                    (56, 1),
                    (57, 8),
                    (65, 1),
                    (66, 8),
                    (74, 1),
                    (75, 8),
                    (83, 1),
                ],
            ),
            (
                108,
                [
                    (48, 8),
                    (56, 1),
                    (57, 8),
                    (65, 1),
                    (66, 8),
                    (74, 1),
                    (75, 8),
                    (83, 1),
                    (84, 8),
                    (92, 1),
                    (93, 8),
                    (101, 1),
                    (102, 8),
                    (110, 1),
                    (111, 8),
                    (119, 1),
                    (120, 8),
                    (128, 1),
                    (129, 8),
                    (137, 1),
                    (138, 8),
                    (146, 1),
                    (147, 8),
                    (155, 1),
                ],
            ),
        ],
    )
    def test_utils_userhelpers_docs_positions_offset_and_length_pairs_functionality(
        self, size, result
    ):
        returned = _docs_positions_offset_and_length_pairs(size)
        assert returned == result

    # # _extract_uint
    @pytest.mark.parametrize(
        "index,length,result",
        [
            (0, 8, 10000000),
            (8, 8, 200000000),
            (16, 8, 0),
            (24, 8, 0),
            (32, 8, 2000500),
            (40, 8, 2055200),
            (48, 8, 1000),
            (56, 1, 1),
            (57, 8, 1100),
            (65, 1, 2),
            (66, 8, 1200),
            (74, 1, 3),
            (75, 8, 1300),
            (83, 1, 4),
            (84, 8, 1400),
            (92, 1, 5),
            (93, 8, 1500),
            (101, 1, 6),
            (102, 8, 1600),
            (110, 1, 7),
            (111, 8, 1700),
            (119, 1, 8),
            (120, 8, 1800),
            (128, 1, 9),
            (129, 8, 1900),
            (137, 1, 10),
            (138, 8, 2000),
            (146, 1, 11),
            (147, 8, 2010),
            (155, 1, 12),
        ],
    )
    def test_utils_userhelpers_extract_uint_functionality(self, index, length, result):
        data = (
            "AAAAAACYloAAAAAAC+vCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB6GdAAAAAAAH1wgAAAAAAA"
            "AA+gBAAAAAAAABEwCAAAAAAAABLADAAAAAAAABRQEAAAAAAAABXgFAAAAAAAABdwGAAAAAA"
            "AABkAHAAAAAAAABqQIAAAAAAAABwgJAAAAAAAAB2wKAAAAAAAAB9ALAAAAAAAAB9oM"
        )
        returned = _extract_uint(base64.b64decode(data), index, length)
        assert returned == result

    # # _starting_positions_offset_and_length_pairs
    def test_utils_userhelpers_starting_positions_offset_and_length_pairs_functionality(
        self,
    ):
        returned = _starting_positions_offset_and_length_pairs()
        assert returned == [
            (0, 8),
            (8, 8),
            (16, 8),
            (24, 8),
            (32, 8),
            (40, 8),
        ]

    # # _values_offset_and_length_pairs
    def test_utils_userhelpers_values_offset_and_length_pairs_functionality(
        self, mocker
    ):
        docs_data_size = mocker.MagicMock()
        starting = [(0, 8), (8, 1)]
        docs = [(48, 8), (56, 1)]
        mocked_starting = mocker.patch(
            "utils.userhelpers._starting_positions_offset_and_length_pairs",
            return_value=starting,
        )
        mocked_docs = mocker.patch(
            "utils.userhelpers._docs_positions_offset_and_length_pairs",
            return_value=docs,
        )
        returned = _values_offset_and_length_pairs(docs_data_size)
        assert returned == starting + docs
        mocked_starting.assert_called_once()
        mocked_starting.assert_called_with()
        mocked_docs.assert_called_once()
        mocked_docs.assert_called_with(docs_data_size)

    # # deserialize_values_data
    @pytest.mark.parametrize("values,data", _valid_boxes_values_and_data())
    def test_utils_userhelpers_deserialize_values_data_functionality(
        self, values, data
    ):
        returned = deserialize_values_data(data)
        assert returned == values

    # # deserialized_permission_dapp_box_value
    def test_utils_userhelpers_deserialized_permission_dapp_box_value_for_error(
        self, mocker
    ):
        client, app_id, box_name = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        client.application_box_by_name.side_effect = AlgodHTTPError("")
        mocked_deserialize = mocker.patch("utils.userhelpers.deserialize_values_data")
        returned = deserialized_permission_dapp_box_value(client, app_id, box_name)
        assert returned is None
        client.application_box_by_name.assert_called_once()
        client.application_box_by_name.assert_called_with(app_id, box_name)
        mocked_deserialize.assert_not_called()

    def test_utils_userhelpers_deserialized_permission_dapp_box_value_functionality(
        self, mocker
    ):
        client, app_id, box_name = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        mocked_deserialize = mocker.patch("utils.userhelpers.deserialize_values_data")
        response = {
            "value": (
                "QUFBQUFBQUtRMVFBQUFDbEY5a3luQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFB"
                "QUMyUElaYmNRQUFBQWg5K29ySkFBQUFsUUw1QUFBQkFBQUFCNWJscDlQSg=="
            )
        }
        client.application_box_by_name.return_value = response
        returned = deserialized_permission_dapp_box_value(client, app_id, box_name)
        assert returned == mocked_deserialize.return_value
        client.application_box_by_name.assert_called_once()
        client.application_box_by_name.assert_called_with(app_id, box_name)
        mocked_deserialize.assert_called_once()
        mocked_deserialize.assert_called_with(
            base64.b64decode(response.get("value")).decode("utf8")
        )


class TestUtilsUserHelpersFunctions:
    """Testing class for :py:mod:`utils.userhelpers` functions."""

    # # address_votes_and_permission_from_permission_dapp
    def test_utils_userhelpers_address_votes_and_permission_from_permission_dapp_no_box(
        self, mocker
    ):
        algod_client = mocker.MagicMock()
        address = TEST_ADDRESS2
        mocked_client = mocker.patch(
            "utils.userhelpers.algod_instance", return_value=algod_client
        )
        mocked_deserialized = mocker.patch(
            "utils.userhelpers.deserialized_permission_dapp_box_value",
            return_value=None,
        )
        returned = address_votes_and_permission_from_permission_dapp(address)
        assert returned == (0, 0)
        mocked_client.assert_called_once()
        mocked_client.assert_called_with()
        mocked_deserialized.assert_called_once()
        mocked_deserialized.assert_called_with(
            algod_client,
            PERMISSION_APP_ID,
            (
                b"\xd1*l\xf0&t\x97\xb4\xfb\x94\xc0\xc9\xa0\xd0"
                b"\xd3l\xc3\x9c\xe5h\xef+HA\xb9\xca\xf0!\xb8k\xc6\xf7"
            ),
        )

    def test_utils_userhelpers_address_votes_and_permission_from_permission_function(
        self, mocker
    ):
        algod_client = mocker.MagicMock()
        address = TEST_ADDRESS2
        mocked_client = mocker.patch(
            "utils.userhelpers.algod_instance", return_value=algod_client
        )
        mocked_deserialized = mocker.patch(
            "utils.userhelpers.deserialized_permission_dapp_box_value",
            return_value=[1, 2, 3, 4, 5, 6, 7, 8, 9],
        )
        returned = address_votes_and_permission_from_permission_dapp(address)
        assert returned == [1, 2]
        mocked_client.assert_called_once()
        mocked_client.assert_called_with()
        mocked_deserialized.assert_called_once()
        mocked_deserialized.assert_called_with(
            algod_client,
            PERMISSION_APP_ID,
            (
                b"\xd1*l\xf0&t\x97\xb4\xfb\x94\xc0\xc9\xa0\xd0"
                b"\xd3l\xc3\x9c\xe5h\xef+HA\xb9\xca\xf0!\xb8k\xc6\xf7"
            ),
        )

    # # box_name_from_address
    @pytest.mark.parametrize(
        "address,box_name",
        [
            (
                "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU",
                (
                    b"\xd1*l\xf0&t\x97\xb4\xfb\x94\xc0\xc9\xa0\xd0"
                    b"\xd3l\xc3\x9c\xe5h\xef+HA\xb9\xca\xf0!\xb8k\xc6\xf7"
                ),
            ),
            (
                "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU",
                (
                    b"\xad\xbb\xd5gm/\x0c7Y\x1fC\xec\xb3de\xb3oeJ#"
                    b"\xeb\xc98\xac`\x0ekN\xdd\xea\x8aS"
                ),
            ),
            (
                "LXJ3Q6RZ2TJ6VCJDFMSM4ZVNYYYE4KVSL3N2TYR23PLNCJCIXBM3NYTBYE",
                (
                    b"]\xd3\xb8z9\xd4\xd3\xea\x89#+$\xcef\xad\xc60N*"
                    b"\xb2^\xdb\xa9\xe2:\xdb\xd6\xd1$H\xb8Y"
                ),
            ),
            (
                "VKENBO5W2DZAZFQR45SOQO6IMWS5UMVZCHLPEACNOII7BDJTGBZKSEL4Y4",
                (
                    b"\xaa\x88\xd0\xbb\xb6\xd0\xf2\x0c\x96\x11\xe7d"
                    b"\xe8;\xc8e\xa5\xda2\xb9\x11\xd6\xf2\x00Mr\x11\xf0\x8d30r"
                ),
            ),
        ],
    )
    def test_userhelpers_box_name_from_address_functionality(self, address, box_name):
        returned = box_name_from_address(address)
        assert returned == box_name

    # # check_authorization_transaction
    def test_utils_userhelpers_check_authorization_transaction_for_no_transaction(
        self, mocker
    ):
        profile = mocker.MagicMock()
        address = "address"
        profile.address = address
        indexer_client = mocker.MagicMock()
        mocked_client = mocker.patch(
            "utils.userhelpers.indexer_instance", return_value=indexer_client
        )
        note = "note"
        profile.address_authorization_note.return_value = note
        params = {
            "txn_type": "pay",
            "min_round": ADMPOOL_AUTHORIZATION_MIN_ROUND,
            "address": ADMPOOL_ADDRESS,
            "address_role": "receiver",
        }
        next_token1, next_token2 = "next_token1", "next_token2"
        txns1 = {
            "transactions": [
                {
                    "sender": "address1",
                },
                {
                    "sender": "address2",
                },
            ],
            "next-token": next_token1,
        }
        txns2 = {
            "transactions": [
                {
                    "sender": "address3",
                },
                {
                    "sender": "address4",
                },
            ],
            "next-token": next_token2,
        }
        mocked_search = mocker.patch(
            "utils.userhelpers.search_transactions",
            side_effect=[txns1, txns2, {}],
        )
        returned = check_authorization_transaction(profile)
        assert returned == ""
        mocked_client.assert_called_once()
        mocked_client.assert_called_with()
        profile.address_authorization_note.assert_called_once()
        profile.address_authorization_note.assert_called_with()
        calls = [
            mocker.call(params, indexer_client, delay=0.05),
            mocker.call(params, indexer_client, next_page=next_token1, delay=0.05),
            mocker.call(params, indexer_client, next_page=next_token2, delay=0.05),
        ]
        mocked_search.assert_has_calls(calls, any_order=True)
        assert mocked_search.call_count == 3

    def test_utils_userhelpers_check_authorization_transaction_for_no_note(
        self, mocker
    ):
        profile = mocker.MagicMock()
        address = "address"
        profile.address = address
        indexer_client = mocker.MagicMock()
        mocked_client = mocker.patch(
            "utils.userhelpers.indexer_instance", return_value=indexer_client
        )
        note = "note"
        profile.address_authorization_note.return_value = note
        params = {
            "txn_type": "pay",
            "min_round": ADMPOOL_AUTHORIZATION_MIN_ROUND,
            "address": ADMPOOL_ADDRESS,
            "address_role": "receiver",
        }
        next_token1, next_token2 = "next_token1", "next_token2"
        txns1 = {
            "transactions": [
                {
                    "sender": address,
                },
                {
                    "sender": "address2",
                },
            ],
            "next-token": next_token1,
        }
        txns2 = {
            "transactions": [
                {
                    "sender": "address3",
                },
                {"sender": address, "note": "dGV4dA=="},
            ],
            "next-token": next_token2,
        }
        mocked_search = mocker.patch(
            "utils.userhelpers.search_transactions",
            side_effect=[txns1, txns2, {}],
        )
        returned = check_authorization_transaction(profile)
        assert returned == ""
        mocked_client.assert_called_once()
        mocked_client.assert_called_with()
        profile.address_authorization_note.assert_called_once()
        profile.address_authorization_note.assert_called_with()
        calls = [
            mocker.call(params, indexer_client, delay=0.05),
            mocker.call(params, indexer_client, next_page=next_token1, delay=0.05),
            mocker.call(params, indexer_client, next_page=next_token2, delay=0.05),
        ]
        mocked_search.assert_has_calls(calls, any_order=True)
        assert mocked_search.call_count == 3

    def test_utils_userhelpers_check_authorization_transaction_uppercase(self, mocker):
        profile = mocker.MagicMock()
        address = "address"
        profile.address = address
        indexer_client = mocker.MagicMock()
        mocked_client = mocker.patch(
            "utils.userhelpers.indexer_instance", return_value=indexer_client
        )
        note = "note"
        profile.address_authorization_note.return_value = note
        params = {
            "txn_type": "pay",
            "min_round": ADMPOOL_AUTHORIZATION_MIN_ROUND,
            "address": ADMPOOL_ADDRESS,
            "address_role": "receiver",
        }
        next_token1, next_token2 = "next_token1", "next_token2"
        transaction_id = "transaction_id"
        txns1 = {
            "transactions": [
                {
                    "sender": address,
                },
                {
                    "sender": "address2",
                },
            ],
            "next-token": next_token1,
        }
        txns2 = {
            "transactions": [
                {
                    "sender": "address3",
                },
                {"sender": address, "note": "Tk9URQ==", "id": transaction_id},
            ],
            "next-token": next_token2,
        }
        mocked_search = mocker.patch(
            "utils.userhelpers.search_transactions",
            side_effect=[txns1, txns2, {}],
        )
        returned = check_authorization_transaction(profile)
        assert returned == transaction_id
        mocked_client.assert_called_once()
        mocked_client.assert_called_with()
        profile.address_authorization_note.assert_called_once()
        profile.address_authorization_note.assert_called_with()
        calls = [
            mocker.call(params, indexer_client, delay=0.05),
            mocker.call(params, indexer_client, next_page=next_token1, delay=0.05),
        ]
        mocked_search.assert_has_calls(calls, any_order=True)
        assert mocked_search.call_count == 2

    def test_utils_userhelpers_check_authorization_transaction_lowercase(self, mocker):
        profile = mocker.MagicMock()
        address = "address"
        profile.address = address
        indexer_client = mocker.MagicMock()
        mocked_client = mocker.patch(
            "utils.userhelpers.indexer_instance", return_value=indexer_client
        )
        note = "note"
        profile.address_authorization_note.return_value = note
        params = {
            "txn_type": "pay",
            "min_round": ADMPOOL_AUTHORIZATION_MIN_ROUND,
            "address": ADMPOOL_ADDRESS,
            "address_role": "receiver",
        }
        next_token1, next_token2 = "next_token1", "next_token2"
        transaction_id = "transaction_id"
        txns1 = {
            "transactions": [
                {
                    "sender": address,
                },
                {
                    "sender": "address2",
                },
            ],
            "next-token": next_token1,
        }
        txns2 = {
            "transactions": [
                {
                    "sender": "address3",
                },
                {"sender": address, "note": "bm90ZQ==", "id": transaction_id},
            ],
            "next-token": next_token2,
        }
        mocked_search = mocker.patch(
            "utils.userhelpers.search_transactions",
            side_effect=[txns1, txns2, {}],
        )
        returned = check_authorization_transaction(profile)
        assert returned == transaction_id
        mocked_client.assert_called_once()
        mocked_client.assert_called_with()
        profile.address_authorization_note.assert_called_once()
        profile.address_authorization_note.assert_called_with()
        calls = [
            mocker.call(params, indexer_client, delay=0.05),
            mocker.call(params, indexer_client, next_page=next_token1, delay=0.05),
        ]
        mocked_search.assert_has_calls(calls, any_order=True)
        assert mocked_search.call_count == 2

    # # decode_unique_hash
    def test_utils_userhelpers_decode_unique_hash_returns_0_for_wrong_uid(self):
        assert decode_unique_hash("bla") == 0

    # # slugified_bundle_name
    def test_utils_userhelpers_slugified_bundle_name_strips_non_ascii(self):
        assert slugified_bundle_name("Tëst Name") == "Test-Name"

    def test_utils_userhelpers_slugified_bundle_name_for_allow_unicode(self):
        assert slugified_bundle_name("Café Münch", allow_unicode=True) == "Café-Münch"

    # # truncated_timestamp_and_address
    def test_utils_userhelpers_truncated_timestamp_and_address_functionality(self):
        timestamp = 1734863388.859522
        address = TEST_ADDRESS2
        returned = truncated_timestamp_and_address(timestamp, address)
        assert returned == 251162

    # # unique_hash_from_number
    def test_utils_userhelpers_create_uid_returns_original_number(self):
        number = 1388358497
        uid = unique_hash_from_number(number)
        assert decode_unique_hash(uid) == number

    def test_utils_userhelpers_unique_hash_from_number_length_not_greater_than_8(self):
        number = 1388358495
        note = unique_hash_from_number(number)
        assert len(note) in range(7, 9)

    # # delete_deactivated
    @pytest.mark.django_db
    def test_utils_delete_deactivated_deletes_nothing_for_no_inactive_users(self):
        get_user_model().objects.create(email="permission1@subscribed.com")
        count = delete_deactivated()
        assert count == 0

    @pytest.mark.django_db
    def test_utils_delete_deactivated_functionality(self):
        get_user_model().objects.create(
            username="{}deleted.com".format(time.time()), is_active=False
        )
        get_user_model().objects.create(
            username="{}nondeleted.com".format(time.time()),
        )
        get_user_model().objects.create(
            username="{}deleted.com".format(time.time()), is_active=False
        )
        assert Profile.objects.all().count() == 3
        count = delete_deactivated()
        assert count == 2
        assert get_user_model().objects.all().count() == 1
        assert Profile.objects.all().count() == 1

    # # is_system_reserved_url_path
    @pytest.mark.parametrize(
        "url_path",
        ["api", "profile", "about", "subscriptions", "reddit24.png", "logo.png"],
    )
    def test_utils_userhelpers_is_system_reserved_url_path_for_true(self, url_path):
        assert is_system_reserved_url_path(url_path) is True

    @pytest.mark.parametrize(
        "url_path",
        [
            "api.1",
            "profile-address",
            "about-me",
            "subscription",
            "name",
            "reddit24",
            "logo",
        ],
    )
    def test_utils_userhelpers_is_system_reserved_url_path_for_false(self, url_path):
        assert is_system_reserved_url_path(url_path) is False

    # # user_display
    def test_utils_userhelpers_user_display_calls_and_returns_profile_name(
        self, mocker
    ):
        user = mocker.MagicMock()
        returned = user_display(user)
        assert returned == user.profile.name

    # validate_address_or_algo_name_url_path
    def test_utils_userhelpers_validate_address_or_algo_name_url_path_raises(
        self, mocker
    ):
        url_path = "name.algo"
        mocked_check = mocker.patch(
            "utils.userhelpers.check_algorand_address", return_value="addresses"
        )
        with pytest.raises(ValidationError) as exception:
            validate_address_or_algo_name_url_path(url_path)
        assert str(exception.value) == f"['{ADDRESS_AND_ALGO_NAME_URL_PATH_ERROR}']"
        mocked_check.assert_called_once()
        mocked_check.assert_called_with(url_path)

    def test_utils_userhelpers_validate_address_or_algo_name_url_path_functionality(
        self, mocker
    ):
        url_path = "some-name"
        mocked_check = mocker.patch(
            "utils.userhelpers.check_algorand_address", return_value=""
        )
        validate_address_or_algo_name_url_path(url_path)
        mocked_check.assert_called_once()
        mocked_check.assert_called_with(url_path)
