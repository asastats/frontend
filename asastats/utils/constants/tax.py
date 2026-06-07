"""Module containing tax CSV files creation constants."""

TAX_FORM_PROVIDERS = [
    ("koinly", "Koinly"),
    ("cryptocom", "Crypto.com"),
    ("cointracker", "CoinTracker"),
    ("cointracking", "CoinTracking"),
]
TAX_FORM_USE_MVE_HELP_TEXT = (
    "Select to calculate fiat values concerning available asset AMM liquidity "
    "at that time or leave it unselected for applying asset price per unit only"
)
TAX_FORM_NON_ZERO_HELP_TEXT = (
    "Select to add an additional CSV file to archive "
    "with only non-zero entries (in USD)"
)

TAX_DURATION_MESSAGE = (
    "The procedure entails retrieving every address transaction and handling it "
    "through our engine. The first request for an address will last the longest as "
    "all the related transactions are fetched from the blockchain. In contrast, the "
    "subsequent requests use cached data and the actual process consists only of the "
    "actual evaluation in the engine. (*)\n"
    "The entire procedure could take a few minutes to many hours, depending on whether "
    "it is the first request for an address, the volume of address transactions, and "
    "the number of addresses in our engine's queue.\n"
    "As soon as your report is ready, you will receive an alert on the ASA Stats "
    "website.\n"
    "(*) All the ASA Stats Governors' addresses and a few hundred other addresses "
    "are prefetched and tested during the development.\n"
)
