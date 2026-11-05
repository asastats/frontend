"""Module containing assetfeedback app configuration."""

from django.apps import AppConfig


class AssetfeedbackConfig(AppConfig):
    """Application configuration for the assetfeedback app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "assetfeedback"
    verbose_name = "Asset feedback"

    def ready(self):
        """Clear a deleted account's contact details from its reports."""
        from django.contrib.auth import get_user_model
        from django.db.models.signals import pre_delete

        from assetfeedback.models import clear_contact_of_deleted_user

        pre_delete.connect(
            clear_contact_of_deleted_user,
            sender=get_user_model(),
            dispatch_uid="assetfeedback_clear_contact",
        )
