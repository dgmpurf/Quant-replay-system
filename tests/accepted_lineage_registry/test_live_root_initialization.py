from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes, sha256_bytes
from quant_replay_system.accepted_lineage_registry.live_workflow import (
    APPROVAL_MISSING_STOP,
    ENTRY_EXISTS_STOP,
    IDEMPOTENT_CLASSIFICATION,
    INCOMPLETE_REVIEW_STOP,
    PLATFORM_HARDENING_STOP,
    REPLAY_CONFLICT_STOP,
    SUCCESS_CLASSIFICATION,
    WRONG_POLICY_STOP,
    initialize_governed_live_registry,
)
from quant_replay_system.accepted_lineage_registry.models import (
    GovernedCandidateRegistryPolicy,
    RegistryError,
    RegistryPolicy,
    RegistrySchema,
)
from quant_replay_system.accepted_lineage_registry.transaction import initialize_synthetic_registry
from quant_replay_system.accepted_lineage_registry.windows_live_backend import WindowsLiveFilesystemBackend


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
    def __init__(self, *, controls_available: bool = True) -> None:
        self.controls_available = controls_available

    def capability_report(self):
        value = self.controls_available
        return SimpleNamespace(
            backend_status="IMPLEMENTED_FAIL_CLOSED_PENDING_SEPARATE_L2_HUMAN_ACCEPTANCE",
            windows_backend_available=value,
            reparse_safe_handle_open=value,
            volume_and_file_identity_queries=value,
            hardlink_count_query=value,
            file_handle_flush=value,
            handle_relative_same_volume_rename=value,
            verified_handle_lock_disposition=value,
            L2_platform_acceptance_granted=False,
            risk_waiver_granted=False,
        )

    def open_directory_no_reparse(self, path, *, writable=False, delete=False):
        return _Handle(path, directory=True)

    def open_file_no_reparse(self, path, *, writable=False, delete=False):
        return _Handle(path, directory=False)

    def query_handle_identity(self, handle: _Handle) -> _Identity:
        stat_result = os.stat(handle.path)
        return _Identity(
            device=int(stat_result.st_dev),
            inode=int(stat_result.st_ino),
            number_of_links=int(stat_result.st_nlink),
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


def _material(tmp_path: Path, *, root_name: str = "mode-neutral-empty-live-root") -> dict[str, object]:
    admin = tmp_path / "admin"
    repository = tmp_path / "repository"
    admin.mkdir()
    repository.mkdir()
    candidate = admin / "synthetic-candidate-fixture"
    initialize_synthetic_registry(candidate, approved_admin_root=admin, repository_root=repository)
    review_output = tmp_path / "review-output"
    return {
        "root": admin / root_name,
        "expected_live_registry_root": admin / root_name,
        "candidate_registry_root": candidate,
        "approved_admin_root": admin,
        "repository_root": repository,
        "live_platform_acceptance_id": "L2_TEMP_PLATFORM_ACCEPTANCE_001",
        "live_root_initialization_authorization_id": "L3_EMPTY_ROOT_AUTHORIZATION_001",
        "expected_live_root_initialization_authorization_id": "L3_EMPTY_ROOT_AUTHORIZATION_001",
        "registry_instance_id": "LIVE_INSTANCE_001",
        "operator_alias": "bounded-live-initializer",
        "operation_id": "P3_EMPTY_ROOT_OPERATION_001",
        "initialized_at": "2026-07-14T00:00:00Z",
        "review_output_root": review_output,
        "review_zip_path": review_output / "empty-root-review.zip",
        "backend": _DeterministicBackend(),
    }


def _initialize(material: dict[str, object]) -> dict[str, object]:
    return initialize_governed_live_registry(**material)


def test_successful_temporary_empty_root_initialization(tmp_path: Path) -> None:
    material = _material(tmp_path)
    result = _initialize(material)
    assert result["classification"] == SUCCESS_CLASSIFICATION
    assert Path(material["root"]).is_dir()


def test_actual_windows_backend_temporary_empty_live_root_initialization(tmp_path: Path) -> None:
    assert os.name == "nt"
    material = _material(tmp_path, root_name="actual-backend-empty-live-root")
    material["backend"] = WindowsLiveFilesystemBackend()

    result = _initialize(material)
    root = Path(material["root"])

    assert result["classification"] == SUCCESS_CLASSIFICATION
    assert root.is_dir()
    assert list((root / "entries").iterdir()) == []
    assert result["health"]["authoritative_entry_count"] == 0
    assert result["live_entry_materialized"] is False
    assert result["materialization_authorized"] is False


def test_exact_empty_live_root_structure(tmp_path: Path) -> None:
    material = _material(tmp_path)
    _initialize(material)
    root = Path(material["root"])
    assert {item.name for item in root.iterdir()} == {
        ".staging",
        "derived",
        "entries",
        "registry_initialization_seal.json",
        "registry_instance_manifest.json",
        "registry_policy.json",
        "registry_schema.json",
    }
    assert {item.name for item in (root / "derived").iterdir()} == {
        "registry_index.jsonl",
        "registry_index_manifest.json",
    }


def test_zero_authoritative_entries_and_no_materialization(tmp_path: Path) -> None:
    material = _material(tmp_path)
    result = _initialize(material)
    root = Path(material["root"])
    assert list((root / "entries").iterdir()) == []
    assert result["health"]["authoritative_entry_count"] == 0
    assert result["live_entry_materialized"] is False
    assert result["materialization_authorized"] is False


def test_policy_schema_and_instance_bindings(tmp_path: Path) -> None:
    material = _material(tmp_path)
    _initialize(material)
    root = Path(material["root"])
    policy = json.loads((root / "registry_policy.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "registry_schema.json").read_text(encoding="utf-8"))
    instance = json.loads((root / "registry_instance_manifest.json").read_text(encoding="utf-8"))
    assert policy["candidate_registry"] is False
    assert policy["live_registry"] is True
    assert policy["live_registry_allowed"] is True
    assert schema == RegistrySchema().to_dict()
    assert instance["registry_instance_id"] == material["registry_instance_id"]
    assert instance["live_root_initialization_authorization_id"] == material[
        "live_root_initialization_authorization_id"
    ]


def test_initialization_seal_binds_exact_documents(tmp_path: Path) -> None:
    material = _material(tmp_path)
    result = _initialize(material)
    root = Path(material["root"])
    seal = json.loads((root / "registry_initialization_seal.json").read_text(encoding="utf-8"))
    assert seal["registry_policy_sha256"] == sha256_bytes((root / "registry_policy.json").read_bytes())
    assert seal["registry_schema_sha256"] == sha256_bytes((root / "registry_schema.json").read_bytes())
    assert seal["registry_instance_manifest_sha256"] == sha256_bytes(
        (root / "registry_instance_manifest.json").read_bytes()
    )
    assert seal["registry_index_sha256"] == sha256_bytes((root / "derived/registry_index.jsonl").read_bytes())
    assert seal["registry_index_manifest_sha256"] == sha256_bytes(
        (root / "derived/registry_index_manifest.json").read_bytes()
    )
    assert result["initialization_seal_sha256"] == sha256_bytes(
        (root / "registry_initialization_seal.json").read_bytes()
    )


def test_empty_index_and_manifest_binding(tmp_path: Path) -> None:
    material = _material(tmp_path)
    _initialize(material)
    root = Path(material["root"])
    index_bytes = (root / "derived/registry_index.jsonl").read_bytes()
    manifest = json.loads((root / "derived/registry_index_manifest.json").read_text(encoding="utf-8"))
    assert index_bytes == b""
    assert manifest["entry_count"] == 0
    assert manifest["registry_index_sha256"] == sha256_bytes(index_bytes)
    assert manifest["status"] == "DERIVED_NON_AUTHORITATIVE_EMPTY_LIVE_INDEX_VALID"


def test_initial_health_invariants(tmp_path: Path) -> None:
    health = _initialize(_material(tmp_path))["health"]
    assert health["entry_verification_status"] == "PASS_EMPTY"
    assert health["derived_index_status"] == "PASS"
    assert health["root_mode_binding_status"] == "PASS"
    assert health["lock_status"] == "UNLOCKED"
    assert health["orphan_temporary_directories"] == 0
    assert health["next_task_authorized_by_registry"] is False


def test_identical_initialization_is_idempotent(tmp_path: Path) -> None:
    material = _material(tmp_path)
    _initialize(material)
    replay = _initialize(material)
    assert replay["classification"] == IDEMPOTENT_CLASSIFICATION


def test_missing_initialization_authorization_stops_before_root(tmp_path: Path) -> None:
    material = _material(tmp_path)
    material["live_root_initialization_authorization_id"] = ""
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == APPROVAL_MISSING_STOP
    assert not Path(material["root"]).exists()


def test_mismatched_initialization_authorization_stops(tmp_path: Path) -> None:
    material = _material(tmp_path)
    material["expected_live_root_initialization_authorization_id"] = "L3_OTHER_AUTHORIZATION"
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == APPROVAL_MISSING_STOP


def test_initialization_authorization_replay_conflict_stops(tmp_path: Path) -> None:
    material = _material(tmp_path)
    _initialize(material)
    material["live_root_initialization_authorization_id"] = "L3_EMPTY_ROOT_AUTHORIZATION_002"
    material["expected_live_root_initialization_authorization_id"] = "L3_EMPTY_ROOT_AUTHORIZATION_002"
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == REPLAY_CONFLICT_STOP


def test_platform_hardening_unavailable_stops_before_root(tmp_path: Path) -> None:
    material = _material(tmp_path)
    material["backend"] = _DeterministicBackend(controls_available=False)
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == PLATFORM_HARDENING_STOP
    assert not Path(material["root"]).exists()


def test_same_candidate_and_live_root_stops(tmp_path: Path) -> None:
    material = _material(tmp_path)
    material["root"] = material["candidate_registry_root"]
    material["expected_live_registry_root"] = material["candidate_registry_root"]
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == "LIVE_REGISTRY_CANDIDATE_ROOT_OVERLAP_STOP"


@pytest.mark.parametrize("relation", ["live_inside_candidate", "candidate_inside_live"])
def test_candidate_live_overlap_in_either_direction_stops(tmp_path: Path, relation: str) -> None:
    material = _material(tmp_path)
    if relation == "live_inside_candidate":
        live = Path(material["candidate_registry_root"]) / "nested-live"
    else:
        live = Path(material["approved_admin_root"]) / "outer-live"
        nested_candidate = live / "synthetic-nested-candidate"
        live.mkdir()
        initialize_synthetic_registry(
            nested_candidate,
            approved_admin_root=material["approved_admin_root"],
            repository_root=material["repository_root"],
        )
        material["candidate_registry_root"] = nested_candidate
    material["root"] = live
    material["expected_live_registry_root"] = live
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == "LIVE_REGISTRY_CANDIDATE_ROOT_OVERLAP_STOP"


def test_candidate_policy_cannot_be_reclassified_as_live(tmp_path: Path) -> None:
    material = _material(tmp_path)
    root = Path(material["root"])
    root.mkdir()
    (root / "registry_policy.json").write_bytes(canonical_json_bytes(GovernedCandidateRegistryPolicy().to_dict()))
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == "LIVE_REGISTRY_CANDIDATE_POLICY_RECLASSIFICATION_STOP"


def test_wrong_existing_policy_stops(tmp_path: Path) -> None:
    material = _material(tmp_path)
    root = Path(material["root"])
    root.mkdir()
    (root / "registry_policy.json").write_bytes(canonical_json_bytes(RegistryPolicy().to_dict()))
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == WRONG_POLICY_STOP


def test_existing_root_containing_entry_stops(tmp_path: Path) -> None:
    material = _material(tmp_path)
    _initialize(material)
    (Path(material["root"]) / "entries" / "unexpected-entry").mkdir()
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == ENTRY_EXISTS_STOP


def test_partial_initialized_root_requires_review(tmp_path: Path) -> None:
    material = _material(tmp_path)
    Path(material["root"]).mkdir()
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == INCOMPLETE_REVIEW_STOP
    assert Path(material["root"]).exists()


def test_mode_is_not_inferred_from_directory_name(tmp_path: Path) -> None:
    material = _material(tmp_path, root_name="accepted_lineage_registry_v0_1")
    result = _initialize(material)
    assert result["classification"] == SUCCESS_CLASSIFICATION


def test_default_and_explicit_authority_fields_remain_none(tmp_path: Path) -> None:
    material = _material(tmp_path)
    result = _initialize(material)
    policy = json.loads((Path(material["root"]) / "registry_policy.json").read_text(encoding="utf-8"))
    for field in (
        "business_authority",
        "research_authority",
        "evidence_acceptance_authority",
        "PIT_authority",
        "replay_authority",
        "buy_review_authority",
        "trading_authority",
    ):
        assert policy[field] == "none"
        assert result["health"][field] == "none"


def test_authorization_must_be_distinct_from_platform_acceptance(tmp_path: Path) -> None:
    material = _material(tmp_path)
    material["live_root_initialization_authorization_id"] = material["live_platform_acceptance_id"]
    material["expected_live_root_initialization_authorization_id"] = material["live_platform_acceptance_id"]
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == APPROVAL_MISSING_STOP


def test_required_identity_must_be_nfc_stable(tmp_path: Path) -> None:
    material = _material(tmp_path)
    material["operation_id"] = "operation-e\u0301"
    with pytest.raises(RegistryError) as caught:
        _initialize(material)
    assert caught.value.classification == APPROVAL_MISSING_STOP


def test_no_retained_candidate_or_real_live_root_is_accessed(tmp_path: Path) -> None:
    material = _material(tmp_path)
    retained_sentinel = tmp_path / "retained-candidate-sentinel.txt"
    retained_sentinel.write_text("unchanged\n", encoding="utf-8")
    prospective_real_root = tmp_path / "prospective-real-live-root-sentinel"
    _initialize(material)
    assert retained_sentinel.read_text(encoding="utf-8") == "unchanged\n"
    assert not prospective_real_root.exists()
