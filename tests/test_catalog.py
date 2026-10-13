import importlib.util
from pathlib import Path

import pytest
from computedeck.marketplace import Catalog

_spec = importlib.util.spec_from_file_location(
    "update_catalog", Path(__file__).resolve().parents[1] / "scripts/update_catalog.py"
)
assert _spec and _spec.loader
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)


def release(**kwargs):
    return {
        "info": {"name": "computedeck-network", "version": "0.3.0"},
        "urls": [
            {
                "packagetype": "bdist_wheel",
                "yanked": False,
                "digests": {"sha256": "a" * 64},
                **kwargs,
            }
        ],
    }


def test_network_wheel_updates_both_tools():
    entries = _module.catalog_entries("network", "0.3.0", release())
    assert {e["name"] for e in entries} == {"proxy", "egress"}
    catalog = Catalog.model_validate({"name": "official", "plugins": entries})
    assert all(e.source.sha256 == ["a" * 64] for e in catalog.plugins)
    assert all(e.permissions for e in catalog.plugins)


@pytest.mark.parametrize(
    "changes", [{"yanked": True}, {"packagetype": "sdist"}, {"digests": {"sha256": ""}}]
)
def test_no_catalog_entry_without_an_actual_wheel(changes):
    with pytest.raises(ValueError):
        _module.catalog_entries("network", "0.3.0", release(**changes))


def test_wrong_version_is_rejected():
    with pytest.raises(ValueError):
        _module.catalog_entries("network", "0.4.0", release())
