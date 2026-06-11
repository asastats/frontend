"""Testing module for :py:mod:`core.models` module."""

import time
import types
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DataError, connection, models
from django.db.utils import IntegrityError
from django.http import Http404
from django.utils import timezone

from core.models import BundleName, Profile
from utils.constants.users import (
    DUPLICATE_BUNDLE_ERROR,
    DUPLICATE_BUNDLE_NAME_ERROR,
    DUPLICATE_PUBLIC_BUNDLE_NAME_ERROR,
    PUBLIC_BUNDLE_ADDRESSES_NOT_ALLOWED_HELP_TEXT,
    SUBSCRIPTION_TIER_PERMISSIONS,
    SUBSCRIPTION_TIER_PUBLIC_BUNDLE_NAMES_COUNT,
    SYSTEM_RESERVED_URL_PATH_ERROR,
)
from utils.tests.fixtures import TEST_ADDRESS, TEST_ADDRESS2, TEST_ADDRESS3
from utils.userhelpers import slugified_bundle_name

user_model = get_user_model()


class TestProfileModel:
    """Testing class for :class:`Profile` model."""

    # # fields characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("user", models.OneToOneField),
            ("address", models.CharField),
            ("authorized", models.CharField),
            ("votes", models.BigIntegerField),
            ("permission", models.BigIntegerField),
            ("currency", models.CharField),
        ],
    )
    def test_profile_model_fields(self, name, typ):
        assert hasattr(Profile, name)
        assert isinstance(Profile._meta.get_field(name), typ)

    @pytest.mark.django_db
    def test_profile_model_user_is_not_optional(self):
        with pytest.raises(ValidationError):
            Profile().full_clean()

    @pytest.mark.django_db
    def test_profile_model_delete_new_user_delete_its_profile(self):
        user = user_model.objects.create()
        profile_id = user.profile.id
        user.delete()
        with pytest.raises(Profile.DoesNotExist):
            Profile.objects.get(pk=profile_id)

    @pytest.mark.django_db
    def test_profile_model_cannot_save_too_long_address(self):
        profile = Profile(currency="a" * 100)
        with pytest.raises(DataError):
            profile.save()
            profile.full_clean()

    @pytest.mark.django_db
    def test_profile_model_cannot_save_too_long_currency(self):
        profile = Profile(currency="too long currency")
        with pytest.raises(DataError):
            profile.save()
            profile.full_clean()

    def test_profile_model_default_votes_for_profile(self):
        profile = Profile()
        assert profile.votes == 0

    def test_profile_model_default_permission_for_profile(self):
        profile = Profile()
        assert profile.permission == 0

    def test_profile_model_default_currency_for_profile(self):
        profile = Profile()
        assert profile.currency == "ALGO"

    # # __str__
    @pytest.mark.django_db
    def test_profile_model_string_representation_is_profilenama(self):
        user = user_model.objects.create(
            first_name="John", last_name="Doe", username="username", email="abs@abc.com"
        )
        assert str(user.profile) == user.profile.name

    # # _query_bundle_names
    def test_profile_model_query_bundle_names_functionality(self):
        profile = Profile()
        with mock.patch("core.models.BundleName.objects.filter") as mocked_filter:
            returned = profile._query_bundle_names()
            assert returned == mocked_filter.return_value
            mocked_filter.assert_called_once_with(profile=profile)

    # # _query_public_bundle_names
    def test_profile_model_query_public_bundle_names_functionality(self):
        profile = Profile()
        with mock.patch("core.models.BundleName.objects.filter") as mocked_filter:
            returned = profile._query_public_bundle_names()
            assert returned == mocked_filter.return_value
            mocked_filter.assert_called_once_with(profile=profile, public=True)

    # # address_authorization_note
    @pytest.mark.django_db
    def test_profile_model_address_authorization_note_functionality(self, mocker):
        user = user_model.objects.create(email="authorizationnote@example.com")
        user.profile.address = TEST_ADDRESS2
        user.profile.save()
        mocked_truncate = mocker.patch("core.models.truncated_timestamp_and_address")
        mocked_hash = mocker.patch("core.models.unique_hash_from_number")
        returned = user.profile.address_authorization_note()
        assert returned == mocked_hash.return_value
        mocked_truncate.assert_called_once_with(
            user.date_joined.timestamp(), TEST_ADDRESS2
        )
        mocked_hash.assert_called_once_with(mocked_truncate.return_value)

    # # check_votes_and_permission

    @pytest.mark.django_db
    def test_profile_model_check_votes_and_permission_skips_on_none(self, mocker):
        provider = mocker.patch("core.models.get_permission_provider").return_value
        provider.votes_and_permission.return_value = None
        profile = Profile()
        save = mocker.patch.object(Profile, "save")
        profile.check_votes_and_permission()
        save.assert_not_called()

    @pytest.mark.django_db
    def test_profile_model_check_votes_and_permission_updates(self, mocker):
        provider = mocker.patch("core.models.get_permission_provider").return_value
        provider.votes_and_permission.return_value = (3, 100)
        profile = Profile(votes=0, permission=0, address="A")
        save = mocker.patch.object(Profile, "save")
        profile.check_votes_and_permission()
        assert (profile.votes, profile.permission) == (3, 100)
        save.assert_called_once()

    # # save
    @pytest.mark.django_db
    def test_profile_model_save_for_no_address(self):
        user = user_model.objects.create(email="save1@subscribed.com")
        user.profile.address = ""
        user.profile.permission = 0
        user.profile.authorized = ""
        user.profile.save()
        assert user.profile.address == ""
        user.profile.address = TEST_ADDRESS2
        user.profile.save()
        assert user.profile.address == TEST_ADDRESS2
        assert user.profile.permission == 0
        assert user.profile.authorized == ""

    @pytest.mark.django_db
    def test_profile_model_save_for_existing_instance_same_address(self):
        user = user_model.objects.create(email="save1@subscribed.com")
        user.profile.address = TEST_ADDRESS
        user.profile.permission = 1_000_000_000_000
        user.profile.authorized = "authorized"
        user.profile.save()
        assert user.profile.address == TEST_ADDRESS
        assert user.profile.permission == 1_000_000_000_000
        user.profile.address = TEST_ADDRESS
        user.profile.save()
        assert user.profile.address == TEST_ADDRESS
        assert user.profile.permission == 1_000_000_000_000
        assert user.profile.authorized == "authorized"

    @pytest.mark.django_db
    def test_profile_model_save_for_existing_instance_address_changed(self):
        user = user_model.objects.create(email="save1@subscribed.com")
        user.profile.address = TEST_ADDRESS
        user.profile.permission = 1_000_000_000_000
        user.profile.authorized = "authorized"
        user.profile.save()
        assert user.profile.address == TEST_ADDRESS
        assert user.profile.permission == 1_000_000_000_000
        assert user.profile.authorized == "authorized"
        user.profile.address = TEST_ADDRESS2
        user.profile.save()
        assert user.profile.address == TEST_ADDRESS2
        assert user.profile.permission == 0
        assert user.profile.authorized == ""

    # # tier_name
    @pytest.mark.parametrize(
        "permission,name",
        [
            (0, "Trial"),
            (2_329_968_942, "Trial"),
            (2_329_968_943, "Intro"),
            (23_299_689_437, "Intro"),
            (23_299_689_438, "Asastatser"),
            (258_885_438_199, "Asastatser"),
            (258_885_438_200, "Professional"),
            (3_236_067_977_499, "Professional"),
            (3_236_067_977_500, "Cluster"),
            (1_000_000_000_000_000, "Cluster"),
        ],
    )
    def test_profile_model_tier_name_functionality(self, permission, name):
        profile = Profile()
        profile.permission = permission
        assert profile.tier_name() == name

    # # update_authorized
    @pytest.mark.django_db
    def test_profile_model_update_authorized_functionality(self, mocker):
        user = user_model.objects.create(email="update_authorized@example.com")
        user.profile.address = TEST_ADDRESS
        user.profile.save()
        transaction_id = "S5BH36JWJXD3NPOTTNNU3FOPUY53I6B4JXIFYU2K3HCXCV2ARZRA"
        mocked_check = mocker.patch("core.models.Profile.check_votes_and_permission")
        user.profile.update_authorized(transaction_id)
        assert user.profile.authorized == transaction_id
        mocked_check.assert_called_once_with()

    # # PERMISSIONS
    # # _bundlename_limit_data
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,result",
        [
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1,
                [],
                [(0, 0, 5)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Intro"],
                [["1"] * 8],
                [(1, 3, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Intro"],
                [],
                [(0, 3, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [["1"] * 8],
                [(0, 3, 15), (1, 5, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [],
                [(0, 3, 15), (0, 5, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 9, ["1"] * 8, ["1"] * 7],
                [(0, 3, 35), (0, 5, 15), (3, 10, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 9, ["1"] * 8],
                [(0, 3, 35), (0, 5, 15), (2, 10, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 8, ["1"] * 7],
                [(0, 3, 35), (0, 5, 15), (2, 10, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 9, ["1"] * 7],
                [(0, 3, 35), (0, 5, 15), (2, 10, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 9],
                [(0, 3, 35), (0, 5, 15), (1, 10, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 8],
                [(0, 3, 35), (0, 5, 15), (1, 10, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12, ["1"] * 9, ["1"] * 9, ["1"] * 8, ["1"] * 7],
                [(0, 3, 100), (0, 5, 35), (1, 10, 15), (4, 20, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 9, ["1"] * 9, ["1"] * 8, ["1"] * 7],
                [(0, 3, 100), (0, 5, 35), (0, 10, 15), (4, 20, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12, ["1"] * 9, ["1"] * 8, ["1"] * 7],
                [(0, 3, 100), (0, 5, 35), (1, 10, 15), (3, 20, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12, ["1"] * 9, ["1"] * 9, ["1"] * 8],
                [(0, 3, 100), (0, 5, 35), (1, 10, 15), (3, 20, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12, ["1"] * 9, ["1"] * 9],
                [(0, 3, 100), (0, 5, 35), (1, 10, 15), (2, 20, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12, ["1"] * 8, ["1"] * 9],
                [(0, 3, 100), (0, 5, 35), (1, 10, 15), (2, 20, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 9],
                [(0, 3, 100), (0, 5, 35), (0, 10, 15), (1, 20, 10)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12],
                [(0, 3, 100), (0, 5, 35), (1, 10, 15), (0, 20, 10)],
            ),
        ],
    )
    def test_profile_model_bundlename_limit_data_functionality(
        self, permission, collection, result, mocker
    ):
        bundlenames = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundlenames.append(bundlename)
        user = user_model.objects.create(
            username="{}_bundlename_limit_data.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        returned = user.profile._bundlename_limit_data(bundlenames)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == result

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,result",
        [
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [["1"] * 8],
                [(0, 0, 10), (1, 1, 8)],
            ),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], [], [(0, 0, 10), (0, 1, 8)]),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 9, ["1"] * 8, ["1"] * 7],
                [(0, 0, 15), (1, 1, 10), (2, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 9, ["1"] * 8],
                [(0, 0, 15), (1, 1, 10), (1, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 8, ["1"] * 7],
                [(0, 0, 15), (0, 1, 10), (2, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 9, ["1"] * 7],
                [(0, 0, 15), (1, 1, 10), (1, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 9],
                [(0, 0, 15), (1, 1, 10), (0, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 8],
                [(0, 0, 15), (0, 1, 10), (1, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12, ["1"] * 9, ["1"] * 9, ["1"] * 8, ["1"] * 7],
                [(0, 0, 35), (1, 1, 15), (2, 2, 10), (2, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 9, ["1"] * 9, ["1"] * 8, ["1"] * 7],
                [(0, 0, 35), (0, 1, 15), (2, 2, 10), (2, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12, ["1"] * 9, ["1"] * 8, ["1"] * 7],
                [(0, 0, 35), (1, 1, 15), (1, 2, 10), (2, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12, ["1"] * 9, ["1"] * 9, ["1"] * 8],
                [(0, 0, 35), (1, 1, 15), (2, 2, 10), (1, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12, ["1"] * 9, ["1"] * 9],
                [(0, 0, 35), (1, 1, 15), (2, 2, 10), (0, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12, ["1"] * 8, ["1"] * 9],
                [(0, 0, 35), (1, 1, 15), (1, 2, 10), (1, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 9],
                [(0, 0, 35), (0, 1, 15), (1, 2, 10), (0, 2, 8)],
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 12],
                [(0, 0, 35), (1, 1, 15), (0, 2, 10), (0, 2, 8)],
            ),
        ],
    )
    def test_profile_model_bundlename_limit_data_for_public_functionality(
        self, permission, collection, result, mocker
    ):
        bundlenames = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundlenames.append(bundlename)
        user = user_model.objects.create(
            username="{}_bundlename_limit_data.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        returned = user.profile._bundlename_limit_data(
            bundlenames, collection=SUBSCRIPTION_TIER_PUBLIC_BUNDLE_NAMES_COUNT
        )
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == result

    # # _can_sort_and_filter
    @pytest.mark.parametrize(
        "permission",
        [
            SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
            SUBSCRIPTION_TIER_PERMISSIONS["Professional"] + 1,
            SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
            SUBSCRIPTION_TIER_PERMISSIONS["Cluster"] + 1,
        ],
    )
    def test_profile_model_can_sort_and_filter_functionality_for_permission(
        self, permission
    ):
        profile = Profile()
        profile.permission = permission
        assert profile._can_sort_and_filter() is True

    @pytest.mark.parametrize(
        "permission",
        [
            SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1,
            SUBSCRIPTION_TIER_PERMISSIONS["Intro"],
            SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"] - 1,
            SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"] + 1,
            SUBSCRIPTION_TIER_PERMISSIONS["Professional"] - 1,
        ],
    )
    def test_profile_model_can_sort_and_filter_functionality_for_false(
        self, permission
    ):
        profile = Profile()
        profile.permission = permission
        assert profile._can_sort_and_filter() is False

    # # bundle_size_limit
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,limit",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1, 5),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], 8),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 15),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 35),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 100),
        ],
    )
    def test_profile_model_bundle_size_limit_for_no_bundlenames(
        self, permission, limit, mocker
    ):
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=[]
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.bundle_size_limit() == limit
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,limit",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1, [["1"] * 5], 5),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], [["1"] * 7], 8),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], [["1"] * 15, ["1"] * 8], 15),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 20, ["1"] * 35],
                35,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 20, ["1"] * 100],
                100,
            ),
        ],
    )
    def test_profile_model_bundle_size_limit_for_rare_bundlenames(
        self, permission, collection, limit, mocker
    ):
        bundlenames = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundlenames.append(bundlename)
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.bundle_size_limit() == limit
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,limit",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], [["1"] * 7, ["1"] * 8], 8),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 12,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 2,
                ],
                10,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [
                    ["1"] * 35,
                    ["1"] * 30,
                    ["1"] * 25,
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 15,
                    ["1"] * 14,
                ],
                15,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [
                    ["1"] * 100,
                    ["1"] * 90,
                    ["1"] * 36,
                    ["1"] * 35,
                    ["1"] * 25,
                    ["1"] * 30,
                    ["1"] * 24,
                ],
                35,
            ),
        ],
    )
    def test_profile_model_bundle_size_limit_for_full_right(
        self, permission, collection, limit, mocker
    ):
        bundlenames = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundlenames.append(bundlename)
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.bundle_size_limit() == limit
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,limit",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], [["1"] * 7, ["1"] * 8], 8),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 12,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 2,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                ],
                10,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [
                    ["1"] * 35,
                    ["1"] * 30,
                    ["1"] * 25,
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 11,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 1,
                    ["1"] * 10,
                ],
                10,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [
                    ["1"] * 100,
                    ["1"] * 90,
                    ["1"] * 36,
                    ["1"] * 35,
                    ["1"] * 25,
                    ["1"] * 30,
                    ["1"] * 32,
                    ["1"] * 20,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 11,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 15,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 1,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 1,
                    ["1"] * 5,
                    ["1"] * 5,
                ],
                10,
            ),
        ],
    )
    def test_profile_model_bundle_size_limit_for_almost_full_left(
        self, permission, collection, limit, mocker
    ):
        bundlenames = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundlenames.append(bundlename)
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.bundle_size_limit() == limit
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,limit",
        [
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Intro"],
                [["1"] * 7, ["1"] * 8, ["1"] * 8],
                8,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 12,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 2,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 5,
                ],
                10,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [
                    ["1"] * 35,
                    ["1"] * 30,
                    ["1"] * 25,
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 11,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 1,
                    ["1"] * 8,
                    ["1"] * 5,
                ],
                10,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [
                    ["1"] * 100,
                    ["1"] * 90,
                    ["1"] * 36,
                    ["1"] * 35,
                    ["1"] * 25,
                    ["1"] * 30,
                    ["1"] * 25,
                    ["1"] * 18,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 11,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 15,
                    ["1"] * 15,
                    ["1"] * 15,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 1,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 1,
                    ["1"] * 5,
                    ["1"] * 10,
                ],
                10,
            ),
        ],
    )
    def test_profile_model_bundle_size_limit_for_full(
        self, permission, collection, limit, mocker
    ):
        bundlenames = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundlenames.append(bundlename)
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.bundle_size_limit() == limit
        mocked_query.assert_called_once_with()

    # # bundle_size_limit_for_public
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,limit",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1, 0),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], 0),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 8),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 10),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 15),
        ],
    )
    def test_profile_model_bundle_size_limit_for_public_for_no_bundlenames(
        self, permission, limit, mocker
    ):
        mocked_query = mocker.patch(
            "core.models.Profile._query_public_bundle_names", return_value=[]
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.bundle_size_limit_for_public() == limit
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,limit",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], [], 8),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], [], 10),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], [], 15),
        ],
    )
    def test_profile_model_bundle_size_limit_for_public_for_empty(
        self, permission, collection, limit, mocker
    ):
        bundlenames = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundlenames.append(bundlename)
        mocked_query = mocker.patch(
            "core.models.Profile._query_public_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.bundle_size_limit_for_public() == limit
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,limit",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], [["1"] * 9], 8),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 12, ["1"] * 9],
                8,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
                [["1"] * 28, ["1"] * 12, ["1"] * 11],
                10,
            ),
        ],
    )
    def test_profile_model_bundle_size_limit_for_public_for_almost_full(
        self, permission, collection, limit, mocker
    ):
        bundlenames = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundlenames.append(bundlename)
        mocked_query = mocker.patch(
            "core.models.Profile._query_public_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.bundle_size_limit_for_public() == limit
        mocked_query.assert_called_once_with()

    # # can_access_api
    @pytest.mark.django_db
    def test_profile_model_can_access_api_for_true(self):
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        user.profile.save()
        assert user.profile.can_access_api() is True

    @pytest.mark.django_db
    def test_profile_model_can_access_api_for_false(self):
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"] - 1
        user.profile.save()
        assert user.profile.can_access_api() is False

    # # can_access_authorize
    @pytest.mark.django_db
    def test_profile_model_can_access_authorize_for_true(self):
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.authorized = ""
        user.profile.save()
        assert user.profile.can_access_authorize() is True

    @pytest.mark.django_db
    def test_profile_model_can_access_authorize_for_false(self):
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.authorized = "value"
        user.profile.save()
        assert user.profile.can_access_authorize() is False

    # # can_add_bundle_name
    @pytest.mark.django_db
    def test_profile_model_can_add_bundle_name_calls_query_bundle_names(self, mocker):
        mocker.patch("core.models.Profile.tier_name", return_value="Trial")
        mocked_query = mocker.patch("core.models.Profile._query_bundle_names")
        mocked_query.return_value.count.return_value = 1
        user = user_model.objects.create(username="callsquery")
        user.profile.can_add_bundle_name()
        mocked_query.assert_called_once_with()
        mocked_query.return_value.count.assert_called_once_with()

    @pytest.mark.django_db
    def test_profile_model_can_add_bundle_name_callstier_name(self, mocker):
        mocked_query = mocker.patch("core.models.Profile._query_bundle_names")
        mocked_query.return_value.count.return_value = 1
        mocked_teir = mocker.patch("core.models.Profile.tier_name", return_value="Foo")
        user = user_model.objects.create(username="callstiername")
        returned = user.profile.can_add_bundle_name()
        mocked_teir.assert_called_once_with()
        assert returned is False

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,count",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], 1),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], 2),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 1),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 4),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 7),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 1),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 9),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 17),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 1),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 19),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 37),
        ],
    )
    def test_profile_model_can_add_bundle_name_for_true(
        self, permission, count, mocker
    ):
        query = mocker.MagicMock()
        query.count.return_value = count
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=query
        )
        user = user_model.objects.create(
            username="username{}{}".format(permission, count)
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.can_add_bundle_name() is True
        mocked_query.assert_called_once_with()
        query.count.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,count",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1, 1),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1, 10),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], 3),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], 10),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 8),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 18),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 18),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 40),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 38),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 100),
        ],
    )
    def test_profile_model_can_add_bundle_name_for_false(
        self, permission, count, mocker
    ):
        query = mocker.MagicMock()
        query.count.return_value = count
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=query
        )
        user = user_model.objects.create(
            username="username{}{}".format(permission, count)
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.can_add_bundle_name() is False
        mocked_query.assert_called_once_with()
        query.count.assert_called_once_with()

    # # can_add_public_bundle_name
    @pytest.mark.django_db
    def test_profile_model_can_add_public_bundle_name_returns_false_no_instance(
        self, mocker
    ):
        mocker.patch("core.models.Profile.tier_name", return_value="Trial")
        mocked_limit = mocker.patch(
            "core.models.Profile.bundle_size_limit_for_public", return_value=0
        )
        addresses = f"{TEST_ADDRESS2} {TEST_ADDRESS3}"
        user = user_model.objects.create(username="bundle_size_limit_for_public1")
        returned = user.profile.can_add_public_bundle_name(None, addresses)
        assert returned is False
        mocked_limit.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,count",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 0),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 1),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 2),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 0),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 1),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 2),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 3),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 4),
        ],
    )
    def test_profile_model_can_add_public_bundle_name_for_true_no_instance(
        self, permission, count, mocker
    ):
        mocker.patch(
            "core.models.Profile.bundle_size_limit_for_public", return_value=10
        )
        bundlenames = [mocker.MagicMock()] * count
        mocked_query = mocker.patch(
            "core.models.Profile._query_public_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="username{}{}".format(permission, count)
        )
        user.profile.permission = permission
        user.profile.save()
        addresses = "1 2 3"
        assert user.profile.can_add_public_bundle_name(None, addresses) is True
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,count",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 0),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 1),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 2),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 0),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 1),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 2),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 3),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 4),
        ],
    )
    def test_profile_model_can_add_public_bundle_name_for_true_with_instance(
        self, permission, count, mocker
    ):
        mocker.patch(
            "core.models.Profile.bundle_size_limit_for_public", return_value=10
        )
        bundlenames = [mocker.MagicMock()] * count
        user = user_model.objects.create(
            username="username{}{}".format(permission, count)
        )
        user.profile.permission = permission
        user.profile.save()
        unique = str(time.time())[5:]
        bundlename = BundleName.objects.create(
            profile=user.profile,
            name=f"name-{unique}",
            addresses=TEST_ADDRESS2,
        )
        if count:
            bundlenames[0].id = bundlename.id

        mocked_query = mocker.patch(
            "core.models.Profile._query_public_bundle_names", return_value=bundlenames
        )

        addresses = "1 2 3"
        assert user.profile.can_add_public_bundle_name(bundlename.id, addresses) is True
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,count",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 1),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 3),
            (SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 5),
        ],
    )
    def test_profile_model_can_add_public_bundle_name_for_false(
        self, permission, count, mocker
    ):
        mocker.patch(
            "core.models.Profile.bundle_size_limit_for_public", return_value=10
        )
        bundlenames = [mocker.MagicMock()] * count
        mocked_query = mocker.patch(
            "core.models.Profile._query_public_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="username{}{}".format(permission, count)
        )
        user.profile.permission = permission
        user.profile.save()
        addresses = "1 2 3"
        assert user.profile.can_add_public_bundle_name(None, addresses) is False
        mocked_query.assert_called_once_with()

    # # can_use_bundle_names
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,result",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1, False),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], True),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], True),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], True),
        ],
    )
    def test_profile_model_can_use_bundle_names_for_no_bundlenames(
        self, permission, result, mocker
    ):
        bundlenames = mocker.MagicMock()
        bundlenames.count.return_value = 0
        bundlenames.__iter__.return_value = []
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.can_use_bundle_names() is result
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,count,result",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], 3, True),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 8, True),
            (SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 18, True),
        ],
    )
    def test_profile_model_can_use_bundle_names_for_allowed_total_count(
        self, permission, count, result, mocker
    ):
        bundlenames = mocker.MagicMock()
        bundlenames.count.return_value = count
        bundlenames.__iter__.return_value = []
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.can_use_bundle_names() is result
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,result",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1, [["1"] * 5], False),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], [["1"] * 7], True),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [["1"] * 15, ["1"] * 8],
                True,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [["1"] * 20, ["1"] * 35],
                True,
            ),
        ],
    )
    def test_profile_model_can_use_bundle_names_for_rare_bundlenames(
        self, permission, collection, result, mocker
    ):
        bundles = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundles.append(bundlename)
        bundlenames = mocker.MagicMock()
        bundlenames.count.return_value = len(bundles)
        bundlenames.__iter__.return_value = bundles
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.can_use_bundle_names() is result
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,result",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1, [["1"] * 7, ["1"] * 8], False),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], [["1"] * 7, ["1"] * 8], True),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 12,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 2,
                ],
                True,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [
                    ["1"] * 35,
                    ["1"] * 30,
                    ["1"] * 25,
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 15,
                    ["1"] * 14,
                ],
                True,
            ),
        ],
    )
    def test_profile_model_can_use_bundle_names_for_full_right(
        self, permission, collection, result, mocker
    ):
        bundles = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundles.append(bundlename)
        bundlenames = mocker.MagicMock()
        bundlenames.count.return_value = len(bundles)
        bundlenames.__iter__.return_value = bundles
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.can_use_bundle_names() is result
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,result",
        [
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1, [["1"] * 7, ["1"] * 8], False),
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], [["1"] * 7, ["1"] * 8], True),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 12,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 2,
                ],
                True,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [
                    ["1"] * 35,
                    ["1"] * 30,
                    ["1"] * 25,
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 11,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 1,
                    ["1"] * 10,
                ],
                True,
            ),
        ],
    )
    def test_profile_model_can_use_bundle_names_for_almost_full_left(
        self, permission, collection, result, mocker
    ):
        bundles = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundles.append(bundlename)
        bundlenames = mocker.MagicMock()
        bundlenames.count.return_value = len(bundles)
        bundlenames.__iter__.return_value = bundles
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.can_use_bundle_names() is result
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,result",
        [
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1,
                [["1"] * 7, ["1"] * 8],
                False,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Intro"],
                [["1"] * 7, ["1"] * 8, ["1"] * 8],
                True,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 12,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 2,
                    ["1"] * 10,
                ],
                True,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [
                    ["1"] * 35,
                    ["1"] * 30,
                    ["1"] * 25,
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 11,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 1,
                    ["1"] * 8,
                    ["1"] * 5,
                ],
                True,
            ),
        ],
    )
    def test_profile_model_can_use_bundle_names_for_full(
        self, permission, collection, result, mocker
    ):
        bundles = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundles.append(bundlename)
        bundlenames = mocker.MagicMock()
        bundlenames.count.return_value = len(bundles)
        bundlenames.__iter__.return_value = bundles
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.can_use_bundle_names() is result
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "permission,collection,result",
        [
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1,
                [["1"] * 7, ["1"] * 8],
                False,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Intro"],
                [["1"] * 7, ["1"] * 8, ["1"] * 8, ["1"] * 8],
                False,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Intro"],
                [
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 12,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 2,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 5,
                ],
                False,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [
                    ["1"] * 15,
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 12,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 2,
                    ["1"] * 10,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 5,
                ],
                False,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
                [
                    ["1"] * 35,
                    ["1"] * 30,
                    ["1"] * 25,
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 11,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 1,
                    ["1"] * 8,
                    ["1"] * 5,
                ],
                False,
            ),
            (
                SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
                [
                    ["1"] * 35,
                    ["1"] * 30,
                    ["1"] * 25,
                    ["1"] * 15,
                    ["1"] * 14,
                    ["1"] * 15,
                    ["1"] * 12,
                    ["1"] * 11,
                    ["1"] * 12,
                    ["1"] * 11,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 10,
                    ["1"] * 9,
                    ["1"] * 8,
                    ["1"] * 5,
                    ["1"] * 1,
                    ["1"] * 8,
                    ["1"] * 5,
                ],
                False,
            ),
        ],
    )
    def test_profile_model_can_use_bundle_names_for_more_than_allowed(
        self, permission, collection, result, mocker
    ):
        bundles = []
        for addresses in collection:
            bundlename = mocker.MagicMock()
            bundlename.addresses = " ".join(addresses)
            bundles.append(bundlename)
        bundlenames = mocker.MagicMock()
        bundlenames.count.return_value = len(bundles)
        bundlenames.__iter__.return_value = bundles
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=bundlenames
        )
        user = user_model.objects.create(
            username="{}permission.com".format(time.time())
        )
        user.profile.permission = permission
        user.profile.save()
        assert user.profile.can_use_bundle_names() is result
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    def test_profile_model_can_use_bundle_names_for_cluster(self, mocker):
        mocked_query = mocker.patch("core.models.Profile._query_bundle_names")
        user = user_model.objects.create(username="usernamecluster")
        user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]
        user.profile.save()
        assert user.profile.can_use_bundle_names() is True
        mocked_query.assert_not_called()

    # # show_sort_and_filter
    @pytest.mark.django_db
    def test_profile_model_show_sort_and_filter_calls_can_sort_and_filter(self, mocker):
        mocked_query = mocker.patch("core.models.Profile._query_bundle_names")
        mocked_sort = mocker.patch(
            "core.models.Profile._can_sort_and_filter", return_value=False
        )
        user = user_model.objects.create(username="callsquery")
        returned = user.profile.show_sort_and_filter()
        assert returned is False
        mocked_sort.assert_called_once_with()
        mocked_query.assert_not_called()

    @pytest.mark.django_db
    def test_profile_model_show_sort_and_filter_calls_query_bundle_names(self, mocker):
        mocker.patch("core.models.Profile._can_sort_and_filter", return_value=True)
        mocked_query = mocker.patch("core.models.Profile._query_bundle_names")
        mocked_query.return_value.count.return_value = 1
        user = user_model.objects.create(username="callsquery")
        returned = user.profile.show_sort_and_filter()
        assert returned is False
        mocked_query.assert_called_once_with()

    @pytest.mark.django_db
    def test_profile_model_show_sort_and_filter_returns_true(self, mocker):
        mocker.patch("core.models.Profile._can_sort_and_filter", return_value=True)
        mocked = mocker.patch("core.models.Profile._query_bundle_names")
        mocked.return_value.count.return_value = 2
        user = user_model.objects.create(username="callsquery")
        returned = user.profile.show_sort_and_filter()
        assert returned is True

    # # HELPERS
    # # bundlename_by_name
    @pytest.mark.django_db
    def test_profile_model_bundlename_by_name_returns_valid_bundle_name(self):
        profile = user_model.objects.create(username="bundlename_by_name").profile
        bundlename = BundleName.objects.create(
            profile=profile,
            name="name-b7",
            addresses=TEST_ADDRESS2,
        )
        name = bundlename.name
        assert profile.bundlename_by_name(name) == bundlename

    @pytest.mark.django_db
    def test_profile_model_bundlename_by_name_for_changed_case(self):
        profile = user_model.objects.create(username="bundlename_by_name").profile
        bundlename = BundleName.objects.create(
            profile=profile,
            name="name-b7",
            addresses=TEST_ADDRESS2,
        )
        name = bundlename.name
        assert profile.bundlename_by_name(name.upper()) == bundlename

    @pytest.mark.django_db
    def test_profile_model_bundlename_by_name_raises_404_for_invalid_name(self):
        user = user_model.objects.create()
        BundleName.objects.create(
            profile=user.profile,
            name="name-b7",
            addresses=TEST_ADDRESS2,
        )
        with pytest.raises(Http404):
            user.profile.bundlename_by_name("foobar")

    # # bundlename_system_reserved_url_path_check
    @pytest.mark.django_db
    def test_profile_model_bundlename_system_reserved_url_path_check_raises_error(
        self, mocker
    ):
        mocked_is_system = mocker.patch(
            "core.models.is_system_reserved_url_path", return_value=True
        )
        profile = user_model.objects.create(
            username="bundlename_system_reserved_url_path_check"
        ).profile
        name = "Reserved name"
        with pytest.raises(ValidationError) as exception:
            profile.bundlename_system_reserved_url_path_check(name)
            assert str(exception.value) == SYSTEM_RESERVED_URL_PATH_ERROR
        mocked_is_system.assert_called_once_with(slugified_bundle_name(name))

    @pytest.mark.django_db
    def test_profile_model_bundlename_system_reserved_url_path_check_for_valid_name(
        self, mocker
    ):
        mocked_slugified = mocker.patch("core.models.slugified_bundle_name")
        mocked_is_system = mocker.patch(
            "core.models.is_system_reserved_url_path", return_value=False
        )
        profile = user_model.objects.create(
            username="bundlename_system_reserved_url_path_check"
        ).profile
        name = "Reserved name"
        profile.bundlename_system_reserved_url_path_check(name)
        mocked_slugified.assert_called_once_with(name)
        mocked_is_system.assert_called_once_with(mocked_slugified.return_value)

    # # bundlenames
    @pytest.mark.django_db
    def test_profile_model_bundle_names_functionality(self, mocker):
        user = user_model.objects.create(email="_query_bundle_names1@subscribed.com")
        query = mocker.MagicMock()
        mocked_query = mocker.patch(
            "core.models.Profile._query_bundle_names", return_value=query
        )
        returned = user.profile.bundlenames()
        assert returned == query.all.return_value
        mocked_query.assert_called_once_with()
        query.all.assert_called_once_with()

    # # get_absolute_url
    @pytest.mark.django_db
    def test_profile_model_get_absolute_url(self):
        user = user_model.objects.create(username="username")
        assert user.profile.get_absolute_url() == "/profile/"

    # # integrity_check_for_bundlename
    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_bundlename_for_existing_bundle(
        self, mocker
    ):
        profile = user_model.objects.create(
            username="integrity_check_for_bundlename3"
        ).profile
        returned = profile.integrity_check_for_bundlename(1, mocker.MagicMock())
        assert returned is False

    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_bundlename_for_duplicate_name(
        self,
    ):
        profile = user_model.objects.create(
            username="integrity_check_for_bundlename1"
        ).profile
        name = "Old name"
        BundleName.objects.create(
            profile=profile,
            name=slugified_bundle_name(name),
            addresses=TEST_ADDRESS2,
        )
        cleaned_data = {"name": name, "addresses": TEST_ADDRESS3}
        with pytest.raises(ValidationError) as exception:
            profile.integrity_check_for_bundlename(None, cleaned_data)
            assert str(exception.value) == DUPLICATE_BUNDLE_NAME_ERROR

    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_bundlename_raises_error_case_insensitive(
        self,
    ):
        profile = user_model.objects.create(
            username="integrity_check_for_bundlename1"
        ).profile
        name = "OldName"
        BundleName.objects.create(
            profile=profile,
            name=slugified_bundle_name(name),
            addresses=TEST_ADDRESS2,
        )
        cleaned_data = {"name": name.lower(), "addresses": TEST_ADDRESS3}
        with pytest.raises(ValidationError) as exception:
            profile.integrity_check_for_bundlename(None, cleaned_data)
            assert str(exception.value) == DUPLICATE_BUNDLE_NAME_ERROR

    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_bundlename_for_duplicate_bundle(
        self,
    ):
        profile = user_model.objects.create(
            username="integrity_check_for_bundlename2"
        ).profile
        addresses = f"{TEST_ADDRESS2} {TEST_ADDRESS3}"
        BundleName.objects.create(
            profile=profile,
            name="old-name2",
            addresses=addresses,
        )
        cleaned_data = {"name": "new-name", "addresses": addresses}
        with pytest.raises(ValidationError) as exception:
            profile.integrity_check_for_bundlename(None, cleaned_data)
            assert str(exception.value) == DUPLICATE_BUNDLE_ERROR

    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_bundlename_does_mothing_for_valid_data(
        self,
    ):
        profile = user_model.objects.create(
            username="integrity_check_for_bundlename3"
        ).profile
        BundleName.objects.create(
            profile=profile,
            name="old-name3",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
        )
        cleaned_data = {"name": "new-name5", "addresses": TEST_ADDRESS2}
        returned = profile.integrity_check_for_bundlename(None, cleaned_data)
        assert returned is None

    # # integrity_check_for_public_bundlename
    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_public_bundlename_for_duplicate_name(
        self,
    ):
        profile = user_model.objects.create(
            username="integrity_check_for_public_bundlename1"
        ).profile
        other_profile = user_model.objects.create(
            username="integrity_check_for_public_bundlename_other"
        ).profile
        name = "Old name"
        BundleName.objects.create(
            profile=other_profile,
            name=slugified_bundle_name(name),
            addresses=TEST_ADDRESS2,
            public=True,
        )
        cleaned_data = {
            "name": name,
            "addresses": TEST_ADDRESS3,
            "public": True,
        }
        with pytest.raises(ValidationError) as exception:
            profile.integrity_check_for_public_bundlename(None, cleaned_data)
            assert str(exception.value) == DUPLICATE_PUBLIC_BUNDLE_NAME_ERROR

    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_public_bundlename_case_insensitive(
        self,
    ):
        profile = user_model.objects.create(
            username="integrity_check_for_public_bundlename5"
        ).profile
        other_profile = user_model.objects.create(
            username="integrity_check_for_public_bundlename_other5"
        ).profile
        name = "OldName"
        BundleName.objects.create(
            profile=other_profile,
            name=slugified_bundle_name(name),
            addresses=TEST_ADDRESS2,
            public=True,
        )
        cleaned_data = {
            "name": name,
            "addresses": TEST_ADDRESS3,
            "public": True,
        }
        with pytest.raises(ValidationError) as exception:
            profile.integrity_check_for_public_bundlename(None, cleaned_data)
            assert str(exception.value) == DUPLICATE_BUNDLE_NAME_ERROR

    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_public_bundlename_same_instance(
        self, mocker
    ):
        mocked_add = mocker.patch(
            "core.models.Profile.can_add_public_bundle_name", return_value=True
        )
        profile = user_model.objects.create(
            username="integrity_check_for_public_bundlename1"
        ).profile
        name = "Old name"
        bundlename = BundleName.objects.create(
            profile=profile,
            name=slugified_bundle_name(name),
            addresses=TEST_ADDRESS2,
            public=True,
        )
        cleaned_data = {
            "name": name,
            "addresses": TEST_ADDRESS3,
            "public": True,
        }
        profile.integrity_check_for_public_bundlename(bundlename.id, cleaned_data)
        mocked_add.assert_called_once_with(bundlename.id, TEST_ADDRESS3)

    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_public_bundlename_cannot_add(
        self, mocker
    ):
        mocked_add = mocker.patch(
            "core.models.Profile.can_add_public_bundle_name", return_value=False
        )
        profile = user_model.objects.create(
            username="integrity_check_for_public_bundlename4"
        ).profile
        bundlename = BundleName.objects.create(
            profile=profile,
            name="old-name3",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
            public=True,
        )
        cleaned_data = {"name": "new-name7", "addresses": TEST_ADDRESS2, "public": True}
        with pytest.raises(ValidationError) as exception:
            profile.integrity_check_for_public_bundlename(bundlename.id, cleaned_data)
            assert str(exception.value) == PUBLIC_BUNDLE_ADDRESSES_NOT_ALLOWED_HELP_TEXT
        mocked_add.assert_called_once_with(bundlename.id, TEST_ADDRESS2)

    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_public_bundlename_for_valid_data(
        self, mocker
    ):
        mocked_add = mocker.patch(
            "core.models.Profile.can_add_public_bundle_name", return_value=True
        )
        profile = user_model.objects.create(
            username="integrity_check_for_public_bundlename3"
        ).profile
        BundleName.objects.create(
            profile=profile,
            name="old-name3",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
            public=True,
        )
        cleaned_data = {"name": "new-name5", "addresses": TEST_ADDRESS2, "public": True}
        returned = profile.integrity_check_for_public_bundlename(None, cleaned_data)
        assert returned is None
        mocked_add.assert_called_once_with(None, TEST_ADDRESS2)

    @pytest.mark.django_db
    def test_profile_model_integrity_check_for_public_bundlename_valid_existing(
        self, mocker
    ):
        mocked_add = mocker.patch(
            "core.models.Profile.can_add_public_bundle_name", return_value=True
        )
        profile = user_model.objects.create(
            username="integrity_check_for_public_bundlename3"
        ).profile
        bundlename = BundleName.objects.create(
            profile=profile,
            name="old-name3",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
            public=True,
        )
        cleaned_data = {"name": "new-name5", "addresses": TEST_ADDRESS2, "public": True}
        returned = profile.integrity_check_for_public_bundlename(
            bundlename.id, cleaned_data
        )
        assert returned is None
        mocked_add.assert_called_once_with(bundlename.id, TEST_ADDRESS2)

    # # profile
    @pytest.mark.django_db
    def test_profile_model_profile_returns_self(self):
        user = user_model.objects.create()
        assert user.profile.profile() == user.profile

    # # PROPERTIES
    # # name
    @pytest.mark.django_db
    def test_profile_model_name_is_user_first_name_and_last_name(self):
        user = user_model.objects.create(
            first_name="John", last_name="Doe", username="username", email="abs@abc.com"
        )
        assert user.profile.name == "{} {}".format(user.first_name, user.last_name)

    @pytest.mark.django_db
    def test_profile_model_name_is_user_first_name(self):
        user = user_model.objects.create(
            first_name="John", username="username", email="abs@abc.com"
        )
        assert user.profile.name == user.first_name

    @pytest.mark.django_db
    def test_profile_model_name_is_user_last_name(self):
        user = user_model.objects.create(
            last_name="Doe", username="username", email="abs@abc.com"
        )
        assert user.profile.name == user.last_name

    @pytest.mark.django_db
    def test_profile_model_name_is_user_username(self):
        user = user_model.objects.create(username="username", email="abs@abc.com")
        assert user.profile.name == user.username

    @pytest.mark.django_db
    def test_profile_model_name_is_user_email_without_domain(self):
        user = user_model.objects.create(email="abs@abc.com")
        assert user.profile.name == "abs"

    # # WIDGETS
    # @pytest.mark.django_db
    def test_profile_model_can_access_historic_widget(self, mocker):
        gate = mocker.patch("core.models.can_access_widget", return_value=True)
        profile = Profile()
        assert profile.can_access_historic_widget(3) is True
        gate.assert_called_once_with("historic", profile, 3)


class TestBundleNameModel:
    """Testing class for :class:`BundleName` model."""

    # # test helper methods
    def _create_bundlename(self):
        suffix = str(time.time()).replace(".", "")
        user = user_model.objects.create(
            email=f"{suffix}test.com",
            username=suffix,
        )
        user.profile.permission = 258_885_438_201
        user.profile.save()
        return BundleName.objects.create(
            profile=user.profile,
            name=f"BundleName {suffix}",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
        )

    def _get_constraints(self):
        """Helper to return constraints for BundleName table."""
        with connection.cursor() as cursor:
            return connection.introspection.get_constraints(
                cursor, BundleName._meta.db_table
            )

    # # fields characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("profile", models.ForeignKey),
            ("name", models.CharField),
            ("addresses", models.CharField),
            ("bundle", models.CharField),
            ("public", models.BooleanField),
            ("created", models.DateTimeField),
            ("modified", models.DateTimeField),
        ],
    )
    def test_bundlename_model_fields(self, name, typ):
        assert hasattr(BundleName, name)
        assert isinstance(BundleName._meta.get_field(name), typ)

    @pytest.mark.django_db
    def test_bundlename_model_is_related_to_profile(self):
        user = user_model.objects.create()
        bundlename = BundleName()
        bundlename.profile = user.profile
        bundlename.save()
        assert bundlename in user.profile.bundlename_set.all()

    @pytest.mark.django_db
    def test_bundlename_model_cannot_save_empty_bundlename_name(self):
        profile = Profile.objects.create()
        bundlename = BundleName(
            profile=profile, name="", addresses="", bundle="some desc"
        )
        with pytest.raises(ValidationError):
            bundlename.save()
            bundlename.full_clean()

    @pytest.mark.django_db
    def test_bundlename_model_cannot_save_empty_bundlename_addresses(self):
        profile = Profile.objects.create()
        bundlename = BundleName(profile=profile, addresses="", bundle="some desc")
        with pytest.raises(ValidationError):
            bundlename.save()
            bundlename.full_clean()

    @pytest.mark.django_db
    def test_bundlename_model_cannot_save_too_long_bundlename_addresses(self):
        profile = Profile.objects.create()
        bundlename = BundleName(
            profile=profile, name="name", addresses=" ".join([TEST_ADDRESS2] * 120)
        )
        with pytest.raises(DataError):
            bundlename.save()
            bundlename.full_clean()

    @pytest.mark.django_db
    def test_bundlename_model_cannot_save_too_long_bundlename_name(self):
        profile = Profile.objects.create()
        bundlename = BundleName(
            profile=profile, name="xyz" * 20, addresses=TEST_ADDRESS2
        )
        with pytest.raises(DataError):
            bundlename.save()
            bundlename.full_clean()

    @pytest.mark.django_db
    def test_bundlename_model_public_field_set(self):
        user = user_model.objects.create()
        bundlename = BundleName.objects.create(
            profile=user.profile, name="name5", addresses=TEST_ADDRESS2
        )
        assert bundlename.public is False

    @pytest.mark.django_db
    def test_bundlename_model_creation_datetime_field_set(self):
        user = user_model.objects.create()
        bundlename = BundleName.objects.create(
            profile=user.profile, name="name1", addresses=TEST_ADDRESS2
        )
        assert bundlename.created <= timezone.now()

    def test_bundlename_model_default_name(self):
        bundlename = BundleName()
        assert bundlename.name == ""

    def test_bundlename_model_default_addresses(self):
        bundlename = BundleName()
        assert bundlename.addresses == ""

    def test_bundlename_model_default_bundle(self):
        bundlename = BundleName()
        assert bundlename.bundle == ""

    # # Meta
    @pytest.mark.django_db
    def test_bundlename_model_profile_bundlenames_ordering(self):
        profile1 = Profile.objects.create()
        bundlename1 = BundleName.objects.create(
            profile=profile1, name="name2", addresses=TEST_ADDRESS2
        )
        bundlename2 = BundleName.objects.create(
            profile=profile1, name="name1", addresses=TEST_ADDRESS3
        )
        bundlename3 = BundleName.objects.create(
            profile=profile1, name="name3", addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}"
        )
        assert list(BundleName.objects.all()) == [bundlename2, bundlename1, bundlename3]

    @pytest.mark.django_db
    def test_bundlename_model_unique_constraints_exist(self):
        constraints = self._get_constraints()
        names = constraints.keys()
        # Check your defined unique constraints
        assert "unique_private_profile_name" in names
        assert "unique_profile_bundle" in names
        assert "unique_public_name" in names
        # Verify they are actually UNIQUE
        assert constraints["unique_private_profile_name"]["unique"]
        assert constraints["unique_profile_bundle"]["unique"]
        assert constraints["unique_public_name"]["unique"]

    @pytest.mark.django_db
    def test_bundlename_model_indexes_exist(self):
        constraints = self._get_constraints()
        names = constraints.keys()
        # Check that indexes were created
        assert "idx_lower_name" in names
        assert "idx_lower_name_public" in names
        # Verify they are indexes (not unique constraints)
        assert constraints["idx_lower_name"]["index"]
        assert constraints["idx_lower_name_public"]["index"]

    # #  __str__
    def test_bundlename_model_string_representation(self):
        bundlename = BundleName(name="bundlename1", addresses=TEST_ADDRESS3)
        assert str(bundlename) == "bundlename1"

    # # get_absolute_url
    @pytest.mark.django_db
    def test_bundlename_model_get_absolute_url(self):
        bundlename = self._create_bundlename()
        assert bundlename.get_absolute_url() == "/profile/{}/".format(bundlename.name)

    # # is_eligible_public_bundlename
    def test_core_models_bundlename_is_eligible_public_bundlename(self):
        assert BundleName().is_eligible_public_bundlename() is True

    # # save
    @pytest.mark.django_db
    def test_bundlename_model_save_calls_slugified_bundle_name_and_sets_addresses(
        self, mocker
    ):
        user = user_model.objects.create(email="{}test.com".format(time.time()))
        mocker.patch("core.models.models.Model.save")
        mocked_slugified = mocker.patch("core.models.slugified_bundle_name")
        name = "BundleName 1"
        bundlename = BundleName(
            profile=user.profile,
            name=name,
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
        )
        bundlename.save()
        mocked_slugified.assert_called_once_with(name)
        assert bundlename.addresses == f"{TEST_ADDRESS2} {TEST_ADDRESS3}"

    @pytest.mark.django_db
    def test_bundlename_model_keeps_original_case(self):
        user = user_model.objects.create(email="{}test.com".format(time.time()))
        name = "BundleName1"
        bundlename = BundleName(
            profile=user.profile, name=name, addresses=TEST_ADDRESS2
        )
        bundlename.save()
        bundlename.name = name
        bundlename.save()
        assert bundlename.name == name

    @pytest.mark.django_db
    def test_bundlename_model_save_duplicate_bundlename_addressess_are_invalid(self):
        profile = Profile.objects.create()
        BundleName.objects.create(
            profile=profile, name="name1", addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}"
        )
        with pytest.raises(IntegrityError):
            bundlename = BundleName(
                profile=profile,
                name="name2",
                addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
            )
            bundlename.save()

    @pytest.mark.django_db
    def test_bundlename_model_save_same_bundlename_addresses_to_different_profile(self):
        user1 = user_model.objects.create(username="first")
        user2 = user_model.objects.create(username="second")
        BundleName.objects.create(
            profile=user1.profile,
            name="name1",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
        )
        bundlename = BundleName(
            profile=user2.profile,
            name="name1",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
        )
        bundlename.save()

    @pytest.mark.django_db
    def test_bundlename_model_save_duplicate_name_for_public_true_is_invalid(self):
        profile = Profile.objects.create()
        profile2 = Profile.objects.create()
        BundleName.objects.create(
            profile=profile,
            name="publicname",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
            public=True,
        )
        with pytest.raises(IntegrityError):
            bundlename = BundleName(
                profile=profile2,
                name="publicname",
                addresses=f"{TEST_ADDRESS} {TEST_ADDRESS3}",
                public=True,
            )
            bundlename.save()

    @pytest.mark.django_db
    def test_bundlename_model_save_duplicate_name_for_public_false_is_valid(self):
        profile = Profile.objects.create()
        profile2 = Profile.objects.create()
        BundleName.objects.create(
            profile=profile,
            name="publicname",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
            public=False,
        )
        bundlename = BundleName(
            profile=profile2,
            name="publicname",
            addresses=f"{TEST_ADDRESS} {TEST_ADDRESS3}",
            public=False,
        )
        bundlename.save()

    @pytest.mark.django_db
    def test_bundlename_model_save_updates_bundle_if_changed(self, mocker):
        user = user_model.objects.create(email="{}test.com".format(time.time()))
        updated = "updated"
        mocked_create = mocker.patch("core.models.create_bundle", return_value=updated)
        bundlename = BundleName(
            profile=user.profile,
            name="name2",
            addresses="addresses2",
            bundle="bundle",
        )
        bundlename.save()
        assert bundlename.bundle == updated
        mocked_create.assert_called_once_with("addresses2")

    @pytest.mark.django_db
    def test_bundlename_model_save_keeps_the_same_bundle(self, mocker):
        user = user_model.objects.create(email="{}test.com".format(time.time()))
        bundle = "bundle"
        mocked_create = mocker.patch("core.models.create_bundle", return_value=bundle)
        bundlename = BundleName(
            profile=user.profile,
            name="name2",
            addresses="addresses2",
            bundle=bundle,
        )
        bundlename.save()
        assert bundlename.bundle == bundle
        mocked_create.assert_called_once_with("addresses2")

    @pytest.mark.django_db
    def test_bundlename_model_save_calls_super_save(self, mocker):
        user = user_model.objects.create(email="{}test.com".format(time.time()))
        mocked = mocker.patch("core.models.models.Model.save")
        bundlename = BundleName(
            profile=user.profile,
            name="name2",
            addresses="addresses2",
            bundle="bundle",
        )
        kwargs = {"name1": 1, "name2": 2}
        bundlename.save(**kwargs)
        mocked.assert_called_once_with(**kwargs)

    # # bundlename
    @pytest.mark.django_db
    def test_bundlename_model_bundlename_returns_self(self):
        bundlename = self._create_bundlename()
        assert bundlename.bundlename() == bundlename

    # # PROPERTIES
    # # class_name
    def test_bundlename_model_class_name(self):
        assert BundleName().class_name == "bundlename"

    # # short_created
    @pytest.mark.django_db
    def test_bundlename_model_short_creation_property(self):
        user = user_model.objects.create()
        bundlename = BundleName.objects.create(
            profile=user.profile,
            name="bundlename-a1",
            addresses=TEST_ADDRESS2,
        )
        assert bundlename.short_created == bundlename.created.strftime("%x")

    # # short_modified
    @pytest.mark.django_db
    def test_bundlename_model_short_modified_property(self):
        user = user_model.objects.create()
        bundlename = BundleName.objects.create(
            profile=user.profile,
            name="bundlename-a2",
            addresses=TEST_ADDRESS3,
        )
        assert bundlename.short_modified == bundlename.modified.strftime("%x %X UTC")

    # # size
    @pytest.mark.django_db
    def test_bundlename_model_size_property(self):
        user = user_model.objects.create()
        bundlename = BundleName.objects.create(
            profile=user.profile,
            name="bundlename-a2",
            addresses=f"{TEST_ADDRESS3} {TEST_ADDRESS2} {TEST_ADDRESS}",
        )
        assert bundlename.size == 3

    # # str_created
    @pytest.mark.django_db
    def test_bundlename_model_str_creation_property(self):
        user = user_model.objects.create()
        bundlename = BundleName.objects.create(
            profile=user.profile,
            name="bundlename-a6",
            addresses=TEST_ADDRESS3,
        )
        assert bundlename.str_created == bundlename.created.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    # # str_modified
    @pytest.mark.django_db
    def test_bundlename_model_str_modified_property(self):
        user = user_model.objects.create()
        bundlename = BundleName.objects.create(
            profile=user.profile,
            name="bundlename-a4",
            addresses=TEST_ADDRESS3,
        )
        assert bundlename.str_modified == bundlename.modified.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    # # WIDGETS
    # # can_access_historic_widget
    @pytest.mark.django_db
    def test_core_models_bundlename_can_access_historic_widget(self, mocker):
        gate = mocker.patch("core.models.can_access_widget", return_value=False)
        user = user_model.objects.create()
        bundlename = BundleName.objects.create(
            profile=user.profile,
            name="bundlename-a7",
            addresses=f"{TEST_ADDRESS} {TEST_ADDRESS2} {TEST_ADDRESS3}",
        )
        assert bundlename.can_access_historic_widget() is False
        gate.assert_called_once_with("historic", user.profile, 3)
