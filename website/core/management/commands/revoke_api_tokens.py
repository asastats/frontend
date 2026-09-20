"""Revoke every API token one account holds, or restore them.

The thing to reach for when a credential leaks. Sets
`Profile.api_tokens_valid_from` to now, after which
`api.authentication.RevocableJWTAuthentication` refuses any token issued
earlier - which is all of them.

**Why not rotate the signing key.** That is the only other kill switch a
stateless JWT has, and it invalidates every token in existence at once:
`WIDGETS_API_TOKEN`, the token baked into the published mobile app, and every
third-party integration. It cannot be aimed at one account.

Usage::

    python manage.py revoke_api_tokens 355
    python manage.py revoke_api_tokens 355 --restore
    python manage.py revoke_api_tokens 355 --show

The account holder recovers without us: re-issuing from `/profile/api/`
produces a token whose `iat` postdates the cutoff, and it works immediately.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Revoke (or restore) every API token belonging to one user."

    # See snapshot_cost in the engine for the same reasoning: system checks
    # import the URL conf, and this touches one model field.
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int, help="the account's user id")
        parser.add_argument(
            "--restore",
            action="store_true",
            help="clear the cutoff, so previously issued tokens work again",
        )
        parser.add_argument(
            "--show",
            action="store_true",
            help="report the current state and change nothing",
        )

    def handle(self, *args, **options):
        """Set, clear, or report this account's token cutoff."""
        user_id = options["user_id"]
        try:
            user = User.objects.select_related("profile").get(pk=user_id)
        except User.DoesNotExist as error:
            raise CommandError(f"no user with id {user_id}") from error

        profile = getattr(user, "profile", None)
        if profile is None:
            raise CommandError(
                f"user {user_id} ({user.username}) has no profile, so it has "
                "no tokens to revoke - and cannot authenticate at all."
            )

        self.stdout.write(f"user {user_id}: {user.username}")
        self.stdout.write(f"  active     {user.is_active}")
        self.stdout.write(f"  permission {profile.permission}")
        self.stdout.write(f"  cutoff     {profile.api_tokens_valid_from or 'none'}")

        if options["show"]:
            return

        if options["restore"]:
            if profile.api_tokens_valid_from is None:
                self.stdout.write("\nnothing to restore - no cutoff was set")
                return
            profile.api_tokens_valid_from = None
            profile.save(update_fields=["api_tokens_valid_from"])
            self.stdout.write(
                self.style.SUCCESS(
                    "\nRESTORED. Tokens issued before the old cutoff work again."
                )
            )
            return

        profile.api_tokens_valid_from = timezone.now()
        profile.save(update_fields=["api_tokens_valid_from"])
        self.stdout.write(
            self.style.SUCCESS(
                f"\nREVOKED at {profile.api_tokens_valid_from}. Every token this "
                "account holds is now refused."
            )
        )
        # Said plainly because it decides whether this is safe to run: the
        # widgets and the published mobile app authenticate as accounts too,
        # and revoking one of those takes the site or the app down with it.
        self.stdout.write(
            "\nA new token from /profile/api/ will work immediately - its `iat` "
            "postdates the cutoff.\nIf this account is WIDGETS_API_TOKEN's or "
            "the mobile app's, reissue before\nanyone notices: nothing else "
            "authenticates for them."
        )
