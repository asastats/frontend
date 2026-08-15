"""The two base templates must load the same scripts, minus the framework.

While the site has both base.html (Materialize) and base_tw.html (DaisyUI), a
page's behaviour must not depend on which one it extends. That is easy to get
wrong in one direction only: base_tw.html was written from scratch, so anything
simply forgotten is absent rather than wrong, and absence has no symptom until
something silently stops working.

It happened. base_tw.html shipped without jQuery, without site.js and without
bundle.js, which meant that on every converted page:

* home.js, index.js, tax.js, subscriptions.js and profile-authorize.js threw on
  load, because all of them are jQuery -- sorting, filtering, the namespace
  radios and the progress bars quietly did nothing;
* the cookie-consent banner never initialised;
* copy-to-clipboard never bound;
* the wallet package never loaded, so wallet connect, the EVM flow and the swap
  bridge were all dead.

None of that raised an error a user or a template test would see.
"""

import re
from pathlib import Path

from django.conf import settings

#: Scripts base.html loads that base_tw.html deliberately does not, with why.
INTENTIONALLY_ABSENT = {
    "materialize.min.js": "the framework being migrated away from",
    "color-mode.min.js": "replaced by the inline data-theme stamp and theme.js",
}

#: Scripts only base_tw.html loads. Listed so the check stays two-directional.
NEW_ONLY = {
    "theme.js": "the appearance picker, which replaces the dark/light toggle",
    "authmodal.js": "the login dialog, which replaces M.Modal and M.Tabs",
}


def _scripts(template_name):
    """Return the script filenames a template links, ignoring cache-busting."""
    for directory in settings.TEMPLATES[0]["DIRS"]:
        path = Path(directory) / template_name
        if path.is_file():
            found = re.findall(r"""static\s+['"]js/([\w.-]+)['"]""", path.read_text())
            # style.min078 -> style.min, so a version bump is not a difference
            return {re.sub(r"\d+(?=\.js$)", "", name) for name in found}
    raise AssertionError(f"{template_name} not found in TEMPLATES[0]['DIRS']")


class TestBaseTemplateParity:
    """Testing class for script parity between the two base templates."""

    def test_core_base_templates_are_both_found(self):
        """Guard the guard: a typo in a name would make this vacuous."""
        assert _scripts("base.html")
        assert _scripts("base_tw.html")

    def test_core_base_tw_loads_everything_base_html_does(self):
        """Anything base.html loads must be on base_tw.html or excused."""
        old = _scripts("base.html")
        new = _scripts("base_tw.html")
        excused = {re.sub(r"\d+(?=\.js$)", "", n) for n in INTENTIONALLY_ABSENT}
        missing = old - new - excused
        assert not missing, (
            f"base_tw.html does not load {sorted(missing)}, which base.html "
            "does. A page on the new base loses that behaviour with no error "
            "anywhere -- add the script, or add it to INTENTIONALLY_ABSENT "
            "with a reason."
        )

    def test_core_base_tw_extras_are_declared(self):
        """And the other direction: no unexplained additions."""
        old = _scripts("base.html")
        new = _scripts("base_tw.html")
        extra = new - old - set(NEW_ONLY)
        assert not extra, (
            f"base_tw.html loads {sorted(extra)}, which base.html does not. "
            "Add it to NEW_ONLY with a reason so the difference is deliberate."
        )
