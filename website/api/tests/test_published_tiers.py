"""The published tier table must match what the code actually does.

**This is the failure `api/tiers.py` was already written against.** Its own
docstring records a `block_time` flag that sat in the band table read by nothing
and asserted by a test, and calls that "how a later change comes to be written
against a promise the code never kept". A number printed in the API
documentation is the same hazard aimed at customers instead of at us: nothing
in a docstring or a Swagger page fails when the limit beneath it moves.

So every number in the published table is parsed back out of the rendered
description here and checked against the function that enforces it.
"""

import re

import pytest

from api.tiers import block_time, max_addresses
from utils.constants.apiv2 import SPECTACULAR_DESCRIPTION
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from widgets.inhouse.liverefresh import warmset
from widgets.inhouse.liverefresh.manifest import MANIFEST

#: One row of the published table: tier, per-request cap, freshness, warm cap.
ROW = re.compile(
    r"^\| (Asastatser|Professional|Cluster) \| (\d+) \| ([^|]+?) \| ([^|]+?) \|$",
    re.MULTILINE,
)


def published_rows():
    """Return the table as the API documentation actually renders it."""
    return {
        match.group(1): {
            "addresses": int(match.group(2)),
            "freshness": match.group(3).strip(),
            "warm": match.group(4).strip(),
        }
        for match in ROW.finditer(SPECTACULAR_DESCRIPTION)
    }


class TestPublishedTierTable:
    """The table at `/api/v2/schema/swagger-ui/`, checked against the code."""

    def test_api_published_table_has_a_row_for_every_paid_tier(self):
        """A tier that can reach the API and is not in the table is a customer
        who has to guess."""
        assert set(published_rows()) == {"Asastatser", "Professional", "Cluster"}

    @pytest.mark.parametrize("tier", ["Asastatser", "Professional", "Cluster"])
    def test_api_published_addresses_match_what_is_enforced(self, tier):
        """**The number in the docs is the number in the refusal.**

        `enforce_address_limit` tells a caller "your subscription allows 5".
        Until this table existed nothing had ever told them 5, and if the two
        drift the documentation becomes worse than silence.
        """
        assert published_rows()[tier]["addresses"] == max_addresses(
            SUBSCRIPTION_TIER_PERMISSIONS[tier]
        )

    @pytest.mark.parametrize("tier", ["Asastatser", "Professional", "Cluster"])
    def test_api_published_freshness_matches_the_band(self, tier):
        """Block-time is sold here and gated in `api/tiers.py`; the two have to
        agree or we are advertising something we refuse to serve."""
        row = published_rows()[tier]
        claims_block_time = "block-time" in row["freshness"]

        assert claims_block_time is block_time(SUBSCRIPTION_TIER_PERMISSIONS[tier])

    @pytest.mark.parametrize("tier", ["Professional", "Cluster"])
    def test_api_published_warm_cap_matches_the_widget_bands(self, tier):
        """**The cap comes from the widget manifest, not from a second list.**

        One warm set per reader spans browser and API, so the number published
        to an API customer is the same number a browser tab spends. A table
        carrying its own copy would drift the first time a tier moved.
        """
        cap = warmset.cap_for(
            SUBSCRIPTION_TIER_PERMISSIONS[tier], MANIFEST.required_permission
        )

        assert published_rows()[tier]["warm"] == str(cap)

    def test_api_published_asastatser_claims_no_warm_addresses(self):
        """It never subscribes, so a number here would promise something the
        tier does not buy."""
        assert published_rows()["Asastatser"]["warm"] == "&mdash;"

    def test_api_published_description_names_the_warm_header(self):
        """A header no documentation mentions is one no caller will look for,
        and this one is how they tell whether they are getting what they pay
        for."""
        assert "X-ASAStats-Warm" in SPECTACULAR_DESCRIPTION

    def test_api_published_description_recommends_a_poll_rate(self):
        """The whole point of the section: without it, a customer paying for
        block-time data will reasonably assume they should poll every block."""
        assert "polling every 10 to 60 seconds" in SPECTACULAR_DESCRIPTION
