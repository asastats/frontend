"""Asset icons load lazily. See logbook: snippets asset icons loading="lazy"."""

import re
from pathlib import Path

TEMPLATES = Path(__file__).parent.parent.parent / "templates" / "snippets"
ICON_TEMPLATES = ["asas.html", "nonval.html", "dynamic/asset.html"]


def _asset_icons(name):
    source = (TEMPLATES / name).read_text()
    return [
        tag
        for tag in re.findall(r"<img\b[^>]*>", source)
        if re.search(r'class="asaicon\b', tag)
    ]


def test_every_asset_icon_template_still_has_its_icon():
    for name in ICON_TEMPLATES:
        assert _asset_icons(name), name


def test_every_asset_icon_loads_lazily():
    for name in ICON_TEMPLATES:
        for tag in _asset_icons(name):
            assert 'loading="lazy"' in tag, (name, tag)
            assert 'decoding="async"' in tag, (name, tag)
