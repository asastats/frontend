"""Integration tests for the CSV export flow.

**This whole module is skipped.** Tax processing is far too heavy for the
machine the suite currently runs on -- it is the one flow that cannot be
reduced to a cheap fixture, because the thing being tested *is* the long
backend job. The tests are written and ready; run them where there is enough
hardware, by deleting the ``pytestmark`` below.

They have therefore **never been executed**. Treat the first run as part of the
work: expect to adjust the polling budget in ``EXPORT_DEADLINE`` and possibly
the exact status keys, which are read from
:func:`api.client.export_status` and are the least-documented part of the
seam.

Why the flow is worth covering at all: it is the only stateful conversation the
website has with the backend, and it spans four endpoints that no test touches
today --

* ``POST   /api/v2/exports/``                 via :func:`api.client.start_export`
* ``GET    /api/v2/exports/<bundle>/status/`` via :func:`api.client.export_status`
* ``GET    /api/v2/exports/<bundle>/download/`` via :func:`api.client.download_export`
* ``DELETE /api/v2/exports/<bundle>/``        via :func:`api.client.reset_export`

-- and the backend runs the work through huey, so a huey process must be up or
the status never leaves ``processing_tax``. That is a real prerequisite, not an
incidental one: without it these tests fail by timing out, which looks like
slowness rather than a missing service.

``ExportPageTest`` is the cheap half -- it only reads status and renders -- and
is the sensible thing to un-skip first.

The lifecycle test mutates backend state, so it resets the export in
``tearDown`` whether or not it passed. A left-behind archive would make the
next run start from the finished state and skip the part being tested.
"""

import time
import zipfile
from io import BytesIO

import pytest
from django.test import TestCase

from api.client import download_export, export_status, reset_export, start_export

pytestmark = pytest.mark.skip("Will be tested on more powerful computer")

#: An address with almost no transaction history -- the cheapest thing that
#: still produces a real report. Tax processing walks the whole history, so
#: the addresses used elsewhere in these tests are far too expensive here.
TINY_ADDRESS = "STATSEJBVP7OTEF6R3XKSXEXGFXC62USSJQ6BQKILMHLX4GBDB2C5SNVBM"

#: How long to wait for huey to finish before giving up, in seconds.
EXPORT_DEADLINE = 600

#: Gap between status polls. Long enough not to hammer the backend while it is
#: doing the actual work.
POLL_INTERVAL = 5


def _wait_for_report(address, deadline=EXPORT_DEADLINE):
    """Poll until a report exists, and return the final status.

    :param address: address the export was started for
    :type address: str
    :param deadline: seconds to wait before giving up
    :type deadline: int
    :return: dict
    """
    started = time.time()
    status = export_status(address)
    while time.time() - started < deadline:
        if status.get("tax_report"):
            return status
        time.sleep(POLL_INTERVAL)
        status = export_status(address)
    return status


class ExportPageTest(TestCase):
    """Testing class for the export page itself.

    The cheap half: reads export status and renders. No processing is started,
    so this is the part to un-skip first on modest hardware.
    """

    def test_integration_export_page_renders_for_an_address(self):
        response = self.client.get(f"/export/{TINY_ADDRESS}/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "export.html")

    def test_integration_export_page_prepares_its_tax_context(self):
        """`prepare_tax_context` is what the template's URLs are built from."""
        response = self.client.get(f"/export/{TINY_ADDRESS}/")

        self.assertEqual(response.context["url_value"], TINY_ADDRESS)
        self.assertEqual(
            response.context["address"],
            [TINY_ADDRESS],
            "the page prepared a different address list than the url asked "
            "for, so the form would enqueue the wrong account",
        )

    def test_integration_export_status_answers_for_an_unprocessed_address(self):
        """The status endpoint must answer even with nothing to report.

        A missing export is a normal state, not an error -- the page asks
        before anything has ever been started.
        """
        status = export_status(TINY_ADDRESS)

        self.assertIsInstance(
            status,
            dict,
            f"status endpoint returned {type(status).__name__}: {status!r}",
        )


class ExportLifecycleTest(TestCase):
    """Testing class for the full start -> finish -> download -> reset cycle.

    One ordered test rather than four, because each step depends on the state
    the previous one left behind; split across tests they would either repeat
    the expensive processing or depend on execution order.
    """

    def tearDown(self):
        # Always clean up: a finished archive left on the backend would make
        # the next run start from the download state and never exercise
        # processing at all.
        try:
            reset_export(TINY_ADDRESS)
        except Exception:  # noqa: BLE001 - teardown must not mask a failure
            pass

    def test_integration_export_runs_end_to_end(self):
        reset_export(TINY_ADDRESS)

        with self.subTest("start"):
            start_export(TINY_ADDRESS, TINY_ADDRESS)
            status = export_status(TINY_ADDRESS)
            self.assertTrue(
                status.get("processing_tax") or status.get("tax_report"),
                "the backend reported neither processing nor a finished "
                f"report just after the job was enqueued: {status!r}. If this "
                "stays empty, huey is probably not running.",
            )

        with self.subTest("finish"):
            status = _wait_for_report(TINY_ADDRESS)
            self.assertTrue(
                status.get("tax_report"),
                f"no report after {EXPORT_DEADLINE}s: {status!r}. Either the "
                "budget is too small for this hardware, or huey is not "
                "consuming the queue.",
            )

        report = export_status(TINY_ADDRESS)["tax_report"]

        with self.subTest("report name is addressable"):
            # export_download splits the name on "_" and expects three parts,
            # using the last as the bundle value. A name shaped otherwise
            # redirects the user to the index with no explanation.
            parts = report.split("_")
            self.assertEqual(
                len(parts),
                3,
                f"report name {report!r} does not split into three parts, so "
                "core.views.export_download would redirect to the index "
                "instead of serving it",
            )
            self.assertEqual(parts[-1], TINY_ADDRESS)

        with self.subTest("download"):
            content = download_export(TINY_ADDRESS)
            self.assertTrue(content, "the download returned no bytes")
            self.assertTrue(
                zipfile.is_zipfile(BytesIO(content)),
                "the download is not a zip archive, though the view serves it "
                "as application/zip",
            )
            with zipfile.ZipFile(BytesIO(content)) as archive:
                names = archive.namelist()
            self.assertTrue(names, "the archive is empty")
            self.assertTrue(
                any(name.endswith(".csv") for name in names),
                f"the archive holds no CSV file: {names}",
            )

        with self.subTest("page offers the download once ready"):
            response = self.client.get(f"/export/{TINY_ADDRESS}/")
            self.assertEqual(
                response.context.get("finished_tax"),
                report,
                "the page does not know the report is ready, so the user is "
                "shown the processing form again instead of a download",
            )

        with self.subTest("reset"):
            reset_export(TINY_ADDRESS)
            status = export_status(TINY_ADDRESS)
            self.assertFalse(
                status.get("tax_report"),
                f"the report survived a reset: {status!r}. The refresh button "
                "on the page would then hand back the stale archive.",
            )
