"""Chromium's pipe: commands on its descriptor 3, answers and events on 4."""

import sys
import textwrap

from kidux import browser

#: A stand-in for Chromium: it answers every command, and sends an event first
#: when asked to navigate.
FAKE = textwrap.dedent('''
    import json, os
    buffer = b""
    while True:
        chunk = os.read(3, 65536)
        if not chunk:
            break
        buffer += chunk
        while b"\\0" in buffer:
            raw, buffer = buffer.split(b"\\0", 1)
            message = json.loads(raw)
            out = []
            if message["method"] == "Page.navigate":
                out.append({"method": "Page.loadEventFired", "params": {}})
            if message["method"] == "Target.getTargets":
                result = {"targetInfos": [{"type": "browser", "targetId": "b"},
                                          {"type": "page", "targetId": "p1"}]}
            elif message["method"] == "Target.attachToTarget":
                result = {"sessionId": "s-" + message["params"]["targetId"]}
            elif message["method"] == "Broken":
                out.append({"id": message["id"], "error": {"message": "no such thing"}})
                result = None
            else:
                result = {"echo": message}
            if result is not None:
                out.append({"id": message["id"], "result": result})
            for item in out:
                os.write(4, json.dumps(item).encode() + b"\\0")
''')


def test_commands_go_on_3_and_answers_come_on_4(tmp_path):
    fake = tmp_path / "chromium.py"
    fake.write_text(FAKE)
    process, pipe = browser.start([sys.executable, str(fake)])
    try:
        assert process.args[-1] == "--remote-debugging-pipe"
        session = pipe.page()
        assert session == "s-p1"
        echoed = pipe.call("Page.navigate", {"url": "https://example.org/"}, session)["echo"]
        assert echoed["sessionId"] == "s-p1" and echoed["params"]["url"] == "https://example.org/"
        # The event that came before the answer is kept for whoever waits for it.
        assert pipe.event("Page.loadEventFired") == {"method": "Page.loadEventFired", "params": {}}
        try:
            pipe.call("Broken")
        except RuntimeError as error:
            assert "no such thing" in str(error)
        else:
            raise AssertionError("an error was not raised")
    finally:
        process.kill()
        process.wait()


def test_a_closed_browser_is_said(tmp_path):
    gone = tmp_path / "gone.py"
    gone.write_text("import os\nos.close(4)\n")
    process, pipe = browser.start([sys.executable, str(gone)])
    process.wait()
    try:
        pipe.call("Target.getTargets")
    except browser.BrowserGone:
        pass
    else:
        raise AssertionError("a closed pipe was not said")
