"""Django management command setting a report's status and clearing its contact."""

from django.core.management.base import BaseCommand, CommandError

from assetfeedback.models import AssetFeedback

RESOLVED = [s for s in AssetFeedback.Status.values if s != AssetFeedback.Status.NEW]


class Command(BaseCommand):
    help = "Resolve one asset feedback report. Its contact is cleared."

    def add_arguments(self, parser):
        parser.add_argument("report_id", type=int)
        parser.add_argument("status", choices=RESOLVED)
        parser.add_argument("--note", default="", help="reviewer's note")

    def handle(self, *args, **options):
        """Update the report."""
        updated = AssetFeedback.objects.filter(pk=options["report_id"]).update(
            status=options["status"], reviewer_note=options["note"], contact=""
        )
        if not updated:
            raise CommandError(f"No report {options['report_id']}")
        self.stdout.write(f"Report {options['report_id']}: {options['status']}")
