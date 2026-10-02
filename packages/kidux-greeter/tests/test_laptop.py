"""A laptop's keys on the trusted screens (laptop.py, D61)."""

from kidux_greeter import laptop


class Hardware:
    def __init__(self):
        self.keys = []

    def key(self, what, how):
        self.keys.append((what, how))
        return True


def test_each_of_a_laptop_s_keys_does_its_thing():
    hardware = Hardware()
    for keyval in laptop.KEYSYMS:
        assert laptop.press(keyval, hardware)
    assert hardware.keys == [("brightness", "up"), ("brightness", "down"),
                             ("keyboard", "up"), ("keyboard", "down"),
                             ("volume", "up"), ("volume", "down"), ("volume", "mute")]


def test_any_other_key_is_left_to_the_screen():
    hardware = Hardware()
    # Escape, Tab, a, F4, and nothing at all.
    for keyval in (0xFF1B, 0xFF09, 0x61, 0xFFC1, 0):
        assert not laptop.press(keyval, hardware)
    assert hardware.keys == []


def test_every_key_is_one_kidux_hardware_does():
    from kidux import hardware

    assert {f"{what} {how}" for _name, (what, how) in laptop.KEYSYMS.values()} \
        == set(hardware.KEYS)

