"""Swap-gate endpoint.

Returns which of the queried addresses are connected to the caller, so a
front-end widget can decide whether to render a Swap button. Self-scoped:
anonymous callers (and addresses belonging to other accounts) yield nothing.
"""

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from walletauth.gating import linked_addresses_for_user


class SwapGateAPIView(APIView):
    """Report which browsed addresses are connected to the current user."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Return the subset of the requested addresses linked to the caller.

        Accepts ``{"addresses": [...]}`` or a single ``{"address": "..."}``.
        Anonymous callers always receive an empty set.

        :param request: the request carrying the address(es) to test
        :type request: rest_framework.request.Request
        :var addresses: the browsed addresses to check
        :type addresses: list[str]
        :return: JSON ``{"linked": [...]}`` (sorted subset that is connected)
        :rtype: rest_framework.response.Response
        """
        addresses = request.data.get("addresses")
        if addresses is None:
            single = request.data.get("address")
            addresses = [single] if single else []
        if not isinstance(addresses, list):
            return Response(
                {"success": False, "error": "addresses must be a list"}, status=400
            )

        linked = linked_addresses_for_user(request.user, addresses)
        return Response({"linked": sorted(linked)})
