from functools import partialmethod
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def without_api_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Plugin tests exercise routes behind the core's token check, in a scratch data dir."""
    monkeypatch.setattr(
        TestClient, "__init__", partialmethod(TestClient.__init__, base_url="http://127.0.0.1")
    )
    monkeypatch.setenv("COMPUTEDECK_AUTH", "off")
    monkeypatch.setenv("COMPUTEDECK_DATA_DIR", str(tmp_path / "default-data"))
