"""The committed stylesheet is what the templates currently build to.

Tailwind v4 emits a rule only for a class it has *seen*, and what it scans is
the templates (`@source` in `input.css`, not the default auto-detection). So a
utility written into a template after the last build simply has no rule behind
it: the markup is correct, every markup test passes, and the page renders
without the padding, the colour or the gap that was asked for.

That has now happened twice on this project and both times it reached a
screenshot before anything noticed:

* `gap-x-3` was written into two profile pages and was not in the build, so
  both rendered with their columns touching.
* `text-base-content/40` was written into `home.html` for the email beside the
  reader's name and was not in the build, so the email rendered at full
  contrast -- the exact opposite of the "quieter than the name" it was for.

Neither is visible to a test that reads markup, because the markup is right.
What is wrong is that the *build* is behind the templates.

**Why a byte comparison rather than a search for particular classes.** Deciding
from a class attribute alone which tokens are Tailwind's and which are this
project's (`.pgroup-total`, `.dynamic-page`, `.fitem`) needs a heuristic, and a
heuristic here fails in the direction that hurts -- quietly passing the class it
did not recognise. Rebuilding needs no heuristic: the fresh build is the
authority on what these templates ask for, the build is deterministic (verified:
two runs are byte-identical), and comparing it to the committed file answers the
real question exactly.

**What it cannot see.** Classes that only ever appear in JavaScript. `input.css`
scans `templates` and `widgets`, not `static/js`, so a utility assigned from a
script is not compiled and never was -- that is a property of the build
configuration, not something this test is failing to notice.

The toolchain is fetched per machine and gitignored, so this skips where it is
absent. It also skips, loudly, when the local Tailwind differs in version from
the one that produced the committed file: `fetch-tailwind.sh` pulls *latest*, so
two developers can hold different binaries, and a diff between versions says
nothing about whether anybody forgot to rebuild.
"""

import re
import subprocess

from pathlib import Path

import pytest
from django.conf import settings

#: Where the toolchain and the build output live.
CSS_DIR = Path(settings.STATICFILES_DIRS[0]) / "css"

#: The build output every page loads.
STYLESHEET = CSS_DIR / "style.tw.css"

#: The source the build reads, which names the template roots to scan.
SOURCE = CSS_DIR / "input.css"

#: The standalone binary and the two plugins `build-tailwind.sh` requires.
TOOLCHAIN = [CSS_DIR / "tailwindcss", CSS_DIR / "daisyui.mjs", CSS_DIR / "daisyui-theme.mjs"]

#: The attribution line `build-tailwind.sh` prepends after minifying. Lightning
#: CSS strips even preserve-comments, so the script puts it back; it is not part
#: of what Tailwind emits and has to come off before comparing.
BANNER_MARK = "DaisyUI themes by Dachi"

#: Tailwind stamps its own version into the first line of its output.
VERSION = re.compile(r"tailwindcss v(\S+)")

#: A class selector in minified CSS, escapes included: `.-mt-4`,
#: `.text-base-content\/40`, `.md\:flex`.
#:
#: The first character may not be a digit, which is what separates a selector
#: from the fractional part of a number: `padding-bottom:0.3126rem` otherwise
#: reads as a rule for a class called `3126rem`, and that lands in the failure
#: message as a utility somebody supposedly wrote into a template. A class that
#: really does start with a digit is escaped by Tailwind (`.\32 xl\:flex`), so
#: it starts with the backslash and is still matched.
SELECTOR = re.compile(r"\.((?:\\.|[a-zA-Z_-])(?:\\.|[-\w])*)")


def _version(text):
    """Return the Tailwind version stamped in some output, or None."""
    found = VERSION.search(text)
    return found.group(1) if found else None


def _classes(css):
    """Return every class name a stylesheet defines a rule for.

    Used only to describe a failure. The comparison itself is on bytes.

    :param css: stylesheet text
    :type css: str
    :return: set of str
    """
    return {name.replace("\\", "") for name in SELECTOR.findall(css)}


@pytest.fixture(scope="module")
def committed():
    """The committed stylesheet, with the attribution line taken off."""
    if not STYLESHEET.is_file():
        pytest.skip(f"{STYLESHEET} has not been built")
    text = STYLESHEET.read_text()
    first, newline, rest = text.partition("\n")
    return rest if BANNER_MARK in first and newline else text


@pytest.fixture(scope="module")
def rebuilt(tmp_path_factory, committed):
    """Build the stylesheet again from the templates as they stand now.

    Written to a temporary file: a test must never overwrite the artefact it is
    checking, or a second run would pass whatever the first one produced.
    """
    missing = [path.name for path in TOOLCHAIN if not path.exists()]
    if missing:
        pytest.skip(
            f"the Tailwind toolchain is not on this machine ({', '.join(missing)}); "
            "run website/fetch-tailwind.sh to make this test able to run"
        )

    out = tmp_path_factory.mktemp("tailwind") / "style.tw.css"
    try:
        result = subprocess.run(
            [str(TOOLCHAIN[0]), "-i", str(SOURCE), "-o", str(out), "--minify"],
            capture_output=True,
            text=True,
            timeout=180,
        )
    except OSError as error:  # wrong architecture, not executable
        pytest.skip(f"the Tailwind binary did not run: {error}")

    if result.returncode != 0:
        pytest.fail(f"the Tailwind build failed:\n{result.stderr}")

    fresh = out.read_text()
    here = _version(result.stderr) or _version(fresh)
    theirs = _version(committed)
    if here and theirs and here != theirs:
        pytest.skip(
            f"this machine builds with Tailwind v{here} and the committed "
            f"stylesheet was built with v{theirs}; the difference between two "
            "versions says nothing about whether the build is behind the "
            "templates. Run website/fetch-tailwind.sh and "
            "website/build-tailwind.sh to bring them back together."
        )
    return fresh


def test_the_committed_stylesheet_is_not_behind_the_templates(committed, rebuilt):
    """Rebuild and compare. Any difference means somebody did not rebuild.

    The message does the diagnosis, because "the files differ" is useless to
    whoever hits this: the classes a fresh build has and the committed file
    lacks are, almost always, exactly the utilities just written into a
    template.
    """
    if committed == rebuilt:
        return

    added = sorted(_classes(rebuilt) - _classes(committed))
    dropped = sorted(_classes(committed) - _classes(rebuilt))
    detail = ""
    if added:
        detail += (
            "\n\nUsed in a template but with no rule in the committed build "
            f"({len(added)}): {', '.join(added[:25])}"
            f"{' ...' if len(added) > 25 else ''}"
        )
    if dropped:
        detail += (
            f"\n\nStill in the committed build but no longer used ({len(dropped)}): "
            f"{', '.join(dropped[:25])}{' ...' if len(dropped) > 25 else ''}"
        )
    if not detail:
        # Same class list, different bytes: a changed declaration rather than a
        # changed set of utilities -- an edit to input.css or a theme.
        detail = (
            "\n\nThe same classes are defined either way, so this is a changed "
            "rule rather than a changed template -- input.css or a theme was "
            "edited without rebuilding."
        )

    pytest.fail(
        "static/css/style.tw.css is not what these templates build to. "
        "Run website/build-tailwind.sh and commit the result." + detail
    )
