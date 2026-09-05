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
from utils.helpers import parse_export_limits  # noqa: E402

#: Obviously not a secret, and never used against a real token: the suite both
#: mints and verifies with it.
SIMPLE_JWT_KEY = "automated-tests-signing-key-not-a-secret"
SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": SIMPLE_JWT_KEY}  # noqa: F405

#: The example from `core.checks`' own hint. `free` has to be present or a
#: permission-0 reader sees no CSV export link.
EXPORT_TIERS_ADDRESSES_LIMIT = parse_export_limits(
    "free:5,Intro:6,Asastatser:7,Professional:8,Cluster:10"
)
