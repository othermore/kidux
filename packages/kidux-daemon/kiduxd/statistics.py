"""Usage statistics: an identifier of this machine's on every fetch of the archive.

The archive's server counts the machines that follow it from its logs
(packaging.md, "The public archive"; D109). Every fetch already says it comes
from a Kidux machine; with *Share usage statistics* on, the panel's and the
first-run wizard's, it says which one, by an identifier made here for that
alone: random, never the system's machine-id, kept in config.toml so that the
machine counts as the same one for as long as it lives. Turning the sharing
off removes the snippet and keeps the identifier, so that turning it on again
counts the same machine, not a new one.
"""

import secrets

from kidux import paths

from .advanced import write_file
from .config import Config

#: What 60kidux-user-agent of kidux-apt-source says without an identifier.
USER_AGENT = "Debian APT-HTTP/1.3 Kidux"


def apply(config: Config) -> None:
    """The snippet as the setting says: written with the identifier, made
    and saved the first time, while the sharing is on; gone while it is off."""
    if not config.apt_statistics:
        paths.APT_STATISTICS.unlink(missing_ok=True)
        return
    if not config.apt_statistics_id:
        config.apt_statistics_id = secrets.token_hex(16)
        config.save()
    write_file(paths.APT_STATISTICS, (
        "// Written by kidux-daemon while an adult shares usage statistics: the\n"
        "// archive's logs count this machine as one machine by this identifier,\n"
        "// made for that alone (docs/dev/packaging.md, \"The public archive\").\n"
        f'Acquire::http::User-Agent "{USER_AGENT}/{config.apt_statistics_id}";\n'))
