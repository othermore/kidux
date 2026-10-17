"""Kidux's answer to a link out of a module (kidux.closed, D107): a
bubble, in the child's words, and nothing opened."""

from kidux import closed


def test_a_link_out_sends_the_bubble_and_says_it_was_not_opened(capsys):
    sent = []

    assert closed.main(["https://phet.colorado.edu/"], send=sent.append,
                       translate=lambda text: f"[{text}]") == 0

    assert sent == [("Kidux", 0, "", "[That opens the internet, which is closed here.]",
                     "", [], {}, -1)]
    assert "not opened: https://phet.colorado.edu/" in capsys.readouterr().err


def test_without_a_bubble_the_program_that_asked_is_still_told_all_went_well(capsys):
    def no_bus(_arguments):
        raise OSError("no session bus")

    assert closed.main(["file:///tmp/a.html"], send=no_bus) == 0
    assert "no bubble: no session bus" in capsys.readouterr().err
