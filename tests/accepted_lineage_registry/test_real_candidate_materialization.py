from __future__ import annotations

import io
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes, sha256_bytes
from quant_replay_system.accepted_lineage_registry.cli import build_parser, run as cli_run
from quant_replay_system.accepted_lineage_registry.health import registry_health
from quant_replay_system.accepted_lineage_registry.index import regenerate_index, verify_index
from quant_replay_system.accepted_lineage_registry.models import (
    GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
    RegistryError,
)
from quant_replay_system.accepted_lineage_registry.real_candidate_materialization import (
    ARTIFACT_SET_MISMATCH_STOP,
    AUTHORIZATION_MISMATCH_STOP,
    AUTHORIZATION_MISSING_STOP,
    AUTHORIZATION_NOT_DISTINCT_STOP,
    IDEMPOTENT_CLASSIFICATION,
    LIVE_ROOT_COLLISION_STOP,
    PACKET_HASH_MISMATCH_STOP,
    RECEIPT_COLLISION_STOP,
    REVIEW_DECISION_MISMATCH_STOP,
    REVIEWER_INPUT_HASH_MISMATCH_STOP,
    ROOT_ALREADY_EXISTS_STOP,
    ROOT_UNSAFE_STOP,
    RUNTIME_FIELD_PRESENT_STOP,
    SUCCESS_CLASSIFICATION,
    materialize_real_candidate,
)
from quant_replay_system.accepted_lineage_registry.verification import preflight_next_task, verify_entry


SUBJECT_ID = "SYNTHETIC-REAL-CANDIDATE-SUPPORT-SUBJECT-001"
RECEIPT_ID = "SYNTHETIC-REAL-CANDIDATE-SUPPORT-RECEIPT-001"
REVIEW_ID = "SYNTHETIC-REAL-CANDIDATE-SUPPORT-REVIEW-001"
PACKET_ID = "SYNTHETIC-REAL-CANDIDATE-SUPPORT-PACKET-001"
AUTHORIZATION_ID = "SYNTHETIC-REAL-CANDIDATE-SUPPORT-AUTH-001"
FIXED_TIME = datetime(2026, 7, 13, 1, 2, 3, tzinfo=timezone.utc)


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


def make_candidate_material(tmp_path: Path) -> dict[str, Any]:
    admin = tmp_path / "admin"
    repository = tmp_path / "repository"
    input_root = admin / "synthetic_reviewer_inputs"
    artifact_root = admin / "synthetic_subject_artifacts"
    for root in (admin, repository, input_root, artifact_root):
        root.mkdir()

    artifact_bytes = {
        "metadata/summary.txt": b"synthetic real-candidate support fixture\n",
        "tables/rows.csv": b"fixture_id,value\nA,1\nB,2\n",
    }
    for relative_path, exact_bytes in artifact_bytes.items():
        target = artifact_root / Path(*relative_path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(exact_bytes)
    packet_bytes = _packet_bytes(artifact_bytes)
    packet_path = input_root / "synthetic_subject_packet.zip"
    packet_path.write_bytes(packet_bytes)
    artifacts = [
        {
            "relative_path": relative_path,
            "byte_length": len(exact_bytes),
            "sha256": sha256_bytes(exact_bytes),
        }
        for relative_path, exact_bytes in sorted(artifact_bytes.items())
    ]
    manifest = {
        "allow_empty_artifacts": False,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "schema": "quant-synthetic-real-candidate-subject-manifest-v0.1",
        "subject_packet_identifier": PACKET_ID,
        "subject_packet_sha256": sha256_bytes(packet_bytes),
        "subject_phase_id": SUBJECT_ID,
    }
    manifest_bytes = canonical_json_bytes(manifest)
    payload = {
        "PIT_effect": "NONE",
        "S5_WP04_effect": "NONE",
        "accepted_classification": "SYNTHETIC_REAL_CANDIDATE_SUPPORT_ONLY",
        "accepted_verdict": "SYNTHETIC_NON_LIVE_CANDIDATE_ONLY",
        "authority_effects": {
            "business_authority": "NONE",
            "materialization_authority": "NONE_BY_THIS_REISSUE",
            "research_authority": "NONE",
        },
        "blocker_effects": {"live_registry": "RETAINED"},
        "evidence_state_after": "SYNTHETIC_UNCHANGED",
        "evidence_state_before": "SYNTHETIC_UNCHANGED",
        "needs_fix": False,
        "operational_result": "SYNTHETIC_GOVERNED_CANDIDATE_SUPPORT",
        "privacy_issue_stop": False,
        "prompt_accounting": {"synthetic": True},
        "receipt_id": RECEIPT_ID,
        "replay_effect": "NONE",
        "review_decision_id": REVIEW_ID,
        "review_limitations": ["Synthetic fixture only", "No live registry authority"],
        "review_status": "ACCEPTED_WITH_LIMITATIONS",
        "review_surface": "LOCAL_SYNTHETIC_TEST",
        "reviewed_at": "2026-07-13T01:00:00Z",
        "reviewer_alias": "synthetic-reviewer",
        "schema": "quant-human-review-payload-v0.1",
        "subject_artifact_manifest_sha256": sha256_bytes(manifest_bytes),
        "subject_packet_identifier": PACKET_ID,
        "subject_packet_sha256": sha256_bytes(packet_bytes),
        "subject_phase_id": SUBJECT_ID,
    }
    payload_bytes = canonical_json_bytes(payload)
    receipt_bytes = (
        "# Synthetic Real Candidate Support Receipt\n\n"
        f"receipt_id = {RECEIPT_ID}\n"
        f"subject_phase_id = {SUBJECT_ID}\n"
        f"review_decision_id = {REVIEW_ID}\n"
        "materialization_authorization_id = null\n"
    ).encode("utf-8")
    paths = {
        "payload_path": input_root / "human_review_payload.json",
        "manifest_path": input_root / "materialization_subject_artifact_manifest.json",
        "receipt_path": input_root / "reviewer_payload_reissue_receipt.md",
    }
    paths["payload_path"].write_bytes(payload_bytes)
    paths["manifest_path"].write_bytes(manifest_bytes)
    paths["receipt_path"].write_bytes(receipt_bytes)
    return {
        "admin": admin,
        "repository": repository,
        "input_root": input_root,
        "artifact_root": artifact_root,
        "artifact_bytes": artifact_bytes,
        "packet_bytes": packet_bytes,
        "packet_path": packet_path,
        "manifest": manifest,
        "manifest_bytes": manifest_bytes,
        "payload": payload,
        "payload_bytes": payload_bytes,
        "receipt_bytes": receipt_bytes,
        "candidate_root": admin / "governed_candidate_registry",
        "future_live_root": admin / "accepted_lineage_registry_v0_1",
        **paths,
    }


def call_materialize(material: dict[str, Any], **overrides: Any):
    kwargs = {
        "approved_admin_root": material["admin"],
        "repository_root": material["repository"],
        "expected_candidate_root": material["candidate_root"],
        "future_live_registry_root": material["future_live_root"],
        "human_review_payload_bytes": material["payload_bytes"],
        "subject_artifact_manifest_bytes": material["manifest_bytes"],
        "subject_packet_path": material["packet_path"],
        "subject_artifact_root": material["artifact_root"],
        "review_receipt_bytes": material["receipt_bytes"],
        "expected_review_decision_id": REVIEW_ID,
        "expected_payload_sha256": sha256_bytes(material["payload_bytes"]),
        "expected_subject_manifest_sha256": sha256_bytes(material["manifest_bytes"]),
        "expected_review_receipt_sha256": sha256_bytes(material["receipt_bytes"]),
        "materialization_authorization_id": AUTHORIZATION_ID,
        "expected_materialization_authorization_id": AUTHORIZATION_ID,
        "operator_alias": "synthetic-candidate-operator",
        "operation_id": "synthetic-candidate-operation-001",
        "materialized_at": FIXED_TIME,
    }
    root = overrides.pop("root", material["candidate_root"])
    kwargs.update(overrides)
    return materialize_real_candidate(root, **kwargs)


def assert_stop(material: dict[str, Any], classification: str, **overrides: Any) -> None:
    with pytest.raises(RegistryError) as caught:
        call_materialize(material, **overrides)
    assert caught.value.classification == classification


def candidate_authority(material: dict[str, Any]) -> dict[str, Any]:
    return {
        "approved_admin_root": material["admin"],
        "repository_root": material["repository"],
        "expected_registry_root": material["candidate_root"],
        "protected_roots": (material["future_live_root"],),
        "registry_mode": GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
    }


@pytest.mark.parametrize(
    ("current", "expected"),
    [(None, AUTHORIZATION_ID), (AUTHORIZATION_ID, None), ("", AUTHORIZATION_ID), (AUTHORIZATION_ID, "")],
)
def test_missing_or_empty_materialization_authorization_stops(tmp_path: Path, current: str | None, expected: str | None) -> None:
    material = make_candidate_material(tmp_path)
    assert_stop(
        material,
        AUTHORIZATION_MISSING_STOP,
        materialization_authorization_id=current,
        expected_materialization_authorization_id=expected,
    )


def test_mismatched_materialization_authorization_stops(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    assert_stop(material, AUTHORIZATION_MISMATCH_STOP, expected_materialization_authorization_id="SYNTHETIC-DIFFERENT-AUTH")


def test_materialization_authorization_equal_to_review_decision_stops_before_candidate_root(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    assert_stop(
        material,
        AUTHORIZATION_NOT_DISTINCT_STOP,
        materialization_authorization_id=REVIEW_ID,
        expected_materialization_authorization_id=REVIEW_ID,
    )
    assert not material["candidate_root"].exists()


def test_materialization_authorization_equal_to_receipt_id_stops_before_candidate_root(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    assert_stop(
        material,
        AUTHORIZATION_NOT_DISTINCT_STOP,
        materialization_authorization_id=RECEIPT_ID,
        expected_materialization_authorization_id=RECEIPT_ID,
    )
    assert not material["candidate_root"].exists()


def test_non_nfc_authorization_stops(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    unstable = "SYNTHETIC-AUTH-e\u0301"
    assert_stop(
        material,
        AUTHORIZATION_MISMATCH_STOP,
        materialization_authorization_id=unstable,
        expected_materialization_authorization_id=unstable,
    )


def test_review_decision_id_mismatch_stops(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    assert_stop(material, REVIEW_DECISION_MISMATCH_STOP, expected_review_decision_id="SYNTHETIC-WRONG-REVIEW")


@pytest.mark.parametrize(
    "field",
    ["expected_payload_sha256", "expected_subject_manifest_sha256", "expected_review_receipt_sha256"],
)
def test_reviewer_input_hash_mismatch_stops(tmp_path: Path, field: str) -> None:
    material = make_candidate_material(tmp_path)
    assert_stop(material, REVIEWER_INPUT_HASH_MISMATCH_STOP, **{field: "0" * 64})


def test_reviewer_input_hash_format_is_strict(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    assert_stop(material, REVIEWER_INPUT_HASH_MISMATCH_STOP, expected_payload_sha256="NOT-A-HASH")


def test_runtime_only_field_in_reviewer_payload_stops(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    payload = {**material["payload"], "candidate_registry": True}
    payload_bytes = canonical_json_bytes(payload)
    assert_stop(
        material,
        RUNTIME_FIELD_PRESENT_STOP,
        human_review_payload_bytes=payload_bytes,
        expected_payload_sha256=sha256_bytes(payload_bytes),
    )


def test_packet_hash_mismatch_stops(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    material["packet_path"].write_bytes(material["packet_bytes"] + b"changed")
    assert_stop(material, PACKET_HASH_MISMATCH_STOP)


def test_artifact_set_mismatch_stops(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    (material["artifact_root"] / "metadata" / "summary.txt").write_bytes(b"changed")
    assert_stop(material, ARTIFACT_SET_MISMATCH_STOP)


@pytest.mark.parametrize("location", ["outside", "repository"])
def test_candidate_root_outside_authorized_surface_stops(tmp_path: Path, location: str) -> None:
    material = make_candidate_material(tmp_path)
    root = tmp_path / "outside_candidate" if location == "outside" else material["repository"] / "candidate_registry"
    assert_stop(material, ROOT_UNSAFE_STOP, root=root, expected_candidate_root=root)


@pytest.mark.parametrize("location", ["equal", "below"])
def test_candidate_root_live_collision_stops(tmp_path: Path, location: str) -> None:
    material = make_candidate_material(tmp_path)
    root = material["future_live_root"] if location == "equal" else material["future_live_root"] / "candidate_registry"
    assert_stop(material, LIVE_ROOT_COLLISION_STOP, root=root, expected_candidate_root=root)


def test_existing_future_live_root_stops(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    material["future_live_root"].mkdir()
    assert_stop(material, LIVE_ROOT_COLLISION_STOP)


def test_unexpected_existing_candidate_root_stops(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    material["candidate_root"].mkdir()
    (material["candidate_root"] / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    assert_stop(material, ROOT_ALREADY_EXISTS_STOP)


def test_valid_candidate_materialization_succeeds(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    result = call_materialize(material)
    assert result.classification == SUCCESS_CLASSIFICATION
    assert result.materialization_verified is True


def test_exact_five_file_candidate_entry_verifies(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    result = call_materialize(material)
    entry = material["candidate_root"] / "entries" / result.subject_key / result.receipt_key
    assert sorted(path.name for path in entry.iterdir()) == sorted(
        ["human_review_payload.json", "subject_artifact_manifest.json", "review_receipt.md", "entry_manifest.json", "entry_seal.json"]
    )
    verified = verify_entry(
        material["candidate_root"],
        result.subject_key,
        result.receipt_key,
        subject_packet_path=material["packet_path"],
        subject_artifact_root=material["artifact_root"],
        **candidate_authority(material),
    )
    assert verified["status"] == "PASS"
    assert verified["candidate_registry"] is True


def test_candidate_policy_records_non_live_mode_and_no_authority(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    call_materialize(material)
    policy = json.loads((material["candidate_root"] / "registry_policy.json").read_text(encoding="utf-8"))
    assert policy["registry_mode"] == GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE
    assert policy["candidate_registry"] is True
    assert policy["live_registry"] is False
    assert policy["next_task_authorized_by_registry"] is False
    assert policy["Stage1B_A_authority"] == "none_by_mode"


def test_runtime_manifest_records_required_candidate_metadata(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    result = call_materialize(material)
    path = material["candidate_root"] / "entries" / result.subject_key / result.receipt_key / "entry_manifest.json"
    runtime = json.loads(path.read_text(encoding="utf-8"))
    assert runtime["mode"] == GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE
    assert runtime["materialization_authorization_id"] == AUTHORIZATION_ID
    assert runtime["review_decision_id"] == REVIEW_ID
    assert runtime["artifact_verification_result"] == "PASS"
    assert runtime["candidate_registry"] is True
    assert runtime["live_registry"] is False


def test_reviewer_and_subject_inputs_remain_byte_identical(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    before = {
        "payload": material["payload_path"].read_bytes(),
        "manifest": material["manifest_path"].read_bytes(),
        "receipt": material["receipt_path"].read_bytes(),
        "packet": material["packet_path"].read_bytes(),
        "artifacts": {name: (material["artifact_root"] / Path(*name.split("/"))).read_bytes() for name in material["artifact_bytes"]},
    }
    call_materialize(material)
    assert material["payload_path"].read_bytes() == before["payload"]
    assert material["manifest_path"].read_bytes() == before["manifest"]
    assert material["receipt_path"].read_bytes() == before["receipt"]
    assert material["packet_path"].read_bytes() == before["packet"]
    assert {name: (material["artifact_root"] / Path(*name.split("/"))).read_bytes() for name in material["artifact_bytes"]} == before["artifacts"]


def test_identical_replay_is_idempotent_and_keeps_timestamp(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    first = call_materialize(material)
    entry_manifest = material["candidate_root"] / "entries" / first.subject_key / first.receipt_key / "entry_manifest.json"
    before = entry_manifest.read_bytes()
    replay = call_materialize(material, materialized_at=datetime(2030, 1, 1, tzinfo=timezone.utc))
    assert replay.classification == IDEMPOTENT_CLASSIFICATION
    assert replay.idempotent_replay is True
    assert entry_manifest.read_bytes() == before


def test_changed_matching_authorization_does_not_redefine_immutable_identity(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    call_materialize(material)
    replay = call_materialize(
        material,
        materialization_authorization_id="SYNTHETIC-REAL-CANDIDATE-SUPPORT-AUTH-002",
        expected_materialization_authorization_id="SYNTHETIC-REAL-CANDIDATE-SUPPORT-AUTH-002",
    )
    assert replay.classification == IDEMPOTENT_CLASSIFICATION


def test_conflicting_reviewer_payload_stops_as_receipt_collision(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    call_materialize(material)
    payload = {**material["payload"], "review_limitations": ["Synthetic changed limitation"]}
    payload_bytes = canonical_json_bytes(payload)
    assert_stop(
        material,
        RECEIPT_COLLISION_STOP,
        human_review_payload_bytes=payload_bytes,
        expected_payload_sha256=sha256_bytes(payload_bytes),
    )


def test_derived_index_and_health_pass(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    call_materialize(material)
    assert verify_index(material["candidate_root"], **candidate_authority(material))["status"] == "PASS"
    assert regenerate_index(material["candidate_root"], **candidate_authority(material))["status"] == "PASS"
    health = registry_health(material["candidate_root"], **candidate_authority(material))
    assert health.entry_verification_status == "PASS"
    assert health.derived_index_status == "PASS"
    assert health.privacy_warnings == ()


def test_missing_next_task_approval_stops_and_registry_never_authorizes(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    result = call_materialize(material)
    with pytest.raises(RegistryError) as caught:
        preflight_next_task(
            material["candidate_root"],
            result.subject_key,
            result.receipt_key,
            current_task_approval_id=None,
            **candidate_authority(material),
        )
    assert caught.value.classification == "NEXT_TASK_EXACT_APPROVAL_MISSING_STOP"
    allowed = preflight_next_task(
        material["candidate_root"],
        result.subject_key,
        result.receipt_key,
        current_task_approval_id="SYNTHETIC-CURRENT-TASK-APPROVAL-001",
        **candidate_authority(material),
    )
    assert allowed.next_task_authorized_by_registry is False


def test_live_registry_mode_remains_unavailable(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    result = call_materialize(material)
    authority = candidate_authority(material)
    authority["registry_mode"] = "LIVE_REGISTRY"
    with pytest.raises(RegistryError) as caught:
        verify_entry(material["candidate_root"], result.subject_key, result.receipt_key, **authority)
    assert caught.value.classification == "LIVE_REGISTRY_MODE_NOT_AUTHORIZED_STOP"


def test_failure_before_authoritative_rename_leaves_no_entry(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    assert_stop(material, "ATOMIC_WRITE_FAILED_NO_AUTHORITATIVE_ENTRY_CREATED", failure_injection="before_rename")
    assert list((material["candidate_root"] / "entries").rglob("human_review_payload.json")) == []


def test_index_failure_after_verified_entry_preserves_entry_and_marks_stale(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    result = call_materialize(material, failure_injection="after_rename_before_index")
    assert result.classification == "DERIVED_INDEX_REGENERATION_FAILED_ENTRY_VERIFIED_INDEX_STALE"
    assert result.entry_verified is True
    assert verify_index(material["candidate_root"], **candidate_authority(material))["status"] == "STALE"


def test_temporary_candidate_root_can_be_cleaned_without_input_changes(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    call_materialize(material)
    shutil.rmtree(material["candidate_root"])
    assert not material["candidate_root"].exists()
    assert material["packet_path"].exists()
    assert material["artifact_root"].exists()


def test_fixture_identifiers_are_synthetic_only(tmp_path: Path) -> None:
    material = make_candidate_material(tmp_path)
    assert material["payload"]["subject_phase_id"].startswith("SYNTHETIC-")
    assert material["payload"]["receipt_id"].startswith("SYNTHETIC-")
    assert material["payload"]["review_decision_id"].startswith("SYNTHETIC-")


def test_cli_parser_keeps_existing_modes_and_adds_materialization() -> None:
    parser = build_parser()
    choices = next(action for action in parser._actions if action.dest == "command").choices
    assert {"materialize-synthetic", "dry-run-real-candidate", "materialize-real-candidate"}.issubset(choices)


def _cli_args(material: dict[str, Any]) -> list[str]:
    return [
        "materialize-real-candidate",
        "--root", str(material["candidate_root"]),
        "--approved-admin-root", str(material["admin"]),
        "--repository-root", str(material["repository"]),
        "--expected-candidate-root", str(material["candidate_root"]),
        "--future-live-registry-root", str(material["future_live_root"]),
        "--payload", str(material["payload_path"]),
        "--subject-manifest", str(material["manifest_path"]),
        "--subject-packet", str(material["packet_path"]),
        "--subject-artifact-root", str(material["artifact_root"]),
        "--review-receipt", str(material["receipt_path"]),
        "--expected-review-decision-id", REVIEW_ID,
        "--expected-payload-sha256", sha256_bytes(material["payload_bytes"]),
        "--expected-subject-manifest-sha256", sha256_bytes(material["manifest_bytes"]),
        "--expected-review-receipt-sha256", sha256_bytes(material["receipt_bytes"]),
        "--materialization-authorization-id", AUTHORIZATION_ID,
        "--expected-materialization-authorization-id", AUTHORIZATION_ID,
        "--operator-alias", "synthetic-cli-operator",
        "--operation-id", "synthetic-cli-operation-001",
        "--materialized-at", "2026-07-13T01:02:03Z",
    ]


def test_cli_materialize_and_idempotent_replay(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    material = make_candidate_material(tmp_path)
    assert cli_run(_cli_args(material)) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["classification"] == SUCCESS_CLASSIFICATION
    assert cli_run(_cli_args(material)) == 0
    replay = json.loads(capsys.readouterr().out)
    assert replay["classification"] == IDEMPOTENT_CLASSIFICATION


def test_cli_authorization_mismatch_returns_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    material = make_candidate_material(tmp_path)
    args = _cli_args(material)
    index = args.index("--expected-materialization-authorization-id") + 1
    args[index] = "SYNTHETIC-DIFFERENT-AUTH"
    assert cli_run(args) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["classification"] == AUTHORIZATION_MISMATCH_STOP


def test_cli_authorization_equal_to_review_decision_returns_two_before_candidate_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    material = make_candidate_material(tmp_path)
    args = _cli_args(material)
    for flag in ("--materialization-authorization-id", "--expected-materialization-authorization-id"):
        args[args.index(flag) + 1] = REVIEW_ID
    assert cli_run(args) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["classification"] == AUTHORIZATION_NOT_DISTINCT_STOP
    assert not material["candidate_root"].exists()


def test_cli_authorization_equal_to_receipt_id_returns_two_before_candidate_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    material = make_candidate_material(tmp_path)
    args = _cli_args(material)
    for flag in ("--materialization-authorization-id", "--expected-materialization-authorization-id"):
        args[args.index(flag) + 1] = RECEIPT_ID
    assert cli_run(args) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["classification"] == AUTHORIZATION_NOT_DISTINCT_STOP
    assert not material["candidate_root"].exists()
