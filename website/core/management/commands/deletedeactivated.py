from django.core.management.base import BaseCommand

from utils.userhelpers import delete_deactivated


class Command(BaseCommand):
    help = "Delete all the deactivated accounts."

    def handle(self, *args, **options):
        """Deletes all deactivated accounts.

        :var count: number of deleted users
        :type count: integer
        :return: string
        """
        count = delete_deactivated()
        return "{} deactivated accounts deleted!".format(count)
