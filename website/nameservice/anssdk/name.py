import datetime
from audioop import add
from curses import meta

from nameservice.anssdk.resolver import AnsResolver
from nameservice.anssdk.transactions import Transactions


class Name:
    def __init__(self, name, client, indexer=None):
        self.name = name
        self.resolver_obj = AnsResolver(client, indexer)
        self.transactions_obj = Transactions(client)

    def get_owner(self):
        domain_info = self.resolver_obj.resolve_name(self.name)
        if domain_info["found"] is True:
            return domain_info["owner"]

    def get_value(self):
        domain_info = self.resolver_obj.resolve_name(self.name)
        if domain_info["found"] is True:
            return domain_info["value"]

    def get_content(self):
        metadata = self.resolver_obj.resolve_name(self.name)["metadata"]
        for data in metadata:
            if data.get("content") is not None:
                return data.get("content")

    def get_text(self, key):
        metadata = self.resolver_obj.resolve_name(self.name)["metadata"]
        socials = self.resolver_obj.resolve_name(self.name)["socials"]
        for data in metadata:
            if data.get(key) is not None:
                return data.get(key)

        for data in socials:
            if data.get(key) is not None:
                return data.get(key)

        raise Exception("Property {key} is not set".format(key=key))

    def get_all_information(self):
        return self.resolver_obj.resolve_name(self.name)

    def get_expiry(self):
        info = self.resolver_obj.resolve_name(self.name)
        if info["found"] is True:
            return datetime.datetime.fromtimestamp(info["expiry"])

    def register(self, address, period):
        info = self.resolver_obj.resolve_name(self.name)
        if info["found"] is True:
            raise Exception(
                "Domain {domain} is already registered".format(domain=self.name)
            )

        return self.transactions_obj.prepare_name_registration_transactions(
            self.name, address, period
        )

    def update(self, address, edited_handles):
        info = self.resolver_obj.resolve_name(self.name)
        if info["found"] is not True:
            raise Exception(
                "Domain {domain} is not registered".format(domain=self.name)
            )

        return self.transactions_obj.prepare_update_name_property_transactions(
            self.name, address, edited_handles
        )

    def renew(self, address, period):
        info = self.resolver_obj.resolve_name(self.name)
        if info["found"] is not True:
            raise Exception(
                "Domain {domain} is not registered".format(domain=self.name)
            )

        return self.transactions_obj.prepare_name_renewal_transactions(
            self.name, address, period
        )

    def init_transfer(self, owner, new_owner, price):
        info = self.resolver_obj.resolve_name(self.name)
        if info["found"] is not True:
            raise Exception(
                "Domain {domain} is not registered".format(domain=self.name)
            )

        if info["owner"] != owner:
            raise Exception(
                "Domain {domain} is not owned by {address}".format(
                    domain=self.name, address=owner
                )
            )

        return self.transactions_obj.prepare_initiate_name_transfer_transaction(
            self.name, owner, new_owner, price
        )

    def accept_transfer(self, new_owner, owner, price):
        info = self.resolver_obj.resolve_name(self.name)
        if info["found"] is not True:
            raise Exception(
                "Domain {domain} is not registered".format(domain=self.name)
            )

        if info["owner"] != owner:
            raise Exception(
                "Domain {domain} is not owned by {address}".format(
                    domain=self.name, address=owner
                )
            )

        return self.transactions_obj.prepare_accept_name_transfer_transactions(
            self.name, new_owner, owner, price
        )
