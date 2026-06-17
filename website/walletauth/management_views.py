"""Authenticated step-up challenge endpoint.

``manage/nonce/`` issues a single-use challenge bound to the caller's current
primary address; the browser signs it with the primary wallet to authorize a
privilege-expanding change. The signature is verified (and bound to the specific
operation) server-side by :func:`walletauth.management.verify_step_up`, which
the htmx management view calls. The address list and the operations themselves
are rendered/handled as server HTML (htmx), so there is no JSON manage API.
"""

import logging
from secrets import token_hex

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from walletauth.management import _current_primary
from walletauth.models import WalletNonce
from walletauth.throttling import WalletAuthRateThrottle

logger = logging.getLogger(__name__)


class ManageNonceAPIView(APIView):
    """Issue a step-up challenge to be signed by the current primary wallet."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [WalletAuthRateThrottle]

    def post(self, request, *args, **kwargs):
        """Create a nonce bound to the caller's primary address.

        The browser composes the operation-bound challenge
        (``prefix + "{nonce}:{operation}:{target_id}"``) before signing, so the
        nonce itself carries no operation; binding is enforced at verification.

        :param request: the authenticated request
        :type request: rest_framework.request.Request
        :return: ``{nonce, prefix, address, chain}`` for the primary to sign
        :rtype: rest_framework.response.Response
        """
        primary = _current_primary(request.user.profile)
        if primary is None:
            return Response(
                {"success": False, "error": "No primary address to authorize with"},
                status=400,
            )
        nonce = token_hex(16)
        WalletNonce.objects.create(
            user=request.user,
            address=primary.address,
            nonce=nonce,
            chain=primary.chain,
        )
        return Response(
            {
                "nonce": nonce,
                "prefix": WALLET_CONNECT_NONCE_PREFIX,
                "address": primary.address,
                "chain": primary.chain,
            }
        )
