from __future__ import annotations

from pathlib import Path

import pytest

from conftest import authority_kwargs, materialization_kwargs
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.transaction import materialize_synthetic
from quant_replay_system.accepted_lineage_registry.verification import ENTRY_FILES, verify_entry


def _materialize(root: Path, material, **kwargs):
    return materialize_synthetic(
        root,
        **materialization_kwargs(material),
        materialization_authorization_id="SYNTHETIC-AUTH-001",
        operation_id="transaction-test",
        **kwargs,
    )


def test_successful_synthetic_materialization_creates_exact_five_file_entry(synthetic_root, synthetic_material) -> None:
    result = _materialize(synthetic_root, synthetic_material)
    target = synthetic_root / "entries" / result.subject_key / result.receipt_key
    assert result.classification == "NEW_ENTRY_MATERIALIZED_SUCCESSFULLY"
    assert result.entry_created is True
    assert result.entry_verified is True
    assert result.materialization_verified is True
    assert result.entry_verification_completed is True
    assert result.derived_index_completed is True
    assert sorted(path.name for path in target.iterdir()) == sorted(ENTRY_FILES)
    assert verify_entry(
        synthetic_root,
        result.subject_key,
        result.receipt_key,
        subject_packet_path=synthetic_material["subject_packet_path"],
        subject_artifact_root=synthetic_material["subject_artifact_root"],
        **authority_kwargs(synthetic_material),
    )["status"] == "PASS"


@pytest.mark.parametrize("point", ["after_stage_created", "after_immutable_files", "after_manifest", "after_seal", "before_rename"])
def test_pre_rename_failure_leaves_no_authoritative_entry(point: str, synthetic_root, synthetic_material) -> None:
    with pytest.raises(RegistryError) as caught:
        _materialize(synthetic_root, synthetic_material, failure_injection=point)
    assert caught.value.classification == "ATOMIC_WRITE_FAILED_NO_AUTHORITATIVE_ENTRY_CREATED"
    assert not any((synthetic_root / "entries").rglob("receipt_key"))
    assert list((synthetic_root / ".staging").iterdir()) == []


def test_input_mutation_before_rename_stops_and_cleans_stage(synthetic_root, synthetic_material) -> None:
    with pytest.raises(RegistryError) as caught:
        _materialize(synthetic_root, synthetic_material, failure_injection="mutate_human_payload_before_rename")
    assert caught.value.classification == "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP"
    assert list((synthetic_root / ".staging").iterdir()) == []


def test_post_rename_index_failure_preserves_valid_entry_and_marks_stale(synthetic_root, synthetic_material) -> None:
    result = _materialize(synthetic_root, synthetic_material, failure_injection="index_regeneration")
    assert result.classification == "DERIVED_INDEX_REGENERATION_FAILED_ENTRY_VERIFIED_INDEX_STALE"
    assert result.entry_created is True
    assert result.entry_verified is True
    assert result.materialization_verified is False
    assert result.entry_verification_passed is True
    assert result.derived_index_passed is False
    assert result.derived_index_status == "STALE"
    assert verify_entry(synthetic_root, result.subject_key, result.receipt_key, **authority_kwargs(synthetic_material))["status"] == "PASS"
    assert (synthetic_root / "derived" / "registry_index_stale.json").exists()


def test_materialization_never_modifies_caller_bytes(synthetic_root, synthetic_material) -> None:
    before = {key: bytes(synthetic_material[key]) for key in ("payload_bytes", "manifest_bytes", "receipt_bytes")}
    _materialize(synthetic_root, synthetic_material)
    assert {key: synthetic_material[key] for key in before} == before


def test_live_named_root_is_rejected(tmp_path, synthetic_material) -> None:
    live = synthetic_material["approved_admin_root"] / "accepted_lineage_registry_v0_1"
    kwargs = materialization_kwargs(synthetic_material)
    kwargs["expected_registry_root"] = live
    with pytest.raises(RegistryError) as caught:
        materialize_synthetic(
            live,
            **kwargs,
            materialization_authorization_id="SYNTHETIC-AUTH-001",
        )
    assert caught.value.classification == "LIVE_REGISTRY_MODE_NOT_AUTHORIZED_STOP"
    assert not live.exists()
