"""Keep the linked-address registry consistent with ``Profile.address``.

The walletauth flows (authorize, set-primary, link) reconcile the registry
themselves, but the profile can also be edited elsewhere -- e.g. clearing or
changing the address on the profile page. This ``post_save`` receiver makes the
registry track ``Profile.address`` wherever it changes: it drops any ``is_primary``
row that no longer matches the current address (and all of them when the address
is cleared). It deliberately does not *create* the primary row -- that happens
when the address is proven via the wallet flow -- so it never collides with code
that stamps the row explicitly. Crucially, dropping a stale primary also removes
its ``login_enabled`` flag, so a removed address can no longer be used to sign in.

Matching is on the raw stored ``address`` (which mirrors ``Profile.address``), so
no canonicalization or algod call is needed in the save path.
"""

import logging

from walletauth.models import LinkedAddress

logger = logging.getLogger(__name__)


def reconcile_primary_registry(sender, instance, **kwargs):
    """Drop primary rows that no longer match ``instance.address``.

    :param sender: the Profile model class
    :param instance: the profile just saved
    :type instance: core.models.Profile
    """
    try:
        stale = LinkedAddress.objects.filter(profile=instance, is_primary=True)
        if instance.address:
            stale = stale.exclude(address=instance.address)
        stale.delete()
    except Exception:  # never let reconciliation break a profile save
        logger.exception("walletauth: primary registry reconcile failed")
