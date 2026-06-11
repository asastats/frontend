"""Testing module for :py:mod:`core.permission_providers.permissiondapp`."""

import base64

import pytest

pytest.importorskip("permissiondapp.dapp.config")

from algosdk.error import AlgodHTTPError  # noqa: E402

from core.permission_providers.permissiondapp import (  # noqa: E402
    PermissionDappProvider,
    _deserialized_box_value,
    _format_days_diff_message,
    _format_tier_name_as_link,
    formatted_subscription_timestamps,
)

MODULE = "core.permission_providers.permissiondapp"


class TestCorePermissiondappDeserializedBoxValue:
    """Testing class for :py:func:`...permissiondapp._deserialized_box_value`."""

    def test_core_permissiondapp_deserialized_box_value_functionality(self, mocker):
        client = mocker.MagicMock()
        client.application_box_by_name.return_value = {
            "value": base64.b64encode(b"payload").decode("ascii")
        }
        deserialize = mocker.patch(
            f"{MODULE}.deserialize_values_data", return_value=[5, 100]
        )
        assert _deserialized_box_value(client, 1, "box") == [5, 100]
        deserialize.assert_called_once_with("payload")

    def test_core_permissiondapp_deserialized_box_value_on_http_error(self, mocker):
        client = mocker.MagicMock()
        client.application_box_by_name.side_effect = AlgodHTTPError("boom")
        assert _deserialized_box_value(client, 1, "box") is None


class TestCorePermissiondappFormatTierNameAsLink:
    """Testing class for :py:func:`...permissiondapp._format_tier_name_as_link`."""

    def test_core_permissiondapp_format_tier_name_as_link_functionality(self, mocker):
        mocker.patch(f"{MODULE}.SUBSCRIPTION_PERMISSIONS", {42: (0, 0, "Cluster")})
        mocker.patch(f"{MODULE}.SUBTOPIA_URL_PREFIX", "https://x.io/")
        link = _format_tier_name_as_link("Cluster")
        assert 'href="https://x.io/42"' in link
        assert "Cluster tier</a>" in link


class TestCorePermissiondappPermissionDappProvider:
    """Testing class for :py:class:`...permissiondapp.PermissionDappProvider`."""

    def test_core_permissiondapp_votes_and_permission_from_box(self, mocker):
        mocker.patch(f"{MODULE}._mainnet_algod_client")
        mocker.patch(f"{MODULE}.box_name_from_address", return_value="box")
        mocker.patch(f"{MODULE}._deserialized_box_value", return_value=[5, 100, 7])
        assert PermissionDappProvider().votes_and_permission("ADDRESS") == (5, 100)

    def test_core_permissiondapp_votes_and_permission_without_box(self, mocker):
        mocker.patch(f"{MODULE}._mainnet_algod_client")
        mocker.patch(f"{MODULE}.box_name_from_address", return_value="box")
        mocker.patch(f"{MODULE}._deserialized_box_value", return_value=None)
        assert PermissionDappProvider().votes_and_permission("ADDRESS") == (0, 0)

    def test_core_permissiondapp_subscriptions_with_data(self, mocker):
        mocker.patch(f"{MODULE}._mainnet_algod_client")
        mocker.patch(
            f"{MODULE}.fetch_subscriptions_for_address", return_value={"tier": 1}
        )
        formatted = mocker.patch(
            f"{MODULE}.formatted_subscription_timestamps", return_value={"msg": "x"}
        )
        assert PermissionDappProvider().subscriptions("ADDRESS") == {"msg": "x"}
        formatted.assert_called_once_with({"tier": 1})

    def test_core_permissiondapp_subscriptions_without_data(self, mocker):
        mocker.patch(f"{MODULE}._mainnet_algod_client")
        mocker.patch(f"{MODULE}.fetch_subscriptions_for_address", return_value=None)
        assert PermissionDappProvider().subscriptions("ADDRESS") is None

    def test_core_permissiondapp_refresh_updates_mainnet_boxes(self, mocker):
        update = mocker.patch(f"{MODULE}.check_and_update_permission_dapp_boxes")
        PermissionDappProvider().refresh()
        update.assert_called_once_with(network="mainnet")

    def test_core_permissiondapp_tier_link_delegates(self, mocker):
        formatter = mocker.patch(
            f"{MODULE}._format_tier_name_as_link", return_value="<a>"
        )
        assert PermissionDappProvider().tier_link("Cluster") == "<a>"
        formatter.assert_called_once_with("Cluster")


class TestCorePermissiondappFormatDaysDiffMessage:
    """Testing class for :py:func:`...permissiondapp._format_days_diff_message`."""

    def test_core_permissiondapp_format_days_diff_message_active(self, mocker):
        from datetime import datetime as real_datetime

        clock = mocker.patch(f"{MODULE}.datetime")
        clock.fromtimestamp.return_value = real_datetime(2025, 1, 11)
        clock.now.return_value = real_datetime(2025, 1, 1)
        assert _format_days_diff_message(123) == "expires in 10 days"

    def test_core_permissiondapp_format_days_diff_message_expired(self, mocker):
        from datetime import datetime as real_datetime

        clock = mocker.patch(f"{MODULE}.datetime")
        clock.fromtimestamp.return_value = real_datetime(2025, 1, 1)
        clock.now.return_value = real_datetime(2025, 1, 11)
        assert _format_days_diff_message(123) == "EXPIRED"


class TestCorePermissiondappFormattedSubscriptionTimestamps:
    """Testing class for `...permissiondapp.formatted_subscription_timestamps`."""

    def test_core_permissiondapp_formatted_subscription_timestamps_functionality(
        self, mocker
    ):
        mocker.patch(
            f"{MODULE}._format_tier_name_as_link", side_effect=lambda name: f"L:{name}"
        )
        mocker.patch(
            f"{MODULE}._format_days_diff_message", side_effect=lambda ts: f"D:{ts}"
        )
        result = formatted_subscription_timestamps({"Cluster": 100, "Intro": 200})
        assert result == {"L:Cluster": "D:100", "L:Intro": "D:200"}
