"""Testing module for :py:mod:`widgethost.access` module."""

from widgethost.access import can_access_widget


class TestWidgethostAccessCanAccessWidget:
    """Testing class for :py:func:`widgethost.access.can_access_widget`."""

    def test_widgethost_access_can_access_widget_for_installed(self, mocker):
        manifest = mocker.MagicMock(required_permission=5)
        mocker.patch("widgethost.access.manifest_for", return_value=manifest)
        gate = mocker.patch("widgethost.access.can_access", return_value=True)
        profile = mocker.MagicMock(permission=9)
        assert can_access_widget("historic", profile, 2) is True
        gate.assert_called_once_with(9, 5, 2)

    def test_widgethost_access_can_access_widget_for_missing(self, mocker):
        mocker.patch("widgethost.access.manifest_for", return_value=None)
        assert can_access_widget("nope", mocker.MagicMock(), 2) is False
