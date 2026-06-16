"""Module containing functions for xChain Accounts."""

import base64
import logging

from algosdk.transaction import LogicSigAccount

from utils.constants.core import ALGOD_EXCEPTIONS

ALGO_X_EVM_LSIG_TEAL = "#pragma version 11\n#pragma typetrack false\n\n// smart_contracts/algo-x-evm/logicsig.algo.ts::program() -> uint64:\nmain:\n    bytecblock TMPL_OWNER\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:32\n    // const txnIdPayload = Global.groupSize === 1 ? Txn.txId : Global.groupId\n    global GroupSize\n    pushint 1 // 1\n    ==\n    bz main_ternary_false@2\n    txn TxID\n\nmain_ternary_merge@3:\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:35\n    // const sig = op.arg(0)\n    arg_0\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:40\n    // assert(op.extract(sig, 0, 1) === Bytes.fromHex('01'))\n    dup\n    extract 0 1\n    pushbytes 0x01\n    ==\n    assert\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:42\n    // const r = op.extract(sig, 1, 32)\n    dup\n    extract 1 32\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:43\n    // const s = op.extract(sig, 33, 32)\n    dig 1\n    extract 33 32\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:44\n    // const v = op.btoi(op.extract(sig, 65, 1))\n    uncover 2\n    pushint 65 // 65\n    getbyte\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:45\n    // const recoveryId: uint64 = v - 27 // Ethereum uses 27/28, AVM expects 0/1\n    pushint 27 // 27\n    -\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:61\n    // const messageHash = op.keccak256(messageTypeHash.concat(txnIdPayload))\n    pushbytes 0x612f2598ebd964c16ba67a8b06d6f08ce24ab0911f0ff5a267a22fe01e687334\n    uncover 4\n    concat\n    keccak256\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:66\n    // const digest = op.keccak256(Bytes.fromHex('1901').concat(domainSeparator).concat(messageHash))\n    pushbytes 0x1901cef8b9829414ba4a13ea8f8c442b747ffe119c643d2213d22b4e137036a2d573\n    swap\n    concat\n    keccak256\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:69\n    // const [pubkeyX, pubkeyY] = op.ecdsaPkRecover(op.Ecdsa.Secp256k1, digest, recoveryId, r, s)\n    swap\n    uncover 3\n    uncover 3\n    ecdsa_pk_recover Secp256k1\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:73\n    // const recoveredAddress = op.extract(op.keccak256(op.concat(pubkeyX, pubkeyY)), 12, 20)\n    concat\n    keccak256\n    extract 12 20\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:76\n    // return recoveredAddress === owner.bytes\n    bytec_0 // TMPL_OWNER\n    ==\n    return\n\nmain_ternary_false@2:\n    // smart_contracts/algo-x-evm/logicsig.algo.ts:32\n    // const txnIdPayload = Global.groupSize === 1 ? Txn.txId : Global.groupId\n    global GroupID\n    b main_ternary_merge@3\n"

logger = logging.getLogger(__name__)


def _normalize_address(evm_address):
    """Return normalized EVM address without 0x prefix and in lowercase.

    :param evm_address: EVM address to normalize
    :type evm_address: str
    :return: str
    """
    if evm_address.startswith("0x") or evm_address.startswith("0X"):
        return evm_address[2:].lower()
    return evm_address.lower()


def _compiled_evm_address(evm_address, algod_client):
    """Return compiled EVM address logic signature bytes.

    :param evm_address: EVM address to compile
    :type evm_address: str
    :param algod_client: Algorand node client instance
    :type algod_client: :class:`AlgodClient`
    :var normalized: normalized EVM address without 0x prefix
    :type normalized: str
    :var owner_hex: hex-formatted EVM address for TEAL injection
    :type owner_hex: str
    :var teal_source: TEAL source code with substituted owner address
    :type teal_source: str
    :var result: compilation response from Node instance
    :type result: dict
    :return: bytes
    """
    normalized = _normalize_address(evm_address)
    # Substitute the TMPL_OWNER in the TEAL template.
    # Ensure proper hex formatting for TEAL byte arrays (e.g., 0x...)
    owner_hex = f"0x{normalized}"
    teal_source = ALGO_X_EVM_LSIG_TEAL.replace("TMPL_OWNER", owner_hex)
    result = algod_client.compile(teal_source)
    return base64.b64decode(result["result"])


# # PUBLIC
def check_evm_address(evm_address, algod_client):
    """Return Algorand address for a given EVM address.

    :param evm_address: EVM address to check
    :type evm_address: str
    :param algod_client: Algorand node client instance
    :type algod_client: :class:`AlgodClient`
    :var compiled: compiled logic signature bytes
    :type compiled: bytes
    :var lsig: LogicSigAccount instance initialized with compiled bytes
    :type lsig: :class:`LogicSigAccount`
    :return: str
    """
    try:
        compiled = _compiled_evm_address(evm_address, algod_client)
        lsig = LogicSigAccount(compiled)
        return lsig.address()
    except ALGOD_EXCEPTIONS:
        return evm_address
