"""
Copyright (c) 2022 Algorand Name Service

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
"""

import datetime
import sys
import unittest
from cmath import exp
from unicodedata import name
from xml.dom.pulldom import default_bufsize

import ans_helper as anshelper

sys.path.append("../")
from nameservice.anssdk import constants
from nameservice.anssdk.ans import ANS

unittest.TestLoader.sortTestMethodsUsing = None


class TestDotAlgoNameRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.algod_client = anshelper.SetupClient()
        cls.algod_indexer = anshelper.SetupIndexer()
        cls.sdk = ANS(cls.algod_client, cls.algod_indexer)

    def test_name_resolution(self):
        owner = self.sdk.name("lalith.algo").get_owner()
        self.assertEqual(
            owner, "PD2CGHFAZZQNYBRPZH7HNTA275K3FKZPENRSUXWZHBIVNPHVDFHLNIUSXU"
        )

    def test_name_resolution_value_property(self):
        value = self.sdk.name("lalith.algo").get_value()
        self.assertEqual(
            value, "PD2CGHFAZZQNYBRPZH7HNTA275K3FKZPENRSUXWZHBIVNPHVDFHLNIUSXU"
        )

    def test_name_resolution_content_property(self):
        content = self.sdk.name("ans.algo").get_content()
        self.assertEqual(
            content, "sia://CABxqjJm9_J1fDCeytsQrmsKn3f0z2nbzfgE_N73MU0bpA"
        )

    def test_name_resolution_text_property(self):
        value = self.sdk.name("ans.algo").get_text("discord")
        self.assertEqual(value, "https://discord.gg/6fKwtXWKUR")

    def test_name_resolution_get_all_information(self):
        info = self.sdk.name("ans.algo").get_all_information()
        self.assertEqual(info["found"], True)

    def test_name_resolution_get_expiry(self):
        expiry = self.sdk.name("ans.algo").get_expiry()
        self.assertEqual(expiry, datetime.datetime(2023, 2, 25, 21, 58, 50))

    def test_names_owned_by_address(self):
        names = self.sdk.address(
            "PD2CGHFAZZQNYBRPZH7HNTA275K3FKZPENRSUXWZHBIVNPHVDFHLNIUSXU"
        ).get_names(socials=True, limit=2)

        self.assertGreaterEqual(len(names), 2)

    def test_default_domain(self):
        default_domain = self.sdk.address(
            "PD2CGHFAZZQNYBRPZH7HNTA275K3FKZPENRSUXWZHBIVNPHVDFHLNIUSXU"
        ).get_default_domain()
        self.assertEqual(default_domain, "sanjaysahu.algo")

    def test_prep_name_reg_txns(self):
        name_reg_txns = self.sdk.name("xyz1234.algo").register(
            "RANDGVRRYGVKI3WSDG6OGTZQ7MHDLIN5RYKJBABL46K5RQVHUFV3NY5DUE", 5
        )
        self.assertGreaterEqual(len(name_reg_txns), 2)

    def test_prep_link_socials_txn(self):
        edited_handles = {"discord": "lmedury", "twitter": "lmedury"}

        update_name_property_txns = self.sdk.name("ans.algo").update(
            "PD2CGHFAZZQNYBRPZH7HNTA275K3FKZPENRSUXWZHBIVNPHVDFHLNIUSXU", edited_handles
        )
        self.assertGreaterEqual(len(update_name_property_txns), 2)

    def test_prep_name_renew_txns(self):
        name_renew_txns = self.sdk.name("ans.algo").renew(
            "PD2CGHFAZZQNYBRPZH7HNTA275K3FKZPENRSUXWZHBIVNPHVDFHLNIUSXU", 2
        )
        self.assertEqual(len(name_renew_txns), 2)

    def test_prep_initiate_name_transfer_txn(self):
        initiate_transfer_txn = self.sdk.name("ans.algo").init_transfer(
            "PD2CGHFAZZQNYBRPZH7HNTA275K3FKZPENRSUXWZHBIVNPHVDFHLNIUSXU",
            "RANDGVRRYGVKI3WSDG6OGTZQ7MHDLIN5RYKJBABL46K5RQVHUFV3NY5DUE",
            0,
        )

    def test_prep_accept_name_transfer_txns(self):
        accept_transfer_txns = self.sdk.name("ans.algo").accept_transfer(
            "RANDGVRRYGVKI3WSDG6OGTZQ7MHDLIN5RYKJBABL46K5RQVHUFV3NY5DUE",
            "PD2CGHFAZZQNYBRPZH7HNTA275K3FKZPENRSUXWZHBIVNPHVDFHLNIUSXU",
            0,
        )
        self.assertEqual(len(accept_transfer_txns), 3)


if __name__ == "__main__":
    unittest.main()
