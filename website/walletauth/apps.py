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

    def ready(self):
        """Connect the primary-registry reconciliation to ``Profile`` saves."""
        from django.db.models.signals import post_save

        from core.models import Profile
        from walletauth.signals import reconcile_primary_registry

        post_save.connect(
            reconcile_primary_registry,
            sender=Profile,
            dispatch_uid="walletauth_reconcile_primary_registry",
        )
