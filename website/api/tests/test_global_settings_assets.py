"""The paths API_GLOBAL_SETTINGS hands the mobile app must exist.

``SettingsView`` returns ``API_GLOBAL_SETTINGS`` verbatim, and the app joins
``providers.path`` onto the site url to fetch a provider's icon. Nothing on the
server ever follows that path, so when the directory it names went missing the
only symptom was missing icons inside a shipped app -- no exception, no log
line, and no failing test. It stayed that way for some time.

The website is no help as an early warning either: its templates resolve
provider icons through ``provider_icon``, which points at the CDN, so the site
looked perfectly healthy throughout.

These tests follow the path for real, against the same finders
``collectstatic`` uses, so a directory that stops shipping fails here instead
of on someone's phone.
"""

import pytest
from django.contrib.staticfiles import finders

from utils.constants.api import API_GLOBAL_SETTINGS

#: Provider icons the code can actually ask for. `provider_icon` derives the
#: filename from engine-supplied provider names, so this cannot be exhaustive
#: -- it is every name the filter is known to produce, from
#: test_templatetags.py, plus the two namespace providers index.html renders.
KNOWN_PROVIDERS = [
    "anote",
    "ans",
    "coinmarketcap",
    "dexscreener",
    "haystack",
    "livecoinwatch",
    "lofty",
    "nfd",
    "vestige",
]


class TestGlobalSettingsAssets:
    """Testing class for asset paths published through the settings endpoint."""

    def test_api_providers_path_is_published(self):
        """Guard the guard: a renamed key would make the rest vacuous."""
        assert API_GLOBAL_SETTINGS["providers"]["path"], (
            "API_GLOBAL_SETTINGS no longer publishes providers.path -- if the "
            "app stopped needing it, delete this module and "
            "static/icons/providers/ with it"
        )

    def test_api_providers_path_resolves_to_a_real_directory(self):
        """The published path must name something collectstatic ships."""
        path = API_GLOBAL_SETTINGS["providers"]["path"]
        prefix = path.removeprefix("static/").rstrip("/")
        found = finders.find(prefix)
        assert found, (
            f"API_GLOBAL_SETTINGS publishes {path!r} to the mobile app, but "
            "no static directory answers it. Every provider icon the app "
            "requests is a 404, and nothing server-side notices -- the "
            "website reads its own icons from the CDN instead."
        )

    @pytest.mark.parametrize("provider", KNOWN_PROVIDERS)
    def test_api_provider_icon_ships(self, provider):
        """`provider` must have an icon under the published path.

        :param provider: icon basename `provider_icon` can produce
        :type provider: str
        """
        path = API_GLOBAL_SETTINGS["providers"]["path"]
        prefix = path.removeprefix("static/").rstrip("/")
        assert finders.find(f"{prefix}/{provider}.png"), (
            f"{provider}.png is missing from {path}. `provider_icon` can "
            "produce that name, so the app will ask for it and get a 404. "
            "These files are a second copy of what the CDN serves the "
            "website; the two have to be kept in step while the legacy app "
            "lives."
        )
