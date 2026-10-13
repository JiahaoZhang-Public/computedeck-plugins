from pathlib import Path

import pytest
from computedeck import credentials, paths
from computedeck import plugins as plugin_host
from computedeck.errors import SourceError
from computedeck_shell_credentials import plugin as shell_credentials
from computedeck_shell_credentials.plugin import credential_value


@pytest.fixture(autouse=True)
def clean_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    for name in ("Runpod_API_Key", "GPUHub_API_Key", "UNRELATED_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_credentials_read_only_allowed_literal_assignments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMPUTEDECK_DATA_DIR", str(tmp_path / "data"))
    marker = tmp_path / "never-created"
    (tmp_path / ".zshrc").write_text(
        f"touch '{marker}'\n"
        "export Runpod_API_Key='runpod-literal' # a comment\n"
        'GPUHub_API_Key="gpuhub-literal"\n'
        "UNRELATED_API_KEY=unrelated-private-value\n"
    )
    assert credential_value("Runpod_API_Key") == "runpod-literal"
    assert credential_value("GPUHub_API_Key") == "gpuhub-literal"
    assert credential_value("UNRELATED_API_KEY") is None
    assert not marker.exists()
    monkeypatch.setenv("Runpod_API_Key", "environment-override")
    assert credential_value("Runpod_API_Key") == "environment-override"


def test_private_app_credentials_precedence_and_allowed_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_dir = tmp_path / "App Data"
    data_dir.mkdir()
    monkeypatch.setenv("COMPUTEDECK_DATA_DIR", str(data_dir))
    (tmp_path / ".zshrc").write_text("Runpod_API_Key=shell-token\nGPUHub_API_Key=shell-gpuhub\n")
    private_file = data_dir / "credentials.env"
    private_file.write_text("Runpod_API_Key='app-token'\nUNRELATED_API_KEY=private-value\n")
    private_file.chmod(0o600)
    assert credential_value("Runpod_API_Key") == "app-token"
    assert credential_value("GPUHub_API_Key") == "shell-gpuhub"
    assert credential_value("UNRELATED_API_KEY") is None
    monkeypatch.setenv("Runpod_API_Key", "environment-token")
    assert credential_value("Runpod_API_Key") == "environment-token"


def test_private_credentials_default_path_and_permissions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The default data directory comes from the core, which derives it from $HOME.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("COMPUTEDECK_DATA_DIR", raising=False)
    data_dir = paths.data_dir()
    assert data_dir.is_relative_to(tmp_path)
    data_dir.mkdir(parents=True)
    private_file = data_dir / "credentials.env"
    private_file.write_text("Runpod_API_Key=private-token\n")
    private_file.chmod(0o644)
    with pytest.raises(ValueError, match="chmod 600"):
        credential_value("Runpod_API_Key")
    private_file.chmod(0o600)
    assert credential_value("Runpod_API_Key") == "private-token"
    private_file.write_text('Runpod_API_Key="$(touch /tmp/never-execute)"\n')
    with pytest.raises(ValueError, match="shell expansion"):
        credential_value("Runpod_API_Key")


@pytest.mark.parametrize(
    "assignment",
    [
        'export Runpod_API_Key="$(touch /tmp/never-run)"',
        "export Runpod_API_Key=secret; touch /tmp/never-run",
        "export Runpod_API_Key=`cat private`",
        'export Runpod_API_Key="${PRIVATE_KEY}"',
        "export Runpod_API_Key='unterminated-secret",
    ],
)
def test_credentials_reject_shell_expressions_without_exposing_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    assignment: str,
) -> None:
    monkeypatch.setenv("COMPUTEDECK_DATA_DIR", str(tmp_path / "data"))
    (tmp_path / ".zshrc").write_text(assignment)
    with pytest.raises(ValueError) as error:
        credential_value("Runpod_API_Key")
    assert "secret" not in str(error.value)
    assert "private" not in str(error.value)


def test_plugin_registers_shell_credential_scheme(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolvers = dict(credentials._RESOLVERS)
    resolvers.pop("shell", None)
    monkeypatch.setattr(credentials, "_RESOLVERS", resolvers)
    with pytest.raises(SourceError):
        credentials.resolve("shell:Runpod_API_Key")
    plugin_host.load([shell_credentials.plugin], plugin_host.Runtime(tmp_path))
    assert "shell" in credentials.schemes()
    monkeypatch.setenv("COMPUTEDECK_DATA_DIR", str(tmp_path / "data"))
    (tmp_path / ".zshrc").write_text("export Runpod_API_Key='runpod-literal'\n")
    assert credentials.resolve("shell:Runpod_API_Key") == "runpod-literal"
    assert credentials.resolve("shell:UNRELATED_API_KEY") is None
    monkeypatch.setenv("Runpod_API_Key", "environment-token")
    assert credentials.resolve("shell:Runpod_API_Key") == "environment-token"
    for reference in ("shell:", "shell:bad-name", "shell:1_KEY"):
        with pytest.raises(SourceError):
            credentials.validate_reference(reference)
