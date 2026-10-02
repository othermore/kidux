"""The machine's network, for the panel (network.py, D62), against real
outputs of ip and nmcli kept under samples/network: the test machine with a
simulated Wi-Fi joined, and the development MacBook, whose Wi-Fi ifupdown
set up."""

import json
from pathlib import Path

import pytest

from kiduxd import network as net
from kiduxd.errors import Busy, InvalidArgument

SAMPLES = Path(__file__).parent / "samples" / "network"


def sample(name: str) -> str:
    return (SAMPLES / name).read_text()


@pytest.fixture
def sysfs(tmp_path):
    """/sys/class/net as the test machine has it: a wired card, two
    simulated Wi-Fi radios, and the radio monitor without a device."""
    root = tmp_path / "sys"
    for name, wireless in (("enp0s2", False), ("wlan0", True), ("wlan1", True),
                           ("wlp4s0", True)):
        (root / "class" / "net" / name / "device").mkdir(parents=True)
        if wireless:
            (root / "class" / "net" / name / "phy80211").mkdir()
    (root / "class" / "net" / "hwsim0").mkdir(parents=True)
    return root


class Machine:
    """ip, nmcli, iw and systemd-run as a machine answers them: what
    each says is set per test; every call is kept."""

    def __init__(self, *, addr="vm-ip-addr.json", route="vm-ip-route.json",
                 devices="vm-nmcli-devices.txt", wifi="vm-nmcli-wifi.txt",
                 connections="vm-nmcli-connections.txt", manager=True):
        self.answers = {"ip addr": sample(addr), "ip route": sample(route),
                        "devices": sample(devices) if devices else "",
                        "wifi": sample(wifi) if wifi else "",
                        "connections": sample(connections) if connections else ""}
        self.manager = manager
        self.calls: list[list[str]] = []
        self.up_code, self.up_output = 0, "Connection successfully activated"
        self.ping_code = 0
        self.iw = "Not connected.\n"

    def __call__(self, argv, *, timeout=10, input=None):
        self.calls.append(list(argv))
        if argv[:3] == ["ip", "-j", "addr"]:
            return 0, self.answers["ip addr"], ""
        if argv[:3] == ["ip", "-j", "route"]:
            return 0, self.answers["ip route"], ""
        if argv[0] == "iw":
            return 0, self.iw, ""
        if argv[0] == "systemd-run":
            return self.ping_code, "", ""
        if argv[0] != "nmcli":
            return 127, "", "not found"
        if not self.manager:
            return 8, "", "Error: NetworkManager is not running."
        rest = argv[1:]
        if rest[:4] == ["-t", "-f", "RUNNING", "general"]:
            return 0, "running\n", ""
        if "device" in rest and "status" in rest:
            return 0, self.answers["devices"], ""
        if "wifi" in rest and "list" in rest:
            return 0, self.answers["wifi"], ""
        if rest[:4] == ["-t", "-f", "NAME,UUID,TYPE", "connection"]:
            return 0, self.answers["connections"], ""
        if "up" in rest:
            return self.up_code, self.up_output, ""
        return 0, "", ""

    def nm(self, *words):
        return [c for c in self.calls if c[0] == "nmcli" and all(w in c for w in words)]


def network(machine, sysfs, tmp_path, audit=None):
    connections = tmp_path / "system-connections"
    connections.mkdir(exist_ok=True)
    proc = tmp_path / "wireless"
    proc.write_text(sample("macbook-proc-wireless.txt"))
    keep = (lambda *a, **k: audit.append((a, k))) if audit is not None else (lambda *a, **k: None)
    return net.Network(runner=machine, sys_root=sysfs, proc_wireless=proc,
                       connections_dir=connections, audit=keep, start=lambda job: job())


# --- reading ---------------------------------------------------------------------


@pytest.mark.parametrize("line, fields", [
    ("yes:Kidux test net:90:WPA2", ["yes", "Kidux test net", "90", "WPA2"]),
    (r"no:Cafe\: free:40:", ["no", "Cafe: free", "40", ""]),
    (r"no:back\\slash:10:WPA1 WPA2", ["no", "back\\slash", "10", "WPA1 WPA2"]),
    ("wlp4s0:wifi:unmanaged:", ["wlp4s0", "wifi", "unmanaged", ""]),
])
def test_nmcli_s_terse_lines_split_with_their_escapes(line, fields):
    assert net.split_terse(line) == fields


def test_the_test_machine_s_interfaces(sysfs):
    found = net.interfaces(sample("vm-ip-addr.json"), sysfs)
    assert [(i["name"], i["kind"], i["up"], i["address"]) for i in found] == [
        ("enp0s2", "ethernet", True, "10.0.2.15"),
        ("wlan0", "wifi", True, "192.168.77.18"),
        ("wlan1", "wifi", True, "192.168.77.1"),
    ]


def test_an_interface_without_a_device_or_an_address_is_left_out(sysfs):
    names = [i["name"] for i in net.interfaces(sample("vm-ip-addr.json"), sysfs)]
    assert "lo" not in names and "hwsim0" not in names


def test_the_default_route_with_the_lowest_metric(sysfs):
    routes = json.dumps([
        {"dst": "default", "gateway": "192.168.77.1", "dev": "wlan0", "metric": 600},
        {"dst": "default", "gateway": "10.0.2.2", "dev": "enp0s2", "metric": 100},
    ])
    assert net.default_gateway(routes) == ("10.0.2.2", "enp0s2")
    assert net.default_gateway("[]") == ("", "")
    assert net.default_gateway("not json") == ("", "")


def test_networks_once_each_the_one_in_use_first():
    wifi = "\n".join(["no:Neighbours:40:WPA2", "no:Neighbours:70:WPA2", "no::30:WPA2",
                      "yes:Home:55:WPA1 WPA2", "no:Cafe:80:", "no:Office:60:WPA2 802.1X",
                      "no:New:50:WPA3"])
    found = net.networks(wifi, {"Home"})
    assert [(n["ssid"], n["signal"], n["active"], n["known"], n["security"]) for n in found] == [
        ("Home", 55, True, True, "psk"),
        ("Cafe", 80, False, False, "open"),
        ("Neighbours", 70, False, False, "psk"),
        ("Office", 60, False, False, "unsupported"),
        ("New", 50, False, False, "sae"),
    ]
    assert [n["secured"] for n in found] == [True, False, True, True, True]


@pytest.mark.parametrize("security, kind", [
    ("", "open"), ("WPA2", "psk"), ("WPA1 WPA2", "psk"), ("WPA2 WPA3", "psk"),
    ("WPA3", "sae"), ("WEP", "unsupported"), ("WPA2 802.1X", "unsupported"),
])
def test_what_kidux_can_join(security, kind):
    assert net.security_kind(security) == kind


def test_a_wifi_ifupdown_set_up_is_named_by_iw_and_its_signal_read():
    assert net.iw_network(sample("macbook-iw-link.txt")) == "Casa"
    assert net.iw_network("Connected to 02:00:5e:00:53:01 (on wlan0)\n\tSSID: Casa 5G\n") \
        == "Casa 5G"
    assert net.iw_network("Not connected.\n") == "" and net.iw_network("") == ""
    assert net.wireless_signal(sample("macbook-proc-wireless.txt"), "wlp4s0") == 93
    assert net.wireless_signal(sample("macbook-proc-wireless.txt"), "wlan0") == -1


@pytest.mark.parametrize("kind, password", [
    ("psk", "short"), ("psk", "x" * 64), ("psk", "tab\there!"), ("psk", ""),
    ("psk", "ñ" * 32), ("unsupported", "whatever1"), ("sae", ""),
])
def test_a_password_the_network_cannot_take_is_refused(kind, password):
    with pytest.raises(InvalidArgument):
        net.check_password(kind, password)


@pytest.mark.parametrize("kind, password", [
    ("psk", "kidux password 1"), ("psk", "a" * 63), ("psk", "0123456789abcdef" * 4),
    ("psk", "contraseña de casa"), ("sae", "x"), ("open", ""),
])
def test_a_password_the_network_takes(kind, password):
    net.check_password(kind, password)


def test_the_connection_file_joins_the_network_for_the_whole_machine():
    from gi.repository import GLib

    data = net.connection_file("Café; home", "kidux password 1", "psk", "1234")
    keyfile = GLib.KeyFile()
    keyfile.load_from_data(data, len(data.encode()), GLib.KeyFileFlags.NONE)
    assert keyfile.get_string("wifi", "ssid") == "Café; home"
    assert keyfile.get_string("connection", "id") == "Café; home"
    assert keyfile.get_string("wifi-security", "key-mgmt") == "wpa-psk"
    assert keyfile.get_string("wifi-security", "psk") == "kidux password 1"
    assert "permissions" not in data
    open_file = net.connection_file("Cafe", "", "open", "5678")
    assert "wifi-security" not in open_file


@pytest.mark.parametrize("output, failure", [
    ("Error: Connection activation failed: Secrets were required, but not provided\n",
     "wrong_password"),
    ("Error: Connection activation failed: The Wi-Fi network could not be found\nHint: x\n",
     "Connection activation failed: The Wi-Fi network could not be found"),
    ("", "no answer"),
])
def test_what_a_failure_says(output, failure):
    assert net.failure_of(output) == failure


# --- the page's reading --------------------------------------------------------------


def test_the_test_machine_with_its_simulated_wifi_joined(sysfs, tmp_path):
    summary, found, networks = network(Machine(), sysfs, tmp_path).read()
    assert summary["manager"] and summary["wifi"] and summary["wifi_changeable"]
    assert summary["gateway"] == "10.0.2.2" and summary["router"] == ""
    wlan0 = next(i for i in found if i["name"] == "wlan0")
    assert wlan0["managed"] and wlan0["network"] == "Kidux test net" and wlan0["signal"] == 90
    assert not next(i for i in found if i["name"] == "enp0s2")["managed"]
    assert networks == [{"ssid": "Kidux test net", "signal": 90, "secured": True,
                         "security": "psk", "active": True, "known": True}]


def test_the_macbook_whose_wifi_ifupdown_set_up(sysfs, tmp_path):
    machine = Machine(addr="macbook-ip-addr.json", route="macbook-ip-route.json",
                      devices="macbook-nmcli-devices.txt", wifi=None, connections=None)
    machine.iw = sample("macbook-iw-link.txt")
    summary, found, networks = network(machine, sysfs, tmp_path).read()
    assert summary["manager"] and summary["wifi"] and not summary["wifi_changeable"]
    assert summary["gateway"] == "192.168.1.1"
    wifi = next(i for i in found if i["name"] == "wlp4s0")
    assert not wifi["managed"] and wifi["network"] == "Casa" and wifi["signal"] == 93
    assert networks == [] and not machine.nm("wifi", "list")
    # Named by iw, never by wpa_cli, whose answer cannot reach the daemon.
    assert ["iw", "dev", "wlp4s0", "link"] in machine.calls
    assert not [c for c in machine.calls if c[0] == "wpa_cli"]


def test_without_networkmanager_the_facts_and_nothing_to_change(sysfs, tmp_path):
    summary, found, networks = network(Machine(manager=False), sysfs, tmp_path).read()
    assert not summary["manager"] and not summary["wifi_changeable"]
    assert [i["name"] for i in found] == ["enp0s2", "wlan0", "wlan1"] and networks == []


# --- the jobs --------------------------------------------------------------------------


def test_looking_again_scans_and_pings_the_gateway_outside_the_daemon(sysfs, tmp_path):
    machine = Machine()
    page = network(machine, sysfs, tmp_path)
    page.check()
    # The scan waited for, not only asked for: the page reads a fresh list.
    assert machine.nm("wifi", "list", "--rescan", "yes")
    ping = next(c for c in machine.calls if c[0] == "systemd-run")
    assert "--property=DynamicUser=yes" in ping and ping[-1] == "10.0.2.2"
    assert page.read()[0]["router"] == "answers"
    machine.ping_code = 1
    page.check()
    assert page.read()[0]["router"] == "silent" and page.state.job == "idle"


def test_the_router_s_answer_is_for_the_gateway_it_was_asked_of(sysfs, tmp_path):
    machine = Machine()
    page = network(machine, sysfs, tmp_path)
    page.check()
    machine.answers["ip route"] = json.dumps([{"dst": "default", "gateway": "192.168.1.1",
                                               "dev": "wlan0", "metric": 600}])
    assert page.read()[0]["router"] == ""


def test_joining_a_new_network_writes_its_file_and_keeps_the_older_one_out(sysfs, tmp_path):
    machine = Machine()
    machine.answers["wifi"] = "no:Kidux test net:90:WPA2\nno:Cafe:70:\n"
    audit = []
    page = network(machine, sysfs, tmp_path, audit)
    page.connect("Kidux test net", "kidux password 1")
    files = list((tmp_path / "system-connections").glob("kidux-*.nmconnection"))
    assert len(files) == 1 and oct(files[0].stat().st_mode & 0o777) == "0o600"
    assert "psk=kidux password 1" in files[0].read_text()
    assert machine.nm("connection", "load")
    # The connection that was there before, with the old password, goes.
    assert machine.nm("connection", "delete", "6942119d-804b-4a7f-8a15-100430a70e94")
    summary = page.read()[0]
    assert (summary["outcome"], summary["ssid"], summary["job"]) == \
        ("connected", "Kidux test net", "idle")
    # The password is on no command line and in no audit line.
    assert not any("kidux password 1" in " ".join(c) for c in machine.calls)
    assert "kidux password 1" not in repr(audit)
    assert audit[-1][0][:2] == ("wifi joined", "ok")


def test_a_wrong_password_is_said_and_not_kept(sysfs, tmp_path):
    machine = Machine()
    machine.answers["connections"] = ""
    machine.up_code = 4
    machine.up_output = ("Error: Connection activation failed: Secrets were required, "
                         "but not provided\n")
    page = network(machine, sysfs, tmp_path)
    page.connect("Kidux test net", "not the password")
    assert list((tmp_path / "system-connections").iterdir()) == []
    assert machine.nm("connection", "delete")
    summary = page.read()[0]
    assert (summary["outcome"], summary["detail"]) == ("failed", "wrong_password")


def test_a_known_network_is_joined_again_without_a_password(sysfs, tmp_path):
    machine = Machine()
    page = network(machine, sysfs, tmp_path)
    page.connect("Kidux test net", "")
    up = machine.nm("connection", "up")[0]
    assert up[-1] == "6942119d-804b-4a7f-8a15-100430a70e94"
    assert list((tmp_path / "system-connections").iterdir()) == []


def test_an_open_network_needs_no_password(sysfs, tmp_path):
    machine = Machine()
    machine.answers["wifi"] = "no:Cafe:70:\n"
    page = network(machine, sysfs, tmp_path)
    page.connect("Cafe", "")
    text = next((tmp_path / "system-connections").glob("*")).read_text()
    assert "psk" not in text


@pytest.mark.parametrize("ssid, password", [
    ("Not in reach", "kidux password 1"),
    ("", "kidux password 1"),
    ("x" * 33, "kidux password 1"),
    ("Kidux test net", "short"),
])
def test_what_cannot_be_joined_is_refused_before_any_job(sysfs, tmp_path, ssid, password):
    machine = Machine()
    machine.answers["connections"] = ""
    page = network(machine, sysfs, tmp_path)
    with pytest.raises(InvalidArgument):
        page.connect(ssid, password)
    assert page.state.job == "idle" and not machine.nm("connection", "up")


def test_a_secured_network_never_joined_needs_its_password(sysfs, tmp_path):
    machine = Machine()
    machine.answers["connections"] = ""
    with pytest.raises(InvalidArgument):
        network(machine, sysfs, tmp_path).connect("Kidux test net", "")


def test_one_job_at_a_time(sysfs, tmp_path):
    machine = Machine()
    started = []
    page = net.Network(runner=machine, sys_root=sysfs, start=started.append,
                       connections_dir=tmp_path)
    page.check()
    with pytest.raises(Busy):
        page.connect("Kidux test net", "kidux password 1")
    with pytest.raises(Busy):
        page.forget("Kidux test net")
    assert page.read()[0]["job"] == "checking"
    started[0]()
    assert page.read()[0]["job"] == "idle"


def test_forgetting_deletes_every_connection_to_the_network(sysfs, tmp_path):
    machine = Machine()
    machine.answers["connections"] = ("Home:aaaa:802-11-wireless\nHome:bbbb:802-11-wireless\n"
                                      "Wired:cccc:802-3-ethernet\n")
    page = network(machine, sysfs, tmp_path)
    page.forget("Home")
    deleted = [c[-1] for c in machine.nm("connection", "delete")]
    assert deleted == ["aaaa", "bbbb"]
    assert page.read()[0]["outcome"] == "forgotten"
    page.forget("Nothing")
    assert page.read()[0]["outcome"] == "failed"
