#!/usr/bin/python3
"""What every test in tests/session/ uses: the machine, and the ways to drive it.

Imported by tests/lib/session-vm.py and by every test it runs. The machine is
driven from outside: SSH for the administrator, the QEMU monitor for keys, the
power button and pictures (docs/dev/session.md, section 8). `report` prints a
PASS or FAIL line and counts the failures in `failures`.
"""

import json
import os
import re
import shutil
import socket
import subprocess
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VM = Path(os.environ.get("KIDUX_VM_DIR", REPO / "build" / "vm"))
SEED_SOURCE = REPO / "tests" / "lib" / "seed"
BASE = VM / "debian-13-genericcloud-amd64.qcow2"

#: What a run expects of the machine it sets up in each language: how many
#: Tabs past the wizard's first language, English, it presses; the locale and
#: keyboard the machine saves; two of the folders a child's home gets; the
#: tests' hello modules' words in it, and the file hello-web saves; the name
#: of Chromium's translation it loads; and the ports the run uses, its own,
#: so that the battery runs every language at once.
LANGUAGES = {
    "es": {"tabs": 1, "locale": "es_ES.UTF-8", "keyboard": "es", "lang": "es",
           "folders": ("Documentos", "Descargas"),
           "hello": "[Prueba] Hola", "done": "Hecho", "heading": "¡Hola!", "pak": "es",
           "saved": "hola.txt",
           "blockly": "Juegos de Blockly",
           "seed_port": 8002, "ssh_port": 2222},
    "en": {"tabs": 0, "locale": "en_US.UTF-8", "keyboard": "us", "lang": "en",
           "folders": ("Documents", "Downloads"),
           "hello": "[Test] Hello", "done": "Done", "heading": "Hello!", "pak": "en-US",
           "saved": "hello.txt",
           "blockly": "Blockly Games",
           "seed_port": 8003, "ssh_port": 2223},
}
#: The language the machine is set up in, and so of every screen and picture
#: (KIDUX_VM_LANGUAGE): Spanish, the tests' own, unless it says otherwise.
LANGUAGE = os.environ.get("KIDUX_VM_LANGUAGE", "es")
SPEAKS = LANGUAGES[LANGUAGE]
#: A run's files, and its pictures' names: `session` in Spanish,
#: `session-en` in English.
RUN = "session" if LANGUAGE == "es" else f"session-{LANGUAGE}"
DISK = VM / f"{RUN}.qcow2"
KEY = VM / f"{RUN}_key"
SEED = VM / f"seed-{RUN}"
MONITOR = VM / f"{RUN}-monitor.sock"
CONSOLE = VM / f"{RUN}-console.log"
SEED_PORT = int(os.environ.get("KIDUX_VM_SEED_PORT", SPEAKS["seed_port"]))
SSH_PORT = int(os.environ.get("KIDUX_VM_SSH_PORT", SPEAKS["ssh_port"]))
#: The VNC display a machine for the quick loop offers its screen on, 1 being
#: port 5901, and unset for the battery's, which nobody watches. Its password
#: is "kidux", on this machine's loopback address only, as ci/vm/try.sh's.
VNC_DISPLAY = os.environ.get("KIDUX_VM_VNC", "")
#: The screen's size, "1920x1200", for looking at a larger screen in the
#: quick loop; unset, the card's own 1280x800, which every picture is of.
SCREEN = os.environ.get("KIDUX_VM_SCREEN", "")
ARCHIVE = "http://kidux.local/apt"

#: The first picture on the sign-in screen, which has the keyboard's focus
#: when the screen comes up: children are listed by name, and kidux-as makes
#: Leo and Marta.
CHILD, CHILD_PASSWORD = "leo", "leo password"
ADULT_PASSWORD = "the adult password"
#: The child the first-run wizard creates. After Leo and Marta by name, so Leo
#: stays the first picture.
WIZARD_CHILD, WIZARD_CHILD_NAME, WIZARD_CHILD_PASSWORD = "nora", "Nora", "nora password"

#: QEMU's names for the keys that are not their own character.
KEY_NAMES = {" ": "spc", "\n": "ret", "-": "minus", ".": "dot", ",": "comma", "/": "slash"}

#: The pause after each key, a quick child's: QEMU holds a key down for a
#: tenth of a second, and a screen needs a moment to take it.
KEY_PACE = 0.15

failures = 0


def report(name: str, passed: bool, detail: str = "") -> bool:
    global failures
    print(("PASS  " if passed else "FAIL  ") + name, flush=True)
    if not passed:
        failures += 1
        if detail:
            for line in str(detail).strip().splitlines()[-15:]:
                print("      " + line, flush=True)
    return passed

def wait(condition, seconds: float, step: float = 1.0) -> bool:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            if condition():
                return True
        except Exception:
            pass
        time.sleep(step)
    return False

def _answer(connection: socket.socket, seconds: float = 10) -> str:
    """What the monitor says, up to its prompt: it answers a command when
    the command is done."""
    connection.settimeout(seconds)
    data = b""
    try:
        while not data.rstrip(b" ").endswith(b"(qemu)"):
            chunk = connection.recv(65536)
            if not chunk:
                break
            data += chunk
    except OSError:
        pass
    return data.decode(errors="replace")


def difference(first: bytes, second: bytes) -> float:
    """The share of the pixels sampled that differ between two screen dumps,
    1.0 when they cannot be compared."""
    if not first or len(first) != len(second):
        return 1.0
    if first == second:
        return 0.0
    step = 3 * 7
    sampled = len(first) // step
    differing = sum(1 for i in range(0, len(first) - 2, step) if first[i:i + 3] != second[i:i + 3])
    return differing / max(1, sampled)


def _alike(first: bytes, second: bytes) -> bool:
    """Whether two screen dumps differ in at most one pixel in a thousand:
    a blinking text cursor, not a new screen."""
    return difference(first, second) <= 0.001


def _ppm_share(data: bytes, colour: tuple, box, tolerance: int) -> float:
    """colour_share() for a screen dump as QEMU writes it, a binary PPM."""
    header = re.match(rb"P6\s+(\d+)\s+(\d+)\s+\d+\s", data)
    if header is None:
        return 0.0
    width, height = int(header.group(1)), int(header.group(2))
    pixels = data[header.end():]
    if len(pixels) < width * height * 3:
        return 0.0
    left, top, right, bottom = box
    hits = total = 0
    for y in range(int(top * height), int(bottom * height), 4):
        row = y * width * 3
        for x in range(int(left * width), int(right * width), 4):
            pixel = pixels[row + x * 3:row + x * 3 + 3]
            total += 1
            if all(abs(pixel[i] - colour[i]) <= tolerance for i in range(3)):
                hits += 1
    return hits / max(1, total)


class Machine:
    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.pictures = 0

    def boot(self) -> None:
        MONITOR.unlink(missing_ok=True)
        ovmf_vars = VM / f"OVMF_VARS_{RUN}.fd"
        if not ovmf_vars.exists():
            shutil.copy("/usr/share/OVMF/OVMF_VARS_4M.fd", ovmf_vars)
        accel = ["-enable-kvm", "-cpu", "host"] if os.access("/dev/kvm", os.W_OK) else ["-cpu", "max"]
        self.process = subprocess.Popen(
            [
                "qemu-system-x86_64", *accel,
                "-m", "2048", "-smp", "2", "-machine", "q35",
                "-drive", "if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd",
                "-drive", f"if=pflash,format=raw,unit=1,file={ovmf_vars}",
                "-drive", f"file={DISK},format=qcow2,if=virtio",
                "-netdev", f"user,id=net0,hostfwd=tcp:127.0.0.1:{SSH_PORT}-:22",
                "-device", "virtio-net-pci,netdev=net0",
                "-smbios", f"type=1,serial=ds=nocloud;s=http://10.0.2.2:{SEED_PORT}/",
                # Not virtio: with no display attached, QEMU's virtio card
                # never completes a frame, and a Wayland client waits for
                # one before drawing its next. The screen would stay on its
                # first frame until a key was pressed.
                *(["-vga", "none", "-device",
                   "VGA,edid=on,xres={},yres={}".format(*SCREEN.split("x"))]
                  if SCREEN else ["-vga", "std"]),
                "-monitor", f"unix:{MONITOR},server,nowait",
                "-serial", f"file:{CONSOLE}",
                "-display", "none",
                *(["-vnc", f"127.0.0.1:{VNC_DISPLAY},password=on", "-k", "es"]
                  if VNC_DISPLAY else []),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait(MONITOR.exists, 10, 0.2)
        if VNC_DISPLAY:
            # QEMU starts VNC with a password but none set; eight characters
            # at most.
            self.monitor("set_password vnc kidux")

    def monitor(self, command: str) -> str:
        """One command to QEMU's monitor, and what it answered."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.connect(str(MONITOR))
            _answer(connection)
            connection.sendall(command.encode() + b"\n")
            return _answer(connection)

    def key(self, keys: str) -> None:
        self.monitor(f"sendkey {keys}")
        time.sleep(KEY_PACE)

    def click(self) -> None:
        """One click of the mouse's left button where the pointer rests: over
        the window that fills the screen, whichever it is."""
        self.monitor("mouse_button 1")
        time.sleep(0.2)
        self.monitor("mouse_button 0")
        time.sleep(KEY_PACE)

    def type(self, text: str) -> None:
        """Type on the machine's keyboard, one key at a time, as a child would."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.connect(str(MONITOR))
            _answer(connection)
            for character in text:
                name = KEY_NAMES.get(character, character.lower())
                if character.isupper():
                    name = f"shift-{name}"
                connection.sendall(f"sendkey {name}\n".encode())
                _answer(connection)
                time.sleep(KEY_PACE)

    def frame(self) -> bytes:
        """The screen as it is now, as raw pixels, to compare with another."""
        path = VM / f"{RUN}-frame.ppm"
        path.unlink(missing_ok=True)
        self.monitor(f"screendump {path}")
        wait(lambda: path.exists() and path.stat().st_size > 0, 5, 0.05)
        try:
            return path.read_bytes()
        except OSError:
            return b""

    def showing(self, colour: tuple, box=(0.0, 0.0, 1.0, 1.0), share: float = 0.3,
                seconds: float = 120, tolerance: int = 16) -> bool:
        """Wait until `colour` covers `share` of `box` on the screen. A page
        that draws itself after loading, as a web editor does, is still a
        blank page for a while: still() returns at once on it, and its title
        is there before anything is drawn."""
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if _ppm_share(self.frame(), colour, box, tolerance) >= share:
                return True
            time.sleep(1)
        return False

    def still(self, seconds: float = 4) -> bool:
        """Wait until the screen stops changing: two frames a quarter of a
        second apart that differ in no more than a text cursor's worth of
        pixels. False if it was still changing after `seconds`."""
        end = time.monotonic() + seconds
        last = self.frame()
        while time.monotonic() < end:
            time.sleep(0.25)
            now = self.frame()
            if _alike(last, now):
                return True
            last = now
        return False

    def mark(self) -> Counter:
        """How many times each trusted screen has been drawn, before a key:
        the journal holds the whole boot, so only a screen drawn after the
        mark counts."""
        return screens_counted()

    def submit(self, text: str) -> Counter:
        """Type `text`, then Enter, and return the mark taken before."""
        mark = self.mark()
        self.type(text + "\n")
        return mark

    def shown(self, name: str, mark: Counter, seconds: float = 15) -> bool:
        """Wait until a trusted screen has drawn `name` after `mark`, and
        the screen is still."""
        drawn = wait(lambda: screens_counted((name,))[name] > mark[name], seconds, 0.5)
        if drawn:
            self.still()
        return drawn

    def settled(self) -> bytes:
        """The screen once it is still, for changes() to compare with: a
        frame taken while a focus ring still moves would count as a change."""
        self.still()
        return self.frame()

    def changes(self, before: bytes, seconds: float = 10, share: float = 0.001) -> bool:
        """Wait until the screen differs from the frame `before`, taken with
        settled() before the key that changes it, in more than `share` of its
        pixels, and then until it is still: for a change no program logs, a
        dialog opening or a window coming up. A share of a few hundredths
        waits past a button that only looks pressed for what it opens.
        False if it never changed."""
        changed = wait(lambda: difference(before, self.frame()) > share, seconds, 0.1)
        self.still()
        return changed

    def screenshot(self, name: str) -> Path:
        """A picture of the screen once it is drawn, numbered in the order
        it was taken."""
        self.still()
        self.pictures += 1
        path = VM / f"{RUN}-{self.pictures:02d}-{name}.png"
        path.unlink(missing_ok=True)
        self.monitor(f"screendump {path} -f png")
        wait(lambda: path.exists() and path.stat().st_size > 0, 5, 0.2)
        return path

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(20)
            except subprocess.TimeoutExpired:
                self.process.kill()

def ssh(command: str, timeout: float = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "ssh", "-i", str(KEY), "-p", str(SSH_PORT),
            "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
            "debian@127.0.0.1", command,
        ],
        capture_output=True, text=True, timeout=timeout,
    )

def root(command: str, timeout: float = 300) -> subprocess.CompletedProcess:
    return ssh(f"sudo sh -c {shlex_quote(command)}", timeout)

def shlex_quote(text: str) -> str:
    return "'" + text.replace("'", "'\"'\"'") + "'"

def up() -> bool:
    try:
        return ssh("true", timeout=10).returncode == 0
    except subprocess.TimeoutExpired:
        return False

def copy(source: Path, destination: str, mode: str = "0755") -> None:
    subprocess.run(
        [
            "scp", "-i", str(KEY), "-P", str(SSH_PORT),
            "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR", str(source), f"debian@127.0.0.1:/tmp/{source.name}",
        ],
        check=True, capture_output=True,
    )
    root(f"install -D -m {mode} /tmp/{source.name} {destination}")

def keyboard(*steps: str, background: bool = False) -> None:
    """Keys pressed as a person presses them, on a keyboard of the machine's
    own (keyboard.py, which says what a step is): Alt held down while Tab is
    pressed twice, which QEMU's `sendkey` cannot do. In the background it
    returns at once, and the keys start keyboard.SETTLE seconds later."""
    program = "/usr/local/lib/kidux-tests/keyboard.py"
    if root(f"test -x {program}").returncode != 0:
        copy(REPO / "tests" / "lib" / "keyboard.py", program)
    command = f"{program} {' '.join(steps)}"
    root(f"systemd-run --quiet --collect {command}" if background else command)

def boot_id() -> str:
    return ssh("cat /proc/sys/kernel/random/boot_id").stdout.strip()

def active_terminal() -> str:
    return ssh("cat /sys/class/tty/tty0/active").stdout.strip()

def reboot(machine: Machine) -> bool:
    before = boot_id()
    root("systemctl reboot", timeout=20)
    return wait(lambda: up() and boot_id() not in ("", before), 240, 3)

def write_seed() -> None:
    SEED.mkdir(parents=True, exist_ok=True)
    public_key = (KEY.with_suffix(".pub")).read_text().strip()
    (SEED / "meta-data").write_text(f"instance-id: kidux-session-{int(time.time())}\n"
                                    "local-hostname: kidux-session\n")
    (SEED / "vendor-data").write_text("")
    shutil.copy(SEED_SOURCE / "network-config", SEED / "network-config")
    (SEED / "user-data").write_text(f"""#cloud-config
hostname: kidux-session
ssh_authorized_keys:
  - {public_key}
write_files:
  - path: /etc/hosts
    append: true
    content: |
      10.0.2.2 kidux.local
  - path: /etc/apt/apt.conf.d/99kidux-vm-lean
    content: |
      Acquire::Languages "none";
runcmd:
  - [ sh, -c, "sed -i 's/^Types: deb deb-src/Types: deb/' /etc/apt/sources.list.d/debian.sources || true" ]
""")

def child_session():
    for line in ssh("loginctl list-sessions --no-legend").stdout.splitlines():
        fields = line.split()
        if len(fields) >= 6 and fields[2] == CHILD and fields[5] == "user":
            return fields[0]
    return None

def greeter_log() -> str:
    return root("journalctl -b --no-pager -o cat -t kidux-greeter -t greetd -t cage "
                "| grep -v pam_unix | tail -40").stdout

def screens_shown(name: str) -> int:
    """How many times this boot a trusted screen has drawn `name`: it logs
    `drawn <name>` once the screen is painted (greeter.md section 7)."""
    return screens_counted((name,))[name]


def screens_counted(names=None) -> Counter:
    """screens_shown for several screens, or for every one, asked once."""
    lines = root("journalctl -b -o cat -t kidux-greeter | grep -F ': drawn '").stdout
    drawn = Counter(line.rsplit(": drawn ", 1)[-1] for line in lines.splitlines())
    return drawn if names is None else Counter({name: drawn[name] for name in names})


def journal_count(tag: str, text: str, whole: bool = False) -> int:
    """How many lines this boot, from the program logging as `tag`, hold
    `text`; or, when `whole`, whose message after the logger's name and
    level is `text` and nothing more."""
    lines = root(f"journalctl -b -o cat -t {tag} | grep -F -- {shlex_quote(text)}").stdout
    if whole:
        return sum(1 for line in lines.splitlines() if line.endswith(": " + text))
    return len(lines.splitlines())


def logged(tag: str, text: str, before: int, seconds: float = 15) -> bool:
    """Wait until `tag` has logged `text` once more than `before` times."""
    return wait(lambda: journal_count(tag, text) > before, seconds, 0.5)


def children_count() -> int:
    members = root("getent group kidux-children").stdout.strip().split(":")[-1]
    return len([m for m in members.split(",") if m])

def open_panel(machine: "Machine") -> bool:
    """From everyone's pictures to the panel. Back from the first picture
    until the focus is on Adult, which is further back the more children
    there are; any other screen reached on the way is left again."""
    names = ("adult", "password", "power")
    for tabs in range(1, 10):
        for _ in range(tabs):
            machine.key("shift-tab")
        mark = machine.mark()
        machine.key("ret")
        reached: Counter = Counter()

        def moved() -> bool:
            reached.clear()
            reached.update(screens_counted(names))
            return any(reached[name] > mark[name] for name in names)

        if not wait(moved, 5, 0.5):
            continue
        machine.still()
        if reached["adult"] > mark["adult"]:
            return machine.shown("panel_children", machine.submit(ADULT_PASSWORD))
        back = machine.mark()
        if reached["password"] > mark["password"]:
            machine.key("esc")                   # a child's picture: Back
        elif reached["power"] > mark["power"]:
            machine.key("ret")                   # Turn off asks first; Cancel has the focus
        machine.shown("choose", back)
    return False


def to_the_modules_page(machine: "Machine") -> bool:
    """From the first child's name on the panel: back past the five controls
    that give time, every child, Add, Network and System, to Modules."""
    for _ in range(5 + children_count() + 4):
        machine.key("shift-tab")
    before = machine.mark()
    machine.key("ret")
    return machine.shown("panel_modules", before, 10)


def as_child(command: str) -> subprocess.CompletedProcess:
    """A command run as Leo, with his runtime directory, over SSH as root."""
    uid = root(f"id -u {CHILD}").stdout.strip()
    return root(f"runuser -u {CHILD} -- env XDG_RUNTIME_DIR=/run/user/{uid} {command}")


#: What `on_screen` says when the launcher's window is the active one.
HOME = "home"


def windows() -> list[dict]:
    """Every window in Leo's session, as the launcher sees them: app_id,
    title, module ("home" for the launcher's), and the states activated,
    maximized, minimized and fullscreen (the kidux-toplevels tool, over the
    compositor's foreign-toplevel protocol). None while the session is
    frozen under the lock screen."""
    answer = as_child("timeout 10 /usr/local/bin/kidux-toplevels").stdout
    return [json.loads(line) for line in answer.splitlines() if line.startswith("{")]


def on_screen() -> str:
    """The module whose window is active on Leo's screen, HOME for the
    launcher's; "" when no window is."""
    active = next((w for w in windows() if w.get("activated")), None)
    return (active.get("module") or "") if active else ""


def window_of(app_id: str) -> dict:
    return next((w for w in windows() if w.get("app_id") == app_id), {})


def launcher_shown(machine: "Machine", seconds: float = 30) -> bool:
    """Wait until Leo's launcher has its window on the screen, and the
    screen is still: a key pressed before then is lost."""
    shown = wait(lambda: window_of("org.kidux.Launcher") != {}, seconds)
    machine.still()
    return shown


def lock_screen_adult(machine: "Machine") -> None:
    """From the lock screen, with Continue focused, to what an adult can do
    there: Adult, then the adult password."""
    machine.key("tab")                       # from Continue to Adult
    mark = machine.mark()
    machine.key("ret")
    machine.shown("adult_password", mark)
    machine.shown("adult_choice", machine.submit(ADULT_PASSWORD))


def launcher_log() -> str:
    return root("journalctl -b -o cat -t kidux-launcher | tail -8").stdout


def launcher_pid() -> str:
    # The launcher itself, not session-inner, whose command line names it too.
    return root(f"pgrep -u {CHILD} -f '^/usr/bin/python3 /usr/libexec/kidux-launcher'").stdout.strip()

def _png():
    """tests/lib/screenshot-diff.py's PNG reader, which needs nothing installed."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("screenshot_diff", REPO / "tests" / "lib" / "screenshot-diff.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: The colours pictures are checked for (branding/README.md).
CREAM = (0xFF, 0xF6, 0xE9)
NIGHT = (0x24, 0x31, 0x3F)


def colour_share(picture: Path, colour: tuple, box=(0.0, 0.0, 1.0, 1.0), tolerance: int = 10) -> float:
    """The share of a picture's pixels close to `colour`, inside `box`.

    `box` is (left, top, right, bottom) as fractions of the picture, so a check
    reads "the bottom middle of the screen" whatever its resolution. Every
    fourth pixel each way is enough to tell a logo from no logo."""
    try:
        width, height, rows = _png().read_png(picture)
    except (OSError, ValueError):
        return 0.0
    left, top, right, bottom = box
    hits = total = 0
    for y in range(int(top * height), int(bottom * height), 4):
        row = rows[y]
        for x in range(int(left * width), int(right * width), 4):
            pixel = row[x * 3:x * 3 + 3]
            total += 1
            if all(abs(pixel[i] - colour[i]) <= tolerance for i in range(3)):
                hits += 1
    return hits / max(1, total)


def colour_middle(picture: Path, colour: tuple, box=(0.0, 0.0, 1.0, 1.0),
                  tolerance: int = 10) -> float | None:
    """Where a colour is across a picture, inside `box`: the mean x of its
    pixels, as a fraction of the picture's width; None where it is not.
    Which of a row of buttons is lit, whatever their widths in a language."""
    try:
        width, height, rows = _png().read_png(picture)
    except (OSError, ValueError):
        return None
    left, top, right, bottom = box
    xs = []
    for y in range(int(top * height), int(bottom * height), 4):
        row = rows[y]
        for x in range(int(left * width), int(right * width), 2):
            pixel = row[x * 3:x * 3 + 3]
            if all(abs(pixel[i] - colour[i]) <= tolerance for i in range(3)):
                xs.append(x)
    return sum(xs) / len(xs) / width if xs else None


def catch_the_splash(machine: Machine) -> Path | None:
    """A picture of the boot splash, if the next boot shows it.

    The splash is up for a few seconds at an unknown moment, so the screen is
    photographed four times a second for thirty seconds; the splash is the
    first frame that is cream with the logo's night blue in the middle of it. The sign-in screen that
    follows is cream too, but its middle is the children's pictures."""
    frames = VM / f"{RUN}-splash-frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    # Photographed first, four times a second through one connection, and
    # looked at afterwards: looking takes longer than the splash lasts.
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(str(MONITOR))
        connection.settimeout(0.05)
        for number in range(120):
            connection.sendall(f"screendump {frames / f'{number:03d}.png'} -f png\n".encode())
            time.sleep(0.25)
            try:
                connection.recv(65536)
            except OSError:
                pass
    time.sleep(1)
    found = None
    for frame in sorted(frames.glob("*.png")):
        if (colour_share(frame, CREAM) > 0.5
                and colour_share(frame, NIGHT, (0.3, 0.3, 0.7, 0.7)) > 0.02):
            found = frame
            break
    if found is None:
        # Kept, to see what the boot showed instead.
        missed = VM / f"{RUN}-splash-frames-missed"
        shutil.rmtree(missed, ignore_errors=True)
        frames.rename(missed)
        return None
    machine.pictures += 1
    kept = VM / f"{RUN}-{machine.pictures:02d}-boot-splash.png"
    shutil.copy(found, kept)
    shutil.rmtree(frames, ignore_errors=True)
    return kept