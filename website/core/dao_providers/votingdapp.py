"""ASA Stats DAO provider backed by the voting-dapp and permission-dapp submodules.

Imported only when ``settings.DAO_PROVIDER`` names it. Reads are cached for
``settings.DAO_CACHE_SECONDS``; see docs/logbook.md.
"""

from pathlib import Path

from algosdk.v2client.algod import AlgodClient
from django.conf import settings
from django.core.cache import cache

from core.dao_provider import DaoProvider
from permissiondapp.dapp.helpers import environment_variables
from permissiondapp.dapp.network import permission_dapp_values_from_boxes
from votingdapp.dapp.configuration import VOTING_APP_ID, VOTING_APP_ID_TESTNET
from votingdapp.dapp.helpers import (
    ARTIFACTS,
    DAPP_NAME,
    permission_dapp_id,
    read_json,
)
from votingdapp.dapp.network import (
    app_global_state,
    session_ballots,
    session_values,
)

DOCUMENT_NAMES = ("proposal.md", "snapshot.json")


class VotingDappProvider(DaoProvider):
    """Read the Voting dApp and the Permission dApp on ``settings.DAO_NETWORK``."""

    def __init__(self):
        self.network = getattr(settings, "DAO_NETWORK", "mainnet")
        self.app_id = (
            VOTING_APP_ID if self.network == "mainnet" else VOTING_APP_ID_TESTNET
        )
        self.permission_app_id = permission_dapp_id(self.network)
        self.timeout = getattr(settings, "DAO_CACHE_SECONDS", 30)
        self._client = None
        self._vote_method = None

    def _algod(self):
        """Return the algod client for the configured network, built once.

        :var env: permission-dApp environment variables
        :type env: dict
        :return: :class:`AlgodClient`
        """
        if self._client is None:
            env = environment_variables()
            self._client = AlgodClient(
                env.get(f"algod_token_{self.network}") or "",
                env.get(f"algod_address_{self.network}"),
            )
        return self._client

    def _cached(self, key, read):
        """Return `read()`'s value, cached under a key unique to this dApp.

        :param key: cache key suffix
        :type key: str
        :param read: function doing the network read
        :type read: callable
        :return: object
        """
        full_key = f"dao:{self.network}:{self.app_id}:{key}"
        value = cache.get(full_key)
        if value is None:
            value = read()
            cache.set(full_key, value, self.timeout)
        return value

    def available(self):
        """Return True if the Voting dApp is deployed on the configured network.

        :return: Boolean
        """
        return self.app_id is not None

    def current_round(self):
        """Return the network's latest round.

        :return: int
        """
        return self._cached("round", lambda: self._algod().status().get("last-round"))

    def session_count(self):
        """Return the dApp's `session_count` global.

        :return: int
        """
        if not self.available():
            return 0
        return self._cached(
            "count",
            lambda: app_global_state(self._algod(), self.app_id).get("session_count", 0),
        )

    def session(self, session_id):
        """Return the decoded session box, None if there is no such session.

        :param session_id: voting session identifier
        :type session_id: int
        :return: dict
        """
        if not self.available() or not 0 < session_id <= self.session_count():
            return None
        return self._cached(
            f"session:{session_id}",
            lambda: session_values(self._algod(), self.app_id, session_id),
        )

    def ballots(self, session_id):
        """Return the session's decoded ballots keyed by seat address.

        :param session_id: voting session identifier
        :type session_id: int
        :return: dict
        """
        if not self.available():
            return {}
        return self._cached(
            f"ballots:{session_id}",
            lambda: session_ballots(self._algod(), self.app_id, session_id),
        )

    def seat_votes(self):
        """Return every address with votes in the Permission dApp.

        :return: dict
        """

        def read():
            values = permission_dapp_values_from_boxes(
                self._algod(), permission_dapp_id(self.network)
            )
            return {address: row[0] for address, row in values.items() if row[0] > 0}

        return self._cached("seats", read)

    def vote_method(self):
        """Return `vote`'s ARC-4 signature from the committed ARC-56 file, read once.

        :var spec: the ARC-56 entry of the `vote` method
        :type spec: dict
        :return: str
        """
        if self._vote_method is None:
            contract = read_json(ARTIFACTS / f"{DAPP_NAME}.arc56.json")
            spec = next(m for m in contract["methods"] if m["name"] == "vote")
            arguments = ",".join(argument["type"] for argument in spec["args"])
            self._vote_method = f"vote({arguments}){spec['returns']['type']}"
        return self._vote_method

    def document(self, session_id, name):
        """Return a published file from ``DAO_DOCUMENTS_DIR/<session id>/``.

        :param session_id: voting session identifier
        :type session_id: int
        :param name: one of :data:`DOCUMENT_NAMES`
        :type name: str
        :return: bytes, or None
        """
        folder = getattr(settings, "DAO_DOCUMENTS_DIR", "")
        if not folder or name not in DOCUMENT_NAMES:
            return None
        path = Path(folder) / str(session_id) / name
        return path.read_bytes() if path.is_file() else None
