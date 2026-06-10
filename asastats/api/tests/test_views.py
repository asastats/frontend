"""Testing module for :py:mod:`api.views` module."""

import pytest
from django.contrib.auth.models import User
from factory import Sequence
from factory.django import DjangoModelFactory
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from api.data import (
    API_EXAMPLE_ADDRESS1,
    API_EXAMPLE_ADDRESS2,
    API_EXAMPLE_ADDRESS3,
    API_EXAMPLE_ADDRESS5,
    API_EXAMPLE_BUNDLE1,
    API_EXAMPLE_BUNDLE2,
    API_EXAMPLE_NFD_NAME1,
    API_EXAMPLE_NFD_NAME2,
)
from api.permissions import CanAccessApiPermission
from api.views import (
    AddressView,
    BaseAddressView,
    BundleNameView,
    BundleView,
    NfdNameView,
    RawPostView,
    SettingsView,
)

pytestmark = pytest.mark.django_db


class UserFactory(DjangoModelFactory):
    username = Sequence("testuser{}".format)
    email = Sequence("testuser{}@company.com".format)

    class Meta:
        model = User


class BaseView:
    """Base helper class for testing custom views."""

    def setup_view(self, view, request, *args, **kwargs):
        """Mimic as_view() returned callable, but returns view instance.

        args and kwargs are the same as those passed to ``reverse()``

        """
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view

    # # helper methods
    def setup_method(self):
        # Setup request
        self.factory = APIRequestFactory()
        self.user = UserFactory(username="bob", email="bob@work.com")
        self.request = self.factory.get("/api/v2/fake-path")


class BasePostView:
    """Base helper class for testing custom views."""

    def setup_view(self, view, request, *args, **kwargs):
        """Mimic as_view() returned callable, but returns view instance.

        args and kwargs are the same as those passed to ``reverse()``

        """
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view

    # # helper methods
    def setup_method(self):
        # Setup request
        self.factory = APIRequestFactory()
        self.user = UserFactory(username="bob", email="bob@work.com")
        self.request = self.factory.post(
            "/api/v2/", {"addresses": API_EXAMPLE_ADDRESS1}
        )
        self.request.data = self.request.POST


class TestApiV2BaseAddressView(BaseView):
    """Testing class for :class:`api.views.BaseAddressView`."""

    # # BaseAddressView
    def test_api_v2_baseaddressview_issubclass_of_apiview(self):
        assert issubclass(BaseAddressView, APIView)

    def test_api_v2_baseaddressview_initializes_permission_classes(self):
        assert isinstance(BaseAddressView.permission_classes, tuple)
        assert BaseAddressView.permission_classes == (
            IsAuthenticated,
            CanAccessApiPermission,
        )

    def test_api_v2_baseaddressview_get_for_provided_asset_id_true(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        # self.request.data = self.request.POST
        view = BaseAddressView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        bundle = API_EXAMPLE_BUNDLE1
        serialized_data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=serialized_data
        )
        processed_data = mocker.MagicMock()
        mocked_processed = mocker.patch(
            "api.views.processed_asaitems", return_value=processed_data
        )
        mocked_filtered_asa = mocker.patch("api.views.filtered_asaitem")
        mocked_processed_nftitems = mocker.patch("api.views.processed_nftitems")
        mocked_filtered_nft = mocker.patch("api.views.filtered_nftitem")
        mocked_processed_nftcollections = mocker.patch(
            "api.views.processed_nftcollections"
        )
        mocked_filtered_nftcollection = mocker.patch("api.views.filtered_nftcollection")
        mocked_entities = mocker.patch("api.views.account_entities")
        mocked_processed_account = mocker.patch("api.views.processed_account")
        mocker.patch("api.views.check_bundle_addresses", return_value="")
        asset_id = True
        response = view.get(self.request, bundle=bundle, asset_id=asset_id)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == processed_data
        mocked_fetch.assert_called_once_with(bundle, "")
        mocked_processed.assert_called_once_with(serialized_data, self.request.GET)
        mocked_filtered_asa.assert_not_called()
        mocked_processed_nftitems.assert_not_called()
        mocked_filtered_nft.assert_not_called()
        mocked_processed_nftcollections.assert_not_called()
        mocked_filtered_nftcollection.assert_not_called()
        mocked_entities.assert_not_called()
        mocked_processed_account.assert_not_called()

    def test_api_v2_baseaddressview_get_for_provided_asset_id(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        # self.request.data = self.request.POST
        view = BaseAddressView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        bundle = API_EXAMPLE_BUNDLE1
        serialized_data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=serialized_data
        )
        filtered_data = mocker.MagicMock()
        mocked_processed_asaitems = mocker.patch("api.views.processed_asaitems")
        mocked_filtered_asa = mocker.patch(
            "api.views.filtered_asaitem", return_value=filtered_data
        )
        mocked_processed_nftitems = mocker.patch("api.views.processed_nftitems")
        mocked_filtered_nft = mocker.patch("api.views.filtered_nftitem")
        mocked_processed_nftcollections = mocker.patch(
            "api.views.processed_nftcollections"
        )
        mocked_filtered_nftcollection = mocker.patch("api.views.filtered_nftcollection")
        mocked_entities = mocker.patch("api.views.account_entities")
        mocked_processed_account = mocker.patch("api.views.processed_account")
        mocker.patch("api.views.check_bundle_addresses", return_value="")
        asset_id = 505
        response = view.get(self.request, bundle=bundle, asset_id=asset_id)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == filtered_data
        mocked_fetch.assert_called_once_with(bundle, "")
        mocked_filtered_asa.assert_called_once_with(
            asset_id, serialized_data, self.request.GET
        )
        mocked_processed_asaitems.assert_not_called()
        mocked_processed_nftitems.assert_not_called()
        mocked_filtered_nft.assert_not_called()
        mocked_processed_nftcollections.assert_not_called()
        mocked_filtered_nftcollection.assert_not_called()
        mocked_entities.assert_not_called()
        mocked_processed_account.assert_not_called()

    def test_api_v2_baseaddressview_get_for_provided_nft_id_true(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        # self.request.data = self.request.POST
        view = BaseAddressView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        bundle = API_EXAMPLE_BUNDLE1
        serialized_data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=serialized_data
        )
        processed_data = mocker.MagicMock()
        mocked_processed_asaitems = mocker.patch("api.views.processed_asaitems")
        mocked_filtered_asa = mocker.patch("api.views.filtered_asaitem")
        mocked_processed_nftitems = mocker.patch(
            "api.views.processed_nftitems", return_value=processed_data
        )
        mocked_filtered_nft = mocker.patch("api.views.filtered_nftitem")
        mocked_processed_nftcollections = mocker.patch(
            "api.views.processed_nftcollections"
        )
        mocked_filtered_nftcollection = mocker.patch("api.views.filtered_nftcollection")
        mocked_entities = mocker.patch("api.views.account_entities")
        mocked_processed_account = mocker.patch("api.views.processed_account")
        mocker.patch("api.views.check_bundle_addresses", return_value="")
        nft_id = True
        response = view.get(self.request, bundle=bundle, nft_id=nft_id)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == processed_data
        mocked_fetch.assert_called_once_with(bundle, "")
        mocked_processed_nftitems.assert_called_once_with(
            serialized_data, self.request.GET
        )
        mocked_processed_asaitems.assert_not_called()
        mocked_filtered_asa.assert_not_called()
        mocked_processed_nftcollections.assert_not_called()
        mocked_filtered_nftcollection.assert_not_called()
        mocked_filtered_nft.assert_not_called()
        mocked_entities.assert_not_called()
        mocked_processed_account.assert_not_called()

    def test_api_v2_baseaddressview_get_for_provided_nft_id(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        # self.request.data = self.request.POST
        view = BaseAddressView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        bundle = API_EXAMPLE_BUNDLE1
        serialized_data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=serialized_data
        )
        filtered_data = mocker.MagicMock()
        mocked_processed_asaitems = mocker.patch("api.views.processed_asaitems")
        mocked_filtered_asa = mocker.patch("api.views.filtered_asaitem")
        mocked_processed_nftitems = mocker.patch("api.views.processed_nftitems")
        mocked_filtered_nft = mocker.patch(
            "api.views.filtered_nftitem", return_value=filtered_data
        )
        mocked_processed_nftcollections = mocker.patch(
            "api.views.processed_nftcollections"
        )
        mocked_filtered_nftcollection = mocker.patch("api.views.filtered_nftcollection")
        mocked_entities = mocker.patch("api.views.account_entities")
        mocked_processed_account = mocker.patch("api.views.processed_account")
        mocker.patch("api.views.check_bundle_addresses", return_value="")
        nft_id = 505
        response = view.get(self.request, bundle=bundle, nft_id=nft_id)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == filtered_data
        mocked_fetch.assert_called_once_with(bundle, "")
        mocked_filtered_nft.assert_called_once_with(
            nft_id, serialized_data, self.request.GET
        )
        mocked_processed_asaitems.assert_not_called()
        mocked_filtered_asa.assert_not_called()
        mocked_processed_nftitems.assert_not_called()
        mocked_processed_nftcollections.assert_not_called()
        mocked_filtered_nftcollection.assert_not_called()
        mocked_entities.assert_not_called()
        mocked_processed_account.assert_not_called()

    def test_api_v2_baseaddressview_get_for_provided_collection_true(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        # self.request.data = self.request.POST
        view = BaseAddressView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        bundle = API_EXAMPLE_BUNDLE1
        serialized_data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=serialized_data
        )
        processed_data = mocker.MagicMock()
        mocked_processed_asaitems = mocker.patch("api.views.processed_asaitems")
        mocked_filtered_asa = mocker.patch("api.views.filtered_asaitem")
        mocked_processed_nftitems = mocker.patch("api.views.processed_nftitems")
        mocked_filtered_nft = mocker.patch("api.views.filtered_nftitem")
        mocked_processed_nftcollections = mocker.patch(
            "api.views.processed_nftcollections", return_value=processed_data
        )
        mocked_filtered_nftcollection = mocker.patch("api.views.filtered_nftcollection")
        mocked_entities = mocker.patch("api.views.account_entities")
        mocked_processed_account = mocker.patch("api.views.processed_account")
        mocker.patch("api.views.check_bundle_addresses", return_value="")
        collection = True
        response = view.get(self.request, bundle=bundle, collection=collection)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == processed_data
        mocked_fetch.assert_called_once_with(bundle, "")
        mocked_processed_nftcollections.assert_called_once_with(
            serialized_data, self.request.GET
        )
        mocked_processed_asaitems.assert_not_called()
        mocked_filtered_asa.assert_not_called()
        mocked_processed_nftitems.assert_not_called()
        mocked_filtered_nftcollection.assert_not_called()
        mocked_filtered_nft.assert_not_called()
        mocked_entities.assert_not_called()
        mocked_processed_account.assert_not_called()

    def test_api_v2_baseaddressview_get_for_provided_collection(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        # self.request.data = self.request.POST
        view = BaseAddressView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        bundle = API_EXAMPLE_BUNDLE1
        serialized_data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=serialized_data
        )
        filtered_data = mocker.MagicMock()
        mocked_processed_asaitems = mocker.patch("api.views.processed_asaitems")
        mocked_filtered_asa = mocker.patch("api.views.filtered_asaitem")
        mocked_processed_nftitems = mocker.patch("api.views.processed_nftitems")
        mocked_filtered_nft = mocker.patch("api.views.filtered_nftitem")
        mocked_processed_nftcollections = mocker.patch(
            "api.views.processed_nftcollections"
        )
        mocked_filtered_nftcollection = mocker.patch(
            "api.views.filtered_nftcollection", return_value=filtered_data
        )
        mocked_entities = mocker.patch("api.views.account_entities")
        mocked_processed_account = mocker.patch("api.views.processed_account")
        mocker.patch("api.views.check_bundle_addresses", return_value="")
        collection = "collection"
        response = view.get(self.request, bundle=bundle, collection=collection)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == filtered_data
        mocked_fetch.assert_called_once_with(bundle, "")
        mocked_filtered_nftcollection.assert_called_once_with(
            collection, serialized_data, self.request.GET
        )
        mocked_processed_asaitems.assert_not_called()
        mocked_filtered_asa.assert_not_called()
        mocked_processed_nftitems.assert_not_called()
        mocked_processed_nftcollections.assert_not_called()
        mocked_filtered_nft.assert_not_called()
        mocked_entities.assert_not_called()
        mocked_processed_account.assert_not_called()

    def test_api_v2_baseaddressview_get_for_provided_entities(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        # self.request.data = self.request.POST
        view = BaseAddressView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        bundle = API_EXAMPLE_BUNDLE1
        serialized_data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=serialized_data
        )
        mocked_processed_asaitems = mocker.patch("api.views.processed_asaitems")
        mocked_filtered_asa = mocker.patch("api.views.filtered_asaitem")
        mocked_processed_nftitems = mocker.patch("api.views.processed_nftitems")
        mocked_filtered_nft = mocker.patch("api.views.filtered_nftitem")
        mocked_processed_nftcollections = mocker.patch(
            "api.views.processed_nftcollections"
        )
        mocked_filtered_nftcollection = mocker.patch("api.views.filtered_nftcollection")
        mocked_processed_account = mocker.patch("api.views.processed_account")
        mocker.patch("api.views.check_bundle_addresses", return_value="")
        account_entities = mocker.MagicMock()
        mocked_entities = mocker.patch(
            "api.views.account_entities", return_value=account_entities
        )
        entities = True
        response = view.get(self.request, bundle=bundle, entities=entities)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == account_entities
        mocked_fetch.assert_called_once_with(bundle, "")
        mocked_entities.assert_called_once_with(serialized_data)
        mocked_filtered_nftcollection.assert_not_called()
        mocked_processed_asaitems.assert_not_called()
        mocked_filtered_asa.assert_not_called()
        mocked_processed_nftitems.assert_not_called()
        mocked_processed_nftcollections.assert_not_called()
        mocked_filtered_nft.assert_not_called()
        mocked_processed_account.assert_not_called()

    def test_api_v2_baseaddressview_get_for_no_additional_kwargs(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        # self.request.data = self.request.POST
        view = BaseAddressView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        bundle = API_EXAMPLE_BUNDLE1
        serialized_data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=serialized_data
        )
        mocked_processed_asaitems = mocker.patch("api.views.processed_asaitems")
        mocked_filtered_asa = mocker.patch("api.views.filtered_asaitem")
        mocked_processed_nftitems = mocker.patch("api.views.processed_nftitems")
        mocked_filtered_nft = mocker.patch("api.views.filtered_nftitem")
        mocked_processed_nftcollections = mocker.patch(
            "api.views.processed_nftcollections"
        )
        mocked_filtered_nftcollection = mocker.patch("api.views.filtered_nftcollection")
        mocked_entities = mocker.patch("api.views.account_entities")
        processed_account = mocker.MagicMock()
        mocked_processed_account = mocker.patch(
            "api.views.processed_account", return_value=processed_account
        )
        mocker.patch("api.views.check_bundle_addresses", return_value="")
        response = view.get(self.request, bundle=bundle)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == processed_account
        mocked_fetch.assert_called_once_with(bundle, "")
        mocked_processed_account.assert_called_once_with(
            serialized_data, self.request.GET
        )
        mocked_filtered_nftcollection.assert_not_called()
        mocked_processed_asaitems.assert_not_called()
        mocked_filtered_asa.assert_not_called()
        mocked_processed_nftitems.assert_not_called()
        mocked_processed_nftcollections.assert_not_called()
        mocked_filtered_nft.assert_not_called()
        mocked_entities.assert_not_called()


class TestApiV2AddressView(BaseView):
    """Testing class for :class:`api.views.AddressView`."""

    # # AddressView
    def test_api_v2_addressview_issubclass_of_baseaddressview(self):
        assert issubclass(AddressView, BaseAddressView)

    def test_api_v2_addressview_get_functionality(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        # self.request.data = self.request.POST
        view = AddressView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        address = API_EXAMPLE_ADDRESS1
        validated_address = API_EXAMPLE_ADDRESS2
        mocked_validate = mocker.patch(
            "api.views.validate_address", return_value=validated_address
        )
        data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=data
        )
        response = view.get(self.request, address=address)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == data
        mocked_validate.assert_called_once_with(address)
        mocked_fetch.assert_called_once_with(validated_address, "")


class TestApiV2NfdBundleNameView(BaseView):
    """Testing class for :class:`api.views.BundleNameView`."""

    # # BundleNameView
    def test_api_v2_bundlenameview_issubclass_of_apiview(self):
        assert issubclass(BundleNameView, APIView)

    def test_api_v2_bundlenameview_get_functionality(self, mocker):
        # Setup view
        self.request = self.factory.get("/api/v2/foo")
        # self.request.data = self.request.POST
        view = BundleNameView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        with pytest.raises(NotImplementedError):
            view.get(self.request)


class TestApiV2BundleView(BaseView):
    """Testing class for :class:`api.views.BundleView`."""

    # # BundleView
    def test_api_v2_bundlesview_issubclass_of_baseaddressview(self):
        assert issubclass(BundleView, BaseAddressView)

    def test_api_v2_bundleview_get_functionality(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        # self.request.data = self.request.POST
        view = BundleView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        bundle = API_EXAMPLE_BUNDLE1
        validated_bundle = API_EXAMPLE_BUNDLE2
        mocked_validate = mocker.patch(
            "api.views.validate_bundle", return_value=validated_bundle
        )
        addresses = (
            f"{API_EXAMPLE_ADDRESS1} {API_EXAMPLE_ADDRESS5} "
            f"{API_EXAMPLE_ADDRESS3} {API_EXAMPLE_ADDRESS2}"
        )
        mocker.patch("utils.helpers.cached_bundle", return_value=addresses)
        data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=data
        )
        response = view.get(self.request, bundle=bundle)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == data
        mocked_validate.assert_called_once_with(bundle)
        mocked_fetch.assert_called_once_with(
            validated_bundle,
            addresses,
        )


class TestApiV2NfdNameView(BaseView):
    """Testing class for :class:`api.views.NfdNameView`."""

    # # NfdNameView
    def test_api_v2_nfdnameview_issubclass_of_baseaddressview(self):
        assert issubclass(NfdNameView, BaseAddressView)

    def test_api_v2_nfdnameview_get_functionality(self, mocker):
        # Setup view
        self.request = self.factory.get(f"/api/v2/{API_EXAMPLE_NFD_NAME1}")
        # self.request.data = self.request.POST
        view = NfdNameView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        nfd_name = API_EXAMPLE_NFD_NAME1
        validated_nfd_name = API_EXAMPLE_NFD_NAME2
        mocked_validate = mocker.patch(
            "api.views.validate_nfd_name", return_value=validated_nfd_name
        )
        data = mocker.MagicMock()
        mocked_fetch = mocker.patch(
            "api.views.fetch_and_serialize_account", return_value=data
        )
        response = view.get(self.request, nfd_name=nfd_name)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == data
        mocked_validate.assert_called_once_with(nfd_name)
        mocked_fetch.assert_called_once_with(validated_nfd_name, "")


class TestApiV2RawPostView(BasePostView):
    """Testing class for :class:`api.views.RawPostView`."""

    # # RawPostView
    def test_api_v2_rawpostview_issubclass_of_apiview(self):
        assert issubclass(RawPostView, APIView)

    def test_api_v2_rawpostview_initializes_permission_classes(self):
        assert isinstance(RawPostView.permission_classes, tuple)
        assert RawPostView.permission_classes == (
            IsAuthenticated,
            CanAccessApiPermission,
        )

    def test_api_v2_rawpostview_post_for_single_address(self, mocker):
        # Setup view
        view = RawPostView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        addresses = f"{API_EXAMPLE_ADDRESS1}"
        mocked_validate = mocker.patch(
            "api.views.validate_raw_addresses", return_value=addresses
        )
        mocked_bundle = mocker.patch("api.views.create_bundle")
        mocked_serializer = mocker.patch("api.views.BundleHashSerializer")
        response = view.post(self.request)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == mocked_serializer.return_value.data
        mocked_validate.assert_called_once_with(self.request.data.get("addresses"))
        mocked_serializer.assert_called_once_with({"bundle": addresses})
        mocked_bundle.assert_not_called()

    def test_api_v2_rawpostview_post_for_multiple_addresses(self, mocker):
        # Setup view
        self.request = self.factory.post(
            "/api/v2/", {"addresses": f"{API_EXAMPLE_ADDRESS1},{API_EXAMPLE_NFD_NAME1}"}
        )
        self.request.data = self.request.POST
        view = RawPostView()
        view = self.setup_view(view, self.request)
        # Make an authenticated request to the view...
        force_authenticate(self.request, user=self.user)
        addresses = f"{API_EXAMPLE_ADDRESS1} {API_EXAMPLE_ADDRESS3}"
        mocked_validate = mocker.patch(
            "api.views.validate_raw_addresses", return_value=addresses
        )
        bundle = "bundle"
        mocked_bundle = mocker.patch("api.views.create_bundle", return_value=bundle)
        mocked_serializer = mocker.patch("api.views.BundleHashSerializer")
        response = view.post(self.request)
        # Check.
        assert response.status_code == status.HTTP_200_OK
        assert response.data == mocked_serializer.return_value.data
        mocked_validate.assert_called_once_with(self.request.data.get("addresses"))
        mocked_bundle.assert_called_once_with(addresses)
        mocked_serializer.assert_called_once_with({"bundle": bundle})


class TestApiV2SettingsView:
    """Testing class for :class:`api.views.SettingsView`.

    Same dispatch-style as ``BaseView`` (GET endpoint, single-method
    surface), so we inline a minimal ``setup_method`` rather than
    inheriting from ``BaseView``.
    """

    def setup_method(self):
        from django.contrib.auth.models import User
        from factory import Sequence
        from factory.django import DjangoModelFactory
        from rest_framework.test import APIRequestFactory

        class _UserFactory(DjangoModelFactory):
            username = Sequence("settingsuser{}".format)
            email = Sequence("settingsuser{}@company.com".format)

            class Meta:
                model = User

        self.factory = APIRequestFactory()
        self.user = _UserFactory(username="settings-user", email="s@u.com")
        self.request = self.factory.get("/api/v2/settings/")

    def _setup_view(self, view):
        view.request = self.request
        view.args = ()
        view.kwargs = {}
        return view

    def test_settingsview_issubclass_of_apiview(self):
        # Plain DRF APIView, same family as RawPostView etc.
        assert issubclass(SettingsView, APIView)

    def test_settingsview_initializes_permission_classes(self):
        # Matches v1 ApiSettingsView and v2 RawPostView. The mobile app's
        # existing API_KEY -> bearer-token auth flow continues to work.
        assert isinstance(SettingsView.permission_classes, tuple)
        assert SettingsView.permission_classes == (
            IsAuthenticated,
            CanAccessApiPermission,
        )

    def test_settingsview_returns_global_settings_payload(self, mocker):
        # The view's only behaviour: return API_GLOBAL_SETTINGS verbatim.
        # We patch the module-level constant so the test doesn't depend on
        # the live settings shape (which can grow over time).
        sentinel = {"asa_colors": {"0": "#fff"}, "slogans": ["test slogan"]}
        mocker.patch("api.views.API_GLOBAL_SETTINGS", sentinel)

        view = self._setup_view(SettingsView())
        force_authenticate(self.request, user=self.user)

        response = view.get(self.request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == sentinel

    def test_settingsview_get_ignores_args_and_kwargs(self, mocker):
        # The URL pattern doesn't capture any path parameters, but the
        # method signature accepts *args / **kwargs for forwarding
        # compatibility with @method_decorator(cache_page).
        # This test guards against a regression where someone accidentally
        # tightens the signature and breaks the cache_page wrapping.
        sentinel = {"slogans": []}
        mocker.patch("api.views.API_GLOBAL_SETTINGS", sentinel)

        view = self._setup_view(SettingsView())
        force_authenticate(self.request, user=self.user)

        # Pass extra args / kwargs — should be silently accepted.
        response = view.get(self.request, "spurious-arg", spurious_kwarg=True)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == sentinel
