"""Django management command clearing contacts from reports older than 12 months."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from assetfeedback.models import AssetFeedback

CONTACT_RETENTION_DAYS = 365


class Command(BaseCommand):
    help = "Clear the contact of every report older than 12 months."

    def handle(self, *args, **options):
        """Clear the contacts."""
        cutoff = timezone.now() - timedelta(days=CONTACT_RETENTION_DAYS)
        cleared = (
            AssetFeedback.objects.filter(created__lt=cutoff)
            .exclude(contact="")
            .update(contact="")
        )
        self.stdout.write(f"Cleared {cleared} contacts")
