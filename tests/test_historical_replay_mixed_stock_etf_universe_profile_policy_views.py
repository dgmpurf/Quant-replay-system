import csv
import json
from pathlib import Path

from quant_replay_system.historical_replay_mixed_stock_etf_universe_profile_policy import (
    OUTPUT_FILES,
    run_historical_replay_mixed_stock_etf_universe_profile_policy,
)
from quant_replay_system.historical_replay_mixed_stock_etf_universe_profile_policy_health import (
    STATUS_HEALTH_FAIL,
    STATUS_HEALTH_PASS,
    check_historical_replay_mixed_stock_etf_universe_profile_policy_health,
)
from quant_replay_system.historical_replay_mixed_stock_etf_universe_profile_policy_index import (
    STATUS_INDEX_CREATED,
    build_historical_replay_mixed_stock_etf_universe_profile_policy_index,
)
from quant_replay_system.historical_replay_mixed_stock_etf_universe_profile_policy_status import (
    NEXT_TASK,
    STATUS_CREATED,
    run_historical_replay_mixed_stock_etf_universe_profile_policy_status,
)


EXPECTED_NEXT_TASK = (
    "Historical Replay Source / Evidence Sufficiency Policy Planning Without Evidence Collection Report-Only v0.1"
)
OLD_NEXT_TASK = (
    "Historical Replay Mixed STOCK/ETF Universe Profile Policy Tag and Source Readiness Planning Report-Only v0.1"
)


def test_index_discovers_mixed_profile_policy_fixture_and_exports_counts(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)

    result = build_historical_replay_mixed_stock_etf_universe_profile_policy_index(root=tmp_path / "out")
    row = result.rows[0]

    assert result.status == STATUS_INDEX_CREATED
    assert result.artifact_count == 1
    assert row["run_id"] == run.run_id
    assert row["row_count"] == 9
    assert row["stock_row_count"] == 7
    assert row["etf_row_count"] == 2
    assert row["profile_conflict_count"] == 7
    assert row["profile_aligned_context_count"] == 2
    assert row["profile_policy_accepted_count"] == 0
    assert row["no_hit_row_count"] == 9
    assert row["not_accepted_count"] == 9
    assert row["accepted_context_count"] == 0
    assert row["universe_membership_approved_count"] == 0
    assert row["survivorship_warning_count"] == 9
    assert row["safety_true_count"] == 0
    assert row["recommended_next_task"] == EXPECTED_NEXT_TASK
    assert row["recommended_next_task"] != OLD_NEXT_TASK
    assert row["report_path"].endswith(OUTPUT_FILES["report"])


def test_health_passes_for_complete_report_only_fixture(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)

    result = check_historical_replay_mixed_stock_etf_universe_profile_policy_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_PASS
    assert result.checked_artifact_count == 1
    assert result.error_count == 0
    assert result.issue_count == 0


def test_health_fails_on_missing_file_or_unsafe_flags(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    run.artifact_paths["metadata"].unlink()

    result = check_historical_replay_mixed_stock_etf_universe_profile_policy_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)

    run = _create_core_artifact(tmp_path, run_id="unsafe")
    _patch_json(run.artifact_paths["metadata"], {"profile_conflict_resolved": True})
    rows = _read_csv(run.artifact_paths["policy_rows"])
    rows[0]["profile_conflict_resolved"] = "true"
    _write_csv(run.artifact_paths["policy_rows"], rows)

    result = check_historical_replay_mixed_stock_etf_universe_profile_policy_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    codes = _issue_codes(result)
    assert "FORBIDDEN_METADATA_FLAG_TRUE" in codes
    assert "FORBIDDEN_ROW_FLAG_TRUE" in codes


def test_health_fails_when_profile_conflict_or_membership_boundary_is_violated(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    rows = _read_csv(run.artifact_paths["policy_rows"])
    rows[0]["profile_conflict"] = "false"
    rows[0]["profile_policy_status"] = "accepted_for_policy_context_only_not_pit_approved"
    rows[1]["legacy_universe_label_is_universe_proof"] = "true"
    rows[2]["blocker_reason"] = ""
    _write_csv(run.artifact_paths["policy_rows"], rows)

    result = check_historical_replay_mixed_stock_etf_universe_profile_policy_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    codes = _issue_codes(result)
    assert "PROFILE_CONFLICT_VISIBILITY_MISMATCH" in codes
    assert "PROFILE_POLICY_ACCEPTED_UNSAFE" in codes
    assert "FORBIDDEN_ROW_FLAG_TRUE" in codes
    assert "PROFILE_POLICY_BLOCKERS_MISSING" in codes


def test_status_summarizes_latest_artifact_and_recommended_next_task(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)

    result = run_historical_replay_mixed_stock_etf_universe_profile_policy_status(root=tmp_path / "out")

    assert result.status == STATUS_CREATED
    assert result.latest_run_id == run.run_id
    assert result.latest_status == "MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_FIXTURE_CREATED_REPORT_ONLY"
    assert result.latest_health_status == STATUS_HEALTH_PASS
    assert result.latest_workflow_stage == (
        "HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_FIXTURE_CREATED_REPORT_ONLY"
    )
    assert result.recommended_next_task == EXPECTED_NEXT_TASK
    assert NEXT_TASK == EXPECTED_NEXT_TASK
    assert result.recommended_next_task != OLD_NEXT_TASK
    assert result.summary["latest_row_count"] == 9
    assert result.summary["latest_profile_conflict_count"] == 7
    assert result.summary["latest_profile_policy_accepted_count"] == 0
    assert result.summary["latest_no_hit_row_count"] == 9
    assert result.summary["latest_not_accepted_count"] == 9
    assert result.summary["latest_accepted_context_count"] == 0
    assert result.summary["latest_universe_membership_approved_count"] == 0
    assert result.summary["latest_survivorship_warning_count"] == 9
    assert result.summary["latest_buy_review_allowed"] is False
    assert result.summary["latest_trading_allowed"] is False


def test_status_no_artifacts_is_benign_report_only(tmp_path: Path) -> None:
    result = run_historical_replay_mixed_stock_etf_universe_profile_policy_status(root=tmp_path / "empty")

    assert result.latest_run_id == ""
    assert result.latest_status == "MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_STATUS_NO_ARTIFACTS"
    assert result.summary["report_only"] is True
    assert result.summary["diagnostic_only"] is True
    assert result.summary["latest_buy_review_allowed"] is False
    assert result.summary["latest_trading_allowed"] is False
    assert result.summary["latest_no_hit_row_count"] == 0
    assert result.summary["latest_survivorship_warning_count"] == 0


def _create_core_artifact(tmp_path: Path, run_id: str = "view_mixed_profile"):
    return run_historical_replay_mixed_stock_etf_universe_profile_policy(
        root=tmp_path / "reports",
        output_dir=tmp_path / "out",
        run_id=run_id,
    )


def _issue_codes(result) -> set[str]:
    return {row["issue_code"] for row in result.rows}


def _patch_json(path: Path, patch: dict) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(patch)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
