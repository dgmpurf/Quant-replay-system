import csv
import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system.historical_replay_official_source_hierarchy_and_evidence_collection_worklist import (
    OUTPUT_FILES,
    RECOMMENDED_NEXT_TASK,
    REQUIRED_COLLECTION_FIELDS,
    SAFETY_FALSE_FIELDS,
    STATUS_CREATED,
    WORKFLOW_STAGE,
    run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist,
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
EXPECTED_SOURCE_CLASSES = {
    "exchange official listing and trading-status source",
    "exchange disclosure or issuer announcement source",
    "official quotation or trading-status publication source",
    "ETF issuer or fund company disclosure source",
    "index or provider membership source",
    "reviewed local manual evidence metadata source",
    "reviewer no-hit query log source",
}
EXPECTED_FAMILIES = {
    "listed_active_status",
    "delisted_not_delisted_status",
    "st_no_st_status",
    "etf_st_not_applicable_policy",
    "suspension_trading_status",
    "universe_membership",
    "source_lineage",
    "reviewer_no_hit_handoff",
    "survivorship_rationale",
}
EXPECTED_NEXT_TASK = (
    "Historical Replay Official Source Hierarchy and Evidence Collection Worklist "
    "Artifact Views / Status Report-Only v0.1"
)


def test_core_function_writes_all_required_artifacts_to_tmp_path(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.status == STATUS_CREATED
    assert result.workflow_stage == WORKFLOW_STAGE
    assert set(result.artifact_paths) == set(OUTPUT_FILES)
    for path in result.artifact_paths.values():
        assert path.exists()
        assert tmp_path / "out" in path.parents


def test_metadata_records_run_id_selected_context_status_and_report_path(tmp_path: Path) -> None:
    result = _run(tmp_path)
    metadata = _read_json(result.artifact_paths["metadata"])

    assert metadata["run_id"] == "unit_test_run"
    assert metadata["workflow_name"] == "historical_replay_official_source_hierarchy_and_evidence_collection_worklist"
    assert metadata["workflow_stage"] == WORKFLOW_STAGE
    assert metadata["runtime_status"] == STATUS_CREATED
    assert metadata["health_status"] == "WARN"
    assert metadata["historical_decision_date"] == "2024-04-02"
    assert metadata["universe_name"] == "etf_core"
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["local_only"] is True
    assert metadata["selected_sample_context_only"] is True
    assert metadata["report_path"].endswith(OUTPUT_FILES["report"])
    assert metadata["recommended_next_task"] == EXPECTED_NEXT_TASK
    assert RECOMMENDED_NEXT_TASK == EXPECTED_NEXT_TASK
    assert set(metadata["artifact_paths"]) == set(OUTPUT_FILES)


def test_metadata_counts_match_selected_sample_and_worklist_contract(tmp_path: Path) -> None:
    result = _run(tmp_path)
    metadata = _read_json(result.artifact_paths["metadata"])

    assert metadata["row_count"] == 9
    assert metadata["stock_row_count"] == 7
    assert metadata["etf_row_count"] == 2
    assert metadata["source_class_count"] == 7
    assert metadata["evidence_family_count"] == 9
    assert metadata["evidence_collection_worklist_row_count"] == 72
    assert metadata["no_hit_handoff_row_count"] == 9
    assert metadata["profile_conflict_count"] == 7
    assert metadata["survivorship_warning_count"] == 9
    assert metadata["blocked_count"] == 72
    assert metadata["manual_review_required_count"] == 72
    assert metadata["collection_required_count"] == 72


def test_selected_symbols_are_exact_strings_with_leading_zeros(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])
    seen = list(dict.fromkeys(row["symbol"] for row in rows))

    assert seen == list(EXPECTED_ROWS)
    assert rows[0]["symbol"] == "000001"
    assert rows[1]["symbol"] == "000001"
    assert isinstance(rows[0]["symbol"], str)


def test_worklist_rows_preserve_stock_and_etf_identity_fields(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])

    for row in rows:
        expected_type, expected_profile, expected_conflict = EXPECTED_ROWS[row["symbol"]]
        assert row["historical_decision_date"] == "2024-04-02"
        assert row["universe_name"] == "etf_core"
        assert row["legacy_universe_label"] == "etf_core"
        assert row["instrument_type"] == expected_type
        assert row["recommended_profile"] == expected_profile
        assert row["profile_conflict"] == expected_conflict
        assert set(REQUIRED_COLLECTION_FIELDS).issubset(row)


def test_source_hierarchy_matrix_contains_seven_source_classes(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["source_hierarchy_matrix"])

    assert len(rows) == 7
    assert {row["source_class"] for row in rows} == EXPECTED_SOURCE_CLASSES
    assert {row["manual_review_required"] for row in rows} == {"true"}
    assert {row["limitation_note_required"] for row in rows} == {"true"}


def test_evidence_family_requirement_matrix_contains_nine_families(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["evidence_family_requirement_matrix"])

    assert len(rows) == 9
    assert {row["evidence_family"] for row in rows} == EXPECTED_FAMILIES
    assert {row["default_status"] for row in rows} <= {
        "collection_required",
        "manual_review_required",
        "no_hit_query_required",
        "lineage_fields_missing",
    }


def test_evidence_collection_worklist_has_72_blocked_records(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])

    assert len(rows) == 72
    assert {row["status"] for row in rows} <= {
        "collection_required",
        "manual_review_required",
        "no_hit_query_required",
        "lineage_fields_missing",
        "blocked",
    }
    assert {row["blocked"] for row in rows} == {"true"}
    assert {row["closure_status"] for row in rows} == {"blocked"}


def test_stock_rows_require_st_no_st_status_and_profile_conflict_review(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])

    for symbol, (instrument_type, _, _) in EXPECTED_ROWS.items():
        families = {row["evidence_family"] for row in rows if row["symbol"] == symbol}
        if instrument_type == "STOCK":
            assert "st_no_st_status" in families
            assert "etf_st_not_applicable_policy" not in families
            stock_rows = [row for row in rows if row["symbol"] == symbol]
            assert {row["profile_conflict"] for row in stock_rows} == {"true"}
            assert any("blocker_profile_conflict_unreviewed" in row["blocker_reason"] for row in stock_rows)


def test_etf_rows_require_st_not_applicable_policy_and_no_profile_conflict(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])

    for symbol, (instrument_type, _, _) in EXPECTED_ROWS.items():
        families = {row["evidence_family"] for row in rows if row["symbol"] == symbol}
        if instrument_type == "ETF":
            assert "etf_st_not_applicable_policy" in families
            assert "st_no_st_status" not in families
            etf_rows = [row for row in rows if row["symbol"] == symbol]
            assert {row["profile_conflict"] for row in etf_rows} == {"false"}
            assert any("blocker_missing_etf_st_not_applicable_policy" in row["blocker_reason"] for row in etf_rows)


def test_required_source_lineage_fields_and_blockers_are_visible(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["source_lineage_requirement_matrix"])

    assert len(rows) == 72
    for row in rows:
        assert row["source_id_required"] == "true"
        assert row["source_name_required"] == "true"
        assert row["source_type_required"] == "true"
        assert row["permission_class_required"] == "true"
        assert row["raw_reference_required"] == "true"
        assert row["revision_id_required"] == "true"
        assert row["available_time_required"] == "true"
        assert row["available_time_timezone_required"] == "true"
        assert row["quality_status_required"] == "true"
        assert row["limitation_note_required"] == "true"
        assert "blocker_missing_source_id" in row["default_blocker_reason"]
        assert "blocker_missing_available_time" in row["default_blocker_reason"]


def test_no_hit_defaults_are_not_accepted_and_require_reviewer_handoff(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["no_hit_handoff_matrix"])

    assert len(rows) == 9
    for row in rows:
        assert row["no_hit_review_needed"] == "true"
        assert row["no_hit_acceptance_status"] == "not_accepted"
        assert row["no_hit_reviewer_required"] == "true"
        assert row["no_hit_query_window_start"] == "missing"
        assert row["no_hit_query_window_end"] == "missing"
        assert "not source reliability scoring" in row["non_approval_note"]


def test_survivorship_warning_is_true_for_all_symbols(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])

    assert {row["survivorship_warning_flag"] for row in rows} == {"true"}
    assert all("blocker_missing_survivorship_rationale" in row["blocker_reason"] for row in rows)


def test_all_safety_fields_remain_false_in_metadata_safety_and_rows(tmp_path: Path) -> None:
    result = _run(tmp_path)
    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    rows = _read_csv(result.artifact_paths["worklist"])

    for field in SAFETY_FALSE_FIELDS:
        assert metadata[field] is False
        assert safety[field] is False
        assert {row[field] for row in rows} == {"false"}


def test_collection_blocker_matrix_includes_required_blockers(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["blocker_matrix"])
    blockers = {row["blocker"] for row in rows}

    assert "blocker_missing_source_class" in blockers
    assert "blocker_missing_source_id" in blockers
    assert "blocker_missing_raw_reference" in blockers
    assert "blocker_missing_permission_class" in blockers
    assert "blocker_missing_revision_id" in blockers
    assert "blocker_missing_available_time" in blockers
    assert "blocker_missing_no_hit_query_window" in blockers
    assert "blocker_missing_survivorship_rationale" in blockers
    assert "blocker_missing_stock_st_source" in blockers
    assert "blocker_missing_etf_st_not_applicable_policy" in blockers


def test_report_text_includes_non_approval_boundaries(tmp_path: Path) -> None:
    result = _run(tmp_path)
    report = result.artifact_paths["report"].read_text(encoding="utf-8")

    assert "worklist row is not PIT approval" in report
    assert "not source reliability scoring" in report
    assert "source_hash_preview is not source hash validation" in report
    assert "local_file_hash_preview is not PIT evidence by itself" in report
    assert "Universe membership cannot be inferred from legacy etf_core label alone" in report
    assert EXPECTED_NEXT_TASK in report


@pytest.mark.parametrize("blocked", ["data/raw", "data/processed", "data/cache", "docs/project_sources"])
def test_output_root_rejects_protected_paths(tmp_path: Path, blocked: str) -> None:
    with pytest.raises(ValueError, match="protected output path"):
        run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist(
            root=tmp_path / "repo",
            output_dir=Path(blocked),
        )


def test_no_repo_outputs_or_docs_project_sources_are_created_when_using_tmp_path(tmp_path: Path) -> None:
    _run(tmp_path)

    assert not (tmp_path / "outputs").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_static_status_vocabulary_excludes_forbidden_positive_readiness_terms() -> None:
    unsafe_terms = {
        "PIT_ADMISSIBLE",
        "PIT_APPROVED",
        "READY_FOR_REPLAY",
        "ACTIVE_REPLAY_INPUT_READY",
        "BUY_REVIEW_READY",
        "TRADING_READY",
        "APPROVED_FOR_PAPER",
        "PERFORMANCE_VALIDATED",
    }

    assert not unsafe_terms.intersection(_module_status_constants())


def test_public_api_does_not_accept_source_paths_or_csv_paths() -> None:
    signature = inspect.signature(run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist)

    assert "source_path" not in signature.parameters
    assert "csv_path" not in signature.parameters
    assert "input_path" not in signature.parameters
    assert "target_csv" not in signature.parameters


def _run(tmp_path: Path):
    return run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist(
        root=tmp_path / "repo",
        output_dir=tmp_path / "out",
        run_id="unit_test_run",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _module_status_constants() -> set[str]:
    return {STATUS_CREATED, WORKFLOW_STAGE, RECOMMENDED_NEXT_TASK}
