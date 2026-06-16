"""Module containing api app's serializers."""

from algosdk.constants import ADDRESS_LEN
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    DecimalField,
    IntegerField,
    ListField,
    Serializer,
    StringRelatedField,
    URLField,
)

from api.data import (
    API_EXAMPLE_ADDRESS1,
    API_EXAMPLE_ADDRESS2,
    API_EXAMPLE_ADDRESS3,
    API_EXAMPLE_BUNDLE1,
    API_EXAMPLE_NFD_NAME1,
    API_EXAMPLE_NFD_NAME2,
    NFT_SALE_TYPES,
)


# # INPUT
@extend_schema_serializer(
    component_name="AddressesInput",
    examples=[
        OpenApiExample("Single address", value={"addresses": API_EXAMPLE_ADDRESS1}),
        OpenApiExample(
            "Addresses",
            value={"addresses": f"{API_EXAMPLE_ADDRESS1};{API_EXAMPLE_ADDRESS2}"},
        ),
        OpenApiExample(
            "NFD name",
            value={"addresses": f"{API_EXAMPLE_NFD_NAME1}"},
        ),
        OpenApiExample(
            "Addresses and names",
            value={
                "addresses": (
                    f"{API_EXAMPLE_ADDRESS1} {API_EXAMPLE_NFD_NAME1} "
                    f"{API_EXAMPLE_ADDRESS2}"
                )
            },
        ),
        OpenApiExample(
            "NFD names",
            value={"addresses": f"{API_EXAMPLE_NFD_NAME1},{API_EXAMPLE_NFD_NAME2}"},
        ),
    ],
)
class BundleHashFromAddressesSerializer(Serializer):
    """Serialize collection of addresses and .algo names.

    :var BundleRetrieveSerializer.addresses: collection of public Algorand addresses
    :type BundleRetrieveSerializer.addresses: :class:`CharField`
    """

    addresses = CharField()


@extend_schema_serializer(
    component_name="Bundle",
    examples=[
        OpenApiExample("Regular bundle", value={"bundle": API_EXAMPLE_BUNDLE1}),
        OpenApiExample("From address", value={"bundle": API_EXAMPLE_ADDRESS1}),
        OpenApiExample("From NFD name", value={"bundle": API_EXAMPLE_ADDRESS3}),
    ],
)
class BundleHashSerializer(Serializer):
    """Serialize bundle hash.

    :var BundleRetrieveSerializer.bundle: unique hash for public Algorand addresses
    :type BundleRetrieveSerializer.bundle: :class:`CharField`
    """

    bundle = CharField(min_length=40, max_length=40)


@extend_schema_serializer(component_name="NfdName")
class NfdNameSerializer(Serializer):
    """Serialize .algo name.

    :var NfdNameSerializer.nfd_name: NFD .algo name
    :type NfdNameSerializer.nfd_name: :class:`CharField`
    """

    nfd_name = CharField(max_length=ADDRESS_LEN)


@extend_schema_serializer(component_name="NftSaleType")
class NftSaleTypeQuerySerializer(Serializer):
    type = ChoiceField(required=False, choices=NFT_SALE_TYPES)


# # PROVIDERS
@extend_schema_serializer(component_name="Provider")
class ProviderSerializer(Serializer):
    """Serialize dApp provider.

    :var ProviderSerializer.name: provider's unique name
    :type ProviderSerializer.name: :class:`CharField`
    :var ProviderSerializer.info: provider's information
    :type ProviderSerializer.info: :class:`CharField`
    """

    name = CharField(max_length=20)
    info = CharField(max_length=100)

    def to_representation(self, instance):
        """Return collection of non-empty field-value pairs.

        :param instance: provider's serializer instance
        :type instance: :class:`ProviderSerializer`
        :var result: provider  serializer's field name and value pairs
        :type result: dict
        :return: dict
        """
        result = super().to_representation(instance)
        return {key: value for key, value in result.items() if value is not None}


# # ASA
@extend_schema_serializer(component_name="AsaProgram")
class AsaProgramSerializer(Serializer):
    """Serialize dApp program object.

    :var AsaProgramSerializer.type: program's type
    :type AsaProgramSerializer.type: :class:`CharField`
    :var AsaProgramSerializer.name: program's name
    :type AsaProgramSerializer.name: :class:`CharField`
    :var AsaProgramSerializer.provider: program's provider
    :type AsaProgramSerializer.provider: :class:`ProviderSerializer`
    :var AsaProgramSerializer.url: program's URL
    :type AsaProgramSerializer.url: :class:`URLField`
    :var AsaProgramSerializer.code: unique program's code
    :type AsaProgramSerializer.code: :class:`CharField`
    """

    type = CharField(max_length=20)
    name = CharField(max_length=30)
    provider = ProviderSerializer()
    url = URLField()
    code = CharField(max_length=5)

    def to_representation(self, instance):
        """Return collection of non-empty field-value pairs.

        :param instance: ASA program's serializer instance
        :type instance: :class:`AsaProgramSerializer`
        :var result: ASA program  serializer's field name and value pairs
        :type result: dict
        :return: dict
        """
        result = super().to_representation(instance)
        return {key: value for key, value in result.items() if value is not None}


@extend_schema_serializer(component_name="UserAsaProgramDistributionLink")
class DistributionLinkSerializer(Serializer):
    """Serialize dApp program distribution link object.

    :var DistributionLinkSerializer.provider: program distribution's provider
    :type DistributionLinkSerializer.provider: :class:`ProviderSerializer`
    :var DistributionLinkSerializer.text: program distribution's link text
    :type DistributionLinkSerializer.text: :class:`CharField`
    :var DistributionLinkSerializer.url: program distribution's URL
    :type DistributionLinkSerializer.url: :class:`URLField`
    """

    provider = ProviderSerializer()
    text = CharField(max_length=30)
    url = URLField()


@extend_schema_serializer(component_name="UserAsaProgramDistribution")
class DistributionSerializer(Serializer):
    """Serialize asset dApp program distribution object.

    :var DistributionSerializer.value: asset's value in ALGO
    :type DistributionSerializer.value: :class:`DecimalField`
    :var DistributionSerializer.amount: asset's amount
    :type DistributionSerializer.amount: :class:`IntegerField`
    :var DistributionSerializer.links: program distribution link serializer
    :type DistributionSerializer.links: :class:`DistributionLinkSerializer`
    """

    value = DecimalField(max_digits=20, decimal_places=6)
    amount = IntegerField()
    link = DistributionLinkSerializer()


@extend_schema_serializer(component_name="LinkedData")
class LinkedDataSerializer(Serializer):
    """Serialize data linked to ASA program item.

    :var LinkedDataSerializer.provider: linked data's provider serializer
    :type LinkedDataSerializer.provider: :class:`ProviderSerializer`
    :var LinkedDataSerializer.text: linked data accompanied text
    :type LinkedDataSerializer.text: str
    :var LinkedDataSerializer.link: link to provider's website
    :type LinkedDataSerializer.link: :class:`URLField`
    :var LinkedDataSerializer.value: asset's value in ALGO
    :type LinkedDataSerializer.value: :class:`DecimalField`
    :var LinkedDataSerializer.amount: asset's amount
    :type LinkedDataSerializer.amount: :class:`IntegerField`
    :var LinkedDataSerializer.balance: asset's balance
    :type LinkedDataSerializer.balance: :class:`IntegerField`
    :var LinkedDataSerializer.info: addintional information for linked data
    :type LinkedDataSerializer.info: str
    :var LinkedDataSerializer.id: unique identifier for linked data
    :type LinkedDataSerializer.id: str
    """

    provider = ProviderSerializer()
    text = CharField()
    link = URLField()
    value = DecimalField(max_digits=20, decimal_places=6)
    amount = IntegerField()
    balance = IntegerField()
    info = CharField()
    id = IntegerField()

    def to_representation(self, instance):
        """Return collection of non-empty field-value pairs.

        :param instance: linked data's serializer instance
        :type instance: :class:`LinkedDataSerializer`
        :var result: linked data serializer's field name and value pairs
        :type result: dict
        :return: dict
        """
        result = super().to_representation(instance)
        return {key: value for key, value in result.items() if value is not None}


@extend_schema_serializer(component_name="UserAsaProgram")
class AsaItemProgramSerializer(Serializer):
    """Serialize asset dApp program object.

    :var AsaItemProgramSerializer.program: program's serializer
    :type AsaItemProgramSerializer.program: :class:`ProgramSerializer`
    :var AsaItemProgramSerializer.value: asset's value in ALGO
    :type AsaItemProgramSerializer.value: :class:`DecimalField`
    :var AsaItemProgramSerializer.amount: asset's amount
    :type AsaItemProgramSerializer.amount: :class:`IntegerField`
    :var AsaItemProgramSerializer.proxy: placeholder
    :type AsaItemProgramSerializer.proxy: :class:`StringRelatedField`
    :var AsaItemProgramSerializer.distribution: user's program distribution serializer
    :type AsaItemProgramSerializer.distribution: :class:`DistributionSerializer`
    :var AsaItemProgramSerializer.linked: serilazer of data linked to ASA item program
    :type AsaItemProgramSerializer.linked: :class:`LinkedDataSerializer`
    """

    program = AsaProgramSerializer()
    value = DecimalField(max_digits=20, decimal_places=6)
    amount = IntegerField()
    proxy = StringRelatedField(many=True)
    distribution = DistributionSerializer(many=True)
    linked = LinkedDataSerializer(many=True)

    def to_representation(self, instance):
        """Return collection of non-empty field-value pairs.

        :param instance: ASA item program's serializer instance
        :type instance: :class:`AsaItemProgramSerializer`
        :var result: ASA item program serializer's field name and value pairs
        :type result: dict
        :return: dict
        """
        result = super().to_representation(instance)
        return {key: value for key, value in result.items() if value is not None}


@extend_schema_serializer(component_name="OffchainLink")
class AsaLinkSerializer(Serializer):
    """Serialize dApp program object.

    :var AsaLinkSerializer.provider: link's provider serializer
    :type AsaLinkSerializer.provider: :class:`ProviderSerializer`
    :var AsaLinkSerializer.link: link to ASA page on provider's website
    :type AsaLinkSerializer.link: :class:`URLField`
    :var AsaLinkSerializer.title: link's description
    :type AsaLinkSerializer.title: :class:`URLField`
    """

    provider = ProviderSerializer()
    link = URLField()
    title = CharField(max_length=32)


@extend_schema_serializer(component_name="Asa")
class AsaSerializer(Serializer):
    """Serialize ASA object.

    :var AsaSerializer.id: asset's unique identifier
    :type AsaSerializer.id: :class:`IntegerField`
    :var AsaSerializer.name: asset's name
    :type AsaSerializer.name: :class:`CharField`
    :var AsaSerializer.unit: asset's unit name
    :type AsaSerializer.unit: :class:`CharField`
    :var AsaSerializer.total: asset's total supply
    :type AsaSerializer.total: :class:`IntegerField`
    :var AsaSerializer.decimals: asset's number of digits after decimal point
    :type AsaSerializer.decimals: :class:`IntegerField`
    :var AsaSerializer.url: asset's URL field
    :type AsaSerializer.url: :class:`CharField`
    :var AsaSerializer.links: asset's offchain links
    :type AsaSerializer.links: :class:`AsaLinkSerializer`
    """

    id = IntegerField()
    name = CharField(max_length=32)
    unit = CharField(max_length=8)
    total = IntegerField()
    decimals = IntegerField()
    url = CharField(max_length=96)
    links = AsaLinkSerializer(many=True)


@extend_schema_serializer(component_name="AsaItem")
class AsaItemSerializer(Serializer):
    """Serialize account's ASA item.

    :var AsaItemSerializer.value: asset's total value in ALGO
    :type AsaItemSerializer.value: :class:`DecimalField`
    :var AsaItemSerializer.asset: asset's serializer
    :type AsaItemSerializer.asset: :class:`AsaSerializer`
    :var AsaItemSerializer.amount: asset's total amount
    :type AsaItemSerializer.amount: :class:`IntegerField`
    :var AsaItemSerializer.price: ASA's price in ALGO
    :type AsaItemSerializer.price: :class:`DecimalField`
    :var AsaItemSerializer.programs: collection of asset's program serializers
    :type AsaItemSerializer.programs: :class:`AsaItemProgramSerializer`
    """

    value = DecimalField(max_digits=20, decimal_places=6)
    asset = AsaSerializer()
    amount = IntegerField()
    price = DecimalField(max_digits=20, decimal_places=6)
    programs = AsaItemProgramSerializer(many=True)


# # NFT
@extend_schema_serializer(component_name="NftCurrency")
class NftCurrencySerializer(Serializer):
    """Serialize NFT currency object.

    :var NftCurrencySerializer.amount: currency's amount
    :type NftCurrencySerializer.amount: :class:`IntegerField`
    :var NftCurrencySerializer.asset: asset's serializer
    :type NftCurrencySerializer.asset: :class:`AsaSerializer`
    """

    amount = IntegerField()
    asset = AsaSerializer()


@extend_schema_serializer(component_name="NftListing")
class NftListingSerializer(Serializer):
    """Serialize NFT listing object.

    :var NftListingSerializer.price: NFT's listed price in ALGO
    :type NftListingSerializer.price: :class:`DecimalField`
    :var NftListingSerializer.market: NFT market provider's serializer
    :type NftListingSerializer.market: :class:`ProviderSerializer`
    :var NftListingSerializer.link: link to listed NFT's page on NFT market website
    :type NftListingSerializer.link: :class:`URLField`
    :var NftListingSerializer.currency: NFT listing's currency object
    :type NftListingSerializer.currency: :class:`NftCurrencySerializer`
    """

    price = DecimalField(max_digits=20, decimal_places=6)
    market = ProviderSerializer()
    link = URLField()
    currency = NftCurrencySerializer()


@extend_schema_serializer(component_name="NftPurchase")
class NftPurchaseSerializer(Serializer):
    """Serialize NFT purchase object.

    :var NftPurchaseSerializer.price: NFT's listed price in ALGO
    :type NftPurchaseSerializer.price: :class:`DecimalField`
    :var NftPurchaseSerializer.market: NFT market provider's serializer
    :type NftPurchaseSerializer.market: :class:`ProviderSerializer`
    :var NftPurchaseSerializer.link: link to transaction's page in blockchain explorer
    :type NftPurchaseSerializer.link: :class:`URLField`
    :var NftPurchaseSerializer.epoch: seconds since epoch when purchase happened
    :type NftPurchaseSerializer.epoch: :class:`IntegerField`
    :var NftPurchaseSerializer.currency: NFT purchase's currency object
    :type NftPurchaseSerializer.currency: :class:`NftCurrencySerializer`
    """

    price = DecimalField(max_digits=20, decimal_places=6)
    market = ProviderSerializer()
    link = URLField()
    epoch = IntegerField()
    currency = NftCurrencySerializer()


@extend_schema_serializer(component_name="NftTrait")
class NftTraitSerializer(Serializer):
    """Serialize NFT trait object.

    :var NftTraitSerializer.name: NFT trait name
    :type NftTraitSerializer.name: :class:`CharField`
    :var NftTraitSerializer.value: NFT trait value
    :type NftTraitSerializer.value: :class:`CharField`
    """

    name = CharField(max_length=40)
    value = CharField(max_length=40)


@extend_schema_serializer(component_name="NftUrl")
class NftUrlSerializer(Serializer):
    """Serialize NFT URL object.

    :var NftUrlSerializer.typ: NFT URL type
    :type NftUrlSerializer.typ: :class:`CharField`
    :var NftUrlSerializer.url: URL value
    :type NftUrlSerializer.url: :class:`URLField`
    """

    typ = CharField(max_length=32)
    url = URLField()


@extend_schema_serializer(component_name="Nft")
class NftSerializer(Serializer):
    """Serialize NFT object.

    :var NftSerializer.id: unique NFT identifier
    :type NftSerializer.id: :class:`IntegerField`
    :var NftSerializer.name: NFT's name
    :type NftSerializer.name: :class:`CharField`
    :var NftSerializer.unit: NFT's unit name
    :type NftSerializer.unit: :class:`CharField`
    :var NftSerializer.total: NFT's total supply
    :type NftSerializer.total: :class:`IntegerField`
    :var NftSerializer.decimals: NFT's number of digits after decimal point
    :type NftSerializer.decimals: :class:`IntegerField`
    :var NftSerializer.creator: NFT's creator address
    :type NftSerializer.creator: :class:`CharField`
    :var NftSerializer.image: relative path to NFT's image representation
    :type NftSerializer.image: :class:`CharField`
    :var NftSerializer.thumbnail: relative path to NFT's thumbnail
    :type NftSerializer.thumbnail: :class:`CharField`
    :var NftSerializer.urls: NFTs URL serializers
    :type NftSerializer.urls: :class:`NftUrlSerializer`
    :var NftSerializer.listings: NFT's listing serializer
    :type NftSerializer.listings: :class:`NftListingSerializer`
    :var NftSerializer.last_purchase: NFT's last purchase serializer
    :type NftSerializer.last_purchase: :class:`NftPurchaseSerializer`
    :var NftSerializer.max_purchase: NFT's maximum purchase serializer
    :type NftSerializer.max_purchase: :class:`NftPurchaseSerializer`
    :var NftSerializer.title: NFT's title metadata
    :type NftSerializer.title: :class:`CharField`
    :var NftSerializer.description: NFT's description attribute
    :type NftSerializer.description: :class:`CharField`
    :var NftSerializer.rarity: NFT's rarity attribute
    :type NftSerializer.rarity: :class:`CharField`
    :var NftSerializer.traits: NFT's traits serializers
    :type NftSerializer.traits: :class:`NftTraitSerializer`
    """

    id = IntegerField()
    name = CharField(max_length=32)
    unit = CharField(max_length=8)
    total = IntegerField()
    decimals = IntegerField()
    creator = CharField(max_length=32)
    image = CharField(max_length=40)
    thumbnail = CharField(max_length=40)
    urls = NftUrlSerializer(many=True)
    listings = NftListingSerializer(many=True)
    floor = NftListingSerializer(many=True)  # TODO: will be removed from here
    last_purchase = NftPurchaseSerializer()
    max_purchase = NftPurchaseSerializer()
    title = CharField(max_length=30)
    description = CharField(max_length=200)
    rarity = CharField(max_length=30)
    traits = NftTraitSerializer(many=True)

    def to_representation(self, instance):
        """Return collection of non-empty field-value pairs.

        :param instance: ASA item program's serializer instance
        :type instance: :class:`AsaItemProgramSerializer`
        :var result: ASA item program serializer's field name and value pairs
        :type result: dict
        :return: dict
        """
        result = super().to_representation(instance)
        return {
            key: value
            for key, value in result.items()
            if value is not None or key == "unit"
        }


@extend_schema_serializer(component_name="NftItem")
class NftItemSerializer(Serializer):
    """Serialize user's NFT item object.

    :var NftItemSerializer.value: NFT's value in ALGO
    :type NftItemSerializer.value: :class:`DecimalField`
    :var NftItemSerializer.nft: NFT serializer
    :type NftItemSerializer.nft: :class:`NftSerializer`
    :var NftItemSerializer.amount: NFT's amount
    :type NftItemSerializer.amount: :class:`IntegerField`
    :var NftItemSerializer.price: NFT's price in ALGO
    :type NftItemSerializer.price: :class:`DecimalField`
    """

    value = DecimalField(max_digits=20, decimal_places=6)
    nft = NftSerializer()
    amount = IntegerField()
    price = DecimalField(max_digits=20, decimal_places=6)


@extend_schema_serializer(component_name="NftCollection")
class NftCollectionSerializer(Serializer):
    """Serialize NFT object.

    :var NftCollectionSerializer.value: NFT collection's value in ALGO
    :type NftCollectionSerializer.value: :class:`DecimalField`
    :var NftCollectionSerializer.name: NFT's collection name
    :type NftCollectionSerializer.name: :class:`CharField`
    :var NftCollectionSerializer.amount: total number of NFTs in collection
    :type NftCollectionSerializer.amount: :class:`IntegerField`
    :var NftCollectionSerializer.nfts: collection's NFT item serializers
    :type NftCollectionSerializer.nfts: :class:`NftItemSerializer`
    :var NftCollectionSerializer.floor: collection's minimum price listing
    :type NftCollectionSerializer.floor: :class:`NftListingSerializer`
    """

    value = DecimalField(max_digits=20, decimal_places=6)
    name = CharField(max_length=100)
    amount = IntegerField()
    nfts = NftItemSerializer(many=True)
    # floor = NftListingSerializer()  # TODO: will be moved here


# # ACCOUNT
@extend_schema_serializer(component_name="EntitiesSerializer")
class EntitiesSerializer(Serializer):
    """Serialize account's programs, providers, and markets.

    :var EntitiesSerializer.programs: account's dApp programs
    :type EntitiesSerializer.programs: :class:`AsaProgramSerializer`
    :var EntitiesSerializer.providers: account's dApp providers
    :type EntitiesSerializer.providers: :class:`ProviderSerializer`
    :var EntitiesSerializer.markets: account's NFT markets
    :type EntitiesSerializer.markets: :class:`ProviderSerializer`
    """

    programs = AsaProgramSerializer(many=True)
    providers = ProviderSerializer(many=True)
    markets = ProviderSerializer(many=True)


@extend_schema_serializer(component_name="NotEvaluatedItem")
class NotevalItemSerializer(Serializer):
    """Serialize not-evaluated asset object.

    :var NotevalItemSerializer.asset: asset's serializer
    :type NotevalItemSerializer.asset: :class:`AsaSerializer`
    :var NotevalItemSerializer.amount: asset's amount
    :type NotevalItemSerializer.amount: :class:`IntegerField`
    :var NotevalItemSerializer.programs: collection of asset's program serializers
    :type NotevalItemSerializer.programs: :class:`AsaItemProgramSerializer`
    """

    asset = AsaSerializer()
    amount = IntegerField()
    programs = AsaItemProgramSerializer(many=True)


@extend_schema_serializer(component_name="Total")
class TotalSerializer(Serializer):
    """Serialize total object.

    :var TotalSerializer.algo: total ALGO amount
    :type TotalSerializer.algo: :class:`DecimalField`
    :var TotalSerializer.asa: total value of ASAs in ALGO
    :type TotalSerializer.asa: :class:`DecimalField`
    :var TotalSerializer.nft: total value of NFTs in ALGO
    :type TotalSerializer.nft: :class:`DecimalField`
    :var TotalSerializer.total: total account value in ALGO
    :type TotalSerializer.total: :class:`DecimalField`
    :var TotalSerializer.totalusdc: total account value in USDC
    :type TotalSerializer.totalusdc: :class:`DecimalField`
    :var TotalSerializer.priceusdc: current ALGO price in USDC
    :type TotalSerializer.priceusdc: :class:`DecimalField`
    :var TotalSerializer.pricealgo: current USDC price in ALGO
    :type TotalSerializer.pricealgo: :class:`DecimalField`
    :var TotalSerializer.noteval: total number of not evaluated assets
    :type TotalSerializer.noteval: :class:`IntegerField`
    :var TotalSerializer.totalwonft: account's total value without NFTs in ALGO
    :type TotalSerializer.totalwonft: :class:`DecimalField`
    :var TotalSerializer.totalwonftusdc: account's total value without NFTs in USDC
    :type TotalSerializer.totalwonftusdc: :class:`DecimalField`
    """

    algo = DecimalField(max_digits=20, decimal_places=6)
    asa = DecimalField(max_digits=20, decimal_places=6)
    nft = DecimalField(max_digits=20, decimal_places=6)
    total = DecimalField(max_digits=20, decimal_places=6)
    totalusdc = DecimalField(max_digits=20, decimal_places=6)
    priceusdc = DecimalField(max_digits=20, decimal_places=6)
    pricealgo = DecimalField(max_digits=20, decimal_places=6)
    noteval = IntegerField()
    totalwonft = DecimalField(max_digits=20, decimal_places=6)
    totalwonftusdc = DecimalField(max_digits=20, decimal_places=6)


@extend_schema_serializer(component_name="AccountInfo")
class AccountInfoSerializer(Serializer):
    """Serialize account information object.

    :var AccountInfoSerializer.addresses: collection of public addresses
    :type AccountInfoSerializer.addresses: :class:`CharField`
    :var AccountInfoSerializer.bundle: unique hash for public Algorand addresses
    :type AccountInfoSerializer.bundle: :class:`CharField`
    :var AccountInfoSerializer.values_in: currency of all serialized values fields
    :type AccountInfoSerializer.values_in: :class:`ChoiceField`
    :var AccountInfoSerializer.online: does any address participate in consensus
    :type AccountInfoSerializer.online: :class:`BooleanField`
    :var AccountInfoSerializer.points: total number of Algoland points
    :type AccountInfoSerializer.points: :class:`IntegerField`
    """

    addresses = ListField(
        child=CharField(min_length=ADDRESS_LEN, max_length=ADDRESS_LEN)
    )
    bundle = CharField(min_length=40, max_length=40)
    values_in = ChoiceField(choices=["ALGO", "USD"])
    online = BooleanField()
    points = IntegerField()


@extend_schema_serializer(component_name="SystemInfo")
class SystemInfoSerializer(Serializer):
    """Serialize system information object.

    :var SystemInfoSerializer.warning: system's warning message
    :type SystemInfoSerializer.warning: :class:`DecimalField`
    :var SystemInfoSerializer.information: system's information message
    :type SystemInfoSerializer.information: :class:`DecimalField`
    """

    warning = CharField(max_length=50)
    information = CharField(max_length=50)

    def to_representation(self, instance):
        """Return collection of non-empty field-value pairs.

        :param instance: system information's serializer instance
        :type instance: :class:`SystemInfoSerializer`
        :var result: system information serializer's field name and value pairs
        :type result: dict
        :return: dict
        """
        result = super().to_representation(instance)
        return {key: value for key, value in result.items() if value is not None}


@extend_schema_serializer(component_name="EvaluatedAccount")
class EvaluatedAccountSerializer(Serializer):
    """Serialize evaluated account.

    :var EvaluatedAccountSerializer.account_info: extra account data serializer
    :type EvaluatedAccountSerializer.account_info: :class:`AccountInfoSerializer`
    :var EvaluatedAccountSerializer.system_info: system info object serializer
    :type EvaluatedAccountSerializer.system_info: :class:`SystemInfoSerializer`
    :var EvaluatedAccountSerializer.total: total values and prices serializer
    :type EvaluatedAccountSerializer.total: :class:`TotalSerializer`
    :var EvaluatedAccountSerializer.asaitems: collection of ASA item serializers
    :type EvaluatedAccountSerializer.asaitems: :class:`AsaItemSerializer`
    :var EvaluatedAccountSerializer.nfts: NFT collection serializers
    :type EvaluatedAccountSerializer.nfts: :class:`NftCollectionSerializer`
    :var EvaluatedAccountSerializer.notevals: collection of Noteval serializers
    :type EvaluatedAccountSerializer.notevals: :class:`NotevalItemSerializer`
    """

    account_info = AccountInfoSerializer()
    system_info = SystemInfoSerializer()
    total = TotalSerializer()
    asaitems = AsaItemSerializer(many=True)
    nftcollections = NftCollectionSerializer(many=True)
    notevals = NotevalItemSerializer(many=True)
