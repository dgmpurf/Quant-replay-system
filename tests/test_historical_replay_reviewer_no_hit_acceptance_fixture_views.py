import csv
import json
from pathlib import Path

from quant_replay_system.historical_replay_reviewer_no_hit_acceptance_fixture import (
    OUTPUT_FILES,
    run_historical_replay_reviewer_no_hit_acceptance_fixture,
)
from quant_replay_system.historical_replay_reviewer_no_hit_acceptance_fixture_health import (
    STATUS_HEALTH_FAIL,
    STATUS_HEALTH_PASS,
    check_historical_replay_reviewer_no_hit_acceptance_fixture_health,
)
from quant_replay_system.historical_replay_reviewer_no_hit_acceptance_fixture_index import (
    STATUS_INDEX_CREATED,
    build_historical_replay_reviewer_no_hit_acceptance_fixture_index,
)
from quant_replay_system.historical_replay_reviewer_no_hit_acceptance_fixture_status import (
    NEXT_TASK,
    STATUS_CREATED,
    run_historical_replay_reviewer_no_hit_acceptance_fixture_status,
)


EXPECTED_NEXT_TASK = "Historical Replay Reviewer No-Hit Acceptance Fixture Generated Artifact Review Report-Only v0.1"


def test_index_discovers_no_hit_acceptance_fixture_and_exports_counts(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)

    result = build_historical_replay_reviewer_no_hit_acceptance_fixture_index(root=tmp_path / "out")
    row = result.rows[0]

    assert result.status == STATUS_INDEX_CREATED
    assert result.artifact_count == 1
    assert row["run_id"] == run.run_id
    assert row["row_count"] == 9
    assert row["stock_row_count"] == 7
    assert row["etf_row_count"] == 2
    assert row["no_hit_row_count"] == 9
    assert row["not_accepted_count"] == 9
    assert row["accepted_context_count"] == 0
    assert row["row_with_blocker_count"] == 9
    assert row["profile_conflict_count"] == 7
    assert row["survivorship_warning_count"] == 9
    assert row["safety_true_count"] == 0
    assert row["recommended_next_task"] == EXPECTED_NEXT_TASK
    assert row["report_path"].endswith(OUTPUT_FILES["report"])


def test_health_passes_for_complete_not_accepted_fixture(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)

    result = check_historical_replay_reviewer_no_hit_acceptance_fixture_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_PASS
    assert result.checked_artifact_count == 1
    assert result.error_count == 0
    assert result.issue_count == 0


def test_health_fails_on_missing_required_file(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    run.artifact_paths["metadata"].unlink()

    result = check_historical_replay_reviewer_no_hit_acceptance_fixture_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_on_accepted_no_hit_context_or_positive_safety_flag(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    rows = _read_csv(run.artifact_paths["reviewer_no_hit_acceptance_rows"])
    rows[0]["no_hit_acceptance_status"] = "accepted_for_review_context_only_not_evidence"
    context_field = "no_hit_context_accepted"
    rows[0][context_field] = "true"
    _write_csv(run.artifact_paths["reviewer_no_hit_acceptance_rows"], rows)
    _patch_json(run.artifact_paths["safety_flags"], {"trading_allowed": True})

    result = check_historical_replay_reviewer_no_hit_acceptance_fixture_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    codes = _issue_codes(result)
    assert "NO_HIT_CONTEXT_ACCEPTED_UNSAFE" in codes
    assert "FORBIDDEN_SAFETY_FLAG_TRUE" in codes


def test_health_fails_on_missing_blockers_or_private_reviewer_identity(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    rows = _read_csv(run.artifact_paths["reviewer_no_hit_acceptance_rows"])
    rows[0]["blocker_reason"] = ""
    rows[1]["reviewer_private_identity_disclosed"] = "yes"
    _write_csv(run.artifact_paths["reviewer_no_hit_acceptance_rows"], rows)

    result = check_historical_replay_reviewer_no_hit_acceptance_fixture_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    codes = _issue_codes(result)
    assert "NO_HIT_BLOCKERS_MISSING" in codes
    assert "PRIVATE_REVIEWER_IDENTITY_DISCLOSED" in codes


def test_status_summarizes_latest_artifact_and_preserves_next_task(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)

    result = run_historical_replay_reviewer_no_hit_acceptance_fixture_status(root=tmp_path / "out")

    assert result.status == STATUS_CREATED
    assert result.latest_run_id == run.run_id
    assert result.latest_status == "REVIEWER_NO_HIT_ACCEPTANCE_FIXTURE_CREATED_REPORT_ONLY"
    assert result.latest_health_status == STATUS_HEALTH_PASS
    assert result.latest_workflow_stage == (
        "HISTORICAL_REPLAY_REVIEWER_NO_HIT_ACCEPTANCE_FIXTURE_CREATED_REPORT_ONLY"
    )
    assert result.recommended_next_task == EXPECTED_NEXT_TASK
    assert NEXT_TASK == EXPECTED_NEXT_TASK
    assert result.summary["latest_no_hit_row_count"] == 9
    assert result.summary["latest_not_accepted_count"] == 9
    assert result.summary["latest_accepted_context_count"] == 0
    assert result.summary["latest_row_with_blocker_count"] == 9
    assert result.summary["latest_safety_true_count"] == 0
    assert result.summary["latest_buy_review_allowed"] is False
    assert result.summary["latest_trading_allowed"] is False


def test_status_no_artifacts_is_benign_and_report_only(tmp_path: Path) -> None:
    result = run_historical_replay_reviewer_no_hit_acceptance_fixture_status(root=tmp_path / "empty")

    assert result.latest_run_id == ""
    assert result.latest_status == "REVIEWER_NO_HIT_ACCEPTANCE_FIXTURE_STATUS_NO_ARTIFACTS"
    assert result.recommended_next_task == EXPECTED_NEXT_TASK
    assert result.summary["report_only"] is True
    assert result.summary["diagnostic_only"] is True
    assert result.summary["latest_buy_review_allowed"] is False
    assert result.summary["latest_trading_allowed"] is False


def _create_core_artifact(tmp_path: Path):
    return run_historical_replay_reviewer_no_hit_acceptance_fixture(
        root=tmp_path / "reports",
        output_dir=tmp_path / "out",
        run_id="view_no_hit",
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
