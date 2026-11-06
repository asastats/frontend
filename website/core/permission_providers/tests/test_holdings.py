"""Testing module for :py:mod:`core.permission_providers.holdings` module."""

import base64
from datetime import UTC, datetime, timedelta

import pytest
from algosdk.logic import get_application_address
from django.contrib.auth.models import User

from core.models import AddressHolding
from core.permission_providers import holdings
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from walletauth.models import LinkedAddress

MODULE = "core.permission_providers.holdings"
ADDRESS = "A" * 58
OTHER = "B" * 58
INSIDE_WEEK = datetime(2026, 11, 12, tzinfo=UTC)
AFTER_WEEK = datetime(2026, 11, 20, tzinfo=UTC)


def _tokens(amount):
    return amount * holdings.MICRO


def _hold(address, amount, at):
    AddressHolding.objects.create(address=address, weight=_tokens(amount), at=at)


def _profile(username="holder", address=ADDRESS, authorized="proof", at=None):
    profile = User.objects.create(username=username).profile
    profile.address = address
    profile.authorized = authorized
    profile.authorized_at = at or INSIDE_WEEK
    profile.save()
    return profile


class TestHoldingSince:
    """Testing class for :py:func:`holdings.holding_since`."""

    def _rows(self, *rows):
        return [(address, _tokens(amount), at) for address, amount, at in rows]

    def test_holding_since_returns_none_for_no_rows(self):
        assert holdings.holding_since([], 1, INSIDE_WEEK) is None

    def test_holding_since_returns_start_of_holding(self):
        rows = self._rows((ADDRESS, 10, INSIDE_WEEK))
        assert holdings.holding_since(rows, _tokens(10), AFTER_WEEK) == INSIDE_WEEK

    def test_holding_since_sums_addresses(self):
        later = INSIDE_WEEK + timedelta(days=1)
        rows = self._rows((ADDRESS, 6, INSIDE_WEEK), (OTHER, 4, later))
        assert holdings.holding_since(rows, _tokens(10), AFTER_WEEK) == later

    def test_holding_since_moving_between_own_addresses_keeps_the_start(self):
        later = INSIDE_WEEK + timedelta(days=1)
        rows = self._rows(
            (ADDRESS, 10, INSIDE_WEEK), (ADDRESS, 0, later), (OTHER, 10, later)
        )
        assert holdings.holding_since(rows, _tokens(10), AFTER_WEEK) == INSIDE_WEEK

    def test_holding_since_returns_none_after_a_drop(self):
        later = INSIDE_WEEK + timedelta(days=1)
        rows = self._rows((ADDRESS, 10, INSIDE_WEEK), (ADDRESS, 9, later))
        assert holdings.holding_since(rows, _tokens(10), AFTER_WEEK) is None

    def test_holding_since_keeps_the_start_inside_the_grace(self):
        later = INSIDE_WEEK + timedelta(days=1)
        rows = self._rows((ADDRESS, 10, INSIDE_WEEK), (ADDRESS, 9, later))
        now = later + timedelta(minutes=30)
        assert holdings.holding_since(rows, _tokens(10), now) == INSIDE_WEEK

    def test_holding_since_short_dip_keeps_the_start(self):
        dip = INSIDE_WEEK + timedelta(days=1)
        rows = self._rows(
            (ADDRESS, 10, INSIDE_WEEK),
            (ADDRESS, 9, dip),
            (ADDRESS, 10, dip + timedelta(minutes=15)),
        )
        assert holdings.holding_since(rows, _tokens(10), AFTER_WEEK) == INSIDE_WEEK

    def test_holding_since_long_dip_restarts(self):
        dip = INSIDE_WEEK + timedelta(days=1)
        back = dip + timedelta(hours=2)
        rows = self._rows(
            (ADDRESS, 10, INSIDE_WEEK), (ADDRESS, 9, dip), (ADDRESS, 10, back)
        )
        assert holdings.holding_since(rows, _tokens(10), AFTER_WEEK) == back


@pytest.mark.django_db
class TestEarnedPermission:
    """Testing class for :py:func:`holdings.earned_permission`."""

    def test_earned_permission_is_zero_before_the_start(self):
        profile = _profile()
        _hold(ADDRESS, 500_000, datetime(2026, 11, 7, tzinfo=UTC))
        now = holdings.HOLDING_START - timedelta(seconds=1)
        assert holdings.earned_permission(profile, now) == 0

    def test_earned_permission_existing_holding_counts_at_the_start(self):
        profile = _profile()
        _hold(ADDRESS, 500_000, datetime(2026, 11, 7, tzinfo=UTC))
        assert (
            holdings.earned_permission(profile, holdings.HOLDING_START)
            == SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        )

    @pytest.mark.parametrize(
        "amount,tier",
        [
            (50_000, "Intro"),
            (500_000, "Asastatser"),
            (5_000_000, "Professional"),
            (50_000_000, "Cluster"),
        ],
    )
    def test_earned_permission_thresholds(self, amount, tier):
        profile = _profile()
        _hold(ADDRESS, amount, INSIDE_WEEK)
        assert (
            holdings.earned_permission(profile, INSIDE_WEEK)
            == SUBSCRIPTION_TIER_PERMISSIONS[tier]
        )

    def test_earned_permission_is_zero_below_the_lowest_threshold(self):
        profile = _profile()
        _hold(ADDRESS, 49_999, INSIDE_WEEK)
        assert holdings.earned_permission(profile, INSIDE_WEEK) == 0

    def test_earned_permission_start_in_the_last_moment_of_the_week_has_no_wait(self):
        profile = _profile()
        moment = holdings.NO_WAIT_END - timedelta(seconds=1)
        _hold(ADDRESS, 500_000, moment)
        assert holdings.earned_permission(profile, moment) > 0

    def test_earned_permission_start_after_the_week_waits_30_days(self):
        profile = _profile()
        _hold(ADDRESS, 500_000, holdings.NO_WAIT_END)
        almost = holdings.NO_WAIT_END + timedelta(days=30, seconds=-1)
        assert holdings.earned_permission(profile, almost) == 0
        assert (
            holdings.earned_permission(profile, almost + timedelta(seconds=1))
            == SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        )

    def test_earned_permission_week_holder_keeps_it_after_the_week(self):
        profile = _profile()
        _hold(ADDRESS, 500_000, INSIDE_WEEK)
        assert holdings.earned_permission(profile, AFTER_WEEK) > 0

    def test_earned_permission_drop_in_the_week_then_return_after_it_waits(self):
        profile = _profile()
        _hold(ADDRESS, 500_000, INSIDE_WEEK)
        _hold(ADDRESS, 0, INSIDE_WEEK + timedelta(days=1))
        _hold(ADDRESS, 500_000, holdings.NO_WAIT_END + timedelta(days=1))
        assert holdings.earned_permission(profile, AFTER_WEEK) == 0

    def test_earned_permission_top_up_waits_only_for_the_higher_tier(self):
        profile = _profile()
        _hold(ADDRESS, 500_000, INSIDE_WEEK)
        _hold(ADDRESS, 5_000_000, holdings.NO_WAIT_END + timedelta(days=1))
        assert (
            holdings.earned_permission(profile, AFTER_WEEK)
            == SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        )

    def test_earned_permission_is_zero_for_unauthorized_profile(self):
        profile = _profile(authorized="")
        _hold(ADDRESS, 500_000, INSIDE_WEEK)
        assert holdings.earned_permission(profile, INSIDE_WEEK) == 0

    def test_earned_permission_sums_linked_addresses(self):
        profile = _profile()
        LinkedAddress.objects.create(
            profile=profile,
            address=OTHER,
            canonical_address=OTHER,
            chain="algorand",
            auth_method="algorand_wallet",
        )
        _hold(ADDRESS, 250_000, INSIDE_WEEK)
        _hold(OTHER, 250_000, INSIDE_WEEK)
        assert (
            holdings.earned_permission(profile, INSIDE_WEEK)
            == SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        )

    def test_earned_permission_repeated_address_counts_for_the_first_account(self):
        first = _profile("first", at=INSIDE_WEEK - timedelta(days=1))
        second = _profile("second")
        _hold(ADDRESS, 500_000, INSIDE_WEEK)
        assert holdings.earned_permission(first, INSIDE_WEEK) > 0
        assert holdings.earned_permission(second, INSIDE_WEEK) == 0


def _state(**values):
    return [
        {"key": base64.b64encode(key.encode()).decode(), "value": {"uint": value}}
        for key, value in values.items()
    ]


class TestStateValues:
    """Testing class for :py:func:`holdings._state_values`."""

    def test_state_values_returns_values_in_the_order_of_keys(self):
        state = _state(A=1, B=2, L=3)
        assert holdings._state_values(state, ("L", "A")) == [3, 1]

    def test_state_values_raises_for_a_missing_key(self):
        with pytest.raises(KeyError):
            holdings._state_values(_state(A=1), ("L",))


class TestPools:
    """Testing class for :py:func:`holdings._pools`."""

    def test_pools_reads_every_allowlisted_pool(self, mocker):
        client = mocker.MagicMock()
        pact_state = {
            "reserve_a": 1,
            "reserve_b": 2,
            "issued_lp": 3,
            "A": 4,
            "B": 5,
            "L": 6,
        }
        client.applications.return_value = {
            "application": {"params": {"global-state": _state(**pact_state)}}
        }
        client.account_info.return_value = {
            "account": {
                "apps-local-state": [
                    {
                        "key-value": _state(
                            asset_1_reserves=7,
                            asset_2_reserves=8,
                            issued_pool_tokens=9,
                        )
                    }
                ]
            }
        }
        assert holdings._pools(client) == [
            (3684485531, get_application_address(3684485528), 1, 2, 3),
            (2757667448, get_application_address(2757667443), 4, 5, 6),
            (1129173576, get_application_address(1129173571), 4, 5, 6),
            (holdings.TINYMAN_LP, holdings.TINYMAN_POOL, 7, 8, 9),
        ]
        client.account_info.assert_called_once_with(holdings.TINYMAN_POOL)


class TestReadWeights:
    """Testing class for :py:func:`holdings.read_weights`."""

    def _client(self, mocker, wallets, lp=None):
        client = mocker.MagicMock()
        balances = {holdings.ASASTATS_ID: wallets, **(lp or {})}
        client.asset_balances.side_effect = lambda asset_id, **kwargs: {
            "balances": [
                {"address": address, "amount": amount}
                for address, amount in balances.get(asset_id, {}).items()
            ]
        }
        return client

    def test_read_weights_counts_lp_at_total_value_at_the_reference_price(self, mocker):
        algo = 1_000 * holdings.MICRO
        tokens = algo * holdings.REFERENCE_ASASTATS_PER_ALGO
        mocker.patch(
            f"{MODULE}._pools",
            return_value=[(7, "POOL", algo, tokens, 1000)],
        )
        client = self._client(
            mocker,
            {ADDRESS: holdings.ASASTATS_SUPPLY},
            {7: {OTHER: 100, "POOL": 900}},
        )
        weights = holdings.read_weights(client)
        assert weights[OTHER] == 2 * tokens // 10
        assert "POOL" not in weights

    def test_read_weights_price_move_leaves_the_lp_value_unchanged(self, mocker):
        algo = 1_000 * holdings.MICRO
        tokens = algo * holdings.REFERENCE_ASASTATS_PER_ALGO
        mocker.patch(f"{MODULE}._pools", return_value=[(7, "POOL", algo * 4, tokens // 4, 10)])
        client = self._client(mocker, {ADDRESS: holdings.ASASTATS_SUPPLY}, {7: {OTHER: 1}})
        assert holdings.read_weights(client)[OTHER] == 2 * tokens // 10

    def test_read_weights_refuses_incomplete_balances(self, mocker):
        client = self._client(mocker, {ADDRESS: 5})
        with pytest.raises(ValueError):
            holdings.read_weights(client)


@pytest.mark.django_db
class TestRecordWeights:
    """Testing class for :py:func:`holdings.record_weights`."""

    def test_record_weights_writes_only_changes(self):
        assert holdings.record_weights({ADDRESS: 100}, INSIDE_WEEK) == 1
        assert holdings.record_weights({ADDRESS: 100}, AFTER_WEEK) == 0

    def test_record_weights_records_a_vanished_address_as_zero(self):
        holdings.record_weights({ADDRESS: 100}, INSIDE_WEEK)
        assert holdings.record_weights({}, AFTER_WEEK) == 1
        assert AddressHolding.objects.latest("at").weight == 0

    def test_record_weights_skips_small_drift(self):
        start = _tokens(1_000_000)
        holdings.record_weights({ADDRESS: start}, INSIDE_WEEK)
        assert holdings.record_weights({ADDRESS: start + 1000}, AFTER_WEEK) == 0

    def test_record_weights_small_change_across_a_threshold_is_recorded(self):
        below = _tokens(500_000) - 1
        holdings.record_weights({ADDRESS: below}, INSIDE_WEEK)
        assert holdings.record_weights({ADDRESS: below + 1}, AFTER_WEEK) == 1


@pytest.mark.django_db
class TestSyncHoldings:
    """Testing class for :py:func:`holdings.sync_holdings`."""

    @pytest.fixture(autouse=True)
    def _provider(self, mocker, settings):
        mocker.patch(
            "core.permission_providers.permissiondapp."
            "PermissionDappProvider.votes_and_permission",
            return_value=(0, 7),
        )
        mocker.patch("core.permission_providers.permissiondapp.holdings.timezone.now",
                     return_value=INSIDE_WEEK)

    def test_sync_holdings_grants_and_keeps_the_higher_paid_value(self, mocker):
        profile = _profile()
        mocker.patch(f"{MODULE}.read_weights", return_value={ADDRESS: _tokens(500_000)})
        assert holdings.sync_holdings(INSIDE_WEEK) == (1, 1)
        profile.refresh_from_db()
        earned = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        assert (profile.permission, profile.earned_permission) == (earned, earned)

    def test_sync_holdings_revokes_after_the_grace(self, mocker):
        profile = _profile()
        read = mocker.patch(
            f"{MODULE}.read_weights", return_value={ADDRESS: _tokens(500_000)}
        )
        holdings.sync_holdings(INSIDE_WEEK)
        read.return_value = {}
        later = INSIDE_WEEK + timedelta(hours=2)
        mocker.patch(f"{MODULE}.timezone.now", return_value=later)
        assert holdings.sync_holdings(later) == (1, 0)
        mocker.patch(f"{MODULE}.timezone.now", return_value=later + timedelta(hours=2))
        assert holdings.sync_holdings(later + timedelta(hours=2)) == (0, 1)
        profile.refresh_from_db()
        assert (profile.permission, profile.earned_permission) == (7, 0)

    def test_sync_holdings_failed_read_changes_nothing(self, mocker):
        _profile()
        mocker.patch(f"{MODULE}.read_weights", side_effect=ValueError)
        with pytest.raises(ValueError):
            holdings.sync_holdings(INSIDE_WEEK)
        assert not AddressHolding.objects.exists()

    def test_sync_holdings_skips_profiles_without_a_holding(self, mocker):
        _profile()
        check = mocker.patch("core.models.Profile.check_votes_and_permission")
        mocker.patch(f"{MODULE}.read_weights", return_value={ADDRESS: 5})
        holdings.sync_holdings(INSIDE_WEEK)
        check.assert_not_called()

    def test_sync_holdings_one_failing_profile_does_not_stop_the_others(self, mocker):
        _profile()
        _profile("second", address=OTHER)
        check = mocker.patch(
            "core.models.Profile.check_votes_and_permission",
            side_effect=[RuntimeError, None],
        )
        mocker.patch(
            f"{MODULE}.read_weights",
            return_value={ADDRESS: _tokens(500_000), OTHER: _tokens(500_000)},
        )
        assert holdings.sync_holdings(INSIDE_WEEK) == (2, 1)
        assert check.call_count == 2


@pytest.mark.django_db
class TestHoldingStatusAndTerms:
    """Testing class for the page data of :py:mod:`holdings`."""

    def test_holding_status_is_none_for_unauthorized_profile(self):
        profile = _profile(authorized="")
        _hold(ADDRESS, 500_000, INSIDE_WEEK)
        assert holdings.holding_status(profile, INSIDE_WEEK) is None

    def test_holding_status_is_none_below_the_lowest_threshold(self):
        profile = _profile()
        _hold(ADDRESS, 10, INSIDE_WEEK)
        assert holdings.holding_status(profile, INSIDE_WEEK) is None

    def test_holding_status_shows_the_tier_and_the_next_one(self):
        profile = _profile()
        _hold(ADDRESS, 500_000, INSIDE_WEEK)
        moment = holdings.NO_WAIT_END + timedelta(days=1)
        _hold(ADDRESS, 5_000_000, moment)
        assert holdings.holding_status(profile, AFTER_WEEK) == {
            "held": 5_000_000,
            "tier": "Asastatser",
            "next_tier": "Professional",
            "next_date": moment + timedelta(days=30),
        }

    def test_holding_terms_pool_amount_is_half_of_the_wallet_amount(self):
        rows = holdings.holding_terms()["rows"]
        assert rows[0] == {"tier": "Intro", "wallet": 50_000, "pool": 25_000}
        assert [row["tier"] for row in rows][-1] == "Cluster"


@pytest.mark.django_db
class TestHoldingPages:
    """Testing class for the holding markup on the subscriptions and profile pages."""

    def test_subscriptions_page_shows_the_holding_table(self, client, mocker):
        mocker.patch(
            "core.context_processors.fetch_capabilities",
            return_value={"permission": 0},
        )
        content = client.get("/subscriptions/").content.decode()
        assert 'id="holding"' in content
        assert "250,000" in content

    def test_profile_page_shows_the_holding_status(self, client, mocker):
        mocker.patch(
            "core.context_processors.fetch_capabilities",
            return_value={"permission": 0},
        )
        mocker.patch(
            "core.permission_providers.permissiondapp."
            "PermissionDappProvider.subscriptions",
            return_value=None,
        )
        mocker.patch(
            "core.permission_providers.permissiondapp."
            "PermissionDappProvider.votes_and_permission",
            return_value=(0, 0),
        )
        profile = _profile()
        _hold(ADDRESS, 500_000, INSIDE_WEEK)
        client.force_login(profile.user)
        content = client.get("/profile/").content.decode()
        assert 'id="holding-status"' in content
        assert "500,000 ASASTATS" in content
