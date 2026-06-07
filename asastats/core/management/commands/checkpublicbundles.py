"""Django management command for updating public bundle files on disk."""

from django.core.management.base import BaseCommand

from core.helpers import check_public_bundles


class Command(BaseCommand):
    help = "Calls public bundle files on disk updating routine."

    def handle(self, *args, **options):
        """Call check_public_bundles function to update files on disk.

        :var data: is there any new data or not
        :type data: Boolean
        :var output: changed public bundles collection
        :type output: str
        """
        data = check_public_bundles()
        if len(data) == 0:
            self.stdout.write("No changes")
        else:
            output = " ".join(data)
            self.stdout.write(f"Updated: {output}")
