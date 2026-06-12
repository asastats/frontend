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
