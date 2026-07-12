from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes, sha256_bytes
from quant_replay_system.accepted_lineage_registry.transaction import materialize_synthetic


FIXED_TIME = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def _synthetic_packet_bytes() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        info = zipfile.ZipInfo("SYNTHETIC_PACKET_NOTICE.txt", date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_STORED
        archive.writestr(info, b"Synthetic packet bytes only.\n")
    return output.getvalue()


def make_synthetic_material(
    base_dir: Path,
    *,
    subject_phase_id: str = "SYNTHETIC-SUBJECT-001",
    receipt_id: str = "SYNTHETIC-RECEIPT-001",
    payload_overrides: dict[str, Any] | None = None,
    manifest_overrides: dict[str, Any] | None = None,
    approved_admin_root: Path | None = None,
    repository_root: Path | None = None,
    registry_root: Path | None = None,
) -> dict[str, Any]:
    base_dir = Path(base_dir)
    if approved_admin_root is None:
        approved_admin_root = base_dir / "admin"
        repository_root = base_dir / "repository"
        input_root = approved_admin_root / "synthetic_review"
        registry_root = input_root / "synthetic_registry"
    else:
        assert repository_root is not None
        assert registry_root is not None
        input_root = base_dir
    approved_admin_root.mkdir(parents=True, exist_ok=True)
    repository_root.mkdir(parents=True, exist_ok=True)
    input_root.mkdir(parents=True, exist_ok=True)

    subject_packet_path = input_root / "synthetic_subject_packet.zip"
    subject_packet_bytes = _synthetic_packet_bytes()
    subject_packet_path.write_bytes(subject_packet_bytes)
    subject_packet_sha256 = sha256_bytes(subject_packet_bytes)

    subject_artifact_root = input_root / "synthetic_subject_artifacts"
    artifact_bytes = {
        "metadata/summary.txt": b"synthetic summary only\n",
        "tables/rows.csv": b"synthetic_id,synthetic_value\nA,1\nB,2\n",
    }
    for relative_path, exact_bytes in artifact_bytes.items():
        target = subject_artifact_root / Path(*relative_path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(exact_bytes)
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
        "schema": "quant-synthetic-subject-artifact-manifest-v0.1",
        "subject_packet_identifier": "SYNTHETIC-PACKET-001",
        "subject_packet_sha256": subject_packet_sha256,
        "subject_phase_id": subject_phase_id,
    }
    manifest.update(manifest_overrides or {})
    manifest_bytes = canonical_json_bytes(manifest)
    payload = {
        "PIT_effect": "NONE",
        "S5_WP04_effect": "NONE",
        "accepted_classification": "SYNTHETIC_ACCEPTED_LINEAGE_FIXTURE_ONLY",
        "accepted_verdict": "SYNTHETIC_ONLY_NOT_A_PILOT",
        "authority_effects": {"registry_recording": "SYNTHETIC_ONLY"},
        "blocker_effects": {},
        "evidence_state_after": "SYNTHETIC_UNCHANGED",
        "evidence_state_before": "SYNTHETIC_UNCHANGED",
        "needs_fix": False,
        "operational_result": "SYNTHETIC_VALIDATION_ONLY",
        "privacy_issue_stop": False,
        "prompt_accounting": {"synthetic": True},
        "receipt_id": receipt_id,
        "replay_effect": "NONE",
        "review_decision_id": "SYNTHETIC-REVIEW-DECISION-001",
        "review_limitations": ["Synthetic fixture only", "Not a pilot"],
        "review_status": "ACCEPTED_WITH_LIMITATIONS",
        "review_surface": "LOCAL_SYNTHETIC_TEST",
        "reviewed_at": "2026-01-02T03:04:05Z",
        "reviewer_alias": "synthetic-reviewer",
        "schema": "quant-human-review-payload-v0.1",
        "subject_artifact_manifest_sha256": sha256_bytes(manifest_bytes),
        "subject_packet_identifier": str(manifest["subject_packet_identifier"]),
        "subject_packet_sha256": str(manifest["subject_packet_sha256"]),
        "subject_phase_id": subject_phase_id,
    }
    payload.update(payload_overrides or {})
    payload_bytes = canonical_json_bytes(payload)
    receipt_bytes = (
        "# Synthetic Review Receipt\n\n"
        f"receipt_id = {receipt_id}\n"
        f"subject_phase_id = {subject_phase_id}\n"
        "classification = SYNTHETIC_FIXTURE_ONLY_NOT_A_PILOT\n"
    ).encode("utf-8")
    return {
        "payload": payload,
        "payload_bytes": payload_bytes,
        "manifest": manifest,
        "manifest_bytes": manifest_bytes,
        "receipt_bytes": receipt_bytes,
        "subject_packet_bytes": subject_packet_bytes,
        "subject_packet_path": subject_packet_path,
        "subject_packet_sha256": subject_packet_sha256,
        "subject_artifact_root": subject_artifact_root,
        "artifact_bytes": artifact_bytes,
        "approved_admin_root": approved_admin_root,
        "repository_root": repository_root,
        "review_output_root": input_root,
        "registry_root": registry_root,
    }


def authority_kwargs(material: dict[str, Any]) -> dict[str, Any]:
    return {
        "approved_admin_root": material["approved_admin_root"],
        "repository_root": material["repository_root"],
        "expected_registry_root": material["registry_root"],
    }


def materialization_kwargs(material: dict[str, Any]) -> dict[str, Any]:
    return {
        **authority_kwargs(material),
        "subject_packet_path": material["subject_packet_path"],
        "subject_artifact_root": material["subject_artifact_root"],
        "human_review_payload_bytes": material["payload_bytes"],
        "subject_artifact_manifest_bytes": material["manifest_bytes"],
        "review_receipt_bytes": material["receipt_bytes"],
    }


@pytest.fixture
def synthetic_material(tmp_path: Path) -> dict[str, Any]:
    return make_synthetic_material(tmp_path)


@pytest.fixture
def synthetic_root(synthetic_material: dict[str, Any]) -> Path:
    return synthetic_material["registry_root"]


@pytest.fixture
def materialized_entry(synthetic_root: Path, synthetic_material: dict[str, Any]):
    result = materialize_synthetic(
        synthetic_root,
        **materialization_kwargs(synthetic_material),
        materialization_authorization_id="SYNTHETIC-MATERIALIZATION-AUTH-001",
        operation_id="synthetic-operation-001",
        materialized_at=FIXED_TIME,
    )
    return synthetic_root, synthetic_material, result
