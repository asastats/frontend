"""Django system checks for credentials that fail silently.

``WIDGETS_API_TOKEN`` is a long-lived JWT the widget host presents to our own
API. Nothing renders it, nothing logs it, and no page breaks when it goes bad:
the only symptom is a 401 from an endpoint most of the suite never calls. It
has gone wrong twice in two different ways, and both times the discovery came
from running a test suite nobody runs routinely:

* the token sat expired for nine months;
* its replacement was signed with the *engine's* ``SIMPLE_JWT_KEY`` rather than
  this project's. The two are separate ``.env`` files, and the frontend is what
  validates the token -- ``SIMPLE_JWT["SIGNING_KEY"]`` here is the frontend's
  key. A token minted on the other side fails with "Given token not valid for
  any token type", which reads like an expiry problem and is not one.

A system check turns both into a message on every ``manage.py`` invocation --
so a deploy that would have shipped a dead token says so before it restarts
anything. Validation goes through ``AccessToken`` rather than a hand-rolled
decode, so what is checked here is exactly what DRF will do at request time.

Severities are chosen so that only an unambiguous misconfiguration blocks a
command: a token that is present but broken is an Error, while an absent one is
a Warning, because a checkout that never calls the widget API is a normal state
in development. Silence any of these through ``SILENCED_SYSTEM_CHECKS``.
"""

from datetime import datetime, timezone

from django.conf import settings
from django.core.checks import Error, Warning, register

#: How close to expiry the token may get before the check starts complaining.
#: A year-long token that is inside its final month needs minting well before
#: the day it dies, not on it.
EXPIRY_WARNING_DAYS = 30

#: Prefix for this project's check ids, keeping them out of Django's namespace.
ID_PREFIX = "asastats"


def _expiry(token):
    """Return `token`'s expiry as an aware datetime, or None.

    :param token: a validated token instance
    :type token: :class:`rest_framework_simplejwt.tokens.AccessToken`
    :return: :class:`datetime.datetime` or None
    """
    exp = token.payload.get("exp")
    if not exp:
        return None
    return datetime.fromtimestamp(exp, tz=timezone.utc)


@register()
def check_widgets_api_token(app_configs, **kwargs):
    """Validate WIDGETS_API_TOKEN against this project's signing key.

    :param app_configs: apps being checked, unused -- this is a settings check
    :type app_configs: list
    :return: list
    """
    # Imported here rather than at module scope: checks are registered from
    # AppConfig.ready(), and simplejwt pulls in the user model.
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import AccessToken

    token = getattr(settings, "WIDGETS_API_TOKEN", "")
    key = getattr(settings, "SIMPLE_JWT_KEY", "")

    if not key:
        return [
            Error(
                "SIMPLE_JWT_KEY is empty, so no JWT this project issues or "
                "accepts can be verified.",
                hint=(
                    "Set SIMPLE_JWT_KEY in website/.env. It is the signing key "
                    "for SIMPLE_JWT and must match the key the engine is "
                    "started with -- see integration_tests/conftest.py, which "
                    "forces it into the backend's environment for that reason."
                ),
                id=f"{ID_PREFIX}.E001",
            )
        ]

    if not token:
        return [
            Warning(
                "WIDGETS_API_TOKEN is not set, so calls to our own API from "
                "the widget host will be rejected with 401.",
                hint=(
                    "Run website/mint-widgets-token.sh to create one. Harmless "
                    "in a checkout that never exercises the widget API."
                ),
                id=f"{ID_PREFIX}.W001",
            )
        ]

    try:
        parsed = AccessToken(token)
    except TokenError as exc:
        # simplejwt reports expiry and a bad signature through the same
        # exception type, and the two need opposite advice -- so the hint is
        # chosen from the message rather than being one paragraph covering
        # both. Guessing wrong here is what cost an afternoon: "token not
        # valid for any token type" was read as expiry when the token had ten
        # months left on it and simply carried the other project's key.
        if "expired" in str(exc).lower():
            hint = (
                "The token has lapsed. Mint a replacement from this directory "
                "with website/mint-widgets-token.sh."
            )
        else:
            hint = (
                "The token did not verify, which usually means it was minted "
                "somewhere other than this project: SIMPLE_JWT signs with this "
                "project's SIMPLE_JWT_KEY, and one minted against the engine's "
                "key fails here even though its expiry is fine. Mint a new one "
                "from this directory with website/mint-widgets-token.sh."
            )
        return [
            Error(
                f"WIDGETS_API_TOKEN is not usable: {exc}",
                hint=hint,
                id=f"{ID_PREFIX}.E002",
            )
        ]

    expires = _expiry(parsed)
    if expires is None:
        return []

    remaining = expires - datetime.now(tz=timezone.utc)
    if remaining.days <= EXPIRY_WARNING_DAYS:
        return [
            Warning(
                f"WIDGETS_API_TOKEN expires in {remaining.days} day(s), on "
                f"{expires:%Y-%m-%d}.",
                hint=(
                    "Mint a replacement with website/mint-widgets-token.sh. "
                    "Once it lapses the widget API returns 401 and nothing "
                    "logs a reason."
                ),
                id=f"{ID_PREFIX}.W002",
            )
        ]

    return []


@register()
def check_export_tier_limits(app_configs, **kwargs):
    """Warn when EXPORT_TIERS_ADDRESSES_LIMIT leaves the CSV export unreachable.

    The same class of failure as the token above: nothing errors, nothing logs,
    and the only symptom is a link that is not on the page. The address page
    gates its CSV export on `tier_allows`, which reads these limits, and the
    fallbacks in `exportpermissions._DEFAULT_LIMITS` give free, Intro,
    Asastatser and Professional **zero** addresses each. So a deployment that
    does not set this variable does not get a conservative default -- it gets a
    site where only a Cluster-tier reader may export anything at all, while the
    Historic data link beside it keeps working because it is gated by a
    different mechanism entirely.

    That combination is what makes it hard to diagnose from the page: one of two
    adjacent links disappears, which reads like a bug in that link rather than a
    setting nobody set. It cost a full investigation -- the deployment
    permission, the reader's tier, the shared cache entry and the browser
    session were all eliminated first.

    A Warning rather than an Error, for the reason the token check gives: a
    checkout that never exercises CSV export is a normal state in development,
    and only an unambiguous misconfiguration should block a command.

    :param app_configs: apps being checked, unused -- this is a settings check
    :type app_configs: list
    :return: list
    """
    from core.exportpermissions import _DEFAULT_LIMITS

    limits = getattr(settings, "EXPORT_TIERS_ADDRESSES_LIMIT", None) or {}
    if limits:
        return []

    blocked = sorted(
        tier for tier, size in _DEFAULT_LIMITS.items() if tier != "Cluster" and size < 1
    )
    if not blocked:
        return []

    return [
        Warning(
            "EXPORT_TIERS_ADDRESSES_LIMIT is not set, so the built-in defaults "
            "apply and these tiers may not export even a single address: "
            f"{', '.join(blocked)}. The CSV export link is hidden on the "
            "address page for every reader below Cluster.",
            hint=(
                "Set EXPORT_TIERS_ADDRESSES_LIMIT in the environment the server "
                'runs in, in the form "free:5,Intro:6,Asastatser:7,'
                'Professional:8,Cluster:10". It is read from os.environ at '
                "import time, so a server started before the variable was "
                "exported keeps the old, empty value until it is restarted."
            ),
            id=f"{ID_PREFIX}.W002",
        )
    ]
