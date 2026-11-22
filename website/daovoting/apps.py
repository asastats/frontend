"""Module containing the daovoting app's configuration."""

from django.apps import AppConfig


class DaovotingConfig(AppConfig):
    """Configuration of the read-only DAO voting pages."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "daovoting"
