from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

from conftest import make_synthetic_material, materialization_kwargs
from quant_replay_system.accepted_lineage_registry.canonical import (
    canonical_json_bytes,
    sha256_bytes,
)
from quant_replay_system.accepted_lineage_registry.cli import run as cli_run
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.real_candidate import (
    ARTIFACT_SET_STOP,
    AUTHORITY_PRESENT_STOP,
    CANDIDATE_EXISTS_STOP,
    CANDIDATE_UNSAFE_STOP,
    GOVERNED_REAL_CANDIDATE_MODE,
    LIVE_COLLISION_STOP,
    MANIFEST_HASH_STOP,
    PACKET_HASH_STOP,
    PAYLOAD_HASH_STOP,
    REVIEW_DECISION_STOP,
    REVIEW_RECEIPT_HASH_STOP,
    REVIEW_RECEIPT_STOP,
    RUNTIME_FIELD_STOP,
    SUCCESS_CLASSIFICATION,
    dry_run_real_candidate,
)
from quant_replay_system.accepted_lineage_registry.transaction import materialize_synthetic


REVIEW_DECISION_ID = "REVIEW-REAL-CANDIDATE-001"
SUBJECT_PHASE_ID = "REAL-CANDIDATE-SUBJECT-001"
RECEIPT_ID = "REAL-CANDIDATE-RECEIPT-001"
PACKET_ID = "REAL-CANDIDATE-PACKET-001"


def _packet_bytes(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, files[name])
    return output.getvalue()


def make_real_candidate_material(tmp_path: Path) -> dict[str, Any]:
    admin = tmp_path / "admin"
    repository = tmp_path / "repository"
    input_root = admin / "reviewer_inputs"
    artifact_root = admin / "immutable_subject_artifacts"
    admin.mkdir()
    repository.mkdir()
    input_root.mkdir()
    artifact_root.mkdir()

    artifact_bytes = {
        "artifact_alpha.txt": b"real candidate alpha fixture\n",
        "artifact_beta.json": canonical_json_bytes({"fixture": "real-candidate", "value": 2}),
    }
    for name, exact_bytes in artifact_bytes.items():
        (artifact_root / name).write_bytes(exact_bytes)

    packet_bytes = _packet_bytes(artifact_bytes)
    packet_path = input_root / "subject_packet.zip"
    packet_path.write_bytes(packet_bytes)
    artifacts = [
        {
            "relative_path": name,
            "byte_length": len(exact_bytes),
            "sha256": sha256_bytes(exact_bytes),
        }
        for name, exact_bytes in sorted(artifact_bytes.items())
    ]
    manifest = {
        "allow_empty_artifacts": False,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "schema": "quant-subject-artifact-manifest-v0.1",
        "subject_packet_identifier": PACKET_ID,
        "subject_packet_sha256": sha256_bytes(packet_bytes),
        "subject_phase_id": SUBJECT_PHASE_ID,
    }
    manifest_bytes = canonical_json_bytes(manifest)
    payload = {
        "PIT_effect": "NONE",
        "S5_WP04_effect": "BLOCKED",
        "accepted_classification": "REAL_CANDIDATE_REVIEWED_WITH_LIMITATIONS",
        "accepted_verdict": "REAL_CANDIDATE_DRY_RUN_ONLY",
        "authority_effects": {
            "business_authority": "NONE",
            "materialization_authority": "NONE_BY_THIS_REISSUE",
            "research_authority": "NONE",
        },
        "blocker_effects": {"materialization": "RETAINED"},
        "evidence_state_after": "UNCHANGED",
        "evidence_state_before": "UNCHANGED",
        "needs_fix": False,
        "operational_result": "REAL_CANDIDATE_DRY_RUN_REVIEW",
        "privacy_issue_stop": False,
        "prompt_accounting": {"fixture": True},
        "receipt_id": RECEIPT_ID,
        "replay_effect": "NONE",
        "review_decision_id": REVIEW_DECISION_ID,
        "review_limitations": ["Dry run only", "No materialization authority"],
        "review_status": "ACCEPTED_WITH_LIMITATIONS",
        "review_surface": "LOCAL_HUMAN_REVIEW",
        "reviewed_at": "2026-07-12T19:28:04Z",
        "reviewer_alias": "HUMAN_REVIEW_AUTHORITY_001",
        "schema": "quant-human-review-payload-v0.1",
        "subject_artifact_manifest_sha256": sha256_bytes(manifest_bytes),
        "subject_packet_identifier": PACKET_ID,
        "subject_packet_sha256": sha256_bytes(packet_bytes),
        "subject_phase_id": SUBJECT_PHASE_ID,
    }
    payload_bytes = canonical_json_bytes(payload)
    receipt_bytes = (
        "# Real Candidate Review Receipt\n\n"
        f"receipt_id = {RECEIPT_ID}\n"
        f"subject_phase_id = {SUBJECT_PHASE_ID}\n"
        f"review_decision_id = {REVIEW_DECISION_ID}\n"
        "materialization_authorization_id = null\n"
    ).encode("utf-8")
    payload_path = input_root / "human_review_payload.json"
    manifest_path = input_root / "subject_artifact_manifest.json"
    receipt_path = input_root / "review_receipt.md"
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_bytes(manifest_bytes)
    receipt_path.write_bytes(receipt_bytes)
    return {
        "admin": admin,
        "repository": repository,
        "input_root": input_root,
        "artifact_root": artifact_root,
        "artifact_bytes": artifact_bytes,
        "packet_path": packet_path,
        "packet_bytes": packet_bytes,
        "manifest": manifest,
        "manifest_bytes": manifest_bytes,
        "manifest_path": manifest_path,
        "payload": payload,
        "payload_bytes": payload_bytes,
        "payload_path": payload_path,
        "receipt_bytes": receipt_bytes,
        "receipt_path": receipt_path,
        "candidate_root": admin / "future_candidate_pilot" / "registry_candidate",
    }


def call_dry_run(material: dict[str, Any], **overrides: Any):
    kwargs = {
        "approved_admin_root": material["admin"],
        "repository_root": material["repository"],
        "expected_candidate_root": material["candidate_root"],
        "human_review_payload_bytes": material["payload_bytes"],
        "subject_artifact_manifest_bytes": material["manifest_bytes"],
        "subject_packet_path": material["packet_path"],
        "subject_artifact_root": material["artifact_root"],
        "review_receipt_bytes": material["receipt_bytes"],
        "expected_review_decision_id": REVIEW_DECISION_ID,
        "expected_payload_sha256": sha256_bytes(material["payload_bytes"]),
        "expected_subject_manifest_sha256": sha256_bytes(material["manifest_bytes"]),
        "expected_review_receipt_sha256": sha256_bytes(material["receipt_bytes"]),
    }
    candidate_root = overrides.pop("candidate_root", material["candidate_root"])
    kwargs.update(overrides)
    return dry_run_real_candidate(candidate_root, **kwargs)


def assert_stop(material: dict[str, Any], classification: str, **overrides: Any) -> None:
    with pytest.raises(RegistryError) as caught:
        call_dry_run(material, **overrides)
    assert caught.value.classification == classification


def _cli_args(material: dict[str, Any]) -> list[str]:
    return [
        "dry-run-real-candidate",
        "--candidate-root",
        str(material["candidate_root"]),
        "--approved-admin-root",
        str(material["admin"]),
        "--repository-root",
        str(material["repository"]),
        "--expected-candidate-root",
        str(material["candidate_root"]),
        "--payload",
        str(material["payload_path"]),
        "--subject-manifest",
        str(material["manifest_path"]),
        "--subject-packet",
        str(material["packet_path"]),
        "--subject-artifact-root",
        str(material["artifact_root"]),
        "--review-receipt",
        str(material["receipt_path"]),
        "--expected-review-decision-id",
        REVIEW_DECISION_ID,
        "--expected-payload-sha256",
        sha256_bytes(material["payload_bytes"]),
        "--expected-subject-manifest-sha256",
        sha256_bytes(material["manifest_bytes"]),
        "--expected-review-receipt-sha256",
        sha256_bytes(material["receipt_bytes"]),
    ]


def test_valid_real_candidate_dry_run_passes(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    result = call_dry_run(material).to_dict()
    assert result["status"] == "PASS"
    assert result["classification"] == SUCCESS_CLASSIFICATION
    assert result["mode"] == GOVERNED_REAL_CANDIDATE_MODE
    assert result["review_decision_valid"] is True
    assert result["reviewer_input_hashes_valid"] is True
    assert result["subject_packet_valid"] is True
    assert result["subject_artifact_set_valid"] is True


def test_exact_reviewer_payload_hash_is_required(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    assert_stop(material, PAYLOAD_HASH_STOP, expected_payload_sha256="0" * 64)


def test_exact_subject_manifest_hash_is_required(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    assert_stop(material, MANIFEST_HASH_STOP, expected_subject_manifest_sha256="0" * 64)


def test_exact_review_receipt_hash_is_required(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    assert_stop(material, REVIEW_RECEIPT_HASH_STOP, expected_review_receipt_sha256="0" * 64)


@pytest.mark.parametrize(
    "expected_hash",
    ["A" * 64, "a" * 63, "g" * 64],
)
def test_expected_review_receipt_hash_format_is_strict(
    tmp_path: Path, expected_hash: str
) -> None:
    material = make_real_candidate_material(tmp_path)
    assert_stop(
        material,
        REVIEW_RECEIPT_HASH_STOP,
        expected_review_receipt_sha256=expected_hash,
    )


def test_one_byte_review_receipt_mutation_stops_on_hash(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    receipt = material["receipt_bytes"][:-1] + b" "
    assert_stop(material, REVIEW_RECEIPT_HASH_STOP, review_receipt_bytes=receipt)


def test_appended_unapproved_receipt_semantic_stops_on_hash(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    receipt = material["receipt_bytes"] + b"unapproved_reviewer_semantic = SHOULD_NOT_PASS\n"
    assert_stop(material, REVIEW_RECEIPT_HASH_STOP, review_receipt_bytes=receipt)


def test_review_decision_id_mismatch_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    assert_stop(material, REVIEW_DECISION_STOP, expected_review_decision_id="REVIEW-WRONG")


def test_missing_reviewed_at_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    payload = dict(material["payload"])
    payload.pop("reviewed_at")
    payload_bytes = canonical_json_bytes(payload)
    assert_stop(
        material,
        REVIEW_DECISION_STOP,
        human_review_payload_bytes=payload_bytes,
        expected_payload_sha256=sha256_bytes(payload_bytes),
    )


def test_runtime_only_reviewer_field_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    payload = dict(material["payload"])
    payload["materialized_at"] = "2026-01-01T00:00:00Z"
    payload_bytes = canonical_json_bytes(payload)
    assert_stop(
        material,
        RUNTIME_FIELD_STOP,
        human_review_payload_bytes=payload_bytes,
        expected_payload_sha256=sha256_bytes(payload_bytes),
    )


@pytest.mark.parametrize("field", ["subject_phase_id", "receipt_id"])
def test_review_receipt_logical_id_mismatch_stops(tmp_path: Path, field: str) -> None:
    material = make_real_candidate_material(tmp_path)
    original = SUBJECT_PHASE_ID if field == "subject_phase_id" else RECEIPT_ID
    receipt = material["receipt_bytes"].replace(original.encode(), b"WRONG-LOGICAL-ID")
    assert_stop(
        material,
        REVIEW_RECEIPT_STOP,
        review_receipt_bytes=receipt,
        expected_review_receipt_sha256=sha256_bytes(receipt),
    )


def test_review_receipt_materialization_authority_not_null_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    receipt = material["receipt_bytes"].replace(
        b"materialization_authorization_id = null",
        b"materialization_authorization_id = REAL-AUTH-001",
    )
    assert_stop(
        material,
        REVIEW_RECEIPT_STOP,
        review_receipt_bytes=receipt,
        expected_review_receipt_sha256=sha256_bytes(receipt),
    )


def test_review_receipt_exact_review_decision_field_line_is_required(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    receipt = material["receipt_bytes"].replace(
        f"review_decision_id = {REVIEW_DECISION_ID}\n".encode(), b""
    )
    assert_stop(
        material,
        REVIEW_RECEIPT_STOP,
        review_receipt_bytes=receipt,
        expected_review_receipt_sha256=sha256_bytes(receipt),
    )


def test_review_receipt_substring_only_review_decision_does_not_pass(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    receipt = material["receipt_bytes"].replace(
        f"review_decision_id = {REVIEW_DECISION_ID}".encode(),
        f"note = reviewed under {REVIEW_DECISION_ID}".encode(),
    )
    assert_stop(
        material,
        REVIEW_RECEIPT_STOP,
        review_receipt_bytes=receipt,
        expected_review_receipt_sha256=sha256_bytes(receipt),
    )


def test_duplicate_contradictory_review_decision_lines_stop(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    receipt = material["receipt_bytes"] + b"review_decision_id = REVIEW-CONTRADICTORY\n"
    assert_stop(
        material,
        REVIEW_RECEIPT_STOP,
        review_receipt_bytes=receipt,
        expected_review_receipt_sha256=sha256_bytes(receipt),
    )


def test_duplicate_contradictory_materialization_authority_lines_stop(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    receipt = material["receipt_bytes"] + b"materialization_authorization_id = REAL-AUTH-001\n"
    assert_stop(
        material,
        REVIEW_RECEIPT_STOP,
        review_receipt_bytes=receipt,
        expected_review_receipt_sha256=sha256_bytes(receipt),
    )


def test_packet_hash_mismatch_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    material["packet_path"].write_bytes(material["packet_bytes"] + b"changed")
    assert_stop(material, PACKET_HASH_STOP)


def test_missing_artifact_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    (material["artifact_root"] / "artifact_alpha.txt").unlink()
    assert_stop(material, ARTIFACT_SET_STOP)


def test_extra_artifact_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    (material["artifact_root"] / "extra.txt").write_text("extra", encoding="utf-8")
    assert_stop(material, ARTIFACT_SET_STOP)


def test_artifact_byte_mismatch_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    (material["artifact_root"] / "artifact_alpha.txt").write_bytes(b"changed\n")
    assert_stop(material, ARTIFACT_SET_STOP)


def test_candidate_root_already_exists_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    material["candidate_root"].mkdir(parents=True)
    assert_stop(material, CANDIDATE_EXISTS_STOP)


def test_candidate_root_inside_repository_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    candidate = material["repository"] / "candidate" / "registry_candidate"
    assert_stop(
        material,
        CANDIDATE_UNSAFE_STOP,
        candidate_root=candidate,
        expected_candidate_root=candidate,
    )


@pytest.mark.parametrize("descendant", [False, True])
def test_candidate_root_equal_or_descendant_of_live_root_stops(
    tmp_path: Path, descendant: bool
) -> None:
    material = make_real_candidate_material(tmp_path)
    live = material["admin"] / "accepted_lineage_registry_v0_1"
    candidate = live / "child" if descendant else live
    assert_stop(
        material,
        LIVE_COLLISION_STOP,
        candidate_root=candidate,
        expected_candidate_root=candidate,
    )


def test_candidate_root_inside_immutable_packet_root_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    candidate = material["input_root"] / "candidate" / "registry_candidate"
    assert_stop(
        material,
        CANDIDATE_UNSAFE_STOP,
        candidate_root=candidate,
        expected_candidate_root=candidate,
    )


def test_candidate_root_outside_approved_admin_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    candidate = tmp_path / "outside" / "registry_candidate"
    assert_stop(
        material,
        CANDIDATE_UNSAFE_STOP,
        candidate_root=candidate,
        expected_candidate_root=candidate,
    )


def test_materialization_authorization_id_supplied_to_dry_run_stops(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    assert_stop(
        material,
        AUTHORITY_PRESENT_STOP,
        materialization_authorization_id="UNAUTHORIZED-DRY-RUN-MATERIALIZATION-ID",
    )


def test_valid_result_reports_materialization_not_ready_and_no_active_authority(
    tmp_path: Path,
) -> None:
    material = make_real_candidate_material(tmp_path)
    result = call_dry_run(material).to_dict()
    assert result["materialization_authorization_present"] is False
    assert result["materialization_ready"] is False
    assert result["next_task_authorized_by_registry"] is False
    assert result["would_stop_materialization_with"] == "MATERIALIZATION_EXACT_APPROVAL_MISSING_STOP"
    for field in (
        "candidate_root_created",
        "acceptance_entry_created",
        "runtime_manifest_created",
        "entry_seal_created",
        "derived_index_created",
        "live_registry_created",
    ):
        assert result[field] is False


def test_valid_dry_run_creates_no_registry_root_or_parent(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    candidate_parent = material["candidate_root"].parent
    assert not candidate_parent.exists()
    call_dry_run(material)
    assert not candidate_parent.exists()
    assert not material["candidate_root"].exists()


def test_dry_run_result_is_deterministic_across_two_calls(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    left = canonical_json_bytes(call_dry_run(material).to_dict())
    right = canonical_json_bytes(call_dry_run(material).to_dict())
    assert left == right


def test_dry_run_identity_contains_all_three_reviewer_input_hashes(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    identity = call_dry_run(material).to_dict()["dry_run_input_identity"]
    assert identity["human_review_payload_sha256"] == sha256_bytes(material["payload_bytes"])
    assert identity["subject_artifact_manifest_sha256"] == sha256_bytes(
        material["manifest_bytes"]
    )
    assert identity["review_receipt_sha256"] == sha256_bytes(material["receipt_bytes"])


def test_existing_materialize_synthetic_rejects_real_payload(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    synthetic_root = material["admin"] / "synthetic_real_payload_registry"
    with pytest.raises(RegistryError) as caught:
        materialize_synthetic(
            synthetic_root,
            approved_admin_root=material["admin"],
            repository_root=material["repository"],
            expected_registry_root=synthetic_root,
            subject_packet_path=material["packet_path"],
            subject_artifact_root=material["artifact_root"],
            human_review_payload_bytes=material["payload_bytes"],
            subject_artifact_manifest_bytes=material["manifest_bytes"],
            review_receipt_bytes=material["receipt_bytes"],
            materialization_authorization_id="SYNTHETIC-AUTH-ONLY",
        )
    assert caught.value.classification == "LIVE_REGISTRY_MODE_NOT_AUTHORIZED_STOP"
    assert not synthetic_root.exists()


def test_existing_synthetic_workflow_remains_passing(tmp_path: Path) -> None:
    material = make_synthetic_material(tmp_path)
    result = materialize_synthetic(
        material["registry_root"],
        **materialization_kwargs(material),
        materialization_authorization_id="SYNTHETIC-REGRESSION-AUTH-001",
    )
    assert result.classification == "NEW_ENTRY_MATERIALIZED_SUCCESSFULLY"
    assert result.materialization_verified is True


def test_platform_limitations_are_explicit_without_unsupported_pass(tmp_path: Path) -> None:
    material = make_real_candidate_material(tmp_path)
    result = call_dry_run(material).to_dict()
    assert isinstance(result["platform_limitations"], list)
    if result["platform_limitations"]:
        assert result["platform_control_status"] == "PASS_WITH_EXPLICIT_PLATFORM_LIMITATIONS"
    else:
        assert result["platform_control_status"] == "PASS"


def test_cli_valid_dry_run_is_byte_deterministic_and_path_private(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    material = make_real_candidate_material(tmp_path)
    args = _cli_args(material)
    assert cli_run(args) == 0
    first = capsys.readouterr().out
    assert cli_run(args) == 0
    second = capsys.readouterr().out
    assert first == second
    output = json.loads(first)
    assert output["classification"] == SUCCESS_CLASSIFICATION
    assert output["reviewer_input_hashes_valid"] is True
    assert output["dry_run_input_identity"]["review_receipt_sha256"] == sha256_bytes(
        material["receipt_bytes"]
    )
    assert str(tmp_path) not in first
    assert not material["candidate_root"].exists()


def test_cli_requires_expected_review_receipt_sha256(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    material = make_real_candidate_material(tmp_path)
    args = _cli_args(material)
    flag_index = args.index("--expected-review-receipt-sha256")
    del args[flag_index : flag_index + 2]
    with pytest.raises(SystemExit) as caught:
        cli_run(args)
    assert caught.value.code == 2
    assert "--expected-review-receipt-sha256" in capsys.readouterr().err


def test_cli_passes_expected_review_receipt_sha256_to_api(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    material = make_real_candidate_material(tmp_path)
    args = _cli_args(material)
    hash_index = args.index("--expected-review-receipt-sha256") + 1
    args[hash_index] = "0" * 64
    assert cli_run(args) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "STOP"
    assert output["classification"] == REVIEW_RECEIPT_HASH_STOP
    assert not material["candidate_root"].exists()


def test_cli_materialization_authority_present_stops_before_input_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    material = make_real_candidate_material(tmp_path)
    args = _cli_args(material) + [
        "--materialization-authorization-id",
        "UNAUTHORIZED-DRY-RUN-MATERIALIZATION-ID",
    ]
    assert cli_run(args) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "STOP"
    assert output["classification"] == AUTHORITY_PRESENT_STOP
    assert not material["candidate_root"].exists()
