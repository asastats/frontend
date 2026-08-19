"""Stable identifiers for the positions inside an asset.

A position is one row in an asset's breakdown: a balance, an LP stake, a
deposit, a borrow. The address page needs to name one and still find it after a
refresh -- to pin it to the top, to remember it was expanded, to link to it --
and neither of the obvious handles works. Its value changes with the price, and
its index changes whenever the ranking does.

So the identifier is built from what the position *is*. Six fields describe it,
and on the real 76-asset bundle that is enough for 185 of 190 positions. The
remaining five are not hard to tell apart, they are **indistinguishable**: two
Pact ALGO-ASASTATS liquidity positions, two Lofty AMM entries, two Cometa
stakes, two Gora.fi validator delegations, each pair identical in type, name,
provider, code and link.

Two of those five are recoverable here. A Pact liquidity position carries a
``Source LP token`` in its ``linked`` data, and the two positions hold different
LP tokens -- 1129173576 against 2757667448. Promoting that asset id into the
identifier separates them, and takes the bundle to 187 distinct ids.

The other three cannot be fixed at this layer and are **not papered over**. An
ordinal suffix would make them unique and unstable: two Cometa stakes ranked by
value swap places the moment their values cross, and a pin would then point at
the other position with nothing to show that it had moved. Silently wrong beats
noisily unknown only if nobody is relying on it. They are flagged instead, so
the page can say so and the engine team can see exactly which providers need to
emit a discriminator -- an application id, an escrow address, a position index.

.. note::
   ``PID_VERSION`` is part of every identifier. Changing what goes into the
   hash changes every id, which would silently invalidate saved pins; bumping
   the version makes them recognisably stale instead of quietly wrong.
"""

from hashlib import blake2s

#: Bumped whenever the recipe below changes, so stored ids that no longer mean
#: what they meant can be detected rather than mismatched.
PID_VERSION = "p1"

#: Bytes of digest kept. 8 bytes is 16 hex characters: ample for a few hundred
#: positions, short enough to sit in a URL fragment or a localStorage key.
_DIGEST_BYTES = 8

#: `linked` entries whose `id` identifies the position rather than describing
#: it. A Pact liquidity position is only distinguishable by its LP token.
_IDENTIFYING_LINK_TEXTS = frozenset({"Source LP token"})


def _discriminators(asset_id, program):
    """Ordered parts that describe one position.

    :param asset_id: the asset the position belongs to
    :type asset_id: int | str
    :param program: one serialized entry from an asset's ``programs``
    :type program: dict
    :return: list of str
    """
    detail = program.get("program") or {}
    provider = detail.get("provider") or {}
    parts = [
        str(asset_id),
        detail.get("type") or "",
        detail.get("name") or "",
        provider.get("name") or "",
        detail.get("code") or "",
        detail.get("url") or "",
    ]
    # Sorted, because `linked` order is the engine's business and a reordering
    # there must not change the identity of the position.
    parts.extend(
        sorted(
            str(link["id"])
            for link in (program.get("linked") or [])
            if link.get("id") is not None and link.get("text") in _IDENTIFYING_LINK_TEXTS
        )
    )
    return parts


def position_id(asset_id, program):
    """Return the stable identifier for one position.

    :param asset_id: the asset the position belongs to
    :type asset_id: int | str
    :param program: one serialized entry from an asset's ``programs``
    :type program: dict
    :return: str
    """
    payload = "\x1f".join(_discriminators(asset_id, program)).encode()
    digest = blake2s(payload, digest_size=_DIGEST_BYTES).hexdigest()
    return f"{PID_VERSION}-{asset_id}-{digest}"


def annotate_positions(asset_id, programs):
    """Give every program a ``pid`` and a ``pid_ambiguous``.

    Mutates in place and returns the same list, so it can be dropped into a
    serializer's ``to_representation`` without rebuilding the structure.

    :param asset_id: the asset the positions belong to
    :type asset_id: int | str
    :param programs: an asset's serialized ``programs``
    :type programs: list
    :return: list
    """
    if not programs:
        return programs

    for program in programs:
        program["pid"] = position_id(asset_id, program)

    counts = {}
    for program in programs:
        counts[program["pid"]] = counts.get(program["pid"], 0) + 1

    for program in programs:
        # Deliberately a flag rather than a suffix: see the module docstring. A
        # consumer that pins this position has to be told it may not be able to
        # find its way back to this exact row.
        #
        # Always written, never omitted. The rest of this API drops empty
        # values, but a flag that is absent when false forces every consumer to
        # tell "not ambiguous" apart from "this build does not report it", and
        # the OpenAPI schema would have to describe it as optional when the
        # only reason it is missing is that the answer was no.
        program["pid_ambiguous"] = counts[program["pid"]] > 1

    return programs
