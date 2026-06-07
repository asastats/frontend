"""Module containing classes and functions for accessing API through widgets system."""

import requests
from algosdk.constants import ADDRESS_LEN
from django.conf import settings

from api.helpers import validate_bundle
from utils.constants.apiv2 import BASE_API_URL
from utils.helpers import check_bundle_addresses, create_bundle


class BearerAuth(requests.auth.AuthBase):
    """Requests auth class adding the widgets API bearer token to a request."""

    def __call__(self, r):
        """Attach the widgets API bearer token to the request's headers.

        :param r: prepared request the authorization header is added to
        :type r: :class:`requests.PreparedRequest`
        :return: :class:`requests.PreparedRequest`
        """
        r.headers["authorization"] = "Bearer " + settings.WIDGETS_API_TOKEN
        return r


def bundle_and_addresses_from_path(url_path, force_bundle=True):
    """Return bundle and Algorand addresses defined by provided `url_path`.

    :param url_path: address or bundle value found in URL
    :type url_path: str
    :var bundle: hash made from public Algorand addresses
    :type bundle: str
    :var addresses: space separated collection of public Algorand addresses
    :type addresses: str
    :return: two-tuple
    """
    bundle = validate_bundle(url_path)
    if len(bundle) == ADDRESS_LEN:
        addresses = bundle
        if force_bundle:
            bundle = create_bundle(addresses)

    else:
        addresses = check_bundle_addresses(bundle)

    return bundle, addresses


def widgets_api_view(endpoint, filter=""):
    """Fetch and return decoded JSON from a widgets API `endpoint`.

    :param endpoint: API endpoint path segment to request
    :type endpoint: str
    :param filter: optional query string appended to the request URL
    :type filter: str
    :var api_url: fully qualified URL the request is sent to
    :type api_url: str
    :var response: HTTP response returned by the widgets API
    :type response: :class:`requests.Response`
    :return: dict
    """
    api_url = f"{BASE_API_URL}{endpoint}/"
    if filter:
        api_url += "?" + filter
    response = requests.get(api_url, auth=BearerAuth())
    return response.json()
