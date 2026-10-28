"""A long NFT trait value wraps inside its chip. See logbook: snippets/dynamic/nft.html trait chips."""

import re
from pathlib import Path

INPUT_CSS = Path(__file__).parent.parent.parent / "static" / "css" / "input.css"


def test_trait_chips_wrap_long_values():
    rule = re.search(r"\.dynamic-page \.trait \{([^}]*)\}", INPUT_CSS.read_text()).group(1)
    assert "max-width: 100%;" in rule
    assert "overflow-wrap: anywhere;" in rule
