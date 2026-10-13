from computedeck.app import create_app
from fastapi.testclient import TestClient

from computedeck_hello import plugin

HEADERS = {"Origin": "http://127.0.0.1:8710", "X-ComputeDeck": "1"}


def test_the_plugin_answers_once_switched_on(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPUTEDECK_AUTH", "off")
    with TestClient(
        create_app(tmp_path, polling=False, plugins=[plugin]), base_url="http://127.0.0.1"
    ) as client:
        assert client.get("/api/plugins/hello/hello").status_code == 404
        client.put("/api/toolbox/hello", json={"enabled": True}, headers=HEADERS)
        assert client.get("/api/plugins/hello/hello").json() == {"greeting": "hello"}
