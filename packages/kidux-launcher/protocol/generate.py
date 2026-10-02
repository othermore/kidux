#!/usr/bin/python3
"""The Python for wlr-foreign-toplevel-management, made when the package is built.

    python3 protocol/generate.py <directory>

pywayland's scanner turns the protocol's XML into a package of classes. Its
command line wants pkg-config and writes beside pywayland's own protocols,
so the scanner is called here directly: the core protocol's interfaces the
XML names are pywayland's, and the imports the scanner writes for them are
made absolute, so that the package can live inside kidux_launcher.
"""

import pathlib
import sys

from pywayland.scanner import Protocol

XML = pathlib.Path(__file__).with_name("wlr-foreign-toplevel-management-unstable-v1.xml")
CORE = ("wl_seat", "wl_output", "wl_surface")


def main(argv: list[str]) -> int:
    out = pathlib.Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    protocol = Protocol.parse_file(str(XML))
    imports = {interface.name: protocol.name for interface in protocol.interface}
    imports.update((name, "wayland") for name in CORE)
    protocol.output(str(out), imports)
    for module in (out / protocol.name).glob("*.py"):
        text = module.read_text()
        module.write_text(text.replace("from ..wayland import",
                                       "from pywayland.protocol.wayland import"))
    (out / "__init__.py").write_text('"""Wayland protocols the launcher speaks, made at build."""\n')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
