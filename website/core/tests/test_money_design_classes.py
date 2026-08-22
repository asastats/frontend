"""Every class the money-column designs use is one we meant to use.

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

#: The money-column designs' own templates. Design 1's are deliberately absent:
#: it is the untouched old page and its classes predate all of this.
MONEY_TEMPLATES = (
    TEMPLATES / "address_money.html",
    TEMPLATES / "snippets/money/asset.html",
    TEMPLATES / "snippets/money/position.html",
    TEMPLATES / "snippets/money/band.html",
    TEMPLATES / "snippets/money/toolbar.html",
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
def test_money_design_every_class_is_accounted_for(template):
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


def test_money_design_avoids_the_two_known_daisyui_collisions():
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
