"""What of kidux.scroll needs no display (D63)."""

import pytest

from kidux import scroll


@pytest.mark.parametrize("value, lower, upper, page, before, after", [
    (0, 0, 500, 500, False, False),        # it fits
    (0, 0, 900, 500, False, True),         # more below
    (400, 0, 900, 500, True, False),       # scrolled to the end
    (200, 0, 900, 500, True, True),        # in the middle
    (0.5, 0, 500.5, 500, False, False),    # half a pixel is no more
])
def test_more_before_and_after_what_is_shown(value, lower, upper, page, before, after):
    assert scroll.more(value, lower, upper, page) == (before, after)


def test_the_look_draws_the_scrollbar_and_a_shade_on_every_edge():
    for node in ("slider", "trough", "undershoot.top", "undershoot.bottom",
                 "undershoot.left", "undershoot.right"):
        assert node in scroll.CSS
    assert "kidux-scroll" in scroll.CSS


def test_an_area_overflows_by_more_than_a_pixel_once_it_is_shown():
    assert scroll.overflows(500, 900)
    assert not scroll.overflows(500, 500.5)
    assert not scroll.overflows(0, 900)


class Timers:
    """GLib's timeouts as a list: each added one kept until it is fired or
    removed."""

    def __init__(self):
        self.pending, self.next = {}, 1

    def add(self, _ms, function, *args):
        self.pending[self.next] = (function, args)
        self.next += 1
        return self.next - 1

    def remove(self, source):
        del self.pending[source]

    def fire(self):
        for source in list(self.pending):
            function, args = self.pending.pop(source)
            function(*args)


def test_a_size_is_judged_once_it_has_settled_not_while_it_passes():
    # A window is first shown small, then maximised: only the last size
    # counts, once it has held for SETTLE_MS.
    judged, timers = [], Timers()
    settling = scroll.Settling(judged.append, timers.add, timers.remove)

    settling.changed("tall")
    settling.changed("tall")
    settling.changed("wide")
    assert judged == [] and len(timers.pending) == 2

    timers.fire()
    assert sorted(judged) == ["tall", "wide"]
    settling.changed("tall")
    timers.fire()
    assert judged.count("tall") == 2
