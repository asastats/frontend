"""Testing module for :py:mod:`widgethost.registry` module."""

import widgethost.registry as registry
from widgethost.registry import discover_manifests, discover_widgets, manifest_for


class TestWidgethostRegistryDiscoverManifests:
    """Testing class for :py:func:`widgethost.registry.discover_manifests`."""

    def test_widgethost_registry_discover_manifests_functionality(
        self, tmp_path, mocker
    ):
        widget_dir = tmp_path / "inhouse" / "historic"
        widget_dir.mkdir(parents=True)
        (widget_dir / "widget.toml").write_text("")
        mocker.patch("widgethost.registry._widgets_root", return_value=tmp_path)
        manifest = mocker.MagicMock()
        mocker.patch("widgethost.registry.load_manifest", return_value=manifest)
        result = dict(discover_manifests())
        assert result["widgets.inhouse.historic"] is manifest


class TestWidgethostRegistryDiscoverWidgets:
    """Testing class for :py:func:`widgethost.registry.discover_widgets`."""

    def test_widgethost_registry_discover_widgets_splits_by_origin(self, mocker):
        inhouse = mocker.MagicMock(origin="inhouse", id="historic")
        thirdparty = mocker.MagicMock(origin="thirdparty", id="swap")
        mocker.patch(
            "widgethost.registry.discover_manifests",
            return_value=[("a", inhouse), ("b", thirdparty)],
        )
        assert discover_widgets() == (["historic"], ["swap"])


class TestWidgethostRegistryManifestFor:
    """Testing class for :py:func:`widgethost.registry.manifest_for`."""

    def test_widgethost_registry_manifest_for_returns_manifest(self, mocker):
        registry._manifests_by_id = None
        manifest = mocker.MagicMock(id="historic")
        mocker.patch(
            "widgethost.registry.discover_manifests",
            return_value=[("a", manifest)],
        )
        assert manifest_for("historic") is manifest
        registry._manifests_by_id = None

    def test_widgethost_registry_manifest_for_missing_returns_none(self, mocker):
        registry._manifests_by_id = None
        mocker.patch("widgethost.registry.discover_manifests", return_value=[])
        assert manifest_for("absent") is None
        registry._manifests_by_id = None
