"""What the launcher takes from the daemon's answers."""

from kidux_launcher.daemon import SystemDaemon


class FakeClient:
    def list_modules(self, username):
        assert username == "ana"
        return [{"id": "abc", "enabled": True}, {"id": "hello", "enabled": False},
                {"id": "xyz", "enabled": True}]


def test_only_the_modules_enabled_for_the_child_get_a_tile():
    daemon = SystemDaemon.__new__(SystemDaemon)
    daemon._username, daemon._client = "ana", FakeClient()

    assert daemon.modules() == ["abc", "xyz"]
