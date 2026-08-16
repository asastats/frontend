"""Module containing core app configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Main class for core application.

    :var CoreConfig.name: app name
    :type CoreConfig.name: str
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """Run these imports when Django starts."""
        import core.signals

        # Registers the system checks; importing the module is what registers
        # them, hence the noqa rather than a call.
        import core.checks  # noqa: F401
