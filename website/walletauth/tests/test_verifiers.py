"""Testing module for :py:mod:`walletauth.verifiers` module."""

import base64

import pytest
from algosdk import account, encoding
from algosdk.transaction import (
    PaymentTxn,
    PQSig,
    PQSignedTransaction,
    SignedTransaction,
    SuggestedParams,
)
from falcon_python import Falcon1024

from utils.constants.core import (
    MAINNET_GENESIS_HASH,
    MAINNET_GENESIS_ID,
    WALLET_CONNECT_NONCE_PREFIX,
)
from walletauth.verifiers import (
    MAX_SIGNED_TXN_B64_LENGTH,
    VERIFIERS,
    AlgorandSignedTxnVerifier,
    EvmXChainVerifier,
    WalletProofVerifier,
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


def make_pq_stxn(
    pk=None,
    sk=None,
    sender=None,
    authorizing_address=None,
    scheme=b"f1",
    salt=None,
    note=None,
    tamper_sig=False,
):
    if pk is None or sk is None:
        pk, sk = Falcon1024.generate_keypair()
    derived_addr, canonical_salt = encoding.address_from_pq_key(
        scheme if isinstance(scheme, bytes) else scheme.encode(), pk
    )
    if salt is None:
        salt = canonical_salt
    actual_sender = sender or derived_addr
    txn = make_self_payment(actual_sender, note or make_note())
    to_sign = txn.bytes_to_sign()
    sig = Falcon1024.detached_sign(sk, to_sign)
    if tamper_sig:
        sig = bytearray(sig)
        sig[50] ^= 0xFF
        sig = bytes(sig)
    pqsig = PQSig(scheme, salt, pk, sig)
    return PQSignedTransaction(txn, pqsig, authorizing_address=authorizing_address)


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
    verifier = AlgorandSignedTxnVerifier(algod_factory=algod_factory or fake_algod())
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

    def test_algorand_verifier_oversized_payload_returns_none(self):
        verifier = AlgorandSignedTxnVerifier(algod_factory=fake_algod())
        assert (
            verifier.verify(
                address="A" * 58,
                nonce=NONCE,
                prefix=WALLET_CONNECT_NONCE_PREFIX,
                payload={"signedTransaction": "A" * (MAX_SIGNED_TXN_B64_LENGTH + 1)},
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

    # # verify - post-quantum
    def test_algorand_verifier_valid_native_pq_returns_address(self):
        pk, sk = Falcon1024.generate_keypair()
        derived_addr, _ = encoding.address_from_pq_key(b"f1", pk)
        stxn = make_pq_stxn(pk=pk, sk=sk)
        assert verify(stxn, derived_addr) == derived_addr

    def test_algorand_verifier_tampered_pq_sig_returns_none(self):
        pk, sk = Falcon1024.generate_keypair()
        derived_addr, _ = encoding.address_from_pq_key(b"f1", pk)
        stxn = make_pq_stxn(pk=pk, sk=sk, tamper_sig=True)
        assert verify(stxn, derived_addr) is None

    def test_algorand_verifier_mismatched_native_pq_sender_returns_none(self):
        pk, sk = Falcon1024.generate_keypair()
        _, other_addr = account.generate_account()
        # Sender is other_addr, but pk derives derived_addr, with no authorizing_address
        stxn = make_pq_stxn(pk=pk, sk=sk, sender=other_addr)
        assert verify(stxn, other_addr) is None

    def test_algorand_verifier_confirmed_pq_rekey_returns_legacy_sender(self):
        _, legacy_sender = account.generate_account()
        pk, sk = Falcon1024.generate_keypair()
        auth_addr, _ = encoding.address_from_pq_key(b"f1", pk)
        stxn = make_pq_stxn(
            pk=pk, sk=sk, sender=legacy_sender, authorizing_address=auth_addr
        )
        assert (
            verify(
                stxn,
                legacy_sender,
                algod_factory=fake_algod(auth_addr=auth_addr),
            )
            == legacy_sender
        )

    def test_algorand_verifier_unconfirmed_pq_rekey_returns_none(self):
        _, legacy_sender = account.generate_account()
        pk, sk = Falcon1024.generate_keypair()
        auth_addr, _ = encoding.address_from_pq_key(b"f1", pk)
        stxn = make_pq_stxn(
            pk=pk, sk=sk, sender=legacy_sender, authorizing_address=auth_addr
        )
        assert (
            verify(
                stxn,
                legacy_sender,
                algod_factory=fake_algod(auth_addr=None),
            )
            is None
        )

    def test_algorand_verifier_mismatched_pq_authorizing_address_returns_none(self):
        _, legacy_sender = account.generate_account()
        _, fake_auth_addr = account.generate_account()
        pk, sk = Falcon1024.generate_keypair()
        # The key derives derived_addr, but authorizing_address is fake_auth_addr
        stxn = make_pq_stxn(
            pk=pk, sk=sk, sender=legacy_sender, authorizing_address=fake_auth_addr
        )
        assert (
            verify(
                stxn,
                legacy_sender,
                algod_factory=fake_algod(auth_addr=fake_auth_addr),
            )
            is None
        )

    def test_algorand_verifier_pq_payload_larger_than_2kb_succeeds(self):
        pk, sk = Falcon1024.generate_keypair()
        derived_addr, _ = encoding.address_from_pq_key(b"f1", pk)
        stxn = make_pq_stxn(pk=pk, sk=sk)
        payload = make_payload(stxn)
        # Verify base64 string length is indeed > 2048 chars (the old limit)
        assert len(payload["signedTransaction"]) > 2048
        assert len(payload["signedTransaction"]) <= MAX_SIGNED_TXN_B64_LENGTH
        assert verify(stxn, derived_addr) == derived_addr

    def test_algorand_verifier_recover_returns_native_pq_sender(self):
        pk, sk = Falcon1024.generate_keypair()
        derived_addr, _ = encoding.address_from_pq_key(b"f1", pk)
        stxn = make_pq_stxn(pk=pk, sk=sk)
        verifier = AlgorandSignedTxnVerifier(algod_factory=fake_algod())
        proven = verifier.recover(
            nonce=NONCE,
            prefix=WALLET_CONNECT_NONCE_PREFIX,
            payload=make_payload(stxn),
        )
        assert proven == derived_addr

    def test_algorand_verifier_recover_returns_rekeyed_pq_legacy_sender(self):
        _, legacy_sender = account.generate_account()
        pk, sk = Falcon1024.generate_keypair()
        auth_addr, _ = encoding.address_from_pq_key(b"f1", pk)
        stxn = make_pq_stxn(
            pk=pk, sk=sk, sender=legacy_sender, authorizing_address=auth_addr
        )
        verifier = AlgorandSignedTxnVerifier(
            algod_factory=fake_algod(auth_addr=auth_addr)
        )
        proven = verifier.recover(
            nonce=NONCE,
            prefix=WALLET_CONNECT_NONCE_PREFIX,
            payload=make_payload(stxn),
        )
        assert proven == legacy_sender

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
            verify(stxn, rekeyed, algod_factory=fake_algod(auth_addr=signer)) == rekeyed
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

    # # _network_ok
    def test_algorand_verifier_network_ok_normalizes_bytes_genesis_hash(self):
        secret, address = account.generate_account()
        stxn = make_self_payment(address, make_note()).sign(secret)
        txn = stxn.transaction
        txn.genesis_hash = base64.b64decode(MAINNET_GENESIS_HASH)
        verifier = AlgorandSignedTxnVerifier(algod_factory=fake_algod())
        assert verifier._network_ok(txn) is True

    def test_algorand_verifier_network_ok_rejects_wrong_bytes_genesis_hash(self):
        secret, address = account.generate_account()
        stxn = make_self_payment(address, make_note()).sign(secret)
        txn = stxn.transaction
        txn.genesis_hash = b"z" * 32
        verifier = AlgorandSignedTxnVerifier(algod_factory=fake_algod())
        assert verifier._network_ok(txn) is False

    # # recover (login entry point)
    def test_algorand_verifier_recover_returns_sender(self):
        secret, address = account.generate_account()
        stxn = make_self_payment(address, make_note()).sign(secret)
        verifier = AlgorandSignedTxnVerifier(algod_factory=fake_algod())
        proven = verifier.recover(
            nonce=NONCE,
            prefix=WALLET_CONNECT_NONCE_PREFIX,
            payload=make_payload(stxn),
        )
        assert proven == address

    def test_algorand_verifier_recover_rejects_non_self_payment(self):
        secret, address = account.generate_account()
        _, receiver = account.generate_account()
        txn = PaymentTxn(
            sender=address, sp=make_params(), receiver=receiver, amt=0, note=make_note()
        )
        verifier = AlgorandSignedTxnVerifier(algod_factory=fake_algod())
        assert (
            verifier.recover(
                nonce=NONCE,
                prefix=WALLET_CONNECT_NONCE_PREFIX,
                payload=make_payload(txn.sign(secret)),
            )
            is None
        )

    def test_evm_verifier_recover_is_separate_from_algorand(self):
        # The EVM verifier is its own implementation; the Algorand verifier's
        # recover handles only signed transactions.
        assert isinstance(VERIFIERS["evm"], EvmXChainVerifier)

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


class TestWalletProofVerifier:
    """Testing class for the :class:`WalletProofVerifier` interface."""

    # # verify
    def test_walletauth_walletproofverifier_verify_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            WalletProofVerifier().verify(
                address="A" * 58,
                nonce=NONCE,
                prefix=WALLET_CONNECT_NONCE_PREFIX,
                payload={},
            )


class TestEvmXChainVerifier:
    """Testing class for :class:`EvmXChainVerifier` verifier."""

    @staticmethod
    def _sign(message):
        from eth_account import Account
        from eth_account.messages import encode_defunct

        acct = Account.create()
        signed = acct.sign_message(encode_defunct(text=message))
        raw = signed.signature.hex()
        return acct.address, raw if raw.startswith("0x") else "0x" + raw

    # # recover
    def test_evm_verifier_recover_returns_lowercased_signer(self):
        address, signature = self._sign(WALLET_CONNECT_NONCE_PREFIX + NONCE)
        proven = EvmXChainVerifier().recover(
            nonce=NONCE,
            prefix=WALLET_CONNECT_NONCE_PREFIX,
            payload={"signature": signature},
        )
        assert proven == address.lower()

    def test_evm_verifier_recover_none_without_signature(self):
        assert (
            EvmXChainVerifier().recover(
                nonce=NONCE, prefix=WALLET_CONNECT_NONCE_PREFIX, payload={}
            )
            is None
        )

    def test_evm_verifier_recover_none_on_bad_signature(self):
        assert (
            EvmXChainVerifier().recover(
                nonce=NONCE,
                prefix=WALLET_CONNECT_NONCE_PREFIX,
                payload={"signature": "0xdeadbeef"},
            )
            is None
        )

    def test_evm_verifier_recover_none_on_oversized_signature(self):
        assert (
            EvmXChainVerifier().recover(
                nonce=NONCE,
                prefix=WALLET_CONNECT_NONCE_PREFIX,
                payload={"signature": "0x" + "a" * 300},
            )
            is None
        )

    def test_evm_verifier_recover_none_on_wrong_nonce(self):
        # A signature over a different challenge recovers a different (unrelated)
        # address, never the claimed one; here we only assert it doesn't match a
        # signature made for another nonce when looked up against this one.
        address, signature = self._sign(WALLET_CONNECT_NONCE_PREFIX + "other-nonce")
        proven = EvmXChainVerifier().recover(
            nonce=NONCE,
            prefix=WALLET_CONNECT_NONCE_PREFIX,
            payload={"signature": signature},
        )
        # recovery still yields *an* address, but not the signer's intended one
        assert proven != address.lower()

    # # verify (inherited wrapper)
    def test_evm_verifier_verify_uses_recover(self):
        address, signature = self._sign(WALLET_CONNECT_NONCE_PREFIX + NONCE)
        result = EvmXChainVerifier().verify(
            address=address.lower(),
            nonce=NONCE,
            prefix=WALLET_CONNECT_NONCE_PREFIX,
            payload={"signature": signature},
        )
        assert result == address.lower()
