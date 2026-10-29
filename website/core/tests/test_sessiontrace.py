"""Testing the app session trace: middleware, sign-in receiver and digest."""

import logging

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.backends.db import SessionStore
from django.test import Client, RequestFactory
from django.urls import reverse

from core.middleware import AppClientMiddleware, AppSessionTraceMiddleware
from core.sessions import key_digest
from core.signals import trace_app_login

ANDROID_UA = "Mozilla/5.0 (Linux; Android 11; wv) ASAStatsApp/1.1.0 (android)"
BROWSER_UA = "Mozilla/5.0 (X11; Linux aarch64) Chrome/141.0.0.0 Safari/537.36"
LOGGER = "core.sessiontrace"


def _request(user_agent=ANDROID_UA, cookie=None, path="/home/"):
    headers = {"HTTP_USER_AGENT": user_agent}
    request = RequestFactory().get(path, **headers)
    if cookie is not None:
        request.COOKIES[settings.SESSION_COOKIE_NAME] = cookie
    AppClientMiddleware(lambda r: None)(request)
    request.session = SessionStore(cookie)
    return request


def _signed_in_key(user):
    session = SessionStore()
    session["_auth_user_id"] = str(user.pk)
    session.create()
    return session.session_key


def _run(request, user=None):
    """Run the middleware; the inner view sets `request.user` unless `user` is False."""

    def view(req):
        if user is not False:
            req.user = user or AnonymousUser()
        return "response"

    return AppSessionTraceMiddleware(view)(request)


@pytest.fixture
def user(db):
    return User.objects.create_user("trace", password="x")


class TestCoreSessionsKeyDigest:
    def test_key_digest_is_short_stable_and_not_the_key(self):
        assert key_digest("abc") == key_digest("abc")
        assert len(key_digest("abc")) == 12
        assert key_digest("abc") != key_digest("abd")
        assert "abc" not in key_digest("abc")


@pytest.mark.django_db
class TestCoreAppSessionTraceMiddleware:
    def test_middleware_follows_app_client_middleware(self):
        middleware = settings.MIDDLEWARE
        assert middleware.index("core.middleware.AppSessionTraceMiddleware") == (
            middleware.index("core.middleware.AppClientMiddleware") + 1
        )

    def test_an_unknown_app_cookie_is_logged_with_its_digest(self, caplog):
        caplog.set_level(logging.INFO, logger=LOGGER)

        assert _run(_request(cookie="gone" * 8, path="/faq/")) == "response"

        assert [r.getMessage() for r in caplog.records] == [
            f"App session {key_digest('gone' * 8)} not found: android 1.1.0 GET /faq/"
        ]

    def test_a_browser_cookie_is_not_logged(self, caplog):
        caplog.set_level(logging.INFO, logger=LOGGER)

        _run(_request(user_agent=BROWSER_UA, cookie="gone" * 8))

        assert caplog.records == []

    def test_an_app_request_without_a_cookie_is_not_logged(self, caplog):
        caplog.set_level(logging.INFO, logger=LOGGER)

        _run(_request())

        assert caplog.records == []

    def test_a_signed_in_app_session_is_not_logged(self, caplog, user):
        caplog.set_level(logging.INFO, logger=LOGGER)

        _run(_request(cookie=_signed_in_key(user)), user=user)

        assert caplog.records == []

    def test_a_session_that_loses_its_user_is_logged(self, caplog, user):
        caplog.set_level(logging.INFO, logger=LOGGER)
        key = _signed_in_key(user)

        _run(_request(cookie=key, path="/accounts/logout/"))

        assert [r.getMessage() for r in caplog.records] == [
            f"App session {key_digest(key)} lost its user: android 1.1.0 GET /accounts/logout/"
        ]

    def test_a_request_that_never_got_a_user_is_not_logged(self, caplog, user):
        caplog.set_level(logging.INFO, logger=LOGGER)

        _run(_request(cookie=_signed_in_key(user)), user=False)

        assert caplog.records == []


@pytest.mark.django_db
class TestCoreSignalsTraceAppLogin:
    def test_an_app_sign_in_logs_the_new_session(self, caplog, user):
        caplog.set_level(logging.INFO, logger=LOGGER)
        key = _signed_in_key(user)

        trace_app_login(User, user, _request(cookie=key))

        assert [r.getMessage() for r in caplog.records] == [
            f"App session {key_digest(key)} signed in: user {user.pk}, android 1.1.0"
        ]

    def test_a_browser_sign_in_is_not_logged(self, caplog, user):
        caplog.set_level(logging.INFO, logger=LOGGER)

        trace_app_login(
            User, user, _request(user_agent=BROWSER_UA, cookie=_signed_in_key(user))
        )

        assert caplog.records == []

    def test_a_sign_in_without_a_request_or_session_key_is_not_logged(self, caplog, user):
        caplog.set_level(logging.INFO, logger=LOGGER)

        trace_app_login(User, user, None)
        trace_app_login(User, user, _request())

        assert caplog.records == []

    def test_allauth_login_logs_the_key_the_app_receives(self, caplog, user):
        caplog.set_level(logging.INFO, logger=LOGGER)
        client = Client(HTTP_USER_AGENT=ANDROID_UA)

        client.post(reverse("account_login"), {"login": "trace", "password": "x"})

        key = client.cookies[settings.SESSION_COOKIE_NAME].value
        assert f"App session {key_digest(key)} signed in: user {user.pk}" in caplog.text
