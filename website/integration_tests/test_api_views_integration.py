"""Integration testing module for :py:mod:`api.views` module."""

import json
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from api.data import (
    API_EXAMPLE_ADDRESS1,
    API_EXAMPLE_ADDRESS2,
    API_EXAMPLE_BUNDLE1,
    API_EXAMPLE_BUNDLE2,
    API_EXAMPLE_NFD_NAME1,
    API_EXAMPLE_NFD_NAME2,
)



def user_for_widgets_token():
    """Return a user the `WIDGETS_API_TOKEN` will actually resolve to.

    **The auth class stopped trusting the token's claims.**
    `JWTStatelessUserAuthentication` built a user out of the claims and never
    touched the database, so any `user_id` resolved. `JWTAuthentication` looks it
    up - which is the whole point, since a tier cannot be read off a token - and
    a token naming a user who is not there is a 401.

    Creating the user with an auto primary key made the first test in a class
    pass and every later one fail: the sequence keeps climbing across tests
    while the token keeps naming the same id, so only the first ever matched.
    Reading the id out of the credential and creating *that* user tests the
    credential production actually uses, rather than a convenient substitute.
    """
    import base64
    import json

    from django.conf import settings
    from django.contrib.auth.models import User

    payload = settings.WIDGETS_API_TOKEN.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    user_id = json.loads(base64.urlsafe_b64decode(payload))["user_id"]
    user, _ = User.objects.get_or_create(
        pk=int(user_id), defaults={"email": f"{uuid.uuid4()}@email.com"}
    )
    return user

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


class TestSetup(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = user_for_widgets_token()
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {settings.WIDGETS_API_TOKEN}"
        )


class TestApiV2IntegrationRawPostJson(TestSetup):
    def test_api_v2_integration_raw_post_address_json(self):
        response = self.client.post(
            "/api/v2/",
            json.dumps({"addresses": API_EXAMPLE_ADDRESS1}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert response.data == {"bundle": API_EXAMPLE_ADDRESS1}

    def test_api_v2_integration_raw_post_addresses_json(self):
        response = self.client.post(
            "/api/v2/",
            json.dumps({"addresses": f"{API_EXAMPLE_ADDRESS1} {API_EXAMPLE_ADDRESS2}"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert response.data == {"bundle": API_EXAMPLE_BUNDLE1}

    def test_api_v2_integration_raw_post_addresses_and_nfd_names_json(self):
        response = self.client.post(
            "/api/v2/",
            json.dumps(
                {
                    "addresses": (
                        f"{API_EXAMPLE_ADDRESS1}_{API_EXAMPLE_NFD_NAME1},"
                        f"{API_EXAMPLE_ADDRESS2};{API_EXAMPLE_NFD_NAME2}"
                    )
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert response.data == {"bundle": API_EXAMPLE_BUNDLE2}


class TestApiV2IntegrationRawPostXml(TestSetup):
    def test_api_v2_integration_raw_post_address_xml(self):
        response = self.client.post(
            "/api/v2/",
            (
                f"<AddressesInput><addresses>{API_EXAMPLE_ADDRESS1}"
                f"</addresses></AddressesInput>"
            ),
            content_type="application/xml",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert response.data == {"bundle": API_EXAMPLE_ADDRESS1}

    def test_api_v2_integration_raw_post_addresses_xml(self):
        response = self.client.post(
            "/api/v2/",
            (
                f"<AddressesInput><addresses>{API_EXAMPLE_ADDRESS1}_"
                f"{API_EXAMPLE_ADDRESS2}</addresses></AddressesInput>"
            ),
            content_type="application/xml",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert response.data == {"bundle": API_EXAMPLE_BUNDLE1}

    def test_api_v2_integration_raw_post_addresses_and_nfd_names_xml(self):
        response = self.client.post(
            "/api/v2/",
            (
                f"<AddressesInput><addresses>"
                f"{API_EXAMPLE_ADDRESS1}_{API_EXAMPLE_NFD_NAME1},"
                f"{API_EXAMPLE_ADDRESS2},{API_EXAMPLE_NFD_NAME2}"
                f"</addresses></AddressesInput>"
            ),
            content_type="application/xml",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert response.data == {"bundle": API_EXAMPLE_BUNDLE2}


class TestApiV2IntegrationRawPostYaml(TestSetup):
    def test_api_v2_integration_raw_post_address_yaml(self):
        response = self.client.post(
            "/api/v2/",
            f"addresses: {API_EXAMPLE_ADDRESS1}",
            content_type="application/yaml",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert response.data == {"bundle": API_EXAMPLE_ADDRESS1}

    def test_api_v2_integration_raw_post_addresses_yaml(self):
        response = self.client.post(
            "/api/v2/",
            f"addresses: {API_EXAMPLE_ADDRESS1};{API_EXAMPLE_ADDRESS2}",
            content_type="application/yaml",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert response.data == {"bundle": API_EXAMPLE_BUNDLE1}

    def test_api_v2_integration_raw_post_addresses_and_nfd_names_yaml(self):
        response = self.client.post(
            "/api/v2/",
            (
                f"addresses: {API_EXAMPLE_ADDRESS1},{API_EXAMPLE_NFD_NAME1},"
                f"{API_EXAMPLE_ADDRESS2},{API_EXAMPLE_NFD_NAME2}"
            ),
            content_type="application/yaml",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert response.data == {"bundle": API_EXAMPLE_BUNDLE2}
