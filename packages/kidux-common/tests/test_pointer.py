"""The pointer's speed and the touchpad's scroll, from the panel's steps to
labwc's configuration."""

import pytest

from kidux import pointer

TEMPLATE = "<?xml version=\"1.0\"?>\n<labwc_config>\n  <core/>\n</labwc_config>\n"


def test_five_steps_slower_to_faster_with_today_s_pointer_and_half_its_scroll_in_the_middle():
    assert pointer.STEPS == (-2, -1, 0, 1, 2)
    assert [pointer.POINTER_SPEED[s] for s in pointer.STEPS] == sorted(
        pointer.POINTER_SPEED.values())
    assert [pointer.SCROLL_FACTOR[s] for s in pointer.STEPS] == sorted(
        pointer.SCROLL_FACTOR.values())
    assert pointer.POINTER_SPEED[0] == 0.0
    assert pointer.SCROLL_FACTOR[0] == 0.5 and pointer.SCROLL_FACTOR[2] == 1.0
    assert all(-1 <= speed <= 1 for speed in pointer.POINTER_SPEED.values())


@pytest.mark.parametrize("bad", [3, -3, 1.0, True, "1", None])
def test_only_a_step_is_taken(bad):
    with pytest.raises(ValueError):
        pointer.step(bad)


def test_the_written_part_reads_back(tmp_path):
    path = tmp_path / "input.xml"
    path.write_text(pointer.libinput(-1, 2))

    assert pointer.read(path) == (-0.3, 1.0)
    assert '<device category="touchpad"><pointerSpeed>-0.3</pointerSpeed>' \
           '<scrollFactor>1.0</scrollFactor></device>' in path.read_text()


@pytest.mark.parametrize("text", ["", "<libinput>", "<other/>",
                                  '<libinput><device category="touchpad"><pointerSpeed>0.9'
                                  '</pointerSpeed><scrollFactor>0.5</scrollFactor></device>'
                                  '</libinput>'])
def test_a_file_that_says_anything_else_is_the_middle_steps(tmp_path, text):
    path = tmp_path / "input.xml"
    path.write_text(text)
    assert pointer.read(path) == (0.0, 0.5)
    assert pointer.read(tmp_path / "missing.xml") == (0.0, 0.5)


def test_labwc_s_configuration_gets_the_part_before_its_end(tmp_path):
    path = tmp_path / "input.xml"
    path.write_text(pointer.libinput(1, -2))

    with_it = pointer.rc_xml(TEMPLATE, path)
    without = pointer.rc_xml(TEMPLATE, tmp_path / "missing.xml")

    assert with_it.index("<core/>") < with_it.index("<libinput>") < with_it.index(
        "</labwc_config>")
    assert "<pointerSpeed>0.3</pointerSpeed><scrollFactor>0.25</scrollFactor>" in with_it
    assert "<pointerSpeed>0.0</pointerSpeed><scrollFactor>0.5</scrollFactor>" in without
    with pytest.raises(ValueError):
        pointer.rc_xml("<openbox_config/>", path)
