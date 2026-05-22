import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.paper_artifact_index import (
    build_paper_artifact_index,
    load_paper_artifact_metadata,
    scan_paper_trading_artifacts,
)


pytestmark = [pytest.mark.integration, pytest.mark.slow]


def test_artifact_index_scans_daily_artifacts(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _daily_artifact(root, journal_id="daily-a")

    result = build_paper_artifact_index(root=root, output_dir=tmp_path / "index", artifact_type="daily")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["artifact_type"] == "DAILY"
    assert row["artifact_id"] == "daily-a"
    assert row["artifact_date"] == "2024-05-20"
    assert row["open_position_count"] == 1
    assert row["closed_trade_count"] == 0


def test_artifact_index_scans_review_artifacts(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _review_artifact(root, review_id="review-a")

    frame = scan_paper_trading_artifacts(root, artifact_type="review")

    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["artifact_type"] == "REVIEW"
    assert row["artifact_id"] == "review-a"
    assert row["reviewed_decisions_path"].endswith("reviewed_decisions.csv")


def test_artifact_index_scans_reconciliation_artifacts(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _reconciliation_artifact(root, reconciliation_id="recon-a", status="FAIL", errors=2)

    result = build_paper_artifact_index(root=root, output_dir=tmp_path / "index", artifact_type="reconciliation")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["artifact_type"] == "RECONCILIATION"
    assert row["status"] == "FAIL"
    assert row["error_count"] == 2
    assert row["reconciliation_report_path"].endswith("reconciliation_report.md")


def test_missing_metadata_is_skipped_by_default(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _daily_artifact(root, journal_id="daily-a")
    (root / "daily" / "missing-metadata").mkdir(parents=True)

    result = build_paper_artifact_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    assert "missing-metadata" not in set(result.index_frame["artifact_id"])
    assert not result.warnings


def test_missing_metadata_can_be_included_with_warning(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    (root / "daily" / "missing-metadata").mkdir(parents=True)

    result = build_paper_artifact_index(
        root=root,
        output_dir=tmp_path / "index",
        include_missing_metadata=True,
    )

    assert result.artifact_count == 1
    assert result.index_frame.iloc[0]["status"] == "MISSING_METADATA"
    assert result.warnings


def test_index_csv_is_written_and_readable_by_pandas(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _daily_artifact(root)

    result = build_paper_artifact_index(root=root, output_dir=tmp_path / "index")
    csv_frame = pd.read_csv(result.artifact_paths["paper_artifact_index_csv"])

    assert len(csv_frame) == 1
    assert "artifact_type" in csv_frame.columns


def test_index_markdown_report_is_written(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _daily_artifact(root)

    result = build_paper_artifact_index(root=root, output_dir=tmp_path / "index")
    content = result.artifact_paths["paper_artifact_index"].read_text(encoding="utf-8")

    assert "# Paper Trading Artifact Index" in content
    assert "## Artifact Index" in content


def test_index_json_is_written(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _daily_artifact(root)

    result = build_paper_artifact_index(root=root, output_dir=tmp_path / "index")
    payload = json.loads(result.artifact_paths["paper_artifact_index_json"].read_text(encoding="utf-8"))

    assert isinstance(payload, list)
    assert payload[0]["artifact_type"] == "DAILY"


def test_index_metadata_json_is_written(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _daily_artifact(root)

    result = build_paper_artifact_index(root=root, output_dir=tmp_path / "index")
    metadata = load_paper_artifact_metadata(result.artifact_paths["metadata"])

    assert metadata["artifact_count"] == 1
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_no_live_trading_statement_detection_works(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _daily_artifact(root, journal_id="with-statement", include_no_live_statement=True)
    _daily_artifact(root, journal_id="without-statement", include_no_live_statement=False)

    result = build_paper_artifact_index(root=root, output_dir=tmp_path / "index", artifact_type="daily")
    by_id = {
        row["artifact_id"]: row["no_live_trading_statement_present"]
        for row in result.index_frame.to_dict("records")
    }

    assert bool(by_id["with-statement"]) is True
    assert bool(by_id["without-statement"]) is False


def test_cli_paper_index_works(tmp_path: Path, capsys) -> None:
    root = _paper_root(tmp_path)
    _daily_artifact(root)

    code = cli.main(["paper-index", "--root", str(root), "--output-dir", str(tmp_path / "index")])
    output = capsys.readouterr()

    assert code == 0
    assert "artifact_count: 1" in output.out
    assert (tmp_path / "index" / "paper_artifact_index.md").exists()


def test_cli_paper_index_prints_no_live_trading_statement(tmp_path: Path, capsys) -> None:
    root = _paper_root(tmp_path)
    _daily_artifact(root)

    code = cli.main(["paper-index", "--root", str(root), "--output-dir", str(tmp_path / "index")])
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_artifact_index_output_is_deterministic(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _reconciliation_artifact(root, reconciliation_id="recon-b", status="WARN", errors=0, warnings=1)
    _daily_artifact(root, journal_id="daily-a")
    _review_artifact(root, review_id="review-c")

    first = build_paper_artifact_index(root=root, output_dir=tmp_path / "index")
    second = build_paper_artifact_index(root=root, output_dir=tmp_path / "index")

    assert first.index_frame.to_dict("records") == second.index_frame.to_dict("records")
    assert first.artifact_paths == second.artifact_paths


def test_artifact_index_does_not_invoke_live_trading_or_broker(tmp_path: Path) -> None:
    root = _paper_root(tmp_path)
    _daily_artifact(root)

    result = build_paper_artifact_index(root=root, output_dir=tmp_path / "index")

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["paper_trading_only"] is True


def _paper_root(tmp_path: Path) -> Path:
    root = tmp_path / "paper_trading"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _daily_artifact(
    root: Path,
    *,
    journal_id: str = "daily-a",
    include_no_live_statement: bool = True,
) -> Path:
    folder = root / "daily" / f"2024-05-20_{journal_id}"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_report.md"
    decisions = folder / "decisions.csv"
    fills = folder / "fills.csv"
    daily_summary = folder / "daily_summary.csv"
    report.write_text(
        "No broker or live trading integration was invoked."
        if include_no_live_statement
        else "Local artifact without the explicit safety sentence.",
        encoding="utf-8",
    )
    pd.DataFrame([{"decision_id": "d1", "symbol": "AAA"}]).to_csv(decisions, index=False)
    pd.DataFrame([{"fill_id": "f1", "symbol": "AAA"}]).to_csv(fills, index=False)
    pd.DataFrame(
        [
            {
                "paper_cash": 9000.0,
                "total_equity": 10050.0,
                "open_position_count": 1,
                "closed_trade_count": 0,
            }
        ]
    ).to_csv(daily_summary, index=False)
    metadata = {
        "paper_date": "2024-05-20T00:00:00",
        "journal_id": journal_id,
        "created_at": "2024-05-20T00:00:00",
        "decision_count": 1,
        "fill_count": 1,
        "open_position_count": 1,
        "closed_trade_count": 0,
        "reconciliation": {
            "status": "PASS",
            "report_path": "",
            "issue_count": 0,
            "error_count": 0,
            "warning_count": 0,
        },
        "output_files": {
            "paper_report": str(report),
            "decisions": str(decisions),
            "fills": str(fills),
            "daily_summary": str(daily_summary),
        },
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
    }
    if include_no_live_statement:
        metadata["no_live_trading_statement"] = "No broker or live trading integration was invoked."
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return folder


def _review_artifact(root: Path, *, review_id: str = "review-a") -> Path:
    folder = root / "reviews" / review_id
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_review_report.md"
    reviewed = folder / "reviewed_decisions.csv"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    pd.DataFrame([{"decision_id": "d1", "manual_review_status": "APPROVED_FOR_PAPER"}]).to_csv(
        reviewed,
        index=False,
    )
    metadata = {
        "review_id": review_id,
        "created_at": "2024-05-20T00:00:00",
        "output_files": {
            "paper_review_report": str(report),
            "reviewed_decisions": str(reviewed),
        },
        "warnings": [],
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return folder


def _reconciliation_artifact(
    root: Path,
    *,
    reconciliation_id: str = "recon-a",
    status: str = "PASS",
    errors: int = 0,
    warnings: int = 0,
) -> Path:
    folder = root / "reconciliation" / reconciliation_id
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "reconciliation_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    metadata = {
        "reconciliation_id": reconciliation_id,
        "created_at": "2024-05-20T00:00:00",
        "status": status,
        "issue_count": errors + warnings,
        "error_count": errors,
        "warning_count": warnings,
        "output_files": {
            "reconciliation_report": str(report),
        },
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
    }
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return folder
