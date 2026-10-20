"""Testing module for website's settings modules."""

from django.conf import settings


class TestChannelLayerSettings:
    """Testing class for the channel layer's Redis connection settings."""

    def test_channel_layer_read_timeout_outlasts_the_blocking_receive(self):
        # channels_redis waits on BZPOPMIN for 5 s; redis-py 8 reads for 5 s by default
        host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
        assert host["socket_timeout"] > 5
        assert host["address"] == settings.CHANNEL_LAYER_ADDRESS
