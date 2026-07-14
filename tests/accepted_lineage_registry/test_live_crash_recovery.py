from __future__ import annotations

import json
from pathlib import Path

import pytest

from quant_replay_system.accepted_lineage_registry.canonical import sha256_bytes
from quant_replay_system.accepted_lineage_registry.live_workflow import recover_live_accepted_lineage_index
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from test_live_materialization import (
    _initialized_case,
    _materialize,
    _tree_hashes,
)


@pytest.mark.parametrize(
    "crash_point,classification",
    [
        ("after_staging_creation", "LIVE_ENTRY_PRE_RENAME_WRITE_INCOMPLETE"),
        ("after_human_review_payload_write", "LIVE_ENTRY_PRE_RENAME_WRITE_INCOMPLETE"),
        ("after_subject_manifest_write", "LIVE_ENTRY_PRE_RENAME_WRITE_INCOMPLETE"),
        ("after_review_receipt_write", "LIVE_ENTRY_PRE_RENAME_WRITE_INCOMPLETE"),
        ("after_entry_manifest_write", "LIVE_ENTRY_PRE_RENAME_WRITE_INCOMPLETE"),
        ("after_entry_seal_write", "LIVE_ENTRY_PRE_RENAME_WRITE_INCOMPLETE"),
        ("immediately_before_authoritative_rename", "LIVE_ENTRY_COMMIT_NOT_ATTEMPTED"),
    ],
)
def test_pre_rename_crash_cleans_only_exact_stage_and_does_not_consume_authorization(
    tmp_path: Path,
    crash_point: str,
    classification: str,
) -> None:
    case = _initialized_case(tmp_path)
    with pytest.raises(RegistryError) as caught:
        _materialize(case, failure_injection=crash_point)
    assert caught.value.classification == classification
    root = Path(case["root"])
    assert list((root / ".staging").iterdir()) == []
    assert list((root / "entries").rglob("entry_manifest.json")) == []
    assert not (root / ".registry-write.lock").exists()


def test_ambiguous_rename_stops_without_cleanup_or_automatic_retry(tmp_path: Path) -> None:
    case = _initialized_case(tmp_path)
    with pytest.raises(RegistryError) as caught:
        _materialize(case, failure_injection="rename_result_ambiguous")
    assert caught.value.classification == "LIVE_WINDOWS_RENAME_RESULT_UNVERIFIED_STOP"
    root = Path(case["root"])
    entries = list((root / "entries").rglob("entry_manifest.json"))
    assert len(entries) == 1
    assert list((root / ".staging").iterdir()) == []
    assert (root / "derived/registry_index.jsonl").read_bytes() == b""


def test_proven_rename_before_verification_consumes_authorization_and_retains_entry(tmp_path: Path) -> None:
    case = _initialized_case(tmp_path)
    result = _materialize(case, failure_injection="immediately_after_proven_authoritative_rename")
    assert result["classification"] == "LIVE_ENTRY_CREATED_VERIFICATION_INCOMPLETE_REVIEW_REQUIRED"
    assert result["authorization_state"] == "CONSUMED_PENDING_HUMAN_LIVE_ENTRY_REVIEW"
    assert result["authorization_consumed"] is True
    assert result["entry_created"] is True
    assert result["entry_verified"] is False


def test_post_rename_verification_failure_never_rolls_back_authoritative_entry(tmp_path: Path) -> None:
    case = _initialized_case(tmp_path)
    result = _materialize(case, failure_injection="during_entry_verification")
    assert result["classification"] == "LIVE_ENTRY_VERIFICATION_FAILED_AFTER_AUTHORITATIVE_RENAME"
    assert result["authorization_state"] == "CONSUMED_REVIEW_REQUIRED"
    assert len(list((Path(case["root"]) / "entries").rglob("entry_manifest.json"))) == 1
    assert (Path(case["root"]) / "derived/registry_index_stale.json").is_file()


@pytest.mark.parametrize(
    "crash_point,classification",
    [
        ("before_index_transaction_marker", "DERIVED_INDEX_REGENERATION_FAILED_ENTRY_REMAINS_VALID_INDEX_STALE"),
        ("after_index_transaction_marker", "DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED"),
        ("after_first_index_pair_replacement", "DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED"),
    ],
)
def test_index_crash_keeps_verified_entry_authoritative_and_reports_exact_recovery_state(
    tmp_path: Path,
    crash_point: str,
    classification: str,
) -> None:
    case = _initialized_case(tmp_path)
    result = _materialize(case, failure_injection=crash_point)
    assert result["classification"] == classification
    assert result["entry_verified"] is True
    assert result["authorization_state"] == "CONSUMED_PENDING_HUMAN_LIVE_ENTRY_REVIEW"
    assert len(list((Path(case["root"]) / "entries").rglob("entry_manifest.json"))) == 1


def test_stale_index_recovery_rebuilds_derived_pair_without_rematerializing_entry(tmp_path: Path) -> None:
    case = _initialized_case(tmp_path)
    failed = _materialize(case, failure_injection="after_index_transaction_marker")
    root = Path(case["root"])
    entry = root / "entries" / failed["subject_key"] / failed["receipt_key"]
    before = _tree_hashes(entry)
    recovered = recover_live_accepted_lineage_index(
        root,
        expected_live_registry_root=case["expected_live_registry_root"],
        candidate_registry_root=case["candidate_registry_root"],
        approved_admin_root=case["approved_admin_root"],
        repository_root=case["repository_root"],
        registry_instance_id=case["registry_instance_id"],
        recovery_approval_id="synthetic-index-recovery-approval-001",
        operator_alias="synthetic-index-recovery",
        operation_id="synthetic-index-recovery-operation-001",
        backend=case["backend"],
    )
    assert recovered["classification"] == "DERIVED_INDEX_RECOVERY_COMPLETED"
    assert recovered["authoritative_entry_rematerialized"] is False
    assert _tree_hashes(entry) == before
    assert not (root / "derived/registry_index_transaction.json").exists()
    assert not (root / "derived/registry_index_stale.json").exists()
    manifest = json.loads((root / "derived/registry_index_manifest.json").read_text(encoding="utf-8"))
    assert manifest["entry_count"] == 1
    assert manifest["registry_index_sha256"] == sha256_bytes((root / "derived/registry_index.jsonl").read_bytes())


def test_recovery_requires_separate_exact_approval(tmp_path: Path) -> None:
    case = _initialized_case(tmp_path)
    _materialize(case, failure_injection="before_index_transaction_marker")
    with pytest.raises(RegistryError) as caught:
        recover_live_accepted_lineage_index(
            case["root"],
            expected_live_registry_root=case["expected_live_registry_root"],
            candidate_registry_root=case["candidate_registry_root"],
            approved_admin_root=case["approved_admin_root"],
            repository_root=case["repository_root"],
            registry_instance_id=case["registry_instance_id"],
            recovery_approval_id="",
            operator_alias="synthetic-index-recovery",
            operation_id="synthetic-index-recovery-operation-001",
            backend=case["backend"],
        )
    assert caught.value.classification == "LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP"
