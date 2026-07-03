"""Module containing functions for NF Domains name service."""

import base64
import hashlib
import logging
from copy import deepcopy

from algosdk.encoding import encode_address
from algosdk.transaction import LogicSigAccount

from utils.constants.core import ALGOD_EXCEPTIONS
from utils.constants.nameservice import (
    NFD_APP_ID,
    NFD_LOGICSIG_BYTECODE,
    NFD_OWNER_KEY,
    NFD_SUFFIX,
    NFD_VERIFIED_CAALGO_KEY,
)

logger = logging.getLogger(__name__)


# # NFD v1
def _app_id_from_logicsig(logic_sig, algod_client):
    """Return NFD application identifier connected with provided `address`.

    :param logic_sig: logic signature account instance
    :type logic_sig: :class:`algosdk.transaction.LogicSigAccount`
    :param algod_client: Algorand node client instance
    :type algod_client: :class:`AlgodClient`
    :return: int
    """
    app_id = None
    lsig_info = algod_client.account_info(logic_sig.address())

    local_state = lsig_info["apps-local-state"]
    for state in local_state:
        for item in state["key-value"]:
            if item["key"] == "aS5hcHBpZA==":
                app_id = int.from_bytes(base64.b64decode(item["value"]["bytes"]), "big")

    return app_id


def _logicsig_from_name(prefix, lookup, app_id):
    """Create and return LogicSigAccount instance from provided arguments.

    :param prefix: predefined prefix for the app call
    :type prefix: str
    :param lookup: .algo name we're looking for
    :type lookup: str
    :param app_id: NFD application identifier
    :type app_id: int
    :return: :class:`algosdk.transaction.LogicSigAccount`
    """
    logicsig_bytecode = deepcopy(NFD_LOGICSIG_BYTECODE)

    app_bytes = list(app_id.to_bytes(8, "big"))
    logicsig_bytecode[6:14] = app_bytes

    bytes_to_append = list(prefix.encode("utf-8")) + list(lookup.encode("utf-8"))

    composed_bytecode = (
        logicsig_bytecode + _variant_buffer(len(bytes_to_append)) + bytes_to_append
    )
    return LogicSigAccount(bytes(composed_bytecode))


def _variant_buffer(number):
    """Return buffer sequence from provided `number`.

    :param number: number to create bytecode sequence from
    :type number: int
    :return: list
    """

    buf = []

    while True:
        towrite = number & 0x7F
        number >>= 7
        if number:
            buf.append(towrite | 0x80)
        else:
            buf.append(towrite)
            break

    return buf


# # NFD v2
def _check_boxes_addresses(v2_app_id, algod_client):
    """Return collection of addresses found in provided NFD v2 dApp's boxes.

    :param v2_app_id: NFD v2 application identifier
    :type v2_app_id: int
    :param algod_client: Algorand node client instance
    :type algod_client: :class:`AlgodClient`
    :var boxes: collection of box names
    :type boxes: list
    :var addresses: collection of addresses found in boxes
    :type addresses: set
    :var box: currently processed Algorand box
    :type box: list
    :var box_name: currently processed Algorand box' name
    :type box_name: bytes
    :var box_name_str: currently processed Algorand box' name as string
    :type box_name_str: str
    :var address: currently processed public Algorand address
    :type address: str
    :return: list
    """
    boxes = algod_client.application_boxes(v2_app_id)
    addresses = set()
    for box in boxes.get("boxes", []):
        box_name = base64.b64decode(box.get("name"))
        box_name_str = box_name.decode()
        if box_name_str.startswith("v.caAlgo") or box_name_str.startswith("u.caalgo"):
            try:
                response = algod_client.application_box_by_name(v2_app_id, box_name)
            except ALGOD_EXCEPTIONS:
                continue

            if box_name_str.startswith("v.caAlgo"):
                for address in _address_from_bytes_value(response.get("value", "")):
                    if address and not address.startswith("AAAAA"):
                        addresses.add(address)

            else:
                address = base64.b64decode(response.get("value", "")).decode()
                if address:
                    addresses.add(address)

    return list(addresses)


def _app_state_from_box(v2_app_id, algod_client):
    """Return NFD application state for provided NFD v2 application identifier.

    :param v2_app_id: NFD v2 application identifier
    :type v2_app_id: int
    :param algod_client: Algorand node client instance
    :type algod_client: :class:`AlgodClient`
    :var app_info: application information collection
    :type app_info: dict
    :return: int
    """
    if not v2_app_id:
        return []

    try:
        app_info = algod_client.application_info(v2_app_id)
    except ALGOD_EXCEPTIONS:
        return []

    return app_info.get("params", {}).get("global-state", [])


def _box_name_for_algo_name(name):
    """Return NFD registry app box name for provided algo name .

    :param name: .algo name connected with NFD registry app box name
    :type name: str
    :return: bytes
    """
    return hashlib.sha256(bytes("name/" + name, "utf-8")).digest()


# # COMMON
def _address_from_bytes_value(bytes_value):
    """Yield address from provided bytes value.

    :param bytes_value: representation of bytes value
    :type bytes_value: str
    :var value: state row value
    :type value: bytes
    :var address: currently processed public Algorand address
    :type address: str
    :yield: str
    """
    value = base64.b64decode(bytes_value)
    for address in [
        encode_address(value[i : i + 32]) for i in range(0, len(value), 32)
    ]:
        yield address


def _append_addresses_from_global_state_for_key(addresses, global_state, key):
    """Append addresses to `results` from provided application global state.

    :param addresses: collection of all addresses found in NFD
    :type addresses: list
    :param global_state: NFD application global state
    :type global_state: list
    :param key: target state key
    :type key: bytes
    :var state: related application global state's row
    :type state: list
    :var address: currentyl processed public Algorand address
    :type address: str
    """
    state = next((state for state in global_state if state.get("key") == key), [])
    if state:
        for address in _address_from_bytes_value(
            state.get("value", {}).get("bytes", "")
        ):
            if address not in addresses:
                addresses.append(address)


def _addresses_from_app_state(global_state, box_addresses):
    """Return address from provided application global state.

    :param global_state: NFD application global state
    :type global_state: list
    :var box_addresses: NFD v2 addresses found in boxes
    :type box_addresses: list
    :var addresses: collection of all addresses found in NFD
    :type addresses: list
    :return: str
    """
    addresses = box_addresses[:]
    _append_addresses_from_global_state_for_key(
        addresses, global_state, NFD_VERIFIED_CAALGO_KEY
    )

    if not addresses:
        _append_addresses_from_global_state_for_key(
            addresses, global_state, NFD_OWNER_KEY
        )

    return " ".join(addresses)


def _app_state_for_algo_name(name, v2_app_id, algod_client):
    """Return NFD application state from one of provided arguments (v1 or v2).

    :param name: .algo name we're looking for
    :type name: str
    :param v2_app_id: NFD v2 application identifier
    :type v2_app_id: int
    :param algod_client: Algorand node client instance
    :type algod_client: :class:`AlgodClient`
    :var app_state: application global state entries
    :type app_state: list
    :var logic_sig: logic signature account instance
    :type logic_sig: :class:`algosdk.transaction.LogicSigAccount`
    :var app_id: NFD application identifier
    :type app_id: int
    :var app_info: application information collection
    :type app_info: dict
    :return: int
    """
    # NFD V2
    app_state = _app_state_from_box(v2_app_id, algod_client)
    if len(app_state) == 0:
        # NFD V1
        logic_sig = _logicsig_from_name("name/", name, NFD_APP_ID)
        app_id = _app_id_from_logicsig(logic_sig, algod_client)
        if app_id is None:
            # non-existing name
            return []
        app_info = algod_client.application_info(app_id)
        app_state = app_info.get("params", {}).get("global-state", [])

    return app_state


# # PUBLIC
def check_name(name, algod_client):
    """Return provided address or addresses connected with NFD.

    :param name: NFD name or Algorand address
    :type name: str
    :param algod_client: Algorand node client instance
    :type algod_client: :class:`AlgodClient`
    :var algo_name: base name with truncated eventual /nfd suffix
    :type algo_name: str
    :var v2_app_id: NFC v2 smart contract application ID
    :type v2_app_id: int
    :var app_state: related NFD application global state
    :type app_state: int
    :var box_addresses: Algorand address(es) connected with NFD v2
    :type box_addresses: str
    :var addresses: Algorand address(es) connected with provided .algo name
    :type addresses: str
    :return: str
    """
    algo_name = name.lower().replace(NFD_SUFFIX, "")
    if not algo_name.endswith(".algo"):
        return name

    v2_app_id = nfd_app_id_from_algo_name(algo_name, algod_client)
    app_state = _app_state_for_algo_name(algo_name, v2_app_id, algod_client)

    if len(app_state) == 0:
        return name

    box_addresses = _check_boxes_addresses(v2_app_id, algod_client) if v2_app_id else []
    addresses = _addresses_from_app_state(app_state, box_addresses)

    return addresses or name


def nfd_app_id_from_algo_name(name, algod_client):
    """Return NFD application identifier connected with provided `name`.

    :param name: .algo name we're looking for
    :type name: str
    :param algod_client: Algorand node client instance
    :type algod_client: :class:`AlgodClient`
    :var box_name: Algorand box name connected with provided algo name
    :type box_name: :class:`AlgodClient`
    :var response: Algorand box fetching result
    :type response: dict
    :var hexed: box value hexadecimal string representation
    :type hexed: str
    :return: int
    """
    box_name = _box_name_for_algo_name(name)
    try:
        response = algod_client.application_box_by_name(NFD_APP_ID, box_name)
    except ALGOD_EXCEPTIONS:
        return None

    if len(response.get("value", "")) != 24:
        return None

    hexed = base64.b64decode(response.get("value")).hex()

    return int(hexed[16:], 16)
