"""The command a module is started with, argument by argument.

This test is the specification of how a module runs (D32, D42): a scope of
its own with the manifest's memory cap, its own settings, data and cache
directories, and nothing between it and the child's files.
"""

from pathlib import Path

import pytest

from kidux.modules import Module
from kidux_launcher import launch

HOME = "/home/leo"
DATA = "/home/leo/.local/share/kidux/hello"
CONFIG = "/home/leo/.config/kidux/hello"
CACHE = "/home/leo/.cache/kidux/hello"


def module(program="/usr/libexec/kidux-module-hello --fullscreen", **extra):
    return Module(id="hello", name="Hello", launch={"exec": program}, **extra)


SCOPE = [
    "systemd-run", "--user", "--scope", "--quiet", "--collect",
    "--unit=kidux-module-hello",
    "--property=MemoryMax=2G",
    f"--setenv=XDG_DATA_HOME={DATA}",
    f"--setenv=XDG_CONFIG_HOME={CONFIG}",
    f"--setenv=XDG_CACHE_HOME={CACHE}",
    "--",
]
PROGRAM = ["/usr/libexec/kidux-module-hello", "--fullscreen"]


def test_a_module_runs_in_its_own_scope():
    assert launch.command(module(), HOME) == SCOPE + PROGRAM


def test_the_memory_cap_is_the_manifests():
    assert "--property=MemoryMax=3G" in launch.command(module(memory_max="3G"), HOME)


def test_the_program_is_split_as_a_shell_would_and_never_run_through_one():
    argv = launch.command(module(program="/usr/bin/x --name 'a b' ;rm"), HOME)

    assert argv[len(SCOPE):] == ["/usr/bin/x", "--name", "a b", ";rm"]


def test_a_web_application_is_opened_by_kidux_webapp_in_its_scope():
    web = Module(id="scratch", name="Scratch", launch={"webapp": "scratch"},
                 memory_max="3G")

    argv = launch.command(web, HOME)

    assert argv[-2:] == ["/usr/libexec/kidux-webapp", "scratch"]
    assert "--unit=kidux-module-scratch" in argv and "--property=MemoryMax=3G" in argv


def test_a_website_is_opened_by_kidux_webapp_with_the_module_s_id():
    web = Module(id="codecombat", name="CodeCombat", launch={"web": "https://codecombat.com/"})

    assert launch.command(web, HOME)[-2:] == ["/usr/libexec/kidux-webapp", "codecombat"]


@pytest.mark.parametrize("launch_", [{"webapp": "../x"}, {"webapp": "Scratch"}, {"webapp": ""},
                                     {}, {"exec": ""}, {"web": "http://example.org/"}])
def test_a_manifest_with_nothing_to_start_starts_nothing(launch_):
    with pytest.raises(ValueError):
        launch.command(Module(id="scratch", name="Scratch", launch=launch_), HOME)


def test_the_modules_own_directories():
    assert launch.directories(HOME, "hello") == (DATA, CONFIG, CACHE)
    assert launch.unit("hello") == "kidux-module-hello"


def test_a_module_finds_the_childs_folders_by_their_names_in_its_own_settings(tmp_path):
    home = tmp_path
    (home / ".config").mkdir()
    (home / ".config" / "user-dirs.dirs").write_text('XDG_DOCUMENTS_DIR="$HOME/Documentos"\n')
    config = Path(launch.config_home(str(home), "scratchjr"))
    config.mkdir(parents=True)

    launch.share_user_dirs(str(home), "scratchjr")
    launch.share_user_dirs(str(home), "scratchjr")

    linked = config / "user-dirs.dirs"
    assert linked.is_symlink() and linked.read_text().endswith('/Documentos"\n')
    assert not (config / "user-dirs.locale").exists()


def test_a_modules_own_user_dirs_file_is_left_as_it_is(tmp_path):
    home = tmp_path
    (home / ".config").mkdir()
    (home / ".config" / "user-dirs.dirs").write_text("the child's\n")
    config = Path(launch.config_home(str(home), "odd"))
    config.mkdir(parents=True)
    (config / "user-dirs.dirs").write_text("the module's\n")

    launch.share_user_dirs(str(home), "odd")

    assert (config / "user-dirs.dirs").read_text() == "the module's\n"


def test_a_module_still_running_from_before_is_found_by_its_scope(monkeypatch):
    class Listed:
        stdout = ("kidux-module-hello.scope loaded active running [systemd-run] python3\n"
                  "other.scope loaded active running x\n")

    monkeypatch.setattr(launch.subprocess, "run", lambda *a, **k: Listed())
    assert launch.running() == ["hello"]

    def refused(*_a, **_k):
        raise OSError("no systemctl")

    monkeypatch.setattr(launch.subprocess, "run", refused)
    assert launch.running() == []


def test_a_module_is_ended_by_stopping_its_scope(monkeypatch):
    ran = []
    monkeypatch.setattr(launch.subprocess, "run", lambda argv, **_kw: ran.append(argv))

    launch.stop("robin")

    assert ran == [["systemctl", "--user", "stop", "kidux-module-robin.scope"]]
