"""The vote panel: one card per seat the signed-in user has linked; see docs/logbook.md."""

import json

from daovoting.summary import MICRO, potential_weight
from walletauth.models import LinkedAddress


def linked_seats(user, seat_votes):
    """Return the user's Algorand-linked addresses that hold votes, sorted.

    The authorized profile address counts too: legacy profiles have no
    LinkedAddress row for it (logbook, 2026-11-25).

    :param user: requesting user
    :type user: :class:`django.contrib.auth.models.User`
    :param seat_votes: maximum votes keyed by seat address
    :type seat_votes: dict
    :return: list
    """
    if not getattr(user, "is_authenticated", False):
        return []
    addresses = set(
        LinkedAddress.objects.filter(profile__user=user, chain="algorand").values_list(
            "address", flat=True
        )
    )
    profile = getattr(user, "profile", None)
    if profile is not None and profile.address and profile.authorized:
        addresses.add(profile.algorand_address)
    return sorted(address for address in addresses if seat_votes.get(address, 0) > 0)


def snapshot_venues(snapshot):
    """Return each seat's venues from a published snapshot file, {} if unreadable.

    :param snapshot: content of ``snapshot.json`` (the engine's ``daosnapshot`` output)
    :type snapshot: bytes
    :return: dict
    """
    try:
        seats = json.loads(snapshot)["seats"]
        return {
            address: dict(values["venues"])
            for address, values in seats.items()
            if isinstance(values, dict) and isinstance(values.get("venues"), dict)
        }
    except (TypeError, ValueError, KeyError, AttributeError):
        return {}


def venue_label(name):
    """Return a reader's label for a snapshot venue key.

    :param name: ``wallet``, ``lp <token>`` or ``<code> <dApp>[ lp <token>]``
    :type name: str
    :return: str
    """
    if name == "wallet":
        return "Wallet"
    if name.startswith("lp "):
        return f"LP token {name[3:]}"
    return name


def vote_cards(seats, rows, seat_votes, venues):
    """Return one card per seat: votes, snapshot amount, venues, weight, own ballot.

    :param seats: the user's seat addresses
    :type seats: list
    :param rows: the session summary's ballot rows
    :type rows: list
    :param seat_votes: maximum votes keyed by seat address
    :type seat_votes: dict
    :param venues: venues keyed by seat, from a snapshot file that matches the chain
    :type venues: dict
    :return: list
    """
    by_address = {row["address"]: row for row in rows}
    cards = []
    for address in seats:
        votes = seat_votes[address]
        row = by_address.get(address)
        card = {"address": address, "votes": votes, "in_snapshot": row is not None}
        if row is not None:
            card.update(
                {
                    "eligible": row["eligible"],
                    "weight": potential_weight(row["eligible"], votes),
                    "below_max": row["eligible"] < votes * MICRO,
                    "voted_option": row["option"] if row["voted"] else None,
                    "venues": [
                        {"name": venue_label(name), "amount": amount}
                        for name, amount in venues.get(address, {}).items()
                    ],
                }
            )
        cards.append(card)
    return cards
