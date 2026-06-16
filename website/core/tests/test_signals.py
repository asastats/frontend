"""Testing module for :py:mod:`core.signals` module."""

from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import Profile
from utils.tests.fixtures import TEST_ADDRESS

user_model = get_user_model()


class TestCoreSignals:
    """Testing class for :py:mod:`core.signals` module."""

    # # create_user_profile
    @pytest.mark.django_db
    def test_core_signals_new_user_creation_creates_its_profile(self):
        user = user_model.objects.create()
        assert isinstance(user.profile, Profile)

    # # save_user_profile
    @pytest.mark.django_db
    def test_core_signals_user_saving_saves_its_profile(self):
        user = user_model.objects.create()
        profile_id = user.profile.id
        permission = 100
        user.profile.permission = permission
        assert Profile.objects.get(pk=profile_id).permission != permission
        user.save()
        assert Profile.objects.get(pk=profile_id).permission == permission


class TestCoreSignalsPostLogin(TestCase):
    """Testing class for :py:mod:`core.signals` post_login function."""

    # # post_login
    @pytest.mark.django_db
    def test_core_signals_post_login_for_not_authorized(self):
        user = user_model.objects.create(
            email="not_authorized@testprofile.com",
            username="not_authorized",
        )
        user.set_password("12345o")
        user.save()
        user.profile.address = TEST_ADDRESS
        user.profile.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            self.client.login(username="not_authorized", password="12345o")
            mocked_provider.assert_not_called()

    @pytest.mark.django_db
    def test_core_signals_post_login_functionality(self):
        user = user_model.objects.create(
            email="post_login@testprofile.com",
            username="post_login",
        )
        user.set_password("12345o")
        user.save()
        user.profile.address = TEST_ADDRESS
        user.profile.authorized = "authorized"
        user.profile.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="post_login", password="12345o")
            mocked_provider.return_value.votes_and_permission.assert_called_once_with(
                TEST_ADDRESS
            )
