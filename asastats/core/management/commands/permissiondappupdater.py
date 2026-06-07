"""Django management command for updating Permission dApp boxes."""

from django.core.management.base import BaseCommand

from utils.permissions import run_permissions_update


class Command(BaseCommand):
    help = "Run routine for updating Permission dApp boxes in an indefinite loop."

    def handle(self, *args, **options):
        """Run infinite loop with multiprocessing.Pool in context."""

        run_permissions_update()
        self.stdout.write("Permission dApp updater exited")
