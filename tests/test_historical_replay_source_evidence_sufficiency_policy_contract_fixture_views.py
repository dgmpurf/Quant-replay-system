from __future__ import annotations

import csv
import json
from pathlib import Path

from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture import (
    run_historical_replay_source_evidence_sufficiency_policy_contract_fixture,
)
from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture_health import (
    STATUS_HEALTH_FAIL,
    STATUS_HEALTH_PASS,
    STATUS_HEALTH_WARN,
    check_historical_replay_source_evidence_sufficiency_policy_contract_fixture_health,
)
from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture_index import (
    build_historical_replay_source_evidence_sufficiency_policy_contract_fixture_index,
)
from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture_status import (
    STATUS_NO_ARTIFACTS,
    run_historical_replay_source_evidence_sufficiency_policy_contract_fixture_status,
)


NEXT_TASK = (
    "Historical Replay Source / Evidence Sufficiency Policy Contract Fixture "
    "Checkpoint Documentation Bundle Report-Only v0.1"
)
OLD_COMPLETED_REVIEW_TASK = (
    "Historical Replay Source / Evidence Sufficiency Policy Contract Fixture "
    "Generated Artifact Review Report-Only v0.1"
)


def _build(root: Path, run_id: str = "fixture-run"):
    return run_historical_replay_source_evidence_sufficiency_policy_contract_fixture(
        root=root,
        output_dir=root,
        run_id=run_id,
    )


def test_index_emits_one_safe_relative_row_for_one_valid_run(tmp_path: Path) -> None:
    _build(tmp_path)
    result = build_historical_replay_source_evidence_sufficiency_policy_contract_fixture_index(
        root=tmp_path
    )

    assert result.artifact_count == 1
    row = result.rows[0]
    assert row["run_id"] == "fixture-run"
    assert row["artifact_path"] == "fixture-run"
    assert row["report_path"].startswith("fixture-run/")
    assert not Path(row["report_path"]).is_absolute()
    assert row["row_count"] == 9
    assert row["stock_row_count"] == 7
    assert row["etf_row_count"] == 2
    assert row["evidence_family_count"] == 17
    assert row["row_evidence_family_contract_count"] == 153
    assert row["applicable_contract_row_count"] == 144
    assert row["instrument_not_applicable_context_row_count"] == 9
    assert row["safety_true_count"] == 0
    assert row["recommended_next_task"] == NEXT_TASK
    assert row["recommended_next_task"] != OLD_COMPLETED_REVIEW_TASK
    assert result.artifact_paths["index_csv"].is_file()


def test_safe_fixture_health_passes_and_status_preserves_negative_proof(
    tmp_path: Path,
) -> None:
    core = _build(tmp_path)
    health = check_historical_replay_source_evidence_sufficiency_policy_contract_fixture_health(
        root=tmp_path
    )
    status = run_historical_replay_source_evidence_sufficiency_policy_contract_fixture_status(
        root=tmp_path
    )

    assert health.status == STATUS_HEALTH_PASS
    assert health.checked_artifact_count == 1
    assert health.issue_count == health.error_count == health.warning_count == 0
    assert status.latest_run_id == core.run_id
    assert status.latest_health_status == STATUS_HEALTH_PASS
    assert status.summary["latest_row_count"] == 9
    assert status.summary["latest_selected_row_with_blocker_count"] == 9
    assert status.summary["latest_sufficiency_candidate_count"] == 0
    assert status.summary["latest_evidence_accepted_count"] == 0
    assert status.summary["latest_evidence_closed_count"] == 0
    assert status.summary["latest_pit_admissible_count"] == 0
    assert status.summary["latest_replay_ready_count"] == 0
    assert status.summary["latest_safety_true_count"] == 0
    assert status.recommended_next_task == NEXT_TASK
    assert status.recommended_next_task != OLD_COMPLETED_REVIEW_TASK


def test_no_artifact_mode_is_benign_warn_and_zero_count(tmp_path: Path) -> None:
    index = build_historical_replay_source_evidence_sufficiency_policy_contract_fixture_index(
        root=tmp_path
    )
    health = check_historical_replay_source_evidence_sufficiency_policy_contract_fixture_health(
        root=tmp_path
    )
    status = run_historical_replay_source_evidence_sufficiency_policy_contract_fixture_status(
        root=tmp_path
    )

    assert index.artifact_count == 0
    assert health.status == STATUS_HEALTH_WARN
    assert health.error_count == 0
    assert status.latest_status == STATUS_NO_ARTIFACTS
    assert status.latest_run_id == ""
    assert status.summary["latest_row_count"] == 0
    assert status.summary["latest_safety_true_count"] == 0


def test_optional_context_limitation_produces_warning_only(tmp_path: Path) -> None:
    result = _build(tmp_path)
    metadata_path = result.artifact_paths["metadata"]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["optional_context_limitation"] = "Vocabulary note requires human review."
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    health = check_historical_replay_source_evidence_sufficiency_policy_contract_fixture_health(
        root=tmp_path
    )
    assert health.status == STATUS_HEALTH_WARN
    assert health.error_count == 0
    assert health.warning_count == 1
    assert health.rows[0]["issue_code"] == "OPTIONAL_CONTEXT_LIMITATION"


def test_unsafe_selected_state_mutation_fails_health(tmp_path: Path) -> None:
    result = _build(tmp_path)
    path = result.artifact_paths["selected_rows"]
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    rows[0]["selected_row_evidence_accepted"] = "true"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    health = check_historical_replay_source_evidence_sufficiency_policy_contract_fixture_health(
        root=tmp_path
    )
    assert health.status == STATUS_HEALTH_FAIL
    assert any(row["issue_code"] == "FORBIDDEN_SELECTED_ROW_STATE_TRUE" for row in health.rows)


def test_missing_artifact_and_public_disclosure_fail_health(tmp_path: Path) -> None:
    result = _build(tmp_path)
    result.artifact_paths["required_fields"].unlink()
    result.artifact_paths["report"].write_text(
        result.artifact_paths["report"].read_text(encoding="utf-8")
        + "\nunsafe="
        + "a" * 64
        + "\n",
        encoding="utf-8",
    )

    health = check_historical_replay_source_evidence_sufficiency_policy_contract_fixture_health(
        root=tmp_path
    )
    issue_codes = {row["issue_code"] for row in health.rows}
    assert health.status == STATUS_HEALTH_FAIL
    assert "MISSING_REQUIRED_ARTIFACT" in issue_codes
    assert "FULL_HASH_DISCLOSURE" in issue_codes
