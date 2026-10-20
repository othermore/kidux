"""lib/compositor: a compositor that stops at once is started again, drawing
in software; any other is left as it is (docs/dev/session.md, section 2).

The compositor here is a stand-in that writes down each start, with the
renderer it was given, and exits as the test says.
"""

import subprocess
from pathlib import Path

COMPOSITOR = Path(__file__).resolve().parents[1] / "lib" / "compositor"


def run(tmp_path, statuses, renderer=None, grace=None):
    """compositor run on a stand-in that exits with `statuses`, one a start;
    its exit status and the renderer of each start."""
    log = tmp_path / "starts"
    stand_in = tmp_path / "stand-in"
    stand_in.write_text(
        "#!/bin/sh\n"
        f'echo "${{WLR_RENDERER:-none}}" >> {log}\n'
        f'n=$(wc -l < {log})\n'
        f'set -- {" ".join(str(s) for s in statuses)}\n'
        'shift $((n - 1)); exit "${1:-0}"\n')
    stand_in.chmod(0o755)
    env = {"PATH": "/usr/bin:/bin"}
    if renderer:
        env["WLR_RENDERER"] = renderer
    if grace is not None:
        env["KIDUX_COMPOSITOR_GRACE"] = str(grace)
    done = subprocess.run([str(COMPOSITOR), str(stand_in), "--", "inner"],
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
