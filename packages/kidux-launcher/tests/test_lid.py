"""The lid (lid.py): the screen off while it is closed, and the session
locked when it closes (D67)."""

from kidux_launcher.lid import Lid


def lid(events):
    return Lid([], set_screen=lambda on: events.append("on" if on else "off"),
               on_closed=lambda: events.append("lock"))


def test_closing_the_lid_locks_the_session_then_turns_the_screen_off():
    events = []
    watched = lid(events)
    watched._apply(False)                      # open at start
    events.clear()

    watched._apply(True)

    assert events == ["lock", "off"]


def test_opening_it_turns_the_screen_on_and_locks_nothing():
    events = []
    watched = lid(events)
    watched._apply(True)
    events.clear()

    watched._apply(False)

    assert events == ["on"]


def test_a_lid_closed_when_the_launcher_starts_is_not_a_closing():
    events = []
    watched = lid(events)

    watched._apply(True)

    assert events == ["off"]


def test_the_same_state_twice_is_one_change():
    events = []
    watched = lid(events)
    watched._apply(False)
    watched._apply(True)
    watched._apply(True)

    assert events == ["on", "lock", "off"]
