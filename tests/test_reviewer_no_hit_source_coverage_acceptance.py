import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance import (
    build_reviewer_no_hit_source_coverage_acceptance,
)
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance_health import (
    check_reviewer_no_hit_source_coverage_acceptance_health,
)
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance_index import (
    build_reviewer_no_hit_source_coverage_acceptance_index,
)
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance_status import (
    run_reviewer_no_hit_source_coverage_acceptance_status,
)


def test_reviewer_no_hit_acceptance_creates_review_template_without_approvals(tmp_path: Path) -> None:
    enrichment = _enrichment_fixture(tmp_path)
    audit = _audit_fixture(tmp_path)
    comparison = _comparison_fixture(tmp_path)

    result = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=enrichment,
        audit=audit,
        policy_comparison=comparison,
        output_dir=tmp_path / "acceptance",
    )

    assert result.row_count == 8
    assert result.accepted_count == 0
    assert result.needs_review_count == 8
    assert result.reviewer_acceptance_required_count == 8
    assert result.checklist_pass_count == 0
    assert result.remaining_blocked_count == 2
    assert set(result.acceptance_frame["symbol"]) == {"000001", "159915"}
    assert not result.acceptance_frame["approval_applied"].any()
    assert not result.acceptance_frame["pit_review_run"].any()
    assert not result.acceptance_frame["universe_exported"].any()
    assert result.acceptance_frame["no_data_raw_write"].all()
    assert result.acceptance_frame["no_data_processed_write"].all()
    assert result.acceptance_frame["no_current_candidates_generated"].all()
    assert "APPROVED_FOR_PIT_UNIVERSE" not in result.acceptance_frame.to_csv(index=False)


def test_reviewer_no_hit_acceptance_supporting_context_still_does_not_pass_checklist(tmp_path: Path) -> None:
    enrichment = _enrichment_fixture(tmp_path)
    audit = _audit_fixture(tmp_path)
    comparison = _comparison_fixture(tmp_path)
    updates = tmp_path / "reviewer_acceptance.csv"
    pd.DataFrame(
        [
            {
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "stock_core",
                "exception_type": "DELISTING",
                "acceptance_status": "ACCEPTED_AS_SUPPORTING_CONTEXT",
                "source_coverage_accepted": True,
                "query_window_accepted": True,
                "no_hit_inference_accepted": True,
                "accepted_by": "reviewer",
                "accepted_at": "2026-06-05T10:00:00",
                "acceptance_reason": "Source coverage accepted as supporting no-hit context.",
                "evidence_reference": "local-diagnostics://no-hit-source",
            }
        ]
    ).to_csv(updates, index=False)

    result = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=enrichment,
        audit=audit,
        policy_comparison=comparison,
        reviewer_acceptance=updates,
        output_dir=tmp_path / "acceptance",
    )

    accepted = result.acceptance_frame.loc[
        result.acceptance_frame["acceptance_status"] == "ACCEPTED_AS_SUPPORTING_CONTEXT"
    ]
    assert len(accepted) == 1
    assert result.accepted_count == 1
    assert result.accepted_supporting_context_count == 1
    assert result.checklist_pass_count == 0
    assert result.remaining_blocked_count == 2


def test_reviewer_no_hit_acceptance_blocks_incomplete_survivorship_acceptance(tmp_path: Path) -> None:
    enrichment = _enrichment_fixture(tmp_path)
    audit = _audit_fixture(tmp_path)
    comparison = _comparison_fixture(tmp_path)
    updates = tmp_path / "reviewer_acceptance.csv"
    pd.DataFrame(
        [
            {
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "stock_core",
                "exception_type": "SURVIVORSHIP_RATIONALE",
                "acceptance_status": "ACCEPTED_AS_SUPPORTING_CONTEXT",
                "source_coverage_accepted": True,
                "query_window_accepted": True,
                "no_hit_inference_accepted": True,
                "accepted_by": "reviewer",
                "accepted_at": "2026-06-05T10:00:00",
                "acceptance_reason": "Coverage accepted.",
                "evidence_reference": "local-diagnostics://no-hit-source",
            }
        ]
    ).to_csv(updates, index=False)

    result = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=enrichment,
        audit=audit,
        policy_comparison=comparison,
        reviewer_acceptance=updates,
        output_dir=tmp_path / "acceptance",
    )

    row = result.acceptance_frame.loc[
        result.acceptance_frame["exception_type"] == "SURVIVORSHIP_RATIONALE"
    ].iloc[0]
    assert row["acceptance_status"] == "NEEDS_MORE_EVIDENCE"
    assert "survivorship_rationale" in row["blocker_reason"]
    assert not bool(row["accepted_as_supporting_context"])


def test_reviewer_no_hit_acceptance_index_health_status_and_cli(tmp_path: Path) -> None:
    result = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=_enrichment_fixture(tmp_path),
        audit=_audit_fixture(tmp_path),
        policy_comparison=_comparison_fixture(tmp_path),
        output_dir=tmp_path / "acceptance",
    )

    index = build_reviewer_no_hit_source_coverage_acceptance_index(
        root=tmp_path / "acceptance",
        output_dir=tmp_path / "acceptance" / "index",
    )
    health = check_reviewer_no_hit_source_coverage_acceptance_health(
        root=tmp_path / "acceptance",
        output_dir=tmp_path / "acceptance" / "health",
    )
    status = run_reviewer_no_hit_source_coverage_acceptance_status(
        root=tmp_path / "acceptance",
        output_dir=tmp_path / "acceptance" / "status",
    )

    assert index["artifact_count"] == 1
    assert health["status"] == "PASS"
    assert status["status"] == "WARN"
    assert status["workflow_stage"] == "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_NEEDS_REVIEW"
    assert status["latest_acceptance_id"] == result.acceptance_id

    code = cli.main(
        [
            "reviewer-no-hit-source-coverage-acceptance-status",
            "--root",
            str(tmp_path / "acceptance"),
            "--output-dir",
            str(tmp_path / "acceptance" / "status_cli"),
        ]
    )
    assert code == 0


def test_reviewer_no_hit_acceptance_health_fails_on_approval_text(tmp_path: Path) -> None:
    result = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=_enrichment_fixture(tmp_path),
        audit=_audit_fixture(tmp_path),
        policy_comparison=_comparison_fixture(tmp_path),
        output_dir=tmp_path / "acceptance",
    )
    csv_path = result.artifact_paths["acceptance_csv"]
    frame = pd.read_csv(csv_path, keep_default_na=False)
    frame.loc[0, "acceptance_status"] = "APPROVED_FOR_PIT_UNIVERSE"
    frame.to_csv(csv_path, index=False)

    health = check_reviewer_no_hit_source_coverage_acceptance_health(
        root=tmp_path / "acceptance",
        output_dir=tmp_path / "acceptance" / "health",
    )

    assert health["status"] == "FAIL"
    assert "APPROVED_FOR_PIT_UNIVERSE_DETECTED" in set(health["health_frame"]["issue_code"])


def _enrichment_fixture(tmp_path: Path) -> Path:
    folder = tmp_path / "enrichment" / "enrichment-a"
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"signal_date": "2024-04-02", "symbol": "000001", "universe_name": "stock_core"},
            {"signal_date": "2024-04-02", "symbol": "159915", "universe_name": "etf_core"},
        ]
    ).to_csv(folder / "pit_official_status_evidence_packet_enrichment.csv", index=False)
    (folder / "metadata.json").write_text(
        json.dumps(
            {
                "enrichment_id": "enrichment-a",
                "source_packet_id": "packet-a",
                "policy_comparison_id": "comparison-a",
                "created_at": "2026-06-05T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    return folder


def _audit_fixture(tmp_path: Path) -> Path:
    folder = tmp_path / "audit"
    folder.mkdir(parents=True, exist_ok=True)
    for name in [
        "source_coverage_acceptance_rules.csv",
        "query_window_rules.csv",
        "survivorship_rationale_template.csv",
        "blocker_after_acceptance_matrix.csv",
    ]:
        pd.DataFrame([{"rule": "review_required"}]).to_csv(folder / name, index=False)
    return folder


def _comparison_fixture(tmp_path: Path) -> Path:
    folder = tmp_path / "comparison" / "comparison-a"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "metadata.json").write_text(json.dumps({"comparison_id": "comparison-a"}), encoding="utf-8")
    return folder
