"""A screen left alone: what kidux-idle decides (D67)."""

from kidux import idle


def test_a_screen_in_front_starts_counting():
    assert idle.step(7, 7, running=False, gap=2) == "start"


def test_a_screen_in_front_that_counts_goes_on():
    assert idle.step(7, 7, running=True, gap=2) is None


def test_a_screen_behind_another_stops_counting():
    assert idle.step(7, 8, running=True, gap=2) == "stop"
    assert idle.step(7, 8, running=False, gap=2) is None


def test_a_screen_thawed_in_front_starts_afresh():
    # Frozen under the lock screen: the count it had is not the child's.
    assert idle.step(7, 7, running=True, gap=900) == "restart"


def test_a_screen_whose_terminal_is_not_known_is_taken_to_be_in_front():
    assert idle.step(None, 8, running=False, gap=2) == "start"


def test_swayidle_arms_what_has_a_time():
    program = "/usr/lib/kidux/kidux-idle"
    assert idle.swayidle_argv(300, 600, program) == [
        "swayidle", "-w",
        "timeout", "300", f"{program} lock",
        "timeout", "600", f"{program} screen off", "resume", f"{program} screen on",
    ]
    assert idle.swayidle_argv(0, 600, program) == [
        "swayidle", "-w",
        "timeout", "600", f"{program} screen off", "resume", f"{program} screen on",
    ]


def test_seconds_from_the_environment():
    assert idle.seconds({"X": "300"}, "X", 5) == 300
    assert idle.seconds({}, "X", 5) == 5
    assert idle.seconds({"X": "soon"}, "X", 5) == 5
    assert idle.seconds({"X": "-3"}, "X", 5) == 0


def test_a_terminal_s_number():
    assert idle.vt_number("7") == 7
    assert idle.vt_number("tty8\n") == 8
    assert idle.vt_number("") is None and idle.vt_number(None) is None
