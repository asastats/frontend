"""Testing module for website's asynchronous routing module."""

import importlib
from unittest import mock

from config import routing


class TestAsastatsRouting:
    """Testing class for :py:mod:`website.config.routing` module."""

    def test_config_routing_adds_widgets_websocket_urlpatterns(self, mocker):
        urlpattern1, urlpattern2 = mocker.MagicMock(), mocker.MagicMock()

        with mock.patch(
            "widgets.routing.websocket_urlpatterns", [urlpattern1, urlpattern2]
        ):
            importlib.reload(routing)
            url = routing.websocket_urlpatterns
            assert url == [urlpattern1, urlpattern2]
