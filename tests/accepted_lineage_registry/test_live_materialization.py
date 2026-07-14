from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes, sha256_bytes
from quant_replay_system.accepted_lineage_registry.live_workflow import (
    IDEMPOTENT_PASS_EXISTING_IDENTICAL_LIVE_ENTRY_PENDING_HUMAN_REVIEW,
    LIVE_ENTRY_AUTHORIZATION_REPLAY_CONFLICT_STOP,
    LIVE_ENTRY_CANDIDATE_PROVENANCE_MISMATCH_STOP,
    LIVE_ENTRY_FORBIDDEN_CANDIDATE_SOURCE_STOP,
    LIVE_ENTRY_PREFLIGHT_SUCCESS,
    LIVE_ENTRY_RECEIPT_COLLISION_STOP,
    NEW_LIVE_ENTRY_MATERIALIZED_PENDING_HUMAN_REVIEW,
    initialize_governed_live_registry,
    materialize_live_accepted_lineage_entry,
    preflight_live_accepted_lineage_materialization,
)
from quant_replay_system.accepted_lineage_registry.models import (
    GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
    SYNTHETIC_MODE,
    HumanReviewPayload,
    RegistryError,
    SubjectArtifactManifest,
)
from quant_replay_system.accepted_lineage_registry.path_safety import derive_receipt_key, derive_subject_key
from quant_replay_system.accepted_lineage_registry.transaction import initialize_synthetic_registry


@dataclass(frozen=True)
class _Identity:
    device: int
    inode: int
    number_of_links: int
    is_directory: bool


class _Handle:
    def __init__(self, path: str | Path, *, directory: bool) -> None:
        self.path = Path(path)
        self.directory = directory

    def __enter__(self) -> "_Handle":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


class _DeterministicBackend:
    def __init__(self) -> None:
        self.rename_observations: list[dict[str, object]] = []

    def capability_report(self):
        return SimpleNamespace(
            backend_status="SYNTHETIC_TEST_BACKEND",
            windows_backend_available=True,
            reparse_safe_handle_open=True,
            volume_and_file_identity_queries=True,
            hardlink_count_query=True,
            file_handle_flush=True,
            handle_relative_same_volume_rename=True,
            verified_handle_lock_disposition=True,
            L2_platform_acceptance_granted=False,
            risk_waiver_granted=False,
        )

    def open_directory_no_reparse(self, path, *, writable=False, delete=False):
        return _Handle(path, directory=True)

    def open_file_no_reparse(self, path, *, writable=False, delete=False):
        return _Handle(path, directory=False)

    def query_handle_identity(self, handle: _Handle) -> _Identity:
        observed = os.stat(handle.path)
        return _Identity(
            device=int(observed.st_dev),
            inode=int(observed.st_ino),
            number_of_links=int(observed.st_nlink),
            is_directory=handle.directory,
        )

    def query_link_count(self, handle: _Handle) -> int:
        count = self.query_handle_identity(handle).number_of_links
        if count != 1:
            raise RegistryError("LIVE_WINDOWS_HARDLINK_OR_IDENTITY_DRIFT_STOP", "unexpected link count")
        return count

    def flush_file_handle(self, handle: _Handle) -> None:
        assert handle.path.is_file()

    def flush_directory_handle(self, handle: _Handle) -> bool:
        assert handle.path.is_dir()
        return True

    def verify_committed_directory_identity(self, path, expected):
        observed = self.query_handle_identity(_Handle(path, directory=True))
        if observed != expected:
            raise RegistryError("LIVE_WINDOWS_RENAME_RESULT_UNVERIFIED_STOP", "directory identity changed")
        return observed

    def rename_directory_by_handle(self, source_path, target_parent, target_name):
        source = Path(source_path)
        target = Path(target_parent) / target_name
        before = self.query_handle_identity(_Handle(source, directory=True))
        children = sorted(item.name for item in source.iterdir())
        os.rename(source, target)
        observed = self.verify_committed_directory_identity(target, before)
        self.rename_observations.append(
            {
                "source_disappeared": not os.path.lexists(source),
                "target_exists": target.is_dir(),
                "target_identity_verified": observed == before,
                "source_children": children,
            }
        )
        return observed

    def dispose_lock_by_verified_handle(self, lock_path, expected) -> None:
        path = Path(lock_path)
        observed = self.query_handle_identity(_Handle(path, directory=False))
        if observed != expected:
            raise RegistryError("LIVE_WINDOWS_LOCK_OWNERSHIP_UNVERIFIED_STOP", "lock identity changed")
        path.unlink()


def _case(tmp_path: Path) -> dict[str, object]:
    admin = tmp_path / "admin"
    inputs = admin / "reviewer-inputs"
    artifacts = inputs / "subject-artifacts"
    repository = tmp_path / "repository"
    artifacts.mkdir(parents=True)
    repository.mkdir()
    packet = inputs / "synthetic-subject-packet.zip"
    packet.write_bytes(b"synthetic subject packet")
    records = []
    for index in range(6):
        target = artifacts / f"artifact-{index}.bin"
        exact_bytes = f"synthetic artifact {index}".encode()
        target.write_bytes(exact_bytes)
        records.append({"relative_path": target.name, "byte_length": len(exact_bytes), "sha256": sha256_bytes(exact_bytes)})
    manifest_data = {"artifact_count": 6, "artifacts": records, "subject_packet_sha256": sha256_bytes(packet.read_bytes())}
    manifest_bytes = canonical_json_bytes(manifest_data)
    manifest = SubjectArtifactManifest(manifest_bytes, manifest_data, sha256_bytes(manifest_bytes))
    payload_data = {"subject_packet_sha256": manifest_data["subject_packet_sha256"]}
    payload_bytes = canonical_json_bytes(payload_data)
    payload = HumanReviewPayload(payload_bytes, payload_data, sha256_bytes(payload_bytes))
    receipt = b"synthetic review receipt"
    expected_hashes = {
        "human_review_payload_sha256": payload.exact_sha256,
        "review_receipt_sha256": sha256_bytes(receipt),
        "subject_artifact_manifest_sha256": manifest.exact_sha256,
        "subject_artifact_sha256_by_path": {r["relative_path"]: r["sha256"] for r in records},
        "subject_packet_sha256": manifest_data["subject_packet_sha256"],
    }
    seal = sha256_bytes(b"accepted synthetic candidate entry seal")
    pilot = sha256_bytes(b"accepted synthetic pilot review zip")
    return {
        "root": admin / "prospective-live",
        "expected_live_registry_root": admin / "prospective-live",
        "candidate_registry_root": admin / "synthetic-candidate",
        "expected_candidate_registry_root": admin / "synthetic-candidate",
        "approved_admin_root": admin,
        "repository_root": repository,
        "live_registry_mode": GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
        "candidate_registry_mode": SYNTHETIC_MODE,
        "registry_instance_id": "live-instance-001",
        "expected_registry_instance_id": "live-instance-001",
        "logical_subject_identity": "subject-alpha",
        "expected_logical_subject_identity": "subject-alpha",
        "review_decision_id": "review-decision-001",
        "receipt_id": "receipt-001",
        "expected_receipt_id": "receipt-001",
        "candidate_materialization_authorization_id": "candidate-auth-001",
        "live_platform_acceptance_id": "platform-acceptance-001",
        "live_root_initialization_authorization_id": "root-init-auth-001",
        "live_materialization_authorization_id": "live-materialize-auth-001",
        "expected_live_materialization_authorization_id": "live-materialize-auth-001",
        "live_entry_review_decision_id": "live-review-decision-001",
        "next_task_approval_id": "next-task-approval-001",
        "authorization_state": "ISSUED_NOT_ACTIVATED",
        "execution_approval_id": "execution-approval-001",
        "human_review_payload": payload,
        "subject_artifact_manifest": manifest,
        "subject_packet_path": packet,
        "subject_artifact_root": artifacts,
        "review_receipt": receipt,
        "expected_reviewer_input_hashes": expected_hashes,
        "accepted_candidate_entry_seal_sha256": seal,
        "candidate_entry_seal_sha256": seal,
        "accepted_pilot_review_zip_sha256": pilot,
        "pilot_review_zip_sha256": pilot,
    }


def _preflight(case: dict[str, object], **overrides: object) -> dict[str, object]:
    kwargs = dict(case)
    kwargs.update(overrides)
    root = kwargs.pop("root")
    return preflight_live_accepted_lineage_materialization(root, **kwargs)


def _input_bytes(case: dict[str, object]) -> dict[str, bytes]:
    packet = case["subject_packet_path"]
    artifact_root = case["subject_artifact_root"]
    return {"packet": packet.read_bytes(), **{p.name: p.read_bytes() for p in sorted(artifact_root.iterdir())}}


def _initialized_case(tmp_path: Path) -> dict[str, object]:
    case = _case(tmp_path)
    backend = _DeterministicBackend()
    initialize_synthetic_registry(
        case["candidate_registry_root"],
        approved_admin_root=case["approved_admin_root"],
        repository_root=case["repository_root"],
        expected_registry_root=case["expected_candidate_registry_root"],
    )
    review_output = tmp_path / "synthetic-review-output"
    initialize_governed_live_registry(
        case["root"],
        expected_live_registry_root=case["expected_live_registry_root"],
        candidate_registry_root=case["candidate_registry_root"],
        approved_admin_root=case["approved_admin_root"],
        repository_root=case["repository_root"],
        live_platform_acceptance_id=case["live_platform_acceptance_id"],
        live_root_initialization_authorization_id=case["live_root_initialization_authorization_id"],
        expected_live_root_initialization_authorization_id=case["live_root_initialization_authorization_id"],
        registry_instance_id=case["registry_instance_id"],
        operator_alias="synthetic-live-initializer",
        operation_id="synthetic-live-root-operation",
        initialized_at="2026-07-15T00:00:00Z",
        review_output_root=review_output,
        review_zip_path=review_output / "synthetic-live-root-review.zip",
        backend=backend,
    )
    case.update(
        {
            "operator_alias": "synthetic-live-materializer",
            "operation_id": "synthetic-live-entry-operation-001",
            "materialized_at": "2026-07-15T00:01:00Z",
            "backend": backend,
        }
    )
    return case


def _materialize(case: dict[str, object], **overrides: object) -> dict[str, object]:
    kwargs = dict(case)
    kwargs.update(overrides)
    root = kwargs.pop("root")
    return materialize_live_accepted_lineage_entry(root, **kwargs)


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_bytes(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_success_is_no_write_and_synthetic_inputs_remain_byte_identical(tmp_path: Path) -> None:
    case = _case(tmp_path)
    before = _input_bytes(case)
    result = _preflight(case)
    assert result["classification"] == LIVE_ENTRY_PREFLIGHT_SUCCESS
    assert _input_bytes(case) == before
    assert not case["root"].exists()
    assert not case["candidate_registry_root"].exists()
    assert result["authoritative_write_performed"] is False
    assert result["staging_created"] is False
    assert result["live_entry_materialized"] is False


@pytest.mark.parametrize(
    "hash_field",
    [
        "human_review_payload_sha256",
        "subject_artifact_manifest_sha256",
        "review_receipt_sha256",
        "subject_packet_sha256",
    ],
)
def test_reviewer_and_subject_packet_hash_mismatches_fail_closed(tmp_path: Path, hash_field: str) -> None:
    case = _case(tmp_path)
    expected = dict(case["expected_reviewer_input_hashes"])
    expected["subject_artifact_sha256_by_path"] = dict(expected["subject_artifact_sha256_by_path"])
    expected[hash_field] = "0" * 64
    with pytest.raises(RegistryError) as caught:
        _preflight(case, expected_reviewer_input_hashes=expected)
    assert caught.value.classification == "LIVE_ENTRY_IMMUTABLE_INPUT_HASH_MISMATCH_STOP"


@pytest.mark.parametrize("artifact_index", range(6))
def test_each_of_six_subject_artifact_hash_mismatches_fails_closed(tmp_path: Path, artifact_index: int) -> None:
    case = _case(tmp_path)
    expected = dict(case["expected_reviewer_input_hashes"])
    artifact_hashes = dict(expected["subject_artifact_sha256_by_path"])
    artifact_hashes[f"artifact-{artifact_index}.bin"] = "0" * 64
    expected["subject_artifact_sha256_by_path"] = artifact_hashes
    with pytest.raises(RegistryError) as caught:
        _preflight(case, expected_reviewer_input_hashes=expected)
    assert caught.value.classification == "LIVE_ENTRY_IMMUTABLE_INPUT_HASH_MISMATCH_STOP"


@pytest.mark.parametrize("field", ["candidate_entry_seal_sha256", "pilot_review_zip_sha256"])
def test_candidate_provenance_hash_mismatch_fails_closed(tmp_path: Path, field: str) -> None:
    with pytest.raises(RegistryError) as caught:
        _preflight(_case(tmp_path), **{field: "0" * 64})
    assert caught.value.classification == LIVE_ENTRY_CANDIDATE_PROVENANCE_MISMATCH_STOP


def test_candidate_entry_bytes_cannot_be_a_write_source(tmp_path: Path) -> None:
    with pytest.raises(RegistryError) as caught:
        _preflight(_case(tmp_path), candidate_entry_bytes=b"forbidden candidate entry bytes")
    assert caught.value.classification == LIVE_ENTRY_FORBIDDEN_CANDIDATE_SOURCE_STOP


@pytest.mark.parametrize("intent", ["copy", "import", "rename", "promotion"])
def test_candidate_copy_import_rename_and_promotion_intents_fail_closed(tmp_path: Path, intent: str) -> None:
    with pytest.raises(RegistryError) as caught:
        _preflight(_case(tmp_path), candidate_source_intent=intent)
    assert caught.value.classification == LIVE_ENTRY_FORBIDDEN_CANDIDATE_SOURCE_STOP


def test_preflight_never_accesses_retained_candidate_or_prospective_live_root(tmp_path: Path) -> None:
    case = _case(tmp_path)
    assert not case["candidate_registry_root"].exists()
    assert not case["root"].exists()
    _preflight(case)
    assert not case["candidate_registry_root"].exists()
    assert not case["root"].exists()


def test_existing_empty_root_initialization_entry_point_remains_callable() -> None:
    assert callable(initialize_governed_live_registry)


def test_synthetic_authoritative_materialization_creates_exact_verified_five_file_entry(tmp_path: Path) -> None:
    case = _initialized_case(tmp_path)
    candidate_before = _tree_hashes(Path(case["candidate_registry_root"]))
    result = _materialize(case)
    assert result["classification"] == NEW_LIVE_ENTRY_MATERIALIZED_PENDING_HUMAN_REVIEW
    assert result["authorization_state"] == "CONSUMED_PENDING_HUMAN_LIVE_ENTRY_REVIEW"
    assert result["entry_created"] is True
    assert result["entry_verified"] is True
    assert result["next_task_authorized_by_registry"] is False
    entry = Path(case["root"]) / "entries" / result["subject_key"] / result["receipt_key"]
    assert {item.name for item in entry.iterdir()} == {
        "human_review_payload.json",
        "subject_artifact_manifest.json",
        "review_receipt.md",
        "entry_manifest.json",
        "entry_seal.json",
    }
    manifest = json.loads((entry / "entry_manifest.json").read_text(encoding="utf-8"))
    assert manifest["accepted_candidate_entry_seal_sha256"] == case["accepted_candidate_entry_seal_sha256"]
    assert manifest["accepted_pilot_review_zip_sha256"] == case["accepted_pilot_review_zip_sha256"]
    assert manifest["immutable_input_verification_sha256"] == sha256_bytes(
        canonical_json_bytes(manifest["immutable_input_verification"])
    )
    assert manifest["registry_instance_id"] == case["registry_instance_id"]
    assert _tree_hashes(Path(case["candidate_registry_root"])) == candidate_before
    assert case["backend"].rename_observations == [
        {
            "source_disappeared": True,
            "target_exists": True,
            "target_identity_verified": True,
            "source_children": [
                "entry_manifest.json",
                "entry_seal.json",
                "human_review_payload.json",
                "review_receipt.md",
                "subject_artifact_manifest.json",
            ],
        }
    ]


def test_identical_replay_requires_same_consumed_authorization_and_changes_no_entry_bytes(tmp_path: Path) -> None:
    case = _initialized_case(tmp_path)
    first = _materialize(case)
    root = Path(case["root"])
    before = _tree_hashes(root)
    replay = _materialize(
        case,
        authorization_state="CONSUMED_PENDING_HUMAN_LIVE_ENTRY_REVIEW",
        consumed_live_materialization_authorization_ids=(case["live_materialization_authorization_id"],),
    )
    assert replay["classification"] == IDEMPOTENT_PASS_EXISTING_IDENTICAL_LIVE_ENTRY_PENDING_HUMAN_REVIEW
    assert replay["idempotent_replay"] is True
    assert replay["entry_created"] is False
    assert _tree_hashes(root) == before


def test_same_identity_with_new_authorization_is_exact_replay_conflict(tmp_path: Path) -> None:
    case = _initialized_case(tmp_path)
    _materialize(case)
    root = Path(case["root"])
    before = _tree_hashes(root)
    with pytest.raises(RegistryError) as caught:
        _materialize(
            case,
            live_materialization_authorization_id="live-materialize-auth-002",
            expected_live_materialization_authorization_id="live-materialize-auth-002",
            operation_id="synthetic-live-entry-operation-002",
        )
    assert caught.value.classification == LIVE_ENTRY_AUTHORIZATION_REPLAY_CONFLICT_STOP
    assert _tree_hashes(root) == before


@pytest.mark.parametrize(
    "accepted_field,observed_field",
    [
        ("accepted_candidate_entry_seal_sha256", "candidate_entry_seal_sha256"),
        ("accepted_pilot_review_zip_sha256", "pilot_review_zip_sha256"),
    ],
)
def test_replay_provenance_drift_is_exact_receipt_collision_and_preserves_all_live_bytes(
    tmp_path: Path,
    accepted_field: str,
    observed_field: str,
) -> None:
    case = _initialized_case(tmp_path)
    _materialize(case)
    root = Path(case["root"])
    before = _tree_hashes(root)
    changed_provenance = sha256_bytes(f"changed {accepted_field}".encode("utf-8"))
    with pytest.raises(RegistryError) as caught:
        _materialize(
            case,
            **{
                accepted_field: changed_provenance,
                observed_field: changed_provenance,
                "authorization_state": "CONSUMED_PENDING_HUMAN_LIVE_ENTRY_REVIEW",
                "consumed_live_materialization_authorization_ids": (
                    case["live_materialization_authorization_id"],
                ),
            },
        )
    assert caught.value.classification == LIVE_ENTRY_RECEIPT_COLLISION_STOP
    assert _tree_hashes(root) == before


def test_different_immutable_identity_with_same_receipt_is_exact_collision(tmp_path: Path) -> None:
    case = _initialized_case(tmp_path)
    _materialize(case)
    payload_data = {**case["human_review_payload"].data, "synthetic_variant": "different"}
    payload_bytes = canonical_json_bytes(payload_data)
    payload = HumanReviewPayload(payload_bytes, payload_data, sha256_bytes(payload_bytes))
    expected_hashes = dict(case["expected_reviewer_input_hashes"])
    expected_hashes["subject_artifact_sha256_by_path"] = dict(expected_hashes["subject_artifact_sha256_by_path"])
    expected_hashes["human_review_payload_sha256"] = payload.exact_sha256
    with pytest.raises(RegistryError) as caught:
        _materialize(
            case,
            human_review_payload=payload,
            expected_reviewer_input_hashes=expected_hashes,
            live_materialization_authorization_id="live-materialize-auth-002",
            expected_live_materialization_authorization_id="live-materialize-auth-002",
            operation_id="synthetic-live-entry-operation-002",
        )
    assert caught.value.classification == LIVE_ENTRY_RECEIPT_COLLISION_STOP


def test_live_index_is_derived_and_binds_the_single_authoritative_entry(tmp_path: Path) -> None:
    case = _initialized_case(tmp_path)
    result = _materialize(case)
    root = Path(case["root"])
    rows = [json.loads(line) for line in (root / "derived/registry_index.jsonl").read_text(encoding="utf-8").splitlines()]
    manifest = json.loads((root / "derived/registry_index_manifest.json").read_text(encoding="utf-8"))
    assert len(rows) == 1
    assert rows[0]["subject_key"] == result["subject_key"]
    assert rows[0]["receipt_key"] == result["receipt_key"]
    assert manifest["entry_count"] == 1
    assert manifest["registry_index_sha256"] == sha256_bytes((root / "derived/registry_index.jsonl").read_bytes())


def test_unvalidated_target_is_not_probed_before_exact_root_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _case(tmp_path)
    case.update(
        {
            "operator_alias": "synthetic-live-materializer",
            "operation_id": "synthetic-live-entry-operation-untrusted-root",
            "materialized_at": "2026-07-15T00:01:00Z",
            "backend": _DeterministicBackend(),
        }
    )
    target = (
        Path(case["root"]).absolute()
        / "entries"
        / derive_subject_key(str(case["logical_subject_identity"]))
        / derive_receipt_key(str(case["receipt_id"]))
    )
    probes: list[str] = []

    def guarded_path_method(name: str, original):
        def guarded(path: Path, *args, **kwargs):
            if path.absolute() == target:
                probes.append(name)
                raise AssertionError(f"unvalidated target probe: {name}")
            return original(path, *args, **kwargs)

        return guarded

    for method_name in ("is_dir", "exists", "stat", "glob", "rglob"):
        monkeypatch.setattr(
            Path,
            method_name,
            guarded_path_method(method_name, getattr(Path, method_name)),
        )
    original_listdir = os.listdir

    def guarded_listdir(path):
        if Path(path).absolute() == target:
            probes.append("listdir")
            raise AssertionError("unvalidated target probe: listdir")
        return original_listdir(path)

    monkeypatch.setattr(os, "listdir", guarded_listdir)
    with pytest.raises(RegistryError) as caught:
        _materialize(
            case,
            expected_live_registry_root=Path(case["root"]).with_name("different-live-root"),
        )
    assert caught.value.classification == "LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP"
    assert probes == []
