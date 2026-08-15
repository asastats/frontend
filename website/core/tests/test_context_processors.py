"""Testing module for :py:mod:`core.context_processors` module."""

import re
from pathlib import Path
from unittest import mock

from django.conf import settings

import core.context_processors
from api.client import BackendError
from core.context_processors import (
    deployment_capabilities,
    global_constants,
    walletconnect,
)


class TestCoreContextProcessors:
    """Testing class for :py:mod:`core.context_processors` functions."""

    # # deployment_capabilities
    def test_core_context_processors_deployment_capabilities_returns_cached_value(
        self, mocker
    ):
        cache = mocker.patch("core.context_processors.cache")
        cache.get.return_value = {"permission": 5}
        fetch = mocker.patch("core.context_processors.fetch_capabilities")
        result = deployment_capabilities(mocker.Mock())
        assert result == {"deployment_capabilities": {"permission": 5}}
        fetch.assert_not_called()
        cache.set.assert_not_called()

    def test_core_context_processors_deployment_capabilities_fetches_and_caches_on_miss(
        self, mocker
    ):
        cache = mocker.patch("core.context_processors.cache")
        cache.get.return_value = None
        fetch = mocker.patch(
            "core.context_processors.fetch_capabilities",
            return_value={"permission": 3},
        )
        result = deployment_capabilities(mocker.Mock())
        assert result == {"deployment_capabilities": {"permission": 3}}
        fetch.assert_called_once_with()
        cache.set.assert_called_once_with(
            "deployment_capabilities", {"permission": 3}, 300
        )

    def test_core_context_processors_deployment_capabilities_stub_on_backend_error(
        self, mocker
    ):
        cache = mocker.patch("core.context_processors.cache")
        cache.get.return_value = None
        mocker.patch(
            "core.context_processors.fetch_capabilities",
            side_effect=BackendError("backend down"),
        )
        warning = mocker.patch("core.context_processors.logger.warning")
        result = deployment_capabilities(mocker.Mock())
        assert result == {"deployment_capabilities": {"permission": 0}}
        cache.set.assert_called_once_with(
            "deployment_capabilities", {"permission": 0}, 300
        )
        warning.assert_called_once_with(
            "Could not fetch deployment capabilities", exc_info=True
        )

    def test_core_context_processors_deployment_capabilities_stub_on_unexpected_error(
        self, mocker
    ):
        cache = mocker.patch("core.context_processors.cache")
        cache.get.return_value = None
        mocker.patch(
            "core.context_processors.fetch_capabilities",
            side_effect=ValueError("unexpected"),
        )
        warning = mocker.patch("core.context_processors.logger.warning")
        result = deployment_capabilities(mocker.Mock())
        assert result == {"deployment_capabilities": {"permission": 0}}
        cache.set.assert_called_once_with(
            "deployment_capabilities", {"permission": 0}, 300
        )
        warning.assert_called_once_with(
            "Could not fetch deployment capabilities", exc_info=True
        )

    # # global_constants
    def test_core_context_processors_global_constants_functionality(self, mocker):
        returned = global_constants(mocker.MagicMock())
        assert returned == {
            "WEBSITE_SHORT_NAME": settings.WEBSITE_SHORT_NAME,
            "WEBSITE_NAME": settings.WEBSITE_NAME,
            "WEBSITE_URL": settings.WEBSITE_URL,
            "WEBSITE_DOMAIN": settings.WEBSITE_DOMAIN,
            "BASE_CDN_URL": settings.BASE_CDN_URL,
            "X_HANDLE": settings.X_HANDLE,
            "SUBREDDIT_NAME": settings.SUBREDDIT_NAME,
            "ANDROID_APP": settings.ANDROID_APP,
            "IOS_APP": settings.IOS_APP,
            "MEDIUM_NAME": settings.MEDIUM_NAME,
            "DISCORD_INVITE": settings.DISCORD_INVITE,
            "GITHUB_ORGANIZATION": settings.GITHUB_ORGANIZATION,
            "AVAILABLE_THEMES": settings.AVAILABLE_THEMES,
        }

    # # AVAILABLE_THEMES
    def test_core_context_processors_every_offered_theme_is_built(self):
        """Every theme in the picker must exist in the compiled stylesheet.

        The theme list is declared twice by necessity -- Django renders the
        picker from settings, Tailwind builds the CSS from ``input.css`` -- and
        the two cannot import from each other. A theme offered but not built
        renders as an unstyled page, so the drift is caught here instead.
        """
        source = (
            Path(settings.STATICFILES_DIRS[0]) / "css" / "input.css"
        ).read_text()
        # Comments first: a `/* ... */` in the themes list fuses to the name
        # that follows it, which silently swallowed "light" when this was
        # written the other way round.
        source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
        # `themes: a, b, c;` inside the daisyui plugin block, plus each
        # `@plugin "./daisyui-theme.mjs" { name: "x"; ... }` registration.
        listed = re.search(r"themes:(.*?);", source, re.S)
        built = {
            name.strip()
            for name in (listed.group(1) if listed else "").split(",")
            if name.strip()
        }
        built |= set(re.findall(r'name:\s*"([^"]+)"', source))

        assert set(settings.AVAILABLE_THEMES) <= built, (
            "offered in settings.AVAILABLE_THEMES but not registered in "
            f"input.css: {sorted(set(settings.AVAILABLE_THEMES) - built)}"
        )

    # # walletconnect
    def test_core_context_processors_walletconnect_functionality(self, mocker):
        settings = mocker.MagicMock()
        project_id = "PROJECTID"
        settings.WALLET_CONNECT_PROJECT_ID = project_id
        with mock.patch.object(core.context_processors, "settings", settings):
            result = walletconnect(mocker.Mock())
        assert result == {"WALLET_CONNECT_PROJECT_ID": project_id}
