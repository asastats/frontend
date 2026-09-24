"""Root URLconf for the automated suite: the site's own, plus served icons.

**Why the suite needs its own.** `automated_tests.py` sets `BASE_CDN_URL = ""`
so the browser suite never waits on a host on the internet - `_open_page` waits
for every image to report `complete`, and one CDN image that accepts the
connection and never replies is enough to fail a test on a CI runner.

Emptying it makes `asa_icon` emit root-relative paths, which the live server
answers with a 404. A 404 was assumed to be harmless, on the reasoning that it
sets `img.complete` at once and no test asserts an icon *loaded*. That was
wrong, and `SwapModalTest.test_the_source_picker_lists_holdings_without_a_round_trip`
is what found it: `static/js/csp-safe-handlers.js` listens for image `error`
events and rewrites `src` to the element's `data-fallback`. So the 404 did not
merely fail to load - it replaced the icon's `src` with `empty.png`, under a
test that reads that `src` back and asserts what it points at.

Answering those paths with a real pixel fixes both halves: nothing is fetched
off the network, and nothing errors, so the fallback handler stays asleep and
the markup the templates produced is the markup a test reads. It also silences
roughly 180 `Not Found` warnings per browser test, which were burying anything
real in the captured log.

Prepended rather than appended: `config.urls` ends with `re_path(r"^", ...)`, which
matches everything, so a route added after it is never reached.
"""

import base64

from django.http import HttpResponse
from django.urls import re_path

from config.urls import handler500  # noqa: F401 - re-exported for this urlconf
from config.urls import urlpatterns as _site_urlpatterns

#: A 1x1 fully transparent PNG, 70 bytes. Small enough to be free, real enough
#: that the browser fires `load` rather than `error`.
_PIXEL = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAC"
    b"hwGA60e6kgAAAABJRU5ErkJggg=="
)


def serve_placeholder_image(request, *args, **kwargs):
    """Return a pixel for any icon or thumbnail path the suite asks for.

    Deliberately indifferent to which asset was asked for: the point is that
    *something* loads, not that it is the right picture. A test that cares which
    icon an element points at reads the `src`, which is exactly what the
    fallback handler was overwriting.

    :param request: current request
    :type request: :class:`HttpRequest`
    :return: :class:`HttpResponse`
    """
    return HttpResponse(_PIXEL, content_type="image/png")


urlpatterns = [
    re_path(r"^(?:icons|thumbnails)/.+\.png$", serve_placeholder_image),
] + _site_urlpatterns
