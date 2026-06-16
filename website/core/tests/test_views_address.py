"""Tests for :class:`core.views.BaseAddressView` after the Phase 1 refactor.

These tests cover the website's address-page view now that it consumes the
API 2.0 serialized payload via :func:`api.main.fetch_and_serialize_account`
instead of building presentation context from scratch.

Conventions follow :py:mod:`api.tests.test_views`: instantiate the view by
hand, set ``request`` / ``args`` / ``kwargs`` directly, and patch every
collaborator the method talks to. We're testing the view's *wiring*, not the
helpers it composes (those are covered by their own test modules).

Two cross-cutting invariants worth calling out:

* **No legacy context keys.** ``asas``, ``values``, ``nft_values``,
  ``total``, ``online``, ``points``, ``warning``, ``information`` must not
  appear in the rendered context. A dedicated test asserts this so a future
  half-revert doesn't sneak the old keys back.
* **One bundle-lookup per request.** ``dispatch`` resolves the bundle and
  stashes it on ``self``; ``get_context_data`` reads from ``self.addresses``
  rather than calling :func:`check_bundle_addresses` again. The legacy view
  called it twice; the new contract is once.
"""

from unittest.mock import call

from django.test import RequestFactory
from django.views.generic.base import TemplateView

from core.views import AddressView, AddressViewCustom, BaseAddressView

# An arbitrary 58-char address used for single-address dispatch tests; needs
# to be uppercase and >50 chars to exercise the single-address branch.
ADDRESS = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
# 40-char bundle hash from the captured sample payload; exercises the
# short-URL branch through check_bundle_addresses.
BUNDLE = "540A5D8CEC896E073F9170AF0A962503E69147CF"
# What check_bundle_addresses would return for the bundle above: two
# space-separated addresses.
BUNDLE_ADDRESSES = (
    "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU "
    "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
)


def _build_view(args=(), kwargs=None):
    """Return a :class:`BaseAddressView` instance wired with a fake request.

    Mirrors the ``setup_view`` helper from :class:`api.tests.test_views.BaseView`.
    """
    factory = RequestFactory()
    view = BaseAddressView()
    view.request = factory.get("/")
    view.args = args
    view.kwargs = kwargs or {}
    return view


class TestBaseAddressViewClass:
    """Class-level invariants for :class:`BaseAddressView`."""

    def test_subclasses_templateview(self):
        # Plain Django TemplateView, not a DRF view -- the website page is
        # server-rendered HTML.
        assert issubclass(BaseAddressView, TemplateView)

    def test_uses_address_template(self):
        assert BaseAddressView.template_name == "address.html"

    def test_address_view_subclasses_base(self):
        # The two concrete views differ only in their @cache_page decorator;
        # they must continue to delegate render logic to BaseAddressView.
        assert issubclass(AddressView, BaseAddressView)
        assert issubclass(AddressViewCustom, BaseAddressView)


class TestBaseAddressViewDispatch:
    """Tests for :meth:`BaseAddressView.dispatch`."""

    def test_uppercases_url_value_before_forbidden_check(self, mocker):
        # The URL routing regex permits mixed case (it lists [0-9A-Za-z]); the
        # view normalises to upper before checking the deny-list and before
        # using the value as a cache key downstream.
        mocked_forbidden = mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch.object(TemplateView, "dispatch")
        view = _build_view(args=(ADDRESS.lower(),))

        view.dispatch(view.request)

        # First call is the URL value, normalised to upper.
        assert mocked_forbidden.call_args_list[0] == call(ADDRESS)

    def test_single_address_skips_bundle_lookup(self, mocker):
        # Long URL values are addresses; we must not hit Redis for them.
        mocker.patch("core.views.check_forbidden_addresses")
        mocked_bundle = mocker.patch("core.views.check_bundle_addresses")
        mocker.patch.object(TemplateView, "dispatch")
        view = _build_view(args=(ADDRESS,))

        view.dispatch(view.request)

        mocked_bundle.assert_not_called()
        # The address itself becomes the stashed address-list source.
        assert view.addresses == ADDRESS

    def test_bundle_resolves_to_addresses(self, mocker):
        mocker.patch("core.views.check_forbidden_addresses")
        mocked_bundle = mocker.patch(
            "core.views.check_bundle_addresses", return_value=BUNDLE_ADDRESSES
        )
        mocker.patch.object(TemplateView, "dispatch")
        view = _build_view(args=(BUNDLE,))

        view.dispatch(view.request)

        mocked_bundle.assert_called_once_with(BUNDLE)
        assert view.addresses == BUNDLE_ADDRESSES

    def test_bundle_checks_forbidden_against_resolved_addresses(self, mocker):
        # The bundle hash itself can't be on the forbidden list (it's a sha1
        # digest), but the addresses it resolves to can be -- so the deny
        # check has to run a second time against the resolved set.
        mocked_forbidden = mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch("core.views.check_bundle_addresses", return_value=BUNDLE_ADDRESSES)
        mocker.patch.object(TemplateView, "dispatch")
        view = _build_view(args=(BUNDLE,))

        view.dispatch(view.request)

        assert mocked_forbidden.call_args_list == [
            call(BUNDLE),
            call(BUNDLE_ADDRESSES),
        ]

    def test_unknown_bundle_redirects_to_index(self, mocker):
        # An empty-string return means the bundle hash isn't in our cache;
        # this can happen when a user shares an old link after cache eviction
        # or just types nonsense. We bounce to the index page rather than
        # 500ing on a downstream empty-address-list.
        mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch("core.views.check_bundle_addresses", return_value="")
        mocked_redirect = mocker.patch("core.views.redirect")
        super_dispatch = mocker.patch.object(TemplateView, "dispatch")
        view = _build_view(args=(BUNDLE,))

        returned = view.dispatch(view.request)

        mocked_redirect.assert_called_once_with("index")
        assert returned == mocked_redirect.return_value
        # Critical: we must short-circuit before calling super().dispatch,
        # since downstream code (get_context_data) reads self.addresses and
        # would crash on an empty bundle.
        super_dispatch.assert_not_called()

    def test_forwards_to_super_dispatch_on_success(self, mocker):
        mocker.patch("core.views.check_forbidden_addresses")
        mocked_super = mocker.patch.object(TemplateView, "dispatch")
        view = _build_view(args=(ADDRESS,))

        returned = view.dispatch(view.request, "extra", flag=True)

        mocked_super.assert_called_once_with(view.request, "extra", flag=True)
        assert returned == mocked_super.return_value


class TestBaseAddressViewGetContextData:
    """Tests for :meth:`BaseAddressView.get_context_data`."""

    def _patch_collaborators(self, mocker, account=None):
        """Patch every external function get_context_data talks to.

        Returns a dict of mocks so tests can assert against them by name
        rather than re-creating long patch lists per test.
        """
        # check_export_status returns a dict-like; default to {} (tax not started).
        mocked_tax = mocker.patch("core.views.check_export_status", return_value={})
        mocked_banner = mocker.patch(
            "core.views.weighted_randomized_banner", return_value="banner.png"
        )
        mocked_fetch = mocker.patch(
            "core.views.fetch_and_serialize_account",
            return_value=account if account is not None else mocker.MagicMock(),
        )
        # The chart helpers return 4-tuples; we model the unpacking so the
        # view's assignments succeed without giving each slot a real value.
        asachart, nftchart, colors, nft_colors = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        mocked_base = mocker.patch(
            "core.views.prepare_base_charts_from_serialized_data",
            return_value=(asachart, nftchart, colors, nft_colors),
        )
        distchart, ratiochart, nftfloorchart, consolidated = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        mocked_consolidated = mocker.patch(
            "core.views.prepare_consolidated_charts_from_serialized_data",
            return_value=(distchart, ratiochart, nftfloorchart, consolidated),
        )
        return {
            "tax": mocked_tax,
            "banner": mocked_banner,
            "fetch": mocked_fetch,
            "base_charts": mocked_base,
            "consolidated_charts": mocked_consolidated,
            "asachart": asachart,
            "nftchart": nftchart,
            "colors": colors,
            "nft_colors": nft_colors,
            "distchart": distchart,
            "ratiochart": ratiochart,
            "nftfloorchart": nftfloorchart,
            "consolidated": consolidated,
        }

    def test_uppercases_url_value(self, mocker):
        # If the URL value wasn't upper-cased, fetch_and_serialize_account
        # would receive a lowercase string and miss the cache key written
        # by the API view (which always upper-cases).
        mocks = self._patch_collaborators(mocker)
        view = _build_view(args=(ADDRESS.lower(),))
        view.addresses = ADDRESS

        view.get_context_data()

        mocks["fetch"].assert_called_once_with(ADDRESS, ADDRESS)

    def test_sets_finished_tax_when_tax_pipeline_incomplete(self, mocker):
        # check_export_status returns {"finished_tax": False} while a tax export
        # job is queued or in progress; the template uses this to colour the
        # "Download CSV" button red.
        mocks = self._patch_collaborators(mocker)
        mocks["tax"].return_value = {"finished_tax": False}
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        context = view.get_context_data()

        assert context["finished_tax"] is True

    def test_does_not_set_finished_tax_when_tax_completed(self, mocker):
        # finished_tax=True means a CSV is ready for download; the template
        # treats absence-of-key the same way ("default state"), so we leave
        # the key out rather than writing False.
        mocks = self._patch_collaborators(mocker)
        mocks["tax"].return_value = {"finished_tax": True}
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        context = view.get_context_data()

        assert "finished_tax" not in context

    def test_does_not_set_finished_tax_when_tax_data_missing(self, mocker):
        # Empty dict is the default (no tax export ever attempted).
        mocks = self._patch_collaborators(mocker)
        mocks["tax"].return_value = {}
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        context = view.get_context_data()

        assert "finished_tax" not in context

    def test_writes_banner(self, mocker):
        mocks = self._patch_collaborators(mocker)
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        context = view.get_context_data()

        mocks["banner"].assert_called_once_with()
        assert context["banner"] == "banner.png"

    def test_writes_account_payload(self, mocker):
        # The API 2.0 payload becomes context["account"]; the Phase 2
        # templates iterate account.asaitems / account.nftcollections off it.
        sentinel = {"sentinel": "payload"}
        mocks = self._patch_collaborators(mocker, account=sentinel)
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        context = view.get_context_data()

        mocks["fetch"].assert_called_once_with(ADDRESS, ADDRESS)
        assert context["account"] is sentinel

    def test_single_address_writes_address_key_not_bundle(self, mocker):
        self._patch_collaborators(mocker)
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        context = view.get_context_data()

        # Templates do `{% if bundle %}...{% else %}...{% endif %}`; a
        # single-address page must leave bundle unset.
        assert context["address"] == [ADDRESS]
        assert "bundle" not in context
        assert context["is_bundle"] is False

    def test_bundle_writes_bundle_key_not_address(self, mocker):
        self._patch_collaborators(mocker)
        view = _build_view(args=(BUNDLE,))
        view.addresses = BUNDLE_ADDRESSES

        context = view.get_context_data()

        # Mirror image of the single-address case.
        assert context["bundle"] == BUNDLE_ADDRESSES.split(" ")
        assert "address" not in context
        assert context["is_bundle"] is True

    def test_writes_base_chart_outputs_under_expected_keys(self, mocker):
        # address.js consumes these keys via {{ asachart|json_script }};
        # renaming any one of them breaks chart rendering silently in JS.
        mocks = self._patch_collaborators(mocker)
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        context = view.get_context_data()

        mocks["base_charts"].assert_called_once_with(context["account"])
        assert context["asachart"] is mocks["asachart"]
        assert context["nftchart"] is mocks["nftchart"]
        assert context["colors"] is mocks["colors"]
        assert context["nft_colors"] is mocks["nft_colors"]

    def test_writes_consolidated_chart_outputs_under_expected_keys(self, mocker):
        mocks = self._patch_collaborators(mocker)
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        context = view.get_context_data()

        mocks["consolidated_charts"].assert_called_once_with(
            context["account"], mocks["nft_colors"]
        )
        assert context["distchart"] is mocks["distchart"]
        assert context["ratiochart"] is mocks["ratiochart"]
        assert context["nftfloorchart"] is mocks["nftfloorchart"]
        assert context["consolidated"] is mocks["consolidated"]

    def test_consolidated_charts_receive_nft_colors_from_base_charts(self, mocker):
        # The two chart helpers share the nft_colors dict by identity: the
        # base charts populate it (one slot per NFT collection), then the
        # consolidated charts re-use the same mapping so the NFT-floor chart
        # colour-codes consistently with the per-collection NFT chart.
        mocks = self._patch_collaborators(mocker)
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        view.get_context_data()

        # Identity check: same object passed through, not a copy.
        consolidated_call_args = mocks["consolidated_charts"].call_args
        assert consolidated_call_args.args[1] is mocks["nft_colors"]

    def test_does_not_write_legacy_context_keys(self, mocker):
        # Regression guard. The Phase 1 contract is a clean break from the
        # legacy context shape; if any of these keys reappear it means
        # someone re-introduced prepare_context() into the address page.
        self._patch_collaborators(mocker)
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        context = view.get_context_data()

        legacy_keys = {
            "asas",
            "values",
            "nft_values",
            "total",
            "online",
            "points",
            "warning",
            "information",
        }
        assert legacy_keys.isdisjoint(context.keys()), (
            "Legacy context keys leaked back in: " f"{legacy_keys & context.keys()}"
        )

    def test_full_context_shape(self, mocker):
        # Lock the exact set of keys written by get_context_data, so any
        # silent addition or removal triggers an explicit test update.
        # Excludes TemplateView's own ``view`` key which is added by
        # super().get_context_data when self.request is bound.
        self._patch_collaborators(mocker)
        view = _build_view(args=(ADDRESS,))
        view.addresses = ADDRESS

        context = view.get_context_data()

        # ``view`` comes from TemplateView.get_context_data via ContextMixin.
        expected = {
            "view",
            "banner",
            "account",
            "address",
            "is_bundle",
            "asachart",
            "nftchart",
            "colors",
            "nft_colors",
            "distchart",
            "ratiochart",
            "nftfloorchart",
            "consolidated",
        }
        assert set(context.keys()) == expected


class TestBaseAddressViewIntegration:
    """End-to-end render of the view against the real sample payload.

    Only ``fetch_and_serialize_account`` and the dispatch-side validators
    are mocked; the chart helpers and ``get_context_data`` orchestration
    run for real. Locks in the glue between the view and
    :func:`utils.charts.prepare_*_from_serialized_data`.
    """

    def test_renders_with_real_sample_payload(self, mocker):
        import json
        from pathlib import Path

        from utils.constants.charts import DISTRIBUTION_COLORS

        sample = json.loads(
            (
                Path(__file__).parent.parent.parent
                / "utils"
                / "tests"
                / "sample_serialized_540A5.json"
            ).read_text()
        )

        mocker.patch("core.views.check_export_status", return_value={})
        mocker.patch("core.views.weighted_randomized_banner", return_value="b.png")
        mocker.patch("core.views.fetch_and_serialize_account", return_value=sample)

        view = _build_view(args=(BUNDLE,))
        view.addresses = BUNDLE_ADDRESSES

        context = view.get_context_data()

        # Account payload landed under the right key with the right shape.
        assert context["account"] is sample
        assert context["is_bundle"] is True
        assert context["bundle"] == BUNDLE_ADDRESSES.split(" ")

        # Charts came out structurally valid (not just MagicMocks).
        assert set(context["asachart"].keys()) == {"labels", "datasets"}
        assert set(context["nftchart"].keys()) == {"labels", "datasets"}
        # Distribution chart: one dataset per segment.
        assert len(context["distchart"]["datasets"]) == len(DISTRIBUTION_COLORS)
        # Ratio chart: balance/staked/liquidity/defi + NFT.
        assert context["ratiochart"]["labels"] == [
            *DISTRIBUTION_COLORS.keys(),
            "NFT",
        ]
        # Consolidated totals are positive (sample has every category populated).
        assert context["consolidated"].balance > 0
        assert context["consolidated"].nftfloor > 0
