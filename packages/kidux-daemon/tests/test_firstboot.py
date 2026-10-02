"""First boot (daemon.md section 12)."""

import subprocess

from kidux import paths, state
from kiduxd import firstboot
from kiduxd.adults import AdultPassword
from kiduxd.config import Config

from conftest import LANGUAGES


class Recorder:
    """Stands in for subprocess.run and remembers every command."""

    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def __call__(self, argv, **kwargs):
        self.commands.append(list(argv))
        stdout = ""
        if argv[0] == "grub-mkpasswd-pbkdf2":
            stdout = "Enter password:\nPBKDF2 hash of your password is grub.pbkdf2.sha512.10000.AB.CD\n"
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")


def run(tmp_path, recorder, monkeypatch, locale="LANG=es_ES.UTF-8\n", keyboard='XKBLAYOUT="es,us"\n',
        administrators=("maria",)):
    (tmp_path / "locale").write_text(locale)
    (tmp_path / "keyboard").write_text(keyboard)
    monkeypatch.setattr(firstboot.shutil, "which", lambda name: f"/usr/sbin/{name}")
    return firstboot.run(
        locale_file=tmp_path / "locale",
        keyboard_file=tmp_path / "keyboard",
        run_command=recorder,
        chown=False,
        languages=LANGUAGES,
        administrators=lambda: list(administrators),
    )


def test_first_boot_creates_the_state_directory_closed_to_everyone_else(tmp_path, monkeypatch):
    assert run(tmp_path, Recorder(), monkeypatch)

    for directory in (paths.STATE_ROOT, paths.CHILDREN_DIR, paths.STATE_DIR):
        assert directory.is_dir()
        assert directory.stat().st_mode & 0o777 == 0o750


def test_the_machine_language_and_keyboard_become_the_defaults(tmp_path, monkeypatch):
    run(tmp_path, Recorder(), monkeypatch)

    config = Config.load()
    assert config.default_language == "es_ES.UTF-8"
    assert config.default_keyboard == "es"
    assert config.setup_complete is False


def test_an_unshipped_language_falls_back_to_english(tmp_path, monkeypatch):
    run(tmp_path, Recorder(), monkeypatch, locale="LANG=de_DE.UTF-8\n", keyboard="")

    config = Config.load()
    assert config.default_language == "en_US.UTF-8"
    assert config.default_keyboard == "us"


def test_the_recovery_password_is_made_and_grub_is_told(tmp_path, monkeypatch):
    recorder = Recorder()
    run(tmp_path, recorder, monkeypatch)

    password, hashed = AdultPassword().grub()
    assert len(password) == firstboot.RECOVERY_LENGTH
    assert hashed == "grub.pbkdf2.sha512.10000.AB.CD"
    assert ["update-grub"] in recorder.commands
    # The password went to GRUB's tool on standard input, never as an argument.
    assert all(password not in " ".join(argv) for argv in recorder.commands)


def test_administrators_become_adults_of_the_state_directory(tmp_path, monkeypatch):
    recorder = Recorder()
    run(tmp_path, recorder, monkeypatch, administrators=("maria", "pedro"))

    assert ["gpasswd", "--add", "maria", paths.ADMIN_GROUP] in recorder.commands
    assert ["gpasswd", "--add", "pedro", paths.ADMIN_GROUP] in recorder.commands


def test_first_boot_runs_once(tmp_path, monkeypatch):
    assert run(tmp_path, Recorder(), monkeypatch)
    recorder = Recorder()

    assert not run(tmp_path, recorder, monkeypatch)
    assert recorder.commands == []


def test_an_interrupted_first_boot_runs_again(tmp_path, monkeypatch):
    # config.toml is written last; without it, first boot has not happened.
    run(tmp_path, Recorder(), monkeypatch)
    paths.CONFIG_FILE.unlink()

    assert run(tmp_path, Recorder(), monkeypatch)


def test_an_existing_recovery_password_is_kept(tmp_path, monkeypatch):
    AdultPassword().set_grub("already-here", "grub.pbkdf2.sha512.10000.EE.FF")

    run(tmp_path, Recorder(), monkeypatch)

    assert AdultPassword().grub() == ("already-here", "grub.pbkdf2.sha512.10000.EE.FF")


def test_first_boot_is_audited(tmp_path, monkeypatch):
    run(tmp_path, Recorder(), monkeypatch)

    assert '"first boot"' in paths.AUDIT_LOG.read_text()
    assert state.read(paths.CONFIG_FILE, "config")["schema_version"] == 1
