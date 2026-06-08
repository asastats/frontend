"""Per-request widget access enforcement for the host site.

The reusable gate compares the user's permission against the widget manifest's
``required_permission`` band for a resolved address count. Each widget resolves
its own bundle/addresses (via the host's ``bundle_and_addresses_from_path``) and
calls :meth:`WidgetAccessMixin.manifest_test_func` with the resolved count, so the
mixin stays agnostic of how a widget reads its URL value. It composes with the
widgets app's existing ``BaseUserPassesTestMixin`` (authentication and profile
presence checks).
"""

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
