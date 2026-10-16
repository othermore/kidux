"""What is shown again, and what only moves on (screen.py)."""

from kidux_greeter.screen import Screen, only_progress_differs


def polled(fraction: float, package: str = "thunderbird", job: str = "installing", **more):
    update = {"job": job, "fraction": fraction, "package": package, "outcome": "", "detail": ""}
    return Screen("panel_modules", "es_ES.UTF-8",
                  {"modules": [{"id": "mail"}], "installing": "mail", "polling": True,
                   "update": update, **more}, owner="panel")


def test_a_jobs_progress_moving_on_is_not_a_page_to_draw_again():
    assert only_progress_differs(polled(0.2), polled(0.5))
    assert only_progress_differs(polled(0.5, "thunderbird"), polled(0.6, "libnotify4"))


def test_anything_else_changed_is_drawn_again():
    assert not only_progress_differs(polled(0.2), polled(0.5, job="removing"))
    assert not only_progress_differs(polled(0.2), polled(0.5, failure="apt said no"))
    assert not only_progress_differs(polled(0.2), polled(0.5, modules=[]))
    done = polled(1.0)
    done.data["polling"] = False
    assert not only_progress_differs(polled(0.9), done)
    assert not only_progress_differs(polled(0.2),
                                     Screen("panel_system", "es_ES.UTF-8", polled(0.5).data,
                                            owner="panel"))
    assert not only_progress_differs(polled(0.2), polled(0.5).__class__(
        "panel_modules", "es_ES.UTF-8", polled(0.5).data, notice="Installed", owner="panel"))
