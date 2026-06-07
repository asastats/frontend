"""Testing module for :py:mod:`nameservice.ans` module."""

import pytest

from nameservice.ans import check_name


class TestNameServiceAnsFunctions:
    """Testing class for :py:mod:`nameservice.ans` functions."""

    # check_name
    @pytest.mark.parametrize(
        "name",
        ["foo.balgo", "algo.foo", "foo-algo", "foo,algo", ".algo.1"],
    )
    def test_nameservice_ans_check_name_returns_name_for_not_algo_name(
        self, name, mocker
    ):
        mocked = mocker.patch("nameservice.ans.AnsResolver")
        assert check_name(name, mocker.MagicMock()) == name
        mocked.assert_not_called()

    def test_nameservice_ans_check_name_returns_name_for_exception(self, mocker):
        mocked_resolver = mocker.patch("nameservice.ans.AnsResolver")
        algod_client = mocker.MagicMock()
        name = "foobar.algo/Ans"
        mocked_resolver.return_value.resolve_name.side_effect = Exception("")
        assert check_name(name, algod_client) == name

    def test_nameservice_ans_check_name_resolves_with_slash_ans_suffix(self, mocker):
        mocked_resolver = mocker.patch("nameservice.ans.AnsResolver")
        algod_client = mocker.MagicMock()
        name = "foobar.algo/Ans"
        name_info = {"found": False}
        mocked_resolver.return_value.resolve_name.return_value = name_info
        name = name.lower().replace("/ans", "")
        assert check_name(name, algod_client) == name
        mocked_resolver.assert_called_once()
        mocked_resolver.assert_called_with(algod_client)
        mocked_resolver.return_value.resolve_name.assert_called_once()
        mocked_resolver.return_value.resolve_name.assert_called_with(name)

    def test_nameservice_ans_check_name_resolves_uppercases_name(self, mocker):
        mocked_resolver = mocker.patch("nameservice.ans.AnsResolver")
        algod_client = mocker.MagicMock()
        name = "FOOBAR.ALGO"
        name_info = {"found": False}
        mocked_resolver.return_value.resolve_name.return_value = name_info
        assert check_name(name, algod_client) == name
        mocked_resolver.assert_called_once()
        mocked_resolver.assert_called_with(algod_client)
        mocked_resolver.return_value.resolve_name.assert_called_once()
        mocked_resolver.return_value.resolve_name.assert_called_with(name.lower())

    def test_nameservice_ans_check_name_returns_name_for_not_registered_name(
        self, mocker
    ):
        mocked_resolver = mocker.patch("nameservice.ans.AnsResolver")
        algod_client = mocker.MagicMock()
        name = "foobar.algo"
        name_info = {"found": False}
        mocked_resolver.return_value.resolve_name.return_value = name_info
        assert check_name(name, algod_client) == name
        mocked_resolver.assert_called_once()
        mocked_resolver.assert_called_with(algod_client)
        mocked_resolver.return_value.resolve_name.assert_called_once()
        mocked_resolver.return_value.resolve_name.assert_called_with(name)

    def test_nameservice_ans_check_name_returns_owner_for_registered_name(self, mocker):
        mocked_resolver = mocker.patch("nameservice.ans.AnsResolver")
        algod_client = mocker.MagicMock()
        name = "foobar.algo"
        owner = mocker.MagicMock()
        name_info = {"found": True, "owner": owner}
        mocked_resolver.return_value.resolve_name.return_value = name_info
        assert check_name(name, algod_client) == owner
        mocked_resolver.assert_called_once()
        mocked_resolver.assert_called_with(algod_client)
        mocked_resolver.return_value.resolve_name.assert_called_once()
        mocked_resolver.return_value.resolve_name.assert_called_with(name)
