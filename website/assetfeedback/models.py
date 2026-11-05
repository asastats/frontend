"""Module containing readers' reports about not-evaluated assets."""

from django.conf import settings
from django.db import models


class AssetFeedback(models.Model):
    """One reader's report about one asset. No IP address is stored."""

    class Kind(models.TextChoices):
        MARKET = "market", "Where it can be sold"
        ABOUT = "about", "What this asset is"
        NO_MARKET = "no_market", "I know of no market for it"
        OTHER = "other", "Other"

    class Source(models.TextChoices):
        WEB = "web", "Web"
        APP = "app", "App"

    class Status(models.TextChoices):
        NEW = "new", "New"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        DUPLICATE = "duplicate", "Duplicate"
        REWARDED = "rewarded", "Rewarded"

    asset_id = models.PositiveBigIntegerField(db_index=True)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    # Stored as text only: never fetched, never rendered as a link.
    link = models.URLField(max_length=500, blank=True)
    details = models.TextField(max_length=1000, blank=True)
    contact = models.CharField(max_length=200, blank=True)
    reporter_address = models.CharField(max_length=58, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="asset_feedback",
    )
    source = models.CharField(max_length=8, choices=Source.choices, default=Source.WEB)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    reviewer_note = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.asset_id} {self.kind} {self.status}"


def clear_contact_of_deleted_user(sender, instance, **kwargs):
    """Clear contact details before `SET_NULL` unlinks the reports.

    :param sender: user model
    :type sender: type
    :param instance: user being deleted
    :type instance: :class:`django.contrib.auth.models.User`
    """
    AssetFeedback.objects.filter(user=instance).update(contact="", reporter_address="")
