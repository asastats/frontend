"""The CSP's ``script-src`` allows no ``'unsafe-inline'``: no template may run inline code."""

import re
from pathlib import Path

import pytest
from django.test import Client

WEBSITE = Path(__file__).resolve().parents[2]
TEMPLATE_DIRS = [WEBSITE / "templates", WEBSITE / "widgets"]
#: Script types the browser never executes, so the CSP does not apply to them.
DATA_TYPES = {"application/ld+json", "application/json"}
SCRIPT_TAG = re.compile(r"<script\b([^>]*)>", re.IGNORECASE)
TYPE_ATTR = re.compile(r"""\btype\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
HANDLER = re.compile(r"""\son[a-z]+\s*=\s*["']""", re.IGNORECASE)


def templates():
    for folder in TEMPLATE_DIRS:
        for path in folder.rglob("*.html"):
            if "tests" not in path.parts and "node_modules" not in path.parts:
                yield path


def inline_scripts(text):
    for attributes in SCRIPT_TAG.findall(text):
        if "src=" in attributes:
            continue
        kind = TYPE_ATTR.search(attributes)
        if kind and kind.group(1).lower() in DATA_TYPES:
            continue
        yield attributes


@pytest.mark.parametrize(
    "path", sorted(templates()), ids=lambda p: str(p.relative_to(WEBSITE))
)
def test_template_has_no_inline_script_or_handler(path):
    text = path.read_text()
    assert list(inline_scripts(text)) == []
    assert HANDLER.search(text) is None


def test_the_scan_sees_inline_code():
    assert list(inline_scripts("<script>alert(1)</script>")) == [""]
    assert list(inline_scripts('<script type="module">x</script>')) == [' type="module"']
    assert list(inline_scripts('<script type="application/ld+json">{}</script>')) == []
    assert list(inline_scripts('<script src="/a.js"></script>')) == []
    assert HANDLER.search('<img src="x" onerror="go()">')


@pytest.mark.django_db
def test_swagger_ui_loads_its_config_as_a_script_file():
    page = Client().get("/api/v2/schema/swagger-ui/")
    assert page.status_code == 200
    html = page.content.decode()
    assert list(inline_scripts(html)) == []
    script = Client().get("/api/v2/schema/swagger-ui/?script=")
    assert script.status_code == 200
    assert "SwaggerUIBundle" in script.content.decode()
