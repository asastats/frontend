"""Module containing public API constants."""

NFT_SALE_TYPES = [
    ("purchase", "NFTs that have been purchased"),
    ("no-purchase", "NFTs that haven't been purchased"),
    ("listing", "NFTs that are listed"),
    ("no-listing", "NFTs that aren't listed"),
    ("floor", "NFTs that have a floor listing"),
    ("no-floor", "NFTs that don't have a floor listing"),
]

ASA_DEFI_TYPES = [
    "balance",
    "stake",
    "farm",
    "deposit",
    "borrow",
    "withdrawal",
    "liquidity",
    "orders",
    "cdp",
    "governance",
    "vault",
    "fee",
    "reward",
    "lock",
]

# # OpenAPI schema examples (inlined; formerly imported from utils.tests.fixtures)
API_EXAMPLE_ADDRESS1 = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
API_EXAMPLE_ADDRESS2 = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
API_EXAMPLE_ADDRESS3 = "VKENBO5W2DZAZFQR45SOQO6IMWS5UMVZCHLPEACNOII7BDJTGBZKSEL4Y4"
API_EXAMPLE_ADDRESS4 = "MULILZCPNVCE3DZHTIWY4B2SDY2H3U2QN6KWZFFSS6JSFU6FWZFSXO3BBM"
API_EXAMPLE_ADDRESS5 = "MQ2QJHZSZ6A7ZXPFE2EPIWLYUMRRDO3DQBEO6NIQ2B5A5OJ4VMWOOI2AX4"
API_EXAMPLE_BUNDLE1 = "540A5D8CEC896E073F9170AF0A962503E69147CF"
API_EXAMPLE_BUNDLE2 = "EF3DF9D854814A2786C6EEF40AC7FECF124D5151"
API_EXAMPLE_NFD_NAME1 = "asastats.algo"
API_EXAMPLE_NFD_NAME2 = "patrick.algo"
