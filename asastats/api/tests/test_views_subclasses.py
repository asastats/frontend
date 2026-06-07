"""Testing module for :py:mod:`api.views` address/bundle/nfd subclasses."""

import pytest
from django.contrib.auth.models import User
from factory import Sequence
from factory.django import DjangoModelFactory
from rest_framework.test import APIRequestFactory, force_authenticate

from api.data import (
    API_EXAMPLE_ADDRESS1,
    API_EXAMPLE_ADDRESS2,
    API_EXAMPLE_BUNDLE1,
    API_EXAMPLE_BUNDLE2,
    API_EXAMPLE_NFD_NAME1,
    API_EXAMPLE_NFD_NAME2,
)
from api.views import (
    AddressEntities,
    AddressViewAsas,
    AddressViewAsasAsset,
    AddressViewNftCollections,
    AddressViewNftCollectionsCollection,
    AddressViewNfts,
    AddressViewNftsAsset,
    BaseAddressView,
    BundleEntities,
    BundleViewAsas,
    BundleViewAsasAsset,
    BundleViewNftCollections,
    BundleViewNftCollectionsCollection,
    BundleViewNfts,
    BundleViewNftsAsset,
    NfdNameEntities,
    NfdNameViewAsas,
    NfdNameViewAsasAsset,
    NfdNameViewNftCollections,
    NfdNameViewNftCollectionsCollection,
    NfdNameViewNfts,
    NfdNameViewNftsAsset,
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
        self.factory = APIRequestFactory()
        self.user = UserFactory(username="bob", email="bob@work.com")
        self.request = self.factory.get("/api/v2/fake-path")


class TestApiV2AddressViewAsas(BaseView):
    """Testing class for :class:`api.views.AddressViewAsas`."""

    def test_api_v2_addressviewasas_issubclass_of_baseaddressview(self):
        assert issubclass(AddressViewAsas, BaseAddressView)

    def test_api_v2_addressviewasas_get_functionality(self, mocker):
        view = self.setup_view(AddressViewAsas(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_address", return_value=API_EXAMPLE_ADDRESS2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, address=API_EXAMPLE_ADDRESS1, id=True)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_ADDRESS1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_ADDRESS2, asset_id=True
        )


class TestApiV2AddressViewAsasAsset(BaseView):
    """Testing class for :class:`api.views.AddressViewAsasAsset`."""

    def test_api_v2_addressviewasasasset_issubclass_of_baseaddressview(self):
        assert issubclass(AddressViewAsasAsset, BaseAddressView)

    def test_api_v2_addressviewasasasset_get_functionality(self, mocker):
        view = self.setup_view(AddressViewAsasAsset(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_address", return_value=API_EXAMPLE_ADDRESS2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, address=API_EXAMPLE_ADDRESS1, id=123)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_ADDRESS1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_ADDRESS2, asset_id=123
        )


class TestApiV2AddressViewNfts(BaseView):
    """Testing class for :class:`api.views.AddressViewNfts`."""

    def test_api_v2_addressviewnfts_issubclass_of_baseaddressview(self):
        assert issubclass(AddressViewNfts, BaseAddressView)

    def test_api_v2_addressviewnfts_get_functionality(self, mocker):
        view = self.setup_view(AddressViewNfts(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_address", return_value=API_EXAMPLE_ADDRESS2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, address=API_EXAMPLE_ADDRESS1, id=True)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_ADDRESS1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_ADDRESS2, nft_id=True
        )


class TestApiV2AddressViewNftsAsset(BaseView):
    """Testing class for :class:`api.views.AddressViewNftsAsset`."""

    def test_api_v2_addressviewnftsasset_issubclass_of_baseaddressview(self):
        assert issubclass(AddressViewNftsAsset, BaseAddressView)

    def test_api_v2_addressviewnftsasset_get_functionality(self, mocker):
        view = self.setup_view(AddressViewNftsAsset(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_address", return_value=API_EXAMPLE_ADDRESS2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, address=API_EXAMPLE_ADDRESS1, id=123)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_ADDRESS1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_ADDRESS2, nft_id=123
        )


class TestApiV2AddressViewNftCollections(BaseView):
    """Testing class for :class:`api.views.AddressViewNftCollections`."""

    def test_api_v2_addressviewnftcollections_issubclass_of_baseaddressview(self):
        assert issubclass(AddressViewNftCollections, BaseAddressView)

    def test_api_v2_addressviewnftcollections_get_functionality(self, mocker):
        view = self.setup_view(AddressViewNftCollections(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_address", return_value=API_EXAMPLE_ADDRESS2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, address=API_EXAMPLE_ADDRESS1, name=True)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_ADDRESS1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_ADDRESS2, collection=True
        )


class TestApiV2AddressViewNftCollectionsCollection(BaseView):
    """Testing class for :class:`api.views.AddressViewNftCollectionsCollection`."""

    def test_api_v2_addressviewnftcollectionscollection_issubclass_of_base(self):
        assert issubclass(AddressViewNftCollectionsCollection, BaseAddressView)

    def test_api_v2_addressviewnftcollectionscollection_get_functionality(self, mocker):
        view = self.setup_view(AddressViewNftCollectionsCollection(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_address", return_value=API_EXAMPLE_ADDRESS2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, address=API_EXAMPLE_ADDRESS1, name="coll")
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_ADDRESS1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_ADDRESS2, collection="coll"
        )


class TestApiV2AddressEntities(BaseView):
    """Testing class for :class:`api.views.AddressEntities`."""

    def test_api_v2_addressentities_issubclass_of_baseaddressview(self):
        assert issubclass(AddressEntities, BaseAddressView)

    def test_api_v2_addressentities_get_functionality(self, mocker):
        view = self.setup_view(AddressEntities(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_address", return_value=API_EXAMPLE_ADDRESS2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, address=API_EXAMPLE_ADDRESS1)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_ADDRESS1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_ADDRESS2, entities=True
        )


class TestApiV2BundleViewAsas(BaseView):
    """Testing class for :class:`api.views.BundleViewAsas`."""

    def test_api_v2_bundleviewasas_issubclass_of_baseaddressview(self):
        assert issubclass(BundleViewAsas, BaseAddressView)

    def test_api_v2_bundleviewasas_get_functionality(self, mocker):
        view = self.setup_view(BundleViewAsas(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_bundle", return_value=API_EXAMPLE_BUNDLE2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, bundle=API_EXAMPLE_BUNDLE1, id=True)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_BUNDLE1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_BUNDLE2, asset_id=True
        )


class TestApiV2BundleViewAsasAsset(BaseView):
    """Testing class for :class:`api.views.BundleViewAsasAsset`."""

    def test_api_v2_bundleviewasasasset_issubclass_of_baseaddressview(self):
        assert issubclass(BundleViewAsasAsset, BaseAddressView)

    def test_api_v2_bundleviewasasasset_get_functionality(self, mocker):
        view = self.setup_view(BundleViewAsasAsset(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_bundle", return_value=API_EXAMPLE_BUNDLE2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, bundle=API_EXAMPLE_BUNDLE1, id=123)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_BUNDLE1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_BUNDLE2, asset_id=123
        )


class TestApiV2BundleViewNfts(BaseView):
    """Testing class for :class:`api.views.BundleViewNfts`."""

    def test_api_v2_bundleviewnfts_issubclass_of_baseaddressview(self):
        assert issubclass(BundleViewNfts, BaseAddressView)

    def test_api_v2_bundleviewnfts_get_functionality(self, mocker):
        view = self.setup_view(BundleViewNfts(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_bundle", return_value=API_EXAMPLE_BUNDLE2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, bundle=API_EXAMPLE_BUNDLE1, id=True)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_BUNDLE1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_BUNDLE2, nft_id=True
        )


class TestApiV2BundleViewNftsAsset(BaseView):
    """Testing class for :class:`api.views.BundleViewNftsAsset`."""

    def test_api_v2_bundleviewnftsasset_issubclass_of_baseaddressview(self):
        assert issubclass(BundleViewNftsAsset, BaseAddressView)

    def test_api_v2_bundleviewnftsasset_get_functionality(self, mocker):
        view = self.setup_view(BundleViewNftsAsset(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_bundle", return_value=API_EXAMPLE_BUNDLE2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, bundle=API_EXAMPLE_BUNDLE1, id=123)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_BUNDLE1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_BUNDLE2, nft_id=123
        )


class TestApiV2BundleViewNftCollections(BaseView):
    """Testing class for :class:`api.views.BundleViewNftCollections`."""

    def test_api_v2_bundleviewnftcollections_issubclass_of_baseaddressview(self):
        assert issubclass(BundleViewNftCollections, BaseAddressView)

    def test_api_v2_bundleviewnftcollections_get_functionality(self, mocker):
        view = self.setup_view(BundleViewNftCollections(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_bundle", return_value=API_EXAMPLE_BUNDLE2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, bundle=API_EXAMPLE_BUNDLE1, name=True)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_BUNDLE1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_BUNDLE2, collection=True
        )


class TestApiV2BundleViewNftCollectionsCollection(BaseView):
    """Testing class for :class:`api.views.BundleViewNftCollectionsCollection`."""

    def test_api_v2_bundleviewnftcollectionscollection_issubclass_of_base(self):
        assert issubclass(BundleViewNftCollectionsCollection, BaseAddressView)

    def test_api_v2_bundleviewnftcollectionscollection_get_functionality(self, mocker):
        view = self.setup_view(BundleViewNftCollectionsCollection(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, bundle=API_EXAMPLE_BUNDLE1, collection="coll")
        assert returned == mocked_super.return_value
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_BUNDLE1, collection="coll"
        )


class TestApiV2BundleEntities(BaseView):
    """Testing class for :class:`api.views.BundleEntities`."""

    def test_api_v2_bundleentities_issubclass_of_baseaddressview(self):
        assert issubclass(BundleEntities, BaseAddressView)

    def test_api_v2_bundleentities_get_functionality(self, mocker):
        view = self.setup_view(BundleEntities(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_bundle", return_value=API_EXAMPLE_BUNDLE2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, bundle=API_EXAMPLE_BUNDLE1)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_BUNDLE1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_BUNDLE2, entities=True
        )


class TestApiV2NfdNameViewAsas(BaseView):
    """Testing class for :class:`api.views.NfdNameViewAsas`."""

    def test_api_v2_nfdnameviewasas_issubclass_of_baseaddressview(self):
        assert issubclass(NfdNameViewAsas, BaseAddressView)

    def test_api_v2_nfdnameviewasas_get_functionality(self, mocker):
        view = self.setup_view(NfdNameViewAsas(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_nfd_name", return_value=API_EXAMPLE_NFD_NAME2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, nfd_name=API_EXAMPLE_NFD_NAME1, id=True)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_NFD_NAME1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_NFD_NAME2, asset_id=True
        )


class TestApiV2NfdNameViewAsasAsset(BaseView):
    """Testing class for :class:`api.views.NfdNameViewAsasAsset`."""

    def test_api_v2_nfdnameviewasasasset_issubclass_of_baseaddressview(self):
        assert issubclass(NfdNameViewAsasAsset, BaseAddressView)

    def test_api_v2_nfdnameviewasasasset_get_functionality(self, mocker):
        view = self.setup_view(NfdNameViewAsasAsset(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_nfd_name", return_value=API_EXAMPLE_NFD_NAME2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, nfd_name=API_EXAMPLE_NFD_NAME1, id=123)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_NFD_NAME1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_NFD_NAME2, asset_id=123
        )


class TestApiV2NfdNameViewNfts(BaseView):
    """Testing class for :class:`api.views.NfdNameViewNfts`."""

    def test_api_v2_nfdnameviewnfts_issubclass_of_baseaddressview(self):
        assert issubclass(NfdNameViewNfts, BaseAddressView)

    def test_api_v2_nfdnameviewnfts_get_functionality(self, mocker):
        view = self.setup_view(NfdNameViewNfts(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_nfd_name", return_value=API_EXAMPLE_NFD_NAME2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, nfd_name=API_EXAMPLE_NFD_NAME1, id=True)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_NFD_NAME1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_NFD_NAME2, nft_id=True
        )


class TestApiV2NfdNameViewNftsAsset(BaseView):
    """Testing class for :class:`api.views.NfdNameViewNftsAsset`."""

    def test_api_v2_nfdnameviewnftsasset_issubclass_of_baseaddressview(self):
        assert issubclass(NfdNameViewNftsAsset, BaseAddressView)

    def test_api_v2_nfdnameviewnftsasset_get_functionality(self, mocker):
        view = self.setup_view(NfdNameViewNftsAsset(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_nfd_name", return_value=API_EXAMPLE_NFD_NAME2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, nfd_name=API_EXAMPLE_NFD_NAME1, id=123)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_NFD_NAME1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_NFD_NAME2, nft_id=123
        )


class TestApiV2NfdNameViewNftCollections(BaseView):
    """Testing class for :class:`api.views.NfdNameViewNftCollections`."""

    def test_api_v2_nfdnameviewnftcollections_issubclass_of_baseaddressview(self):
        assert issubclass(NfdNameViewNftCollections, BaseAddressView)

    def test_api_v2_nfdnameviewnftcollections_get_functionality(self, mocker):
        view = self.setup_view(NfdNameViewNftCollections(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_nfd_name", return_value=API_EXAMPLE_NFD_NAME2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, nfd_name=API_EXAMPLE_NFD_NAME1, name=True)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_NFD_NAME1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_NFD_NAME2, collection=True
        )


class TestApiV2NfdNameViewNftCollectionsCollection(BaseView):
    """Testing class for :class:`api.views.NfdNameViewNftCollectionsCollection`."""

    def test_api_v2_nfdnameviewnftcollectionscollection_issubclass_of_base(self):
        assert issubclass(NfdNameViewNftCollectionsCollection, BaseAddressView)

    def test_api_v2_nfdnameviewnftcollectionscollection_get_functionality(self, mocker):
        view = self.setup_view(NfdNameViewNftCollectionsCollection(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(
            self.request, nfd_name=API_EXAMPLE_NFD_NAME1, collection="coll"
        )
        assert returned == mocked_super.return_value
        mocked_super.assert_called_once_with(
            self.request, nfd_name=API_EXAMPLE_NFD_NAME1, collection="coll"
        )


class TestApiV2NfdNameEntities(BaseView):
    """Testing class for :class:`api.views.NfdNameEntities`."""

    def test_api_v2_nfdnameentities_issubclass_of_baseaddressview(self):
        assert issubclass(NfdNameEntities, BaseAddressView)

    def test_api_v2_nfdnameentities_get_functionality(self, mocker):
        view = self.setup_view(NfdNameEntities(), self.request)
        force_authenticate(self.request, user=self.user)
        mocked_validate = mocker.patch(
            "api.views.validate_nfd_name", return_value=API_EXAMPLE_NFD_NAME2
        )
        mocked_super = mocker.patch("api.views.BaseAddressView.get")
        returned = view.get(self.request, nfd_name=API_EXAMPLE_NFD_NAME1)
        assert returned == mocked_super.return_value
        mocked_validate.assert_called_once_with(API_EXAMPLE_NFD_NAME1)
        mocked_super.assert_called_once_with(
            self.request, bundle=API_EXAMPLE_NFD_NAME2, entities=True
        )
