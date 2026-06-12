"""Module containing views for wallet address authorization.

Unlike the Rewards Suite, these endpoints do NOT log a user in. The user is
already authenticated via allauth; a successful verify *authorizes* an address
onto ``request.user.profile``. Both endpoints are therefore session
authenticated and require an authenticated user, and they operate strictly on
the address already stored on the user's profile.
"""

import logging
from secrets import token_hex

from algosdk.encoding import is_valid_address
from django.urls import reverse
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.constants.core import (
    ALGORAND_WALLETS,
    WALLET_CONNECT_NONCE_PREFIX,
)
from walletauth.models import WalletNonce
from walletauth.verifiers import AUTH_METHOD_BY_CHAIN, VERIFIERS, NotSupported

logger = logging.getLogger(__name__)


class WalletsAPIView(APIView):
    """Return the list of supported Algorand wallets for the frontend."""

    def get(self, request, *args, **kwargs):
        """Return supported wallets as ``[{"id", "name"}, ...]``.

        :param request: incoming HTTP request
        :type request: :class:`rest_framework.request.Request`
        :return: JSON list of supported wallet descriptors
        :rtype: :class:`rest_framework.response.Response`
        """
        return Response(ALGORAND_WALLETS)


class WalletNonceAPIView(APIView):
    """Issue a single-use challenge bound to the authenticated user's address."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Create a nonce for the profile's own address.

        Expected JSON: ``{"address": str, "chain": str?}``. ``address`` must
        match the address already on the user's profile.

        :param request: incoming HTTP request
        :type request: :class:`rest_framework.request.Request`
        :var address: address submitted for authorization
        :type address: str
        :var chain: target chain, defaulting to ``"algorand"``
        :type chain: str
        :var profile_address: address already stored on the user's profile
        :type profile_address: str
        :var nonce: freshly generated single-use challenge
        :type nonce: str
        :return: JSON ``{"nonce": str, "prefix": str}``
        :rtype: :class:`rest_framework.response.Response`
        """
        address = (request.data.get("address") or "").strip()
        chain = request.data.get("chain", "algorand")

        if not is_valid_address(address):
            return Response({"error": "Invalid or missing address"}, status=400)

        profile_address = request.user.profile.address
        if not profile_address or address != profile_address:
            return Response(
                {"error": "Address does not match your profile address"}, status=400
            )

        if chain not in VERIFIERS:
            return Response({"error": "Unsupported chain"}, status=400)

        nonce = token_hex(16)
        WalletNonce.objects.create(
            user=request.user, address=address, nonce=nonce, chain=chain
        )
        return Response({"nonce": nonce, "prefix": WALLET_CONNECT_NONCE_PREFIX})


class WalletVerifyAPIView(APIView):
    """Verify a signed challenge and authorize the address on the profile."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Verify the proof and stamp ``profile`` on success.

        Expected JSON: ``{"nonce": str, "chain": str?, ...proof fields}``. The
        address is taken from the profile, never from the request body, so a
        client cannot authorize an address it has not set on its own profile.

        :param request: incoming HTTP request
        :type request: :class:`rest_framework.request.Request`
        :var profile: the authenticated user's profile
        :type profile: :class:`core.models.Profile`
        :var address: address being authorized, read from the profile
        :type address: str
        :var nonce_str: challenge value submitted by the client
        :type nonce_str: str
        :var chain: target chain, defaulting to ``"algorand"``
        :type chain: str
        :var verifier: chain-specific proof verifier
        :type verifier: :class:`walletauth.verifiers.WalletProofVerifier`
        :var nonce_obj: the matching unused, user-bound nonce
        :type nonce_obj: :class:`walletauth.models.WalletNonce`
        :var proven: proven Algorand address returned by the verifier
        :type proven: str | None
        :return: JSON ``{"success": bool, "redirect_url": str}``
        :rtype: :class:`rest_framework.response.Response`
        """
        profile = request.user.profile
        address = profile.address
        nonce_str = request.data.get("nonce")
        chain = request.data.get("chain", "algorand")

        if not address or not is_valid_address(address):
            return Response(
                {"success": False, "error": "Your profile has no valid address"},
                status=400,
            )
        if not nonce_str:
            return Response({"success": False, "error": "Missing nonce"}, status=400)

        verifier = VERIFIERS.get(chain)
        if verifier is None:
            return Response(
                {"success": False, "error": "Unsupported chain"}, status=400
            )

        try:
            nonce_obj = WalletNonce.objects.get(
                nonce=nonce_str, address=address, user=request.user, used=False
            )
        except WalletNonce.DoesNotExist:
            logger.warning("walletauth: nonce not found or used for an authenticated user")
            return Response(
                {"success": False, "error": "Nonce not found or already used"},
                status=400,
            )

        if nonce_obj.is_expired():
            return Response({"success": False, "error": "Nonce expired"}, status=400)

        try:
            proven = verifier.verify(
                address=address,
                nonce=nonce_str,
                prefix=WALLET_CONNECT_NONCE_PREFIX,
                payload=request.data,
            )
        except NotSupported as exc:
            return Response({"success": False, "error": str(exc)}, status=400)

        if not proven or proven != address:
            return Response(
                {"success": False, "error": "Signature verification failed"},
                status=400,
            )

        nonce_obj.mark_used()
        profile.update_authorized(
            nonce_obj.nonce, method=AUTH_METHOD_BY_CHAIN.get(chain, "algorand_wallet")
        )
        logger.info("walletauth: address authorized via %s wallet", chain)

        # Always redirect to the profile page; never honor a client-supplied
        # next target, to avoid open-redirect.
        return Response({"success": True, "redirect_url": reverse("profile")})
