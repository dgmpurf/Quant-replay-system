from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import authority_kwargs, materialization_kwargs
from quant_replay_system.accepted_lineage_registry import transaction
from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes, sha256_bytes
from quant_replay_system.accepted_lineage_registry.health import registry_health
from quant_replay_system.accepted_lineage_registry.index import INDEX_ROW_FIELDS, regenerate_index, verify_index
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.path_safety import derive_receipt_key, derive_subject_key
from quant_replay_system.accepted_lineage_registry.transaction import materialize_synthetic
from quant_replay_system.accepted_lineage_registry.verification import preflight_next_task, verify_entry


def _write_json(path: Path, value: dict) -> None:
    path.write_bytes(canonical_json_bytes(value))


def _entry(root: Path, result) -> Path:
    return root / "entries" / result.subject_key / result.receipt_key


def _rebind_runtime_files(entry: Path, *, subject_key: str, receipt_key: str) -> None:
    manifest_path = entry / "entry_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["subject_key"] = subject_key
    manifest["receipt_key"] = receipt_key
    manifest["entry_relative_path"] = f"entries/{subject_key}/{receipt_key}/"
    _write_json(manifest_path, manifest)
    seal_path = entry / "entry_seal.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["subject_key"] = subject_key
    seal["receipt_key"] = receipt_key
    seal["entry_manifest_sha256"] = sha256_bytes(manifest_path.read_bytes())
    _write_json(seal_path, seal)


def _relocate_entry(root: Path, result, *, subject_key: str, receipt_key: str) -> Path:
    original = _entry(root, result)
    original_subject_parent = original.parent
    subject_parent = root / "entries" / subject_key
    subject_parent.mkdir(exist_ok=True)
    relocated = subject_parent / receipt_key
    original.rename(relocated)
    if original_subject_parent != subject_parent:
        original_subject_parent.rmdir()
    _rebind_runtime_files(relocated, subject_key=subject_key, receipt_key=receipt_key)
    return relocated


def _tamper_index(root: Path, *, updates: dict | None = None, remove: str | None = None, extra: dict | None = None) -> None:
    index_path = root / "derived" / "registry_index.jsonl"
    manifest_path = root / "derived" / "registry_index_manifest.json"
    row = json.loads(index_path.read_text(encoding="utf-8"))
    row.update(updates or {})
    if remove is not None:
        row.pop(remove)
    row.update(extra or {})
    index_bytes = canonical_json_bytes(row)
    index_path.write_bytes(index_bytes)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["registry_index_sha256"] = sha256_bytes(index_bytes)
    _write_json(manifest_path, manifest)


def _materialize(root: Path, material, **kwargs):
    return materialize_synthetic(
        root,
        **materialization_kwargs(material),
        materialization_authorization_id="SYNTHETIC-TRUTHFULNESS-AUTH-001",
        operation_id="truthfulness-test",
        **kwargs,
    )


def test_valid_subject_and_receipt_binding_passes(materialized_entry) -> None:
    root, material, result = materialized_entry
    verified = verify_entry(root, result.subject_key, result.receipt_key, **authority_kwargs(material))
    assert verified["status"] == "PASS"
    assert result.subject_key == derive_subject_key(verified["subject_phase_id"])
    assert result.receipt_key == derive_receipt_key(verified["receipt_id"])


@pytest.mark.parametrize("component", ["subject", "receipt"])
def test_changed_directory_key_stops(component: str, materialized_entry) -> None:
    root, material, result = materialized_entry
    subject_key = derive_subject_key("SYNTHETIC-OTHER-SUBJECT") if component == "subject" else result.subject_key
    receipt_key = derive_receipt_key("SYNTHETIC-OTHER-RECEIPT") if component == "receipt" else result.receipt_key
    _relocate_entry(root, result, subject_key=subject_key, receipt_key=receipt_key)
    with pytest.raises(RegistryError) as caught:
        verify_entry(root, subject_key, receipt_key, **authority_kwargs(material))
    assert caught.value.classification == "LOGICAL_ID_OPAQUE_KEY_BINDING_MISMATCH_STOP"


@pytest.mark.parametrize("surface", ["manifest", "seal"])
def test_runtime_key_mismatch_stops(surface: str, materialized_entry) -> None:
    root, material, result = materialized_entry
    entry = _entry(root, result)
    path = entry / f"entry_{surface}.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["subject_key"] = derive_subject_key("SYNTHETIC-OTHER-SUBJECT")
    _write_json(path, value)
    if surface == "manifest":
        seal_path = entry / "entry_seal.json"
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
        seal["entry_manifest_sha256"] = sha256_bytes(path.read_bytes())
        _write_json(seal_path, seal)
    with pytest.raises(RegistryError) as caught:
        verify_entry(root, result.subject_key, result.receipt_key, **authority_kwargs(material))
    assert caught.value.classification == "LOGICAL_ID_OPAQUE_KEY_BINDING_MISMATCH_STOP"


def test_relocated_entry_is_rejected_by_all_consumers(materialized_entry) -> None:
    root, material, result = materialized_entry
    subject_key = derive_subject_key("SYNTHETIC-RELOCATED-SUBJECT")
    receipt_key = derive_receipt_key("SYNTHETIC-RELOCATED-RECEIPT")
    _relocate_entry(root, result, subject_key=subject_key, receipt_key=receipt_key)
    authority = authority_kwargs(material)
    with pytest.raises(RegistryError, match="Opaque entry keys"):
        verify_entry(root, subject_key, receipt_key, **authority)
    health = registry_health(root, **authority)
    assert health.entry_verification_status == "FAIL"
    assert "LOGICAL_ID_OPAQUE_KEY_BINDING_MISMATCH_STOP" in health.path_safety_warnings
    with pytest.raises(RegistryError) as rebuild_error:
        regenerate_index(root, **authority)
    assert rebuild_error.value.classification == "LOGICAL_ID_OPAQUE_KEY_BINDING_MISMATCH_STOP"
    with pytest.raises(RegistryError) as predecessor_error:
        preflight_next_task(root, subject_key, receipt_key, current_task_approval_id="CURRENT-APPROVAL", **authority)
    assert predecessor_error.value.classification == "LOGICAL_ID_OPAQUE_KEY_BINDING_MISMATCH_STOP"


def test_valid_index_row_has_exact_semantic_schema(materialized_entry) -> None:
    root, material, _ = materialized_entry
    row = json.loads((root / "derived" / "registry_index.jsonl").read_text(encoding="utf-8"))
    assert set(row) == INDEX_ROW_FIELDS
    assert verify_index(root, **authority_kwargs(material))["status"] == "PASS"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("subject_phase_id", "SYNTHETIC-TAMPERED-SUBJECT"),
        ("receipt_id", "SYNTHETIC-TAMPERED-RECEIPT"),
        ("review_status", "TAMPERED_STATUS"),
        ("accepted_classification", "TAMPERED_CLASSIFICATION"),
        ("registry_schema_version", "tampered-schema"),
        ("registry_policy_version", "tampered-policy"),
        ("entry_seal_sha256", "0" * 64),
    ],
)
def test_hash_consistent_semantic_tampering_stops(field: str, value: str, materialized_entry) -> None:
    root, material, _ = materialized_entry
    _tamper_index(root, updates={field: value})
    with pytest.raises(RegistryError) as caught:
        verify_index(root, **authority_kwargs(material))
    assert caught.value.classification == "DERIVED_INDEX_SEMANTIC_RECORD_MISMATCH_STOP"


@pytest.mark.parametrize("shape", ["missing", "unexpected"])
def test_index_row_schema_drift_stops(shape: str, materialized_entry) -> None:
    root, material, _ = materialized_entry
    if shape == "missing":
        _tamper_index(root, remove="review_status")
    else:
        _tamper_index(root, extra={"unexpected_semantic_field": "not-allowed"})
    with pytest.raises(RegistryError) as caught:
        verify_index(root, **authority_kwargs(material))
    assert caught.value.classification == "DERIVED_INDEX_SEMANTIC_RECORD_MISMATCH_STOP"


def test_rebuild_restores_authoritative_semantic_row(materialized_entry) -> None:
    root, material, _ = materialized_entry
    authority = authority_kwargs(material)
    _tamper_index(root, updates={"review_status": "TAMPERED_STATUS"})
    with pytest.raises(RegistryError):
        verify_index(root, **authority)
    rebuilt = regenerate_index(root, **authority)
    assert rebuilt["status"] == "PASS"
    assert verify_index(root, **authority)["status"] == "PASS"


@pytest.mark.parametrize("point", ["after_authoritative_rename", "before_entry_verification"])
def test_post_rename_exception_before_verification_is_truthful(point: str, synthetic_root, synthetic_material) -> None:
    result = _materialize(synthetic_root, synthetic_material, failure_injection=point)
    assert result.classification == "ENTRY_CREATED_VERIFICATION_INCOMPLETE_REVIEW_REQUIRED"
    assert result.authoritative_entry_created is True
    assert result.entry_verification_started is False
    assert result.entry_verification_completed is False
    assert result.entry_verified is False
    assert result.materialization_verified is False
    assert result.derived_index_attempted is False


def test_exception_during_verify_entry_is_truthful(monkeypatch, synthetic_root, synthetic_material) -> None:
    def fail_verify(*args, **kwargs):
        raise OSError("synthetic verification interruption")

    monkeypatch.setattr(transaction, "verify_entry", fail_verify)
    result = _materialize(synthetic_root, synthetic_material)
    assert result.classification == "ENTRY_VERIFICATION_FAILED_AFTER_AUTHORITATIVE_RENAME"
    assert result.entry_verification_started is True
    assert result.entry_verification_completed is False
    assert result.entry_verified is False
    assert result.materialization_verified is False


def test_non_pass_verify_entry_result_is_truthful(monkeypatch, synthetic_root, synthetic_material) -> None:
    monkeypatch.setattr(transaction, "verify_entry", lambda *args, **kwargs: {"status": "FAIL"})
    result = _materialize(synthetic_root, synthetic_material)
    assert result.classification == "ENTRY_VERIFICATION_FAILED_AFTER_AUTHORITATIVE_RENAME"
    assert result.entry_verification_started is True
    assert result.entry_verification_completed is True
    assert result.entry_verification_passed is False
    assert result.entry_verified is False
    assert result.materialization_verified is False


def test_verified_entry_with_index_failure_preserves_truthful_state(synthetic_root, synthetic_material) -> None:
    result = _materialize(synthetic_root, synthetic_material, failure_injection="index_regeneration")
    assert result.classification == "DERIVED_INDEX_REGENERATION_FAILED_ENTRY_VERIFIED_INDEX_STALE"
    assert result.entry_verified is True
    assert result.entry_verification_passed is True
    assert result.derived_index_attempted is True
    assert result.derived_index_completed is False
    assert result.derived_index_passed is False
    assert result.materialization_verified is False


def test_successful_entry_and_index_proofs_are_truthful(synthetic_root, synthetic_material) -> None:
    result = _materialize(synthetic_root, synthetic_material)
    assert result.classification == "NEW_ENTRY_MATERIALIZED_SUCCESSFULLY"
    assert result.authoritative_entry_created is True
    assert result.entry_verification_started is True
    assert result.entry_verification_completed is True
    assert result.entry_verification_passed is True
    assert result.entry_verified is True
    assert result.derived_index_attempted is True
    assert result.derived_index_completed is True
    assert result.derived_index_passed is True
    assert result.materialization_verified is True
