import csv
import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system.historical_replay_mixed_stock_etf_universe_profile_policy import (
    BLOCKER_VOCABULARY,
    OUTPUT_FILES,
    RECOMMENDED_NEXT_TASK,
    REQUIRED_PROFILE_POLICY_FIELDS,
    SAFETY_FALSE_FIELDS,
    STATUS_CREATED,
    STATUS_VOCABULARY,
    WORKFLOW_STAGE,
    run_historical_replay_mixed_stock_etf_universe_profile_policy,
)


EXPECTED_ROWS = {
    "000001": ("STOCK", "stock_core", "true", "unresolved_profile_conflict"),
    "000002": ("STOCK", "stock_core", "true", "unresolved_profile_conflict"),
    "159915": ("ETF", "etf_core", "false", "profile_aligned_context_only_not_universe_proof"),
    "300750": ("STOCK", "stock_core", "true", "unresolved_profile_conflict"),
    "510300": ("ETF", "etf_core", "false", "profile_aligned_context_only_not_universe_proof"),
    "600000": ("STOCK", "stock_core", "true", "unresolved_profile_conflict"),
    "600519": ("STOCK", "stock_core", "true", "unresolved_profile_conflict"),
    "601318": ("STOCK", "stock_core", "true", "unresolved_profile_conflict"),
    "688981": ("STOCK", "stock_core", "true", "unresolved_profile_conflict"),
}
EXPECTED_NEXT_TASK = (
    "Historical Replay Mixed STOCK/ETF Universe Profile Policy Checkpoint Documentation Bundle Report-Only v0.1"
)
OLD_NEXT_TASK = (
    "Historical Replay Mixed STOCK/ETF Universe Profile Policy Generated Artifact Review Report-Only v0.1"
)


def test_core_writes_required_mixed_profile_policy_artifacts_to_tmp_path(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.status == STATUS_CREATED
    assert result.workflow_stage == WORKFLOW_STAGE
    assert result.health_status == "PASS"
    assert set(result.artifact_paths) == set(OUTPUT_FILES)
    for path in result.artifact_paths.values():
        assert path.exists()
        assert tmp_path / "out" in path.parents


def test_metadata_records_exact_counts_and_non_approval_safety(tmp_path: Path) -> None:
    result = _run(tmp_path)
    metadata = _read_json(result.artifact_paths["metadata"])

    assert metadata["run_id"] == "unit_mixed_profile"
    assert metadata["historical_decision_date"] == "2024-04-02"
    assert metadata["universe_name"] == "etf_core"
    assert metadata["runtime_status"] == STATUS_CREATED
    assert metadata["workflow_stage"] == WORKFLOW_STAGE
    assert metadata["health_status"] == "PASS"
    assert metadata["row_count"] == 9
    assert metadata["stock_row_count"] == 7
    assert metadata["etf_row_count"] == 2
    assert metadata["profile_conflict_count"] == 7
    assert metadata["profile_aligned_context_count"] == 2
    assert metadata["unresolved_profile_conflict_count"] == 7
    assert metadata["profile_policy_accepted_count"] == 0
    assert metadata["universe_membership_approved_count"] == 0
    assert metadata["official_status_evidence_accepted_count"] == 0
    assert metadata["no_hit_row_count"] == 9
    assert metadata["not_accepted_count"] == 9
    assert metadata["accepted_context_count"] == 0
    assert metadata["row_with_blocker_count"] == 9
    assert metadata["survivorship_warning_count"] == 9
    assert metadata["safety_true_count"] == 0
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["local_only"] is True
    assert metadata["synthetic_only"] is True
    assert metadata["selected_sample_context_only"] is True
    assert metadata["mixed_stock_etf_profile_policy_fixture_only"] is True
    assert metadata["recommended_next_task"] == EXPECTED_NEXT_TASK
    assert RECOMMENDED_NEXT_TASK == EXPECTED_NEXT_TASK
    assert metadata["recommended_next_task"] != OLD_NEXT_TASK
    for field in SAFETY_FALSE_FIELDS:
        assert metadata[field] is False


def test_selected_rows_preserve_symbols_profiles_and_blockers(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["policy_rows"])

    assert [row["selected_symbol"] for row in rows] == list(EXPECTED_ROWS)
    assert rows[0]["selected_symbol"] == "000001"
    assert len(rows) == 9
    for row in rows:
        expected_type, expected_profile, expected_conflict, expected_status = EXPECTED_ROWS[row["selected_symbol"]]
        blockers = set(row["blocker_reason"].split(";"))
        assert set(REQUIRED_PROFILE_POLICY_FIELDS).issubset(row)
        assert row["historical_decision_date"] == "2024-04-02"
        assert row["universe_name"] == "etf_core"
        assert row["legacy_universe_label"] == "etf_core"
        assert row["instrument_type"] == expected_type
        assert row["recommended_profile"] == expected_profile
        assert row["profile_conflict"] == expected_conflict
        assert row["profile_policy_status"] == expected_status
        assert row["universe_membership_evidence_required"] == "true"
        assert row["official_status_evidence_required"] == "true"
        assert row["profile_policy_reviewer_required"] == "true"
        assert row["profile_policy_reviewer_alias"] == "missing"
        assert row["profile_policy_reviewer_scope"] == "missing"
        assert row["profile_policy_downstream_use_policy"] == "context_only_not_evidence"
        assert row["profile_policy_no_hit_override_allowed"] == "false"
        assert row["profile_policy_pit_approval_allowed"] == "false"
        assert row["profile_policy_replay_readiness_allowed"] == "false"
        assert row["profile_policy_buy_review_allowed"] == "false"
        assert row["profile_policy_trading_allowed"] == "false"
        assert row["no_hit_context_can_resolve_profile_conflict"] == "false"
        assert row["legacy_universe_label_is_universe_proof"] == "false"
        assert row["recommended_profile_is_stock_profile_validation"] == "false"
        assert row["same_day_quote_is_official_status_proof"] == "false"
        assert row["forward_return_used_in_decision_context"] == "false"
        assert row["universe_membership_approved"] == "false"
        assert row["official_status_evidence_accepted"] == "false"
        assert row["profile_conflict_resolved"] == "false"
        assert row["stock_profile_validated"] == "false"
        assert row["pit_admissibility_approved"] == "false"
        assert row["active_replay_input"] == "false"
        assert row["replay_execution_allowed"] == "false"
        assert row["buy_review_allowed"] == "false"
        assert row["trading_allowed"] == "false"
        assert "blocker_missing_universe_membership_evidence" in blockers
        assert "blocker_missing_official_status_evidence" in blockers
        assert "blocker_missing_profile_policy_reviewer_scope" in blockers
        if row["instrument_type"] == "STOCK":
            assert row["st_policy_family_required"] == "stock_st_no_st_evidence_required"
            assert row["etf_not_applicable_policy_required"] == "false"
            assert "blocker_profile_conflict_hidden_or_removed" in blockers
            assert "blocker_missing_stock_st_no_st_evidence" in blockers
        else:
            assert row["st_policy_family_required"] == "false"
            assert row["etf_not_applicable_policy_required"] == "true"
            assert "blocker_missing_etf_st_not_applicable_policy" in blockers


def test_vocabularies_and_policy_matrix_are_bounded(tmp_path: Path) -> None:
    result = _run(tmp_path)
    statuses = _read_csv(result.artifact_paths["status_vocabulary"])
    blockers = _read_csv(result.artifact_paths["blocker_vocabulary"])
    policies = _read_csv(result.artifact_paths["policy_matrix"])

    assert {row["status"] for row in statuses} == set(STATUS_VOCABULARY)
    accepted_row = next(row for row in statuses if row["status"] == "accepted_for_policy_context_only_not_pit_approved")
    assert accepted_row["allowed_for_current_fixture_rows"] == "false"
    assert {row["blocker"] for row in blockers} == set(BLOCKER_VOCABULARY)
    policy_text = json.dumps(policies)
    assert "legacy_universe_label is context only" in policy_text
    assert "recommended_profile is a policy hint only" in policy_text
    assert "no-hit context cannot resolve profile conflict" in policy_text
    assert "same-day quote is not official status proof" in policy_text


def test_safety_flags_false_and_public_outputs_have_no_private_or_readiness_content(tmp_path: Path) -> None:
    result = _run(tmp_path)
    safety = _read_json(result.artifact_paths["safety_flags"])
    combined_text = "\n".join(path.read_text(encoding="utf-8") for path in result.artifact_paths.values())

    for field in SAFETY_FALSE_FIELDS:
        assert safety[field] is False
    assert safety["report_only"] is True
    assert safety["diagnostic_only"] is True
    assert safety["local_only"] is True
    assert safety["synthetic_only"] is True
    for forbidden in [
        "C:\\",
        "G:\\",
        "private legal identity",
        "PIT_ADMISSIBLE",
        "PIT_APPROVED",
        "READY_FOR_REPLAY",
        "ACTIVE_REPLAY_INPUT_READY",
        "BUY_REVIEW_READY",
        "TRADING_READY",
        "APPROVED_FOR_PAPER",
        "PERFORMANCE_VALIDATED",
    ]:
        assert forbidden not in combined_text


def test_rejects_protected_output_roots(tmp_path: Path) -> None:
    for protected in [
        tmp_path / "data" / "raw",
        tmp_path / "data" / "processed",
        tmp_path / "data" / "cache",
        tmp_path / "docs" / "project_sources",
    ]:
        with pytest.raises(ValueError):
            run_historical_replay_mixed_stock_etf_universe_profile_policy(
                root=tmp_path / "reports",
                output_dir=protected,
                run_id="blocked",
            )


def test_public_api_does_not_accept_evidence_or_approval_inputs() -> None:
    signature = inspect.signature(run_historical_replay_mixed_stock_etf_universe_profile_policy)

    for forbidden_arg in [
        "official_url",
        "source_file",
        "source_path",
        "filled_template_path",
        "collect_official_evidence",
        "accept_official_evidence",
        "approve_universe_membership",
        "resolve_profile_conflict",
        "validate_stock_profile",
        "approve_pit",
        "active_replay_input",
        "run_replay",
        "buy_review",
        "trade",
    ]:
        assert forbidden_arg not in signature.parameters


def _run(tmp_path: Path):
    return run_historical_replay_mixed_stock_etf_universe_profile_policy(
        root=tmp_path / "reports",
        output_dir=tmp_path / "out",
        run_id="unit_mixed_profile",
    )


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
