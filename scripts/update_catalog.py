"""Update marketplace entries from an actual PyPI release, never placeholder digests."""

import argparse
import json
import re
import tomllib
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def catalog_entries(plugin: str, version: str, release: dict[str, Any]) -> list[dict[str, Any]]:
    package = f"computedeck-{plugin}"
    if release["info"]["name"] != package or release["info"]["version"] != version:
        raise ValueError("PyPI returned a different project or version")
    wheels = [file for file in release["urls"] if file["packagetype"] == "bdist_wheel"]
    if not wheels or any(file.get("yanked") for file in wheels):
        raise ValueError("The release must have a non-yanked wheel")
    hashes = [file["digests"]["sha256"] for file in wheels]
    if any(not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in hashes):
        raise ValueError("PyPI did not provide valid wheel digests")
    project = tomllib.loads((ROOT / plugin / "pyproject.toml").read_text())["project"]
    definitions = {
        "proxy": (
            "Proxy diagnostics",
            "代理诊断",
            "Read proxy configuration and OS networking state",
            "读取代理配置和系统网络状态",
        ),
        "egress": (
            "Egress test",
            "出口测速",
            "Request https://checkip.amazonaws.com/ and authenticate to configured "
            "IP SOCKS5 upstreams on demand",
            "按需访问 https://checkip.amazonaws.com/ 并向已配置的 IP SOCKS5 上游认证",
        ),
        "shell-credentials": (
            "Shell credentials",
            "Shell 凭据",
            "Read environment variables, credentials.env and literal assignments in ~/.zshrc",
            "读取环境变量、credentials.env 和 ~/.zshrc 中的字面量赋值",
        ),
    }
    entries = []
    for name in project["entry-points"]["computedeck.plugins"]:
        en, zh, permission_en, permission_zh = definitions[name]
        entries.append(
            {
                "name": name,
                "display_name": {"en": en, "zh-CN": zh},
                "version": version,
                "source": {
                    "type": "pypi",
                    "package": package,
                    "version": version,
                    "sha256": hashes,
                },
                "package": package,
                "requires": ">=0.3,<0.4",
                "license": "Apache-2.0",
                "permissions": [{"en": permission_en, "zh-CN": permission_zh}],
            }
        )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin", choices=["network", "shell-credentials"])
    parser.add_argument("version")
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        raise ValueError("The production catalog only accepts stable versions")
    url = f"https://pypi.org/pypi/computedeck-{args.plugin}/{args.version}/json"
    with urllib.request.urlopen(url, timeout=30) as response:
        release = json.load(response)
    entries = catalog_entries(args.plugin, args.version, release)
    path = ROOT / "computedeck-marketplace.json"
    catalog = json.loads(path.read_text())
    names = {entry["name"] for entry in entries}
    catalog["plugins"] = [
        entry for entry in catalog["plugins"] if entry["name"] not in names
    ] + entries
    path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
