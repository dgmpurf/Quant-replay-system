from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.raw_document_store_schema_fixture import (
    REQUIRED_RAW_DOCUMENT_STORE_FIELDS,
    build_raw_document_store_schema_fixture,
)


FORBIDDEN_FALSE_METADATA_FLAGS = [
    "production_raw_document_store_created",
    "real_source_permission_created",
    "real_data_fetched",
    "raw_document_ingestion_created",
    "factor_observations_created",
    "event_ingestion_created",
    "company_exposure_created",
    "replay_evidence_bundle_created",
    "live_trading_enabled",
    "broker_api_called",
    "external_api_called",
    "llm_api_called",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "active_stock_profile_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
    "operational_global_approved_for_paper_granted",
]


EXPECTED_ARTIFACTS = {
    "raw_document_store_schema_fixture_metadata.json",
    "raw_document_store_schema_fields.csv",
    "raw_document_store_fixture_rows.csv",
    "raw_document_store_permission_matrix.csv",
    "raw_document_store_storage_policy_matrix.csv",
    "raw_document_store_pit_timing_matrix.csv",
    "raw_document_store_validation_summary.csv",
    "raw_document_store_limitations.md",
    "recommended_next_task.md",
}


def test_raw_document_store_schema_fixture_writes_expected_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"

    result = build_raw_document_store_schema_fixture(output_dir=output_dir)

    assert result.status == "PASS"
    assert result.workflow_stage == "RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED"
    assert result.document_count == 7
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(output_dir)
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_metadata_keeps_report_only_and_all_forbidden_side_effects_false(tmp_path: Path) -> None:
    result = build_raw_document_store_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["raw_document_store_schema_fixture_created"] is True
    assert metadata["status"] == "PASS"
    assert metadata["workflow_stage"] == "RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED"
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    for flag in FORBIDDEN_FALSE_METADATA_FLAGS:
        assert metadata[flag] is False


def test_schema_fields_and_fixture_rows_include_required_fields(tmp_path: Path) -> None:
    result = build_raw_document_store_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"
    )

    fields = pd.read_csv(result.artifact_paths["schema_fields"], dtype=str)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str)

    assert set(REQUIRED_RAW_DOCUMENT_STORE_FIELDS).issubset(set(fields["field_name"]))
    assert set(REQUIRED_RAW_DOCUMENT_STORE_FIELDS).issubset(set(rows.columns))
    assert set(rows["document_id"]) == {
        "LOCAL_CSV_REVIEWED_DATASET_SAMPLE",
        "PUBLIC_OFFICIAL_ANNOUNCEMENT_REFERENCE_SAMPLE",
        "PUBLIC_EXCHANGE_DISCLOSURE_REFERENCE_SAMPLE",
        "PUBLIC_POLICY_DOCUMENT_REFERENCE_SAMPLE",
        "PUBLIC_MACRO_RELEASE_DATASET_SAMPLE",
        "COPYRIGHTED_NEWS_REFERENCE_ONLY_SAMPLE",
        "BLOCKED_PRIVATE_RUMOR_SAMPLE",
    }
    assert rows["document_id"].map(type).eq(str).all()
    assert rows["document_version_id"].map(type).eq(str).all()
    assert rows["source_id"].map(type).eq(str).all()
    assert (rows["report_only"] == "True").all()
    assert (rows["diagnostic_only"] == "True").all()


def test_required_identity_timing_hash_revision_and_policy_fields_are_present(tmp_path: Path) -> None:
    result = build_raw_document_store_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"
    )
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).fillna("")

    assert rows["document_id"].str.len().gt(0).all()
    assert rows["document_version_id"].str.len().gt(0).all()
    assert rows["source_id"].str.len().gt(0).all()
    assert rows["available_time"].str.len().gt(0).all()
    assert rows.apply(lambda row: bool(row["source_hash"]) or bool(row["content_hash"]), axis=1).all()
    assert rows["revision_id"].str.len().gt(0).all()
    assert rows["permission_class"].str.len().gt(0).all()
    assert rows["storage_policy"].str.len().gt(0).all()
    assert rows["manual_review_status"].str.len().gt(0).all()
    assert rows["quality_status"].str.len().gt(0).all()
    assert set(rows["pit_valid"]) <= {"True", "False"}
    assert set(rows["decision_time_eligible"]) <= {"True", "False"}


def test_pit_timing_constraints_are_conservative(tmp_path: Path) -> None:
    result = build_raw_document_store_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"
    )
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).fillna("")

    populated_publication = rows[rows["published_at"].str.len().gt(0)].copy()
    assert (
        pd.to_datetime(populated_publication["published_at"]) <= pd.to_datetime(populated_publication["available_time"])
    ).all()

    periodic = rows[rows["period_end"].str.len().gt(0)].copy()
    assert (pd.to_datetime(periodic["period_end"]) <= pd.to_datetime(periodic["available_time"])).all()

    timing = pd.read_csv(result.artifact_paths["pit_timing_matrix"], dtype=str)
    assert (timing["available_time_present"] == "True").all()
    assert (timing["pit_check_passed"] == "True").all()


def test_fixture_row_policies_are_report_only_and_non_production(tmp_path: Path) -> None:
    result = build_raw_document_store_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"
    )
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).set_index("document_id")

    local_csv = rows.loc["LOCAL_CSV_REVIEWED_DATASET_SAMPLE"]
    assert local_csv["storage_policy"] == "LOCAL_REVIEWED_COPY_ALLOWED"
    assert local_csv["permission_class"] == "USER_PROVIDED_LOCAL"
    assert local_csv["report_only"] == "True"
    assert local_csv["diagnostic_only"] == "True"

    for document_id in [
        "PUBLIC_OFFICIAL_ANNOUNCEMENT_REFERENCE_SAMPLE",
        "PUBLIC_EXCHANGE_DISCLOSURE_REFERENCE_SAMPLE",
        "PUBLIC_POLICY_DOCUMENT_REFERENCE_SAMPLE",
        "PUBLIC_MACRO_RELEASE_DATASET_SAMPLE",
    ]:
        row = rows.loc[document_id]
        assert row["storage_policy"] in {"REFERENCE_ONLY", "HASH_ONLY", "STRUCTURED_EXTRACT_ONLY"}
        assert row["raw_content_stored"] == "False"

    copyrighted = rows.loc["COPYRIGHTED_NEWS_REFERENCE_ONLY_SAMPLE"]
    assert copyrighted["storage_policy"] in {"REFERENCE_ONLY", "STRUCTURED_EXTRACT_ONLY"}
    assert copyrighted["raw_content_stored"] == "False"
    assert copyrighted["copyright_storage_policy"] in {"REFERENCE_ONLY", "STRUCTURED_EXTRACT_ONLY"}

    blocked = rows.loc["BLOCKED_PRIVATE_RUMOR_SAMPLE"]
    assert blocked["permission_class"] == "PROHIBITED"
    assert blocked["storage_policy"] == "BLOCKED"
    assert blocked["pit_valid"] == "False"
    assert blocked["decision_time_eligible"] == "False"
    assert blocked["rumor_flag"] == "True"


def test_permission_storage_and_validation_matrices_capture_required_guards(tmp_path: Path) -> None:
    result = build_raw_document_store_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"
    )

    permission = pd.read_csv(result.artifact_paths["permission_matrix"], dtype=str).set_index("document_id")
    storage = pd.read_csv(result.artifact_paths["storage_policy_matrix"], dtype=str).set_index("document_id")
    validation = pd.read_csv(result.artifact_paths["validation_summary"], dtype=str)

    assert permission.loc["BLOCKED_PRIVATE_RUMOR_SAMPLE", "permission_decision"] == "BLOCK"
    assert permission.loc["LOCAL_CSV_REVIEWED_DATASET_SAMPLE", "fixture_grants_real_permission"] == "False"
    assert storage.loc["COPYRIGHTED_NEWS_REFERENCE_ONLY_SAMPLE", "full_raw_content_allowed"] == "False"
    assert storage.loc["BLOCKED_PRIVATE_RUMOR_SAMPLE", "content_storage_allowed"] == "False"
    assert (validation["passed"] == "True").all()


def test_fixture_contains_no_token_secret_or_disallowed_pii_values(tmp_path: Path) -> None:
    result = build_raw_document_store_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"
    )
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).fillna("")
    row_text = " ".join(rows.astype(str).agg(" ".join, axis=1)).lower()

    assert not re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\\s+[a-z0-9])", row_text)
    non_blocked = rows[rows["document_id"] != "BLOCKED_PRIVATE_RUMOR_SAMPLE"]
    assert (non_blocked["pii_flag"] == "False").all()


def test_recommended_next_task_and_no_views_commands_boundary(tmp_path: Path) -> None:
    result = build_raw_document_store_schema_fixture(
        output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"
    )
    next_task = result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8")

    assert "Raw Document Store Schema Fixture Views Report-Only v0.1" in next_task
    assert "research-status" not in next_task.lower()
    assert not (tmp_path / "docs" / "project_sources").exists()

    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "raw-document-store-schema-fixture" in help_output
    assert "raw-document-store-schema-fixture-index" in help_output
    assert "raw-document-store-schema-fixture-health" in help_output
    assert "raw-document-store-schema-fixture-status" in help_output
    assert "raw-document-store-schema-fixture-research-status" not in help_output


def test_cli_command_runs_successfully(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "raw_document_store_schema_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "raw-document-store-schema-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "raw_document_store_schema_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert "workflow_stage: RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED" in completed.stdout
    assert "document_count: 7" in completed.stdout
    assert "report_only: True" in completed.stdout
    assert "diagnostic_only: True" in completed.stdout
    assert "No data/raw, data/processed, data/cache" in completed.stdout
    assert "raw_document_store_fixture_rows.csv" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "raw_document_store_fixture_rows.csv").exists()
