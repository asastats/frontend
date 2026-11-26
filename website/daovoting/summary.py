"""Render-ready values computed from the Voting dApp's boxes; no network here."""

import hashlib
import json

MICRO = 1_000_000
NOT_VOTED = 255
ROUNDS_PER_DAY = 31_900  # testnet, measured 2026-11-26 (docs/logbook.md)
EMPTY_HASH = "0" * 64

STATUS_OPEN, STATUS_SEALED, STATUS_PASSED, STATUS_FAILED = 0, 1, 2, 3

#: phase key -> label; the keys are asserted by the functional tests
PHASES = {
    "upcoming": "Voting not started",
    "voting": "Voting open",
    "weighing": "Voting ended, weights under review",
    "sealed": "Weights sealed, result not recorded",
    "passed": "Passed",
    "failed": "Failed",
}


def phase(session, current_round):
    """Return the phase key of `session` at `current_round`.

    :param session: decoded session box
    :type session: dict
    :param current_round: latest round, None if unknown
    :type current_round: int
    :return: str
    """
    status = session["status"]
    if status == STATUS_PASSED:
        return "passed"
    if status == STATUS_FAILED:
        return "failed"
    if status == STATUS_SEALED:
        return "sealed"
    now = current_round or 0
    if now < session["start_round"]:
        return "upcoming"
    return "voting" if now <= session["end_round"] else "weighing"


def countdown(target_round, current_round):
    """Return rounds and approximate days until `target_round`, None if past.

    :param target_round: round to count down to
    :type target_round: int
    :param current_round: latest round, None if unknown
    :type current_round: int
    :return: dict
    """
    if current_round is None or target_round <= current_round:
        return None
    rounds = target_round - current_round
    return {"rounds": rounds, "days": round(rounds / ROUNDS_PER_DAY, 1)}


def potential_weight(amount, votes):
    """Return min(votes × 10⁶, amount), the weight a seat's lowest amount gives.

    :param amount: lowest micro-ASASTATS held
    :type amount: int
    :param votes: the seat's maximum votes
    :type votes: int
    :return: int
    """
    return min(votes * MICRO, amount)


def hash_check(document, onchain_hash):
    """Return how a published file compares with its on-chain sha256.

    :param document: file content, None if not published on this site
    :type document: bytes
    :param onchain_hash: hex sha256 stored in the session box
    :type onchain_hash: str
    :return: str, one of "unset", "missing", "match", "differs"
    """
    if onchain_hash == EMPTY_HASH:
        return "unset"
    if document is None:
        return "missing"
    return "match" if hashlib.sha256(document).hexdigest() == onchain_hash else "differs"


def period_file(document):
    """Return a published final or so-far file's rounds and seats, None if unreadable.

    :param document: content of ``final.json`` or ``sofar.json`` (``daosnapshot --to``)
    :type document: bytes
    :return: dict
    """
    try:
        data = json.loads(document)
        seats = {
            address: {"total": int(values["total"]), "venues": dict(values["venues"])}
            for address, values in data["seats"].items()
        }
        return {
            "end_round": int(data["end_round"]),
            "end_timestamp": int(data.get("end_timestamp") or 0),
            "seats": seats,
        }
    except (TypeError, ValueError, KeyError, AttributeError):
        return None


def ballot_rows(ballots, seat_votes, amounts):
    """Return one row per seat with votes or a ballot, the most votes first.

    A written final amount wins; otherwise the weight comes from `amounts` (the
    so-far file) as an upper bound, and is None without it.

    :param ballots: decoded ballots keyed by seat address
    :type ballots: dict
    :param seat_votes: maximum votes keyed by seat address
    :type seat_votes: dict
    :param amounts: lowest micro-ASASTATS so far keyed by seat, None if unknown
    :type amounts: dict
    :return: list
    """
    rows = []
    for address in set(seat_votes) | set(ballots):
        ballot = ballots.get(address)
        votes = ballot["max_votes"] if ballot else seat_votes.get(address, 0)
        row = {
            "address": address,
            "voted": ballot is not None,
            "option": ballot["option"] if ballot else None,
            "max_votes": votes,
            "final": bool(ballot and ballot["weighed"]),
            "amount": None,
            "weight": None,
        }
        if row["final"]:
            row.update({"amount": ballot["eligible"], "weight": ballot["weight"]})
        elif amounts is not None:
            amount = amounts.get(address, 0)
            row.update({"amount": amount, "weight": potential_weight(amount, votes)})
        rows.append(row)
    return sorted(rows, key=lambda row: (-row["max_votes"], row["address"]))


def _provisional_totals(rows, options_count):
    """Return the so-far totals per option from the voters' rows.

    :param rows: ballot rows
    :type rows: list
    :param options_count: number of options
    :type options_count: int
    :return: list
    """
    totals = [0] * options_count
    for row in rows:
        if row["voted"] and row["weight"] is not None and row["option"] < options_count:
            totals[row["option"]] += row["weight"]
    return totals


def session_summary(session_id, session, ballots, seat_votes, current_round, sofar=None):
    """Return everything the index and session pages show about one session.

    Before any final amount is written, the totals are those of the so-far file
    (`provisional`, an upper bound), or unknown without one.

    :param session_id: voting session identifier
    :type session_id: int
    :param session: decoded session box
    :type session: dict
    :param ballots: decoded ballots keyed by seat address
    :type ballots: dict
    :param seat_votes: maximum votes keyed by seat address
    :type seat_votes: dict
    :param current_round: latest round, None if unknown
    :type current_round: int
    :param sofar: the published so-far file, read by :func:`period_file`
    :type sofar: dict
    :return: dict
    """
    key = phase(session, current_round)
    on_chain = session["status"] != STATUS_OPEN or session["weighed_count"] > 0
    amounts = None
    if sofar is not None and not on_chain:
        amounts = {address: seat["total"] for address, seat in sofar["seats"].items()}
    rows = ballot_rows(ballots, seat_votes, amounts)
    if on_chain:
        totals = session["totals"]
    elif amounts is not None:
        totals = _provisional_totals(rows, session["options_count"])
    else:
        totals = None

    turnout = sum(totals) if totals is not None else None
    weights = [row["weight"] for row in rows if row["weight"] is not None]
    possible = sum(weights) if weights else None
    abstain = session["abstain"]
    options = [
        {
            "index": index,
            "abstain": index == abstain,
            "total": total,
            "share": round(100 * total / turnout, 2) if turnout else 0,
            "winner": key == "passed" and index == session["winner"],
        }
        for index, total in enumerate(totals or [None] * session["options_count"])
    ]
    quorum = session["quorum"]
    return {
        "id": session_id,
        "phase": key,
        "phase_label": PHASES[key],
        "session": session,
        "options": options,
        "rows": rows,
        "seats": len(rows),
        "voters": session["voters_count"],
        "weighed": session["weighed_count"],
        "provisional": totals is not None and not on_chain,
        "sofar_round": sofar["end_round"] if amounts is not None else None,
        "sofar_timestamp": sofar["end_timestamp"] if amounts is not None else None,
        "turnout": turnout,
        "possible": possible,
        "turnout_share": (
            round(100 * turnout / possible, 2) if turnout is not None and possible else 0
        ),
        "quorum": quorum,
        "quorum_share": (
            min(100, round(100 * turnout / quorum, 2)) if quorum and turnout else 0
        ),
        "threshold": f"{session['threshold_num']}/{session['threshold_den']}",
        "has_abstain": abstain < session["options_count"],
        "to_start": countdown(session["start_round"], current_round),
        "to_end": countdown(session["end_round"] + 1, current_round),
        "to_seal": countdown(session["seal_round"], current_round),
    }


def governor_rows(seat_votes, sessions_ballots):
    """Return one row per seat: votes and the sessions it voted in.

    :param seat_votes: maximum votes keyed by seat address
    :type seat_votes: dict
    :param sessions_ballots: ballots keyed by session id, then by seat address
    :type sessions_ballots: dict
    :return: list
    """
    rows = [
        {
            "address": address,
            "votes": votes,
            "voted": [
                sid
                for sid in sorted(sessions_ballots)
                if address in sessions_ballots[sid]
            ],
        }
        for address, votes in seat_votes.items()
    ]
    return sorted(rows, key=lambda row: (-row["votes"], row["address"]))
