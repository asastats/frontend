"""Module containing core app's views."""

import logging

from algosdk.constants import ADDRESS_LEN
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.helpers import (
    validate_address,
    validate_bundle,
    validate_nfd_name,
    validate_raw_addresses,
)
from api.main import (
    account_entities,
    fetch_and_serialize_account,
    filtered_asaitem,
    filtered_nftcollection,
    filtered_nftitem,
    processed_account,
    processed_asaitems,
    processed_nftcollections,
    processed_nftitems,
)
from api.permissions import CanAccessApiPermission
from api.serializers import (
    AsaItemSerializer,
    BundleHashFromAddressesSerializer,
    BundleHashSerializer,
    EntitiesSerializer,
    EvaluatedAccountSerializer,
    NfdNameSerializer,
    NftCollectionSerializer,
    NftItemSerializer,
    NftSaleTypeQuerySerializer,
)
from utils.constants.api import API_GLOBAL_SETTINGS
from utils.constants.apiv2 import (
    ACCOUNT_ASAS_ASSET_PARAMETERS,
    ACCOUNT_ASAS_PARAMETERS,
    ACCOUNT_NFTS_ASSET_PARAMETERS,
    ACCOUNT_NFTS_PARAMETERS,
    ACCOUNT_PARAMETERS,
    ADDRESS_ASAS_ASSET_DESCRIPTION,
    ADDRESS_ASAS_DESCRIPTION,
    ADDRESS_DESCRIPTION,
    ADDRESS_ENTITIES_DESCRIPTION,
    ADDRESS_NFTCOLLECTIONS_COLLECTION_DESCRIPTION,
    ADDRESS_NFTCOLLECTIONS_DESCRIPTION,
    ADDRESS_NFTS_ASSET_DESCRIPTION,
    ADDRESS_NFTS_DESCRIPTION,
    BUNDLE_ASAS_ASSET_DESCRIPTION,
    BUNDLE_ASAS_DESCRIPTION,
    BUNDLE_DESCRIPTION,
    BUNDLE_ENTITIES_DESCRIPTION,
    BUNDLE_NFTCOLLECTIONS_COLLECTION_DESCRIPTION,
    BUNDLE_NFTCOLLECTIONS_DESCRIPTION,
    BUNDLE_NFTS_ASSET_DESCRIPTION,
    BUNDLE_NFTS_DESCRIPTION,
    NFD_NAME_ASAS_ASSET_DESCRIPTION,
    NFD_NAME_ASAS_DESCRIPTION,
    NFD_NAME_DESCRIPTION,
    NFD_NAME_ENTITIES_DESCRIPTION,
    NFD_NAME_NFTCOLLECTIONS_COLLECTION_DESCRIPTION,
    NFD_NAME_NFTCOLLECTIONS_DESCRIPTION,
    NFD_NAME_NFTS_ASSET_DESCRIPTION,
    NFD_NAME_NFTS_DESCRIPTION,
    RAW_POST_DESCRIPTION,
    SETTINGS_DESCRIPTION,
)
from utils.constants.core import CACHE_TTL_ADDRESS
from utils.helpers import check_bundle_addresses, create_bundle

logger = logging.getLogger(__name__)


@extend_schema_view(
    get=extend_schema(
        request=BundleHashSerializer,  # noqa: F821 (already imported in your file)
        responses={200: EvaluatedAccountSerializer},  # noqa: F821
        tags=["Account"],
    )
)
@method_decorator(csrf_protect, name="dispatch")
class BaseAddressView(APIView):
    """API view for presenting account data.

    :var permission_classes: collection of DRF permission classes
    :type permission_classes: tuple
    """

    permission_classes = (IsAuthenticated, CanAccessApiPermission)  # noqa: F821

    def get(self, request, **kwargs):
        """Call rendering document routine using request's data.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var bundle: hash made from provided addresses or single address
        :type bundle: str
        :var addresses: space-joined addresses resolved for a multi-address bundle
        :type addresses: str
        :var asset_id: Algorand standard asset identifier
        :type asset_id: int
        :var nft_id: Algorand standard asset identifier
        :type nft_id: int
        :var collection: NFT collection name
        :type collection: str
        :var entities: should account entities be returned or not
        :type entities: Boolean
        :var serialized_data: serialized data ready to initialize response with
        :type serialized_data: dict
        :return: :class:`Response`
        """
        bundle = kwargs.pop("bundle", "")
        asset_id = kwargs.pop("asset_id", None)
        nft_id = kwargs.pop("nft_id", None)
        collection = kwargs.pop("collection", None)
        entities = kwargs.pop("entities", None)

        # Single address: the value is the address itself -> no lookup needed.
        # Bundle hash: resolve to the addresses the backend needs to fetch.
        addresses = "" if len(bundle) == ADDRESS_LEN else check_bundle_addresses(bundle)

        serialized_data = fetch_and_serialize_account(bundle, addresses)  # noqa: F821

        if asset_id is True:
            serialized_data = processed_asaitems(
                serialized_data, request.GET
            )  # noqa: F821
        elif asset_id is not None:
            serialized_data = filtered_asaitem(
                asset_id, serialized_data, request.GET
            )  # noqa: F821
        elif nft_id is True:
            serialized_data = processed_nftitems(
                serialized_data, request.GET
            )  # noqa: F821
        elif nft_id is not None:
            serialized_data = filtered_nftitem(
                nft_id, serialized_data, request.GET
            )  # noqa: F821
        elif collection is True:
            serialized_data = processed_nftcollections(
                serialized_data, request.GET
            )  # noqa: F821
        elif collection is not None:
            serialized_data = filtered_nftcollection(
                collection, serialized_data, request.GET  # noqa: F821
            )
        elif entities is not None:
            serialized_data = account_entities(serialized_data)  # noqa: F821
        else:
            serialized_data = processed_account(
                serialized_data, request.GET
            )  # noqa: F821

        return Response(serialized_data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateAddress",
        description=ADDRESS_DESCRIPTION,
        summary="Evaluate public Algorand address",
        request=BundleHashSerializer,
        responses={200: EvaluatedAccountSerializer},
        parameters=ACCOUNT_PARAMETERS,
        tags=["Account"],
    )
)
class AddressView(BaseAddressView):
    """API view used to evaluate single public Algorand address."""

    def get(self, request, **kwargs):
        """Call rendering document routine using request's data.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var address: public Algorand address
        :type address: str
        :return: :class:`Response`
        """
        address = kwargs.pop("address", "")
        return super().get(request, bundle=validate_address(address), **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateAddressAsas",
        description=ADDRESS_ASAS_DESCRIPTION,
        summary="Evaluate address' ASA items",
        request=BundleHashSerializer,
        responses={200: AsaItemSerializer(many=True)},
        parameters=ACCOUNT_ASAS_PARAMETERS,
        tags=["ASA"],
    ),
)
class AddressViewAsas(BaseAddressView):
    """API view used to evaluate address' ASA items."""

    def get(self, request, **kwargs):
        """Evaluate address and return ASA items response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var address: public Algorand address
        :type address: str
        :var asset_id: Algorand standard asset identifier
        :type asset_id: int
        :return: :class:`Response`
        """
        address = kwargs.pop("address", "")
        asset_id = kwargs.pop("id")
        return super().get(
            request, bundle=validate_address(address), asset_id=asset_id, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateAddressAsasAsset",
        description=ADDRESS_ASAS_ASSET_DESCRIPTION,
        summary="Address' single ASA item",
        request=BundleHashSerializer,
        responses={200: AsaItemSerializer},
        parameters=ACCOUNT_ASAS_ASSET_PARAMETERS,
        tags=["ASA"],
    ),
)
class AddressViewAsasAsset(AddressViewAsas):
    """API view used to evaluate address' single ASA item."""

    def get(self, request, **kwargs):
        """Evaluate bundle and return response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :return: :class:`Response`
        """
        return super().get(request, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateAddressNfts",
        description=ADDRESS_NFTS_DESCRIPTION,
        summary="Evaluate address' NFT items",
        request=BundleHashSerializer,
        responses={200: NftItemSerializer(many=True)},
        parameters=ACCOUNT_NFTS_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class AddressViewNfts(BaseAddressView):
    """API view used to evaluate address' NFT items."""

    def get(self, request, **kwargs):
        """Evaluate address and return NFT items response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var address: public Algorand address
        :type address: str
        :var nft_id: Algorand standard asset identifier
        :type nft_id: int
        :return: :class:`Response`
        """
        address = kwargs.pop("address", "")
        nft_id = kwargs.pop("id")
        return super().get(
            request, bundle=validate_address(address), nft_id=nft_id, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateAddressNftsAsset",
        description=ADDRESS_NFTS_ASSET_DESCRIPTION,
        summary="Address' single NFT item",
        request=BundleHashSerializer,
        responses={200: NftItemSerializer},
        parameters=ACCOUNT_NFTS_ASSET_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class AddressViewNftsAsset(AddressViewNfts):
    """API view used to evaluate address' single NFT item."""

    def get(self, request, **kwargs):
        """Evaluate bundle and return response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :return: :class:`Response`
        """
        return super().get(request, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateAddressNftCollections",
        description=ADDRESS_NFTCOLLECTIONS_DESCRIPTION,
        summary="Evaluate address' NFT collections",
        request=BundleHashSerializer,
        responses={200: NftCollectionSerializer(many=True)},
        parameters=ACCOUNT_NFTS_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class AddressViewNftCollections(BaseAddressView):
    """API view used to evaluate address' NFT collections."""

    def get(self, request, **kwargs):
        """Evaluate address and return NFT collections response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var address: public Algorand address
        :type address: str
        :var collection: NFT collection name
        :type collection: str
        :return: :class:`Response`
        """
        address = kwargs.pop("address", "")
        collection = kwargs.pop("name")
        return super().get(
            request, bundle=validate_address(address), collection=collection, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateAddressNftCollectionsCollection",
        description=ADDRESS_NFTCOLLECTIONS_COLLECTION_DESCRIPTION,
        summary="Evaluate address' single NFT collection",
        request=BundleHashSerializer,
        responses={200: NftCollectionSerializer},
        parameters=ACCOUNT_NFTS_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class AddressViewNftCollectionsCollection(AddressViewNftCollections):
    """API view used to evaluate address' single NFT collection."""

    def get(self, request, **kwargs):
        """Evaluate address and return NFT collection response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :return: :class:`Response`
        """
        return super().get(request, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="AddressEntities",
        description=ADDRESS_ENTITIES_DESCRIPTION,
        summary="Return all address' entities",
        request=BundleHashSerializer,
        responses={200: EntitiesSerializer},
        tags=["Account"],
    ),
)
class AddressEntities(BaseAddressView):
    """API view used to return all program entities found in account."""

    def get(self, request, **kwargs):
        """Evaluate address and return NFT collections response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var address: public Algorand address
        :type address: str
        :return: :class:`Response`
        """
        address = kwargs.pop("address", "")
        return super().get(
            request, bundle=validate_address(address), entities=True, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateBundleName",
        description="Evaluates bundle name (coming soon).",
        summary="Evaluate bundle name (coming soon)",
        request=BundleHashSerializer,
        responses={200: EvaluatedAccountSerializer},
        tags=["Account"],
    )
)
class BundleNameView(APIView):
    """API view that will be used to evaluate bundle name."""

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """ """
        raise NotImplementedError


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateBundleHash",
        description=BUNDLE_DESCRIPTION,
        summary="Evaluate bundle hash",
        request=BundleHashSerializer,
        responses={200: EvaluatedAccountSerializer},
        parameters=ACCOUNT_PARAMETERS,
        tags=["Account"],
    )
)
class BundleView(BaseAddressView):
    """API view used to evaluate collection of Algorand addresses and/or .algo names."""

    def get(self, request, **kwargs):
        """Evaluate bundle hash and return response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var bundle: hash made from addresses
        :type bundle: str
        :return: :class:`Response`
        """
        bundle = kwargs.pop("bundle", "")
        return super().get(request, bundle=validate_bundle(bundle), **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateBundleAsas",
        description=BUNDLE_ASAS_DESCRIPTION,
        summary="Evaluate bundle's ASA items",
        request=BundleHashSerializer,
        responses={200: AsaItemSerializer(many=True)},
        parameters=ACCOUNT_ASAS_PARAMETERS,
        tags=["ASA"],
    ),
)
class BundleViewAsas(BaseAddressView):
    """API view used to evaluate bundle's ASA items."""

    def get(self, request, **kwargs):
        """Evaluate bundle and return ASA items response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var bundle: hash made from addresses
        :type bundle: str
        :var asset_id: Algorand standard asset identifier
        :type asset_id: int
        :return: :class:`Response`
        """
        bundle = kwargs.pop("bundle", "")
        asset_id = kwargs.pop("id")
        return super().get(
            request, bundle=validate_bundle(bundle), asset_id=asset_id, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateBundleAsasAsset",
        description=BUNDLE_ASAS_ASSET_DESCRIPTION,
        summary="Evaluate bundle's single ASA item",
        request=BundleHashSerializer,
        responses={200: AsaItemSerializer},
        parameters=ACCOUNT_ASAS_ASSET_PARAMETERS,
        tags=["ASA"],
    ),
)
class BundleViewAsasAsset(BundleViewAsas):
    """API view used to evaluate bundle's single ASA item."""

    def get(self, request, **kwargs):
        """Evaluate bundle and return response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :return: :class:`Response`
        """
        return super().get(request, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateBundleNfts",
        description=BUNDLE_NFTS_DESCRIPTION,
        summary="Evaluate bundle's NFT items",
        request=BundleHashSerializer,
        responses={200: NftItemSerializer(many=True)},
        parameters=ACCOUNT_NFTS_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class BundleViewNfts(BaseAddressView):
    """API view used to evaluate bundle's NFT items."""

    def get(self, request, **kwargs):
        """Evaluate bundle and return NFT items response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var bundle: hash made from addresses
        :type bundle: str
        :var nft_id: Algorand standard asset identifier
        :type nft_id: int
        :return: :class:`Response`
        """
        bundle = kwargs.pop("bundle", "")
        nft_id = kwargs.pop("id")
        return super().get(
            request, bundle=validate_bundle(bundle), nft_id=nft_id, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateBundleNftsAsset",
        description=BUNDLE_NFTS_ASSET_DESCRIPTION,
        summary="Evaluate bundle's single NFT item",
        request=BundleHashSerializer,
        responses={200: NftItemSerializer},
        parameters=ACCOUNT_NFTS_ASSET_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class BundleViewNftsAsset(BundleViewNfts):
    """API view used to evaluate bundle's single NFT item."""

    def get(self, request, **kwargs):
        """Evaluate bundle and return response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :return: :class:`Response`
        """
        return super().get(request, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateBundleNftCollections",
        description=BUNDLE_NFTCOLLECTIONS_DESCRIPTION,
        summary="Evaluate bundle's NFT collections",
        request=BundleHashSerializer,
        responses={200: NftCollectionSerializer(many=True)},
        parameters=ACCOUNT_NFTS_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class BundleViewNftCollections(BaseAddressView):
    """API view used to evaluate bundle's NFT collections."""

    def get(self, request, **kwargs):
        """Evaluate bundle and return NFT collections response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var bundle: hash made from addresses
        :type bundle: str
        :var collection: NFT collection name
        :type collection: str
        :return: :class:`Response`
        """
        bundle = kwargs.pop("bundle", "")
        collection = kwargs.pop("name")
        return super().get(
            request, bundle=validate_bundle(bundle), collection=collection, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateBundleNftCollectionsCollection",
        description=BUNDLE_NFTCOLLECTIONS_COLLECTION_DESCRIPTION,
        summary="Evaluate bundle's single NFT collection",
        request=BundleHashSerializer,
        responses={200: NftCollectionSerializer},
        parameters=ACCOUNT_NFTS_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class BundleViewNftCollectionsCollection(BaseAddressView):
    """API view used to evaluate bundle's single NFT collection."""

    def get(self, request, **kwargs):
        """Evaluate bundle and return NFT collection response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :return: :class:`Response`
        """
        return super().get(request, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="BundleEntities",
        description=BUNDLE_ENTITIES_DESCRIPTION,
        summary="Return all bundle's entities",
        request=BundleHashSerializer,
        responses={200: EntitiesSerializer},
        tags=["Account"],
    ),
)
class BundleEntities(BaseAddressView):
    """API view used to return all program entities found in account."""

    def get(self, request, **kwargs):
        """Evaluate address and return NFT collections response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var bundle: hash made from addresses
        :type bundle: str
        :return: :class:`Response`
        """
        bundle = kwargs.pop("bundle", "")
        return super().get(
            request, bundle=validate_bundle(bundle), entities=True, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateNfdName",
        description=NFD_NAME_DESCRIPTION,
        summary="Evaluate .algo name",
        request=NfdNameSerializer,
        responses={200: EvaluatedAccountSerializer},
        parameters=ACCOUNT_PARAMETERS,
        tags=["Account"],
    )
)
class NfdNameView(BaseAddressView):
    """API view used to evaluate NFD .algo name."""

    def get(self, request, **kwargs):
        """Evaluate NFD name and return response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var nfd_name: NFDomains .algo name
        :type nfd_name: str
        :return: :class:`Response`
        """
        nfd_name = kwargs.pop("nfd_name", "")
        return super().get(request, bundle=validate_nfd_name(nfd_name), **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateNfdNameAsas",
        description=NFD_NAME_ASAS_DESCRIPTION,
        summary="Evaluate .algo name's ASA items",
        request=BundleHashSerializer,
        responses={200: AsaItemSerializer(many=True)},
        parameters=ACCOUNT_ASAS_PARAMETERS,
        tags=["ASA"],
    ),
)
class NfdNameViewAsas(BaseAddressView):
    """API view used to evaluate NFD .algo name's ASA items."""

    def get(self, request, **kwargs):
        """Evaluate NFD name and return ASA items response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var nfd_name: NFDomains .algo name
        :type nfd_name: str
        :var asset_id: Algorand standard asset identifier
        :type asset_id: int
        :return: :class:`Response`
        """
        nfd_name = kwargs.pop("nfd_name", "")
        asset_id = kwargs.pop("id")
        return super().get(
            request, bundle=validate_nfd_name(nfd_name), asset_id=asset_id, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateNfdNameAsasAsset",
        description=NFD_NAME_ASAS_ASSET_DESCRIPTION,
        summary="Evaluate .algo name's single ASA item",
        request=BundleHashSerializer,
        responses={200: AsaItemSerializer},
        parameters=ACCOUNT_ASAS_ASSET_PARAMETERS,
        tags=["ASA"],
    ),
)
class NfdNameViewAsasAsset(NfdNameViewAsas):
    """API view used to evaluate NFD .algo name's single ASA item."""

    def get(self, request, **kwargs):
        """Evaluate NFD name and return response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :return: :class:`Response`
        """
        return super().get(request, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateNfdNameNfts",
        description=NFD_NAME_NFTS_DESCRIPTION,
        summary="Evaluate .algo name's NFT items",
        request=BundleHashSerializer,
        responses={200: NftItemSerializer(many=True)},
        parameters=ACCOUNT_NFTS_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class NfdNameViewNfts(BaseAddressView):
    """API view used to evaluate NFD .algo name's NFT items."""

    def get(self, request, **kwargs):
        """Evaluate NFD name and return NFT items response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var nfd_name: NFDomains .algo name
        :type nfd_name: str
        :var nft_id: Algorand standard asset identifier
        :type nft_id: int
        :return: :class:`Response`
        """
        nfd_name = kwargs.pop("nfd_name", "")
        nft_id = kwargs.pop("id")
        return super().get(
            request, bundle=validate_nfd_name(nfd_name), nft_id=nft_id, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateNfdNameNftsAsset",
        description=NFD_NAME_NFTS_ASSET_DESCRIPTION,
        summary="Evaluate .algo name's single NFT item",
        request=BundleHashSerializer,
        responses={200: NftItemSerializer},
        parameters=ACCOUNT_NFTS_ASSET_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class NfdNameViewNftsAsset(NfdNameViewNfts):
    """API view used to evaluate NFD .algo name's single NFT item."""

    def get(self, request, **kwargs):
        """Evaluate NFD name and return response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :return: :class:`Response`
        """
        return super().get(request, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateNfdNameNftCollections",
        description=NFD_NAME_NFTCOLLECTIONS_DESCRIPTION,
        summary="Evaluate .algo name's NFT collections",
        request=BundleHashSerializer,
        responses={200: NftCollectionSerializer(many=True)},
        parameters=ACCOUNT_NFTS_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class NfdNameViewNftCollections(BaseAddressView):
    """API view used to evaluate NFD .algo name's NFT collections."""

    def get(self, request, **kwargs):
        """Evaluate NFD name and return NFT collections response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var nfd_name: NFDomains .algo name
        :type nfd_name: str
        :var collection: NFT collection name
        :type collection: str
        :return: :class:`Response`
        """
        nfd_name = kwargs.pop("nfd_name", "")
        collection = kwargs.pop("name")
        return super().get(
            request, bundle=validate_nfd_name(nfd_name), collection=collection, **kwargs
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="EvaluateNfdNameNftCollectionsCollection",
        description=NFD_NAME_NFTCOLLECTIONS_COLLECTION_DESCRIPTION,
        summary="Evaluate .algo name's single NFT collection",
        request=BundleHashSerializer,
        responses={200: NftCollectionSerializer},
        parameters=ACCOUNT_NFTS_PARAMETERS + [NftSaleTypeQuerySerializer],
        tags=["NFT"],
    ),
)
class NfdNameViewNftCollectionsCollection(BaseAddressView):
    """API view used to evaluate NFD .algo name's single NFT collection."""

    def get(self, request, **kwargs):
        """Evaluate NFD name and return NFT collection response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :return: :class:`Response`
        """
        return super().get(request, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="NfdNameEntities",
        description=NFD_NAME_ENTITIES_DESCRIPTION,
        summary="Return all .algo name entities",
        request=BundleHashSerializer,
        responses={200: EntitiesSerializer},
        tags=["Account"],
    ),
)
class NfdNameEntities(BaseAddressView):
    """API view used to return all program entities found in account."""

    def get(self, request, **kwargs):
        """Evaluate address and return NFT collections response object.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var nfd_name: NFDomains .algo name
        :type nfd_name: str
        :return: :class:`Response`
        """
        nfd_name = kwargs.pop("nfd_name", "")
        return super().get(
            request, bundle=validate_nfd_name(nfd_name), entities=True, **kwargs
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="RetrieveBundleHash",
        description=RAW_POST_DESCRIPTION,
        summary="Return bundle hash",
        request=BundleHashFromAddressesSerializer,
        responses={200: BundleHashSerializer},
        tags=["Account"],
    )
)
class RawPostView(APIView):
    """API view used to return bundle hash created from provided addresses.

    :var permission_classes: collection of DRF permission classes
    :type permission_classes: tuple
    """

    permission_classes = (IsAuthenticated, CanAccessApiPermission)

    def post(self, request, **kwargs):
        """Check and return address or bundle from request's data.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var addresses: collection of addresses and .algo names
        :type addresses: str
        :var serialized_bundle: serialized evaluated bundle
        :type serialized_bundle: :class:`BundleHashSerializer`
        :return: :class:`Response`
        """
        addresses = validate_raw_addresses(request.data.get("addresses"))
        serialized_bundle = BundleHashSerializer(
            {"bundle": create_bundle(addresses) if " " in addresses else addresses}
        )
        return Response(serialized_bundle.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        operation_id="RetrieveSettings",
        description=SETTINGS_DESCRIPTION,
        summary="Return global settings",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Account"],
    )
)
@method_decorator(cache_page(CACHE_TTL_ADDRESS), name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class SettingsView(APIView):
    """API view used to return global settings data.

    Returns the same ``API_GLOBAL_SETTINGS`` payload the v1 ``ApiSettingsView``
    served, kept identical so the mobile-app migration to v2 is a pure URL
    swap on the settings call. Cached for ``CACHE_TTL_ADDRESS`` to match the
    v1 endpoint's behaviour.

    :var permission_classes: collection of DRF permission classes
    :type permission_classes: tuple
    """

    permission_classes = (IsAuthenticated, CanAccessApiPermission)

    def get(self, request, *args, **kwargs):
        """Return global settings data.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :return: :class:`Response`
        """
        return Response(API_GLOBAL_SETTINGS, status=status.HTTP_200_OK)
