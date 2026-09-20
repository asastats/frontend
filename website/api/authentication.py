"""Authentication for the public API, with revocation a stateless JWT lacks.

`rest_framework_simplejwt` verifies a token by signature and expiry alone, so
a leaked credential stays valid until it expires. The only kill switch the
library offers out of the box is rotating `SIMPLE_JWT_KEY`, which invalidates
**every** token at once - `WIDGETS_API_TOKEN`, the token baked into the
published mobile app, and every third-party integration - and is therefore
unusable for the case it would actually be needed in.

`token_blacklist` is the documented alternative and is the wrong shape here: it
adds a table and a lookup per request, and by default covers *refresh* tokens
rather than the access tokens that are in circulation.

The move to `JWTAuthentication` already pays for a profile read on every API
request, so comparing the token's `iat` against one nullable field on that
profile buys instant, per-account revocation for an attribute read. See
`Profile.api_tokens_valid_from`.
"""

from datetime import datetime, timezone

from rest_framework_simplejwt.authentication import JWTAuthentication


class RevocableJWTAuthentication(JWTAuthentication):
    """`JWTAuthentication` that honours `Profile.api_tokens_valid_from`."""

    def get_user(self, validated_token):
        """Return the token's user, unless the token has been revoked.

        **Refused as authentication, not as permission.** A revoked credential
        is not a caller who may not do this - it is a caller we no longer
        believe is who the token says. That distinction is the difference
        between a 401 telling an integration to re-issue and a 403 telling it
        to buy a subscription it already has.

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

        # **A token that cannot prove when it was issued is refused once a
        # cutoff exists.** Every token simplejwt mints carries `iat`, so this
        # is unreachable in practice - and the safe direction for something
        # unreachable is the one that fails closed, because the alternative
        # would make omitting a claim a way around revocation.
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
