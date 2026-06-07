"""Testing module for :py:mod:`nameservice.nfd` module."""

from copy import deepcopy
from urllib.error import HTTPError

import pytest

from nameservice.nfd import (
    _address_from_bytes_value,
    _addresses_from_app_state,
    _app_id_from_logicsig,
    _app_state_for_algo_name,
    _app_state_from_box,
    _append_addresses_from_global_state_for_key,
    _box_name_for_algo_name,
    _check_boxes_addresses,
    _logicsig_from_name,
    _variant_buffer,
    check_name,
    nfd_app_id_from_algo_name,
)
from utils.constants.core import ALGOD_EXCEPTIONS
from utils.constants.nameservice import NFD_APP_ID
from utils.tests.fixtures import (
    TESTING_NFD_ADDRESS,
    TESTING_NFD_ADDRESS_STATE,
    TESTING_NFD_LOCAL_STATES,
    TESTING_NFD_NAME_BYTECODES,
)


class TestNameServiceNfdV1Functions:
    """Testing class for :py:mod:`nameservice.nfd` V1 functions."""

    # # _app_id_from_logicsig
    @pytest.mark.parametrize(
        "app_id,state",
        [(key, val) for key, val in TESTING_NFD_LOCAL_STATES.items()],
    )
    def test_nameservice_nfd_app_id_from_logicsig_returns_app_id(
        self, app_id, state, mocker
    ):
        logic_sig, algod_client = mocker.MagicMock(), mocker.MagicMock()
        algod_client.account_info.return_value = {"apps-local-state": state}
        returned = _app_id_from_logicsig(logic_sig, algod_client)
        assert returned == app_id
        algod_client.account_info.assert_called_once()
        algod_client.account_info.assert_called_with(logic_sig.address.return_value)

    # # _logicsig_from_name
    @pytest.mark.parametrize(
        "name,bytecode",
        [(key, val) for key, val in TESTING_NFD_NAME_BYTECODES.items()],
    )
    def test_nameservice_nfd_logicsig_from_name_returns_logicsigaccount(
        self, name, bytecode, mocker
    ):
        mocked = mocker.patch("nameservice.nfd.LogicSigAccount")
        returned = _logicsig_from_name("name/", name, NFD_APP_ID)
        assert returned == mocked.return_value
        mocked.assert_called_once()
        mocked.assert_called_with(bytecode)

    # # _logicsig_from_name
    @pytest.mark.parametrize(
        "number,buf",
        [
            (1, [1]),
            (3, [3]),
            (1500, [220, 11]),
            (5000003, [195, 150, 177, 2]),
        ],
    )
    def test_nameservice_nfd_variant_buffer_returns_list_buffer(self, number, buf):
        assert _variant_buffer(number) == buf


class TestNameServiceNfdV2Functions:
    """Testing class for :py:mod:`nameservice.nfd` V2 functions."""

    # # _check_boxes_addresses
    def test_nameservice_nfd_check_boxes_addresses_for_no_boxes(self, mocker):
        algod_client = mocker.MagicMock()
        v2_app_id = 88778506
        algod_client.application_boxes.return_value = {}
        returned = _check_boxes_addresses(v2_app_id, algod_client)
        assert returned == []
        algod_client.application_boxes.assert_called_once()
        algod_client.application_boxes.assert_called_with(v2_app_id)

    def test_nameservice_nfd_check_boxes_addresses_for_no_related_box(self, mocker):
        algod_client = mocker.MagicMock()
        v2_app_id = 88778506
        box = {"name": "dS5iYW5uZXI="}
        algod_client.application_boxes.return_value = {"boxes": [box]}
        returned = _check_boxes_addresses(v2_app_id, algod_client)
        assert returned == []
        algod_client.application_boxes.assert_called_once()
        algod_client.application_boxes.assert_called_with(v2_app_id)

    @pytest.mark.parametrize(
        "exception",
        [
            exception("", "", "", "", "") if exception == HTTPError else exception("")
            for exception in ALGOD_EXCEPTIONS
        ],
    )
    def test_nameservice_nfd_check_boxes_addresses_for_exception(
        self, exception, mocker
    ):
        algod_client = mocker.MagicMock()
        v2_app_id = 88778506
        box = {"name": "di5jYUFsZ28uMC5hcw=="}
        algod_client.application_boxes.return_value = {"boxes": [box]}
        algod_client.application_box_by_name.side_effect = exception
        returned = _check_boxes_addresses(v2_app_id, algod_client)
        assert returned == []
        algod_client.application_boxes.assert_called_once()
        algod_client.application_boxes.assert_called_with(v2_app_id)
        algod_client.application_box_by_name.assert_called_once()
        algod_client.application_box_by_name.assert_called_with(
            v2_app_id, b"v.caAlgo.0.as"
        )

    def test_nameservice_nfd_check_boxes_addresses_functionality(self, mocker):
        algod_client = mocker.MagicMock()
        v2_app_id = 88778506
        box1 = {"name": "di5jYUFsZ28uMC5hcw=="}
        box2 = {"name": "dS5iYW5uZXI="}
        box3 = {"name": "dS5jYWFsZ28="}
        box4 = {"name": "di5jYUFsZ28uMC5hcw=="}
        box5 = {"name": "di5jYUFsZ28uMC5hcw=="}
        box6 = {"name": "di5jYUFsZ28uMC5hcw=="}
        algod_client.application_boxes.return_value = {
            "boxes": [box1, box2, box3, box4, box5, box6]
        }
        response1 = {"value": "pqqulym8wk2D/ek6PwU1hGVaZBtdGebNpdoLpC9/8y0="}
        response2 = {
            "value": (
                "VFpHWVhaNk9HNUFFRjdESDVERkgyQTY1UkgzQ1ZV"
                "Tk9KTjM2RDI3TUo1WVdWNlpDNjdEWDRIRENJTQ=="
            )
        }
        response3 = {"value": ""}
        response4 = {
            "value": (
                "pqqulym8wk2D/ek6PwU1hGVaZBtdGebNpdoLpC9/8y2M"
                "q6wI9wfZYxZ33bCPzqYEu27c/WfzCt3vjD42zbbfnQ=="
            )
        }
        response5 = {
            "value": (
                "0tcLeFUBnInbmPQkmS/drsIOnI2KOQfZt8wOqj3rtbYA"
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
            )
        }
        algod_client.application_box_by_name.side_effect = [
            response1,
            response2,
            response3,
            response4,
            response5,
        ]
        returned = _check_boxes_addresses(v2_app_id, algod_client)
        assert sorted(returned) == sorted(
            list(
                {
                    "2LLQW6CVAGOITW4Y6QSJSL65V3BA5HENRI4QPWNXZQHKUPPLWW3FU23X5I",
                    "RSV2YCHXA7MWGFTX3WYI7TVGAS5W5XH5M7ZQVXPPRQ7DNTNW36OW2TRR6I",
                    "TZGYXZ6OG5AEF7DH5DFH2A65RH3CVUNOJN36D27MJ5YWV6ZC67DX4HDCIM",
                    "U2VK5FZJXTBE3A755E5D6BJVQRSVUZA3LUM6NTNF3IF2IL376MWTGMNPFA",
                }
            )
        )
        algod_client.application_boxes.assert_called_once()
        algod_client.application_boxes.assert_called_with(v2_app_id)
        calls = [
            mocker.call(v2_app_id, b"v.caAlgo.0.as"),
        ]
        algod_client.application_box_by_name.assert_has_calls(calls, any_order=True)
        assert algod_client.application_box_by_name.call_count == 5

    # # _app_state_from_box
    @pytest.mark.parametrize("v2_app_id", [0, None, False])
    def test_nameservice_nfd_app_state_from_box_returns_empty_list_for_no_app(
        self, v2_app_id, mocker
    ):
        algod_client = mocker.MagicMock()
        returned = _app_state_from_box(v2_app_id, algod_client)
        assert returned == []
        algod_client.application_info.assert_not_called()

    @pytest.mark.parametrize(
        "exception",
        [
            exception("", "", "", "", "") if exception == HTTPError else exception("")
            for exception in ALGOD_EXCEPTIONS
        ],
    )
    def test_nameservice_nfd_app_state_from_box_returns_empty_list_for_app_error(
        self, exception, mocker
    ):
        algod_client = mocker.MagicMock()
        v2_app_id = 88778506
        algod_client.application_info.side_effect = exception
        returned = _app_state_from_box(v2_app_id, algod_client)
        assert returned == []
        algod_client.application_info.assert_called_once()
        algod_client.application_info.assert_called_with(v2_app_id)

    def test_nameservice_nfd_app_state_from_box_returns_empty_list_for_no_state(
        self, mocker
    ):
        algod_client = mocker.MagicMock()
        v2_app_id = 88778506
        algod_client.application_info.return_value = {"params": {"global-state": []}}
        returned = _app_state_from_box(v2_app_id, algod_client)
        assert returned == []
        algod_client.application_info.assert_called_once()
        algod_client.application_info.assert_called_with(v2_app_id)

    def test_nameservice_nfd_app_state_from_box_functionality(self, mocker):
        algod_client = mocker.MagicMock()
        v2_app_id = 88778506
        state = mocker.MagicMock()
        algod_client.application_info.return_value = {"params": {"global-state": state}}
        returned = _app_state_from_box(v2_app_id, algod_client)
        assert returned == state
        algod_client.application_info.assert_called_once()
        algod_client.application_info.assert_called_with(v2_app_id)

    # # _box_name_for_algo_name
    @pytest.mark.parametrize(
        "name,box_name",
        [
            (
                "whitebit.algo",
                b"\xe9D\xb22S\xf8O\xdd<4\xeaz\xb9\x8a?\x9a\x8f#\xdc,d[\xdd\xe6\x18\x83\xc7\x83\x81a\xd3\xb1",
            ),
            (
                "dashawnsun.algo",
                b"\xf5\xda\x01\x01\x1cR\xc9\x0f8\xad\x8bc*6\xfeY\xb2~\x0f\xe1B\x84\x1f\xd9XC\xc6\x08L\xa9\xf4\x85",
            ),
            (
                "patrick.algo",
                b"\xfa9\xbe\x18\xf4_[9\x1e\x94.M#\xc9KF\x151U\xcd\x15\x89\xff\xcb^\x88z^\xaa\nW\x8f",
            ),
            (
                "prata.foundrystaging.algo",
                b"+\xf8g\x00\xe0\xa4\xdc\xb6\xd2\xf3\x84Y\x00\x83\x069\n\xf2\xe7s\xb6 D\xd1QJJ\x85\xecX\x07&",
            ),
        ],
    )
    def test_nameservice_box_name_for_algo_name_functionality(self, name, box_name):
        assert _box_name_for_algo_name(name) == box_name


class TestNameServiceNfdCommonFunctions:
    """Testing class for :py:mod:`nameservice.nfd` functions common to v1 and v2."""

    # # _address_from_bytes_value
    def test_nameservice_nfd_address_from_bytes_value_for_empty_bytes(self):
        assert list(_address_from_bytes_value("")) == []

    def test_nameservice_nfd_address_from_bytes_value_functionality(self):
        bytes_value = (
            "pqqulym8wk2D/ek6PwU1hGVaZBtdGebNpdoLpC9/8y2M"
            "q6wI9wfZYxZ33bCPzqYEu27c/WfzCt3vjD42zbbfnQ=="
        )
        assert list(_address_from_bytes_value(bytes_value)) == [
            "U2VK5FZJXTBE3A755E5D6BJVQRSVUZA3LUM6NTNF3IF2IL376MWTGMNPFA",
            "RSV2YCHXA7MWGFTX3WYI7TVGAS5W5XH5M7ZQVXPPRQ7DNTNW36OW2TRR6I",
        ]

    # # _append_addresses_from_global_state_for_key
    def test_nameservice_nfd_append_addresses_from_global_state_for_key_for_no_key(
        self,
    ):
        addresses = []
        global_state = [
            {
                "key": "aS5vd25lci5h",
                "value": {
                    "bytes": "qzLlaA6woB7VeN8T2drb1VK8XPeq1oMnhbySKQGelPQ=",
                    "type": 1,
                    "uint": 0,
                },
            },
            {
                "key": "aS5zZWdtZW50TG9ja2Vk",
                "value": {"bytes": "MQ==", "type": 1, "uint": 0},
            },
        ]
        key = "di5jYUFsZ28uMC5hcw=="
        _append_addresses_from_global_state_for_key(addresses, global_state, key)
        assert addresses == []

    def test_nameservice_nfd_append_addresses_from_global_state_for_key_for_no_address(
        self,
    ):
        addresses = ["RSV2YCHXA7MWGFTX3WYI7TVGAS5W5XH5M7ZQVXPPRQ7DNTNW36OW2TRR6I"]
        global_state = [
            {
                "key": "aS5vd25lci5h",
                "value": {
                    "bytes": "",
                    "type": 1,
                    "uint": 0,
                },
            },
            {
                "key": "aS5zZWdtZW50TG9ja2Vk",
                "value": {"bytes": "MQ==", "type": 1, "uint": 0},
            },
        ]
        key = "aS5vd25lci5h"
        _append_addresses_from_global_state_for_key(addresses, global_state, key)
        assert addresses == [
            "RSV2YCHXA7MWGFTX3WYI7TVGAS5W5XH5M7ZQVXPPRQ7DNTNW36OW2TRR6I"
        ]

    def test_nameservice_nfd_append_addresses_from_global_state_for_key_functionality(
        self,
    ):
        addresses = ["RSV2YCHXA7MWGFTX3WYI7TVGAS5W5XH5M7ZQVXPPRQ7DNTNW36OW2TRR6I"]
        global_state = [
            {
                "key": "aS5vd25lci5h",
                "value": {
                    "bytes": "qzLlaA6woB7VeN8T2drb1VK8XPeq1oMnhbySKQGelPQ=",
                    "type": 1,
                    "uint": 0,
                },
            },
            {
                "key": "aS5zZWdtZW50TG9ja2Vk",
                "value": {"bytes": "MQ==", "type": 1, "uint": 0},
            },
        ]
        key = "aS5vd25lci5h"
        _append_addresses_from_global_state_for_key(addresses, global_state, key)
        assert addresses == [
            "RSV2YCHXA7MWGFTX3WYI7TVGAS5W5XH5M7ZQVXPPRQ7DNTNW36OW2TRR6I",
            "VMZOK2AOWCQB5VLY34J5TWW32VJLYXHXVLLIGJ4FXSJCSAM6ST2EVWZBXI",
        ]

    # # _addresses_from_app_state
    def test_nameservice_nfd_addresses_from_app_state_for_found_caalgo(self):
        global_state = [
            {
                "key": "di5jYUFsZ28uMC5hcw==",
                "value": {
                    "bytes": "qzLlaA6woB7VeN8T2drb1VK8XPeq1oMnhbySKQGelPQ=",
                    "type": 1,
                    "uint": 0,
                },
            },
            {
                "key": "aS5vd25lci5h",
                "value": {
                    "bytes": "pqqulym8wk2D/ek6PwU1hGVaZBtdGebNpdoLpC9/8y0=",
                    "type": 1,
                    "uint": 0,
                },
            },
        ]
        returned = _addresses_from_app_state(global_state, [])
        assert returned == "VMZOK2AOWCQB5VLY34J5TWW32VJLYXHXVLLIGJ4FXSJCSAM6ST2EVWZBXI"

    def test_nameservice_nfd_addresses_from_app_state_for_found_caalgo_and_provided(
        self,
    ):
        global_state = [
            {
                "key": "di5jYUFsZ28uMC5hcw==",
                "value": {
                    "bytes": "qzLlaA6woB7VeN8T2drb1VK8XPeq1oMnhbySKQGelPQ=",
                    "type": 1,
                    "uint": 0,
                },
            },
            {
                "key": "aS5vd25lci5h",
                "value": {
                    "bytes": "pqqulym8wk2D/ek6PwU1hGVaZBtdGebNpdoLpC9/8y0=",
                    "type": 1,
                    "uint": 0,
                },
            },
        ]
        box_addresses = ["2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"]
        returned = _addresses_from_app_state(global_state, box_addresses)
        assert returned == (
            "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU "
            "VMZOK2AOWCQB5VLY34J5TWW32VJLYXHXVLLIGJ4FXSJCSAM6ST2EVWZBXI"
        )

    def test_nameservice_nfd_addresses_from_app_state_for_not_found_caalgo(self):
        global_state = [
            {
                "key": "aS5vd25lci5h",
                "value": {
                    "bytes": "pqqulym8wk2D/ek6PwU1hGVaZBtdGebNpdoLpC9/8y0=",
                    "type": 1,
                    "uint": 0,
                },
            },
        ]
        returned = _addresses_from_app_state(global_state, [])
        assert returned == "U2VK5FZJXTBE3A755E5D6BJVQRSVUZA3LUM6NTNF3IF2IL376MWTGMNPFA"

    def test_nameservice_nfd_addresses_from_app_state_for_not_found_caalgo_and_provided(
        self,
    ):
        global_state = [
            {
                "key": "aS5vd25lci5h",
                "value": {
                    "bytes": "pqqulym8wk2D/ek6PwU1hGVaZBtdGebNpdoLpC9/8y0=",
                    "type": 1,
                    "uint": 0,
                },
            },
        ]
        box_addresses = ["2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"]
        returned = _addresses_from_app_state(global_state, box_addresses)
        assert returned == "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

    # # _app_state_for_algo_name
    def test_nameservice_nfd_app_state_for_algo_name_returns_app_state_for_v2(
        self, mocker
    ):
        mocked_lsig = mocker.patch("nameservice.nfd._logicsig_from_name")
        app_state, algod_client = [1, 2, 3], mocker.MagicMock()
        name = "foobar.algo"
        v2_app_id = 505050
        mocked_app_box = mocker.patch(
            "nameservice.nfd._app_state_from_box", return_value=app_state
        )
        assert _app_state_for_algo_name(name, v2_app_id, algod_client) == app_state
        mocked_app_box.assert_called_once()
        mocked_app_box.assert_called_with(v2_app_id, algod_client)
        mocked_lsig.assert_not_called()

    def test_nameservice_nfd_app_state_for_algo_name_for_non_existing_name(
        self, mocker
    ):
        mocked_app_box = mocker.patch(
            "nameservice.nfd._app_state_from_box", return_value=[]
        )
        mocked_lsig = mocker.patch("nameservice.nfd._logicsig_from_name")
        algod_client = mocker.MagicMock()
        mocked_app_lsig = mocker.patch(
            "nameservice.nfd._app_id_from_logicsig", return_value=None
        )
        name = "foobar9.algo"
        v2_app_id = 505050
        returned = _app_state_for_algo_name(name, v2_app_id, algod_client)
        assert returned == []
        mocked_app_box.assert_called_once()
        mocked_app_box.assert_called_with(v2_app_id, algod_client)
        mocked_lsig.assert_called_once()
        mocked_lsig.assert_called_with("name/", name, NFD_APP_ID)
        mocked_app_lsig.assert_called_once()
        mocked_app_lsig.assert_called_with(mocked_lsig.return_value, algod_client)
        algod_client.application_info.assert_not_called()

    def test_nameservice_nfd_app_state_for_algo_name_returns_app_state_v1(self, mocker):
        mocked_app_box = mocker.patch(
            "nameservice.nfd._app_state_from_box", return_value=[]
        )
        mocked_lsig = mocker.patch("nameservice.nfd._logicsig_from_name")
        algod_client, app_id, app_state = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        mocked_app_lsig = mocker.patch(
            "nameservice.nfd._app_id_from_logicsig", return_value=app_id
        )
        algod_client.application_info.return_value = {
            "params": {"global-state": app_state}
        }
        name = "foobar.algo"
        v2_app_id = 505050
        returned = _app_state_for_algo_name(name, v2_app_id, algod_client)
        assert returned == app_state
        mocked_app_box.assert_called_once()
        mocked_app_box.assert_called_with(v2_app_id, algod_client)
        mocked_lsig.assert_called_once()
        mocked_lsig.assert_called_with("name/", name, NFD_APP_ID)
        mocked_app_lsig.assert_called_once()
        mocked_app_lsig.assert_called_with(mocked_lsig.return_value, algod_client)
        algod_client.application_info.assert_called_once()
        algod_client.application_info.assert_called_with(app_id)


class TestNameServiceNfdPublicFunctions:
    """Testing class for :py:mod:`nameservice.nfd` public functions."""

    # # nfd_app_id_from_algo_name
    @pytest.mark.parametrize(
        "exception",
        [
            exception("", "", "", "", "") if exception == HTTPError else exception("")
            for exception in ALGOD_EXCEPTIONS
        ],
    )
    def test_nameservice_nfd_nfd_app_id_from_algo_name_returns_none_for_box_error(
        self, exception, mocker
    ):
        name = "foobar.algo"
        algod_client = mocker.MagicMock()
        mocked_box = mocker.patch("nameservice.nfd._box_name_for_algo_name")
        algod_client.application_box_by_name.side_effect = exception
        returned = nfd_app_id_from_algo_name(name, algod_client)
        assert returned is None
        mocked_box.assert_called_once()
        mocked_box.assert_called_with(name)
        algod_client.application_box_by_name.assert_called_once()
        algod_client.application_box_by_name.assert_called_with(
            NFD_APP_ID, mocked_box.return_value
        )

    def test_nameservice_nfd_nfd_app_id_from_algo_name_returns_none_for_no_value(
        self, mocker
    ):
        name = "foobar.algo"
        algod_client = mocker.MagicMock()
        mocked_box = mocker.patch("nameservice.nfd._box_name_for_algo_name")
        value = ""
        algod_client.application_box_by_name.return_value = {"value": value}
        returned = nfd_app_id_from_algo_name(name, algod_client)
        assert returned is None
        mocked_box.assert_called_once()
        mocked_box.assert_called_with(name)
        algod_client.application_box_by_name.assert_called_once()
        algod_client.application_box_by_name.assert_called_with(
            NFD_APP_ID, mocked_box.return_value
        )

    @pytest.mark.parametrize(
        "value",
        [
            "AAAAAAAA",
            "AAAAAAAAAAAAAAVKpxAAAAAABUqnCg==",
            "AAAAAAAAVKpxAAAAAABUqnCg==",
            "AAAAAAAAAAAAAAAAAAAAAA",
            "AAAAAAAAAAAAAA",
        ],
    )
    def test_nameservice_nfd_nfd_app_id_from_algo_name_returns_none_for_wrong_value(
        self, value, mocker
    ):
        name = "foobar.algo"
        algod_client = mocker.MagicMock()
        mocked_box = mocker.patch("nameservice.nfd._box_name_for_algo_name")
        algod_client.application_box_by_name.return_value = {"value": value}
        returned = nfd_app_id_from_algo_name(name, algod_client)
        assert returned is None
        mocked_box.assert_called_once()
        mocked_box.assert_called_with(name)
        algod_client.application_box_by_name.assert_called_once()
        algod_client.application_box_by_name.assert_called_with(
            NFD_APP_ID, mocked_box.return_value
        )

    def test_nameservice_nfd_nfd_app_id_from_algo_name_returns_0_for_no_app(
        self, mocker
    ):
        name = "foobar.algo"
        algod_client = mocker.MagicMock()
        mocked_box = mocker.patch("nameservice.nfd._box_name_for_algo_name")
        value = "AAAAAAVKpxAAAAAAAAAAAAAA"
        algod_client.application_box_by_name.return_value = {"value": value}
        returned = nfd_app_id_from_algo_name(name, algod_client)
        assert returned == 0
        mocked_box.assert_called_once()
        mocked_box.assert_called_with(name)
        algod_client.application_box_by_name.assert_called_once()
        algod_client.application_box_by_name.assert_called_with(
            NFD_APP_ID, mocked_box.return_value
        )

    def test_nameservice_nfd_nfd_app_id_from_algo_name_functionality(self, mocker):
        name = "foobar.algo"
        algod_client = mocker.MagicMock()
        mocked_box = mocker.patch("nameservice.nfd._box_name_for_algo_name")
        value = "AAAAAAVKpxAAAAAABUqnCg=="
        app_id = 88778506
        algod_client.application_box_by_name.return_value = {"value": value}
        state = mocker.MagicMock()
        algod_client.application_info.return_value = {"params": {"global-state": state}}
        returned = nfd_app_id_from_algo_name(name, algod_client)
        assert returned == app_id
        mocked_box.assert_called_once()
        mocked_box.assert_called_with(name)
        algod_client.application_box_by_name.assert_called_once()
        algod_client.application_box_by_name.assert_called_with(
            NFD_APP_ID, mocked_box.return_value
        )

    # check_name
    @pytest.mark.parametrize(
        "name",
        ["foo.balgo", "algo.foo", "foo-algo", "foo,algo", ".algo.1"],
    )
    def test_nameservice_nfd_check_name_returns_name_for_not_algo_name(
        self, name, mocker
    ):
        mocked_app = mocker.patch("nameservice.nfd.nfd_app_id_from_algo_name")
        assert check_name(name, mocker.MagicMock()) == name
        mocked_app.assert_not_called()

    def test_nameservice_nfd_check_name_returns_name_for_empty_app_state(self, mocker):
        v2_app_id = 505050
        mocked_app = mocker.patch(
            "nameservice.nfd.nfd_app_id_from_algo_name", return_value=v2_app_id
        )
        mocked_state = mocker.patch(
            "nameservice.nfd._app_state_for_algo_name", return_value=[]
        )
        mocked_addresses = mocker.patch("nameservice.nfd._addresses_from_app_state")
        algod_client = mocker.MagicMock()
        algo_name = "foobar.algo"
        name = f"{algo_name}/nfd"
        assert check_name(name, algod_client) == name
        mocked_app.assert_called_once()
        mocked_app.assert_called_with(algo_name, algod_client)
        mocked_state.assert_called_once()
        mocked_state.assert_called_with(algo_name, v2_app_id, algod_client)
        mocked_addresses.assert_not_called()

    def test_nameservice_nfd_check_name_for_v1_not_found(self, mocker):
        v2_app_id = None
        mocked_app = mocker.patch(
            "nameservice.nfd.nfd_app_id_from_algo_name", return_value=v2_app_id
        )
        app_state = [1, 2, 3]
        mocked_state = mocker.patch(
            "nameservice.nfd._app_state_for_algo_name", return_value=app_state
        )
        mocked_boxes = mocker.patch("nameservice.nfd._check_boxes_addresses")
        mocked_addresses = mocker.patch(
            "nameservice.nfd._addresses_from_app_state", return_value=None
        )
        algod_client = mocker.MagicMock()
        algo_name = "foobar.algo"
        name = f"{algo_name}/nfd"
        assert check_name(name, algod_client) == name
        mocked_app.assert_called_once()
        mocked_app.assert_called_with(algo_name, algod_client)
        mocked_state.assert_called_once()
        mocked_state.assert_called_with(algo_name, v2_app_id, algod_client)
        mocked_addresses.assert_called_once()
        mocked_addresses.assert_called_with(app_state, [])
        mocked_boxes.assert_not_called()

    def test_nameservice_nfd_check_name_for_v1_found_addresses(self, mocker):
        v2_app_id = None
        mocked_app = mocker.patch(
            "nameservice.nfd.nfd_app_id_from_algo_name", return_value=v2_app_id
        )
        app_state = [1, 2, 3]
        mocked_state = mocker.patch(
            "nameservice.nfd._app_state_for_algo_name", return_value=app_state
        )
        mocked_boxes = mocker.patch("nameservice.nfd._check_boxes_addresses")
        addresses = mocker.MagicMock()
        mocked_addresses = mocker.patch(
            "nameservice.nfd._addresses_from_app_state", return_value=addresses
        )
        algod_client = mocker.MagicMock()
        name = "foobar.algo"
        assert check_name(name, algod_client) == addresses
        mocked_app.assert_called_once()
        mocked_app.assert_called_with(name, algod_client)
        mocked_state.assert_called_once()
        mocked_state.assert_called_with(name, v2_app_id, algod_client)
        mocked_addresses.assert_called_once()
        mocked_addresses.assert_called_with(app_state, [])
        mocked_boxes.assert_not_called()

    def test_nameservice_nfd_check_name_for_v2_not_found(self, mocker):
        v2_app_id = 505050
        mocked_app = mocker.patch(
            "nameservice.nfd.nfd_app_id_from_algo_name", return_value=v2_app_id
        )
        app_state = [1, 2, 3]
        mocked_state = mocker.patch(
            "nameservice.nfd._app_state_for_algo_name", return_value=app_state
        )
        mocked_boxes = mocker.patch("nameservice.nfd._check_boxes_addresses")
        mocked_addresses = mocker.patch(
            "nameservice.nfd._addresses_from_app_state", return_value=None
        )
        algod_client = mocker.MagicMock()
        algo_name = "foobar.algo"
        name = f"{algo_name}/nfd"
        assert check_name(name, algod_client) == name
        mocked_app.assert_called_once()
        mocked_app.assert_called_with(algo_name, algod_client)
        mocked_state.assert_called_once()
        mocked_state.assert_called_with(algo_name, v2_app_id, algod_client)
        mocked_boxes.assert_called_once()
        mocked_boxes.assert_called_with(v2_app_id, algod_client)
        mocked_addresses.assert_called_once()
        mocked_addresses.assert_called_with(app_state, mocked_boxes.return_value)

    def test_nameservice_nfd_check_name_for_v2_found_addresses(self, mocker):
        v2_app_id = 505050
        mocked_app = mocker.patch(
            "nameservice.nfd.nfd_app_id_from_algo_name", return_value=v2_app_id
        )
        app_state = [1, 2, 3]
        mocked_state = mocker.patch(
            "nameservice.nfd._app_state_for_algo_name", return_value=app_state
        )
        mocked_boxes = mocker.patch("nameservice.nfd._check_boxes_addresses")
        addresses = mocker.MagicMock()
        mocked_addresses = mocker.patch(
            "nameservice.nfd._addresses_from_app_state", return_value=addresses
        )
        algod_client = mocker.MagicMock()
        name = "foobar.algo"
        assert check_name(name, algod_client) == addresses
        mocked_app.assert_called_once()
        mocked_app.assert_called_with(name, algod_client)
        mocked_state.assert_called_once()
        mocked_state.assert_called_with(name, v2_app_id, algod_client)
        mocked_boxes.assert_called_once()
        mocked_boxes.assert_called_with(v2_app_id, algod_client)
        mocked_addresses.assert_called_once()
        mocked_addresses.assert_called_with(app_state, mocked_boxes.return_value)

    def test_nameservice_nfd_check_name_returns_address_for_uppercased_name(
        self, mocker
    ):
        name = "FOOBAR.ALGO"
        algod_client = mocker.MagicMock()
        state = deepcopy(TESTING_NFD_ADDRESS_STATE)
        mocker.patch("nameservice.nfd.nfd_app_id_from_algo_name", return_value=None)
        mocker.patch("nameservice.nfd._app_state_for_algo_name", return_value=state)
        assert check_name(name, algod_client) == TESTING_NFD_ADDRESS

    def test_nameservice_nfd_check_name_returns_address_for_nfd_suffix(self, mocker):
        name = "foobar.algo/nfd"
        algod_client = mocker.MagicMock()
        state = deepcopy(TESTING_NFD_ADDRESS_STATE)
        mocker.patch("nameservice.nfd.nfd_app_id_from_algo_name", return_value=None)
        mocker.patch("nameservice.nfd._app_state_for_algo_name", return_value=state)
        assert check_name(name, algod_client) == TESTING_NFD_ADDRESS
