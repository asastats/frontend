"""Testing module for :py:mod:`nameservice.xchain` module."""

import base64
from urllib.error import HTTPError

import pytest

from nameservice.xchain import (
    _compiled_evm_address,
    _normalize_address,
    check_evm_address,
)
from utils.constants.core import ALGOD_EXCEPTIONS


class TestNameServiceXChainPrivateFunctions:
    """Testing class for :py:mod:`nameservice.xchain` private functions."""

    # # _normalize_address
    @pytest.mark.parametrize(
        "evm_address,expected",
        [
            (
                "0x67C812D729F4fC4515E603118115788a6e7FCaa3",
                "67c812d729f4fc4515e603118115788a6e7fcaa3",
            ),
            (
                "67C812D729F4fC4515E603118115788a6e7FCaa3",
                "67c812d729f4fc4515e603118115788a6e7fcaa3",
            ),
            ("0XABCD", "abcd"),
            ("abcd", "abcd"),
        ],
    )
    def test_nameservice_xchain_normalize_address(self, evm_address, expected):
        assert _normalize_address(evm_address) == expected

    # # _compiled_evm_address
    def test_nameservice_xchain_compiled_evm_address(self, mocker):
        algod_client = mocker.MagicMock()
        evm_address = "0x67C812D729F4fC4515E603118115788a6e7FCaa3"
        normalized = "67c812d729f4fc4515e603118115788a6e7fcaa3"

        mock_normalize = mocker.patch(
            "nameservice.xchain._normalize_address", return_value=normalized
        )

        expected_bytes = b"mocked_compiled_bytes"
        expected_b64 = base64.b64encode(expected_bytes).decode("utf-8")
        algod_client.compile.return_value = {"result": expected_b64}

        returned = _compiled_evm_address(evm_address, algod_client)

        assert returned == expected_bytes
        mock_normalize.assert_called_once_with(evm_address)
        algod_client.compile.assert_called_once()

        # Verify the template substitution contains the owner_hex
        called_teal = algod_client.compile.call_args[0][0]
        assert f"0x{normalized}" in called_teal


class TestNameServiceXChainPublicFunctions:
    """Testing class for :py:mod:`nameservice.xchain` public functions."""

    # # check_evm_address
    def test_nameservice_xchain_check_evm_address_success(self, mocker):
        algod_client = mocker.MagicMock()
        evm_address = "0x67C812D729F4fC4515E603118115788a6e7FCaa3"
        compiled_bytes = b"mocked_compiled_bytes"
        algorand_address = "VCMCNM3GUKP4K5R4U74NIFV7S2E5P2VHY36R5ZIXFUK3PUDYJ5Q4QVQ5M4"

        mock_compiled = mocker.patch(
            "nameservice.xchain._compiled_evm_address", return_value=compiled_bytes
        )

        mock_lsig_instance = mocker.MagicMock()
        mock_lsig_instance.address.return_value = algorand_address
        mock_lsig_class = mocker.patch(
            "nameservice.xchain.LogicSigAccount", return_value=mock_lsig_instance
        )

        returned = check_evm_address(evm_address, algod_client)

        assert returned == algorand_address
        mock_compiled.assert_called_once_with(evm_address, algod_client)
        mock_lsig_class.assert_called_once_with(compiled_bytes)
        mock_lsig_instance.address.assert_called_once()

    @pytest.mark.parametrize(
        "exception",
        [
            exception("", "", "", "", "") if exception == HTTPError else exception("")
            for exception in ALGOD_EXCEPTIONS
        ],
    )
    def test_nameservice_xchain_check_evm_address_exception(self, exception, mocker):
        algod_client = mocker.MagicMock()
        evm_address = "0x67C812D729F4fC4515E603118115788a6e7FCaa3"

        mock_compiled = mocker.patch(
            "nameservice.xchain._compiled_evm_address", side_effect=exception
        )
        mock_lsig_class = mocker.patch("nameservice.xchain.LogicSigAccount")

        returned = check_evm_address(evm_address, algod_client)

        # Should return the original EVM address upon catching an ALGOD exception
        assert returned == evm_address
        mock_compiled.assert_called_once_with(evm_address, algod_client)
        mock_lsig_class.assert_not_called()
