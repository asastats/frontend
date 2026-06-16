"""Module containing walletauth app's URL configuration.

Mounted under ``/api/v2/wallet/`` from the project root urlconf, ABOVE the
general ``^api/v2/`` include so these routes resolve before the greedy
account-pattern catch-alls in ``api/urls.py``.
"""

from django.urls import path

from walletauth.gating_views import SwapGateAPIView
from walletauth.link_views import (
    WalletLinkNonceAPIView,
    WalletLinkVerifyAPIView,
)
from walletauth.login_views import (
    WalletLoginNonceAPIView,
    WalletLoginVerifyAPIView,
)
from walletauth.management_views import (
    ManageAddressAPIView,
    ManageNonceAPIView,
    WalletAddressesAPIView,
)
from walletauth.views import (
    WalletNonceAPIView,
    WalletsAPIView,
    WalletVerifyAPIView,
)

urlpatterns = [
    path("wallets/", WalletsAPIView.as_view(), name="wallet_wallets"),
    path("nonce/", WalletNonceAPIView.as_view(), name="wallet_nonce"),
    path("verify/", WalletVerifyAPIView.as_view(), name="wallet_verify"),
    # Sign-in (unauthenticated): mounted under .../login/ so the same frontend
    # WalletComponent works by pointing data-api-base at "/api/v2/wallet/login".
    # The bundle derives ".../wallets/", ".../nonce/" and ".../verify/" from that
    # base, so all three are mirrored here. ``wallets`` is the same public list.
    path(
        "login/wallets/",
        WalletsAPIView.as_view(),
        name="wallet_login_wallets",
    ),
    path(
        "login/nonce/",
        WalletLoginNonceAPIView.as_view(),
        name="wallet_login_nonce",
    ),
    path(
        "login/verify/",
        WalletLoginVerifyAPIView.as_view(),
        name="wallet_login_verify",
    ),
    # Linking (authenticated, connect-and-store) for EVM/xChain wallets.
    path(
        "link/nonce/",
        WalletLinkNonceAPIView.as_view(),
        name="wallet_link_nonce",
    ),
    path(
        "link/verify/",
        WalletLinkVerifyAPIView.as_view(),
        name="wallet_link_verify",
    ),
    # Address management (authenticated; step-up for set-primary / enable-login).
    path(
        "manage/addresses/",
        WalletAddressesAPIView.as_view(),
        name="wallet_manage_addresses",
    ),
    path(
        "manage/nonce/",
        ManageNonceAPIView.as_view(),
        name="wallet_manage_nonce",
    ),
    path(
        "manage/",
        ManageAddressAPIView.as_view(),
        name="wallet_manage",
    ),
    # Swap gate: which browsed addresses are connected to the caller.
    path(
        "gate/",
        SwapGateAPIView.as_view(),
        name="wallet_swap_gate",
    ),
]
