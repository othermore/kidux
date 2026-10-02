"""Shared fixtures, and finding the source tree from wherever pytest was run.

Some tests are deliberately run against the real shipped files — the actual
avatars a child will be offered, the actual Spanish catalogue — rather than
against fixtures, because a test on invented files would not say whether a
Spanish child sees Spanish.

That means the tests have to find those files, and they are run from at least
two places: from the source tree while writing code, and from a copy under
.pybuild during the package build, where only the Python package and the tests
were copied and the data was left behind. So the root is looked up rather than
assumed, and the packaging passes it in explicitly.
"""

import os
from pathlib import Path

import pytest


def _find_source_root() -> Path:
    """The kidux-common source directory: the one holding data/ and po/."""
    from_environment = os.environ.get("KIDUX_SOURCE_ROOT")
    if from_environment:
        return Path(from_environment)

    for candidate in Path(__file__).resolve().parents:
        if (candidate / "data" / "avatars").is_dir() and (candidate / "po").is_dir():
            return candidate

    raise RuntimeError(
        "cannot find the kidux-common source tree. Set KIDUX_SOURCE_ROOT to it."
    )


SOURCE_ROOT = _find_source_root()


@pytest.fixture(scope="session")
def source_root() -> Path:
    return SOURCE_ROOT


@pytest.fixture(scope="session")
def shipped_avatars(source_root) -> Path:
    return source_root / "data" / "avatars"


@pytest.fixture(scope="session")
def catalogues(source_root) -> Path:
    return source_root / "po"
