"""Module containing walletauth app's URL configuration.

Mounted under ``/api/v2/wallet/`` from the project root urlconf, ABOVE the
general ``^api/v2/`` include so these routes resolve before the greedy
account-pattern catch-alls in ``api/urls.py``.
"""

from django.urls import path

from walletauth.views import (
    WalletNonceAPIView,
    WalletsAPIView,
    WalletVerifyAPIView,
)

urlpatterns = [
    path("wallets/", WalletsAPIView.as_view(), name="wallet_wallets"),
    path("nonce/", WalletNonceAPIView.as_view(), name="wallet_nonce"),
    path("verify/", WalletVerifyAPIView.as_view(), name="wallet_verify"),
]
