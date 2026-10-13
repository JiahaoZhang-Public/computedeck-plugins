import json
import socket
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from computedeck.app import create_app
from computedeck_network import diagnostics as network
from computedeck_network import plugins as network_plugin
from fastapi.testclient import TestClient

HEADERS = {"Origin": "http://127.0.0.1:8710", "X-ComputeDeck": "1"}
PROXY = "/api/plugins/proxy"
EGRESS = "/api/plugins/egress"


@pytest.fixture
def config():
    return {
        "mixed-port": 7890,
        "mode": "rule",
        "proxies": [
            {
                "name": "upstream",
                "type": "socks5",
                "server": "192.0.2.1",
                "port": 1080,
                "username": "test-user",
                "password": "test-secret",
            },
        ],
        "rules": ["DOMAIN-KEYWORD,restricted-example,PROXY", "MATCH,DIRECT"],
        "dns": {"enable": True, "enhanced-mode": "fake-ip"},
    }


@pytest.fixture
def isolated(monkeypatch, config):
    monkeypatch.setattr(
        network, "load_config", lambda: (Path("/test/config.yaml"), config, True, None)
    )
    monkeypatch.setattr(network, "command", lambda args, timeout=5: "")
    return config


def test_status_never_uses_network_or_exposes_credentials(monkeypatch, isolated):
    def denied(*args, **kwargs):
        pytest.fail("Status must not connect to any host")

    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(network, "transfer", denied)
    report = network.diagnose()
    serialized = json.dumps(report)
    assert "test-secret" not in serialized
    assert "test-user" not in serialized
    assert report["predicted_rule"].startswith("DIRECT")
    assert report["tests"] == []


def test_probe_skips_all_upstream_hostnames_and_dynamic_core_dns(monkeypatch, isolated):
    isolated["proxies"].append(
        {
            "name": "restricted",
            "type": "socks5",
            "server": "signin.restricted.example.invalid",
            "port": 1080,
        }
    )
    isolated["dns"]["nameserver"] = ["https://dns.restricted.example.invalid/dns-query"]
    calls = []
    monkeypatch.setattr(network, "transfer", lambda *args: {"ok": True, "egress_ip": "192.0.2.3"})
    monkeypatch.setattr(
        network, "probe_upstream", lambda p: calls.append(p["server"]) or {"ok": True}
    )
    report = network.diagnose(True)
    assert calls == ["192.0.2.1"]
    assert not report["mixed_testable"]
    assert report["upstreams"][1]["testable"] is False


def test_rule_prediction_stops_at_unobserved_rules(config):
    assert network.predicted_rule(config) == "DIRECT (MATCH, configuration prediction)"
    config["rules"].insert(0, "RULE-SET,unknown,PROXY")
    assert "require runtime verification" in network.predicted_rule(config)
    assert not network.safe_mixed_probe(config)


def test_curl_is_fixed_target_no_redirects_and_no_credentials_in_argv(monkeypatch):
    seen = {}

    def run(args, **kwargs):
        seen.update(args=args, **kwargs)
        return subprocess.CompletedProcess(
            args, 0, '192.0.2.5\n{"http":200,"seconds":1.2,"peer":"192.0.2.1"}', ""
        )

    monkeypatch.setattr(subprocess, "run", run)
    result = network.transfer("socks5h://192.0.2.1:1080", "user:private-pass")
    assert result["ok"] and result["egress_ip"] == "192.0.2.5"
    assert seen["args"][-1] == "https://checkip.amazonaws.com/"
    assert "--location" not in seen["args"] and "-L" not in seen["args"]
    assert seen["args"][1] == "--disable"
    assert "private-pass" not in " ".join(seen["args"])
    assert "private-pass" in seen["input"]
    assert 'noproxy = ""' in seen["input"]
    assert "private-pass" not in json.dumps(result)


def test_redirect_response_is_not_success_or_followed(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda args, **kw: subprocess.CompletedProcess(
            args, 0, '\n{"http":302,"seconds":0.1,"peer":"192.0.2.1"}', ""
        ),
    )
    assert network.transfer()["ok"] is False


def test_direct_test_disables_environment_proxy(monkeypatch):
    seen = {}

    def run(args, **kwargs):
        seen.update(kwargs)
        return subprocess.CompletedProcess(
            args, 0, '192.0.2.5\n{"http":200,"seconds":1,"peer":"192.0.2.1"}', ""
        )

    monkeypatch.setattr(subprocess, "run", run)
    network.transfer()
    assert 'proxy = ""' in seen["input"] and 'noproxy = "*"' in seen["input"]


def test_auth_handles_fragmented_responses_and_never_sends_connect(monkeypatch, config):
    sock = MagicMock()
    sock.__enter__.return_value = sock
    sock.recv.side_effect = [b"\x05", b"\x02", b"\x01", b"\x00"]
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kw: sock)
    report = network.authenticate(config["proxies"][0])
    assert report["tcp"] and report["auth"]
    assert sock.sendall.call_count == 2  # method offer and credentials only


def test_auth_timeout_blocks_transfer(monkeypatch, config):
    monkeypatch.setattr(network, "route", lambda host: {})
    monkeypatch.setattr(
        network, "authenticate", lambda p: {"tcp": True, "auth": False, "error": "timeout"}
    )
    transfer = MagicMock()
    monkeypatch.setattr(network, "transfer", transfer)
    assert not network.probe_upstream(config["proxies"][0])["ok"]
    transfer.assert_not_called()


def test_network_api_separates_status_and_probe_and_rejects_urls(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        network, "diagnose", lambda probe=False: calls.append(probe) or {"tests": []}
    )
    app = create_app(tmp_path, polling=False, plugins=[network_plugin.proxy, network_plugin.egress])
    with TestClient(app) as client:
        assert client.get(PROXY + "/status").status_code == 200
        assert calls == [False]
        # Status reads only; testing is the egress plugin's, and only by POST.
        assert client.post(PROXY + "/probe", json={}, headers=HEADERS).status_code in (404, 405)
        assert client.post(EGRESS + "/probe", json={}, headers=HEADERS).status_code == 200
        assert calls == [False, True]
        assert client.post(EGRESS + "/probe", json={}).status_code == 403
        assert (
            client.post(
                EGRESS + "/probe",
                json={"url": "https://restricted.example.invalid"},
                headers=HEADERS,
            ).status_code
            == 422
        )
        assert calls == [False, True]
