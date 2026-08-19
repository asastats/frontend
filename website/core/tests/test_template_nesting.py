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
``{% empty %}`` and ``{% elif %}`` arms are dropped, then the remaining Django
tags are stripped. That reads a template the way one request renders it. Two
templates genuinely open an element in one arm and close it in another, so no
single branch balances; they are named in ``BRANCH_STRADDLING`` with the reason,
rather than being caught by a pattern that would quietly excuse others too.
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
DJANGO_COMMENT = re.compile(
    r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", re.DOTALL
)

#: The alternative arms of a conditional. Removing them leaves the branch a
#: request takes when every condition holds.
ELSE_ARM = re.compile(
    r"\{%\s*(?:else|empty)\s*%\}.*?(?=\{%\s*end(?:if|for)\s*%\})", re.DOTALL
)
ELIF_ARM = re.compile(
    r"\{%\s*elif\b.*?%\}.*?(?=\{%\s*(?:elif|else|endif)\b)", re.DOTALL
)

#: Everything else Django owns.
DJANGO_TAG = re.compile(r"\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}", re.DOTALL)

#: Templates where an element is opened in one branch and closed in another, so
#: no single branch balances on its own. Both are deliberate: the page is two
#: different documents depending on the condition, sharing a closing tag.
BRANCH_STRADDLING = {
    "password_reset_from_key.html": (
        "the token_fail branch and the form branch share closing markup"
    ),
    "position.html": (
        "the Balance-on-ALGO branch and the general branch share closing markup"
    ),
}


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
    primary = ELIF_ARM.sub("", ELSE_ARM.sub("", without_comments))
    return DJANGO_TAG.sub("", primary)


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

    def test_core_template_nesting_skips_only_the_two_known_templates(self):
        """The exemption list must stay an exception, not become the rule.

        A pattern-based skip is what the first version of this test used, and
        it silently excused half the templates in the project -- including the
        one whose defect prompted the test. A named list cannot do that
        quietly: growing it is an edit somebody has to justify.
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
