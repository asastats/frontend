"""Chain-agnostic wallet proof verifiers.

Every supported chain implements the same shape: given the address being
authorized plus the issued ``nonce``/``prefix`` and the raw request ``payload``,
return the proven **Algorand** address on success or ``None`` on failure. For
Algorand the proven address is the signer's own address; for the deferred EVM
path it will be the xChain-derived Algorand counterpart, so the existing
permission/portfolio model applies unchanged either way.
"""

import base64
import logging

import msgpack
from algosdk.transaction import SignedTransaction

from utils.clients import algod_instance
from utils.constants.core import MAINNET_GENESIS_HASH, MAINNET_GENESIS_ID
from walletauth.crypto import verify_signed_transaction

logger = logging.getLogger(__name__)

#: Upper bound on the base64 signed-transaction payload. A signed 0-ALGO
#: self-payment carrying the nonce is a few hundred bytes; this generous cap
#: rejects oversized payloads before base64/msgpack decoding (defense in depth;
#: Django's DATA_UPLOAD_MAX_MEMORY_SIZE already bounds the request body).
MAX_SIGNED_TXN_B64_LENGTH = 2048


class NotSupported(Exception):
    """Raised when a verifier for a recognized chain is not yet enabled."""


class WalletProofVerifier:
    """Interface: prove that a signed challenge demonstrates control of an address.

    Subclasses implement :meth:`recover`, which validates a chain-specific proof
    and returns the **proven Algorand address** that produced it (the signer's
    own address for Algorand; the xChain-derived counterpart for EVM). The
    shared :meth:`verify` wraps :meth:`recover` for the authorize flow, where the
    expected address is already known; the login flow calls :meth:`recover`
    directly and resolves the account from whatever address signed.
    """

    def recover(self, *, nonce, prefix, payload):
        """Validate the proof and return the proven address, or ``None``.

        :param nonce: server-issued single-use challenge
        :type nonce: str
        :param prefix: domain-scoped nonce prefix
        :type prefix: str
        :param payload: raw request data (chain-specific proof fields)
        :type payload: dict
        :return: proven Algorand address or None
        :rtype: str | None
        """
        raise NotImplementedError

    def verify(self, *, address, nonce, prefix, payload):
        """Return ``address`` when the proof proves control of it, else ``None``.

        :param address: address the user is trying to authorize
        :type address: str
        :param nonce: server-issued single-use challenge
        :type nonce: str
        :param prefix: domain-scoped nonce prefix
        :type prefix: str
        :param payload: raw request data (chain-specific proof fields)
        :type payload: dict
        :var proven: address recovered from the proof, if any
        :type proven: str | None
        :return: ``address`` when ``recover`` returns it, else None
        :rtype: str | None
        """
        proven = self.recover(nonce=nonce, prefix=prefix, payload=payload)
        return proven if proven == address else None


class AlgorandSignedTxnVerifier(WalletProofVerifier):
    """Verify a signed 0-ALGO self-payment carrying the nonce in its note.

    Rekeyed accounts are supported: when the signed transaction claims an
    authorizing address that differs from the sender, the claim is confirmed
    against on-chain ``auth-addr`` state via algod before the signature is
    trusted. A fabricated rekey claim is therefore rejected.
    """

    def __init__(
        self,
        *,
        expected_genesis_id=MAINNET_GENESIS_ID,
        expected_genesis_hash=MAINNET_GENESIS_HASH,
        algod_factory=algod_instance,
    ):
        """Configure network pinning and the algod client factory.

        :param expected_genesis_id: genesis id the transaction must declare, or
            a falsy value to skip the check
        :type expected_genesis_id: str
        :param expected_genesis_hash: base64 genesis hash the transaction must
            declare, or a falsy value to skip the check
        :type expected_genesis_hash: str
        :param algod_factory: zero-argument callable returning an algod client,
            used only to confirm rekey claims
        :type algod_factory: collections.abc.Callable
        """
        self.expected_genesis_id = expected_genesis_id
        self.expected_genesis_hash = expected_genesis_hash
        self.algod_factory = algod_factory

    def recover(self, *, nonce, prefix, payload):
        """Validate the Algorand proof and return the signer's address.

        :param nonce: server-issued single-use challenge
        :type nonce: str
        :param prefix: domain-scoped nonce prefix
        :type prefix: str
        :param payload: raw request data; must carry ``signedTransaction``
        :type payload: dict
        :var signed_b64: base64-encoded signed transaction from the payload
        :type signed_b64: str
        :var raw: msgpack bytes decoded from ``signed_b64``
        :type raw: bytes
        :var stxn: reconstructed signed transaction
        :type stxn: :class:`algosdk.transaction.SignedTransaction`
        :var txn: the inner (unsigned) transaction being inspected
        :type txn: :class:`algosdk.transaction.Transaction`
        :var sender: the self-payment sender, returned as the proven address
        :type sender: str
        :return: the proven (sender) address when valid, else None
        :rtype: str | None
        """
        signed_b64 = payload.get("signedTransaction")
        if not signed_b64:
            logger.warning("walletauth: missing signedTransaction in payload")
            return None
        if len(signed_b64) > MAX_SIGNED_TXN_B64_LENGTH:
            logger.warning("walletauth: oversized signedTransaction payload rejected")
            return None

        try:
            raw = base64.b64decode(signed_b64)
            stxn = SignedTransaction.undictify(msgpack.unpackb(raw))
        except Exception:  # noqa: BLE001 - any decode failure is a rejected proof
            logger.warning("walletauth: undecodable signed transaction")
            return None

        txn = stxn.transaction

        if not self._shape_ok(txn):
            return None
        sender = txn.sender
        if not self._note_ok(txn, prefix, nonce):
            logger.warning("walletauth: note mismatch for %s", _short(sender))
            return None
        if not self._network_ok(txn):
            logger.warning("walletauth: genesis mismatch for %s", _short(sender))
            return None
        if not self._signature_ok(stxn):
            logger.warning("walletauth: signature rejected for %s", _short(sender))
            return None

        return sender

    # -- individual checks -------------------------------------------------

    @staticmethod
    def _shape_ok(txn):
        """Require a 0-amount self-payment (sender == receiver).

        The sender is the proven identity, so binding sender to a specific
        address is the caller's concern (``verify`` for authorize); here we only
        require that the proof is a zero-value self-payment.

        :param txn: transaction to inspect
        :type txn: :class:`algosdk.transaction.Transaction`
        :return: Boolean
        """
        sender = getattr(txn, "sender", None)
        return (
            getattr(txn, "type", None) == "pay"
            and getattr(txn, "amt", 0) == 0
            and bool(sender)
            and getattr(txn, "receiver", None) == sender
        )

    @staticmethod
    def _note_ok(txn, prefix, nonce):
        """Require the note to equal exactly ``prefix + nonce``.

        :param txn: transaction whose note is checked
        :type txn: :class:`algosdk.transaction.Transaction`
        :param prefix: domain-scoped nonce prefix
        :type prefix: str
        :param nonce: server-issued challenge
        :type nonce: str
        :return: Boolean
        """
        return txn.note == f"{prefix}{nonce}".encode()

    def _network_ok(self, txn):
        """Pin the transaction to the expected network (defense in depth).

        :param txn: transaction whose genesis id/hash are checked
        :type txn: :class:`algosdk.transaction.Transaction`
        :var gh: transaction genesis hash normalized to a base64 str
        :type gh: str
        :return: Boolean
        """
        if self.expected_genesis_id and txn.genesis_id != self.expected_genesis_id:
            return False
        if self.expected_genesis_hash:
            gh = txn.genesis_hash or b""
            # algosdk 2.x keeps genesis_hash as a base64 str; future/other
            # versions may yield raw bytes. Normalize to a base64 str.
            if isinstance(gh, (bytes, bytearray)):
                gh = base64.b64encode(gh).decode()
            if gh != self.expected_genesis_hash:
                return False
        return True

    def _signature_ok(self, stxn):
        """Verify the signature, confirming any claimed rekey on-chain first.

        :param stxn: signed transaction to check
        :type stxn: :class:`algosdk.transaction.SignedTransaction`
        :var auth: authorizing (rekey) address claimed by the transaction, if any
        :type auth: str | None
        :var sender: transaction sender address
        :type sender: str
        :return: Boolean
        """
        auth = stxn.authorizing_address
        sender = stxn.transaction.sender
        if auth is not None and auth != sender:
            if not self._rekey_confirmed(sender, auth):
                logger.warning(
                    "walletauth: unconfirmed rekey claim, sender=%s", _short(sender)
                )
                return False
        return verify_signed_transaction(stxn)

    def _rekey_confirmed(self, address, auth_address):
        """Return True only if ``address`` is on-chain rekeyed to ``auth_address``.

        :param address: account whose signing authority is in question
        :type address: str
        :param auth_address: authorizing address claimed by the signed txn
        :type auth_address: str
        :var info: algod account information for ``address``
        :type info: dict
        :return: Boolean
        """
        try:
            info = self.algod_factory().account_info(address)
        except Exception:  # noqa: BLE001 - treat any lookup failure as unconfirmed
            logger.exception("walletauth: algod account_info failed")
            return False
        return info.get("auth-addr") == auth_address


class EvmXChainVerifier(WalletProofVerifier):
    """DEFERRED. Recover an EVM signer from an EIP-712/EIP-4361 signature over
    the nonce, derive the xChain Algorand counterpart server-side, and return
    it. Implementing :meth:`recover` is all that is needed: the shared
    :meth:`verify` (authorize) and the login flow both build on it. Disabled
    until xChain Accounts ships a non-React/vanilla integration path.
    """

    def recover(self, *, nonce, prefix, payload):
        raise NotSupported("EVM/xChain sign-in is not yet enabled")


VERIFIERS = {
    "algorand": AlgorandSignedTxnVerifier(),
    "evm": EvmXChainVerifier(),
}

#: auth_method recorded on the profile, keyed by request chain.
AUTH_METHOD_BY_CHAIN = {
    "algorand": "algorand_wallet",
    "evm": "evm_xchain",
}


def _short(address):
    """Return a log-safe truncation of an address.

    :param address: address to truncate for logging
    :type address: str
    :return: truncated ``AAAAA..ZZZZZ`` form, or the input unchanged when short
    :rtype: str
    """
    return (
        f"{address[:5]}..{address[-5:]}" if address and len(address) > 10 else address
    )
