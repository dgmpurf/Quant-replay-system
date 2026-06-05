import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance import (
    build_reviewer_no_hit_source_coverage_acceptance,
)
from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact import (
    build_reviewer_no_hit_acceptance_downstream_impact,
)
from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact_health import (
    check_reviewer_no_hit_acceptance_downstream_impact_health,
)
from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact_index import (
    build_reviewer_no_hit_acceptance_downstream_impact_index,
)
from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact_status import (
    run_reviewer_no_hit_acceptance_downstream_impact_status,
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


def test_tiny_reviewer_no_hit_acceptance_smoke_accepts_one_supporting_context_only(
    tmp_path: Path,
) -> None:
    enrichment = _first_batch_enrichment_fixture(tmp_path)
    audit = _audit_fixture(tmp_path)
    comparison = _comparison_fixture(tmp_path)

    baseline = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=enrichment,
        audit=audit,
        policy_comparison=comparison,
        output_dir=tmp_path / "baseline_acceptance",
    )
    assert baseline.row_count == 64
    assert baseline.accepted_count == 0
    assert baseline.checklist_pass_count == 0
    assert baseline.remaining_blocked_count == 16

    updates = tmp_path / "tiny_reviewer_no_hit_acceptance_update.csv"
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
                "accepted_by": "diagnostics_reviewer",
                "accepted_at": "2026-06-05T17:45:00+08:00",
                "acceptance_reason": (
                    "Diagnostics-only smoke accepts recorded source coverage/query window/no-hit "
                    "inference as supporting context only."
                ),
                "limitations": (
                    "No-hit support remains policy-dependent and does not prove PIT approval, "
                    "survivorship resolution, checklist pass, or universe export."
                ),
                "survivorship_rationale": "",
                "evidence_reference": "local-fixture://reviewer-no-hit-source-coverage",
            }
        ]
    ).to_csv(updates, index=False)

    result = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=enrichment,
        audit=audit,
        policy_comparison=comparison,
        reviewer_acceptance=updates,
        output_dir=tmp_path / "diagnostics_acceptance",
    )

    accepted = result.acceptance_frame.loc[
        result.acceptance_frame["acceptance_status"] == "ACCEPTED_AS_SUPPORTING_CONTEXT"
    ]
    assert len(accepted) == 1
    accepted_row = accepted.iloc[0]
    assert accepted_row["signal_date"] == "2024-04-02"
    assert accepted_row["symbol"] == "000001"
    assert accepted_row["universe_name"] == "stock_core"
    assert accepted_row["exception_type"] == "DELISTING"
    assert result.accepted_count == 1
    assert result.accepted_supporting_context_count == 1
    assert result.needs_review_count == 63
    assert result.checklist_pass_count == 0
    assert result.remaining_blocked_count == 16

    safety_columns = [
        "accepted_as_supporting_context",
        "remaining_blocked",
        "no_clean_review_updates_created",
        "no_data_raw_write",
        "no_data_processed_write",
        "no_current_candidates_generated",
        "acceptance_only",
    ]
    assert accepted_row[safety_columns].map(bool).all()
    forbidden_columns = [
        "checklist_pass_candidate",
        "approval_applied",
        "pit_review_run",
        "export_readiness_run",
        "export_staging_run",
        "universe_exported",
    ]
    assert not accepted_row[forbidden_columns].map(bool).any()
    assert "APPROVED_FOR_PIT_UNIVERSE" not in result.acceptance_frame.to_csv(index=False)
    assert not list(result.artifact_paths["artifact_dir"].glob("*review_updates*.csv"))
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()

    baseline_metadata = json.loads(baseline.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert baseline_metadata["accepted_count"] == 0
    assert baseline_metadata["checklist_pass_count"] == 0
    assert baseline_metadata["remaining_blocked_count"] == 16


def test_reviewer_no_hit_multi_exception_smoke_accepts_supporting_context_only(
    tmp_path: Path,
) -> None:
    enrichment = _first_batch_enrichment_fixture(tmp_path)
    audit = _audit_fixture(tmp_path)
    comparison = _comparison_fixture(tmp_path)
    exception_types = [
        "DELISTING",
        "ST_RISK_WARNING",
        "SUSPENSION_RESUMPTION",
        "SURVIVORSHIP_RATIONALE",
    ]

    updates = tmp_path / "reviewer_no_hit_multi_exception_update.csv"
    update_rows = []
    for exception_type in exception_types:
        row = {
            "signal_date": "2024-04-02",
            "symbol": "000001",
            "universe_name": "stock_core",
            "exception_type": exception_type,
            "acceptance_status": "ACCEPTED_AS_SUPPORTING_CONTEXT",
            "source_coverage_accepted": True,
            "query_window_accepted": True,
            "no_hit_inference_accepted": True,
            "accepted_by": "diagnostics_reviewer",
            "accepted_at": "2026-06-05T18:15:00+08:00",
            "acceptance_reason": (
                "Diagnostics-only multi-exception smoke accepts recorded no-hit source coverage "
                "as supporting context only."
            ),
            "limitations": (
                "No-hit support remains policy-dependent and does not prove PIT approval, "
                "checklist pass, universe export, or candidate generation."
            ),
            "survivorship_rationale": "",
            "evidence_reference": "local-fixture://reviewer-no-hit-multi-exception-smoke",
        }
        if exception_type == "SURVIVORSHIP_RATIONALE":
            row["survivorship_rationale"] = (
                "Reviewer accepts documented source coverage and query windows as survivorship-bias "
                "supporting context only; PIT approval remains blocked pending the full evidence checklist."
            )
        update_rows.append(row)
    pd.DataFrame(update_rows).to_csv(updates, index=False)

    result = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=enrichment,
        audit=audit,
        policy_comparison=comparison,
        reviewer_acceptance=updates,
        output_dir=tmp_path / "diagnostics_acceptance",
    )

    accepted = result.acceptance_frame.loc[
        result.acceptance_frame["acceptance_status"] == "ACCEPTED_AS_SUPPORTING_CONTEXT"
    ].copy()
    assert len(accepted) == 4
    assert set(accepted["exception_type"]) == set(exception_types)
    assert set(accepted["signal_date"]) == {"2024-04-02"}
    assert set(accepted["symbol"]) == {"000001"}
    assert set(accepted["universe_name"]) == {"stock_core"}
    assert result.accepted_count == 4
    assert result.accepted_supporting_context_count == 4
    assert result.needs_review_count == 60
    assert result.checklist_pass_count == 0
    assert result.remaining_blocked_count == 16

    truthy_safety_columns = [
        "accepted_as_supporting_context",
        "remaining_blocked",
        "no_clean_review_updates_created",
        "no_data_raw_write",
        "no_data_processed_write",
        "no_current_candidates_generated",
        "acceptance_only",
    ]
    for column in truthy_safety_columns:
        assert accepted[column].map(bool).all()
    false_safety_columns = [
        "checklist_pass_candidate",
        "approval_applied",
        "pit_review_run",
        "export_readiness_run",
        "export_staging_run",
        "universe_exported",
    ]
    for column in false_safety_columns:
        assert not accepted[column].map(bool).any()
    assert "APPROVED_FOR_PIT_UNIVERSE" not in result.acceptance_frame.to_csv(index=False)
    assert not list(result.artifact_paths["artifact_dir"].glob("*review_updates*.csv"))
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_reviewer_no_hit_downstream_impact_reports_zero_context_for_no_accepted_rows(
    tmp_path: Path,
) -> None:
    acceptance = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=_first_batch_enrichment_fixture(tmp_path),
        audit=_audit_fixture(tmp_path),
        policy_comparison=_comparison_fixture(tmp_path),
        output_dir=tmp_path / "acceptance",
    )

    result = build_reviewer_no_hit_acceptance_downstream_impact(
        acceptance=acceptance.artifact_paths["artifact_dir"],
        enrichment=tmp_path / "enrichment" / "enrichment-a",
        validator=_validator_fixture(tmp_path),
        policy_comparison=_policy_comparison_fixture(tmp_path),
        output_dir=tmp_path / "impact",
    )

    assert result.row_count == 64
    assert result.accepted_no_hit_context_count == 0
    assert result.packet_context_gap_reduced_count == 0
    assert result.checklist_pass_count == 0
    assert result.remaining_blocked_count == 16
    assert set(result.impact_frame["symbol"]) == {"000001", "159915"}
    assert not result.impact_frame["approval_applied"].any()
    assert not result.impact_frame["pit_review_run"].any()
    assert not result.impact_frame["export_readiness_run"].any()
    assert not result.impact_frame["export_staging_run"].any()
    assert not result.impact_frame["universe_exported"].any()
    assert result.impact_frame["no_clean_review_updates_created"].all()
    assert result.impact_frame["no_data_raw_write"].all()
    assert result.impact_frame["no_data_processed_write"].all()
    assert result.impact_frame["no_current_candidates_generated"].all()
    assert "APPROVED_FOR_PIT_UNIVERSE" not in result.impact_frame.to_csv(index=False)
    assert not list(result.artifact_paths["artifact_dir"].glob("*review_updates*.csv"))


def test_reviewer_no_hit_downstream_impact_links_multi_exception_context_only(
    tmp_path: Path,
) -> None:
    enrichment = _first_batch_enrichment_fixture(tmp_path)
    updates = _multi_exception_acceptance_updates(tmp_path)
    acceptance = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=enrichment,
        audit=_audit_fixture(tmp_path),
        policy_comparison=_comparison_fixture(tmp_path),
        reviewer_acceptance=updates,
        output_dir=tmp_path / "acceptance",
    )

    result = build_reviewer_no_hit_acceptance_downstream_impact(
        acceptance=acceptance.artifact_paths["artifact_dir"],
        enrichment=enrichment,
        validator=_validator_fixture(tmp_path),
        policy_comparison=_policy_comparison_fixture(tmp_path),
        output_dir=tmp_path / "impact",
    )

    accepted = result.impact_frame.loc[result.impact_frame["accepted_no_hit_context"].map(bool)]
    assert len(accepted) == 4
    assert set(accepted["exception_type"]) == {
        "DELISTING",
        "ST_RISK_WARNING",
        "SUSPENSION_RESUMPTION",
        "SURVIVORSHIP_RATIONALE",
    }
    assert set(accepted["symbol"]) == {"000001"}
    assert result.accepted_no_hit_context_count == 4
    assert result.packet_context_gap_reduced_count == 1
    assert result.checklist_pass_count == 0
    assert result.remaining_blocked_count == 16
    assert accepted["accepted_no_hit_context_only"].map(bool).all()
    assert not accepted["checklist_pass_after"].map(bool).any()
    assert not accepted["approval_applied"].map(bool).any()
    assert not accepted["pit_review_run"].map(bool).any()
    assert not accepted["export_readiness_run"].map(bool).any()
    assert not accepted["export_staging_run"].map(bool).any()
    assert not accepted["universe_exported"].map(bool).any()
    packet_row = result.packet_linkage_frame.loc[
        (result.packet_linkage_frame["signal_date"] == "2024-04-02")
        & (result.packet_linkage_frame["symbol"] == "000001")
    ].iloc[0]
    assert int(packet_row["accepted_no_hit_context_count"]) == 4
    assert packet_row["accepted_no_hit_exception_types"] == (
        "DELISTING;ST_RISK_WARNING;SUSPENSION_RESUMPTION;SURVIVORSHIP_RATIONALE"
    )
    assert "APPROVED_FOR_PIT_UNIVERSE" not in result.impact_frame.to_csv(index=False)
    assert not list(result.artifact_paths["artifact_dir"].glob("*review_updates*.csv"))
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()

    code = cli.main(
        [
            "reviewer-no-hit-acceptance-downstream-impact",
            "--acceptance",
            str(acceptance.artifact_paths["artifact_dir"]),
            "--enrichment",
            str(enrichment),
            "--validator",
            str(tmp_path / "validator" / "validator-a"),
            "--policy-comparison",
            str(tmp_path / "policy" / "comparison-a"),
            "--output-dir",
            str(tmp_path / "impact_cli"),
        ]
    )
    assert code == 0


def test_reviewer_no_hit_downstream_impact_requires_exception_type_for_linkage(
    tmp_path: Path,
) -> None:
    enrichment = _first_batch_enrichment_fixture(tmp_path)
    updates = _multi_exception_acceptance_updates(tmp_path)
    acceptance = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=enrichment,
        audit=_audit_fixture(tmp_path),
        policy_comparison=_comparison_fixture(tmp_path),
        reviewer_acceptance=updates,
        output_dir=tmp_path / "acceptance",
    )
    acceptance_csv = acceptance.artifact_paths["acceptance_csv"]
    frame = pd.read_csv(acceptance_csv, keep_default_na=False, dtype=str)
    accepted_mask = frame["acceptance_status"] == "ACCEPTED_AS_SUPPORTING_CONTEXT"
    frame.loc[accepted_mask, "exception_type"] = ""
    frame.to_csv(acceptance_csv, index=False)

    result = build_reviewer_no_hit_acceptance_downstream_impact(
        acceptance=acceptance.artifact_paths["artifact_dir"],
        enrichment=enrichment,
        validator=_validator_fixture(tmp_path),
        policy_comparison=_policy_comparison_fixture(tmp_path),
        output_dir=tmp_path / "impact",
    )

    assert result.accepted_no_hit_context_count == 0
    assert result.packet_context_gap_reduced_count == 0
    assert result.checklist_pass_count == 0
    assert result.remaining_blocked_count == 16
    assert "000001" in set(result.impact_frame["symbol"])


def test_reviewer_no_hit_downstream_impact_index_health_status_and_cli(tmp_path: Path) -> None:
    acceptance = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=_first_batch_enrichment_fixture(tmp_path),
        audit=_audit_fixture(tmp_path),
        policy_comparison=_comparison_fixture(tmp_path),
        output_dir=tmp_path / "acceptance",
    )
    impact = build_reviewer_no_hit_acceptance_downstream_impact(
        acceptance=acceptance.artifact_paths["artifact_dir"],
        enrichment=tmp_path / "enrichment" / "enrichment-a",
        validator=_validator_fixture(tmp_path),
        policy_comparison=_policy_comparison_fixture(tmp_path),
        output_dir=tmp_path / "impact",
    )

    index = build_reviewer_no_hit_acceptance_downstream_impact_index(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact" / "index",
    )
    health = check_reviewer_no_hit_acceptance_downstream_impact_health(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact" / "health",
    )
    status = run_reviewer_no_hit_acceptance_downstream_impact_status(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact" / "status",
    )

    assert index["artifact_count"] == 1
    assert index["index_frame"].iloc[0]["impact_id"] == impact.impact_id
    assert health["status"] == "PASS"
    assert status["status"] == "WARN"
    assert status["workflow_stage"] == "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_NO_ACCEPTED_CONTEXT"
    assert status["latest_impact_id"] == impact.impact_id
    assert status["accepted_no_hit_context_count"] == 0
    assert status["checklist_pass_count"] == 0
    assert status["remaining_blocked_count"] == 16

    for command in [
        "reviewer-no-hit-acceptance-downstream-impact-index",
        "reviewer-no-hit-acceptance-downstream-impact-health",
        "reviewer-no-hit-acceptance-downstream-impact-status",
    ]:
        assert (
            cli.main(
                [
                    command,
                    "--root",
                    str(tmp_path / "impact"),
                    "--output-dir",
                    str(tmp_path / "impact" / f"{command}_cli"),
                ]
            )
            == 0
        )


def test_reviewer_no_hit_downstream_impact_status_supporting_context_only(
    tmp_path: Path,
) -> None:
    enrichment = _first_batch_enrichment_fixture(tmp_path)
    acceptance = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=enrichment,
        audit=_audit_fixture(tmp_path),
        policy_comparison=_comparison_fixture(tmp_path),
        reviewer_acceptance=_multi_exception_acceptance_updates(tmp_path),
        output_dir=tmp_path / "acceptance",
    )
    impact = build_reviewer_no_hit_acceptance_downstream_impact(
        acceptance=acceptance.artifact_paths["artifact_dir"],
        enrichment=enrichment,
        validator=_validator_fixture(tmp_path),
        policy_comparison=_policy_comparison_fixture(tmp_path),
        output_dir=tmp_path / "impact",
    )

    status = run_reviewer_no_hit_acceptance_downstream_impact_status(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact" / "status",
    )

    assert impact.accepted_no_hit_context_count == 4
    assert status["workflow_stage"] == "REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_SUPPORTING_CONTEXT_ONLY"
    assert status["accepted_no_hit_context_count"] == 4
    assert status["packet_context_gap_reduced_count"] == 1
    assert status["checklist_pass_count"] == 0
    assert status["remaining_blocked_count"] == 16
    assert not status["approval_applied"]


def test_reviewer_no_hit_downstream_impact_health_fails_on_approval_or_review_updates(
    tmp_path: Path,
) -> None:
    acceptance = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=_first_batch_enrichment_fixture(tmp_path),
        audit=_audit_fixture(tmp_path),
        policy_comparison=_comparison_fixture(tmp_path),
        output_dir=tmp_path / "acceptance",
    )
    impact = build_reviewer_no_hit_acceptance_downstream_impact(
        acceptance=acceptance.artifact_paths["artifact_dir"],
        enrichment=tmp_path / "enrichment" / "enrichment-a",
        validator=_validator_fixture(tmp_path),
        policy_comparison=_policy_comparison_fixture(tmp_path),
        output_dir=tmp_path / "impact",
    )
    metadata_path = impact.artifact_paths["metadata"]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["approval_applied"] = True
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    health = check_reviewer_no_hit_acceptance_downstream_impact_health(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact" / "health_approval",
    )
    assert health["status"] == "FAIL"
    assert "APPROVAL_APPLIED_DETECTED" in set(health["health_frame"]["issue_code"])

    metadata["approval_applied"] = False
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    (impact.artifact_paths["artifact_dir"] / "clean_review_updates.csv").write_text(
        "signal_date,symbol\n2024-04-02,000001\n",
        encoding="utf-8",
    )

    health = check_reviewer_no_hit_acceptance_downstream_impact_health(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact" / "health_review_updates",
    )
    assert health["status"] == "FAIL"
    assert "CLEAN_REVIEW_UPDATES_CREATED" in set(health["health_frame"]["issue_code"])


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


def _first_batch_enrichment_fixture(tmp_path: Path) -> Path:
    folder = tmp_path / "enrichment" / "enrichment-a"
    folder.mkdir(parents=True, exist_ok=True)
    signal_dates = [
        "2024-04-02",
        "2024-04-09",
        "2024-04-11",
        "2024-04-16",
        "2024-04-19",
        "2024-04-24",
        "2024-04-26",
        "2024-05-06",
    ]
    rows = []
    for signal_date in signal_dates:
        rows.extend(
            [
                {
                    "signal_date": signal_date,
                    "symbol": "000001",
                    "universe_name": "stock_core",
                    "reviewed_no_hit_context_supported": True,
                    "missing_evidence_categories": "not_delisted;ST_no_ST;survivorship_bias",
                },
                {
                    "signal_date": signal_date,
                    "symbol": "159915",
                    "universe_name": "etf_core",
                    "reviewed_no_hit_context_supported": True,
                    "missing_evidence_categories": "not_delisted;survivorship_bias",
                },
            ]
        )
    pd.DataFrame(rows).to_csv(folder / "pit_official_status_evidence_packet_enrichment.csv", index=False)
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


def _multi_exception_acceptance_updates(tmp_path: Path) -> Path:
    exception_types = [
        "DELISTING",
        "ST_RISK_WARNING",
        "SUSPENSION_RESUMPTION",
        "SURVIVORSHIP_RATIONALE",
    ]
    rows = []
    for exception_type in exception_types:
        row = {
            "signal_date": "2024-04-02",
            "symbol": "000001",
            "universe_name": "stock_core",
            "exception_type": exception_type,
            "acceptance_status": "ACCEPTED_AS_SUPPORTING_CONTEXT",
            "source_coverage_accepted": True,
            "query_window_accepted": True,
            "no_hit_inference_accepted": True,
            "accepted_by": "diagnostics_reviewer",
            "accepted_at": "2026-06-05T18:15:00+08:00",
            "acceptance_reason": (
                "Diagnostics-only multi-exception smoke accepts recorded no-hit source coverage "
                "as supporting context only."
            ),
            "limitations": (
                "No-hit support remains policy-dependent and does not prove PIT approval, "
                "checklist pass, universe export, or candidate generation."
            ),
            "survivorship_rationale": "",
            "evidence_reference": "local-fixture://reviewer-no-hit-multi-exception-smoke",
        }
        if exception_type == "SURVIVORSHIP_RATIONALE":
            row["survivorship_rationale"] = (
                "Reviewer accepts documented source coverage and query windows as survivorship-bias "
                "supporting context only; PIT approval remains blocked pending the full evidence checklist."
            )
        rows.append(row)
    path = tmp_path / "reviewer_no_hit_multi_exception_update.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _validator_fixture(tmp_path: Path) -> Path:
    folder = tmp_path / "validator" / "validator-a"
    folder.mkdir(parents=True, exist_ok=True)
    signal_dates = [
        "2024-04-02",
        "2024-04-09",
        "2024-04-11",
        "2024-04-16",
        "2024-04-19",
        "2024-04-24",
        "2024-04-26",
        "2024-05-06",
    ]
    rows = []
    for signal_date in signal_dates:
        rows.extend(
            [
                {
                    "validator_id": "validator-a",
                    "signal_date": signal_date,
                    "symbol": "000001",
                    "universe_name": "stock_core",
                    "profile": "stock_core",
                    "checklist_status": "CHECKLIST_BLOCKED",
                    "checklist_pass": False,
                    "blocked": True,
                    "blocker_reason": "missing as_of_date; survivorship unresolved; stock ST/no-ST evidence missing",
                },
                {
                    "validator_id": "validator-a",
                    "signal_date": signal_date,
                    "symbol": "159915",
                    "universe_name": "etf_core",
                    "profile": "etf_core",
                    "checklist_status": "CHECKLIST_BLOCKED",
                    "checklist_pass": False,
                    "blocked": True,
                    "blocker_reason": "missing as_of_date; survivorship unresolved",
                },
            ]
        )
    pd.DataFrame(rows).to_csv(folder / "pit_evidence_checklist_validation.csv", index=False)
    (folder / "metadata.json").write_text(
        json.dumps(
            {
                "validator_id": "validator-a",
                "row_count": 16,
                "checklist_pass_count": 0,
                "blocked_count": 16,
            }
        ),
        encoding="utf-8",
    )
    return folder


def _policy_comparison_fixture(tmp_path: Path) -> Path:
    folder = tmp_path / "policy" / "comparison-a"
    folder.mkdir(parents=True, exist_ok=True)
    signal_dates = [
        "2024-04-02",
        "2024-04-09",
        "2024-04-11",
        "2024-04-16",
        "2024-04-19",
        "2024-04-24",
        "2024-04-26",
        "2024-05-06",
    ]
    rows = []
    for signal_date in signal_dates:
        rows.extend(
            [
                {
                    "comparison_id": "comparison-a",
                    "signal_date": signal_date,
                    "symbol": "000001",
                    "recommended_future_universe": "stock_core",
                    "checklist_pass_under_reviewed_no_hit_support": False,
                    "remaining_blockers": "missing as_of_date; survivorship unresolved; stock ST/no-ST evidence missing",
                },
                {
                    "comparison_id": "comparison-a",
                    "signal_date": signal_date,
                    "symbol": "159915",
                    "recommended_future_universe": "etf_core",
                    "checklist_pass_under_reviewed_no_hit_support": False,
                    "remaining_blockers": "missing as_of_date; survivorship unresolved",
                },
            ]
        )
    pd.DataFrame(rows).to_csv(folder / "pit_evidence_policy_profile_comparison.csv", index=False)
    (folder / "metadata.json").write_text(
        json.dumps(
            {
                "comparison_id": "comparison-a",
                "reviewed_no_hit_support_pass_count": 0,
                "remaining_blocked_count": 16,
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
