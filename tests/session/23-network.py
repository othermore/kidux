"""The adult panel's Network page (phase-3-plan.md, step 3.23; D62).

The test machine has one wired card, which NetworkManager leaves to
systemd-networkd, so a Wi-Fi is made for it: two simulated radios
(`mac80211_hwsim`), one an access point with a password (`hostapd`, and
`dnsmasq` to give addresses), the other NetworkManager's. On the panel, by
keyboard: the page shows the wired connection and the router answering, and
the network in reach with a padlock; Connect asks its password in place, a
wrong one is said and not kept, the right one joins, in a connection file of
root's that holds the password where no command line did; Forget asks once
and forgets. Then the same radio as the Debian installer leaves a Wi-Fi:
NetworkManager's hands off it and wpa_supplicant started for it by hand;
the page names its network, and answers well inside the greeter's ten
seconds (step 3.24: nothing the daemon runs may wait on an answer that
cannot reach it). Everything made for the test is taken away at the end.
"""

import time

from sessionlib import (
    Machine,
    children_count,
    greeter_log,
    open_panel,
    report,
    root,
    screens_counted,
    wait,
)

AUDIT = "/home/.kidux/state/audit.log"
AS = "runuser -u debian -- /usr/local/bin/kidux-as"
SSID, PASSWORD = "Kidux test net", "kidux password 1"
CONNECTIONS = "/etc/NetworkManager/system-connections"
HOSTAPD = f"""interface=wlan1
driver=nl80211
ssid={SSID}
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase={PASSWORD}
"""
#: wpa_supplicant as ifupdown starts it, its socket under /run.
SUPPLICANT = f"""ctrl_interface=/run/wpa_supplicant
network={{
    ssid="{SSID}"
    psk="{PASSWORD}"
}}
"""


def audited(action: str, outcome: str) -> int:
    lines = root(f"grep '\"action\": \"{action}\"' {AUDIT}").stdout.splitlines()
    return sum(f'"outcome": "{outcome}"' in line for line in lines)


def joined() -> bool:
    status = root("nmcli -t -f DEVICE,STATE,CONNECTION device status").stdout
    return f"wlan0:connected:{SSID}" in status


def kidux_files() -> list[str]:
    return root(f"ls {CONNECTIONS} | grep '^kidux-'").stdout.split()


def make_the_wifi() -> bool:
    """Two simulated radios, an access point on the second, and NetworkManager
    seeing it from the first."""
    installed = root("DEBIAN_FRONTEND=noninteractive apt-get install -y "
                     "--no-install-recommends hostapd dnsmasq-base", timeout=600)
    root("modprobe mac80211_hwsim radios=2")
    wait(lambda: root("ip link show wlan1").returncode == 0, 10, 0.5)
    root("nmcli device set wlan1 managed no")
    root("ip link set wlan1 up && ip addr add 192.168.77.1/24 dev wlan1")
    root(f"printf '%s' '{HOSTAPD}' > /run/kidux-test-hostapd.conf")
    root("systemd-run --quiet --unit=kidux-test-ap hostapd /run/kidux-test-hostapd.conf")
    root("systemd-run --quiet --unit=kidux-test-dhcp dnsmasq --no-daemon --interface=wlan1 "
         "--bind-interfaces --port=0 --dhcp-range=192.168.77.10,192.168.77.50,12h")
    time.sleep(3)
    root("nmcli device wifi rescan")
    return installed.returncode == 0 and wait(
        lambda: SSID in root("nmcli -t -f SSID device wifi list --rescan no").stdout, 30, 2)


def as_the_installer_leaves_it() -> bool:
    """wlan0 as ifupdown runs a Wi-Fi: NetworkManager told to leave it,
    wpa_supplicant started for it by hand, an address of its own."""
    root("nmcli device set wlan0 managed no")
    root(f"printf '%s' '{SUPPLICANT}' > /run/kidux-test-wpa.conf")
    root("systemd-run --quiet --unit=kidux-test-wpa wpa_supplicant -i wlan0 "
         "-c /run/kidux-test-wpa.conf")
    root("ip addr add 192.168.77.10/24 dev wlan0")
    return wait(lambda: f"SSID: {SSID}" in root("iw dev wlan0 link").stdout, 30, 1)


def named_at_once() -> tuple[bool, str]:
    """The page's reading, as the panel asks for it, and how long it took."""
    start = time.monotonic()
    listed = root(f"{AS} network", timeout=60)
    took = time.monotonic() - start
    said = f"{listed.stdout}{listed.stderr}answered in {took:.2f} s"
    return (f"wlan0 wifi 192.168.77.10 {SSID}" in listed.stdout.splitlines()
            and took < 5), said


def take_it_away() -> None:
    for name in kidux_files():
        root(f"nmcli connection delete filename {CONNECTIONS}/{name}")
    root("systemctl stop kidux-test-wpa kidux-test-ap kidux-test-dhcp")
    root("rm -f /run/kidux-test-wpa.conf")
    root("rmmod mac80211_hwsim")
    root("rm -f /run/kidux-test-hostapd.conf")


def to_the_network_page(machine: Machine) -> bool:
    """From the first child's name: back past the five controls that give
    time, every child and Add, to Network; then the page looks again, the
    router asked and the Wi-Fi scanned, and says so when it is done."""
    for _ in range(5 + children_count() + 2):
        machine.key("shift-tab")
    before = machine.mark()
    machine.key("ret")
    return machine.shown("panel_network", before, 10)


def looked_again(seconds: float = 60) -> bool:
    """Wait until the Network page has looked again: while the router is
    asked and the Wi-Fi scanned the page is drawn once a second, its
    buttons insensitive, and it is done when it has not been drawn for
    three seconds. A fixed wait was too short under the battery's load."""
    end = time.monotonic() + seconds
    last, quiet = screens_counted(("panel_network",))["panel_network"], 0
    while time.monotonic() < end:
        time.sleep(1)
        now = screens_counted(("panel_network",))["panel_network"]
        quiet = quiet + 1 if now == last else 0
        last = now
        if quiet >= 3:
            return True
    return False


def run(machine: Machine) -> None:
    report("a simulated Wi-Fi with a password is in reach of the machine", make_the_wifi(),
           root("nmcli -t -f DEVICE,TYPE,STATE device status").stdout
           + root("systemctl status kidux-test-ap --no-pager").stdout[-600:])

    report("the adult panel opens from the sign-in screen", open_panel(machine), greeter_log())
    machine.still()
    report("its Network page opens by keyboard", to_the_network_page(machine), greeter_log())
    looked_again()                               # the router pinged, the Wi-Fi scanned
    machine.still()
    machine.screenshot("panel-network-before")

    # A wrong password first: from Look again, Tab to Connect, which asks
    # the password in place, typed and Enter.
    failures = audited("wifi join", "failed")
    machine.key("tab")
    machine.key("ret")
    time.sleep(1)
    machine.type("not the password")
    machine.key("ret")
    report("a wrong password is said, and nothing of it is kept",
           wait(lambda: audited("wifi join", "failed") > failures, 45, 2)
           and not joined() and kidux_files() == [],
           root(f"tail -3 {AUDIT}").stdout + root(f"ls -l {CONNECTIONS}").stdout)
    time.sleep(2)
    machine.screenshot("panel-network-wrong-password")

    # The page asks again with the field in place and the focus in it.
    joins = audited("wifi joined", "ok")
    machine.type(PASSWORD)
    machine.key("ret")
    report("the right one joins the network",
           wait(lambda: audited("wifi joined", "ok") > joins, 45, 2) and wait(joined, 15),
           root("nmcli -t -f DEVICE,STATE,CONNECTION device status").stdout
           + root(f"tail -3 {AUDIT}").stdout)
    files = kidux_files()
    kept = root(f"stat -c '%U %a' {CONNECTIONS}/{files[0]}").stdout.strip() if files else ""
    report("in a connection file of root's, 0600, the only place its password is",
           len(files) == 1 and kept == "root 600"
           and PASSWORD not in root(f"cat {AUDIT}").stdout
           and PASSWORD not in root("journalctl -b -o cat -u kidux-daemon").stdout,
           f"{files} {kept}")
    time.sleep(3)
    machine.still()
    machine.screenshot("panel-network")

    # Forget: from Look again, Tab to Forget, which asks once, Cancel first.
    forgotten = audited("wifi forgotten", "ok")
    machine.key("tab")
    machine.key("ret")
    time.sleep(1)
    machine.key("tab")                           # from Cancel to Forget
    machine.key("ret")
    report("Forget asks once, and forgets the network",
           wait(lambda: audited("wifi forgotten", "ok") > forgotten, 30, 2)
           and wait(lambda: not joined() and kidux_files() == [], 15),
           root(f"tail -3 {AUDIT}").stdout + root(f"ls -l {CONNECTIONS}").stdout)

    report("the radio run as the Debian installer leaves a Wi-Fi",
           as_the_installer_leaves_it(),
           root("iw dev wlan0 link").stdout
           + root("systemctl status kidux-test-wpa --no-pager").stdout[-600:])
    ok, said = named_at_once()
    report("the page names its network, and answers within five seconds", ok, said)

    before = machine.mark()
    machine.key("esc")                           # the panel closes
    machine.shown("choose", before)
    take_it_away()
    machine.still()
