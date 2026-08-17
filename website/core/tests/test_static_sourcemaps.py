"""No shipped asset may point at a sourcemap that is not shipped with it.

A `//# sourceMappingURL=` comment naming a file that does not exist is
invisible in development -- the browser requests it, gets a 404, and carries
on. Under ManifestStaticFilesStorage it is fatal: collectstatic follows the
reference, cannot hash what is not there, and aborts the deploy with

    ValueError: The file 'historic/hammer.min.js.map' could not be found

That is exactly what a vendored copy of hammerjs did, and it has now been
reintroduced twice by a file being overwritten with its upstream version. The
strictness is worth keeping -- it is the same check that would catch a typo in
any asset reference -- so the dangling pointer is what has to go, and this
test is what notices when it comes back.

Runs in milliseconds against the source tree, so the failure arrives while
someone is editing rather than while they are deploying.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

#: `//# sourceMappingURL=<path>`, the form browsers and collectstatic both read.
SOURCEMAP = re.compile(r"sourceMappingURL=([^\s*'\"]+)")

#: Data-uri maps are inline and reference nothing on disk.
INLINE = "data:"


def _assets():
    """Yield every js and css file collectstatic would post-process."""
    for directory in settings.STATICFILES_DIRS:
        root = Path(directory)
        if not root.is_dir():
            continue
        for pattern in ("*.js", "*.css"):
            for path in sorted(root.rglob(pattern)):
                # build output is generated from these same sources
                if "build" in path.parts or "node_modules" in path.parts:
                    continue
                yield path


ASSETS = list(_assets())


class TestStaticSourcemaps:
    """Testing class for sourcemap references in shipped assets."""

    def test_core_static_assets_are_discoverable(self):
        """Guard the guard: an empty list would make this suite vacuous."""
        assert len(ASSETS) > 10, f"found almost no assets: {ASSETS[:3]}"

    @pytest.mark.parametrize("path", ASSETS, ids=[p.name for p in ASSETS])
    def test_core_static_asset_sourcemap_exists(self, path):
        """Any sourcemap `path` names must sit beside it.

        :param path: a js or css file that collectstatic will process
        :type path: :class:`pathlib.Path`
        """
        try:
            content = path.read_text(errors="ignore")
        except OSError:  # pragma: no cover - unreadable file is its own problem
            return

        for reference in SOURCEMAP.findall(content):
            if reference.startswith(INLINE):
                continue
            assert (path.parent / reference).is_file(), (
                f"{path.name} points at {reference!r}, which is not shipped. "
                "In development that is a silent 404; under "
                "ManifestStaticFilesStorage it aborts collectstatic and the "
                "deploy with it. Either ship the map or drop the comment."
            )
