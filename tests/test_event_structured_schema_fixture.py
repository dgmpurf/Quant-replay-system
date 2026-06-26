from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.event_structured_schema_fixture import (
    ALLOWED_TRADE_USAGE,
    DIRECTION_FOR_AFFECTED_ENTITY,
    DIRECTION_RULE_TYPES,
    EVENT_SCOPES,
    EVENT_STATUSES,
    EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED,
    EVENT_TYPES,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    FORBIDDEN_TRADE_USAGE,
    MANUAL_REVIEW_STATUSES,
    QUALITY_STATUSES,
    REQUIRED_EVENT_STRUCTURED_FIELDS,
    SOURCE_TIERS,
    build_event_structured_schema_fixture,
)


EXPECTED_ARTIFACTS = {
    "event_structured_schema_fixture_metadata.json",
    "event_structured_schema_fields.csv",
    "event_structured_fixture_rows.csv",
    "event_structured_type_matrix.csv",
    "event_structured_direction_matrix.csv",
    "event_structured_pit_lineage_matrix.csv",
    "event_structured_source_quality_matrix.csv",
    "event_structured_validation_summary.csv",
    "event_structured_limitations.md",
    "recommended_next_task.md",
}


def _build(tmp_path: Path):
    return build_event_structured_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "event_structured_schema_fixture_v0_1"
    )


def _rows(result) -> pd.DataFrame:
    return pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).fillna("")


def _metadata(result) -> dict:
    return json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))


def test_event_structured_schema_fixture_writes_expected_artifacts(tmp_path: Path) -> None:
    result = _build(tmp_path)

    assert result.status == "PASS"
    assert result.workflow_stage == EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED
    assert result.status != EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED
    assert result.event_count == 10
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(
        tmp_path / "outputs" / "reports" / "manual_diagnostics" / "event_structured_schema_fixture_v0_1"
    )
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_metadata_keeps_report_only_flags_and_forbidden_flags_false(tmp_path: Path) -> None:
    result = _build(tmp_path)
    metadata = _metadata(result)

    assert metadata["event_structured_schema_fixture_created"] is True
    assert metadata["event_structured_rows_created"] is True
    assert metadata["status"] == "PASS"
    assert metadata["workflow_stage"] == EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED
    assert metadata["event_count"] == 10
    assert metadata["validation_issue_count"] == 0
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert metadata[flag] is False


def test_schema_fields_and_rows_include_all_required_fields(tmp_path: Path) -> None:
    result = _build(tmp_path)
    fields = pd.read_csv(result.artifact_paths["schema_fields"], dtype=str)
    rows = _rows(result)

    assert set(REQUIRED_EVENT_STRUCTURED_FIELDS).issubset(set(fields["field_name"]))
    assert set(REQUIRED_EVENT_STRUCTURED_FIELDS).issubset(set(rows.columns))
    assert len(rows) == 10
    assert rows["event_structured_id"].is_unique
    assert rows["event_version"].str.len().gt(0).all()
    assert rows["event_key"].str.len().gt(0).all()


def test_fixture_rows_use_valid_enums_and_non_actionable_trade_usage(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)

    assert set(rows["event_type"]) <= EVENT_TYPES
    assert set(rows["event_scope"]) <= EVENT_SCOPES
    assert set(rows["source_tier"]) <= SOURCE_TIERS
    assert set(rows["direction_rule_type"]) <= DIRECTION_RULE_TYPES
    assert set(rows["direction_for_affected_entity"]) <= DIRECTION_FOR_AFFECTED_ENTITY
    assert set(rows["event_status"]) <= EVENT_STATUSES
    assert set(rows["quality_status"]) <= QUALITY_STATUSES
    assert set(rows["manual_review_status"]) <= MANUAL_REVIEW_STATUSES
    assert set(rows["trade_usage"]) <= ALLOWED_TRADE_USAGE
    assert not set(rows["trade_usage"]) & FORBIDDEN_TRADE_USAGE


def test_timing_pit_and_lineage_fields_are_present_and_ordered(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)

    for column in [
        "event_time",
        "publish_time",
        "available_time",
        "as_of_date",
        "source_id",
        "document_id",
        "document_version_id",
        "revision_id",
        "parser_version",
        "extractor_version",
    ]:
        assert rows[column].str.len().gt(0).all()

    assert rows.apply(lambda row: pd.Timestamp(row["available_time"]) <= pd.Timestamp(row["as_of_date"]), axis=1).all()
    assert rows.apply(lambda row: pd.Timestamp(row["available_time"]) <= pd.Timestamp(row["stale_after"]), axis=1).all()
    assert rows.apply(
        lambda row: bool(row["source_hash"]) or bool(row["content_hash"]),
        axis=1,
    ).all()
    separated = rows[(rows["event_time"] != rows["publish_time"]) & (rows["publish_time"] != rows["available_time"])]
    assert len(separated) >= 6


def test_direction_cases_preserve_context_without_factor_observations(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result).set_index("event_structured_id")

    iron = rows.loc["SYNTH_IRON_ORE_PRICE_SHOCK_PUBLIC"]
    assert iron["event_type"] == "COMMODITY_PRICE_SHOCK"
    assert iron["direction_rule_type"] == "MIXED_BY_EXPOSURE"
    assert iron["direction_for_affected_entity"] == "MIXED"
    assert "steel buyer" in iron["direction_rule_detail"]
    assert "resource producer" in iron["direction_rule_detail"]
    assert iron["factor_id_refs"] != ""
    assert iron["company_exposure_id_refs"] != ""
    assert iron["model_training_allowed"] == "False"

    policy = rows.loc["SYNTH_OFFICIAL_STEEL_CAPACITY_RESTRICTION"]
    assert policy["direction_rule_type"] == "CONDITIONAL"
    assert policy["company_exposure_id_refs"] != ""
    assert policy["trade_usage"] in {"event_mapping", "exposure_context", "research_context"}

    conditional = rows[
        rows["direction_rule_type"].isin(["CONDITIONAL", "MIXED_BY_EXPOSURE", "MIXED_BY_REGIME"])
        | rows["direction_for_affected_entity"].isin(["CONDITIONAL", "MIXED"])
    ]
    assert conditional["direction_rule_detail"].str.len().gt(0).all()


def test_special_rows_keep_risk_blocked_and_etf_boundaries(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result).set_index("event_structured_id")

    risk = rows.loc["SYNTH_ST_DELIST_RISK_VETO_EVENT"]
    assert risk["direction_rule_type"] == "RISK_VETO_ONLY"
    assert risk["direction_for_affected_entity"] == "RISK_VETO_ONLY"
    assert risk["trade_usage"] in {"risk_filter", "no_trade"}
    assert risk["is_alpha_claim"] == "False"
    assert "no positive alpha" in risk["direction_rule_detail"]

    blocked = rows.loc["SYNTH_BLOCKED_UNVERIFIED_RUMOR_EVENT"]
    assert blocked["event_type"] == "RUMOR_UNVERIFIED"
    assert blocked["event_status"] == "BLOCKED"
    assert blocked["quality_status"] == "BLOCKED"
    assert blocked["manual_review_status"] == "BLOCKED"
    assert blocked["trade_usage"] == "no_trade"
    assert blocked["pit_valid"] == "False"
    assert blocked["decision_time_eligible"] == "False"

    etf = rows.loc["SYNTH_INDEX_REBALANCE_CONTEXT"]
    assert etf["event_scope"] == "ETF_INDEX"
    assert "does not claim real or current holdings ingestion" in etf["validation_notes"]
    assert etf["trade_usage"] in {"research_context", "event_mapping", "observe_only"}


def test_confidence_fields_are_bounded_and_not_return_probabilities(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths["artifact_dir"].iterdir()
        if path.suffix in {".json", ".csv", ".md"}
    ).lower()

    assert rows["extraction_confidence"].astype(float).between(0, 1).all()
    assert rows["event_confidence"].astype(float).between(0, 1).all()
    assert "not return probability" in text
    assert "not a model weight" in text
    assert "active_portfolio_weight" not in set(rows["trade_usage"])


def test_rows_remain_report_only_and_never_live_alpha_model_or_trading(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)

    for flag in ["report_only", "diagnostic_only"]:
        assert (rows[flag] == "True").all()
    for flag in [
        "is_live_signal",
        "is_alpha_claim",
        "signal_score_implemented",
        "model_training_allowed",
        "active_weight_allowed",
        "active_threshold_allowed",
        "stock_profile_validation_allowed",
        "real_buy_review_allowed",
        "trading_allowed",
    ]:
        assert (rows[flag] == "False").all()


def test_validation_summary_recommended_next_task_and_project_source_boundary(tmp_path: Path) -> None:
    result = _build(tmp_path)
    validation = pd.read_csv(result.artifact_paths["validation_summary"], dtype=str)
    next_task = result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8")
    limitations = result.artifact_paths["limitations"].read_text(encoding="utf-8")

    assert (validation["passed"] == "True").all()
    assert "Event Structured Schema Fixture Views Report-Only v0.1" in next_task
    assert "research-status" not in next_task.lower()
    assert "No production event ingestion is created" in limitations
    assert "No factor observations" in limitations
    assert "No replay evidence bundles" in limitations
    assert "No signal_score" in limitations
    assert "No model training" in limitations
    assert "No buy-review eligibility" in limitations
    assert "No trading" in limitations
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_cli_command_runs_successfully_and_only_core_command_is_added(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "event_structured_schema_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "event-structured-schema-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "event_structured_schema_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert f"workflow_stage: {EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED}" in completed.stdout
    assert "event_count: 10" in completed.stdout
    assert "validation_issue_count: 0" in completed.stdout
    assert "report_only: True" in completed.stdout
    assert "diagnostic_only: True" in completed.stdout
    assert "No production event ingestion" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "event_structured_fixture_rows.csv").exists()

    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "event-structured-schema-fixture" in help_output
    assert "event-structured-schema-fixture-index" not in help_output
    assert "event-structured-schema-fixture-health" not in help_output
    assert "event-structured-schema-fixture-status" not in help_output

