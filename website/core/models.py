"""Module containing website's ORM models."""

import logging
from collections import Counter

from algosdk.constants import ADDRESS_LEN
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from core.permission_provider import get_permission_provider
from utils.constants.explorers import normalized_explorer
from utils.constants.users import (
    DUPLICATE_BUNDLE_ERROR,
    DUPLICATE_BUNDLE_NAME_ERROR,
    DUPLICATE_PUBLIC_BUNDLE_NAME_ERROR,
    PUBLIC_BUNDLE_ADDRESSES_NOT_ALLOWED_HELP_TEXT,
    SUBSCRIPTION_TIER_BUNDLE_NAMES_COUNT,
    SUBSCRIPTION_TIER_PERMISSIONS,
    SUBSCRIPTION_TIER_PUBLIC_BUNDLE_NAMES_COUNT,
    SYSTEM_RESERVED_URL_PATH_ERROR,
)
from utils.helpers import bundle_from_addresses, create_bundle
from utils.userhelpers import (
    is_system_reserved_url_path,
    slugified_bundle_name,
    truncated_timestamp_and_address,
    unique_hash_from_number,
)
from widgethost.access import can_access_widget

logger = logging.getLogger(__name__)


class Profile(models.Model):
    """App's connection to main django user model."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    address = models.CharField(max_length=ADDRESS_LEN, blank=True)
    authorized = models.CharField(max_length=64, blank=True)
    auth_method = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("escrow", "Escrow note"),
            ("algorand_wallet", "Algorand wallet"),
            ("evm_xchain", "EVM / xChain"),
        ],
    )
    authorized_at = models.DateTimeField(null=True, blank=True)
    votes = models.BigIntegerField(default=0, blank=True)
    permission = models.BigIntegerField(default=0, blank=True)
    currency = models.CharField(max_length=5, blank=True, default="ALGO")
    preferred_router = models.CharField(max_length=32, blank=True, default="")
    preferred_explorer = models.CharField(max_length=32, blank=True, default="")

    def __str__(self):
        """Return string representation of the profile instance

        :return: str
        """
        return self.name

    def _query_bundle_names(self):
        """Return bundle names set query.

        :return: :class:`QuerySet`
        """
        return BundleName.objects.filter(profile=self)

    def _query_public_bundle_names(self):
        """Return public bundle names set query.

        :return: :class:`QuerySet`
        """
        return BundleName.objects.filter(profile=self, public=True)

    def address_authorization_note(self):
        """Return unique user's hash."""
        return unique_hash_from_number(
            truncated_timestamp_and_address(
                self.user.date_joined.timestamp(), self.address
            )
        )

    def preferred_router_or_default(self):
        """Return the chosen swap router id, or the first available default.

        Imported lazily to avoid a models <-> widget-registry import cycle.

        :return: str
        """
        from widgethost.registry import swap_routers

        available = [router_id for router_id, _ in swap_routers()]
        if self.preferred_router in available:
            return self.preferred_router
        return available[0] if available else ""

    def preferred_explorer_or_default(self):
        """Return the chosen explorer key, or the default when unset/unknown.

        Permission is intentionally *not* re-checked here: the right to *change*
        this setting is gated on the settings page (Intro tier), but a value
        already saved keeps applying. Mirrors
        :meth:`preferred_router_or_default`.

        :return: str
        """
        return normalized_explorer(self.preferred_explorer)

    def can_access_explorer_setting(self):
        """Return True if the user may choose a preferred explorer.

        Available from the Intro subscription tier upward; below that the
        settings page shows the option disabled and routes a click to the
        subscriptions page.

        :return: Boolean
        """
        return self.permission >= SUBSCRIPTION_TIER_PERMISSIONS["Intro"]

    def check_votes_and_permission(self):
        """Check and possibly update profile with new votes and permission values.

        :var result: provider's (votes, permission) pair, or None
        :type result: tuple
        :var votes: user's governance votes count
        :type votes: int
        :var permission: user's permission on website
        :type permission: int
        """
        result = get_permission_provider().votes_and_permission(self.algorand_address)
        if result is None:
            return

        votes, permission = result
        if self.votes != votes or self.permission != permission:
            if self.votes and votes == 0:
                return

            self.votes = votes
            self.permission = permission
            self.save()

    def save(self, **kwargs):
        """Reset authorized and permission fields if authorized address is changed."""
        if self.id:
            instance = Profile.objects.get(pk=self.id)
            if instance.address and instance.address != self.address:
                self.authorized = ""
                self.auth_method = ""
                self.authorized_at = None
                self.permission = 0

        super().save(**kwargs)

    def tier_name(self):
        """Return subscription tier name from instance's permission value.

        :return: str
        """
        if self.permission < SUBSCRIPTION_TIER_PERMISSIONS["Intro"]:
            return "Trial"
        if self.permission < SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]:
            return "Intro"
        if self.permission < SUBSCRIPTION_TIER_PERMISSIONS["Professional"]:
            return "Asastatser"
        if self.permission < SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]:
            return "Professional"
        return "Cluster"

    def update_authorized(self, proof, method="escrow"):
        """Record an authorization proof and best-effort refresh permission.

        The authorization is always persisted; a failing permission refresh is
        logged and swallowed so the authorization is never lost. Permission then
        reconciles on the next login (post_login) or a later refresh.

        :param proof: provenance string (escrow txid, or the consumed nonce)
        :type proof: str
        :param method: one of "escrow", "algorand_wallet", "evm_xchain"
        :type method: str
        :var refreshed: whether the permission refresh completed
        :type refreshed: bool
        :return: True if permission was refreshed, False to reconcile later
        :rtype: bool
        """
        self.authorized = proof
        self.auth_method = method
        self.authorized_at = timezone.now()
        refreshed = True
        try:
            self.check_votes_and_permission()
        except Exception:  # noqa: BLE001 - permission refresh is best-effort
            logger.exception(
                "Permission refresh failed for profile pk=%s; authorization "
                "recorded, permission will reconcile on next login/refresh.",
                self.pk,
            )
            refreshed = False
        self.save()
        return refreshed

    # # PERMISSIONS
    def _bundlename_limit_data(
        self, bundlenames, collection=SUBSCRIPTION_TIER_BUNDLE_NAMES_COUNT
    ):
        """Calculate and yield pair of user bundle names count and the related limit.

        :param bundlenames: profile's bundle names collection
        :type bundlenames: :class:`QuerySet`
        :param collection: predefined collection of bundle name limits
        :type collection: dict
        :var limits: collection of pre-defined bundle configuration limits for tier
        :type limits: list
        :var counter: user bundle names counter collection
        :type counter: :class:`Counter`
        :var index: currently processed limit's index in limits collection
        :type index: int
        :var limit: currently processed limit instance
        :type limit: :class:`utils.constants.users.BundleLimit`
        :var left_boundary: minimum number of addresses for currently processed limit
        :type left_boundary: int
        :var right_boundary: maximum number of addresses for currently processed limit
        :type right_boundary: int
        :var current_sum: total count of bundle names for currently processed limit
        :type current_sum: int
        :return: tuple
        """
        limits = collection.get(self.tier_name(), collection["Trial"])
        counter = Counter(
            len(bundlename.addresses.split(" ")) for bundlename in bundlenames
        )
        for index, limit in enumerate(limits):
            left_boundary, right_boundary = (
                (limits[index + 1].size + 1, limit.size)
                if index != len(limits) - 1
                else (1, limit.size)
            )
            current_sum = sum(
                count
                for size, count in counter.items()
                if size in range(left_boundary, right_boundary + 1)
            )
            yield (current_sum, limit.count, limit.size)

    def _can_sort_and_filter(self):
        """Return True if user is allowed to sort and filter templates.

        :return: Boolean
        """
        return self.permission >= SUBSCRIPTION_TIER_PERMISSIONS["Professional"]

    def bundle_size_limit(self, instance=None):
        """Return maximum bundle size for profile based on bundle name `instance`.

        :param instance: bundle name instance
        :type instance: :class:`BundleName`
        :var current_sum: total count of bundle names for currently processed limit
        :type current_sum: int
        :var count: currently processed bundle name limit's allowed bundle names number
        :type count: int
        :var size: currently processed bundle name limit's allowed addresses number
        :type size: int
        :return: int
        """
        for current_sum, count, size in self._bundlename_limit_data(
            self._query_bundle_names()
        ):
            if current_sum < count:
                break

        if instance is None:
            return size

        return max(len(instance.addresses.split(" ")), size)

    def bundle_size_limit_for_public(self):
        """Return maximum public bundle size for profile.

        :var current_sum: total count of bundle names for currently processed limit
        :type current_sum: int
        :var count: currently processed bundle name limit's allowed bundle names number
        :type count: int
        :var size: currently processed bundle name limit's allowed addresses number
        :type size: int
        :return: int
        """
        for current_sum, count, size in self._bundlename_limit_data(
            self._query_public_bundle_names(),
            collection=SUBSCRIPTION_TIER_PUBLIC_BUNDLE_NAMES_COUNT,
        ):
            if current_sum < count:
                break

        else:
            return 0

        return size

    def can_access_api(self):
        """Return True if user is allowed to access API.

        :return: Boolean
        """
        return self.permission >= SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]

    def can_access_authorize(self):
        """Return True if user is allowed to access authorize page.

        :return: Boolean
        """
        return not self.authorized

    def can_add_bundle_name(self):
        """Return True if user is allowed to create another bundle name.

        :var count: total number of already created bundle names
        :type count: int
        :var limits: collection of pre-defined bundle configuration limits for tier
        :type limits: list
        :return: Boolean
        """
        count = self._query_bundle_names().count()
        limits = SUBSCRIPTION_TIER_BUNDLE_NAMES_COUNT.get(
            self.tier_name(), SUBSCRIPTION_TIER_BUNDLE_NAMES_COUNT["Trial"]
        )
        return count < sum(limit.count for limit in limits)

    def can_add_public_bundle_name(self, instance_id, addresses):
        """Return True if user is allowed to create another public bundle name.

        :param instance_id: bundle name instance ID
        :type instance_id: int
        :param addresses: collection of public Algorand addresses separated by spaces
        :type addresses: str
        :var bundlename: bundle name instance
        :type bundlename: :class:`BundleName`
        :var limit: maximum number of addresses in public bundle for user
        :type limit: int
        :var bundlenames: profile's bundle names collection
        :type bundlenames: :class:`QuerySet`
        :var count: total number of already created bundle names
        :type count: int
        :var limits: collection of pre-defined bundle configuration limits for tier
        :type limits: list
        :return: Boolean
        """
        limit = self.bundle_size_limit_for_public()
        if limit < len(addresses.split(" ")):
            return False

        bundlenames = self._query_public_bundle_names()
        count = len(
            [bundlename for bundlename in bundlenames if bundlename.id != instance_id]
        )
        limits = SUBSCRIPTION_TIER_PUBLIC_BUNDLE_NAMES_COUNT.get(
            self.tier_name(), SUBSCRIPTION_TIER_PUBLIC_BUNDLE_NAMES_COUNT["Trial"]
        )
        return count < sum(limit.count for limit in limits)

    def can_use_bundle_names(self):
        """Return True if user is allowed to use created bundle names.

        :var bundlenames: profile's bundle names collection
        :type bundlenames: :class:`QuerySet`
        :var total_count: total number of already created bundle names
        :type total_count: int
        :var tier_name: user's subscription tier name
        :type tier_name: str
        :var limits: collection of pre-defined bundle configuration limits for tier
        :type limits: list
        :var current_sum: total count of bundle names for currently processed limit
        :type current_sum: int
        :var count: currently processed bundle name limit's number allowed bundle names
        :type count: int
        :return: Boolean
        """
        tier_name = self.tier_name()
        if tier_name == "Cluster":
            return True

        bundlenames = self._query_bundle_names()
        total_count = bundlenames.count()
        limits = SUBSCRIPTION_TIER_BUNDLE_NAMES_COUNT.get(
            tier_name, SUBSCRIPTION_TIER_BUNDLE_NAMES_COUNT["Trial"]
        )
        if total_count > sum(limit.count for limit in limits):
            return False

        for current_sum, count, _ in self._bundlename_limit_data(bundlenames):
            if current_sum > count or count == 0:
                return False

        return True

    def show_sort_and_filter(self):
        """Return True if sorting and filtering panel should be presented to user.

        :return: Boolean
        """
        return self._can_sort_and_filter() and self._query_bundle_names().count() > 1

    # # HELPERS
    def bundlename_by_name(self, name):
        """Return profile's bundle name instance having provided name.

        :param name: unique bundle name
        :type name: str
        :return: :class:`BundleName`
        """
        try:
            return self.bundlename_set.get(name__iexact=name)
        except ObjectDoesNotExist:
            raise Http404

    def bundlename_system_reserved_url_path_check(self, name):
        """Raise Validation error if provided 'name' holds system reserved URL.

        :param name: bundle name to check
        :type name: str
        """
        if is_system_reserved_url_path(slugified_bundle_name(name)):
            raise ValidationError(SYSTEM_RESERVED_URL_PATH_ERROR)

    def bundlenames(self):
        """Return all profile's bundle names.

        :return: :class:`QuerySet`
        """
        return self._query_bundle_names().all()

    def get_absolute_url(self):
        """Return url of the profile home page.

        :return: url
        """
        return reverse("profile")

    def integrity_check_for_bundlename(self, instance_id, cleaned_data):
        """Raise Validation error if `cleaned_data` holds duplicate name or addresses.

        :param instance_id: bundle name instance ID
        :type instance_id: int
        :param cleaned_data: model form's cleaned data
        :type cleaned_data: dict
        :var name: bundle name
        :type name: str
        :var addresses: collection of public Algorand addresses separated by spaces
        :type addresses: str
        """
        if instance_id is not None:
            return False

        name = slugified_bundle_name(cleaned_data.get("name"))
        try:
            self.bundlename_set.get(name__iexact=name)
            raise ValidationError(DUPLICATE_BUNDLE_NAME_ERROR)

        except ObjectDoesNotExist:
            pass

        addresses = cleaned_data.get("addresses")
        try:
            self.bundlename_set.get(bundle=bundle_from_addresses(addresses))
            raise ValidationError(DUPLICATE_BUNDLE_ERROR)

        except ObjectDoesNotExist:
            pass

    def integrity_check_for_public_bundlename(self, instance_id, cleaned_data):
        """Raise Validation error if `cleaned_data` holds reserved public name

        or if user's limit is reached.

        :param instance_id: bundle name instance ID
        :type instance_id: int
        :param cleaned_data: model form's cleaned data
        :type cleaned_data: dict
        :var name: bundle name
        :type name: str
        :var addresses: collection of public Algorand addresses separated by spaces
        :type addresses: str
        """
        name = slugified_bundle_name(cleaned_data.get("name"))
        try:
            bundlename = BundleName.objects.get(name__iexact=name)
            if bundlename.id != instance_id:
                raise ValidationError(DUPLICATE_PUBLIC_BUNDLE_NAME_ERROR)

        except ObjectDoesNotExist:
            pass

        addresses = cleaned_data.get("addresses")
        if not self.can_add_public_bundle_name(instance_id, addresses):
            raise ValidationError(PUBLIC_BUNDLE_ADDRESSES_NOT_ALLOWED_HELP_TEXT)

    def profile(self):
        """Return self instance for generic templating purposes.

        It is accessed by 'object.profile' in some templates.

        :return: :class:`Profile`
        """
        return self

    @property
    def algorand_address(self):
        """Return this profile's Algorand address.

        Native Algorand wallets store their base32 address directly and it is
        returned unchanged. EVM/xChain wallets store the ``0x`` EVM address; its
        deterministic Algorand logicsig counterpart is derived on demand via the
        xChain helper. Returns an empty string when no address is set.

        :var address: the raw stored address
        :type address: str
        :return: an Algorand address (or empty string)
        :rtype: str
        """
        address = self.address or ""
        if address.startswith("0x"):
            from nameservice.xchain import check_evm_address
            from utils.clients import algod_instance

            return check_evm_address(address, algod_instance())
        return address

    @property
    def name(self):
        """Return user/profile name made depending on data fields availability.

        :return: str
        """
        return (
            "{} {}".format(self.user.first_name, self.user.last_name).strip()
            if (self.user.first_name or self.user.last_name)
            else self.user.username or self.user.email.split("@")[0]
        )

    # # WIDGETS
    def can_access_historic_widget(self, size):
        """Return True if historic data for bundle can be accessed by user.

        :param size: number of Algorand addresses in the bundle
        :type size: int
        :return: Boolean
        """
        return can_access_widget("historic", self, size)


class BundleName(models.Model):
    """User's bundle names distincted by name field."""

    profile = models.ForeignKey(Profile, default=None, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="")
    addresses = models.CharField(max_length=ADDRESS_LEN * 110, default="")
    bundle = models.CharField(max_length=40, blank=True, default="")
    public = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        """Define ordering and fields that make unique indexes.

        Default ordering is by bundle name.
        Each bundle name has to be unique per profile by name and containing addresses.
        """

        constraints = [
            # (1) Unique per profile when not public
            models.UniqueConstraint(
                "profile",
                Lower("name"),
                condition=models.Q(public=False),
                name="unique_private_profile_name",
            ),
            # (2) Unique bundle per profile
            models.UniqueConstraint(
                fields=["profile", "bundle"], name="unique_profile_bundle"
            ),
            # (3) Globally unique public names
            models.UniqueConstraint(
                Lower("name"),
                condition=models.Q(public=True),
                name="unique_public_name",
            ),
        ]
        indexes = [
            # Speed up queries & uniqueness checks on (name, public)
            models.Index(Lower("name"), name="idx_lower_name"),
            models.Index(Lower("name"), "public", name="idx_lower_name_public"),
        ]
        ordering = [Lower("name")]

    def __str__(self):
        """Return bundle's instance string representation.

        :return: str
        """
        return self.name

    def bundlename(self):
        """Return self instance for generic templating purposes.

        Some templates call 'object.bundlename' so this approach is convenient

        :return: :class:`BundleName`
        """
        return self

    def get_absolute_url(self):
        """Return url of the edit bundle name page.

        :return: str
        """
        return reverse("bundlename_edit", args=[self.name])

    def is_eligible_public_bundlename(self):
        """Return whether this bundle name may be made public.

        TODO: implement and test
        TODO: check if user subscription expired as that's the only way
              how user can be ineligible.

        :return: bool
        """
        return True

    def save(self, **kwargs):
        """Call super save method after name and bundle fields are created if needed."""
        slugified = slugified_bundle_name(self.name)
        if self.name != slugified:
            self.name = slugified
        bundle = create_bundle(self.addresses)
        if self.bundle != bundle:
            self.bundle = bundle

        super().save(**kwargs)

    @property
    def class_name(self):
        """Return lowercased class name to be used in templates.

        :return: str
        """
        return self.__class__.__name__.lower()

    @property
    def short_created(self):
        """Return short string representation of created value.

        :return: str
        """
        return self.created.strftime("%x")

    @property
    def short_modified(self):
        """Return short string representation of modified value.

        :return: str
        """
        return self.modified.strftime("%x %X UTC")

    @property
    def size(self):
        """Return number of addresses in bundle.

        :return: int
        """
        return len(self.addresses.split(" "))

    @property
    def str_created(self):
        """Return universal string representation of created value.

        :return: str
        """
        return self.created.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def str_modified(self):
        """Return universal string representation of modified value.

        :return: str
        """
        return self.modified.strftime("%Y-%m-%d %H:%M:%S")

    # # WIDGETS
    def can_access_historic_widget(self):
        """Return True if historic data for bundle can be accessed by user.

        :return: Boolean
        """
        return can_access_widget("historic", self.profile, self.size)
