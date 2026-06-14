"""Testing module for :py:mod:`core.context_processors` module."""

from api.client import BackendError
from core.context_processors import deployment_capabilities


class TestDeploymentCapabilities:
    """Testing class for :func:`deployment_capabilities` context processor."""

    # # cache hit
    def test_deployment_capabilities_returns_cached_value(self, mocker):
        cache = mocker.patch("core.context_processors.cache")
        cache.get.return_value = {"permission": 5}
        fetch = mocker.patch("core.context_processors.fetch_capabilities")

        result = deployment_capabilities(mocker.Mock())

        assert result == {"deployment_capabilities": {"permission": 5}}
        fetch.assert_not_called()
        cache.set.assert_not_called()

    # # cache miss -> fetch
    def test_deployment_capabilities_fetches_and_caches_on_miss(self, mocker):
        cache = mocker.patch("core.context_processors.cache")
        cache.get.return_value = None
        fetch = mocker.patch(
            "core.context_processors.fetch_capabilities",
            return_value={"permission": 3},
        )

        result = deployment_capabilities(mocker.Mock())

        assert result == {"deployment_capabilities": {"permission": 3}}
        fetch.assert_called_once_with()
        cache.set.assert_called_once_with(
            "deployment_capabilities", {"permission": 3}, 300
        )

    # # backend failure -> zero-permission stub
    def test_deployment_capabilities_stub_on_backend_error(self, mocker):
        cache = mocker.patch("core.context_processors.cache")
        cache.get.return_value = None
        mocker.patch(
            "core.context_processors.fetch_capabilities",
            side_effect=BackendError("backend down"),
        )
        warning = mocker.patch("core.context_processors.logger.warning")

        result = deployment_capabilities(mocker.Mock())

        assert result == {"deployment_capabilities": {"permission": 0}}
        cache.set.assert_called_once_with(
            "deployment_capabilities", {"permission": 0}, 300
        )
        warning.assert_called_once_with(
            "Could not fetch deployment capabilities", exc_info=True
        )

    # # unexpected failure -> zero-permission stub
    def test_deployment_capabilities_stub_on_unexpected_error(self, mocker):
        cache = mocker.patch("core.context_processors.cache")
        cache.get.return_value = None
        mocker.patch(
            "core.context_processors.fetch_capabilities",
            side_effect=ValueError("unexpected"),
        )
        warning = mocker.patch("core.context_processors.logger.warning")

        result = deployment_capabilities(mocker.Mock())

        assert result == {"deployment_capabilities": {"permission": 0}}
        cache.set.assert_called_once_with(
            "deployment_capabilities", {"permission": 0}, 300
        )
        warning.assert_called_once_with(
            "Could not fetch deployment capabilities", exc_info=True
        )
