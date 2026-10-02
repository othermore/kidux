"""Policy and time, against a clock the tests control (daemon.md section 7).

Every scenario the phase 1 plan lists for step 9.4 is here by name. These are
the rules a child will try hardest to get round, so each one is written as
the situation a family would actually be in.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from kiduxd.access import (
    EVERY_DAY,
    UNLIMITED,
    WARNINGS,
    Policy,
    Usage,
    Warnings,
    accounting_day,
    available,
    check_access,
    grant,
    roll_day,
    set_left,
    spend,
    days_text,
    validate_policy,
    weekday_of,
)

TZ = timezone(timedelta(hours=2))
RESET = 4


def at(day: int, hour: int, minute: int = 0) -> datetime:
    """A moment in September 2026, local time."""
    return datetime(2026, 9, day, hour, minute, tzinfo=TZ)


def day_of(moment: datetime) -> date:
    return accounting_day(moment, RESET)


def tick(policy, usage, now: datetime, seconds: int):
    """What the session tracker does each tick: new day first, then charge."""
    policy, usage, change = roll_day(policy, usage, day_of(now))
    policy, usage = spend(policy, usage, seconds)
    return policy, usage, change


DAILY = Policy(mode="daily", daily_minutes=60)
MANUAL = Policy(mode="manual")

#: The day of the week, Monday 0, of 22 September 2026, the day most of
#: these tests are on, and of the next day.
TUE, WED = 1, 2
#: Every day but Tuesday.
NOT_TUESDAY = (True, False, True, True, True, True, True)


# --- the accounting day ------------------------------------------------------


def test_the_day_changes_at_four_in_the_morning_not_at_midnight():
    # An evening session is not cut in half by the calendar.
    assert day_of(at(22, 23, 59)) == date(2026, 9, 22)
    assert day_of(at(23, 0, 30)) == date(2026, 9, 22)
    assert day_of(at(23, 3, 59)) == date(2026, 9, 22)
    assert day_of(at(23, 4, 0)) == date(2026, 9, 23)


# --- the three modes ---------------------------------------------------------


def test_unlimited_is_always_allowed_and_never_runs_out():
    policy = Policy(mode="unlimited")
    usage = Usage(seconds_used_today=10 * 3600)

    assert check_access(policy, usage, TUE) == ("allowed", UNLIMITED)
    assert available(policy, usage, TUE) == UNLIMITED


def test_a_fresh_day():
    _, usage, _ = roll_day(DAILY, Usage(), day_of(at(22, 16)))

    assert check_access(DAILY, usage, TUE) == ("allowed", 3600)


def test_partly_spent():
    usage = Usage(last_day="2026-09-22", seconds_used_today=1500)

    assert check_access(DAILY, usage, TUE) == ("allowed", 2100)


def test_exactly_spent_is_blocked_in_daily_mode():
    usage = Usage(last_day="2026-09-22", seconds_used_today=3600)

    assert check_access(DAILY, usage, TUE) == ("blocked", 0)


def test_overspent_is_blocked_not_negative():
    usage = Usage(last_day="2026-09-22", seconds_used_today=4000)

    assert available(DAILY, usage, TUE) == 0


def test_manual_with_an_empty_bank_needs_an_adult():
    assert check_access(MANUAL, Usage(), TUE) == ("needs_adult", 0)


# --- grants: the bank (D14) --------------------------------------------------


def test_a_grant_always_gives_its_minutes():
    # The day's allowance is below what was used, because an adult cut it
    # after use or because today is no longer a ticked day: the grant covers
    # the difference first, so the child has its minutes and no less.
    cut = Usage(last_day="2026-09-22", seconds_used_today=100 * 60)
    assert available(grant(DAILY, cut, TUE, 15), cut, TUE) == 15 * 60

    morning = Usage(last_day="2026-09-22", seconds_used_today=3 * 3600)
    for mode in ("daily", "unlimited"):
        policy = Policy(mode=mode, days=NOT_TUESDAY)
        assert check_access(grant(policy, morning, TUE, 15), morning, TUE) == ("allowed", 900)
    # And no more than its minutes: what is left is kept.
    some_left = Usage(last_day="2026-09-22", seconds_used_today=50 * 60)
    assert available(grant(DAILY, some_left, TUE, 15), some_left, TUE) == 25 * 60


def test_a_grant_is_added_to_the_bank():
    policy = grant(MANUAL, Usage(), TUE, 30)

    assert check_access(policy, Usage(), TUE) == ("allowed", 1800)


def test_a_daily_grant_adds_to_today():
    usage = Usage(last_day="2026-09-22", seconds_used_today=3600)
    policy = grant(DAILY, Usage(), TUE, 15)

    assert check_access(policy, usage, TUE) == ("allowed", 900)


def test_a_manual_grant_is_spent_across_two_sessions():
    policy, usage = grant(MANUAL, Usage(), TUE, 30), Usage(last_day="2026-09-22")

    policy, usage, _ = tick(policy, usage, at(22, 16), 600)   # first session, 10 min
    assert available(policy, usage, TUE) == 1200

    policy, usage, _ = tick(policy, usage, at(22, 19), 900)   # second session, 15 min
    assert available(policy, usage, TUE) == 300


def test_a_manual_grant_survives_the_night():
    # What an adult gives is not lost because a child logged out early.
    policy, usage = grant(MANUAL, Usage(), TUE, 30), Usage(last_day="2026-09-22")
    policy, usage, _ = tick(policy, usage, at(22, 16), 600)

    policy, usage, change = tick(policy, usage, at(23, 16), 0)

    assert change.rolled
    assert available(policy, usage, TUE) == 1200


def test_a_daily_grant_dies_at_the_rollover():
    # A daily limit is a daily limit.
    policy, usage = grant(DAILY, Usage(), TUE, 30), Usage(last_day="2026-09-22", seconds_used_today=3600)
    assert available(policy, usage, TUE) == 1800

    policy, usage, change = tick(policy, usage, at(23, 16), 0)

    assert change.rolled
    assert policy.granted_seconds == 0
    assert available(policy, usage, TUE) == 3600


def test_the_bank_never_goes_below_zero():
    policy, usage = grant(MANUAL, Usage(), TUE, 1), Usage(last_day="2026-09-22")

    policy, usage, _ = tick(policy, usage, at(22, 16), 500)

    assert policy.granted_seconds == 0
    assert available(policy, usage, TUE) == 0


@pytest.mark.parametrize("minutes", [0, -5, 24 * 60 + 1, 2.5, True])
def test_a_grant_out_of_range_is_refused(minutes):
    with pytest.raises(ValueError):
        grant(MANUAL, Usage(), TUE, minutes)


# --- the time left, set by an adult (D50) --------------------------------------


def test_setting_what_a_daily_child_has_left_keeps_what_they_used():
    usage = Usage(last_day="2026-09-22", seconds_used_today=5 * 60)

    policy = set_left(DAILY, usage, TUE, 5)

    assert available(policy, usage, TUE) == 5 * 60
    assert usage.seconds_used_today == 5 * 60
    assert policy.granted_seconds == -50 * 60


def test_setting_more_than_the_day_s_allowance_gives_the_rest():
    usage = Usage(last_day="2026-09-22", seconds_used_today=50 * 60)

    assert available(set_left(DAILY, usage, TUE, 90), usage, TUE) == 90 * 60


def test_zero_leaves_nothing_and_the_child_is_blocked():
    usage = Usage(last_day="2026-09-22", seconds_used_today=60)

    assert check_access(set_left(DAILY, usage, TUE, 0), usage, TUE) == ("blocked", 0)
    assert check_access(set_left(MANUAL, usage, TUE, 0), usage, TUE) == ("needs_adult", 0)


def test_setting_what_a_manual_child_has_left_sets_their_bank():
    assert available(set_left(grant(MANUAL, Usage(), TUE, 30), Usage(), TUE, 5), Usage(), TUE) == 5 * 60


def test_what_was_taken_away_comes_back_with_the_next_day():
    usage = Usage(last_day="2026-09-22", seconds_used_today=5 * 60)
    policy = set_left(DAILY, usage, TUE, 0)

    policy, usage, change = tick(policy, usage, at(23, 16), 0)

    assert change.rolled and available(policy, usage, TUE) == 3600


def test_a_child_with_no_limit_has_nothing_to_set():
    with pytest.raises(ValueError):
        set_left(Policy(mode="unlimited"), Usage(), TUE, 5)


@pytest.mark.parametrize("minutes", [-1, 24 * 60 + 1, 2.5, True])
def test_a_time_left_out_of_range_is_refused(minutes):
    with pytest.raises(ValueError):
        set_left(DAILY, Usage(), TUE, minutes)


# --- the days of the week (D54) ---------------------------------------------


def test_the_day_of_the_week_is_the_accounting_day_s():
    # Tuesday until four on Wednesday morning.
    _, usage, _ = roll_day(DAILY, Usage(), day_of(at(23, 3, 59)))
    assert weekday_of(usage) == TUE
    _, usage, _ = roll_day(DAILY, usage, day_of(at(23, 4, 0)))
    assert weekday_of(usage) == WED


@pytest.mark.parametrize("mode", ["daily", "unlimited"])
def test_a_day_not_ticked_gives_nothing(mode):
    policy = Policy(mode=mode, daily_minutes=60, days=NOT_TUESDAY)
    usage = Usage(last_day="2026-09-22")

    assert available(policy, usage, TUE) == 0
    assert check_access(policy, usage, TUE) == ("day_off", 0)
    assert check_access(policy, usage, WED)[0] == "allowed"


@pytest.mark.parametrize("mode", ["daily", "unlimited"])
def test_a_grant_on_a_day_not_ticked_gives_its_minutes_and_no_more(mode):
    policy = grant(Policy(mode=mode, daily_minutes=60, days=NOT_TUESDAY), Usage(), TUE, 30)
    usage = Usage(last_day="2026-09-22")

    assert check_access(policy, usage, TUE) == ("allowed", 1800)
    policy, usage, _ = tick(policy, usage, at(22, 16), 600)
    assert available(policy, usage, TUE) == 1200
    policy, usage, _ = tick(policy, usage, at(22, 17), 1200)
    assert check_access(policy, usage, TUE) == ("day_off", 0)


@pytest.mark.parametrize("mode", ["daily", "unlimited"])
def test_a_grant_on_a_day_not_ticked_is_for_that_day_only(mode):
    days = (True, False, False, True, True, True, True)
    policy, usage = grant(Policy(mode=mode, days=days), Usage(), TUE, 30), Usage(last_day="2026-09-22")

    policy, usage, change = tick(policy, usage, at(23, 16), 0)

    assert change.rolled and policy.granted_seconds == 0
    assert check_access(policy, usage, WED) == ("day_off", 0)


def test_manual_mode_does_not_ask_the_days():
    policy = grant(Policy(mode="manual", days=(False,) * 7), Usage(), TUE, 30)

    assert check_access(policy, Usage(), TUE) == ("allowed", 1800)
    assert check_access(Policy(mode="manual", days=(False,) * 7), Usage(), TUE) \
        == ("needs_adult", 0)


def test_a_session_open_at_four_into_a_day_not_ticked_runs_out():
    days = (True, True, False, True, True, True, True)
    policy, usage = Policy(mode="daily", days=days), Usage(last_day="2026-09-22",
                                                           seconds_used_today=600)
    assert available(policy, usage, TUE) == 3000

    policy, usage, change = tick(policy, usage, at(23, 4, 0), 30)

    assert change.rolled
    assert available(policy, usage, weekday_of(usage)) == 0


def test_the_time_left_on_a_day_not_ticked_is_set_from_none():
    usage = Usage(last_day="2026-09-22", seconds_used_today=5 * 60)
    for mode in ("daily", "unlimited"):
        policy = set_left(Policy(mode=mode, days=NOT_TUESDAY), usage, TUE, 20)
        assert available(policy, usage, TUE) == 20 * 60
    with pytest.raises(ValueError):
        set_left(Policy(mode="unlimited", days=NOT_TUESDAY), usage, WED, 20)


def test_the_days_as_seven_digits():
    assert days_text(EVERY_DAY) == "1111111"
    assert days_text(NOT_TUESDAY) == "1011111"


# --- the day rolling over ----------------------------------------------------


def test_rollover_mid_session():
    policy, usage = DAILY, Usage(last_day="2026-09-22", seconds_used_today=3500)

    policy, usage, change = tick(policy, usage, at(23, 4, 0, ), 30)

    assert change.rolled
    assert usage.seconds_used_today == 30
    assert available(policy, usage, TUE) == 3570


def test_a_session_open_across_four_in_the_morning():
    policy, usage = DAILY, Usage(last_day="2026-09-22")
    moment = at(23, 3, 50)

    while moment < at(23, 4, 10):
        policy, usage, _ = tick(policy, usage, moment, 30)
        moment += timedelta(seconds=30)

    # Only the half after four counts towards the new day.
    assert usage.last_day == "2026-09-23"
    assert usage.seconds_used_today == 600


def test_a_clock_set_back_a_day_resets_nothing():
    # The trick a child would try first.
    policy, usage = DAILY, Usage(last_day="2026-09-23", seconds_used_today=3600)

    policy, usage, change = tick(policy, usage, at(22, 16), 0)

    assert change.backwards
    assert usage.last_day == "2026-09-23"
    assert check_access(policy, usage, TUE) == ("blocked", 0)


def test_a_clock_set_forward_a_week_is_a_new_day_and_is_reported():
    policy, usage = DAILY, Usage(last_day="2026-09-22", seconds_used_today=3600)

    policy, usage, change = tick(policy, usage, at(29, 16), 0)

    assert change.rolled
    assert change.jump_days == 7
    assert available(policy, usage, TUE) == 3600


def test_a_clock_set_back_more_than_a_day_is_reported():
    _, _, change = roll_day(DAILY, Usage(last_day="2026-09-25"), date(2026, 9, 20))

    assert change.backwards
    assert change.jump_days == 5


def test_an_ordinary_next_day_is_not_reported_as_a_jump():
    _, _, change = roll_day(DAILY, Usage(last_day="2026-09-22"), date(2026, 9, 23))

    assert change.rolled
    assert change.jump_days == 0


# --- warnings ----------------------------------------------------------------


def test_each_warning_fires_once():
    warnings = Warnings()
    warnings.arm(3600)

    fired = [warnings.due(left) for left in range(3600, -1, -30)]

    assert [w for w in fired if w is not None] == [600, 300, 60]


def test_signing_in_with_three_minutes_gives_only_the_one_minute_warning():
    warnings = Warnings()
    warnings.arm(180)

    fired = [warnings.due(left) for left in range(180, -1, -10)]

    assert [w for w in fired if w is not None] == [60]


def test_a_long_tick_that_crosses_two_thresholds_gives_the_more_urgent_one():
    warnings = Warnings()
    warnings.arm(700)

    assert warnings.due(250) == 300
    assert warnings.due(240) is None


def test_warnings_re_arm_after_a_grant():
    warnings = Warnings()
    warnings.arm(3600)
    for left in range(3600, -1, -30):
        warnings.due(left)

    warnings.arm(900)   # an adult gave fifteen minutes

    fired = [warnings.due(left) for left in range(900, -1, -30)]
    assert [w for w in fired if w is not None] == [600, 300, 60]


def test_an_unlimited_child_is_never_warned():
    warnings = Warnings()
    warnings.arm(UNLIMITED)

    assert warnings.due(UNLIMITED) is None
    assert warnings.next_threshold(UNLIMITED) is None


def test_the_next_tick_is_timed_to_the_next_warning():
    # So a warning lands within a second of when it is due, not up to thirty
    # seconds late.
    warnings = Warnings()
    warnings.arm(3600)

    assert warnings.next_threshold(610) == 10
    warnings.due(600)
    assert warnings.next_threshold(600) == 300
    assert warnings.next_threshold(45) == 45


def test_the_thresholds_are_ten_five_and_one_minute():
    assert WARNINGS == (600, 300, 60)


# --- validating what the panel sends ------------------------------------------


def test_a_valid_policy():
    assert validate_policy({"mode": "daily", "daily_minutes": 45}) == Policy("daily", 45, 0)
    assert validate_policy({"mode": "daily", "days": list(NOT_TUESDAY)}).days == NOT_TUESDAY


@pytest.mark.parametrize(
    "document",
    [
        {"mode": "forever"},
        {"mode": "daily", "daily_minutes": -1},
        {"mode": "daily", "daily_minutes": 24 * 60 + 1},
        {"mode": "daily", "daily_minutes": "60"},
        {"mode": "daily", "daily_minutes": True},
        {"mode": "manual", "granted_seconds": 99999},
        {"mode": "daily", "days": [True] * 6},
        {"mode": "daily", "days": [True] * 8},
        {"mode": "daily", "days": "1111100"},
        {"mode": "daily", "days": [1, 1, 1, 1, 1, 0, 0]},
        {},
    ],
)
def test_an_invalid_policy_is_refused(document):
    # granted_seconds is not part of a policy: time is given by a grant, which
    # is audited, never by writing the bank directly.
    with pytest.raises(ValueError):
        validate_policy(document)


def test_documents_round_trip():
    policy = Policy("daily", 30, 120, NOT_TUESDAY)
    usage = Usage("2026-09-22", 900, True, "time_up")

    assert Policy.from_document(policy.as_document()) == policy
    assert Usage.from_document(usage.as_document()) == usage
    # A policy written before there were days has every day.
    assert Policy.from_document({"mode": "daily"}).days == EVERY_DAY
