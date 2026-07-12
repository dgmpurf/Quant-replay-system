from __future__ import annotations

import pytest

from conftest import make_synthetic_material, materialization_kwargs
from quant_replay_system.accepted_lineage_registry.models import (
    HUMAN_REVIEW_REQUIRED_FIELDS,
    HumanReviewPayload,
    RegistryError,
    RegistryPolicy,
    RegistrySchema,
)
from quant_replay_system.accepted_lineage_registry.transaction import materialize_synthetic


def test_human_review_payload_requires_all_reviewer_fields(synthetic_material) -> None:
    payload = HumanReviewPayload.from_bytes(synthetic_material["payload_bytes"])
    assert set(HUMAN_REVIEW_REQUIRED_FIELDS).issubset(payload.data)
    assert payload.data["review_status"] == "ACCEPTED_WITH_LIMITATIONS"


@pytest.mark.parametrize("field", ["review_decision_id", "reviewed_at"])
def test_missing_reviewer_authority_field_stops(field: str, tmp_path) -> None:
    material = make_synthetic_material(tmp_path)
    material["payload"].pop(field)
    from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes

    with pytest.raises(RegistryError, match="missing required fields") as caught:
        HumanReviewPayload.from_bytes(canonical_json_bytes(material["payload"]))
    assert caught.value.classification == "REVIEW_PAYLOAD_REQUIRED_FIELD_MISSING_STOP"


def test_missing_materialization_authorization_stops(synthetic_root, synthetic_material) -> None:
    with pytest.raises(RegistryError) as caught:
        materialize_synthetic(
            synthetic_root,
            **materialization_kwargs(synthetic_material),
            materialization_authorization_id=None,
        )
    assert caught.value.classification == "MATERIALIZATION_EXACT_APPROVAL_MISSING_STOP"
    assert not synthetic_root.exists()


def test_reviewer_payload_rejects_runtime_authority_field(tmp_path) -> None:
    material = make_synthetic_material(tmp_path, payload_overrides={"materialized_at": "2026-01-01T00:00:00Z"})
    with pytest.raises(RegistryError) as caught:
        HumanReviewPayload.from_bytes(material["payload_bytes"])
    assert caught.value.classification == "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP"


def test_supersession_is_disabled(tmp_path) -> None:
    material = make_synthetic_material(tmp_path, payload_overrides={"supersedes_receipt_id": "SYNTHETIC-OLD"})
    with pytest.raises(RegistryError) as caught:
        HumanReviewPayload.from_bytes(material["payload_bytes"])
    assert caught.value.classification == "SUPERSESSION_NOT_SUPPORTED_V0_1_STOP"


def test_invalid_review_status_is_constrained(tmp_path) -> None:
    material = make_synthetic_material(tmp_path, payload_overrides={"review_status": "TRADING_READY"})
    with pytest.raises(RegistryError) as caught:
        HumanReviewPayload.from_bytes(material["payload_bytes"])
    assert caught.value.classification == "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP"


def test_default_policy_and_schema_are_synthetic_five_file_only() -> None:
    policy = RegistryPolicy().to_dict()
    schema = RegistrySchema().to_dict()
    assert policy["registry_mode"] == "SYNTHETIC_FIXTURE_ONLY_NOT_A_PILOT"
    assert policy["live_registry_allowed"] is False
    assert policy["supersession_enabled"] is False
    assert schema["entry_file_count"] == 5
    assert schema["entry_files"] == [
        "human_review_payload.json",
        "subject_artifact_manifest.json",
        "review_receipt.md",
        "entry_manifest.json",
        "entry_seal.json",
    ]


def test_non_synthetic_logical_identity_is_rejected(synthetic_root) -> None:
    material = make_synthetic_material(
        synthetic_root.parent,
        approved_admin_root=synthetic_root.parents[1],
        repository_root=synthetic_root.parents[2] / "repository",
        registry_root=synthetic_root,
        subject_phase_id="REAL-SUBJECT-001",
    )
    with pytest.raises(RegistryError) as caught:
        materialize_synthetic(
            synthetic_root,
            **materialization_kwargs(material),
            materialization_authorization_id="SYNTHETIC-AUTH-001",
        )
    assert caught.value.classification == "LIVE_REGISTRY_MODE_NOT_AUTHORIZED_STOP"
    assert not any((synthetic_root / "entries").rglob("entry_manifest.json"))
