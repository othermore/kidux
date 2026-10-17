"""Which guide the pane shows, in each of the child's modes, what it
remembers, and the missions (guides.py, D106)."""

import json

from kidux_launcher import guides

GUIDED = {"kig", "step"}


def has_guide(module_id):
    return module_id in GUIDED


def test_without_windows_the_pane_is_the_guide_of_the_module_on_screen(tmp_path):
    g = guides.Guides(windows=False, path=tmp_path / "s.json")

    assert g.follow(["kig"], "kig", has_guide) == "kig"
    # A module without a guide on screen, or home: no pane.
    assert g.follow(["kig", "canary"], "canary", has_guide) is None
    assert g.follow(["kig", "canary"], None, has_guide) is None
    # Two with a guide: each its own as the child swaps.
    assert g.follow(["kig", "canary", "step"], "step", has_guide) == "step"
    assert g.follow(["kig", "canary", "step"], "kig", has_guide) == "kig"
    # No pin without windows.
    g.pin(True)
    assert g.pinned is None


def test_with_windows_the_pane_stays_while_a_module_with_a_guide_is_open(tmp_path):
    g = guides.Guides(windows=True, path=tmp_path / "s.json")

    assert g.follow(["kig"], "kig", has_guide) == "kig"
    # A window without a guide in use, or home: the last guide stays.
    assert g.follow(["kig", "canary"], "canary", has_guide) == "kig"
    assert g.follow(["kig", "canary"], None, has_guide) == "kig"
    # Another with a guide in use: its guide.
    assert g.follow(["kig", "canary", "step"], "step", has_guide) == "step"
    assert g.open == ["kig", "step"]
    # The one shown closes: the last opened of those left.
    assert g.follow(["kig", "canary"], "canary", has_guide) == "kig"
    # The last with a guide closes: no pane.
    assert g.follow(["canary"], "canary", has_guide) is None


def test_with_windows_a_guide_picked_is_pinned_and_stays(tmp_path):
    g = guides.Guides(windows=True, path=tmp_path / "s.json")
    g.follow(["kig", "step"], "step", has_guide)

    assert g.pick("kig") == "kig" and g.pinned == "kig"
    assert g.follow(["kig", "step"], "step", has_guide) == "kig"
    # Unpinned, it follows the window in use again.
    g.pin(False)
    assert g.follow(["kig", "step"], "step", has_guide) == "step"
    # Pinned by its button, the one shown stays.
    g.pin(True)
    assert g.follow(["kig", "step"], "kig", has_guide) == "step"
    # Its module closes: the pin goes with it.
    assert g.follow(["kig"], "kig", has_guide) == "kig" and g.pinned is None
    # A module not open cannot be picked.
    assert g.pick("step") == "kig"


def test_what_the_child_left_is_remembered_across_sessions(tmp_path):
    path = tmp_path / "share" / "launcher.json"
    g = guides.Guides(windows=False, path=path)
    assert (g.folded("kig"), g.lesson("kig"), g.seen("kig")) == (False, None, False)

    g.remember("kig", lesson=3)
    g.remember("kig", folded=True)
    again = guides.Guides(windows=False, path=path)

    assert (again.folded("kig"), again.lesson("kig"), again.seen("kig")) == (True, 3, True)
    assert json.loads(path.read_text()) == {"guides": {"kig": {"folded": True, "lesson": 3}}}
    # Back to the list.
    again.remember("kig", lesson=None)
    assert guides.Guides(windows=False, path=path).lesson("kig") is None


def test_a_state_that_does_not_read_is_left_aside(tmp_path, caplog):
    path = tmp_path / "launcher.json"
    path.write_text("not json")

    g = guides.Guides(windows=False, path=path)

    assert g.lesson("kig") is None
    assert "does not read" in caplog.text


def test_missions_are_copied_once_and_the_child_s_work_is_never_overwritten(tmp_path):
    source = tmp_path / "content"
    source.mkdir()
    (source / "medio.kig").write_text("mission")
    (source / "paralelas.kig").write_text("mission 2")
    folder = tmp_path / "Documentos" / "Misiones de Kig"
    folder.mkdir(parents=True)
    (folder / "medio.kig").write_text("the child's own")

    copies = guides.copy_missions([str(source / "medio.kig"), str(source / "paralelas.kig"),
                                   str(source / "gone.kig")], folder)

    assert copies == [folder / "medio.kig", folder / "paralelas.kig"]
    assert (folder / "medio.kig").read_text() == "the child's own"
    assert (folder / "paralelas.kig").read_text() == "mission 2"
