import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.config import DataPreparationArtifactHealthSettings
from quant_replay_system.data_preparation_artifact_health import (
    check_data_preparation_artifact_health,
)
from quant_replay_system.data_preparation_artifact_index import (
    build_data_preparation_artifact_index,
    load_data_preparation_metadata,
)


pytestmark = pytest.mark.integration


def test_data_prep_index_scans_data_pipeline_artifacts(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _data_pipeline_artifact(root)

    result = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["artifact_type"] == "DATA_PIPELINE"
    assert row["artifact_id"] == "pipeline-a"
    assert row["snapshot_manifest_path"]
    assert row["processed_path"]


def test_data_prep_index_scans_data_quality_artifacts(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _data_quality_artifact(root)

    result = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")

    row = result.index_frame.iloc[0]
    assert row["artifact_type"] == "DATA_QUALITY"
    assert row["dataset_type"] == "market"
    assert row["issue_count"] == 0


def test_data_prep_index_scans_snapshot_quality_artifacts(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _snapshot_quality_artifact(root)

    result = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")

    row = result.index_frame.iloc[0]
    assert row["artifact_type"] == "SNAPSHOT_QUALITY"
    assert row["snapshot_id"] == "snapshot-a"
    assert row["status"] == "PASS"


def test_data_prep_index_scans_current_candidates_artifacts(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _current_candidate_artifact(root)

    result = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")

    row = result.index_frame.iloc[0]
    assert row["artifact_type"] == "CURRENT_CANDIDATES"
    assert row["decision_date"] == "2024-01-08"
    assert row["universe_name"] == "etf_core"
    assert row["candidates_path"]


def test_data_prep_index_csv_is_written_and_readable_by_pandas(tmp_path: Path) -> None:
    root = _valid_reports_root(tmp_path)

    result = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")
    frame = pd.read_csv(result.artifact_paths["data_preparation_artifact_index_csv"])

    assert len(frame) == 4
    assert "artifact_type" in frame.columns


def test_data_prep_index_markdown_report_is_written(tmp_path: Path) -> None:
    root = _valid_reports_root(tmp_path)

    result = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")
    content = result.artifact_paths["data_preparation_artifact_index"].read_text(encoding="utf-8")

    assert "# Data Preparation Artifact Index" in content
    assert "## Artifact Index" in content


def test_data_prep_index_json_is_written(tmp_path: Path) -> None:
    root = _valid_reports_root(tmp_path)

    result = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")
    payload = json.loads(result.artifact_paths["data_preparation_artifact_index_json"].read_text(encoding="utf-8"))

    assert isinstance(payload, list)
    assert {row["artifact_type"] for row in payload} == {
        "CURRENT_CANDIDATES",
        "DATA_PIPELINE",
        "DATA_QUALITY",
        "SNAPSHOT_QUALITY",
    }


def test_data_prep_index_metadata_json_is_written(tmp_path: Path) -> None:
    root = _valid_reports_root(tmp_path)

    result = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")
    metadata = load_data_preparation_metadata(result.artifact_paths["metadata"])

    assert metadata["artifact_count"] == 4
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False
    assert metadata["network_api_calls_used_in_tests"] is False


def test_missing_metadata_is_skipped_by_default(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    _data_pipeline_artifact(root)
    (root / "data_pipeline" / "missing-pipeline").mkdir(parents=True)

    result = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    assert "missing-pipeline" not in set(result.index_frame["artifact_id"].astype(str))


def test_missing_metadata_can_be_included_with_warning(tmp_path: Path) -> None:
    root = _reports_root(tmp_path)
    (root / "data_pipeline" / "missing-pipeline").mkdir(parents=True)

    result = build_data_preparation_artifact_index(
        root=root,
        output_dir=tmp_path / "index",
        include_missing_metadata=True,
    )

    assert result.artifact_count == 1
    assert result.warnings
    assert result.index_frame.iloc[0]["artifact_id"] == "missing-pipeline"


def test_data_prep_index_cli_works(tmp_path: Path, capsys) -> None:
    root = _valid_reports_root(tmp_path)

    code = cli.main(["data-prep-index", "--root", str(root), "--output-dir", str(tmp_path / "index")])
    output = capsys.readouterr()

    assert code == 0
    assert "artifact_count: 4" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_health_check_passes_for_valid_data_prep_artifacts(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    result = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 4
    assert result.issue_count == 0


def test_missing_report_file_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "data_pipeline", "pipeline-a", "data_pipeline_report.md").unlink()

    result = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "FILE_NOT_FOUND", "report_path")


def test_missing_metadata_file_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "data_pipeline", "pipeline-a", "metadata.json").unlink()

    result = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "FILE_NOT_FOUND", "metadata_path")


def test_unreadable_csv_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "data_pipeline", "pipeline-a", "processed_market.csv").write_bytes(b"\xff\xfe\x00\x00")

    result = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "CSV_UNREADABLE", "processed_path")


def test_unreadable_json_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "data_pipeline", "pipeline-a", "metadata.json").write_text("{", encoding="utf-8")

    result = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "JSON_UNREADABLE", "metadata_path")


def test_empty_candidates_csv_produces_configured_warning(tmp_path: Path) -> None:
    root = _valid_reports_root(tmp_path, empty_candidates=True)
    index = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")

    result = check_data_preparation_artifact_health(
        index_path=index.artifact_paths["data_preparation_artifact_index_csv"],
        output_dir=tmp_path / "health",
    )

    assert result.status == "WARN"
    issue = _issue_row(result.health_frame, "CSV_EMPTY", "candidates_path")
    assert issue["severity"] == "WARN"


def test_data_prep_health_artifacts_are_written_and_readable(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    result = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.artifact_paths["data_preparation_artifact_health_report"].exists()
    issues = pd.read_csv(result.artifact_paths["data_preparation_artifact_health_issues"])
    summary = pd.read_csv(result.artifact_paths["data_preparation_artifact_health_summary"])
    assert list(issues.columns)
    assert summary.iloc[0]["status"] == "PASS"


def test_data_prep_health_metadata_json_is_written(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    result = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["status"] == "PASS"
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_broken_snapshot_manifest_path_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "data_pipeline", "pipeline-a", "snapshot_manifest.json").unlink()

    result = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "FILE_NOT_FOUND", "snapshot_manifest_path")


def test_missing_no_live_statement_uses_configured_severity(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "data_pipeline", "pipeline-a", "data_pipeline_report.md").write_text(
        "Data pipeline report without safety text.",
        encoding="utf-8",
    )

    warn_result = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health_warn")
    fail_result = check_data_preparation_artifact_health(
        index_path=index_path,
        output_dir=tmp_path / "health_fail",
        settings=DataPreparationArtifactHealthSettings(missing_no_live_statement_severity="ERROR"),
    )

    assert warn_result.status == "WARN"
    assert _issue_row(warn_result.health_frame, "MISSING_NO_LIVE_TRADING_STATEMENT", "report_path")["severity"] == "WARN"
    assert fail_result.status == "FAIL"
    assert _issue_row(fail_result.health_frame, "MISSING_NO_LIVE_TRADING_STATEMENT", "report_path")["severity"] == "ERROR"


def test_data_prep_health_cli_works(tmp_path: Path, capsys) -> None:
    index_path = _build_valid_index(tmp_path)

    code = cli.main(["data-prep-health", "--index", str(index_path), "--output-dir", str(tmp_path / "health")])
    output = capsys.readouterr()

    assert code == 0
    assert "Health status: PASS" in output.out
    assert "Report path:" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_data_prep_health_cli_exits_nonzero_on_fail_by_default(tmp_path: Path, capsys) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "data_pipeline", "pipeline-a", "data_pipeline_report.md").unlink()

    code = cli.main(["data-prep-health", "--index", str(index_path), "--output-dir", str(tmp_path / "health")])
    output = capsys.readouterr()

    assert code == 1
    assert "Health status: FAIL" in output.out


def test_data_prep_health_output_is_deterministic(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    first = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health")
    second = check_data_preparation_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert first.health_check_id == second.health_check_id
    assert first.health_frame.to_dict("records") == second.health_frame.to_dict("records")
    assert first.summary_frame.to_dict("records") == second.summary_frame.to_dict("records")


def test_data_prep_index_and_health_do_not_invoke_live_trading_or_network(tmp_path: Path) -> None:
    root = _valid_reports_root(tmp_path)

    index = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")
    health = check_data_preparation_artifact_health(
        index_path=index.artifact_paths["data_preparation_artifact_index_csv"],
        output_dir=tmp_path / "health",
    )

    assert index.audit_metadata["live_trading_enabled"] is False
    assert index.audit_metadata["broker_api_invoked"] is False
    assert index.audit_metadata["network_api_calls_used_in_tests"] is False
    assert health.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False
    assert health.audit_metadata["network_api_calls_used_in_tests"] is False


def _build_valid_index(tmp_path: Path) -> Path:
    root = _valid_reports_root(tmp_path)
    index = build_data_preparation_artifact_index(root=root, output_dir=tmp_path / "index")
    return index.artifact_paths["data_preparation_artifact_index_csv"]


def _valid_reports_root(tmp_path: Path, *, empty_candidates: bool = False) -> Path:
    root = _reports_root(tmp_path)
    _data_pipeline_artifact(root)
    _data_quality_artifact(root)
    _snapshot_quality_artifact(root)
    _current_candidate_artifact(root, empty_candidates=empty_candidates)
    return root


def _reports_root(tmp_path: Path) -> Path:
    root = tmp_path / "reports"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _data_pipeline_artifact(root: Path) -> Path:
    folder = root / "data_pipeline" / "pipeline-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "data_pipeline_report.md"
    processed = folder / "processed_market.csv"
    snapshot_manifest = folder / "snapshot_manifest.json"
    metadata_path = folder / "metadata.json"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    pd.DataFrame([{"symbol": "AAA", "trade_date": "2024-01-08", "close": 10.0}]).to_csv(processed, index=False)
    snapshot_manifest.write_text(
        json.dumps(
            {
                "snapshot_id": "snapshot-a",
                "market_path": str(processed),
                "universe_path": str(processed),
                "trading_calendar_path": str(processed),
            }
        ),
        encoding="utf-8",
    )
    metadata = {
        "pipeline_id": "pipeline-a",
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": "PASS",
        "dataset_count": 1,
        "processed_paths": {"market": str(processed)},
        "snapshot_manifest_path": str(snapshot_manifest),
        "output_files": {
            "data_pipeline_report": str(report),
            "snapshot_manifest": str(snapshot_manifest),
            "metadata": str(metadata_path),
        },
        "warnings": [],
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return folder


def _data_quality_artifact(root: Path) -> Path:
    folder = root / "data_quality" / "market" / "quality-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "data_quality_report.md"
    metadata_path = folder / "metadata.json"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    metadata = {
        "quality_run_id": "quality-a",
        "dataset_type": "market",
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": "PASS",
        "row_count": 2,
        "issue_count": 0,
        "warning_count": 0,
        "error_count": 0,
        "output_files": {
            "data_quality_report": str(report),
            "metadata": str(metadata_path),
        },
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "data_quality_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return folder


def _snapshot_quality_artifact(root: Path) -> Path:
    folder = root / "snapshot_quality" / "snapshot-a_gate-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "snapshot_quality_gate_report.md"
    metadata_path = folder / "metadata.json"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    metadata = {
        "snapshot_id": "snapshot-a",
        "quality_gate_id": "gate-a",
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": "PASS",
        "required_dataset_count": 3,
        "optional_dataset_count": 0,
        "warning_count": 0,
        "error_count": 0,
        "output_files": {
            "snapshot_quality_gate_report": str(report),
            "metadata": str(metadata_path),
        },
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "snapshot_quality_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return folder


def _current_candidate_artifact(root: Path, *, empty_candidates: bool = False) -> Path:
    folder = root / "current_candidates" / "2024-01-08_etf_core_run-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidates_report.md"
    candidates = folder / "candidates.csv"
    metadata_path = folder / "metadata.json"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    candidate_rows = [] if empty_candidates else [{"symbol": "AAA", "final_score": 81.0, "action": "PAPER_TRADE"}]
    pd.DataFrame(candidate_rows, columns=["symbol", "final_score", "action"]).to_csv(candidates, index=False)
    metadata = {
        "decision_date": "2024-01-08T00:00:00",
        "decision_time": "2024-01-08T15:30:00",
        "universe_name": "etf_core",
        "top_n": 5,
        "run_id": "run-a",
        "created_at": "1970-01-01T00:00:00+00:00",
        "row_counts": {
            "factor_dataset": 1,
            "scored_dataset": 1,
            "candidates": len(candidate_rows),
        },
        "output_files": {
            "current_candidates_report": str(report),
            "candidates": str(candidates),
            "metadata": str(metadata_path),
        },
        "snapshot_quality": {"status": "PASS", "report_path": ""},
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return folder


def _artifact_file(tmp_path: Path, *parts: str) -> Path:
    return tmp_path.joinpath("reports", *parts)


def _has_issue(frame: pd.DataFrame, issue_code: str, path_field: str) -> bool:
    if frame.empty:
        return False
    return bool(((frame["issue_code"] == issue_code) & (frame["path_field"] == path_field)).any())


def _issue_row(frame: pd.DataFrame, issue_code: str, path_field: str) -> dict:
    rows = frame.loc[(frame["issue_code"] == issue_code) & (frame["path_field"] == path_field)]
    assert not rows.empty
    return rows.iloc[0].to_dict()
