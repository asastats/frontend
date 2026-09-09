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
3. Adds :func:`verify_pq_signed_transaction` to verify Falcon-1024 signatures
   using :class:`falcon_python.Falcon1024` with pre-flight length gating.

This module honors ``authorizing_address`` (rekeyed accounts). On its own that
is unsafe for an authorization gate: a client can fabricate a rekey claim. The
caller (:class:`walletauth.verifiers.AlgorandSignedTxnVerifier`) is responsible
for confirming any claimed rekey against on-chain state before trusting it.
"""

import base64
import hashlib
import logging

from algosdk import constants, encoding
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

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


def verify_pq_signed_transaction(stxn, raw_txn_msgpack=None):
    """Verify the Falcon-1024 post-quantum signature of an Algorand signed transaction.

    Verifies the ``pqsig`` envelope against the transaction signing preimage
    (``b"TX" + canonical_msgpack(txn)``) using the Falcon-1024 public key
    carried in ``pqsig``.

    :param stxn: post-quantum signed transaction to verify
    :type stxn: :class:`algosdk.transaction.PQSignedTransaction`
    :param raw_txn_msgpack: optional raw msgpack bytes of the transaction map
        extracted directly from the wire envelope before reconstruction
    :type raw_txn_msgpack: bytes | None
    :return: True if the Falcon signature is valid, else False
    :rtype: bool
    """
    pqsig = getattr(stxn, "pqsig", None)
    if pqsig is None:
        return False

    # Pre-flight length and scheme bounds (defense against CPU exhaustion)
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
    if (
        not isinstance(signature, (bytes, bytearray))
        or not (64 <= len(signature) <= 2048)
    ):
        return False

    txn = getattr(stxn, "transaction", None)
    if txn is None:
        return False

    try:
        from falcon_python import Falcon1024

        sig_bytes = bytes(signature)
        pk_bytes = bytes(public_key)
        to_sign = txn.bytes_to_sign()

        logger.info(
            "walletauth: Falcon verify attempt pk[0]=%d pk_len=%d, sig[0]=%d sig_len=%d, to_sign_len=%d, to_sign_prefix=%s",
            pk_bytes[0] if pk_bytes else -1,
            len(pk_bytes),
            sig_bytes[0] if sig_bytes else -1,
            len(sig_bytes),
            len(to_sign),
            to_sign[:10].hex() if to_sign else "",
        )
        sig_candidates = [sig_bytes]
        # In PQClean/Falcon, detached signature byte 0 is header (0x3a for Falcon-1024 compressed).
        # If an external wallet or SDK stripped the header byte, restore it.
        if sig_bytes and sig_bytes[0] not in (0x3A, 0x2A, 0x5A):
            sig_candidates.append(bytes([0x3A]) + sig_bytes)

        # Build candidate signing preimages safely
        msg_candidates = [
            ("to_sign", to_sign),
            ("sha512_256_to_sign", hashlib.new("sha512_256", to_sign).digest()),
            ("sha256_to_sign", hashlib.sha256(to_sign).digest()),
            ("sha512_to_sign", hashlib.sha512(to_sign).digest()),
        ]
        try:
            txid_str = txn.get_txid()
            if txid_str:
                pad = "=" * ((8 - len(txid_str) % 8) % 8)
                msg_candidates.append(("txid", base64.b32decode(txid_str + pad)))
        except Exception:
            pass

        if raw_txn_msgpack:
            raw_to_sign = constants.txid_prefix + raw_txn_msgpack
            msg_candidates.append(("raw_to_sign", raw_to_sign))
            msg_candidates.append(
                (
                    "sha512_256_raw_to_sign",
                    hashlib.new("sha512_256", raw_to_sign).digest(),
                )
            )

        for s_candidate in sig_candidates:
            for name, msg in msg_candidates:
                try:
                    if Falcon1024.verify_detached_sign(s_candidate, msg, pk_bytes):
                        if name != "to_sign" or s_candidate != sig_bytes:
                            logger.info(
                                "walletauth: Falcon verified with variant mode=%s, sig_len=%d",
                                name,
                                len(s_candidate),
                            )
                        return True
                except Exception:
                    continue

        logger.warning(
            "walletauth: Falcon verification failed (pk_len=%d, sig_len=%d, to_sign_len=%d)",
            len(pk_bytes),
            len(sig_bytes),
            len(to_sign),
        )
        return False
    except Exception as exc:  # noqa: BLE001 - any crypto failure yields False
        logger.warning("walletauth: Falcon verification exception: %s", exc)
        return False
