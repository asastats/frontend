"""Testing module for :py:mod:`walletauth.crypto` module."""

import base64

from algosdk import account
from algosdk.transaction import PaymentTxn, SignedTransaction, SuggestedParams

from walletauth.crypto import verify_signed_transaction


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
