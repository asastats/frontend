"""Testing module for :py:mod:`api.tiers` module."""

import pytest

from api.tiers import (
    API_TIER_BANDS,
    DEFAULT_BAND,
    band_for,
    block_time,
    max_addresses,
)
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS as TIERS


class TestApiTiers:
    """What each tier may ask of the API.

    **These are not the website's numbers, and that is the point.** The
    `liverefresh` widget bands how many addresses a reader may *watch* at 1/1/5/20,
    which is a different product sharing the tier names. This project has already
    conflated the two twice - once in the widget runbook, once in
    `live/API-TIERS.md` - so the two tables are pinned apart here rather than
    left to be noticed.
    """

    @pytest.mark.parametrize(
        "tier,addresses",
        (("Cluster", 20), ("Professional", 5), ("Asastatser", 5)),
    )
    def test_api_tiers_band_by_name(self, tier, addresses):
        assert band_for(TIERS[tier])["addresses"] == addresses

    def test_api_tiers_the_table_claims_nothing_it_does_not_do(self):
        """**Every key here must be read by something.**

        `block_time` sat in this table once, read by nothing and asserted by a
        test, which is how a later change comes to be written against a promise
        the code never kept. It was removed, and the rule was that it returns
        when the promise is kept. It is kept now - engine `d5e318c` publishes a
        snapshot per block and `api.live` asks for it and serves it - so the
        flag is back, and this test's job changes from "it must not be here" to
        "nothing may be here that no one reads".

        A new key added to a band without a reader fails this, which is the
        original protection aimed at the thing it was really about.
        """
        served = {"addresses": max_addresses, "block_time": block_time}
        for _, band in API_TIER_BANDS:
            assert set(band) == set(served)
        assert set(DEFAULT_BAND) == set(served)
        for name, reader in served.items():
            assert reader(TIERS["Cluster"]) == API_TIER_BANDS[0][1][name]

    @pytest.mark.parametrize(
        "tier,expected",
        (
            ("Cluster", True),
            ("Professional", True),
            ("Asastatser", False),
            ("Intro", False),
        ),
    )
    def test_api_tiers_block_time_by_name(self, tier, expected):
        """**Asastatser has five addresses and no freshness.**

        Professional's entire advantage over it is block-time data - recorded
        in `post-deploy/DECIDED.md` as deliberate rather than an oversight -
        so this is the line that makes the two tiers different at all.
        """
        assert block_time(TIERS[tier]) is expected

    def test_api_tiers_block_time_is_false_below_every_band(self):
        """The shadow-mode caller gets the cached path, like everyone unpaid."""
        assert block_time(0) is False
        assert block_time(-1) is False

    def test_api_tiers_a_tier_between_bands_takes_the_one_below(self):
        """Permissions are thresholds, not identities: an account a point above
        Professional is a Professional, not an error."""
        assert max_addresses(TIERS["Professional"] + 1) == 5

    def test_api_tiers_below_asastatser_falls_to_the_default(self):
        """**Only reachable while the gate is shadowing.** An unentitled caller
        is let through and still needs an answer, and one address is the honest
        one - they are not paying for a bundle, and shadow mode exists to show
        what enforcement would do rather than to hand out entitlements meanwhile.
        """
        assert band_for(TIERS["Intro"]) == DEFAULT_BAND
        assert band_for(0) == DEFAULT_BAND
        assert max_addresses(0) == 1

    def test_api_tiers_a_negative_permission_gets_the_default(self):
        """A corrupt profile row must not read as the richest band."""
        assert max_addresses(-1) == 1

    def test_api_tiers_the_bands_do_not_track_the_widget(self):
        """**The two tables must be able to move independently.**

        The widget gives Asastatser one address to watch; the API gives it five
        to ask about. If a later edit ever makes these equal by copying one into
        the other, this fails and says why.
        """
        from widgets.inhouse.liverefresh.manifest import MANIFEST

        widget_asastatser = max(
            band["max_addresses"]
            for band in MANIFEST.required_permission
            if band["permission"] <= TIERS["Asastatser"]
        )

        assert widget_asastatser == 1
        assert max_addresses(TIERS["Asastatser"]) == 5


class TestApiTierAddressLimit:
    """The limit as it behaves in a request, rather than as a table."""

    def _request(self, mocker, permission):
        request = mocker.MagicMock()
        request.user.profile.permission = permission
        request.path = "/api/v2/HASH/"
        return request

    def test_api_tiers_shadowing_reports_and_serves(self, mocker, settings):
        """**The switch has to mean one thing.** A limit refusing while the
        permission gate was only observing would make API_TIER_ENFORCED a
        half-truth, and the log written to answer "who breaks?" would be missing
        everyone the address cap had already turned away."""
        from api.tiers import enforce_address_limit

        settings.API_TIER_ENFORCED = False
        logged = mocker.patch("api.tiers.logger")

        enforce_address_limit(
            self._request(mocker, TIERS["Asastatser"]),
            " ".join("A" * 58 for _ in range(7)),
        )

        assert logged.warning.called
        reported = logged.warning.call_args.args
        assert 7 in reported and 5 in reported

    def test_api_tiers_enforcing_refuses_and_names_both_numbers(self, mocker, settings):
        """ "Too many addresses" sends a subscriber to a support thread; the
        counts let them act without one."""
        from rest_framework.exceptions import ValidationError

        from api.tiers import enforce_address_limit

        settings.API_TIER_ENFORCED = True

        with pytest.raises(ValidationError) as raised:
            enforce_address_limit(
                self._request(mocker, TIERS["Asastatser"]),
                " ".join("A" * 58 for _ in range(7)),
            )

        assert "7" in str(raised.value) and "5" in str(raised.value)

    def test_api_tiers_a_bundle_within_the_band_passes_silently(self, mocker, settings):
        from api.tiers import enforce_address_limit

        settings.API_TIER_ENFORCED = True
        logged = mocker.patch("api.tiers.logger")

        enforce_address_limit(
            self._request(mocker, TIERS["Asastatser"]),
            " ".join("A" * 58 for _ in range(3)),
        )

        assert not logged.warning.called

    def test_api_tiers_a_request_with_no_user_does_not_raise_attributeerror(
        self, mocker, settings
    ):
        """**A tier limit must not be what turns a missing user into a 500.**

        `request.user` is absent entirely on a bare WSGIRequest - no
        authentication middleware has run - and this reached for it directly
        until a unit test caught it. Absent reads as no entitlement, which the
        permission gate has already acted on.
        """
        from api.tiers import enforce_address_limit

        settings.API_TIER_ENFORCED = False
        bare = mocker.MagicMock(spec=[])

        enforce_address_limit(bare, " ".join("A" * 58 for _ in range(3)))
