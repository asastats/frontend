"""Vendored Ed25519 verification of an Algorand signed transaction.

Ported from the Rewards Suite ``utils.helpers.verify_signed_transaction``. Two
deliberate differences from the reference:

1. Uses :data:`algosdk.constants.txid_prefix` (``b"TX"``) rather than a literal,
   to make the domain-separation prefix self-documenting. Note this is the
   *transaction* prefix, NOT the ``b"MX"`` used by ``algosdk.util.verify_bytes``
   for arbitrary ``signBytes`` messages -- using the latter here would reject
   every real wallet signature.
2. Broadens the caught exceptions so a malformed signature or address yields
   ``False`` instead of propagating, since this helper is called directly by the
   verifier rather than from inside a blanket ``try/except`` in a view.

This function honors ``authorizing_address`` (rekeyed accounts). On its own that
is unsafe for an authorization gate: a client can fabricate a rekey claim. The
caller (:class:`walletauth.verifiers.AlgorandSignedTxnVerifier`) is responsible
for confirming any claimed rekey against on-chain state before trusting it.
"""

import base64

from algosdk import constants, encoding
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


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
