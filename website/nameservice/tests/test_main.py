"""Testing module for :py:mod:`nameservice.main` module."""

# import pytest
# from django.core.exceptions import ValidationError

# from nameservice.main import PROVIDERS, check_name
# from utils.constants.nameservice import NAME_SERVICE_MULTIPLE
from nameservice.main import check_name


class TestNameServiceMainFunctions:
    """Testing class for :py:mod:`nameservice.main` functions."""

    # # check_name
    def test_nameservice_main_check_name_returns_ans_check_name_for_ans_suffix(
        self, mocker
    ):
        mocked_nfd = mocker.patch("nameservice.nfd.check_name")
        mocked_xchain = mocker.patch("nameservice.xchain.check_evm_address")
        mocked = mocker.patch("nameservice.ans.check_name")
        algod_client = mocker.MagicMock()
        name = "name.algo/ANS"
        returned = check_name(name, algod_client)
        assert returned == mocked.return_value
        mocked.assert_called_once_with(name, algod_client)
        mocked_nfd.assert_not_called()
        mocked_xchain.assert_not_called()

    def test_nameservice_main_check_name_returns_nfd_check_name_for_nfd_suffix(
        self, mocker
    ):
        mocked_ans = mocker.patch("nameservice.ans.check_name")
        mocked_xchain = mocker.patch("nameservice.xchain.check_evm_address")
        mocked = mocker.patch("nameservice.nfd.check_name")
        algod_client = mocker.MagicMock()
        name = "name.algo/Nfd"
        returned = check_name(name, algod_client)
        assert returned == mocked.return_value
        mocked.assert_called_once_with(name, algod_client)
        mocked_ans.assert_not_called()
        mocked_xchain.assert_not_called()

    def test_nameservice_main_check_name_returns_nfd_check_name_for_algo_name(
        self, mocker
    ):
        mocked_ans = mocker.patch("nameservice.ans.check_name")
        mocked_xchain = mocker.patch("nameservice.xchain.check_evm_address")
        mocked = mocker.patch("nameservice.nfd.check_name")
        algod_client = mocker.MagicMock()
        name = "name.algo"
        returned = check_name(name, algod_client)
        assert returned == mocked.return_value
        mocked.assert_called_once_with(name, algod_client)
        mocked_ans.assert_not_called()
        mocked_xchain.assert_not_called()

    def test_nameservice_main_check_name_returns_nfd_check_name_for_evm_address(
        self, mocker
    ):
        mocked_ans = mocker.patch("nameservice.ans.check_name")
        mocked_nfd = mocker.patch("nameservice.nfd.check_name")
        mocked = mocker.patch("nameservice.xchain.check_evm_address")
        algod_client = mocker.MagicMock()
        name = "0x67C812D729F4fC4515E603118115788a6e7FCaa3"
        returned = check_name(name, algod_client)
        assert returned == mocked.return_value
        mocked.assert_called_once_with(name, algod_client)
        mocked_ans.assert_not_called()
        mocked_nfd.assert_not_called()

    def test_nameservice_main_check_name_returns_nfd_check_name_for_no_suffix(
        self, mocker
    ):
        mocked_ans = mocker.patch("nameservice.ans.check_name")
        mocked_xchain = mocker.patch("nameservice.xchain.check_evm_address")
        mocked_nfd = mocker.patch("nameservice.nfd.check_name")
        algod_client = mocker.MagicMock()
        name = "0x67C812D729F4fC4515E603118115788a6e7FCaa3"
        returned = check_name(name, algod_client)
        assert returned == mocked_xchain.return_value
        mocked_xchain.assert_called_once_with(name, algod_client)
        mocked_ans.assert_not_called()
        mocked_nfd.assert_not_called()

    # def test_nameservice_main_check_name_returns_name_for_no_result(self, mocker):
    #     algod_client = mocker.MagicMock()
    #     name = "name.algo"
    #     mocked_providers = []
    #     for provider in PROVIDERS:
    #         provider_name = provider.__name__.split(".")[-1]
    #         mocked_providers.append(
    #             mocker.patch(
    #                 f"nameservice.main.{provider_name}.check_name", return_value=name
    #             )
    #         )
    #     assert check_name(name, algod_client) == name
    #     for mocked in mocked_providers:
    #         mocked.assert_called_once_with(name, algod_client)

    # def test_nameservice_main_check_name_returns_address_for_single_result(
    #     self, mocker
    # ):
    #     algod_client = mocker.MagicMock()
    #     name = "name.algo"
    #     result = "ADDRESS"
    #     mocked_providers = []
    #     for i, provider in enumerate(PROVIDERS):
    #         provider_name = provider.__name__.split(".")[-1]
    #         mocked_providers.append(
    #             mocker.patch(
    #                 f"nameservice.main.{provider_name}.check_name",
    #                 return_value=name if i == 0 else result,
    #             )
    #         )
    #     assert check_name(name, algod_client) == result
    #     for mocked in mocked_providers:
    #         mocked.assert_called_once_with(name, algod_client)

    # def test_nameservice_main_check_name_raise_validation_error_for_duplicate(
    #     self, mocker
    # ):
    #     algod_client = mocker.MagicMock()
    #     name = "name.algo"
    #     results = [["ADDRESS1"], ["ADDRESS2"]]
    #     mocked_providers = []
    #     for i, provider in enumerate(PROVIDERS):
    #         provider_name = provider.__name__.split(".")[-1]
    #         mocked_providers.append(
    #             mocker.patch(
    #                 f"nameservice.main.{provider_name}.check_name",
    #                 return_value=results[i],
    #             )
    #         )
    #     with pytest.raises(ValidationError) as exception:
    #         check_name(name, algod_client)
    #     assert str(exception.value) == f"['{NAME_SERVICE_MULTIPLE}{name}']"
