"""Testing module for :py:mod:`walletauth.crypto` module."""

import base64
import os

import pytest
from algosdk import account, encoding
from algosdk.error import AlgodHTTPError
from algosdk.transaction import (
    PaymentTxn,
    PQSig,
    PQSignedTransaction,
    SignedTransaction,
    SuggestedParams,
)

from walletauth.crypto import (
    FALCON_DET1024_SIG_MAXSIZE,
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
    sender=None,
    authorizing_address=None,
    scheme=b"f1",
    salt=None,
):
    """Build a `pqsig` transaction with correctly *shaped* key and signature.

    **Not a real Falcon signature, and it no longer needs to be.** These used
    to generate a standard Falcon-1024 keypair and sign with it, which passed
    every time while production failed every time - Algorand uses a
    deterministic Falcon variant, and a standard signature is not one. The
    tests were self-consistent and testing the wrong algorithm.

    Verification now asks a node, so what a test needs is material of the right
    shape and a fake node with an opinion.
    """
    if pk is None:
        pk = os.urandom(1793)
    scheme_bytes = scheme if isinstance(scheme, bytes) else scheme.encode()
    derived_addr, canonical_salt = encoding.address_from_pq_key(scheme_bytes, pk)
    if salt is None:
        salt = canonical_salt
    actual_sender = sender or derived_addr
    params = SuggestedParams(
        fee=3000,  # a Falcon signature costs three minimum fees, not one
        first=1,
        last=1000,
        gh=base64.b64encode(b"x" * 32).decode(),
        gen="mainnet-v1.0",
        flat_fee=True,
    )
    txn = PaymentTxn(
        sender=actual_sender, sp=params, receiver=actual_sender, amt=0, note=b"n"
    )
    pqsig = PQSig(
        scheme=scheme_bytes,
        salt=salt,
        public_key=pk,
        signature=os.urandom(1230),
    )
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


class FakeAlgod:
    """A node with an opinion about signatures, and a memory of being asked."""

    def __init__(self, error=None):
        self.error = error
        self.calls = 0

    def simulate_raw_transactions(self, txns):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return {"txn-groups": [{"txn-results": []}]}


class TestVerifyPQSignedTransaction:
    """Verification is the node's answer, and the gate fails closed."""

    def test_walletauth_crypto_pq_node_acceptance_is_a_valid_signature(self):
        """HTTP 200 means every signature verified, whatever the body says.

        A transaction that would not execute - an overspend, an unaffordable
        fee - still returns 200 with a `failure-message`. That has to count as
        verified, or a reader who cannot afford the fee could not prove they
        hold the key.
        """
        assert verify_pq_signed_transaction(make_pq_signed(), FakeAlgod()) is True

    def test_walletauth_crypto_pq_refused_signature_returns_false(self):
        node = FakeAlgod(
            AlgodHTTPError("At least one signature didn't pass verification")
        )
        assert verify_pq_signed_transaction(make_pq_signed(), node) is False

    def test_walletauth_crypto_pq_unreachable_node_returns_false(self):
        """Fails closed: an unverifiable proof is not a verified one."""
        node = FakeAlgod(ConnectionError("connection refused"))
        assert verify_pq_signed_transaction(make_pq_signed(), node) is False

    def test_walletauth_crypto_pq_none_pqsig_returns_false(self):
        stxn = make_pq_signed()
        stxn.pqsig = None
        assert verify_pq_signed_transaction(stxn, FakeAlgod()) is False

    @pytest.mark.parametrize(
        "mutate",
        (
            lambda s: setattr(s.pqsig, "scheme", b"f5"),
            lambda s: setattr(s.pqsig, "salt", 300),
            lambda s: setattr(s.pqsig, "public_key", b"short"),
            lambda s: setattr(s.pqsig, "signature", b"short_sig"),
            lambda s: setattr(s.pqsig, "signature", os.urandom(9999)),
        ),
        ids=("scheme", "salt", "pk_length", "sig_too_short", "sig_too_long"),
    )
    def test_walletauth_crypto_pq_preflight_rejects_without_asking_the_node(self, mutate):
        """Malformed material is refused here, not turned into a round trip."""
        stxn = make_pq_signed()
        mutate(stxn)
        node = FakeAlgod()

        assert verify_pq_signed_transaction(stxn, node) is False
        assert node.calls == 0

    def test_walletauth_crypto_pq_a_signature_at_the_deterministic_ceiling_is_allowed(
        self,
    ):
        """1423 bytes: FALCON_SIG_COMPRESSED_MAXSIZE(10) less the absent nonce.

        The bound has to admit the largest real signature. Getting it wrong in
        the tight direction would reject a legitimate login for a reason no log
        line would explain.
        """
        stxn = make_pq_signed()
        stxn.pqsig.signature = os.urandom(FALCON_DET1024_SIG_MAXSIZE)

        assert verify_pq_signed_transaction(stxn, FakeAlgod()) is True


class TestVerifyPQSignedTransactionRemainingBranches:
    """The four pre-flight paths nothing exercised.

    Each is a gate that fails closed or a diagnostic that must not decide
    anything, and an untested gate is one nobody would notice opening.
    """

    def test_walletauth_crypto_pq_a_string_scheme_is_encoded_not_rejected(self):
        """**A decoder that hands back `str` must not fail a valid signature.**

        The SDK returns `scheme` as bytes, but the field travels as msgpack and
        a decoder configured with `raw=False` yields `str`. Comparing that to
        `b"f1"` is False for a perfectly good envelope, so it is encoded first -
        and without this test the encode could be deleted and only a wallet
        using that decoder would notice.
        """
        stxn = make_pq_signed()
        stxn.pqsig.scheme = "f1"
        node = FakeAlgod()

        assert verify_pq_signed_transaction(stxn, node) is True
        assert node.calls == 1

    def test_walletauth_crypto_pq_a_string_scheme_that_is_wrong_still_fails(self):
        """The encode must not become a way past the check."""
        stxn = make_pq_signed()
        stxn.pqsig.scheme = "f5"
        node = FakeAlgod()

        assert verify_pq_signed_transaction(stxn, node) is False
        assert node.calls == 0

    def test_walletauth_crypto_pq_no_transaction_is_refused_before_the_node(self):
        """An envelope with signature material and nothing signed. The node
        would refuse it too, but only after a round trip - and `simulate` on a
        `None` transaction is an exception rather than an answer."""
        stxn = make_pq_signed()
        stxn.transaction = None
        node = FakeAlgod()

        assert verify_pq_signed_transaction(stxn, node) is False
        assert node.calls == 0

    def test_walletauth_crypto_pq_a_re_encoding_mismatch_warns_and_continues(
        self, caplog
    ):
        """**Diagnostic only.** The node verifies the bytes the SDK re-encodes,
        not the bytes the wallet sent. If they differ the signature fails and
        the gate closes correctly - but it would read as a rejected signature,
        and the next person would start from the cryptography instead of the
        encoding. It must warn and it must not decide."""
        stxn = make_pq_signed()
        node = FakeAlgod()

        with caplog.at_level("WARNING"):
            assert (
                verify_pq_signed_transaction(
                    stxn, node, signed_b64="not-what-this-re-encodes-to"
                )
                is True
            )

        assert "does not re-encode" in caplog.text
        assert node.calls == 1

    def test_walletauth_crypto_pq_a_matching_re_encoding_says_nothing(self, caplog):
        """The usual case, and it must be silent - a warning on every login
        would train the reader to ignore the one that matters."""
        stxn = make_pq_signed()

        with caplog.at_level("WARNING"):
            assert (
                verify_pq_signed_transaction(
                    stxn, FakeAlgod(), signed_b64=encoding.msgpack_encode(stxn)
                )
                is True
            )

        assert "does not re-encode" not in caplog.text

    def test_walletauth_crypto_pq_an_unencodable_transaction_still_verifies(self):
        """The diagnostic is wrapped because it must not decide anything, and
        `msgpack_encode` on a half-decoded object can raise. A verified
        signature has to survive a diagnostic that could not run."""
        stxn = make_pq_signed()
        node = FakeAlgod()

        class Unencodable:
            """Raises from inside `msgpack_encode`, as a partial decode would."""

            def __getattr__(self, name):
                raise ValueError("cannot encode")

        stxn.transaction.note = Unencodable()

        assert verify_pq_signed_transaction(stxn, node, signed_b64="anything") is True
        assert node.calls == 1
