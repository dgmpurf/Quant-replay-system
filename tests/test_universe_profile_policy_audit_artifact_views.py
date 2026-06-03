from pathlib import Path

import json
import pandas as pd

from quant_replay_system import cli
from quant_replay_system.universe_profile_policy_audit import build_universe_profile_policy_audit
from quant_replay_system.universe_profile_policy_audit_health import check_universe_profile_policy_audit_health
from quant_replay_system.universe_profile_policy_audit_index import build_universe_profile_policy_audit_index
from quant_replay_system.universe_profile_policy_audit_status import run_universe_profile_policy_audit_status


def test_index_detects_fake_policy_audit_artifacts(tmp_path: Path) -> None:
    root = _build_policy_audit_root(tmp_path)

    result = build_universe_profile_policy_audit_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["row_count"] == 2
    assert row["stock_row_count"] == 1
    assert row["etf_row_count"] == 1
    assert row["ambiguous_policy_count"] == 2
    assert row["no_universe_export"] == True  # noqa: E712


def test_health_warns_for_expected_ambiguous_mixed_universe(tmp_path: Path) -> None:
    root = _build_policy_audit_root(tmp_path)

    result = check_universe_profile_policy_audit_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "WARN"
    assert result.error_count == 0
    assert "AMBIGUOUS_MIXED_UNIVERSE_CONTEXT" in set(result.health_frame["issue_code"])


def test_health_fails_if_approval_or_rejection_was_applied(tmp_path: Path) -> None:
    root = _build_policy_audit_root(tmp_path)
    audit_csv = next(root.glob("*/universe_profile_policy_audit.csv"))
    frame = pd.read_csv(audit_csv, keep_default_na=False)
    frame.loc[0, "should_approve"] = True
    frame.to_csv(audit_csv, index=False)

    result = check_universe_profile_policy_audit_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "APPROVAL_APPLIED_DETECTED" in set(result.health_frame["issue_code"])


def test_health_fails_if_data_write_or_current_candidates_generation_detected(tmp_path: Path) -> None:
    root = _build_policy_audit_root(tmp_path)
    metadata_path = next(root.glob("*/metadata.json"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["no_data_raw_write"] = False
    metadata["current_candidates_executed"] = True
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    result = check_universe_profile_policy_audit_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    issues = set(result.health_frame["issue_code"])
    assert "DATA_RAW_WRITE_DETECTED" in issues
    assert "CURRENT_CANDIDATES_GENERATED" in issues


def test_status_summarizes_ambiguous_mixed_universe(tmp_path: Path) -> None:
    root = _build_policy_audit_root(tmp_path)

    result = run_universe_profile_policy_audit_status(root=root, output_dir=tmp_path / "status")

    assert result.status == "WARN"
    assert result.workflow_stage == "UNIVERSE_PROFILE_POLICY_AMBIGUOUS_MIXED_UNIVERSE"
    assert result.row_count == 2
    assert result.stock_row_count == 1
    assert result.etf_row_count == 1
    assert result.ambiguous_policy_count == 2


def test_status_ready_for_clean_split_universe(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
            _worklist_row("2024-04-09", "159915", "etf_core", "ETF"),
        ],
    )
    root = tmp_path / "audits"
    build_universe_profile_policy_audit(worklist=worklist, output_dir=root)

    result = run_universe_profile_policy_audit_status(root=root, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == "UNIVERSE_PROFILE_POLICY_AUDIT_READY"
    assert result.ambiguous_policy_count == 0


def test_cli_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = _build_policy_audit_root(tmp_path)

    assert cli.main(["universe-profile-policy-audit-index", "--root", str(root), "--output-dir", str(tmp_path / "index")]) == 0
    assert "artifact_count: 1" in capsys.readouterr().out

    assert cli.main(["universe-profile-policy-audit-health", "--root", str(root), "--output-dir", str(tmp_path / "health")]) == 0
    assert "status: WARN" in capsys.readouterr().out

    assert cli.main(["universe-profile-policy-audit-status", "--root", str(root), "--output-dir", str(tmp_path / "status")]) == 0
    output = capsys.readouterr().out
    assert "workflow_stage: UNIVERSE_PROFILE_POLICY_AMBIGUOUS_MIXED_UNIVERSE" in output
    assert "No approval, rejection, universe export" in output


def _build_policy_audit_root(tmp_path: Path) -> Path:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
        ],
    )
    root = tmp_path / "audits"
    build_universe_profile_policy_audit(worklist=worklist, output_dir=root)
    return root


def _write_worklist(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _worklist_row(signal_date: str, symbol: str, universe_name: str, instrument_type: str) -> dict:
    return {
        "worklist_id": "worklist001",
        "review_id": "review001",
        "signal_date": signal_date,
        "symbol": symbol,
        "universe_name": universe_name,
        "suggested_instrument_type": instrument_type,
        "current_review_status": "NEEDS_MANUAL_REVIEW",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "worklist_only": True,
    }
