"""Testing module for :py:mod:`api.permissions` module."""

import pytest
from rest_framework.permissions import BasePermission

from api.permissions import CanAccessApiPermission


class TestCanAccessApiPermission:
    """Testing class for :class:`api.permissions.CanAccessApiPermission`.

    **The two modes are the subject.** The check has returned `True` since the
    API shipped, so turning it on is the day somebody's integration stops
    working - and the access logs cannot say which tier any caller holds. Shadow
    mode evaluates the tier exactly as enforcement will and lets the request
    through, so the question is answered by the same code that will later do the
    refusing rather than by a second implementation that could disagree.
    """

    def test_api_permissions_canaccessapipermission_issubclass_of_basepermission(self):
        assert issubclass(CanAccessApiPermission, BasePermission)

    # # a tier that may use the API
    @pytest.mark.parametrize("enforced", (True, False))
    def test_api_permissions_an_entitled_tier_is_allowed_either_way(
        self, mocker, settings, enforced
    ):
        """Enforcement decides what happens to the refused, never to the
        entitled - so a tier that qualifies must not be able to tell which mode
        is running."""
        settings.API_TIER_ENFORCED = enforced
        request = mocker.MagicMock()
        request.user.profile.can_access_api.return_value = True

        assert CanAccessApiPermission().has_permission(request, mocker.MagicMock())
        request.user.profile.can_access_api.assert_called_once_with()

    # # shadow mode
    def test_api_permissions_shadow_mode_lets_an_unentitled_caller_through(
        self, mocker, settings
    ):
        settings.API_TIER_ENFORCED = False
        request = mocker.MagicMock()
        request.user.profile.can_access_api.return_value = False

        assert CanAccessApiPermission().has_permission(request, mocker.MagicMock())

    def test_api_permissions_shadow_mode_reports_who_it_would_have_refused(
        self, mocker, settings
    ):
        """**The log is the whole point of the mode.** Letting them through
        without recording it would be the old unconditional `True` with extra
        steps, and the decision it exists to inform - who breaks when this is
        enforced - would still be unanswerable.
        """
        settings.API_TIER_ENFORCED = False
        logged = mocker.patch("api.permissions.logger")
        request = mocker.MagicMock()
        request.user.profile.can_access_api.return_value = False
        request.user.pk = 42
        request.user.profile.permission = 7
        request.path = "/api/v2/SOMEADDRESS/asas/"

        CanAccessApiPermission().has_permission(request, mocker.MagicMock())

        assert logged.warning.called
        reported = logged.warning.call_args.args
        # Who, what tier, and what they were reaching for: less than that and
        # the log cannot answer the question it was written for.
        assert 42 in reported
        assert 7 in reported
        assert "/api/v2/SOMEADDRESS/asas/" in reported

    def test_api_permissions_an_entitled_caller_is_not_logged(self, mocker, settings):
        """Most requests are entitled, and a line per request would bury the
        ones that matter."""
        settings.API_TIER_ENFORCED = False
        logged = mocker.patch("api.permissions.logger")
        request = mocker.MagicMock()
        request.user.profile.can_access_api.return_value = True

        CanAccessApiPermission().has_permission(request, mocker.MagicMock())

        assert not logged.warning.called

    # # enforcing
    def test_api_permissions_enforcing_refuses_an_unentitled_caller(
        self, mocker, settings
    ):
        settings.API_TIER_ENFORCED = True
        request = mocker.MagicMock()
        request.user.profile.can_access_api.return_value = False

        assert not CanAccessApiPermission().has_permission(request, mocker.MagicMock())
        request.user.profile.can_access_api.assert_called_once_with()

    # # exemptions
    def test_api_permissions_an_exempt_id_is_allowed_even_when_enforcing(
        self, mocker, settings
    ):
        """**For credentials that cannot be rotated on our schedule.**

        The mobile app ships a long-lived bearer token inside a released binary,
        so changing which account it names means an app release and a store
        review. Between deciding to enforce the tier gate and a new build
        reaching every phone, the app would simply be down.

        The id here is the one that token carries. Its *tier* is not knowable
        from this machine - the development database is not a copy of production
        and the account at that id is a different person entirely - so this
        pins the mechanism rather than any measurement of the app.
        """
        settings.API_TIER_ENFORCED = True
        settings.API_TIER_EXEMPT_USER_IDS = frozenset({355})
        request = mocker.MagicMock()
        request.user.pk = 355
        request.user.profile.can_access_api.return_value = False

        assert CanAccessApiPermission().has_permission(request, mocker.MagicMock())

    def test_api_permissions_an_exemption_does_not_read_the_tier_at_all(
        self, mocker, settings
    ):
        """The point is not to depend on where an account's tier sits, so it
        must not be consulted - an exemption that still read it could be undone
        by an unrelated change to that account."""
        settings.API_TIER_ENFORCED = True
        settings.API_TIER_EXEMPT_USER_IDS = frozenset({355})
        request = mocker.MagicMock()
        request.user.pk = 355

        CanAccessApiPermission().has_permission(request, mocker.MagicMock())

        assert not request.user.profile.can_access_api.called

    def test_api_permissions_a_non_exempt_id_is_still_refused(self, mocker, settings):
        """An exemption list that leaked would be worse than none: it is meant
        to name a handful of unrotatable credentials, not to soften the gate."""
        settings.API_TIER_ENFORCED = True
        settings.API_TIER_EXEMPT_USER_IDS = frozenset({355})
        request = mocker.MagicMock()
        request.user.pk = 356
        request.user.profile.can_access_api.return_value = False

        assert not CanAccessApiPermission().has_permission(request, mocker.MagicMock())

    def test_api_permissions_the_exemption_list_is_empty_by_default(self, settings):
        """An exemption nobody needs is one nobody should be able to forget
        about, so it is opt-in per deployment."""
        from django.conf import settings as configured

        assert configured.API_TIER_EXEMPT_USER_IDS == frozenset()

    # # a caller with no profile at all
    @pytest.mark.parametrize("enforced", (True, False))
    def test_api_permissions_a_profileless_user_never_counts_as_entitled(
        self, mocker, settings, enforced
    ):
        """**A permission check that fails open is not a permission check.**

        `JWTAuthentication` resolves a real user, but a user with no profile row
        is a broken account rather than a free one. Under enforcement that is a
        refusal; in shadow mode it is reported like any other, because it is
        exactly the kind of caller nobody would think to look for.
        """
        settings.API_TIER_ENFORCED = enforced
        request = mocker.MagicMock(spec=["user", "path"])
        request.user = mocker.MagicMock(spec=["pk"])
        request.user.pk = 3
        request.path = "/api/v2/x/"

        allowed = CanAccessApiPermission().has_permission(request, mocker.MagicMock())

        assert allowed is (not enforced)
