import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.config import CurrentCandidateArtifactHealthSettings
from quant_replay_system.current_candidate_artifact_health import (
    check_current_candidate_artifact_health,
)
from quant_replay_system.current_candidate_artifact_index import (
    build_current_candidate_artifact_index,
    load_current_candidate_metadata,
    scan_current_candidate_artifacts,
)


pytestmark = [pytest.mark.integration, pytest.mark.slow]


def test_current_candidate_artifact_index_scans_valid_artifact_folders(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root, run_id="run-a")

    result = build_current_candidate_artifact_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["artifact_type"] == "CURRENT_CANDIDATES"
    assert row["run_id"] == "run-a"
    assert row["decision_date"] == "2024-05-20"
    assert row["universe_name"] == "etf_core"
    assert row["candidate_count"] == 2


def test_index_csv_is_written_and_readable_by_pandas(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root)

    result = build_current_candidate_artifact_index(root=root, output_dir=tmp_path / "index")
    frame = pd.read_csv(result.artifact_paths["current_candidate_artifact_index_csv"])

    assert len(frame) == 1
    assert "candidates_path" in frame.columns


def test_index_markdown_report_is_written(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root)

    result = build_current_candidate_artifact_index(root=root, output_dir=tmp_path / "index")
    content = result.artifact_paths["current_candidate_artifact_index"].read_text(encoding="utf-8")

    assert "# Current Candidate Artifact Index" in content
    assert "## Artifact Index" in content


def test_index_json_is_written(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root)

    result = build_current_candidate_artifact_index(root=root, output_dir=tmp_path / "index")
    payload = json.loads(result.artifact_paths["current_candidate_artifact_index_json"].read_text(encoding="utf-8"))

    assert isinstance(payload, list)
    assert payload[0]["artifact_type"] == "CURRENT_CANDIDATES"


def test_index_metadata_json_is_written(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root)

    result = build_current_candidate_artifact_index(root=root, output_dir=tmp_path / "index")
    metadata = load_current_candidate_metadata(result.artifact_paths["metadata"])

    assert metadata["artifact_count"] == 1
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_missing_metadata_is_skipped_by_default(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root)
    (root / "2024-05-20_missing_run").mkdir(parents=True)

    result = build_current_candidate_artifact_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    assert "missing_run" not in set(result.index_frame["run_id"].astype(str))


def test_missing_metadata_can_be_included_with_warning(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    (root / "2024-05-20_missing_run").mkdir(parents=True)

    result = build_current_candidate_artifact_index(
        root=root,
        output_dir=tmp_path / "index",
        include_missing_metadata=True,
    )

    assert result.artifact_count == 1
    assert result.warnings
    assert result.index_frame.iloc[0]["run_id"] == "2024-05-20_missing_run"


def test_current_candidates_index_cli_works(tmp_path: Path, capsys) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root)

    code = cli.main(["current-candidates-index", "--root", str(root), "--output-dir", str(tmp_path / "index")])
    output = capsys.readouterr()

    assert code == 0
    assert "artifact_count: 1" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_health_check_passes_for_valid_current_candidate_artifacts(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    result = check_current_candidate_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0


def test_missing_report_file_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "current_candidates_report.md").unlink()

    result = check_current_candidate_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "FILE_NOT_FOUND", "report_path")


def test_missing_candidates_csv_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "candidates.csv").unlink()

    result = check_current_candidate_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "FILE_NOT_FOUND", "candidates_path")


def test_unreadable_candidates_csv_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "candidates.csv").write_bytes(b"\xff\xfe\x00\x00")

    result = check_current_candidate_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "CSV_UNREADABLE", "candidates_path")


def test_empty_candidates_csv_produces_configured_warning(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "candidates.csv").write_text("symbol,final_score,action\n", encoding="utf-8")

    result = check_current_candidate_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "WARN"
    issue = _issue_row(result.health_frame, "CSV_EMPTY", "candidates_path")
    assert issue["severity"] == "WARN"


def test_missing_required_candidate_columns_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    pd.DataFrame([{"symbol": "AAA"}]).to_csv(_artifact_file(tmp_path, "candidates.csv"), index=False)

    result = check_current_candidate_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "MISSING_REQUIRED_CANDIDATE_COLUMN", "candidates_path")


def test_missing_no_live_trading_statement_uses_configured_severity(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "current_candidates_report.md").write_text("Current candidate report.", encoding="utf-8")

    warn_result = check_current_candidate_artifact_health(index_path=index_path, output_dir=tmp_path / "health_warn")
    fail_result = check_current_candidate_artifact_health(
        index_path=index_path,
        output_dir=tmp_path / "health_fail",
        settings=CurrentCandidateArtifactHealthSettings(missing_no_live_statement_severity="ERROR"),
    )

    assert warn_result.status == "WARN"
    assert _issue_row(warn_result.health_frame, "MISSING_NO_LIVE_TRADING_STATEMENT", "report_path")["severity"] == "WARN"
    assert fail_result.status == "FAIL"
    assert _issue_row(fail_result.health_frame, "MISSING_NO_LIVE_TRADING_STATEMENT", "report_path")["severity"] == "ERROR"


def test_current_candidates_health_cli_works(tmp_path: Path, capsys) -> None:
    index_path = _build_valid_index(tmp_path)

    code = cli.main(["current-candidates-health", "--index", str(index_path), "--output-dir", str(tmp_path / "health")])
    output = capsys.readouterr()

    assert code == 0
    assert "Health status: PASS" in output.out
    assert "Report path:" in output.out


def test_health_cli_exits_nonzero_on_fail_by_default(tmp_path: Path, capsys) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "candidates.csv").unlink()

    code = cli.main(["current-candidates-health", "--index", str(index_path), "--output-dir", str(tmp_path / "health")])
    output = capsys.readouterr()

    assert code == 1
    assert "Health status: FAIL" in output.out


def test_health_cli_prints_no_live_trading_statement(tmp_path: Path, capsys) -> None:
    index_path = _build_valid_index(tmp_path)

    code = cli.main(["current-candidates-health", "--index", str(index_path), "--output-dir", str(tmp_path / "health")])
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_health_output_is_deterministic_for_same_input(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    first = check_current_candidate_artifact_health(index_path=index_path, output_dir=tmp_path / "health")
    second = check_current_candidate_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert first.health_check_id == second.health_check_id
    assert first.health_frame.to_dict("records") == second.health_frame.to_dict("records")
    assert first.summary_frame.to_dict("records") == second.summary_frame.to_dict("records")


def test_index_and_health_do_not_invoke_live_trading_or_network(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root)

    index = build_current_candidate_artifact_index(root=root, output_dir=tmp_path / "index")
    health = check_current_candidate_artifact_health(
        index_path=index.artifact_paths["current_candidate_artifact_index_csv"],
        output_dir=tmp_path / "health",
    )

    assert index.audit_metadata["live_trading_enabled"] is False
    assert index.audit_metadata["broker_api_invoked"] is False
    assert health.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False


def test_scan_skips_index_and_health_subfolders(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root)
    (root / "index").mkdir(parents=True)
    (root / "health").mkdir(parents=True)

    frame = scan_current_candidate_artifacts(root)

    assert len(frame) == 1


def _build_valid_index(tmp_path: Path) -> Path:
    root = _current_root(tmp_path)
    _current_artifact(root)
    index = build_current_candidate_artifact_index(root=root, output_dir=tmp_path / "index")
    return index.artifact_paths["current_candidate_artifact_index_csv"]


def _current_root(tmp_path: Path) -> Path:
    root = tmp_path / "current_candidates"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _current_artifact(root: Path, *, run_id: str = "run-a") -> Path:
    folder = root / f"2024-05-20_etf_core_{run_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidates_report.md"
    factor = folder / "factor_dataset.csv"
    scored = folder / "scored_dataset.csv"
    candidates = folder / "candidates.csv"
    metadata_path = folder / "metadata.json"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    pd.DataFrame([{"symbol": "AAA", "decision_date": "2024-05-20"}]).to_csv(factor, index=False)
    pd.DataFrame([{"symbol": "AAA", "final_score": 75.0}]).to_csv(scored, index=False)
    pd.DataFrame(
        [
            {"symbol": "AAA", "final_score": 82.0, "action": "PAPER_TRADE"},
            {"symbol": "BBB", "final_score": 76.0, "action": "PAPER_TRADE"},
        ]
    ).to_csv(candidates, index=False)
    metadata = {
        "decision_date": "2024-05-20T00:00:00",
        "decision_time": "2024-05-20T15:30:00",
        "universe_name": "etf_core",
        "top_n": 5,
        "run_id": run_id,
        "created_at": "2024-05-20T00:00:00",
        "row_counts": {
            "factor_dataset": 1,
            "scored_dataset": 1,
            "candidates": 2,
        },
        "output_files": {
            "current_candidates_report": str(report),
            "factor_dataset": str(factor),
            "scored_dataset": str(scored),
            "candidates": str(candidates),
            "metadata": str(metadata_path),
        },
        "snapshot_quality": {"status": "PASS", "report_path": ""},
        "audit_metadata": {
            "snapshot_quality_preflight_enabled": True,
            "snapshot_quality_status": "PASS",
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return folder


def _artifact_file(tmp_path: Path, filename: str) -> Path:
    return tmp_path / "current_candidates" / "2024-05-20_etf_core_run-a" / filename


def _has_issue(frame: pd.DataFrame, issue_code: str, path_field: str) -> bool:
    if frame.empty:
        return False
    return bool(((frame["issue_code"] == issue_code) & (frame["path_field"] == path_field)).any())


def _issue_row(frame: pd.DataFrame, issue_code: str, path_field: str) -> dict:
    rows = frame.loc[(frame["issue_code"] == issue_code) & (frame["path_field"] == path_field)]
    assert not rows.empty
    return rows.iloc[0].to_dict()
