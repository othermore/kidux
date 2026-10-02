"""The daemon's behaviour through `Service.dispatch`, without a bus.

Most of these tests try to get past a check. Each check in gate.py exists
because of something a child, a bug or a careless call could otherwise do,
and a check nobody has tried to break has not been shown to hold.
"""

import json

import pytest

from kidux import paths, state
from kiduxd import gate as gate_module
from kiduxd.accounts import FakeAccounts
from kiduxd.adults import AdultPassword
from kiduxd.errors import (
    AccessDenied,
    Failed,
    InvalidArgument,
    NoSuchChild,
    NotAuthorized,
    NotUnlocked,
    SessionActive,
    WrongPassword,
)
from kiduxd.gate import Caller, Gate
from kiduxd.logind import FakeLogind, SessionInfo
from kiduxd.children import Children
from kiduxd.service import Service
from kiduxd.tokens import Tokens

from conftest import LANGUAGES

ADMIN = Caller(":1.10", 1000)
GREETER = Caller(":1.11", 110)
ANA = Caller(":1.20", 3001)
LUIS = Caller(":1.21", 3002)
ROOT = Caller(":1.30", 0)

ADULT_PASSWORD = "a family secret"


class FakeAuthority:
    """polkit as the shipped rules describe it (50-kidux.rules)."""

    def __init__(self, accounts: FakeAccounts) -> None:
        self.accounts = accounts
        self.refuse_everything = False

    def check(self, unique_name: str, action_id: str) -> bool:
        if self.refuse_everything:
            return False
        uids = {c.unique_name: c.uid for c in (ADMIN, GREETER, ANA, LUIS, ROOT)}
        uid = uids.get(unique_name, ADMIN.uid)
        name = self.accounts.username_of(uid)
        if self.accounts.in_group(name, paths.ADMIN_GROUP):
            return True
        if name == paths.GREETER_USER:
            return True
        if self.accounts.in_group(name, paths.CHILDREN_GROUP):
            return action_id == gate_module.SELF
        return False


@pytest.fixture
def machine(fast_hasher):
    accounts = FakeAccounts()
    accounts.add_user("admin", 1000, (paths.ADMIN_GROUP, "sudo"))
    accounts.add_user(paths.GREETER_USER, 110)
    accounts.add_user("ana", 3001, (paths.CHILDREN_GROUP, "video"))
    accounts.add_user("luis", 3002, (paths.CHILDREN_GROUP, "video"))
    for child in ("ana", "luis"):
        state.write(paths.child_profile(child), {"display_name": child.title(),
                                                 "language": "es_ES.UTF-8",
                                                 "keyboard": "es", "avatar": "fox"}, "profile")

    logind = FakeLogind()
    authority = FakeAuthority(accounts)
    audit_log = []
    emitted = []

    service = Service(
        gate=Gate(authority, accounts),
        accounts=accounts,
        logind=logind,
        adults=AdultPassword(fast_hasher),
        tokens=Tokens(900),
        children=Children(accounts, logind, LANGUAGES),
        emit=lambda *signal: emitted.append(signal),
        audit=lambda action, outcome, **fields: audit_log.append((action, outcome, fields)),
    )
    service.adults.set(ADULT_PASSWORD)

    class Machine:
        pass

    m = Machine()
    m.service, m.accounts, m.logind, m.authority = service, accounts, logind, authority
    m.audit, m.emitted = audit_log, emitted
    m.call = lambda caller, interface, method, *args: service.dispatch(
        caller, interface, method, *args
    )
    m.unlock = lambda caller=ADMIN: service.dispatch(caller, "Parental1", "Unlock", ADULT_PASSWORD)
    return m


# --- polkit ------------------------------------------------------------------


def test_anyone_may_ping_and_turn_the_computer_off(machine):
    machine.authority.refuse_everything = True

    assert machine.call(ANA, "Daemon1", "Ping")
    machine.call(ANA, "System1", "Shutdown")

    assert machine.logind.powered_off


def test_a_child_may_not_list_the_children(machine):
    # Only the sign-in screen and administrators see who else uses the machine.
    with pytest.raises(AccessDenied):
        machine.call(ANA, "Children1", "List")


def test_a_child_may_not_unlock_the_panel_even_with_the_password(machine):
    # The adult password is only ever typed on a trusted screen (D6). A child's
    # session asking to unlock is exactly the fake prompt that rule is about.
    with pytest.raises(AccessDenied):
        machine.call(ANA, "Parental1", "Unlock", ADULT_PASSWORD)


def test_root_needs_no_polkit(machine):
    machine.authority.refuse_everything = True

    assert machine.call(ROOT, "Children1", "List")


def test_an_unknown_method_is_refused(machine):
    with pytest.raises(NotAuthorized):
        machine.call(ADMIN, "Children1", "DropTables")


def test_every_exported_method_has_a_polkit_decision():
    # A method added to the XML and forgotten here would be refused, which is
    # safe, but it would also be a bug nobody noticed until a screen broke.
    from gi.repository import Gio
    from kiduxd.bus import introspection_xml, short_interface

    node = Gio.DBusNodeInfo.new_for_xml(introspection_xml())
    exported = {
        (short_interface(interface.name), method.name)
        for interface in node.interfaces
        for method in interface.methods
    }
    assert exported == set(gate_module.ACTIONS)


# --- what polkit cannot see: scope -------------------------------------------


def test_a_child_may_ask_about_themselves(machine):
    assert machine.call(ANA, "Modules1", "List", "ana") == []


def test_a_child_may_not_ask_about_a_sibling(machine):
    with pytest.raises(NotAuthorized):
        machine.call(ANA, "Modules1", "List", "luis")


def test_the_greeter_may_ask_about_any_child(machine):
    assert machine.call(GREETER, "Modules1", "List", "luis") == []


# --- modules (phase-3-plan.md, step 3.1) ---------------------------------------


def install_module(module_id: str) -> None:
    directory = paths.MODULES_DIR / module_id
    directory.mkdir(parents=True)
    (directory / "module.toml").write_text(
        f'id = "{module_id}"\nname = "{module_id.title()}"\n'
        f'launch = {{ exec = "/usr/libexec/kidux-module-{module_id}" }}\n')


def enabled_in_file(username: str) -> list:
    return state.read(paths.child_modules(username), "modules")["enabled"]


def test_every_installed_module_is_listed_off_until_an_adult_enables_it(machine):
    install_module("hello")
    install_module("abc")

    assert machine.call(ANA, "Modules1", "List", "ana") == [
        {"id": "abc", "enabled": False}, {"id": "hello", "enabled": False}]


def test_an_adult_enables_a_module_for_one_child(machine):
    install_module("hello")
    token = machine.unlock()

    machine.call(ADMIN, "Modules1", "SetEnabled", token, "ana", "hello", True)

    assert machine.call(ANA, "Modules1", "List", "ana") == [{"id": "hello", "enabled": True}]
    assert machine.call(LUIS, "Modules1", "List", "luis") == [{"id": "hello", "enabled": False}]
    assert ("module enabled", "ok", {"caller": "admin", "child": "ana", "module": "hello"}) \
        in machine.audit
    assert ("Modules1", "ModulesChanged", "(s)", ("ana",)) in machine.emitted
    assert enabled_in_file("ana") == ["hello"]


def test_and_disables_it_again(machine):
    install_module("hello")
    token = machine.unlock()
    machine.call(ADMIN, "Modules1", "SetEnabled", token, "ana", "hello", True)

    machine.call(ADMIN, "Modules1", "SetEnabled", token, "ana", "hello", False)

    assert machine.call(ANA, "Modules1", "List", "ana") == [{"id": "hello", "enabled": False}]
    assert ("module disabled", "ok", {"caller": "admin", "child": "ana", "module": "hello"}) \
        in machine.audit


def test_setting_what_is_already_set_is_not_an_error_and_changes_nothing(machine):
    install_module("hello")
    token = machine.unlock()

    machine.call(ADMIN, "Modules1", "SetEnabled", token, "ana", "hello", False)

    assert not paths.child_modules("ana").exists()
    assert not [a for a in machine.audit if a[0].startswith("module")]
    assert not [e for e in machine.emitted if e[1] == "ModulesChanged"]


def test_a_module_that_is_not_installed_cannot_be_enabled(machine):
    install_module("hello")
    token = machine.unlock()

    for module_id in ("nothing", "../hello", ""):
        with pytest.raises(InvalidArgument):
            machine.call(ADMIN, "Modules1", "SetEnabled", token, "ana", module_id, True)
    assert not paths.child_modules("ana").exists()


def test_a_module_whose_package_is_gone_is_not_listed_and_stays_in_the_file(machine):
    install_module("hello")
    state.write(paths.child_modules("ana"), {"enabled": ["gone", "hello"]}, "modules")
    token = machine.unlock()

    assert machine.call(ANA, "Modules1", "List", "ana") == [{"id": "hello", "enabled": True}]
    machine.call(ADMIN, "Modules1", "SetEnabled", token, "ana", "hello", False)
    # Putting the package back restores the switch.
    assert enabled_in_file("ana") == ["gone"]


def test_switching_modules_takes_the_token_and_a_child(machine):
    install_module("hello")
    token = machine.unlock()

    with pytest.raises(NotUnlocked):
        machine.call(ADMIN, "Modules1", "SetEnabled", "not a token", "ana", "hello", True)
    with pytest.raises(NoSuchChild):
        machine.call(ADMIN, "Modules1", "SetEnabled", token, "admin", "hello", True)


def test_a_child_may_not_switch_modules_for_themselves_or_a_sibling(machine):
    install_module("hello")

    for username in ("ana", "luis"):
        with pytest.raises(AccessDenied):
            machine.call(ANA, "Modules1", "SetEnabled", "", username, "hello", True)


# --- tokens and the adult password -------------------------------------------


def test_unlock_with_the_wrong_password_is_refused_and_audited(machine):
    with pytest.raises(WrongPassword):
        machine.call(ADMIN, "Parental1", "Unlock", "a guess")

    assert ("unlock", "denied", {"caller": "admin"}) in machine.audit


def test_a_wrong_password_is_never_written_down(machine):
    with pytest.raises(WrongPassword):
        machine.call(ADMIN, "Parental1", "Unlock", "hunter2")

    assert "hunter2" not in json.dumps(machine.audit)


def test_changes_need_a_token(machine):
    with pytest.raises(NotUnlocked):
        machine.call(ADMIN, "Children1", "SetChildPassword", "", "ana", "new")


def test_a_token_from_another_connection_is_refused(machine):
    token = machine.unlock(ADMIN)
    other_connection = Caller(":1.99", ADMIN.uid)

    with pytest.raises(NotUnlocked):
        machine.call(other_connection, "Children1", "SetChildPassword", token, "ana", "new")


def test_the_panel_closing_kills_its_token(machine):
    token = machine.unlock(ADMIN)
    machine.service.connection_closed(ADMIN.unique_name)

    with pytest.raises(NotUnlocked):
        machine.call(ADMIN, "Children1", "SetChildPassword", token, "ana", "new")


def test_the_first_password_needs_no_token(fast_hasher, machine):
    # A machine that has never been set up has no password to unlock with.
    paths.ADULTS_FILE.unlink()

    machine.call(GREETER, "Parental1", "SetPassword", "", "the first one")

    assert machine.service.adults.verify("the first one")


def test_changing_the_password_needs_a_token(machine):
    with pytest.raises(NotUnlocked):
        machine.call(ADMIN, "Parental1", "SetPassword", "", "taken over")

    assert machine.service.adults.verify(ADULT_PASSWORD)


# --- which accounts may be managed --------------------------------------------


@pytest.mark.parametrize("target", ["admin", paths.GREETER_USER, "root", "nobody-here"])
def test_only_children_are_ever_managed(machine, target):
    # Whatever the token says: this is what stops an unlocked panel, or a bug
    # in one, from deleting the account that owns the machine.
    token = machine.unlock()

    for method, args in (
        ("Delete", (target, False)),
        ("SetChildPassword", (target, "x")),
        ("SetProfile", (target, {"display_name": "x"})),
    ):
        with pytest.raises(NoSuchChild):
            machine.call(ADMIN, "Children1", method, token, *args)

    assert machine.accounts.exists("admin")


# --- creating and deleting children ------------------------------------------


def create(machine, token, username="marta", **overrides):
    arguments = {
        "display_name": "Marta",
        "language": "es_ES.UTF-8",
        "keyboard": "es",
        "avatar": "owl",
        "password": "marta's password",
    }
    arguments.update(overrides)
    machine.call(
        ADMIN, "Children1", "Create", token, username,
        arguments["display_name"], arguments["language"], arguments["keyboard"],
        arguments["avatar"], arguments["password"],
    )


def test_create_makes_an_account_and_its_files(machine):
    token = machine.unlock()
    create(machine, token)

    assert machine.accounts.in_group("marta", paths.CHILDREN_GROUP)
    assert machine.accounts.in_group("marta", "video")
    assert machine.accounts.users["marta"]["password"] == "marta's password"
    assert state.read(paths.child_profile("marta"), "profile")["avatar"] == "owl"
    # Nothing is allowed until an adult says how much.
    assert state.read(paths.child_access("marta"), "access")["mode"] == "manual"
    assert ("Children1", "ChildrenChanged", "()", ()) in machine.emitted


def test_create_shows_up_in_the_list(machine):
    token = machine.unlock()
    create(machine, token, "marta", display_name="Marta")

    names = [entry["display_name"] for entry in machine.call(GREETER, "Children1", "List")]
    assert names == ["Ana", "Luis", "Marta"]


@pytest.mark.parametrize(
    "username",
    ["Marta", "1marta", "marta smith", "../etc", "", "root", paths.GREETER_USER,
     paths.CHILDREN_GROUP, "admin", "a" * 33],
)
def test_bad_or_taken_usernames_are_refused(machine, username):
    token = machine.unlock()

    with pytest.raises(InvalidArgument):
        create(machine, token, username)


@pytest.mark.parametrize(
    "field,value",
    [
        ("language", "klingon"),
        ("avatar", "not-a-picture"),
        ("avatar", "../../etc/passwd"),
        ("keyboard", "es; rm -rf /"),
        ("display_name", ""),
        ("display_name", "x" * 65),
        ("password", ""),
        ("password", "two\nlines"),
    ],
)
def test_bad_fields_are_refused_before_anything_is_created(machine, field, value):
    token = machine.unlock()

    with pytest.raises(InvalidArgument):
        create(machine, token, **{field: value})

    assert not machine.accounts.exists("marta")
    assert not paths.child_dir("marta").exists()


@pytest.mark.parametrize("failing_step", ["chpasswd", "group:video"])
def test_a_failure_halfway_leaves_no_half_child(machine, failing_step):
    token = machine.unlock()
    machine.accounts.fail_on.add(failing_step)

    with pytest.raises(Exception):
        create(machine, token)

    assert not machine.accounts.exists("marta")
    assert not paths.child_dir("marta").exists()
    assert any(entry[:2] == ("child created", "failed") for entry in machine.audit)


def test_delete_removes_the_account_and_its_files(machine):
    token = machine.unlock()
    create(machine, token)

    machine.call(ADMIN, "Children1", "Delete", token, "marta", False)

    assert not machine.accounts.exists("marta")
    assert not paths.child_dir("marta").exists()


def test_delete_is_refused_while_the_child_is_signed_in(machine):
    token = machine.unlock()
    machine.logind.open.append(SessionInfo("3", 3001, "ana", "seat0", "/s/3"))

    with pytest.raises(SessionActive):
        machine.call(ADMIN, "Children1", "Delete", token, "ana", False)

    assert machine.accounts.exists("ana")


def test_delete_ends_the_user_manager_that_outlives_the_last_session(machine):
    # For the seconds after a child logs out, logind still holds their user
    # manager as a session of class "manager"; that is nobody being signed
    # in, and deluser refuses a user with a process, so it is ended first.
    token = machine.unlock()
    machine.logind.open.append(SessionInfo("4", 3001, "ana", "", "/s/4", session_class="manager"))

    machine.call(ADMIN, "Children1", "Delete", token, "ana", False)

    assert machine.logind.terminated == [3001]
    assert not machine.accounts.exists("ana")


def test_set_profile_changes_only_what_it_is_given(machine):
    token = machine.unlock()
    machine.call(ADMIN, "Children1", "SetProfile", token, "ana",
                 {"avatar": "owl", "age": 7})

    profile = state.read(paths.child_profile("ana"), "profile")
    assert profile["avatar"] == "owl"
    assert profile["age"] == 7
    assert profile["language"] == "es_ES.UTF-8"


def test_windows_are_a_setting_of_the_child_off_until_an_adult_turns_them_on(machine):
    token = machine.unlock(ADMIN)
    listed = {c["username"]: c for c in machine.call(ADMIN, "Children1", "List")}
    assert listed["ana"]["windows"] is False

    machine.call(ADMIN, "Children1", "SetProfile", token, "ana", {"windows": True})

    listed = {c["username"]: c for c in machine.call(ADMIN, "Children1", "List")}
    assert listed["ana"]["windows"] is True
    with pytest.raises(InvalidArgument):
        machine.call(ADMIN, "Children1", "SetProfile", token, "ana", {"windows": "yes"})


def test_set_profile_refuses_fields_it_does_not_know(machine):
    token = machine.unlock()

    with pytest.raises(InvalidArgument):
        machine.call(ADMIN, "Children1", "SetProfile", token, "ana", {"sudo": True})


def test_a_new_display_name_reaches_the_account_too(machine):
    token = machine.unlock()
    machine.call(ADMIN, "Children1", "SetProfile", token, "ana", {"display_name": "Anita"})

    assert machine.accounts.users["ana"]["display_name"] == "Anita"


def test_set_child_password(machine):
    token = machine.unlock()
    machine.call(ADMIN, "Children1", "SetChildPassword", token, "ana", "new one")

    assert machine.accounts.users["ana"]["password"] == "new one"
    assert "new one" not in json.dumps(machine.audit)


# --- config ------------------------------------------------------------------


def test_the_screens_get_the_config_they_cannot_read_themselves(machine):
    config = machine.call(GREETER, "Daemon1", "GetConfig")

    assert config["default_language"]
    assert config["reset_hour"] == 4
    assert config["setup_complete"] is False


def test_the_config_says_whether_a_language_was_chosen(machine):
    assert machine.call(GREETER, "Daemon1", "GetConfig")["language_chosen"] is False


def test_the_panel_changes_the_machines_settings(machine):
    token = machine.unlock(GREETER)

    machine.call(GREETER, "Daemon1", "SetConfig", token, {
        "default_language": "es_ES.UTF-8", "default_keyboard": "es",
        "display_scale": 2.0, "setup_complete": True,
    })

    config = machine.call(GREETER, "Daemon1", "GetConfig")
    assert config["default_language"] == "es_ES.UTF-8"
    assert config["default_keyboard"] == "es"
    assert config["display_scale"] == 2.0
    assert config["setup_complete"] is True
    assert config["language_chosen"] is True
    assert ("config set", "ok", {"caller": paths.GREETER_USER, "fields": [
        "default_keyboard", "default_language", "display_scale", "setup_complete"]}) in machine.audit


def test_settings_need_a_token_once_there_is_a_password(machine):
    with pytest.raises(NotUnlocked):
        machine.call(GREETER, "Daemon1", "SetConfig", "", {"default_language": "es_ES.UTF-8"})


def test_the_scale_is_automatic_until_an_adult_chooses_one(machine):
    assert machine.call(GREETER, "Daemon1", "GetConfig")["display_scale"] == 0.0
    token = machine.unlock(GREETER)

    machine.call(GREETER, "Daemon1", "SetConfig", token, {"display_scale": 1.75})
    assert machine.call(GREETER, "Daemon1", "GetConfig")["display_scale"] == 1.75
    machine.call(GREETER, "Daemon1", "SetConfig", token, {"display_scale": 0.0})
    assert machine.call(GREETER, "Daemon1", "GetConfig")["display_scale"] == 0.0


def test_before_the_first_password_only_language_and_keyboard_are_open(machine):
    # The wizard sets them first, so that the password is typed in the
    # right keyboard; nothing else may be changed without a token.
    paths.ADULTS_FILE.unlink()

    machine.call(GREETER, "Daemon1", "SetConfig", "", {"default_language": "es_ES.UTF-8",
                                                        "default_keyboard": "es"})
    assert machine.call(GREETER, "Daemon1", "GetConfig")["language_chosen"] is True

    for change in ({"setup_complete": True}, {"display_scale": 2.0},
                   {"default_keyboard": "es", "setup_complete": True}):
        with pytest.raises(NotUnlocked):
            machine.call(GREETER, "Daemon1", "SetConfig", "", change)


@pytest.mark.parametrize("change", [
    {"default_language": "xx_YY.UTF-8"},
    {"default_keyboard": "not a layout"},
    {"display_scale": 0.5},
    {"display_scale": 4},
    {"display_scale": True},
    {"setup_complete": "yes"},
    {"reset_hour": 3},
    {"minutes_nobody_offers": 10},
    {"idle_lock_minutes": 0},
    {"idle_lock_minutes": 121},
    {"idle_lock_minutes": True},
    {"idle_lock_minutes": 5.5},
    {"screen_off_minutes": 0},
    {"screen_off_minutes": 241},
    {"save_minutes": 0},
    {"save_minutes": 16},
    {"screen_off_minutes": "10"},
])
def test_bad_settings_are_refused(machine, change):
    token = machine.unlock(GREETER)

    with pytest.raises(InvalidArgument):
        machine.call(GREETER, "Daemon1", "SetConfig", token, change)


def test_a_session_left_alone_locks_after_minutes_an_adult_sets(machine):
    config = machine.call(GREETER, "Daemon1", "GetConfig")
    assert (config["idle_lock_minutes"], config["screen_off_minutes"]) == (5, 10)
    token = machine.unlock(GREETER)

    machine.call(GREETER, "Daemon1", "SetConfig", token,
                 {"idle_lock_minutes": 3, "screen_off_minutes": 20})

    config = machine.call(GREETER, "Daemon1", "GetConfig")
    assert (config["idle_lock_minutes"], config["screen_off_minutes"]) == (3, 20)


def test_unlock_to_save_lasts_the_minutes_the_machine_says(machine):
    assert machine.call(GREETER, "Daemon1", "GetConfig")["save_minutes"] == 5
    token = machine.unlock(GREETER)

    machine.call(GREETER, "Daemon1", "SetConfig", token, {"save_minutes": 1})

    assert machine.call(GREETER, "Daemon1", "GetConfig")["save_minutes"] == 1


def test_the_panel_closes_after_the_same_minutes(machine):
    token = machine.unlock(GREETER)
    machine.call(GREETER, "Daemon1", "SetConfig", token, {"idle_lock_minutes": 2})

    assert machine.service.tokens._timeout == 120


def test_the_recovery_password_is_shown_only_with_a_token(machine):
    machine.service.adults.set_grub("abc123", "grub.pbkdf2.sha512.x")

    with pytest.raises(NotUnlocked):
        machine.call(GREETER, "Parental1", "GetRecoveryPassword", "")
    token = machine.unlock(GREETER)
    assert machine.call(GREETER, "Parental1", "GetRecoveryPassword", token) == "abc123"
    assert ("recovery password shown", "ok", {"caller": paths.GREETER_USER}) in machine.audit
    assert "abc123" not in json.dumps(machine.audit)


def test_the_panel_sets_chromium_s_flags_and_the_file_follows(machine):
    token = machine.unlock(GREETER)

    machine.call(GREETER, "Daemon1", "SetConfig", token,
                 {"chromium_flags": ["--disable-gpu-compositing"]})

    assert machine.call(GREETER, "Daemon1", "GetConfig")["chromium_flags"] == [
        "--disable-gpu-compositing"]
    assert paths.CHROMIUM_FLAGS.read_text() == "--disable-gpu-compositing\n"
    machine.call(GREETER, "Daemon1", "SetConfig", token, {"chromium_flags": []})
    assert not paths.CHROMIUM_FLAGS.exists()


def test_a_bad_chromium_flag_changes_nothing(machine):
    token = machine.unlock(GREETER)
    machine.call(GREETER, "Daemon1", "SetConfig", token, {"chromium_flags": ["--disable-gpu"]})

    with pytest.raises(InvalidArgument):
        machine.call(GREETER, "Daemon1", "SetConfig", token, {"chromium_flags": ["--no-sandbox"]})

    assert paths.CHROMIUM_FLAGS.read_text() == "--disable-gpu\n"


def test_setting_chromium_s_flags_needs_the_adult(machine):
    machine.unlock(GREETER)
    with pytest.raises(NotUnlocked):
        machine.call(GREETER, "Daemon1", "SetConfig", "", {"chromium_flags": ["--disable-gpu"]})


def test_the_panel_grants_time_without_the_password_again(machine):
    token = machine.unlock(GREETER)

    machine.call(GREETER, "Access1", "Grant", token, "ana", 30)

    assert machine.call(GREETER, "Access1", "CheckAccess", "ana") == ("allowed", 1800)
    assert ("grant", "ok", {"caller": paths.GREETER_USER, "child": "ana", "minutes": 30,
                            "source": "panel"}) in machine.audit


def test_the_panel_sets_what_a_child_has_left(machine):
    token = machine.unlock(GREETER)
    machine.call(GREETER, "Access1", "SetPolicy", token, "ana",
                 {"mode": "daily", "daily_minutes": 60})

    machine.call(GREETER, "Access1", "SetTimeLeft", token, "ana", 5)

    assert machine.call(GREETER, "Access1", "CheckAccess", "ana") == ("allowed", 300)
    machine.call(GREETER, "Access1", "SetTimeLeft", token, "ana", 0)
    assert machine.call(GREETER, "Access1", "CheckAccess", "ana") == ("blocked", 0)
    assert ("time set", "ok", {"caller": paths.GREETER_USER, "child": "ana",
                               "minutes": 0}) in machine.audit


def test_setting_the_time_left_is_checked(machine):
    with pytest.raises(NotUnlocked):
        machine.call(GREETER, "Access1", "SetTimeLeft", "", "ana", 5)
    token = machine.unlock(GREETER)
    with pytest.raises(NoSuchChild):
        machine.call(GREETER, "Access1", "SetTimeLeft", token, "admin", 5)
    with pytest.raises(InvalidArgument):
        machine.call(GREETER, "Access1", "SetTimeLeft", token, "ana", 24 * 60 + 1)
    machine.call(GREETER, "Access1", "SetPolicy", token, "ana", {"mode": "unlimited"})
    with pytest.raises(InvalidArgument):
        machine.call(GREETER, "Access1", "SetTimeLeft", token, "ana", 5)


@pytest.mark.parametrize("minutes", [0, 24 * 60 + 1, True])
def test_a_grant_from_the_panel_is_checked(machine, minutes):
    token = machine.unlock(GREETER)

    with pytest.raises(InvalidArgument):
        machine.call(GREETER, "Access1", "Grant", token, "ana", minutes)


def test_a_grant_from_the_panel_needs_a_token_and_a_child(machine):
    with pytest.raises(NotUnlocked):
        machine.call(GREETER, "Access1", "Grant", "", "ana", 30)
    token = machine.unlock(GREETER)
    with pytest.raises(NoSuchChild):
        machine.call(GREETER, "Access1", "Grant", token, "admin", 30)


# --- the network (D62) ---------------------------------------------------------


class FakeNetwork:
    def __init__(self):
        self.calls = []

    def read(self):
        self.calls.append(("read",))
        return {"manager": True}, [], []

    def check(self):
        self.calls.append(("check",))

    def connect(self, ssid, password):
        self.calls.append(("connect", ssid, password))

    def forget(self, ssid):
        self.calls.append(("forget", ssid))


def test_the_network_is_the_panel_s_with_a_token_and_never_a_child_s(machine):
    machine.service.network = FakeNetwork()
    with pytest.raises(NotUnlocked):
        machine.call(GREETER, "Network1", "GetNetwork", "not a token")
    with pytest.raises(AccessDenied):
        machine.call(ANA, "Network1", "GetNetwork", "")
    with pytest.raises(AccessDenied):
        machine.call(ANA, "Network1", "ConnectWifi", "", "Home", "kidux password 1")
    token = machine.unlock(GREETER)
    assert machine.call(GREETER, "Network1", "GetNetwork", token) == ({"manager": True}, [], [])
    machine.call(GREETER, "Network1", "Check", token)
    machine.call(GREETER, "Network1", "ConnectWifi", token, "Home", "kidux password 1")
    machine.call(GREETER, "Network1", "ForgetWifi", token, "Home")
    assert machine.service.network.calls[1:] == [
        ("check",), ("connect", "Home", "kidux password 1"), ("forget", "Home")]
    # The network's name is audited; the password never is.
    assert ("wifi join", "started", {"caller": "_greetd", "network": "Home"}) in machine.audit
    assert "kidux password 1" not in repr(machine.audit)


def test_a_daemon_without_the_network_says_so(machine):
    token = machine.unlock(GREETER)
    with pytest.raises(Failed):
        machine.call(GREETER, "Network1", "GetNetwork", token)


# --- the versions ------------------------------------------------------------------


def test_the_versions_are_dpkg_s_for_the_screens_and_not_for_a_child(machine):
    machine.service.kidux_packages = lambda: (
        "kidux-base 0.2.3 installed\nkidux-daemon 0.3.25 installed\n"
        "kidux-webapps 0.1.3 config-files\npython3-kidux 0.1.35 installed\n")
    assert machine.call(GREETER, "System1", "Versions") == {
        "kidux-base": "0.2.3", "kidux-daemon": "0.3.25", "python3-kidux": "0.1.35"}
    with pytest.raises(AccessDenied):
        machine.call(ANA, "System1", "Versions")


def test_without_dpkg_the_versions_are_none(machine):
    assert machine.call(GREETER, "System1", "Versions") == {}

    def broken():
        raise OSError("no dpkg-query")

    machine.service.kidux_packages = broken
    assert machine.call(GREETER, "System1", "Versions") == {}
