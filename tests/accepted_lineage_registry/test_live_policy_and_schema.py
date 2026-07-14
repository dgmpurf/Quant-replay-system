from __future__ import annotations

import pytest

from quant_replay_system.accepted_lineage_registry import (
    GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
    GovernedLiveRegistryPolicy,
    LiveAuthorizationState,
    LiveRegistryHealthResult,
    ValidatedReviewedSubject,
    validate_exact_reviewed_subject,
)
from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes, sha256_bytes
from quant_replay_system.accepted_lineage_registry.models import RegistryError


def _review_contract_kwargs(material: dict[str, object]) -> dict[str, object]:
    return {
        "human_review_payload_bytes": material["payload_bytes"],
        "subject_artifact_manifest_bytes": material["manifest_bytes"],
        "review_receipt_bytes": material["receipt_bytes"],
        "expected_review_decision_id": material["payload"]["review_decision_id"],
        "expected_payload_sha256": sha256_bytes(material["payload_bytes"]),
        "expected_subject_manifest_sha256": sha256_bytes(material["manifest_bytes"]),
        "expected_review_receipt_sha256": sha256_bytes(material["receipt_bytes"]),
    }


def test_live_policy_is_explicit_and_has_no_downstream_authority() -> None:
    policy = GovernedLiveRegistryPolicy().to_dict()
    assert policy["registry_mode"] == GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE
    assert policy["candidate_registry"] is False
    assert policy["live_registry"] is True
    assert policy["live_registry_allowed"] is True
    assert policy["next_task_authorized_by_registry"] is False
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


def test_live_authorization_state_vocabulary_is_closed() -> None:
    assert {state.value for state in LiveAuthorizationState} == {
        "ISSUED_NOT_ACTIVATED",
        "ACTIVATED_NOT_CONSUMED",
        "CONSUMED_PENDING_HUMAN_LIVE_ENTRY_REVIEW",
        "CONSUMED_ACCEPTED_LIVE_ENTRY",
        "CONSUMED_REVIEW_REQUIRED",
    }


def test_mode_neutral_review_contract_validates_exact_reviewer_bytes(synthetic_material) -> None:
    payload = dict(synthetic_material["payload"])
    authority = dict(payload["authority_effects"])
    authority["materialization_authority"] = "NONE"
    payload["authority_effects"] = authority
    payload_bytes = canonical_json_bytes(payload)
    receipt_bytes = (
        "# Exact Review Receipt\n\n"
        f"receipt_id = {payload['receipt_id']}\n"
        f"subject_phase_id = {payload['subject_phase_id']}\n"
        f"review_decision_id = {payload['review_decision_id']}\n"
        "materialization_authorization_id = null\n"
    ).encode("utf-8")
    kwargs = _review_contract_kwargs(synthetic_material)
    kwargs["human_review_payload_bytes"] = payload_bytes
    kwargs["expected_payload_sha256"] = sha256_bytes(payload_bytes)
    kwargs["review_receipt_bytes"] = receipt_bytes
    kwargs["expected_review_receipt_sha256"] = sha256_bytes(receipt_bytes)
    result = validate_exact_reviewed_subject(**kwargs)
    assert isinstance(result, ValidatedReviewedSubject)
    assert result.payload.data["review_decision_id"] == synthetic_material["payload"]["review_decision_id"]
    assert result.manifest.exact_sha256 == sha256_bytes(synthetic_material["manifest_bytes"])
    assert result.receipt.exact_sha256 == sha256_bytes(receipt_bytes)


def test_mode_neutral_review_contract_rejects_runtime_live_fields(synthetic_material) -> None:
    payload = dict(synthetic_material["payload"])
    payload["registry_instance_id"] = "RUNTIME-ONLY"
    payload_bytes = canonical_json_bytes(payload)
    kwargs = _review_contract_kwargs(synthetic_material)
    kwargs["human_review_payload_bytes"] = payload_bytes
    kwargs["expected_payload_sha256"] = sha256_bytes(payload_bytes)
    with pytest.raises(RegistryError) as caught:
        validate_exact_reviewed_subject(**kwargs)
    assert caught.value.classification == "REVIEW_CONTRACT_RUNTIME_FIELD_PRESENT_STOP"


def test_live_health_result_preserves_report_only_authority_boundary() -> None:
    health = LiveRegistryHealthResult(
        registry_mode=GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
        registry_schema_version="accepted-lineage-registry-v0.1",
        registry_policy_version="accepted-lineage-registry-policy-v0.1",
        root_safety="PASS",
        lock_status="UNLOCKED",
        authoritative_entry_count=0,
        entry_verification_status="NOT_APPLICABLE_EMPTY_ROOT",
        derived_index_status="PASS",
        stale_index_status=False,
        orphan_temporary_directories=0,
        path_safety_warnings=(),
        platform_limitations=(),
        privacy_warnings=(),
        registry_instance_id="SYNTHETIC-LIVE-INSTANCE",
        root_mode_binding="PASS",
        windows_backend_status="IMPLEMENTED_FAIL_CLOSED_PENDING_SEPARATE_L2_HUMAN_ACCEPTANCE",
        windows_capability_fields={"directory_handle_flush": True},
        residual_risk_fields={},
    ).to_dict()
    assert health["candidate_registry"] is False
    assert health["live_registry"] is True
    assert health["next_task_authorized_by_registry"] is False
    assert health["buy_review_authority"] == "none"
    assert health["trading_authority"] == "none"
