"""Django management command for updating user permissions."""

from django.core.management.base import BaseCommand

from core.permission_providers.updater import run_permissions_update


class Command(BaseCommand):
    help = "Run routine for updating user permissions in an indefinite loop."

    def handle(self, *args, **options):
        """Run infinite loop with multiprocessing.Pool in context."""

        run_permissions_update()
        self.stdout.write("Permissions updater exited")
