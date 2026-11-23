"""ASA Stats DAO provider backed by the voting-dapp and permission-dapp submodules.

Imported only when ``settings.DAO_PROVIDER`` names it. Reads are cached (the
``DAO_*_CACHE_SECONDS`` settings) and boxes are read in parallel; see docs/logbook.md.
"""

import base64
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from algosdk.encoding import encode_address
from algosdk.v2client.algod import AlgodClient
from django.conf import settings
from django.core.cache import cache

from core.dao_provider import DaoProvider
from permissiondapp.dapp.helpers import deserialize_values_data, environment_variables
from votingdapp.dapp.configuration import VOTING_APP_ID, VOTING_APP_ID_TESTNET
from votingdapp.dapp.helpers import (
    ARTIFACTS,
    DAPP_NAME,
    decode_ballot,
    permission_dapp_id,
    read_json,
)
from votingdapp.dapp.network import _box_value, app_global_state, session_values

DOCUMENT_NAMES = ("proposal.md", "snapshot.json")
READ_WORKERS = 16  # box reads in flight at once against the node


class VotingDappProvider(DaoProvider):
    """Read the Voting dApp and the Permission dApp on ``settings.DAO_NETWORK``."""

    def __init__(self):
        self.network = getattr(settings, "DAO_NETWORK", "mainnet")
        self.app_id = (
            VOTING_APP_ID if self.network == "mainnet" else VOTING_APP_ID_TESTNET
        )
        self.permission_app_id = permission_dapp_id(self.network)
        self.timeout = getattr(settings, "DAO_CACHE_SECONDS", 30)
        self.seats_timeout = getattr(settings, "DAO_SEATS_CACHE_SECONDS", 600)
        self.sealed_timeout = getattr(settings, "DAO_SEALED_BALLOTS_CACHE_SECONDS", 86400)
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

    def _cached(self, key, read, timeout=None):
        """Return `read()`'s value, cached under a key unique to this dApp.

        :param key: cache key suffix
        :type key: str
        :param read: function doing the network read
        :type read: callable
        :param timeout: seconds to keep it, ``DAO_CACHE_SECONDS`` when omitted
        :type timeout: int
        :return: object
        """
        full_key = f"dao:{self.network}:{self.app_id}:{key}"
        value = cache.get(full_key)
        if value is None:
            value = read()
            cache.set(full_key, value, self.timeout if timeout is None else timeout)
        return value

    def _box_values(self, app_id, prefix=b""):
        """Return the raw values of `app_id`'s boxes whose names start with `prefix`.

        :param app_id: application identifier
        :type app_id: int
        :param prefix: box name prefix
        :type prefix: bytes
        :var names: matching box names
        :type names: list
        :return: dict
        """
        client = self._algod()
        names = [
            name
            for name in (
                base64.b64decode(box.get("name"))
                for box in client.application_boxes(app_id).get("boxes", [])
            )
            if name.startswith(prefix)
        ]
        if not names:
            return {}

        with ThreadPoolExecutor(min(READ_WORKERS, len(names))) as executor:
            values = executor.map(lambda name: _box_value(client, app_id, name), names)
            return {
                name: value for name, value in zip(names, values) if value is not None
            }

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

        def read():
            prefix = b"v" + session_id.to_bytes(8, "big")
            return {
                encode_address(name[len(prefix) :]): decode_ballot(value)
                for name, value in self._box_values(self.app_id, prefix).items()
            }

        session = self.session(session_id)
        if (
            session is None or session["status"] == 0
        ):  # snapshot writes don't touch the session box
            return self._cached(f"ballots:{session_id}", read)

        # sealed: ballots change only with a vote, and every vote changes the session box
        totals = ",".join(str(total) for total in session["totals"])
        key = (
            f"ballots:{session_id}:{session['status']}:{session['voters_count']}:{totals}"
        )
        return self._cached(key, read, self.sealed_timeout)

    def seat_votes(self):
        """Return every address with votes in the Permission dApp.

        :return: dict
        """

        def read():
            rows = {
                encode_address(name): deserialize_values_data(value.decode("utf8"))
                for name, value in self._box_values(self.permission_app_id).items()
            }
            return {
                address: row[0] for address, row in rows.items() if row and row[0] > 0
            }

        return self._cached("seats", read, self.seats_timeout)

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
