Address page DOM contract
=========================

What ``address.js``, ``site.js`` and the two test suites are entitled to find in the
rendered address page. Anything listed here is an interface, not an
implementation detail: renaming it silently breaks behaviour that no test
currently catches.

Why this exists
---------------

The address page has been bitten twice by the same shape of failure.

The jest fixture ``javascript_tests/address.html`` once sat roughly 3,000 lines
behind the template it was supposed to mirror, while every test went on passing
--- because nothing read it. And during the Materialize → DaisyUI conversion the
in-place controls (``.tdist``, ``.price``, ``.unitprice``) lost everything but
``cursor: pointer``; they still *worked*, so nothing failed, and they rendered as
plain text for the whole redesign.

Both are the same bug: the page's behaviour depends on names and structures that
are written down nowhere, so a template edit cannot be checked against them. The
multi-layout redesign moves far more markup than either of those changes did.

**Rule of thumb.** If you are about to rename a class, move an element, or wrap
something in a new container, check it here first. If it is in Tier 1 or Tier 2,
the JavaScript has to change in the same commit.

.. important::

   **Three designs, and this document covers all of them.** Each section says
   which it applies to.

   ``classic`` (design 1)
     The original page, deliberately unchanged, plus the load-more fold. It has
     no pin, no grip, no position component, and it keeps Chart.js. Its
     reference source is the pre-redesign tree at
     ``/home/ipaleka/claude/frontend-before``.

   ``dynamic`` / ``dynamic-compact`` (Dynamic / Dynamic compact,
    designs 2 and 3)
     One template with a compact flag. They carry the position component, the
     entry controls, position pinning, the program grouping and the allocation
     band, and they draw charts as **inline SVG rather than Chart.js**.

   Sections marked *designs 2/3* describe markup that does **not** appear on the
   classic page. Their tests live in
   ``core/tests/test_dynamic_design_contract.py``, which renders
   ``address_dynamic.html`` against the real payload.

   Design 2 is available from **Intro**, while design 3 is gated at
   **Asastatser**. Design 1 is ungated at every tier by construction --- its registry
   entry carries ``tier: None``, and ``normalized_layout`` falls back to it for
   both an unknown key and an unentitled one, so it is always renderable and
   always reachable.

--------------------------------------------------------------------------------

Tier 1 --- load-bearing names
-----------------------------

Renaming any of these breaks the page with no error and no failing test.

Page-level singletons
^^^^^^^^^^^^^^^^^^^^^

+--------------------+---------------------------------------------------------------+-------------------------------------------------------------------------------------+
| Selector           | Bound in                                                      | What breaks if it moves                                                             |
+====================+===============================================================+=====================================================================================+
| ``.pricetip``      | ``address.js`` ``setCurrency``, ``setTotalNoNft``,            | The header total stops converting; ``toggleUnitPrice`` throws on                    |
|                    | ``toggleUnitPrice``                                           | ``[0].dataset.price``                                                               |
+--------------------+---------------------------------------------------------------+-------------------------------------------------------------------------------------+
| ``#filter``        | ``filterChange`` (keypress)                                   | Text filtering                                                                      |
+--------------------+---------------------------------------------------------------+-------------------------------------------------------------------------------------+
| ``#scroll-to-top`` | ``scrollToTop``, ``toggleScrollToTopButton``                  | Back-to-top button                                                                  |
+--------------------+---------------------------------------------------------------+-------------------------------------------------------------------------------------+
| ``#id-cons``       | ``onConsolidatedClick`` (``toggle`` event)                    | The consolidated open/closed memory                                                 |
+--------------------+---------------------------------------------------------------+-------------------------------------------------------------------------------------+
| ``#id-cons-header``| ``test_address_templates``                                    | Per-category totals                                                                 |
+--------------------+---------------------------------------------------------------+-------------------------------------------------------------------------------------+
| ``#id-nft-preview``| ``nftShowTooltip`` / ``nftHideTooltip``                       | NFT hover preview                                                                   |
+--------------------+---------------------------------------------------------------+-------------------------------------------------------------------------------------+

``.pricetip`` is read as ``$(".pricetip")[0]`` --- **the first match wins**. If a
layout ever renders two of them, the second is inert.

Checkbox wrappers
^^^^^^^^^^^^^^^^^

Each of these must **contain** an ``input[type=checkbox]``. The wrapper is the
hook; the input is found by descent.

``.switch`` (ALGO/USD) · ``.refresh`` (auto-refresh) · ``.totalnonft`` (total without
NFTs) · ``.floor`` (NFT floor chart)

Value spans rewritten by ``setCurrency``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+--------------------+---------------------------------------------------------------+
| Selector           | Required attributes                                           |
+====================+===============================================================+
| ``span.val``       | ``data-val``                                                  |
+--------------------+---------------------------------------------------------------+
| ``span.val6``      | ``data-val``                                                  |
+--------------------+---------------------------------------------------------------+
| ``.val.pricealgo`` | ``data-val`` --- special-cased to render a rate               |
+--------------------+---------------------------------------------------------------+
| ``.val.cons-value``| ``data-val`` --- only changes tooltip position                |
+--------------------+---------------------------------------------------------------+
| ``.price``         | ``data-val``, ``data-unit``                                   |
+--------------------+---------------------------------------------------------------+
| ``.unitprice``     | ``data-val``, ``data-unit``                                   |
+--------------------+---------------------------------------------------------------+

**These elements must contain no markup of their own.** ``setCurrency``,
``togglePrice`` and ``toggleUnitPrice`` all assign ``innerHTML``, so any child element
is destroyed on the first currency switch. This has already happened once --- it
is why the screen-reader label for the total lives *outside* ``.pricetip``, and
why ``test_the_label_is_not_inside_the_element_the_script_rewrites`` exists.

Note the element type is part of the selector: ``setCurrency`` matches
``span.val``, not ``.val``. A ``<div class="val">`` is invisible to it.

In-place controls
^^^^^^^^^^^^^^^^^

+-----------------------+---------------------+------------------------------------------------------------------------------------+
| Selector              | Required attributes | Behaviour                                                                          |
+=======================+=====================+====================================================================================+
| ``.tdist``            | ``data-distid``     | Toggles ``.hidden`` on ``#<data-distid>`` and ``shadow asar`` on the nearest       |
|                       |                     | ``[data-program-panel]``                                                           |
+-----------------------+---------------------+------------------------------------------------------------------------------------+
| ``.price``,           | as above            | Flip to the reciprocal reading                                                     |
| ``.unitprice``        |                     |                                                                                    |
+-----------------------+---------------------+------------------------------------------------------------------------------------+
| ``.copy``             | ---                 | Bound in **``site.js``**, not ``address.js``: this is a site-wide contract         |
+-----------------------+---------------------+------------------------------------------------------------------------------------+

``data-distid`` values must be **unique and non-empty** across the page; there is
already a test for it.

Charts
^^^^^^

The six JSON payload blocks are **shared by all three designs**; the renderer
below them is not. Design 1 draws them with Chart.js onto canvases. Designs 2
and 3 draw them as inline SVG and load no Chart.js at all.

Six ``<script type="application/json">`` blocks, addressed by id:
``asachart`` · ``nftchart`` · ``ratiochart`` · ``nftfloorchart`` · ``distchart`` ·
``consolidated``

Six canvases: ``#id-distchart`` · ``#id-ratiochart`` · ``#id-ratiochartfloor`` ·
``#id-asachart`` · ``#id-nftchart`` · ``#id-nftfloorchart``

Six legend containers: ``#id-legend-<name>``.

Four visibility wrappers toggled by ``setNftFloor``: ``#id-chart-ratio`` ·
``#id-chart-ratiofloor`` · ``#id-chart-nft`` · ``#id-chart-nftfloor``

*The canvases, legend containers and visibility wrappers above are design 1
only.*

Every chart function returns early when its canvas is absent, so a layout that
omits the consolidated section is safe --- but only because each guard is
individually present. Keep them. It is also what lets designs 2 and 3 load
``address.js`` for the currency switch without its chart code finding anything
to draw on.

SVG charts --- designs 2 and 3
""""""""""""""""""""""""""""""

``static/js/dynamic.js`` reads the same payload blocks and builds the donuts with
``createElement``. Its contract is small:

``#charts``
  the ``<details>`` panel. Nothing is drawn until it is first opened --- six
  donuts of SVG is a great deal of markup to hand a reader who never looks --
  and it is drawn only once, since the payload does not change while the page
  is open. A panel that arrives already open (restored by the browser) is drawn
  immediately, because no ``toggle`` event is coming.

``#charts-grid``
  where the charts go. ``dynamic.js`` marks it ``data-dynamic-bound`` so a second
  execution cannot draw twice.

``#charts-note``
  carries "nothing to chart" when no payload has anything drawable.

Four things about the geometry are worth not rediscovering:

* **A full ring cannot be one arc.** SVG collapses a 360° arc to nothing, so an
  address holding exactly one thing would render a blank donut with no error.
  A single slice is drawn as two circles with ``fill-rule="evenodd"``.
* **Shares are of magnitude.** A borrowed position is negative; summing signed
  values gives a total smaller than its parts and fractions over 1, which draws
  slices lapping the ring and painting over each other.
* Labels are asset and collection names off the chain --- whatever their creator
  typed. They are set with ``textContent``, never ``innerHTML``. This is the one
  place on the page where markup could be smuggled in.
* Each ``<path>`` carries a ``<title>``, and the ``<svg>`` an ``aria-label``. A
  canvas offers a screen reader nothing, which is half the reason for the swap.

--------------------------------------------------------------------------------

Tier 2 --- structural relationships
-----------------------------------

These are not names but *arrangements*. They survive a rename and break on a
re-nesting, which makes them the easiest thing to lose in a redesign.

``.fitem`` --- the addressable entry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Every asset entry, NFT collection entry and NFT item is a ``.fitem``.
- **Each carries a unique ``id``.** The filter collects ids; ``checkOpened``
  and ``reloadPage`` reopen by id after a refresh.
- ``.fitem`` is **nestable** --- an NFT item ``.fitem`` sits inside its collection
  ``.fitem``. ``getNodesThatContain`` calls ``.parents('.fitem')`` and takes the
  first, i.e. the nearest ancestor. Adding an intermediate ``.fitem`` changes
  which entry the filter thinks it found.
- ``[open]`` is read on ``.fitem`` by ``reloadPage``, so entries must stay
  ``<details>`` (or something else that carries the attribute).

``.asasec`` / ``.nftsec`` → ``.fitem``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``checkOpened`` does ``$('.' + section + 'sec').find('.fitem')``. It is a
**descendant** walk, deliberately --- the rows sit inside a wrapper below the
section heading, so ``.children()`` would find the heading and never reach a row.
Any depth is fine; leaving the section is not.

``.section-list``
^^^^^^^^^^^^^^^^^

Shown and hidden wholesale by the filter, and expected to be an **ancestor** of
the matching ``.fitem``.

NFT thumbnail id pairing
^^^^^^^^^^^^^^^^^^^^^^^^

``showMatchedNodes`` shows a thumbnail only when its id is ``"t" + <fitem id>``.

.. note::

   An ``.nfticon`` for item ``1150857258`` must be ``id="t1150857258"``, inside the
   same ``.section-list`` as ``.fitem#1150857258``.

Break this and filtering an NFT collection shows the row with no image.

``.nfticon`` and ``img.nft``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``.nfticon`` needs ``data-path`` (full-size image for the hover preview).
- ``img.nft`` needs ``data-src``; ``deferImages`` uses
  ``getElementsByClassName('nft')``, so the bare class name matters ---
  ``nft-thumb`` would not be found.

Item headers
^^^^^^^^^^^^

``.item-header`` with a ``.token`` or ``.nft`` modifier on the same element:
``$(".token.item-header")`` → ``showExpiry``, ``$(".nft.item-header")`` → ``showTimes``.
Both walk into the entry to fill ``.epoch`` spans (``data-epoch``).

The money column
^^^^^^^^^^^^^^^^

*Designs 2 and 3 only.*

**This is the design.** One custom property, ``--col``, sets the width of a
single value cell, and four different rows use it: the asset header
(``.chead``), the program subtotal (``.pgroup-head``), the position row
(``.position-row``) and the NFT line. Every figure on the page therefore sits at
the same x, and a reader compares down the page instead of across it — which is
what lets four subtotals be *seen* to add up to the asset's figure without
anyone doing arithmetic.

A row that stops using ``--col`` has left the design behind whatever else it
keeps.

+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| Selector               | Required                                                           | Why                                                                                |
+========================+====================================================================+====================================================================================+
| ``.dynamic-page``        | wraps the whole page body                                          | Every dynamic rule in ``input.css`` is written under it, so none of them can  |
|                        |                                                                    | reach design 1 — the two pages share a base template and a stylesheet              |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.mcard``             | the asset entry; also carries ``.fitem`` and an ``f<asset id>`` id | ``.fitem`` and the id are design 1's contract, reused on purpose: ``pins.js``      |
|                        |                                                                    | finds an entry by ``closest('.fitem')`` and an arrangement is remembered against   |
|                        |                                                                    | the id, so a reader's saved order survives switching designs                       |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.chead``             | five named grid areas: ``grip tile id val pin``                    | Named areas rather than bare columns because the narrow layout rearranges them;    |
|                        |                                                                    | ``order`` on a grid would move the tab sequence with the boxes, so the value would |
|                        |                                                                    | be read before the name it belongs to                                              |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.pgroup``            | ``data-positions``, and ``.pgroup-head`` first                     | The container ``pins.js`` reorders within. The head is not a ``.position``, so it  |
|                        |                                                                    | stays put while positions move around it                                           |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.cval`` / ``.amt``   | ``data-val`` carrying the unvarnished figure                       | The visible text is rounded. ``setCurrency`` recomputes from the attribute, and    |
|                        |                                                                    | reading the text back would compound the rounding on every switch                  |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+

Two breakpoints, both measured rather than guessed. At **860px** ``--col``
narrows to ``7rem``: the name still has room, but 8.5rem of value beside it
starts pushing longer asset names into ellipsis. At **620px** ``--col`` becomes
``auto`` and the header drops to two rows with the value beneath the name —
below that width the fixed cells alone (grip, tile, money column, pin, four
gaps) leave the name under 90px, which is what made "STASIS EURO" break one word
per line. The grip and the pin leave the flow there; a fixed money column is
precisely what there is no longer room for, because there is one figure per row
to read rather than a column of them to compare.

The compact form — design 3
"""""""""""""""""""""""""""

``.rows.cards`` on the list, and nothing else. That single class is the entire
difference between designs 2 and 3: the asset rows become a tile grid, the
five-cell header collapses to a stack, and an opened tile takes the full width
and gets its columns back. Everything inside an opened tile — the money column,
the program groups, the position rows, the breakdown — is *literally the same
rules*. Two copies would drift, and the first sign of it would be a reader
reporting a figure on one design that is missing from the other.

The allocation band
^^^^^^^^^^^^^^^^^^^

*Designs 2 and 3 only.*

"Where the money is": a stacked bar, five category figures, and the charts
panel. All three are drawn from **one** call to
``core_extras.allocation_bands``, so they cannot disagree — a reader who sees
the bar and the figures tell different stories has no way to know which lied.

``.allocation-bar``
  the stacked bar. Segment widths are each category's share **of the five
  categories' own sum**, not of the portfolio total, so the segments reach the
  full width; a rounding gap at the right-hand end reads as money gone missing.

``.fig`` + ``.cat-<key>``
  one figure per category. The five keys are ``balance``, ``staked``,
  ``liquidity``, ``defi``, ``nft``.

.. important::

   **The five category colours do not follow the theme.** All 57 themes recolour
   the chrome around this band, but balance-is-green and NFT-is-red must mean
   the same thing in every one of them, or the bar, the figures and the donut
   stop reading as the same fact. They are defined as ``--c-*`` on
   ``.dynamic-page`` with a light/dark pair, not a per-theme value.

.. note::

   The segments and figures are **static elements, not buttons**, until the
   toolbar lands. In the prototype each is a control that filters the whole
   page, and that is what they will become — but a button that does nothing when
   pressed is worse than a figure that never claimed it would. ``data-band`` is
   already on them to bind to.

Two filters feed all of this. Both are presentation rather than view context:
design 1 renders the same payload ungrouped, and the serialized payload is
shared with the JSON API, which must not grow a website-shaped key.

``core_extras.program_groups``
  groups an asset's positions and subtotals them. **By program, not by venue**:
  ``program.name`` is a venue for most position types ("AlgoRai deposit",
  "CompX token stream") but the category ``Liquidity`` for LP positions, whose
  venue lives in ``program.code``. The reference address puts 18 LP positions
  across five venues under one heading.

``core_extras.allocation_bands``
  the five categories. Note the asymmetry it has to absorb: ``consolidated`` is
  a ``utils.structs.Consolidated`` **namedtuple** while ``total`` is
  ``account.total``, a plain **dict**. Reading both with ``getattr`` silently
  returns zero for the dict — which drew NFT at 0.00 on an address holding 79%
  of its value in them, with the other four shown summing to a tidy 100%.
  ``Consolidated``'s last field is also the NFT *floor*, not the holding.

The position component
^^^^^^^^^^^^^^^^^^^^^^

*Designs 2 and 3 only — the classic page uses ``snippets/asas/program.html``.*

``templates/snippets/dynamic/position.html`` renders one position. Its structure
is a contract in both directions --- the scripts read it, and both designs
depend on it.

+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| Selector               | Required                                                           | Why                                                                                |
+========================+====================================================================+====================================================================================+
| ``.position``          | ``data-pid``                                                       | The position's stable identity, from ``api/position_id.py``. Pinning, deep links   |
|                        |                                                                    | and the saved layout key on it                                                     |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.position``          | ``data-pid-ambiguous`` when, and only when, the id names more than | Lets the page say "cannot promise" instead of pinning one and hoping. Six rows in  |
|                        | one position                                                       | the reference bundle                                                               |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.position``          | wraps the row **and** its breakdown                                | Pinning reorders positions; a breakdown left behind by its row would sit under a   |
|                        |                                                                    | different position entirely                                                        |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.position-row``      | the three-cell grid: identity, money column, pin                   | The middle cell is ``--col`` wide, the same width every other figure on the page   |
|                        |                                                                    | uses                                                                               |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.dist``              | a page-unique ``id``, matching the control's ``data-distid``       | Two ambiguous positions share a ``pid``, so the DOM id keeps the render-scoped     |
|                        |                                                                    | loop counter instead                                                               |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+

**Source order is part of the contract**: the row first, then its breakdown.
A screen reader and a keyboard meet the whole before the parts. Design 1's old
row put the breakdown first and pulled it back with ``order-1``/``order-2``,
which bought a visual arrangement at the cost of the reading order.

Where the presentation lives
""""""""""""""""""""""""""""

**On the server, in the template it picks.** Each layout in
``utils/constants/core.py`` names a ``template`` and a ``compact`` flag;
``BaseAddressView.get_template_names`` returns the first and the context carries
the second. Designs 2 and 3 name the *same* template and differ only in
``compact``, which adds one class:

.. code-block:: html

   <div class="rows{% if compact %} cards{% endif %}" data-folding>

.. code-block:: css

   .dynamic-page .rows { display: flex; flex-direction: column; }
   .dynamic-page .rows.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(158px, 1fr)); }

That is the whole difference between design 2 and design 3. Two template files
would duplicate every asset row, program group and chart in order to change a
handful of grid rules, and the first sign of the two drifting would be a reader
reporting a figure on one that is missing from the other.

How the layout survives a shared cache
""""""""""""""""""""""""""""""""""""""

**The address page's cache entry is shared between readers.** ``cache_page`` is a
*view* decorator, so it runs inside the middleware: ``SessionMiddleware`` appends
``Vary: Cookie`` in its ``process_response``, which happens after
``learn_cache_key`` has already recorded which headers to key the entry on. The
header is on the finished response and plays no part in the lookup --- reading it
as evidence of per-reader caching is an easy and expensive mistake.

The layout escapes that by being folded into the **cache key prefix**:

.. code-block:: python

   self.layout = layout_for_user(getattr(request, "user", None))
   cached = cache_page(self.cache_timeout, key_prefix=f"layout-{self.layout}")(
       super().dispatch
   )

One entry per ``(address, layout)``; readers on the same layout still share one.
``vary_on_cookie`` was the obvious alternative and is the wrong one --- it keys on
the whole cookie, so every session gets its own entry and the sharing is lost.

The prefix is built from the **normalized** layout, which is what stops a paid
design reaching an unentitled reader: ``layout_for_user`` re-checks the tier, so
a lapsed subscriber resolves to ``classic`` before a key exists. There is no
path by which design 2's bytes are served to someone who may not have it.

.. important::

   The layout and its ``compact`` flag are the **only** reader-derived values the
   address context may carry, because they are the only ones the key accounts
   for. Everything else about a reader --- their linked addresses, their router,
   their tier --- would be handed to whoever asked next. That is why
   ``core.views.SwapEntryView`` is a separate non-cached partial, and why pins
   and the saved order live in ``localStorage`` and never reach the server.

.. note::

   This replaces an earlier design in which the layout arrived from a non-cached
   ``/layout-preference/`` partial, was stamped onto ``<html>`` as
   ``data-layout-position``, and was re-stamped before paint from
   ``localStorage``. That existed only because the markup was assumed to be
   unable to vary per reader. Keying the cache is the real answer, and it
   removed ``LayoutPreferenceView``, its URL, ``_layout_preference.html``,
   ``static/js/layout.js`` and the pre-paint stamp in ``base.html``.

.. warning::

   ``core/tests/test_address_layout.py`` demonstrates the shared cache entry
   directly, and includes a test that fails if the suite is ever run with
   caching disabled --- ``config.settings.development`` uses ``DummyCache``,
   under which every one of these tests passes vacuously and the page looks
   perfectly isolated. ``frontend/pytest.ini`` pins the automated-test settings
   for this reason. A probe run outside that rootdir does not get them.

   If those tests start failing, the caching changed. That is news rather than a
   regression: check whether the view gained ``vary_on_cookie`` or moved to
   middleware-level caching, and if so more per-reader state can be rendered
   inline after all. Do not weaken the assertions to make them pass.

Pinning a position
""""""""""""""""""

*Designs 2 and 3 only.*

``[data-pin-position]`` pins one position. Two things happen: it floats to the
top of its program group --- ``[data-positions]`` marks the list it reorders within
--- and a **copy** of it appears in the pinned band at the top of the page.

The band holds copies, not the rows. Moving a position out of its asset would
take it away from the money column it aligns to and the group subtotal it
contributes to, which are the two things that make its figure readable at all.

Every position carries a control, including the only position in its group. That
reversed an earlier rule: when pinning meant nothing but floating within a
group, a group of one had no order to change and the control could not act. The
band changes what pinning means --- for a lone position buried in an asset the
reader must scroll to and open, it is the case the band is *most* useful for.

.. note::

   Positions are grouped by **program**, not by venue, and the difference is
   worth knowing before reading a subtotal. ``program.name`` is a venue for most
   position types --- "AlgoRai deposit", "CompX token stream", "Wallet balance"
   --- but for liquidity positions it is the category ``Liquidity``, with the
   venue inside ``program.code`` ("Pact LP ALGO-EURS"). The reference address
   therefore shows 18 LP positions across five venues under one heading.
   Recovering the venue would mean splitting a string the engine never promised
   the shape of. See ``core.templatetags.core_extras.program_groups``.

A pin whose position is not on the page any more keeps its card, marked
``.stale``. Dropping it silently would tell the reader nothing about why the
thing they pinned vanished, and it may only be inside a folded tail. The stored
pin carries a ``label`` for exactly this: a stale card reading ``p1-3935...``
names nothing a reader can act on.

The hard part is saying *which* position. Three pids in the reference bundle name
two rows each: two Lofty AMM entries, two Cometa stakes, two Gora.fi delegations.
Every identifying field the payload carries is identical for both, and the only
things that differ --- the value and the amount --- are the two things that change
between loads. Those rows carry ``data-pid-ambiguous``.

``data-amount`` is the tiebreaker, and **it is deliberately not part of the
pid**:

* Hashing it into the id would change the id whenever the amount changed, which
  is the one property the id exists to have. That would destabilise all 190
  positions to fix 6.
* Amount rather than value, because value moves with the price on every load
  while amount moves only when the reader actually stakes or unstakes. The
  witness is stable in exactly the situation the pin has to survive.

Restoration is: one pid match, use it; several, take the nearest amount, with an
exact match winning outright. An ordinal was rejected --- unique but *unstable*,
so a pin follows the rank rather than the position and silently lands on the
other row.

.. note::

   This can still choose wrongly, but only if two positions of one program cross
   in magnitude between visits --- far narrower than the ordinal, which breaks on
   *any* reordering, and the cost is a row appearing at the top of a list. The
   row says so: a pinned ambiguous position takes a warning-coloured stripe
   rather than the primary one.

   ``test_the_witness_is_not_part_of_the_identity`` asserts the ambiguous pairs
   really do differ in amount --- and fails if the sample ever stops containing
   an ambiguous pair, so the fallback cannot quietly become untested.

**What may never become a handle**: the value, the amount, the distribution, or
the row's place in the list. All four change between two loads of the same
page. That is why ``pid`` exists, and the same rule applies to any attribute the
markup might be tempted to key on.

Entry controls
^^^^^^^^^^^^^^

*Designs 2 and 3 only — the classic page offers neither pin nor grip.*

The asset header renders the grip and the pin as **direct children** of
``.chead``, because each is a named grid area and a wrapper element would
collapse both into one cell. ``static/js/pins.js`` reads them: the pin sends a
row to the top of its section, the grip reorders it.

There was a shared ``entry_controls.html`` snippet wrapping them in
``.entry-controls``. It was written when the controls were going into design 1,
and nothing included it once design 1 was restored to the untouched old page, so
it and its stylesheet rules are gone.

+--------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| Selector                 | Required                                                           | Why                                                                                |
+==========================+====================================================================+====================================================================================+
| ``[data-pin]``           | the id of the ``.fitem`` it sits inside                            | The id is what survives a reload. An index or a row number does not --- the same   |
|                          |                                                                    | reasoning that produced ``pid`` for positions                                      |
+--------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``[data-pin]``           | ``aria-pressed="false"`` **as rendered**                           | The page is cached and shared; a pressed control here would be pressed for whoever |
|                          |                                                                    | asked next. The script presses the reader's own                                    |
+--------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``[data-pin]``           | an ``aria-label``                                                  | The control's only content is an inline SVG                                        |
+--------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.fitem.pinned``        | applied client-side only                                           | Same reason as ``aria-pressed``                                                    |
+--------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+

**Only top-level entries carry a control.** An NFT item is itself a ``.fitem``
nested inside its collection's ``.fitem``, and ``pins.js`` derives the container
it reorders from the control's own entry --- so a control rendered on a nested
entry would reorder a collection's items instead of the collections.
``test_nested_entries_have_no_control`` is what keeps that true.

**Entries are moved in the DOM, not reordered with CSS ``order``.** ``order``
would avoid a reflow, but it moves a row visually while leaving it where it was
for a screen reader and for keyboard navigation --- the exact fault the position
component was rebuilt to remove, and it would be no more acceptable here. The
served order is captured once before anything moves and every arrangement is
rebuilt from it, so unpinning returns a row to where it belongs rather than to
wherever it ended up.

The grip carries ``data-drag`` with the same id, and offers three ways to move a
row: a pointer drag (Pointer Events, **not** HTML5 drag-and-drop, which does not
fire on touch at all), the arrow keys, and Home/End. The keyboard path is not a
courtesy --- a drag is unusable without sight and awkward with a tremor, and this
is the same operation. After a move the grip's own ``aria-label`` gains "Now 2 of
7"; rewriting the label the reader's focus is already on beats a live region that
can drift out of step with it.

A drag stays inside its own group: a pinned row reorders among pinned rows, an
unpinned row among unpinned. Crossing would mean either silently pinning a row or
recording an order the next render undoes.

Arrangement is stored in ``localStorage`` under ``pins:<path>`` and
``order:<path>``, and never sent to the server. The path is the address or
bundle hash, so every page namespaces itself and the historic widget's copy of
this page stays separate for free.

.. warning::

   **The served order is captured on the container element, and the handlers
   bind once per document.** Both guard against this script running twice --- it
   is a plain ``<script>`` today, but the page already pulls one in through an
   htmx partial, and a second execution with module-scoped state binds a second
   set of delegated handlers. The symptom is silent: one arrow key moves a row
   two places, and every single-test run passes.

Folded rows
^^^^^^^^^^^

*All three designs.* The fold is the one thing from this work that the classic
page kept, because it is a fix rather than a redesign: it stops the page leading
with seventy-six rows.

A section shows the rows accounting for the first
``settings.ADDRESS_SECTION_THRESHOLD`` of its magnitude and folds the rest behind
a control. ``utils/cutoff.py`` is the rule; ``static/js/showmore.js`` reveals
them.

+--------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| Selector                 | Required                                                           | Why                                                                                |
+==========================+====================================================================+====================================================================================+
| ``[data-folding]``       | on the container of a section's rows                               | The class is toggled here, not on sixty rows individually                          |
+--------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.fitem.folded``        | on every row past the cutoff                                       | Hidden by CSS, still in the document --- the filter has to be able to find it      |
+--------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``[data-show-more]``     | ``aria-expanded="false"`` as rendered                              | The reader expands it; the stylesheet reads the attribute for the rows *and* for   |
|                          |                                                                    | the button's own label, so the two cannot disagree                                 |
+--------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.show-more-open`` /    | both rendered inside the control                                   | Keeping the text out of the script is what stops the label and the attribute       |
| ``.show-more-close``     |                                                                    | drifting apart                                                                     |
+--------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+

**Every row is rendered, and the tail is marked rather than withheld.** The
payload is in hand before the page renders, so a request to reveal dust would
cost more than the markup does, and the reader gets an instant answer instead of
a spinner. ``display: none`` rather than a height or an opacity, so a folded row
is out of the accessibility tree and out of tab order --- a reader hearing sixty
rows they cannot see is worse served than one who presses a button.

**Magnitude, not value.** A borrow is negative by rule, so a signed running total
sails past the threshold and back, hiding material rows on the way. An early
version of this reported "the last -68.8% of value".

.. note::

   Anything measuring geometry must unfold first. A hidden row has no box, so a
   layout assertion reads zero and compares it against zero --- which passes as
   often as it fails. ``AssetRowLayoutTest._render`` clicks every control and
   then waits for ``document.images`` to settle, because ``deferImages`` assigns
   each ``src`` after load and every thumbnail that lands pushes the rows below
   it down.

``[data-program-panel]``
^^^^^^^^^^^^^^^^^^^^^^^^

The nearest ancestor of a ``.tdist``. Chosen over ``.parent()`` on purpose: which
element the value span sits directly inside is a layout decision, and
``.closest(".asar")`` would break on the second click because ``asar`` is half of
what gets toggled.

The NFT section
"""""""""""""""

*Designs 2 and 3 only.* ``snippets/dynamic/nfts.html``, ``collection.html`` and
``nft.html``.

This section was design 1's markup included unchanged until pass 3, and the
reason it had to be rebuilt is a measurement rather than a preference: design
1's collection rows put the value wherever the text leaves room, so **the money
column stopped at the assets**. Half a page aligned to a column and half not is
not a page with a money column.

So a collection is an asset card: the same ``.fitem.mcard``, the same five-cell
``.chead``, the same ``--col``. An NFT's facts are ``.nft-line`` rows, which are
the same three tracks a position row uses. The page now has five levels that put
a figure on one edge, and
``functional_tests/test_address_dynamic_nfts.py`` measures all five together:

.. code-block:: text

   asset header       #asset-list > .fitem .chead > .cval
   venue subtotal     #asset-list .pgroup-total
   position row       #asset-list .position-row > .position-val
   collection header  #nft-list > .fitem .chead > .cval
   NFT line           #nft-list .nft-line .position-val

.. warning::

   ``.nft-line`` declares **three** grid tracks and leaves the third empty. Every
   other row on the page reserves 26px on the right for a pin; a two-track row
   puts its figure 38px further right -- the reserved cell plus the gap -- and
   the column breaks at exactly the section the rebuild was bringing into it.
   That is what the first build of this section did.

Hooks kept from design 1, because the scripts are shared: ``.nftsec``,
``.section-list``, ``.nfticon`` with ``data-path``, ``.epoch`` with
``data-epoch``, ``class="nft"`` with ``data-src``.

``.epoch`` is the one where keeping the hook was not enough. ``showTimes`` binds
to ``.nft.item-header`` and fills ``span.epoch`` inside ``.item-body`` siblings,
and this design has neither -- so the section rendered "Last purchase on Rand
Gallery" with no indication of when. ``dynamic.js`` fills them now, on load rather
than on open, using ``address.js``'s ``timeEntry`` so both designs word the same
fact the same way.

Two comparisons are filters rather than template expressions, and both were
wrong as expressions. The payload's prices are decimal *strings*, so
``{% if a > b %}`` compares them character by character: ``"215.98" < "25.00"``,
which would have reported an item worth eight times its floor as not clearing
it. ``clears_floor`` and ``beats_last_purchase`` do the arithmetic instead.
Design 1 makes the ``max_purchase`` comparison in the template and still gets it
wrong sometimes; that is a deliberate divergence, because design 1 is finished
and is not to be edited.

The floor bar (``.mix``) is the one fact about a collection that a single figure
cannot express: the estimate is what the section totals, the floor is what a
marketplace will pay today, and the gap is the risk. Its two halves are flex
children rather than widths, so the pair always fills the track -- what is being
shown is a ratio, and a bar that stopped short would read as a third quantity.

The toolbar
"""""""""""

*Designs 2 and 3 only.* Pass 2, ``snippets/dynamic/toolbar.html`` and
``static/js/toolbar.js``.

Everything the toolbar does happens in the browser, on a page that is already
in the reader's hands. That is not an optimisation: this page's cache entry is
shared by every reader on the layout, so the server cannot know what one reader
has filtered to and must not render it. The state lives under ``view:<path>`` in
their own browser, beside the pins and the saved order, and **every control
ships in its default state** for the same reason --- a control rendered pressed
because *somebody* pressed it would be handed to whoever asked next.

Load-bearing names:

``#toolbar``
   The bound container. ``toolbar.js`` binds its click handler here and on
   ``.band``, not on ``document``, because these controls sit on elements the
   server renders once.

``data-initial`` on ``.asasec`` / ``.nftsec``
   How many rows the section shows, and how many each press of "Show more"
   adds. From ``ADDRESS_INITIAL_ASSETS`` and ``ADDRESS_INITIAL_COLLECTIONS``,
   published so the fold the template renders and every fold ``toolbar.js``
   renders afterwards are one rule rather than two copies.

   These designs do **not** use ``utils/cutoff.py``'s magnitude rule; design 1
   still does. They briefly carried the prototype's 95%/99%/99.5%/All control,
   which was only ever a way to demonstrate the page with everything on screen
   before a load-more existed. "Show me the rows carrying 99.5% of the value"
   is not a sentence a reader thinks in.

   ``showmore.js`` stands down on ``.dynamic-page`` for the same reason: it
   reveals a whole tail in one press, and these reveal a batch.

``data-sort-value`` / ``-amount`` / ``-name`` / ``-positions`` on ``.fitem``
   The sort keys. Rendered rather than read out of the row, because the visible
   figure is rounded and grouped, and Django's thousands separator is
   locale-dependent --- a sort parsing it would silently tie rows that differ.

``data-search`` on ``.fitem`` and ``.position``
   The haystack. Deliberately not the element's ``textContent``, which on a
   closed card includes the asset id, the decimals, the total supply and every
   provider link, so typing "6" would match most of the page.

``data-cat`` on ``.position``
   The allocation category, from ``position_band``. This is what makes the band
   a control rather than a picture. The filter reproduces a rule that lives in
   four dict comprehensions in ``utils.charts``; ``test_dynamic_extras.py`` sums
   the reference payload both ways and asserts the totals agree, which is the
   only reason the duplication is safe to keep.

``data-owner`` on ``.position``
   The asset the row belongs to. On the row itself rather than inferred from its
   ancestors, because "Group by venue" moves the whole ``.pgroup`` out of its
   asset --- for as long as that is on, a position's ancestors say nothing about
   which asset it is a holding of.

``#asset-list`` / ``#venue-list``
   The two lists. Grouping by venue **moves** each ``.pgroup`` into the venue
   that holds it and moves it back afterwards. Moving, never copying: a copy
   would put a second element on the page with the same ``data-pid``, and a pin
   names a position by that id.

Three rules the toolbar is built around, each of which was arrived at the hard
way:

**No filter moves the headline** -- but the currency does. A reader who hides a
category has not become poorer, so no filter, search or category toggle may
touch ``.total``. A *currency* is not a filter: it is the unit the whole page is
denominated in, and a page whose every figure says USD above a total saying ALGO
is not showing a total at all. "Total without NFTs" moves it too, legitimately,
because it changes what is being totalled rather than how it is shown.

Getting that distinction wrong is what left the money column's headline written
by ``address.js`` on load and by nobody afterwards -- so a reader who had ever
chosen USD anywhere met a USD total above ALGO figures.

**Currency, auto-refresh and "without NFTs" are the reader's, not the
address's.** They live in design 1's own top-level keys (``cur``,
``refresh``, ``totalnonft``), so both designs and every open tab agree about
them; only what is filtered, sorted and grouped is stored per address under
``view:<path>``. "Reset view" restores the view and leaves those alone.

**The band's readout says what the visible categories come to.** The headline
holding still is right and leaves a reader who switched DeFi off with no way to
see what the rest adds up to. ``#band-readout`` is that number, and it appears
only when it differs from the headline.

**A switched-off category keeps its figure and its width.** Zeroing it would
say "you hold none" when what happened is "you hid it" --- and a bar segment
shrunk to nothing has no box left to press, so the control would disable
itself. It dims instead.

**Sorting does not reorder the DOM.** Sorting and pinning both decide what
order the rows are in, so if both wrote to the DOM whichever ran last would
undo the other. The toolbar hands ``pins.rebase`` a new baseline and pinning
still wins on top of it, which is right: a pin is the reader saying "this one,
whatever else is going on".

.. warning::

   ``snippets/show_more.html`` must stay the **immediately following sibling**
   of the list it unfolds. ``showmore.js`` finds its container by looking at the
   control wrapper's previous sibling. ``#venue-list`` was originally inserted
   between the two, which pointed the control at the empty venue container ---
   so "Show 38 more assets" revealed nothing and every measurement of a folded
   row read zero. It degrades to the right answer through a fallback; a fallback
   is not where this belongs.

.. note::

   ``address.js`` does not touch ``.dynamic-page``. Its ``setCurrency`` writes
   ``innerHTML`` --- number *and* unit --- into every ``span.val``, which is
   right for design 1, where the unit is part of the value's text. Here each
   figure pairs with a separate unit element, so it left asset headers reading
   "253.74 ALGO ALGO" and destroyed the nested ``<span class="unit">`` in every
   venue subtotal, on every load. Its ``.tdist`` binding is excluded for the
   same class of reason: that design hides its breakdown with the ``hidden``
   *attribute* and this one toggles the ``hidden`` *class*.

--------------------------------------------------------------------------------

Tier 3 --- free to change
-------------------------

Everything not listed above: all Tailwind utilities, ``.itemrow`` / ``.itemleft`` /
``.itemmid`` / ``.itemright``, ``.asal`` / ``.asar`` positioning classes (except
``asar`` as the ``.tdist`` toggle target), ``.icondiv``, spacing, ordering, wrappers.

Some of these appear in ``functional_tests/test_address_page.py`` as convenient
handles rather than as contracts --- update the test with the markup.

--------------------------------------------------------------------------------

Known-fragile --- fix rather than preserve
------------------------------------------

Do **not** carry these into the new layouts.

``chartClick`` hard-codes the header's depth
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: javascript

   var unit = $(".unit").filter(function () { return ($(this).text() === label) });
   var header = unit.parent().parent();
   if (!header.parent().hasClass("active"))

Two problems. ``unit.parent().parent()`` assumes ``.unit`` sits exactly two levels
below the clickable header. And **``active`` is a Materialize leftover** --- no
address-page template emits it, so the condition is always true and the handler
clicks a header that may already be open, closing it. Clicking a chart slice for
an already-open asset collapses it.

Replace with an explicit hook (``[data-unit]`` on the entry, or resolve the id
from the chart payload) and read ``details.open`` instead of ``.active``.

``setNftFloor`` waits 300 ms for an animation that no longer exists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It toggles ``scale-in``, ``scale-out`` and ``valign-wrapper``, then does the real work
inside a 300 ms ``setTimeout``. **None of those three classes has any CSS in the
current build** --- the swap works only because the same function also sets inline
``display``. So the delay is dead time, and the vertical centering
``valign-wrapper`` used to provide is simply gone.

The jest test asserts the class names rather than the effect, which is why it
passes.

``showMatchedNodes`` uses jQuery ``.show()`` / ``.hide()``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These write inline ``display``, which outranks every Tailwind utility and cannot
be undone by class changes. A layout that switches an entry between ``grid`` and
``block`` will fight it. Prefer toggling a ``hidden`` class.

--------------------------------------------------------------------------------

How this is enforced
--------------------

``core/tests/test_selector_contract.py`` renders ``address.html`` against the real
sample payload and asserts every Tier 1 name and Tier 2 relationship above.
``core/tests/test_dynamic_design_contract.py`` does the same for
``address_dynamic.html`` and the designs 2/3 sections.

It is deliberately **not** a snapshot test. A snapshot fails on every whitespace
change and gets regenerated without being read, which is how the jest fixture
drifted 3,000 lines in the first place. Each assertion here names one behaviour
and explains what breaks without it.

When a redesign genuinely needs to move something in Tier 1 or Tier 2: change
the contract, change the test, change the JavaScript, in one commit.

**And regenerate the jest fixture.** ``javascript_tests/address.html`` is a
captured render, so any markup change leaves it describing a page the site no
longer serves --- the original 3,000-line drift, exactly:

.. code-block:: bash

   python scripts/capture_address_fixture.py

The jest suite passing against a stale fixture is not evidence of anything.

Class names must not collide with DaisyUI
-----------------------------------------

*Designs 2 and 3.* The prototype these designs come from is standalone raw CSS
and names things freely. DaisyUI ships components called ``card``, ``stack``,
``list``, ``status``, ``label``, ``link``, ``badge``, ``swap``, ``tab``,
``toggle`` and ``divider``, among others. Port that markup unchanged and the
framework's rules apply to your elements, with no error of any kind.

Both ``.card`` and ``.stack`` came over and had to be renamed --- to ``.mcard``
and ``.allocation-bar``. ``.stack`` is the instructive one: DaisyUI sets
``display: grid`` with **every child in the same grid area**, so the
five-segment allocation bar would have rendered as one segment covering the
other four. The page would simply have shown the wrong thing, and looked
deliberate doing it.

``core/tests/test_dynamic_design_classes.py`` now checks this automatically: every
class used in the four money-design templates must be either declared in
``static/css/input.css`` or named in an explicit allowlist of framework classes
we chose to inherit. It catches collisions **and** classes that style nothing,
in the same assertion --- on its first run it found ``btn-accent`` (the
prototype's name; DaisyUI's is ``btn-primary``) and a never-declared
``addr-list``.

``.card`` and ``.stack`` also get their own named test, because the general
check passes the moment somebody "fixes" a collision by declaring ``.card`` in
``input.css`` --- which starts a specificity fight whose winner depends on
source order.

To check a name by hand:

.. code-block:: bash

   grep -o "\.NAME[ ,{:>~+)]" static/css/style.tw.css   # framework + ours
   grep -o "\.NAME[ ,{:>~+]"  static/css/input.css      # ours alone

A hit in the first and not the second is a framework class.
