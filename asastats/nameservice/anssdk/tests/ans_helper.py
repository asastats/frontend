"""
Copyright (c) 2022 Algorand Name Service

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
"""

import sys

from algosdk.v2client import algod, indexer
from pyteal import *

sys.path.append("../")
import base64
import datetime
import time

from nameservice.anssdk import constants
from nameservice.anssdk.dot_algo_name_record import ValidateRecord


def SetupClient():
    api_key = ""
    with open("api_key.txt", "r") as f:
        api_key = f.readlines()[0]

    # Purestake conn
    algod_address = "https://mainnet-algorand.api.purestake.io/ps2"
    headers = {"X-API-Key": api_key}

    algod_client = algod.AlgodClient(api_key, algod_address, headers=headers)
    return algod_client


def SetupIndexer():
    api_key = ""
    with open("api_key.txt", "r") as f:
        api_key = f.readlines()[0]

    algod_address = "https://mainnet-algorand.api.purestake.io/idx2"
    headers = {
        "X-API-key": api_key,
    }
    algod_indexer = indexer.IndexerClient("", algod_address, headers)

    return algod_indexer
