"""Per-request widget access enforcement for the host site.

The mixin resolves the declared bundle data, counts the resolved addresses, and
gates the view on the user's permission against the widget manifest's
``required_permission`` band. It composes with the widgets app's existing
``BaseUserPassesTestMixin`` (authentication and profile presence checks).
"""

from api.widgets import bundle_and_addresses_from_path
from widgethost.manifest import can_access
from widgets.views import BaseUserPassesTestMixin


class WidgetAccessMixin(BaseUserPassesTestMixin):
    """Gate a widget view on the user's permission for the resolved bundle size.

    The host attaches the widget's manifest via ``as_view(manifest=...)``.

    :var WidgetAccessMixin.manifest: the widget's parsed manifest
    :type WidgetAccessMixin.manifest: :class:`widgethost.manifest.Manifest`
    :var WidgetAccessMixin.lookup_kwarg: URL kwarg holding the address or bundle
    :type WidgetAccessMixin.lookup_kwarg: str
    """

    manifest = None
    lookup_kwarg = "value"

    def resolve_bundle(self):
        """Resolve, cache, and return the bundle and addresses from the URL.

        :var value: address or bundle value found in the URL
        :type value: str
        :return: two-tuple
        """
        value = self.kwargs.get(self.lookup_kwarg)
        self.widget_bundle, self.widget_addresses = bundle_and_addresses_from_path(
            value
        )
        return self.widget_bundle, self.widget_addresses

    def test_func(self):
        """Return whether the current user may access this widget.

        :var addresses: space-separated resolved Algorand addresses
        :type addresses: str
        :var size: number of resolved Algorand addresses
        :type size: int
        :return: Boolean
        """
        _, addresses = self.resolve_bundle()
        size = len(addresses.split(" ")) if addresses else 0
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
