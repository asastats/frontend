"""Module containing walletauth app configuration."""

from django.apps import AppConfig


class WalletauthConfig(AppConfig):
    """Application configuration for the walletauth app.

    :var WalletauthConfig.name: app name
    :type WalletauthConfig.name: str
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "walletauth"
    verbose_name = "Wallet authorization"
