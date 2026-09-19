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


#: The fields a position is identified by, in the order they are hashed.
#:
#: **Named here and nowhere else.** The live pass has to identify the same
#: position from the engine's own structures, which are not the serialized shape
#: `_discriminators` reads - so it sends the fields and this module puts them in
#: order. Were the order duplicated on the engine's side, a reordering would
#: produce ids that hash differently, match no element on the page, and show up
#: only as fragments that quietly land nowhere.
IDENTIFYING_FIELDS = ("type", "name", "provider", "code", "url")


def _parts(asset_id, fields, link_ids):
    """Return the ordered parts that describe one position.

    :param asset_id: the asset the position belongs to
    :type asset_id: int | str
    :param fields: the values of `IDENTIFYING_FIELDS`, keyed by field name
    :type fields: dict
    :param link_ids: ids of `linked` entries that identify rather than describe
    :type link_ids: iterable
    :return: list of str
    """
    parts = [str(asset_id)]
    parts.extend(str(fields.get(name) or "") for name in IDENTIFYING_FIELDS)
    # Sorted, because `linked` order is the engine's business and a reordering
    # there must not change the identity of the position.
    parts.extend(sorted(str(value) for value in link_ids))
    return parts


def _discriminators(asset_id, program):
    """Ordered parts that describe one position, from a serialized program.

    :param asset_id: the asset the position belongs to
    :type asset_id: int | str
    :param program: one serialized entry from an asset's ``programs``
    :type program: dict
    :return: list of str
    """
    detail = program.get("program") or {}
    provider = detail.get("provider") or {}
    return _parts(
        asset_id,
        {
            "type": detail.get("type"),
            "name": detail.get("name"),
            "provider": provider.get("name"),
            "code": detail.get("code"),
            "url": detail.get("url"),
        },
        (
            link["id"]
            for link in (program.get("linked") or [])
            if link.get("id") is not None
            and link.get("text") in _IDENTIFYING_LINK_TEXTS
        ),
    )


def _hash(asset_id, parts):
    """Return the identifier for already-ordered `parts`."""
    payload = "\x1f".join(parts).encode()
    digest = blake2s(payload, digest_size=_DIGEST_BYTES).hexdigest()
    return f"{PID_VERSION}-{asset_id}-{digest}"


def position_id(asset_id, program):
    """Return the stable identifier for one position.

    :param asset_id: the asset the position belongs to
    :type asset_id: int | str
    :param program: one serialized entry from an asset's ``programs``
    :type program: dict
    :return: str
    """
    return _hash(asset_id, _discriminators(asset_id, program))


def identifying_link_ids(links):
    """Return the ids among `links` that identify a position rather than describe it.

    **The rule lives here, which is the point of taking the engine's links
    whole.** It sends every linked id with its text and this decides which of
    them counts - so "a Pact liquidity position is only distinguishable by its
    LP token" stays written down once, and promoting a second kind of link never
    needs an engine release to match.

    :param links: `[[text, id], ...]` as the live payload carries them
    :type links: iterable
    :return: list
    """
    return [
        link_id
        for text, link_id in links or ()
        if text in _IDENTIFYING_LINK_TEXTS
    ]


def position_id_from_fields(asset_id, fields, link_ids=()):
    """Return the identifier for a position described by its fields alone.

    **For the live pass, which never serializes.** `_live_payload` works from
    the engine's own structures because serializing an account every block per
    page is the cost that design exists to avoid - so it cannot hand
    :func:`position_id` the shape that function reads. It sends the identifying
    fields by name instead, and this puts them in order and hashes them.

    The field *names* are the contract; their order is not, and deliberately:
    a name that stops matching fails loudly on the way in, while an order that
    drifts would produce a perfectly valid id for a position nothing on the page
    is called - fragments landing nowhere, which is the failure that hides
    longest.

    Both paths meet at :func:`_parts`, so an id built here and an id built from
    a serialized program are the same id for the same position. The test suite
    pins that against the real bundle rather than trusting it.

    :param asset_id: the asset the position belongs to
    :type asset_id: int | str
    :param fields: values of `IDENTIFYING_FIELDS`, keyed by field name
    :type fields: dict
    :param link_ids: ids of `linked` entries that identify the position
    :type link_ids: iterable
    :return: str
    """
    return _hash(asset_id, _parts(asset_id, fields, link_ids))


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
