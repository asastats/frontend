"""Wallet *sign-in* endpoints.

Unlike the authorize views in :mod:`walletauth.views`, these LOG A USER IN. A
successful proof resolves the account that previously linked the proven address
(via the authorize flow) and establishes an allauth session. No account is ever
created here -- an unlinked address is rejected.

The flow is chain-agnostic by construction: :meth:`WalletProofVerifier.recover`
returns the proven address, the account is resolved from that address (never
from the request body), and EVM/xChain sign-in slots in by enabling its verifier
and account resolver.
"""

import logging
import re
from secrets import token_hex

from algosdk.encoding import is_valid_address as is_valid_algorand_address
from django.conf import settings
from django.contrib.auth import authenticate
from django.shortcuts import resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.constants.core import (
    WALLET_CONNECT_NETWORK_OPTIONS,
    WALLET_CONNECT_NONCE_PREFIX,
)
from walletauth.account_resolution import AmbiguousWalletAddress
from walletauth.models import WalletLoginNonce
from walletauth.throttling import WalletLoginRateThrottle
from walletauth.verifiers import VERIFIERS, NotSupported

logger = logging.getLogger(__name__)

#: Basic EVM address shape, used to validate a login-nonce request before the
#: EVM verifier exists. Algorand uses algosdk's checksum-aware validator.
_EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def is_valid_chain_address(chain, address):
    """Return whether ``address`` is well-formed for ``chain``.

    :param chain: request chain identifier
    :type chain: str
    :param address: address to validate
    :type address: str
    :return: Boolean
    """
    if chain == "algorand":
        return is_valid_algorand_address(address)
    if chain == "evm":
        return bool(_EVM_ADDRESS_RE.match(address))
    return False


def _perform_login(request, user):
    """Establish an allauth session for ``user`` and return its redirect URL.

    Imported lazily and wrapped so the login policy (e.g. mandatory email
    verification) stays allauth's concern and the module imports without
    side effects. The redirect is allauth's normal post-login destination --
    the configured ``LOGIN_REDIRECT_URL`` (``/home/``), honoring ``next`` --
    exactly as for email/password and social sign-in. (This differs from the
    authorize flow, which deliberately returns the user to their profile.)

    :param request: the current request
    :type request: django.http.HttpRequest
    :param user: the authenticated user (carries ``user.backend``)
    :type user: django.contrib.auth.models.User
    :return: URL allauth routes the user to after login
    :rtype: str
    """
    from allauth.account import app_settings as account_settings
    from allauth.account.utils import perform_login

    response = perform_login(
        request,
        user,
        email_verification=account_settings.EMAIL_VERIFICATION,
    )
    return getattr(response, "url", None) or resolve_url(settings.LOGIN_REDIRECT_URL)


def _safe_next(request):
    """Return a same-origin ``next`` from the request body, or ``None``.

    The client may send ``next`` in the verify payload (the swap URL the user was
    heading to). It is validated here — never trusted — so an unlinked/off-site
    target can't turn wallet sign-in into an open redirect.

    :param request: the current request
    :type request: rest_framework.request.Request
    :return: a safe local redirect target, or None
    :rtype: str | None
    """
    target = (request.data.get("next") or "").strip()
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target

    return None


class WalletLoginNonceAPIView(APIView):
    """Issue a single-use sign-in challenge for a claimed address."""

    permission_classes = [AllowAny]
    throttle_classes = [WalletLoginRateThrottle]

    def post(self, request, *args, **kwargs):
        """Create and return a login nonce for ``address`` on ``chain``.

        :param request: incoming request carrying ``address`` and ``chain``
        :type request: rest_framework.request.Request
        :var address: claimed wallet address the challenge is bound to
        :type address: str
        :var chain: request chain (default ``"algorand"``)
        :type chain: str
        :return: JSON ``{nonce, prefix, network}``
        :rtype: rest_framework.response.Response
        """
        address = (request.data.get("address") or "").strip()
        chain = request.data.get("chain", "algorand")
        if chain not in VERIFIERS:
            return Response(
                {"success": False, "error": "Unsupported chain"}, status=400
            )
        if not address or not is_valid_chain_address(chain, address):
            return Response(
                {"success": False, "error": "Invalid or missing address"}, status=400
            )
        # EVM addresses are case-insensitive; store lowercase so the nonce binds
        # to the same form the verifier recovers. Algorand base32 is left as-is.
        if chain == "evm":
            address = address.lower()

        WalletLoginNonce.purge_stale()
        nonce = token_hex(16)
        WalletLoginNonce.objects.create(address=address, chain=chain, nonce=nonce)
        return Response(
            {
                "nonce": nonce,
                "prefix": WALLET_CONNECT_NONCE_PREFIX,
                "network": WALLET_CONNECT_NETWORK_OPTIONS,
            }
        )


class WalletLoginVerifyAPIView(APIView):
    """Verify a sign-in proof and log the linked account in."""

    permission_classes = [AllowAny]
    throttle_classes = [WalletLoginRateThrottle]

    def post(self, request, *args, **kwargs):
        """Verify the proof, resolve the linked account, and log it in.

        :param request: incoming request carrying ``nonce``, ``chain`` and the
            chain-specific proof (e.g. ``signedTransaction``)
        :type request: rest_framework.request.Request
        :var chain: request chain (default ``"algorand"``)
        :type chain: str
        :var nonce_str: the challenge being redeemed
        :type nonce_str: str
        :var proven: address the signature actually proves control of
        :type proven: str | None
        :var nonce_obj: the matching unused login nonce
        :type nonce_obj: walletauth.models.WalletLoginNonce
        :var user: the account linked to ``proven``, if any
        :type user: django.contrib.auth.models.User | None
        :return: JSON ``{success, redirect_url}`` or an error
        :rtype: rest_framework.response.Response
        """
        chain = request.data.get("chain", "algorand")
        nonce_str = request.data.get("nonce")
        if not nonce_str:
            return Response({"success": False, "error": "Missing nonce"}, status=400)

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
        except NotSupported:
            return Response(
                {
                    "success": False,
                    "error": "Sign-in for this chain is not yet enabled",
                },
                status=400,
            )
        if not proven:
            return Response(
                {"success": False, "error": "Signature verification failed"}, status=400
            )

        try:
            nonce_obj = WalletLoginNonce.objects.get(
                nonce=nonce_str, address=proven, chain=chain, used=False
            )
        except WalletLoginNonce.DoesNotExist:
            return Response(
                {"success": False, "error": "Invalid or used nonce"}, status=400
            )
        if nonce_obj.is_expired():
            return Response({"success": False, "error": "Nonce expired"}, status=400)

        # Consume the proof atomically up front: a valid proof is strictly
        # single-use whether or not an account turns out to be linked.
        if not nonce_obj.claim():
            return Response(
                {"success": False, "error": "Nonce already used"}, status=400
            )

        # Resolve the account from the PROVEN address only.
        try:
            user = authenticate(request, verified_wallet_address=proven, chain=chain)
        except AmbiguousWalletAddress:
            return Response(
                {
                    "success": False,
                    "error": (
                        "This wallet is linked to more than one account, so it "
                        "can't be used to sign in. Please log in with your email "
                        "and password or a social account."
                    ),
                },
                status=409,
            )
        if user is None:
            return Response(
                {
                    "success": False,
                    "error": (
                        "No account is linked to this wallet. Sign in another way "
                        "first, then link this wallet from your profile."
                    ),
                },
                status=401,
            )

        default_url = _perform_login(request, user)
        redirect_url = _safe_next(request) or default_url
        logger.info("walletauth: wallet sign-in via %s", chain)
        return Response({"success": True, "redirect_url": redirect_url})
