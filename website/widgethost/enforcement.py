"""Per-request widget access enforcement for the host site.

The reusable gate compares the user's permission against the widget manifest's
``required_permission`` band for a resolved address count. Each widget resolves
its own bundle/addresses (via the host's ``bundle_and_addresses_from_path``) and
calls :meth:`WidgetAccessMixin.manifest_test_func` with the resolved count, so the
mixin stays agnostic of how a widget reads its URL value. It composes with the
widgets app's existing ``BaseUserPassesTestMixin`` (authentication and profile
presence checks).
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from rest_framework.exceptions import ValidationError as ApiValidationError

from widgethost.manifest import can_access
from widgets.views import BaseUserPassesTestMixin


class WidgetAccessMixin(BaseUserPassesTestMixin):
    """Provide a manifest-driven permission gate for widget views.

    The widget sets ``manifest`` (a class attribute or via ``as_view``) and calls
    :meth:`manifest_test_func` from its own ``test_func`` after resolving the size.

    :var WidgetAccessMixin.manifest: the widget's parsed manifest
    :type WidgetAccessMixin.manifest: :class:`widgethost.manifest.Manifest`
    """

    manifest = None
    #: The URL value's validation error, set when `test_func` rejected it.
    invalid_path = None

    def get_test_func(self):
        """Return the view's test function, failing instead of raising on a bad URL.

        An invalid address or unknown bundle hash in the URL raised a 500 from
        `bundle_and_addresses_from_path`; see docs/logbook.md.

        :return: callable
        """
        test_func = super().get_test_func()

        def checked():
            try:
                return test_func()

            except (ValidationError, ApiValidationError) as error:
                # the URL helpers raise DRF's; Django's carries `messages`
                details = getattr(error, "messages", None) or error.detail
                self.invalid_path = str(details[0] if isinstance(details, list) else details)
                return False

        return checked

    def handle_no_permission(self):
        """Send an invalid URL value back to the index with its error, else refuse.

        :return: :class:`django.http.HttpResponse`
        """
        if self.invalid_path:
            messages.error(self.request, self.invalid_path)
            return redirect("index")

        return super().handle_no_permission()

    def manifest_test_func(self, size):
        """Return whether the user clears the manifest gate for `size` addresses.

        :param size: number of resolved Algorand addresses
        :type size: int
        :return: Boolean
        """
        return super().test_func(self._access_callback, size)

    def _access_callback(self, profile, size):
        """Return whether `profile` clears the manifest gate for `size` addresses.

        :param profile: the current user's profile
        :type profile: :class:`core.models.Profile`
        :param size: number of resolved Algorand addresses
        :type size: int
        :return: Boolean
        """
        return can_access(profile.permission, self.manifest.required_permission, size)
