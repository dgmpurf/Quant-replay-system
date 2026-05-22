import json
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.data_preparation_workflow_status import (
    DataPreparationWorkflowStatusResult,
    infer_data_preparation_next_action,
    infer_data_preparation_workflow_stage,
    run_data_preparation_workflow_status,
)


DECISION_DATE = "2024-01-08"
UNIVERSE = "etf_core"


def test_status_dashboard_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_data_preparation_workflow_status(root=_reports_root(tmp_path), output_dir=tmp_path / "status")

    assert isinstance(result, DataPreparationWorkflowStatusResult)
    assert result.workflow_stage == "NO_DATA_PIPELINE"
    assert result.status == "WARN"
    assert result.next_manual_action == "Run data-pipeline."


def test_dashboard_detects_data_pipeline_artifact(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _data_pipeline(root)

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_pipeline_id == "pipeline-a"
    assert result.data_pipeline_status == "PASS"
    assert result.workflow_stage == "DATA_PIPELINE_READY"


def test_dashboard_detects_data_quality_artifact(tmp_path: Path) -> None:
    root = _workflow_to_data_quality(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.data_quality_status == "PASS"
    assert result.workflow_stage == "SNAPSHOT_READY"


def test_dashboard_detects_snapshot_quality_artifact(tmp_path: Path) -> None:
    root = _workflow_to_snapshot_quality(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.snapshot_quality_status == "PASS"
    assert result.latest_snapshot_id == "snapshot-a"
    assert result.workflow_stage == "SNAPSHOT_QUALITY_READY"


def test_dashboard_detects_current_candidates_artifact(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.current_candidate_status == "READY"
    assert result.latest_decision_date == DECISION_DATE
    assert result.workflow_stage == "CURRENT_CANDIDATES_READY"


def test_dashboard_detects_data_prep_index_artifact(tmp_path: Path) -> None:
    root = _workflow_to_data_prep_index(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.data_prep_index_status == "READY"
    assert result.workflow_stage == "DATA_PREP_INDEX_READY"


def test_dashboard_detects_data_prep_health_artifact(tmp_path: Path) -> None:
    root = _workflow_complete(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.data_prep_health_status == "PASS"
    assert result.workflow_stage == "DATA_PREP_WORKFLOW_COMPLETE"
    assert result.status == "PASS"


def test_dashboard_infers_next_manual_action_for_missing_data_pipeline(tmp_path: Path) -> None:
    result = run_data_preparation_workflow_status(root=_reports_root(tmp_path), output_dir=tmp_path / "status")

    assert result.next_manual_action == "Run data-pipeline."


def test_dashboard_infers_next_manual_action_after_data_pipeline(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _data_pipeline(root)

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.next_manual_action == "Run data-quality."


def test_dashboard_infers_next_manual_action_after_snapshot_quality(tmp_path: Path) -> None:
    root = _workflow_to_snapshot_quality(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.next_manual_action == "Run current-candidates."
    assert infer_data_preparation_workflow_stage(result.status_frame) == "SNAPSHOT_QUALITY_READY"


def test_dashboard_infers_next_manual_action_after_current_candidates(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.next_manual_action == "Run data-prep-index."
    assert infer_data_preparation_next_action(result.status_frame) == "Run data-prep-index."


def test_dashboard_marks_needs_attention_when_health_fails(tmp_path: Path) -> None:
    root = _workflow_to_data_prep_index(_reports_root(tmp_path))
    _data_prep_health(root, status="FAIL", errors=1)

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.workflow_stage == "DATA_PREP_NEEDS_ATTENTION"
    assert result.status == "FAIL"
    assert result.next_manual_action == "Review warnings/errors."


def test_dashboard_writes_markdown_report(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.artifact_paths["data_preparation_workflow_status_report"].exists()
    content = result.artifact_paths["data_preparation_workflow_status_report"].read_text(encoding="utf-8")
    assert "# Data Preparation Workflow Status" in content


def test_dashboard_writes_status_csv_readable_by_pandas(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")
    exported = pd.read_csv(result.artifact_paths["data_preparation_workflow_status_csv"])

    assert "component" in exported.columns
    assert "DATA_PIPELINE" in set(exported["component"])


def test_dashboard_writes_summary_csv_readable_by_pandas(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")
    exported = pd.read_csv(result.artifact_paths["data_preparation_workflow_summary"])

    assert exported.iloc[0]["workflow_stage"] == "CURRENT_CANDIDATES_READY"


def test_dashboard_writes_metadata_json(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["workflow_status_id"] == result.workflow_status_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False
    assert metadata["network_api_calls_used_in_tests"] is False


def test_dashboard_status_frame_contains_required_columns(tmp_path: Path) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert {
        "component",
        "status",
        "latest_artifact_id",
        "dataset_type",
        "snapshot_id",
        "decision_date",
        "universe_name",
        "report_path",
        "metadata_path",
        "issue_count",
        "warning_count",
        "error_count",
        "next_action",
        "notes",
    }.issubset(result.status_frame.columns)


def test_cli_data_prep_status_works(tmp_path: Path, capsys) -> None:
    root = _workflow_to_current_candidates(_reports_root(tmp_path))

    code = cli.main(["data-prep-status", "--root", str(root), "--output-dir", str(tmp_path / "status")])
    output = capsys.readouterr()

    assert code == 0
    assert "Workflow status:" in output.out
    assert "Report path:" in output.out


def test_cli_prints_next_manual_action(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)

    code = cli.main(["data-prep-status", "--root", str(root), "--output-dir", str(tmp_path / "status")])
    output = capsys.readouterr()

    assert code == 0
    assert "next_manual_action: Run data-pipeline." in output.out


def test_cli_prints_no_live_trading_statement(tmp_path: Path, capsys) -> None:
    root = _reports_root(tmp_path)

    code = cli.main(["data-prep-status", "--root", str(root), "--output-dir", str(tmp_path / "status")])
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_dashboard_output_is_deterministic(tmp_path: Path) -> None:
    root = _workflow_complete(_reports_root(tmp_path))

    first = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")
    second = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert first.workflow_status_id == second.workflow_status_id
    assert first.status_frame.to_dict("records") == second.status_frame.to_dict("records")
    assert first.summary_frame.to_dict("records") == second.summary_frame.to_dict("records")


def test_dashboard_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    root = _workflow_complete(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["data_preparation_only"] is True
    assert not any("broker" in module_name.lower() for module_name in sys.modules)


def test_dashboard_no_real_network_api_calls_are_used(tmp_path: Path) -> None:
    root = _workflow_complete(_reports_root(tmp_path))

    result = run_data_preparation_workflow_status(root=root, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.audit_metadata["network_api_calls_used_in_tests"] is False


def _reports_root(tmp_path: Path) -> Path:
    root = tmp_path / "reports"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _workflow_to_data_quality(root: Path) -> Path:
    _data_pipeline(root)
    _data_quality(root)
    return root


def _workflow_to_snapshot_quality(root: Path) -> Path:
    _workflow_to_data_quality(root)
    _snapshot_quality(root)
    return root


def _workflow_to_current_candidates(root: Path) -> Path:
    _workflow_to_snapshot_quality(root)
    _current_candidates(root)
    return root


def _workflow_to_data_prep_index(root: Path) -> Path:
    _workflow_to_current_candidates(root)
    _data_prep_index(root)
    return root


def _workflow_complete(root: Path) -> Path:
    _workflow_to_data_prep_index(root)
    _data_prep_health(root, status="PASS")
    return root


def _data_pipeline(root: Path, *, pipeline_id: str = "pipeline-a") -> Path:
    folder = root / "data_pipeline" / pipeline_id
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "data_pipeline_report.md"
    snapshot_manifest = folder / "snapshot_manifest.json"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    snapshot_manifest.write_text(json.dumps({"snapshot_id": "snapshot-a"}), encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "pipeline_id": pipeline_id,
            "created_at": f"{DECISION_DATE}T09:00:00",
            "status": "PASS",
            "dataset_count": 3,
            "dataset_results": [
                {"dataset_type": "market", "status": "PASS"},
                {"dataset_type": "universe", "status": "PASS"},
                {"dataset_type": "trading_calendar", "status": "PASS"},
            ],
            "processed_paths": {"market": str(folder / "market.csv")},
            "snapshot_manifest_path": str(snapshot_manifest),
            "output_files": {"data_pipeline_report": str(report), "snapshot_manifest": str(snapshot_manifest)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _data_quality(root: Path, *, status: str = "PASS") -> Path:
    folder = root / "data_quality" / "market" / "quality-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "data_quality_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "quality_run_id": "quality-a",
            "dataset_type": "market",
            "created_at": f"{DECISION_DATE}T09:10:00",
            "status": status,
            "row_count": 2,
            "issue_count": 0 if status == "PASS" else 1,
            "warning_count": 1 if status == "WARN" else 0,
            "error_count": 1 if status == "FAIL" else 0,
            "output_files": {"data_quality_report": str(report)},
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _snapshot_quality(root: Path, *, status: str = "PASS") -> Path:
    folder = root / "snapshot_quality" / "snapshot-a_gate-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "snapshot_quality_gate_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "snapshot_id": "snapshot-a",
            "quality_gate_id": "gate-a",
            "created_at": f"{DECISION_DATE}T09:20:00",
            "status": status,
            "required_dataset_count": 3,
            "warning_count": 1 if status == "WARN" else 0,
            "error_count": 1 if status == "FAIL" else 0,
            "output_files": {"snapshot_quality_gate_report": str(report)},
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _current_candidates(root: Path, *, run_id: str = "run-a") -> Path:
    folder = root / "current_candidates" / f"{DECISION_DATE}_{UNIVERSE}_{run_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidates_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "run_id": run_id,
            "decision_date": DECISION_DATE,
            "universe_name": UNIVERSE,
            "created_at": f"{DECISION_DATE}T09:30:00",
            "row_counts": {"factor_dataset": 2, "scored_dataset": 2, "candidates": 1},
            "output_files": {"current_candidates_report": str(report), "candidates": str(folder / "candidates.csv")},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _data_prep_index(root: Path) -> Path:
    folder = root / "data_preparation" / "index"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "data_preparation_artifact_index.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "index_id": "data-prep-index-a",
            "created_at": f"{DECISION_DATE}T09:40:00",
            "artifact_count": 4,
            "output_files": {"data_preparation_artifact_index": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _data_prep_health(root: Path, *, status: str = "PASS", errors: int = 0, warnings: int = 0) -> Path:
    folder = root / "data_preparation" / "health" / "data-prep-health-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "data_preparation_artifact_health_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "health_check_id": "data-prep-health-a",
            "created_at": f"{DECISION_DATE}T09:45:00",
            "status": status,
            "checked_artifact_count": 4,
            "issue_count": errors + warnings,
            "error_count": errors,
            "warning_count": warnings,
            "output_files": {"data_preparation_artifact_health_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
