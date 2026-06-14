"""Module containing walletauth app's URL configuration.

Mounted under ``/api/v2/wallet/`` from the project root urlconf, ABOVE the
general ``^api/v2/`` include so these routes resolve before the greedy
account-pattern catch-alls in ``api/urls.py``.
"""

from django.urls import path

from walletauth.login_views import (
    WalletLoginNonceAPIView,
    WalletLoginVerifyAPIView,
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
]
