"""Every page names static files that actually exist.

Production serves static files through ``ManifestStaticFilesStorage``, and
under it ``{% static %}`` **raises** for a path with no entry in
``staticfiles.json``. Development's storage returns the URL and lets the
browser 404 it. So a template that names a file which is not there is a 500 in
production and a silent nothing everywhere else -- including in every other
test in this suite.

That is not hypothetical. ``_swap_entry.html`` loaded
``<router>/<router>-sdk.bundle.js`` for whichever router the reader preferred.
Three routers ship that file; the ASA Stats router does not, because it quotes
in our engine and its adapter lives in ``swap/swap.js``. Choosing it turned the
per-user partial into a 500, which took the swap marker, the modal, ``swap.js``
*and* the Dust Sweep with it -- and left the Swap button to fall through to the
no-JS ``href`` it carries, so the page appeared to reload when clicked. It
reached every reader who had never opened the settings page, because that
router also happens to sort first among the four ids.

``config/settings/zz_manifest_check.py`` was written for exactly this and
wired to nothing. This module is the wiring: it collects static into a
throwaway directory under the production storage -- four seconds, 941 files --
and renders the pages under it.

**Read `test_the_manifest_is_actually_in_force` first.** Without it, every
assertion here would pass just as happily with the ordinary storage, and this
module would be a decorative 500-test that cannot fail.
"""

import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse

from core.staticfiles import BUILD_INPUTS
from walletauth.models import LinkedAddress
from widgethost.registry import swap_routers

#: Collected into a throwaway directory rather than the project's real
#: STATIC_ROOT, which sits outside the repository and is not the suite's to
#: write to.
STATIC_ROOT = tempfile.mkdtemp(prefix="asastats-manifest-check-")

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

MANIFEST_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    },
}


@override_settings(STATIC_ROOT=STATIC_ROOT, STORAGES=MANIFEST_STORAGE)
class TestPagesUnderTheProductionStaticStorage(TestCase):
    """Render under the storage production uses, not the one tests use."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # inside setUpClass so the class-level override is already enabled:
        # collectstatic has to write the manifest through the same storage the
        # renders below will read it back through
        try:
            call_command("collectstatic", interactive=False, verbosity=0)
        except Exception:
            # `TestCase.setUpClass` opened a class-wide atomic block above, and
            # `tearDownClass` -- the only thing that closes it -- does not run
            # when `setUpClass` raises. Left open it takes the connection down
            # with it, and every DB-touching test AFTER this class fails with
            # "the connection is closed": one collectstatic failure here cost
            # 584 failures and 228 errors in a CI run, none of them related.
            # Django does exactly this around its own `setUpTestData`.
            #
            # `cls_atomics` is absent only on a backend without transactions,
            # where there is nothing open to roll back.
            if getattr(cls, "cls_atomics", None):
                cls._rollback_atomics(cls.cls_atomics)
            raise

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(STATIC_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="manifest@example.com",
            email="manifest@example.com",
            password="top_secret",
        )
        self.user.profile.address = ADDRESS
        self.user.profile.save()
        LinkedAddress.objects.create(
            profile=self.user.profile,
            address=ADDRESS,
            canonical_address=ADDRESS,
            chain="algorand",
            auth_method="algorand_wallet",
            is_primary=True,
            login_enabled=True,
        )
        self.client.force_login(self.user)

    def test_the_manifest_is_actually_in_force(self):
        """The anchor. Everything below is worthless if this does not hold.

        `{% static %}` must *raise* for a missing file. If the override did not
        take -- a settings module that resets STORAGES, a collectstatic that
        wrote nowhere -- then rendering a bad path returns a URL instead, every
        other test here passes unconditionally, and this module becomes a
        check that cannot fail. This project has shipped that shape of test
        before.
        """
        template = Template("{% load static %}{% static 'no/such/file.js' %}")

        with self.assertRaises(ValueError) as caught:
            template.render(Context({}))

        assert "no/such/file.js" in str(caught.exception)

    def test_a_file_that_exists_still_resolves(self):
        """The other half: the anchor above must not be passing on everything."""
        template = Template("{% load static %}{% static 'swap/swap.js' %}")

        assert "swap" in template.render(Context({}))

    def test_every_swap_router_renders_the_entry_partial(self):
        """The regression, swept across routers rather than sampled.

        The partial names a per-router SDK bundle, and the fault was in which
        router was chosen -- so testing one would have picked a working one
        three times in four, and the broken one was the default.
        """
        url = reverse("swap_entry", args=[ADDRESS])
        for router_id, _ in swap_routers():
            with self.subTest(router=router_id):
                self.user.profile.preferred_router = router_id
                self.user.profile.save()

                response = self.client.get(url)

                assert response.status_code == 200, (
                    f"the {router_id} router's swap entry is a "
                    f"{response.status_code}; it names a static file that "
                    "production's storage has no entry for"
                )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_address_page_renders(
        self, mocked_account, mocked_status, mocked_capabilities
    ):
        """The heaviest page, and the one that pulls in the most templates."""
        import json
        from pathlib import Path

        sample = (
            Path(__file__).resolve().parent.parent.parent
            / "utils"
            / "tests"
            / "sample_serialized_540A5.json"
        )
        mocked_account.return_value = json.loads(sample.read_text())
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 100}

        assert self.client.get(f"/{ADDRESS}").status_code == 200

    def test_the_home_page_renders(self):
        assert self.client.get("/").status_code == 200

    def test_the_tailwind_build_inputs_are_not_collected(self):
        """They are not servable, and one of them is 110 MB of executable.

        `input.css` opens with `@import "tailwindcss"`, a package name that
        post-processing tries to resolve as a path -- so collecting it either
        aborts the whole collectstatic (CI, where the toolchain is absent) or
        succeeds by publishing the standalone Tailwind binary that happens to
        sit at that path (every developer machine, and the server).

        Asserted against the collected tree rather than the manifest: a file
        can be copied without being post-processed, and copying it is already
        the problem.
        """
        collected = Path(STATIC_ROOT)

        for name in BUILD_INPUTS:
            with self.subTest(name=name):
                assert not (collected / name).exists(), (
                    f"{name} is a Tailwind build input, and collectstatic put "
                    "it in STATIC_ROOT; see core/staticfiles.py"
                )

        # the anchor for the four above: the build's *output* is still there,
        # so this is not passing because collectstatic skipped css/ entirely
        assert (collected / "css" / "style.tw.css").exists()
