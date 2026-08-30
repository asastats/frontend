"""The social login providers, tested on our side of the redirect.

**This replaces a Selenium test that drove Google's and Twitter's own login
pages.** That test was skipped from the day it was written, with the note "test
passed and skipped in early development phase", and by the time anyone looked
at it again it could not have run for four independent reasons: it looked for
element ids (`google_login`) no template has ever rendered; it used the
provider id `twitter`, which became `twitter_oauth2`; it typed into Google's
`Email` / `Passwd` / `signIn` fields, which have not existed for years and
which Google now refuses to serve to an automated browser at all; and it read
credentials from `settings.FIXTURE_DIRS[0]`, a setting this project does not
define. Nothing about it was recoverable.

The deeper problem was what it was aiming at. Driving a provider's login form
tests the *provider*: it needs real credentials, it makes real network calls,
it breaks whenever Google restyles a page, and a failure says nothing about
this codebase. Everything worth pinning is on our side of the redirect, and all
of it can be checked without a browser or a network:

* the URLs in the template resolve at all -- which is exactly the class of
  breakage the dead `twitter` id was an instance of;
* each provider sends the user to the host we think it does;
* the callback comes back to us rather than to somewhere else;
* the failure paths render our templates rather than a stack trace.

The browser half -- that the five buttons are on the page and point at these
URLs -- is already covered by
`functional_tests/test_auth_pages.py::test_every_social_provider_is_offered`,
so it is not repeated here.

No credentials, no network, no browser.
"""

import re

import pytest
from django.conf import settings
from django.urls import reverse

#: Where each configured provider is expected to send the user.
#:
#: Hardcoded on purpose: reading it back out of the same adapter that builds
#: the redirect would assert that allauth agrees with itself. These are the
#: hosts a user's browser actually lands on, so a provider swapping its
#: endpoint -- Twitter's move to `x.com` being the recent one -- shows up as a
#: failure here rather than as a support ticket.
AUTHORIZE_URLS = {
    "discord": "https://discord.com/api/oauth2/authorize",
    "github": "https://github.com/login/oauth/authorize",
    "google": "https://accounts.google.com/o/oauth2/v2/auth",
    "reddit": "https://www.reddit.com/api/v1/authorize",
    "twitter_oauth2": "https://x.com/i/oauth2/authorize",
}

#: `<a id="id_..." href="...">` as `base_auth.html` writes it.
PROVIDER_LINK = re.compile(r'id="id_(\w+)"\s+href="(/accounts/[^"]+)"')


def _installed_providers():
    """Return the provider ids allauth is configured with.

    Derived from `INSTALLED_APPS` rather than listed, so a provider added to
    the project without a button, or a button left behind after a provider is
    removed, is a failure rather than a silence.

    :return: set
    """
    prefix = "allauth.socialaccount.providers."
    return {
        app[len(prefix) :]
        for app in settings.INSTALLED_APPS
        if app.startswith(prefix)
    }


def _template_links(client):
    """Return `{provider id: href}` for the buttons the login page renders.

    :param client: Django test client
    :type client: :class:`django.test.Client`
    :return: dict
    """
    page = client.get(reverse("account_login"))
    assert page.status_code == 200
    return {
        href.split("/")[2]: href
        for _, href in PROVIDER_LINK.findall(page.content.decode())
    }


@pytest.mark.django_db
class TestCoreAllauthProviders:
    """Testing class for the configured social login providers."""

    def test_core_allauth_every_installed_provider_has_a_button(self, client):
        """The buttons in `base_auth.html` carry literal hrefs.

        Nothing generates them from the provider list, so adding a provider to
        `INSTALLED_APPS` does not add a button and removing one does not take
        it away. Comparing the two sets is the only thing that notices.
        """
        assert _installed_providers() == set(_template_links(client))

    def test_core_allauth_the_expected_hosts_are_the_installed_ones(self):
        """Guards this module against the project changing under it."""
        assert set(AUTHORIZE_URLS) == _installed_providers()

    @pytest.mark.parametrize("provider", sorted(AUTHORIZE_URLS))
    def test_core_allauth_login_url_resolves(self, client, provider):
        """The literal href in the template reaches a view.

        This is the check the old test could never make and the one that would
        have caught its own bug: `twitter` became `twitter_oauth2`, and a
        template still pointing at the old id serves a 404 to anyone who
        clicks it.
        """
        response = client.get(f"/accounts/{provider}/login/")

        assert response.status_code == 200, (
            f"/accounts/{provider}/login/ does not resolve"
        )

    @pytest.mark.parametrize("provider", sorted(AUTHORIZE_URLS))
    def test_core_allauth_login_redirects_to_the_provider(self, client, provider):
        """A POST hands the user to the provider's authorization endpoint."""
        response = client.post(f"/accounts/{provider}/login/")

        assert response.status_code == 302
        assert response.headers["Location"].startswith(AUTHORIZE_URLS[provider]), (
            f"{provider} sends the user to {response.headers['Location'][:60]}"
        )

    @pytest.mark.parametrize("provider", sorted(AUTHORIZE_URLS))
    def test_core_allauth_the_provider_is_told_to_come_back_to_us(
        self, client, provider
    ):
        """The `redirect_uri` is where the provider returns the user.

        Worth its own assertion because it is the one parameter in that URL
        whose value is ours rather than the provider's, and a wrong one sends
        an authenticated user somewhere else entirely.
        """
        response = client.post(f"/accounts/{provider}/login/")
        location = response.headers["Location"]

        assert (
            f"redirect_uri=http%3A%2F%2Ftestserver%2Faccounts%2F{provider}"
            "%2Flogin%2Fcallback%2F" in location
        ), f"{provider} does not name our own callback as its redirect_uri"

    @pytest.mark.parametrize("provider", sorted(AUTHORIZE_URLS))
    def test_core_allauth_a_get_does_not_start_the_flow(self, client, provider):
        """`SOCIALACCOUNT_LOGIN_ON_GET` is left at its default of False.

        So the anchor in the template lands on allauth's confirmation page and
        the redirect happens on the POST from there. That is one extra click
        for the reader, and it is deliberate: a plain link that begins an
        OAuth flow can be triggered from anywhere, including an image tag on
        somebody else's site.

        Pinned because the setting is absent rather than written down, and an
        absent setting is easy to "add" without realising it changes this.
        """
        assert not getattr(settings, "SOCIALACCOUNT_LOGIN_ON_GET", False)

        response = client.get(f"/accounts/{provider}/login/")

        assert response.status_code == 200
        assert "Location" not in response.headers


@pytest.mark.django_db
class TestCoreAllauthCallbackFailures:
    """What a reader sees when the provider does not send them back happy.

    These are the paths a user actually hits -- declining the consent screen is
    ordinary -- and neither had a test. Both render our own templates, which
    means both are also the only chance to keep those templates compiling.
    """

    @pytest.mark.parametrize("provider", sorted(AUTHORIZE_URLS))
    def test_core_allauth_a_declined_consent_screen_is_handled(
        self, client, provider
    ):
        response = client.get(
            f"/accounts/{provider}/login/callback/?error=access_denied"
        )

        assert response.status_code == 401
        assert "socialaccount/authentication_error.html" in [
            template.name for template in response.templates if template.name
        ]

    def test_core_allauth_a_callback_with_no_code_is_handled(self, client):
        """A bare callback URL -- a stale bookmark, or a probe."""
        response = client.get("/accounts/google/login/callback/")

        assert response.status_code == 401
        assert "socialaccount/authentication_error.html" in [
            template.name for template in response.templates if template.name
        ]

    def test_core_allauth_the_error_page_renders_our_chrome(self, client):
        """It extends `socialaccount/base.html`, so a broken base takes the
        error page down with it -- and an error page that errors is the one
        failure nobody sees until a user reports a blank screen."""
        response = client.get("/accounts/google/login/callback/?error=access_denied")
        names = [template.name for template in response.templates if template.name]

        assert "socialaccount/base.html" in names
        assert response.content
