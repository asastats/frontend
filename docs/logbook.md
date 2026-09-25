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
