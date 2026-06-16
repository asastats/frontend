"""Testing module for :py:mod:`utils.cache` module."""

from utils.cache import cached_bundle, cupdate_bundle


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
