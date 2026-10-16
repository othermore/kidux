"""A module's notices (notices.py, D98): what the bubble keeps of the
desktop's notifications, and what its server answers, without a display."""

from kidux_launcher import notices


class Recorded:
    def __init__(self):
        self.events = []
        self.notices = notices.Notices(
            show=lambda n: self.events.append(("show", n.id)),
            hide=lambda number: self.events.append(("hide", number)),
            closed=lambda number, reason: self.events.append(("closed", number, reason)),
            invoked=lambda number, key: self.events.append(("invoked", number, key)))

    def notify(self, replaces=0, actions=(), hints=None, timeout=-1, module="mail"):
        return self.notices.notify(module, "Thunderbird", replaces, "Summary", "Text",
                                   list(actions), hints or {}, timeout)


def test_the_server_offers_a_text_and_actions_and_never_a_sound():
    assert notices.CAPABILITIES == ("body", "actions")
    assert "sound" not in notices.CAPABILITIES
    assert '<method name="Notify">' in notices.INTERFACE
    assert '<signal name="NotificationClosed">' in notices.INTERFACE


def test_each_notice_gets_a_number_of_its_own():
    recorded = Recorded()
    first, second = recorded.notify(), recorded.notify()

    assert (first.id, second.id) == (1, 2)
    assert recorded.events == [("show", 1), ("show", 2)]


def test_a_notice_asked_to_replace_another_takes_its_number_and_place():
    recorded = Recorded()
    recorded.notify()
    again = recorded.notify(replaces=1)

    assert again.id == 1
    assert recorded.events == [("show", 1), ("hide", 1), ("show", 1)]
    # One that is not shown any more is not replaced: a new number.
    assert recorded.notify(replaces=7).id == 2


def test_a_notice_goes_by_itself_unless_it_is_urgent_or_never_expires():
    recorded = Recorded()
    plain = recorded.notify()
    urgent = recorded.notify(hints={"urgency": notices.CRITICAL})
    lasting = recorded.notify(timeout=0)
    assert (plain.stays, urgent.stays, lasting.stays) == (False, True, True)

    for notice in (plain, urgent, lasting):
        recorded.notices.expire(notice.id)

    assert list(recorded.notices.shown) == [urgent.id, lasting.id]
    assert ("closed", plain.id, notices.EXPIRED) in recorded.events


def test_closing_by_its_number_says_why_and_a_notice_closes_once():
    recorded = Recorded()
    recorded.notify()

    assert recorded.notices.close(1, notices.CLOSED)
    assert not recorded.notices.close(1, notices.CLOSED)
    assert recorded.events[-2:] == [("hide", 1), ("closed", 1, notices.CLOSED)]


def test_actions_are_pairs_the_click_is_the_default_and_the_rest_are_buttons():
    recorded = Recorded()
    notice = recorded.notify(actions=["default", "Open", "mark-read", "Mark as read", "odd"])

    assert notice.actions == (("default", "Open"), ("mark-read", "Mark as read"))
    assert notice.buttons == (("mark-read", "Mark as read"),)

    recorded.notices.act(notice.id, "nonsense")
    assert notice.id in recorded.notices.shown
    recorded.notices.act(notice.id, "default")
    assert recorded.events[-3:] == [("invoked", 1, "default"), ("hide", 1),
                                    ("closed", 1, notices.DISMISSED)]


def test_a_process_s_module_is_its_scope_s(tmp_path):
    def cgroup(pid, text):
        (tmp_path / str(pid)).mkdir()
        (tmp_path / str(pid) / "cgroup").write_text(text)

    cgroup(10, "0::/user.slice/user-1001.slice/user@1001.service/app.slice/"
               "kidux-module-mail.scope\n")
    cgroup(11, "0::/user.slice/user-1001.slice/user@1001.service/session.slice/"
               "kidux-launcher.service\n")

    assert notices.module_of(10, tmp_path) == "mail"
    assert notices.module_of(11, tmp_path) == ""
    assert notices.module_of(12, tmp_path) == ""
