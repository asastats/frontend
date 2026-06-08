"""Discovery and wiring of widgets from their manifests.

Replaces hand-editing of ``widgets/urls.py`` and ``widgets/routing.py``. Those
modules call :func:`widget_urlpatterns` / :func:`widget_websocket_urlpatterns`,
which discover every ``widget.toml`` under the widgets package and assemble the
route and consumer lists. Each widget declares its own paths and route names in
its manifest, so the assembled URLs match the widget's own front-end; the
registry imposes no extra prefix or namespace.
"""

import importlib
from pathlib import Path

from django.urls import path

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


def _import_attribute(dotted_package, reference):
    """Import and return the attribute named by `reference` in the package.

    :param dotted_package: dotted Python path of the widget package
    :type dotted_package: str
    :param reference: module-and-attribute reference, e.g. "views.HistoricView"
    :type reference: str
    :var module_name: attribute's module reference within the widget package
    :type module_name: str
    :var attribute_name: attribute name within the module
    :type attribute_name: str
    :var module: imported module object
    :type module: module
    :return: object
    """
    module_name, attribute_name = reference.rsplit(".", 1)
    module = importlib.import_module(f"{dotted_package}.{module_name}")
    return getattr(module, attribute_name)


def widget_urlpatterns():
    """Assemble and return the URL patterns for every discovered widget.

    :var patterns: collection of assembled widget route patterns
    :type patterns: list
    :var dotted: dotted Python path of a widget package
    :type dotted: str
    :var manifest: a discovered widget's parsed manifest
    :type manifest: :class:`widgethost.manifest.Manifest`
    :var route: a single route declaration from the manifest
    :type route: dict
    :var view: imported view class for a route
    :type view: object
    :return: list
    """
    patterns = []
    for dotted, manifest in discover_manifests():
        for route in manifest.routes:
            view = _import_attribute(dotted, route["view"])
            patterns.append(
                path(
                    route["path"],
                    view.as_view(manifest=manifest),
                    name=route["name"],
                )
            )
    return patterns


def widget_websocket_urlpatterns():
    """Assemble and return the websocket patterns for every discovered widget.

    :var patterns: collection of assembled widget consumer patterns
    :type patterns: list
    :var dotted: dotted Python path of a widget package
    :type dotted: str
    :var manifest: a discovered widget's parsed manifest
    :type manifest: :class:`widgethost.manifest.Manifest`
    :var consumer_route: a single consumer declaration from the manifest
    :type consumer_route: dict
    :var consumer: imported consumer class for a route
    :type consumer: object
    :return: list
    """
    patterns = []
    for dotted, manifest in discover_manifests():
        for consumer_route in manifest.consumers:
            consumer = _import_attribute(dotted, consumer_route["consumer"])
            patterns.append(path(consumer_route["path"], consumer.as_asgi()))
    return patterns
