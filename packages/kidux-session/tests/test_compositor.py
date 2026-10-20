"""lib/compositor: a compositor that stops at once is started again, drawing
in software; any other is left as it is; and what ends the wrapper ends the
compositor, which is waited for (docs/dev/session.md, section 2).

The compositor here is a stand-in that writes down each start, with the
renderer it was given, and exits as the test says.
"""

import signal
import subprocess
import time
from pathlib import Path

COMPOSITOR = Path(__file__).resolve().parents[1] / "lib" / "compositor"


def stand_in(tmp_path, statuses, on_term=None):
    """A compositor that notes each start's renderer in `starts` and exits
    with `statuses`, one a start; with `on_term`, it waits for SIGTERM and
    then notes `term` and exits with that status."""
    log = tmp_path / "starts"
    program = tmp_path / "stand-in"
    body = ("#!/bin/sh\n"
            f'echo "${{WLR_RENDERER:-none}}" >> {log}\n'
            f'n=$(wc -l < {log})\n'
            f'set -- {" ".join(str(s) for s in statuses)}\n'
            'shift $((n - 1))\n')
    if on_term is not None:
        body += (f'trap \'echo term >> {log}; exit {on_term}\' TERM\n'
                 'while :; do sleep 0.1; done\n')
    body += 'exit "${1:-0}"\n'
    program.write_text(body)
    program.chmod(0o755)
    return program, log


def run(tmp_path, statuses, renderer=None, grace=None):
    """compositor run on a stand-in; its exit status and each start's renderer."""
    program, log = stand_in(tmp_path, statuses)
    env = {"PATH": "/usr/bin:/bin"}
    if renderer:
        env["WLR_RENDERER"] = renderer
    if grace is not None:
        env["KIDUX_COMPOSITOR_GRACE"] = str(grace)
    done = subprocess.run([str(COMPOSITOR), str(program), "--", "inner"],
                          capture_output=True, text=True, env=env)
    return done.returncode, log.read_text().split()


def test_a_compositor_that_draws_is_started_once(tmp_path):
    assert run(tmp_path, [0]) == (0, ["none"])


def test_one_that_stops_at_once_is_started_again_in_software(tmp_path):
    assert run(tmp_path, [1, 0]) == (0, ["none", "pixman"])


def test_it_is_started_again_only_once(tmp_path):
    assert run(tmp_path, [1, 1]) == (1, ["none", "pixman"])


def test_a_renderer_named_is_kept(tmp_path):
    assert run(tmp_path, [1], renderer="gles2") == (1, ["gles2"])


def test_one_that_stops_after_a_while_is_not_started_again(tmp_path):
    assert run(tmp_path, [3], grace=0) == (3, ["none"])


def test_ending_the_wrapper_ends_the_compositor_and_waits_for_it(tmp_path):
    program, log = stand_in(tmp_path, [0], on_term=0)
    wrapper = subprocess.Popen([str(COMPOSITOR), str(program)], env={"PATH": "/usr/bin:/bin"},
                               stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + 5
    while "none" not in log.read_text().split() if log.exists() else True:
        assert time.monotonic() < deadline, "the compositor never started"
        time.sleep(0.05)
    wrapper.send_signal(signal.SIGTERM)
    assert wrapper.wait(5) == 0
    # The compositor got the signal, ended by itself, and was not started
    # again, although it stopped within the grace.
    assert log.read_text().split() == ["none", "term"]


def test_a_compositor_ended_by_a_signal_is_not_started_again(tmp_path):
    program, log = stand_in(tmp_path, [0], on_term=143)
    wrapper = subprocess.Popen([str(COMPOSITOR), str(program)], env={"PATH": "/usr/bin:/bin"},
                               stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + 5
    while "none" not in log.read_text().split() if log.exists() else True:
        assert time.monotonic() < deadline, "the compositor never started"
        time.sleep(0.05)
    wrapper.send_signal(signal.SIGTERM)
    assert wrapper.wait(5) == 143
    assert log.read_text().split() == ["none", "term"]
