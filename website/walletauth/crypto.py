"""Vendored Ed25519 and Falcon-1024 verification of an Algorand signed transaction.

The prefix is :data:`algosdk.constants.txid_prefix` (``b"TX"``), the
*transaction* prefix, not the ``b"MX"`` that
``algosdk.util.verify_bytes`` uses for arbitrary ``signBytes`` messages, and
using that one here would reject every real wallet signature.

A malformed signature or address yields ``False`` rather than raising: this is
called straight from the verifier, not from inside a view's blanket
``try/except``.

**A rekey claim here is the client's word.** This module honours
``authorizing_address``, which on its own is unsafe for an authorization gate.
:class:`walletauth.verifiers.AlgorandSignedTxnVerifier` is responsible for
confirming any claimed rekey against on-chain state before trusting it.
"""

import base64
import logging

from algosdk import constants, encoding
from algosdk.error import AlgodHTTPError
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

#: Ceiling on a deterministic Falcon-1024 signature, from Algorand's
#: `deterministic.h`: FALCON_SIG_COMPRESSED_MAXSIZE(10) - 40 + 1, where the
#: subtraction is the 40-byte nonce the deterministic variant does not carry.
FALCON_DET1024_SIG_MAXSIZE = 1423

logger = logging.getLogger(__name__)


def verify_signed_transaction(stxn):
    """Verify the Ed25519 signature of a signed Algorand transaction.

    Verifies against the sender's key, or the authorizing (rekey) address when
    one is present on the signed transaction.

    :param stxn: signed transaction to verify
    :type stxn: :class:`algosdk.transaction.SignedTransaction`
    :var public_key: address whose key must have produced the signature (the
        sender, or the authorizing address when the transaction is rekeyed)
    :type public_key: str
    :var verify_key: Ed25519 verify key derived from ``public_key``
    :type verify_key: :class:`nacl.signing.VerifyKey`
    :var prefixed_message: ``b"TX"`` domain prefix followed by the canonical
        msgpack encoding of the transaction -- the exact bytes that were signed
    :type prefixed_message: bytes
    :return: True if the signature is valid, else False
    :rtype: bool
    """
    if stxn.signature is None or len(stxn.signature) == 0:
        return False

    public_key = stxn.transaction.sender
    if stxn.authorizing_address is not None:
        public_key = stxn.authorizing_address

    try:
        verify_key = VerifyKey(encoding.decode_address(public_key))
        prefixed_message = constants.txid_prefix + base64.b64decode(
            encoding.msgpack_encode(stxn.transaction)
        )
        verify_key.verify(prefixed_message, base64.b64decode(stxn.signature))
        return True
    except (BadSignatureError, ValueError, TypeError):
        return False


def verify_pq_signed_transaction(stxn, algod_client, signed_b64=None):
    """Verify a post-quantum (``pqsig``) signed transaction, by asking a node.

    **Not verified locally, and that is the whole point.** Algorand's
    post-quantum accounts use a *deterministic* Falcon variant that is
    wire-incompatible with the standard, randomized scheme every Python
    binding implements. No local check can bridge it; the node has the only
    correct implementation, and simulate runs it.

    What the node's answers mean, measured against mainnet:

    - an invalid signature is an HTTP error;
    - a transaction that would not execute - an overspend, say - is HTTP 200
      with a ``failure-message`` in the body;
    - ``allow-empty-signatures`` permits an *absent* signature, never an
      invalid one.

    So HTTP 200 means the signatures verified, whatever the body says about
    execution. That separation is what makes this usable for a login: a reader
    whose account cannot afford the fee must still be able to prove they hold
    the key. Anything else - a refusal, a network failure, a malformed
    response - is unverified, so the gate fails closed.

    :param stxn: post-quantum signed transaction to verify
    :type stxn: :class:`algosdk.transaction.PQSignedTransaction`
    :param algod_client: node to verify through
    :type algod_client: :class:`algosdk.v2client.algod.AlgodClient`
    :param signed_b64: the base64 the transaction was decoded from, used only
        to report a re-encoding mismatch rather than to verify
    :type signed_b64: str or None
    :return: True when the node accepted every signature, else False
    :rtype: bool
    """
    pqsig = getattr(stxn, "pqsig", None)
    if pqsig is None:
        return False

    # Pre-flight bounds, kept from the local implementation: they cost nothing
    # and they stop an obviously malformed payload becoming a node round trip.
    scheme = getattr(pqsig, "scheme", b"")
    if isinstance(scheme, str):
        scheme = scheme.encode("ascii")
    if scheme != b"f1":
        return False

    salt = getattr(pqsig, "salt", None)
    if salt is None or not (0 <= salt <= 255):
        return False

    public_key = getattr(pqsig, "public_key", None)
    if not isinstance(public_key, (bytes, bytearray)) or len(public_key) != 1793:
        return False

    signature = getattr(pqsig, "signature", None)
    if not isinstance(signature, (bytes, bytearray)) or not (
        64 <= len(signature) <= FALCON_DET1024_SIG_MAXSIZE
    ):
        return False

    if getattr(stxn, "transaction", None) is None:
        return False

    # **Diagnostic only.** The node verifies the bytes the SDK re-encodes from
    # this object, not the bytes the wallet sent. A mismatch closes the gate
    # correctly but reads as a rejected signature, so it is named here: the
    # next person debugging starts from the encoding rather than from the
    # cryptography.
    if signed_b64:
        try:
            if encoding.msgpack_encode(stxn) != signed_b64:
                logger.warning(
                    "walletauth: PQ transaction does not re-encode to the bytes "
                    "it arrived as; a rejection below is an encoding mismatch, "
                    "not a bad signature"
                )
        except Exception:  # noqa: BLE001 - a diagnostic must not decide anything
            pass

    try:
        algod_client.simulate_raw_transactions([stxn])
    except AlgodHTTPError as error:
        logger.warning("walletauth: node refused the PQ signature: %s", str(error)[:200])
        return False
    except Exception as exc:  # noqa: BLE001 - unreachable node is not a pass
        logger.warning(
            "walletauth: could not reach a node to verify the PQ signature: %s", exc
        )
        return False

    return True
