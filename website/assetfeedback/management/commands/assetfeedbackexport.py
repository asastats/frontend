"""Django management command writing asset feedback reports as CSV to stdout."""

import csv

from django.core.management.base import BaseCommand
from django.db.models import Count

from assetfeedback.models import AssetFeedback

COLUMNS = (
    "id",
    "asset_id",
    "reports_for_asset",
    "kind",
    "link",
    "details",
    "contact",
    "reporter_address",
    "source",
    "status",
    "created",
)
#: This is anonymous text opened in a spreadsheet.
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value):
    """Return `value` so a spreadsheet will not run it as a formula.

    :param value: cell content
    :type value: object
    :return: str
    """
    text = "" if value is None else str(value)
    return f"'{text}" if text.startswith(FORMULA_PREFIXES) else text


class Command(BaseCommand):
    help = "New reports grouped by asset; --rewards lists accepted ones with an address."

    def add_arguments(self, parser):
        parser.add_argument(
            "--rewards",
            action="store_true",
            help="the first accepted report per asset that left an address",
        )

    def handle(self, *args, **options):
        """Write the CSV."""
        writer = csv.writer(self.stdout)
        writer.writerow(COLUMNS)
        if options["rewards"]:
            reports = (
                AssetFeedback.objects.filter(status=AssetFeedback.Status.ACCEPTED)
                .exclude(reporter_address="")
                .order_by("asset_id", "created")
                .distinct("asset_id")
            )
        else:
            reports = AssetFeedback.objects.filter(status=AssetFeedback.Status.NEW)
        counts = dict(
            reports.order_by().values_list("asset_id").annotate(total=Count("id"))
            if not options["rewards"]
            else ()
        )
        rows = sorted(reports, key=lambda r: (-counts.get(r.asset_id, 1), r.asset_id, r.pk))
        for report in rows:
            writer.writerow(
                [
                    report.pk,
                    report.asset_id,
                    counts.get(report.asset_id, 1),
                    *(
                        safe_cell(value)
                        for value in (
                            report.kind,
                            report.link,
                            report.details,
                            report.contact,
                            report.reporter_address,
                            report.source,
                            report.status,
                        )
                    ),
                    report.created.isoformat(),
                ]
            )
