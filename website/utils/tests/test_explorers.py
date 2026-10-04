"""Tests for :mod:`utils.explorers`."""

from utils.constants.core import DEFAULT_EXPLORER, EXPLORERS
from utils.explorers import (
    explorer_base,
    explorer_choices,
    explorer_link,
    explorer_name,
    explorer_path,
    normalized_explorer,
)


class TestUtilsConstantsExplorersNormalized:
    """Testing class for :func:`normalized_explorer`."""

    def test_utils_constants_explorers_normalized_keeps_known_key(self):
        assert normalized_explorer("lora") == "lora"

    def test_utils_constants_explorers_normalized_falls_back_on_unknown(self):
        assert normalized_explorer("nope") == DEFAULT_EXPLORER

    def test_utils_constants_explorers_normalized_falls_back_on_empty(self):
        assert normalized_explorer("") == DEFAULT_EXPLORER

    def test_utils_constants_explorers_normalized_falls_back_on_none(self):
        assert normalized_explorer(None) == DEFAULT_EXPLORER


class TestUtilsConstantsExplorersChoices:
    """Testing class for :func:`explorer_choices`."""

    def test_utils_constants_explorers_choices_default_first(self):
        assert explorer_choices()[0] == (
            DEFAULT_EXPLORER,
            EXPLORERS[DEFAULT_EXPLORER]["name"],
        )

    def test_utils_constants_explorers_choices_rest_sorted_by_name(self):
        rest = explorer_choices()[1:]
        assert rest == sorted(rest, key=lambda pair: pair[1])

    def test_utils_constants_explorers_choices_cover_every_provider(self):
        assert {key for key, _ in explorer_choices()} == set(EXPLORERS)


class TestUtilsConstantsExplorersLink:
    """Testing class for the three `explorer_*` helpers."""

    def test_utils_constants_explorers_link_address_for_allo(self):
        assert explorer_link("allo", "address", "ADDR") == (
            "https://allo.info/account/ADDR"
        )

    def test_utils_constants_explorers_link_asset_for_pera(self):
        assert explorer_link("pera", "asset", 123) == (
            "https://explorer.perawallet.app/asset/123"
        )

    def test_utils_constants_explorers_link_application_for_pera(self):
        assert explorer_link("pera", "application", 123) == (
            "https://explorer.perawallet.app/application/123"
        )

    def test_utils_constants_explorers_link_transaction_path_differs(self):
        assert explorer_link("lora", "transaction", "TX").endswith("/transaction/TX")
        assert explorer_link("allo", "transaction", "TX").endswith("/tx/TX")

    def test_utils_constants_explorers_link_unknown_explorer_uses_default(self):
        assert explorer_link("bogus", "asset", 1) == "https://allo.info/asset/1"

    def test_utils_constants_explorers_link_unknown_entity_returns_base(self):
        assert explorer_link("lora", "weird", "X") == ("https://lora.algokit.io/mainnet/")

    def test_utils_constants_explorers_base_for_algosurf(self):
        assert explorer_base("algosurf") == "https://algo.surf/"

    def test_utils_constants_explorers_path_strips_placeholder(self):
        assert explorer_path("allo", "transaction") == "tx/"
        assert explorer_path("lora", "transaction") == "transaction/"
        assert explorer_path("allo", "address") == "account/"
        assert explorer_path("allo", "application") == "application/"

    def test_utils_constants_explorers_name_for_pera(self):
        assert explorer_name("pera") == "Pera Explorer"


class TestUtilsExplorersMarkers:
    """Testing class for engine explorer markers."""

    def test_utils_explorers_parse_marker_for_each_entity(self):
        from utils.explorers import parse_marker

        assert parse_marker("application=1") == ("application", "1")
        assert parse_marker("asset=2") == ("asset", "2")
        assert parse_marker("address=ADDR") == ("address", "ADDR")
        assert parse_marker("transaction=TX") == ("transaction", "TX")
        assert parse_marker("group=a/b+c=") == ("group", "a/b+c=")

    def test_utils_explorers_parse_marker_rejects_non_markers(self):
        from utils.explorers import parse_marker

        assert parse_marker("https://exa.market/asset/1") is None
        assert parse_marker("application=abc") is None
        assert parse_marker("asset=abc") is None
        assert parse_marker(None) is None

    def test_utils_explorers_marker_link_keeps_urls(self):
        from utils.explorers import marker_link

        assert marker_link("pera", "https://exa.market/") == "https://exa.market/"

    def test_utils_explorers_marker_link_group_per_explorer(self):
        from utils.explorers import marker_link

        assert marker_link("allo", "group=a/b+c=") == (
            "https://allo.info/tx/group/a%2Fb%2Bc%3D"
        )
        assert marker_link("pera", "group=a/b+c=") == (
            "https://explorer.perawallet.app/tx-group/a/b+c=/"
        )
        assert marker_link("algosurf", "group=G=") == "https://allo.info/tx/group/G%3D"

    def test_utils_explorers_is_escrow_marker(self):
        from utils.explorers import is_escrow_marker

        assert is_escrow_marker("application=1") is True
        assert is_escrow_marker("address=ADDR") is True
        assert is_escrow_marker("asset=1") is True
        assert is_escrow_marker("transaction=TX") is False
        assert is_escrow_marker("https://allo.info/asset/1") is False
