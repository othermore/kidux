"""kidux-chromium-policy: the base policy, with the installed modules' hosts
in its allowlist and nothing else of theirs (D85)."""

import json
import stat
from pathlib import Path

from test_server import load

generator = load("kidux-chromium-policy")

BASE = Path(__file__).parent.parent / "policies" / "kidux.json"


def module(root, module_id, hosts=None, launch='{ webapp = "x" }'):
    (root / module_id).mkdir(parents=True)
    text = f'id = "{module_id}"\nname = "X"\nlaunch = {launch}\n'
    if hosts is not None:
        text += "hosts = [" + ", ".join(f'"{h}"' for h in hosts) + "]\n"
    (root / module_id / "module.toml").write_text(text)


def generate(tmp_path, root):
    output = tmp_path / "etc" / "kidux.json"
    assert generator.main(["kidux-chromium-policy", "--root", str(root), "--base", str(BASE),
                           "--output", str(output)]) == 0
    return output


def test_the_modules_hosts_go_between_the_server_and_blob_each_once(tmp_path):
    root = tmp_path / "modules"
    module(root, "hello-web")
    module(root, "codecombat", ["codecombat.com", "cdn.codecombat.com"],
           launch='{ web = "https://codecombat.com/" }')
    module(root, "scratch", ["assets.scratch.mit.edu", "codecombat.com"])

    policy = json.loads(generate(tmp_path, root).read_text())

    assert policy["URLAllowlist"] == ["127.0.0.1:8123", "assets.scratch.mit.edu",
                                      "cdn.codecombat.com", "codecombat.com", "blob:*"]


def test_no_modules_is_the_base_s_allowlist(tmp_path):
    policy = json.loads(generate(tmp_path, tmp_path / "nothing").read_text())

    assert policy["URLAllowlist"] == ["127.0.0.1:8123", "blob:*"]


def test_every_other_key_of_the_base_is_kept(tmp_path):
    root = tmp_path / "modules"
    module(root, "site", ["example.org"])
    base = json.loads(BASE.read_text())

    policy = json.loads(generate(tmp_path, root).read_text())

    assert {k: v for k, v in policy.items() if k != "URLAllowlist"} == \
        {k: v for k, v in base.items() if k != "URLAllowlist"}
    assert policy["URLBlocklist"] == ["*"]


def test_the_policy_is_readable_by_everyone_and_written_whole(tmp_path):
    output = generate(tmp_path, tmp_path / "nothing")

    assert stat.S_IMODE(output.stat().st_mode) == 0o644
    assert [path.name for path in output.parent.iterdir()] == ["kidux.json"]
