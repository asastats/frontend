"""Vestige-compatible price endpoints: Vestige's requests and response shapes.

Reasons and what "compatible" covers: docs/logbook.md.

:var VESTIGE_QUOTES: engine quote by Vestige denominating asset
:type VESTIGE_QUOTES: dict
:var VESTIGE_PATHS: Vestige paths served, as (path regex, view name, URL name)
:type VESTIGE_PATHS: tuple
"""

import logging

from django.core.cache import cache
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from api import client
from api.serializers import VestigeAssetPriceSerializer
from utils.constants.apiv2 import (
    VESTIGE_ASSET_PRICES_DESCRIPTION,
    VESTIGE_ASSET_PRICES_PARAMETERS,
    VESTIGE_MAX_ASSET_ID,
    VESTIGE_MAX_ASSETS,
    VESTIGE_PRICE_CACHE_SECONDS,
    VESTIGE_TAG,
)

logger = logging.getLogger(__name__)

ALGO_ID = 0
USDC_ID = 31566704
VESTIGE_QUOTES = {ALGO_ID: "algo", USDC_ID: "usd"}
#: Trailing slash optional: Vestige's own paths have none.
VESTIGE_PATHS = (
    (r"^assets/price/?$", "VestigeAssetPricesView", "api_vestige_asset_prices"),
)


class VestigeRateThrottle(SimpleRateThrottle):
    """Per-IP throttle of the Vestige-compatible endpoints, which take no key.

    :var VestigeRateThrottle.scope: throttle scope key for the rate lookup
    :type VestigeRateThrottle.scope: str
    """

    scope = "vestige"

    def get_cache_key(self, request, view):
        """Return the cache key of the caller's address.

        :param request: incoming DRF request
        :type request: :class:`rest_framework.request.Request`
        :param view: view being throttled
        :type view: :class:`rest_framework.views.APIView`
        :return: str
        """
        # nginx sets X-Real-IP itself; X-Forwarded-For carries what the client sent
        return self.cache_format % {
            "scope": self.scope,
            "ident": request.META.get("HTTP_X_REAL_IP")
            or request.META.get("REMOTE_ADDR", ""),
        }


def _refused(status_code, detail):
    """Return a refusal in Vestige's shape.

    :param status_code: HTTP status
    :type status_code: int
    :param detail: Vestige's message, or FastAPI's list of validation errors
    :type detail: str or list
    :return: :class:`rest_framework.response.Response`
    """
    return Response({"detail": detail}, status=status_code)


def _whole_number(raw):
    """Return True if `raw` is a non-negative whole number of sensible length.

    :param raw: value as sent
    :type raw: str
    :return: Boolean
    """
    return raw.isascii() and raw.isdecimal() and len(raw) <= 20


def _integer_parameter(params, name):
    """Return query parameter `name` as (value, refusal), 0 when it is absent.

    :param params: request's query parameters
    :type params: :class:`django.http.QueryDict`
    :param name: parameter's name
    :type name: str
    :var raw: value as sent
    :type raw: str
    :return: two-tuple: int or None, :class:`rest_framework.response.Response` or None
    """
    raw = params.get(name)
    if raw is None:
        return 0, None

    if not _whole_number(raw.strip()):
        return None, _refused(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "int_parsing",
                    "loc": ["query", name],
                    "msg": "Input should be a valid integer, "
                    "unable to parse string as an integer",
                    "input": raw,
                }
            ],
        )

    return int(raw), None


def _vestige_price(entry, denominating_asset_id):
    """Return one engine price entry as Vestige's price object.

    An asset without a price is zeros, as it is at Vestige.

    :param entry: engine's latest price of an asset
    :type entry: dict
    :param denominating_asset_id: 0 for ALGO or USDC's identifier
    :type denominating_asset_id: int
    :return: dict
    """
    # key order is Vestige's
    return {
        "network_id": 0,
        "asset_id": entry["asset_id"],
        "denominating_asset_id": denominating_asset_id,
        "price": float(entry.get("price") or 0.0),
        "confidence": 1.0 if entry.get("price") else 0.0,
        "total_lockup": float(entry.get("lockup") or 0.0),
    }


class VestigeView(APIView):
    """Base of the Vestige-compatible views: no key, JSON only, any origin.

    :var authentication_classes: none, a token sent is not looked at
    :type authentication_classes: tuple
    :var permission_classes: collection of DRF permission classes
    :type permission_classes: tuple
    :var throttle_classes: collection of DRF throttle classes
    :type throttle_classes: tuple
    :var renderer_classes: collection of DRF renderer classes
    :type renderer_classes: tuple
    """

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (VestigeRateThrottle,)
    renderer_classes = (JSONRenderer,)

    def get_throttles(self):
        """Return the request's throttles, kept for the response's headers.

        :return: list
        """
        self.throttles = super().get_throttles()
        return self.throttles

    def finalize_response(self, request, response, *args, **kwargs):
        """Add the CORS header and Vestige's rate limit headers to `response`.

        :param request: incoming DRF request
        :type request: :class:`rest_framework.request.Request`
        :param response: view's response
        :type response: :class:`rest_framework.response.Response`
        :var throttle: request's throttle, if it got as far as being checked
        :type throttle: :class:`VestigeRateThrottle` or None
        :return: :class:`rest_framework.response.Response`
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Access-Control-Allow-Origin"] = "*"
        throttle = next(iter(getattr(self, "throttles", ())), None)
        if throttle is not None and getattr(throttle, "num_requests", None):
            response["X-RateLimit-Limit"] = str(throttle.num_requests)
            response["X-RateLimit-Remaining"] = str(
                max(throttle.num_requests - len(getattr(throttle, "history", ())), 0)
            )

        return response


@extend_schema_view(
    get=extend_schema(
        operation_id="VestigeAssetPrices",
        summary="Current asset prices, in Vestige's format",
        description=VESTIGE_ASSET_PRICES_DESCRIPTION,
        parameters=VESTIGE_ASSET_PRICES_PARAMETERS,
        responses={200: VestigeAssetPriceSerializer(many=True)},
        auth=[],
        tags=[VESTIGE_TAG],
    )
)
class VestigeAssetPricesView(VestigeView):
    """Vestige's `GET /assets/price`: the current price of each listed asset."""

    def get(self, request):
        """Return a bare array with one price object per asset, in request order.

        :param request: incoming DRF request
        :type request: :class:`rest_framework.request.Request`
        :var parts: asset identifiers as sent
        :type parts: list
        :var key: cache key of this exact request
        :type key: str
        :var prices: Vestige price objects
        :type prices: list
        :return: :class:`rest_framework.response.Response`
        """
        params = request.query_params
        if params.get("asset_ids") is None:
            return _refused(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                [
                    {
                        "type": "missing",
                        "loc": ["query", "asset_ids"],
                        "msg": "Field required",
                        "input": None,
                    }
                ],
            )

        network_id, refusal = _integer_parameter(params, "network_id")
        if refusal is None:
            denominating, refusal = _integer_parameter(params, "denominating_asset_id")

        if refusal is not None:
            return refusal

        parts = [part.strip() for part in params["asset_ids"].split(",")]
        if not all(
            _whole_number(part) and int(part) <= VESTIGE_MAX_ASSET_ID for part in parts
        ):
            return _refused(status.HTTP_400_BAD_REQUEST, "Invalid asset list")

        if len(parts) > VESTIGE_MAX_ASSETS:
            return _refused(status.HTTP_406_NOT_ACCEPTABLE, "Too many assets")

        if network_id != 0:
            return _refused(status.HTTP_400_BAD_REQUEST, "Unsupported network")

        if denominating not in VESTIGE_QUOTES:
            return _refused(
                status.HTTP_400_BAD_REQUEST,
                "Unsupported denominating asset; use 0 (ALGO) or 31566704 (USDC)",
            )

        key = f"vestige:price:{denominating}:{','.join(str(int(p)) for p in parts)}"
        prices = cache.get(key)
        if prices is None:
            try:
                prices = [
                    _vestige_price(entry, denominating)
                    for entry in client.prices_latest(
                        [int(part) for part in parts], VESTIGE_QUOTES[denominating]
                    )
                ]
            except client.BackendError as error:
                logger.error("Vestige prices: the engine refused or failed: %s", error)
                return _refused(
                    status.HTTP_503_SERVICE_UNAVAILABLE, "Price service unavailable"
                )

            cache.set(key, prices, VESTIGE_PRICE_CACHE_SECONDS)

        return Response(prices)
