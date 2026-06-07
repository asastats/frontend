"""Testing module for website's asgi module."""

from channels.auth import AuthMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import CookieMiddleware, SessionMiddleware
from django.core.handlers.asgi import ASGIHandler
from django.urls import URLPattern

from asastats import asgi


class TestAsastatsAsgi:
    """Testing class for :py:mod:`asastats.asastats.asgi` module."""

    app = None

    def setup_method(self):
        self.app = asgi.application
        self.router = self.app.application_mapping.get(
            "websocket"
        ).application.inner.inner.inner

    def test_asastats_asgi_sets_application_as_protocoltyperouter(self):
        assert isinstance(self.app, ProtocolTypeRouter)

    def test_asastats_asgi_sets_websocket_as_authmiddlewarestack(self):
        middleware = self.app.application_mapping.get("websocket")
        assert isinstance(middleware.application, CookieMiddleware)
        assert isinstance(middleware.application.inner, SessionMiddleware)
        assert isinstance(middleware.application.inner.inner, AuthMiddleware)

    def test_asastats_asgi_sets_websocket_authmiddleware_urlrouter(self):
        assert isinstance(self.router, URLRouter)

    def test_asastats_asgi_websocket_routes_count(self):
        assert len(self.router.routes) == 1

    def test_asastats_asgi_defines_historic_user_widget_websocket_url(self):
        url = self.router.routes[0]
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "widgets.inhouse.historic.consumers.HistoricConsumer"
        assert str(url.pattern) == "widgets/historic/(?P<bundle>\\w{40}|\\w{58})/$"

    def test_asastats_asgi_sets_http_as_asgihandler(self):
        handler = self.app.application_mapping.get("http")
        assert isinstance(handler, ASGIHandler)
