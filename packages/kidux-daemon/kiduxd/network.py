"""The machine's network, for the panel's Network page (daemon.md section 16, D62).

What the page shows is read here: every interface with an address or a
device behind it, from `ip -j addr`; the default route's gateway, from `ip
-j route`; and, when NetworkManager runs, which interfaces it manages and
the Wi-Fi networks in reach, from `nmcli -t`. An interface NetworkManager
does not manage, a Wi-Fi set up by `ifupdown` when Debian was installed, is
shown and never changed: `iw` and `/proc/net/wireless` say its network's
name and signal. Not `wpa_cli`, whose answer comes back to a socket it
binds under `/tmp`, which the daemon's own `/tmp` hides from
`wpa_supplicant`: it would wait out its ten seconds every time.

What the page changes, only through NetworkManager: a Wi-Fi network joined,
with its password written into a connection file of NetworkManager's own,
root's and 0600, and never on a command line, where any user could read it
in `ps`; and a network forgotten. Each is a job in a thread of its own, as
is looking again (a rescan, and one ping of the gateway), since each can take
seconds and the daemon's bus must never wait for it. One job at a time; the
panel asks `state` again every second while one runs.

The daemon's unit may not open an internet socket (`RestrictAddressFamilies`),
so the ping runs in a transient unit of its own, as a dynamic user, through
`systemd-run`. `ip` and `iw` speak netlink and `nmcli` the system bus, all
allowed.
"""

import json
import os
import re
import subprocess
import threading
import uuid as uuidlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .errors import Busy, InvalidArgument

SYS = Path("/sys")
PROC_WIRELESS = Path("/proc/net/wireless")
CONNECTIONS = Path("/etc/NetworkManager/system-connections")

#: How long joining a network may take before it is given up, in seconds:
#: nmcli's own wait, and a little more for the process around it.
CONNECT_SECONDS = 40
#: Any other nmcli or ip call.
QUICK_SECONDS = 10
#: A Wi-Fi scan waited for: a card takes a few seconds, some more.
SCAN_SECONDS = 20

#: What nmcli says when a secured network refused the password it was given.
WRONG_PASSWORD = "Secrets were required"

#: A WPA key given as 64 hex digits, which is the key itself; anything else
#: is a passphrase, 8 to 63 bytes long as NetworkManager and wpa_supplicant
#: count it, so that a letter with an accent counts as two.
HEX_KEY = re.compile(r"\A[0-9a-fA-F]{64}\Z")

Run = Callable[..., tuple[int, str, str]]


def run(argv: list[str], *, timeout: float = QUICK_SECONDS, input: str | None = None
        ) -> tuple[int, str, str]:
    """A program's exit status and output; 127 when it is not there, 124 when
    it took too long."""
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                              input=input)
    except FileNotFoundError:
        return 127, "", f"{argv[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, "", f"{argv[0]}: took longer than {timeout:.0f} seconds"
    return done.returncode, done.stdout, done.stderr


# --- reading ------------------------------------------------------------------

def split_terse(line: str) -> list[str]:
    """One line of `nmcli -t`: fields split on ':', with '\\:' and '\\\\' as
    the colon and the backslash inside a field (a network's name may have
    either)."""
    fields, current, escaped = [], [], False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(current))
            current = []
        else:
            current.append(char)
    fields.append("".join(current))
    return fields


def kind_of(name: str, link_type: str, sys_root: Path = SYS) -> str:
    """"wifi", "ethernet" or "other" for an interface."""
    net = sys_root / "class" / "net" / name
    if (net / "wireless").exists() or (net / "phy80211").exists():
        return "wifi"
    if link_type == "ether":
        return "ethernet"
    return "other"


def interfaces(ip_addr: str, sys_root: Path = SYS) -> list[dict]:
    """`ip -j addr` as the page lists it: every interface but the loopback
    that has a device behind it or an IPv4 address, virtual bridges and the
    like without one left out, by name."""
    try:
        entries = json.loads(ip_addr or "[]")
    except json.JSONDecodeError:
        return []
    found = []
    for entry in entries:
        name = entry.get("ifname", "")
        link_type = entry.get("link_type", "")
        if not name or link_type == "loopback":
            continue
        address = next((info.get("local", "") for info in entry.get("addr_info", [])
                        if info.get("family") == "inet"), "")
        if not address and not (sys_root / "class" / "net" / name / "device").exists():
            continue
        found.append({"name": name, "kind": kind_of(name, link_type, sys_root),
                      "up": entry.get("operstate") == "UP", "address": address,
                      "network": "", "signal": -1, "managed": False})
    return sorted(found, key=lambda i: i["name"])


def default_gateway(ip_route: str) -> tuple[str, str]:
    """The default route with the lowest metric, as (gateway, interface);
    ("", "") without one."""
    try:
        routes = json.loads(ip_route or "[]")
    except json.JSONDecodeError:
        return "", ""
    routes = [r for r in routes if r.get("dst") == "default" and r.get("gateway")]
    if not routes:
        return "", ""
    best = min(routes, key=lambda r: r.get("metric", 0))
    return best["gateway"], best.get("dev", "")


def devices(nmcli_devices: str) -> dict[str, dict]:
    """`nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status`, by device."""
    found = {}
    for line in nmcli_devices.splitlines():
        parts = split_terse(line)
        if len(parts) >= 4 and parts[0]:
            found[parts[0]] = {"type": parts[1], "state": parts[2], "connection": parts[3]}
    return found


def security_kind(security: str) -> str:
    """How Kidux can join a network with this `SECURITY` field: "open",
    "psk" (WPA or WPA2 personal, and WPA3 in transition), "sae" (WPA3 only),
    or "unsupported" (enterprise, WEP)."""
    words = security.split()
    if not words:
        return "open"
    if "802.1X" in words or "WEP" in words:
        return "unsupported"
    if words == ["WPA3"]:
        return "sae"
    if any(w in ("WPA1", "WPA2", "WPA3", "WPA") for w in words):
        return "psk"
    return "unsupported"


def networks(nmcli_wifi: str, known: set[str]) -> list[dict]:
    """`nmcli -t -f ACTIVE,SSID,SIGNAL,SECURITY device wifi list`: each
    network once, at its strongest, hidden ones left out, the one in use
    first and then by signal. `known` is the networks with a saved
    connection, by name."""
    found: dict[str, dict] = {}
    for line in nmcli_wifi.splitlines():
        parts = split_terse(line)
        if len(parts) < 4 or not parts[1]:
            continue
        active, ssid, signal, security = parts[0] == "yes", parts[1], parts[2], parts[3]
        try:
            strength = int(signal)
        except ValueError:
            strength = 0
        entry = found.get(ssid)
        if entry is None or strength > entry["signal"] or active:
            kind = security_kind(security)
            found[ssid] = {"ssid": ssid, "signal": max(strength, entry["signal"] if entry
                                                       else 0),
                           "secured": kind != "open", "security": kind,
                           "active": active or bool(entry and entry["active"]),
                           "known": ssid in known}
    return sorted(found.values(), key=lambda n: (not n["active"], -n["signal"], n["ssid"]))


def connections(nmcli_connections: str) -> list[tuple[str, str]]:
    """`nmcli -t -f NAME,UUID,TYPE connection show`: the Wi-Fi connections,
    as (name, uuid); a network may have more than one."""
    found = []
    for line in nmcli_connections.splitlines():
        parts = split_terse(line)
        if len(parts) >= 3 and parts[2] == "802-11-wireless":
            found.append((parts[0], parts[1]))
    return found


def iw_network(iw_link: str) -> str:
    """The network's name in `iw dev <name> link`, for a Wi-Fi
    NetworkManager does not manage; "" when it says `Not connected.`"""
    for line in iw_link.splitlines():
        if line.strip().startswith("SSID: "):
            return line.strip()[len("SSID: "):]
    return ""


def wireless_signal(proc: str, name: str) -> int:
    """`/proc/net/wireless`'s link quality for `name`, out of 70, as a
    percentage; -1 when it does not say."""
    for line in proc.splitlines():
        head, _, rest = line.partition(":")
        if head.strip() == name:
            words = rest.split()
            try:
                return max(0, min(100, round(float(words[1].rstrip(".")) * 100 / 70)))
            except (IndexError, ValueError):
                return -1
    return -1


def passphrase_fits(password: str) -> bool:
    """Whether a WPA personal network can take `password`: printable, 8 to 63
    bytes long, or the 64 hex digits of the key itself."""
    return bool(HEX_KEY.match(password)) or (
        password.isprintable() and 8 <= len(password.encode()) <= 63)


def check_password(kind: str, password: str) -> None:
    if kind == "open":
        return
    if kind == "unsupported":
        raise InvalidArgument("this network needs a setting Kidux cannot make")
    if kind == "psk" and not passphrase_fits(password or ""):
        raise InvalidArgument("a Wi-Fi password is 8 to 63 characters")
    if kind == "sae" and not (password and len(password) <= 128 and password.isprintable()):
        raise InvalidArgument("a Wi-Fi password is up to 128 characters")


def connection_file(ssid: str, password: str, kind: str, uuid: str) -> str:
    """A NetworkManager keyfile that joins `ssid`: a connection for the
    whole machine, so that the Wi-Fi comes up before anyone signs in, and
    that comes back by itself after a restart. GLib's own writer does the
    escaping a network's name may need."""
    from gi.repository import GLib

    keyfile = GLib.KeyFile()
    keyfile.set_string("connection", "id", ssid)
    keyfile.set_string("connection", "uuid", uuid)
    keyfile.set_string("connection", "type", "wifi")
    keyfile.set_string("wifi", "mode", "infrastructure")
    keyfile.set_string("wifi", "ssid", ssid)
    if kind in ("psk", "sae"):
        keyfile.set_string("wifi-security", "key-mgmt", "wpa-psk" if kind == "psk" else "sae")
        keyfile.set_string("wifi-security", "psk", password)
    keyfile.set_string("ipv4", "method", "auto")
    keyfile.set_string("ipv6", "method", "auto")
    return keyfile.to_data()[0]


def failure_of(output: str) -> str:
    """What joining a network says when it fails: "wrong_password", or
    nmcli's own sentence, its "Error: " taken off."""
    if WRONG_PASSWORD in output:
        return "wrong_password"
    for line in output.splitlines():
        if line.startswith("Error: "):
            return line[len("Error: "):].strip()
    return output.strip().splitlines()[-1] if output.strip() else "no answer"


# --- the jobs -----------------------------------------------------------------

@dataclass
class State:
    """What the page shows between one reading and the next."""
    #: "idle", "checking", "connecting" or "forgetting".
    job: str = "idle"
    #: The gateway last pinged, and whether it answered: "answers",
    #: "silent", or "" before it has been asked.
    gateway: str = ""
    router: str = ""
    #: How the last job ended, for the page to say: "connected", "failed",
    #: "forgotten" or "", the network it was about, and why it failed.
    outcome: str = ""
    ssid: str = ""
    detail: str = ""
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


class Network:
    def __init__(self, *, runner: Run = run, sys_root: Path = SYS,
                 proc_wireless: Path = PROC_WIRELESS, connections_dir: Path = CONNECTIONS,
                 audit: Callable[..., None] = lambda *a, **k: None,
                 start: Callable[[Callable[[], None]], None] | None = None) -> None:
        self._run = runner
        self._sys = sys_root
        self._proc_wireless = proc_wireless
        self._connections = connections_dir
        self._audit = audit
        self._start = start or (lambda job: threading.Thread(target=job, daemon=True).start())
        self.state = State()

    # --- what is there ------------------------------------------------------

    def _nm(self, *args: str, timeout: float = QUICK_SECONDS) -> tuple[int, str, str]:
        return self._run(["nmcli", *args], timeout=timeout)

    def manager_runs(self) -> bool:
        code, out, _ = self._nm("-t", "-f", "RUNNING", "general")
        return code == 0 and out.strip() == "running"

    def read(self) -> tuple[dict, list[dict], list[dict]]:
        """The page's three parts: a summary, the interfaces, the networks."""
        _, addr, _ = self._run(["ip", "-j", "addr"])
        _, route, _ = self._run(["ip", "-j", "route", "show", "default"])
        found = interfaces(addr, self._sys)
        gateway, route_dev = default_gateway(route)
        manager = self.manager_runs()
        managed = {}
        if manager:
            _, out, _ = self._nm("-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device",
                                 "status")
            managed = devices(out)
        try:
            proc = self._proc_wireless.read_text()
        except OSError:
            proc = ""
        for interface in found:
            device = managed.get(interface["name"])
            interface["managed"] = bool(device and device["state"] != "unmanaged")
            if interface["kind"] == "wifi":
                if device and interface["managed"]:
                    interface["network"] = device["connection"]
                elif interface["address"]:
                    _, out, _ = self._run(["iw", "dev", interface["name"], "link"])
                    interface["network"] = iw_network(out)
                interface["signal"] = wireless_signal(proc, interface["name"])
        wifi_changeable = manager and any(i["kind"] == "wifi" and i["managed"] for i in found)
        networks_found: list[dict] = []
        if wifi_changeable:
            _, known_out, _ = self._nm("-t", "-f", "NAME,UUID,TYPE", "connection", "show")
            _, wifi_out, _ = self._nm("-t", "-f", "ACTIVE,SSID,SIGNAL,SECURITY", "device",
                                      "wifi", "list", "--rescan", "no")
            networks_found = networks(wifi_out, {name for name, _ in connections(known_out)})
            for interface in found:
                active = next((n for n in networks_found if n["active"]), None)
                if interface["kind"] == "wifi" and interface["managed"] and active \
                        and interface["network"] == active["ssid"]:
                    interface["signal"] = active["signal"]
        state = self.state
        with state.lock:
            router = state.router if state.gateway == gateway else ""
            summary = {"manager": manager, "wifi": any(i["kind"] == "wifi" for i in found),
                       "wifi_changeable": wifi_changeable, "gateway": gateway,
                       "gateway_interface": route_dev, "router": router, "job": state.job,
                       "outcome": state.outcome, "ssid": state.ssid, "detail": state.detail}
        return summary, found, networks_found

    # --- the jobs -----------------------------------------------------------

    def _begin(self, job: str) -> None:
        with self.state.lock:
            if self.state.job != "idle":
                raise Busy(f"the network is already {self.state.job}")
            self.state.job = job
            self.state.outcome = self.state.ssid = self.state.detail = ""

    def _end(self, outcome: str = "", ssid: str = "", detail: str = "") -> None:
        with self.state.lock:
            self.state.job = "idle"
            self.state.outcome, self.state.ssid, self.state.detail = outcome, ssid, detail

    def check(self) -> None:
        """Look again: the Wi-Fi scanned anew, when NetworkManager manages
        one, and the gateway pinged once. The scan is waited for (`wifi list
        --rescan yes` returns when it is done; `wifi rescan` only asks for
        it), so that the page reads a fresh list when the job ends."""
        self._begin("checking")

        def job():
            try:
                if self.manager_runs():
                    self._nm("device", "wifi", "list", "--rescan", "yes",
                             timeout=SCAN_SECONDS)
                _, route, _ = self._run(["ip", "-j", "route", "show", "default"])
                gateway, _ = default_gateway(route)
                answer = ""
                if gateway:
                    code, _, _ = self._run(
                        ["systemd-run", "--wait", "--collect", "--quiet", "--pipe",
                         "--property=DynamicUser=yes", "--property=ProtectSystem=strict",
                         "--property=PrivateTmp=yes", "--",
                         "ping", "-n", "-q", "-c", "1", "-W", "1", gateway],
                        timeout=QUICK_SECONDS)
                    answer = "answers" if code == 0 else "silent"
                with self.state.lock:
                    self.state.gateway, self.state.router = gateway, answer
            finally:
                self._end()

        self._start(job)

    def connect(self, ssid: str, password: str) -> None:
        """Join `ssid`: a saved connection when there is one and no new
        password, or a new connection file otherwise, which is taken away
        again if joining fails, so that a wrong password is not kept. The
        network must be in reach, and its password what its security takes:
        both are checked here, before the job, so that the panel hears at
        once."""
        if not ssid or len(ssid.encode()) > 32:
            raise InvalidArgument("a network's name is 1 to 32 bytes")
        _, known_out, _ = self._nm("-t", "-f", "NAME,UUID,TYPE", "connection", "show")
        known = [u for name, u in connections(known_out) if name == ssid]
        _, wifi_out, _ = self._nm("-t", "-f", "ACTIVE,SSID,SIGNAL,SECURITY", "device", "wifi",
                                  "list", "--rescan", "no")
        network = next((n for n in networks(wifi_out, set()) if n["ssid"] == ssid), None)
        if network is None:
            raise InvalidArgument(f"{ssid!r} is not in reach")
        if password or not known:
            check_password(network["security"], password)
        self._begin("connecting")

        def job():
            outcome, detail = "failed", ""
            try:
                if known and not password:
                    code, out, err = self._nm("--wait", str(CONNECT_SECONDS), "connection",
                                              "up", "uuid", known[0],
                                              timeout=CONNECT_SECONDS + 5)
                    outcome = "connected" if code == 0 else "failed"
                    detail = "" if code == 0 else failure_of(out + err)
                    return
                uuid = str(uuidlib.uuid4())
                path = self._connections / f"kidux-{uuid}.nmconnection"
                data = connection_file(ssid, password, network["security"], uuid)
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "w") as file:
                    file.write(data)
                self._nm("connection", "load", str(path))
                code, out, err = self._nm("--wait", str(CONNECT_SECONDS), "connection", "up",
                                          "uuid", uuid, timeout=CONNECT_SECONDS + 5)
                if code == 0:
                    outcome = "connected"
                    # The older connections to the same network go: the new
                    # one has the password that works.
                    for other in known:
                        self._nm("connection", "delete", "uuid", other)
                else:
                    detail = failure_of(out + err)
                    self._nm("connection", "delete", "uuid", uuid)
                    path.unlink(missing_ok=True)
            except OSError as error:
                detail = str(error)
            finally:
                self._audit("wifi joined" if outcome == "connected" else "wifi join",
                            "ok" if outcome == "connected" else "failed", network=ssid,
                            **({"reason": detail} if detail else {}))
                self._end(outcome, ssid, detail)

        self._start(job)

    def forget(self, ssid: str) -> None:
        """Every saved connection to `ssid` deleted: the machine no longer
        joins it by itself."""
        self._begin("forgetting")

        def job():
            outcome = "failed"
            try:
                _, known_out, _ = self._nm("-t", "-f", "NAME,UUID,TYPE", "connection", "show")
                uuids = [u for name, u in connections(known_out) if name == ssid]
                codes = [self._nm("connection", "delete", "uuid", u)[0] for u in uuids]
                outcome = "forgotten" if uuids and all(c == 0 for c in codes) else "failed"
            finally:
                self._audit("wifi forgotten", "ok" if outcome == "forgotten" else "failed",
                            network=ssid)
                self._end(outcome, ssid)

        self._start(job)
