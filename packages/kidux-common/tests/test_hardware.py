"""What the machine has (hardware.py), read from a directory of files."""

import struct

import pytest

from kidux import hardware


def write(root, path, text):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text + "\n")


@pytest.fixture
def macbook(tmp_path):
    """The development MacBook, as its /sys reads."""
    tmp_path = tmp_path / "mac"
    write(tmp_path, "class/dmi/id/sys_vendor", "Apple Inc.")
    write(tmp_path, "module/hid_apple/parameters/fnmode", "3")
    write(tmp_path, "class/power_supply/ADP1/type", "Mains")
    write(tmp_path, "class/power_supply/ADP1/online", "1")
    write(tmp_path, "class/power_supply/BAT0/type", "Battery")
    write(tmp_path, "class/power_supply/BAT0/status", "Charging")
    write(tmp_path, "class/power_supply/BAT0/capacity", "71")
    write(tmp_path, "class/backlight/gmux_backlight/type", "platform")
    write(tmp_path, "class/backlight/gmux_backlight/brightness", "512")
    write(tmp_path, "class/backlight/gmux_backlight/max_brightness", "1023")
    write(tmp_path, "class/leds/smc::kbd_backlight/brightness", "0")
    write(tmp_path, "class/leds/smc::kbd_backlight/max_brightness", "255")
    write(tmp_path, "class/leds/input4::capslock/brightness", "0")
    write(tmp_path, "class/input/event0/device/capabilities/sw", "1")
    write(tmp_path, "class/input/event20/device/capabilities/sw", "10")
    return tmp_path


@pytest.fixture
def desktop(tmp_path):
    """A desktop PC, or the test machine: nothing of a laptop's."""
    tmp_path = tmp_path / "pc"
    write(tmp_path, "class/dmi/id/sys_vendor", "QEMU")
    write(tmp_path, "class/input/event2/device/capabilities/sw", "0")
    return tmp_path


def test_the_macbook_has_a_battery_charging_on_mains(macbook):
    cell = hardware.battery(macbook)
    assert cell == hardware.Battery(capacity=71, status="Charging", plugged=True)
    assert cell.charging


def test_a_battery_discharging_off_mains(macbook):
    write(macbook, "class/power_supply/ADP1/online", "0")
    write(macbook, "class/power_supply/BAT0/status", "Discharging")
    cell = hardware.battery(macbook)
    assert cell.capacity == 71 and not cell.charging


def test_a_mouse_s_battery_is_not_the_machine_s(desktop):
    write(desktop, "class/power_supply/hidpp_battery_0/type", "Battery")
    write(desktop, "class/power_supply/hidpp_battery_0/scope", "Device")
    write(desktop, "class/power_supply/hidpp_battery_0/capacity", "40")
    assert hardware.battery(desktop) is None


def test_a_desktop_has_no_battery_backlight_keyboard_light_or_lid(desktop):
    assert hardware.battery(desktop) is None
    assert hardware.backlight(desktop) is None
    assert hardware.keyboard_backlight(desktop) is None
    assert hardware.lid_devices(desktop) == []
    assert not hardware.has_lid(desktop)


def test_the_backlight_and_the_keyboard_light_as_levels(macbook):
    light = hardware.backlight(macbook)
    assert light == hardware.Level("gmux_backlight", 512, 1023) and light.percent == 50
    keys = hardware.keyboard_backlight(macbook)
    assert keys == hardware.Level("smc::kbd_backlight", 0, 255) and keys.percent == 0


def test_the_panel_s_own_backlight_is_preferred_to_the_firmware_s(desktop):
    write(desktop, "class/backlight/acpi_video0/type", "firmware")
    write(desktop, "class/backlight/acpi_video0/brightness", "3")
    write(desktop, "class/backlight/acpi_video0/max_brightness", "10")
    write(desktop, "class/backlight/intel_backlight/type", "raw")
    write(desktop, "class/backlight/intel_backlight/brightness", "3000")
    write(desktop, "class/backlight/intel_backlight/max_brightness", "7500")
    assert hardware.backlight(desktop).name == "intel_backlight"


def test_the_lid_switch_is_found_by_its_capability(macbook):
    assert hardware.lid_devices(macbook) == ["/dev/input/event0"]
    assert hardware.has_lid(macbook)


@pytest.mark.parametrize("percent, up, floor, expected", [
    (50, True, 0, 60), (50, False, 0, 40), (95, True, 0, 100), (100, True, 0, 100),
    (7, False, 5, 5), (0, False, 0, 0), (3, True, 0, 10), (12, False, 0, 10),
    (10, False, 5, 5), (5, False, 5, 5),
])
def test_a_key_steps_a_level_on_the_tens_within_its_floor(percent, up, floor, expected):
    assert hardware.step(percent, up, floor) == expected


@pytest.mark.parametrize("text, expected", [
    ("Volume: 0.45\n", (45, False)),
    ("Volume: 0.45 [MUTED]\n", (45, True)),
    ("Volume: 1.00\n", (100, False)),
    ("", None),
    ("Node not found\n", None),
])
def test_wpctl_s_volume_is_read(text, expected):
    assert hardware.parse_volume(text) == expected


def test_pipewire_s_dummy_output_is_no_output():
    dummy = ('id 35, type PipeWire:Interface:Node\n    factory.name = "support.null-audio-sink"\n'
             '  * node.description = "Dummy Output"\n')
    real = ('id 52, type PipeWire:Interface:Node\n    factory.name = "api.alsa.pcm.sink"\n'
            '  * node.description = "Built-in Audio Analog Stereo"\n')
    assert not hardware.real_output(dummy)
    assert hardware.real_output(real)
    assert not hardware.real_output("")


def test_lid_events_are_read_from_the_device_s_bytes():
    close = hardware.EVENT.pack(0, 0, hardware.EV_SW, hardware.SW_LID, 1)
    sync = hardware.EVENT.pack(0, 0, 0, 0, 0)
    open_ = hardware.EVENT.pack(0, 0, hardware.EV_SW, hardware.SW_LID, 0)
    other = hardware.EVENT.pack(0, 0, hardware.EV_SW, 2, 1)
    assert hardware.lid_events(close + sync + other + open_ + sync) == [True, False]
    assert hardware.lid_events(b"") == []
    assert struct.calcsize("llHHi") == hardware.EVENT.size


def test_a_mac_s_function_keys_want_fn_unless_fnmode_says_otherwise(macbook, desktop):
    assert hardware.is_mac(macbook) and hardware.function_keys_need_fn(macbook)
    assert hardware.function_key("F4", macbook) == "(fn)F4"
    assert hardware.super_key(macbook) == "⌘"
    write(macbook, "module/hid_apple/parameters/fnmode", "2")
    assert not hardware.function_keys_need_fn(macbook)
    assert hardware.function_key("F4", macbook) == "F4"
    assert not hardware.is_mac(desktop) and not hardware.function_keys_need_fn(desktop)
    assert hardware.function_key("F4", desktop) == "F4"
    assert hardware.super_key(desktop) == "Win"


def test_a_mac_without_the_fnmode_file_wants_fn(tmp_path):
    write(tmp_path, "class/dmi/id/sys_vendor", "Apple Inc.")
    assert hardware.function_keys_need_fn(tmp_path)


def test_the_summary_says_what_there_is(macbook, desktop):
    assert hardware.summary(macbook) == ("battery=71% backlight=gmux_backlight "
                                         "keyboard=smc::kbd_backlight lid=yes mac=yes fn=yes")
    assert hardware.summary(desktop) == "battery=none backlight=none keyboard=none lid=no mac=no fn=no"


# --- the panel among the outputs, and the keys -----------------------------------


def test_the_laptop_s_panel_among_a_compositor_s_outputs():
    listing = ('eDP-1 "Apple Computer Inc Color LCD"\n  Enabled: yes\n  Modes:\n'
               '    2880x1800 px, 59.93 Hz (preferred, current)\n'
               'HDMI-A-1 "Dell"\n  Enabled: yes\n')
    assert hardware.wlr_randr_outputs(listing) == ["eDP-1", "HDMI-A-1"]
    assert hardware.panel_outputs(["eDP-1", "HDMI-A-1"]) == ["eDP-1"]
    assert hardware.panel_outputs(["LVDS-1"]) == ["LVDS-1"]
    assert hardware.panel_outputs(["Virtual-1"]) == ["Virtual-1"]
    assert hardware.panel_outputs(["DP-1", "HDMI-A-1"]) == []
    assert hardware.wlopm_outputs("eDP-1 on\nHDMI-A-1 off\n") == ["eDP-1", "HDMI-A-1"]


@pytest.fixture
def recorded(monkeypatch):
    """brightnessctl and wpctl as a machine answers them: every call kept."""
    calls = []
    state = {"volume": "Volume: 0.45\n", "inspect": 'factory.name = "api.alsa.pcm.sink"\n'}

    def run(argv, **_kwargs):
        calls.append(list(argv))

        class Done:
            returncode = 0
            stdout = state["inspect"] if argv[:2] == ["wpctl", "inspect"] else \
                state["volume"] if argv[:2] == ["wpctl", "get-volume"] else ""
        return Done()

    monkeypatch.setattr(hardware.subprocess, "run", run)
    return calls, state


def test_the_keys_step_the_screen_the_keyboard_and_the_sound(macbook, recorded):
    calls, state = recorded
    assert hardware.key("brightness", "up", macbook)
    assert calls[-1][-1] == "60%" and "gmux_backlight" in calls[-1]
    assert hardware.key("keyboard", "down", macbook)
    assert calls[-1][-1] == "0%" and "smc::kbd_backlight" in calls[-1]
    assert hardware.key("volume", "up", macbook)
    assert calls[-1] == ["wpctl", "set-volume", "--limit", "1.0", "@DEFAULT_AUDIO_SINK@", "50%"]
    state["volume"] = "Volume: 0.45 [MUTED]\n"
    hardware.key("volume", "down", macbook)
    assert ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"] in calls
    assert calls[-1][-1] == "40%"
    hardware.key("volume", "mute", macbook)
    assert calls[-1] == ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"]


def test_the_screen_never_goes_dark_by_its_key(macbook, recorded):
    calls, _ = recorded
    write(macbook, "class/backlight/gmux_backlight/brightness", "40")
    hardware.key("brightness", "down", macbook)
    assert calls[-1][-1] == f"{hardware.SCREEN_FLOOR}%"


def test_a_key_that_is_not_one_and_a_machine_without_the_thing(desktop, recorded):
    calls, state = recorded
    assert not hardware.key("brightness", "sideways", desktop)
    assert not hardware.key("toaster", "up", desktop)
    state["inspect"] = 'factory.name = "support.null-audio-sink"\n'
    for what, how in (("brightness", "up"), ("keyboard", "up"), ("volume", "mute")):
        assert hardware.key(what, how, desktop)
    assert not [c for c in calls if c[0] == "brightnessctl" or "set-mute" in c]


def test_a_program_that_fails_is_logged_with_what_it_said(caplog):
    with caplog.at_level("WARNING", logger="kidux.hardware"):
        assert not hardware._run(["sh", "-c", "echo \"Can't modify brightness:\" >&2; "
                                  "echo Permission denied >&2; exit 1"])
    assert "sh: Can't modify brightness: Permission denied" in caplog.text


def test_a_program_that_is_not_there_is_logged(caplog):
    with caplog.at_level("WARNING", logger="kidux.hardware"):
        assert not hardware._run(["kidux-no-such-program"])
    assert "kidux-no-such-program did not run" in caplog.text


def test_a_program_that_works_says_nothing(caplog):
    with caplog.at_level("WARNING", logger="kidux.hardware"):
        assert hardware._run(["true"])
    assert caplog.text == ""


def test_the_levels_file_is_the_session_s_own(tmp_path):
    assert hardware.levels_file({"XDG_RUNTIME_DIR": str(tmp_path)}) \
        == tmp_path / "kidux" / "levels"
    assert hardware.levels_file({}) is None


def test_a_key_that_changed_a_level_touches_the_levels_file(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(hardware, "volume", lambda: (40, False))
    monkeypatch.setattr(hardware, "set_volume", lambda percent: True)
    assert hardware.key("volume", "up")
    assert (tmp_path / "kidux" / "levels").exists()


def test_a_key_that_changed_nothing_touches_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(hardware, "volume", lambda: (40, False))
    monkeypatch.setattr(hardware, "set_volume", lambda percent: False)
    hardware.key("volume", "up")
    monkeypatch.setattr(hardware, "volume", lambda: None)
    hardware.key("volume", "down")
    assert not (tmp_path / "kidux").exists()


def test_without_a_runtime_directory_a_key_still_works(monkeypatch):
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    monkeypatch.setattr(hardware, "volume", lambda: (40, False))
    monkeypatch.setattr(hardware, "set_volume", lambda percent: True)
    assert hardware.key("volume", "up")
