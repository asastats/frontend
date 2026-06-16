import base64
import time

from algosdk import encoding, logic
from algosdk.transaction import LogicSig
from pyteal import *
from pyteal import Mode, compileTeal

from nameservice.anssdk import constants, dot_algo_name_record
from nameservice.anssdk.constants import (
    VALID_ADDRESS_PROPERTIES,
    VALID_BYTE_PROPERTIES,
    VALID_INT_PROPERTIES,
)
from nameservice.anssdk.helper import validation


class AnsResolver:
    def __init__(self, client, indexer=None):
        self.algod_client = client
        if indexer is not None:
            self.algod_indexer = indexer

    def compile_program(self, algod_client, source_code):
        compile_response = algod_client.compile(source_code.decode("utf-8"))
        return base64.b64decode(compile_response["result"])

    def prep_name_record_logic_sig(self, name, reg_app_id):
        reg_escrow_acct = logic.get_application_address(reg_app_id)
        logic_sig_teal = compileTeal(
            dot_algo_name_record.ValidateRecord(name, reg_app_id, reg_escrow_acct),
            Mode.Signature,
            version=4,
        )
        validate_name_record_program = self.compile_program(
            self.algod_client, str.encode(logic_sig_teal)
        )
        lsig = LogicSig(validate_name_record_program)
        return lsig

    def resolve_name(self, name):
        name = name.split(".algo")[0]
        name = name.lower()
        validation.is_valid_name(name)
        reg_app_id = constants.APP_ID
        account_info = self.algod_client.account_info(
            address=self.prep_name_record_logic_sig(name, reg_app_id).address()
        )
        if len(account_info["apps-local-state"]) == 0:
            return {"found": False}
        try:
            socials = []
            metadata = []
            allowed_socials = [
                "twitter",
                "github",
                "youtube",
                "telegram",
                "reddit",
                "discord",
            ]
            value_property = None
            for apps_local_data in account_info["apps-local-state"]:
                owner = None
                expiry = None
                if apps_local_data["id"] == reg_app_id:
                    for key_value in apps_local_data["key-value"]:
                        key = validation.decode_value(key_value["key"])
                        if key == "name":
                            continue
                        if key in VALID_ADDRESS_PROPERTIES:
                            kv = {}
                            value = validation.decode_address(
                                key_value["value"]["bytes"]
                            )
                            if key == "owner":
                                owner = value
                            elif key == "value":
                                value_property = value
                            elif key == "transfer_to":
                                if value != b"":
                                    kv[key] = value
                                    metadata.append(kv)
                        elif key in VALID_BYTE_PROPERTIES:
                            value = validation.decode_value(key_value["value"]["bytes"])
                            kv = {}
                            if value == b"":
                                continue
                            if key in allowed_socials:
                                kv[key] = value
                                socials.append(kv)
                                continue
                            kv[key] = value
                            metadata.append(kv)
                        elif key in VALID_INT_PROPERTIES:
                            kv = {}
                            value = key_value["value"]["uint"]
                            kv[key] = value
                            if key == "expiry":
                                expiry = value
                                continue
                            metadata.append(kv)

                if owner != None and expiry != None and expiry > int(time.time()):
                    if value_property is None:
                        value_property = owner
                    return {
                        "found": True,
                        "owner": owner,
                        "expiry": expiry,
                        "socials": socials,
                        "metadata": metadata,
                        "value": value_property,
                    }
                else:
                    return {"found": False}

        except Exception as e:
            return {"found": False}

    def get_names_owned_by_address(
        self, address, socials=False, metadata=False, limit=0
    ):
        is_valid_address = encoding.is_valid_address(address)
        indexer = None
        try:
            if self.algod_indexer is not None:
                indexer = self.algod_indexer
        except Exception as err:
            return {"err": "Indexer is not instantiated"}
            return

        if is_valid_address is False:
            return {"err": "Invalid Algorand address"}
        else:
            next_token = ""
            txn_length = 1
            txns = []

            while txn_length > 0:
                account_info = indexer.search_transactions(
                    address=address,
                    address_role="sender",
                    limit=10000,
                    next_page=next_token,
                    txn_type="appl",
                    application_id=constants.APP_ID,
                    start_time="2022-02-25",
                )

                if len(account_info["transactions"]) > 0:
                    txn_length = len(account_info["transactions"])
                    txns += account_info["transactions"]
                    if account_info["next-token"] is not None:
                        next_token = account_info["next-token"]
                    else:
                        break
                else:
                    break

            names = []
            owned_names = []
            try:
                for txn in txns:
                    if txn["tx-type"] == "appl":
                        if (
                            txn["application-transaction"]["application-id"]
                            == constants.APP_ID
                        ):
                            args = txn["application-transaction"]["application-args"]
                            method = base64.b64decode(args[0]).decode("utf-8")
                            if len(args) >= 2 or method == "accept_transfer":
                                if method == "register_name":
                                    arg_1 = base64.b64decode(args[1]).decode("utf-8")
                                    if arg_1 not in names:
                                        names.append(arg_1 + ".algo")
                                elif method == "accept_transfer":
                                    lsig_account = txn["application-transaction"][
                                        "accounts"
                                    ][0]
                                    lsig_account_info = indexer.account_info(
                                        lsig_account
                                    )
                                    lsig_account_info = lsig_account_info["account"][
                                        "apps-local-state"
                                    ]

                                    for app in lsig_account_info:
                                        if app["id"] == constants.APP_ID:
                                            kv_pairs = app["key-value"]

                                            for kv_pair in kv_pairs:
                                                key = base64.b64decode(
                                                    kv_pair["key"]
                                                ).decode("utf-8")
                                                value = base64.b64decode(
                                                    kv_pair["value"]["bytes"]
                                                )
                                                # print(key)
                                                if key == "name":
                                                    if value not in names:
                                                        names.append(
                                                            value.decode("utf-8")
                                                            + ".algo"
                                                        )
                                                        break
                owned_names = []
                for name in names:
                    if len(owned_names) >= limit and limit > 0:
                        return owned_names

                    domain_info = self.resolve_name(name)
                    if domain_info["owner"] == address:
                        kv = {}
                        kv["name"] = name
                        if socials is True:
                            kv["socials"] = domain_info["socials"]
                        if metadata is True:
                            kv["metadata"] = domain_info["metadata"]
                        owned_names.append(kv)

            except Exception as err:
                print("Error: ", err)
                return []

            return owned_names

    def get_default_domain(self, address):
        is_valid_address = encoding.is_valid_address(address)
        indexer = None
        try:
            if self.algod_indexer is not None:
                indexer = self.algod_indexer
        except Exception as err:
            return {"err": "Indexer is not instantiated"}
            return

        if is_valid_address is False:
            return {"err": "Invalid Algorand address"}
        else:
            next_token = ""
            txn_length = 1
            txns = []

            while txn_length > 0:
                account_info = indexer.search_transactions(
                    address=address,
                    address_role="sender",
                    limit=10000,
                    next_page=next_token,
                    txn_type="appl",
                    application_id=constants.APP_ID,
                    start_time="2022-02-25",
                )

                if len(account_info["transactions"]) > 0:
                    txn_length = len(account_info["transactions"])
                    txns += account_info["transactions"]
                    if account_info["next-token"] is not None:
                        next_token = account_info["next-token"]
                    else:
                        break
                else:
                    break

            for txn in txns:
                arg_0 = txn["application-transaction"]["application-args"][0]
                if base64.b64decode(arg_0).decode("utf-8") == "set_default_account":
                    acc_0 = txn["application-transaction"]["accounts"]
                    account_info = self.algod_client.account_info(acc_0)
                    for apps_local_data in account_info["apps-local-state"]:
                        owner = None
                        expiry = None
                        if apps_local_data["id"] == constants.APP_ID:
                            for key_value in apps_local_data["key-value"]:
                                if validation.decode_value(key_value["key"]) == "name":
                                    return validation.decode_value(
                                        key_value["value"]["bytes"]
                                    )

            domain = self.get_names_owned_by_address(address, False, False, 1)
            return domain[0]["name"]
