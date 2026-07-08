import csv
import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system.historical_replay_reviewer_no_hit_acceptance_fixture import (
    OUTPUT_FILES,
    RECOMMENDED_NEXT_TASK,
    REQUIRED_NO_HIT_FIELDS,
    SAFETY_FALSE_FIELDS,
    STATUS_CREATED,
    STATUS_VOCABULARY,
    WORKFLOW_STAGE,
    run_historical_replay_reviewer_no_hit_acceptance_fixture,
)


EXPECTED_ROWS = {
    "000001": ("STOCK", "stock_core", "true"),
    "000002": ("STOCK", "stock_core", "true"),
    "159915": ("ETF", "etf_core", "false"),
    "300750": ("STOCK", "stock_core", "true"),
    "510300": ("ETF", "etf_core", "false"),
    "600000": ("STOCK", "stock_core", "true"),
    "600519": ("STOCK", "stock_core", "true"),
    "601318": ("STOCK", "stock_core", "true"),
    "688981": ("STOCK", "stock_core", "true"),
}
EXPECTED_NEXT_TASK = "Historical Replay Reviewer No-Hit Acceptance Fixture Generated Artifact Review Report-Only v0.1"
EXPECTED_BLOCKERS = {
    "blocker_missing_no_hit_query_window",
    "blocker_missing_no_hit_timezone",
    "blocker_missing_no_hit_result_reference",
    "blocker_missing_reviewer_alias",
    "blocker_missing_reviewer_role",
    "blocker_missing_reviewer_scope",
}


def test_core_writes_required_no_hit_acceptance_artifacts_to_tmp_path(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.status == STATUS_CREATED
    assert result.workflow_stage == WORKFLOW_STAGE
    assert result.health_status == "PASS"
    assert set(result.artifact_paths) == set(OUTPUT_FILES)
    for path in result.artifact_paths.values():
        assert path.exists()
        assert tmp_path / "out" in path.parents


def test_metadata_records_selected_no_hit_counts_and_safety(tmp_path: Path) -> None:
    result = _run(tmp_path)
    metadata = _read_json(result.artifact_paths["metadata"])

    assert metadata["run_id"] == "unit_no_hit"
    assert metadata["historical_decision_date"] == "2024-04-02"
    assert metadata["universe_name"] == "etf_core"
    assert metadata["runtime_status"] == STATUS_CREATED
    assert metadata["workflow_stage"] == WORKFLOW_STAGE
    assert metadata["health_status"] == "PASS"
    assert metadata["row_count"] == 9
    assert metadata["stock_row_count"] == 7
    assert metadata["etf_row_count"] == 2
    assert metadata["no_hit_row_count"] == 9
    assert metadata["not_accepted_count"] == 9
    assert metadata["accepted_context_count"] == 0
    assert metadata["row_with_blocker_count"] == 9
    assert metadata["profile_conflict_count"] == 7
    assert metadata["survivorship_warning_count"] == 9
    assert metadata["safety_true_count"] == 0
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["local_only"] is True
    assert metadata["synthetic_only"] is True
    assert metadata["selected_sample_context_only"] is True
    assert metadata["no_hit_contract_fixture_only"] is True
    assert metadata["no_hit_context_accepted"] is False
    assert metadata["recommended_next_task"] == EXPECTED_NEXT_TASK
    assert RECOMMENDED_NEXT_TASK == EXPECTED_NEXT_TASK
    for field in SAFETY_FALSE_FIELDS:
        assert metadata[field] is False


def test_selected_no_hit_rows_are_exact_strings_and_not_accepted(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["reviewer_no_hit_acceptance_rows"])

    assert list(row["symbol"] for row in rows) == list(EXPECTED_ROWS)
    assert rows[0]["symbol"] == "000001"
    assert len(rows) == 9
    for row in rows:
        expected_type, expected_profile, expected_conflict = EXPECTED_ROWS[row["symbol"]]
        assert set(REQUIRED_NO_HIT_FIELDS).issubset(row)
        assert row["historical_decision_date"] == "2024-04-02"
        assert row["universe_name"] == "etf_core"
        assert row["legacy_universe_label"] == "etf_core"
        assert row["instrument_type"] == expected_type
        assert row["recommended_profile"] == expected_profile
        assert row["profile_conflict"] == expected_conflict
        assert row["no_hit_review_needed"] == "true"
        assert row["no_hit_source_family"] == "official_manual_evidence_collection_template"
        assert row["no_hit_evidence_family"] == "reviewer_no_hit_handoff"
        assert row["no_hit_query_window_start"] == "missing"
        assert row["no_hit_query_window_end"] == "missing"
        assert row["no_hit_query_window_timezone"] == "missing"
        assert row["no_hit_query_terms"] == "template_placeholder_only"
        assert row["no_hit_query_method"] == "template_placeholder_only"
        assert row["no_hit_result"] == "missing"
        assert row["no_hit_result_reference"] == "missing"
        assert row["no_hit_acceptance_status"] == "not_accepted"
        assert row["no_hit_reviewer_required"] == "true"
        assert row["reviewer_id_or_alias"] == "missing"
        assert row["reviewer_role"] == "missing"
        assert row["reviewer_scope"] == "missing"
        assert row["reviewer_private_identity_disclosed"] == "no"
        assert row["no_hit_downstream_use_policy"] == "context_only_not_evidence"
        assert row["no_hit_context_accepted"] == "false"
        assert row["no_hit_used_as_source_reliability_score"] == "false"
        assert row["no_hit_used_as_official_evidence"] == "false"
        assert row["no_hit_used_as_pit_approval"] == "false"
        assert EXPECTED_BLOCKERS.issubset(set(row["blocker_reason"].split(";")))


def test_status_and_blocker_vocabularies_are_bounded(tmp_path: Path) -> None:
    result = _run(tmp_path)
    statuses = _read_csv(result.artifact_paths["status_vocabulary"])
    blockers = _read_csv(result.artifact_paths["blocker_vocabulary"])

    assert {row["status"] for row in statuses} == set(STATUS_VOCABULARY)
    assert {row["allowed_for_current_fixture_rows"] for row in statuses if row["status"] == "not_accepted"} == {
        "true"
    }
    assert {
        "blocker_missing_no_hit_query_window",
        "blocker_missing_reviewer_scope",
        "blocker_no_hit_used_as_pit_approval",
        "blocker_forbidden_downstream_flag",
    }.issubset({row["blocker"] for row in blockers})


def test_required_fields_and_policy_matrix_explain_context_only_not_evidence(tmp_path: Path) -> None:
    result = _run(tmp_path)
    fields = _read_csv(result.artifact_paths["required_fields"])
    policies = _read_csv(result.artifact_paths["policy_matrix"])

    assert {"field_name", "required", "default_value", "blocker_if_missing", "notes"} == set(fields[0])
    assert "no_hit_context_accepted" in {row["field_name"] for row in fields}
    policy_text = json.dumps(policies)
    assert "context_only_not_evidence" in policy_text
    assert "reviewer no-hit context cannot close evidence gaps" in policy_text


def test_safety_flags_are_false_and_positive_context_is_bounded(tmp_path: Path) -> None:
    result = _run(tmp_path)
    safety = _read_json(result.artifact_paths["safety_flags"])

    for field in SAFETY_FALSE_FIELDS:
        assert safety[field] is False
    assert safety["report_only"] is True
    assert safety["diagnostic_only"] is True
    assert safety["local_only"] is True
    assert safety["synthetic_only"] is True
    assert safety["selected_sample_context_only"] is True
    assert safety["no_hit_contract_fixture_only"] is True
    assert safety["no_hit_context_accepted"] is False


def test_static_outputs_do_not_expose_private_paths_or_positive_readiness(tmp_path: Path) -> None:
    result = _run(tmp_path)
    combined_text = "\n".join(path.read_text(encoding="utf-8") for path in result.artifact_paths.values())

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
            run_historical_replay_reviewer_no_hit_acceptance_fixture(
                root=tmp_path / "reports",
                output_dir=protected,
                run_id="blocked",
            )


def test_public_api_does_not_accept_real_evidence_or_approval_paths() -> None:
    signature = inspect.signature(run_historical_replay_reviewer_no_hit_acceptance_fixture)

    for forbidden_arg in [
        "source_path",
        "source_file",
        "official_url",
        "target_csv",
        "filled_template_path",
        "collect_official_evidence",
        "accept_official_evidence",
        "approve_pit",
        "active_replay_input",
        "run_replay",
        "buy_review",
        "trade",
    ]:
        assert forbidden_arg not in signature.parameters


def _run(tmp_path: Path):
    return run_historical_replay_reviewer_no_hit_acceptance_fixture(
        root=tmp_path / "reports",
        output_dir=tmp_path / "out",
        run_id="unit_no_hit",
    )


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
