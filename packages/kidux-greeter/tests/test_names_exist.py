"""Every `vocabulary.X` and `words.X` the screens name exists.

The view is not run by the unit tests, so a string renamed in one place and
not the other would only be found by drawing the screen on the VM, as the
emergency screen. This is the check that finds it here.
"""

import re
from pathlib import Path

from kidux import vocabulary

from kidux_greeter import words

PACKAGE = Path(__file__).resolve().parent.parent / "kidux_greeter"
NAMED = re.compile(r"\b(vocabulary|words)\.([A-Z][A-Z0-9_]*)\b")


def test_every_named_string_exists():
    missing = set()
    for source in PACKAGE.glob("*.py"):
        for module, name in NAMED.findall(source.read_text(encoding="utf-8")):
            if not hasattr({"vocabulary": vocabulary, "words": words}[module], name):
                missing.add(f"{source.name}: {module}.{name}")
    assert not missing, sorted(missing)
