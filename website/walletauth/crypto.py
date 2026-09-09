"""Vendored Ed25519 and Falcon-1024 verification of an Algorand signed transaction.

Ported from the Rewards Suite ``utils.helpers.verify_signed_transaction`` with
additions for native Post-Quantum Falcon-1024 (``pqsig``) verification.

Deliberate differences from the reference:

1. Uses :data:`algosdk.constants.txid_prefix` (``b"TX"``) rather than a literal,
   to make the domain-separation prefix self-documenting. Note this is the
   *transaction* prefix, NOT the ``b"MX"`` used by ``algosdk.util.verify_bytes``
   for arbitrary ``signBytes`` messages -- using the latter here would reject
   every real wallet signature.
2. Broadens the caught exceptions so a malformed signature or address yields
   ``False`` instead of propagating, since this helper is called directly by the
   verifier rather than from inside a blanket ``try/except`` in a view.
3. Adds :func:`verify_pq_signed_transaction`, which verifies Falcon-1024
   (``pqsig``) signatures **through a node** rather than locally. Algorand uses
   a deterministic Falcon variant that is wire-incompatible with the standard
   scheme every Python binding implements, and no local check can bridge that;
   the node has the only correct implementation. Its docstring has the detail.

This module honors ``authorizing_address`` (rekeyed accounts). On its own that
is unsafe for an authorization gate: a client can fabricate a rekey claim. The
caller (:class:`walletauth.verifiers.AlgorandSignedTxnVerifier`) is responsible
for confirming any claimed rekey against on-chain state before trusting it.
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

    **Not verified locally, and that is the whole point.** The previous
    implementation used :class:`falcon_python.Falcon1024`, which is *standard,
    randomized* Falcon-1024. Algorand's post-quantum accounts use a
    **deterministic** Falcon variant, and Algorand's own `deterministic.h` says
    the two are wire-incompatible: the deterministic signature drops the
    40-byte nonce, adds a salt-version byte, and changes the header from
    ``0x3A`` to ``0xBA``. No message preimage and no header fix-up can bridge
    that - the verifier is running a different algorithm on an encoding that
    omits a field it requires. See ``~/claude/post-quantum/FINDING-falcon-mismatch.md``.

    There is no Python binding for the deterministic variant. There is,
    however, a correct implementation in every algod node, and simulate runs
    it. Measured against mainnet:

    - a signature replaced with random bytes is refused with
      *"At least one signature didn't pass verification"*, an **HTTP error**;
    - a transaction that would not execute - an overspend, say - returns
      **HTTP 200** with a ``failure-message`` in the body;
    - ``allow-empty-signatures`` permits an *absent* signature, never an
      invalid one.

    So **HTTP 200 means the signatures verified**, whatever the body says about
    execution, and that separation is what makes this usable for a login: a
    reader whose account cannot afford the fee must still be able to prove they
    hold the key. Anything else - a refusal, a network failure, a malformed
    response - is treated as unverified, so the gate fails closed.

    It also outlives this scheme. The ``pqsig`` envelope is built to carry
    others (``f5``, Falcon-512, is defined and reserved), and a node-side check
    supports each one the day the network does, with no new binding to build.

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
    # this object, not the bytes the wallet sent. Those should be identical -
    # the object was decoded from them - and if they are not, the signature
    # fails and this gate closes, which is correct but would be logged as a
    # rejected signature. Saying so here means the next person debugging starts
    # from the encoding rather than from the cryptography, which is exactly the
    # detour this module has already made once.
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
        logger.warning(
            "walletauth: node refused the PQ signature: %s", str(error)[:200]
        )
        return False
    except Exception as exc:  # noqa: BLE001 - unreachable node is not a pass
        logger.warning(
            "walletauth: could not reach a node to verify the PQ signature: %s", exc
        )
        return False

    return True
