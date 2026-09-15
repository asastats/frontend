"""Testing module for :py:mod:`utils.cache` module."""

from utils.cache import cached_bundle, cached_live_holdings, cupdate_bundle
from utils.constants.core import LIVEREFRESH_HOLDINGS_KEY


# # BUNDLE
class TestBundleCacheFunctions:
    """Testing class for :py:mod:`utils.cache` functions for bundles."""

    # # cached_bundle
    def test_utils_cache_cached_bundle_returns_false_for_no_cache(self, mocker):
        cache_client = mocker.MagicMock()
        bundle = "bundle"
        cache_client.get.return_value = None
        returned = cached_bundle(bundle, cache_client)
        assert returned is False
        cache_client.get.assert_called_once_with(bundle)

    def test_utils_cache_cached_bundle_returns_false_for_valueerror(self, mocker):
        cache_client = mocker.MagicMock()
        bundle = "bundle"
        value = mocker.MagicMock()
        cache_client.get.return_value = value
        key = bundle
        value.decode.side_effect = ValueError("")
        returned = cached_bundle(bundle, cache_client)
        assert returned is False
        cache_client.get.assert_called_once_with(key)

    def test_utils_cache_cached_bundle_returns_addresses(self, mocker):
        cache_client = mocker.MagicMock()
        bundle = "bundle"
        addresses = "address1 address2"
        cache_client.get.return_value = b"address1 address2"
        returned = cached_bundle(bundle, cache_client)
        assert returned == addresses

    # # cupdate_bundle
    def test_utils_cache_cupdate_bundle_updates_cache(self, mocker):
        cache_client = mocker.MagicMock()
        bundle, addresses = "bundle", "address1 address2"
        key = f"{bundle}"
        cupdate_bundle(bundle, addresses, cache_client)
        cache_client.set.assert_called_once_with(key, addresses)


class TestUtilsCacheLiveHoldings:
    """What the engine says a watched page *holds*, as opposed to its worth.

    **The live refresh can only swap figures into rows the page already has.**
    So an asset just bought has nowhere to arrive, one just sold is never
    mentioned and its row stays as it was, and an amount column is not what a
    value fragment carries. A change to this is answered with a page reload,
    and it keys the rendered page so that reload cannot be served the markup
    that prompted it.
    """

    def test_utils_cache_live_holdings_reads_the_page_field(self, mocker):
        """One field per page in the hash the engine writes."""
        client = mocker.MagicMock()
        client.hget.return_value = b"beef1234"

        assert cached_live_holdings("AAA", client) == "beef1234"
        client.hget.assert_called_once_with(LIVEREFRESH_HOLDINGS_KEY, "AAA")

    def test_utils_cache_live_holdings_is_empty_for_an_unwatched_page(self, mocker):
        """**A value, not a failure.** Every page nobody watches has no entry,
        and an empty fingerprint keys them exactly as they were keyed before any
        of this existed."""
        client = mocker.MagicMock()
        client.hget.return_value = None

        assert cached_live_holdings("AAA", client) == ""

    def test_utils_cache_live_holdings_accepts_an_already_decoded_value(self, mocker):
        """Redis answers bytes, but a client configured to decode answers `str`,
        and a fingerprint compared against the wrong type would make every page
        look changed on every block."""
        client = mocker.MagicMock()
        client.hget.return_value = "beef1234"

        assert cached_live_holdings("AAA", client) == "beef1234"
