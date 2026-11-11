"""Testing module for :py:mod:`website.core.management.commands` module."""

import io
import re
from pathlib import Path
from unittest import mock

from django.core.management import call_command


class TestCheckPublicBundlesCommand:
    """Testing class for management command

    :py:mod:`core.management.commands.checkpublicbundles`."""

    def test_checkpublicbundles_command_output_for_no_update(self, mocker):
        mocked_check = mocker.patch(
            "core.management.commands.checkpublicbundles.check_public_bundles",
            return_value=[],
        )
        with mock.patch("django.core.management.base.OutputWrapper.write") as output:
            call_command("checkpublicbundles")
            output.assert_called_once_with("No changes")
        mocked_check.assert_called_once_with()

    def test_checkpublicbundles_command_output_for_update(self, mocker):
        mocked_check = mocker.patch(
            "core.management.commands.checkpublicbundles.check_public_bundles",
            return_value=["bundle1", "bundle2"],
        )
        with mock.patch("django.core.management.base.OutputWrapper.write") as output:
            call_command("checkpublicbundles")
            output.assert_called_once_with("Updated: bundle1 bundle2")
        mocked_check.assert_called_once_with()


class TestDeleteDeactivatedCommand:
    """Testing class for management command

    :py:mod:`core.management.commands.deletedeactivated`."""

    def test_deletedeactivated_command_output_for_no_deletion(self, mocker):
        mocked_delete = mocker.patch(
            "core.management.commands.deletedeactivated.delete_deactivated",
            return_value=0,
        )
        with mock.patch("django.core.management.base.OutputWrapper.write") as output:
            call_command("deletedeactivated")
            output.assert_called_once_with("0 deactivated accounts deleted!")
        mocked_delete.assert_called_once_with()

    def test_deletedeactivated_command_output_for_deleted_accounts(self, mocker):
        mocked_delete = mocker.patch(
            "core.management.commands.deletedeactivated.delete_deactivated",
            return_value=5,
        )
        with mock.patch("django.core.management.base.OutputWrapper.write") as output:
            call_command("deletedeactivated")
            output.assert_called_once_with("5 deactivated accounts deleted!")
        mocked_delete.assert_called_once_with()


class TestPermissionUpdaterCommand:
    """Testing class for management command

    :py:mod:`core.management.commands.permissionsupdater`."""

    def test_permissionupdater_command_output(self, mocker):
        mocked_run = mocker.patch(
            "core.management.commands.permissionsupdater.run_permissions_update"
        )
        with mock.patch("django.core.management.base.OutputWrapper.write") as output:
            call_command("permissionsupdater")
            output.assert_called_once_with("Permissions updater exited")
        mocked_run.assert_called_once_with()


class TestSyncHoldingsCommand:
    """Testing class for management command

    :py:mod:`core.management.commands.syncholdings`."""

    def test_syncholdings_command_output(self, mocker):
        mocked_sync = mocker.patch(
            "core.management.commands.syncholdings.sync_holdings",
            return_value=(3, 1),
        )
        with mock.patch("django.core.management.base.OutputWrapper.write") as output:
            call_command("syncholdings")
            output.assert_called_once_with("Recorded 3, updated 1")
        mocked_sync.assert_called_once_with()


class TestRenderErrorPagesCommand:
    """Testing class for management command
    :class:`core.management.commands.rendererrorpages.Command`.
    """

    def _run(self, output):
        out = io.StringIO()
        call_command("rendererrorpages", "--output", str(output), stdout=out)
        return out.getvalue()

    def test_rendererrorpages_writes_every_nginx_page_as_plain_html(self, tmp_path, settings):
        from core.management.commands.rendererrorpages import NGINX_ERROR_PAGES

        settings.WEBSITE_URL = "https://www.example.com"
        output = tmp_path / "errorpages"

        assert self._run(output).strip() == f"4 error pages written to {output}"

        assert sorted(p.name for p in output.iterdir()) == sorted(NGINX_ERROR_PAGES)
        for name in NGINX_ERROR_PAGES:
            html = (output / name).read_text()
            assert "{{" not in html and "{%" not in html, name
            assert "<!doctype html>" in html.lower(), name
        assert 'href="https://www.example.com"' in (output / "500.html").read_text()
        # error_style.html's palette is inlined, not left as an include.
        assert "--bg" in (output / "500.html").read_text()
        assert "in-app" not in (output / "404.html").read_text()
        assert {oct(p.stat().st_mode & 0o777) for p in output.iterdir()} == {"0o644"}

    def test_rendererrorpages_second_run_writes_nothing(self, tmp_path):
        self._run(tmp_path)
        before = {p.name: p.stat().st_mtime_ns for p in tmp_path.iterdir()}

        assert self._run(tmp_path).startswith("0 error pages written")

        assert {p.name: p.stat().st_mtime_ns for p in tmp_path.iterdir()} == before

    def test_rendererrorpages_rewrites_a_changed_page(self, tmp_path):
        self._run(tmp_path)
        (tmp_path / "500.html").write_text("stale")

        assert self._run(tmp_path).startswith("1 error pages written")
        assert "Internal server error" in (tmp_path / "500.html").read_text()
        assert not list(tmp_path.glob("*.tmp"))

    def test_rendererrorpages_defaults_to_the_setting(self, tmp_path, settings):
        settings.ERROR_PAGES_ROOT = tmp_path / "default"
        out = io.StringIO()

        call_command("rendererrorpages", stdout=out)

        assert (tmp_path / "default" / "500.html").exists()

    def test_rendererrorpages_pages_match_the_nginx_locations(self):
        from core.management.commands.rendererrorpages import NGINX_ERROR_PAGES

        conf = (
            Path(__file__).resolve().parents[3]
            / "deploy/roles/nginx/templates/site_server_block.conf"
        ).read_text()
        served = set(re.findall(r"location = /(\S+\.html)", conf)) - {"robots.txt"}

        assert served == set(NGINX_ERROR_PAGES)
