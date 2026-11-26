"""A DAO provider with fixed data, named by ``DAO_PROVIDER`` in tests."""

import hashlib
import json

from core.dao_provider import DaoProvider

SEAT_A = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
SEAT_B = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
SEAT_C = "HKLGS7UL3W33J53KZ5SKOIRHDPPUVMVLEPZNDBVHHS5AEJ35TVKCD7NLMY"
PROPOSAL = b"Raise the fee.\n\nOption 0: yes\nOption 1: no\nOption 2: abstain\n"
CURRENT_ROUND = 5000
ZERO = "0" * 64


def _period(end_round, end_timestamp, seats):
    """Return a ``daosnapshot --to`` file for `seats` as {address: (total, venues)}."""
    return (
        json.dumps(
            {
                "start_round": 67_000_000,
                "end_round": end_round,
                "start_timestamp": 1_795_000_000,
                "end_timestamp": end_timestamp,
                "asset_id": 393537671,
                "seats": {
                    address: {"start_total": total, "total": total, "venues": venues}
                    for address, (total, venues) in seats.items()
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()


FINAL_1 = _period(
    67_200_000,
    1_795_560_000,
    {
        SEAT_A: (900_000_000, {"wallet": 900_000_000}),
        SEAT_B: (10_000_000, {"wallet": 10_000_000}),
    },
)
SOFAR_2 = _period(
    67_100_000,
    1_795_280_000,
    {
        SEAT_A: (
            50_000_000,
            {"gat 1047879402": 20_000_000, "lp 1234": 5_000_000, "wallet": 25_000_000},
        ),
        SEAT_B: (40_000_000, {"wallet": 40_000_000}),
    },
)


def _session(**values):
    session = {
        "start_round": 2000,
        "end_round": 9000,
        "seal_round": 9500,
        "options_count": 3,
        "abstain": 2,
        "quorum": 100_000_000,
        "threshold_num": 1,
        "threshold_den": 2,
        "proposal_hash": hashlib.sha256(PROPOSAL).hexdigest(),
        "final_hash": ZERO,
        "status": 0,
        "winner": 255,
        "voters_count": 0,
        "weighed_count": 0,
        "totals": [0, 0, 0],
    }
    session.update(values)
    return session


def _ballot(option, max_votes, eligible=0, weight=0, weighed=False):
    return {
        "option": option,
        "max_votes": max_votes,
        "eligible": eligible,
        "weight": weight,
        "weighed": weighed,
    }


SESSIONS = {
    1: _session(
        status=2,
        winner=0,
        final_hash=hashlib.sha256(FINAL_1).hexdigest(),
        voters_count=2,
        weighed_count=2,
        totals=[300_000_000, 10_000_000, 0],
    ),
    2: _session(voters_count=1),
    3: _session(start_round=9000, end_round=12000, seal_round=13000),
    4: _session(
        start_round=1000,
        end_round=4000,
        seal_round=6000,
        voters_count=2,
        weighed_count=1,
        totals=[10_000_000, 0, 0],
    ),
}
BALLOTS = {
    1: {
        SEAT_A: _ballot(0, 300, 900_000_000, 300_000_000, True),
        SEAT_B: _ballot(1, 20, 10_000_000, 10_000_000, True),
    },
    2: {SEAT_A: _ballot(0, 300)},
    3: {},
    4: {
        SEAT_A: _ballot(0, 300, 10_000_000, 10_000_000, True),
        SEAT_B: _ballot(2, 20),
    },
}
DOCUMENTS = {
    1: {"proposal.md": PROPOSAL, "final.json": FINAL_1},
    2: {"proposal.md": PROPOSAL, "sofar.json": SOFAR_2},
    4: {"proposal.md": PROPOSAL, "sofar.json": SOFAR_2},
}


class FakeProvider(DaoProvider):
    """Four sessions: passed, voting open, not started, weights under review."""

    network = "testnet"
    app_id = 775947805
    permission_app_id = 750094865

    def vote_method(self):
        return "vote(uint64,uint64)void"

    def available(self):
        return True

    def current_round(self):
        return CURRENT_ROUND

    def session_count(self):
        return len(SESSIONS)

    def session(self, session_id):
        return dict(SESSIONS[session_id]) if session_id in SESSIONS else None

    def ballots(self, session_id):
        return BALLOTS.get(session_id, {})

    def seat_votes(self):
        return {SEAT_A: 300, SEAT_B: 20, SEAT_C: 5}

    def document(self, session_id, name):
        return DOCUMENTS.get(session_id, {}).get(name)


class MainnetFakeProvider(FakeProvider):
    """The same data, read as if from mainnet."""

    network = "mainnet"
