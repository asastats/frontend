"""Django settings module used by the automated test suite.

Not to be confused with ``testing.py``, which configures the deployed staging
host (see deploy/molecule/*/molecule.yml). This module is what pytest.ini
points at, and it exists for one reason: the cache.

``development.py`` sets ``DummyCache``, which discards every write. That is the
right choice for ``runserver`` -- six views are ``cache_page``'d, three of them
for ninety minutes, and a developer wants to see an edit immediately rather
than in an hour and a half. It is the wrong choice for the suite, because it
means no test ever exercises a caching code path, and any caching contract can
break in production without a single failure.

It also has a cost that is easy to miss. ``deployment_capabilities`` runs on
every render and is meant to be cached for five minutes; with DummyCache it
makes a live HTTP call to the backend on *every page load in the suite*. A
functional test walking eight pages fires eight backend requests. On modest
hardware, with Chrome and Django competing for the same CPU, that queueing is
a plausible cause of the timeouts that pass when a test is run on its own.

LocMemCache rather than Redis, deliberately, even though Redis is already a
project requirement:

* Django rolls the database back between tests; it never clears the cache.
  Redis outlives the run, so an entry written by one run would still be there
  for the next, and a failure would depend on run history. LocMemCache lives
  and dies with the process.
* the Redis cache is shared -- staging uses the same db and KEY_PREFIX, and a
  developer's browsing on :8000 would populate the very keys `cache_page` then
  serves to a test.
* the 1000-odd unit tests currently need no Redis running, and should not
  start to.

Per-test isolation is provided by the autouse fixture in conftest.py at the
repository root, which clears the cache before each test. The combination is
the point: caching is exercised *within* a test, and cannot leak *between*
tests.
"""

from .development import *  # noqa: F401,F403

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "asastats-automated-tests",
    }
}


# --- Values the suite must not inherit from whoever's .env ---
#
# `load_dotenv()` in base.py reads `website/.env`, which exists on a developer's
# machine and does not exist in CI. Two settings that default to empty then
# behave differently in the two places, and the suite was green locally while
# failing 16 tests on GitHub:
#
# * an empty `SIMPLE_JWT_KEY` makes `jwt` refuse to sign at all
#   (`InvalidKeyError: HMAC key must not be empty`) and turns
#   `core.checks.widgets_api_token` into `asastats.E001`, so every test that
#   asserts a *different* code fails on the first one instead;
# * empty export limits hide the CSV export link for every tier below Cluster,
#   which is what `TestCacheIsKeyedOnEntitlementToo` renders and asserts on.
#
# Pinned here rather than exported in the workflow so the suite is
# deterministic in both places, and so a developer whose `.env` is unusual
# gets the same result as CI.
import uuid  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

import jwt  # noqa: E402

from utils.helpers import parse_export_limits  # noqa: E402

#: Obviously not a secret, and never used against a real token: the suite both
#: mints and verifies with it.
SIMPLE_JWT_KEY = "automated-tests-signing-key-not-a-secret"
SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": SIMPLE_JWT_KEY}  # noqa: F405

#: Minted here, with the key above, and for the same reason the key is pinned.
#:
#: `WIDGETS_API_TOKEN` comes from `website/.env`, where a developer's copy is a
#: real token signed with the *real* `SIMPLE_JWT_KEY`. Pinning the key without
#: also minting the token left the two halves of one credential disagreeing:
#: the token verified everywhere except under the settings the suite runs with,
#: so every test that authenticates as the widget host got a 401 that no check
#: reported -- `manage.py check` passes, because it validates against the real
#: key. On CI, where the variable is absent entirely, it was a 401 too.
#:
#: Signed with PyJWT rather than `AccessToken` because minting through simplejwt
#: imports the user model, and a settings module is not allowed to.
_TOKEN_MINTED_AT = datetime.now(tz=timezone.utc)
WIDGETS_API_TOKEN = jwt.encode(
    {
        "token_type": "access",
        "exp": _TOKEN_MINTED_AT + SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
        "iat": _TOKEN_MINTED_AT,
        "jti": uuid.uuid4().hex,
        "user_id": "1",
    },
    SIMPLE_JWT_KEY,
    algorithm="HS256",
)

#: The example from `core.checks`' own hint. `free` has to be present or a
#: permission-0 reader sees no CSV export link.
EXPORT_TIERS_ADDRESSES_LIMIT = parse_export_limits(
    "free:5,Intro:6,Asastatser:7,Professional:8,Cluster:10"
)


# --- The browser suite must not depend on an external host ---
#
# Every icon and thumbnail the site renders is `BASE_CDN_URL` plus a path, so
# with the real value a browser test fetches them from `cdn.asastats.com` for
# real -- two provider icons on the home page, and one per row on an address
# page, which is dozens. Selenium's default page load strategy makes
# `browser.get` wait for `load`, and `load` waits for every one of them.
#
# That makes the suite's slowest pages hostage to a third party. A CDN that is
# merely *slow*, or a runner whose egress stalls rather than refusing, turns
# into a `browser.get` that does not return -- which is a 120 s
# `ReadTimeoutError` from chromedriver and a test that failed for no reason of
# its own. `test_profile_pages.LinkedAddressesPageTest` did exactly that on CI
# on 2026-09-13, and reproduces here about once in twenty runs.
#
# Port 9 on loopback, because **Chrome refuses it before opening a socket**.
# 9 is `discard`, one of the ports on Chrome's restricted list, so the request
# fails as `ERR_UNSAFE_PORT` immediately and unconditionally -- it is a rule in
# the browser, not a property of the machine, so it holds whatever the runner
# happens to be doing. No DNS, no egress, and -- unlike pointing this at a
# local path -- no request through the live server either, which would have put
# dozens of extra 404 renders on the very thread already under suspicion.
#
# A high port picked for being unused is *not* the same guarantee and was the
# first thing tried here: `ip_local_port_range` is a tunable, a CI image may
# set it differently, and anything that did bind the port would silently start
# serving these requests -- or hang, which is the failure being removed.
#
# Two things make this safe rather than merely quiet:
#
# * every `data-fallback` in the templates is built from this same setting, so
#   the placeholder a broken image falls back to is redirected with it rather
#   than reaching for the real CDN;
# * the tests that assert on icons measure the *box*, which is CSS (`.mono-tile`
#   is 38px and its image 30px whatever the image does), and the recorder in
#   `functional_tests.base.record_javascript_errors` listens for `error`
#   without `capture`, so a failed image never reaches it. A resource error
#   only reaches an ancestor in the capture phase -- which is precisely why
#   `test_swap_widget._disarm_icon_fallback` passes `true`.
#
# Nothing asserts the literal host: every unit test compares against
# `settings.BASE_CDN_URL` itself, and the jest fixtures are guarded on classes
# and ids rather than bytes. The one hardcoded CDN URL left in the tree is
# design 1's `deferImages` fallback in `static/js/address.js`, which is a
# single URL the browser caches after the first miss.
BASE_CDN_URL = "http://127.0.0.1:9"
