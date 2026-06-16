"""Authentication backend for wallet sign-in.

The backend trusts a single kwarg, ``verified_wallet_address``, and resolves the
linked account from it. That kwarg is only ever passed by
:class:`walletauth.views.WalletLoginVerifyAPIView` *after* the cryptographic
proof has been validated, so the trust boundary is explicit and narrow -- the
same pattern social and magic-link logins use. The backend is unreachable via
the normal username/password path because it ignores those credentials.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

from walletauth.account_resolution import resolve_account


class WalletAddressBackend(BaseBackend):
    """Resolve a user from an already-verified wallet address."""

    def authenticate(
        self, request, verified_wallet_address=None, chain="algorand", **kwargs
    ):
        """Return the account linked to a verified address, or ``None``.

        :param request: the current request (unused; required by the interface)
        :type request: django.http.HttpRequest
        :param verified_wallet_address: address already proven by the caller
        :type verified_wallet_address: str | None
        :param chain: chain the address belongs to
        :type chain: str
        :return: the linked user, or None
        :rtype: django.contrib.auth.models.User | None
        """
        if not verified_wallet_address:
            return None
        return resolve_account(chain, verified_wallet_address)

    def get_user(self, user_id):
        """Return the user for ``user_id`` as required by the backend interface.

        :param user_id: primary key of the user
        :type user_id: int
        :return: the user, or None
        :rtype: django.contrib.auth.models.User | None
        """
        return get_user_model().objects.filter(pk=user_id).first()
