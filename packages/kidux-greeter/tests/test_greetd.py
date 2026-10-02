"""greetd's IPC, against a fake greetd on a real Unix socket.

The fake speaks greetd's framing — a native-endian 32-bit length, then JSON —
and plays the part of PAM: one password prompt, then success or auth_error.
"""

import json
import socket
import struct
import threading

import pytest

from kidux_greeter.greetd import Greetd, GreetdError


class FakeGreetd:
    def __init__(self, path, password="right", prompts=("secret",)):
        self.path = str(path)
        self.password = password
        self.prompts = list(prompts)
        self.received: list[dict] = []
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(self.path)
        self.server.listen(1)
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        connection, _ = self.server.accept()
        with connection:
            pending = []
            while True:
                header = connection.recv(4)
                if len(header) < 4:
                    return
                (length,) = struct.unpack("=I", header)
                message = json.loads(connection.recv(length))
                self.received.append(message)
                reply = self.answer(message, pending)
                payload = json.dumps(reply).encode()
                connection.sendall(struct.pack("=I", len(payload)) + payload)

    def answer(self, message, pending):
        kind = message["type"]
        if kind == "create_session":
            pending[:] = list(self.prompts)
            return self.next_prompt(pending, None)
        if kind == "post_auth_message_response":
            return self.next_prompt(pending, message.get("response"))
        if kind in ("start_session", "cancel_session"):
            return {"type": "success"}
        return {"type": "error", "error_type": "error", "description": "unknown"}

    def next_prompt(self, pending, response):
        if response is not None and self.prompts[len(self.prompts) - len(pending) - 1] == "secret":
            if response != self.password:
                return {"type": "error", "error_type": "auth_error",
                        "description": "pam_authenticate: AUTH_ERR"}
        if pending:
            kind = pending.pop(0)
            return {"type": "auth_message", "auth_message_type": kind,
                    "auth_message": "Password:" if kind == "secret" else "Welcome"}
        return {"type": "success"}


@pytest.fixture
def greetd(tmp_path):
    return lambda **kw: FakeGreetd(tmp_path / "greetd.sock", **kw)


def test_the_right_password_authenticates(greetd):
    fake = greetd()
    client = Greetd(fake.path)

    outcome = client.authenticate("ana", "right")

    assert outcome.authenticated
    assert fake.received[0] == {"type": "create_session", "username": "ana"}
    assert fake.received[1] == {"type": "post_auth_message_response", "response": "right"}


def test_a_wrong_password_is_reported_as_such_and_the_session_cancelled(greetd):
    fake = greetd()
    client = Greetd(fake.path)

    outcome = client.authenticate("ana", "wrong")

    assert not outcome.authenticated
    assert outcome.wrong_password
    assert fake.received[-1] == {"type": "cancel_session"}


def test_only_secret_prompts_get_the_password(greetd):
    # An informational message from PAM must never be answered with the
    # password: it would be written wherever that message came from.
    fake = greetd(prompts=("info", "secret"))
    client = Greetd(fake.path)

    assert client.authenticate("ana", "right").authenticated
    responses = [m["response"] for m in fake.received if m["type"] == "post_auth_message_response"]
    assert responses == ["", "right"]


def test_starting_the_session_sends_the_command_and_environment(greetd):
    fake = greetd()
    client = Greetd(fake.path)
    client.authenticate("ana", "right")

    client.start(["/usr/libexec/kidux-session"], {"LANG": "es_ES.UTF-8", "KIDUX_DISPLAY_SCALE": "2"})

    assert fake.received[-1] == {
        "type": "start_session",
        "cmd": ["/usr/libexec/kidux-session"],
        "env": ["KIDUX_DISPLAY_SCALE=2", "LANG=es_ES.UTF-8"],
    }


def test_without_greetd_the_error_says_so():
    with pytest.raises(GreetdError):
        Greetd("").authenticate("ana", "right")


def test_an_unreachable_socket_is_an_error_not_a_crash(tmp_path):
    with pytest.raises(GreetdError):
        Greetd(str(tmp_path / "nothing-here")).authenticate("ana", "right")
