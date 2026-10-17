"""A child's session sends web pages and links to kidux-closed (D104): the
list of defaults and the desktop file agree, and the session puts both
first where every program reads them."""

import configparser
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
TYPES = {"text/html", "application/xhtml+xml", "x-scheme-handler/http",
         "x-scheme-handler/https"}


def read(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    return parser


def test_web_pages_and_links_default_to_kidux_closed():
    defaults = read(HERE / "conf" / "xdg" / "mimeapps.list")["Default Applications"]

    assert set(defaults) == TYPES
    assert set(defaults.values()) == {"kidux-closed.desktop"}


def test_kidux_closed_takes_them_and_is_in_no_menu():
    entry = read(HERE / "conf" / "applications" / "kidux-closed.desktop")["Desktop Entry"]

    assert entry["Type"] == "Application"
    assert entry["Exec"] == "/usr/libexec/kidux-closed %u"
    assert set(filter(None, entry["MimeType"].split(";"))) == TYPES
    assert entry["NoDisplay"] == "true"


def test_the_session_puts_them_first_where_they_are_installed():
    session = (HERE / "bin" / "kidux-session").read_text()
    rules = (HERE / "debian" / "rules").read_text()

    assert 'XDG_CONFIG_DIRS="/usr/share/kidux/session/xdg:' in session
    assert 'XDG_DATA_DIRS="/usr/share/kidux/session/share:' in session
    assert "$(DEST)/usr/share/kidux/session/xdg/mimeapps.list" in rules
    assert "$(DEST)/usr/share/kidux/session/share/applications/kidux-closed.desktop" in rules
    assert "$(DEST)/usr/libexec/kidux-closed" in rules
