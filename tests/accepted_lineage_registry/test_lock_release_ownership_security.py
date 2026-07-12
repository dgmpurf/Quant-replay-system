from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from conftest import authority_kwargs
from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes
from quant_replay_system.accepted_lineage_registry.locking import RegistryWriteLock
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.transaction import initialize_synthetic_registry


def _lock(root: Path, material, operation: str = "lock-security-operation") -> RegistryWriteLock:
    return RegistryWriteLock(
        root,
        "synthetic-security-operator",
        operation,
        material["approved_admin_root"],
        material["repository_root"],
        expected_registry_root=root,
        timeout_seconds=0,
    )


def _cleanup(*paths: Path) -> None:
    for path in paths:
        if path.exists() or path.is_symlink():
            path.unlink()


def test_lock_replacement_before_release_is_preserved_for_review(synthetic_material) -> None:
    root = initialize_synthetic_registry(synthetic_material["registry_root"], **authority_kwargs(synthetic_material))
    lock = _lock(root, synthetic_material)
    lock.acquire()
    original = root / ".original-lock-for-test"
    os.replace(lock.lock_path, original)
    replacement_bytes = canonical_json_bytes(
        {
            "created_at": "2026-01-02T03:04:05Z",
            "lock_schema_version": "accepted-lineage-registry-write-lock-v0.1",
            "operation_identifier": "replacement-operation",
            "operation_nonce": "0" * 64,
            "process_identifier": 1,
            "synthetic_operator_alias": "replacement",
        }
    )
    lock.lock_path.write_bytes(replacement_bytes)
    try:
        with pytest.raises(RegistryError) as caught:
            lock.release()
        assert caught.value.classification == "REGISTRY_WRITE_LOCK_RELEASE_FAILED_HEALTH_WARNING"
        assert lock.lock_path.read_bytes() == replacement_bytes
        assert str(root) not in str(caught.value.to_dict())
    finally:
        _cleanup(lock.lock_path, original)


def test_lock_content_replacement_before_release_is_not_unlinked(synthetic_material) -> None:
    root = initialize_synthetic_registry(synthetic_material["registry_root"], **authority_kwargs(synthetic_material))
    lock = _lock(root, synthetic_material)
    lock.acquire()
    data = json.loads(lock.lock_path.read_text(encoding="utf-8"))
    data["synthetic_operator_alias"] = "changed-synthetic-operator"
    changed = canonical_json_bytes(data)
    lock.lock_path.write_bytes(changed)
    try:
        with pytest.raises(RegistryError) as caught:
            lock.release()
        assert caught.value.classification == "REGISTRY_WRITE_LOCK_RELEASE_FAILED_HEALTH_WARNING"
        assert lock.lock_path.read_bytes() == changed
    finally:
        _cleanup(lock.lock_path)


def test_lock_nonce_mismatch_is_not_unlinked(synthetic_material) -> None:
    root = initialize_synthetic_registry(synthetic_material["registry_root"], **authority_kwargs(synthetic_material))
    lock = _lock(root, synthetic_material)
    lock.acquire()
    lock._operation_nonce = "f" * 64
    try:
        with pytest.raises(RegistryError) as caught:
            lock.release()
        assert caught.value.classification == "REGISTRY_WRITE_LOCK_RELEASE_FAILED_HEALTH_WARNING"
        assert lock.lock_path.exists()
    finally:
        _cleanup(lock.lock_path)


def test_lock_hardlink_count_mismatch_is_not_unlinked(synthetic_material) -> None:
    root = initialize_synthetic_registry(synthetic_material["registry_root"], **authority_kwargs(synthetic_material))
    lock = _lock(root, synthetic_material)
    lock.acquire()
    second_link = root / ".lock-hardlink-for-test"
    os.link(lock.lock_path, second_link)
    try:
        with pytest.raises(RegistryError) as caught:
            lock.release()
        assert caught.value.classification == "REGISTRY_WRITE_LOCK_RELEASE_FAILED_HEALTH_WARNING"
        assert lock.lock_path.exists() and second_link.exists()
    finally:
        _cleanup(lock.lock_path, second_link)
