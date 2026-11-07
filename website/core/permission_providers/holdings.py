"""Permission from holding ASASTATS or its LP tokens, read from public chain data.

Why it is built this way: ``docs/logbook.md``.
"""

import base64
import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from math import isqrt

from algosdk.logic import get_application_address
from django.utils import timezone

from core.models import AddressHolding, Profile
from utils.clients import indexer_instance
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from walletauth.models import LinkedAddress

logger = logging.getLogger(__name__)

ASASTATS_ID = 393537671
ASASTATS_SUPPLY = 10**15
MICRO = 10**6

#: Whole tokens, highest first. Removing a row makes that tier subscription-only.
HOLDING_THRESHOLDS = (
    ("Cluster", 50_000_000),
    ("Professional", 5_000_000),
    ("Asastatser", 500_000),
    ("Intro", 50_000),
)
HOLDING_START = datetime(2026, 11, 9, tzinfo=UTC)
#: Pages say nothing about holding before this moment: the launch is a surprise.
HOLDING_PUBLIC_FROM = HOLDING_START
#: A holding that starts before this moment has no waiting period.
NO_WAIT_END = datetime(2026, 11, 16, tzinfo=UTC)
WAITING_PERIOD = timedelta(days=30)
#: Below a threshold for less than this is not a drop: the reads are not atomic.
DROP_GRACE = timedelta(hours=1)
#: Fixed on purpose: a live price would let price moves take access away.
REFERENCE_ASASTATS_PER_ALGO = 6020
#: LP value drifts with fees; smaller changes are not worth a row.
MIN_RECORDED_CHANGE = 0.005

TINYMAN_POOL = "UXOJX6NJDGLJ3KALT3JYGGGXFPXJIKMWJZTXSLB2KAVY5O7WJHPA2B3HJE"
#: (LP asset, Pact application, its reserve and issued LP keys)
PACT_POOLS = (
    (3684485531, 3684485528, ("reserve_a", "reserve_b", "issued_lp")),
    (2757667448, 2757667443, ("A", "B", "L")),
    (1129173576, 1129173571, ("A", "B", "L")),
)
#: (LP asset, farm application, staked key in the wallet's state, total staked key).
#: A farm has to be listed before it opens: unlisted, staking reads as selling.
PACT_FARMS = (
    (3684485531, 3736990647, "staked", "total_staked"),
    (3684485531, 3689996789, "Staked", "TotalStaked"),
    (2757667448, 2966663202, "Staked", "TotalStaked"),
    (1129173576, 1140566471, "Staked", "TotalStaked"),
)
TINYMAN_LP = 1002623676
TINYMAN_KEYS = ("asset_1_reserves", "asset_2_reserves", "issued_pool_tokens")


def _state_uints(key_value):
    """Return the unsigned integers of an on-chain state, keyed by decoded key.

    :param key_value: application state items, as the Indexer returns them
    :type key_value: list
    :return: dict
    """
    return {
        base64.b64decode(item["key"]).decode("latin1"): item["value"].get("uint")
        for item in key_value
    }


def _state_values(key_value, keys):
    """Return the unsigned integers stored under `keys` in an on-chain state.

    :param key_value: application state items, as the Indexer returns them
    :type key_value: list
    :param keys: state keys to read
    :type keys: tuple
    :return: list
    """
    state = _state_uints(key_value)
    return [state[key] for key in keys]


def _asset_balances(client, asset_id):
    """Return every non-zero balance of an asset, keyed by address.

    :param client: Indexer client
    :type client: :class:`algosdk.v2client.indexer.IndexerClient`
    :param asset_id: asset identifier
    :type asset_id: int
    :return: dict
    """
    balances, next_page = {}, None
    while True:
        response = client.asset_balances(
            asset_id, limit=1000, next_page=next_page
        )
        balances.update(
            (item["address"], item["amount"])
            for item in response["balances"]
            if item["amount"]
        )
        next_page = response.get("next-token")
        if not next_page:
            return balances


def _farm_stakes(client, farm_app, staked_key, total_key):
    """Return every non-zero stake in a Pact farm, keyed by the staker's wallet.

    Raises if the stakes miss the farm's total, as a partial list would read as selling.

    :param client: Indexer client
    :type client: :class:`algosdk.v2client.indexer.IndexerClient`
    :param farm_app: farm application identifier
    :type farm_app: int
    :param staked_key: key of the stake in the wallet's local state
    :type staked_key: str
    :param total_key: key of the farm's total in its global state
    :type total_key: str
    :return: dict
    """
    stakes, next_page = {}, None
    while True:
        response = client.accounts(
            application_id=farm_app,
            limit=1000,
            next_page=next_page,
            exclude="assets,created-assets,created-apps",
        )
        for account in response["accounts"]:
            for state in account.get("apps-local-state", []):
                if state["id"] == farm_app:
                    staked = _state_uints(state.get("key-value", [])).get(staked_key)
                    if staked:
                        stakes[account["address"]] = staked

        next_page = response.get("next-token")
        if not next_page:
            break

    app_state = client.applications(farm_app)["application"]["params"]["global-state"]
    if sum(stakes.values()) != _state_values(app_state, (total_key,))[0]:
        raise ValueError(f"Incomplete stakes in Pact farm {farm_app}")

    return stakes


def _lp_positions(client, lp_asset, pool_address):
    """Return each address's LP tokens, in its wallet plus staked in listed farms.

    :param client: Indexer client
    :type client: :class:`algosdk.v2client.indexer.IndexerClient`
    :param lp_asset: LP asset identifier
    :type lp_asset: int
    :param pool_address: pool account, left out
    :type pool_address: str
    :return: dict
    """
    positions = defaultdict(int, _asset_balances(client, lp_asset))
    positions.pop(pool_address, None)
    # Farms after wallets: staking mid-read then counts high, never low.
    for farm_lp, farm_app, staked_key, total_key in PACT_FARMS:
        if farm_lp == lp_asset:
            stakes = _farm_stakes(client, farm_app, staked_key, total_key)
            for address, staked in stakes.items():
                positions[address] += staked

    return positions


def _pools(client):
    """Return allowlisted pools as (LP asset, pool address, x, y, issued LP).

    :param client: Indexer client
    :type client: :class:`algosdk.v2client.indexer.IndexerClient`
    :return: list
    """
    pools = []
    for lp_asset, app_id, keys in PACT_POOLS:
        state = client.applications(app_id)["application"]["params"]["global-state"]
        pools.append(
            (lp_asset, get_application_address(app_id), *_state_values(state, keys))
        )

    account = client.account_info(TINYMAN_POOL)["account"]
    state = account["apps-local-state"][0]["key-value"]
    pools.append((TINYMAN_LP, TINYMAN_POOL, *_state_values(state, TINYMAN_KEYS)))
    return pools


def read_weights(client=None):
    """Return each address's holding in base units, with LP at its total value.

    Raises on any failed read, because a partial result would look like selling.

    :param client: Indexer client
    :type client: :class:`algosdk.v2client.indexer.IndexerClient`
    :var weights: holding per address
    :type weights: dict
    :return: dict
    """
    client = client or indexer_instance()
    # Wallets first: adding liquidity mid-read then counts high, never low.
    wallets = _asset_balances(client, ASASTATS_ID)
    if not 0.99 * ASASTATS_SUPPLY <= sum(wallets.values()) <= ASASTATS_SUPPLY:
        raise ValueError("Incomplete ASASTATS balances")

    weights = defaultdict(int, wallets)
    for lp_asset, pool_address, reserve_x, reserve_y, issued in _pools(client):
        root = isqrt(reserve_x * reserve_y * REFERENCE_ASASTATS_PER_ALGO)
        for address, amount in _lp_positions(client, lp_asset, pool_address).items():
            weights[address] += 2 * amount * root // issued

    return dict(weights)


def _bucket(weight):
    """Return how many holding thresholds `weight` reaches.

    :param weight: holding in base units
    :type weight: int
    :return: int
    """
    return sum(weight >= tokens * MICRO for _, tokens in HOLDING_THRESHOLDS)


def record_weights(weights, now=None):
    """Append a row for every address whose holding changed.

    :param weights: holding per address
    :type weights: dict
    :param now: moment of the reading
    :type now: :class:`datetime.datetime`
    :return: int
    """
    now = now or timezone.now()
    latest = dict(
        AddressHolding.objects.order_by("address", "-at")
        .distinct("address")
        .values_list("address", "weight")
    )
    rows = []
    for address in latest.keys() | weights.keys():
        old, new = latest.get(address, 0), weights.get(address, 0)
        if old == new:
            continue

        if (
            old
            and new
            and _bucket(old) == _bucket(new)
            and abs(new - old) < old * MIN_RECORDED_CHANGE
        ):
            continue

        rows.append(AddressHolding(address=address, weight=new, at=now))

    AddressHolding.objects.bulk_create(rows, batch_size=1000)
    return len(rows)


def _counted_addresses(profile):
    """Return the addresses this profile may count; each address counts once.

    :param profile: authorized profile
    :type profile: :class:`core.models.Profile`
    :return: set
    """
    addresses = set(
        LinkedAddress.objects.filter(profile=profile).values_list(
            "canonical_address", flat=True
        )
    )
    primary = profile.algorand_address
    if primary and primary not in addresses:
        # The note flow makes no LinkedAddress row and can repeat an address.
        linked = LinkedAddress.objects.filter(canonical_address=primary).exists()
        first = (
            Profile.objects.filter(address=profile.address)
            .exclude(authorized="")
            .order_by("authorized_at", "id")
            .first()
        )
        if not linked and first is not None and first.pk == profile.pk:
            addresses.add(primary)

    return addresses


def holding_since(rows, threshold, now):
    """Return when the unbroken holding at or above `threshold` began, or None.

    :param rows: (address, weight, moment) rows ordered by moment
    :type rows: list
    :param threshold: holding in base units
    :type threshold: int
    :param now: moment of the check
    :type now: :class:`datetime.datetime`
    :return: :class:`datetime.datetime`
    """
    current, start, below = {}, None, None
    index = 0
    while index < len(rows):
        moment = rows[index][2]
        while index < len(rows) and rows[index][2] == moment:
            current[rows[index][0]] = rows[index][1]
            index += 1

        if sum(current.values()) >= threshold:
            if start is None or (below and moment - below >= DROP_GRACE):
                start = moment
            below = None
        elif start is not None and below is None:
            below = moment

    if start is None or (below and now - below >= DROP_GRACE):
        return None

    return start


def _rows(profile):
    """Return the holding history of a profile's counted addresses, oldest first.

    :param profile: authorized profile
    :type profile: :class:`core.models.Profile`
    :return: list
    """
    return list(
        AddressHolding.objects.filter(address__in=_counted_addresses(profile))
        .order_by("at")
        .values_list("address", "weight", "at")
    )


def _available_from(since):
    """Return when a holding that began at `since` gives its permission.

    :param since: start of the holding
    :type since: :class:`datetime.datetime`
    :return: :class:`datetime.datetime`
    """
    if since < NO_WAIT_END:
        return HOLDING_START

    return since + WAITING_PERIOD


def earned_permission(profile, now=None):
    """Return the permission a profile's holding gives right now.

    :param profile: profile to check
    :type profile: :class:`core.models.Profile`
    :param now: moment of the check
    :type now: :class:`datetime.datetime`
    :return: int
    """
    now = now or timezone.now()
    if not profile.authorized or now < HOLDING_START:
        return 0

    rows = _rows(profile)
    for tier, tokens in HOLDING_THRESHOLDS:
        since = holding_since(rows, tokens * MICRO, now)
        if since is not None and now >= _available_from(since):
            return SUBSCRIPTION_TIER_PERMISSIONS[tier]

    return 0


def holding_status(profile, now=None):
    """Return what the profile page shows about a holding, or None.

    :param profile: profile to check
    :type profile: :class:`core.models.Profile`
    :param now: moment of the check
    :type now: :class:`datetime.datetime`
    :return: dict
    """
    now = now or timezone.now()
    if not profile.authorized or now < HOLDING_PUBLIC_FROM:
        return None

    rows = _rows(profile)
    current = {}
    for address, weight, _ in rows:
        current[address] = weight

    held = sum(current.values())
    if held < HOLDING_THRESHOLDS[-1][1] * MICRO:
        return None

    status = {"held": held // MICRO, "tier": None, "next_tier": None, "next_date": None}
    for tier, tokens in HOLDING_THRESHOLDS:
        since = holding_since(rows, tokens * MICRO, now)
        if since is None:
            continue

        available = _available_from(since)
        if now >= available:
            status["tier"] = tier
            break

        if status["next_tier"] is None:
            status["next_tier"], status["next_date"] = tier, available

    return status


def _pool_algo(tokens):
    """Return the ALGO beside the pool side of `tokens`, to two significant digits.

    :param tokens: wallet amount in whole tokens
    :type tokens: int
    :return: str
    """
    return f"{float(f'{tokens / 2 / REFERENCE_ASASTATS_PER_ALGO:.2g}'):,g}"


def holding_terms(now=None):
    """Return the published terms: thresholds and dates, or None before they are public.

    :param now: moment of the check
    :type now: :class:`datetime.datetime`
    :return: dict
    """
    if (now or timezone.now()) < HOLDING_PUBLIC_FROM:
        return None

    return {
        "rows": [
            {
                "tier": tier,
                "wallet": tokens,
                "pool": tokens // 2,
                "pool_algo": _pool_algo(tokens),
            }
            for tier, tokens in reversed(HOLDING_THRESHOLDS)
        ],
        "reference_price": REFERENCE_ASASTATS_PER_ALGO,
        "start": HOLDING_START,
        "last_no_wait_day": NO_WAIT_END - timedelta(days=1),
        "waiting_days": WAITING_PERIOD.days,
    }


def sync_holdings(now=None):
    """Read the chain, record changes and update profiles whose holding tier changed.

    :param now: moment of the reading
    :type now: :class:`datetime.datetime`
    :var weights: holding per address
    :type weights: dict
    :return: two-tuple of recorded rows and updated profiles
    """
    now = now or timezone.now()
    weights = read_weights()
    recorded = record_weights(weights, now)
    lowest = HOLDING_THRESHOLDS[-1][1] * MICRO
    updated = 0
    profiles = (
        Profile.objects.exclude(authorized="")
        .exclude(address="")
        .prefetch_related("linked_addresses")
    )
    for profile in profiles:
        addresses = {profile.algorand_address} | {
            linked.canonical_address for linked in profile.linked_addresses.all()
        }
        if not profile.earned_permission and (
            sum(weights.get(address, 0) for address in addresses) < lowest
        ):
            continue

        try:
            if earned_permission(profile, now) != profile.earned_permission:
                profile.check_votes_and_permission()
                updated += 1
        except Exception:  # noqa: BLE001 - one profile must not stop the others
            logger.exception("Holding sync failed for profile %s", profile.pk)

    return recorded, updated
