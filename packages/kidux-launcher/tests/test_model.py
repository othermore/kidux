"""The launcher's figures and words, against a clock the tests move."""

import gettext

import pytest

from kidux_launcher.model import UNLIMITED, Model

ENGLISH = gettext.NullTranslations()


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


def test_a_child_with_no_limit_is_shown_no_time_at_all(clock):
    model = Model(clock)
    model.update(600, UNLIMITED)

    assert model.unlimited
    assert model.time_text(ENGLISH) is None


@pytest.mark.parametrize("left,text", [
    (1500, "25 minutes left"), (61, "2 minutes left"), (60, "1 minute left"),
    (1, "1 minute left"), (0, "0 minutes left"),
])
def test_the_time_left_in_words_rounds_up(clock, left, text):
    model = Model(clock)
    model.update(0, left)

    assert model.time_text(ENGLISH) == text


def test_it_counts_down_between_two_answers(clock):
    model = Model(clock)
    model.update(0, 600)

    clock.now += 125
    assert model.left() == 475
    assert model.minutes_left() == 8


def test_it_never_counts_below_zero_on_its_own(clock):
    model = Model(clock)
    model.update(0, 30)
    clock.now += 300

    assert model.left() == 0


def test_with_the_daemon_away_the_figures_stay_where_they_were(clock):
    model = Model(clock)
    model.update(0, 600)
    clock.now += 60
    model.daemon_away()
    clock.now += 600

    assert model.left() == 540
    assert not model.daemon_there

    model.update(100, 500)
    assert model.daemon_there and model.left() == 500


@pytest.mark.parametrize("seconds,text", [
    (600, "10 minutes left. Save your work."),
    (300, "5 minutes left. Save your work."),
    (60, "1 minute left. Save your work."),
    (20, "1 minute left. Save your work."),
])
def test_the_warnings_say_to_save(clock, seconds, text):
    model = Model(clock)
    model.warn(seconds)

    assert model.warning_text(ENGLISH) == text
    model.dismiss()
    assert model.warning_text(ENGLISH) is None


@pytest.mark.parametrize("minutes, clock", [(51, "00:51"), (90, "01:30"), (0, "00:00"),
                                            (5, "00:05"), (600, "10:00")])
def test_the_time_left_as_a_clock_reads_it(minutes, clock):
    model = Model()
    model.minutes_left = lambda: minutes
    assert model.time_clock() == clock


def test_no_clock_without_a_limit():
    model = Model()
    model.minutes_left = lambda: None
    assert model.time_clock() is None
