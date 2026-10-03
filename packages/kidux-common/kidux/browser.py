"""Chromium driven through a pipe only its starter holds (phase-4c-plan.md,
4.17 and 4.18).

`kidux-webapp` starts a module's Chromium with `--remote-debugging-pipe`:
Chromium reads commands of its DevTools protocol on its file descriptor 3
and writes answers and events on 4, each a JSON message ended by a NUL
byte. Nothing else can reach that pipe: there is no port, and the daemon
refuses the flag among the machine's own. Through it `kidux-webapp` gives
the window the cookies a module's sign-in returned, takes it to the site,
runs a module's script in a page, and has a module's page script run in
every page the window shows.
"""

import json
import os
import subprocess

#: How Chromium is told to take its commands on the pipe.
PIPE_FLAG = "--remote-debugging-pipe"


class BrowserGone(Exception):
    """Chromium closed its end: the window was closed."""


class Pipe:
    """The two ends `kidux-webapp` keeps: commands out, answers and events in."""

    def __init__(self, commands: int, answers: int) -> None:
        self._commands = commands
        self._answers = answers
        self._buffer = b""
        self._next = 0
        #: Events that arrived while an answer was awaited, oldest first.
        self.events: list[dict] = []

    def _read(self) -> dict:
        while b"\0" not in self._buffer:
            chunk = os.read(self._answers, 65536)
            if not chunk:
                raise BrowserGone("Chromium closed the pipe")
            self._buffer += chunk
        message, self._buffer = self._buffer.split(b"\0", 1)
        return json.loads(message)

    def send(self, method: str, params: dict | None = None, session: str = "") -> int:
        self._next += 1
        message = {"id": self._next, "method": method, "params": params or {}}
        if session:
            message["sessionId"] = session
        data = json.dumps(message).encode() + b"\0"
        try:
            while data:
                data = data[os.write(self._commands, data):]
        except BrokenPipeError:
            raise BrowserGone("Chromium closed the pipe") from None
        return self._next

    def call(self, method: str, params: dict | None = None, session: str = "") -> dict:
        """Send a command and wait for its answer; RuntimeError for an error."""
        number = self.send(method, params, session)
        while True:
            message = self._read()
            if message.get("id") == number:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error'].get('message')}")
                return message.get("result", {})
            if "method" in message:
                self.events.append(message)

    def event(self, method: str) -> dict:
        """Wait for the next event called `method`, keeping the others."""
        for index, message in enumerate(self.events):
            if message.get("method") == method:
                return self.events.pop(index)
        while True:
            message = self._read()
            if message.get("method") == method:
                return message
            if "method" in message:
                self.events.append(message)

    def drain(self) -> None:
        """Read and drop whatever Chromium says until it closes the pipe, so
        that nothing piles up on its side while the window is open."""
        self.events.clear()
        try:
            while True:
                self._read()
        except BrowserGone:
            return

    def page(self) -> str:
        """Attach to the window's page; the session its commands go to."""
        targets = self.call("Target.getTargets")["targetInfos"]
        page = next(target for target in targets if target.get("type") == "page")
        return self.call("Target.attachToTarget",
                         {"targetId": page["targetId"], "flatten": True})["sessionId"]


def start(argv: list[str]) -> tuple[subprocess.Popen, Pipe]:
    """Start Chromium, `argv`, with the pipe on its descriptors 3 and 4."""
    command_read, command_write = os.pipe()
    answer_read, answer_write = os.pipe()
    # Out of the way of 3 and 4 first, so that putting one in place never
    # closes the other.
    high = [os.dup(fd) for fd in (command_read, answer_write)]

    def descriptors() -> None:
        os.dup2(high[0], 3)
        os.dup2(high[1], 4)

    process = subprocess.Popen([*argv, PIPE_FLAG], preexec_fn=descriptors, pass_fds=(3, 4))
    for fd in (command_read, answer_write, *high):
        os.close(fd)
    return process, Pipe(command_write, answer_read)
