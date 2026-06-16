"""Testing module for :py:mod:`api.structs` module."""

import inspect

import api.structs


class TestApiStructsNamedTuples:
    """Testing class for :py:mod:`api.structs` namedtuples."""

    # # ACCOUNT
    # # Entities
    def test_api_structs_defines_entities_tuple(self):
        assert inspect.isclass(api.structs.Entities)
        assert api.structs.Entities.__name__ == "Entities"

    def test_api_structs_entities_tuple_fields(self):
        assert api.structs.Entities._fields == (
            "programs",
            "providers",
            "markets",
        )

    def test_api_structs_entities_defaults(self):
        assert api.structs.Entities._field_defaults == {
            "programs": None,
            "providers": None,
            "markets": None,
        }

    # # AccountInfo
    def test_api_structs_defines_accountinfo_tuple(self):
        assert inspect.isclass(api.structs.AccountInfo)
        assert api.structs.AccountInfo.__name__ == "AccountInfo"

    def test_api_structs_accountinfo_tuple_fields(self):
        assert api.structs.AccountInfo._fields == (
            "addresses",
            "bundle",
            "values_in",
            "online",
            "points",
        )

    def test_api_structs_accountinfo_defaults(self):
        assert api.structs.AccountInfo._field_defaults == {
            "addresses": None,
            "bundle": None,
            "values_in": "ALGO",
            "online": None,
            "points": None,
        }

    # # AsaItem
    def test_api_structs_defines_asaitem_tuple(self):
        assert inspect.isclass(api.structs.AsaItem)
        assert api.structs.AsaItem.__name__ == "AsaItem"

    def test_api_structs_asaitem_tuple_fields(self):
        assert api.structs.AsaItem._fields == (
            "value",
            "asset",
            "amount",
            "price",
            "programs",
        )

    # # AsaItemProgram
    def test_api_structs_defines_asaitemprogram_tuple(self):
        assert inspect.isclass(api.structs.AsaItemProgram)
        assert api.structs.AsaItemProgram.__name__ == "AsaItemProgram"

    def test_api_structs_asaitemprogram_tuple_fields(self):
        assert api.structs.AsaItemProgram._fields == (
            "program",
            "value",
            "amount",
            "proxy",
            "distribution",
            "linked",
        )

    def test_api_structs_asaitemprogram_defaults(self):
        assert api.structs.AsaItemProgram._field_defaults == {
            "program": "program",
            "value": None,
            "amount": None,
            "proxy": None,
            "distribution": None,
            "linked": None,
        }

    # # AsaProgram
    def test_api_structs_defines_asaprogram_tuple(self):
        assert inspect.isclass(api.structs.AsaProgram)
        assert api.structs.AsaProgram.__name__ == "AsaProgram"

    def test_api_structs_asaprogram_tuple_fields(self):
        assert api.structs.AsaProgram._fields == (
            "type",
            "name",
            "provider",
            "url",
            "code",
        )

    def test_api_structs_asaprogram_defaults(self):
        assert api.structs.AsaProgram._field_defaults == {
            "type": None,
            "name": None,
            "provider": None,
            "url": None,
            "code": None,
        }

    # # AsaLink
    def test_api_structs_defines_asalink_tuple(self):
        assert inspect.isclass(api.structs.AsaLink)
        assert api.structs.AsaLink.__name__ == "AsaLink"

    def test_api_structs_asalink_tuple_fields(self):
        assert api.structs.AsaLink._fields == ("provider", "link", "title")

    # # Distribution
    def test_api_structs_defines_distribution_tuple(self):
        assert inspect.isclass(api.structs.Distribution)
        assert api.structs.Distribution.__name__ == "Distribution"

    def test_api_structs_distribution_tuple_fields(self):
        assert api.structs.Distribution._fields == ("value", "amount", "link")

    # # DistributionLink
    def test_api_structs_defines_distributionlink_tuple(self):
        assert inspect.isclass(api.structs.DistributionLink)
        assert api.structs.DistributionLink.__name__ == "DistributionLink"

    def test_api_structs_distributionlink_tuple_fields(self):
        assert api.structs.DistributionLink._fields == ("provider", "text", "url")

    # # LinkedData
    def test_api_structs_defines_linkeddata_tuple(self):
        assert inspect.isclass(api.structs.LinkedData)
        assert api.structs.LinkedData.__name__ == "LinkedData"

    def test_api_structs_linkeddata_tuple_fields(self):
        assert api.structs.LinkedData._fields == (
            "provider",
            "text",
            "link",
            "value",
            "amount",
            "balance",
            "info",
            "id",
        )

    def test_api_structs_linkeddata_defaults(self):
        assert api.structs.LinkedData._field_defaults == {
            "provider": None,
            "text": "text",
            "link": None,
            "value": None,
            "amount": None,
            "balance": None,
            "info": None,
            "id": None,
        }

    # # Provider
    def test_api_structs_defines_provider_tuple(self):
        assert inspect.isclass(api.structs.Provider)
        assert api.structs.Provider.__name__ == "Provider"

    def test_api_structs_provider_tuple_fields(self):
        assert api.structs.Provider._fields == ("name", "info")

    def test_api_structs_provider_defaults(self):
        assert api.structs.Provider._field_defaults == {
            "name": "Unknown",
            "info": None,
        }

    # # NftCollection
    def test_api_structs_defines_nftcollection_tuple(self):
        assert inspect.isclass(api.structs.NftCollection)
        assert api.structs.NftCollection.__name__ == "NftCollection"

    def test_api_structs_nftcollection_tuple_fields(self):
        assert api.structs.NftCollection._fields == ("value", "name", "amount", "nfts")

    # # NftItem
    def test_api_structs_defines_nftitem_tuple(self):
        assert inspect.isclass(api.structs.NftItem)
        assert api.structs.NftItem.__name__ == "NftItem"

    def test_api_structs_nftitem_tuple_fields(self):
        assert api.structs.NftItem._fields == ("value", "nft", "amount", "price")

    # # Nft
    def test_api_structs_defines_nft_tuple(self):
        assert inspect.isclass(api.structs.Nft)
        assert api.structs.Nft.__name__ == "Nft"

    def test_api_structs_nft_tuple_fields(self):
        assert api.structs.Nft._fields == (
            "id",
            "name",
            "unit",
            "total",
            "decimals",
            "creator",
            "image",
            "thumbnail",
            "urls",
            "listings",
            "floor",
            "last_purchase",
            "max_purchase",
            "title",
            "description",
            "rarity",
            "traits",
        )

    # # NftCurrency
    def test_api_structs_defines_nftcurrency_tuple(self):
        assert inspect.isclass(api.structs.NftCurrency)
        assert api.structs.NftCurrency.__name__ == "NftCurrency"

    def test_api_structs_nftcurrency_tuple_fields(self):
        assert api.structs.NftCurrency._fields == ("amount", "asset")

    # # NftListing
    def test_api_structs_defines_nftlisting_tuple(self):
        assert inspect.isclass(api.structs.NftListing)
        assert api.structs.NftListing.__name__ == "NftListing"

    def test_api_structs_nftlisting_tuple_fields(self):
        assert api.structs.NftListing._fields == ("price", "market", "link", "currency")

    # # NftPurchase
    def test_api_structs_defines_nftpurchase_tuple(self):
        assert inspect.isclass(api.structs.NftPurchase)
        assert api.structs.NftPurchase.__name__ == "NftPurchase"

    def test_api_structs_nftpurchase_tuple_fields(self):
        assert api.structs.NftPurchase._fields == (
            "price",
            "market",
            "link",
            "epoch",
            "currency",
        )

    # # NftTrait
    def test_api_structs_defines_nfttrait_tuple(self):
        assert inspect.isclass(api.structs.NftTrait)
        assert api.structs.NftTrait.__name__ == "NftTrait"

    def test_api_structs_nfttrait_tuple_fields(self):
        assert api.structs.NftTrait._fields == ("name", "value")

    # # NftUrl
    def test_api_structs_defines_nfturl_tuple(self):
        assert inspect.isclass(api.structs.NftUrl)
        assert api.structs.NftUrl.__name__ == "NftUrl"

    def test_api_structs_nfturl_tuple_fields(self):
        assert api.structs.NftUrl._fields == ("typ", "url")

    # # SystemInfo
    def test_api_structs_defines_systeminfo_tuple(self):
        assert inspect.isclass(api.structs.SystemInfo)
        assert api.structs.SystemInfo.__name__ == "SystemInfo"

    def test_api_structs_systeminfo_tuple_fields(self):
        assert api.structs.SystemInfo._fields == ("warning", "information")

    def test_api_structs_systeminfo_defaults(self):
        assert api.structs.SystemInfo._field_defaults == {
            "warning": None,
            "information": None,
        }

    # # Total
    def test_api_structs_defines_total_tuple(self):
        assert inspect.isclass(api.structs.Total)
        assert api.structs.Total.__name__ == "Total"

    def test_api_structs_total_tuple_fields(self):
        assert api.structs.Total._fields == (
            "algo",
            "asa",
            "nft",
            "total",
            "totalusdc",
            "priceusdc",
            "pricealgo",
            "noteval",
            "totalwonft",
            "totalwonftusdc",
        )

    # # LP
    # # LpProvider
    def test_api_structs_defines_lpprovider_tuple(self):
        assert inspect.isclass(api.structs.LpProvider)
        assert api.structs.LpProvider.__name__ == "LpProvider"

    def test_api_structs_lpprovider_tuple_fields(self):
        assert api.structs.LpProvider._fields == ("code", "name", "baselink")

    # # LpFarming
    def test_api_structs_defines_lpfarming_tuple(self):
        assert inspect.isclass(api.structs.LpFarming)
        assert api.structs.LpFarming.__name__ == "LpFarming"

    def test_api_structs_lpfarming_tuple_fields(self):
        assert api.structs.LpFarming._fields == ("code", "name", "baselink")
