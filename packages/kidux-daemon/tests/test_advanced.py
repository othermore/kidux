"""The machine's advanced settings: Chromium's flags (advanced.py, D52)."""

import stat

import pytest

from kiduxd.advanced import check_flags, write_flags



@pytest.mark.parametrize("flags", [
    [],
    ["--disable-gpu-compositing"],
    ["--use-gl=angle", "--use-angle=gl"],
    ["--disable-features=WaylandLinuxDrmSyncobj,Vulkan"],
])
def test_flags_as_chromium_takes_them(flags):
    assert check_flags(flags) == flags


def test_blank_lines_and_spaces_around_are_dropped():
    assert check_flags(["  --disable-gpu ", "", "   "]) == ["--disable-gpu"]


@pytest.mark.parametrize("flags", [
    "--disable-gpu",
    ["disable-gpu"],
    ["-disable-gpu"],
    ["--disable gpu"],
    ["--disable-gpu\n--app=http://example.org"],
    ["--Disable-GPU"],
    ["--x=" + "a" * 200],
    ["--flag"] * 21,
    [3],
])
def test_anything_else_is_refused(flags):
    with pytest.raises(ValueError):
        check_flags(flags)


@pytest.mark.parametrize("flag", ["--app=http://example.org", "--user-data-dir=/tmp/x",
                                  "--remote-debugging-port=9222", "--no-sandbox",
                                  "--load-extension=/tmp/e", "--proxy-server=x:1",
                                  "--single-process", "--disable-setuid-sandbox",
                                  "--allow-file-access-from-files",
                                  "--ignore-certificate-errors", "--new-window",
                                  "--host-rules=MAP * 1.2.3.4"])
def test_a_flag_that_would_take_a_module_out_of_kidux_s_hold_is_refused(flag):
    with pytest.raises(ValueError):
        check_flags([flag])


def test_the_file_holds_one_flag_a_line_readable_by_everyone(tmp_path):
    path = tmp_path / "kidux" / "chromium-flags"

    write_flags(["--disable-gpu-compositing", "--use-gl=angle"], path)

    assert path.read_text() == "--disable-gpu-compositing\n--use-gl=angle\n"
    assert stat.S_IMODE(path.stat().st_mode) == 0o644


def test_no_flags_is_no_file(tmp_path):
    path = tmp_path / "chromium-flags"
    write_flags(["--disable-gpu"], path)

    write_flags([], path)

    assert not path.exists()
