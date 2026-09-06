"""Whatever a jest suite requires, ``website/package.json`` has to declare.

``website``'s jest config has no ``roots``, so its rootDir is ``website`` and it
collects **every** ``*.test.js`` beneath it -- 21 of its own and, at the time of
writing, four inside in-house widgets. One jest, one node_modules, one coverage
report.

The widgets are submodules that carry their own ``package.json``, and they
declare what their tests need. That declaration is right, and it is also not
enough: the suites run from ``website``, so node resolves their imports against
``website/node_modules``. A dependency that exists only in the widget's own
manifest resolves on a machine where somebody has run ``npm install`` inside the
widget, and nowhere else.

Which is exactly how ``fast-check`` behaved. ``dustsweep.property.test.js``
requires it, ``widgets/inhouse/dustsweep/package.json`` declares it, and the
build workflow -- which installs ``website`` and ``wallet`` and no widget --
failed with ``Cannot find module 'fast-check'`` while every developer machine
was green.

**Not every widget dependency belongs in website's manifest.** Four of the six
in-house packages declare a vendor SDK and ``esbuild``, which build a browser
bundle and are never imported by a test. So the rule is not "union the
manifests"; it is "anything a suite *requires* must resolve", which is what this
module checks and all that CI needs.

Read `test_a_module_nobody_declares_is_reported` first: without it a typo in
the regex below leaves a test that scans nothing and passes.
"""

import json
import re
from pathlib import Path

WEBSITE = Path(__file__).resolve().parents[2]

PACKAGE_JSON = WEBSITE / "package.json"

#: `require("x")` and `require('x')`, capturing the module name. Bare specifiers
#: only -- a relative path is the suite loading the code under test.
REQUIRE = re.compile(r"""require\(\s*["'](?P<module>[^"'./][^"']*)["']\s*\)""")

#: Node ships these; no manifest names them. Only the ones the suites actually
#: use, so an unexpected builtin shows up as a finding rather than passing on a
#: list nobody curates.
NODE_BUILTINS = frozenset({"fs", "path", "crypto", "os", "util", "assert"})


def _suites():
    """Return every test file website's jest would collect.

    :return: list of :class:`pathlib.Path`
    """
    return [
        path
        for path in WEBSITE.rglob("*.test.js")
        if "node_modules" not in path.parts
    ]


def _required_packages(text):
    """Return the package names a suite's source requires.

    A subpath import (``require("foo/bar/baz")``) is satisfied by the package,
    so it is reported as ``foo``; a scoped name keeps both segments.

    :param text: JavaScript source
    :type text: str
    :return: set of str
    """
    packages = set()
    for match in REQUIRE.finditer(text):
        module = match.group("module")
        parts = module.split("/")
        packages.add(
            "/".join(parts[:2]) if module.startswith("@") else parts[0]
        )
    return packages - NODE_BUILTINS


def _declared():
    """Return every package name website's manifest declares.

    :return: set of str
    """
    manifest = json.loads(PACKAGE_JSON.read_text())
    return set(manifest.get("dependencies", {})) | set(
        manifest.get("devDependencies", {})
    )


class TestJestSuitesResolveTheirImports:
    """One node_modules runs all of these, so one manifest has to cover them."""

    def test_every_required_package_is_declared(self):
        declared = _declared()
        missing = {}

        for suite in _suites():
            for package in _required_packages(suite.read_text()):
                if package not in declared:
                    missing.setdefault(package, []).append(
                        str(suite.relative_to(WEBSITE))
                    )

        assert not missing, (
            "these jest suites require packages website/package.json does not "
            "declare, so they pass where someone has installed a widget's own "
            f"node_modules and fail in CI: {missing}. Add each to "
            "website/package.json -- the widget's own manifest is not what "
            "`npm install` reads in the build workflow."
        )

    def test_a_module_nobody_declares_is_reported(self):
        """The anchor: the scan must actually find requires and judge them.

        Without this, a regex that matches nothing -- or a `_declared` that
        returns every name -- leaves `test_every_required_package_is_declared`
        passing on an empty scan, which is the shape of test this repository
        has shipped before.
        """
        found = _required_packages(
            'const fc = require("fast-check");\n'
            'const nope = require("not-a-real-package");\n'
            'const sub = require("@scope/pkg/deep/path");\n'
            'const own = require("../../static/dustsweep/dustsweep.js");\n'
            'const builtin = require("path");\n'
        )

        assert found == {"fast-check", "not-a-real-package", "@scope/pkg"}
        assert "not-a-real-package" not in _declared()

    def test_the_widget_suites_are_in_scope(self):
        """The rule is only worth anything if it reaches past website's own.

        `website`'s jest collects widget suites because they sit under its
        rootDir. If that stops being true -- a `roots` key, a moved widget --
        this module would go on passing while checking 21 files instead of 25.
        """
        suites = {str(path.relative_to(WEBSITE)) for path in _suites()}

        assert len(suites) >= 25, f"only found {len(suites)} suites"
        assert any(part.startswith("widgets/") for part in suites)
        assert (
            "widgets/inhouse/dustsweep/tests/javascript/"
            "dustsweep.property.test.js" in suites
        )

    def test_fast_check_is_declared(self):
        """The regression itself, named.

        `test_every_required_package_is_declared` covers it, but only as long
        as the property suite exists. This says the thing the build workflow
        needed out loud.
        """
        assert "fast-check" in _declared()
