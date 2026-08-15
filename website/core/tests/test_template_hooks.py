"""Class names the JavaScript selects on must survive template edits.

A redesign moves presentation around freely, and that is fine -- right up to
the point where a class turns out not to be presentational at all. During the
Materialize-to-DaisyUI migration four hooks were removed as "orphans" because
no stylesheet defined them, and each one silently broke behaviour instead of
appearance:

* ``.bundlenames`` -- home.js sorts ``$(".bundlenames > div")``, so removing it
  left the sort radios doing nothing;
* ``.ns`` -- index.js binds the address-namespace radios through it;
* ``.checks`` -- subscriptions.js suppresses clicks on the feature list;
* ``.indeterminate`` -- index.js and tax.js add ``.progress`` to its *parent*
  when a form is submitted, which is why static analysis of the stylesheet said
  it was dead markup when it was not.

None of those failures looked like a styling bug, and none of them were caught
by a template that still compiled. This test reads the selectors straight out
of the scripts, so the list cannot drift from what the code actually uses.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

#: Scripts whose selectors are the contract. Minified builds are skipped: they
#: are generated from these, so checking both would double-count.
SCRIPT_DIRS = ["js"]

#: Hooks that are legitimately absent from templates because something else
#: creates the element -- a third-party widget, or JavaScript building its own
#: DOM. Anything added here needs a reason beside it.
NOT_IN_TEMPLATES = {
    "accept-all": "rendered by the cookie-consent vendor bundle",
    "magic-iframe": "injected by the email-preview iframe helper",
    "scale-in": "toggled at runtime; never authored in a template",
    "scale-out": "toggled at runtime; never authored in a template",
    "visible": "toggled at runtime; never authored in a template",
    "nftpreview": "built by address.js from the NFT payload",
    "thelink": "built by address.js when it renders a copy control",
    "progress": "added to a wrapper at submit time by index.js and tax.js",
}


def _script_paths():
    for directory in settings.STATICFILES_DIRS:
        for name in SCRIPT_DIRS:
            root = Path(directory) / name
            if not root.is_dir():
                continue
            for path in sorted(root.glob("*.js")):
                if ".min" in path.name or path.name == "bundle.js":
                    continue
                yield path


def _selected_classes():
    """Return every class name the first-party scripts select on."""
    found = set()
    for path in _script_paths():
        source = path.read_text(errors="ignore")
        found |= set(re.findall(r"""\$\(["']\.([\w-]+)""", source))
        found |= set(re.findall(r"""querySelector(?:All)?\(["']\.([\w-]+)""", source))
        found |= set(re.findall(r"""closest\(["']\.([\w-]+)""", source))
    return found - set(NOT_IN_TEMPLATES)


def _template_markup():
    text = []
    for directory in settings.TEMPLATES[0]["DIRS"]:
        for path in Path(directory).rglob("*.html"):
            text.append(path.read_text(errors="ignore"))
    return "\n".join(text)


SELECTED = sorted(_selected_classes())


class TestTemplateHooks:
    """Testing class for class names shared between scripts and templates."""

    def test_core_scripts_are_discoverable(self):
        """Guard the guard: an empty list would make this suite vacuous."""
        assert len(SELECTED) > 5, (
            "found almost no class selectors in static/js -- discovery is "
            f"probably looking in the wrong place: {SELECTED}"
        )

    @pytest.mark.parametrize("hook", SELECTED)
    def test_core_template_still_carries_hook(self, hook):
        """Some template must still render `hook`.

        :param hook: class name a script selects on
        :type hook: str
        """
        markup = _template_markup()
        assert re.search(r'class="[^"]*\b' + re.escape(hook) + r"\b", markup), (
            f".{hook} is selected by a script in static/js but no template "
            "renders it any more. Either restore the class or delete the code "
            "that depends on it -- silently, it does nothing."
        )
