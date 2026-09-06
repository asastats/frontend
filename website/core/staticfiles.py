"""What ``collectstatic`` must not publish out of ``static/``.

``static/css/`` holds the *inputs* to the Tailwind build as well as its output.
The output -- ``style.tw.css`` -- is what the templates load and what belongs in
STATIC_ROOT. The inputs do not, and two of them are actively harmful there:

**``input.css`` cannot survive post-processing.** Its first line is

    @import "tailwindcss" source(none);

which is a Tailwind directive naming a *package*, not a URL. Django's
``ManifestStaticFilesStorage`` rewrites ``@import`` targets in every collected
CSS file, so it resolves that name relative to the file -- ``css/tailwindcss``
-- and raises ``ValueError: The file 'css/tailwindcss' could not be found`` when
nothing is there.

**On a machine where something *is* there, the outcome is worse than an error.**
``css/tailwindcss`` is the standalone Tailwind binary, 110 MB of ELF, fetched
per machine by ``fetch-tailwind.sh`` and gitignored. When it is present the
import resolves, and collectstatic copies the binary into STATIC_ROOT -- twice,
once under its own name and once content-hashed -- and nginx serves an
executable at a public URL. That is the state a developer's collectstatic has
always produced, quietly, and it is why the missing-file error only ever
appeared on CI.

Ignoring the inputs fixes both halves. The build reads them from the source
tree, which is where they live and where ``build-tailwind.sh`` looks; nothing
reads them through ``{% static %}``.

Wired in via INSTALLED_APPS rather than a ``--ignore`` flag on the deploy's
collectstatic, because ``collectstatic`` reads these patterns from the app
registry -- so every invocation gets them, including a hand-run one on the
server and the one in ``core/tests/test_static_manifest.py``.
"""

from django.contrib.staticfiles.apps import StaticFilesConfig

#: Matched against the basename first and then the path relative to each
#: STATICFILES_DIRS entry, so ``css/…`` reaches only ours -- a widget shipping
#: a file of the same name at its own root is untouched.
BUILD_INPUTS = [
    # Tailwind/DaisyUI source. `style.tw.css` is the collected artefact.
    "css/input.css",
    # The toolchain `fetch-tailwind.sh` puts beside it. Present on a developer's
    # machine and on the server, absent on CI, gitignored everywhere.
    "css/tailwindcss",
    "css/daisyui.mjs",
    "css/daisyui-theme.mjs",
]


class AsastatsStaticFilesConfig(StaticFilesConfig):
    """``django.contrib.staticfiles``, plus the ignores above.

    ``collectstatic.set_options`` reads ``ignore_patterns`` off the installed
    ``staticfiles`` app config and appends them to whatever ``--ignore`` gave,
    so replacing the app's config entry is the supported way to make an ignore
    permanent.
    """

    ignore_patterns = StaticFilesConfig.ignore_patterns + BUILD_INPUTS
