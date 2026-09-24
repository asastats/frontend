"""Block-time answers for API callers entitled to them.

**What the engine publishes and what this reads.** The live pass re-prices a
watched page every block. For a browser it publishes a *diff* (`lvp`) - the
figures that moved - because the browser is holding the rendered page and swaps
fragments into it. A REST caller holds nothing: its first request must be a
whole account, so a diff is no answer at all. Engine `d5e318c` therefore
publishes a second thing, a full serialized account (`lvn:{page}`), but **only
for pages named in `lva`**. This module is what names them.

    lvx   pages the pass should re-price      written here and by the widget
    lva   pages that also want a snapshot     written here alone
    lvn   the snapshot itself                 read here, written by the engine
    lvnh  the fingerprint that snapshot is of read here, written by the engine

**`lvn:` holds an account and nothing else, and that is a contract rather than
a convention.** This module serves it to entitled callers, so its shape cannot
be changed by an engine deploy that lands before a website deploy - the two
services sync separately, and minutes out of step is ordinary. Anything the
browser's live widget needs *about* a snapshot goes in a key beside it.

**Why the subscription and the cap are the same call.** Before this, an API
request cost the engine nothing per block - `website/api/` wrote none of these
keys - so capping API callers would have refused the heaviest of them for zero
saving, which is why `post-deploy/NEXT-unified-budget.md` stopped its step 3
where it did. Asking for a page to be kept warm is what makes the cap bound
something real, so the two arrive together or neither should.

**Only Professional and up.** `api/tiers.py` says freshness lands in its table
when something serves it; this is that something. Asastatser keeps the
60-second cached path it has today, which is unchanged and still what every
un-entitled caller gets.

**A failure here is never an error.** Every function degrades to "no snapshot",
which is the cached answer the caller got last week. The Redis holding these
keys belongs to the live feature, not to the API, and an API that 500s because
the live pass is down would be a worse product than one that serves data a
minute old.
"""

import logging
import time

from django.conf import settings

from api.tiers import block_time
from api.widgets import page_key_from_addresses
from utils.clients import redis_instance

logger = logging.getLogger(__name__)


def _warm_set():
    """Return the widget's warm-set module and manifest, or `(None, None)`.

    **Imported here rather than at module scope, and this is not style.** These
    live in the *widgets* repo, which is synced separately from this one, so
    "the frontend is newer than the widgets" is an ordinary state of the world
    for minutes at a time - and on 2026-09-20 it took the whole site down for
    exactly that reason. A module-level import made `api.views` unimportable,
    which made `config/urls.py` unimportable, which 500s every page on the site
    rather than the one feature that needed the module.

    This module's own docstring promises that a failure here is never an error.
    An import that cannot fail to be satisfied is the one way that promise can
    be broken before any of the guards below ever run.

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

    **Off by default, like `API_TIER_ENFORCED` beside it.** Subscribing is the
    first thing here that costs the *engine* something per block rather than
    costing this process a Redis round trip, and it starts the moment an
    entitled caller makes a request - there is no ramp. So it ships inert and is
    turned on deliberately, once the engine publishing it is deployed and once
    the shared-token question below is settled.

    :return: bool
    """
    return getattr(settings, "API_LIVE_ENABLED", False)


def is_shared_token(user_pk):
    """Return whether this account is a credential many people share.

    **A per-account limit measures a person, and a shared token is not one.**
    The mobile app ships a single baked credential for its whole installed base
    - 80 client addresses and no login - so its account is not a reader, it is a
    population. Letting it subscribe would put every address any phone user
    glanced at into the live pass to be re-priced every block, and would spend
    one warm set of five between all of them.

    `FINDING-shared-token-vs-per-account-limits.md` reaches that conclusion, and
    `RUN-mobile-token-swap.md` §4 states it as a rule: the app stays on the
    cached path and never subscribes. This is that rule in code, rather than a
    tier check that happens to exclude it today and stops doing so the moment
    somebody upgrades an account.

    `WIDGETS_API_TOKEN` has the same shape and belongs here too.

    :param user_pk: the caller's primary key
    :type user_pk: int
    :return: bool
    """
    return user_pk in getattr(settings, "API_LIVE_SHARED_TOKEN_USER_IDS", frozenset())


def wants_block_time(permission):
    """Return whether this caller's tier includes block-time data.

    **Read from `api/tiers.py`, which is the table that decides it.** A second
    permission constant here would be a second answer to the same question, and
    the two would be edited apart the first time a tier moved.

    :param permission: the caller's permission integer
    :type permission: int
    :return: bool
    """
    return block_time(permission)


def page_key(value, addresses):
    """Return the key the engine publishes this page under.

    A bundle is keyed by its hash and a single address by itself, which is what
    `_live_page` computes on the other side.

    **Derived from the addresses whenever there are any**, because a bundle
    hash naming one address is a page a reader can visit and the engine keys
    it by that address rather than by the hash. Taking the path's value there
    asked for a key nothing writes, and the caller silently never saw a
    snapshot.

    `value` is the answer only when the caller has no addresses to offer,
    which is how a single-address request arrives.

    :param value: single address, or the bundle hash from the path
    :type value: str
    :param addresses: space-joined addresses for a multi-address bundle
    :type addresses: str
    :return: str
    """
    return page_key_from_addresses(addresses) or value


def subscribe(value, addresses, user_pk, permission, client=None, now=None):
    """Ask the pass to keep this page warm, and report whether it fits.

    Returns True when the page is now warm for this reader. False means the
    caller is over their warm-set cap and **nothing was subscribed** - the
    caller still gets an answer, from the cached path, exactly as they did
    before this existed.

    **Refused whole, never in part.** `warmset.touch(evict=False)` admits the
    whole bundle or none of it: half a bundle kept warm is a response where
    some rows are block-fresh and others are a minute old, with nothing in it
    saying which - the same "partially fresh" failure that ruled option C out.

    **The browser's half evicts; this one refuses.** A tab that loses its slot
    silently goes static, which is a better failure than an error on a page
    nobody is looking at. A machine consumer wants to be told.

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

    # **Checked after the tier, because it is not a tier question.** This
    # account may be entitled twice over and still must not subscribe: it is a
    # credential shared by a whole installed base, so the warm set it would
    # spend is not one reader's.
    if is_shared_token(user_pk):
        return False

    warmset, manifest = _warm_set()
    if warmset is None:
        # The widgets repo has not caught up with this one. No cap can be
        # applied, so nothing is subscribed: an unbounded warm set is a worse
        # answer than a cached one.
        return False

    members = addresses.split() if addresses else [value]
    now = time.time() if now is None else now
    try:
        client = redis_instance() if client is None else client
        # **The widget's own bands, not a second list.** The unified budget is
        # one warm set per reader across both surfaces, so the cap has to be
        # the same number from the same place - and a tier change must not be
        # able to land in one of them and not the other.
        cap = warmset.cap_for(permission, manifest.required_permission)
        admitted, _ = warmset.touch(
            user_pk, members, cap, client, now, evict=False
        )
        if not admitted:
            return False

        page = page_key(value, addresses)
        # `lvx` is what the pass re-prices and its members are address strings,
        # not page keys - that is the shape the widget writes and the engine
        # normalises. `lva` is keyed by page, because that is what `_live_page`
        # tests membership with once it has resolved the bundle.
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

    **The fingerprint is what the browser's reader needs and the API does not.**
    An API caller wants the freshest account there is and has nothing to compare
    it against. The live widget re-renders one venue group from this instead of
    reloading the page, and then writes onto the page the fingerprint it has
    caught up to - so it has to know which fingerprint this snapshot actually
    describes rather than assume it is the one just published.

    **`lvn:` keeps the shape it has always had**, because this process serves it
    to entitled API callers and an engine deployed ahead of this one must not be
    able to change what they get. The fingerprint lives in `lvnh:`, a key that
    did not exist before: an engine that predates it leaves it absent, which
    reads as "cannot tell" and costs the reader a reload rather than an answer.

    One `MGET`, so the pair comes back as the engine wrote it rather than as a
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
        # `strict_map_key=False` for the same reason the widget's payload read
        # needs it: these structures are keyed by asset id, and msgpack refuses
        # integer keys by default.
        return msgpack.unpackb(raw, strict_map_key=False), holdings or ""
    except Exception as error:  # noqa: BLE001 - see the module docstring
        logger.warning("api live snapshot unreadable: %s", error, exc_info=True)
        return None
