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

Six ``<script type="application/json">`` blocks, addressed by id:
``asachart`` · ``nftchart`` · ``ratiochart`` · ``nftfloorchart`` · ``distchart`` ·
``consolidated``

Six canvases: ``#id-distchart`` · ``#id-ratiochart`` · ``#id-ratiochartfloor`` ·
``#id-asachart`` · ``#id-nftchart`` · ``#id-nftfloorchart``

Six legend containers: ``#id-legend-<name>``.

Four visibility wrappers toggled by ``setNftFloor``: ``#id-chart-ratio`` ·
``#id-chart-ratiofloor`` · ``#id-chart-nft`` · ``#id-chart-nftfloor``

Every chart function returns early when its canvas is absent, so a layout that
omits the consolidated section is safe --- but only because each guard is
individually present. Keep them.

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

The position component
^^^^^^^^^^^^^^^^^^^^^^

``templates/snippets/asas/position.html`` renders one position. Its structure is
a contract in both directions --- the scripts read it, and the two presentations
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
| ``.position``          | **no** presentation class --- see below                            | The reader's layout may not be rendered into this cached page                      |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.position-summary``  | also carries ``asar`` and ``data-program-panel``                   | ``toggleDist`` swaps ``shadow``/``asar`` on it                                     |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+
| ``.position-breakdown``| a page-unique ``id``, matching the control's ``data-distid``       | Two ambiguous positions share a ``pid``, so the DOM id keeps the render-scoped     |
|                        |                                                                    | loop counter instead                                                               |
+------------------------+--------------------------------------------------------------------+------------------------------------------------------------------------------------+

**Source order is part of the contract**: summary first, then breakdown. Named
grid areas place them, so a screen reader and a keyboard meet the whole before
the parts. The old row put the breakdown first and pulled it back with
``order-1``/``order-2``, which bought a visual arrangement at the cost of the
reading order --- and made a second layout impossible without a second copy of
the markup.

Where the presentation lives
""""""""""""""""""""""""""""

**Not on the component.** Placement is selected by ``data-layout-position`` on
the root ``<html>`` element:

.. code-block:: css

   .position { grid-template-areas: "breakdown summary"; }          /* rows */
   [data-layout-position="cards"] .position {
     grid-template-areas: "summary" "breakdown";
   }

Rows is the default, so a ``.position`` with no ancestor attribute is still fully
laid out --- the historic widget renders this component with none of the address
page's chrome and depends on that.

This is not a style preference. **The address page's cache entry is shared
between signed-in readers**, so a modifier class written into the component would
hand the first reader's layout to everybody who followed. ``cache_page`` is a
*view* decorator, so it runs inside the middleware: ``SessionMiddleware`` appends
``Vary: Cookie`` in its ``process_response``, which happens after
``learn_cache_key`` has already recorded which headers to key the entry on. The
header is on the finished response and plays no part in the lookup --- reading it
as evidence of per-reader caching is an easy and expensive mistake.

So the preference travels off the cache, the same route the swap config takes:

``core.views.LayoutPreferenceView``
  A non-cached partial at ``/layout-preference/``, loaded by htmx on the address
  page. Takes no address --- a reader's layout does not depend on which address
  they are looking at.

``static/js/layout.js``
  Stamps ``data-layout-position`` from that partial and mirrors it into
  ``localStorage``.

``base.html``
  Re-stamps the remembered value inline **before paint**, exactly as it does for
  the theme and the typeface. Without it every visit would reflow once when the
  partial landed.

The two values are named a second time in ``utils/constants/core.py``, as each
layout's ``position`` key. Rename one and the registry hands out an attribute
value no stylesheet matches, which is silent --- the page simply stays in rows.
``test_utils_layouts_registry_position_is_a_known_modifier`` pins the registry
side and
``core/tests/test_selector_contract.py::TestPositionPresentation`` pins the
markup side; change both together.

.. warning::

   ``core/tests/test_address_layout.py`` demonstrates the shared cache entry
   directly, and includes a test that fails if the suite is ever run with
   caching disabled --- ``config.settings.development`` uses ``DummyCache``,
   under which every one of these tests passes vacuously and the page looks
   perfectly isolated. ``frontend/pytest.ini`` pins the automated-test settings
   for this reason. A probe run outside that rootdir does not get them.

   If those tests start failing, the caching changed. Check whether
   ``AddressView`` gained ``vary_on_cookie``; if so, the partial can be dropped
   and the layout rendered inline after all. Do not weaken the assertions.

Pinning a position
""""""""""""""""""

``[data-pin-position]`` sends one position to the top of its asset's list.
``[data-positions]`` marks the list it reorders within, and a single-position
asset renders no control --- pinning within a list of one changes nothing.

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

``templates/snippets/entry_controls.html`` renders the grip and the pin,
included from the asset and collection headers. ``static/js/pins.js`` reads
them: the pin sends a row to the top of its section, the grip reorders it.

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
