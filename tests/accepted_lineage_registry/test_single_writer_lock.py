from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from conftest import authority_kwargs
from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes
from quant_replay_system.accepted_lineage_registry.locking import LOCK_FILENAME, RegistryWriteLock, inspect_lock
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.transaction import initialize_synthetic_registry


def _lock(root, material, operator, operation, **kwargs):
    return RegistryWriteLock(
        root,
        operator,
        operation,
        material["approved_admin_root"],
        material["repository_root"],
        expected_registry_root=root,
        **kwargs,
    )


def test_single_writer_acquires_and_releases(synthetic_root, synthetic_material) -> None:
    root = initialize_synthetic_registry(synthetic_root, **authority_kwargs(synthetic_material))
    with _lock(root, synthetic_material, "synthetic-operator", "operation-1", timeout_seconds=0):
        assert inspect_lock(root, **authority_kwargs(synthetic_material)) == "LOCKED"
    assert inspect_lock(root, **authority_kwargs(synthetic_material)) == "UNLOCKED"


@pytest.mark.parametrize("second_operation", ["same-receipt-writer", "different-receipt-writer"])
def test_concurrent_writer_times_out(second_operation: str, synthetic_root, synthetic_material) -> None:
    root = initialize_synthetic_registry(synthetic_root, **authority_kwargs(synthetic_material))
    first = _lock(root, synthetic_material, "first", "operation-1", timeout_seconds=0)
    first.acquire()
    try:
        second = _lock(root, synthetic_material, "second", second_operation, timeout_seconds=0, stale_after_seconds=3600)
        with pytest.raises(RegistryError) as caught:
            second.acquire()
        assert caught.value.classification == "REGISTRY_WRITE_LOCK_TIMEOUT_STOP"
    finally:
        first.release()


def test_stale_lock_requires_human_review_and_is_not_deleted(synthetic_root, synthetic_material) -> None:
    root = initialize_synthetic_registry(synthetic_root, **authority_kwargs(synthetic_material))
    lock_path = root / LOCK_FILENAME
    lock_path.write_bytes(
        canonical_json_bytes(
            {
                "created_at": "2000-01-01T00:00:00Z",
                "lock_schema_version": "accepted-lineage-registry-write-lock-v0.1",
                "operation_identifier": "old-operation",
                "process_identifier": 1,
                "synthetic_operator_alias": "old-synthetic-writer",
            }
        )
    )
    lock = _lock(root, synthetic_material, "new", "new-operation", timeout_seconds=0, stale_after_seconds=1)
    with pytest.raises(RegistryError) as caught:
        lock.acquire()
    assert caught.value.classification == "REGISTRY_STALE_LOCK_DETECTED_HUMAN_REVIEW_REQUIRED"
    assert lock_path.exists()


def test_lock_metadata_contains_no_absolute_path(synthetic_root, synthetic_material) -> None:
    root = initialize_synthetic_registry(synthetic_root, **authority_kwargs(synthetic_material))
    lock = _lock(root, synthetic_material, "synthetic", "operation-1", timeout_seconds=0)
    lock.acquire()
    try:
        text = lock.lock_path.read_text(encoding="utf-8")
        assert str(root) not in text
        assert "operation-1" in text
    finally:
        lock.release()
