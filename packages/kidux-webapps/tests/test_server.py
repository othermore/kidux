"""The web applications' server: what it serves, and everything it refuses."""

import http.client
import importlib.machinery
import importlib.util
import os
import sys
import threading
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]


def load(name: str):
    sys.dont_write_bytecode = True
    module_name = name.replace("-", "_")
    loader = importlib.machinery.SourceFileLoader(module_name, str(PACKAGE / "bin" / name))
    spec = importlib.util.spec_from_loader(module_name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


server = load("kidux-webapps")


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "webapps"
    (root / "hello-web").mkdir(parents=True)
    (root / "hello-web" / "index.html").write_text("<p>hello</p>")
    (root / "hello-web" / "app.js").write_text("1;")
    (root / "empty").mkdir()
    (root / "games").mkdir()
    (root / "games" / "index.html").write_text("<p>games</p>")
    (root / "games" / "maze.html").write_text("<p>maze</p>")
    (root / "games" / "maze").mkdir()
    (root / "games" / "maze" / "maze.js").write_text("1;")
    (root / "games" / "pond.html").write_text("<p>pond</p>")
    (tmp_path / "secret").write_text("not for a child")
    (tmp_path / "secret.html").write_text("not for a child either")
    (root / "hello-web" / "out").symlink_to(tmp_path / "secret")
    (root / "outside").symlink_to(tmp_path)
    return root


@pytest.mark.parametrize("target,status", [
    ("/hello-web/", 200),
    ("/hello-web/index.html", 200),
    ("/hello-web/app.js", 200),
    ("/hello-web/?lang=es", 200),
    ("/", 404),
    ("/empty/", 404),
    ("/nothing/", 404),
    ("/hello-web/missing.png", 404),
    ("/../secret", 403),
    ("/hello-web/../../secret", 403),
    ("/hello-web/%2e%2e/%2e%2e/secret", 403),
    ("/hello-web/out", 403),
    ("/outside/secret", 403),
    ("/hello-web/%00", 403),
    # A page by its name without .html, as Blockly Games link their games,
    # beside a directory of the same name or not; never out of the directory.
    ("/games/maze?lang=es", 200),
    ("/games/maze/maze.js", 200),
    ("/games/maze/", 404),
    ("/games/pond", 200),
    ("/games/index", 200),
    ("/games/bird", 404),
    ("/games/../../secret", 403),
])
def test_what_is_served_and_what_is_refused(tree, target, status):
    got, path = server.resolve(tree, target)

    assert got == status
    assert (path is not None) == (status == 200)
    if path is not None:
        assert tree.resolve() in path.parents


def test_a_page_named_without_html_is_that_page(tree):
    got, path = server.resolve(tree, "/games/maze?lang=es")

    assert (got, path.name) == (200, "maze.html")


def test_types_are_named_by_extension():
    assert server.content_type(Path("a.html")) == "text/html; charset=utf-8"
    assert server.content_type(Path("a.js")) == "text/javascript; charset=utf-8"
    assert server.content_type(Path("a.wasm")) == "application/wasm"


def test_the_server_answers_with_the_file_and_never_a_listing(tree):
    handler = type("Handler", (server.Handler,), {"root": tree})
    httpd = server.http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        def get(target):
            connection = http.client.HTTPConnection("127.0.0.1", httpd.server_address[1],
                                                    timeout=5)
            connection.request("GET", target)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()

        status, headers, body = get("/hello-web/")
        assert (status, body) == (200, b"<p>hello</p>")
        assert headers["Content-Type"] == "text/html; charset=utf-8"
        assert headers["Cache-Control"] == "no-store"
        status, _, body = get("/")
        assert status == 404 and b"hello-web" not in body
        assert get("/hello-web/../../secret")[0] == 403
    finally:
        httpd.shutdown()


def test_it_listens_on_the_loopback_address_only():
    assert server.ADDRESS == ("127.0.0.1", 8123)
    assert os.path.basename(str(server.ROOT)) == "webapps"
