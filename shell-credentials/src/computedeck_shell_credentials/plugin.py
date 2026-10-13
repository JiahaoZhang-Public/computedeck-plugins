"""``shell:NAME`` credentials: a literal assignment in a private file or ~/.zshrc.

Lets a service started from Finder or launchd use the API keys exported in the
user's shell profile, without running shell code.
"""

import os
import re
import shlex
from pathlib import Path

from computedeck import paths
from computedeck.sdk import Plugin, PluginContext

_SHELL_KEYS = {"Runpod_API_Key", "GPUHub_API_Key"}


def credential_value(env_name: str) -> str | None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env_name):
        raise ValueError("Invalid credential environment variable name")
    value = os.environ.get(env_name)
    if value:
        return value
    if env_name not in _SHELL_KEYS:
        return None
    private_file = paths.data_dir() / "credentials.env"
    if private_file.is_file():
        if private_file.stat().st_mode & 0o077:
            raise ValueError("credentials.env must be private to its owner (chmod 600)")
        value = _literal_value(private_file, env_name)
        if value:
            return value
    return _literal_value(Path.home() / ".zshrc", env_name)


def _literal_value(path: Path, env_name: str) -> str | None:
    if not path.is_file():
        return None
    # Read only exact assignments to the allowlisted keys. shlex parses quotes;
    # it does not expand variables, run commands, or source the startup file.
    assignment = re.compile(rf"^\s*(?:export\s+)?{re.escape(env_name)}=")
    result = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not assignment.match(line):
            continue
        lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|<>()")
        lexer.whitespace_split = True
        try:
            parts = list(lexer)
        except ValueError:
            raise ValueError(
                f"Credential assignment in {path.name} must be a single literal"
            ) from None
        if parts and parts[0] == "export":
            parts.pop(0)
        if len(parts) != 1 or not parts[0].startswith(env_name + "="):
            raise ValueError(f"Credential assignment in {path.name} must be a single literal")
        result = parts[0].split("=", 1)[1]
        if any(char in result for char in ("$", "`", "\n", "\r")):
            raise ValueError(f"Credential assignment in {path.name} cannot use shell expansion")
    return result or None


def setup(ctx: PluginContext) -> None:
    ctx.credential_scheme("shell", credential_value, r"[A-Za-z_][A-Za-z0-9_]*")


plugin = Plugin(
    requires=">=0.3,<0.4",
    icon="key",
    id="shell-credentials",
    setup=setup,
    name={"en": "Shell credentials", "zh-CN": "Shell 凭据"},
    description={
        "en": "shell:NAME references: API keys assigned in a private file or ~/.zshrc.",
        "zh-CN": "shell:变量名 引用：读取私有文件或 ~/.zshrc 中赋值的 API Key。",
    },
    permissions=(
        {
            "en": "reads ~/.zshrc and a private credentials file",
            "zh-CN": "读取 ~/.zshrc 和私有凭据文件",
        },
    ),
)
