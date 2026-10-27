"""Testing module for :py:mod:`core.appclient` module."""

import pytest
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse

from core.appclient import (
    APP_CLIENT_REGEX,
    AppClient,
    app_cache_prefix,
    app_client,
    hidden_widgets,
    parse_app_client,
    purchase_hidden,
    supported_wallets,
    wallet_supported,
    widget_hidden,
)
from core.context_processors import app_client as app_client_processor
from core.middleware import AppClientMiddleware
from utils.constants.core import ALGORAND_WALLETS

ANDROID_UA = (
    "Mozilla/5.0 (Linux; Android 16; Pixel 8; wv) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Version/4.0 Chrome/141.0.0.0 Mobile Safari/537.36 "
    "ASAStatsApp/1.1.0 (android)"
)
IOS_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Mobile/15E148 ASAStatsApp/1.1.0 (ios)"
)
BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)


def _request(user_agent=None):
    """Return a request that went through :class:`AppClientMiddleware`.

    :return: :class:`django.http.HttpRequest`
    """
    headers = {} if user_agent is None else {"HTTP_USER_AGENT": user_agent}
    request = RequestFactory().get("/", **headers)
    AppClientMiddleware(lambda r: None)(request)
    return request


class TestCoreAppClientParsing:
    """Testing class for :py:func:`core.appclient.parse_app_client`."""

    def test_core_appclient_parse_app_client_for_android(self):
        assert parse_app_client(ANDROID_UA) == AppClient("android", (1, 1, 0))

    def test_core_appclient_parse_app_client_for_ios(self):
        assert parse_app_client(IOS_UA) == AppClient("ios", (1, 1, 0))

    def test_core_appclient_parse_app_client_for_a_future_version(self):
        client = parse_app_client("Mozilla/5.0 ASAStatsApp/2.10.3 (ios)")

        assert client.version == (2, 10, 3)
        assert client.version_string == "2.10.3"

    @pytest.mark.parametrize("user_agent", [None, "", BROWSER_UA])
    def test_core_appclient_parse_app_client_for_absent_token(self, user_agent):
        assert parse_app_client(user_agent) is None

    @pytest.mark.parametrize(
        "user_agent",
        [
            "ASAStatsApp/1.1 (ios)",
            "ASAStatsApp/1.1.0 (windows)",
            "ASAStatsApp/1.1.0 ios",
            "ASAStatsApp/one.1.0 (android)",
            "ASAStatsApp/1.1.0 (Android)",
            "NotASAStatsApp/1.1.0 (ios)",
        ],
    )
    def test_core_appclient_parse_app_client_for_malformed_token(self, user_agent):
        assert parse_app_client(user_agent) is None

    def test_core_appclient_regex_matches_the_capacitor_format(self):
        # mobile/capacitor.config.ts: `ASAStatsApp/${version} (${platform})`
        assert APP_CLIENT_REGEX.search("x ASAStatsApp/1.1.0 (android)")


class TestCoreAppClientRequest:
    """Testing class for the request helpers in :py:mod:`core.appclient`."""

    def test_core_appclient_middleware_sets_app_client(self):
        assert _request(IOS_UA).app_client == AppClient("ios", (1, 1, 0))

    def test_core_appclient_middleware_sets_none_for_a_browser(self):
        assert _request(BROWSER_UA).app_client is None

    def test_core_appclient_middleware_sets_none_without_user_agent(self):
        assert _request().app_client is None

    def test_core_appclient_middleware_returns_the_response(self):
        response = object()

        assert (
            AppClientMiddleware(lambda r: response)(RequestFactory().get("/")) is response
        )

    def test_core_appclient_app_client_without_middleware(self):
        assert app_client(RequestFactory().get("/")) is None

    def test_core_appclient_context_processor(self):
        assert app_client_processor(_request(ANDROID_UA))["APP_CLIENT"] == AppClient(
            "android", (1, 1, 0)
        )
        assert app_client_processor(_request(BROWSER_UA))["APP_CLIENT"] is None

    def test_core_appclient_app_cache_prefix(self):
        assert app_cache_prefix(_request(IOS_UA)) == "app-ios"
        assert app_cache_prefix(_request(ANDROID_UA)) == "app-android"

    def test_core_appclient_app_cache_prefix_is_none_for_a_browser(self):
        assert app_cache_prefix(_request(BROWSER_UA)) is None


class TestCoreAppClientPredicates:
    """Testing class for the per-platform switches in :py:mod:`core.appclient`."""

    # # purchase_hidden
    def test_core_appclient_purchase_hidden_by_default_on_both_platforms(self):
        assert purchase_hidden(_request(IOS_UA)) is True
        assert purchase_hidden(_request(ANDROID_UA)) is True

    def test_core_appclient_purchase_hidden_never_in_a_browser(self):
        assert purchase_hidden(_request(BROWSER_UA)) is False

    @override_settings(APP_HIDE_PURCHASE=frozenset({"ios"}))
    def test_core_appclient_purchase_hidden_per_platform(self):
        assert purchase_hidden(_request(IOS_UA)) is True
        assert purchase_hidden(_request(ANDROID_UA)) is False

    # # widget_hidden
    def test_core_appclient_widget_hidden_nothing_by_default(self):
        assert widget_hidden(_request(IOS_UA), "swapcore") is False
        assert widget_hidden(_request(ANDROID_UA), "swapcore") is False

    @override_settings(
        APP_HIDDEN_WIDGETS={"ios": frozenset({"swapcore"}), "android": frozenset()}
    )
    def test_core_appclient_widget_hidden_per_platform(self):
        assert widget_hidden(_request(IOS_UA), "swapcore") is True
        assert widget_hidden(_request(IOS_UA), "historic") is False
        assert widget_hidden(_request(ANDROID_UA), "swapcore") is False
        assert widget_hidden(_request(BROWSER_UA), "swapcore") is False

    @override_settings(APP_HIDDEN_WIDGETS={})
    def test_core_appclient_widget_hidden_for_a_platform_not_configured(self):
        assert widget_hidden(_request(IOS_UA), "swapcore") is False

    # # wallet_supported
    @pytest.mark.parametrize("wallet_id", ["kibisis", "lute"])
    def test_core_appclient_wallet_supported_drops_defaults_in_app(self, wallet_id):
        assert wallet_supported(_request(IOS_UA), wallet_id) is False
        assert wallet_supported(_request(BROWSER_UA), wallet_id) is True

    @pytest.mark.parametrize("wallet_id", ["pera", "defly"])
    def test_core_appclient_wallet_supported_keeps_mobile_wallets(self, wallet_id):
        assert wallet_supported(_request(ANDROID_UA), wallet_id) is True

    @override_settings(APP_UNSUPPORTED_WALLETS=frozenset({"defly"}))
    def test_core_appclient_wallet_supported_follows_the_setting(self):
        assert wallet_supported(_request(IOS_UA), "defly") is False
        assert wallet_supported(_request(IOS_UA), "kibisis") is True


class TestCoreAppClientSupportedWallets:
    """Every source of the wallet cards leaves out the wallets the app cannot use."""

    @pytest.fixture(autouse=True)
    def _capabilities(self, mocker):
        mocker.patch(
            "core.context_processors.fetch_capabilities", return_value={"permission": 0}
        )

    def test_core_appclient_supported_wallets_in_a_browser(self):
        assert supported_wallets(_request(BROWSER_UA)) == ALGORAND_WALLETS

    def test_core_appclient_supported_wallets_in_the_app(self):
        assert [w["id"] for w in supported_wallets(_request(IOS_UA))] == ["pera", "defly"]

    def test_core_appclient_wallets_api_in_the_app(self):
        response = Client(HTTP_USER_AGENT=ANDROID_UA).get("/api/v2/wallet/wallets/")

        assert [w["id"] for w in response.json()] == ["pera", "defly"]

    @pytest.mark.django_db
    def test_core_appclient_login_page_cards_in_the_app(self):
        html = (
            Client(HTTP_USER_AGENT=ANDROID_UA)
            .get(reverse("account_login"))
            .content.decode()
        )

        assert 'id="wallet-pera"' in html
        assert 'id="wallet-lute"' not in html
        assert 'id="wallet-kibisis"' not in html
        assert 'id="wallet-exodus"' not in html

    @pytest.mark.django_db
    def test_core_appclient_login_page_cards_in_a_browser(self):
        html = (
            Client(HTTP_USER_AGENT=BROWSER_UA)
            .get(reverse("account_login"))
            .content.decode()
        )

        assert 'id="wallet-lute"' in html


class TestCoreAppClientBaseTemplate:
    """base.html in app mode, and its cache entries kept apart from a browser's."""

    @pytest.fixture(autouse=True)
    def _capabilities(self, mocker):
        mocker.patch(
            "core.context_processors.fetch_capabilities", return_value={"permission": 0}
        )

    def _faq(self, user_agent):
        return Client(HTTP_USER_AGENT=user_agent).get(reverse("faq")).content.decode()

    def test_core_appclient_base_template_in_app_mode(self):
        html = self._faq(ANDROID_UA)

        assert '<html lang="en" class="in-app" data-app-platform="android">' in html
        assert "viewport-fit=cover" in html
        assert "env(safe-area-inset-top)" in html
        assert "/static/js/app.js" in html
        assert "apps.apple.com" not in html
        assert "play.google.com" not in html

    def test_core_appclient_404_page_in_app_mode(self):
        html = Client(HTTP_USER_AGENT=ANDROID_UA).get("/no/such/page/").content.decode()

        assert '<html lang="en" class="in-app" data-app-platform="android">' in html
        assert "/static/js/app.js" in html

    def test_core_appclient_404_page_in_a_browser(self):
        html = Client(HTTP_USER_AGENT=BROWSER_UA).get("/no/such/page/").content.decode()

        assert '<html lang="en">' in html
        assert "/static/js/app.js" not in html

    def test_core_appclient_base_template_in_a_browser(self):
        html = self._faq(BROWSER_UA)

        assert '<html lang="en">' in html
        assert "in-app" not in html
        assert "viewport-fit" not in html
        assert "safe-area-inset" not in html
        assert "/static/js/app.js" not in html
        assert "apps.apple.com" in html
        assert "play.google.com" in html

    def test_core_appclient_base_template_app_page_is_not_served_to_a_browser(self):
        assert "in-app" in self._faq(IOS_UA)

        assert "in-app" not in self._faq(BROWSER_UA)

    def test_core_appclient_base_template_browser_page_is_not_served_to_the_app(self):
        assert "in-app" not in self._faq(BROWSER_UA)

        assert 'data-app-platform="ios"' in self._faq(IOS_UA)
        assert 'data-app-platform="android"' in self._faq(ANDROID_UA)


PURCHASE_LINK_MARKERS = (
    "/subscriptions/",
    "subtopia.io",
    "app.pact.fi",
    "app.tinyman.org",
)


def _purchase_links(html):
    """Return the hrefs in `html` that lead towards buying."""
    import re

    return [
        href
        for href in re.findall(r'href="([^"]*)"', html)
        if any(marker in href for marker in PURCHASE_LINK_MARKERS)
    ]


class TestCoreAppClientPurchaseHidden:
    """Calls to buy or upgrade are not rendered for the app (F10)."""

    @pytest.fixture(autouse=True)
    def _capabilities(self, mocker):
        mocker.patch(
            "core.context_processors.fetch_capabilities", return_value={"permission": 0}
        )

    def _page(self, name, user_agent):
        return Client(HTTP_USER_AGENT=user_agent).get(reverse(name)).content.decode()

    def test_core_appclient_context_processor_purchase_hidden(self):
        from core.appclient import PURCHASE_HIDDEN_TEXT

        context = app_client_processor(_request(IOS_UA))

        assert context["PURCHASE_HIDDEN"] is True
        assert context["PURCHASE_HIDDEN_TEXT"] == PURCHASE_HIDDEN_TEXT
        assert app_client_processor(_request(BROWSER_UA))["PURCHASE_HIDDEN"] is False

    def test_core_appclient_main_navigation_drops_subscriptions_in_app(self):
        from django.contrib.auth.models import AnonymousUser

        from core.context_processors import MAIN_NAVIGATION_ANONYMOUS, main_navigation

        request = _request(ANDROID_UA)
        request.user = AnonymousUser()
        names = [name for name, _ in main_navigation(request)["main_navigation"]]

        assert "subscriptions" not in names
        assert len(names) == len(MAIN_NAVIGATION_ANONYMOUS) - 1

    @pytest.mark.parametrize("name", ["faq", "subscriptions", "about", "features"])
    def test_core_appclient_pages_have_no_purchase_links_in_app(self, name):
        assert _purchase_links(self._page(name, ANDROID_UA)) == []
        assert _purchase_links(self._page(name, IOS_UA)) == []

    @pytest.mark.parametrize("name", ["faq", "subscriptions"])
    def test_core_appclient_pages_keep_purchase_links_in_a_browser(self, name):
        assert _purchase_links(self._page(name, BROWSER_UA))

    def test_core_appclient_subscriptions_page_keeps_the_plans_in_app(self):
        html = self._page("subscriptions", IOS_UA)

        assert "Subscription Models" in html
        assert "How to Subscribe" not in html
        assert "SUBSCRIBE</a>" not in html

    def test_core_appclient_faq_hides_buying_and_upgrading_in_app(self):
        html = self._page("faq", IOS_UA)

        assert "Where can I buy ASASTATS?" not in html
        assert "Can I upgrade or cancel my subscription?" not in html
        assert "How are subscriptions handled?" in html

    @override_settings(APP_HIDE_PURCHASE=frozenset())
    def test_core_appclient_purchase_links_return_when_switched_off(self):
        assert _purchase_links(self._page("faq", ANDROID_UA))


@pytest.mark.django_db
class TestCoreAppClientPurchaseHiddenProfile:
    """The profile pages' locked-feature hints, without the upgrade links."""

    @pytest.fixture(autouse=True)
    def _capabilities(self, mocker):
        mocker.patch(
            "core.context_processors.fetch_capabilities", return_value={"permission": 0}
        )

    def _page(self, name, user_agent, django_user_model):
        user = django_user_model.objects.create_user(
            username=f"purchase-{name}-{len(user_agent)}", password="x"
        )
        client = Client(HTTP_USER_AGENT=user_agent)
        client.force_login(user)
        return client.get(reverse(name)).content.decode()

    @pytest.mark.parametrize(
        "name", ["profile_settings", "profile_appearance", "profile_account"]
    )
    def test_core_appclient_profile_pages_in_app(self, name, django_user_model):
        html = self._page(name, ANDROID_UA, django_user_model)

        assert _purchase_links(html) == []
        assert "Tap to upgrade" not in html

    def test_core_appclient_profile_settings_in_a_browser(self, django_user_model):
        html = self._page("profile_settings", BROWSER_UA, django_user_model)

        assert _purchase_links(html)
        assert "Tap to upgrade" in html


ADDRESS = "A" * 58
IOS_HIDES = {"ios": frozenset({"historic", "swapcore"}), "android": frozenset()}


class TestCoreAppClientHiddenWidgets:
    """Widgets switched off per platform answer 404 in the app (F11)."""

    @pytest.fixture(autouse=True)
    def _capabilities(self, mocker):
        mocker.patch(
            "core.context_processors.fetch_capabilities", return_value={"permission": 0}
        )

    def test_core_appclient_hidden_widgets_empty_for_a_browser(self):
        with override_settings(APP_HIDDEN_WIDGETS=IOS_HIDES):
            assert hidden_widgets(_request(BROWSER_UA)) == frozenset()

    def test_core_appclient_hidden_widgets_per_platform(self):
        with override_settings(APP_HIDDEN_WIDGETS=IOS_HIDES):
            assert hidden_widgets(_request(IOS_UA)) == {"historic", "swapcore"}
            assert hidden_widgets(_request(ANDROID_UA)) == frozenset()

    @override_settings(APP_HIDDEN_WIDGETS=IOS_HIDES)
    def test_core_appclient_hidden_widget_is_404_in_the_app(self):
        response = Client(HTTP_USER_AGENT=IOS_UA).get(f"/widgets/historic/{ADDRESS}")

        assert response.status_code == 404

    @override_settings(APP_HIDDEN_WIDGETS=IOS_HIDES)
    def test_core_appclient_every_path_of_a_hidden_widget_is_404(self):
        client = Client(HTTP_USER_AGENT=IOS_UA)

        assert client.get("/widgets/swapcore/anything/deeper").status_code == 404

    @override_settings(APP_HIDDEN_WIDGETS=IOS_HIDES)
    @pytest.mark.parametrize("user_agent", [ANDROID_UA, BROWSER_UA])
    def test_core_appclient_widget_is_served_elsewhere(self, user_agent):
        response = Client(HTTP_USER_AGENT=user_agent).get(f"/widgets/historic/{ADDRESS}")

        assert response.status_code != 404

    @override_settings(APP_HIDDEN_WIDGETS=IOS_HIDES)
    def test_core_appclient_other_widgets_are_served_in_the_app(self):
        response = Client(HTTP_USER_AGENT=IOS_UA).get(f"/widgets/pnl/{ADDRESS}")

        assert response.status_code != 404

    def test_core_appclient_middleware_ignores_non_widget_paths(self):
        from core.middleware import WIDGET_PATH_REGEX

        assert WIDGET_PATH_REGEX.match("/widgets/historic/x").group("name") == "historic"
        assert WIDGET_PATH_REGEX.match("/historic/widgets/x") is None


class TestCoreAppClientWidgetShownFilter:
    """Testing class for the fail-open :func:`core_extras.widget_shown` filter."""

    @override_settings(APP_HIDDEN_WIDGETS=IOS_HIDES)
    def test_core_extras_widget_shown(self):
        from core.templatetags.core_extras import widget_shown

        assert widget_shown(_request(IOS_UA), "swapcore") is False
        assert widget_shown(_request(IOS_UA), "pnl") is True
        assert widget_shown(_request(ANDROID_UA), "swapcore") is True
        assert widget_shown(_request(BROWSER_UA), "swapcore") is True

    @override_settings(APP_HIDDEN_WIDGETS=IOS_HIDES)
    @pytest.mark.parametrize("request_value", [None, ""])
    def test_core_extras_widget_shown_fails_open(self, request_value):
        from core.templatetags.core_extras import widget_shown

        assert widget_shown(request_value, "swapcore") is True
