"""Render-ready values computed from the Voting dApp's boxes; no network here."""

import hashlib

MICRO = 1_000_000
NOT_VOTED = 255
ROUNDS_PER_DAY = 30_000  # the Voting dApp README's figure
EMPTY_HASH = "0" * 64

STATUS_SNAPSHOT_OPEN, STATUS_SEALED, STATUS_PASSED, STATUS_FAILED = 0, 1, 2, 3

#: phase key -> label; the keys are asserted by the functional tests
PHASES = {
    "snapshot": "Snapshot not taken yet",
    "review": "Snapshot under review",
    "lapsed": "Not sealed before the start, no voting",
    "sealed": "Snapshot sealed, voting not started",
    "voting": "Voting open",
    "ended": "Voting ended, result not recorded",
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
    now = current_round or 0
    if status == STATUS_SNAPSHOT_OPEN:
        if now >= session["start_round"]:
            return "lapsed"  # the contract refuses both the seal and votes now
        return "snapshot" if now < session["snapshot_round"] else "review"
    if now < session["start_round"]:
        return "sealed"
    return "voting" if now <= session["end_round"] else "ended"


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


def potential_weight(eligible, votes):
    """Return a seat's weight if it voted now: min(votes × 10⁶, eligible).

    :param eligible: micro-ASASTATS in the snapshot
    :type eligible: int
    :param votes: the seat's maximum votes
    :type votes: int
    :return: int
    """
    return min(votes * MICRO, eligible)


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


def ballot_rows(ballots, seat_votes):
    """Return one row per seat in the snapshot, the largest eligible first.

    :param ballots: decoded ballots keyed by seat address
    :type ballots: dict
    :param seat_votes: maximum votes keyed by seat address
    :type seat_votes: dict
    :return: list
    """
    rows = []
    for address, ballot in ballots.items():
        voted = ballot["option"] != NOT_VOTED
        rows.append(
            {
                "address": address,
                "eligible": ballot["eligible"],
                "voted": voted,
                "option": ballot["option"] if voted else None,
                "max_votes": ballot["max_votes"] if voted else seat_votes.get(address, 0),
                "weight": (
                    ballot["weight"]
                    if voted
                    else potential_weight(ballot["eligible"], seat_votes.get(address, 0))
                ),
            }
        )
    return sorted(rows, key=lambda row: (-row["eligible"], row["address"]))


def session_summary(session_id, session, ballots, seat_votes, current_round):
    """Return everything the index and session pages show about one session.

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
    :return: dict
    """
    rows = ballot_rows(ballots, seat_votes)
    turnout = sum(session["totals"])
    possible = sum(row["weight"] for row in rows)
    key = phase(session, current_round)
    options = [
        {
            "index": index,
            "total": total,
            "share": round(100 * total / turnout, 2) if turnout else 0,
            "winner": key == "passed" and index == session["winner"],
        }
        for index, total in enumerate(session["totals"])
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
        "turnout": turnout,
        "possible": possible,
        "turnout_share": round(100 * turnout / possible, 2) if possible else 0,
        "quorum": quorum,
        "quorum_share": min(100, round(100 * turnout / quorum, 2)) if quorum else 100,
        "threshold": f"{session['threshold_num']}/{session['threshold_den']}",
        "to_snapshot": countdown(session["snapshot_round"], current_round),
        "to_start": countdown(session["start_round"], current_round),
        "to_end": countdown(session["end_round"] + 1, current_round),
    }


def governor_rows(seat_votes, sessions_ballots):
    """Return one row per seat: votes, latest snapshot amount, participation.

    :param seat_votes: maximum votes keyed by seat address
    :type seat_votes: dict
    :param sessions_ballots: ballots keyed by session id, then by seat address
    :type sessions_ballots: dict
    :return: list
    """
    latest = max(
        (sid for sid, ballots in sessions_ballots.items() if ballots), default=None
    )
    rows = []
    for address, votes in seat_votes.items():
        in_snapshot = [
            sid for sid in sorted(sessions_ballots) if address in sessions_ballots[sid]
        ]
        voted = [
            sid
            for sid in in_snapshot
            if sessions_ballots[sid][address]["option"] != NOT_VOTED
        ]
        eligible = (
            sessions_ballots[latest].get(address, {}).get("eligible", 0)
            if latest is not None
            else None
        )
        rows.append(
            {
                "address": address,
                "votes": votes,
                "eligible": eligible,
                "in_snapshot": in_snapshot,
                "voted": voted,
            }
        )
    return sorted(rows, key=lambda row: (-row["votes"], row["address"])), latest
