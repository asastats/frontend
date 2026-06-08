"""User access checks for widgets, resolved by widget id via the registry.

Lets the host (core models, template filters) ask whether a user may use a
widget without importing that widget's modules — so a widget being absent yields
a denied result rather than an import error.
"""

from widgethost.manifest import can_access
from widgethost.registry import manifest_for


def can_access_widget(widget_id, profile, size):
    """Return whether `profile` may access the widget for `size` addresses.

    Returns False when the widget identified by `widget_id` is not installed.

    :param widget_id: unique widget identifier
    :type widget_id: str
    :param profile: the user's profile
    :type profile: :class:`core.models.Profile`
    :param size: number of Algorand addresses
    :type size: int
    :var manifest: the widget's parsed manifest, or None when not installed
    :type manifest: :class:`widgethost.manifest.Manifest`
    :return: Boolean
    """
    manifest = manifest_for(widget_id)
    if manifest is None:
        return False
    return can_access(profile.permission, manifest.required_permission, size)
