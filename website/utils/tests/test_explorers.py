"""Tests for :mod:`utils.constants.explorers`."""

from utils.constants.explorers import (
    DEFAULT_EXPLORER,
    EXPLORERS,
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
    """Testing class for :func:`explorer_link`, :func:`explorer_base`, :func:`explorer_name`."""

    def test_utils_constants_explorers_link_address_for_allo(self):
        assert explorer_link("allo", "address", "ADDR") == (
            "https://allo.info/account/ADDR"
        )

    def test_utils_constants_explorers_link_asset_for_pera(self):
        assert explorer_link("pera", "asset", 123) == (
            "https://explorer.perawallet.app/asset/123"
        )

    def test_utils_constants_explorers_link_transaction_path_differs(self):
        assert explorer_link("lora", "transaction", "TX").endswith("/transaction/TX")
        assert explorer_link("allo", "transaction", "TX").endswith("/tx/TX")

    def test_utils_constants_explorers_link_unknown_explorer_uses_default(self):
        assert explorer_link("bogus", "asset", 1) == "https://allo.info/asset/1"

    def test_utils_constants_explorers_link_unknown_entity_returns_base(self):
        assert explorer_link("lora", "weird", "X") == (
            "https://lora.algokit.io/mainnet/"
        )

    def test_utils_constants_explorers_base_for_algosurf(self):
        assert explorer_base("algosurf") == "https://algo.surf/"

    def test_utils_constants_explorers_path_strips_placeholder(self):
        assert explorer_path("allo", "transaction") == "tx/"
        assert explorer_path("lora", "transaction") == "transaction/"
        assert explorer_path("allo", "address") == "account/"

    def test_utils_constants_explorers_name_for_pera(self):
        assert explorer_name("pera") == "Pera Explorer"
