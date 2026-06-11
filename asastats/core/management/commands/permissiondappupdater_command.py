"""Management command updating the Permission dApp boxes (ASA Stats deployment).

Lives in the frontend because the permission-dapp submodule is not a Django app.
Django imports every command module at startup, so the ``permissiondapp`` import
is done lazily inside ``handle`` — a deployment without the submodule keeps a
working ``manage.py`` and this command simply reports that it is unavailable.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Update the on-chain Permission dApp boxes."""

    help = "Update Permission dApp boxes from chain."

    def handle(self, *args, **options):
        """Run the on-chain Permission dApp box update; skip if not installed.

        :return: None
        """
        try:
            from permissiondapp.dapp.foundation import (
                check_and_update_permission_dapp_boxes,
            )
        except ImportError:
            self.stderr.write("permissiondapp submodule not installed; skipping.")
            return
        check_and_update_permission_dapp_boxes(network="mainnet")
