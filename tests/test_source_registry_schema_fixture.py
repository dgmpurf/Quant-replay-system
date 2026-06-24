from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.source_registry_schema_fixture import (
    REQUIRED_SOURCE_REGISTRY_FIELDS,
    build_source_registry_schema_fixture,
)


FORBIDDEN_FALSE_METADATA_FLAGS = [
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


def test_source_registry_schema_fixture_writes_expected_artifacts(tmp_path: Path) -> None:
    result = build_source_registry_schema_fixture(output_dir=tmp_path)

    assert result.status == "PASS"
    assert result.source_count == 5
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True

    artifact_dir = result.artifact_paths["artifact_dir"]
    assert artifact_dir.is_relative_to(tmp_path)
    expected_files = {
        "source_registry_schema_fixture_metadata.json",
        "source_registry_schema_fields.csv",
        "source_registry_fixture_rows.csv",
        "source_registry_permission_matrix.csv",
        "source_registry_replay_suitability_matrix.csv",
        "source_registry_validation_summary.csv",
        "source_registry_limitations.md",
        "recommended_next_task.md",
    }
    assert {path.name for path in artifact_dir.iterdir()} == expected_files
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_metadata_keeps_report_only_and_forbidden_side_effects_false(tmp_path: Path) -> None:
    result = build_source_registry_schema_fixture(output_dir=tmp_path)

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["source_registry_schema_fixture_created"] is True
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    for flag in FORBIDDEN_FALSE_METADATA_FLAGS:
        assert metadata[flag] is False


def test_schema_fields_and_fixture_rows_include_required_fields(tmp_path: Path) -> None:
    result = build_source_registry_schema_fixture(output_dir=tmp_path)

    fields = pd.read_csv(result.artifact_paths["schema_fields"], dtype=str)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str)

    assert set(REQUIRED_SOURCE_REGISTRY_FIELDS).issubset(set(fields["field_name"]))
    assert set(REQUIRED_SOURCE_REGISTRY_FIELDS).issubset(set(rows.columns))
    assert set(rows["source_id"]) == {
        "LOCAL_CSV_REVIEWED_SAMPLE",
        "PUBLIC_OFFICIAL_ANNOUNCEMENT_SAMPLE",
        "PUBLIC_WRAPPER_OPTIONAL_SAMPLE",
        "PAID_VENDOR_FUTURE_BACKUP_SAMPLE",
        "BLOCKED_PRIVATE_UNVERIFIED_SAMPLE",
    }
    assert (rows["report_only"] == "True").all()
    assert (rows["diagnostic_only"] == "True").all()
    assert rows["source_id"].map(type).eq(str).all()


def test_fixture_row_policies_are_conservative(tmp_path: Path) -> None:
    result = build_source_registry_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).set_index("source_id")

    local_csv = rows.loc["LOCAL_CSV_REVIEWED_SAMPLE"]
    assert local_csv["project_role"] == "PRIMARY_LOCAL_FALLBACK"
    assert local_csv["manual_review_required"] == "True"
    assert local_csv["replay_suitability"] == "REPLAY_READY_AFTER_REVIEW"
    assert local_csv["report_only"] == "True"

    public_wrapper = rows.loc["PUBLIC_WRAPPER_OPTIONAL_SAMPLE"]
    assert public_wrapper["source_type"] == "PUBLIC_WRAPPER"
    assert public_wrapper["reliability_status"] == "PARTIALLY_VERIFIED"
    assert public_wrapper["manual_review_required"] == "True"
    assert public_wrapper["replay_suitability"] == "VALIDATION_ONLY"

    paid_vendor = rows.loc["PAID_VENDOR_FUTURE_BACKUP_SAMPLE"]
    assert paid_vendor["source_type"] == "PAID_VENDOR"
    assert paid_vendor["project_role"] == "FUTURE_BACKUP"
    assert paid_vendor["replay_suitability"] == "REPLAY_CONTEXT_ONLY"
    assert paid_vendor["quality_status"] == "REVIEW_REQUIRED"

    blocked_private = rows.loc["BLOCKED_PRIVATE_UNVERIFIED_SAMPLE"]
    assert blocked_private["source_type"] == "BLOCKED_PRIVATE"
    assert blocked_private["permission_class"] == "PROHIBITED"
    assert blocked_private["replay_suitability"] == "BLOCKED"
    assert blocked_private["quality_status"] == "BLOCKED"


def test_no_source_row_implies_trading_buy_review_or_performance(tmp_path: Path) -> None:
    result = build_source_registry_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str)
    row_text = " ".join(rows.fillna("").astype(str).agg(" ".join, axis=1)).lower()

    assert "token" not in row_text
    assert "secret" not in row_text
    assert "trading_allowed=true" not in row_text
    assert "buy_review_allowed=true" not in row_text
    assert "real_buy_review_eligible=true" not in row_text
    assert "strategy_performance_validated=true" not in row_text

    validation = pd.read_csv(result.artifact_paths["validation_summary"], dtype=str)
    assert (validation["passed"] == "True").all()


def test_permission_and_replay_matrices_capture_blockers(tmp_path: Path) -> None:
    result = build_source_registry_schema_fixture(output_dir=tmp_path)
    permission = pd.read_csv(result.artifact_paths["permission_matrix"], dtype=str).set_index("source_id")
    replay = pd.read_csv(result.artifact_paths["replay_suitability_matrix"], dtype=str).set_index("source_id")

    assert permission.loc["BLOCKED_PRIVATE_UNVERIFIED_SAMPLE", "permission_decision"] == "BLOCK"
    assert replay.loc["BLOCKED_PRIVATE_UNVERIFIED_SAMPLE", "replay_allowed_without_review"] == "False"
    assert replay.loc["PAID_VENDOR_FUTURE_BACKUP_SAMPLE", "current_dependency_allowed"] == "False"
    assert replay.loc["PUBLIC_WRAPPER_OPTIONAL_SAMPLE", "canonical_permission_source"] == "False"


def test_cli_command_runs_successfully(tmp_path: Path) -> None:
    output_dir = tmp_path / "manual_diagnostics" / "source_registry_schema_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "source-registry-schema-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "source_registry_schema_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert "source_count: 5" in completed.stdout
    assert "report_only: True" in completed.stdout
    assert "diagnostic_only: True" in completed.stdout
    assert "No data/raw, data/processed, data/cache" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "source_registry_fixture_rows.csv").exists()


def test_recommended_next_task_and_project_source_boundary(tmp_path: Path) -> None:
    result = build_source_registry_schema_fixture(output_dir=tmp_path)

    next_task = result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8")

    assert "Source Registry Schema Fixture Views Report-Only v0.1" in next_task
    assert not (tmp_path / "docs" / "project_sources").exists()
