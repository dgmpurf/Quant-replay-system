from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import authority_kwargs, materialization_kwargs
from quant_replay_system.accepted_lineage_registry import transaction
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.path_safety import capture_path_snapshot, revalidate_path_snapshot
from quant_replay_system.accepted_lineage_registry.transaction import initialize_synthetic_registry, materialize_synthetic


def _materialize(root, material, **kwargs):
    return materialize_synthetic(
        root,
        **materialization_kwargs(material),
        materialization_authorization_id="SYNTHETIC-FAILURE-AUTH-001",
        operation_id="failure-injection-test",
        **kwargs,
    )


def test_filesystem_device_mismatch_stops_before_entry_write(synthetic_root, synthetic_material, monkeypatch) -> None:
    monkeypatch.setattr(transaction, "same_filesystem", lambda left, right: False)
    with pytest.raises(RegistryError, match="filesystems differ") as caught:
        _materialize(synthetic_root, synthetic_material)
    assert caught.value.classification == "PATH_KEY_DERIVATION_OR_VALIDATION_STOP"
    assert not any((synthetic_root / "entries").rglob("entry_manifest.json"))


def test_toctou_snapshot_detects_root_identity_change(synthetic_root, synthetic_material, monkeypatch) -> None:
    root = initialize_synthetic_registry(synthetic_root, **authority_kwargs(synthetic_material))
    snapshot = capture_path_snapshot(root)
    from quant_replay_system.accepted_lineage_registry import path_safety

    original_capture = path_safety.capture_path_snapshot

    def changed(path):
        current = original_capture(path)
        signatures = list(current.signatures)
        first = signatures[0]
        signatures[0] = (first[0], first[1] + 1, first[2], first[3])
        return type(current)(current.logical_root_name, tuple(signatures), current.platform_limitations)

    monkeypatch.setattr(path_safety, "capture_path_snapshot", changed)
    with pytest.raises(RegistryError, match="TOCTOU"):
        path_safety.revalidate_path_snapshot(root, snapshot)


def test_release_after_safe_pre_rename_failure(synthetic_root, synthetic_material) -> None:
    with pytest.raises(RegistryError):
        _materialize(synthetic_root, synthetic_material, failure_injection="before_rename")
    assert not (synthetic_root / ".registry-write.lock").exists()


def test_no_silent_platform_skip_contract_is_represented(materialized_entry) -> None:
    root, _, _ = materialized_entry
    from quant_replay_system.accepted_lineage_registry.health import registry_health

    _, material, _ = materialized_entry
    health = registry_health(root, **authority_kwargs(material))
    assert health.root_safety == "PASS"
    assert all(item.startswith("PLATFORM_LIMITATION") for item in health.platform_limitations)


def test_authoritative_files_have_single_link_count(materialized_entry) -> None:
    root, _, result = materialized_entry
    entry = root / "entries" / result.subject_key / result.receipt_key
    for path in entry.iterdir():
        assert path.is_file()
        assert os.stat(path).st_nlink == 1
