"""The lid (lid.py): the screen and the keyboard's light off while it is
closed, and the session locked when it closes (D67, D97)."""

from kidux_launcher.lid import Lid


def lid(events):
    return Lid([], set_screen=lambda on: events.append("on" if on else "off"),
               on_closed=lambda: events.append("lock"),
               light_off=lambda: events.append("light off"),
               light_back=lambda: events.append("light back"))


def test_closing_the_lid_locks_the_session_then_turns_the_screen_and_the_light_off():
    events = []
    watched = lid(events)
    watched._apply(False)                      # open at start
    events.clear()

    watched._apply(True)

    assert events == ["lock", "off", "light off"]


def test_opening_it_gives_the_light_back_and_turns_the_screen_on_and_locks_nothing():
    events = []
    watched = lid(events)
    watched._apply(True)
    events.clear()

    watched._apply(False)

    assert events == ["light back", "on"]


def test_a_lid_closed_when_the_launcher_starts_is_not_a_closing():
    events = []
    watched = lid(events)

    watched._apply(True)

    assert events == ["off", "light off"]


def test_the_same_state_twice_is_one_change():
    events = []
    watched = lid(events)
    watched._apply(False)
    watched._apply(True)
    watched._apply(True)

    assert events == ["light back", "on", "lock", "off", "light off"]
