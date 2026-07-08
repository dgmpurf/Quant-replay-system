import csv
import json
from pathlib import Path

from quant_replay_system.historical_replay_official_manual_evidence_collection_template_fixture import (
    OUTPUT_FILES,
    run_historical_replay_official_manual_evidence_collection_template_fixture,
)
from quant_replay_system.historical_replay_official_manual_evidence_collection_template_fixture_health import (
    STATUS_HEALTH_FAIL,
    STATUS_HEALTH_PASS,
    check_historical_replay_official_manual_evidence_collection_template_fixture_health,
)
from quant_replay_system.historical_replay_official_manual_evidence_collection_template_fixture_index import (
    STATUS_INDEX_CREATED,
    build_historical_replay_official_manual_evidence_collection_template_fixture_index,
)
from quant_replay_system.historical_replay_official_manual_evidence_collection_template_fixture_status import (
    NEXT_TASK,
    STATUS_CREATED,
    run_historical_replay_official_manual_evidence_collection_template_fixture_status,
)


EXPECTED_NEXT_TASK = (
    "Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1"
)


def test_index_discovers_template_fixture_and_exports_counts(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)

    result = build_historical_replay_official_manual_evidence_collection_template_fixture_index(
        root=tmp_path / "out"
    )
    row = result.rows[0]

    assert result.status == STATUS_INDEX_CREATED
    assert result.artifact_count == 1
    assert row["run_id"] == run.run_id
    assert row["row_count"] == 9
    assert row["stock_row_count"] == 7
    assert row["etf_row_count"] == 2
    assert row["evidence_collection_template_row_count"] == 72
    assert row["source_lineage_template_row_count"] == 72
    assert row["no_hit_template_row_count"] == 9
    assert row["survivorship_template_row_count"] == 9
    assert row["reviewer_notes_template_row_count"] == 9
    assert row["profile_conflict_count"] == 7
    assert row["survivorship_warning_count"] == 9
    assert row["safety_true_count"] == 0
    assert row["recommended_next_task"] == EXPECTED_NEXT_TASK
    assert row["report_path"].endswith(OUTPUT_FILES["report"])


def test_health_passes_for_complete_empty_synthetic_template(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)

    result = check_historical_replay_official_manual_evidence_collection_template_fixture_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_PASS
    assert result.checked_artifact_count == 1
    assert result.error_count == 0
    assert result.issue_count == 0


def test_health_fails_on_missing_required_file(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    run.artifact_paths["metadata"].unlink()

    result = check_historical_replay_official_manual_evidence_collection_template_fixture_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_on_wrong_counts_or_positive_safety_flag(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    _patch_json(run.artifact_paths["metadata"], {"evidence_collection_template_row_count": 71})

    result = check_historical_replay_official_manual_evidence_collection_template_fixture_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "EVIDENCE_TEMPLATE_COUNT_MISMATCH" in _issue_codes(result)

    run = _create_core_artifact(tmp_path / "unsafe")
    _patch_json(run.artifact_paths["safety_flags"], {"trading_allowed": True})
    result = check_historical_replay_official_manual_evidence_collection_template_fixture_health(
        root=run.artifact_paths["metadata"].parents[1]
    )

    assert result.status == STATUS_HEALTH_FAIL
    assert "FORBIDDEN_SAFETY_FLAG_TRUE" in _issue_codes(result)


def test_health_fails_if_no_hit_or_reviewer_rows_imply_acceptance(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    no_hit = _read_csv(run.artifact_paths["no_hit_query_handoff_template"])
    no_hit[0]["no_hit_acceptance_status"] = "accepted"
    _write_csv(run.artifact_paths["no_hit_query_handoff_template"], no_hit)
    reviewer = _read_csv(run.artifact_paths["reviewer_notes_template"])
    reviewer[0]["reviewer_private_identity_disclosed"] = "yes"
    _write_csv(run.artifact_paths["reviewer_notes_template"], reviewer)

    result = check_historical_replay_official_manual_evidence_collection_template_fixture_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    codes = _issue_codes(result)
    assert "NO_HIT_ACCEPTED_UNSAFE" in codes
    assert "PRIVATE_REVIEWER_IDENTITY_DISCLOSED" in codes


def test_status_summarizes_latest_artifact_and_preserves_next_task(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)

    result = run_historical_replay_official_manual_evidence_collection_template_fixture_status(root=tmp_path / "out")

    assert result.status == STATUS_CREATED
    assert result.latest_run_id == run.run_id
    assert result.latest_status == "OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_CREATED_REPORT_ONLY"
    assert result.latest_health_status == STATUS_HEALTH_PASS
    assert result.latest_workflow_stage == (
        "HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_CREATED_REPORT_ONLY"
    )
    assert result.recommended_next_task == EXPECTED_NEXT_TASK
    assert NEXT_TASK == EXPECTED_NEXT_TASK
    assert result.summary["latest_evidence_collection_template_row_count"] == 72
    assert result.summary["latest_source_lineage_template_row_count"] == 72
    assert result.summary["latest_safety_true_count"] == 0
    assert result.summary["latest_buy_review_allowed"] is False
    assert result.summary["latest_trading_allowed"] is False


def test_status_no_artifacts_is_benign_and_report_only(tmp_path: Path) -> None:
    result = run_historical_replay_official_manual_evidence_collection_template_fixture_status(root=tmp_path / "empty")

    assert result.latest_run_id == ""
    assert result.latest_status == "OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_STATUS_NO_ARTIFACTS"
    assert result.recommended_next_task == EXPECTED_NEXT_TASK
    assert result.summary["report_only"] is True
    assert result.summary["diagnostic_only"] is True
    assert result.summary["latest_buy_review_allowed"] is False
    assert result.summary["latest_trading_allowed"] is False


def _create_core_artifact(tmp_path: Path):
    return run_historical_replay_official_manual_evidence_collection_template_fixture(
        root=tmp_path / "reports",
        output_dir=tmp_path / "out",
        run_id="view_run",
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
