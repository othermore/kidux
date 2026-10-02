"""The adult password and the tokens it hands out (daemon.md sections 4 and 5)."""

import pytest

from kidux import paths, state
from kiduxd.adults import AdultPassword
from kiduxd.errors import InvalidArgument, NotUnlocked
from kiduxd.tokens import Tokens


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


# --- tokens ------------------------------------------------------------------


def test_a_token_works_for_the_connection_it_was_issued_to():
    tokens = Tokens(900, Clock())
    token = tokens.issue(":1.5", 1000)

    tokens.check(token, ":1.5", 1000)


def test_a_token_is_worthless_on_another_connection():
    # The same value presented by a second connection, even of the same uid:
    # a leaked token must not open the panel anywhere else.
    tokens = Tokens(900, Clock())
    token = tokens.issue(":1.5", 1000)

    with pytest.raises(NotUnlocked):
        tokens.check(token, ":1.6", 1000)


def test_a_token_is_worthless_for_another_uid():
    tokens = Tokens(900, Clock())
    token = tokens.issue(":1.5", 1000)

    with pytest.raises(NotUnlocked):
        tokens.check(token, ":1.5", 2000)


def test_a_wrong_value_is_refused():
    tokens = Tokens(900, Clock())
    tokens.issue(":1.5", 1000)

    for wrong in ("", "not-the-token"):
        with pytest.raises(NotUnlocked):
            tokens.check(wrong, ":1.5", 1000)


def test_a_token_dies_after_being_left_alone():
    clock = Clock()
    tokens = Tokens(900, clock)
    token = tokens.issue(":1.5", 1000)

    clock.now += 901

    with pytest.raises(NotUnlocked):
        tokens.check(token, ":1.5", 1000)


def test_a_new_timeout_applies_from_the_next_check():
    clock = Clock()
    tokens = Tokens(900, clock)
    token = tokens.issue(":1.5", 1000)
    tokens.set_timeout(120)

    clock.now += 121

    with pytest.raises(NotUnlocked):
        tokens.check(token, ":1.5", 1000)


def test_using_a_token_keeps_it_alive():
    # An adult actually working in the panel is never thrown out mid-task.
    clock = Clock()
    tokens = Tokens(900, clock)
    token = tokens.issue(":1.5", 1000)

    for _ in range(5):
        clock.now += 600
        tokens.check(token, ":1.5", 1000)


def test_the_sweep_reports_who_was_locked_out():
    clock = Clock()
    tokens = Tokens(900, clock)
    tokens.issue(":1.5", 1000)
    tokens.issue(":1.6", 1001)

    clock.now += 500
    tokens.check(tokens.issue(":1.6", 1001), ":1.6", 1001)
    clock.now += 500

    assert tokens.expire() == [1000]
    assert len(tokens) == 1


def test_lock_revokes():
    tokens = Tokens(900, Clock())
    token = tokens.issue(":1.5", 1000)

    assert tokens.revoke(token, ":1.5")
    with pytest.raises(NotUnlocked):
        tokens.check(token, ":1.5", 1000)


def test_a_connection_leaving_the_bus_revokes_its_token():
    tokens = Tokens(900, Clock())
    token = tokens.issue(":1.5", 1000)

    assert tokens.revoke_name(":1.5")
    with pytest.raises(NotUnlocked):
        tokens.check(token, ":1.5", 1000)


def test_unlocking_again_replaces_the_old_token():
    tokens = Tokens(900, Clock())
    first = tokens.issue(":1.5", 1000)
    second = tokens.issue(":1.5", 1000)

    tokens.check(second, ":1.5", 1000)
    with pytest.raises(NotUnlocked):
        tokens.check(first, ":1.5", 1000)


# --- the adult password ------------------------------------------------------


def test_no_password_on_a_fresh_machine(fast_hasher):
    adults = AdultPassword(fast_hasher)

    assert not adults.is_set()
    assert not adults.verify("anything")


def test_the_password_verifies_after_it_is_set(fast_hasher):
    adults = AdultPassword(fast_hasher)
    adults.set("correct horse battery staple")

    assert adults.is_set()
    assert adults.verify("correct horse battery staple")
    assert not adults.verify("Correct horse battery staple")
    assert not adults.verify("")


def test_any_non_empty_password_is_accepted(fast_hasher):
    # D5: no minimum length, no digits-only rule. How strong it is, is the
    # family's call.
    adults = AdultPassword(fast_hasher)
    for password in ("a", "1234", "ñandú 🐧"):
        adults.set(password)
        assert adults.verify(password)


def test_an_empty_password_is_refused(fast_hasher):
    with pytest.raises(InvalidArgument):
        AdultPassword(fast_hasher).set("")


def test_the_password_is_stored_hashed(fast_hasher):
    AdultPassword(fast_hasher).set("a secret")

    raw = paths.ADULTS_FILE.read_text()
    assert "a secret" not in raw
    assert "$argon2id$" in raw


def test_an_old_hash_is_upgraded_on_the_next_good_password(fast_hasher):
    import argon2

    AdultPassword(fast_hasher).set("a secret")
    old = state.read(paths.ADULTS_FILE, "adults")["password_hash"]

    stronger = argon2.PasswordHasher(time_cost=2, memory_cost=16, parallelism=1)
    assert AdultPassword(stronger).verify("a secret")

    new = state.read(paths.ADULTS_FILE, "adults")["password_hash"]
    assert new != old
    assert AdultPassword(stronger).verify("a secret")


def test_setting_the_password_keeps_the_recovery_password(fast_hasher):
    adults = AdultPassword(fast_hasher)
    adults.set_grub("recovery", "grub.pbkdf2.sha512.10000.AA.BB")
    adults.set("a secret")

    assert adults.grub() == ("recovery", "grub.pbkdf2.sha512.10000.AA.BB")
