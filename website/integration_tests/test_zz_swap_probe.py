from django.test import TestCase

from api.client import fetch_account_holdings, fetch_asset_matches
from widgets.inhouse.swapcore.manifest import MANIFEST

LIGHT = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M"


class SwapProbe(TestCase):
    def test_probe(self):
        h = fetch_account_holdings(LIGHT, MANIFEST.engine_endpoints)
        print("\n  holdings type:", type(h).__name__, "| count:", len(h))
        items = list(h.items())[:3]
        for k, v in items:
            print(f"    key={k!r} ({type(k).__name__}) -> {v}")
        print("  has '0':", "0" in h, "| has 0:", 0 in h)
        m = fetch_asset_matches("USDC", MANIFEST.engine_endpoints)
        print("  matches type:", type(m).__name__, "| count:", len(m))
        print("  first match:", m[0] if m else None)
        print("  scopes:", MANIFEST.engine_endpoints)
