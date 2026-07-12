from __future__ import annotations

from pathlib import Path

import pytest

from conftest import authority_kwargs
from quant_replay_system.accepted_lineage_registry.index import (
    TRANSACTION_MARKER_FILENAME,
    regenerate_index,
    verify_index,
)
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.verification import verify_entry


@pytest.mark.parametrize(
    "failure_point",
    [
        "after_index_file_write",
        "after_manifest_file_write",
        "before_derived_activation",
        "after_first_authoritative_derived_replacement",
        "before_stale_marker_cleanup",
    ],
)
def test_derived_index_interruption_is_detectable_and_recoverable(materialized_entry, failure_point: str) -> None:
    root, material, result = materialized_entry
    authority = authority_kwargs(material)
    with pytest.raises(RegistryError) as caught:
        regenerate_index(root, failure_injection=failure_point, **authority)
    assert caught.value.classification == "DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED"
    assert (root / "derived" / TRANSACTION_MARKER_FILENAME).is_file()
    assert verify_index(root, **authority) == {
        "status": "STALE_OR_REBUILD_REQUIRED",
        "classification": "DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED",
    }
    assert verify_entry(root, result.subject_key, result.receipt_key, **authority)["status"] == "PASS"
    recovered = regenerate_index(root, **authority)
    assert recovered["status"] == "PASS"
    assert recovered["classification"] == "DERIVED_INDEX_RECOVERY_COMPLETED"
    assert verify_index(root, **authority)["status"] == "PASS"
    assert not (root / "derived" / TRANSACTION_MARKER_FILENAME).exists()


def test_failure_before_transaction_marker_preserves_valid_index(materialized_entry) -> None:
    root, material, _ = materialized_entry
    authority = authority_kwargs(material)
    before = (root / "derived" / "registry_index.jsonl").read_bytes()
    with pytest.raises(RegistryError) as caught:
        regenerate_index(root, failure_injection="before_derived_transaction_marker", **authority)
    assert caught.value.classification == "DERIVED_INDEX_REGENERATION_FAILED_ENTRY_REMAINS_VALID_INDEX_STALE"
    assert not (root / "derived" / TRANSACTION_MARKER_FILENAME).exists()
    assert verify_index(root, **authority)["status"] == "PASS"
    assert (root / "derived" / "registry_index.jsonl").read_bytes() == before


def test_recovery_interruption_remains_bounded_until_success(materialized_entry) -> None:
    root, material, _ = materialized_entry
    authority = authority_kwargs(material)
    with pytest.raises(RegistryError):
        regenerate_index(root, failure_injection="after_index_file_write", **authority)
    with pytest.raises(RegistryError) as caught:
        regenerate_index(root, failure_injection="during_rebuild", **authority)
    assert caught.value.classification == "DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED"
    assert verify_index(root, **authority)["status"] == "STALE_OR_REBUILD_REQUIRED"
    assert regenerate_index(root, **authority)["classification"] == "DERIVED_INDEX_RECOVERY_COMPLETED"


def test_recovered_index_bytes_are_deterministic(materialized_entry) -> None:
    root, material, _ = materialized_entry
    authority = authority_kwargs(material)
    expected_index = (root / "derived" / "registry_index.jsonl").read_bytes()
    expected_manifest = (root / "derived" / "registry_index_manifest.json").read_bytes()
    with pytest.raises(RegistryError):
        regenerate_index(root, failure_injection="after_first_authoritative_derived_replacement", **authority)
    regenerate_index(root, **authority)
    assert (root / "derived" / "registry_index.jsonl").read_bytes() == expected_index
    assert (root / "derived" / "registry_index_manifest.json").read_bytes() == expected_manifest
