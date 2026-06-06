import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.first_batch_partial_completion_impact import (
    build_first_batch_partial_completion_impact,
)
from quant_replay_system.first_batch_partial_completion_impact_health import (
    check_first_batch_partial_completion_impact_health,
)
from quant_replay_system.first_batch_partial_completion_impact_index import (
    build_first_batch_partial_completion_impact_index,
)
from quant_replay_system.first_batch_partial_completion_impact_status import (
    run_first_batch_partial_completion_impact_status,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan import (
    build_first_batch_reviewer_evidence_completion_plan,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_health import (
    check_first_batch_reviewer_evidence_completion_plan_health,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_index import (
    build_first_batch_reviewer_evidence_completion_plan_index,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_status import (
    run_first_batch_reviewer_evidence_completion_plan_status,
)
from quant_replay_system.local_research_dashboard import run_local_research_dashboard
from quant_replay_system.material_pit_evidence_gate_closure_plan import (
    build_material_pit_evidence_gate_closure_plan,
)
from quant_replay_system.material_pit_evidence_gate_closure_plan_health import (
    check_material_pit_evidence_gate_closure_plan_health,
)
from quant_replay_system.material_pit_evidence_gate_closure_plan_index import (
    build_material_pit_evidence_gate_closure_plan_index,
)
from quant_replay_system.material_pit_evidence_gate_closure_plan_status import (
    run_material_pit_evidence_gate_closure_plan_status,
)


DATES = [
    "2024-04-02",
    "2024-04-09",
    "2024-04-11",
    "2024-04-16",
    "2024-04-19",
    "2024-04-24",
    "2024-04-26",
    "2024-05-06",
]
EXCEPTION_TYPES = [
    "DELISTING",
    "ST_RISK_WARNING",
    "SUSPENSION_RESUMPTION",
    "SURVIVORSHIP_RATIONALE",
]


def test_builds_report_only_first_batch_completion_plan(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)

    result = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "out",
    )

    assert result.row_count == 16
    assert result.stock_core_row_count == 8
    assert result.etf_core_row_count == 8
    assert result.reviewer_completion_required_count == 16
    assert result.no_hit_acceptance_required_count == 16
    assert result.survivorship_rationale_required_count == 16
    assert result.metadata_completion_required_count == 16
    assert result.checklist_pass_count == 0
    assert result.remaining_blocked_count == 16
    assert result.clean_review_updates_created is False
    assert result.approval_applied is False

    plan = pd.read_csv(result.artifact_paths["plan_csv"], dtype=str, keep_default_na=False)
    assert len(plan) == 16
    assert set(plan["symbol"]) == {"000001", "159915"}
    assert set(plan["review_status"]) == {"NEEDS_MORE_EVIDENCE"}
    assert set(plan["include_flag"]) == {"False"}
    assert set(plan["valid_for_signal_date"]) == {"False"}
    assert set(plan["survivorship_bias_resolved"]) == {"False"}
    assert set(plan["approved_for_pit_universe_candidate"]) == {"False"}
    assert set(plan["reviewer_completion_required"]) == {"True"}
    assert set(plan["strong_official_date_specific_quotation"]) == {"True"}
    assert set(plan["quotation_proves_not_delisted"]) == {"False"}
    assert set(plan["quotation_proves_st_no_st"]) == {"False"}
    assert set(plan["quotation_resolves_survivorship"]) == {"False"}

    template = pd.read_csv(result.artifact_paths["reviewer_completion_template"], dtype=str, keep_default_na=False)
    assert "APPROVED_FOR_PIT_UNIVERSE" not in set(template["review_status"])
    assert set(template["include_flag"]) == {"False"}
    assert set(template["valid_for_signal_date"]) == {"False"}
    assert set(template["symbol"]) == {"000001", "159915"}

    assert not (result.artifact_paths["artifact_dir"] / "review_updates.csv").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_tiny_manual_reviewer_completion_fixture_remains_non_approved(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    result = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "out",
    )
    template = pd.read_csv(result.artifact_paths["reviewer_completion_template"], dtype=str, keep_default_na=False)
    target = template.loc[
        (template["signal_date"] == "2024-04-02")
        & (template["symbol"] == "000001")
        & (template["universe_name"] == "stock_core")
    ]
    assert len(target) == 1

    fixture = target.copy()
    fixture.loc[:, "review_status"] = "NEEDS_MORE_EVIDENCE"
    fixture.loc[:, "include_flag"] = "False"
    fixture.loc[:, "valid_for_signal_date"] = "False"
    fixture.loc[:, "survivorship_bias_resolved"] = "False"
    fixture.loc[:, "reviewer"] = "diagnostics_reviewer"
    fixture.loc[:, "reviewed_at"] = "2026-06-06T00:00:00+08:00"
    fixture.loc[:, "review_reason"] = "Diagnostics-only manual completion smoke; not PIT approval."
    fixture.loc[:, "evidence_source"] = "DIAGNOSTICS_ONLY_FIXTURE"
    fixture.loc[:, "evidence_reference"] = "Shape validation only; no authoritative PIT evidence asserted."
    fixture_dir = tmp_path / "manual_diagnostics" / "tiny_manual_reviewer_completion_smoke"
    fixture_dir.mkdir(parents=True)
    fixture_path = fixture_dir / "tiny_manual_reviewer_completion_fixture.csv"
    fixture.to_csv(fixture_path, index=False)

    validated = pd.read_csv(fixture_path, dtype=str, keep_default_na=False)
    assert len(validated) == 1
    assert validated.iloc[0]["symbol"] == "000001"
    assert validated.iloc[0]["review_status"] == "NEEDS_MORE_EVIDENCE"
    assert validated.iloc[0]["include_flag"] == "False"
    assert validated.iloc[0]["valid_for_signal_date"] == "False"
    assert validated.iloc[0]["survivorship_bias_resolved"] == "False"
    assert "APPROVED_FOR_PIT_UNIVERSE" not in fixture_path.read_text(encoding="utf-8")
    assert result.checklist_pass_count == 0
    assert result.remaining_blocked_count == 16
    assert result.clean_review_updates_created is False
    assert result.approval_applied is False
    assert not (fixture_dir / "review_updates.csv").exists()
    assert not (fixture_dir / "clean_review_updates.csv").exists()
    assert not (result.artifact_paths["artifact_dir"] / "review_updates.csv").exists()
    assert not (tmp_path / "point_in_time_universe_overlay_review").exists()
    assert not (tmp_path / "point_in_time_universe_overlay_export_readiness").exists()
    assert not (tmp_path / "point_in_time_universe_export_staging").exists()
    assert not (tmp_path / "current_candidates").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_outputs_missing_evidence_and_todo_matrices(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    result = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "out",
    )

    missing = pd.read_csv(result.artifact_paths["row_level_missing_evidence_matrix"], dtype=str, keep_default_na=False)
    no_hit = pd.read_csv(result.artifact_paths["reviewer_no_hit_acceptance_todo"], dtype=str, keep_default_na=False)
    survivorship = pd.read_csv(result.artifact_paths["survivorship_rationale_todo"], dtype=str, keep_default_na=False)
    metadata = pd.read_csv(result.artifact_paths["metadata_completion_todo"], dtype=str, keep_default_na=False)

    assert len(missing) == 16
    assert "as_of_date" in missing.loc[0, "missing_evidence_fields"]
    assert len(no_hit) == 64
    assert set(no_hit["exception_type"]) == set(EXCEPTION_TYPES)
    assert set(no_hit["acceptance_status"]) == {"NEEDS_REVIEW"}
    assert len(survivorship) == 16
    assert len(metadata) == 16

    reusable = pd.read_csv(result.artifact_paths["reusable_symbol_level_evidence_plan"], dtype=str, keep_default_na=False)
    date_specific = pd.read_csv(result.artifact_paths["date_specific_evidence_plan"], dtype=str, keep_default_na=False)
    assert set(reusable["symbol"]) == {"000001", "159915"}
    assert set(date_specific["symbol"]) == {"000001", "159915"}
    assert set(date_specific["signal_date"]) == set(DATES)


def test_index_health_status_and_cli_for_completion_plan(tmp_path: Path, capsys) -> None:
    inputs = _write_inputs(tmp_path)
    assert (
        cli.main(
            [
                "first-batch-reviewer-evidence-completion-plan",
                "--evidence-update-plan",
                str(inputs["evidence_update_plan"]),
                "--downstream-impact",
                str(inputs["downstream_impact"]),
                "--enrichment",
                str(inputs["enrichment"]),
                "--validator",
                str(inputs["validator"]),
                "--policy-comparison",
                str(inputs["policy_comparison"]),
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
        == 0
    )
    assert "row_count: 16" in capsys.readouterr().out

    index = build_first_batch_reviewer_evidence_completion_plan_index(
        root=tmp_path / "out",
        output_dir=tmp_path / "index",
    )
    assert index.artifact_count == 1
    assert index.index_frame.iloc[0]["reviewer_completion_required_count"] == 16

    health = check_first_batch_reviewer_evidence_completion_plan_health(
        root=tmp_path / "out",
        output_dir=tmp_path / "health",
    )
    assert health.status == "PASS"
    assert health.issue_count == 0

    status = run_first_batch_reviewer_evidence_completion_plan_status(
        root=tmp_path / "out",
        output_dir=tmp_path / "status",
    )
    assert status.status == "WARN"
    assert status.workflow_stage == "FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW"
    assert status.row_count == 16
    assert status.clean_review_updates_created is False
    assert status.approval_applied is False

    for command in [
        "first-batch-reviewer-evidence-completion-plan-index",
        "first-batch-reviewer-evidence-completion-plan-health",
        "first-batch-reviewer-evidence-completion-plan-status",
    ]:
        assert cli.main([command, "--root", str(tmp_path / "out"), "--output-dir", str(tmp_path / command)]) == 0
    output = capsys.readouterr().out
    assert "FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW" in output


def test_health_fails_if_completion_plan_claims_approval_or_clean_updates(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    result = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "out",
    )
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["approval_applied"] = True
    metadata["clean_review_updates_created"] = True
    result.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    health = check_first_batch_reviewer_evidence_completion_plan_health(
        root=tmp_path / "out",
        output_dir=tmp_path / "health",
    )

    assert health.status == "FAIL"
    assert "APPROVAL_APPLIED_DETECTED" in set(health.health_frame["issue_code"])
    assert "CLEAN_REVIEW_UPDATES_DETECTED" in set(health.health_frame["issue_code"])


def test_research_status_includes_completion_plan_and_preserves_paper_priority(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    inputs = _write_inputs(tmp_path / "inputs")
    plan = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=reports / "first_batch_reviewer_evidence_completion_plan",
    )
    _write_paper_workflow_status(reports)

    result = run_local_research_dashboard(root=reports, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_first_batch_reviewer_evidence_completion_plan_id == plan.plan_id
    assert result.first_batch_reviewer_evidence_completion_plan_stage == (
        "FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW"
    )
    assert result.first_batch_reviewer_evidence_completion_plan_reviewer_completion_required_count == 16
    assert result.first_batch_reviewer_evidence_completion_plan_clean_review_updates_created is False
    assert result.first_batch_reviewer_evidence_completion_plan_approval_applied is False

    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str, keep_default_na=False)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert summary.iloc[0]["latest_first_batch_reviewer_evidence_completion_plan_id"] == plan.plan_id
    assert metadata["first_batch_reviewer_evidence_completion_plan_reviewer_completion_required_count"] == 16


def test_partial_completion_impact_without_fixture_keeps_all_rows_blocked(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    plan = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "completion_plan",
    )

    impact = build_first_batch_partial_completion_impact(
        completion_plan=plan.artifact_paths["artifact_dir"],
        output_dir=tmp_path / "impact",
    )

    assert impact.row_count == 16
    assert impact.completed_field_count == 0
    assert impact.blocker_reduced_count == 0
    assert impact.checklist_pass_count == 0
    assert impact.remaining_blocked_count == 16
    assert impact.clean_review_updates_created is False
    assert impact.approval_applied is False

    frame = pd.read_csv(impact.artifact_paths["impact_csv"], dtype=str, keep_default_na=False)
    assert set(frame["symbol"]) == {"000001", "159915"}
    assert set(frame["checklist_pass_after_partial_completion"]) == {"False"}
    assert set(frame["approval_candidate_after_partial_completion"]) == {"False"}
    assert set(frame["include_flag_after_partial_completion"]) == {"False"}
    assert set(frame["valid_for_signal_date_after_partial_completion"]) == {"False"}
    assert "APPROVED_FOR_PIT_UNIVERSE" not in impact.artifact_paths["impact_csv"].read_text(encoding="utf-8")
    assert not (impact.artifact_paths["artifact_dir"] / "review_updates.csv").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_partial_completion_impact_fixture_reduces_only_reviewer_metadata(tmp_path: Path, capsys) -> None:
    inputs = _write_inputs(tmp_path)
    plan = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "completion_plan",
    )
    fixture = _write_tiny_manual_completion_fixture(plan.artifact_paths["reviewer_completion_template"], tmp_path)

    impact = build_first_batch_partial_completion_impact(
        completion_plan=plan.artifact_paths["artifact_dir"],
        partial_completion=fixture,
        output_dir=tmp_path / "impact",
    )

    assert impact.row_count == 16
    assert impact.completed_row_count == 1
    assert impact.completed_field_count == 5
    assert impact.blocker_reduced_count == 1
    assert impact.material_blocker_reduced_count == 0
    assert impact.checklist_pass_count == 0
    assert impact.remaining_blocked_count == 16
    assert impact.clean_review_updates_created is False
    assert impact.approval_applied is False

    frame = pd.read_csv(impact.artifact_paths["impact_csv"], dtype=str, keep_default_na=False)
    target = frame.loc[
        (frame["signal_date"] == "2024-04-02")
        & (frame["symbol"] == "000001")
        & (frame["universe_name"] == "stock_core")
    ]
    assert len(target) == 1
    row = target.iloc[0]
    assert row["symbol"] == "000001"
    assert row["partial_completion_found"] == "True"
    assert row["completed_reviewer_metadata"] == "reviewer;reviewed_at;review_reason;evidence_source;evidence_reference"
    assert row["blocker_reduction_class"] == "REVIEWER_METADATA_ONLY"
    assert row["material_checklist_blocker_reduced"] == "False"
    assert row["review_status_after_partial_completion"] == "NEEDS_MORE_EVIDENCE"
    assert row["include_flag_after_partial_completion"] == "False"
    assert row["valid_for_signal_date_after_partial_completion"] == "False"
    assert row["survivorship_bias_resolved_after_partial_completion"] == "False"
    assert "as_of_date" in row["remaining_missing_evidence_fields"]
    assert "survivorship_bias_resolution" in row["remaining_missing_evidence_categories"]
    assert "APPROVED_FOR_PIT_UNIVERSE" not in impact.artifact_paths["impact_csv"].read_text(encoding="utf-8")
    assert not (impact.artifact_paths["artifact_dir"] / "review_updates.csv").exists()
    assert not (tmp_path / "point_in_time_universe_overlay_review").exists()
    assert not (tmp_path / "point_in_time_universe_overlay_export_readiness").exists()
    assert not (tmp_path / "point_in_time_universe_export_staging").exists()
    assert not (tmp_path / "current_candidates").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()

    assert (
        cli.main(
            [
                "first-batch-partial-completion-impact",
                "--completion-plan",
                str(plan.artifact_paths["artifact_dir"]),
                "--partial-completion",
                str(fixture),
                "--output-dir",
                str(tmp_path / "impact_cli"),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "row_count: 16" in output
    assert "completed_row_count: 1" in output
    assert "checklist_pass_count: 0" in output
    assert "approval_applied: False" in output


def test_partial_completion_impact_index_health_status_and_cli(tmp_path: Path, capsys) -> None:
    inputs = _write_inputs(tmp_path)
    plan = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "completion_plan",
    )
    impact = build_first_batch_partial_completion_impact(
        completion_plan=plan.artifact_paths["artifact_dir"],
        output_dir=tmp_path / "impact",
    )

    index = build_first_batch_partial_completion_impact_index(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact_index",
    )
    assert index.artifact_count == 1
    assert index.index_frame.iloc[0]["impact_id"] == impact.impact_id
    assert index.index_frame.iloc[0]["completed_row_count"] == 0

    health = check_first_batch_partial_completion_impact_health(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact_health",
    )
    assert health.status == "PASS"
    assert health.issue_count == 0

    status = run_first_batch_partial_completion_impact_status(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact_status",
    )
    assert status.status == "WARN"
    assert status.workflow_stage == "FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_NO_COMPLETION"
    assert status.latest_impact_id == impact.impact_id
    assert status.completed_row_count == 0
    assert status.approval_applied is False
    assert status.clean_review_updates_created is False

    for command in [
        "first-batch-partial-completion-impact-index",
        "first-batch-partial-completion-impact-health",
        "first-batch-partial-completion-impact-status",
    ]:
        assert cli.main([command, "--root", str(tmp_path / "impact"), "--output-dir", str(tmp_path / command)]) == 0
    output = capsys.readouterr().out
    assert "FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_NO_COMPLETION" in output


def test_partial_completion_impact_health_fails_for_unsafe_artifacts(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    plan = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "completion_plan",
    )
    impact = build_first_batch_partial_completion_impact(
        completion_plan=plan.artifact_paths["artifact_dir"],
        output_dir=tmp_path / "impact",
    )

    metadata = json.loads(impact.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["approval_applied"] = True
    impact.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    frame = pd.read_csv(impact.artifact_paths["impact_csv"], dtype=str, keep_default_na=False)
    frame.loc[0, "review_status_after_partial_completion"] = "APPROVED_FOR_PIT_UNIVERSE"
    frame.to_csv(impact.artifact_paths["impact_csv"], index=False)
    (impact.artifact_paths["artifact_dir"] / "review_updates.csv").write_text("symbol\n000001\n", encoding="utf-8")

    health = check_first_batch_partial_completion_impact_health(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact_health",
    )

    assert health.status == "FAIL"
    issues = set(health.health_frame["issue_code"])
    assert "APPROVAL_APPLIED_DETECTED" in issues
    assert "APPROVED_FOR_PIT_UNIVERSE_DETECTED" in issues
    assert "CLEAN_REVIEW_UPDATES_FILE_DETECTED" in issues


def test_partial_completion_impact_status_for_metadata_only_fixture(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    plan = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "completion_plan",
    )
    fixture = _write_tiny_manual_completion_fixture(plan.artifact_paths["reviewer_completion_template"], tmp_path)
    impact = build_first_batch_partial_completion_impact(
        completion_plan=plan.artifact_paths["artifact_dir"],
        partial_completion=fixture,
        output_dir=tmp_path / "impact",
    )

    status = run_first_batch_partial_completion_impact_status(
        root=tmp_path / "impact",
        output_dir=tmp_path / "impact_status",
    )

    assert status.latest_impact_id == impact.impact_id
    assert status.workflow_stage == "FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_METADATA_ONLY_REDUCTION"
    assert status.completed_row_count == 1
    assert status.completed_field_count == 5
    assert status.blocker_reduced_count == 1
    assert status.material_blocker_reduced_count == 0
    assert status.checklist_pass_count == 0
    assert status.remaining_blocked_count == 16
    assert status.approval_applied is False


def test_research_status_includes_partial_completion_impact_and_preserves_paper_priority(
    tmp_path: Path,
    capsys,
) -> None:
    reports = tmp_path / "reports"
    inputs = _write_inputs(tmp_path / "inputs")
    plan = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=reports / "first_batch_reviewer_evidence_completion_plan",
    )
    impact = build_first_batch_partial_completion_impact(
        completion_plan=plan.artifact_paths["artifact_dir"],
        output_dir=reports / "first_batch_partial_completion_impact",
    )
    _write_paper_workflow_status(reports)

    result = run_local_research_dashboard(root=reports, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_first_batch_partial_completion_impact_id == impact.impact_id
    assert result.first_batch_partial_completion_impact_stage == "FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_NO_COMPLETION"
    assert result.first_batch_partial_completion_impact_completed_row_count == 0
    assert result.first_batch_partial_completion_impact_checklist_pass_count == 0
    assert result.first_batch_partial_completion_impact_remaining_blocked_count == 16
    assert result.first_batch_partial_completion_impact_clean_review_updates_created is False
    assert result.first_batch_partial_completion_impact_approval_applied is False

    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str, keep_default_na=False)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert summary.iloc[0]["latest_first_batch_partial_completion_impact_id"] == impact.impact_id
    assert metadata["latest_first_batch_partial_completion_impact_id"] == impact.impact_id
    assert metadata["first_batch_partial_completion_impact_remaining_blocked_count"] == 16

    assert (
        cli.main(
            [
                "research-status",
                "--root",
                str(reports),
                "--output-dir",
                str(tmp_path / "dashboard_cli"),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert f"latest_first_batch_partial_completion_impact_id: {impact.impact_id}" in output
    assert "first_batch_partial_completion_impact_stage: FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_NO_COMPLETION" in output
    assert "first_batch_partial_completion_impact_approval_applied: False" in output


def test_material_pit_evidence_gate_closure_plan_builds_report_only_templates(
    tmp_path: Path,
    capsys,
) -> None:
    inputs = _write_inputs(tmp_path)
    completion_plan = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "completion_plan",
    )
    partial_impact = build_first_batch_partial_completion_impact(
        completion_plan=completion_plan.artifact_paths["artifact_dir"],
        output_dir=tmp_path / "partial_impact",
    )

    result = build_material_pit_evidence_gate_closure_plan(
        audit=None,
        partial_impact=partial_impact.artifact_paths["artifact_dir"],
        completion_plan=completion_plan.artifact_paths["artifact_dir"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "material_plan",
    )

    assert result.row_count == 16
    assert result.checklist_pass_candidate_count == 0
    assert result.remaining_blocked_count == 16
    assert result.reusable_symbol_level_closure_count == 2
    assert result.date_specific_closure_required_count == 16
    assert result.reviewer_no_hit_acceptance_required_count == 16
    assert result.survivorship_rationale_required_count == 16
    assert result.metadata_closure_required_count == 16
    assert result.stock_st_no_st_required_count == 8
    assert result.clean_review_updates_created is False
    assert result.approval_applied is False

    plan = pd.read_csv(result.artifact_paths["plan_csv"], dtype=str, keep_default_na=False)
    assert len(plan) == 16
    assert set(plan["symbol"]) == {"000001", "159915"}
    assert set(plan["universe_name"]) == {"stock_core", "etf_core"}
    assert not plan.duplicated(["signal_date", "symbol", "universe_name"]).any()
    assert set(plan.loc[plan["symbol"] == "000001", "stock_st_no_st_required"]) == {"True"}
    assert set(plan.loc[plan["symbol"] == "159915", "stock_st_no_st_required"]) == {"False"}
    assert set(plan["checklist_pass_candidate"]) == {"False"}
    assert set(plan["include_flag"]) == {"False"}
    assert set(plan["valid_for_signal_date"]) == {"False"}
    assert set(plan["approval_applied"]) == {"False"}
    assert set(plan["clean_review_updates_created"]) == {"False"}
    assert set(plan["no_data_raw_write"]) == {"True"}
    assert set(plan["no_data_processed_write"]) == {"True"}
    assert set(plan["no_current_candidates_generated"]) == {"True"}
    assert set(plan["no_snapshot_built"]) == {"True"}
    assert set(plan["no_forward_labels"]) == {"True"}
    assert "REUSABLE_SYMBOL_LEVEL" in ";".join(plan["closure_paths_required"])
    assert "DATE_SPECIFIC" in ";".join(plan["closure_paths_required"])
    assert "REVIEWER_NO_HIT_ACCEPTANCE" in ";".join(plan["closure_paths_required"])
    assert "SURVIVORSHIP_RATIONALE" in ";".join(plan["closure_paths_required"])
    assert "PIT_METADATA" in ";".join(plan["closure_paths_required"])
    assert "STOCK_ONLY_ST_NO_ST" in ";".join(plan.loc[plan["symbol"] == "000001", "closure_paths_required"])
    assert "APPROVED_FOR_PIT_UNIVERSE" not in result.artifact_paths["plan_csv"].read_text(encoding="utf-8")

    reusable = pd.read_csv(
        result.artifact_paths["reusable_symbol_level_closure_plan"],
        dtype=str,
        keep_default_na=False,
    )
    date_specific = pd.read_csv(result.artifact_paths["date_specific_closure_plan"], dtype=str, keep_default_na=False)
    no_hit = pd.read_csv(
        result.artifact_paths["reviewer_no_hit_acceptance_closure_plan"],
        dtype=str,
        keep_default_na=False,
    )
    survivorship = pd.read_csv(
        result.artifact_paths["survivorship_rationale_closure_plan"],
        dtype=str,
        keep_default_na=False,
    )
    metadata = pd.read_csv(result.artifact_paths["metadata_closure_plan"], dtype=str, keep_default_na=False)
    fill_template = pd.read_csv(
        result.artifact_paths["reviewer_fill_template_by_closure_path"],
        dtype=str,
        keep_default_na=False,
    )
    lineage = pd.read_csv(result.artifact_paths["source_lineage_summary"], dtype=str, keep_default_na=False)
    requirements = pd.read_csv(
        result.artifact_paths["checklist_pass_candidate_requirements"],
        dtype=str,
        keep_default_na=False,
    )
    blocker_matrix = pd.read_csv(
        result.artifact_paths["row_level_material_blocker_matrix"],
        dtype=str,
        keep_default_na=False,
    )

    assert len(reusable) == 2
    assert len(date_specific) == 16
    assert len(no_hit) == 64
    assert len(survivorship) == 16
    assert len(metadata) == 16
    assert len(requirements) == 16
    assert len(blocker_matrix) == 16
    assert set(fill_template["review_status"]) == {"NEEDS_MORE_EVIDENCE"}
    assert set(fill_template["include_flag"]) == {"False"}
    assert set(fill_template["valid_for_signal_date"]) == {"False"}
    assert set(fill_template["approval_applied"]) == {"False"}
    assert "first_batch_reviewer_evidence_completion_plan_id" in set(lineage["lineage_field"])
    assert not (result.artifact_paths["artifact_dir"] / "review_updates.csv").exists()
    assert not (result.artifact_paths["artifact_dir"] / "clean_review_updates.csv").exists()
    assert not (tmp_path / "point_in_time_universe_overlay_review").exists()
    assert not (tmp_path / "point_in_time_universe_overlay_export_readiness").exists()
    assert not (tmp_path / "point_in_time_universe_export_staging").exists()
    assert not (tmp_path / "current_candidates").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()

    assert (
        cli.main(
            [
                "material-pit-evidence-gate-closure-plan",
                "--audit",
                "",
                "--partial-impact",
                str(partial_impact.artifact_paths["artifact_dir"]),
                "--completion-plan",
                str(completion_plan.artifact_paths["artifact_dir"]),
                "--validator",
                str(inputs["validator"]),
                "--policy-comparison",
                str(inputs["policy_comparison"]),
                "--enrichment",
                str(inputs["enrichment"]),
                "--reviewer-no-hit-acceptance",
                "",
                "--reviewer-no-hit-downstream-impact",
                str(inputs["downstream_impact"]),
                "--output-dir",
                str(tmp_path / "material_plan_cli"),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "row_count: 16" in output
    assert "checklist_pass_candidate_count: 0" in output
    assert "remaining_blocked_count: 16" in output
    assert "stock_st_no_st_required_count: 8" in output
    assert "approval_applied: False" in output


def test_material_pit_evidence_gate_closure_plan_index_health_status_and_cli(
    tmp_path: Path,
    capsys,
) -> None:
    inputs = _write_inputs(tmp_path)
    result = _build_material_gate_closure_plan(tmp_path, inputs)
    plan_root = tmp_path / "material_pit_evidence_gate_closure_plan"

    index = build_material_pit_evidence_gate_closure_plan_index(
        root=plan_root,
        output_dir=tmp_path / "material_plan_index",
    )
    assert index.artifact_count == 1
    assert index.index_frame.iloc[0]["plan_id"] == result.plan_id
    assert index.index_frame.iloc[0]["row_count"] == 16

    health = check_material_pit_evidence_gate_closure_plan_health(
        root=plan_root,
        output_dir=tmp_path / "material_plan_health",
    )
    assert health.status == "PASS"
    assert health.issue_count == 0

    status = run_material_pit_evidence_gate_closure_plan_status(
        root=plan_root,
        output_dir=tmp_path / "material_plan_status",
    )
    assert status.status == "WARN"
    assert status.workflow_stage == "MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE"
    assert status.latest_plan_id == result.plan_id
    assert status.row_count == 16
    assert status.checklist_pass_candidate_count == 0
    assert status.remaining_blocked_count == 16
    assert status.reusable_symbol_level_closure_count == 2
    assert status.date_specific_closure_required_count == 16
    assert status.reviewer_no_hit_acceptance_required_count == 16
    assert status.survivorship_rationale_required_count == 16
    assert status.metadata_closure_required_count == 16
    assert status.stock_st_no_st_required_count == 8
    assert status.clean_review_updates_created is False
    assert status.approval_applied is False

    assert (
        cli.main(
            [
                "material-pit-evidence-gate-closure-plan-index",
                "--root",
                str(plan_root),
                "--output-dir",
                str(tmp_path / "material_plan_index_cli"),
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "material-pit-evidence-gate-closure-plan-health",
                "--root",
                str(plan_root),
                "--output-dir",
                str(tmp_path / "material_plan_health_cli"),
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "material-pit-evidence-gate-closure-plan-status",
                "--root",
                str(plan_root),
                "--output-dir",
                str(tmp_path / "material_plan_status_cli"),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "artifact_count: 1" in output
    assert "Health status: PASS" in output
    assert "workflow_stage: MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE" in output


def test_material_pit_evidence_gate_closure_plan_health_fails_for_unsafe_artifacts(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    result = _build_material_gate_closure_plan(tmp_path, inputs)
    plan_root = tmp_path / "material_pit_evidence_gate_closure_plan"

    metadata_path = result.artifact_paths["metadata"]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["approval_applied"] = True
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    plan = pd.read_csv(result.artifact_paths["plan_csv"], dtype=str, keep_default_na=False)
    plan.loc[0, "include_flag"] = "True"
    plan.loc[0, "valid_for_signal_date"] = "True"
    plan.loc[0, "closure_paths_required"] = "APPROVED_FOR_PIT_UNIVERSE"
    plan.to_csv(result.artifact_paths["plan_csv"], index=False)
    (result.artifact_paths["artifact_dir"] / "review_updates.csv").write_text("symbol\n000001\n", encoding="utf-8")

    health = check_material_pit_evidence_gate_closure_plan_health(
        root=plan_root,
        output_dir=tmp_path / "material_plan_health",
    )

    assert health.status == "FAIL"
    issues = set(health.health_frame["issue_code"])
    assert "APPROVAL_APPLIED_DETECTED" in issues
    assert "INCLUDE_FLAG_TRUE_DETECTED" in issues
    assert "VALID_FOR_SIGNAL_DATE_TRUE_DETECTED" in issues
    assert "APPROVED_FOR_PIT_UNIVERSE_DETECTED" in issues
    assert "CLEAN_REVIEW_UPDATES_FILE_DETECTED" in issues


def test_research_status_includes_material_gate_closure_plan_and_preserves_paper_priority(
    tmp_path: Path,
    capsys,
) -> None:
    reports = tmp_path / "reports"
    inputs = _write_inputs(tmp_path / "inputs")
    result = _build_material_gate_closure_plan(reports, inputs)
    _write_paper_workflow_status(reports)

    dashboard = run_local_research_dashboard(root=reports, output_dir=tmp_path / "dashboard")

    assert dashboard.workflow_stage == "PAPER_WORKFLOW_READY"
    assert dashboard.latest_material_pit_evidence_gate_closure_plan_id == result.plan_id
    assert (
        dashboard.material_pit_evidence_gate_closure_plan_stage
        == "MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE"
    )
    assert dashboard.material_pit_evidence_gate_closure_plan_row_count == 16
    assert dashboard.material_pit_evidence_gate_closure_plan_checklist_pass_candidate_count == 0
    assert dashboard.material_pit_evidence_gate_closure_plan_remaining_blocked_count == 16
    assert dashboard.material_pit_evidence_gate_closure_plan_reusable_symbol_level_closure_count == 2
    assert dashboard.material_pit_evidence_gate_closure_plan_date_specific_closure_required_count == 16
    assert dashboard.material_pit_evidence_gate_closure_plan_stock_st_no_st_required_count == 8
    assert dashboard.material_pit_evidence_gate_closure_plan_clean_review_updates_created is False
    assert dashboard.material_pit_evidence_gate_closure_plan_approval_applied is False

    summary = pd.read_csv(dashboard.artifact_paths["local_research_summary"], dtype=str, keep_default_na=False)
    metadata = json.loads(dashboard.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert summary.iloc[0]["latest_material_pit_evidence_gate_closure_plan_id"] == result.plan_id
    assert metadata["latest_material_pit_evidence_gate_closure_plan_id"] == result.plan_id
    assert metadata["material_pit_evidence_gate_closure_plan_remaining_blocked_count"] == 16

    assert (
        cli.main(
            [
                "research-status",
                "--root",
                str(reports),
                "--output-dir",
                str(tmp_path / "dashboard_cli"),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert f"latest_material_pit_evidence_gate_closure_plan_id: {result.plan_id}" in output
    assert (
        "material_pit_evidence_gate_closure_plan_stage: "
        "MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE"
    ) in output
    assert "material_pit_evidence_gate_closure_plan_approval_applied: False" in output


def _build_material_gate_closure_plan(
    output_root: Path,
    inputs: dict[str, Path],
):
    completion_plan = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=output_root / "first_batch_reviewer_evidence_completion_plan",
    )
    partial_impact = build_first_batch_partial_completion_impact(
        completion_plan=completion_plan.artifact_paths["artifact_dir"],
        output_dir=output_root / "first_batch_partial_completion_impact",
    )
    return build_material_pit_evidence_gate_closure_plan(
        audit=None,
        partial_impact=partial_impact.artifact_paths["artifact_dir"],
        completion_plan=completion_plan.artifact_paths["artifact_dir"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=output_root / "material_pit_evidence_gate_closure_plan",
    )


def _write_inputs(tmp_path: Path) -> dict[str, Path]:
    evidence_update_plan = _write_evidence_update_plan(tmp_path)
    downstream = _write_downstream_impact(tmp_path)
    enrichment = _write_enrichment(tmp_path)
    validator = _write_validator(tmp_path)
    policy = _write_policy_comparison(tmp_path)
    return {
        "evidence_update_plan": evidence_update_plan,
        "downstream_impact": downstream,
        "enrichment": enrichment,
        "validator": validator,
        "policy_comparison": policy,
    }


def _write_evidence_update_plan(tmp_path: Path) -> Path:
    root = tmp_path / "activated_replacement_worklist_evidence_update_plan" / "plan123"
    root.mkdir(parents=True)
    rows = [_first_batch_row(date, "000001", "stock_core", "STOCK") for date in DATES]
    rows += [_first_batch_row(date, "159915", "etf_core", "ETF") for date in DATES]
    frame = pd.DataFrame(rows)
    frame.to_csv(root / "activated_replacement_worklist_evidence_update_plan.csv", index=False)
    frame.loc[frame["universe_name"] == "stock_core"].to_csv(root / "stock_core_first_batch_package.csv", index=False)
    frame.loc[frame["universe_name"] == "etf_core"].to_csv(root / "etf_core_first_batch_package.csv", index=False)
    (root / "metadata.json").write_text(
        json.dumps(
            {
                "plan_id": "plan123",
                "activation_id": "activation123",
                "acceptance_id": "acceptance123",
                "replacement_plan_id": "replacement123",
                "source_split_plan_id": "split123",
                "source_policy_audit_id": "policy123",
                "source_worklist_id": "legacy123",
                "output_files": {
                    "stock_core_first_batch_package": str(root / "stock_core_first_batch_package.csv"),
                    "etf_core_first_batch_package": str(root / "etf_core_first_batch_package.csv"),
                },
            }
        ),
        encoding="utf-8",
    )
    return root


def _write_downstream_impact(tmp_path: Path) -> Path:
    root = tmp_path / "reviewer_no_hit_acceptance_downstream_impact" / "impact123"
    root.mkdir(parents=True)
    rows = []
    for date, symbol, universe in _targets():
        for exception_type in EXCEPTION_TYPES:
            rows.append(
                {
                    "impact_id": "impact123",
                    "acceptance_id": "acceptance_no_hit123",
                    "enrichment_id": "enrichment123",
                    "source_packet_id": "packet123",
                    "reviewed_no_hit_policy_comparison_id": "comparison123",
                    "validator_id": "validator123",
                    "signal_date": date,
                    "symbol": symbol,
                    "universe_name": universe,
                    "exception_type": exception_type,
                    "acceptance_status": "NEEDS_REVIEW",
                    "accepted_no_hit_context": False,
                    "accepted_no_hit_context_only": False,
                    "checklist_pass_after": False,
                    "remaining_blocked": True,
                    "approval_applied": False,
                    "pit_review_run": False,
                    "export_readiness_run": False,
                    "export_staging_run": False,
                    "universe_exported": False,
                    "no_clean_review_updates_created": True,
                    "no_data_raw_write": True,
                    "no_data_processed_write": True,
                    "no_current_candidates_generated": True,
                    "impact_only": True,
                }
            )
    pd.DataFrame(rows).to_csv(root / "reviewer_no_hit_acceptance_downstream_impact.csv", index=False)
    (root / "metadata.json").write_text(
        json.dumps(
            {
                "impact_id": "impact123",
                "acceptance_id": "acceptance_no_hit123",
                "enrichment_id": "enrichment123",
                "source_packet_id": "packet123",
                "reviewed_no_hit_policy_comparison_id": "comparison123",
                "validator_id": "validator123",
                "accepted_no_hit_context_count": 0,
                "checklist_pass_count": 0,
                "remaining_blocked_count": 16,
                "approval_applied": False,
            }
        ),
        encoding="utf-8",
    )
    return root


def _write_enrichment(tmp_path: Path) -> Path:
    root = tmp_path / "pit_official_status_evidence_packet_enrichment" / "enrichment123"
    root.mkdir(parents=True)
    rows = []
    for date, symbol, universe in _targets():
        rows.append(
            {
                "enrichment_id": "enrichment123",
                "source_packet_id": "packet123",
                "policy_comparison_id": "comparison123",
                "signal_date": date,
                "symbol": symbol,
                "universe_name": universe,
                "strong_official_date_specific_quotation": True,
                "quotation_source_url": f"https://example.test/{symbol}/{date}",
                "reviewed_no_hit_context_supported": True,
                "reviewer_acceptance_required": True,
                "missing_evidence_categories": (
                    "active_not_delisted_evidence; pit_safe_as_of_date; reviewer_no_hit_acceptance; "
                    "stock_st_no_st_evidence; survivorship_bias_resolution"
                ),
                "remaining_blocked": True,
                "checklist_pass": False,
                "no_approval_applied": True,
                "no_universe_export": True,
                "no_current_candidates_generated": True,
            }
        )
    pd.DataFrame(rows).to_csv(root / "pit_official_status_evidence_packet_enrichment.csv", index=False)
    (root / "metadata.json").write_text(json.dumps({"enrichment_id": "enrichment123"}), encoding="utf-8")
    return root


def _write_validator(tmp_path: Path) -> Path:
    root = tmp_path / "pit_evidence_checklist_validator" / "validator123"
    root.mkdir(parents=True)
    rows = []
    for date, symbol, universe in _targets():
        missing = "as_of_date, industry, is_active, is_active_evidence, revision_id, t_plus_rule"
        if symbol == "000001":
            missing += ", is_st"
        rows.append(
            {
                "validator_id": "validator123",
                "signal_date": date,
                "symbol": symbol,
                "universe_name": universe,
                "checklist_pass": False,
                "blocked": True,
                "missing_required_fields": missing,
                "blocker_reason": "missing evidence; PIT timing blocked; survivorship unresolved",
                "survivorship_blocker": True,
                "stock_st_blocker": symbol == "000001",
            }
        )
    pd.DataFrame(rows).to_csv(root / "pit_evidence_checklist_validation.csv", index=False)
    (root / "metadata.json").write_text(
        json.dumps({"validator_id": "validator123", "checklist_pass_count": 0, "blocked_count": 16}),
        encoding="utf-8",
    )
    return root


def _write_policy_comparison(tmp_path: Path) -> Path:
    root = tmp_path / "pit_evidence_policy_profile_comparison" / "comparison123"
    root.mkdir(parents=True)
    rows = []
    for date, symbol, universe in _targets():
        rows.append(
            {
                "comparison_id": "comparison123",
                "signal_date": date,
                "symbol": symbol,
                "universe_name": universe,
                "recommended_future_universe": universe,
                "reviewed_no_hit_support_pass": False,
                "remaining_blockers": "survivorship_bias_resolved remains false",
            }
        )
    pd.DataFrame(rows).to_csv(root / "pit_evidence_policy_profile_comparison.csv", index=False)
    (root / "metadata.json").write_text(json.dumps({"comparison_id": "comparison123"}), encoding="utf-8")
    return root


def _targets() -> list[tuple[str, str, str]]:
    return [(date, "000001", "stock_core") for date in DATES] + [(date, "159915", "etf_core") for date in DATES]


def _first_batch_row(date: str, symbol: str, universe: str, instrument_type: str) -> dict[str, object]:
    return {
        "plan_id": "plan123",
        "activation_id": "activation123",
        "acceptance_id": "acceptance123",
        "replacement_plan_id": "replacement123",
        "source_split_plan_id": "split123",
        "source_policy_audit_id": "policy123",
        "source_worklist_id": "legacy123",
        "signal_date": date,
        "symbol": symbol,
        "current_universe_name": "etf_core",
        "future_universe_name": universe,
        "universe_name": universe,
        "resolved_instrument_type": instrument_type,
        "review_status": "NEEDS_MANUAL_REVIEW",
        "include_flag": False,
        "valid_for_signal_date": False,
        "survivorship_bias_resolved": False,
        "manual_review_required": True,
        "evidence_update_planning_only": True,
        "clean_review_updates_created": False,
        "active_worklist_mutated": False,
        "no_approval_applied": True,
        "no_rejection_applied": True,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
    }


def _write_paper_workflow_status(root: Path) -> None:
    status_dir = root / "paper_trading" / "workflow_status" / "paper-ready"
    status_dir.mkdir(parents=True)
    report = status_dir / "paper_workflow_status_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    (status_dir / "metadata.json").write_text(
        json.dumps(
            {
                "workflow_status_id": "paper-ready",
                "created_at": "2024-05-20T16:15:00",
                "status": "WARN",
                "workflow_stage": "WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
                "latest_decision_date": "2024-05-20",
                "next_manual_action": "Continue WATCH_ONLY paper workflow.",
                "total_warning_count": 1,
                "expected_demo_warning_count": 1,
                "stale_warning_count": 0,
                "actionable_warning_count": 0,
                "blocking_error_count": 0,
                "component_statuses": {
                    "total_warning_count": 1,
                    "expected_demo_warning_count": 1,
                    "stale_warning_count": 0,
                    "actionable_warning_count": 0,
                    "blocking_error_count": 0,
                },
                "output_files": {"paper_workflow_status_report": str(report)},
                "warnings": [],
                "live_trading_enabled": False,
                "broker_api_invoked": False,
            }
        ),
        encoding="utf-8",
    )


def _write_tiny_manual_completion_fixture(template_path: Path, tmp_path: Path) -> Path:
    template = pd.read_csv(template_path, dtype=str, keep_default_na=False)
    fixture = template.loc[
        (template["signal_date"] == "2024-04-02")
        & (template["symbol"] == "000001")
        & (template["universe_name"] == "stock_core")
    ].copy()
    assert len(fixture) == 1
    fixture.loc[:, "review_status"] = "NEEDS_MORE_EVIDENCE"
    fixture.loc[:, "include_flag"] = "False"
    fixture.loc[:, "valid_for_signal_date"] = "False"
    fixture.loc[:, "survivorship_bias_resolved"] = "False"
    fixture.loc[:, "reviewer"] = "diagnostics_reviewer"
    fixture.loc[:, "reviewed_at"] = "2026-06-06T00:00:00+08:00"
    fixture.loc[:, "review_reason"] = "Diagnostics-only manual completion smoke; not PIT approval."
    fixture.loc[:, "evidence_source"] = "DIAGNOSTICS_ONLY_FIXTURE"
    fixture.loc[:, "evidence_reference"] = "Shape validation only; no authoritative PIT evidence asserted."
    fixture_dir = tmp_path / "manual_diagnostics"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = fixture_dir / "tiny_manual_reviewer_completion_fixture.csv"
    fixture.to_csv(fixture_path, index=False)
    return fixture_path
