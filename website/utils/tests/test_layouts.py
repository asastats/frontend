"""Tests for :mod:`utils.layouts`."""

import pytest

from utils.constants.core import ADDRESS_LAYOUTS, DEFAULT_ADDRESS_LAYOUT
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from utils.layouts import (
    can_access_layout,
    layout_choices,
    layout_name,
    layout_position,
    layout_tier,
    locked_layouts,
    normalized_layout,
)

TRIAL = 0
INTRO = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
PROFESSIONAL = SUBSCRIPTION_TIER_PERMISSIONS["Professional"]


class TestUtilsLayoutsRegistry:
    """Testing class for the shape of :data:`ADDRESS_LAYOUTS` itself.

    Every function in the module indexes these keys directly, so a new entry
    missing one of them fails at render time rather than here without this.
    """

    def test_utils_layouts_registry_default_is_a_member(self):
        assert DEFAULT_ADDRESS_LAYOUT in ADDRESS_LAYOUTS

    def test_utils_layouts_registry_default_is_ungated(self):
        """The fallback must be reachable by everyone, or nothing can fall back."""
        assert ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT]["tier"] is None

    @pytest.mark.parametrize("key", sorted(ADDRESS_LAYOUTS))
    def test_utils_layouts_registry_entry_carries_every_key(self, key):
        assert set(ADDRESS_LAYOUTS[key]) == {"name", "summary", "position", "tier"}

    @pytest.mark.parametrize("key", sorted(ADDRESS_LAYOUTS))
    def test_utils_layouts_registry_position_is_a_known_modifier(self, key):
        """`.position--rows` and `.position--cards` are the only two that exist.

        A third value would render a bare `.position`, which declares no grid
        areas, so its summary and breakdown would overlap.
        """
        assert ADDRESS_LAYOUTS[key]["position"] in {"rows", "cards"}

    @pytest.mark.parametrize("key", sorted(ADDRESS_LAYOUTS))
    def test_utils_layouts_registry_tier_is_none_or_a_real_tier(self, key):
        tier = ADDRESS_LAYOUTS[key]["tier"]
        assert tier is None or tier in SUBSCRIPTION_TIER_PERMISSIONS

    @pytest.mark.parametrize("key", sorted(ADDRESS_LAYOUTS))
    def test_utils_layouts_registry_key_fits_the_model_field(self, key):
        """`Profile.preferred_layout` is `max_length=32`."""
        assert len(key) <= 32

    def test_utils_layouts_registry_names_are_distinct(self):
        names = [conf["name"] for conf in ADDRESS_LAYOUTS.values()]
        assert len(set(names)) == len(names)


class TestUtilsLayoutsCanAccess:
    """Testing class for :func:`can_access_layout`."""

    def test_utils_layouts_can_access_ungated_layout_at_trial(self):
        assert can_access_layout("classic", TRIAL) is True

    def test_utils_layouts_can_access_intro_layout_below_intro(self):
        assert can_access_layout("classic-compact", TRIAL) is False

    def test_utils_layouts_can_access_intro_layout_at_intro(self):
        assert can_access_layout("classic-compact", INTRO) is True

    def test_utils_layouts_can_access_asastatser_layout_at_intro(self):
        assert can_access_layout("money-column", INTRO) is False

    def test_utils_layouts_can_access_asastatser_layout_at_asastatser(self):
        assert can_access_layout("money-column", ASASTATSER) is True

    def test_utils_layouts_can_access_gated_layout_above_its_tier(self):
        assert can_access_layout("money-column", PROFESSIONAL) is True

    def test_utils_layouts_can_access_rejects_unknown_key(self):
        """An unknown key names nothing to render, at any tier."""
        assert can_access_layout("nope", PROFESSIONAL) is False

    def test_utils_layouts_can_access_rejects_empty(self):
        assert can_access_layout("", PROFESSIONAL) is False

    def test_utils_layouts_can_access_rejects_none(self):
        assert can_access_layout(None, PROFESSIONAL) is False


class TestUtilsLayoutsNormalized:
    """Testing class for :func:`normalized_layout`."""

    def test_utils_layouts_normalized_keeps_entitled_key(self):
        assert normalized_layout("money-column", ASASTATSER) == "money-column"

    def test_utils_layouts_normalized_falls_back_on_unknown(self):
        assert normalized_layout("nope", ASASTATSER) == DEFAULT_ADDRESS_LAYOUT

    def test_utils_layouts_normalized_falls_back_on_empty(self):
        assert normalized_layout("", ASASTATSER) == DEFAULT_ADDRESS_LAYOUT

    def test_utils_layouts_normalized_falls_back_on_none(self):
        assert normalized_layout(None, ASASTATSER) == DEFAULT_ADDRESS_LAYOUT

    def test_utils_layouts_normalized_falls_back_when_tier_lapses(self):
        """The saved key survives; what it resolves to does not.

        This is the difference from `normalized_explorer`, which re-checks
        nothing: a layout is the subscription benefit, so a lapsed reader gets
        the default back while their choice waits for a renewal.
        """
        assert normalized_layout("money-column", TRIAL) == DEFAULT_ADDRESS_LAYOUT

    @pytest.mark.parametrize("permission", [TRIAL, INTRO, ASASTATSER, PROFESSIONAL])
    def test_utils_layouts_normalized_result_is_always_entitled(self, permission):
        result = normalized_layout("money-column-compact", permission)
        assert can_access_layout(result, permission) is True


class TestUtilsLayoutsChoices:
    """Testing class for :func:`layout_choices`."""

    def test_utils_layouts_choices_default_first(self):
        assert layout_choices(PROFESSIONAL)[0] == (
            DEFAULT_ADDRESS_LAYOUT,
            ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT]["name"],
        )

    def test_utils_layouts_choices_at_trial_is_default_alone(self):
        assert layout_choices(TRIAL) == [
            (DEFAULT_ADDRESS_LAYOUT, ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT]["name"])
        ]

    def test_utils_layouts_choices_at_intro_adds_the_compact_default(self):
        assert [key for key, _ in layout_choices(INTRO)] == [
            "classic",
            "classic-compact",
        ]

    def test_utils_layouts_choices_at_asastatser_is_every_layout(self):
        assert {key for key, _ in layout_choices(ASASTATSER)} == set(ADDRESS_LAYOUTS)

    def test_utils_layouts_choices_never_repeat_the_default(self):
        keys = [key for key, _ in layout_choices(PROFESSIONAL)]
        assert keys.count(DEFAULT_ADDRESS_LAYOUT) == 1

    @pytest.mark.parametrize("permission", [TRIAL, INTRO, ASASTATSER, PROFESSIONAL])
    def test_utils_layouts_choices_are_all_entitled(self, permission):
        """The choices *are* the entitlement -- the form has no second check."""
        assert all(
            can_access_layout(key, permission) for key, _ in layout_choices(permission)
        )


class TestUtilsLayoutsLocked:
    """Testing class for :func:`locked_layouts`."""

    def test_utils_layouts_locked_at_asastatser_is_empty(self):
        assert locked_layouts(ASASTATSER) == []

    def test_utils_layouts_locked_at_trial_names_every_gated_layout(self):
        assert [entry["name"] for entry in locked_layouts(TRIAL)] == [
            ADDRESS_LAYOUTS[key]["name"]
            for key in ADDRESS_LAYOUTS
            if ADDRESS_LAYOUTS[key]["tier"] is not None
        ]

    def test_utils_layouts_locked_at_intro_names_only_the_money_column(self):
        assert [entry["tier"] for entry in locked_layouts(INTRO)] == [
            "Asastatser",
            "Asastatser",
        ]

    @pytest.mark.parametrize("permission", [TRIAL, INTRO, ASASTATSER])
    def test_utils_layouts_locked_and_choices_partition_the_registry(self, permission):
        """Nothing may be both offered and withheld, and nothing may vanish."""
        offered = {key for key, _ in layout_choices(permission)}
        withheld = {entry["name"] for entry in locked_layouts(permission)}
        offered_names = {ADDRESS_LAYOUTS[key]["name"] for key in offered}
        assert offered_names.isdisjoint(withheld)
        assert offered_names | withheld == {
            conf["name"] for conf in ADDRESS_LAYOUTS.values()
        }

    @pytest.mark.parametrize("permission", [TRIAL, INTRO])
    def test_utils_layouts_locked_entries_carry_a_tier_to_name(self, permission):
        assert all(entry["tier"] for entry in locked_layouts(permission))


class TestUtilsLayoutsName:
    """Testing class for :func:`layout_name`."""

    def test_utils_layouts_name_returns_display_name(self):
        assert layout_name("money-column") == "Money column"

    def test_utils_layouts_name_falls_back_on_unknown(self):
        assert layout_name("nope") == ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT]["name"]

    def test_utils_layouts_name_takes_no_permission(self):
        """It answers what a layout is called, which is the same for everybody."""
        assert layout_name("money-column") == "Money column"


class TestUtilsLayoutsPosition:
    """Testing class for :func:`layout_position`."""

    def test_utils_layouts_position_default_is_rows(self):
        assert layout_position(DEFAULT_ADDRESS_LAYOUT) == "rows"

    def test_utils_layouts_position_compact_is_cards(self):
        assert layout_position("classic-compact") == "cards"

    def test_utils_layouts_position_falls_back_on_unknown(self):
        assert layout_position("nope") == "rows"


class TestUtilsLayoutsTier:
    """Testing class for :func:`layout_tier`."""

    def test_utils_layouts_tier_none_for_the_default(self):
        assert layout_tier(DEFAULT_ADDRESS_LAYOUT) is None

    def test_utils_layouts_tier_names_the_gate(self):
        assert layout_tier("money-column") == "Asastatser"

    def test_utils_layouts_tier_falls_back_on_unknown(self):
        assert layout_tier("nope") is None
