"""Module containing walletauth app's ORM models."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class WalletNonce(models.Model):
    """Single-use, user-bound challenge for wallet address authorization.

    A nonce is issued for an (``user``, ``address``) pair and consumed once the
    matching signed challenge is verified. Binding to ``user`` prevents a nonce
    solicited in one session from being redeemed in another.
    """

    #: Time a nonce remains valid after creation.
    NONCE_TTL = timedelta(minutes=5)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet_nonces",
    )
    address = models.CharField(max_length=58, db_index=True)
    nonce = models.CharField(max_length=64, unique=True)
    chain = models.CharField(max_length=16, default="algorand")
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["address", "used"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        """Return instance's string representation.

        :return: str
        """
        return f"{self.address[:5]}..{self.address[-5:]} - {self.nonce}"

    def is_expired(self):
        """Return True once the nonce is older than :attr:`NONCE_TTL`.

        :return: Boolean
        """
        return self.created_at < timezone.now() - self.NONCE_TTL

    def mark_used(self):
        """Mark this nonce as consumed so it cannot be replayed."""
        self.used = True
        self.save(update_fields=["used"])

    def claim(self):
        """Atomically transition this nonce from unused to used.

        Race-safe single-use: only the caller that performs the unused->used
        transition gets ``True``; a concurrent request that already consumed the
        nonce gets ``False``.

        :var claimed: number of rows the conditional update changed (0 or 1)
        :type claimed: int
        :return: True if this call consumed the nonce, else False
        :rtype: bool
        """
        claimed = type(self).objects.filter(pk=self.pk, used=False).update(used=True)
        if claimed:
            self.used = True
        return bool(claimed)

    @classmethod
    def purge_stale(cls):
        """Delete used or expired nonces. Intended for a periodic job.

        :var cutoff: timestamp before which unused nonces are considered expired
        :type cutoff: :class:`datetime.datetime`
        :var stale: queryset of nonces that are used or past ``cutoff``
        :type stale: :class:`django.db.models.QuerySet`
        :var deleted: total number of rows deleted
        :type deleted: int
        :return: number of rows deleted
        :rtype: int
        """
        cutoff = timezone.now() - cls.NONCE_TTL
        stale = cls.objects.filter(models.Q(used=True) | models.Q(created_at__lt=cutoff))
        deleted, _ = stale.delete()
        return deleted


class WalletLoginNonce(models.Model):
    """Single-use, address-bound challenge for wallet *sign-in* (no user yet).

    Unlike :class:`WalletNonce` (authorize), there is no authenticated user when
    a login challenge is issued, so the nonce is bound to the claimed address and
    chain. Security does not rely on that binding: the verify step resolves the
    account from the address the signature actually proves, never from the
    request body, so a nonce issued for one address cannot be redeemed by a
    signature proving a different one.
    """

    #: Time a nonce remains valid after creation.
    NONCE_TTL = timedelta(minutes=5)

    address = models.CharField(max_length=58, db_index=True)
    nonce = models.CharField(max_length=64, unique=True)
    chain = models.CharField(max_length=16, default="algorand")
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["address", "used"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        """Return instance's string representation.

        :return: str
        """
        return f"login {self.address[:5]}..{self.address[-5:]} - {self.nonce}"

    def is_expired(self):
        """Return True once the nonce is older than :attr:`NONCE_TTL`.

        :return: Boolean
        """
        return self.created_at < timezone.now() - self.NONCE_TTL

    def claim(self):
        """Atomically transition this nonce from unused to used.

        :var claimed: number of rows the conditional update changed (0 or 1)
        :type claimed: int
        :return: True if this call consumed the nonce, else False
        :rtype: bool
        """
        claimed = type(self).objects.filter(pk=self.pk, used=False).update(used=True)
        if claimed:
            self.used = True
        return bool(claimed)

    @classmethod
    def purge_stale(cls):
        """Delete used or expired login nonces. Intended for a periodic job.

        :var cutoff: timestamp before which unused nonces are considered expired
        :type cutoff: :class:`datetime.datetime`
        :return: number of rows deleted
        :rtype: int
        """
        cutoff = timezone.now() - cls.NONCE_TTL
        stale = cls.objects.filter(models.Q(used=True) | models.Q(created_at__lt=cutoff))
        deleted, _ = stale.delete()
        return deleted


class LinkedAddress(models.Model):
    """A verified wallet address connected to a user's profile.

    Each profile has exactly one *primary* address -- mirrored from
    ``Profile.address``, the sole source of permission, subscription and
    governance -- and any number of *secondary* addresses used only for login
    (opt-in via ``login_enabled``) and action-gating (e.g. showing a Swap
    button). Secondaries confer no privilege.

    Rows are globally unique on :attr:`canonical_address` so one on-chain account
    cannot be claimed by two profiles, and a primary is always login-capable
    (enforced by ``ck_linkedaddress_primary_login``).
    """

    profile = models.ForeignKey(
        "core.Profile",
        on_delete=models.CASCADE,
        related_name="linked_addresses",
    )
    #: Stored/display form (EVM lower-cased ``0x…`` or Algorand base32).
    address = models.CharField(max_length=58)
    #: Canonical dedup key: lsig counterpart for EVM, the address itself for native.
    canonical_address = models.CharField(max_length=58, db_index=True)
    #: Chain identifier (``"algorand"`` or ``"evm"``).
    chain = models.CharField(max_length=20)
    #: Verification method (``"algorand_wallet"`` or ``"evm_xchain"``).
    auth_method = models.CharField(max_length=20)
    #: Proof token (nonce) from the verification that linked this address.
    authorized = models.CharField(max_length=64, blank=True, default="")
    #: Whether this is the privilege-bearing primary (mirrors ``Profile.address``).
    is_primary = models.BooleanField(default=False)
    #: Whether this address may be used to log in. Off by default for
    #: secondaries; always on for the primary.
    login_enabled = models.BooleanField(default=False)
    #: Optional user-supplied label.
    label = models.CharField(max_length=64, blank=True, default="")
    #: When this address was last verified.
    verified_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["canonical_address"],
                name="uniq_linkedaddress_canonical",
            ),
            models.UniqueConstraint(
                fields=["profile"],
                condition=models.Q(is_primary=True),
                name="uniq_linkedaddress_one_primary",
            ),
            models.CheckConstraint(
                condition=models.Q(is_primary=False) | models.Q(login_enabled=True),
                name="ck_linkedaddress_primary_login",
            ),
        ]

    def __str__(self):
        kind = "primary" if self.is_primary else "secondary"
        return f"{self.address} ({kind})"

    @classmethod
    def secondary_count(cls, profile):
        """Return the number of secondary (non-primary) addresses on ``profile``.

        :param profile: the profile to count secondaries for
        :type profile: core.models.Profile
        :return: count of non-primary linked addresses
        :rtype: int
        """
        return cls.objects.filter(profile=profile, is_primary=False).count()

    @classmethod
    def at_secondary_capacity(cls, profile):
        """Return whether ``profile`` already holds the maximum secondaries.

        :param profile: the profile to test
        :type profile: core.models.Profile
        :return: True if no further secondaries may be added
        :rtype: bool
        """
        from walletauth.addresses import max_secondary_addresses

        return cls.secondary_count(profile) >= max_secondary_addresses()
