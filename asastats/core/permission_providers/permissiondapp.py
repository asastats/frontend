"""ASA Stats permission provider backed by the permission-dapp submodule.

This is ASA-Stats deployment glue. It is imported only when
``settings.PERMISSION_PROVIDER`` names it, so the open frontend never imports it
(nor the permission-dapp submodule) unless this deployment configures it. The
permission-dapp repo stays a pure, standalone smart-contract project with no
Django dependency; the dependency points one way only, this adapter ->
``permissiondapp.dapp.*``, never the reverse.
"""

import base64
from datetime import UTC, datetime

from algosdk.error import AlgodHTTPError
from algosdk.v2client.algod import AlgodClient

from core.permission_provider import PermissionProvider
from permissiondapp.dapp.config import (
    PERMISSION_APP_ID,
    SUBSCRIPTION_PERMISSIONS,
    SUBTOPIA_URL_PREFIX,
)
from permissiondapp.dapp.foundation import (
    check_and_update_permission_dapp_boxes,
)
from permissiondapp.dapp.helpers import (
    box_name_from_address,
    deserialize_values_data,
    environment_variables,
)
from permissiondapp.dapp.network import fetch_subscriptions_for_address


def _mainnet_algod_client():
    """Return a mainnet Algod client built from the dApp's own environment.

    :var env: permission-dApp environment variables
    :type env: dict
    :return: :class:`AlgodClient`
    """
    env = environment_variables()
    return AlgodClient(env["algod_token_mainnet"], env["algod_address_mainnet"])


def _format_tier_name_as_link(tier_name):
    """Return Subtopia tier link markup for a tier name.

    :param tier_name: subscription tier name
    :type tier_name: str
    :var app_id: subscription tier's decentralized application identifier
    :type app_id: int
    :return: str
    """
    app_id = next(
        app_id
        for app_id, (_, _, name) in SUBSCRIPTION_PERMISSIONS.items()
        if name == tier_name
    )
    return (
        f'<a href="{SUBTOPIA_URL_PREFIX}{app_id}" target="_blank" rel="noopener" '
        f'title="Open Subtopia.io subscription tier page">{tier_name} tier</a>'
    )


def _format_days_diff_message(timestamp):
    """Return formatted message with difference in days between `timestamp` and now.

    :param timestamp: seconds since epoch value to compare with now
    :type timestamp: int
    :var delta: difference between provided timestamp and now
    :type delta: :class:`datetime.timedelta`
    :return: str
    """
    delta = datetime.fromtimestamp(timestamp, UTC) - datetime.now(UTC)
    return f"expires in {delta.days} days" if delta.days >= 0 else "EXPIRED"


def formatted_subscription_timestamps(subscriptions):
    """Return provided subscriptions with values in a form of days left.

    :param subscriptions: collection of tier names and expiration epochs
    :type subscriptions: dict
    :return: dict
    """
    return {
        _format_tier_name_as_link(tier_name): _format_days_diff_message(timestamp)
        for tier_name, timestamp in subscriptions.items()
    }


def _deserialized_box_value(client, app_id, box_name):
    """Fetch a Permission dApp box value and return its deserialized data.

    :param client: Algorand Node client instance
    :type client: :class:`AlgodClient`
    :param app_id: Permission dApp identifier
    :type app_id: int
    :param box_name: base64 encoded box name
    :type box_name: str
    :var response: application box fetch response
    :type response: dict
    :return: list, or None
    """
    try:
        response = client.application_box_by_name(app_id, box_name)
    except AlgodHTTPError:
        return None
    return deserialize_values_data(
        base64.b64decode(response.get("value")).decode("utf8")
    )


class PermissionDappProvider(PermissionProvider):
    """Permission backend backed by the on-chain Permission dApp and Subtopia."""

    def votes_and_permission(self, address):
        """Fetch votes and permission for an address from the Permission dApp.

        :param address: public Algorand address
        :type address: str
        :var box_name: base64 encoded box name
        :type box_name: str
        :var values: deserialized box values
        :type values: list
        :return: two-tuple
        """
        box_name = box_name_from_address(address)
        values = _deserialized_box_value(
            _mainnet_algod_client(), PERMISSION_APP_ID, box_name
        )
        return tuple(values[:2]) if values is not None else (0, 0)

    def subscriptions(self, address):
        """Fetch and format the address's subscriptions for the profile page.

        :param address: public Algorand address
        :type address: str
        :var subscriptions: raw subscription data from chain
        :type subscriptions: object
        :return: render-ready collection, or None
        """
        subscriptions = fetch_subscriptions_for_address(
            _mainnet_algod_client(), address
        )
        if not subscriptions:
            return None
        return formatted_subscription_timestamps(subscriptions)

    def refresh(self):
        """Update the mainnet Permission dApp boxes from chain.

        :return: None
        """
        check_and_update_permission_dapp_boxes(network="mainnet")

    def tier_link(self, tier_name):
        """Return Subtopia tier link markup for a tier name.

        :param tier_name: subscription tier name
        :type tier_name: str
        :return: str
        """
        return _format_tier_name_as_link(tier_name)
