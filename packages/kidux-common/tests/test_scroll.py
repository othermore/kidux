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
