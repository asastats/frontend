"""Testing module for :py:mod:`walletauth.verifiers` module."""

import base64

from algosdk import account, encoding
from algosdk.transaction import PaymentTxn, SignedTransaction, SuggestedParams

from utils.constants.core import (
    MAINNET_GENESIS_HASH,
    MAINNET_GENESIS_ID,
    WALLET_CONNECT_NONCE_PREFIX,
)
from walletauth.verifiers import (
    AlgorandSignedTxnVerifier,
    EvmXChainVerifier,
    NotSupported,
)

NONCE = "deadbeefcafe0001"


# # HELPERS
def make_params():
    return SuggestedParams(
        fee=0,
        first=1,
        last=1000,
        gh=MAINNET_GENESIS_HASH,
        gen=MAINNET_GENESIS_ID,
        flat_fee=True,
    )


def make_self_payment(address, note):
    return PaymentTxn(
        sender=address, sp=make_params(), receiver=address, amt=0, note=note
    )


def make_payload(stxn):
    return {"signedTransaction": encoding.msgpack_encode(stxn)}


def make_note(nonce=NONCE):
    return f"{WALLET_CONNECT_NONCE_PREFIX}{nonce}".encode()


def fake_algod(auth_addr=None):
    class _Client:
        def account_info(self, address):
            return {"auth-addr": auth_addr} if auth_addr else {}

    return lambda: _Client()


def verify(stxn, address, nonce=NONCE, algod_factory=None):
    verifier = AlgorandSignedTxnVerifier(
        algod_factory=algod_factory or fake_algod()
    )
    return verifier.verify(
        address=address,
        nonce=nonce,
        prefix=WALLET_CONNECT_NONCE_PREFIX,
        payload=make_payload(stxn),
    )


class TestAlgorandSignedTxnVerifier:
    """Testing class for :class:`AlgorandSignedTxnVerifier` verifier."""

    # # verify - own key
    def test_algorand_verifier_valid_own_key_returns_address(self):
        secret, address = account.generate_account()
        stxn = make_self_payment(address, make_note()).sign(secret)
        assert verify(stxn, address) == address

    def test_algorand_verifier_missing_signed_transaction_returns_none(self):
        verifier = AlgorandSignedTxnVerifier(algod_factory=fake_algod())
        assert (
            verifier.verify(
                address="A" * 58,
                nonce=NONCE,
                prefix=WALLET_CONNECT_NONCE_PREFIX,
                payload={},
            )
            is None
        )

    def test_algorand_verifier_undecodable_payload_returns_none(self):
        verifier = AlgorandSignedTxnVerifier(algod_factory=fake_algod())
        assert (
            verifier.verify(
                address="A" * 58,
                nonce=NONCE,
                prefix=WALLET_CONNECT_NONCE_PREFIX,
                payload={"signedTransaction": "not-base64-msgpack"},
            )
            is None
        )

    # # verify - shape
    def test_algorand_verifier_wrong_sender_returns_none(self):
        secret, address = account.generate_account()
        _, other = account.generate_account()
        stxn = make_self_payment(address, make_note()).sign(secret)
        assert verify(stxn, other) is None

    def test_algorand_verifier_nonzero_amount_returns_none(self):
        secret, address = account.generate_account()
        txn = PaymentTxn(
            sender=address, sp=make_params(), receiver=address, amt=1, note=make_note()
        )
        assert verify(txn.sign(secret), address) is None

    # # verify - note
    def test_algorand_verifier_wrong_note_returns_none(self):
        secret, address = account.generate_account()
        stxn = make_self_payment(address, b"asastats-auth:not-the-nonce").sign(secret)
        assert verify(stxn, address) is None

    # # verify - network
    def test_algorand_verifier_wrong_network_returns_none(self):
        secret, address = account.generate_account()
        params = SuggestedParams(
            fee=0,
            first=1,
            last=1000,
            gh=base64.b64encode(b"t" * 32).decode(),
            gen="testnet-v1.0",
            flat_fee=True,
        )
        txn = PaymentTxn(
            sender=address, sp=params, receiver=address, amt=0, note=make_note()
        )
        assert verify(txn.sign(secret), address) is None

    # # verify - rekey
    def test_algorand_verifier_forged_rekey_returns_none(self):
        _, victim = account.generate_account()
        attacker_secret, attacker = account.generate_account()
        txn = make_self_payment(victim, make_note())
        signature = base64.b64encode(txn.raw_sign(attacker_secret)).decode()
        forged = SignedTransaction(txn, signature, authorizing_address=attacker)
        assert verify(forged, victim, algod_factory=fake_algod(auth_addr=None)) is None

    def test_algorand_verifier_confirmed_rekey_returns_address(self):
        _, rekeyed = account.generate_account()
        signer_secret, signer = account.generate_account()
        txn = make_self_payment(rekeyed, make_note())
        signature = base64.b64encode(txn.raw_sign(signer_secret)).decode()
        stxn = SignedTransaction(txn, signature, authorizing_address=signer)
        assert (
            verify(stxn, rekeyed, algod_factory=fake_algod(auth_addr=signer))
            == rekeyed
        )

    def test_algorand_verifier_rekey_lookup_failure_returns_none(self):
        _, rekeyed = account.generate_account()
        signer_secret, signer = account.generate_account()
        txn = make_self_payment(rekeyed, make_note())
        signature = base64.b64encode(txn.raw_sign(signer_secret)).decode()
        stxn = SignedTransaction(txn, signature, authorizing_address=signer)

        def boom():
            raise RuntimeError("algod down")

        assert verify(stxn, rekeyed, algod_factory=boom) is None

    # # configuration
    def test_algorand_verifier_skips_genesis_when_unset(self):
        secret, address = account.generate_account()
        params = SuggestedParams(
            fee=0,
            first=1,
            last=1000,
            gh=base64.b64encode(b"z" * 32).decode(),
            gen="anything-v1.0",
            flat_fee=True,
        )
        txn = PaymentTxn(
            sender=address, sp=params, receiver=address, amt=0, note=make_note()
        )
        verifier = AlgorandSignedTxnVerifier(
            algod_factory=fake_algod(),
            expected_genesis_id="",
            expected_genesis_hash="",
        )
        proven = verifier.verify(
            address=address,
            nonce=NONCE,
            prefix=WALLET_CONNECT_NONCE_PREFIX,
            payload=make_payload(txn.sign(secret)),
        )
        assert proven == address


class TestEvmXChainVerifier:
    """Testing class for the deferred :class:`EvmXChainVerifier` verifier."""

    # # verify
    def test_evm_verifier_raises_not_supported(self):
        verifier = EvmXChainVerifier()
        try:
            verifier.verify(
                address="A" * 58,
                nonce=NONCE,
                prefix=WALLET_CONNECT_NONCE_PREFIX,
                payload={},
            )
            raised = False
        except NotSupported:
            raised = True
        assert raised
