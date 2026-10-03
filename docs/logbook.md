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

**An unresolved bundle hash used to reach `lvx`, 2026-09-24.** `api/views.py`
computes `addresses` as `"" if len(bundle) == ADDRESS_LEN else
check_bundle_addresses(bundle)`, and `check_bundle_addresses` returns `""` on a
cache miss — so a bundle hash nobody can resolve produces exactly the same
falsy `addresses` a single-address request does, and `addresses or value` then
fell through to `value`, which for a bundle request is the 40-character SHA-1
hash. `enforce_address_limit` was skipped on that path too, being guarded by
`if addresses:`.

The engine's live pass then called `fetch_account("<40 hex>")` on it every
block, which reached `box/reti.py:_box_name_for_address` and raised
`WrongKeyLengthError: key length must be 58`. Two such members sat in `lvx`
from somewhere between 09:28 and 11:11 on 2026-09-24 until this was fixed on
2026-09-25.

No reader saw a wrong figure — a page that raises falls back to the cached
answer, which is the right answer for a bundle that does not resolve. The
damage was noise: the liveserver's `appstransmitter` log went from ~330 KB per
two-hour rotation to ~8 MB, 5,053 WARNING lines against 379 INFO lines, about
96 MB a day of one repeated traceback, plus two wasted `fetch_account`
attempts a block.

Found by reading the liveserver logs, not by any alert. The tell was the page
label: `_live_page` logs `addresses[:6]`, and `6F50FC` and `9F055C` both
contain `0`, which is not in the base32 alphabet an Algorand address is written
in. Every page that succeeded in the same file had a base32 label.

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

---

## website/core/views.py

### `service_worker`

`index_file` above already serves `robots.txt` from the root this way; this is
the same trick with a different content type.

### `AddressView._live_holdings`

The fingerprint is what lets a live page show an asset that has just arrived.
An out-of-band swap reaches only an element the page already has: a bought
asset has no row to land in, a sold one is never mentioned and its row stays as
it was. So the widget answers a change to it with a reload - and a reload
served out of a `cache_page` entry built before the change would show the same
stale rows, which is why the fingerprint is in the key.

Every page nobody watches keys exactly as it did before, at the cost of one
Redis field lookup.

### `AddressView.get_context_data`

**Why only the layout may be reader-derived.** Everything else about the reader
- their addresses, their router, their subscription - is shared between
signed-in readers by the cache entry. `core/tests/test_address_layout.py` holds
the line.

**What the light payload bought.** Measured on a 7,002-NFT account: NFT
serialization from 0.499 s to about 0.126 s. Every collection and item is still
present; what each record drops is the listings and purchase history only an
opened collection shows.

The engine sizes admission by the reader's permission rather than by a
per-minute limit that punishes a lone reader on an idle box. See
`core.views.reader_permission` there.

### `preferred_linked_address`

Alphabetical order was the previous rule and correlates with nothing at all. On
a bundle page it silently picked whichever of the reader's accounts happened to
sort first.

### `SwapEntryView`

**The 2026-09-13 report.** The Dust Sweep button was missing in a normal window
and present in a private one. An old heuristically-cached copy of this partial
holds old content-hashed URLs and keeps loading the old scripts indefinitely,
which is why `never_cache` is on it - the same decorator the widgets' own
router endpoints carry.

**Why the swap marker carries a list and not just a guess.** The guess alone
was wrong on a bundle: it opened on the profile's primary, so a reader
connected to the bundle's *other* address was shown that other account's
holdings. Nothing unsafe - the Swap button stays disabled unless the wallet
owns the from-address - but the holdings, balances and percentage buttons were
all somebody else's.

The ASA Stats router's endpoint URLs were absent entirely until they were
added, which is why selecting our own router on an address page answered "this
deployment has no ASA Stats router endpoint".

### `NftCollectionItemsView`

A page showing 7,002 NFTs opens almost none of them, which is the whole reason
the payload is split in two.

---

## website/core/templatetags/core_extras.py

### `identicon`

Every account has one on the day it is created, including the
wallet-authenticated majority who would never have a social avatar, and there
is no image to host, resize or moderate. It is also the honest picture for this
product: what identifies a row here *is* its addresses.

Five columns rather than the more common eight - at the 32px this is drawn at,
eight columns is a texture rather than a mark.

### `program_groups`

The reference address groups 18 LP positions across five venues under one
"Liquidity" heading, because that is what `program.name` says for a liquidity
position. It is a useful grouping and an honest one; calling it a venue
grouping would not be.

Design 1 renders the same programs ungrouped, which is why the grouping is
presentation rather than payload.

### `position_band`

**Why the band and the filter must agree exactly.** A reader who presses
"Staked" and sees a balance row has been told the band was lying. The category
has to be known per position and `utils.structs.Consolidated` arrives already
summed, so the rule is reproduced here.

The deliberate difference: `_balance_totals` uses `next(...)`, so a second
`Balance` position on the same asset contributes nothing to the balance total,
and the `defi` comprehension excludes every `Balance` position - so that second
one lands in no category and is missing from the band. This filter calls it
`balance`. The reference payload has no such asset, which is why the two agree
today; if one appears, the band under-reports and this filter is right.

### `breakdown_key`

Three pairs of positions on the reference bundle are genuinely
indistinguishable, so `position_id` gives each pair one identifier and flags
it. The markup already declined to put `pq-`/`pv-` ids on those; the breakdown
panel did not, so expanding one position opened the other one's breakdown.

### `defer_items`

Measured on one real account - 1,990 collections, 28,008 NFTs - the rendered
items were 19.3 MB of a 22 MB page and 152,294 elements the browser had to lay
out before it would scroll.

---

## website/core/models.py

### `Profile.api_tokens_valid_from`

`token_blacklist` would have added a table and a lookup per request, and by
default covers refresh tokens rather than the access tokens actually in
circulation. Rotating `SIMPLE_JWT_KEY` invalidates every token at once,
including `WIDGETS_API_TOKEN` and the one baked into the published mobile app.
Neither is usable for a single leaked credential.

### `Profile.can_access_fold_setting`

The address page's cache key is `layout-{layout}-e{export}h{historic}-{holdings}`.
Folding a fourth boolean into it would double the entries for every address,
and what that buys is stopping a reader hand-editing their own browser storage
to see more of their own rows. Not worth halving the hit rate of the cache that
heavy pages depend on.

### `LiveAllowanceBucket`

**Why the free tier is keyed by address and Intro by reader.** An allowance
bound to an account is bound to the cheapest thing in the system - accounts are
free and need no email - so a hundred of them would be a hundred allowances.
Bound to the address, getting more free time means splitting a portfolio, which
costs fees and minimum balances and fragments the combined view that was the
reason to watch. The abuse has to destroy the thing it is abusing for.

A paying reader is not what that defends against, and per-address would hand an
Intro subscriber four hours for every address they open, which is no limit at
all.

**Why the row exists at all when Redis carries the spend.** Redis is allowed to
lose things - an eviction, a flush, a failover. For a daily allowance that
costs a reader one day; for a refilling bucket it would hand every key a fresh
grant. The failure mode of the anti-abuse mechanism must not be the abuse.

---

## website/walletauth/crypto.py

### Module

Ported from the Rewards Suite's `utils.helpers.verify_signed_transaction`, with
Falcon-1024 (`pqsig`) verification added. Two deliberate differences from that
reference: the domain-separation prefix is named rather than written as a
literal, and the caught exceptions are broadened because this is called
straight from the verifier rather than from inside a view's blanket
`try/except`.

### `verify_pq_signed_transaction`

**Why it asks a node instead of verifying locally.** The first implementation
used `falcon_python.Falcon1024`, which is standard, *randomized* Falcon-1024.
Algorand's post-quantum accounts use a deterministic variant, and Algorand's
own `deterministic.h` records the three ways they differ on the wire: the
deterministic signature drops the 40-byte nonce, adds a salt-version byte, and
changes the header from `0x3A` to `0xBA`. No message preimage and no header
fix-up bridges that - the verifier was running a different algorithm on an
encoding missing a field it requires. `~/claude/post-quantum/FINDING-falcon-mismatch.md`
has the working.

There is no Python binding for the deterministic variant. There is a correct
implementation in every algod node.

**It also outlives this scheme.** The `pqsig` envelope is built to carry others
- `f5`, Falcon-512, is defined and reserved - and a node-side check supports
each the day the network does, with no new binding to build.

The re-encoding diagnostic exists because this module has already taken the
detour once: a mismatch between the bytes the wallet sent and the bytes the SDK
re-encodes fails the signature, which reads as bad cryptography rather than as
an encoding problem.

---

## website/walletauth/management.py

### `is_bootstrap_promotion`

The branch exists for accounts whose `Profile.address` predates the
linked-address registry. Linking that same address creates a *non-primary* row,
because `link_address` sees `Profile.address` already set - so the account has
a proven address and no primary, and step-up can never be satisfied. Removing
the bootstrap path strands them.

---

## website/walletauth/verifiers.py

### `EvmXChainVerifier`

The xChain logicsig's own on-chain scheme is EIP-712, which matters when
spending from the account. It does not matter here, because proving control of
the EVM key is what proves control of the derived Algorand account.

---

## website/widgethost/registry.py

### `swap_endpoint_urls`

Written because the address-page modal did not carry these at all. The router's
own shell page has always rendered `data-quote-url`, so the ASA Stats router
worked there and failed everywhere else with "this deployment has no ASA Stats
router endpoint" - a message about configuration for what was two missing lines
of context.

**Why the optional URL is resolved separately.** `reauthorize` was added to the
dict inside the same `try`. On a deployment whose widgets are a release behind
- which is every deployment for as long as the second repository takes to ship
- resolving it raised `NoReverseMatch` and the `except` discarded `quote_url`
and `group_url` with it. The swap panel then rendered with no endpoints and
refused every quote: one optional feature taking the whole router down, in
production, for a URL nothing needs until a wallet rewrites a group.

### `swap_sdk_static`

A router with no bundle turned the per-user partial into a 500 under
`ManifestStaticFilesStorage`: no marker, no modal, no `swap.js`, and a Swap
button that fell through to its no-JS `href` and navigated. Development uses a
storage that returns the URL and lets the browser 404 it, which is why nothing
caught it before production.

---

## website/nameservice/

`anssdk/` is a vendored third-party SDK. It is excluded from black, isort and
ruff: every finding in the package is inside it, and fixing them would be
editing an upstream copy to satisfy a convention it never agreed to.

`nfd.py`, `ans.py`, `main.py` and `xchain.py` carry no history worth moving -
section markers and step comments only. `xchain.py` is excluded from black for
the same reason as the fixture files: one line of it is a 2,598-character data
literal.

---

## website/permissiondapp/ and website/widgets/

Submodules, each with its own repository. `widgets/` gets its own logbook at
`website/widgets/docs/logbook.md` rather than entries here; `permissiondapp/`
is out of scope.

---

# Templates

The same rule as for the Python modules. A template comment stays when a
reader editing the markup would otherwise break something they cannot see -
an attribute a script binds to, an id a fragment swaps on, an element another
widget replaces whole. Everything else is here.

---

## website/templates/snippets/dynamic/asset.html

### Module

**Why a `<details>` and not a button and a panel.** Design 1 uses the latter.
This one works with the script disabled, the open state is the browser's to
remember, and a screen reader is told it is a disclosure without being told so
twice.

**The header is five rigid cells** - grip, tile, identity, value, pin - and the
fourth is the money column, `--col` wide, the same width the venue subtotals and
every position row inside use. Below 620px they cannot all fit and the
stylesheet drops to two rows with the value under the name; the media query in
`input.css` carries the measurement behind that number.

**Why design 1's `.fitem` and `f<id>` are reused rather than renamed.** They are
what a reader's saved order is remembered against, so reusing them is what lets
an arrangement survive switching designs.

**Why the sort keys are attributes.** `toolbar.js` sorts, filters and re-cuts
the list in the browser. Reading the keys back out of the rendered text would
mean parsing "1,234.57", whose separator is locale-dependent, against a figure
that is already rounded - so a sort would silently tie rows that differ.
`data-val` existed for the currency switch for exactly this reason; the other
three are the same idea.

`data-search` is deliberately not the card's `textContent`, which includes the
asset id, decimals, total supply and every provider link in the closed body:
typing "6" would match most of the page.

### The header controls

There was a shared `entry_controls.html` snippet wrapping the grip and the pin.
It was written for design 1 back when the controls were going there, nothing
included it once design 1 was restored, and a wrapper is wrong here anyway -
each control is a named grid area and a wrapper collapses both into one cell.

The prototype puts a dismiss control in the pin's cell, hiding an asset from the
list. That is a separate feature and is not built.

### `assetamount` and the unit span

**2026-09-19, live for about an hour.** The asset's own unit was wrapped in
`<span class="u unit">`, which looks like styling and is not: `paintUnits`
selects `.dynamic-page .u.unit` and writes the *display currency* into every one
of them. Every row of every non-ALGO asset read "0.1022 ALGO" where "0.1022 g"
belonged. A class here is a subscription to somebody else's behaviour.

The `q` span carries no class, because it inherits the cell's styling and a
class would be a name that does nothing and still has to be de-collided against
DaisyUI. `q` for quantity: `v` is the value and `.amt` is taken - it is the
value span on a position and `pins.js` reads it.

The band above follows the opposite rule: `bandtotal` keeps its unit *inside*,
precisely because `address.js` overwrites that element wholesale. Which element
the swap replaces is what decides where the unit goes.

### `assetvalue`

`data-sort-value` on the row was a stale sort key until `toolbar.js` was pointed
at this span's `data-val` instead - the same unrounded quantity, swapped every
block, with the row attribute as the fallback when the cell is missing or
unreadable. A sort after an hour of updates now agrees with the column beside
it.

### Total supply

Read `amount_repr` until it was noticed being wrong by orders of magnitude
against the same asset in design 1: ALGO's ten billion rendered as ten thousand.
`amount_repr` divides by `10 ** decimals` and is right everywhere else in these
templates because everywhere else is a holding, which the chain reports in base
units. `asset.total` arrives already scaled.

### The Swap entry

Placed with the asset's own facts rather than at the foot of the row, where it
sat below every position and every provider link - a scroll away from the thing
it operates on.

**Design 1's inline panel is deliberately not copied.** It carries a
`swap-panel-<id>` div for `handleInlineSwapClick`, which reads a
`data-swap-target` attribute no template sets, and which is not registered as a
listener either. Only `handleSwapModalClick` is. The panel is vestigial there
and would be dead markup here.

### `programgroups`

Positions are grouped by venue because a reader holding the same asset in four
places is asking how much of it is on Tinyman, and a flat list makes them add it
up themselves.

A position opening or closing used to reload the whole page: a fragment reaches
only elements that already exist, and the value fragments carry figures rather
than rows. Re-rendering the group from this markup is what makes the heading,
the count and the subtotal right at once, without a second copy of the markup in
JavaScript.

### The group heading

Moved into a venue card, a group named by its venue would be a column of
identical "Wallet balance" headings with no way to tell which holding each one
is. Both headings render and the stylesheet picks, so the switch cannot get out
of step with where the group sits - which a script writing the text would
eventually manage.

A group of one had the same figure twice, three lines apart: the subtotal beside
the venue and the position's own value under it. They cannot differ, because
with one position the subtotal is that position.

### The position counter

Two ambiguous positions in different groups collided exactly as the shared `pid`
did, because positions are a loop inside a loop over program groups and the
inner counter restarts.

---

## website/templates/snippets/dynamic/position.html

### Module

**Why the row's class is `.position` and not the prototype's `.pos`.**
`static/js/pins.js` and its jest suite already address positions by that name
and are covered to 100%. A cosmetic rename would churn a tested engine to no
reader's benefit. The prototype is the spec for the design, not for
identifiers.

**Why the two link idioms have to be distinguishable at rest.** A reader
deciding where to click has not pointed at anything yet. `.out` underlines on
hover; `.tdist` is dotted at rest and resolves to solid under the pointer.

**Why `data-pid` does not hash the amount.** The amount moves. Hashing it would
restabilise nothing while destabilising every position that never changed.
Three positions on the reference bundle are genuinely indistinguishable, which
is what `data-amount` and `pid_ambiguous` exist for.

### `counter` and the breakdown key

This template's header carried a "known collision, not fixed here" note for as
long as the breakdown id was `prog.pid|default:counter`: ambiguous positions
shared an element id, so expanding either toggled whichever `getElementById`
reached first. Substituting `counter` outright was worse - it is the grouped
inner loop's counter, so it restarts at 1 in every group and collides within a
single asset.

**Closed** by `breakdown_key` plus a two-number counter from `asset.html`
(`"<group>-<position>"`, namespaced by asset id). Positional keys are acceptable
for this one thing and nowhere else in the feature: a breakdown panel opens and
closes inside a single rendered page, so a key that changes on the next render
costs nothing, while a pid that moved between renders would silently move a
reader's pin.

### `positionamount`

**2026-09-19.** Nothing inside a position carried an id, so no fragment could
reach one and a full reload was the only thing that ever updated a position. A
row's aggregate would move while the "Wallet balance" inside it sat at its
rendered figure.

---

## website/templates/snippets/dynamic/collection.html

### Module

A collection is a holding, so it uses the asset card's shell. Giving it its own
layout would break the one thing this design promises.

**The `.nft` tile modifier was a collision.** Design 1 owns `.nft` and pairs it
with the colour slot in `.nft.cN` rules, which were landing on the collection
tile and setting a `--stripe` nothing here consumes. Renamed to `.collection`.

`.cid-meta` carries the floor/estimate split as a two-part bar because it is the
one fact about a collection a single figure cannot express: the estimate is what
the section totals, the floor is what a marketplace will pay today, and the gap
between them is the risk. A collection whose floor is most of its estimate reads
as solid; one where it is a sliver reads as mostly hope.

### The `hx-get`

**htmx 4 has no `from:` modifier.** It was
`hx-trigger="toggle once from:closest details"` on the inner div: the string
never bound, the toggle never fired, and opening a collection fetched nothing.
Three browser tests caught it and nothing else could, because the markup is
still valid HTML and the card still opens. Moved to the `<details>` rather than
respelled, so there is no modifier left to get wrong.

### The header cells

The grip cell was empty while the space it reserves was still there, so a
collection header had an asset's indent with nothing in it.

The tile held the collection's initials for a while, as a stand-in for "a
collection has no logo of its own". Four grey capitals tell a reader nothing
they cannot read in the name beside them, so the one place on the row reserved
for recognition was spending itself on a second copy of the name. The art is
what a reader recognises a collection by, and the first item is on the page
anyway.

### `items-<slug>`

Rendering every item for every collection put **87.9% of one real account's
22 MB page** into markup nobody could see - a closed `<details>` renders none of
it - and then discarded it on open. The measurement is in
`snippets/nfts/collection.html`.

---

## website/templates/snippets/dynamic/toolbar.html

### Module

Filtering 190 positions is a class toggle rather than a round trip, which is why
every sort key and category is rendered onto the rows.

**Two prototype controls are deliberately absent.** A Rows/Cards toggle: that
choice is the layout the reader picked on the settings page, `dynamic` against
`dynamic-compact`, which is a server-side preference and part of the cache key -
a second client-side control would let the two disagree about which design the
reader is looking at. And dismissing an asset, which is not built, so `reset`
has nothing to undo for it.

There was a 95%/99%/99.5%/All control. It was never a setting: it existed to
demonstrate the page with everything on screen, before a load-more did. "Show me
the rows carrying 99.5% of the value" is not a sentence a reader thinks in. Each
section now shows a fixed first batch and offers the next - see
`ADDRESS_INITIAL_ASSETS` and `ADDRESS_INITIAL_COLLECTIONS`.

There was also a spacer between the two halves, as the prototype has, pushing
the right-hand controls to the edge. With a dozen controls the row wraps on any
realistic width, so all it achieved was a gap in the middle of the first line
and two lonely controls on the second.

### `tb-toggle`

`aria-pressed` was all there was for a while: a screen reader was told which of
these was on and a sighted reader was told nothing, because `.ghost` had rules
for rest, hover and disabled and none for the pressed state.

### `tb-refresh`

The title said "about once a minute", was corrected to "after 60 seconds of
inactivity" because that was what the code did - `resetTimer` was bound to
`mousemove` and `keypress`, so any movement put the count back to zero and a
reader who moved the mouse never saw it fire at all - and then went back, once
the code was fixed so that only the *firing* waits for a pause. A reader who
keeps touching the page now gets refreshed a little late rather than never.

---

## website/templates/base.html

### Module

This file is the DaisyUI base standing beside the Materialize one; when the last
page moves off that one, this becomes `base.html`. The eleven-class collision
listed at the top is why the cutover is page by page rather than global.

### The header

Three changes made when the chrome was rebuilt: the primary nav marks the
current section with `aria-current="page"` (the same contract the auth tabs and
the profile sub-nav use, and without it a reader could only tell where they were
by reading the url); account actions were separated from navigation, because
Logout sat in the same row as Home and API and so leaving the site looked like
another destination; and the appearance control, which was an unlabelled circle,
now says what it is to a screen reader and on hover.

**Why `h-14`.** 56px with a 40px logo leaves 8px above and below. The wordmark is
two lines of type in a 605x256 bitmap with no padding baked in, so every pixel of
the bar that is not the logo reads as air around it - at the previous 64/36 it
was 14px a side, nearly a third of the logo's own height.

### The favicon links

`favicon-16x16` and `favicon-32x32` carry `expires 365d`, so a reader who visited
before the 2026-09-05 logo change would otherwise have kept the old tab icon for
up to a year.

Pera Wallet's SDK reads `favicon: ae()[0]`, where `ae()` collects every `<link>`
whose `rel` *contains* "icon". The 180x180 apple-touch-icon is first because it
is the best size of the set for a wallet's connect screen.

### The footer

The old footer was two structures stacked: a column grid, a rule, then a second
row for copyright, legal and the app stores. That split is Materialize's -
`.page-footer` above `.footer-copyright` - and it made the footer read as two
footers, the second an afterthought holding whatever did not fit above.

The copyright now leads the tagline instead of closing the page. As the last line
under the columns it put the one piece of text nobody reads at the end of the
scroll, and gave the footer a second horizontal band.

The liquidity entries were sprite images, fixed at 133x32 with a light background
and both states baked in, so they could not follow a theme and were invisible on
the dark ones.

Each footer column is a heading and its list, so the groups stay landmarks for a
screen reader rather than one flat run of links. Two columns below `sm` is the
only thing that changes on a narrow screen.

### Fonts

Self-hosted: every face is declared in `typefaces.css` and served from
`static/fonts`. Only the pair the active theme uses is downloaded, because a
browser fetches a font file when text actually matches it - so declaring 77
families costs their declarations and nothing more.

---

## website/templates/address_dynamic.html

### Module

**One template for two layouts.** Two files would duplicate every asset row,
venue group and chart in order to change a handful of grid rules.

**Why the charts are SVG and not Chart.js.** Design 1 keeps Chart.js; this page
does not load it. 57 themes an SVG `fill` can follow and a canvas cannot, slices
that are real buttons sharing one filter state, and ~200 KB saved. The full
reasoning is in `frontend/docs/address_page_dom.rst`.

### `bandtotal`

The unquoted-attribute bug: a payload without `pricealgo` made `data-pricealgo`
read `"data-total=216.3"` and `data-total` vanish entirely, so the currency
switch computed the total from `undefined`. Two figures lost to one missing key.

### The header actions

A reader reported not being able to find the CSV export at all: a bare `.btn`
fills with a colour within a few percent of the page background, so on a dark
theme both buttons read as static text.

### The fold control

The venue list sat between the asset list and its fold control, which pointed
`showmore.js` at the empty venue container - so pressing "Show 38 more assets"
revealed nothing and every measurement of a folded row read zero. It degrades to
the right answer through a fallback, which is not where this belongs.

### `venue-list`

Rendering the venue grouping server-side as a second list was the alternative. It
doubles a page that already carries 190 positions, and the two copies would drift
the first time one of them was edited.

---

## website/templates/address.html

### Module

**What the Materialize removal changed beyond styling.** The accordions became
native `<details>`/`<summary>`, so `address.js` no longer initialises anything
and the hook names moved with them: `.collapsible-header` to `.item-header`,
`.collapsible-body` to `.item-body`, and the `<ul class="collapsible">`
containers to `.section-list`. `.tooltipped`/`data-tooltip` needed `M.Tooltip`
to say anything at all and became DaisyUI's CSS-only pair. The icon font went,
which is one fewer font to load and no stray ligature while the page fetches.

The consolidated totals were a Materialize collapsible whose open state had to
be restored by JavaScript.

### The h1

The heading was the number itself, so a screen reader announced "heading level
one, 1,234.56 ALGO" - a figure with nothing saying what it counts, on a page
whose actual subject, the address, sat below it as a paragraph.

Every tooltip other than the total's repeats an amount in the other currency,
which the currency switch gives in one keystroke. Those stay pointer
conveniences rather than a tab stop on each of several dozen numbers.

The money designs need none of this: their `.pricetip` carries no `.tooltip`
class, and `.total-sub` prints the same figure and rate permanently, for
everyone.

### The system warning

It was an `<h2>` carrying red text, which put a heading in the document outline
that is not a section and left the message to be noticed by colour alone.

### The action buttons

A reader reported not being able to find the CSV export at all, on this design
and on the money ones, where it was rendering as text with no edge. The old
Materialize markup was `btn-flat`, so the weak affordance was carried across
faithfully rather than introduced by the conversion.

### The filter row

These controls sat bare between the totals card and the first asset row, so the
one region a reader operates was the one region with no surface under it. It
read as a gap rather than as a toolbar.

### The swap modal

Included here as well as in the per-user partial, it put two `#swap-modal`
elements and two sets of its controls on the page for any linked viewer. For
anonymous viewers the copy was inert, because the controller is loaded by that
same partial and never arrived.

---

## website/templates/snippets/asas.html

### The load-more rule

It was a magnitude rule: show whatever number of rows accounted for 99.5% of the
section's value, then reveal *all* of the rest in one press. Both halves read as
arbitrary from the outside. The first showed 33 rows on one address and 8 on the
next with nothing on the page to explain the difference; the second made the
control's own promise wrong - "Show 39 more assets" over a button that then
showed thirty-nine, which is an unfold rather than a load-more. The dynamic
designs already used a plain count, so the change was the two designs agreeing.

### The asset header

The icon sits in the middle of the header because that is where the old design
put it: `.icondiv` was absolutely positioned at `left: 50%`, and the conversion
moved it to the start of a flex row instead.

Each program panel used to end with a `<br />` to separate it from the next.
Spacing between siblings belongs to the list that holds them.

### `classicamount` and the unit

The band above follows the opposite rule: `bandtotal` keeps its unit *inside*,
because `address.js` overwrites that element wholesale. Which element the swap
replaces is what decides where the unit goes. See
`snippets/dynamic/asset.html` for the `u unit` incident and the `q`/`v` naming.

---

## website/templates/snippets/asas/program.html

### Module

The `{% templatetag openblock %} with %}` binding of `decimals` was written
after this shape took the address page down with a 500 on 2026-09-18, in
`snippets/nonval.html`. `amount_repr` already answers "0" to anything it cannot
divide by, so a wrong figure on one line beats a dead page.

The template still carries the shape of a phase of work labelled W1-W7: the
distribution-bearing rows starting as `asar` and toggling to `shadow`; non-ALGO
Balance rows structured like generic rows, with the same `tdist`/`data-distid`
toggle and panel rather than a stand-alone provider line; per-row price lines on
distribution sub-rows; "Source LP token" filtered out of linked rows; the
amount line rendered after them; and negative programs - Borrowed, Loss, Debt,
the legacy `ffb`/`afb`/`gab`/`gl` keys - shown as an absolute value in
parentheses and `text-error`, triggered on `prog.value < 0` alone.

### The Balance label

It was green because the Materialize site painted this label in its link colour
and the conversion carried the colour across as the nearest token rather than as
a decision - so the one coloured label on the page was claiming "success", which
is not what a balance is. `text-primary` says "this is the site's colour", is
defined by all 57 themes, and already marks emphasis here through `btn-primary`
and the scroll-to-top control.

### The breakdown panel

Until it was given a surface and a border it was bare text, distinguished from
the summary it belongs to only by position.

---

## website/templates/_swap_entry.html

### The Dust Sweep button

It was a button per linked address, so a bundle page offered several - of which
every one but the connected account is an offer the reader cannot take. A sweep
is signed by one key and a wallet has one active account, so pressing any of the
others built a group that account cannot sign, and the reader found that out at
the signature prompt.

### Alerts

They sit in this partial rather than behind a second htmx request because what
the toolbar says is per-reader - how many rules you keep, how many your tier
still allows - and that second partial would be a second request for a question
this one already answers.

The count badge lives in the toolbar while the panel swap replaces the modal's
contents only, so nothing touched it and the count went stale the moment a reader
added their first rule.

### `id-liverefresh-left`

Rendering a per-reader balance into the shared address-page entry would show
whoever warmed the cache to everybody else. This is the trap the Dust Sweep
button hit; see `dustsweep-button-hidden-by-swap-bridge`.

---

## website/templates/home.html

### Module

Rebuilt on 2026-08-22 from a page that centred every line, spaced with
`<br><br>`, and put each bundle's name *above* the card rather than in it - so a
bundle was three separate things: a centred name, a centred "Historic data"
link, and a wide box whose entire area was a fourth link to a fourth place.
Nothing said which of the three destinations a click would take, and a column of
centred names of different widths has no edge to scan down.

The rail went with the shell. It held one box printing `profile.name`,
`user.username` and `user.email`, which are the same address three times on
every account that signed up with one.

### The account chip

**It was a grey line of text that did not look like anything**: a name and an
email in the same muted colour as the rest of the page, underlined only on
hover, directly under a heading. A reader had no reason to think it went
anywhere, and the profile page is where the subscription address is authorised.

`profile.name` answers "what do we call this reader" - first and last name if
either is set, else the username, else the local part of the email. Naming the
email directly ignored a name the reader had set, and an account without one - a
wallet sign-in has no email at all - fell back through a different chain.

`identicon` draws the mark from the reader's own subscription address: no
upload, no storage, nothing to moderate, and every account has one the day it is
created, including the wallet-authenticated ones a social avatar would leave
blank.

### The sort panel

The radios were two ragged fieldsets with the second pushed down five units, so
its rows never lined up with the first's. As one segmented row, four sort
options plus a label and a Descending toggle pushed past both edges of the card
and clipped the label, because the group's own content sets a floor it cannot
shrink below.

---

## website/templates/snippets/nfts/collection.html

### The deferred item list

The measurement behind `ADDRESS_DEFER_ITEMS_ABOVE_COLLECTIONS`: on one real
account, 1,990 cards carrying a 9,698-character body each came to **19.3 MB of
the page's 22 - 87.9% of it markup nobody could ever see** - and 152,294 `<div>`
elements for a browser to lay out before it would scroll at all. The page never
finished loading.

---

## website/templates/snippets/dynamic/band.html

### Module

The segments and figures became controls in pass 2. Before that the band was a
picture: three drawings of one set of numbers that a reader could read but not
act on.

The charts panel is a `<details>` so that a closed page costs nothing to draw;
`dynamic.js` renders the donuts as inline SVG from the JSON payload blocks, and
design 1's Chart.js is not loaded here at all.

The prototype models the fifth category the same way this does: four entries in
`CAT`, and a separate `showNft`.

---

## Template comments compile into CSS, and can keep a dead hook alive

Found on 2026-09-24 while shortening the comments, by two tests that changed
their answer when prose was deleted.

**Tailwind scans the comments.** `@source` in `input.css` names the template
roots, and the extractor reads the whole file - so a bare word in a
`{% templatetag openblock %} comment %}` block is a candidate class. "a social
avatar would leave blank" in `home.html` is why `.avatar` and `.avatar-group`
had rules in the committed stylesheet; nothing rendered either. Writing the
word "sticky" into a rewritten comment put a `.sticky` rule back the same way.
Keep framework words out of prose, or spell them as part of a sentence rather
than as a bare token.

**`test_template_hooks` was satisfied by prose.** `address.html` explained that
`<ul class="collapsible">` containers had become `.section-list`. That sentence
contains the literal `class="collapsible"`, which is what the test searches
for - so `.collapsible` counted as still rendered, and
`profile-authorize.js`'s `M.Collapsible.init(...)` looked live. No template has
rendered it since the Materialize removal. The dead initialiser is gone, its
three jest tests with it (they built their own `.collapsible` element, so they
passed on a DOM no page produces), and `_template_markup` now strips comments
before searching.

---

## website/templates/snippets/messages.html

### Module

Before this existed, **nine templates each rendered `messages` themselves and no
two agreed**. Six used a bare `alert` with no tag branch, so a failure and a
success were the same neutral box. `export.html` put Django's tag straight into
`class` - `class="success"`, which is not a DaisyUI class - and rendered plain
unstyled list items. `base.html` rendered none, which is why each page had to.

The section tags are skipped here so a full page load does not show them twice:
the htmx post keeps only its `hx-select` fragment, and those sections render
their own from `snippets/messages_section.html`.

---

## website/templates/snippets/dynamic/nfts.html

### Module

This page included design 1's `snippets/nfts.html` unchanged at first, which made
the section a different design bolted to the bottom of this one: its rows are a
three-column flex arrangement with the value wherever the text left room, so the
money column stopped at the assets. A section that opts out of that column is not
a section of this page.

---

## website/templates/base_profile.html

### Module

The profile pages inherited `base_home`'s three-column shape: a breadcrumb rail
on the left, content in the middle, actions stacked on the right. On a profile
page that produced two mostly empty gutters, a ragged column of identical green
pills for navigation, and page actions sitting so far from the fields they
operate on that the relationship was invisible. Every control was the same
weight, so nothing read as the primary one.

---

## website/templates/snippets/theme_picker.html

### Module

Recent is a separate group rather than the list re-sorting itself because a menu
that reorders under a reader makes their muscle memory wrong every time they use
it.

A reader who never reaches the appearance page is not shown a credit for themes
they were never offered, which is why the credit renders there and not here.

---

## website/templates/profile_settings.html

### The fold section

It sits beside the layout preference because both are about how the address page
is arranged, and a reader looking for "how much of my account do I see at once"
looks there rather than under Themes.

### The live-refresh section

The upgrade prompt names the allowance at the point it means something. Every
authenticated reader may switch live refresh on; what a subscription buys is the
limit coming off, and a page that quietly stops later is indistinguishable from
a broken one.

---

## website/templates/profile_appearance.html

### Module

The header dropdown lists every theme by name, which is a list you scan rather
than choose from - "abyss" and "nightfox" tell a reader nothing.

Three tabs replaced one long page: 57 swatches in a single column meant
scrolling past every dark theme to reach a light one, and the typeface section -
an independent axis, and the only gated one - was stranded at the bottom where a
reader had to already know it existed.

Radio tabs so the panels switch with no script: a reader whose JavaScript failed
still gets a working page rather than three headings and nothing under them.

`tabs-lift` is gone. It is DaisyUI's folder-tab style, and it was the one
control on the site that did not match the rest. What replaced it is the login
modal's segmented control, which is itself the swap modal's `.swap-modes`
written against theme tokens instead of `--swap-*`.

Every specimen renders in the face it offers, for the same reason the theme
swatches render in their own colours.

---

## website/templates/snippets/dynamic/nft.html

### Module

Design 1 lays the same facts out as three columns of running text with the
numbers wherever they fall, and renders "Floor price: 25.00 ALGO" eight lines
from the estimate it should be read against. None of these numbers means
anything alone: an estimate above a floor and one below it are the same number
and opposite news.

The "best offer" line shows only when it beats the last purchase, because on the
reference address the two are the same transaction for most items.

---

## website/templates/profile_authorize.html

### Module

The page now states the two routes before offering either, rather than
presenting the wallet cards and leaving the by-hand fallback to be discovered
inside a collapsible with no lead-in. That collapsible was Materialize's, and
nothing on the page initialises one any more.

What else changed in that pass: `<blockquote>` was used for addresses, though
nothing here is being quoted - the same call was already made for the historic
page, where `test_historic_assets_template.py` asserts the element is gone. The
messages block carried four colour classes at once (`badge-outline bg-neutral
text-neutral-content text-base-content/60`), so which one won depended on source
order, and carried no `role`, without which a message appearing after load is
announced to nobody. `<!-- HTML comments -->` shipped three banner rules to every
reader. And there was a `<br><br>` before the check button, above a 7/5 grid
whose right-hand column held one button.

---

## website/templates/base_bundlename.html

### Module

Rebuilt on 2026-08-22 with the shell. The fields sat in nine of twelve columns
with the actions in the other three, so Save was a third of a page to the right
of the last field it saves, level with the first - and the list of other bundles
was wedged into the rail beside them, which is real navigation in a gutter.

The primary action was previously indistinguishable from Back.

A list that silently omits the current entry makes the reader count, which is why
sibling navigation includes the page you are on.

---

## website/templates/profile_link_address.html

### Module

The two wallet families were two bare `<div>`s in a row with nothing saying where
one ended and the next began. A reader with only an Algorand wallet met a
heading-less empty area below their own wallets and no way to know it was for
something else.

**This template used to hand-roll its own copy of the EVM container, and the copy
was wrong twice over.** It had no `#evm-app-error`, so a reader with no EVM
wallet met an empty box and no explanation - `evmWalletComponent.showNoWallets`
looks for that id and does nothing without it. And it read
`wallet_connect_project_id`, which nothing provides: the context processor
supplies `WALLET_CONNECT_PROJECT_ID`, so the attribute was always empty and
WalletConnect was unconfigured on this page alone.

A second `#app-error` was invalid HTML whose only effect was that a page which
could not fetch its wallet list showed the snippet's banner and left this one
hidden forever.

---

## website/templates/snippets/home_bundlenames.html

### Module

The old card was four links to three destinations with nothing to tell them
apart: the name went to the evaluation, a line under it to the historic widget,
and the entire box below - addresses, size badge and all - was a fourth link to
the edit form. A reader could not know where a click would take them without
watching the status bar.

The filter also read `$(this).children().children().attr('title')`, which was the
literal string "Evaluate bundle" on every row - so typing "eval" showed
everything and the title matched nothing a reader would type. `home.js` matches
on the data attributes only now.

---

## website/templates/snippets/taxfinished.html

### Module

This snippet was still shaped for Materialize, and a reader reported the page
arriving as one undifferentiated column: under Tailwind's preflight the bare
`<h4>` and `<h5>` had no size and no weight, so both headings read as body text.
The redesigned `taxprepare.html` beside it already carried its own classes.

The three buttons were each wrapped in `<div class="w-1/3">` with no flex parent,
so they stacked vertically at a third of the width apiece. The agreement was four
paragraphs separated by `<br><br>` and numbered by hand; it is an `<ol>`, which
is what it always was.

### The contact links

They were four empty `<a>` elements with the label pushed off-screen by
`text-indent: -99999px` and the icon coming from `img/social/social-c.png`, a
sprite sheet no longer in the tree. With the image gone they rendered as four
blank 32x32 boxes: a paragraph asking the reader to get in touch, followed by
nothing to click.

---

## website/templates/profile_addresses.html

### The button hierarchy

Every action was a plain `btn`, so "Remove" - which is irreversible and asks for
confirmation - looked exactly like "Make primary", and "Add address", the reason
most people open this page, looked like neither.

---

## website/templates/snippets/asas/meta.html

### The metadata list

It was a `<dl>` whose children were plain `<div>`s with the label written into
the text, so it announced a list with no terms and no definitions in it - the one
structure a screen reader could have used to read "Total supply" and its number
as a pair.

---

## website/templates/snippets/nonval.html

### The amount

Observed in production on 2026-09-18 against `BNFIREKG…`: a null `asset` in a
filter argument took the whole address page down with a 500. This is the shape
`snippets/asas/program.html` was then guarded against too.

---

## website/templates/base_home.html

### Module

These pages kept the arrangement the profile section left behind on 2026-08-22: a
four-column grid with the content in three of them and a narrow rail in the
fourth, carrying right-aligned breadcrumbs and whatever the page had spare. On
home that rail held one box printing the reader's email three times, and
three-quarters of the column was empty; on the bundle forms it held a list of
other bundles, which is real content wedged into a gutter.

The old shell put the main column first so a phone met the content before the
navigation. A single column does that by construction.

---

## website/templates/profile_api.html

### Module

**The copy controls were dead.** `site.js` binds `copyToClipboard` to `.copy` and
copies `$(this).prev()`; both clipboard spans here carried `cursor-pointer` and
no `.copy`, so they said "click me" and did nothing. Three other templates -
`snippets/asas/meta.html`, `nonval.html`, `nfts/item.html` - had it right, which
is why this went unnoticed: the control looks identical and only this copy of it
was inert.

Rebuilt otherwise from a page that used `<br><br>` five times for spacing and put
the tier in a right-hand column opposite the tokens, as though the two were
comparable.

---

## website/templates/profile_account.html

### Module

Rebuilt from a 25-line page that used `<br><br>` twice for vertical spacing and
`&nbsp;` for horizontal, inside a 7/5 column split holding one line of text on
each side. The split was inherited from a denser page and made the tier and the
deactivate link read as two comparable things placed side by side, when one is a
status and the other is the most destructive action in the account.

A solid red button in the middle of a settings page is inviting, which is the one
thing deactivation must not be.

---

## website/templates/snippets/show_more.html

### Module

The rows are in the document already because the payload is in hand by the time
the page renders: a round trip to reveal dust would cost more than the markup
does, and the reader gets an instant answer instead of a spinner.

"Show more" alone tells a reader nothing about whether it is worth the tap.

---

## The Materialize migration is finished

Confirmed 2026-09-24: nothing under `website/templates/` or `website/static/`
loads Materialize, no first-party script reads `window.M`, and every template
extends `base.html` or one of its shells. What remains are prose references and
two legacy stylesheets under `widgets/inhouse/historic/`.

Three template comments still described the migration as under way, each
claiming a Materialize counterpart that no longer exists - `base.html` ("this
file becomes base.html when the last page moves off"), `snippets/modal_login.html`
and `snippets/wallet_signing.html` (both "the Materialize original stays at
<their own path>", a self-reference left by the rename). All three are corrected.

`site.js` still carries two `M.` mentions, both in comments explaining what a
call used to do. `snippets/wallet_signing.html` still explains why
`browser-default` is absent, which is worth keeping: it is a class somebody
would otherwise add back.

---

## website/templates/account/base_auth.html

The Sign up / Log in pair was a Materialize `.tabs` widget, but it never was one:
the two anchors are ordinary links to two different pages, and the child template
marked the current one with `class="active"`.

The wide-screen order - providers left of the form - is the order the old
`push-m6`/`pull-m6` pair produced.

---

## website/templates/snippets/taxprepare.html

Every hint on this page was a Materialize tooltip: `.tooltipped` with
`data-tooltip` and `data-position`, initialised by `$.fn.tooltip()`. That plugin
left with Materialize and `tax.js` guards the call, so **the hints rendered as
nothing at all** - the "Not implemented yet" note on every provider but Koinly,
and both option help texts from `core/forms.py`, were invisible. `.providertip`
went with the plugin call that was its only reader.

---

## website/templates/profile.html

`{{ field }}` was rendered *before* `{{ field.label_tag }}`, which is a
Materialize floating-label arrangement; without it the page read
"2EVGZ4... Address:" - value first, label after.

The widgets in `core/forms.py` carry no class, so they rendered with no border at
all: the name fields were invisible and only their labels showed.

Every control was a filled button, so Update carried no more weight than Social.

---

## website/templates/index.html

A lone theme switcher floating above the logo made it the first thing on the
page, which is not what it is worth - hence `footer_appearance`.

The provider icons were `{% templatetag openblock %} static %}` calls, but there
is no `static/icons/` directory any more, so nginx's `try_files` fallback had
been quietly serving `empty.png` in place of both.

---

## website/templates/export.html

`mb-10` on the page header is load-bearing: `test_page_headers` finds the header
by it.

---

## website/templates/tokenomics.html

This page had its Tailwind wrappers already - the centred column, `space-y-4`,
the muted body colour - around content still written the way Materialize left it:
every list a run of `&#8226;` characters and `<br>` tags inside one `<p>`. So the
five facts under Token Overview were one paragraph, and that is what a screen
reader announced. The table was a bare `<table>`, browser default, no borders and
no padding.

---

## Smaller templates: what was moved out of them

**`snippets/taxprocessing.html`** — the heading was a bare `<h4>` followed by a
`<br>`, which under Tailwind's preflight is body text followed by a blank line.
Same shape as `taxfinished.html`.

**`disclaimer.html`** — the first page on the DaisyUI base. Its sections were
`row` + `col s12` purely to get one readable column, so they became a capped
measure and spacing utilities: no grid is needed to replace a grid that was not
doing any grid work.

**`account/snippets/already_logged_in.html`** — was a Materialize `.chip` with a
close icon that closed nothing. There was no handler behind it.

**`features.html`** — the lead-in read "ASASTATS is used for:", copied from the
token page's Utility section. These bullets are about the tracker, not the token.
Removed rather than reworded, because every other feature below is bullets with
no lead-in.

**`subscriptions.html`** — the "1. 2. 3." were literal text, so nothing announced
the steps as a sequence and nothing would renumber them if one were added.

**`about.html`** — the pull quote was a line of text in an unclosed paragraph, so
nothing said it was a quotation.

**`bundlename_edit.html`** — deletion was a red link three lines under Save.

**`snippets/evm_signing.html`** — its comment said `data-notice` is styled by
*both* stylesheets so the snippet needs no Materialize/DaisyUI variant. There is
one stylesheet now; the snippet is still the single EVM container shared by the
authorize and link pages, which is the part worth keeping.

**`snippets/theme_icon.html`** — a half-filled circle reads as light/dark at that
size, where a sun or moon would claim a state the control does not always have.

---

## pyproject.toml

### `[tool.black] extend-exclude`

`website/utils/tests/fixtures.py` and `website/nameservice/xchain.py` are
captured payloads and fixture tables whose long lines are single data literals
black will not split; hand-wrapping them only makes them harder to diff against
a fresh capture. `website/nameservice/anssdk` is a vendored SDK and should stay
diffable against whatever it came from.

**The two submodules were added 2026-09-25.** Black picks its project root by
walking up until it finds `.git`, and a submodule's `.git` is a *file* — which
still counts — so given a path inside one it already re-roots there and reads
that submodule's own config. The exclusion covers the other case: a run from
this directory that walks into them, which would format them under this file's
settings and produce a diff in a repository this one does not own.

**This is also why `line-length = 90` had never applied inside the submodules.**
Black fell back to its default 88 there. Measured: 30 of 120 widget files format
differently at 88 than at 90. `widgets/pyproject.toml` now sets 90 explicitly,
which is also what the standalone checkout at `~/dev/widgets` needs, since this
file does not exist there. `permissiondapp/` carries no black config and is
somebody else's code.

### `[tool.isort]`

**This block does not govern `website/`.** isort walks up from each file and
stops at the first config it finds, so `website/.isort.cfg` wins for everything
under it and this one is reached only for paths outside `website/`. Verified
2026-09-25:

    website/core/views.py            -> website/.isort.cfg
    website/widgets/views.py         -> website/widgets/pyproject.toml
    website/permissiondapp/dapp/...  -> website/permissiondapp/dapp/.isort.cfg

The two disagree: `.isort.cfg` has `line_length=79`, no `profile`, and an empty
`known_first_party`, against 90/black/ten packages here. The wrapping style
matches anyway — `multi_line_output=3` plus `include_trailing_comma` is what
`profile=black` sets — so the practical difference is only how early an import
list wraps. Worth consolidating onto one file; not done.

`website/.isort.cfg` already skipped `widgets/*` and `permissiondapp/*` before
today. The globs here repeat that so the two cannot drift.

---

## website/static/js/address.js

### Module

**Why `lastRefreshAt` is armed at `Date.now()` rather than left at zero.** The tick starts at DOM ready, but `initAddress` runs on `window.onload` — after every image, font and stylesheet. On a slow page there was a window where the clock read zero, the refresh was already an eternity overdue, and the first two quiet seconds reloaded a page the reader had only just opened. On a heavy bundle that window is tens of seconds: one reloaded itself twenty-five seconds in, to a byte-identical copy of what was already on screen.

The `#id-liverefresh` guard below cannot cover it, because the marker arrives in a non-cached partial later still — twenty seconds after the document on that same page.

### `wireFetchedItems`

**A collection's items are not on the page until the reader opens it.** They used to be: every collection wrote out every item, hidden inside a closed `<details>`, and the fetch on open replaced them. On one real account that was 87.9% of a 22 MB page — markup nobody could see, and 152,294 elements a browser had to lay out before the page would scroll.

`deferImages` runs once, over the elements present at load, so items arriving later never had their `data-src` promoted to `src` and their art never appeared. That was already true of the design-2 layout, which has fetched on open all along; it is simply visible now that both layouts do.

### `restoreDisplayChoices`

**The live poll ships figures the server rendered, and the server does not know what the reader chose.** `lvp` is one payload per page, shared by everyone watching it, so it can only ever carry ALGO and the full total. The classic fragments swap the band, the `.pricetip` and every changed `span.val` — each one arriving as freshly rendered ALGO — so a reader who picked USD watched it revert on the next block, and one who had turned NFTs out of the total watched them come back.

`setCurrency` and `setTotalNoNft` ran once, at load. That was true for as long as nothing rewrote a figure after load, which stopped being true when real-time refresh shipped.

Only when the reader is away from the defaults: both functions walk every `span.val` on the page, and doing that three seconds apart on a long page for a reader who never left ALGO would be work with no effect. Both are design 1's — they return immediately on a dynamic page, where `toolbar.js` owns this and reads its own keys.

### `repaintClassicLive`

**The classic consolidated card is derived from program rows (2026-10-01).** The live payload already carries changed positions, but the classic layout previously swapped only the asset header, leaving Balance/Staked/Liquidity/DeFi figures and their Chart.js datasets at page-load values. Classic position fragments now carry stable targets; this repaint sums those rows, updates the card, and refreshes the ratio, asset, and distribution charts without touching the dynamic layout.

### `mainAddress`

**Why `toggle` fires on `<details>` and not on `<summary>`.** It fires for keyboard and programmatic opens too — which a click handler on the header would miss.

**Why `.tdist` is scoped to exclude `.dynamic-page`.** The dynamic designs use the same `.tdist` idiom — dotted at rest, opens in place — but hide their panel with the `hidden` *attribute* and carry `aria-expanded` on a real button, neither of which this handler touches. Bound here as well, the two would fight: `dynamic.js` clears the attribute while this adds the `hidden` class, and the panel stays shut with both designs believing it opened.

**Why `scroll wheel touchmove` all call `noteActivity`.** Scrolling is the interaction the guard exists for, and it is the one mousemove does not report: a wheel or a touch drag moves the page without moving the pointer.

### `noteActivity`

**This no longer resets the refresh clock, which is the whole change.** Bound to mousemove and keypress, restarting the count meant a reader who twitched once a minute was never refreshed at all — the reported "120 second delay", which was really "no refresh, ever, while you are at the keyboard". The due time is now fixed and only the *firing* waits for a quiet moment.

### `timerIncrement`

**Elapsed time, not a count of ticks.** The old version added one per second and compared against 60, which a browser breaks in two ways: it throttles a background tab's interval to roughly once a minute, so the counter advanced sixty times too slowly and a tab left open came back an hour stale; and it cannot notice time the machine spent asleep at all. A timestamp is immune to both, and it is what lets `refreshOnReturn` ask one question instead of keeping its own clock.

**Due, but busy, defers rather than cancels.** A reader who is scrolling gets left alone — a reload mid-scroll throws the page out from under them — but the due time does not move, so the refresh happens the moment they settle rather than being pushed another minute away.

**The clock moved backwards.** An NTP correction, a laptop waking with a corrected time, or the reader setting it by hand. Left alone, a stamp in the future makes `now - then` negative, which reads as "just now" forever: the refresh would defer for as long as the jump was, which can be hours. Start the minute again instead, with the reader counted as idle so a due refresh is not held back by an interaction that now appears not to have happened yet.

**Disarmed: keep the clock with the reader.** Ticking the box does not immediately fire a refresh left over from however long it has been off.

**The subscriber poll owns refreshing this page.** It swaps the figures that changed and leaves scroll position, open sections and filters alone; reloading on top of that would throw away the one thing it exists to preserve. The marker arrives in a non-cached partial after load, so this is asked every tick rather than once at startup.

### `refreshOnReturn`

**Asked as "how long since the last refresh", not "how long was it hidden".** The two agree in the ordinary case and differ in the one that matters — a tab hidden for thirty seconds when the clock already stood at forty-five has been stale for over a minute, and only the first question notices.

### `setCurrency` / `setTotalNoNft`

**Design 1 only.** This writes `innerHTML` — number *and* unit — into every `span.val`, which is right for design 1, where the unit is part of the value's own text. The dynamic designs pair each figure with a separate unit element: a sibling `.u.unit` in an asset header, a nested `<span class="unit">` in a venue subtotal. So this rewrote the header to "253.74 ALGO" beside a sibling still reading "ALGO", and destroyed the nested span in every subtotal — on every load, because it runs unconditionally with the stored currency. It also cannot reach a breakdown figure there at all, which is a `<button>` rather than a span.

`toolbar.js` owns currency on that page and writes only the number.

### `checkOpened`

**The entries are `<details>` children of the section container, so the one to reopen is addressed by id and opened directly — no index into a widget's internal list.**

**`.find()`, not `.children()`.** The rows are wrapped inside the section rather than being its direct children — the section carries a heading above them — so a child walk finds the heading and the wrapper and never reaches an entry. The remembered row then silently fails to reopen after a refresh.

### `reloadPage`

Reloads the page and reopens the same accordions by storing open section ids in localStorage before reload.

### `setTotalNoNft`

**Design 1 only, for the same reason `setCurrency` is.** This writes the headline's `innerHTML` — figure *and* unit — reading the currency from design 1's own global `cur` key. On the dynamic page that meant the total was written by design 1 on load and by nobody afterwards: a reader who had ever chosen USD anywhere got a USD headline in a fresh tab, and pressing USD in that page's own toolbar changed every figure except the one at the top. `toolbar.js` owns the headline there.

### `nftShowTooltip`

**Built as elements rather than an HTML string.** The old call handed `unsafeHTML` a concatenated `<img src='...'>`, so an engine-supplied path containing a quote could close the attribute and inject markup. Setting `.src` cannot do that whatever the value.

### `setTip`

**`data-tip` is the attribute DaisyUI's `.tooltip` reads.** This code wrote `data-tooltip`, which is Materialize's and which nothing on this site has read since the conversion — so the total's tooltip was correct as the server rendered it and then never changed again. Switch to USD and it still quoted the ALGO figure and the old rate.

**`data-position` went the same way:** also Materialize's, also dead. DaisyUI places a tooltip with `tooltip-top`/`tooltip-bottom` classes, and design 1 asks for neither, so the writes are simply gone rather than translated.

**An element that wants its tip *announced* points `aria-describedby` at a visually hidden span**, and this keeps that span in step: a tooltip drawn with `content: attr(data-tip)` is not dependably in the accessibility tree, so the hidden text is what a screen reader actually gets.

**The attribute goes on whatever actually draws the tooltip.** On the site that is a `.tooltip` wrapper around the figure — DaisyUI reveals on `:has(:focus-visible)`, so the focusable element has to be *inside* it — and on the historic widget's page it is the figure itself, which carries the widget's own `.htip`. `closest` covers both without either caller having to know which page it is on.

### `toggleDist`

**Found by a stable attribute rather than by `.parent()`.** The control is the value span, and which element it sits directly inside is a layout decision — wrapping those lines in a block, which is what replacing a column of `<br>` tags means, would silently move the shadow onto the wrapper. Not `.closest(".asar")` either: `asar` is half of what this toggles, so the second click would no longer find the panel.

---

## website/static/js/toolbar.js

### Module

**Why the toolbar exists.** The address page is `cache_page`'d and its entry is shared between every reader on the layout, so the server cannot know what this reader has filtered to and must not render it. The state lives in their browser under `view:<path>`, beside the pins and the saved order.

**One state, three drawings.** The allocation bar, the five category figures and the donuts are three drawings of one set of numbers, and all three are wired to the same `state.cats`. A reader who saw the bar and the figures disagree would have no way to tell which one lied, so they are recomputed together, from the same pass over the same rows, every time anything changes.

**The one figure that never moves.** The headline is what the address is worth. No filter, no search, no category toggle may touch it: a reader who hides a category has not become poorer. Everything below it is a subtotal and is free to respond. This file never writes to `.total`.

**How it shares the page.** Three other scripts already own parts of this page, and the toolbar defers to each rather than duplicating it:
- `pins.js` owns the *order*. Sorting does not reorder the DOM directly; it hands `pins.rebase` a new baseline and lets pinning apply on top, so a pinned row stays pinned through a sort.
- `showmore.js` owned the fold and no longer does here. It reveals a whole tail in one press, which is design 1's rule; these designs show a fixed first batch and add one batch per press, so it stands down on `.dynamic-page` and this file folds instead.
- `dynamic.js` owns the donuts. The toolbar hands it filtered slice data and asks it to redraw.

**Currency is the exception, and deliberately:** `address.js` has `setCurrency`, and it is wrong for this page. It writes `innerHTML` including the unit into every `span.val`, which on this markup destroys the nested `<span class="unit">` inside a venue subtotal and leaves the asset header reading "253.74 ALGO ALGO" — the value cell has a *sibling* unit element. It also cannot reach a breakdown control, which is a `<button>` rather than a span. `address.js` no longer touches `.dynamic-page`; the writer here does, and it writes the number only, leaving every unit element alone.

### `readView`

**Field by field rather than all-or-nothing.** A stored view written by an older build is missing whatever has been added since, and discarding the whole thing would throw away a reader's currency because a sort key appeared. Each field is validated on its own terms, so a value that is no longer offered — a removed sort, a category that stopped existing — falls back without disturbing the rest.

**One try for every read.** A store that refuses one refuses them all — a private window, cleared site data, a browser set to block it — so a second catch further down would be a branch nothing can reach.

**An empty stored array is a reader who switched every category off, and is not the same as no stored array at all.**

### `writeView`

**Removing rather than storing the defaults** keeps a reader who has reset from carrying a key that says nothing, and means "has this reader customised anything" is answerable without comparing objects.

**The reader-level settings are stored under their own keys above;** writing them here too would give one setting two homes that can disagree.

### `fmt`

**Exactly two decimals, always.** A money column has one shape, and every figure in it has to be readable against the one above without counting digits first.

This used to widen anything under half a cent to *six* places, on the reasoning that "0.00" reads as nothing owed rather than as a small debt. The cure was worse: it put a six-decimal figure in a column of two-decimal ones, so a 0.004574 sat under a 1,284.02 and read as the larger number at a glance — and it did it for ordinary dust holdings, which are most of what is down there, not only for borrowings. The server has always rendered these cells with `floatformat:'2g'`, so the widening was also the one thing on the page that changed a figure between the HTML arriving and the first repaint.

A holding worth less than a hundredth of an ALGO *is* "0.00" to a reader deciding anything, and the row still names the amount and the unit beside it. If the near-zero cases ever need distinguishing again, the answer is a "<0.01" treatment, which keeps the column's shape; it is not more digits.

### `evaluate`

**One pass, producing everything the rest of the render needs:** which positions are live, which assets keep any, each asset's filtered value, and the four category totals the band draws. Computing these separately is how a bar and a figure come to disagree.

**A position is live when its category is on *and* it matches the query, or its asset does** — typing an asset's ticker should not require every row inside it to repeat the ticker.

**The category totals ignore the category filter**, and that is not an oversight. Two reasons, and the second is decisive. A figure reading "Liquidity 0.00" the moment it is switched off tells the reader they hold none, when what happened is that they hid it — the honest reading is the real number, dimmed. And a bar segment whose width went to zero would have no box to click, so the only way to switch a category back on would be the figure beside it: the control would disable itself. They respond to the search, which genuinely narrows what the address is being asked about.

### `batchFor`

**Its own function because two callers need it and one of them is the label.** `fold` used to read `data-initial` directly to say "Show N more", while `limit` above preferred the reader's choice — so a reader who set collections to 20 saw twenty rows, pressed a control that said ten, and got twenty. The control was lying about itself in exactly the way the label's own comment says it must not, because the two numbers were derived twice from different places.

### `foldSize`

**Read from the same attribute the CSS reads.** `base.html` stamps it before paint from `localStorage`, the stylesheet acts on it for the gap before this script runs, and this function acts on it afterwards. One value in one place: the alternative is the stylesheet and the script disagreeing about how many rows are shown, which shows up as a control offering to reveal rows already on screen.

`"all"` is `Infinity` rather than a large number, so `Math.min` against the row count does the right thing without a magic constant to outgrow.

### `sortNumber`

**`data-sort-value` is the figure the page was rendered with and does not move.** The live refresh swaps the value *span* out of band on every block and deliberately leaves the row alone — swapping the row would close it, discard the reader's drag order and lose anything open inside. So after a while the two disagree, and sorting by value put the rows in an order that contradicted the column beside it.

The span carries the same quantity — both are the unrounded value — so reading it costs nothing and is right whether the page is a minute or an hour old. `data-sort-value` stays as the fallback for a row whose value cell is missing, and for the three sorts that have no live equivalent.

### `order`

**Not applied to the DOM here.** `pins.js` owns the order: it floats pinned rows above the rest and applies any order the reader dragged, and if this file also called `appendChild` the two would each undo the other depending on which ran last. Instead the sorted list becomes the *baseline* it arranges from, and pinning still wins — which is right, because pinning is the reader saying "this one, whatever else is going on".

Name sorts by the ticker and ties break on it too, so two assets worth exactly the same amount do not swap places between renders.

**The served order is the default sort, so restoring it is what "Reset" hands back** — and `rebase(parent, null)` is the only way to get it, because nothing else keeps a copy.

### `paintAssets`

**Read back from the DOM rather than from `view.live`.** `pins.js` has just reordered, and the fold applies to the first N *as displayed*, which is not the order this function was handed.

### `fold`

**Shared by the two sections because they are the same rule applied to different lists** — and because a second copy is how the assets and the collections come to disagree about what "show more" means.

**From `batchFor`, the same source `limit` folds by.** Reading `data-initial` here instead was how the label came to say ten over a control that revealed twenty.

**Nothing folded means nothing to reveal.** Left in the document rather than removed, because the next keystroke may fold rows again.

### `paintFigures`

**Venue subtotals and asset headers are recomputed from the live positions rather than left at what the server rendered:** a reader who has hidden Liquidity is shown an asset header that still counts it, and the numbers stop adding up down the column — which is the one thing this design promises.

**Asset values use `data-val` when no filter is active, the filtered sum of positions' `data-value` when a filter is active (2026-10-02).** When no filter is on (`!state.q && state.cats.length === CATEGORIES.length`), the asset value span carries the current payload value via `data-val`, set by the OOB swap on every poll regardless of caching. This is the only path that yields correct figures on a cached page: the page cache key is the holdings fingerprint, which excludes values — only asset IDs and position identities are hashed. So a re-price with no position change serves a cached page whose positions' `data-value` attributes are stale. The poll sends only changed positions as fragments, so unchanged positions keep their stale `data-value`. `paintFigures` must not sum them. It reads `data-val` instead, which the OOB swap keeps current. When a filter IS active, `data-val` carries the unfiltered total (the reader did not ask for it), while `view.values[card.id]` correctly sums only the visible positions — and the reader explicitly chose to see only those. The stale-position problem does not bite there because a reader who filtered is looking at positions they can see, which the poll reached and `settlePosition` kept current. Either way a non-number counts as nothing: `num(element, "data-val")` and `num(position, "data-value")` both return 0 for `"n/a"`.

**A subtotal over a single row is that row's own figure said twice, three lines apart, and the two cannot differ.** The template leaves it out for a group served with one position; a filter can take a bigger group down to one, so the same rule applies here.

### `write`

**The reason this file has a currency writer of its own.** Every value cell on this page pairs a number with a unit, and the unit is a separate element — a sibling in the asset header, a child in a venue subtotal. `innerHTML` on the value destroys or duplicates it. Only the number is written, and only into the first text node, so an element that holds `12.34 <span>ALGO</span>` keeps its span.

### `paintTotal`

**The one figure no *filter* may move** — a reader who hides a category has not become poorer — but the currency is not a filter. It is the unit the whole page is denominated in, and a page whose every figure says USD above a total that says ALGO is not showing a total at all. That was the reading this file got wrong.

**"Total without NFTs" moves it legitimately**, because it changes *what is being totalled* rather than how it is displayed. It is design 1's setting and design 1's storage key, so the two pages agree.

`.pricetip`'s own data attributes carry both currencies and both totals, so nothing here recomputes from rendered text.

### `paintReadout`

**"Unfiltered" is read off the state, not off the arithmetic.** It used to be inferred from the two figures differing, which is only the same question while the two agree about the address: `shown` is summed from the rows this page was rendered with, and `whole` comes from whatever the live pass last published. Those are two readers of the same account, and when they disagree — a re-price that valued fewer positions, a reload suppressed by the cooldown, a resync still draining — a page with nothing switched off announced "Showing 29.48 USD of 13.89 USD", which is not a filter and reads as the page having lost track of the money.

Reported from production on 2026-09-18, and the engine side of it is real: the live pass published 304.55 and 143.46 ALGO for the same page within the hour. This element is not the place that surfaces it — it exists to say what the *filters* left out, and it now says nothing when they left out nothing, whatever the two totals think.

### `paintBand`

**Applied here rather than only where it is toggled,** so a reader who hid the collections and came back is not handed them again while the figure still reads "off". Every other part of the state is applied on every render; this one was not, and only a reload showed it.

**The NFT figure keeps its served value:** it is not a subtotal of anything the position filter can reach.

**All three from `view.totals`, in one place,** because they are three drawings of one set of numbers and a reader who sees them disagree has no way to know which one lied.

### `toVenues`

**Moved, never copied:** a copy would put a second element on the page with the same `data-pid`, and a pin names a position by that id. Moving also keeps open breakdowns, bound handlers and the position pins working, because they are the same nodes — `appendChild` on an element already in the document relocates it.

**Where each group came from is remembered on the group itself,** so switching back is exact rather than reconstructed.

**The *index* among its siblings, not the sibling itself.** A remembered `nextElementSibling` is only valid while that sibling is still where it was, and an asset holding four venues has all four moved away — so restoring the first one threw, because the node it was to be inserted before had itself been moved. An index survives its neighbours leaving and coming back.

### `toAssets`

**Sorted by where each group belongs before any of them moves,** so an asset holding four venues gets them back in the order the server ranked them rather than in whatever order the venue cards happened to be built. Appending in ascending index order rebuilds the sequence exactly, because `.program-groups` holds nothing but these.

**The emptied cards, not the list's whole contents.** Wiping the list would take a group that somehow has no remembered home with it — and a position row deleted from the page is the worst thing this file could do, because the reader has no way to tell it was ever there.

### `regroup`

**The section still called itself "Assets 76" over a list of venues.** The served text is kept rather than rebuilt, so switching back restores exactly what the template rendered — including a count that is the server's, not this script's arithmetic.

### `paintReadout`

**"Unfiltered" is read off the state, not off the arithmetic.** It used to be inferred from the two figures differing, which is only the same question while the two agree about the address: `shown` is summed from the rows this page was rendered with, and `whole` comes from whatever the live pass last published. Those are two readers of the same account, and when they disagree — a re-price that valued fewer positions, a reload suppressed by the cooldown, a resync still draining — a page with nothing switched off announced "Showing 29.48 USD of 13.89 USD", which is not a filter and reads as the page having lost track of the money.

Reported from production on 2026-09-18, and the engine side of it is real: the live pass published 304.55 and 143.46 ALGO for the same page within the hour. This element is not the place that surfaces it — it exists to say what the *filters* left out, and it now says nothing when they left out nothing, whatever the two totals think.

### `render`

**Structure first, and that ordering is load-bearing.** Switching to venues *moves* the position rows out of their asset cards, so anything that measured before the move would total an asset at zero and hide every card on the page — which is exactly what "Reset view" did until this ran first.

### `paint`

**The poll ships what the server rendered, and the server does not know what this reader chose.** `lvp` is one payload per page, shared by everyone watching it, so it can only carry ALGO and the full total. The fragments replace the band and every changed figure — so a reader who picked USD watched it revert on the next block, and one who had turned NFTs out of the total watched them come back.

### `repaintAfterSwap`

**Recompute derived figures for the default reader too (2026-10-01).** A live position fragment updates the row's `data-value`, while venue subtotals and the allocation figures are derived DOM values rather than wire fragments. Skipping the repaint only in the default ALGO/full-total state left those values stale beside the refreshed headline; the extra pass is required for correctness, not only for currency conversion.

---

## website/static/js/dynamic.js

### Module

**Why SVG not Chart.js.** Four reasons:
1. **Theming.** The site ships 57 themes. An SVG `fill` can be a `var(--color-...)` and repaints itself when the theme changes; a canvas must be handed literal hex at draw time, which is why design 1's palette is hardcoded and why a theme switch cannot recolour its charts without re-reading computed styles and redrawing.
2. **Interaction.** A slice here is a real element with a `<title>`, so it can be hovered, focused and described. Canvas slices are pixels needing hit-testing and a separate event path — which is exactly why `chartClick` is the function the selector contract lists as known-broken. Under SVG that bug class stops existing rather than being ported.
3. **Size.** Around 200 KB of Chart.js for five slices.

**Live chart repaint (2026-10-01).** The live poll updates DOM position values rather than the JSON blocks used for first draw. The toolbar now supplies current asset totals when it repaints the allocation chart, top-assets chart, or assets-by-value chart, including after a previously closed panel is opened.
4. **Accessibility.** A canvas is opaque to a screen reader.

**The payload is unchanged:** the same six `json_script` blocks design 1 emits, in the same Chart.js-shaped `{labels, datasets: [{data, backgroundColor}]}`. Only the renderer differs, so the JSON API and the website keep one source of truth.

**Nothing is drawn until the reader opens the charts panel.** Six donuts of SVG is a great deal of markup to hand someone who never looks at it.

### `CHARTS` order

`nftfloorchart` is deliberately last: it is the least-asked question on the page, and a reader scanning left to right should meet the allocation and the top assets first.

`total` names what the payload's percentages are a percentage *of*, read off the header's own data attributes in ALGO. Four of the five blocks carry shares rather than amounts — `"46.30882653"` means 46.3% of the assets, not 46.3 ALGO — and the legend was printing those bare, so a reader saw a column of figures in the same shape as every other figure on the page and none of them were money. `distchart` is the exception and says so.

### `colorFor`

**Chart.js accepts `backgroundColor` as either an array — one colour per label — or a single string for the whole dataset, and the payloads use both.** Indexing a string gives *characters*: `"#005a34"[1]` is `"0"`, which is not a colour, and the "Top assets" donut was drawn entirely in invalid fills because of it.

**A stacked payload has one colour per *category*, so no colour of its own for a per-label total.** `palette` is the way out: the assets chart names the same labels and carries a colour for each, so a lookup by name gives the same asset the same colour in both charts. By name and not by index — the two payloads happen to agree on order today, and a lookup that depends on that is a lookup that breaks silently.

### `slices`

**Stacked payloads are summed, not truncated.** `distchart` carries one dataset per allocation category — Balance, Staked, Liquidity, DeFi — and this used to read `datasets[0]` alone, so "Top assets" was really "top *wallet balances*": an asset held entirely in a liquidity pool was drawn as nothing, and the donut did not add up to the section it sat under.

### `palette`

The assets chart is the only payload naming every asset *and* carrying a colour for each, so it is where a stacked payload borrows its colours.

### `headline` / `whole` / `scaleFor`

Reads the same header and attributes `toolbar.js` reads, so the charts and the rows cannot come to different conclusions about what the address is worth.

### `money`

**The rule is `toolbar.js`'s, deliberately.** The two must agree: a chart legend and the asset row it describes are the same figure, and a reader who sees them disagree has no way to tell which one is rounded.

### `arc`

**A full ring cannot be one arc:** SVG collapses a 360-degree arc to nothing, so a single-slice donut would render blank. Two circles wound in opposite directions, punched through with `fill-rule="evenodd"`, is the ring.

### `paint`

**Built with `createElement` and `textContent`.** Labels are asset and collection names that came off the chain, and a unit is whatever its creator typed — the one place on this page where markup could be smuggled in.

**The arcs re-normalise on what is left.** Crossing an asset out is the reader saying "and what does the rest look like" — the same question design 1's chart answers, and the reason its legend is clickable at all. A ring that kept a gap where the crossed slice was would answer a different one.

**The hole is where the figure goes.** Design 1 puts this total in the chart's title block; here the middle of the ring is both empty and exactly where a reader looks, and it is what makes crossing a slice out worth doing — the number moves.

**A real button, because it does something.** It was a `<div>` carrying no affordance at all, which is half of why these charts read as pictures of design 1's rather than as the same control.

### `toggleKey`

**The redraw replaced the button that was pressed, so focus has to be put back on its replacement** or a keyboard reader is returned to the top of the document after every press. Matched by reading the attribute rather than by building a selector from it: a label is an asset name off the chain and may hold a quote.

### `draw`

**The assets chart is the only payload naming every asset *and* carrying a colour for each**, so it is where a stacked payload borrows its colours.

**Which payload a chart was drawn from, so `redrawAllocation` can find the one it is allowed to replace.** Its heading is not the handle: that is copy, and copy changes.

### `redrawAllocation`

**The bar, the five figures and this chart are three drawings of one set of numbers,** so when the toolbar filters a category out all three have to follow. The other charts are of the whole address and are deliberately left alone — the same rule the headline follows: a reader who hides a category has not stopped holding it.

**The category colours come from the stylesheet's `--c-*` custom properties rather than from a table here,** so the donut, the bar and the figures cannot end up painting the same category two different colours.

### `toggleBreakdown`

**The third level of the page:** what the figure in the money column is made of. `address.js` has a handler of the same name for design 1 and it does not work here — it toggles a `hidden` *class*, while this design hides the panel with the `hidden` *attribute*, so the class went on and the panel stayed shut. The control looked exactly right, dotted and inviting, and did nothing; `functional_tests/test_address_dynamic_page.py` is what caught it.

**The control is a real button carrying `aria-expanded`,** so the state is set here too. Design 1's control is a span and has none, which is the other half of why the two cannot share a handler.

### `epochs`

**`.epoch` is design 1's contract and the dynamic section keeps it, but the *filling* could not be kept:** `showTimes` is bound to `.nft.item-header` and looks for `.item-body` siblings, and this design has neither — a collection is a `<details>` with a `.chead` and a `.cbody`. So the section rendered "Last purchase on Rand Gallery" with no indication of when, which reads as a rendering fault rather than as missing data. `functional_tests/test_address_dynamic_nfts.py` is what noticed.

**Filled once on load rather than when a collection opens.** Design 1 defers it because its handler is per-collection; there is no handler here, and formatting sixty-five intervals is not work worth deferring.

**`timeEntry` is `address.js`'s, which this page loads first,** and is used so the two designs word the same fact the same way. The fallback is a plain date rather than nothing: a reader who is told a purchase happened is owed when, and a script that failed to load is not their problem.

### `breakdowns` / `watchSwaps`

**Delegated from the document, so the rows `pins.js` moves — and any that arrive with an htmx partial — need no rebinding.** Guarded on the root element for the same reason `showmore.js` guards there: this file can run twice, and a second set of handlers would open and immediately close.

**`document`, not the swapped region.** `epochs` selects `.dynamic-page .epoch[data-epoch]`, and that ancestor is *above* the swapped region rather than inside it — so a region-scoped query matches nothing. Re-running over the whole page is cheap and recomputes the relative times, which are stale by then anyway.

**`htmx:after:swap` on `document.body` is how the rest of this codebase listens** — `address.js`, `toolbar.js`, `theme.js` and the alerts widget all do. Note the colons: htmx 4 renamed these events, and `htmx:afterSwap` silently never fires.

### `init`

**The charts are drawn on first open rather than on load, and only once.** The payload does not change while the page is open, so redrawing on every toggle would rebuild several hundred nodes to show the same picture.

---

## website/static/js/theme.js

### Module

**Why theme applied inline in head.** The first application happens inline in the document head, before the stylesheet paints, so there is no flash of the default theme; this file only handles the picker itself and the writing.

**The theme is a client-side preference and is never sent to the server.** The list of themes offered comes from `settings.AVAILABLE_THEMES` via the template, so this file never needs to know the names.

**Two controls share this file:** a signed-out reader gets a smaller choice than a signed-in one:
- `[data-theme-toggle]` — a plain light/dark switch, the only appearance control an anonymous reader sees.
- `input[name=theme-dropdown]` — the full list, for signed-in readers.

**The pair the toggle flips between is read from the button's own data attributes** rather than written here, so the brand theme names live in settings and templates only.

### `applyTheme` / `applyTypeface`

**Written to the document element and to localStorage.** Private-browsing quota rules can refuse the write; the theme still applies for this page but will not survive a reload.

### `wireFoldPicker` / `wireFoldReset`

**Written to the same `localStorage` keys the inline head script reads**, and stamped onto the document element here so the choice takes effect on the page the reader is looking at rather than on the next one. The address page's own scripts read the attribute, not the storage, so one value travels: storage across page loads, attribute within one.

**`data-fold-target` on the group names which key its radios write.** One handler for both groups rather than one per section, because "assets" and "collections" differ only in the key.

### `resetFold`

**Not the same as pressing the default's own radio.** Every radio *stores* its value, and an address page reads storage in preference to the site's own setting — so choosing 20 pins 20, where choosing nothing follows `settings.ADDRESS_INITIAL_ASSETS` wherever it goes. Only removing the key returns a reader to the second state, and nothing else in the panel can.

**The attribute goes too,** so the page being looked at changes with the press rather than on the next load — the same reason `applyFold` stamps it.

### `countThemeUse`

**Counting at load time, deliberately.** The alternative is to count on the way out — `beforeunload` or `pagehide` — which is unreliable on mobile, where a tab is often killed without either firing.

Counting at load time also gives the rule this exists for: flipping through swatches on the appearance page fires no page load, so browsing costs nothing, and the theme that survives a navigation is the one that scores. A reader who then visits ten more pages adds nothing further, which is why the count reads as "chosen and kept" rather than "page views".

**Nothing here is sent to the server.** The theme is a client-side preference, so its tally belongs in the same place — a tally that synced while the theme did not would order the menu by a history this browser never had.

### `wireRecentThemes`

**Items are cloned from one the template already rendered,** so the markup for a theme entry exists in exactly one place. A theme promoted into Recent is removed from the list below, because two radios sharing a name and a value are one control rendered twice — they fight over which shows as chosen.

### `selectSchemeTab`

**The tabs are radio inputs with a fixed `checked` in the markup, so without this the page always opens on Dark** — and a reader on a light theme lands on a panel their theme is not in, with no sign that it is one tab away.

### `wireThemePicker`

**Idempotent, so it is safe to call again after an htmx swap replaces the header.** Guarded by a data flag rather than by removing listeners, which would need a reference the caller does not keep.

**The header can be replaced by an htmx swap; re-tick and re-bind after one.**

---

## website/static/js/consolidated.js

### Module

**Why `setTip` copied from `address.js`.** This file is the one the historic widget's page loads, and that page does not load `address.js` at all. Calling across would be a `ReferenceError` on every "without NFTs" toggle — which is exactly how the widget's own currency switch was broken, by a call to a `setTotalCharts` that lived only on the site.

**`data-tip` is what displays the text:** DaisyUI's `.tooltip` on the site, and the widget's own `.htip` on the historic page. This wrote `data-tooltip`, which is Materialize's and which nothing has read since the conversion, so the total's tooltip never changed once the server had rendered it.

**The `aria-describedby` target is what a screen reader gets,** since a tooltip drawn with `content: attr(data-tip)` is not dependably announced.

### `setTotalNoNft`

This page uses `hcur`/`htotalnonft` keys, distinct from the site's `cur`/`totalnonft`, so the two designs keep independent settings.

---

## website/static/js/showmore.js

### Module

**Design 1's address page shows the first `ADDRESS_INITIAL_ASSETS` assets and `ADDRESS_INITIAL_COLLECTIONS` collections,** and each press of the control adds that many again. The section publishes the number as `data-initial`, from the same setting the template rendered the first fold from, so the two cannot disagree about what one press is worth.

**This replaced a magnitude rule** — show the rows accounting for 99.5% of the section's value, then reveal *all* of the rest in one press. Both halves read as arbitrary from the outside: the first showed 33 rows on one address and 8 on the next with nothing on the page to explain the difference, and the second made the control's own label untrue, promising "Show 39 more assets" and then being a one-shot unfold rather than a load-more. The dynamic designs already worked this way (`toolbar.js`), so this is the two designs agreeing.

**There is nothing to fetch,** so there is no loading state, no failure state and no request. The payload is in hand before the page renders, and a round trip to reveal dust would cost more than the markup already does.

**The button owns the state in `aria-expanded`,** and the stylesheet reads it to pick which of the two labels shows. The script writes the *count* inside the "show more" label and nothing else: which label is visible stays a function of the attribute a screen reader already reads, so the two cannot disagree.

### `containerFor`

**The control sits after its container rather than inside it** — it is not one of the rows — so this looks backwards from the wrapper it lives in rather than upwards from the button.

**Falls back to the nearest section,** so a wrapper added between the two degrades to "unfolds the right section" rather than to nothing at all.

### `rows`

**Its `.fitem` children only.** A container may hold other things — a heading arriving later, a note — and counting those would shift the fold by however many of them there are.

### `batchSize`

**Read off the *section* rather than off the folding container,** because that is where the dynamic designs publish it and `toolbar.js` reads it from — one place for the number in both designs, so they cannot drift apart.

**Falls back to "all of them" when no section publishes a batch size,** which is the pre-batching behaviour: a template that forgets the attribute keeps working rather than revealing one row per press.

### `foldSize`

**Read from the same attribute the stylesheet reads.** `base.html` stamps it before paint from `localStorage`, the `html.prefold` rules act on it for the gap before this script runs, and this reads it afterwards. One value in one place: a script and a stylesheet disagreeing about how many rows are shown surfaces as a control offering to reveal rows already on screen.

**Which section it is comes from the section's own class,** the same pair the stylesheet keys on - `.asasec` and `.nftsec` exist in both designs.

### `paint`

**Everything is showing, so the only thing left to offer is putting it back.** A reader who chose to see every row gets a control whose only remaining offer is "Show fewer", and pressing it would reveal the same rows again — the batch is already the whole list. The template renders the control from the *server's* fold, which does not know what the reader chose, so hiding it is this script's job. `toolbar.js` does the same for the dynamic designs.

**The stylesheet's job is over the moment this runs.** `html.prefold` rules position rows by DOM index, which is right until something starts folding by a filtered index instead. This script does not filter, but it does own `.folded` from here on, and leaving both in force would mean two answers to one question. Dropped here rather than at load because, unlike the dynamic designs, nothing paints this page until a press: until then the stylesheet *is* the reader's fold.

### `toggle`

**A press that never travels is a click on the grip, not a drag.**

### `init`

**Design 1 only.** The dynamic designs fold from the toolbar, which also filters and sorts, and two handlers on one control would both act — a batch revealed *and* the batch counted — so the second press would have nothing left to do.

**Delegated from the document so a section arriving later needs no rebinding,** and guarded so a second execution of this file — which the page's htmx partials make possible — does not toggle twice per click.

**Belt as well as braces.** The attribute above stops a second *binding*; this stops a second binding that slipped past it from acting, because the failure mode is silent — two handlers toggle and untoggle, and the button simply looks dead. `defaultPrevented` is the standard way to ask "has something already handled this", and the first handler sets it.

---

## website/static/js/pins.js

### Module

**Why localStorage not server.** The address page is `cache_page`'d and its entry is shared between signed-in readers, so anything per-reader rendered into it would be handed to whoever asked next. The markup therefore ships every control at rest and this file sets the ones belonging to whoever is looking.

**Why DOM not CSS `order`.** `order` would be cheaper and avoid a reflow, but it moves a row visually while leaving it where it was for a screen reader and for keyboard navigation — the precise fault the position component was rebuilt to remove. A row the reader put first has to be first in both senses or it is not first.

### The model

**A section is laid out as pinned entries, then the rest.** Two stores:
- `pins:<path>` — ids in pin order, across both sections
- `order:<path>` — section key -> ids in the reader's order

The server's order is captured once, before anything moves, and every render is rebuilt from it. Rebuilding from the original rather than mutating in place is what lets unpinning put a row back where it belongs instead of wherever it happened to end up, and what keeps an entry that has appeared since the last visit in its served position rather than at an arbitrary end.

**A drag is confined to its own group:** a pinned row reorders among pinned rows, an unpinned row among unpinned. Letting a row cross the boundary would mean either silently pinning it or recording an order that the next render undoes.

### `SERVED_PROP` / `BOUND_ATTR`

**The served order is kept on the container element, not in a module-level Map.** The listeners are bound once per document rather than once per execution. Both are for the same reason: this script can run twice. It is a plain `<script>` today, but the address page already pulls one in through an htmx partial, and a second execution with module-scoped state would bind a second set of delegated handlers — so a single arrow key would move a row twice, and each instance would consult its own idea of the served order.

With the state on the DOM, a second execution is a no-op that re-applies.

### `BASELINE_PROP`

**The toolbar sorts this list.** Sorting and pinning are the same operation applied twice — both decide what order the rows are in — so they cannot each own the DOM independently: whichever ran second would undo the first. Instead the toolbar hands its sorted order here and `layout` treats it as the order the page arrived in, floating pinned rows above it exactly as before.

Kept apart from `SERVED_PROP` rather than overwriting it, because "what the server sent" is still needed: `rebase(parent, null)` restores it, which is what "Reset view" means, and there is no other copy of it anywhere.

### `load` / `save`

**Anything unreadable is treated as nothing stored.** A reader with corrupt state gets the page in the server's order, which is a perfectly good page rather than an error.

**Private browsing and a full quota both throw, and neither is a reason to refuse to rearrange the page.** The reader gets the arrangement they asked for and does not get it back tomorrow.

### `arrange`

**An entry the reader has never moved, or one that has appeared since they last visited, stays where the server put it relative to its neighbours rather than being swept to either end.**

### `baseline` / `rebase`

**The toolbar's sorted order when there is one, the served order otherwise.**

**Only entries the server actually sent are accepted, and every one of them has to appear.** A caller that dropped a row would delete it from the page the next time `layout` ran, because `layout` rebuilds from this list. A sort reorders; it does not filter. Filtering is a class on the row.

### `layout`

**`appendChild` on an element already in the document moves it, so this is a reorder rather than a rebuild.** Open `<details>`, bound handlers and scroll position all survive it.

### `remember`

**Read back from the document rather than computed,** so whatever the reader sees after a move is exactly what is stored. Both groups are written as one list: a row cannot cross the pinned boundary by dragging, so the list stays consistent with the pinned set that `layout` will re-split it by.

### `toggle`

**A newly pinned entry goes to the *end* of the stored list, so it lands at the bottom of the pinned group rather than displacing what is already there.** Pinning a second thing should not move the first.

### `readPositions` / `writePositions`

**Each entry is `{pid, amount}`.** The amount is a *witness*, not part of the identity.

### `resolve`

**Most pids name exactly one row and this is a lookup.** Some do not: where the payload carries nothing that tells two positions of the same program apart — same asset, same type, same venue, same link — they hash to the same pid, and the row is marked `data-pid-ambiguous`.

**For those, the stored amount breaks the tie.** It is not part of the pid on purpose: hashing it in would change the id whenever the amount changed, which is the one property the id exists to have. Amount rather than value because value moves with the price on every load, while amount moves only when the reader actually stakes or unstakes — so the witness is stable in exactly the situation the pin has to survive.

**An exact amount wins outright; otherwise the nearest.** This can still pick the wrong row, but only if two positions of one program cross in magnitude between visits — far narrower than an ordinal, which breaks on *any* reordering — and the row says so via `data-pid-ambiguous`.

### `layoutPositions`

Lays out one asset's positions: pinned first, the rest as served.

### `renderBand`

**The dynamic designs put pinned positions in their own band rather than only floating them within their venue.** A position pinned from an asset the reader has to scroll to and open is otherwise pinned somewhere they cannot see, which is most of the value gone — and in a venue holding one position there is no order for floating to change at all.

**The band holds copies, not the rows themselves.** Moving a position out of its asset would take it away from the money column it is aligned to, and from the venue subtotal it contributes to; both are the reasons the number can be read at all.

**A pin whose position is not on the page any more keeps its card, marked `.stale`.** Dropping it silently would tell the reader nothing about why the thing they pinned vanished — and the position may simply be inside a folded tail rather than gone.

**Built with `createElement` and `textContent`.** Card text is asset and venue names that came off the chain, and `innerHTML` here would be the one place on this page markup could be smuggled in.

### `togglePosition`

**Identified by the control's own row rather than by the pid alone:** two rows can share a pid, and the reader pressed one of them. The amount is captured from that row at pin time, which is what makes it the witness.

### `unpinPosition`

**By pid rather than by row,** because the card in the band may have no row to point at — unpinning a stale card is the main thing this is for.

### `group`

**Its own group, in document order:** pinned rows move among pinned rows and unpinned among unpinned. Crossing the boundary would mean either silently pinning a row or recording an order the next render undoes.

### `move`

**Insert *after* the target when moving down, before it when moving up** — otherwise a one-place move down lands back where it started.

### `announce`

**The grip's own label is rewritten rather than a separate live region:** the control keeps focus across the move, so a screen reader re-reads it, and one element cannot drift out of step with another that does not exist.

### `onKeydown`

**The keyboard path is not a courtesy:** a pointer drag is unusable without sight and awkward with a tremor, and this is the same operation.

### `onPointerDown` / `onPointerMove` / `onPointerUp`

**Pointer Events rather than HTML5 drag-and-drop:** the latter does not fire on touch at all, so half the readers of this page could not use it.

**The row under the pointer is found by its midpoint rather than by `elementFromPoint`,** which would return the dragged row itself.

**Capture keeps the gesture with the grip when the pointer outruns it,** which it will — the row moves only once the pointer passes a neighbour's edge.

### `init`

**Delegated from the document so entries arriving later — a filter redraw, an htmx swap — need no rebinding.**

**Arrange first, so a second execution still picks up entries that arrived since the first** — it just does not bind a second set of handlers.

**Every handler below bails on an already-handled event.** The attribute stops a second *binding*; this stops a second binding that slipped past it from acting twice, because the failure is silent — one arrow key moves a row twice, and every single-test run passes. Same guard `showmore.js` uses, for the same reason.

**Bound before `[data-pin]` below because a card carries neither attribute,** but keeping the order explicit means a future card that carries both cannot toggle two pins with one click.

---

## website/static/js/showmore.js

## website/core/views.py — `_alerts_allowance` and the alerts control (2026-09-27)

The address page's alerts control keys on `alerts_entitled = allowed > 0`, which
`_alerts_allowance` answers from the widget's `rules_allowed`. Nothing here
changed when alerts opened to every authenticated reader — the table moved and the
control followed, which is the point of reading the allowance rather than naming a
tier.

What did change is what the zero branch means. It used to be "below Asastatser",
which was most readers; it is now "a tier that keeps none", which no authenticated
tier is. The branch stays because a future table could land on it and because the
`{% elif user.is_authenticated %}` upgrade link in `_swap_entry.html` is the right
rendering for it — and both suites now reach it by patching
`ALERT_RULES_PER_TIER`, since a reader can no longer be constructed who needs it.

The tier reasoning and the measurements are in the widgets logbook under
`inhouse/alerts/` and in `post-deploy/alerts-tier-analysis.md`.

## website/static/css/input.css — `.alerts-tiernote`, `.alerts-pages`

`.alerts-tiernote` is `flex: 1 0 100%` because it sits between two fields in the
form's `flex-wrap` row; without it the sentence shares a line with the subject
picker and wraps to two words a line. `.alerts-pages` joins the `.alerts-left`
rule rather than getting its own: it is the same kind of line about a second
quantity, and a second colour would imply a second meaning.

## website/static/js/ — the comment compression, and what it broke (2026-09-27)

Seven modules lost ~700 comment lines to the second pass: `address.js`,
`consolidated.js`, `dynamic.js`, `pins.js`, `showmore.js`, `theme.js`,
`toolbar.js`. The pass itself is sound — the material it removed was already filed
here by the first one, which is why this file needed no additions — but it left
four mechanical artefacts, all repaired the same day.

**172 broken parentheticals.** 105 empty ` ()` and 67 `(: x)`: whatever was inside
the parentheses was dropped and the punctuation stayed, giving lines like
`* Toggles visibility; pie charts update data ().` and
`* htmx:after:swap on document.body (: address.js, toolbar.js do same).` Every
sentence read correctly with the parenthesis simply removed, so the repair needed
no knowledge of what was lost.

**26 summaries placed after a tag.** The pass wrote its one-line summaries over the
blank separator lines inside docblocks, and where that blank sat *between* tags the
summary landed there too — so `@param {Object} item` acquired the description
"Toggles visibility; pie charts update data" and the function had none. JSDoc reads
text following a tag as part of that tag. 20 in `consolidated.js`, 6 in
`address.js`.

Three cases were deliberately left alone, and the distinction is worth keeping:
prose after `@file` **is** the file's description and is conventional; a
continuation line (`*   more text`, two spaces or more) belongs to the tag above
it; and `toolbar.js`'s paragraph after `@returns` is byte-identical to HEAD, so it
is this codebase's existing style rather than damage.

**7 docblocks opened at column zero** inside the four modules that wrap themselves
in an IIFE, with their bodies still indented three. HEAD has none, so the pass
dropped the indent on the opening line only.

**One pointer lost outright.** `pins.js` had named
`core/views.py:BaseAddressView.dispatch` as the counter-example to its own rule —
the layout preference *does* live on the server, reaching the page through the
cache key rather than a fetch. That was in neither logbook and is restored to the
module header.

### The check that found all of it

For a comment-only pass, strip every comment and blank line from both versions and
diff what is left; it must be empty.

```sh
git show HEAD:<file> | grep -vE "^\s*(//|\*|/\*)" | grep -v "^\s*$" > /tmp/a
grep -vE "^\s*(//|\*|/\*)" <file> | grep -v "^\s*$" > /tmp/b
diff /tmp/a /tmp/b
```

All seven pass it, before and after the repair — so nothing in this whole change
can have altered behaviour, which the jest suite agrees with at 1,573 passed and
100% coverage on every module. The same check is what caught a duplicated
`showLeft` listener in the widgets pass the day before; a reviewer's eye had not.

## deploy/ — the 2026-09-27 comment pass

Ten Ansible task files and Molecule plays carried their history inline: cross-repo
dependencies, the bugs that shaped a task's ordering, and why a value is what it
is. It moved here, each file keeping a one-line pointer.

The sections below were written in a `deploy/docs/logbook.md` of their own and
folded in on the same day. `deploy/` is not a separate repository — it is a
directory of this one — so a second logbook inside it would have been a second
place to look for the same kind of note, and the rule in `CLAUDE.md` names this
file. Paths are therefore from the repository root, like every other section here.

### 2026-09-27 — the pass's own artefacts, and where this logbook lives

Four things were repaired the same day, in the pass that wrote the sections above.

**Four pointers had landed inside `fail_msg` scalars** in
`deploy/molecule/shared/verify.yml`. Under `fail_msg: >-` everything indented
beneath is text, so a `#` line is part of the message an operator reads when the
assertion fails, not a comment — one of them ended
*"…copied from the address page. # See docs/logbook.md#…"*. They now sit above
their task's `- name:`, where the file's other pointers are.

**That is also how it was caught.** For a YAML pass the check is not "strip the
comments and diff": it is *parse both versions and compare the data*. Nine files
came out identical and the tenth differed in exactly those four strings. A line
diff would have shown four added comment lines and looked correct.

**Five of nine anchors did not resolve.** Three had lost a path component
(`tasks`, `host`) and two were truncated at the underscore in a filename —
`setup_site` to `setup`, `project_scripts` to `project`. A pointer that does not
resolve is worse than none, because the reader concludes the note was never
written. All ten now resolve; the check is to slug every `## ` heading here
(lowercase, keep word characters, spaces and hyphens, drop the rest) and compare
against every `docs/logbook.md#…` in `deploy/`.

**Three comments sat at column zero** inside indented task lists, which is
`yamllint`'s `comments-indentation`. With those indented and the long pointer lines
wrapped, the pass adds no lint violation of any kind: 52 `line-length` against
HEAD's 54, and the same four pre-existing `braces` warnings.

**And this logbook is the frontend's, not a second one under `deploy/`.** The pass
created `deploy/docs/logbook.md`; `deploy/` is a directory of this repository
rather than a repository of its own, `CLAUDE.md` names this file, and a second
logbook inside the same repo is a second place to look for the same kind of note.

## deploy/roles/setuphost/tasks/prepare.yml

### 2026-09-27 — Node.js/npm installation rationale

`projectsetup` runs `build-static.sh`, which minifies this project's own JavaScript through `npx --yes esbuild`. So the deploy needs npx, and npx comes from npm.

It was never installed. The live server has node because somebody put it there by hand, and the task that needs it carried `failed_when: false` until 31d1538 -- so on a host without node the build did nothing and the deploy went green on whatever static/build already held. A freshly provisioned host could not have built these assets at all, and molecule never said so.

Ubuntu's `nodejs` is old (18.x on 24.04) and that is fine: nothing here runs node itself, it only needs npx to fetch and run a pinned esbuild.

## deploy/roles/projectsetup/tasks/project_scripts.yml

### 2026-09-27 — Static build and collectstatic ordering rationale

**Block 1: Why minified assets must be built before collectstatic**

Minify our own JavaScript before collectstatic runs. static/build is placed first in STATICFILES_DIRS in production, so collectstatic prefers the minified copy over the readable source of the same name.

**That preference is why a failed build is worse than no build.** static/build is gitignored and survives between deploys, so a build that does not run leaves the PREVIOUS release's JavaScript in place and collectstatic keeps choosing it, over the source that was just pulled. The site then serves last release's scripts and nothing anywhere reports a problem.

This used to carry `failed_when: false`, which made exactly that outcome invisible: no node, or no route to the npm registry for `npx esbuild`, and the task reported ok while the deploy went green on stale code.

**Block 2: Why stale build output must be removed when no build script exists**

The honest form of "ships readable sources, which is larger but correct": that is only true once the stale build output is gone. Left in place it is not a fallback, it is the bug above.

**Block 3: Why collectstatic must precede gunicorn restart**

collectstatic must precede the gunicorn restart, not follow it: under ManifestStaticFilesStorage `{% static %}` raises for anything missing from staticfiles.json, so a worker serving pages before the manifest is written returns 500s rather than merely unstyled pages.

Deliberately no `--clear`: old hashed files should accumulate, so a reader holding a page rendered by the previous release can still fetch its assets.

This reported `changed` on every run too, and it was not its own fault: collectstatic copies whatever is newer than its target, and the build above used to rewrite all 17 minified files with fresh mtimes even when their content was identical. Fixing the build to leave unchanged files alone is what makes this task idempotent as well.

## deploy/roles/nginx/tasks/setup_site.yml

### 2026-09-27 — ACME webroot and snippets shared with backend

NOTE: the ACME webroot and the /etc/nginx/snippets (esp. ssl.conf) written below are shared: the backend's api.asastats.com site reuses them. Do not remove them even if www stops needing them.

## deploy/roles/websockets/tasks/main.yml

### 2026-09-27 — Django Channels/Daphne/Supervisor architecture

Django Channels via Daphne under Supervisor (the monorepo's approach, modernized for contemporary Ansible + ansible-lint). Daphne serves ASGI on tcp://127.0.0.1:8001; the nginx www block proxies websocket traffic to it.

## deploy/roles/websockets/handlers/main.yml

### 2026-09-27 — Supervisor restart behavior

Restarting the supervisor service rereads conf.d and (re)starts Daphne — covers both first-time adds and config changes. Supervisor manages only Daphne here.

## deploy/roles/hardening/tasks/audit/usersrestrict.yml

### 2026-09-27 — umask value for testing vs production

NOTE set to 022 for testing purposes, 027 for production. Default umask is 022.

## deploy/roles/nginx/tasks/setup_openresty.yml

### 2026-09-27 — OpenResty/Lua runtime rationale

OpenResty on top of nginx: provides the Lua runtime for the global-bundle feature. The nginx systemd service is overridden to run the OpenResty binary, so the rest of the role (and other repos) keep using the `nginx` service.

## deploy/roles/hardening/tasks/audit/tiger.yml

### 2026-09-27 — yaml-language-server schema directive

yaml-language-server: $schema=none

This directive tells the YAML language server not to validate this file against any schema, as Tiger's config format doesn't match standard Ansible schemas.

## deploy/molecule/shared/verify.yml

### 2026-09-27 — Cross-repo coupling and verification rationale

**Block 1: Cross-repo nginx coupling (lines 102-115)**

Cross-repo coupling: the api.asastats.com drop-in must be includable. The verify step checks that nginx.conf includes the sites-enabled drop-in directory so the backend's api.asastats.com server block is picked up.

**Block 2: Request timings logged (lines 129-138)**

The timed log format is defined and used so the access log carries request duration — worker contention cannot be measured from it otherwise.

**Block 3: Logged line carries timings (lines 149-165)**

The regex_search returns matched text, and ansible-core 2.19 refuses a conditional that did not evaluate to a boolean. A truthiness test would be wrong since a regex can match empty string. This asks whether it matched at all.

**Block 4: Live poll served by ASGI not gunicorn (lines 167-176)**

The live poll routes to the ASGI upstream. /widgets/liverefresh/ has no location of its own, so the poll falls through to /widgets/ and back onto gunicorn's blocking workers — 4.9% of all traffic, growing with readers rather than clicks.

**Block 5: Poll not rate limited (lines 185-194)**

The live poll's location carries no limit_req. zone=main is 4r/m and the poll runs every ~3s, so a limiter from that zone refuses it continuously — and error_page 503 would answer an htmx fragment with an HTML page. The first draft had exactly that, copied from the address page.

**Block 6: Poll reaches ASGI upstream (lines 196-203)**

The poll's location must proxy to channels-backend, not gunicorn's blocking workers.

**Block 7: Unauthenticated-API throttle (lines 205-228)**

Three things must hold: the zone exists, the limit is keyed so a credential exempts it, and it's scoped so browser's wallet and schema paths are never caught. The throttle must be scoped to address-shaped API paths only (^/api/v2/[A-Z2-7]{58}(/|$)). Applied to all of /api/, it throttles the browser's wallet login flow (/api/v2/wallet/nonce/, /verify/, /wallets/), which sends a session cookie and no Authorization header.

## deploy/molecule/shared/converge.yml

### 2026-09-27 — .env parsing quirks and dotenv handling rationale

**Block 1: Shared .env.molecule is required (lines 31-46)**

A host's real `.env.testing` / `.env.production` is legitimately absent here -- that is why the slurp above skips what is not there. But the shared defaults file is what makes provisioning possible at all, and a silent skip of THAT one surfaces 77 tasks later, as `migrate.sh` dying on a Django system check about SIMPLE_JWT_KEY being empty. Say it here, with the list of what did load, so the next reader is not diagnosing a Django error message to find a missing file.

**Block 2: dotenv parsing differences (lines 61-84)**

A dotenv file is not YAML, and two of the differences broke provisioning.

**An inline comment is not part of the value.** `website/.env.example` writes `SIMPLE_JWT_KEY=                     # ROTATED -- never reuse ...` and parsed as `key: rest-of-line` that hands Django a signing key made of comment text.

**An empty value means "not supplied", not "supplied as empty".** The example file leaves every secret blank on purpose and is loaded last, so with `combine()` taking the last definition of a key, its blanks won against `.env-example`'s real DATABASE_USER and against the values `.env.molecule` exists to provide. That is how the ci scenario came to run `psql -c "CREATE USER  WITH PASSWORD '' CREATEDB;"` So a blank fills a key nothing has defined yet, but never overrides one that is already set -- which is what makes the "first, so a real env file below overrides it" ordering above actually hold. Keys blank in every file are still defined, blank: `projectsetup`'s environment_file writes `KEY=` for them, and `get_env_variable` raises for an ABSENT key where it returns "" for an empty one.

## The marker's gate was not the poll's gate (2026-09-28)

File: `website/core/views.py`, `SwapEntryView.get_context_data`.

Reported as three separate things by a reader on a new free account, all one
defect:

1. no allowance badge,
2. the sixty-second reload stopped working too,
3. `asgi.log` filling with tracebacks — **263 of them, 9,468 of the file's 9,973
   lines, 95%**, every one a `PermissionDenied` on
   `GET /widgets/liverefresh/OGRUN…`.

### The chain

`SwapEntryView` rendered the `#id-liverefresh` marker on two conditions: the tier
allows it and the reader asked for it. `LiveRefreshView.test_func` applies a
**third** — the free band is `linked_only`, so `is_linked_to_user` must hold for
every address on the page.

`address.js:1395` stands its own sixty-second reload down whenever the marker is
present, on the grounds that "the subscriber poll owns refreshing this page". So
for a free reader on an address they had not connected:

* the marker was rendered, so the reload stood down,
* the poll was refused 403 on every tick, so nothing replaced it,
* the page had **no refresh at all**, which is worse than either mechanism alone,
* and each refusal wrote a 35-line traceback.

The reader saw a page that had quietly stopped updating and no explanation. The
allowance badge was the symptom they noticed, and it was never the problem:
`showLeft` is driven by the poll's `HX-Trigger`, so a refused poll means no badge
by construction.

### The fix

`_can_poll_liverefresh` asks the question the poll asks, and the marker is
withheld when the answer is no — so the sixty-second reload stays in place and
nothing is refused. Failing that way round is deliberate: a skew between the two
repos costs the reader real-time refresh and leaves the reload, rather than taking
both.

Imported inside the function for `_alerts_allowance`'s reason; a module-level
`from widgets...` in `core.views` took the whole site down on 2026-09-20.

**Only the free band is `linked_only`.** Intro is metered too but keyed on the
*reader* rather than the address, so it needs no connected address and its marker
is unchanged — I got that wrong first and a subtest caught it. Asastatser and up
are unmetered and unaffected.

### What this does not fix, on purpose

* **The poll still hammers a permanent refusal.** 767 requests in 85 minutes
  against a 403 that cannot change. `stop()` exists and is called for the spent
  allowance and the hidden tab; nothing handles an error status. After this change
  a free reader on an unlinked address never starts a poll at all, so the flood is
  gone — but a tier lapsing mid-session would still produce it.

  **Correction, same day: closed.** `liverefresh.js` now stands down on a 4xx —
  see "A refused poll stands down (2026-09-28)" in the widgets logbook.
* **Nothing tells the reader** that real-time refresh wants a connected address.
  The settings page says it, conditionally on the same `linked_only` flag; the
  address page says nothing. That is copy and a possible UI change.

### Two more findings from the same logs, recorded here because they are related

**The Cluster subscriber's "Internal server error" tab title** was nginx's, not
Django's: `website/templates/500.html` is titled exactly *"Internal server error"*
and `site_server_block.conf:29` maps `error_page 500 502 504` to it. So a 502 or
504 from a dead or slow upstream produces that page and leaves **no trace in any
Django log** — which is why there are zero 5xx in `asgi.log` and zero "Internal
server error" in `website_log.txt` for that day. Gone on F5 because the upstream
came back. Two candidates already measured: the three `asastats.com.socket failed`
at 08:27:36, and a 504 from the `created_apps` stalls, one of which is already
known to have killed a worker.

**`asgi.log` was a year in one unrotated file** (25/Sep/2025 → 28/Sep/2026, 8 MB)
until it was rotated on 2026-09-28. That is why month-old exceptions in it read as
current in an earlier check; dating every line before reporting it is the lesson,
and the file being 95% one reader's refusals is what rotation alone does not fix.

## Two rows that did not line up (2026-09-28)

Files: `website/templates/address.html`, `website/static/css/input.css`.

Both reported from screenshots of the deployed classic layout. They look like one
problem and are two, with nothing in common but the symptom.

### The action row: a margin the reset forgot

`input.css` already knew about this shape:

```css
#id-dustsweep-slot { display: contents; }
#id-dustsweep-slot > .dustsweep-toolbar { margin: 0; }
```

`display: contents` takes the slot span out of the box tree, so **both** widget
toolbars inside it become direct flex items of the action row. Both carry
`margin: 0 0 0.5rem` from the shared `.dustsweep-toolbar, .alerts-toolbar` rule —
and the reset named only one of them.

`items-center` centres a flex item's **margin box**, not its border box, so a
0.5rem bottom margin lifts the button 0.25rem above everything beside it. That is
the Alerts button sitting high. `placeToolbar` appends `#id-alerts` into the same
slot, so it inherited the trap the sweep's own rule was written to escape.

### The toolbar: three blocks, three different line boxes

`.totalnonft`, `.refresh` and `.switch` are plain `<div>`s holding an
`inline-flex` label. A block's line box is taller than an inline-flex label
inside it, and *how much* taller depends on what the label holds — a
`checkbox-sm` and text, or a `toggle-sm` and text, or (since the badge moved
here) a badge as well. Each label sat at the top of its own line box, the row
centred the blocks, and the labels then disagreed with each other.

Measured in the browser, midpoints:

| | before | after |
|---|---|---|
| Total without NFTs | 1379 | 1374 |
| Auto-refresh | 1379 | 1374 |
| allowance badge | **1385** | 1374 |
| ALGO/USD | **1382** | 1374 |

So it was the badge 6px low and the switch 3px low, against two labels that
agreed with each other by coincidence — both hold a `checkbox-sm`.

The wrappers are `flex items-center` now, which removes the line-box slack
entirely rather than nudging anything. `.refresh` also takes `gap-2`, because
`showLeft` inserts the badge as a sibling of the label and a flex gap is what
spaces them. The class names stay first in the attribute: `address.js` reads
`.refresh`, `.switch` and `.totalnonft` as hooks.

**The badge was mine**, added earlier the same day; the misalignment of the other
three was not, and predates it.

### A test that could not fail, again

The first version of the action-row test compared the Alerts button's centre to a
peer button's. It passed with the defect still in place, because that page renders
no other action button and there was nothing to compare against — the second time
in one day I wrote an assertion whose premise the fixture did not supply (see the
alerts picker, where containment passed for both shapes).

It now reads `getComputedStyle(...).marginBottom` and asserts `0px`: the rule
rather than the rendering. Measuring boxes needed a second element, and the slot
is `display: contents` so it has no box to measure against either. The toolbar
test *can* be geometric, because it has four elements that must agree — it
asserts their centres span at most 1px, and fails `[1371, 1371, 1377, 1374]`
without the fix.

## website/templates/snippets/asas/program.html — no `ppv-` id for an ambiguous position (2026-10-02)

Two positions on one asset that describe themselves identically share a `pid`
(`api/position_id.py`): in the reference bundle these are two Cometa stakes on
ASASTATS, two Gora.fi delegations, and three Lofty AMM amounts. The engine never
publishes those (`_asset_positions` drops them), and the dynamic layout already
renders them without an id (`pambig`). Classic still gave each one
`id="ppv-<pid>"`, so the page had duplicate ids. The values involved were
cents, so this was not the cause of the consolidated view drifting from the
total. That cause was the engine diffing against a per-process copy, plus tabs
missing payloads: see the engine and widgets logbooks, same date. The ids now
check `pid_ambiguous` as well. The `data-cat`/`data-val` that
`repaintClassicLive` sums are unchanged.

## website/core/helpers.py — `may_view_bundle`: who may open a bundle of more than 5 addresses (2026-10-03)

Reported 2026-10-03: a logged-out reader opened the 13-address bundle
`E8C829B8...` and the page even kept reloading. The free limit is 5
(`MAX_BUNDLE_SIZE`), but it was only ever applied when a bundle is *made*: a
typed bundle is cut to 5 in `addresses_from_raw`, and a saved bundle name is
capped per tier by `Profile.bundle_size_limit`. Any bundle hash already in the
cache resolved and rendered for whoever asked.

Rule, inferred from how bundles come to exist (a bundle over 5 addresses can
only be a saved bundle name): it opens for the name's owner, for anyone when a
**public** name points at it (public names are globally unique, made to be
shared), and for staff. The hash is recomputed from the resolved addresses
(`bundle_from_addresses`), so an old bookmarked hash is judged by the bundle
it names. Only bundles over 5 cost a query.

Applied where nothing else gates the data: the address page
(`BaseAddressView.dispatch`, before its cache), the export (`ExportView.dispatch`,
which the export POST passes through too), and the NFT collection fragment
(`NftCollectionItemsView`, 404). Left alone on purpose: `SwapEntryView` and
`SwapSourceRedirectView` already require login and act only on addresses linked
to the reader; widgets pass `WidgetAccessMixin`'s per-tier size bands; the API
has its own tiers. A refused page goes to the index with
`BUNDLE_NOT_VIEWABLE_ERROR`.

## website/core/sessions.py — sessions in the database as well as the cache (2026-10-03)

Reported 2026-10-03: a reader found themselves logged out after a deploy (see
`consolidated/LOGOUT-CHECK.md` in the workspace). Sessions lived only in Redis
(`django.contrib.sessions.backends.cache`). That engine treats a failed or
missed cache read as "no session", and `SessionMiddleware` then deletes the
cookie, so one Redis hiccup on one request logs the reader out for good.
Redis was ruled out as full (`noeviction`, 0 evicted, 20 MB), so the exact
moment stays unknown; the fragility does not.

Now `cached_db` (`SESSION_ENGINE = "core.sessions"` in production): reads come
from the cache, and on a miss or a failed read from `django_session`; saves go to
both. Django 5.2's `cached_db` already logs and carries on when the cache write
fails. Two overrides, each with a test that fails without it:

- `cache_key_prefix` is the cache-only engine's (`django.contrib.sessions.cache`),
  so every session that existed before the switch is still found; with
  `cached_db`'s own prefix the deploy would log everyone out once.
- `save` creates the database row when an update finds none: a session from the
  cache-only days has no row, and the plain engine raises `UpdateError`, which
  the middleware turns into a 400.

Made safe to do by the widgets' 2026-10-03 change that moved the live-refresh
per-tab state out of the session: a poll no longer saves the session, so this
is not a database write every 3 s per tab. The weekly `clearsessions` cron now
has rows to clear.

## website/utils/charts.py, static/js/{dynamic,toolbar,address}.js — chart slices keyed by asset id (2026-10-03)

Found going through the screenshot CSVs of 2026-10-03: the dynamic layout's
"Top assets" and "Assets by value" charts summed to 419,868 ALGO where the
assets (total without NFTs) were 451,973, about 32,100 short on every capture.
Unit names are not unique. On bundle `E8C829B8...` the current TINY
(2200000000, ~30,400 ALGO, mostly locked in governance) and the old Tinyman v1
TINY (378382099, 0.07 ALGO) share "TINY", and two assets share "UNIT"
(thousands of ALGO against ~4). The live redraw looked values up by lower-cased
unit (`toolbar.js` `redrawCharts`, `dynamic.js` `redrawLive`), so the small
asset overwrote the big one: the chart showed TINY at 0.08 and UNIT at 4.11.

The classic layout's `repaintClassicLive` keyed values the same way
(`readAssetValues`, `readProgramValues`), so its slices were wrong too. It never
showed in a total because classic computes a pie's title from the page total
(`totalChart`), not from its slices.

Now `_base_chart_data_from_serialized_data` and
`_distribution_chart_data_from_serialized_data` send `ids` beside `labels` (the
asset id per slice, null for "others"; collection names on the NFT chart).
`slices` carries them, `redrawLive` takes a by-id map, which `toolbar.js` builds
from the card ids (`f<asset id>`), and classic adds `readAssetValuesById` /
`readProgramValuesById` with `sliceValue` choosing by id when the payload has
ids. A payload without ids (a page cached before this) uses the unit lookup as
before.

## website/static/js/dynamic.js — the NFT floor chart read its total from the wrong element (2026-10-03)

The dynamic layout's "NFT floor value" chart showed 0.00 for every collection
and in total, while the classic page showed ~297,000 ALGO for the same bundle.
`address_dynamic.html` puts `data-totalnftfloor` on the h1, because the live
refresh replaces `.pricetip` whole every block. `whole("nftfloor")` still read
it off `.pricetip`, so it got 0, and every slice (a percentage times that
total) came out 0. It now reads `.dynamic-page [data-totalnftfloor]`, the rule
`address.js` already uses. The test helper had put the attribute on `.pricetip`,
matching the code instead of the template, so it could not catch this; it now
mounts the h1 as the template renders it.
