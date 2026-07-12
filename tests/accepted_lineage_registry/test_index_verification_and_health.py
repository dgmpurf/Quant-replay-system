from __future__ import annotations

from quant_replay_system.accepted_lineage_registry.health import registry_health
from quant_replay_system.accepted_lineage_registry.index import mark_index_stale, regenerate_index, verify_index
import pytest

from conftest import authority_kwargs
from quant_replay_system.accepted_lineage_registry.locking import RegistryWriteLock
from quant_replay_system.accepted_lineage_registry.models import RegistryError


def test_index_is_deterministic_and_verified(materialized_entry) -> None:
    root, _, _ = materialized_entry
    first = (root / "derived" / "registry_index.jsonl").read_bytes()
    result = regenerate_index(root, **authority_kwargs(materialized_entry[1]))
    second = (root / "derived" / "registry_index.jsonl").read_bytes()
    assert result["status"] == "PASS"
    assert first == second
    assert verify_index(root, **authority_kwargs(materialized_entry[1]))["status"] == "PASS"


def test_standalone_index_rebuild_obeys_single_writer_lock(materialized_entry) -> None:
    root, material, _ = materialized_entry
    lock = RegistryWriteLock(
        root,
        "synthetic-test",
        "held-lock",
        material["approved_admin_root"],
        material["repository_root"],
        expected_registry_root=root,
        timeout_seconds=0,
    )
    lock.acquire()
    try:
        with pytest.raises(RegistryError) as caught:
            regenerate_index(root, lock_timeout_seconds=0, **authority_kwargs(material))
        assert caught.value.classification == "REGISTRY_WRITE_LOCK_TIMEOUT_STOP"
    finally:
        lock.release()


def test_stale_index_is_visible_in_health(materialized_entry) -> None:
    root, material, _ = materialized_entry
    mark_index_stale(root, "SYNTHETIC_INJECTED_STALE", **authority_kwargs(material))
    assert verify_index(root, **authority_kwargs(material))["status"] == "STALE"
    health = registry_health(root, **authority_kwargs(material))
    assert health.stale_index_status is True
    assert health.derived_index_status == "STALE"


def test_orphan_temporary_directory_is_visible(materialized_entry) -> None:
    root, material, _ = materialized_entry
    (root / ".staging" / ".tmp-orphan").mkdir()
    health = registry_health(root, **authority_kwargs(material))
    assert health.orphan_temporary_directories == 1
    assert "ORPHAN_TEMPORARY_DIRECTORIES_PRESENT" in health.path_safety_warnings


def test_lock_status_is_visible_in_health(materialized_entry) -> None:
    root, material, _ = materialized_entry
    lock = RegistryWriteLock(
        root,
        "synthetic-health",
        "health-lock",
        material["approved_admin_root"],
        material["repository_root"],
        expected_registry_root=root,
        timeout_seconds=0,
    )
    lock.acquire()
    try:
        assert registry_health(root, **authority_kwargs(material)).lock_status == "LOCKED"
    finally:
        lock.release()
    assert registry_health(root, **authority_kwargs(material)).lock_status == "UNLOCKED"


def test_platform_limitations_are_explicit(materialized_entry) -> None:
    root, material, _ = materialized_entry
    health = registry_health(root, **authority_kwargs(material))
    assert isinstance(health.platform_limitations, tuple)
    if health.platform_limitations:
        assert all(item.startswith("PLATFORM_LIMITATION") for item in health.platform_limitations)


def test_health_contains_no_absolute_root_path(materialized_entry) -> None:
    root, material, _ = materialized_entry
    payload = registry_health(root, **authority_kwargs(material)).to_dict()
    assert str(root) not in str(payload)
    assert payload["registry_mode"] == "SYNTHETIC_FIXTURE_ONLY_NOT_A_PILOT"
