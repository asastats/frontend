"""Block-time answers for API callers entitled to them.

The engine's live pass re-prices a watched page every block and publishes two
different things for two different readers. A browser gets a *diff* (`lvp`),
because it is holding the rendered page and swaps fragments into it. A REST
caller holds nothing and its first request must be a whole account, so it gets
a serialized one (`lvn`), and only for pages named in `lva`, which this module
writes.

    lvx   pages the pass should re-price      written here and by the widget
    lva   pages that also want a snapshot     written here alone
    lvn   the snapshot itself                 read here, written by the engine
    lvnh  the fingerprint that snapshot is of read here, written by the engine

`lvn:` holds a serialized account and nothing else. This module serves it to
entitled callers, so its shape is a contract: the two services sync separately,
minutes out of step is ordinary, and an engine deployed first must not be able
to change what a caller receives. Anything the browser's live widget needs
*about* a snapshot goes in a key beside it.

**No failure here is an error.** Every function degrades to "no snapshot",
which is the cached answer the caller got last week. An API that 500s because
the live pass is down would be worse than one serving data a minute old.
"""

import logging
import time

from algosdk.constants import ADDRESS_LEN
from django.conf import settings

from api.tiers import block_time
from api.widgets import page_key_from_addresses
from utils.clients import redis_instance

logger = logging.getLogger(__name__)

#: Pages the pass re-prices, and those among them that also want a snapshot.
#: Scored by the unix time last asked for; the engine's 90-second read window
#: ages them out, so there is no unsubscribe to keep in step.
SUBSCRIBED_KEY = "lvx"
API_WARM_KEY = "lva"
#: Where the engine publishes a serialized account for an `lva` page.
SNAPSHOT_PREFIX = "lvn"
#: The fingerprint that snapshot describes. Beside `lvn:` rather than inside
#: it, because that key's shape is an API contract. The engine writes it as
#: `CACHE_KEY_LIVE_SNAPSHOT_HOLDINGS`.
SNAPSHOT_HOLDINGS_PREFIX = "lvnh"


def _warm_set():
    """Return the widget's warm-set module and manifest, or `(None, None)`.

    Imported inside the function on purpose: these live in the widgets repo,
    which syncs separately, so a module-level import turns "the frontend is
    ahead of the widgets" into an unimportable `api.views` and a 500 on every
    page of the site.

    :return: tuple of the module and the manifest, or (None, None)
    """
    try:
        from widgets.inhouse.liverefresh import warmset
        from widgets.inhouse.liverefresh.manifest import MANIFEST
    except ImportError as error:  # noqa: BLE001 - see above
        logger.warning("api live warm set unavailable: %s", error)
        return None, None
    return warmset, MANIFEST


#: Pages the pass re-prices, and the pages among them that also want a full
#: snapshot. Written as the widget writes `lvx`: member scored by the unix time
#: it was last asked for, aged out by the engine's 90-second read window, so a
#: caller that stops asking stops costing without anything having to notice.
SUBSCRIBED_KEY = "lvx"
API_WARM_KEY = "lva"
#: Where the engine publishes a serialized account for an `lva` page.
SNAPSHOT_PREFIX = "lvn"
#: The fingerprint that snapshot describes, beside it rather than inside it -
#: this process serves `lvn:` to API callers, so its shape is a contract an
#: engine deploy must not be able to change. See the engine's
#: `CACHE_KEY_LIVE_SNAPSHOT_HOLDINGS`.
SNAPSHOT_HOLDINGS_PREFIX = "lvnh"


def subscribing_enabled():
    """Return whether this deployment lets API callers warm pages at all.

    Off by default. Subscribing is the first thing here that costs the *engine*
    something per block, and it starts the moment an entitled caller makes a
    request, so it is turned on deliberately rather than by being deployed.

    :return: bool
    """
    return getattr(settings, "API_LIVE_ENABLED", False)


def is_shared_token(user_pk):
    """Return whether this account is a credential many people share.

    A per-account cap measures a person, and these accounts are a population:
    the mobile app ships one baked credential for its whole installed base.
    Letting it subscribe would put every address any phone user glanced at into
    the live pass, and spend one warm set of five between all of them. Excluded
    by name rather than by tier, so an upgrade cannot quietly admit it.
    `WIDGETS_API_TOKEN` has the same shape and belongs in the same list.

    :param user_pk: the caller's primary key
    :type user_pk: int
    :return: bool
    """
    return user_pk in getattr(settings, "API_LIVE_SHARED_TOKEN_USER_IDS", frozenset())


def wants_block_time(permission):
    """Return whether this caller's tier includes block-time data.

    Read from `api/tiers.py`, which is the table that decides it. A permission
    constant here would be a second answer to the same question.

    :param permission: the caller's permission integer
    :type permission: int
    :return: bool
    """
    return block_time(permission)


def page_key(value, addresses):
    """Return the key the engine publishes this page under.

    A bundle is keyed by its hash and a single address by itself, matching what
    `_live_page` computes on the other side.

    **Derived from the addresses whenever there are any**, because a bundle hash
    naming one address is a page a reader can visit and the engine keys it by
    that address rather than by the hash. `value` answers only when the caller
    has no addresses to offer, which is how a single-address request arrives.

    :param value: single address, or the bundle hash from the path
    :type value: str
    :param addresses: space-joined addresses for a multi-address bundle
    :type addresses: str
    :return: str
    """
    return page_key_from_addresses(addresses) or value


def subscribe(value, addresses, user_pk, permission, client=None, now=None):
    """Ask the pass to keep this page warm, and report whether it fits.

    True means the page is now warm for this reader. False means they are over
    their warm-set cap and nothing was subscribed - they still get an answer,
    from the cached path, exactly as they did before this existed.

    `touch(evict=False)` admits the whole bundle or none of it. Half a bundle
    kept warm is a response where some rows are block-fresh and others are a
    minute old, with nothing in it saying which. The browser's half of this
    evicts instead, because a tab that silently goes static is a better failure
    than an error on a page nobody is looking at.

    :param value: single address, or the bundle hash from the path
    :type value: str
    :param addresses: space-joined addresses for a multi-address bundle
    :type addresses: str
    :param user_pk: the caller's primary key, which is what the cap is per
    :type user_pk: int
    :param permission: the caller's permission integer
    :type permission: int
    :param client: Redis client instance, for tests
    :type client: :class:`Redis`
    :param now: unix time to score the touch with, for tests
    :type now: float
    :return: bool
    """
    if not subscribing_enabled():
        return False

    if not wants_block_time(permission) or not user_pk:
        return False

    # Not a tier question: an account may be entitled twice over and still
    # must not subscribe.
    if is_shared_token(user_pk):
        return False

    # A bundle hash that did not resolve. `addresses` is falsy for a single
    # address too, so without this `addresses or value` writes the hash into
    # `lvx`, where the pass fetches it as an account. See docs/logbook.md.
    if len(value) != ADDRESS_LEN and not addresses:
        return False

    warmset, manifest = _warm_set()
    if warmset is None:
        # No cap can be applied, and an unbounded warm set is a worse answer
        # than a cached one.
        return False

    members = addresses.split() if addresses else [value]
    now = time.time() if now is None else now
    try:
        client = redis_instance() if client is None else client
        # The widget's own bands, so one tier change cannot land in one surface
        # and not the other.
        cap = warmset.cap_for(permission, manifest.required_permission)
        admitted, _ = warmset.touch(user_pk, members, cap, client, now, evict=False)
        if not admitted:
            return False

        page = page_key(value, addresses)
        # `lvx` members are address strings; `lva` members are page keys. That
        # is what the widget writes and what `_live_page` tests membership with.
        client.zadd(SUBSCRIBED_KEY, {addresses or value: now})
        client.zadd(API_WARM_KEY, {page: now})
    except Exception as error:  # noqa: BLE001 - see the module docstring
        logger.warning("api live subscribe failed: %s", error, exc_info=True)
        return False
    return True


def snapshot(value, addresses, client=None):
    """Return the account the pass published this block, or None.

    None means "serve it the way it has always been served" - the engine call
    behind a 60-second cache. That is the answer on the first request of a new
    subscription too, because the page is not warm until a block has passed
    over it, so a caller's first call is always the cached one and every
    call after it is fresh.

    :param value: single address, or the bundle hash from the path
    :type value: str
    :param addresses: space-joined addresses for a multi-address bundle
    :type addresses: str
    :param client: Redis client instance, for tests
    :type client: :class:`Redis`
    :return: dict or None
    """
    return (stamped_snapshot(value, addresses, client) or (None, ""))[0]


def stamped_snapshot(value, addresses, client=None):
    """Return `(account, holdings fingerprint)` for a page, or None.

    The fingerprint is for the browser's reader, which re-renders one venue
    group from this instead of reloading the page and then writes onto the page
    the fingerprint it has caught up to. It needs the one this snapshot
    describes, not the one last published. An API caller has nothing to compare
    against and uses `snapshot`.

    An engine that predates `lvnh:` leaves it absent, which comes back as "" and
    every caller must read as "cannot tell" rather than as a fingerprint.

    One `MGET`, so the pair is the pair the engine wrote rather than a
    fingerprint from one block against an account from the next.

    :param value: single address, or the bundle hash from the path
    :type value: str
    :param addresses: space-joined addresses for a multi-address bundle
    :type addresses: str
    :param client: Redis client instance, for tests
    :type client: :class:`Redis`
    :return: tuple of (dict, str), or None
    """
    import msgpack

    try:
        client = redis_instance() if client is None else client
        page = page_key(value, addresses)
        raw, holdings = client.mget(
            f"{SNAPSHOT_PREFIX}:{page}", f"{SNAPSHOT_HOLDINGS_PREFIX}:{page}"
        )
        if not raw:
            return None
        if isinstance(holdings, bytes):
            holdings = holdings.decode()
        # These structures are keyed by asset id and msgpack refuses integer
        # keys by default.
        return msgpack.unpackb(raw, strict_map_key=False), holdings or ""
    except Exception as error:  # noqa: BLE001 - see the module docstring
        logger.warning("api live snapshot unreadable: %s", error, exc_info=True)
        return None
