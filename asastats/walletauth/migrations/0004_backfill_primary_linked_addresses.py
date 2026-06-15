"""Backfill one primary :class:`LinkedAddress` per existing authorized profile.

Mirrors each profile's current ``address`` into the new registry as the
``is_primary`` row, preserving today's behaviour: the primary keeps conferring
permission and remains login-capable. Secondary addresses are added later
through the linking flow.

EVM primaries (``0x…``) require algod connectivity to derive their canonical
(lsig) form; run this with algod reachable. Native Algorand primaries need no
network access.
"""

from django.db import migrations


def _canonical(address):
    """Return the canonical dedup form for a profile's primary ``address``.

    :param address: the profile's stored primary address
    :type address: str
    :raises RuntimeError: if an EVM address cannot be canonicalized
    :return: lsig counterpart for EVM, the address itself for native Algorand
    :rtype: str
    """
    if not address.startswith("0x"):
        return address
    from nameservice.xchain import check_evm_address
    from utils.clients import algod_instance

    canonical = check_evm_address(address, algod_instance())
    if not canonical or canonical.lower().startswith("0x"):
        raise RuntimeError(
            f"Backfill could not canonicalize EVM primary {address}; "
            "ensure algod is reachable, then re-run the migration."
        )
    return canonical


def forwards(apps, schema_editor):
    """Create a primary LinkedAddress for every profile that has an address.

    :param apps: historical app registry
    :type apps: django.apps.registry.Apps
    :param schema_editor: migration schema editor (unused)
    :type schema_editor: django.db.backends.base.schema.BaseDatabaseSchemaEditor
    """
    Profile = apps.get_model("core", "Profile")
    LinkedAddress = apps.get_model("walletauth", "LinkedAddress")

    for profile in Profile.objects.exclude(address="").exclude(address__isnull=True):
        address = profile.address
        chain = "evm" if address.startswith("0x") else "algorand"
        auth_method = profile.auth_method or (
            "evm_xchain" if chain == "evm" else "algorand_wallet"
        )
        LinkedAddress.objects.get_or_create(
            canonical_address=_canonical(address),
            defaults={
                "profile": profile,
                "address": address,
                "chain": chain,
                "auth_method": auth_method,
                "authorized": profile.authorized or "",
                "is_primary": True,
                # The primary is always login-capable (preserves current login).
                "login_enabled": True,
            },
        )


def backwards(apps, schema_editor):
    """Remove the primary rows created by :func:`forwards`.

    :param apps: historical app registry
    :type apps: django.apps.registry.Apps
    :param schema_editor: migration schema editor (unused)
    :type schema_editor: django.db.backends.base.schema.BaseDatabaseSchemaEditor
    """
    LinkedAddress = apps.get_model("walletauth", "LinkedAddress")
    LinkedAddress.objects.filter(is_primary=True).delete()


class Migration(migrations.Migration):

    dependencies = [("walletauth", "0003_linkedaddress")]

    operations = [migrations.RunPython(forwards, backwards)]
