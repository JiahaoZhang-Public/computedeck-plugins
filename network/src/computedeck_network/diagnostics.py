"""On-demand proxy diagnostics. No provider URLs, redirects, or background probes."""

import argparse
import ipaddress
import json
import platform
import re
import shlex
import socket
import subprocess
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# These are the only HTTP destinations diagnostics can contact. Keep redirects disabled.
TEST_URL = "https://checkip.amazonaws.com/"
TEST_HOST = "checkip.amazonaws.com"


def command(args: list[str], timeout: int = 5) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return result.stdout if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def route(address: str = "default") -> dict[str, str]:
    # Only numeric upstream addresses are accepted; never resolve a configured hostname.
    if address != "default":
        ipaddress.ip_address(address)
    output = command(["/sbin/route", "-n", "get", address])
    return {
        key: match.group(1)
        for key in ("interface", "gateway")
        if (match := re.search(rf"^\s*{key}:\s*(\S+)", output, re.M))
    }


def system_proxies() -> list[dict[str, Any]]:
    output = command(["/usr/sbin/scutil", "--proxy"])
    proxies = []
    for kind in ("HTTP", "HTTPS", "SOCKS", "ProxyAutoConfig", "ProxyAutoDiscovery"):
        enabled = re.search(rf"\b{kind}Enable\s*:\s*(\d+)", output)
        host = re.search(rf"\b{kind}Proxy\s*:\s*(\S+)", output)
        port = re.search(rf"\b{kind}Port\s*:\s*(\d+)", output)
        proxies.append(
            {
                "kind": kind,
                "enabled": bool(enabled and enabled.group(1) == "1"),
                "host": host.group(1) if host else None,
                "port": int(port.group(1)) if port else None,
                "known": bool(output),
            }
        )
    return proxies


def load_config() -> tuple[Path | None, dict[str, Any], bool, str | None]:
    candidates: list[tuple[Path, bool]] = []
    for line in command(["/bin/ps", "-axww", "-o", "args="]).splitlines():
        try:
            parts = shlex.split(line)
        except ValueError:
            continue
        if not parts or Path(parts[0]).name not in ("mihomo", "clash", "clash-meta"):
            continue
        if "-f" in parts and len(parts) > parts.index("-f") + 1:
            candidates.append((Path(parts[parts.index("-f") + 1]).expanduser(), True))
        elif "-d" in parts and len(parts) > parts.index("-d") + 1:
            candidates.append(
                (Path(parts[parts.index("-d") + 1]).expanduser() / "config.yaml", True)
            )
    candidates.extend(
        (Path(p).expanduser(), False)
        for p in (
            "/opt/homebrew/etc/mihomo/config.yaml",
            "/usr/local/etc/mihomo/config.yaml",
            "~/.config/mihomo/config.yaml",
            "~/.config/clash/config.yaml",
        )
    )
    for path, active in candidates:
        if not path.is_file():
            continue
        try:
            config = yaml.safe_load(path.read_text())
            if not isinstance(config, dict):
                raise ValueError("Expected mapping")
            return path, config, active, None
        except (OSError, ValueError, yaml.YAMLError):
            # YAML exception text may contain the password-bearing source line.
            return (
                path,
                {},
                active,
                "Cannot read proxy configuration; check YAML syntax and file permissions.",
            )
    return None, {}, False, None


def numeric_endpoint(proxy: dict[str, Any]) -> tuple[str, int]:
    address = str(proxy.get("server", ""))
    ipaddress.ip_address(address)
    port = int(proxy.get("port", 0))
    if not 1 <= port <= 65535:
        raise ValueError("Invalid port")
    return address, port


def predicted_rule(config: dict[str, Any]) -> str:
    """Only predict unambiguous domain rules, without DNS, GeoIP, or provider downloads."""
    mode = config.get("mode", "rule")
    if mode == "direct":
        return "DIRECT (configuration prediction)"
    if mode != "rule":
        return "GLOBAL (selected upstream not observed)"
    for rule in config.get("rules", []):
        parts = [p.strip() for p in str(rule).split(",")]
        if len(parts) == 2 and parts[0] == "MATCH":
            return f"{parts[1]} (MATCH, configuration prediction)"
        if len(parts) < 3:
            return "Cannot determine statically"
        kind, value, target = parts[:3]
        value = value.lower()
        if kind == "DOMAIN":
            match = TEST_HOST == value
        elif kind == "DOMAIN-SUFFIX":
            match = TEST_HOST == value or TEST_HOST.endswith("." + value)
        elif kind == "DOMAIN-KEYWORD":
            match = value in TEST_HOST
        else:
            return "Dynamic/IP rules require runtime verification"
        if match:
            return f"{target} ({kind}, configuration prediction)"
    return "No matching rule configured"


def safe_mixed_probe(config: dict[str, Any]) -> bool:
    # An existing core may resolve its own upstream/DNS/provider hostnames. Only
    # test simple DIRECT configurations whose resolution path we can constrain.
    if not predicted_rule(config).startswith("DIRECT（"):
        return False
    if any(config.get(k) for k in ("proxy-providers", "rule-providers", "hosts", "tun")):
        return False
    dns = config.get("dns", {})
    if not isinstance(dns, dict):
        return False
    return not any(k not in ("enable", "enhanced-mode", "ipv6", "listen") for k in dns)


def snapshot() -> tuple[dict[str, Any], dict[str, Any]]:
    path, config, active, error = load_config()
    mixed = config.get("mixed-port")
    port = mixed if isinstance(mixed, int) and 1 <= mixed <= 65535 else None
    listener = bool(
        port and command(["/usr/sbin/lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"])
    )
    upstreams = []
    for item in config.get("proxies", []):
        if not isinstance(item, dict):
            continue
        upstream_port: Any
        try:
            host, upstream_port = numeric_endpoint(item)
            eligible = item.get("type") == "socks5" and not item.get("tls", False)
        except (ValueError, TypeError):
            host, upstream_port, eligible = str(item.get("server", "")), item.get("port"), False
        upstreams.append(
            {
                "name": str(item.get("name", "")),
                "type": str(item.get("type", "")),
                "host": host,
                "port": upstream_port,
                "testable": eligible,
                "note": None
                if eligible
                else (
                    "Only plain SOCKS5 upstreams configured by IP are tested; "
                    "upstream domains are not resolved."
                ),
            }
        )
    return {
        "host": platform.node(),
        "observed_at": datetime.now(UTC).isoformat(),
        "route": route(),
        "system_proxies": system_proxies(),
        "config_path": str(path) if path else None,
        "config_error": error,
        "config_active": active,
        "mode": str(config.get("mode", "rule")) if path else None,
        "mixed_port": port,
        "listening": listener,
        "upstreams": upstreams,
        "test_url": TEST_URL,
        "predicted_rule": predicted_rule(config) if path else "No Mihomo configuration",
        "mixed_testable": bool(active and listener and safe_mixed_probe(config)),
        "tests": [],
    }, config


def receive(sock: socket.socket, count: int) -> bytes:
    data = b""
    while len(data) < count:
        part = sock.recv(count - len(data))
        if not part:
            raise ConnectionError("Upstream closed the connection")
        data += part
    return data


def authenticate(proxy: dict[str, Any]) -> dict[str, Any]:
    start = time.monotonic()
    stage = "TCP"
    result: dict[str, Any] = {"tcp": False, "auth": False}
    try:
        with socket.create_connection(numeric_endpoint(proxy), timeout=6) as sock:
            result["tcp"] = True
            sock.settimeout(6)
            stage = "SOCKS5 negotiation"
            has_credentials = bool(proxy.get("username") or proxy.get("password"))
            sock.sendall(b"\x05\x01\x02" if has_credentials else b"\x05\x01\x00")
            method = receive(sock, 2)
            if method == b"\x05\x02" and has_credentials:
                stage = "Username/password authentication"
                user = str(proxy.get("username", "")).encode()
                password = str(proxy.get("password", "")).encode()
                if not 1 <= len(user) <= 255 or not 1 <= len(password) <= 255:
                    raise ValueError(
                        "Username or password length does not meet SOCKS5 requirements"
                    )
                sock.sendall(bytes([1, len(user)]) + user + bytes([len(password)]) + password)
                if receive(sock, 2) != b"\x01\x00":
                    raise ConnectionError("Upstream rejected authentication")
            elif method != b"\x05\x00":
                raise ConnectionError("Upstream does not accept the offered authentication methods")
            result["auth"] = True
    except (OSError, ValueError) as exc:
        result["error"] = f"{stage}：{'Timed out' if isinstance(exc, TimeoutError) else str(exc)}"
    result["auth_ms"] = round((time.monotonic() - start) * 1000)
    return result


def curl_quote(value: str) -> str:
    return (
        '"'
        + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
        + '"'
    )


def transfer(proxy_url: str = "", credentials: str | None = None) -> dict[str, Any]:
    config = f"proxy = {curl_quote(proxy_url)}\nnoproxy = {curl_quote('' if proxy_url else '*')}\n"
    if credentials is not None:
        config += f"proxy-user = {curl_quote(credentials)}\n"
    args = [
        "/usr/bin/curl",
        "--disable",
        "--config",
        "-",
        "--silent",
        "--show-error",
        "--proto",
        "=https",
        "--connect-timeout",
        "6",
        "--max-time",
        "15",
        "--max-redirs",
        "0",
        "--max-filesize",
        "4096",
        "--write-out",
        '\n{"http":%{http_code},"seconds":%{time_total},"peer":"%{remote_ip}"}',
        TEST_URL,
    ]
    try:
        result = subprocess.run(
            args, input=config, capture_output=True, text=True, timeout=18, check=False
        )
        body, _, metrics = result.stdout.strip().rpartition("\n")
        report = json.loads(metrics)
        report["ok"] = False
        if result.returncode == 0 and report["http"] == 200:
            report["egress_ip"] = str(ipaddress.ip_address(body.strip()))
            report["ok"] = True
        else:
            errors = {
                5: "Proxy resolution failed",
                6: "Test site resolution failed",
                7: "Connection failed",
                28: "Timed out",
                35: "TLS handshake failed",
                60: "TLS certificate verification failed",
                97: "SOCKS handshake failed",
            }
            report["error"] = errors.get(
                result.returncode, f"HTTP {report['http']} / curl {result.returncode}"
            )
        return report
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"ok": False, "error": "Test incomplete or invalid egress IP"}


def probe_upstream(proxy: dict[str, Any]) -> dict[str, Any]:
    host, port = numeric_endpoint(proxy)
    report: dict[str, Any] = {
        "name": str(proxy.get("name", "SOCKS5")),
        "kind": "upstream",
        "ok": False,
        "path": ["Diagnostics", f"SOCKS5 {host}:{port}", TEST_HOST],
        "route": route(host),
    }
    report.update(authenticate(proxy))
    if report["auth"]:
        credentials = None
        if proxy.get("username") or proxy.get("password"):
            credentials = f"{proxy.get('username', '')}:{proxy.get('password', '')}"
        endpoint = f"[{host}]" if ":" in host else host
        report.update(transfer(f"socks5h://{endpoint}:{port}", credentials))
    return report


def diagnose(probe: bool = False) -> dict[str, Any]:
    report, config = snapshot()
    if not probe:
        return report
    with ThreadPoolExecutor(max_workers=4) as pool:
        direct = pool.submit(transfer)
        mixed = (
            pool.submit(transfer, f"http://127.0.0.1:{report['mixed_port']}")
            if report["mixed_testable"]
            else None
        )
        upstreams: list[Future[dict[str, Any]]] = []
        for proxy in config.get("proxies", []):
            if not isinstance(proxy, dict) or proxy.get("type") != "socks5" or proxy.get("tls"):
                continue
            try:
                numeric_endpoint(proxy)
            except (ValueError, TypeError):
                continue
            if len(upstreams) < 4:
                upstreams.append(pool.submit(probe_upstream, proxy))
        report["tests"].append(
            {
                "name": "Direct connection",
                "kind": "direct",
                "path": ["Diagnostics", "DIRECT", TEST_HOST],
                **direct.result(),
            }
        )
        if mixed:
            report["tests"].append(
                {
                    "name": "Local Mihomo",
                    "kind": "mixed",
                    "path": [
                        "Diagnostics",
                        f"127.0.0.1:{report['mixed_port']}",
                        "Further proxy hops not observed",
                        TEST_HOST,
                    ],
                    **mixed.result(),
                }
            )
        report["tests"].extend(task.result() for task in upstreams)
    report["tested_at"] = datetime.now(UTC).isoformat()
    report["test_note"] = (
        "Fixed site, no redirects; at most four IP-addressed SOCKS5 upstreams are tested."
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    print(json.dumps(diagnose(probe=args.probe), ensure_ascii=False))
