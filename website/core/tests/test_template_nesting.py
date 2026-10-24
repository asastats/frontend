"""Every template must close the elements it opens.

A stray ``</div>`` and a missing one cancel out in any count of opening versus
closing tags -- which is what a person, and the obvious version of this test,
would check. The document is still wrong: the stray one closes whatever happens
to be open at that point, and the browser's error recovery decides where the
rest of the page goes. It renders, silently, in the wrong place.

That is what ``subscriptions.html`` did. It carried a ``</div>`` closing nothing
and a ``<div class="mt-10 text-center">`` never closed, so tag counts balanced
while the Free tier card ended up outside the section it was written into,
overlapping the content above it. Nothing failed; the page just looked broken.

So this is a stack, not a count: it walks the tags in order and names the first
one without a partner.

Conditionals are handled by checking the primary branch -- ``{% else %}``,
``{% empty %}`` and ``{% elif %}`` arms are dropped, nested ones included, then
the remaining Django tags are stripped. That reads a template the way one
request renders it. A template that opens an element in one arm and closes it
in another balances on no single branch; name it in ``BRANCH_STRADDLING`` with
the reason, rather than excusing it with a pattern. See docs/logbook.md.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

#: Containers whose mis-nesting moves visible content. Void and self-closing
#: elements are absent: they have no closing tag to match.
TRACKED = ("div", "section", "article", "aside", "nav", "main", "header", "footer")

TAG = re.compile(
    r"</?(?P<name>" + "|".join(TRACKED) + r")\b[^>]*?(?P<self_closing>/)?>",
    re.IGNORECASE,
)

#: `{% comment %}` blocks hold prose, and the prose here often quotes markup.
DJANGO_COMMENT = re.compile(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", re.DOTALL)

#: A Django block tag and its first word.
BLOCK_TAG = re.compile(r"\{%\s*(?P<word>\w+).*?%\}", re.DOTALL)

#: Everything else Django owns.
DJANGO_TAG = re.compile(r"\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}", re.DOTALL)

#: Templates where an element is opened in one branch and closed in another, so
#: no single branch balances on its own. Empty since 2026-10-24: both former
#: entries balanced once nested arms were dropped correctly.
BRANCH_STRADDLING = {}


def _template_paths():
    for directory in settings.TEMPLATES[0]["DIRS"]:
        root = Path(directory)
        if root.is_dir():
            yield from sorted(root.rglob("*.html"))


def _primary_branch(source):
    """Return the template as one request renders it, Django tags removed.

    :param source: raw template text
    :type source: str
    :return: str
    """
    without_comments = DJANGO_COMMENT.sub("", source)
    # One frame per open if/for: True while in its first arm. Text is kept only
    # when every enclosing frame is, so nested conditionals in an else arm drop
    # with it (a regex up to the next endif cut such arms short).
    frames, kept, position = [], [], 0
    for tag in BLOCK_TAG.finditer(without_comments):
        if all(frames):
            kept.append(without_comments[position : tag.start()])
        position = tag.end()
        word = tag.group("word")
        if word in ("if", "for"):
            frames.append(True)
        elif word in ("elif", "else", "empty") and frames:
            frames[-1] = False
        elif word in ("endif", "endfor") and frames:
            frames.pop()
    if all(frames):
        kept.append(without_comments[position:])
    return DJANGO_TAG.sub("", "".join(kept))


def _unbalanced(markup):
    """Return a description of the first unmatched tag, or None.

    :param markup: markup with Django tags already removed
    :type markup: str
    :return: str or None
    """
    stack = []
    for match in TAG.finditer(markup):
        if match.group("self_closing"):
            continue
        name = match.group("name").lower()
        line = markup[: match.start()].count("\n") + 1
        if match.group(0).startswith("</"):
            if not stack:
                return f"line {line}: </{name}> closes nothing"
            open_line, open_name = stack.pop()
            if open_name != name:
                return (
                    f"line {line}: </{name}> closes <{open_name}> "
                    f"opened on line {open_line}"
                )
        else:
            stack.append((line, name))
    if stack:
        line, name = stack[-1]
        return f"line {line}: <{name}> is never closed"
    return None


CHECKED = [p for p in _template_paths() if p.name not in BRANCH_STRADDLING]


class TestCoreTemplateNesting:
    """Testing class for template element nesting."""

    @pytest.mark.parametrize("path", CHECKED, ids=lambda p: p.name)
    def test_core_template_nesting_is_balanced(self, path):
        problem = _unbalanced(_primary_branch(path.read_text()))

        assert problem is None, f"{path.name} {problem}"

    def test_core_template_nesting_skips_only_the_known_templates(self):
        """The exemption list must stay an exception, not become the rule.

        A pattern-based skip is what the first version of this test used, and
        it silently excused half the templates in the project -- including the
        one whose defect prompted the test. A named list cannot do that
        quietly: growing it is an edit somebody has to justify.

        Raised from two to three on 2026-08-20 for the dynamic designs'
        copy of `program.html`, and **back to two on 2026-08-21** when that copy
        was replaced. Its successor, `snippets/dynamic/position.html`, is balanced
        in every branch and needs no exemption -- which is the outcome to want:
        the list shrank because the markup improved, not because the rule was
        relaxed. A third entry should have to argue for itself again.
        """
        assert len(BRANCH_STRADDLING) <= 2
        assert len(CHECKED) > 0.9 * (len(CHECKED) + len(BRANCH_STRADDLING))

    @pytest.mark.parametrize("name", sorted(BRANCH_STRADDLING))
    def test_core_template_nesting_exemption_still_exists(self, name):
        """A stale exemption hides a template that is no longer checked."""
        assert any(
            path.name == name for path in _template_paths()
        ), f"{name} is exempted but no longer exists; remove it from the list"

    @pytest.mark.parametrize("name", sorted(BRANCH_STRADDLING))
    def test_core_template_nesting_exemption_is_still_needed(self, name):
        """And an exemption kept after the template was fixed hides it too."""
        path = next(p for p in _template_paths() if p.name == name)

        assert _unbalanced(_primary_branch(path.read_text())) is not None, (
            f"{name} now balances on its primary branch; drop it from "
            "BRANCH_STRADDLING so it is checked like everything else"
        )
