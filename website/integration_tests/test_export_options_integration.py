"""Integration tests for the export's options, checked before anything is queued.

The export flow itself is in `test_export_integration.py`, skipped on modest
hardware; an option the engine refuses is answered before processing starts, so
these run anywhere.
"""

from django.test import TestCase

from api.client import BackendError, start_export

#: Any address: a refused option is answered before the address is looked at.
ADDRESS = "STATSEJBVP7OTEF6R3XKSXEXGFXC62USSJQ6BQKILMHLX4GBDB2C5SNVBM"


class ExportOptionsTest(TestCase):
    """The engine's `_export_options`, reached through the client the site uses."""

    def _refused(self, options):
        with self.assertRaises(BackendError) as raised:
            start_export(ADDRESS, ADDRESS, options)
        return raised.exception.status_code

    def test_integration_export_refuses_an_unknown_fiat(self):
        self.assertEqual(self._refused({"fiat": "GBP"}), 400)

    def test_integration_export_refuses_a_lower_case_fiat(self):
        self.assertEqual(self._refused({"fiat": "eur"}), 400)

    def test_integration_export_refuses_an_unknown_provider(self):
        self.assertEqual(self._refused({"provider": "foobar"}), 400)
