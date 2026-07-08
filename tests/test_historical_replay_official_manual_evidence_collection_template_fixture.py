import csv
import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system.historical_replay_official_manual_evidence_collection_template_fixture import (
    OUTPUT_FILES,
    RECOMMENDED_NEXT_TASK,
    REQUIRED_EVIDENCE_TEMPLATE_FIELDS,
    SAFETY_FALSE_FIELDS,
    STATUS_CREATED,
    WORKFLOW_STAGE,
    run_historical_replay_official_manual_evidence_collection_template_fixture,
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
EXPECTED_NEXT_TASK = (
    "Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1"
)


def test_core_writes_all_required_template_artifacts_to_tmp_path(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.status == STATUS_CREATED
    assert result.workflow_stage == WORKFLOW_STAGE
    assert set(result.artifact_paths) == set(OUTPUT_FILES)
    for path in result.artifact_paths.values():
        assert path.exists()
        assert tmp_path / "out" in path.parents


def test_metadata_records_selected_context_counts_and_safety(tmp_path: Path) -> None:
    result = _run(tmp_path)
    metadata = _read_json(result.artifact_paths["metadata"])

    assert metadata["run_id"] == "unit_test_run"
    assert metadata["historical_decision_date"] == "2024-04-02"
    assert metadata["universe_name"] == "etf_core"
    assert metadata["runtime_status"] == STATUS_CREATED
    assert metadata["workflow_stage"] == WORKFLOW_STAGE
    assert metadata["health_status"] == "PASS"
    assert metadata["row_count"] == 9
    assert metadata["stock_row_count"] == 7
    assert metadata["etf_row_count"] == 2
    assert metadata["evidence_collection_template_row_count"] == 72
    assert metadata["source_lineage_template_row_count"] == 72
    assert metadata["no_hit_template_row_count"] == 9
    assert metadata["survivorship_template_row_count"] == 9
    assert metadata["reviewer_notes_template_row_count"] == 9
    assert metadata["profile_conflict_count"] == 7
    assert metadata["survivorship_warning_count"] == 9
    assert metadata["safety_true_count"] == 0
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["local_only"] is True
    assert metadata["selected_sample_context_only"] is True
    assert metadata["empty_or_synthetic_template_only"] is True
    assert metadata["filled_evidence_template_created"] is False
    assert metadata["official_evidence_collection_started"] is False
    assert metadata["recommended_next_task"] == EXPECTED_NEXT_TASK
    assert RECOMMENDED_NEXT_TASK == EXPECTED_NEXT_TASK
    for field in SAFETY_FALSE_FIELDS:
        assert metadata[field] is False


def test_selected_symbols_are_exact_strings_with_leading_zeros(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["evidence_collection_template"])

    assert list(dict.fromkeys(row["symbol"] for row in rows)) == list(EXPECTED_ROWS)
    assert rows[0]["symbol"] == "000001"
    assert isinstance(rows[0]["symbol"], str)


def test_template_rows_preserve_stock_and_etf_identity_and_required_fields(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["evidence_collection_template"])

    assert len(rows) == 72
    for row in rows:
        expected_type, expected_profile, expected_conflict = EXPECTED_ROWS[row["symbol"]]
        assert row["historical_decision_date"] == "2024-04-02"
        assert row["universe_name"] == "etf_core"
        assert row["legacy_universe_label"] == "etf_core"
        assert row["instrument_type"] == expected_type
        assert row["recommended_profile"] == expected_profile
        assert row["profile_conflict"] == expected_conflict
        assert set(REQUIRED_EVIDENCE_TEMPLATE_FIELDS).issubset(row)
        assert row["template_status"] in {
            "template_row_created_report_only",
            "evidence_collection_required",
            "manual_review_required",
            "no_hit_query_required",
            "source_lineage_required",
            "survivorship_rationale_required",
            "context_only_not_evidence",
            "blocked",
            "row_ready_for_manual_fill_not_pit_approved",
        }
        assert row["evidence_collection_status"] == "not_collected"


def test_stock_rows_use_stock_st_family_and_etf_rows_use_not_applicable_policy(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["evidence_collection_template"])

    for symbol, (instrument_type, _, _) in EXPECTED_ROWS.items():
        families = {row["evidence_family"] for row in rows if row["symbol"] == symbol}
        if instrument_type == "STOCK":
            assert "st_no_st_status" in families
            assert "etf_st_not_applicable_policy" not in families
        else:
            assert "etf_st_not_applicable_policy" in families
            assert "st_no_st_status" not in families


def test_source_lineage_template_has_72_placeholder_rows_and_no_full_hashes(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["source_lineage_template"])

    assert len(rows) == 72
    for row in rows:
        assert row["source_id"] == "missing"
        assert row["permission_class"] == "missing"
        assert row["source_hash_preview"] in {"missing", "not_collected"}
        assert row["source_hash_disclosure_policy"] == "preview_only_or_hidden_full_hash"
        assert row["local_file_hash_preview"] in {"missing", "not_collected"}
        assert row["local_file_hash_disclosure_policy"] == "preview_only_not_pit_evidence"
        assert row["revision_id"] == "missing"
        assert row["available_time"] == "missing"
        assert row["quality_status"] == "missing"
    _assert_no_full_hashes_or_source_content(rows)


def test_no_hit_survivorship_and_reviewer_templates_remain_unaccepted(tmp_path: Path) -> None:
    result = _run(tmp_path)
    no_hit_rows = _read_csv(result.artifact_paths["no_hit_query_handoff_template"])
    survivorship_rows = _read_csv(result.artifact_paths["survivorship_rationale_template"])
    reviewer_rows = _read_csv(result.artifact_paths["reviewer_notes_template"])

    assert len(no_hit_rows) == 9
    assert len(survivorship_rows) == 9
    assert len(reviewer_rows) == 9
    assert {row["no_hit_review_needed"] for row in no_hit_rows} == {"true"}
    assert {row["no_hit_acceptance_status"] for row in no_hit_rows} == {"not_accepted"}
    assert {row["survivorship_warning_flag"] for row in survivorship_rows} == {"true"}
    assert {row["survivorship_review_status"] for row in survivorship_rows} == {"not_reviewed"}
    assert {row["reviewer_private_identity_disclosed"] for row in reviewer_rows} == {"no"}
    assert {row["reviewer_attestation_status"] for row in reviewer_rows} == {"not_attested"}


def test_safety_flags_are_all_false_and_positive_context_is_bounded(tmp_path: Path) -> None:
    result = _run(tmp_path)
    safety = _read_json(result.artifact_paths["safety_flags"])

    for field in SAFETY_FALSE_FIELDS:
        assert safety[field] is False
    assert safety["report_only"] is True
    assert safety["diagnostic_only"] is True
    assert safety["local_only"] is True
    assert safety["empty_or_synthetic_template_only"] is True
    assert safety["filled_evidence_template_created"] is False
    assert safety["official_evidence_collection_started"] is False


def test_static_outputs_do_not_expose_source_bytes_private_paths_or_readiness_wording(tmp_path: Path) -> None:
    result = _run(tmp_path)
    combined_text = "\n".join(path.read_text(encoding="utf-8") for path in result.artifact_paths.values())

    for forbidden in [
        "C:\\",
        "G:\\",
        "raw source bytes",
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
            run_historical_replay_official_manual_evidence_collection_template_fixture(
                root=tmp_path / "reports",
                output_dir=protected,
                run_id="blocked",
            )


def test_public_api_does_not_accept_source_or_evidence_paths() -> None:
    signature = inspect.signature(run_historical_replay_official_manual_evidence_collection_template_fixture)

    for forbidden_arg in [
        "source_path",
        "official_url",
        "source_file_path",
        "source_pdf_path",
        "filled_evidence_path",
        "collect_official_evidence",
        "approve_pit",
        "active_replay_input",
    ]:
        assert forbidden_arg not in signature.parameters


def _run(tmp_path: Path):
    return run_historical_replay_official_manual_evidence_collection_template_fixture(
        root=tmp_path / "reports",
        output_dir=tmp_path / "out",
        run_id="unit_test_run",
    )


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _assert_no_full_hashes_or_source_content(rows: list[dict[str, str]]) -> None:
    for row in rows:
        for value in row.values():
            text = str(value)
            assert not (len(text) >= 64 and all(ch in "0123456789abcdefABCDEF" for ch in text[:64]))
            assert "source bytes" not in text.lower()
