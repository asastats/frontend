# Frontend logbook

Why the code in this repository is the way it is: the measurements, the
outages, the decisions taken and the ones reversed.

One section per module, under its path from the repository root. Inside it,
`## Module` holds notes about the file as a whole and a subsection per
function, method or constant carries the rest.

The code carries what a reader needs to *use* it correctly. This carries what
they would need to *change* it safely. Nothing here is required reading to work
in a module; it is here so that nobody has to reconstruct a decision from a
diff, and so that the decision survives the comment being edited away.

Entries are dated where the date is known, and append-only: a note that turned
out to be wrong gets a correction beneath it rather than an edit, because "we
believed X until 2026-09-19" is the useful part.

---

## website/api/data.py

Nothing recorded. The module is a table.

---

## website/api/permissions.py

### `CanAccessApiPermission`

**Why enforcement ships off.** The check was written when the API shipped and
then left returning `True`, so every caller has had access for as long as the
endpoint has existed. Turning it on is not a configuration change to them - it
is the day their integration stops working - and the access logs cannot say
which tier any of them holds. Shadow mode is how the population gets measured
before anything is taken away, using the same code that will later refuse
rather than a second implementation that could disagree with it.

**What the population actually is.** Measured over five weeks of access logs
before the check was written: 2,068,287 public API requests, of which 1,011,635
were already 401 and 983,244 were redirects. Only 70,969 succeeded - about
2,000 a day. Enforcement can break that population, not the two million.

---

## website/api/tiers.py

### Module

**Why the widget's bands are not imported.** Conflating the API's
addresses-per-request with the `liverefresh` widget's addresses-per-reader is a
mistake this project made twice, once in the widget runbook and once in
`live/API-TIERS.md`. The numbers are written out here so the two cannot be
edited as though they were one.

**Why `block_time` left this table and came back.** It was taken out once: a
flag read by nothing and asserted by a test, which is how a later change comes
to be written against a promise the code never kept. The rule then was that it
returns when the promise is kept. Engine `d5e318c` publishes a full serialized
account per block for pages an API caller keeps warm, and `api/live.py` asks,
reads and serves it, so it is back.

### `enforce_address_limit`

The integration tests found this the day it was added: they build two- and
three-address bundles for a caller with no tier and started failing with 400 -
precisely what a real unentitled caller would have met on deploy day. That is
what shadow mode is protecting against, and it is why this limit shadows on the
same switch as the permission gate rather than on one of its own.

`DEFAULT_BAND` exists only because the gate shadows: an unentitled caller is
let through and still has to be given some answer.

The Asastatser band deliberately keeps the 60-second cached path. `DECIDED.md`
records that as intentional rather than an oversight: freshness is
Professional's whole advantage over it.

---

## website/api/authentication.py

### Module

**Why not the two options the library offers.** Rotating `SIMPLE_JWT_KEY`
invalidates every token at once - `WIDGETS_API_TOKEN`, the token baked into the
published mobile app, and every third-party integration - which makes it
unusable for the case it would be needed in. `token_blacklist` is the
documented alternative and is the wrong shape: a table and a lookup per
request, covering *refresh* tokens by default rather than the access tokens in
circulation.

The move to `JWTAuthentication` already pays for a profile read on every API
request, so the `iat` comparison is free by comparison.

---

## website/api/widgets.py

### `page_key_from_addresses`

Added 2026-09-24, after two different callers computed this key two different
wrong ways. The alerts widget stored the space-joined address list, so
`payload_for` read `lvp:<ADDR ADDR>` - a key nothing publishes - and every
alert on a multi-address bundle silently never fired; past 128 characters the
rule could not be saved at all and the reader got a 500. `api.live.page_key`
had the mirror of it, returning the path's value for a single address, so a
bundle hash naming one address asked for a key the engine never writes and the
API caller silently never saw a snapshot.

The engine's rule is `bundle_from_addresses(addresses) if " " in addresses else
addresses`, in `utils.transmitters._live_page`. It depends on the addresses and
never on the path.

---

## website/api/live.py

### Module

**Why a second published thing exists.** The live pass already published a diff
for browsers (`lvp`). A REST caller holds no rendered page, so a diff is not an
answer to its first request at all. Engine `d5e318c` added the full serialized
account (`lvn:{page}`), gated on membership of `lva` so that it is built only
for pages somebody is paying to keep warm.

**Why subscribing and capping arrived in the same change.** Before this module,
an API request cost the engine nothing per block - `website/api/` wrote none of
the live keys - so a cap on API callers would have refused the heaviest of them
for no saving. That is where `post-deploy/NEXT-unified-budget.md` stopped its
step 3. Asking for a page to be kept warm is what makes the cap bound something
real, so the two had to ship together.

**Why `lvn:` may not grow a wrapper.** 2026-09-23: the engine briefly wrapped
the snapshot as `{"holdings": ..., "account": ...}` so the browser's regroup
path could tell which fingerprint it had. That changes what an entitled API
caller receives, and the engine and the website sync separately - an engine
deployed a few minutes early would have served every Professional caller a
shape their client had never seen. Replaced by a second key, `lvnh:`, the same
day. Anything else the browser needs *about* a snapshot goes beside it too.

**Tier scope.** Professional and up. `api/tiers.py` says freshness lands in its
table when something serves it, and this is that something; Asastatser keeps
the 60-second cached path unchanged.

### `_warm_set`

2026-09-20: a module-level `from widgets...` import here took the whole site
down. The widgets repo syncs separately from the frontend, so "the frontend is
ahead of the widgets" is an ordinary state of the world for minutes at a time.
The import made `api.views` unimportable, which made `config/urls.py`
unimportable, which 500s every page rather than the one feature that wanted the
module.

### `SUBSCRIBED_KEY` / `API_WARM_KEY`

The scoring scheme is the whole subscription model, and it was chosen so that
there is nothing to unsubscribe. A member is scored by the unix time it was
last asked for, and the engine only reads back members inside a 90-second
window, so a caller that stops asking stops costing the engine anything without
any party having to notice or clean up. The widget writes `lvx` the same way
for the same reason: a reader who closes a tab simply stops polling.

### `SNAPSHOT_HOLDINGS_PREFIX`

Added 2026-09-23 as the second half of the `lvn:`-shape decision recorded under
Module. The first attempt put the fingerprint inside the snapshot; this is the
version that keeps the API contract fixed.

### `subscribing_enabled`

Ships inert, like `API_TIER_ENFORCED` beside it. Subscribing starts costing the
engine per block the moment one entitled caller makes a request - there is no
ramp - so it waits on the engine publishing being deployed and on the
shared-token question being settled.

### `is_shared_token`

`FINDING-shared-token-vs-per-account-limits.md` reaches the conclusion and
`RUN-mobile-token-swap.md` §4 states it as a rule: the mobile app stays on the
cached path and never subscribes. It ships one baked credential for 80 client
addresses with no login, so its account is a population rather than a reader.
Written as an explicit exclusion rather than a tier check, because a tier check
that happens to exclude it today stops doing so the moment somebody upgrades an
account. `WIDGETS_API_TOKEN` has the same shape and belongs in the same list.

### `subscribe`

**Why admission is all-or-nothing.** Option C during the tier design was to
keep part of a bundle warm and serve the rest from cache. That produces a
response where some rows are block-fresh and others are a minute old with
nothing in the payload saying which, which is what ruled it out. `evict=False`
is the same decision in code: the API refuses rather than pushing another of
the reader's pages out, because a machine consumer wants to be told, while the
browser's half evicts because a tab going static beats an error nobody sees.

### `stamped_snapshot`

Added 2026-09-23 for the live widget's regroup path, which re-renders one venue
group instead of reloading the address page. The fingerprint has to be the one
the snapshot describes: writing the *published* fingerprint onto a page
rendered from an older snapshot leaves wrong rows with no mismatch left to
notice them. Read in the same `MGET` as the account for the same reason.

---

## website/api/position_id.py

### Module

**What the six fields are worth, measured.** On the real 76-asset bundle they
distinguish 185 of 190 positions. The remaining five are not merely hard to
tell apart, they are identical in type, name, provider, code and link: two Pact
ALGO-ASASTATS liquidity positions, two Lofty AMM entries, two Cometa stakes,
two Gora.fi validator delegations.

Two of the five are recoverable at this layer. A Pact liquidity position
carries a ``Source LP token`` in its ``linked`` data and the two hold different
tokens - 1129173576 against 2757667448 - so promoting that asset id into the
identifier separates them and takes the bundle to 187 distinct ids.

The other three need a discriminator from the provider: an application id, an
escrow address, a position index. They are flagged rather than papered over.

### `position_id_from_fields`

The live pass works from the engine's own structures because serializing an
account every block per page is the cost that design exists to avoid. Both
paths meet at `_parts`, and the test suite pins that against the real bundle
rather than trusting it.

### `identifying_link_ids`

"A Pact liquidity position is only distinguishable by its LP token" is written
down once, here, rather than in the engine.

---

## website/api/main.py

### `fetch_and_serialize_account`

**Why the annotation sits at this layer.** Before it did, the address page
rendered every position without an identity - no ``data-pid``, and therefore
not one position-pin control on the whole page. `pins.js`, the pinned band and
the whole position-pinning feature were dead against the real backend while
passing every test, because the fixtures annotated themselves.
``integration_tests/test_address_dynamic_integration.py`` is what found it and
is what keeps it found.

---

## website/api/client.py

### `_request`

Opening an NFT collection while the engine was restarting answered a 500 rather
than the "could not be loaded" the template already carries, and the same held
for every other caller in this module: they all catch `BackendError` and a
transport failure was not one.

### `fetch_collection_items`

The re-hash was added after a reader's NFT collection silently never filled.
The *page* renders for an old bundle bookmark because
`api.main.fetch_and_serialize_account` normalises the hash, while this call
400s underneath it - 44 times in one day on a single page, once a minute.

---

## website/api/views.py

### `_etag_for`

**Why an ETag rather than an encoding trick.** `ANALYSIS-bandwidth-lever.md`
measured the real lever and it is poll rate: 22x between block-rate and
60-second polling, against which no encoding competes. This bounds the caller
who polls faster than blocks and nothing else - a re-price moves some figure
most blocks even when the total moves 0.0003%, so a block-rate poller still
gets a changed body.

### `AccountView` (the warm header)

`NEXT-unified-budget.md` specified a 429 when a caller is over their warm-set
cap, on the reasoning that a machine consumer wants a status code rather than
stale data. Half right: they are entitled to the data and asked only for more
breadth than their plan keeps warm, so refusing would turn a working
integration into an outage. The answer is served and the fact is stated
instead.

`request.user` being absent on a bare WSGIRequest has now caused the same
would-be 500 twice in this file, two lines apart. `enforce_address_limit`
learned it from a unit test first.

### Module

`ValidationError` sat imported and unused here after the address refusal moved
to `api/tiers.py`; removed 2026-09-24.

---

## website/api/helpers.py

Nothing recorded. The module is data shaping: no comments and no prose
docstrings.

---

## website/api/structs.py, urls.py, data.py, widgets.py

Nothing recorded beyond `page_key_from_addresses`, above.

---

## website/utils/layouts.py

### Module

The registry follows the same shape as :data:`EXPLORERS` and the swap-router
discovery: joining the table is how a thing becomes selectable. The difference
is that every other preference on the settings page is a single gate - you may
choose an explorer or you may not - while layouts are handed out in stages.

**Why a lapsed subscription loses the layout but keeps the explorer.** Every
explorer is worth the same, so a saved one keeps applying; the layout *is* the
subscription benefit, so it does not.

### `layout_for_user`

It used to return the key paired with a presentation modifier, from when the
page was one template that varied by attribute. Callers now look up whichever
of `layout_template` and `layout_compact` they need.

### `locked_layouts`

Naming the tier a locked layout needs is the same courtesy the explorer section
pays by naming Intro.

---

## website/utils/charts.py

### Module

The six `for i, item in enumerate(rows)` loops each used to open with
`if i == count - 1: break`, and every one was a no-op: `count` is the length of
the list being iterated, so the loop ends on that index anyway, and the only
statement the break skipped is already false at that index.

It was not harmless. The loop could never end by exhaustion, and the guard
above each one makes the list non-empty, so the exit arc was unreachable:
coverage reported six partial branches no test could close, and a real gap in
this file would have been indistinguishable from them.

---

## website/utils/helpers.py

### `canonical_bundle`

`bundle_from_addresses` became sort-and-dedupe over the address set at some
point, and visitors who saved a bundle URL before that still arrive with the
hash it produced then.

Resolving through the cache rather than asking callers for `addresses` kept
this to a one-line change at each call site; threading the addresses through
would have touched four signatures to answer a question the cache already
holds.

---

## website/utils/cache.py

### `cached_live_holdings`

This is the one fact both services agree on, which is why it keys the rendered
address page as well as the widget's reload decision.

### `nft_floor_price`

Allo is the default explorer and the historical hard-coded provider.

The two payload shapes are a deliberate split: the closed page only ever needed
the number, and the listing around it was a quarter of an NFT record's
serialization cost.

Which caller multiplies the price by the item's amount diverges, and predates
the light payload: `utils.charts._nftfloor_totals_from_serialized_data` does,
`core.templatetags.core_extras._collection_totals` does not. Not this
function's to settle.

---

## website/utils/userhelpers.py

### `liverefresh_terms`

The address bands belong to the widget's manifest. This exists only so the
settings page can put a label on them without importing a widget's internals.
