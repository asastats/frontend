"""A DAO provider with fixed data, named by ``DAO_PROVIDER`` in tests."""

import hashlib

from core.dao_provider import DaoProvider

SEAT_A = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
SEAT_B = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
SEAT_C = "HKLGS7UL3W33J53KZ5SKOIRHDPPUVMVLEPZNDBVHHS5AEJ35TVKCD7NLMY"
PROPOSAL = b"Raise the fee.\n\nOption 0: yes\nOption 1: no\n"
SNAPSHOT = (
    b'{"snapshot_round": 1000, "asset_id": 393537671, "seats": {'
    b'"VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU": {"total": 50000000,'
    b' "venues": {"gat 1047879402": 20000000, "lp 1234": 5000000, "wallet": 25000000}},'
    b' "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU": {"total": 40000000,'
    b' "venues": {"wallet": 40000000}}}}\n'
)
CURRENT_ROUND = 5000
ZERO = "0" * 64


def _session(**values):
    session = {
        "snapshot_round": 1000,
        "snapshot_hash": hashlib.sha256(SNAPSHOT).hexdigest(),
        "start_round": 2000,
        "end_round": 9000,
        "options_count": 2,
        "quorum": 100_000_000,
        "threshold_num": 1,
        "threshold_den": 2,
        "proposal_hash": hashlib.sha256(PROPOSAL).hexdigest(),
        "status": 1,
        "winner": 255,
        "voters_count": 1,
        "totals": [50_000_000, 0],
    }
    session.update(values)
    return session


SESSIONS = {
    1: _session(status=2, winner=0, totals=[300_000_000, 10_000_000], voters_count=2),
    2: _session(),
    3: _session(
        snapshot_round=8000,
        start_round=9000,
        end_round=12000,
        status=0,
        snapshot_hash=ZERO,
        voters_count=0,
        totals=[0, 0],
    ),
}
BALLOTS = {
    1: {
        SEAT_A: {
            "eligible": 900_000_000,
            "option": 0,
            "max_votes": 300,
            "weight": 300_000_000,
        },
        SEAT_B: {
            "eligible": 10_000_000,
            "option": 1,
            "max_votes": 20,
            "weight": 10_000_000,
        },
    },
    2: {
        SEAT_A: {
            "eligible": 50_000_000,
            "option": 0,
            "max_votes": 300,
            "weight": 50_000_000,
        },
        SEAT_B: {"eligible": 40_000_000, "option": 255, "max_votes": 0, "weight": 0},
    },
    3: {},
}


class FakeProvider(DaoProvider):
    """Three sessions: passed, voting open, snapshot not taken yet."""

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
        if session_id in (1, 2):
            return {"proposal.md": PROPOSAL, "snapshot.json": SNAPSHOT}.get(name)
        return None


class MainnetFakeProvider(FakeProvider):
    """The same data, read as if from mainnet."""

    network = "mainnet"
