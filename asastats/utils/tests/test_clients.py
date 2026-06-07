"""Testing module for :py:mod:`utils.clients` module."""

from utils.clients import (
    algod_instance,
    indexer_instance,
    redis_instance,
    search_transactions,
)


class TestUtilsClientsFunctions:
    """Testing class for :py:mod:`utils.clients` functions."""

    # # algod_instance
    def test_utils_clients_algod_instance_functionality(self, mocker):
        mocked_settings = mocker.patch("utils.clients.settings")
        mocked_algod = mocker.patch("utils.clients.algod")
        returned = algod_instance()
        assert returned == mocked_algod.AlgodClient.return_value
        mocked_algod.AlgodClient.assert_called_once_with(
            mocked_settings.ALGOD_TOKEN, mocked_settings.ALGOD_URL
        )

    # # indexer_instance
    def test_utils_clients_indexer_instance_functionality(self, mocker):
        mocked_settings = mocker.patch("utils.clients.settings")
        mocked_indexer = mocker.patch("utils.clients.indexer")
        returned = indexer_instance()
        assert returned == mocked_indexer.IndexerClient.return_value
        mocked_indexer.IndexerClient.assert_called_once_with(
            mocked_settings.INDEXER_TOKEN, mocked_settings.INDEXER_URL
        )

    # # redis_instance
    def test_utils_clients_redis_instance_functionality(self, mocker):
        mocked_settings = mocker.patch("utils.clients.settings")
        mocked_redis = mocker.patch("utils.clients.redis")
        returned = redis_instance()
        assert returned == mocked_redis.from_url.return_value
        mocked_redis.from_url.assert_called_once_with(mocked_settings.REDIS_URL)

    # # search_transactions
    def test_utils_clients_search_transactions_returns_single_page(self, mocker):
        client = mocker.MagicMock()
        client.search_transactions.return_value = {
            "transactions": [1, 2],
            "next-token": None,
        }
        returned = search_transactions({"address": "A"}, indexer_client=client)
        assert returned == [1, 2]
        client.search_transactions.assert_called_once_with(
            address="A", limit=1000, next_page=""
        )

    def test_utils_clients_search_transactions_paginates_until_no_token(self, mocker):
        client = mocker.MagicMock()
        client.search_transactions.side_effect = [
            {"transactions": [1], "next-token": "TOKEN"},
            {"transactions": [2], "next-token": None},
        ]
        mocked_sleep = mocker.patch("time.sleep")
        returned = search_transactions({"address": "A"}, indexer_client=client)
        assert returned == [1, 2]
        assert client.search_transactions.call_count == 2
        mocked_sleep.assert_called_once_with(0.05)

    def test_utils_clients_search_transactions_creates_client_when_omitted(
        self, mocker
    ):
        mocked_instance = mocker.patch("utils.clients.indexer_instance")
        mocked_instance.return_value.search_transactions.return_value = {
            "transactions": [],
            "next-token": None,
        }
        returned = search_transactions({"address": "A"})
        assert returned == []
        mocked_instance.assert_called_once_with()
