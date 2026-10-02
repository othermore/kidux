"""The room a screen has (screen.py, D49)."""

import pytest

from kidux import screen


@pytest.mark.parametrize("size,roomy", [
    ((1280, 800), False),
    ((1440, 900), False),
    ((1920, 1080), True),
    ((1600, 960), True),
    ((2560, 900), False),
])
def test_a_screen_is_roomy_with_room_to_spare_each_way(size, roomy):
    assert screen.roomy(*size) is roomy


class Monitors:
    def __init__(self, sizes):
        self._sizes = sizes

    def get_n_items(self):
        return len(self._sizes)

    def get_item(self, index):
        width, height = self._sizes[index]
        geometry = type("Rectangle", (), {"width": width, "height": height})()
        return type("Monitor", (), {"get_geometry": lambda _self: geometry})()


def test_the_logical_size_is_the_first_monitor_s():
    display = type("Display", (), {"get_monitors": lambda _self: Monitors([(1440, 900)])})()
    assert screen.logical_size(display) == (1440, 900)
    empty = type("Display", (), {"get_monitors": lambda _self: Monitors([])})()
    assert screen.logical_size(empty) == (0, 0)


@pytest.mark.parametrize("mode,scale", [
    ((1280, 800), 1.0),
    ((1366, 768), 1.0),
    ((1920, 1080), 1.0),
    ((2560, 1600), 1.5),
    ((2880, 1800), 1.75),
    ((3840, 2160), 2.25),
    ((1024, 600), 1.0),
])
def test_the_automatic_scale_is_the_largest_quarter_that_leaves_the_screen_roomy(mode, scale):
    assert screen.automatic_scale(*mode) == scale
    width, height = mode
    assert scale == 1.0 or screen.roomy(int(width / scale), int(height / scale))


def test_it_answers_session_inner(capsys):
    assert screen.main(["screen", "2880x1800"]) == 0
    assert capsys.readouterr().out == "1.75\n"
    assert screen.main(["screen", "big"]) == 2


def test_the_mode_session_inner_exports(monkeypatch):
    monkeypatch.setenv("KIDUX_SCREEN_MODE", "2880x1800")
    assert screen.mode_from_environment() == (2880, 1800)
    monkeypatch.setenv("KIDUX_SCREEN_MODE", "wide")
    assert screen.mode_from_environment() is None
    monkeypatch.delenv("KIDUX_SCREEN_MODE")
    assert screen.mode_from_environment() is None


def test_the_physical_size_is_the_logical_size_times_the_scale():
    geometry = type("Rectangle", (), {"width": 1645, "height": 1028})()
    monitor = type("Monitor", (), {"get_geometry": lambda _self: geometry,
                                   "get_scale": lambda _self: 1.75})()
    monitors = type("Monitors", (), {"get_n_items": lambda _self: 1,
                                     "get_item": lambda _self, _i: monitor})()
    display = type("Display", (), {"get_monitors": lambda _self: monitors})()
    assert screen.physical_size(display) == (2879, 1799)
    assert screen.automatic_scale(*screen.physical_size(display)) == 1.75


@pytest.mark.parametrize("width, compact", [
    (0, False),        # not measured yet: the full corner
    (640, True),       # 1280x800 at a scale of 2
    (960, True),       # the MacBook at 300 %
    (1199, True),
    (1200, False),
    (1280, False),     # the least a screen is drawn for (D30)
    (1645, False),     # the MacBook at 175 %
])
def test_the_corner_is_compact_on_a_narrow_screen(width, compact):
    assert screen.compact_corner(width) is compact
