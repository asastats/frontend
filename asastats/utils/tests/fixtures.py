"""Testing fixtures module for utils package."""

from utils.structs import Asa

TEST_ADDRESS = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
TEST_ADDRESS2 = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
TEST_ADDRESS3 = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
TEST_BUNDLE = "540A5D8CEC896E073F9170AF0A962503E69147CF"
TEST_NEW_BUNDLE = "65B4307A047B8276EEA9F184EE78975A5F47ACA1"

TESTING_VALUES_SMALL = [
    [212.338704, 226701642, 26872283825, {"e": [(212.338704, 26872283825)]}, 0],
    [5.71359, 287867876, 30000000000, {"e": [(5.71359, 30000000000)]}, 0],
    [2.094182, 300208676, 625000000, {"e": [(2.094182, 625000000)]}, 0],
    [1.993307, 137594422, 20000000, {"e": [(1.993307, 20000000)]}, 0],
]

TESTING_ASAS_SMALL = {
    137594422: Asa(
        id=137594422,
        name="HEADLINE",
        unit="HDL",
        total=25000000000000,
        decimals=6,
        url="headline.dev",
        creator="K3NSXYMHPRCK7PMYT3QUQXUGPZJ4MKWJXW2HJRYPVMQUMKJAOJEIEO4HK4",
        links={},
    ),
    226701642: Asa(
        id=226701642,
        name="Yieldly",
        unit="YLDY",
        total=10000000000000000,
        decimals=6,
        url=None,
        creator="Q2JK6TIJB6XDU3X4TNVDWSW4M2RLKLU6O6EWNTHGYREMFIJGXYPHVURNMY",
        links={},
    ),
    287867876: Asa(
        id=287867876,
        name="Opulous",
        unit="OPUL",
        total=5000000000000000000,
        decimals=10,
        url="https://opulous.org/",
        creator="V537CZUKQJH2ETEJRXHAQI6OUHL54MZU5OIBCAU4J6OE3557ODF74WVQCA",
        links={},
    ),
    300208676: Asa(
        id=300208676,
        name="Smile Coin",
        unit="SMILE",
        total=10000000000000000,
        decimals=6,
        url="https://smilecoin.us",
        creator="KAIPTDPRZBJ7BIDQXEO7ICQ2U2R2E5ATKFOBR3PSKYJRC56WHNYHBW4WVE",
        links={},
    ),
}

TESTING_VALUES = [
    [212.338704, 226701642, 26872283825, {"e": [(212.338704, 26872283825)]}, 0],
    [55.292611, 398853048, 355029, {"e": [(55.292611, 355029)]}, 0],
    [5.860591, 361671874, 1000000100, {"e": [(5.860591, 1000000000)]}, 0],
    [5.71359, 287867876, 30000000010, {"e": [(5.71359, 30000000000)]}, 0],
    [5.500924, 241759159, 5140, {"e": [(5.500924, 5140)]}, 0],
    [2.584535, 353409462, 3000000, {"e": [(2.584535, 3000000)]}, 0],
    [2.094182, 300208676, 625000000, {"e": [(2.094182, 625000000)]}, 0],
    [1.993307, 137594422, 20000000, {"e": [(1.993307, 20000000)]}, 0],
    [1.826867, 305992851, 700000, {"e": [(1.826867, 700000)]}, 0],
    [1.127203, 281003863, 1, {"e": [(1.127203, 1)]}, 0],
    [0.957443, 280627218, 66528345, {"e": [(0.957443, 66528345)]}, 0],
    [0.76184, 329110405, 17000, {"e": [(0.76184, 17000)]}, 0],
    [0.274806, 281003266, 34, {"e": [(0.274806, 34)]}, 0],
    [0, 388950186, 2, {}, 0],
    [0, 365265468, 1, {}, 0],
    [0, 359414344, 399107117, {}, 0],
    [0, 354246661, 1, {}, 0],
    [0, 353048393, 1, {}, 0],
    [0, 319473667, 1500000000, {}, 0],
    [0, 317434432, 1, {}, 0],
    [0, 281004528, 1, {}, 0],
]

TESTING_ASAS = {
    163650: Asa(
        id=163650,
        name="Asia Reserve Currency Coin",
        unit="ARCC",
        total=88616203378510000,
        decimals=6,
        url="https://arcc.io",
        creator="",
        links={},
    ),
    312769: Asa(
        id=312769,
        name="Tether USDt",
        unit="USDt",
        total=18446744073709551615,
        decimals=6,
        url="tether.to",
        creator="",
        links={},
    ),
    31566704: Asa(
        id=31566704,
        name="USDC",
        unit="USDC",
        total=18446744073709551615,
        decimals=6,
        url="https://www.centre.io/usdc",
        creator="",
        links={},
    ),
    137594422: Asa(
        id=137594422,
        name="HEADLINE",
        unit="HDL",
        total=25000000000000,
        decimals=6,
        url="headline.dev",
        creator="",
        links={},
    ),
    226701642: Asa(
        id=226701642,
        name="Yieldly",
        unit="YLDY",
        total=10000000000000000,
        decimals=6,
        url=None,
        creator="",
        links={},
    ),
    230946361: Asa(
        id=230946361,
        name="AlgoGems",
        unit="GEMS",
        total=10000000000000,
        decimals=6,
        url="https://www.algogems.io",
        creator="",
        links={},
    ),
    241759159: Asa(
        id=241759159,
        name="Freckle",
        unit="FRKL",
        total=1000000000000000,
        decimals=0,
        url="https://freckle.sbhelper.com",
        creator="",
        links={},
    ),
    242345487: Asa(
        id=242345487,
        name="AB2 Gallery Flag",
        unit="AB2-F",
        total=1000000000000,
        decimals=0,
        url="https://ab2.gallery/",
        creator="",
        links={},
    ),
    264229768: Asa(
        id=264229768,
        name="Peach Fund",
        unit="Peach",
        total=100000000000,
        decimals=2,
        url="peachcapitalpartners.com",
        creator="",
        links={},
    ),
    280627218: Asa(
        id=280627218,
        name="69,420 Coin",
        unit="SWED",
        total=69420000000,
        decimals=6,
        url=None,
        creator="",
        links={},
    ),
    281003266: Asa(
        id=281003266,
        name="NFT Grocery Store Coupon 🎫",
        unit="Coup🎫",
        total=9007199254740991,
        decimals=0,
        url="https://static.wixstatic.com/media/f3a429_1913db8389cf4407bd04fd077c072869~mv2.png",
        creator="",
        links={},
    ),
    281003863: Asa(
        id=281003863,
        name="G^1 Eureka Lemon 🍋",
        unit="Eure🍋",
        total=9007199254740991,
        decimals=0,
        url="https://video.wixstatic.com/video/f3a429_457fb01a10954f40a71dfee71bb49c32/720p/mp4/file.mp4",
        creator="",
        links={},
    ),
    281004528: Asa(
        id=281004528,
        name="G^2 Sweet Watermelon 🍉",
        unit="Swee🍉",
        total=9007199254740991,
        decimals=0,
        url="https://video.wixstatic.com/video/f3a429_80fbe7d7b01d42cdad0bdaa295116257/720p/mp4/file.mp4",
        creator="",
        links={},
    ),
    287867876: Asa(
        id=287867876,
        name="Opulous",
        unit="OPUL",
        total=5000000000000000000,
        decimals=10,
        url="https://opulous.org/",
        creator="",
        links={},
    ),
    300208676: Asa(
        id=300208676,
        name="Smile Coin",
        unit="SMILE",
        total=10000000000000000,
        decimals=6,
        url="https://smilecoin.us",
        creator="",
        links={},
    ),
    305992851: Asa(
        id=305992851,
        name="Algoneer",
        unit="AGNR",
        total=10000000000,
        decimals=3,
        url="https://www.algoneer.net/",
        creator="",
        links={},
    ),
    317434432: Asa(
        id=317434432,
        name="Algofest21",
        unit="fest",
        total=620,
        decimals=0,
        url="https://ipfs.io/ipfs/bafkreibb2jll4vxzkgaoh7nize5qqr5gm5ygju5lrdc665rlhr2ovmyyue",
        creator="",
        links={},
    ),
    319473667: Asa(
        id=319473667,
        name="Curator Coin",
        unit="CURATOR",
        total=100000000000000,
        decimals=5,
        url="https://www.algocurator.com/",
        creator="",
        links={},
    ),
    329110405: Asa(
        id=329110405,
        name="TacoCoin",
        unit="Tacos",
        total=10000000000,
        decimals=0,
        url="Dorastacos.com",
        creator="",
        links={},
    ),
    342889824: Asa(
        id=342889824,
        name="Board",
        unit="BOARD",
        total=10000000000000000,
        decimals=6,
        url="https://boardofficial.com",
        creator="",
        links={},
    ),
    348055340: Asa(
        id=348055340,
        name="The Algonauts # 3200",
        unit="Algonaut",
        total=1,
        decimals=0,
        url="https://ipfs.io/ipfs/bafybeianjja233lg24jo66pnieoxwngibe6wi7yfw4na44sv4eieywadbm",
        creator="",
        links={},
    ),
    353048393: Asa(
        id=353048393,
        name="ALGO Governors ",
        unit="AlGuv",
        total=2500,
        decimals=0,
        url=None,
        creator="",
        links={},
    ),
    353409462: Asa(
        id=353409462,
        name="AlgoBasket",
        unit="ABSKT",
        total=100000000000000,
        decimals=4,
        url="https://AlgoBasket.io",
        creator="",
        links={},
    ),
    354246661: Asa(
        id=354246661,
        name="Algo Governors - Q4 2021",
        unit="AlGvQ421",
        total=100,
        decimals=0,
        url="https://ipfs.io/ipfs/bafybeidu2ofzfts4hl6m3r2fmvdpu7qbvzbvnwp2izzzeewqv4itnmkoti",
        creator="",
        links={},
    ),
    359314135: Asa(
        id=359314135,
        name="TinymanPool1.1 USDC-ALGO",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    359330978: Asa(
        id=359330978,
        name="TinymanPool1.1 USDC-USDt",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    359342000: Asa(
        id=359342000,
        name="TinymanPool1.1 YLDY-ALGO",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    359362289: Asa(
        id=359362289,
        name="TinymanPool1.1 OPUL-ALGO",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    359363782: Asa(
        id=359363782,
        name="TinymanPool1.1 SMILE-ALGO",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    359399600: Asa(
        id=359399600,
        name="TinymanPool1.1 FRKL-ALGO",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    359414344: Asa(
        id=359414344,
        name="TinymanPool1.1 BOARD-ALGO",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    361671874: Asa(
        id=361671874,
        name="KittenCoin",
        unit="KTNC",
        total=100000000000000,
        decimals=5,
        url="https://robertmm25.wixsite.com/website",
        creator="",
        links={},
    ),
    365265468: Asa(
        id=365265468,
        name="Algonautz 031 - Voidnautz",
        unit="AZ031",
        total=3,
        decimals=0,
        url="https://ipfs.io/ipfs/QmafQ7JQXdWP24L48ePztNEXTz4PvqripRHmtgmSUxDXmy",
        creator="",
        links={},
    ),
    366684238: Asa(
        id=366684238,
        name="TinymanPool1.1 SWED-ALGO",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    368451457: Asa(
        id=368451457,
        name="TinymanPool1.1 7-ALGO",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    380130784: Asa(
        id=380130784,
        name="TinymanPool1.1 ABSKT-ALGO",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    384303832: Asa(
        id=384303832,
        name="AKITA INU TOKEN",
        unit="AKITA",
        total=1000000000,
        decimals=0,
        url=None,
        creator="",
        links={},
    ),
    384305346: Asa(
        id=384305346,
        name="TinymanPool1.1 AKITA-ALGO",
        unit="TM1POOL",
        total=18446744073709551615,
        decimals=6,
        url="https://tinyman.org",
        creator="",
        links={},
    ),
    388950186: Asa(
        id=388950186,
        name="Official AKITA NFT",
        unit="AKITAnft",
        total=10000,
        decimals=0,
        url="https://bit.ly/AKITAnft",
        creator="",
        links={},
    ),
    398853048: Asa(
        id=398853048,
        name="IQ INU",
        unit="IQ",
        total=1000000000,
        decimals=0,
        url=None,
        creator="",
        links={},
    ),
}

TESTING_NFD_LOCAL_STATES = {
    764587869: [
        {
            "id": 760937186,
            "key-value": [
                {
                    "key": "aS5hcHBpZA==",
                    "value": {"bytes": "AAAAAC2Sr10=", "type": 1, "uint": 0},
                },
                {
                    "key": "aS5hc2FpZA==",
                    "value": {"bytes": "AAAAAC2Sr2M=", "type": 1, "uint": 0},
                },
            ],
            "schema": {"num-byte-slice": 16, "num-uint": 0},
        }
    ],
    765925390: [
        {
            "id": 760937186,
            "key-value": [
                {
                    "key": "aS5hcHBpZA==",
                    "value": {"bytes": "AAAAAC2nGA4=", "type": 1, "uint": 0},
                },
                {
                    "key": "aS5hc2FpZA==",
                    "value": {"bytes": "AAAAAC2nGBQ=", "type": 1, "uint": 0},
                },
            ],
            "schema": {"num-byte-slice": 16, "num-uint": 0},
        }
    ],
    764602782: [
        {
            "id": 760937186,
            "key-value": [
                {
                    "key": "aS5hcHBpZA==",
                    "value": {"bytes": "AAAAAC2S6Z4=", "type": 1, "uint": 0},
                },
                {
                    "key": "aS5hc2FpZA==",
                    "value": {"bytes": "AAAAAC2S6aQ=", "type": 1, "uint": 0},
                },
            ],
            "schema": {"num-byte-slice": 16, "num-uint": 0},
        }
    ],
}

TESTING_NFD_NAME_BYTECODES = {
    "asastats.algo": (
        b"\x05 \x01\x01\x80\x08\x00\x00\x00\x00-Z"
        b"\xfa\xe2\x175\x001\x184\x00\x121\x10\x81\x06"
        b'\x12\x101\x19"\x121\x19\x81\x00\x12\x11\x10'
        b'@\x00\x01\x00"C&\x01\x12name/asastats.algo'
    ),
    "name.algo": (
        b"\x05 \x01\x01\x80\x08\x00\x00\x00\x00-Z"
        b"\xfa\xe2\x175\x001\x184\x00\x121\x10\x81\x06"
        b'\x12\x101\x19"\x121\x19\x81\x00\x12\x11\x10'
        b'@\x00\x01\x00"C&\x01\x0ename/name.algo'
    ),
    "my.algo": (
        b"\x05 \x01\x01\x80\x08\x00\x00\x00\x00-Z"
        b"\xfa\xe2\x175\x001\x184\x00\x121\x10\x81\x06"
        b'\x12\x101\x19"\x121\x19\x81\x00\x12\x11\x10'
        b'@\x00\x01\x00"C&\x01\x0cname/my.algo'
    ),
}

TESTING_NFD_ADDRESS = "Z5JLKUAEOTQ6B42VB4IM25KPAUTNA3V5SMQWZSCT3LTMC75AC5RTITB77A"
TESTING_NFD_ADDRESS_STATE = [
    {
        "key": "aS5hc2FpZA==",
        "value": {"bytes": "AAAAAC2Sr2M=", "type": 1, "uint": 0},
    },
    {
        "key": "aS5jYXRlZ29yeQ==",
        "value": {"bytes": "Y29tbW9u", "type": 1, "uint": 0},
    },
    {
        "key": "aS50aW1lQ2hhbmdlZA==",
        "value": {"bytes": "AAAAAGKaT1k=", "type": 1, "uint": 0},
    },
    {
        "key": "aS5jb21taXNzaW9uMkFnZW50LmE=",
        "value": {
            "bytes": "jKusCPcH2WMWd92wj86mBLtu3P1n8wrd74w+Ns22350=",
            "type": 1,
            "uint": 0,
        },
    },
    {
        "key": "aS5jb21taXNzaW9uMg==",
        "value": {"bytes": "AAAAAAAAADI=", "type": 1, "uint": 0},
    },
    {
        "key": "aS5uYW1l",
        "value": {"bytes": "YXNhc3RhdHMuYWxnbw==", "type": 1, "uint": 0},
    },
    {
        "key": "aS5jb250cmFjdExvY2tlZA==",
        "value": {"bytes": "MA==", "type": 1, "uint": 0},
    },
    {"key": "aS5taW50aW5n", "value": {"bytes": "Mg==", "type": 1, "uint": 0}},
    {
        "key": "aS5jb21taXNzaW9uMUFnZW50LmE=",
        "value": {
            "bytes": "EBE87MxYL4wTnQVFyJFQOames+plchQ1QZ5lARDMD+4=",
            "type": 1,
            "uint": 0,
        },
    },
    {
        "key": "aS5vd25lci5h",
        "value": {
            "bytes": "z1K1UAR04eDzVQ8QzXVPBSbQbr2TIWzIU9rmwX+gF2M=",
            "type": 1,
            "uint": 0,
        },
    },
    {
        "key": "aS5jb21taXNzaW9uMQ==",
        "value": {"bytes": "AAAAAAAAADI=", "type": 1, "uint": 0},
    },
    {
        "key": "aS5zYWxlVHlwZQ==",
        "value": {"bytes": "YnV5SXROb3c=", "type": 1, "uint": 0},
    },
    {
        "key": "aS5zZWxsYW10",
        "value": {"bytes": "AAAAAAWDcCA=", "type": 1, "uint": 0},
    },
    {"key": "aS52ZXI=", "value": {"bytes": "MS4wOA==", "type": 1, "uint": 0}},
    {
        "key": "aS5yZXNlcnZlZE93bmVyLmE=",
        "value": {
            "bytes": "qojQu7bQ8gyWEedk6DvIZaXaMrkR1vIATXIR8I0zMHI=",
            "type": 1,
            "uint": 0,
        },
    },
    {
        "key": "aS5zZWxsZXIuYQ==",
        "value": {
            "bytes": "jKusCPcH2WMWd92wj86mBLtu3P1n8wrd74w+Ns22350=",
            "type": 1,
            "uint": 0,
        },
    },
    {
        "key": "aS50aW1lQ3JlYXRlZA==",
        "value": {"bytes": "AAAAAGKaT1k=", "type": 1, "uint": 0},
    },
]
TESTING_NFD_ADDRESS_STATE_MULTIPLE = [
    {
        "key": "aS5hc2FpZA==",
        "value": {"bytes": "AAAAAC2Sr2M=", "type": 1, "uint": 0},
    },
    {
        "key": "aS5vd25lci5h",
        "value": {
            "bytes": "z1K1UAR04eDzVQ8QzXVPBSbQbr2TIWzIU9rmwX+gF2M=",
            "type": 1,
            "uint": 0,
        },
    },
    {
        "key": "di5jYUFsZ28uMC5hcw==",
        "value": {
            "bytes": "z1K1UAR04eDzVQ8QzXVPBSbQbr2TIWzIU9rmwX+gF2PRKmzwJnSXtPuUwMmg0NNsw5zlaO8rSEG5yvAhuGvG96271WdtLww3WR9D7LNkZbNvZUoj68k4rGAOa07d6opT",
            "type": 1,
            "uint": 0,
        },
    },
    {
        "key": "aS5jb21taXNzaW9uMQ==",
        "value": {"bytes": "AAAAAAAAADI=", "type": 1, "uint": 0},
    },
]

TEST_BANNERS = [
    {"image": "img/1.jpg", "weight": 4},
    {"image": "img/2.jpg", "weight": 2},
    {"image": "img/3.jpg", "weight": 1},
]
