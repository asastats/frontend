"""Identifiers that have to survive a refresh, and admit when they cannot.

The address page wants to pin one position out of an asset's breakdown and find
it again next time the page loads. Value moves with the price and index moves
with the ranking, so the identifier has to be built from what the position is.

These tests pin down three things: that the identifier ignores everything
volatile, that it separates the positions the payload can separate, and that it
is honest about the ones it cannot -- the last being the point of the exercise,
because a pin that silently moves to a different position is worse than a pin
that says it is unsure.
"""

import json
from pathlib import Path

import pytest

from api.position_id import PID_VERSION, annotate_positions, position_id

SAMPLE_PATH = (
    Path(__file__).parent.parent.parent / "utils" / "tests" / "sample_serialized_540A5.json"
)

#: What the real bundle currently yields. Written down so a change has to be a
#: decision: the first number may only go up, the second only down.
EXPECTED_POSITIONS = 190
EXPECTED_DISTINCT_IDS = 187
EXPECTED_AMBIGUOUS_ROWS = 6


@pytest.fixture(scope="module")
def payload():
    """The real serialized bundle, 76 assets and 190 positions."""
    if not SAMPLE_PATH.exists():
        pytest.skip(f"sample payload not at {SAMPLE_PATH}")
    with SAMPLE_PATH.open() as handle:
        return json.load(handle)


def _program(**detail):
    """One serialized position, with only the fields identity is built from."""
    linked = detail.pop("linked", None)
    program = {
        "program": {
            "type": detail.pop("type", "Added"),
            "name": detail.pop("name", "Liquidity"),
            "provider": {"name": detail.pop("provider", "Pact LP")},
            "url": detail.pop("url", "https://app.pact.fi/your-liquidity"),
        }
    }
    if "code" in detail:
        program["program"]["code"] = detail.pop("code")
    if linked is not None:
        program["linked"] = linked
    program.update(detail)
    return program


class TestWhatIdentityIgnores:
    """Everything that moves between two loads of the same page."""

    @pytest.mark.parametrize(
        "field,before,after",
        [
            ("value", "8.890945", "9.104112"),
            ("amount", 8890945, 9104112),
        ],
    )
    def test_the_numbers_do_not_change_the_identity(self, field, before, after):
        """A position is the same position when its price or size moves.

        This is the whole reason the identifier exists: the two obvious
        handles, value and amount, are the two things guaranteed to differ on
        the next refresh.
        """
        first = position_id(0, _program(**{field: before}))
        second = position_id(0, _program(**{field: after}))

        assert first == second

    def test_distribution_does_not_change_the_identity(self):
        """Where the value is sourced from is a fact about now, not about what.

        A deposit routed through Tinyman today and Pact tomorrow is still the
        same deposit.
        """
        plain = _program()
        routed = _program(
            distribution=[{"value": "8.89", "amount": 1, "link": {"text": "Tinyman swap"}}]
        )

        assert position_id(0, plain) == position_id(0, routed)

    def test_linked_ordering_does_not_change_the_identity(self):
        """The engine is free to reorder linked data.

        Identity is built from a sorted view of it precisely so that a
        reordering upstream cannot invalidate every stored pin at once.
        """
        forward = _program(
            linked=[
                {"text": "Source LP token", "id": 1129173576},
                {"text": "Pact farm", "link": "https://app.pact.fi/farms"},
            ]
        )
        reversed_ = _program(
            linked=[
                {"text": "Pact farm", "link": "https://app.pact.fi/farms"},
                {"text": "Source LP token", "id": 1129173576},
            ]
        )

        assert position_id(0, forward) == position_id(0, reversed_)

    def test_a_non_identifying_link_does_not_change_the_identity(self):
        """Only `Source LP token` is promoted; a farm link merely describes.

        Two positions in the same pool, one of them farmed, are still the same
        position -- and a farm that opens or closes must not orphan a pin.
        """
        bare = _program(linked=[{"text": "Source LP token", "id": 1129173576}])
        farmed = _program(
            linked=[
                {"text": "Source LP token", "id": 1129173576},
                {"text": "Pact farm", "link": "https://app.pact.fi/farms?tab=yours"},
            ]
        )

        assert position_id(0, bare) == position_id(0, farmed)


class TestWhatIdentitySeparates:
    """The fields that genuinely describe a different position."""

    @pytest.mark.parametrize(
        "field,other",
        [
            ("type", "Borrowed"),
            ("name", "Pact deposit"),
            ("provider", "Tinyman"),
            ("url", "https://app.pact.fi/farms"),
            ("code", "Pact LP ALGO-USDC"),
        ],
    )
    def test_each_descriptive_field_changes_the_identity(self, field, other):
        """Otherwise two different positions would share a pin."""
        fields = {"code": "Pact LP ALGO-ASASTATS"}
        base = _program(**fields)
        changed = _program(**{**fields, field: other})

        assert position_id(0, base) != position_id(0, changed)

    def test_the_same_program_on_two_assets_is_two_positions(self):
        """`Folks v1 deposit` on ALGO and on USDC are unrelated holdings."""
        assert position_id(0, _program()) != position_id(31566704, _program())

    def test_the_source_lp_token_separates_two_pact_positions(self):
        """The case that motivated promoting it.

        Two Pact ALGO-ASASTATS positions are identical in type, name, provider,
        code and url. The only thing that tells them apart anywhere in the
        payload is which LP token they hold.
        """
        first = _program(
            code="Pact LP ALGO-ASASTATS",
            linked=[{"text": "Source LP token", "id": 1129173576}],
        )
        second = _program(
            code="Pact LP ALGO-ASASTATS",
            linked=[{"text": "Source LP token", "id": 2757667448}],
        )

        assert position_id(0, first) != position_id(0, second)


class TestVersioning:
    """Stored ids outlive the code that made them."""

    def test_the_id_carries_its_recipe_version(self):
        """A recipe change invalidates every stored pin.

        Carrying the version means a stale pin can be recognised as stale
        rather than quietly failing to match anything.
        """
        assert position_id(0, _program()).startswith(f"{PID_VERSION}-")

    def test_the_id_names_its_asset(self):
        """Readable in a log, a URL fragment or a stored view without a lookup."""
        assert position_id(31566704, _program()).startswith(f"{PID_VERSION}-31566704-")


class TestAnnotation:
    """`annotate_positions` is what the serializer calls."""

    def test_every_position_gets_an_id(self):
        programs = [_program(name="a"), _program(name="b")]

        annotate_positions(0, programs)

        assert all(p["pid"] for p in programs)

    def test_the_flag_is_written_even_when_false(self):
        """Absent-when-false would make two different things look the same.

        A consumer could not tell "this position is uniquely identified" from
        "this build does not report ambiguity", and the OpenAPI schema would
        have to call the field optional for a reason that has nothing to do
        with the client. Gzipped it costs under 200 bytes on the whole bundle.
        """
        programs = [_program(name="a"), _program(name="b")]

        annotate_positions(0, programs)

        assert [p["pid_ambiguous"] for p in programs] == [False, False]

    def test_indistinguishable_positions_are_flagged_not_renumbered(self):
        """An ordinal suffix would be unique and wrong.

        Two Cometa stakes ranked by value swap the moment their values cross,
        and a pin built on the ordinal would follow the rank rather than the
        position -- moving to the other stake with nothing to show it had. The
        flag says "cannot promise", which a caller can act on.
        """
        programs = [_program(name="Cometa stake"), _program(name="Cometa stake")]

        annotate_positions(0, programs)

        assert programs[0]["pid"] == programs[1]["pid"]
        assert all(p["pid_ambiguous"] for p in programs)

    def test_an_empty_program_list_is_left_alone(self):
        """Not every asset has positions, and none of them should raise."""
        assert annotate_positions(0, []) == []
        assert annotate_positions(0, None) is None


class TestAgainstTheRealBundle:
    """Measured, so the numbers are a decision rather than an assumption."""

    @pytest.fixture(scope="class")
    def annotated(self, payload):
        items = []
        for item in payload["asaitems"]:
            programs = [dict(p) for p in item["programs"]]
            annotate_positions(item["asset"]["id"], programs)
            items.append((item["asset"], programs))
        return items

    def test_the_bundle_still_has_the_positions_we_measured(self, annotated):
        """A moved goalpost should be visible, not silently absorbed."""
        total = sum(len(programs) for _, programs in annotated)

        assert total == EXPECTED_POSITIONS

    def test_identity_covers_all_but_the_known_collisions(self, annotated):
        """187 distinct ids for 190 positions.

        This may only improve. If it drops, something that used to describe a
        position has stopped being emitted, and pins are silently merging.
        """
        ids = [p["pid"] for _, programs in annotated for p in programs]

        assert len(set(ids)) >= EXPECTED_DISTINCT_IDS, (
            f"{len(set(ids))} distinct ids for {len(ids)} positions; "
            f"identity has got weaker, not stronger"
        )

    def test_the_ambiguous_rows_are_the_ones_we_know_about(self, annotated):
        """Six rows, three pairs, and each one is named here on purpose.

        These are the cases waiting on an upstream discriminator. When the
        engine starts emitting one, this list shrinks and the expected count
        comes down with it.
        """
        ambiguous = [
            (asset["unit"], p["program"].get("name") or p["program"]["type"])
            for asset, programs in annotated
            for p in programs
            if p.get("pid_ambiguous")
        ]

        assert len(ambiguous) <= EXPECTED_AMBIGUOUS_ROWS, f"new ambiguity: {ambiguous}"
        assert {name for _, name in ambiguous} == {
            "Lofty AMM",
            "Cometa stake",
            "Gora.fi Validator",
        }

    def test_the_pact_pairs_are_no_longer_ambiguous(self, annotated):
        """The two collisions the LP token was promoted to fix.

        They appear on ALGO and on ASASTATS -- the same pair of pools seen from
        both sides -- so fixing it once fixes four rows.
        """
        pact = [
            p
            for _, programs in annotated
            for p in programs
            if (p["program"].get("code") or "") == "Pact LP ALGO-ASASTATS"
        ]

        assert len(pact) == 4, f"expected four Pact ALGO-ASASTATS rows, got {len(pact)}"
        assert not any(p.get("pid_ambiguous") for p in pact)

    def test_ids_are_stable_across_repeated_annotation(self, payload):
        """Annotating twice must produce the same ids.

        Nothing in the recipe reads a counter, a clock or the position's place
        in the list; this is what proves it.
        """

        def run():
            out = {}
            for item in payload["asaitems"]:
                programs = [dict(p) for p in item["programs"]]
                annotate_positions(item["asset"]["id"], programs)
                for index, program in enumerate(programs):
                    out[(item["asset"]["id"], index)] = program["pid"]
            return out

        assert run() == run()

    def test_reordering_an_assets_positions_does_not_change_their_ids(self, payload):
        """Because the ranking is a presentation choice, not an identity.

        Sorting by amount instead of value, or reversing the list, has to leave
        every pin pointing where it pointed.
        """
        item = next(i for i in payload["asaitems"] if len(i["programs"]) > 5)
        forward = [dict(p) for p in item["programs"]]
        backward = [dict(p) for p in reversed(item["programs"])]

        annotate_positions(item["asset"]["id"], forward)
        annotate_positions(item["asset"]["id"], backward)

        assert sorted(p["pid"] for p in forward) == sorted(p["pid"] for p in backward)


class TestSerializerIntegration:
    """The identifiers have to survive the serializer, not just the function."""

    def test_asaitemserializer_adds_a_pid_to_every_position(self, mocker):
        """`AsaItemSerializer.to_representation` is where the two meet.

        Computed on the serialized output rather than the incoming instance, so
        it does not depend on whatever shape the engine hands in.
        """
        import api.serializers

        mocker.patch.object(
            api.serializers.Serializer,
            "to_representation",
            return_value={
                "asset": {"id": 31566704},
                "programs": [
                    {"program": {"type": "Balance"}},
                    {"program": {"type": "Deposited", "name": "Folks v1 deposit"}},
                ],
            },
        )
        result = api.serializers.AsaItemSerializer().to_representation(object())

        pids = [p["pid"] for p in result["programs"]]
        assert all(pid.startswith(f"{PID_VERSION}-31566704-") for pid in pids)
        assert len(set(pids)) == 2

    def test_an_asset_without_positions_serializes_unchanged(self, mocker):
        """Nothing in the payload guarantees `programs` is present.

        The serializer already drops empty values elsewhere, so this has to
        tolerate their absence rather than assume the key.
        """
        import api.serializers

        mocker.patch.object(
            api.serializers.Serializer,
            "to_representation",
            return_value={"asset": {"id": 0}},
        )
        result = api.serializers.AsaItemSerializer().to_representation(object())

        assert result == {"asset": {"id": 0}}


class TestOpenApiSchema:
    """The published contract has to describe what the endpoint actually sends."""

    @pytest.fixture(scope="class")
    def component(self):
        from drf_spectacular.generators import SchemaGenerator

        schema = SchemaGenerator().get_schema(request=None, public=True)
        return schema["components"]["schemas"]["UserAsaProgram"]

    @pytest.mark.parametrize(
        "field,expected_type", [("pid", "string"), ("pid_ambiguous", "boolean")]
    )
    def test_the_identifier_fields_are_published(self, component, field, expected_type):
        """Undocumented response fields are how a client library goes stale.

        Nothing else in this suite snapshots the schema, so without this a
        field could be added to the output and never described.
        """
        assert field in component["properties"], f"{field} is missing from the schema"
        assert component["properties"][field]["type"] == expected_type

    @pytest.mark.parametrize("field", ["pid", "pid_ambiguous"])
    def test_the_identifier_fields_are_read_only(self, component, field):
        """They are derived from the payload, never accepted from a client."""
        assert component["properties"][field]["readOnly"] is True

    @pytest.mark.parametrize("field", ["pid", "pid_ambiguous"])
    def test_the_identifier_fields_are_required(self, component, field):
        """Both are on every position, so a generated client may rely on them.

        This is the assertion that keeps `annotate_positions` writing the flag
        unconditionally: make it conditional again and the schema starts
        promising something the endpoint does not always send.
        """
        assert field in component["required"]
