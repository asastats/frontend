"""Django management command for updating permission from ASASTATS holdings."""

from django.core.management.base import BaseCommand

from core.permission_providers.holdings import sync_holdings


class Command(BaseCommand):
    help = "Record ASASTATS and LP holdings and update the affected profiles."

    def handle(self, *args, **options):
        """Run one cycle; the cron job repeats it."""
        recorded, updated = sync_holdings()
        self.stdout.write(f"Recorded {recorded}, updated {updated}")
