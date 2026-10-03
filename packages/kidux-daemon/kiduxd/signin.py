"""Signing a child in to a module's website, for the daemon (phase-4c-plan.md,
4.17): one HTTPS request the module's manifest describes, the account's
JSON sent to an address on the module's own hosts, and the session's
cookies the answer sets, of the names the manifest gives, handed back.
Nothing else of the answer is kept or logged.

The daemon's unit may not open an internet socket (RestrictAddressFamilies),
so the request is made by this file run as a program, `python3 -m
kiduxd.signin`, in a transient unit of its own: a dynamic user, no homes, a
read-only system, the internet. The daemon hands it what to send on its
standard input, the password with it, never on a command line, and reads
the cookies, or why there are none, on its standard output.
"""

import json
import subprocess
import sys
import urllib.error
import urllib.request
from http.cookies import CookieError, SimpleCookie
from urllib.parse import urlsplit

from .errors import SignInRefused, SignInUnreachable

#: How long a website has to answer.
TIMEOUT_SECONDS = 20

#: Who asks, as a website reads it: Python's own name is refused by some.
AGENT = "Kidux (https://kidux.org)"


def request(url: str, body: dict, wanted, opener=None) -> list[dict]:
    """POST `body` as JSON to `url`; the cookies named in `wanted` that the
    answer sets, as Chromium's Storage.setCookies takes them. SignInRefused
    when the site answers 4xx, SignInUnreachable when it does not answer,
    answers otherwise, or sets none of the cookies."""
    opener = opener or urllib.request.urlopen
    data = json.dumps(body).encode()
    asked = urllib.request.Request(url, data=data, method="POST",
                                   headers={"Content-Type": "application/json",
                                            "Accept": "application/json",
                                            "User-Agent": AGENT})
    try:
        with opener(asked, timeout=TIMEOUT_SECONDS) as answer:
            headers = answer.headers.get_all("Set-Cookie") or []
    except urllib.error.HTTPError as error:
        if 400 <= error.code < 500:
            raise SignInRefused(f"{urlsplit(url).hostname} said {error.code}") from None
        raise SignInUnreachable(f"{urlsplit(url).hostname} said {error.code}") from None
    except (urllib.error.URLError, OSError, TimeoutError) as error:
        raise SignInUnreachable(f"{urlsplit(url).hostname} did not answer: {error}") from None
    host = urlsplit(url).hostname
    cookies = []
    for header in headers:
        try:
            parsed = SimpleCookie()
            parsed.load(header)
        except CookieError:
            continue
        for name, morsel in parsed.items():
            if name not in wanted:
                continue
            cookies.append({
                "name": name, "value": morsel.value,
                "domain": morsel["domain"] or host, "path": morsel["path"] or "/",
                "secure": bool(morsel["secure"]), "httpOnly": bool(morsel["httponly"]),
                "sameSite": {"none": "None", "lax": "Lax", "strict": "Strict"}.get(
                    (morsel["samesite"] or "").lower(), "Lax"),
            })
    if not cookies:
        raise SignInUnreachable(f"{host} set none of the session's cookies")
    return cookies


#: The transient unit the request runs in, and how long it may take.
UNIT = ["systemd-run", "--wait", "--collect", "--quiet", "--pipe",
        "--property=DynamicUser=yes", "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes", "--property=PrivateTmp=yes",
        "--property=NoNewPrivileges=yes",
        "--property=RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX AF_NETLINK",
        "--", "/usr/bin/python3", "-m", "kiduxd.signin"]
UNIT_SECONDS = TIMEOUT_SECONDS + 15


def request_in_unit(url: str, body: dict, wanted, run=subprocess.run) -> list[dict]:
    """`request`, made in a transient unit with the internet: what the
    daemon calls. The same errors."""
    asked = json.dumps({"url": url, "body": body, "cookies": list(wanted)})
    try:
        done = run(UNIT, input=asked, capture_output=True, text=True, timeout=UNIT_SECONDS)
        said = json.loads(done.stdout or "{}")
    except (subprocess.TimeoutExpired, OSError, ValueError):
        raise SignInUnreachable("the sign-in did not finish") from None
    if said.get("error") == "refused":
        raise SignInRefused(said.get("detail", ""))
    if "cookies" not in said:
        raise SignInUnreachable(said.get("detail", "") or done.stderr[-200:])
    return said["cookies"]


def main() -> int:
    """The program the transient unit runs: what to send on standard
    input, the cookies or why there are none on standard output."""
    asked = json.loads(sys.stdin.read())
    try:
        said = {"cookies": request(asked["url"], asked["body"], tuple(asked["cookies"]))}
    except SignInRefused as error:
        said = {"error": "refused", "detail": str(error)}
    except SignInUnreachable as error:
        said = {"error": "unreachable", "detail": str(error)}
    print(json.dumps(said))
    return 0


if __name__ == "__main__":
    sys.exit(main())

