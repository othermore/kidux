"""greetd's IPC: how the sign-in screen signs a child in.

greetd listens on the socket named in GREETD_SOCK. Each message is a JSON
object preceded by its length as a 32-bit integer in native byte order, and
each request gets exactly one reply (greetd-ipc(7)). A sign-in is:

    create_session(username)
    -> auth_message (a password prompt)        post_auth_message_response(password)
    -> success                                 start_session(cmd, env)
    -> success                                 ...and the greeter exits

The greeter never sees whether the password was right until greetd says so:
PAM, through greetd, is the authority (D10). A wrong password comes back as
an `error` of type `auth_error`, after PAM's own delay.
"""

import json
import os
import socket
import struct
from dataclasses import dataclass


class GreetdError(Exception):
    """greetd could not be reached, or answered something unexpected."""


@dataclass(frozen=True)
class Outcome:
    """How an attempt to authenticate ended."""

    authenticated: bool
    wrong_password: bool = False
    message: str = ""


class Greetd:
    def __init__(self, path: str | None = None) -> None:
        self._path = path or os.environ.get("GREETD_SOCK", "")
        self._sock: socket.socket | None = None

    def _connect(self) -> socket.socket:
        if self._sock is None:
            if not self._path:
                raise GreetdError("GREETD_SOCK is not set: not started by greetd")
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect(self._path)
            except OSError as error:
                sock.close()
                raise GreetdError(f"cannot reach greetd: {error}") from error
            self._sock = sock
        return self._sock

    def _receive_exactly(self, sock: socket.socket, length: int) -> bytes:
        data = b""
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                raise GreetdError("greetd closed the connection")
            data += chunk
        return data

    def request(self, message: dict) -> dict:
        sock = self._connect()
        payload = json.dumps(message).encode("utf-8")
        try:
            sock.sendall(struct.pack("=I", len(payload)) + payload)
            (length,) = struct.unpack("=I", self._receive_exactly(sock, 4))
            return json.loads(self._receive_exactly(sock, length))
        except OSError as error:
            self.close()
            raise GreetdError(f"greetd stopped answering: {error}") from error

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    # --- a sign-in -------------------------------------------------------------

    def authenticate(self, username: str, password: str) -> Outcome:
        """Answer greetd's prompts for `username` with `password`.

        Any prompt asking for a secret gets the password; a visible prompt
        gets nothing, and informational messages are acknowledged. On any
        failure the half-made session is cancelled, so the next attempt starts
        clean.
        """
        reply = self.request({"type": "create_session", "username": username})
        while reply.get("type") == "auth_message":
            kind = reply.get("auth_message_type")
            answer = password if kind == "secret" else ""
            reply = self.request({"type": "post_auth_message_response", "response": answer})

        if reply.get("type") == "success":
            return Outcome(authenticated=True)

        self.cancel()
        if reply.get("type") == "error" and reply.get("error_type") == "auth_error":
            return Outcome(authenticated=False, wrong_password=True,
                           message=reply.get("description", ""))
        return Outcome(authenticated=False, message=reply.get("description", str(reply)))

    def start(self, command: list[str], environment: dict[str, str]) -> None:
        """Start the authenticated session. greetd runs it once the greeter exits."""
        reply = self.request({
            "type": "start_session",
            "cmd": command,
            "env": [f"{key}={value}" for key, value in sorted(environment.items())],
        })
        if reply.get("type") != "success":
            self.cancel()
            raise GreetdError(f"greetd would not start the session: {reply}")

    def cancel(self) -> None:
        """Abandon a session that was being made. Harmless if there is none."""
        try:
            self.request({"type": "cancel_session"})
        except GreetdError:
            pass
