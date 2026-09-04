"""Django messages render once, and errors do not expire.

Nine templates each rendered ``messages`` themselves, and no two agreed. Six
used a bare ``alert`` with no tag branch at all, so a failure and a success were
the same neutral box -- ``BUNDLE_NAME_NOT_FOUND_ERROR`` looked exactly like
"Address enqueued for processing!". ``export.html`` put Django's tag straight
into ``class``, producing ``class="success"``, which is not a DaisyUI class and
styled nothing. ``base.html`` rendered none, which is why every page had to.

They are now rendered once by ``snippets/messages.html``, included from
``base.html``, and split by severity:

* **an error stays on the page**, with ``role="alert"``. It is usually the
  reason a submit failed, is sometimes long, and sometimes carries ``mark_safe``
  markup -- it has to be re-readable, so nothing hides it on a timer.
* **everything else is a dismissable toast**, with ``role="status"`` so a
  confirmation does not interrupt a screen reader mid-sentence.

**The toasts are rendered server-side on purpose.** Building them in JavaScript
would mean a message is invisible with scripting off, and this project has
already shipped that bug once: ``site.js`` records that ``M.toast`` calls became
silent no-ops when Materialize was removed, so a swap redirect happened and the
reason for it was never shown.

The template iterates ``messages`` twice, once per branch. That is safe with
Django's storage -- ``__iter__`` extends and returns ``_loaded_messages``, which
survives a second pass -- but it is not obvious, so
:meth:`TestTheSplit.test_both_branches_render_from_one_storage` pins it against
real ``FallbackStorage`` rather than a list, which would pass either way.
"""

from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
# signed cookies rather than the database backend: nothing here needs a
# database, and a rendering test that cannot run without one is a test
# that stops running the moment PostgreSQL is unavailable.
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase

SNIPPET = "snippets/messages.html"


def _rendered(*added):
    """Return the snippet rendered from real message storage.

    :param added: ``(level function, body, extra tags)`` triples to add
    :type added: tuple
    :return: str
    """
    request = RequestFactory().get("/")
    request.session = SessionStore()
    request._messages = FallbackStorage(request)
    for level, body, extra in added:
        level(request, body, extra_tags=extra)

    return render_to_string(SNIPPET, {"messages": messages.get_messages(request)})


def _toast_half(html):
    """Return only the part of `html` inside the toast container."""
    return html.split("data-message-toasts", 1)[1] if "data-message-toasts" in html else ""


class TestTheSplit(SimpleTestCase):
    """Which messages stay on the page and which float."""

    def test_an_error_renders_on_the_page_and_not_as_a_toast(self):
        html = _rendered((messages.error, "Bundle name not found", ""))

        self.assertIn("alert-error", html)
        self.assertIn('role="alert"', html)
        self.assertNotIn("Bundle name not found", _toast_half(html))

    def test_a_success_renders_as_a_dismissable_toast(self):
        html = _rendered((messages.success, "Address enqueued", ""))
        toasts = _toast_half(html)

        self.assertIn("Address enqueued", toasts)
        self.assertIn("alert-success", toasts)
        self.assertIn("data-dismiss-toast", toasts)
        self.assertIn('role="status"', toasts)

    def test_an_info_message_is_a_toast_too(self):
        """Only ``error`` is inline; `info` is a confirmation like any other."""
        html = _rendered((messages.info, "Authorization confirmed", ""))

        self.assertIn("Authorization confirmed", _toast_half(html))
        self.assertIn("alert-info", html)

    def test_both_branches_render_from_one_storage(self):
        """The template iterates `messages` twice, and that must be safe.

        Asserted against `FallbackStorage` rather than a list. A list re-iterates
        whatever happens, so a list-backed test would pass even if the storage
        emptied itself on the first pass and the toast half came out blank.
        """
        html = _rendered(
            (messages.error, "Bundle name not found", ""),
            (messages.success, "Layout preference saved.", "layout"),
        )

        self.assertIn("Bundle name not found", html)
        self.assertIn("Layout preference saved.", _toast_half(html))

    def test_a_dismiss_button_says_what_it_does(self):
        """The button is an unlabelled glyph, so it needs an accessible name."""
        html = _rendered((messages.success, "Saved", ""))

        self.assertIn("aria-label=", _toast_half(html))

    def test_nothing_renders_when_there_is_nothing_to_say(self):
        """No empty toast container on every page in the site."""
        html = _rendered()

        self.assertNotIn("data-message-toasts", html)
        self.assertEqual("", html.strip())


class TestItIsRenderedInOnePlace(SimpleTestCase):
    """The regression this change exists to prevent.

    Not a style rule. Nine copies is how six of them ended up unable to show an
    error as an error, and how one of them rendered messages with no styling at
    all -- each copy was written for the page in front of its author, and the
    differences were invisible until someone hit the wrong page.
    """

    #: `settings.BASE_DIR` is `website/config`, not `website`. Getting that
    #: wrong is how the first version of this test passed while searching a
    #: directory that does not exist -- nothing scanned is nothing found, and
    #: an absence check that cannot fail is not a check. Hence
    #: `test_the_sweep_actually_reads_templates` below.
    TEMPLATE_ROOTS = [Path(settings.BASE_DIR).parent / "templates"] + [
        Path(entry)
        for entry in settings.TEMPLATES[0]["DIRS"]
        if isinstance(entry, Path)
    ]

    def _templates(self):
        for root in self.TEMPLATE_ROOTS:
            yield from root.rglob("*.html")

    def test_the_sweep_actually_reads_templates(self):
        """The anchor. Without it the next test passes on an empty directory."""
        found = list(self._templates())

        self.assertGreater(
            len(found),
            50,
            f"only {len(found)} templates found under {self.TEMPLATE_ROOTS}; "
            "the roots are wrong and the sweep below proves nothing",
        )
        self.assertIn("base.html", [path.name for path in found])

    def test_only_the_snippet_iterates_messages(self):
        offenders = [
            path.name
            for path in self._templates()
            if path.name != "messages.html"
            and "for message in messages" in path.read_text()
        ]

        self.assertEqual(
            [],
            offenders,
            "these templates render messages themselves; include "
            f"{SNIPPET} from base.html instead",
        )

    def test_base_includes_the_snippet(self):
        """The other half of the rule above: one place, and it is reached."""
        base = (Path(settings.BASE_DIR).parent / "templates" / "base.html").read_text()

        self.assertIn(SNIPPET, base)
