"""Module containing core app signals."""

from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

from core.apple import revoke_for_user
from core.models import AppleSignInToken, Profile

#: Sent with ``user`` when an account is closed (deactivated, deleted within a
#: week). Receivers drop what must stop at once, e.g. push delivery.
user_deactivated = Signal()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile instance if user is successfully created.

    Method is called by signal sent from django infrastructure
    after sender instance is saved.

    :param sender: class responsible for signal sending
    :type sender: :class:`User`
    :param instance: instance of the sender class
    :type instance: :class:`User`
    :param created: value that determines is sender is created or not
    :type created: boolean
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Update profile instance after related user is updated.

    Method is called by signal sent from django infrastructure
    after sender instance is updated.

    :param sender: class responsible for signal sending
    :type sender: :class:`User`
    :param instance: instance of the sender class
    :type instance: object of :class:`User`
    """
    instance.profile.save()


@receiver(user_logged_in)
def post_login(sender, user, request, **kwargs):
    """Check user's votes and permission values upon log in.

    Method is called by signal sent from django infrastructure
    after user logs in.

    :param sender: class responsible for signal sending
    :type sender: :class:`User`
    :param user: instance of the user that just logged in
    :type user: :class:`User`
    """
    if user.profile.authorized:
        user.profile.check_votes_and_permission()


def keep_apple_token(sociallogin):
    """Store the refresh token of a Sign in with Apple login, for revocation.

    :param sociallogin: allauth's record of the social login
    :type sociallogin: :class:`allauth.socialaccount.models.SocialLogin`
    """
    token = sociallogin.token
    if sociallogin.account.provider != "apple" or token is None or not token.token_secret:
        return

    AppleSignInToken.objects.update_or_create(
        user=sociallogin.user,
        defaults={
            "refresh_token": token.token_secret,
            # Set by the app's native sign-in (O3); the web flow leaves it empty.
            "client_id": sociallogin.state.get("apple_client_id", ""),
        },
    )


@receiver(social_account_added)
@receiver(social_account_updated)
def keep_apple_token_on_login(sender, request, sociallogin, **kwargs):
    """Keep the Apple token on a returning login or a connected account."""
    keep_apple_token(sociallogin)


@receiver(user_signed_up)
def keep_apple_token_on_signup(sender, request, user, **kwargs):
    """Keep the Apple token when Sign in with Apple created the account."""
    sociallogin = kwargs.get("sociallogin")
    if sociallogin is not None:
        keep_apple_token(sociallogin)


@receiver(user_deactivated)
def revoke_apple_token_on_deactivation(sender, user, **kwargs):
    """Revoke the user's Sign in with Apple token when the account is closed."""
    revoke_for_user(user)
