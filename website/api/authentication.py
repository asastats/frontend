"""Authentication for the public API, with revocation a stateless JWT lacks.

`rest_framework_simplejwt` verifies a token by signature and expiry alone, so a
leaked credential stays valid until it expires. Comparing the token's `iat`
against `Profile.api_tokens_valid_from` buys per-account revocation for one
attribute read, on a profile this path already loads.
"""

from datetime import datetime, timezone

from rest_framework_simplejwt.authentication import JWTAuthentication


class RevocableJWTAuthentication(JWTAuthentication):
    """`JWTAuthentication` that honours `Profile.api_tokens_valid_from`."""

    def get_user(self, validated_token):
        """Return the token's user, unless the token has been revoked.

        **Refused as authentication, not as permission.** A revoked credential
        is a caller we no longer believe is who the token says, so this is the
        401 that tells an integration to re-issue rather than the 403 that
        tells it to buy a subscription it already has.

        :param validated_token: the token simplejwt has already verified
        :type validated_token: :class:`rest_framework_simplejwt.tokens.Token`
        :var cutoff: the moment before which this account's tokens are refused
        :type cutoff: :class:`datetime.datetime` or None
        :return: the authenticated user
        """
        user = super().get_user(validated_token)

        profile = getattr(user, "profile", None)
        cutoff = getattr(profile, "api_tokens_valid_from", None)
        if cutoff is None:
            return user

        # A token that cannot say when it was issued is refused once a cutoff
        # exists. Every token simplejwt mints carries `iat`, so this is
        # unreachable - and failing closed is the safe direction, because the
        # alternative makes omitting a claim a way around revocation.
        issued = validated_token.payload.get("iat")
        if issued is None:
            raise self._revoked()

        if datetime.fromtimestamp(issued, tz=timezone.utc) < cutoff:
            raise self._revoked()

        return user

    @staticmethod
    def _revoked():
        """Return the error raised for a revoked token.

        Worded for the integration reading it: the token is dead and a new one
        from the profile page will work, which is true because re-issuing
        produces an `iat` after the cutoff.
        """
        from rest_framework_simplejwt.exceptions import AuthenticationFailed

        return AuthenticationFailed(
            "This API token has been revoked. Issue a new one from your "
            "profile's API token page.",
            code="token_revoked",
        )
