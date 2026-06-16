"""Discovery of widgets from their manifests.

Each widget keeps its own ``urls.py`` / ``routing.py`` (regex routes that the
existing ``widgets/urls.py`` and ``widgets/routing.py`` already auto-include).
This module replaces the hand-maintained ``INHOUSE_WIDGETS`` / ``THIRDPARTY_WIDGETS``
lists with manifest discovery: the presence of a ``widget.toml`` registers a widget.
"""

from pathlib import Path

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
