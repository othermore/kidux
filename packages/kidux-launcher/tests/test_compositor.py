"""The windows the foreign-toplevel protocol announces (compositor.py, D58),
from a scripted sequence of its events."""

import struct

from kidux_launcher.compositor import Toplevel, Toplevels, states_of


def states(*numbers: int) -> bytes:
    return struct.pack(f"={len(numbers)}I", *numbers)


def test_the_protocol_s_states_are_the_toplevel_s_fields():
    assert states_of(states(0, 2)) == {"maximized": True, "minimized": False,
                                       "activated": True, "fullscreen": False}
    assert states_of(b"") == {"maximized": False, "minimized": False,
                              "activated": False, "fullscreen": False}


def test_a_window_is_listed_from_its_first_done():
    windows = Toplevels()
    handle = object()
    number = windows.added(handle)
    windows.changed(handle, app_id="org.kidux.tests.Canary", title="Canary")
    assert windows.all() == []

    assert windows.done(handle) is True

    assert windows.all() == [Toplevel(id=number, app_id="org.kidux.tests.Canary",
                                      title="Canary")]


def test_changes_hold_at_done_and_only_changes_count():
    windows = Toplevels()
    handle = object()
    windows.added(handle)
    windows.changed(handle, app_id="a")
    windows.done(handle)
    windows.changed(handle, **states_of(states(2)))
    assert windows.all()[0].activated is False
    assert windows.done(handle) is True
    assert windows.all()[0].activated is True
    windows.changed(handle, **states_of(states(2)))
    assert windows.done(handle) is False


def test_a_dialog_knows_its_window_and_a_closed_window_goes():
    windows = Toplevels()
    main, dialog = object(), object()
    first = windows.added(main)
    windows.done(main)
    second = windows.added(dialog)
    windows.parent(dialog, main)
    windows.done(dialog)
    assert [t.parent for t in windows.all()] == [None, first]
    assert windows.handle_of(second) is dialog and windows.id_of(main) == first

    assert windows.closed(main) is True
    assert [t.id for t in windows.all()] == [second]
    # A window closed before it was ever announced changes nothing seen.
    ghost = object()
    windows.added(ghost)
    assert windows.closed(ghost) is False


def test_numbers_never_repeat():
    windows = Toplevels()
    first = windows.added(object())
    second = windows.added(object())
    assert first != second


def test_the_flags_the_log_says():
    assert Toplevel(id=1, activated=True, maximized=True).flags() == "am"
    assert Toplevel(id=1, minimized=True, parent=3).flags() == "id"
    assert Toplevel(id=1).flags() == "-"
