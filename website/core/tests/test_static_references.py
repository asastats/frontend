"""Templates must name static sources, and every named file must exist.

Two rules, both of which used to be enforced by nobody.

**Name the source, not a build.** Scripts were once referenced by a versioned
filename -- ``js/site.min021.js`` -- so cache-busting lived in the name. Every
change meant renaming the file and editing each referring template, and a
missed edit served a stale script with no error anywhere. Content hashing does
that job now (``ManifestStaticFilesStorage`` in production), so a template that
names a build output has reintroduced the problem the hashing removed.

**Reference something real.** Under manifest storage ``{% static %}`` raises for
a file that is not in the manifest, so a typo that merely 404'd in development
takes the page down in production. That is the right trade, but it is better
found here than at deploy time.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

#: `{% static 'x' %}` with a literal argument. Variable arguments -- e.g.
#: `{% static banner.image %}` -- cannot be resolved without rendering and are
#: deliberately out of scope.
STATIC_TAG = re.compile(r"""\{%\s*static\s+['"]([^'"]+)['"]""")

#: Our own build outputs, which templates must never name. Vendored bundles
#: that ship minified (chart.min.js, jquery-2.2.4.min.js) are sources as far
#: as this project is concerned, so the pattern is deliberately narrow: a
#: `.minNNN.` segment with digits is ours.
BUILD_NAME = re.compile(r"\.min\d+\.")


def _template_paths():
    for directory in settings.TEMPLATES[0]["DIRS"]:
        root = Path(directory)
        if root.is_dir():
            yield from sorted(root.rglob("*.html"))


def _references():
    """Yield (template, referenced path) for every literal {% static %}."""
    for path in _template_paths():
        for reference in STATIC_TAG.findall(path.read_text(errors="ignore")):
            yield path, reference


REFERENCES = list(_references())


class TestStaticReferences:
    """Testing class for {% static %} references across the templates."""

    def test_core_static_references_are_discoverable(self):
        """Guard the guard: an empty list would make this suite vacuous."""
        assert len(REFERENCES) > 10, (
            f"found almost no {{% static %}} references: {REFERENCES[:3]}"
        )

    @pytest.mark.parametrize(
        "template,reference",
        REFERENCES,
        ids=[f"{p.name}:{r}" for p, r in REFERENCES],
    )
    def test_core_static_reference_names_a_source(self, template, reference):
        """`reference` must not be one of our versioned build outputs.

        :param template: template naming the file
        :type template: :class:`pathlib.Path`
        :param reference: the path passed to {% static %}
        :type reference: str
        """
        assert not BUILD_NAME.search(reference), (
            f"{template.name} names the build output {reference!r}. Name the "
            "source instead -- `js/site.js` -- and let "
            "ManifestStaticFilesStorage hash it. Putting the version back in "
            "the filename means every change needs an edit in every referring "
            "template, and a missed one serves a stale file silently."
        )

    @pytest.mark.parametrize(
        "template,reference",
        REFERENCES,
        ids=[f"{p.name}:{r}" for p, r in REFERENCES],
    )
    def test_core_static_reference_exists(self, template, reference):
        """`reference` must resolve to a file on disk.

        :param template: template naming the file
        :type template: :class:`pathlib.Path`
        :param reference: the path passed to {% static %}
        :type reference: str
        """
        found = any(
            (Path(directory) / reference).is_file()
            for directory in settings.STATICFILES_DIRS
        )
        assert found, (
            f"{template.name} references {reference!r}, which is not in any "
            "STATICFILES_DIRS. In development this 404s; under "
            "ManifestStaticFilesStorage it raises at render time and takes the "
            "page down."
        )
