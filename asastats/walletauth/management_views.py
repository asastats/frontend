"""Authenticated address-management endpoints.

``manage/nonce/`` issues a step-up challenge bound to the caller's current
primary address. ``manage/`` dispatches the operations: ``set_primary`` and
enabling login require a fresh signature from the current primary (step-up,
verified here); disabling login and removing a secondary need only the session.
Every operation is strictly scoped to the caller's own addresses.
"""

import logging
from secrets import token_hex

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from walletauth.management import (
    CannotDisablePrimaryLogin,
    CannotRemovePrimary,
    remove_address,
    set_login_enabled,
    set_primary,
)
from walletauth.models import LinkedAddress, WalletNonce
from walletauth.throttling import WalletAuthRateThrottle
from walletauth.verifiers import VERIFIERS, NotSupported

logger = logging.getLogger(__name__)


def _normalized(chain, address):
    """Return the address in comparison form (EVM is case-folded)."""
    return address.lower() if chain == "evm" else address


def _current_primary(profile):
    """Return the profile's primary LinkedAddress, or None."""
    return profile.linked_addresses.filter(is_primary=True).first()


class ManageNonceAPIView(APIView):
    """Issue a step-up challenge to be signed by the current primary wallet."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [WalletAuthRateThrottle]

    def post(self, request, *args, **kwargs):
        """Create a nonce bound to the caller's primary address.

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


class ManageAddressAPIView(APIView):
    """Dispatch a management operation on one of the caller's linked addresses."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [WalletAuthRateThrottle]

    OPERATIONS = {"set_primary", "set_login", "remove"}

    def post(self, request, *args, **kwargs):
        """Validate, enforce step-up where required, and perform the operation.

        :param request: the authenticated request carrying ``operation`` and
            ``target_id`` (plus ``enabled`` for ``set_login`` and a step-up
            ``nonce``/signature for privilege-expanding operations)
        :type request: rest_framework.request.Request
        :var target: the caller's own row the operation acts on
        :type target: walletauth.models.LinkedAddress
        :return: a JSON result, or an error response
        :rtype: rest_framework.response.Response
        """
        operation = request.data.get("operation")
        if operation not in self.OPERATIONS:
            return Response(
                {"success": False, "error": "Unknown operation"}, status=400
            )

        profile = request.user.profile
        try:
            target = profile.linked_addresses.get(id=request.data.get("target_id"))
        except (LinkedAddress.DoesNotExist, ValueError, TypeError):
            # Not found, or not owned by the caller: same answer, no oracle.
            return Response(
                {"success": False, "error": "Address not found"}, status=404
            )

        enabled = bool(request.data.get("enabled"))
        # Expanding access (promoting a primary, minting a login credential)
        # requires proof of the current primary key; reducing surface does not.
        if operation == "set_primary" or (operation == "set_login" and enabled):
            error = self._verify_step_up(request)
            if error is not None:
                return error

        if operation == "set_primary":
            refreshed = set_primary(profile, target)
            return Response({"success": True, "permission_pending": not refreshed})

        if operation == "set_login":
            try:
                set_login_enabled(profile, target, enabled)
            except CannotDisablePrimaryLogin as exc:
                return Response({"success": False, "error": str(exc)}, status=400)
            return Response({"success": True, "login_enabled": enabled})

        try:
            remove_address(profile, target)
        except CannotRemovePrimary as exc:
            return Response({"success": False, "error": str(exc)}, status=400)
        return Response({"success": True})

    def _verify_step_up(self, request):
        """Verify a fresh signature from the current primary, or return an error.

        :param request: request carrying ``nonce`` and the signature payload
        :type request: rest_framework.request.Request
        :var proven: address the step-up signature proves control of
        :type proven: str | None
        :return: an error ``Response`` when step-up fails, else ``None``
        :rtype: rest_framework.response.Response | None
        """
        primary = _current_primary(request.user.profile)
        if primary is None:
            return Response(
                {"success": False, "error": "No primary address"}, status=400
            )
        nonce_str = request.data.get("nonce")
        if not nonce_str:
            return Response(
                {"success": False, "error": "Missing step-up signature"}, status=400
            )

        verifier = VERIFIERS.get(primary.chain)
        if verifier is None:
            return Response(
                {"success": False, "error": "Unsupported chain"}, status=400
            )
        try:
            proven = verifier.recover(
                nonce=nonce_str,
                prefix=WALLET_CONNECT_NONCE_PREFIX,
                payload=request.data,
            )
        except NotSupported as exc:
            return Response({"success": False, "error": str(exc)}, status=400)

        if not proven or _normalized(primary.chain, proven) != _normalized(
            primary.chain, primary.address
        ):
            return Response(
                {
                    "success": False,
                    "error": "Step-up signature did not match your primary address",
                },
                status=401,
            )

        try:
            nonce_obj = WalletNonce.objects.get(
                nonce=nonce_str,
                address=primary.address,
                user=request.user,
                chain=primary.chain,
                used=False,
            )
        except WalletNonce.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Step-up challenge not found or already used",
                },
                status=400,
            )
        if nonce_obj.is_expired() or not nonce_obj.claim():
            return Response(
                {
                    "success": False,
                    "error": "Step-up challenge expired or already used",
                },
                status=400,
            )
        return None
