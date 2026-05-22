import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.current_candidate_artifact_index import build_current_candidate_artifact_index
from quant_replay_system.current_to_paper_handoff import (
    CurrentToPaperHandoffResult,
    generate_current_to_paper_handoff_id,
    run_current_to_paper_handoff,
    select_current_candidate_artifact_for_paper,
)


def test_direct_candidates_path_handoff_works(tmp_path: Path) -> None:
    candidates_path = _direct_candidates(tmp_path)

    result = run_current_to_paper_handoff(
        candidates_path=candidates_path,
        paper_date="2024-05-20",
        config=_settings(tmp_path),
    )

    assert isinstance(result, CurrentToPaperHandoffResult)
    assert result.selected_candidates_path == candidates_path
    assert result.selected_artifact.source_type == "DIRECT_CANDIDATES_PATH"
    assert result.paper_result.decision_count == 2


def test_index_based_handoff_selects_matching_decision_date(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root, decision_date="2024-05-19", run_id="old-run")
    expected = _current_artifact(root, decision_date="2024-05-20", run_id="new-run")
    index_path = _index_path(tmp_path, root)

    selected, _ = select_current_candidate_artifact_for_paper(
        current_candidate_index_path=index_path,
        decision_date="2024-05-20",
        config=_settings(tmp_path),
    )

    assert selected.candidates_path == expected / "candidates.csv"
    assert selected.run_id == "new-run"


def test_index_based_handoff_selects_matching_universe_name(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root, universe_name="stock_core", run_id="stock-run")
    expected = _current_artifact(root, universe_name="etf_core", run_id="etf-run")
    index_path = _index_path(tmp_path, root)

    result = run_current_to_paper_handoff(
        current_candidate_index_path=index_path,
        universe_name="etf_core",
        config=_settings(tmp_path),
    )

    assert result.selected_candidates_path == expected / "candidates.csv"
    assert result.selected_universe_name == "etf_core"


def test_latest_candidate_artifact_is_selected_by_default(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root, decision_date="2024-05-19", run_id="old-run", candidate_count=5)
    latest = _current_artifact(root, decision_date="2024-05-20", run_id="latest-run", candidate_count=1)
    index_path = _index_path(tmp_path, root)

    result = run_current_to_paper_handoff(current_candidate_index_path=index_path, config=_settings(tmp_path))

    assert result.selected_candidates_path == latest / "candidates.csv"
    assert result.selected_run_id == "latest-run"


def test_health_pass_candidate_is_accepted(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root, run_id="pass-run")
    index_path = _index_path(tmp_path, root)

    result = run_current_to_paper_handoff(current_candidate_index_path=index_path, config=_settings(tmp_path))

    assert result.health_status == "PASS"


def test_health_warn_is_rejected_by_default_when_health_pass_required(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root, run_id="warn-run", report_has_no_live_statement=False)
    index_path = _index_path(tmp_path, root)

    with pytest.raises(ValueError, match="passed health requirements"):
        run_current_to_paper_handoff(current_candidate_index_path=index_path, config=_settings(tmp_path))


def test_health_warn_is_accepted_with_allow_health_warn(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root, run_id="warn-run", report_has_no_live_statement=False)
    index_path = _index_path(tmp_path, root)

    result = run_current_to_paper_handoff(
        current_candidate_index_path=index_path,
        allow_health_warn=True,
        config=_settings(tmp_path),
    )

    assert result.health_status == "WARN"
    assert any("health status WARN" in warning for warning in result.warnings)


def test_no_matching_candidate_raises_clear_error(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root, universe_name="etf_core")
    index_path = _index_path(tmp_path, root)

    with pytest.raises(ValueError, match="No current-candidate artifacts matched"):
        run_current_to_paper_handoff(
            current_candidate_index_path=index_path,
            universe_name="missing_universe",
            config=_settings(tmp_path),
        )


def test_daily_paper_runner_is_invoked_and_artifacts_are_produced(tmp_path: Path) -> None:
    candidates_path = _direct_candidates(tmp_path)

    result = run_current_to_paper_handoff(
        candidates_path=candidates_path,
        paper_date="2024-05-20",
        config=_settings(tmp_path),
    )

    assert result.paper_result.decision_count == 2
    assert result.paper_artifact_paths["paper_report"].exists()
    assert result.paper_artifact_paths["decisions"].exists()


def test_handoff_metadata_includes_selected_path_and_source_run_id(tmp_path: Path) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root, run_id="source-run")
    index_path = _index_path(tmp_path, root)

    result = run_current_to_paper_handoff(current_candidate_index_path=index_path, config=_settings(tmp_path))
    metadata = json.loads(result.handoff_artifact_paths["handoff_metadata"].read_text(encoding="utf-8"))
    paper_metadata = json.loads(result.paper_artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["selected_candidates_path"] == str(result.selected_candidates_path)
    assert metadata["selected_run_id"] == "source-run"
    assert paper_metadata["current_to_paper_handoff"]["selected_run_id"] == "source-run"
    assert paper_metadata["current_to_paper_handoff"]["selected_candidates_path"] == str(result.selected_candidates_path)


def test_handoff_report_is_written(tmp_path: Path) -> None:
    candidates_path = _direct_candidates(tmp_path)

    result = run_current_to_paper_handoff(
        candidates_path=candidates_path,
        paper_date="2024-05-20",
        config=_settings(tmp_path),
    )
    content = result.handoff_artifact_paths["handoff_report"].read_text(encoding="utf-8")

    assert "# Current Candidate To Paper Handoff" in content
    assert "No broker or live trading integration was invoked" in content


def test_cli_current_to_paper_works_with_candidates(tmp_path: Path, capsys) -> None:
    candidates_path = _direct_candidates(tmp_path)

    code = cli.main(
        [
            "current-to-paper",
            "--candidates",
            str(candidates_path),
            "--paper-date",
            "2024-05-20",
            "--output-dir",
            str(tmp_path / "handoff_cli"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "selected_candidates_path:" in output.out
    assert "paper_report_path:" in output.out
    assert "handoff_report_path:" in output.out


def test_cli_current_to_paper_works_with_index(tmp_path: Path, capsys) -> None:
    root = _current_root(tmp_path)
    _current_artifact(root, run_id="cli-index-run")
    index_path = _index_path(tmp_path, root)

    code = cli.main(
        [
            "current-to-paper",
            "--index",
            str(index_path),
            "--decision-date",
            "2024-05-20",
            "--output-dir",
            str(tmp_path / "handoff_cli"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "health_status: PASS" in output.out
    assert "selected_candidates_path:" in output.out


def test_cli_current_to_paper_prints_no_live_trading_statement(tmp_path: Path, capsys) -> None:
    candidates_path = _direct_candidates(tmp_path)

    code = cli.main(
        [
            "current-to-paper",
            "--candidates",
            str(candidates_path),
            "--paper-date",
            "2024-05-20",
            "--output-dir",
            str(tmp_path / "handoff_cli"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_handoff_id_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    candidates_path = _direct_candidates(tmp_path)

    first = generate_current_to_paper_handoff_id(
        paper_date="2024-05-20",
        selected_candidates_path=candidates_path,
        selected_run_id="direct-run",
    )
    second = generate_current_to_paper_handoff_id(
        paper_date="2024-05-20",
        selected_candidates_path=candidates_path,
        selected_run_id="direct-run",
    )

    assert first == second


def test_no_live_trading_or_network_is_invoked(tmp_path: Path) -> None:
    candidates_path = _direct_candidates(tmp_path)

    result = run_current_to_paper_handoff(
        candidates_path=candidates_path,
        paper_date="2024-05-20",
        config=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["current_to_paper_handoff_only"] is True


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "current_to_paper_handoff": settings.current_to_paper_handoff.model_copy(
                update={"output_dir": tmp_path / "handoff", "write_artifacts": True}
            ),
            "daily_paper_runner": settings.daily_paper_runner.model_copy(
                update={"output_dir": tmp_path / "paper_daily", "write_artifacts": True}
            ),
            "paper_reconciliation": settings.paper_reconciliation.model_copy(
                update={"output_dir": tmp_path / "reconciliation", "write_artifacts": True}
            ),
            "current_candidate_artifact_health": settings.current_candidate_artifact_health.model_copy(
                update={"output_dir": tmp_path / "health", "write_artifacts": True}
            ),
        }
    )


def _direct_candidates(tmp_path: Path) -> Path:
    path = tmp_path / "direct_candidates.csv"
    _candidate_frame(run_id="direct-run").to_csv(path, index=False)
    return path


def _current_root(tmp_path: Path) -> Path:
    root = tmp_path / "current_candidates"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _index_path(tmp_path: Path, root: Path) -> Path:
    result = build_current_candidate_artifact_index(root=root, output_dir=tmp_path / "index")
    return result.artifact_paths["current_candidate_artifact_index_csv"]


def _current_artifact(
    root: Path,
    *,
    decision_date: str = "2024-05-20",
    universe_name: str = "etf_core",
    run_id: str = "run-a",
    candidate_count: int = 2,
    report_has_no_live_statement: bool = True,
) -> Path:
    folder = root / f"{decision_date}_{universe_name}_{run_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "current_candidates_report.md"
    factor = folder / "factor_dataset.csv"
    scored = folder / "scored_dataset.csv"
    candidates = folder / "candidates.csv"
    metadata_path = folder / "metadata.json"
    report.write_text(
        "No broker or live trading integration was invoked." if report_has_no_live_statement else "Current report.",
        encoding="utf-8",
    )
    pd.DataFrame([{"symbol": "AAA", "decision_date": decision_date}]).to_csv(factor, index=False)
    pd.DataFrame([{"symbol": "AAA", "final_score": 75.0}]).to_csv(scored, index=False)
    _candidate_frame(run_id=run_id, decision_date=decision_date, row_count=candidate_count).to_csv(candidates, index=False)
    metadata = {
        "decision_date": f"{decision_date}T00:00:00",
        "decision_time": f"{decision_date}T15:30:00",
        "universe_name": universe_name,
        "top_n": 5,
        "run_id": run_id,
        "created_at": f"{decision_date}T00:00:00",
        "row_counts": {
            "factor_dataset": 1,
            "scored_dataset": 1,
            "candidates": candidate_count,
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


def _candidate_frame(
    *,
    run_id: str,
    decision_date: str = "2024-05-20",
    row_count: int = 2,
) -> pd.DataFrame:
    rows = []
    for idx in range(row_count):
        symbol = chr(ord("A") + idx) * 3
        rows.append(
            {
                "decision_date": decision_date,
                "rank": idx + 1,
                "symbol": symbol,
                "name": f"{symbol} Fund",
                "final_score": 82.0 - idx,
                "action": "PAPER_TRADE",
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
                "current_candidate_run_id": run_id,
                "source_run_id": run_id,
                "source_report_path": f"outputs/reports/current_candidates/{run_id}/current_candidates_report.md",
            }
        )
    return pd.DataFrame(rows)
