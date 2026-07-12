from __future__ import annotations

from datetime import datetime, timezone

import pytest

from conftest import FIXED_TIME, make_synthetic_material, materialization_kwargs
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.transaction import materialize_synthetic


def _materialize(root, material, *, authorization="SYNTHETIC-AUTH-001", when=FIXED_TIME):
    return materialize_synthetic(
        root,
        **materialization_kwargs(material),
        materialization_authorization_id=authorization,
        operation_id="idempotency-test",
        materialized_at=when,
    )


def test_identical_immutable_identity_returns_idempotent_pass(synthetic_root, synthetic_material) -> None:
    first = _materialize(synthetic_root, synthetic_material)
    second = _materialize(synthetic_root, synthetic_material)
    assert first.classification == "NEW_ENTRY_MATERIALIZED_SUCCESSFULLY"
    assert second.classification == "IDEMPOTENT_PASS_EXISTING_IDENTICAL_ENTRY"
    assert second.entry_created is False
    assert second.idempotent_replay is True


def test_changed_runtime_timestamp_is_irrelevant_to_identity(synthetic_root, synthetic_material) -> None:
    _materialize(synthetic_root, synthetic_material, when=FIXED_TIME)
    replay = _materialize(
        synthetic_root,
        synthetic_material,
        when=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    assert replay.classification == "IDEMPOTENT_PASS_EXISTING_IDENTICAL_ENTRY"


def test_changed_runtime_authorization_is_irrelevant_to_identity(synthetic_root, synthetic_material) -> None:
    _materialize(synthetic_root, synthetic_material, authorization="SYNTHETIC-AUTH-001")
    replay = _materialize(synthetic_root, synthetic_material, authorization="SYNTHETIC-AUTH-002")
    assert replay.classification == "IDEMPOTENT_PASS_EXISTING_IDENTICAL_ENTRY"


def test_changed_human_payload_stops_on_same_receipt_identity(tmp_path, synthetic_root, synthetic_material) -> None:
    _materialize(synthetic_root, synthetic_material)
    changed = make_synthetic_material(
        synthetic_material["approved_admin_root"] / "changed_review_payload",
        approved_admin_root=synthetic_material["approved_admin_root"],
        repository_root=synthetic_material["repository_root"],
        registry_root=synthetic_root,
        payload_overrides={"review_limitations": ["Changed synthetic limitation"]},
    )
    with pytest.raises(RegistryError) as caught:
        _materialize(synthetic_root, changed)
    assert caught.value.classification == "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP"


def test_changed_subject_manifest_stops_before_materialization(tmp_path, synthetic_root, synthetic_material) -> None:
    _materialize(synthetic_root, synthetic_material)
    changed = make_synthetic_material(
        synthetic_material["approved_admin_root"] / "changed_subject_manifest",
        approved_admin_root=synthetic_material["approved_admin_root"],
        repository_root=synthetic_material["repository_root"],
        registry_root=synthetic_root,
        manifest_overrides={
            "artifact_count": 1,
            "artifacts": [{"relative_path": "changed.txt", "byte_length": 1, "sha256": "0" * 64}],
        },
    )
    with pytest.raises(RegistryError) as caught:
        materialize_synthetic(
            synthetic_root,
            approved_admin_root=synthetic_material["approved_admin_root"],
            repository_root=synthetic_material["repository_root"],
            expected_registry_root=synthetic_root,
            subject_packet_path=changed["subject_packet_path"],
            subject_artifact_root=changed["subject_artifact_root"],
            human_review_payload_bytes=synthetic_material["payload_bytes"],
            subject_artifact_manifest_bytes=changed["manifest_bytes"],
            review_receipt_bytes=synthetic_material["receipt_bytes"],
            materialization_authorization_id="SYNTHETIC-AUTH-002",
        )
    assert caught.value.classification == "SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP"


def test_same_receipt_conflicting_review_decision_stops(tmp_path, synthetic_root, synthetic_material) -> None:
    _materialize(synthetic_root, synthetic_material)
    changed = make_synthetic_material(
        synthetic_material["approved_admin_root"] / "changed_review_decision",
        approved_admin_root=synthetic_material["approved_admin_root"],
        repository_root=synthetic_material["repository_root"],
        registry_root=synthetic_root,
        payload_overrides={"review_decision_id": "SYNTHETIC-REVIEW-DECISION-002"},
    )
    with pytest.raises(RegistryError) as caught:
        _materialize(synthetic_root, changed)
    assert caught.value.classification == "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP"
