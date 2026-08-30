"""Every class the dynamic designs use is one we meant to use.

The failure this exists to stop is silent. DaisyUI ships a ``.card`` and a
``.stack``; the prototype these designs come from also calls things ``card`` and
``stack``, in raw CSS with no framework underneath. Bring that markup over
unchanged and the framework's rules apply to it -- ``.stack`` sets
``display: grid`` and piles every child into the same grid area, so the
five-segment allocation bar renders as one segment covering the other four.
Nothing errors. The page just quietly shows the wrong thing.

Both were caught by hand on 2026-08-21. This module is here so the next one is
not, because "check the class names against DaisyUI" is not a step anybody
remembers on the day they add a row.

The rule: a class in a money-design template is either **ours** -- declared in
``static/css/input.css`` -- or an **intentional framework class**, named in
:data:`FRAMEWORK`. Anything else is either a collision or a class that styles
nothing at all, and both are worth a failing test.
"""

import re
from pathlib import Path

import pytest

TEMPLATES = Path(__file__).parent.parent.parent / "templates"
INPUT_CSS = Path(__file__).parent.parent.parent / "static/css/input.css"

#: The dynamic designs' own templates. Design 1's are deliberately absent:
#: it is the untouched old page and its classes predate all of this.
MONEY_TEMPLATES = (
    TEMPLATES / "address_dynamic.html",
    TEMPLATES / "snippets/dynamic/asset.html",
    TEMPLATES / "snippets/dynamic/position.html",
    TEMPLATES / "snippets/dynamic/band.html",
    TEMPLATES / "snippets/dynamic/toolbar.html",
    TEMPLATES / "snippets/dynamic/nfts.html",
    TEMPLATES / "snippets/dynamic/collection.html",
    TEMPLATES / "snippets/dynamic/nft.html",
)

#: Framework classes these templates use on purpose -- Tailwind utilities and
#: DaisyUI components that do exactly what the design wants, so reimplementing
#: them would be worse than using them. Adding a name here is a decision to
#: inherit the framework's rules for it; that is the point of listing it.
FRAMEWORK = frozenset(
    {
        # DaisyUI components, used as themselves.
        "btn",
        "btn-circle",
        "btn-primary",
        # Tailwind utilities.
        "sr-only",
        "cursor-default",
        "fixed",
        "bottom-6",
        "right-6",
        "z-20",
        "h-5",
        "w-5",
        "opacity-0",
        "transition-opacity",
        "[&.visible]:opacity-100",
    }
)

#: Classes shared with design 1 on purpose. These are contracts, not styling:
#: `pins.js` finds an entry by `.fitem`, `showmore.js` folds `.fitem.folded`,
#: `address.js` recomputes `.val`/`.unit` when the currency switches, and
#: `.asasec` is the container it reopens a remembered entry inside. Reusing them
#: is what lets one reader's arrangement survive a change of design.
SHARED_WITH_DESIGN_ONE = frozenset(
    {
        "fitem",
        "folded",
        "asasec",
        "val",
        "unit",
        "pricetip",
        "asaicon",
        "show-more",
        "show-more-open",
        "show-more-close",
        "tdist",
        "out",
        "num",
        # The NFT section's own hooks, kept when it was rebuilt in the money
        # column. `.nftsec` is what `address.js` reopens a remembered collection
        # inside and what `toolbar.js` hides when the NFT band is switched off;
        # `.section-list` is what design 1's filter shows and hides; `.epoch` is
        # filled with "N ago" by `showTimes` when a collection opens, which is
        # why the element is rendered empty.
        "nftsec",
        "section-list",
        "epoch",
        # `site.js` binds the clipboard control to `.copy` and copies the
        # element immediately before it.
        "copy",
        # The Swap entry, which the money designs did not have at all: design 1
        # carries it in `snippets/asas.html`, and that file is included only by
        # `address.html`.
        #
        # Shared rather than renamed because `swap.js` delegates a
        # document-level click to `.id-swap-swap-toggle` and reads `data-from`
        # off it. A second spelling here would need a second listener and would
        # be a second thing to keep in step with the widget, which ships from
        # its own repository. `.swap-action-column` and `.swap-label` come with
        # it: the first is what positions the button, the second is what the
        # (unregistered) inline handler would relabel.
        #
        # Design 1's rules for these are not page-scoped, so they apply here
        # too -- which is the intent. One Swap button should look like the
        # other.
        "id-swap-swap-toggle",
        "swap-action-column",
        "swap-label",
        # `address.js` builds the hover preview from `.nfticon`'s `data-path`
        # and hides them while filtering; `deferImages` collects `img.nft` and
        # swaps in `data-src` after load. The *tile* deliberately does not use
        # `.nft` -- design 1 pairs that name with the colour slot in `.nft.cN`,
        # which was landing on it. It is `.collection` instead.
        "nfticon",
        "nft",
        # DaisyUI's own button variants on the header actions -- CSV export and
        # Historic data. Shared on purpose and in the one direction the rest of
        # this list guards against: these are the *framework's* names, not
        # design 1's, so there is no design-1 rule to leak in. Both designs
        # rendered these as chrome-less text until a reader reported being
        # unable to find the export at all, and the fix is worth nothing if the
        # two designs disagree about what a secondary action looks like.
        "btn-outline",
        "btn-sm",
    }
)


def _declared_in_input_css():
    """Return every class name ``input.css`` declares a rule for.

    A blunt scan of selector text rather than a parse: it over-collects, which
    is the safe direction here -- a class this misses is reported as unknown and
    someone looks, while one it invents only ever hides a failure that a real
    parser would have found. There is no CSS parser in this project's
    dependencies and adding one to police class names would be a poor trade.

    :return: set of class names
    :rtype: set
    """
    return set(re.findall(r"\.([A-Za-z][\w-]*)", INPUT_CSS.read_text()))


def _classes_used(template):
    """Return the class names a template writes into ``class`` attributes.

    Template tags inside an attribute are stripped first, so
    ``class="fitem mcard{% if x %} folded{% endif %}"`` yields the three real
    names rather than fragments of Django syntax.

    A name built by interpolation -- ``cat-{{ band.key }}`` -- is dropped
    rather than reported as the stub ``cat-``. Only the template knows what
    those expand to, so this cannot check them and should not pretend to; the
    stylesheet declares the five ``.cat-*`` classes explicitly for that reason.

    :param template: path to the template
    :type template: :class:`pathlib.Path`
    :var text: the template source
    :type text: str
    :var mark: stands in for a removed variable, so a name built around one is
        recognisable as partial
    :type mark: str
    :return: set of class names
    :rtype: set
    """
    text = template.read_text()
    mark = "\x00"
    names = set()
    for value in re.findall(r'class="([^"]*)"', text):
        value = re.sub(r"\{%.*?%\}", " ", value)
        value = re.sub(r"\{\{.*?\}\}", mark, value)
        for name in value.split():
            if name and mark not in name and not name.startswith(("{", "}")):
                names.add(name)
    return names


@pytest.mark.parametrize("template", MONEY_TEMPLATES, ids=lambda p: p.name)
def test_dynamic_design_every_class_is_accounted_for(template):
    """No class is a collision, and none styles nothing.

    A name that is neither declared in our stylesheet nor deliberately borrowed
    from the framework is one of two mistakes, and this cannot tell them apart:
    either the framework already owns it and is about to restyle the element, or
    it was a typo and the element has no styling at all.
    """
    unknown = (
        _classes_used(template)
        - _declared_in_input_css()
        - FRAMEWORK
        - SHARED_WITH_DESIGN_ONE
    )

    assert not unknown, (
        f"{template.name} uses classes that are neither declared in input.css "
        f"nor listed as intentional: {sorted(unknown)}. If one is a DaisyUI "
        f"component name, rename it -- see this module's docstring."
    )


def test_dynamic_design_avoids_the_two_known_daisyui_collisions():
    """`.card` and `.stack` specifically, because these two already bit.

    Named rather than left to the general check above, because the general check
    passes the moment somebody declares `.card` in `input.css` -- which is
    exactly the wrong fix. The framework's rules apply either way; ours would
    merely fight them, and which one wins depends on source order.
    """
    for template in MONEY_TEMPLATES:
        used = _classes_used(template)

        assert "card" not in used, f"{template.name} uses DaisyUI's .card"
        assert "stack" not in used, f"{template.name} uses DaisyUI's .stack"


#: Design 1's templates. A class used by both designs is either a deliberate
#: contract (see `SHARED_WITH_DESIGN_ONE`) or a collision, and the difference
#: matters: design 1's rules are unscoped, so they reach the money page.
DESIGN_ONE_TEMPLATES = (
    TEMPLATES / "address.html",
    TEMPLATES / "snippets/asas.html",
    TEMPLATES / "snippets/asas/program.html",
    TEMPLATES / "snippets/asas/links.html",
    TEMPLATES / "snippets/asas/meta.html",
    TEMPLATES / "snippets/nfts.html",
    TEMPLATES / "snippets/nfts/collection.html",
    TEMPLATES / "snippets/nfts/item.html",
    TEMPLATES / "snippets/nonval.html",
)


def test_dynamic_design_shares_no_class_with_design_one_by_accident():
    """A name both designs use is a contract or a collision, never a coincidence.

    The DaisyUI check above cannot see this one. It asks whether a class is
    *declared* in `input.css`, and a class design 1 owns is declared -- so a
    collision with our own stylesheet passes it while the framework check is
    still green.

    That is not hypothetical. The dynamic charts panel was
    ``<details class="charts">``; design 1 declares an unscoped
    ``.charts { display: grid }`` that goes two-column at 768px. The panel
    inherited it, put its ``<summary>`` in the first column and the chart grid
    in the second, and every donut stacked vertically inside a half-width
    track. Renamed to ``.chart-panel``.

    Anything genuinely shared belongs in `SHARED_WITH_DESIGN_ONE` with a reason
    beside it, which is what makes this list a decision rather than a leak.
    """
    theirs = set()
    for template in DESIGN_ONE_TEMPLATES:
        if template.exists():
            theirs |= _classes_used(template)

    assert theirs, "found no design 1 classes -- discovery is looking in the wrong place"

    ours = set()
    for template in MONEY_TEMPLATES:
        ours |= _classes_used(template)

    collisions = (ours & theirs) - SHARED_WITH_DESIGN_ONE - FRAMEWORK

    assert not collisions, (
        f"the money designs and design 1 both use {sorted(collisions)}. Design "
        "1's rules are not scoped to a page, so they apply here too. Rename the "
        "money-side class, or add it to SHARED_WITH_DESIGN_ONE with the reason "
        "it is deliberately shared."
    )
