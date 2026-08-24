"""Tests for :mod:`utils.layouts`."""

import pytest
from django.template.loader import get_template

from utils.constants.core import ADDRESS_LAYOUTS, DEFAULT_ADDRESS_LAYOUT
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from utils.layouts import (
    can_access_layout,
    layout_choices,
    layout_compact,
    layout_name,
    layout_template,
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
        assert set(ADDRESS_LAYOUTS[key]) == {
            "name",
            "summary",
            "template",
            "compact",
            "tier",
        }

    @pytest.mark.parametrize("key", sorted(ADDRESS_LAYOUTS))
    def test_utils_layouts_registry_template_exists(self, key):
        """A layout naming a missing template is a 500 on the address page.

        Checked against the loaders rather than the filesystem so a template
        supplied by an app or an override directory still counts.
        """
        get_template(ADDRESS_LAYOUTS[key]["template"])

    @pytest.mark.parametrize("key", sorted(ADDRESS_LAYOUTS))
    def test_utils_layouts_registry_compact_is_a_bool(self, key):
        """It reaches a template as a flag, and `{% if %}` accepts anything.

        A string `"false"` would therefore read as compact, silently.
        """
        assert isinstance(ADDRESS_LAYOUTS[key]["compact"], bool)

    def test_utils_layouts_registry_compact_distinguishes_shared_templates(self):
        """Two layouts on one template must differ in the compact flag.

        Otherwise they render identical bytes under two cache keys, and the
        reader who picked the second one sees no change -- the exact failure
        this registry was re-cut to prevent.
        """
        seen = {}
        for key, conf in ADDRESS_LAYOUTS.items():
            signature = (conf["template"], conf["compact"])
            assert signature not in seen, f"{key} renders the same as {seen.get(signature)}"
            seen[signature] = key

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

    def test_utils_layouts_can_access_ungated_layout_at_every_tier(self):
        """Design 1 is reachable by everybody, including signed-out readers.

        The default is the fallback for both an unknown key and an unentitled
        one, so gating it would leave `normalized_layout` with nowhere to go.
        """
        assert all(
            can_access_layout(DEFAULT_ADDRESS_LAYOUT, permission) is True
            for permission in (TRIAL, INTRO, ASASTATSER, PROFESSIONAL)
        )

    def test_utils_layouts_cannot_access_dynamic_layout_at_trial(self):
        assert can_access_layout("money-column", TRIAL) is False

    def test_utils_layouts_can_access_dynamic_layout_at_intro(self):
        assert can_access_layout("money-column", INTRO) is True

    def test_utils_layouts_cannot_access_compact_layout_at_intro(self):
        assert can_access_layout("money-column-compact", INTRO) is False

    def test_utils_layouts_cannot_access_compact_layout_at_trial(self):
        assert can_access_layout("money-column-compact", TRIAL) is False

    def test_utils_layouts_can_access_asastatser_layout_at_asastatser(self):
        assert can_access_layout("money-column", ASASTATSER) is True

    def test_utils_layouts_can_access_compact_layout_at_asastatser(self):
        assert can_access_layout("money-column-compact", ASASTATSER) is True

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

    def test_utils_layouts_choices_at_intro_includes_dynamic(self):
        """Intro buys Dynamic, not its compact variant."""
        assert [key for key, _ in layout_choices(INTRO)] == [
            DEFAULT_ADDRESS_LAYOUT,
            "money-column",
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

    def test_utils_layouts_locked_at_intro_names_only_the_compact_dynamic_layout(self):
        assert [entry["tier"] for entry in locked_layouts(INTRO)] == [
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
        assert layout_name("money-column") == "Dynamic"

    def test_utils_layouts_name_returns_compact_display_name(self):
        assert layout_name("money-column-compact") == "Dynamic compact"

    def test_utils_layouts_name_falls_back_on_unknown(self):
        assert layout_name("nope") == ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT]["name"]

    def test_utils_layouts_name_takes_no_permission(self):
        """It answers what a layout is called, which is the same for everybody."""
        assert layout_name("money-column") == "Dynamic"


class TestUtilsLayoutsTemplate:
    """Testing class for :func:`layout_template`."""

    def test_utils_layouts_template_default_is_the_classic_page(self):
        assert layout_template(DEFAULT_ADDRESS_LAYOUT) == "address.html"

    def test_utils_layouts_template_money_column_has_its_own(self):
        assert layout_template("money-column") == "address_money.html"

    def test_utils_layouts_template_is_shared_by_a_layout_and_its_compact_form(self):
        """Designs 2 and 3 are one template with a flag, as the prototype builds
        them -- duplicating the file would duplicate every row and chart to
        change a handful of grid rules."""
        assert layout_template("money-column-compact") == layout_template("money-column")

    def test_utils_layouts_template_falls_back_on_unknown(self):
        """A key left behind by a removed layout renders the default page.

        Falling through would raise `TemplateDoesNotExist` at the top of the
        view, turning a stale preference into a 500.
        """
        assert layout_template("nope") == layout_template(DEFAULT_ADDRESS_LAYOUT)


class TestUtilsLayoutsCompact:
    """Testing class for :func:`layout_compact`."""

    def test_utils_layouts_compact_default_is_not_compact(self):
        assert layout_compact(DEFAULT_ADDRESS_LAYOUT) is False

    def test_utils_layouts_compact_money_column_is_not_compact(self):
        assert layout_compact("money-column") is False

    def test_utils_layouts_compact_money_column_compact_is(self):
        assert layout_compact("money-column-compact") is True

    def test_utils_layouts_compact_falls_back_on_unknown(self):
        assert layout_compact("nope") is layout_compact(DEFAULT_ADDRESS_LAYOUT)


class TestUtilsLayoutsTier:
    """Testing class for :func:`layout_tier`."""

    def test_utils_layouts_tier_none_for_the_default(self):
        assert layout_tier(DEFAULT_ADDRESS_LAYOUT) is None

    def test_utils_layouts_tier_names_the_dynamic_gate(self):
        assert layout_tier("money-column") == "Intro"

    def test_utils_layouts_tier_names_the_compact_gate(self):
        assert layout_tier("money-column-compact") == "Asastatser"

    def test_utils_layouts_tier_falls_back_on_unknown(self):
        assert layout_tier("nope") is None
