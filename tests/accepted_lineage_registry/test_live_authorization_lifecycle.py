from __future__ import annotations

from itertools import combinations
from pathlib import Path

import pytest

from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes, sha256_bytes
from quant_replay_system.accepted_lineage_registry.live_workflow import (
    LIVE_AUTHORIZATION_STATES,
    LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP,
    LIVE_ENTRY_AUTHORIZATION_IDENTITY_COLLISION_STOP,
    LIVE_ENTRY_AUTHORIZATION_REUSE_STOP,
    LIVE_ENTRY_AUTHORIZATION_STATE_INVALID_STOP,
    LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP,
    LIVE_ENTRY_PREFLIGHT_SUCCESS,
    LIVE_ENTRY_ROOT_MODE_OR_OVERLAP_STOP,
    LIVE_ENTRY_SUBJECT_OR_RECEIPT_MISMATCH_STOP,
    preflight_live_accepted_lineage_materialization,
)
from quant_replay_system.accepted_lineage_registry.models import (
    GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
    SYNTHETIC_MODE,
    HumanReviewPayload,
    RegistryError,
    SubjectArtifactManifest,
)


IDENTITY_FIELDS = (
    "review_decision_id",
    "receipt_id",
    "candidate_materialization_authorization_id",
    "live_platform_acceptance_id",
    "live_root_initialization_authorization_id",
    "live_materialization_authorization_id",
    "live_entry_review_decision_id",
    "next_task_approval_id",
)


def _case(tmp_path: Path) -> dict[str, object]:
    admin = tmp_path / "admin"
    inputs = admin / "reviewer-inputs"
    artifacts = inputs / "subject-artifacts"
    repository = tmp_path / "repository"
    artifacts.mkdir(parents=True)
    repository.mkdir()
    packet = inputs / "synthetic-subject-packet.zip"
    packet.write_bytes(b"synthetic subject packet")
    artifact_records = []
    for index in range(6):
        target = artifacts / f"artifact-{index}.bin"
        exact_bytes = f"synthetic artifact {index}".encode()
        target.write_bytes(exact_bytes)
        artifact_records.append(
            {"relative_path": target.name, "byte_length": len(exact_bytes), "sha256": sha256_bytes(exact_bytes)}
        )
    manifest_data = {
        "artifact_count": 6,
        "artifacts": artifact_records,
        "subject_packet_sha256": sha256_bytes(packet.read_bytes()),
    }
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
        "subject_artifact_sha256_by_path": {r["relative_path"]: r["sha256"] for r in artifact_records},
        "subject_packet_sha256": manifest_data["subject_packet_sha256"],
    }
    candidate_seal = sha256_bytes(b"accepted synthetic candidate entry seal")
    pilot_zip = sha256_bytes(b"accepted synthetic pilot review zip")
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
        "accepted_candidate_entry_seal_sha256": candidate_seal,
        "candidate_entry_seal_sha256": candidate_seal,
        "accepted_pilot_review_zip_sha256": pilot_zip,
        "pilot_review_zip_sha256": pilot_zip,
    }


def _preflight(case: dict[str, object], **overrides: object) -> dict[str, object]:
    kwargs = dict(case)
    kwargs.update(overrides)
    root = kwargs.pop("root")
    return preflight_live_accepted_lineage_materialization(root, **kwargs)


def test_exact_five_state_lifecycle_representation() -> None:
    assert LIVE_AUTHORIZATION_STATES == (
        "ISSUED_NOT_ACTIVATED",
        "ACTIVATED_NOT_CONSUMED",
        "CONSUMED_PENDING_HUMAN_LIVE_ENTRY_REVIEW",
        "CONSUMED_ACCEPTED_LIVE_ENTRY",
        "CONSUMED_REVIEW_REQUIRED",
    )


def test_valid_transition_is_proposed_but_not_persisted_or_consumed(tmp_path: Path) -> None:
    result = _preflight(_case(tmp_path))
    assert result["classification"] == LIVE_ENTRY_PREFLIGHT_SUCCESS
    assert result["authorization_state_before"] == "ISSUED_NOT_ACTIVATED"
    assert result["authorization_state_after"] == "ACTIVATED_NOT_CONSUMED"
    assert result["authorization_state_persisted"] is False
    assert result["authorization_consumed"] is False
    assert result["authoritative_write_performed"] is False
    assert result["staging_created"] is False
    assert result["live_entry_materialized"] is False


@pytest.mark.parametrize("field", IDENTITY_FIELDS)
def test_all_eight_authorization_identities_are_required(tmp_path: Path, field: str) -> None:
    with pytest.raises(RegistryError) as caught:
        _preflight(_case(tmp_path), **{field: ""})
    assert caught.value.classification == LIVE_ENTRY_AUTHORIZATION_IDENTITY_COLLISION_STOP


@pytest.mark.parametrize("left,right", list(combinations(IDENTITY_FIELDS, 2)))
def test_every_pairwise_identity_collision_fails_closed(tmp_path: Path, left: str, right: str) -> None:
    case = _case(tmp_path)
    with pytest.raises(RegistryError) as caught:
        _preflight(case, **{right: case[left]})
    assert caught.value.classification in {
        LIVE_ENTRY_AUTHORIZATION_IDENTITY_COLLISION_STOP,
        LIVE_ENTRY_AUTHORIZATION_REUSE_STOP,
    }


@pytest.mark.parametrize("source_field", ["candidate_materialization_authorization_id", "live_root_initialization_authorization_id"])
def test_candidate_and_initialization_authorization_reuse_stops(tmp_path: Path, source_field: str) -> None:
    case = _case(tmp_path)
    with pytest.raises(RegistryError) as caught:
        _preflight(case, live_materialization_authorization_id=case[source_field])
    assert caught.value.classification == LIVE_ENTRY_AUTHORIZATION_REUSE_STOP


def test_consumed_live_authorization_reuse_stops(tmp_path: Path) -> None:
    case = _case(tmp_path)
    with pytest.raises(RegistryError) as caught:
        _preflight(case, consumed_live_materialization_authorization_ids=(case["live_materialization_authorization_id"],))
    assert caught.value.classification == LIVE_ENTRY_AUTHORIZATION_REUSE_STOP


def test_prior_receipt_or_root_binding_reuse_stops(tmp_path: Path) -> None:
    case = _case(tmp_path)
    authorization = case["live_materialization_authorization_id"]
    with pytest.raises(RegistryError) as caught:
        _preflight(case, prior_live_materialization_authorization_bindings={authorization: {"receipt_id": "other"}})
    assert caught.value.classification == LIVE_ENTRY_AUTHORIZATION_REUSE_STOP


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_live_registry_root", "other-live"),
        ("expected_candidate_registry_root", "other-candidate"),
        ("expected_registry_instance_id", "other-instance"),
        ("expected_live_materialization_authorization_id", "other-live-auth"),
    ],
)
def test_root_instance_and_authorization_binding_mismatches_stop(tmp_path: Path, field: str, value: str) -> None:
    case = _case(tmp_path)
    override: object = case["approved_admin_root"] / value if field.endswith("root") else value
    with pytest.raises(RegistryError) as caught:
        _preflight(case, **{field: override})
    assert caught.value.classification == LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP


@pytest.mark.parametrize(
    "field,value",
    [("expected_logical_subject_identity", "other-subject"), ("expected_receipt_id", "other-receipt")],
)
def test_subject_and_receipt_mismatches_stop(tmp_path: Path, field: str, value: str) -> None:
    with pytest.raises(RegistryError) as caught:
        _preflight(_case(tmp_path), **{field: value})
    assert caught.value.classification == LIVE_ENTRY_SUBJECT_OR_RECEIPT_MISMATCH_STOP


@pytest.mark.parametrize("state", LIVE_AUTHORIZATION_STATES[1:])
def test_automatic_transition_from_consumed_or_review_states_is_impossible(tmp_path: Path, state: str) -> None:
    with pytest.raises(RegistryError) as caught:
        _preflight(_case(tmp_path), authorization_state=state)
    assert caught.value.classification == LIVE_ENTRY_AUTHORIZATION_STATE_INVALID_STOP


def test_execution_approval_is_explicit_and_required(tmp_path: Path) -> None:
    with pytest.raises(RegistryError) as caught:
        _preflight(_case(tmp_path), execution_approval_id=None)
    assert caught.value.classification == LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP


@pytest.mark.parametrize("direction", ["candidate_inside_live", "live_inside_candidate"])
def test_live_candidate_root_overlap_in_either_direction_stops(tmp_path: Path, direction: str) -> None:
    case = _case(tmp_path)
    if direction == "candidate_inside_live":
        live = case["root"]
        candidate = live / "candidate"
    else:
        candidate = case["candidate_registry_root"]
        live = candidate / "live"
    with pytest.raises(RegistryError) as caught:
        _preflight(
            case,
            root=live,
            expected_live_registry_root=live,
            candidate_registry_root=candidate,
            expected_candidate_registry_root=candidate,
        )
    assert caught.value.classification == LIVE_ENTRY_ROOT_MODE_OR_OVERLAP_STOP


@pytest.mark.parametrize(
    "field,value",
    [("live_registry_mode", SYNTHETIC_MODE), ("candidate_registry_mode", GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE)],
)
def test_registry_mode_is_explicit_and_not_inferred_from_folder_name(tmp_path: Path, field: str, value: str) -> None:
    with pytest.raises(RegistryError) as caught:
        _preflight(_case(tmp_path), **{field: value})
    assert caught.value.classification == LIVE_ENTRY_ROOT_MODE_OR_OVERLAP_STOP


def test_downstream_authority_remains_none_and_next_task_remains_false(tmp_path: Path) -> None:
    result = _preflight(_case(tmp_path))
    for field in (
        "business_authority",
        "research_authority",
        "evidence_acceptance_authority",
        "PIT_authority",
        "replay_authority",
        "buy_review_authority",
        "trading_authority",
    ):
        assert result[field] == "none"
    assert result["next_task_authorized_by_registry"] is False
