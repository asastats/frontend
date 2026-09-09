"""Testing module for :py:mod:`walletauth.crypto` module."""

import base64

from algosdk import account, encoding
from algosdk.transaction import (
    PaymentTxn,
    PQSig,
    PQSignedTransaction,
    SignedTransaction,
    SuggestedParams,
)
from falcon_python import Falcon1024

from walletauth.crypto import (
    verify_pq_signed_transaction,
    verify_signed_transaction,
)


# # HELPERS
def make_signed(secret, address, authorizing_address=None, signer_secret=None):
    params = SuggestedParams(
        fee=0,
        first=1,
        last=1000,
        gh=base64.b64encode(b"x" * 32).decode(),
        gen="mainnet-v1.0",
        flat_fee=True,
    )
    txn = PaymentTxn(sender=address, sp=params, receiver=address, amt=0, note=b"n")
    if authorizing_address is None:
        return txn.sign(secret)
    signature = base64.b64encode(txn.raw_sign(signer_secret)).decode()
    return SignedTransaction(txn, signature, authorizing_address=authorizing_address)


def make_pq_signed(
    pk=None,
    sk=None,
    sender=None,
    authorizing_address=None,
    scheme=b"f1",
    salt=None,
    tamper_sig=False,
):
    if pk is None or sk is None:
        pk, sk = Falcon1024.generate_keypair()
    derived_addr, canonical_salt = encoding.address_from_pq_key(scheme if isinstance(scheme, bytes) else scheme.encode(), pk)
    if salt is None:
        salt = canonical_salt
    actual_sender = sender or derived_addr
    params = SuggestedParams(
        fee=3000,
        first=1,
        last=1000,
        gh=base64.b64encode(b"x" * 32).decode(),
        gen="mainnet-v1.0",
        flat_fee=True,
    )
    txn = PaymentTxn(sender=actual_sender, sp=params, receiver=actual_sender, amt=0, note=b"n")
    to_sign = txn.bytes_to_sign()
    sig = Falcon1024.detached_sign(sk, to_sign)
    if tamper_sig:
        # Flip a byte in the signature
        sig = bytearray(sig)
        sig[100] ^= 0xFF
        sig = bytes(sig)
    pqsig = PQSig(scheme, salt, pk, sig)
    return PQSignedTransaction(txn, pqsig, authorizing_address=authorizing_address)


class TestVerifySignedTransaction:
    """Testing class for :func:`verify_signed_transaction` helper."""

    # # verify_signed_transaction
    def test_walletauth_crypto_valid_own_key_returns_true(self):
        secret, address = account.generate_account()
        assert verify_signed_transaction(make_signed(secret, address)) is True

    def test_walletauth_crypto_empty_signature_returns_false(self):
        secret, address = account.generate_account()
        stxn = make_signed(secret, address)
        stxn.signature = ""
        assert verify_signed_transaction(stxn) is False

    def test_walletauth_crypto_none_signature_returns_false(self):
        secret, address = account.generate_account()
        stxn = make_signed(secret, address)
        stxn.signature = None
        assert verify_signed_transaction(stxn) is False

    def test_walletauth_crypto_tampered_signature_returns_false(self):
        secret, address = account.generate_account()
        other_secret, _ = account.generate_account()
        stxn = make_signed(secret, address)
        tampered = make_signed(other_secret, address)
        stxn.signature = tampered.signature
        assert verify_signed_transaction(stxn) is False

    def test_walletauth_crypto_malformed_signature_returns_false(self):
        secret, address = account.generate_account()
        stxn = make_signed(secret, address)
        stxn.signature = "!!! not base64 !!!"
        assert verify_signed_transaction(stxn) is False

    def test_walletauth_crypto_verifies_against_authorizing_address(self):
        signer_secret, signer = account.generate_account()
        _, rekeyed = account.generate_account()
        stxn = make_signed(
            None, rekeyed, authorizing_address=signer, signer_secret=signer_secret
        )
        assert verify_signed_transaction(stxn) is True

    def test_walletauth_crypto_authorizing_address_wrong_signer_returns_false(self):
        wrong_secret, _ = account.generate_account()
        _, signer = account.generate_account()
        _, rekeyed = account.generate_account()
        stxn = make_signed(
            None, rekeyed, authorizing_address=signer, signer_secret=wrong_secret
        )
        assert verify_signed_transaction(stxn) is False


class TestVerifyPQSignedTransaction:
    """Testing class for :func:`verify_pq_signed_transaction` helper."""

    def test_walletauth_crypto_pq_valid_signature_returns_true(self):
        stxn = make_pq_signed()
        assert verify_pq_signed_transaction(stxn) is True

    def test_walletauth_crypto_pq_none_pqsig_returns_false(self):
        stxn = make_pq_signed()
        stxn.pqsig = None
        assert verify_pq_signed_transaction(stxn) is False

    def test_walletauth_crypto_pq_unsupported_scheme_returns_false(self):
        stxn = make_pq_signed(scheme=b"f5")
        assert verify_pq_signed_transaction(stxn) is False

    def test_walletauth_crypto_pq_invalid_salt_returns_false(self):
        stxn = make_pq_signed(salt=300)
        assert verify_pq_signed_transaction(stxn) is False

    def test_walletauth_crypto_pq_invalid_pk_length_returns_false(self):
        stxn = make_pq_signed()
        stxn.pqsig.public_key = b"short"
        assert verify_pq_signed_transaction(stxn) is False

    def test_walletauth_crypto_pq_invalid_sig_length_returns_false(self):
        stxn = make_pq_signed()
        stxn.pqsig.signature = b"short_sig"
        assert verify_pq_signed_transaction(stxn) is False

    def test_walletauth_crypto_pq_tampered_signature_returns_false(self):
        stxn = make_pq_signed(tamper_sig=True)
        assert verify_pq_signed_transaction(stxn) is False

    def test_walletauth_crypto_pq_tampered_transaction_returns_false(self):
        stxn = make_pq_signed()
        stxn.transaction.amt = 1000
        assert verify_pq_signed_transaction(stxn) is False
