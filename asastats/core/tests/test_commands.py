"""Testing module for :py:mod:`asastats.core.management.commands` module."""

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
