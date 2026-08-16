"""Test-suite-wide fixtures.

Only one thing lives here, and it exists because of a difference in how Django
treats its two kinds of state: the database is rolled back between tests, and
the cache is not.

The suite runs under config.settings.automated_tests, which uses a real
(in-memory) cache rather than the DummyCache development.py sets -- see that
module for why. A real cache without this fixture would be a trade of one
problem for a worse one: `cache_page` decorates six views, three of them for
ninety minutes, so the second test to request a page would be served the first
test's response. The integration tests would quietly stop reaching the backend
at all, which is the one thing they exist to do.

Clearing before each test keeps both properties: caching is exercised within a
test, and nothing leaks between them.
"""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Empty the cache before every test.

    Autouse rather than opt-in: a test that needed this and did not ask for it
    would not fail, it would pass against stale data -- which is the failure
    mode this fixture exists to prevent.
    """
    cache.clear()
    yield
