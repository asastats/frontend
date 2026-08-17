"""Testing module for :py:mod:`core.context_processors` module."""

import re
from pathlib import Path
from unittest import mock

import pytest
from django.conf import settings
from django.urls import reverse

import core.context_processors
from api.client import BackendError
from core.context_processors import (
    deployment_capabilities,
    global_constants,
    load_typefaces,
    main_navigation,
    profile_navigation,
    walletconnect,
)
# The navigation lists live on the module, not in Django settings: they are
# structure rather than configuration, and nothing deploys differently.
from core import context_processors as settings_module


class TestCoreContextProcessors:
    """Testing class for :py:mod:`core.context_processors` functions."""

    # # load_typefaces
    #
    # The cache is a module global, so it is reset around every test here: a
    # value left behind would make the next test pass without reading anything.
    @pytest.fixture(autouse=True)
    def _reset_typeface_cache(self):
        core.context_processors._TYPEFACES_CACHE = None
        yield
        core.context_processors._TYPEFACES_CACHE = None

    def test_core_context_processors_load_typefaces_reads_the_build_output(
        self, mocker
    ):
        path = mocker.patch.object(core.context_processors, "_TYPEFACES_PATH")
        path.read_text.return_value = (
            '{"asastats": {"display": "Sora", "sans": "Inter", "mono": "Fira Code"}}'
        )

        result = load_typefaces()

        assert result == {
            "asastats": {"display": "Sora", "sans": "Inter", "mono": "Fira Code"}
        }

    def test_core_context_processors_load_typefaces_reads_once_per_process(
        self, mocker
    ):
        """Every request renders a page; re-reading the file on each is waste."""
        path = mocker.patch.object(core.context_processors, "_TYPEFACES_PATH")
        path.read_text.return_value = '{"asastats": {"sans": "Inter"}}'

        load_typefaces()
        load_typefaces()

        path.read_text.assert_called_once_with()

    def test_core_context_processors_load_typefaces_empty_when_file_is_missing(
        self, mocker
    ):
        """The file is build output, so a deployment can be missing it.

        Offering no typefaces costs a reader one setting; letting the OSError
        out of a context processor takes down every page on the site.
        """
        path = mocker.patch.object(core.context_processors, "_TYPEFACES_PATH")
        path.read_text.side_effect = FileNotFoundError("no such file")
        warning = mocker.patch("core.context_processors.logger.warning")

        result = load_typefaces()

        assert result == {}
        warning.assert_called_once_with("Could not read %s", path, exc_info=True)

    def test_core_context_processors_load_typefaces_empty_when_file_is_unreadable(
        self, mocker
    ):
        """A permission or device error is an OSError like any other."""
        path = mocker.patch.object(core.context_processors, "_TYPEFACES_PATH")
        path.read_text.side_effect = PermissionError("denied")
        warning = mocker.patch("core.context_processors.logger.warning")

        result = load_typefaces()

        assert result == {}
        warning.assert_called_once_with("Could not read %s", path, exc_info=True)

    def test_core_context_processors_load_typefaces_empty_when_json_is_invalid(
        self, mocker
    ):
        """A half-written file parses as far as the truncation, then raises.

        Fed real malformed text rather than a raised ValueError, so this also
        pins that `json.JSONDecodeError` is caught by the `ValueError` arm.
        """
        path = mocker.patch.object(core.context_processors, "_TYPEFACES_PATH")
        path.read_text.return_value = '{"asastats": {"sans": "Inte'
        warning = mocker.patch("core.context_processors.logger.warning")

        result = load_typefaces()

        assert result == {}
        warning.assert_called_once_with("Could not read %s", path, exc_info=True)

    def test_core_context_processors_load_typefaces_does_not_retry_after_failure(
        self, mocker
    ):
        """`{}` is not `None`, so the empty result is cached like any other.

        A file that failed to read once will not start reading mid-process,
        and retrying would put the failing read on every request instead.
        """
        path = mocker.patch.object(core.context_processors, "_TYPEFACES_PATH")
        path.read_text.side_effect = FileNotFoundError("no such file")
        mocker.patch("core.context_processors.logger.warning")

        load_typefaces()
        second = load_typefaces()

        assert second == {}
        path.read_text.assert_called_once_with()

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
            "AVAILABLE_THEMES_BY_SCHEME": settings.AVAILABLE_THEMES_BY_SCHEME,
            "DEFAULT_THEMES_BY_SCHEME": settings.DEFAULT_THEMES_BY_SCHEME,
            "RECENT_THEMES_SHOWN": settings.RECENT_THEMES_SHOWN,
            "BRAND_THEME_LIGHT": settings.BRAND_THEME_LIGHT,
            "BRAND_THEME_DARK": settings.BRAND_THEME_DARK,
            "THEME_ATTRIBUTION": settings.THEME_ATTRIBUTION,
        }

    # # main_navigation
    def test_core_context_processors_main_navigation_signed_in(self, mocker):
        request = mocker.MagicMock()
        request.user.is_authenticated = True

        assert main_navigation(request) == {
            "main_navigation": settings_module.MAIN_NAVIGATION_AUTHENTICATED
        }

    def test_core_context_processors_main_navigation_signed_out(self, mocker):
        request = mocker.MagicMock()
        request.user.is_authenticated = False

        assert main_navigation(request) == {
            "main_navigation": settings_module.MAIN_NAVIGATION_ANONYMOUS
        }

    def test_core_context_processors_main_navigation_without_a_user(self, mocker):
        """Context processors run on responses AuthenticationMiddleware missed.

        A 500 rendered from a request that never reached the middleware has no
        `request.user`, and a header that raises there replaces the error page
        with a second error. The signed-out list is the safe answer.
        """
        request = mocker.Mock(spec=[])

        assert main_navigation(request) == {
            "main_navigation": settings_module.MAIN_NAVIGATION_ANONYMOUS
        }

    @pytest.mark.parametrize(
        "entries",
        [
            settings_module.MAIN_NAVIGATION_AUTHENTICATED,
            settings_module.MAIN_NAVIGATION_ANONYMOUS,
        ],
    )
    def test_core_context_processors_main_navigation_entries_resolve(self, entries):
        """Every entry must be a real url name.

        The header reverses these, so a renamed or removed view turns the whole
        navigation into a NoReverseMatch on every page of the site -- including
        the error page. Cheap to assert, expensive to discover.
        """
        for url_name, label in entries:
            assert reverse(url_name), f"{url_name} does not reverse"
            assert label.strip(), f"{url_name} has an empty label"

    def test_core_context_processors_main_navigation_offers_no_way_out_to_a_guest(
        self, mocker
    ):
        """Log out on a page nobody is signed in to is a dead control."""
        request = mocker.MagicMock()
        request.user.is_authenticated = False

        labels = [label for _, label in main_navigation(request)["main_navigation"]]

        assert "Log out" not in labels

    # # profile_navigation
    def test_core_context_processors_profile_navigation_functionality(self, mocker):
        assert profile_navigation(mocker.MagicMock()) == {
            "profile_sections": settings_module.PROFILE_SECTIONS
        }

    def test_core_context_processors_profile_navigation_entries_resolve(self):
        for url_name, label in settings_module.PROFILE_SECTIONS:
            assert reverse(url_name), f"{url_name} does not reverse"
            assert label.strip(), f"{url_name} has an empty label"

    def test_core_context_processors_appearance_is_in_the_profile_nav(self):
        """The header's Customize link and the sub-nav must lead to one place.

        Two routes to the same page is fine; two different pages is not, and
        that is what a typo here would produce.
        """
        assert "profile_appearance" in [
            url_name for url_name, _ in settings_module.PROFILE_SECTIONS
        ]

    # # brand themes
    def test_core_context_processors_brand_themes_are_offered_and_built(self):
        """The signed-out switch flips between these two, so they must exist.

        A brand theme missing from AVAILABLE_THEMES would leave the switch
        applying a `data-theme` the stylesheet has no rule for -- an unstyled
        page, from a control that looks like it worked.
        """
        for theme in (settings.BRAND_THEME_LIGHT, settings.BRAND_THEME_DARK):
            assert theme in settings.AVAILABLE_THEMES, (
                f"{theme} is what the light/dark switch applies but it is not "
                "offered in AVAILABLE_THEMES"
            )

    def test_core_context_processors_brand_themes_are_one_of_each_scheme(self):
        """A switch between two themes of the same scheme would do nothing visible."""
        groups = settings.AVAILABLE_THEMES_BY_SCHEME
        assert settings.BRAND_THEME_LIGHT in groups["Light"], (
            f"{settings.BRAND_THEME_LIGHT} is used as the switch's light theme "
            "but is not grouped as one"
        )
        assert settings.BRAND_THEME_DARK in groups["Dark"], (
            f"{settings.BRAND_THEME_DARK} is used as the switch's dark theme "
            "but is not grouped as one"
        )

    # # AVAILABLE_THEMES
    def test_core_context_processors_every_offered_theme_is_built(self):
        """Every theme in the picker must exist in the compiled stylesheet.

        The theme list is declared twice by necessity -- Django renders the
        picker from settings, Tailwind builds the CSS from ``input.css`` -- and
        the two cannot import from each other. A theme offered but not built
        renders as an unstyled page, so the drift is caught here instead.
        """
        css_dir = Path(settings.STATICFILES_DIRS[0]) / "css"
        source = (css_dir / "input.css").read_text()
        # Vendored themes are registered in their own files under themes/ and
        # pulled in with `@import`, so the imports have to be followed -- a
        # theme is just as unbuilt if the file exists but nothing imports it.
        for relative in re.findall(r'@import\s+"([^"]+\.css)"', source):
            imported = (css_dir / relative).resolve()
            if imported.is_file():
                source += "\n" + imported.read_text()
        # Comments first: a `/* ... */` in the themes list fuses to the name
        # that follows it, which silently swallowed "light" when this was
        # written the other way round.
        source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
        # `themes: a, b, c;` inside the daisyui plugin block, plus each
        # `@plugin ".../daisyui-theme.mjs" { name: "x"; ... }` registration.
        listed = re.search(r"themes:(.*?);", source, re.S)
        built = {
            name.strip()
            for name in (listed.group(1) if listed else "").split(",")
            if name.strip()
        }
        built |= set(re.findall(r'name:\s*"([^"]+)"', source))

        assert set(settings.AVAILABLE_THEMES) <= built, (
            "offered in settings.AVAILABLE_THEMES but not registered in "
            f"input.css or an imported theme file: "
            f"{sorted(set(settings.AVAILABLE_THEMES) - built)}"
        )

    def test_core_context_processors_every_theme_is_in_the_right_group(self):
        """A theme must sit under the heading its own `color-scheme` declares.

        The picker groups by light and dark, and the grouping is hand-written
        in settings while the truth lives in each theme's CSS. Getting one
        wrong is not a crash -- a dark theme filed under Light simply looks
        wrong to whoever picks it -- so it is checked against the compiled
        stylesheet, which is where every theme, ours and stock and vendored
        alike, ends up declaring its scheme.
        """
        css = (
            Path(settings.STATICFILES_DIRS[0]) / "css" / "style.tw.css"
        ).read_text()
        declared = {}
        for match in re.finditer(
            r'\[data-theme=(?:"([^"]+)"|([\w-]+))\]\s*\{([^}]*)\}', css
        ):
            name = match.group(1) or match.group(2)
            scheme = re.search(r"color-scheme:\s*([a-z]+)", match.group(3))
            if scheme and name not in declared:
                declared[name] = scheme.group(1)

        assert declared, (
            "no themes found in style.tw.css -- has it been built? "
            "run ./build-tailwind.sh"
        )

        misfiled = {
            theme: (group, declared[theme])
            for group, themes in settings.AVAILABLE_THEMES_BY_SCHEME.items()
            for theme in themes
            if theme in declared and declared[theme] != group.lower()
        }
        assert not misfiled, (
            "themes grouped under the wrong heading in "
            "settings.AVAILABLE_THEMES_BY_SCHEME, as "
            "theme: (grouped as, actually declares) -- "
            f"{misfiled}"
        )

    def test_core_context_processors_theme_groups_have_no_duplicates(self):
        """Guard the guard: the flat list is derived from the groups.

        A theme listed in both groups would render twice in the picker and
        would make every count-based assertion here quietly meaningless.
        """
        flat = settings.AVAILABLE_THEMES
        assert len(flat) == len(set(flat)), (
            "a theme appears in more than one group: "
            f"{sorted({t for t in flat if flat.count(t) > 1})}"
        )

    def test_core_context_processors_attributed_themes_are_offered(self):
        """Every theme we credit must actually be one we ship.

        The attribution is a licence condition, so it has to describe reality:
        crediting a theme that was deleted is misleading, and shipping one of
        theirs without listing it here means the picker never credits it.
        """
        attributed = set(settings.THEME_ATTRIBUTION["themes"])
        offered = set(settings.AVAILABLE_THEMES)

        assert attributed <= offered, (
            "credited in settings.THEME_ATTRIBUTION but no longer offered: "
            f"{sorted(attributed - offered)}"
        )

    def test_core_context_processors_cc_by_themes_are_credited(self):
        """Credit exactly the themes whose licence demands it -- no more.

        Two licences are vendored under static/css/themes/. CC BY 4.0 requires
        the author, source and licence be named where a reader can see them,
        which is what THEME_ATTRIBUTION drives. MIT does not: it is satisfied by
        the copyright notice kept at the top of the file, and crediting an MIT
        theme in the picker would tell a reader something untrue about who is
        owed what.

        Keyed on each file's own banner rather than a list repeated here,
        because the banner is the notice the licence is about -- deleting it to
        make this test pass would be the actual violation.
        """
        attributed = set(settings.THEME_ATTRIBUTION["themes"])
        theme_dir = Path(settings.STATICFILES_DIRS[0]) / "css" / "themes"

        cc_by, mit, unlabelled = set(), set(), set()
        for path in theme_dir.glob("*.css"):
            banner = path.read_text()[:600].upper()
            if "CC BY" in banner:
                cc_by.add(path.stem)
            elif "MIT" in banner:
                mit.add(path.stem)
            else:
                unlabelled.add(path.stem)

        assert not unlabelled, (
            "vendored theme with no licence in its banner -- add the upstream "
            f"notice rather than dropping it: {sorted(unlabelled)}"
        )
        assert cc_by <= attributed, (
            "CC BY 4.0 and vendored, but not credited in "
            f"settings.THEME_ATTRIBUTION: {sorted(cc_by - attributed)}"
        )
        assert not (mit & attributed), (
            "MIT themes need no interface credit, so listing them overstates "
            f"the obligation: {sorted(mit & attributed)}"
        )

    # # dropdown defaults
    def test_core_context_processors_default_themes_are_offered(self):
        """A default that is not in the full set renders an unstyled page.

        The dropdown's twelve are a subset of the appearance page's, not a
        second list -- nothing may appear here that a reader cannot also find
        on the page the dropdown links to.
        """
        missing = set(settings.DEFAULT_THEMES) - set(settings.AVAILABLE_THEMES)

        assert not missing, f"offered in the dropdown but nowhere else: {sorted(missing)}"

    def test_core_context_processors_default_themes_keep_their_scheme(self):
        """A dark theme under the Light heading is a mislabelled menu."""
        for scheme, themes in settings.DEFAULT_THEMES_BY_SCHEME.items():
            for theme in themes:
                assert theme in settings.AVAILABLE_THEMES_BY_SCHEME[scheme], (
                    f"{theme} is listed under {scheme} in the dropdown but not "
                    "on the appearance page"
                )

    def test_core_context_processors_default_themes_lead_with_ours(self):
        """Ours is the default and the one most readers will want back."""
        assert settings.DEFAULT_THEMES_BY_SCHEME["Light"][0] == settings.BRAND_THEME_LIGHT
        assert settings.DEFAULT_THEMES_BY_SCHEME["Dark"][0] == settings.BRAND_THEME_DARK

    def test_core_context_processors_default_themes_are_balanced(self):
        """Neither scheme should look better served than the other."""
        light = settings.DEFAULT_THEMES_BY_SCHEME["Light"]
        dark = settings.DEFAULT_THEMES_BY_SCHEME["Dark"]

        assert len(light) == len(dark), "the dropdown favours one scheme"

    def test_core_context_processors_default_themes_are_not_duplicated(self):
        flat = settings.DEFAULT_THEMES

        assert len(flat) == len(set(flat)), (
            "a theme is offered twice in the dropdown, which renders it as two "
            f"radios sharing a value: {sorted({t for t in flat if flat.count(t) > 1})}"
        )

    def test_core_context_processors_recent_shown_leaves_room_for_the_rest(self):
        """Recent is a nudge, not a replacement for the list underneath it."""
        assert 0 < settings.RECENT_THEMES_SHOWN < len(settings.DEFAULT_THEMES)

    # # walletconnect
    def test_core_context_processors_walletconnect_functionality(self, mocker):
        settings = mocker.MagicMock()
        project_id = "PROJECTID"
        settings.WALLET_CONNECT_PROJECT_ID = project_id
        with mock.patch.object(core.context_processors, "settings", settings):
            result = walletconnect(mocker.Mock())
        assert result == {"WALLET_CONNECT_PROJECT_ID": project_id}
