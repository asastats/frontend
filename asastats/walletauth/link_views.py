"""Wallet *linking* (authorize) for connect-and-store chains (EVM/xChain).

Unlike the Algorand authorize in :mod:`walletauth.views`, which proves control
of the address ALREADY on the profile, linking recovers the address from the
signature and STORES it on the authenticated user's profile. It is used for EVM,
where the user connects a wallet rather than pre-entering an address.

Both endpoints are session-authenticated and require an authenticated user. The
stored address is always the address the signature proves, never one the client
merely names, so a client cannot link an address it does not control.
"""

import logging
from secrets import token_hex

from django.urls import reverse
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from walletauth.login_views import is_valid_chain_address
from walletauth.models import WalletNonce
from walletauth.throttling import WalletAuthRateThrottle
from walletauth.verifiers import AUTH_METHOD_BY_CHAIN, VERIFIERS, NotSupported

logger = logging.getLogger(__name__)

#: Chains that link by recover-and-store. Algorand uses the prove-existing
#: authorize flow in :mod:`walletauth.views`; EVM connects and stores.
LINKABLE_CHAINS = {"evm"}


def _normalized(chain, address):
    """Return the address in the canonical stored form for ``chain``.

    :param chain: request chain identifier
    :type chain: str
    :param address: address to normalize
    :type address: str
    :return: normalized address (lowercased for EVM, unchanged otherwise)
    :rtype: str
    """
    return address.lower() if chain == "evm" else address


class WalletLinkNonceAPIView(APIView):
    """Issue a single-use challenge for linking a connected wallet."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [WalletAuthRateThrottle]

    def post(self, request, *args, **kwargs):
        """Create a user-bound nonce for the claimed wallet address.

        :param request: incoming HTTP request carrying ``address`` and ``chain``
        :type request: rest_framework.request.Request
        :var address: claimed wallet address from the connected wallet
        :type address: str
        :var chain: link chain (default ``"evm"``)
        :type chain: str
        :var nonce: freshly generated single-use challenge
        :type nonce: str
        :return: JSON ``{"nonce": str, "prefix": str}``
        :rtype: rest_framework.response.Response
        """
        address = (request.data.get("address") or "").strip()
        chain = request.data.get("chain", "evm")

        if chain not in LINKABLE_CHAINS:
            return Response(
                {"success": False, "error": "Unsupported chain"}, status=400
            )
        if not address or not is_valid_chain_address(chain, address):
            return Response(
                {"success": False, "error": "Invalid or missing address"}, status=400
            )

        address = _normalized(chain, address)
        nonce = token_hex(16)
        WalletNonce.objects.create(
            user=request.user, address=address, nonce=nonce, chain=chain
        )
        return Response({"nonce": nonce, "prefix": WALLET_CONNECT_NONCE_PREFIX})


class WalletLinkVerifyAPIView(APIView):
    """Verify a link proof and store the recovered address on the profile."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [WalletAuthRateThrottle]

    def post(self, request, *args, **kwargs):
        """Verify the proof and stamp the recovered address onto the profile.

        :param request: incoming request carrying ``nonce``, ``chain`` and proof
        :type request: rest_framework.request.Request
        :var chain: link chain (default ``"evm"``)
        :type chain: str
        :var nonce_str: the challenge being redeemed
        :type nonce_str: str
        :var proven: address the signature proves control of
        :type proven: str | None
        :var nonce_obj: the matching unused, user-bound nonce
        :type nonce_obj: walletauth.models.WalletNonce
        :var profile: the authenticated user's profile
        :type profile: core.models.Profile
        :var refreshed: whether the permission value refreshed in-band
        :type refreshed: bool
        :return: JSON ``{success, redirect_url, permission_pending}`` or an error
        :rtype: rest_framework.response.Response
        """
        chain = request.data.get("chain", "evm")
        nonce_str = request.data.get("nonce")

        if not nonce_str:
            return Response({"success": False, "error": "Missing nonce"}, status=400)
        if chain not in LINKABLE_CHAINS:
            return Response(
                {"success": False, "error": "Unsupported chain"}, status=400
            )

        verifier = VERIFIERS.get(chain)
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
        if not proven:
            return Response(
                {"success": False, "error": "Signature verification failed"}, status=400
            )

        try:
            nonce_obj = WalletNonce.objects.get(
                nonce=nonce_str,
                address=proven,
                user=request.user,
                chain=chain,
                used=False,
            )
        except WalletNonce.DoesNotExist:
            return Response(
                {"success": False, "error": "Nonce not found or already used"},
                status=400,
            )
        if nonce_obj.is_expired():
            return Response({"success": False, "error": "Nonce expired"}, status=400)
        if not nonce_obj.claim():
            return Response(
                {"success": False, "error": "Nonce already used"}, status=400
            )

        profile = request.user.profile
        # Persist the new address first: Profile.save() clears ``authorized`` when
        # the address changes, so update_authorized must run afterwards with the
        # address already in place, or the fresh authorization would be wiped.
        profile.address = proven
        profile.save()
        refreshed = profile.update_authorized(
            nonce_obj.nonce, method=AUTH_METHOD_BY_CHAIN.get(chain, "evm_xchain")
        )
        logger.info(
            "walletauth: %s wallet linked (permission_pending=%s)",
            chain,
            not refreshed,
        )

        return Response(
            {
                "success": True,
                "redirect_url": reverse("profile"),
                "permission_pending": not refreshed,
            }
        )
