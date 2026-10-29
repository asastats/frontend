"""The index logo shrinks on short landscape screens. See logbook: website/templates/index.html."""

import re
from pathlib import Path

INPUT_CSS = Path(__file__).parent.parent.parent / "static" / "css" / "input.css"


def test_index_logo_is_capped_on_short_landscape_screens():
    block = re.search(
        r"@media \(orientation: landscape\) and \(max-height: 540px\) \{\s*#logo \{([^}]*)\}",
        INPUT_CSS.read_text(),
    ).group(1)
    assert "max-height: 25vh;" in block
    assert "width: auto;" in block
    assert "margin-inline: auto;" in block
