"""Discovery of widgets from their manifests.

Each widget keeps its own ``urls.py`` / ``routing.py`` (regex routes that the
existing ``widgets/urls.py`` and ``widgets/routing.py`` already auto-include).
This module replaces the hand-maintained ``INHOUSE_WIDGETS`` / ``THIRDPARTY_WIDGETS``
lists with manifest discovery: the presence of a ``widget.toml`` registers a widget.
"""

from pathlib import Path

from django.conf import settings
from django.urls import NoReverseMatch, reverse

import widgets
from widgethost.manifest import load_manifest

WIDGETS_PACKAGE = "widgets"


def _widgets_root():
    """Return the filesystem directory of the widgets package.

    :return: :class:`pathlib.Path`
    """
    return Path(widgets.__file__).resolve().parent


def discover_manifests():
    """Discover and load every widget manifest under the widgets package.

    :var manifests: collection of dotted-package and parsed-manifest pairs
    :type manifests: list
    :var manifest_path: full path to a discovered widget.toml file
    :type manifest_path: :class:`pathlib.Path`
    :var relative: widget directory path relative to the widgets package
    :type relative: :class:`pathlib.Path`
    :var dotted: dotted Python path of the widget package
    :type dotted: str
    :return: list
    """
    manifests = []
    for manifest_path in sorted(_widgets_root().rglob("widget.toml")):
        relative = manifest_path.parent.relative_to(_widgets_root())
        dotted = ".".join((WIDGETS_PACKAGE, *relative.parts))
        manifests.append((dotted, load_manifest(manifest_path)))
    return manifests


def discover_widgets():
    """Return discovered inhouse and thirdparty widget identifiers.

    :var inhouse: collection of discovered inhouse widget identifiers
    :type inhouse: list
    :var thirdparty: collection of discovered thirdparty widget identifiers
    :type thirdparty: list
    :var manifest: a discovered widget's parsed manifest
    :type manifest: :class:`widgethost.manifest.Manifest`
    :return: two-tuple
    """
    inhouse, thirdparty = [], []
    for _, manifest in discover_manifests():
        if manifest.origin == "inhouse":
            inhouse.append(manifest.id)
        else:
            thirdparty.append(manifest.id)
    return inhouse, thirdparty


_manifests_by_id = None


def manifests_by_id(refresh=False):
    """Return discovered manifests keyed by id, building the cache once.

    :param refresh: rebuild the cache instead of reusing it
    :type refresh: bool
    :var _manifests_by_id: process-wide cache of id to manifest
    :type _manifests_by_id: dict
    :return: dict
    """
    global _manifests_by_id
    if _manifests_by_id is None or refresh:
        _manifests_by_id = {
            manifest.id: manifest for _, manifest in discover_manifests()
        }
    return _manifests_by_id


def manifest_for(widget_id):
    """Return the manifest for `widget_id`, or None when it is not installed.

    :param widget_id: unique widget identifier
    :type widget_id: str
    :return: :class:`widgethost.manifest.Manifest`
    """
    return manifests_by_id().get(widget_id)


def swap_routers():
    """Return discovered swap-router widgets as (id, name) pairs for selection.

    A widget opts in by declaring ``category = "swap"`` in its manifest. The user
    settings page uses this to offer a preferred router; adding a router widget
    therefore makes it selectable with no settings-page change.

    :var routers: collection of (id, name) pairs for swap-category widgets
    :type routers: list
    :return: list
    """
    routers = [
        (manifest.id, manifest.name)
        for manifest in manifests_by_id().values()
        if getattr(manifest, "category", None) == "swap"
    ]
    return sorted(routers)


def swap_entry_url(router_id, value):
    """Return the swap widget shell URL for ``router_id`` and ``value``, or "".

    Single seam for how router widgets are mounted: each swap widget's shell URL
    is named after its widget id (e.g. "folks"). Returns "" when there is no
    router or the name can't be reversed, so callers degrade gracefully.

    :param router_id: chosen swap-router widget id
    :type router_id: str
    :param value: address or bundle hash to swap from
    :type value: str
    :return: str
    """
    if not router_id:
        return ""
    try:
        return reverse(router_id, args=[value])
    except NoReverseMatch:
        return ""


def swap_holdings_tmpl(router_id):
    """Return a holdings-URL template (literal ``ADDRESS`` placeholder) or "".

    Sibling of :func:`swap_entry_url`. Each swap widget names its htmx holdings
    partial ``"<router_id>_holdings"`` and accepts a 58-char address. We reverse
    it with a placeholder address and hand the browser a fill-in-the-address
    template, so the cached, user-agnostic accordion never embeds a per-user
    address -- the connected wallet's address is substituted client-side.

    :param router_id: chosen swap-router widget id
    :type router_id: str
    :return: str
    """
    if not router_id:
        return ""
    placeholder = "A" * 58
    try:
        url = reverse(f"{router_id}_holdings", args=[placeholder])
    except NoReverseMatch:
        return ""
    return url.replace(placeholder, "ADDRESS")


def swap_client_cfg(router_id):
    """Return a router's public swap-client config for the browser.

    :param router_id: the router key, e.g. ``"folks"`` or ``"haystack"``
    :type router_id: str
    :return: ``{"network", "referrer", "fee_bps", "api_key"}``
    :rtype: dict
    """
    prefix = router_id.upper()
    return {
        "network": getattr(settings, f"{prefix}_NETWORK", "mainnet"),
        "referrer": getattr(settings, f"{prefix}_REFERRER_ADDRESS", ""),
        "fee_bps": getattr(settings, f"{prefix}_FEE_BPS", 0),
        "api_key": getattr(settings, f"{prefix}_API_KEY", ""),
    }
