from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.company_exposure_schema_fixture import (
    ALLOWED_TRADE_USAGE,
    DIRECTION_FOR_FACTOR_INCREASE,
    DIRECTION_RULE_TYPES,
    EVIDENCE_SPECIFICITY,
    EXPOSURE_MEASURE_TYPES,
    EXPOSURE_STRENGTH_BUCKETS,
    EXPOSURE_TYPES,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    FORBIDDEN_TRADE_USAGE,
    INSTRUMENT_TYPES,
    MAPPING_METHODS,
    REQUIRED_COMPANY_EXPOSURE_FIELDS,
    build_company_exposure_schema_fixture,
)


EXPECTED_ARTIFACTS = {
    "company_exposure_schema_fixture_metadata.json",
    "company_exposure_schema_fields.csv",
    "company_exposure_fixture_rows.csv",
    "company_exposure_type_matrix.csv",
    "company_exposure_direction_matrix.csv",
    "company_exposure_pit_lineage_matrix.csv",
    "company_exposure_validation_summary.csv",
    "company_exposure_limitations.md",
    "recommended_next_task.md",
}


def _build(tmp_path: Path):
    return build_company_exposure_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "company_exposure_schema_fixture_v0_1"
    )


def _rows(result) -> pd.DataFrame:
    return pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).fillna("")


def _metadata(result) -> dict:
    return json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))


def test_company_exposure_schema_fixture_writes_expected_artifacts(tmp_path: Path) -> None:
    result = _build(tmp_path)

    assert result.status == "PASS"
    assert result.workflow_stage == "COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED"
    assert result.exposure_count == 10
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(
        tmp_path / "outputs" / "reports" / "manual_diagnostics" / "company_exposure_schema_fixture_v0_1"
    )
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_metadata_keeps_report_only_flags_and_forbidden_flags_false(tmp_path: Path) -> None:
    result = _build(tmp_path)
    metadata = _metadata(result)

    assert metadata["company_exposure_schema_fixture_created"] is True
    assert metadata["company_exposure_rows_created"] is True
    assert metadata["status"] == "PASS"
    assert metadata["workflow_stage"] == "COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED"
    assert metadata["exposure_count"] == 10
    assert metadata["validation_issue_count"] == 0
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert metadata[flag] is False


def test_schema_fields_and_rows_include_all_required_fields(tmp_path: Path) -> None:
    result = _build(tmp_path)
    fields = pd.read_csv(result.artifact_paths["schema_fields"], dtype=str)
    rows = _rows(result)

    assert set(REQUIRED_COMPANY_EXPOSURE_FIELDS).issubset(set(fields["field_name"]))
    assert set(REQUIRED_COMPANY_EXPOSURE_FIELDS).issubset(set(rows.columns))
    assert len(rows) == 10
    assert rows["company_exposure_id"].is_unique
    assert rows["company_exposure_version"].str.len().gt(0).all()
    assert rows["entity_id"].map(type).eq(str).all()
    assert rows["symbol"].map(type).eq(str).all()


def test_fixture_rows_use_valid_enums_and_non_actionable_trade_usage(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)

    assert set(rows["instrument_type"]) <= INSTRUMENT_TYPES
    assert set(rows["exposure_type"]) <= EXPOSURE_TYPES
    assert set(rows["exposure_measure_type"]) <= EXPOSURE_MEASURE_TYPES
    assert set(rows["exposure_strength_bucket"]) <= EXPOSURE_STRENGTH_BUCKETS
    assert set(rows["mapping_method"]) <= MAPPING_METHODS
    assert set(rows["evidence_specificity"]) <= EVIDENCE_SPECIFICITY
    assert set(rows["direction_rule_type"]) <= DIRECTION_RULE_TYPES
    assert set(rows["direction_for_factor_increase"]) <= DIRECTION_FOR_FACTOR_INCREASE
    assert set(rows["trade_usage"]) <= ALLOWED_TRADE_USAGE
    assert not set(rows["trade_usage"]) & FORBIDDEN_TRADE_USAGE


def test_iron_ore_rows_share_factor_reference_and_have_opposite_directions(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result).set_index("company_exposure_id")

    buyer = rows.loc["SYNTH_STEEL_IRON_ORE_COST_BUYER"]
    producer = rows.loc["SYNTH_IRON_ORE_RESOURCE_PRODUCER"]

    assert buyer["factor_id_refs"] == "L2_IRON_ORE_PRICE_CHANGE_SAMPLE"
    assert producer["factor_id_refs"] == "L2_IRON_ORE_PRICE_CHANGE_SAMPLE"
    assert buyer["direction_for_factor_increase"] == "NEGATIVE"
    assert producer["direction_for_factor_increase"] == "POSITIVE"
    assert "input-cost steelmakers" in buyer["direction_rule_detail"]
    assert "resource producer" in producer["direction_rule_detail"]


def test_conditional_proxy_and_special_rows_preserve_safety_boundaries(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result).set_index("company_exposure_id")

    conditional = rows[
        rows["direction_for_factor_increase"].isin(["CONDITIONAL", "MIXED"])
        | rows["direction_rule_type"].isin(["CONDITIONAL", "MIXED_BY_EXPOSURE", "MIXED_BY_REGIME"])
    ]
    assert conditional["direction_rule_detail"].str.len().gt(0).all()

    risk = rows.loc["SYNTH_ST_STATUS_RISK_VETO_EXPOSURE"]
    assert risk["direction_for_factor_increase"] == "RISK_VETO_ONLY"
    assert risk["direction_rule_type"] == "RISK_VETO_ONLY"
    assert risk["trade_usage"] in {"risk_filter", "no_trade"}
    assert "cannot create positive alpha" in risk["direction_rule_detail"]

    blocked = rows.loc["SYNTH_BLOCKED_PRIVATE_SUPPLIER_RELATIONSHIP"]
    assert blocked["mapping_method"] == "BLOCKED_UNVERIFIED"
    assert blocked["evidence_specificity"] == "BLOCKED"
    assert blocked["quality_status"] == "BLOCKED"
    assert blocked["manual_review_status"] == "BLOCKED"
    assert blocked["pit_valid"] == "False"
    assert blocked["decision_time_eligible"] == "False"
    assert blocked["trade_usage"] == "no_trade"

    etf = rows.loc["SYNTH_ETF_INDEX_HOLDING_EXPOSURE"]
    assert etf["instrument_type"] == "ETF"
    assert etf["exposure_type"] in {"ETF_HOLDING", "INDEX_MEMBERSHIP"}
    assert "does not claim real or current holdings ingestion" in etf["direction_rule_detail"]

    proxy_rows = rows[rows["is_proxy"] == "True"]
    assert not proxy_rows.empty
    assert proxy_rows["proxy_reason"].str.len().gt(0).all()


def test_pit_versioning_and_lineage_fields_are_present_and_ordered(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)

    assert rows["source_id"].str.len().gt(0).all()
    evidence_backed = rows[rows["evidence_specificity"] != "BLOCKED"]
    assert evidence_backed["document_version_id"].str.len().gt(0).all()
    assert evidence_backed.apply(
        lambda row: bool(row["source_hash"]) or bool(row["content_hash"]),
        axis=1,
    ).all()
    assert rows["revision_id"].str.len().gt(0).all()
    assert rows["mapping_version"].str.len().gt(0).all()
    assert rows["available_time"].str.len().gt(0).all()
    assert rows["quality_status"].str.len().gt(0).all()
    assert rows["manual_review_status"].str.len().gt(0).all()
    assert rows.apply(lambda row: pd.Timestamp(row["available_time"]) <= pd.Timestamp(row["as_of_date"]), axis=1).all()
    assert rows[rows["effective_to"].str.len().gt(0)].apply(
        lambda row: pd.Timestamp(row["effective_from"]) <= pd.Timestamp(row["effective_to"]),
        axis=1,
    ).all()
    assert rows.apply(lambda row: pd.Timestamp(row["available_time"]) <= pd.Timestamp(row["stale_after"]), axis=1).all()


def test_mapping_confidence_is_bounded_and_not_return_probability(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)

    confidence = rows["mapping_confidence"].astype(float)
    assert confidence.between(0, 1).all()
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths["artifact_dir"].iterdir()
        if path.suffix in {".json", ".csv", ".md"}
    ).lower()
    assert "not return probability" in text
    assert "not a model weight" in text
    assert "active_portfolio_weight" not in set(rows["trade_usage"])


def test_rows_remain_report_only_and_never_live_alpha_or_trading(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)

    true_flags = ["report_only", "diagnostic_only"]
    false_flags = [
        "is_live_signal",
        "is_alpha_claim",
        "model_training_allowed",
        "active_weight_allowed",
        "active_threshold_allowed",
        "stock_profile_validation_allowed",
        "real_buy_review_allowed",
        "trading_allowed",
    ]
    for flag in true_flags:
        assert (rows[flag] == "True").all()
    for flag in false_flags:
        assert (rows[flag] == "False").all()


def test_validation_summary_passes_and_project_source_boundary_holds(tmp_path: Path) -> None:
    result = _build(tmp_path)
    validation = pd.read_csv(result.artifact_paths["validation_summary"], dtype=str)
    next_task = result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8")

    assert (validation["passed"] == "True").all()
    assert "Company Exposure Schema Fixture Views Report-Only v0.1" in next_task
    assert "research-status" not in next_task.lower()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_cli_command_runs_successfully_and_no_views_commands_are_added(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "company_exposure_schema_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "company-exposure-schema-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "company_exposure_schema_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert "workflow_stage: COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED" in completed.stdout
    assert "exposure_count: 10" in completed.stdout
    assert "report_only: True" in completed.stdout
    assert "diagnostic_only: True" in completed.stdout
    assert "No production company exposure mapping" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "company_exposure_fixture_rows.csv").exists()

    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "company-exposure-schema-fixture" in help_output
    assert "company-exposure-schema-fixture-index" not in help_output
    assert "company-exposure-schema-fixture-health" not in help_output
    assert "company-exposure-schema-fixture-status" not in help_output
