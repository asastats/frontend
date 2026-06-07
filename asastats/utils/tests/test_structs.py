"""Testing module for :py:mod:`utils.structs` module."""

import inspect

import utils.structs


class TestUtilsStructsNamedTuples:
    """Testing class for :py:mod:`utils.structs` namedtuples."""

    # # Asa
    def test_utils_structs_defines_asa_tuple(self):
        assert inspect.isclass(utils.structs.Asa)
        assert utils.structs.Asa.__name__ == "Asa"

    def test_utils_structs_asa_tuple_fields(self):
        assert utils.structs.Asa._fields == (
            "id",
            "name",
            "unit",
            "total",
            "decimals",
            "url",
            "creator",
            "links",
        )

    # # Nft
    def test_utils_structs_defines_nft_tuple(self):
        assert inspect.isclass(utils.structs.Nft)
        assert utils.structs.Nft.__name__ == "Nft"

    def test_utils_structs_nft_tuple_fields(self):
        assert utils.structs.Nft._fields == (
            "id",
            "name",
            "unit",
            "total",
            "collection",
            "urls",
            "path",
            "tpath",
            "listed",
            "last",
            "max",
            "floor",
            "attrs",
            "title",
            "desc",
            "rarity",
        )

    # # Pool
    def test_utils_structs_defines_pool_tuple(self):
        assert inspect.isclass(utils.structs.Pool)
        assert utils.structs.Pool.__name__ == "Pool"

    def test_utils_structs_pool_tuple_fields(self):
        assert utils.structs.Pool._fields == (
            "app",
            "token",
            "liquidity",
            "asset1",
            "balance1",
            "asset2",
            "balance2",
            "fee",
            "code",
            "address",
            "parent",
        )

    # # Total
    def test_utils_structs_defines_total_tuple(self):
        assert inspect.isclass(utils.structs.Total)
        assert utils.structs.Total.__name__ == "Total"

    def test_utils_structs_total_tuple_fields(self):
        assert utils.structs.Total._fields == (
            "algo",
            "asa",
            "nft",
            "total",
            "totalusdc",
            "priceusdc",
            "pricealgo",
            "noteval",
        )

    # # NftPurchase
    def test_utils_structs_defines_nftpurchase_tuple(self):
        assert inspect.isclass(utils.structs.NftPurchase)
        assert utils.structs.NftPurchase.__name__ == "NftPurchase"

    def test_utils_structs_nftpurchase_fields(self):
        assert utils.structs.NftPurchase._fields == (
            "price",
            "group",
            "gallery",
            "time",
            "currency",
        )

    # # NftListing
    def test_utils_structs_defines_nftlisting_tuple(self):
        assert inspect.isclass(utils.structs.NftListing)
        assert utils.structs.NftListing.__name__ == "NftListing"

    def test_utils_structs_nftlisting_fields(self):
        assert utils.structs.NftListing._fields == (
            "asset",
            "price",
            "quantity",
            "gallery",
            "currency",
            "app",
        )

    # # NftFloor
    def test_utils_structs_defines_nftfloor_tuple(self):
        assert inspect.isclass(utils.structs.NftFloor)
        assert utils.structs.NftFloor.__name__ == "NftFloor"

    def test_utils_structs_nftfloor_fields(self):
        assert utils.structs.NftFloor._fields == ("price", "gallery", "currency", "app")

    # # LimitOrder
    def test_utils_structs_defines_limitorder_tuple(self):
        assert inspect.isclass(utils.structs.LimitOrder)
        assert utils.structs.LimitOrder.__name__ == "LimitOrder"

    def test_utils_structs_limitorder_fields(self):
        assert utils.structs.LimitOrder._fields == (
            "amount_in",
            "asset_out",
            "amount_out",
            "price",
            "escrow",
        )

    # # Consolidated
    def test_utils_structs_defines_consolidated_tuple(self):
        assert inspect.isclass(utils.structs.Consolidated)
        assert utils.structs.Consolidated.__name__ == "Consolidated"

    def test_utils_structs_consolidated_fields(self):
        assert utils.structs.Consolidated._fields == (
            "balance",
            "staked",
            "liquidity",
            "defi",
            "nftfloor",
        )

    # # LedgerProgram
    def test_utils_structs_defines_ledgerapp_tuple(self):
        assert inspect.isclass(utils.structs.LedgerProgram)
        assert utils.structs.LedgerProgram.__name__ == "LedgerProgram"

    def test_utils_structs_ledgerapp_fields(self):
        assert utils.structs.LedgerProgram._fields == ("asset", "code", "dapp")
