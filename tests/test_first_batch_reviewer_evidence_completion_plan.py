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
from quant_replay_system.reviewer_material_evidence_fill_guidance import (
    build_reviewer_material_evidence_fill_guidance,
)
from quant_replay_system.reviewer_material_evidence_fill_guidance_health import (
    check_reviewer_material_evidence_fill_guidance_health,
)
from quant_replay_system.reviewer_material_evidence_fill_guidance_index import (
    build_reviewer_material_evidence_fill_guidance_index,
)
from quant_replay_system.reviewer_material_evidence_fill_guidance_status import (
    run_reviewer_material_evidence_fill_guidance_status,
)
from quant_replay_system.one_row_material_evidence_fill_package import (
    build_one_row_material_evidence_fill_package,
)
from quant_replay_system.one_row_material_evidence_fill_package_health import (
    check_one_row_material_evidence_fill_package_health,
)
from quant_replay_system.one_row_material_evidence_fill_package_index import (
    build_one_row_material_evidence_fill_package_index,
)
from quant_replay_system.one_row_material_evidence_fill_package_status import (
    run_one_row_material_evidence_fill_package_status,
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


def _has_truthy_value(frame: pd.DataFrame, column: str) -> bool:
    return frame[column].astype(str).str.lower().isin({"true", "1", "yes", "y"}).any()


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


def test_reviewer_material_evidence_fill_guidance_builds_report_only_guidance(
    tmp_path: Path,
    capsys,
) -> None:
    inputs = _write_inputs(tmp_path)
    material_plan = _build_material_gate_closure_plan(tmp_path, inputs)

    result = build_reviewer_material_evidence_fill_guidance(
        material_plan=material_plan.artifact_paths["artifact_dir"],
        audit=None,
        completion_plan=tmp_path / "first_batch_reviewer_evidence_completion_plan",
        partial_impact=tmp_path / "first_batch_partial_completion_impact",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "reviewer_guidance",
    )

    assert result.row_count == 16
    assert result.symbol_level_guidance_count == 2
    assert result.date_specific_guidance_count == 16
    assert result.no_hit_acceptance_guidance_count == 64
    assert result.survivorship_rationale_guidance_count == 16
    assert result.metadata_guidance_count == 16
    assert result.reviewer_guidance_row_count == 114
    assert result.checklist_pass_candidate_count == 0
    assert result.remaining_blocked_count == 16
    assert result.clean_review_updates_created is False
    assert result.approval_applied is False
    assert result.material_pit_evidence_gate_closure_plan_id == material_plan.plan_id
    assert result.first_batch_partial_completion_impact_id == material_plan.lineage[
        "first_batch_partial_completion_impact_id"
    ]
    assert result.first_batch_reviewer_evidence_completion_plan_id == material_plan.lineage[
        "first_batch_reviewer_evidence_completion_plan_id"
    ]
    assert result.validator_id == material_plan.lineage["validator_id"]
    assert result.enrichment_id == material_plan.lineage["enrichment_id"]
    assert result.reviewer_no_hit_downstream_impact_id == material_plan.lineage[
        "reviewer_no_hit_downstream_impact_id"
    ]

    guidance = pd.read_csv(result.artifact_paths["guidance_csv"], dtype=str, keep_default_na=False)
    assert len(guidance) == 16
    assert set(guidance["symbol"]) == {"000001", "159915"}
    assert set(guidance["universe_name"]) == {"stock_core", "etf_core"}
    assert not guidance.duplicated(["signal_date", "symbol", "universe_name"]).any()
    assert set(guidance["checklist_pass_candidate"]) == {"False"}
    assert set(guidance["include_flag"]) == {"False"}
    assert set(guidance["valid_for_signal_date"]) == {"False"}
    assert set(guidance["survivorship_bias_resolved"]) == {"False"}
    assert set(guidance["approval_applied"]) == {"False"}
    assert guidance.loc[guidance["symbol"] == "000001", "fill_groups_required"].str.contains(
        "DATE_SPECIFIC_PIT_STATUS"
    ).all()

    fill_order = pd.read_csv(result.artifact_paths["recommended_fill_order"], dtype=str, keep_default_na=False)
    assert fill_order.iloc[0]["fill_group"] == "SAFETY_BASELINE"
    assert "REUSABLE_SYMBOL_LEVEL" in set(fill_order["fill_group"])
    assert "DATE_SPECIFIC_PIT_STATUS" in set(fill_order["fill_group"])

    symbol_guidance = pd.read_csv(
        result.artifact_paths["symbol_level_fill_guidance"],
        dtype=str,
        keep_default_na=False,
    )
    date_guidance = pd.read_csv(
        result.artifact_paths["date_specific_fill_guidance"],
        dtype=str,
        keep_default_na=False,
    )
    no_hit = pd.read_csv(result.artifact_paths["no_hit_acceptance_fill_guidance"], dtype=str, keep_default_na=False)
    survivorship = pd.read_csv(
        result.artifact_paths["survivorship_rationale_fill_guidance"],
        dtype=str,
        keep_default_na=False,
    )
    metadata = pd.read_csv(result.artifact_paths["metadata_fill_guidance"], dtype=str, keep_default_na=False)
    template = pd.read_csv(
        result.artifact_paths["reviewer_fill_template_safe_defaults"],
        dtype=str,
        keep_default_na=False,
    )
    risk = pd.read_csv(result.artifact_paths["reviewer_risk_controls"], dtype=str, keep_default_na=False)

    assert len(symbol_guidance) == 2
    assert len(date_guidance) == 16
    assert len(no_hit) == 64
    assert set(no_hit["supporting_context_only"]) == {"True"}
    assert set(no_hit["can_approve_row"]) == {"False"}
    assert len(survivorship) == 16
    assert len(metadata) == 16
    assert len(template) == 88
    assert set(template["review_status"]) == {"NEEDS_MORE_EVIDENCE"}
    assert set(template["include_flag"]) == {"False"}
    assert set(template["valid_for_signal_date"]) == {"False"}
    assert set(template["survivorship_bias_resolved"]) == {"False"}
    assert set(template["approval_applied"]) == {"False"}
    assert risk["risk_control"].str.contains("Do not create clean review_updates.csv here.").any()

    artifact_text = "\n".join(
        path.read_text(encoding="utf-8")
        for key, path in result.artifact_paths.items()
        if key != "artifact_dir" and path.suffix in {".csv", ".md", ".json"}
    )
    assert "APPROVED_FOR_PIT_UNIVERSE" not in artifact_text
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
                "reviewer-material-evidence-fill-guidance",
                "--material-plan",
                str(material_plan.artifact_paths["artifact_dir"]),
                "--audit",
                "",
                "--completion-plan",
                str(tmp_path / "first_batch_reviewer_evidence_completion_plan"),
                "--partial-impact",
                str(tmp_path / "first_batch_partial_completion_impact"),
                "--validator",
                str(inputs["validator"]),
                "--enrichment",
                str(inputs["enrichment"]),
                "--reviewer-no-hit-acceptance",
                "",
                "--reviewer-no-hit-downstream-impact",
                str(inputs["downstream_impact"]),
                "--output-dir",
                str(tmp_path / "reviewer_guidance_cli"),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "row_count: 16" in output
    assert "symbol_level_guidance_count: 2" in output
    assert "date_specific_guidance_count: 16" in output
    assert "no_hit_acceptance_guidance_count: 64" in output
    assert "approval_applied: False" in output


def test_reviewer_fill_fixture_impact_validation_reduces_only_shape_blocker(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    material_plan = _build_material_gate_closure_plan(tmp_path, inputs)
    guidance = build_reviewer_material_evidence_fill_guidance(
        material_plan=material_plan.artifact_paths["artifact_dir"],
        audit=None,
        completion_plan=tmp_path / "first_batch_reviewer_evidence_completion_plan",
        partial_impact=tmp_path / "first_batch_partial_completion_impact",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "reviewer_material_evidence_fill_guidance",
    )

    template = pd.read_csv(
        guidance.artifact_paths["reviewer_fill_template_safe_defaults"],
        dtype=str,
        keep_default_na=False,
    )
    target_mask = (
        (template["signal_date"] == "2024-04-02")
        & (template["symbol"] == "000001")
        & (template["universe_name"] == "stock_core")
    )
    fixture = template.loc[target_mask].copy()
    assert len(fixture) == 6
    assert set(fixture["symbol"]) == {"000001"}
    assert set(fixture["closure_path"]) == {
        "REUSABLE_SYMBOL_LEVEL",
        "DATE_SPECIFIC",
        "REVIEWER_NO_HIT_ACCEPTANCE",
        "SURVIVORSHIP_RATIONALE",
        "PIT_METADATA",
        "STOCK_ONLY_ST_NO_ST",
    }

    fixture.loc[:, "review_status"] = "NEEDS_MORE_EVIDENCE"
    fixture.loc[:, "reviewer"] = "diagnostics_reviewer"
    fixture.loc[:, "reviewed_at"] = "2026-06-06T00:00:00+08:00"
    fixture.loc[:, "review_reason"] = "Diagnostics-only reviewer fill fixture; not PIT approval."
    fixture.loc[:, "evidence_source"] = "DIAGNOSTICS_ONLY_FIXTURE"
    fixture.loc[:, "evidence_reference"] = "Shape validation only; no authoritative PIT evidence asserted."
    fixture.loc[:, "source_limitations"] = "Fixture only; material PIT blockers remain."
    fixture.loc[:, "reviewer_notes"] = "Reviewer shape fields completed for validation only."
    fixture.loc[:, "include_flag"] = "False"
    fixture.loc[:, "valid_for_signal_date"] = "False"
    fixture.loc[:, "approval_applied"] = "False"

    fixture_dir = tmp_path / "manual_diagnostics" / "reviewer_fill_fixture_impact_validation"
    fixture_dir.mkdir(parents=True)
    fixture_path = fixture_dir / "reviewer_fill_fixture.csv"
    fixture.to_csv(fixture_path, index=False)

    validated = pd.read_csv(fixture_path, dtype=str, keep_default_na=False)
    assert len(validated) == 6
    assert set(validated["symbol"]) == {"000001"}
    assert set(validated["review_status"]) == {"NEEDS_MORE_EVIDENCE"}
    assert not _has_truthy_value(validated, "include_flag")
    assert not _has_truthy_value(validated, "valid_for_signal_date")
    assert not _has_truthy_value(validated, "approval_applied")
    assert "APPROVED_FOR_PIT_UNIVERSE" not in fixture_path.read_text(encoding="utf-8")

    reviewer_shape_fields = ["reviewer", "reviewed_at", "review_reason", "evidence_source", "evidence_reference"]
    reviewer_shape_blocker_reduced_count = int(
        validated[reviewer_shape_fields].apply(lambda column: column.astype(str).str.len().gt(0).all()).all()
    )
    assert reviewer_shape_blocker_reduced_count == 1

    blocker_matrix = pd.read_csv(
        material_plan.artifact_paths["row_level_material_blocker_matrix"],
        dtype=str,
        keep_default_na=False,
    )
    blocker_row = blocker_matrix.loc[
        (blocker_matrix["signal_date"] == "2024-04-02")
        & (blocker_matrix["symbol"] == "000001")
        & (blocker_matrix["universe_name"] == "stock_core")
    ].iloc[0]
    assert blocker_row["remaining_blocked"] == "True"
    assert blocker_row["checklist_pass_candidate"] == "False"
    assert blocker_row["missing_as_of_date"] == "True"
    assert blocker_row["missing_industry"] == "True"
    assert blocker_row["missing_is_active"] == "True"
    assert blocker_row["missing_is_active_evidence"] == "True"
    assert blocker_row["missing_revision_id"] == "True"
    assert blocker_row["missing_t_plus_rule"] == "True"
    assert blocker_row["missing_is_st"] == "True"

    requirements = pd.read_csv(
        material_plan.artifact_paths["checklist_pass_candidate_requirements"],
        dtype=str,
        keep_default_na=False,
    )
    requirement_row = requirements.loc[
        (requirements["signal_date"] == "2024-04-02")
        & (requirements["symbol"] == "000001")
        & (requirements["universe_name"] == "stock_core")
    ].iloc[0]
    assert requirement_row["checklist_pass_candidate_now"] == "False"
    assert requirement_row["approval_allowed_now"] == "False"
    assert requirement_row["clean_review_updates_allowed_now"] == "False"

    assert guidance.checklist_pass_candidate_count == 0
    assert guidance.remaining_blocked_count == 16
    assert material_plan.checklist_pass_candidate_count == 0
    assert material_plan.remaining_blocked_count == 16
    material_blocker_reduced_count = 0
    assert material_blocker_reduced_count == 0
    assert not (fixture_dir / "review_updates.csv").exists()
    assert not (fixture_dir / "clean_review_updates.csv").exists()
    assert not (guidance.artifact_paths["artifact_dir"] / "review_updates.csv").exists()
    assert not (guidance.artifact_paths["artifact_dir"] / "clean_review_updates.csv").exists()
    assert not (tmp_path / "point_in_time_universe_overlay_review").exists()
    assert not (tmp_path / "point_in_time_universe_overlay_export_readiness").exists()
    assert not (tmp_path / "point_in_time_universe_export_staging").exists()
    assert not (tmp_path / "current_candidates").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_one_row_material_evidence_fill_package_remains_report_only(
    tmp_path: Path,
    capsys,
) -> None:
    inputs = _write_inputs(tmp_path)
    material_plan = _build_material_gate_closure_plan(tmp_path, inputs)
    guidance = build_reviewer_material_evidence_fill_guidance(
        material_plan=material_plan.artifact_paths["artifact_dir"],
        audit=None,
        completion_plan=tmp_path / "first_batch_reviewer_evidence_completion_plan",
        partial_impact=tmp_path / "first_batch_partial_completion_impact",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "reviewer_material_evidence_fill_guidance",
    )
    audit = _write_one_row_material_evidence_fill_package_audit(tmp_path)

    result = build_one_row_material_evidence_fill_package(
        audit=audit,
        guidance=guidance.artifact_paths["artifact_dir"],
        material_plan=material_plan.artifact_paths["artifact_dir"],
        partial_impact=tmp_path / "first_batch_partial_completion_impact",
        completion_plan=tmp_path / "first_batch_reviewer_evidence_completion_plan",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "one_row_material_evidence_fill_package",
    )

    assert result.package_row_count == 1
    assert result.request.signal_date == "2024-04-02"
    assert result.request.symbol == "000001"
    assert result.request.universe_name == "stock_core"
    assert result.context_field_drafted_count > 0
    assert result.material_blocker_closed_count == 0
    assert result.checklist_pass_candidate_count == 0
    assert result.remaining_blocked_count == 16
    assert result.clean_review_updates_created is False
    assert result.approval_applied is False
    assert result.reviewer_material_evidence_fill_guidance_id == guidance.guidance_id
    assert result.material_pit_evidence_gate_closure_plan_id == material_plan.plan_id
    assert result.first_batch_partial_completion_impact_id == material_plan.lineage[
        "first_batch_partial_completion_impact_id"
    ]
    assert result.first_batch_reviewer_evidence_completion_plan_id == material_plan.lineage[
        "first_batch_reviewer_evidence_completion_plan_id"
    ]
    assert result.validator_id == material_plan.lineage["validator_id"]
    assert result.enrichment_id == material_plan.lineage["enrichment_id"]

    package = pd.read_csv(result.artifact_paths["package_csv"], dtype=str, keep_default_na=False)
    assert len(package) == 1
    row = package.iloc[0]
    assert row["signal_date"] == "2024-04-02"
    assert row["symbol"] == "000001"
    assert row["universe_name"] == "stock_core"
    assert row["review_status"] == "NEEDS_MORE_EVIDENCE"
    assert row["include_flag"] == "False"
    assert row["valid_for_signal_date"] == "False"
    assert row["survivorship_bias_resolved"] == "False"
    assert row["active_not_delisted_blocked"] == "True"
    assert row["stock_st_no_st_blocked"] == "True"
    assert row["survivorship_blocked"] == "True"
    assert row["approval_applied"] == "False"
    assert row["clean_review_updates_created"] == "False"
    assert row["no_current_candidates_generated"] == "True"

    drafted = pd.read_csv(result.artifact_paths["drafted_context_fields"], dtype=str, keep_default_na=False)
    assert set(drafted["symbol"]) == {"000001"}
    assert {"as_of_date", "industry", "t_plus_rule", "revision_id", "source"}.issubset(set(drafted["field"]))
    assert set(drafted["approval_safe"]) == {"no"}
    assert set(drafted["can_close_material_blocker"]) == {"False"}
    assert not _has_truthy_value(drafted, "include_flag")
    assert not _has_truthy_value(drafted, "valid_for_signal_date")
    assert not _has_truthy_value(drafted, "survivorship_bias_resolved")

    remaining = pd.read_csv(result.artifact_paths["remaining_blockers_after_fill"], dtype=str, keep_default_na=False)
    assert "is_active / active-not-delisted evidence" in set(remaining["blocker"])
    assert "is_st / no-ST evidence" in set(remaining["blocker"])
    assert "survivorship-bias resolution" in set(remaining["blocker"])
    assert set(remaining["checklist_pass_candidate"]) == {"False"}
    assert set(remaining["approval_applied"]) == {"False"}

    risks = pd.read_csv(result.artifact_paths["overclaim_risk_matrix"], dtype=str, keep_default_na=False)
    assert "is_active=true" in set(risks["claim_or_field"])
    assert "is_st=false" in set(risks["claim_or_field"])
    assert "survivorship_bias_resolved=true" in set(risks["claim_or_field"])

    safety = json.loads(result.artifact_paths["package_safety_validation"].read_text(encoding="utf-8"))
    assert safety["validation_status"] == "PASS"
    assert safety["approved_for_pit_universe_present"] is False
    assert safety["include_flag_true_present"] is False
    assert safety["valid_for_signal_date_true_present"] is False
    assert safety["survivorship_bias_resolved_true_present"] is False
    assert safety["clean_review_updates_created"] is False
    assert safety["approval_applied"] is False
    assert safety["no_data_raw_write"] is True
    assert safety["no_data_processed_write"] is True
    assert safety["no_current_candidates_generated"] is True

    lineage = pd.read_csv(result.artifact_paths["source_lineage_summary"], dtype=str, keep_default_na=False)
    assert {
        "reviewer_material_evidence_fill_guidance_id",
        "material_pit_evidence_gate_closure_plan_id",
        "first_batch_partial_completion_impact_id",
        "first_batch_reviewer_evidence_completion_plan_id",
        "validator_id",
        "enrichment_id",
        "reviewer_no_hit_downstream_impact_id",
    }.issubset(set(lineage["lineage_field"]))

    artifact_text = "\n".join(
        path.read_text(encoding="utf-8")
        for key, path in result.artifact_paths.items()
        if key != "artifact_dir" and path.suffix in {".csv", ".md", ".json"}
    )
    assert "APPROVED_FOR_PIT_UNIVERSE" not in artifact_text
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
                "one-row-material-evidence-fill-package",
                "--audit",
                str(audit),
                "--guidance",
                str(guidance.artifact_paths["artifact_dir"]),
                "--material-plan",
                str(material_plan.artifact_paths["artifact_dir"]),
                "--partial-impact",
                str(tmp_path / "first_batch_partial_completion_impact"),
                "--completion-plan",
                str(tmp_path / "first_batch_reviewer_evidence_completion_plan"),
                "--validator",
                str(inputs["validator"]),
                "--enrichment",
                str(inputs["enrichment"]),
                "--reviewer-no-hit-acceptance",
                "",
                "--reviewer-no-hit-downstream-impact",
                str(inputs["downstream_impact"]),
                "--output-dir",
                str(tmp_path / "one_row_material_evidence_fill_package_cli"),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "package_row_count: 1" in output
    assert "symbol: 000001" in output
    assert "material_blocker_closed_count: 0" in output
    assert "checklist_pass_candidate_count: 0" in output
    assert "approval_applied: False" in output


def test_one_row_material_evidence_fill_package_index_health_status_and_cli(
    tmp_path: Path,
    capsys,
) -> None:
    inputs = _write_inputs(tmp_path)
    material_plan = _build_material_gate_closure_plan(tmp_path, inputs)
    guidance = build_reviewer_material_evidence_fill_guidance(
        material_plan=material_plan.artifact_paths["artifact_dir"],
        audit=None,
        completion_plan=tmp_path / "first_batch_reviewer_evidence_completion_plan",
        partial_impact=tmp_path / "first_batch_partial_completion_impact",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "reviewer_material_evidence_fill_guidance",
    )
    package = build_one_row_material_evidence_fill_package(
        audit=_write_one_row_material_evidence_fill_package_audit(tmp_path),
        guidance=guidance.artifact_paths["artifact_dir"],
        material_plan=material_plan.artifact_paths["artifact_dir"],
        partial_impact=tmp_path / "first_batch_partial_completion_impact",
        completion_plan=tmp_path / "first_batch_reviewer_evidence_completion_plan",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "one_row_material_evidence_fill_package",
    )

    index = build_one_row_material_evidence_fill_package_index(
        root=tmp_path / "one_row_material_evidence_fill_package",
        output_dir=tmp_path / "one_row_material_evidence_fill_package" / "index",
    )
    assert index.artifact_count == 1
    assert index.index_frame.iloc[0]["package_id"] == package.package_id
    assert index.index_frame.iloc[0]["target_symbol"] == "000001"

    health = check_one_row_material_evidence_fill_package_health(
        root=tmp_path / "one_row_material_evidence_fill_package",
        output_dir=tmp_path / "one_row_material_evidence_fill_package" / "health",
    )
    assert health.status == "PASS"
    assert health.issue_count == 0

    status = run_one_row_material_evidence_fill_package_status(
        root=tmp_path / "one_row_material_evidence_fill_package",
        output_dir=tmp_path / "one_row_material_evidence_fill_package" / "status",
    )
    assert status.latest_package_id == package.package_id
    assert status.status == "WARN"
    assert status.workflow_stage == "ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_CONTEXT_DRAFTED"
    assert status.health_status == "PASS"
    assert status.target_signal_date == "2024-04-02"
    assert status.target_symbol == "000001"
    assert status.target_universe_name == "stock_core"
    assert status.package_row_count == 1
    assert status.context_field_drafted_count == package.context_field_drafted_count
    assert status.material_blocker_closed_count == 0
    assert status.checklist_pass_candidate_count == 0
    assert status.remaining_blocked_count == 16
    assert status.clean_review_updates_created is False
    assert status.approval_applied is False

    assert (
        cli.main(
            [
                "one-row-material-evidence-fill-package-index",
                "--root",
                str(tmp_path / "one_row_material_evidence_fill_package"),
                "--output-dir",
                str(tmp_path / "one_row_material_evidence_fill_package_cli" / "index"),
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "one-row-material-evidence-fill-package-health",
                "--root",
                str(tmp_path / "one_row_material_evidence_fill_package"),
                "--output-dir",
                str(tmp_path / "one_row_material_evidence_fill_package_cli" / "health"),
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "one-row-material-evidence-fill-package-status",
                "--root",
                str(tmp_path / "one_row_material_evidence_fill_package"),
                "--output-dir",
                str(tmp_path / "one_row_material_evidence_fill_package_cli" / "status"),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert f"latest_package_id: {package.package_id}" in output
    assert "workflow_stage: ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_CONTEXT_DRAFTED" in output
    assert "target_symbol: 000001" in output
    assert "approval_applied: False" in output


def test_one_row_material_evidence_fill_package_health_fails_for_unsafe_artifacts(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    material_plan = _build_material_gate_closure_plan(tmp_path, inputs)
    guidance = build_reviewer_material_evidence_fill_guidance(
        material_plan=material_plan.artifact_paths["artifact_dir"],
        audit=None,
        completion_plan=tmp_path / "first_batch_reviewer_evidence_completion_plan",
        partial_impact=tmp_path / "first_batch_partial_completion_impact",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "reviewer_material_evidence_fill_guidance",
    )
    package = build_one_row_material_evidence_fill_package(
        audit=_write_one_row_material_evidence_fill_package_audit(tmp_path),
        guidance=guidance.artifact_paths["artifact_dir"],
        material_plan=material_plan.artifact_paths["artifact_dir"],
        partial_impact=tmp_path / "first_batch_partial_completion_impact",
        completion_plan=tmp_path / "first_batch_reviewer_evidence_completion_plan",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "one_row_material_evidence_fill_package",
    )
    metadata_path = package.artifact_paths["metadata"]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["approval_applied"] = True
    metadata["clean_review_updates_created"] = True
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    package_frame = pd.read_csv(package.artifact_paths["package_csv"], dtype=str, keep_default_na=False)
    package_frame.loc[0, "review_status"] = "APPROVED_FOR_PIT_UNIVERSE"
    package_frame.loc[0, "include_flag"] = "True"
    package_frame.loc[0, "valid_for_signal_date"] = "True"
    package_frame.loc[0, "survivorship_bias_resolved"] = "True"
    package_frame.to_csv(package.artifact_paths["package_csv"], index=False)
    (package.artifact_paths["artifact_dir"] / "clean_review_updates.csv").write_text(
        "signal_date,symbol,universe_name\n2024-04-02,000001,stock_core\n",
        encoding="utf-8",
    )

    health = check_one_row_material_evidence_fill_package_health(
        root=tmp_path / "one_row_material_evidence_fill_package",
        output_dir=tmp_path / "one_row_material_evidence_fill_package" / "health",
    )
    issue_codes = set(health.health_frame["issue_code"])
    assert health.status == "FAIL"
    assert "APPROVAL_APPLIED_DETECTED" in issue_codes
    assert "CLEAN_REVIEW_UPDATES_FILE_DETECTED" in issue_codes
    assert "APPROVED_FOR_PIT_UNIVERSE_DETECTED" in issue_codes
    assert "INCLUDE_FLAG_TRUE_DETECTED" in issue_codes
    assert "VALID_FOR_SIGNAL_DATE_TRUE_DETECTED" in issue_codes
    assert "SURVIVORSHIP_BIAS_RESOLVED_TRUE_DETECTED" in issue_codes


def test_reviewer_material_evidence_fill_guidance_index_health_status_and_cli(
    tmp_path: Path,
    capsys,
) -> None:
    inputs = _write_inputs(tmp_path)
    material_plan = _build_material_gate_closure_plan(tmp_path, inputs)
    guidance = build_reviewer_material_evidence_fill_guidance(
        material_plan=material_plan.artifact_paths["artifact_dir"],
        audit=None,
        completion_plan=tmp_path / "first_batch_reviewer_evidence_completion_plan",
        partial_impact=tmp_path / "first_batch_partial_completion_impact",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "reviewer_material_evidence_fill_guidance",
    )

    index = build_reviewer_material_evidence_fill_guidance_index(
        root=tmp_path / "reviewer_material_evidence_fill_guidance",
        output_dir=tmp_path / "reviewer_material_evidence_fill_guidance" / "index",
    )
    assert index.artifact_count == 1
    assert index.index_frame.iloc[0]["guidance_id"] == guidance.guidance_id
    assert index.index_frame.iloc[0]["row_count"] == 16

    health = check_reviewer_material_evidence_fill_guidance_health(
        root=tmp_path / "reviewer_material_evidence_fill_guidance",
        output_dir=tmp_path / "reviewer_material_evidence_fill_guidance" / "health",
    )
    assert health.status == "PASS"
    assert health.issue_count == 0

    status = run_reviewer_material_evidence_fill_guidance_status(
        root=tmp_path / "reviewer_material_evidence_fill_guidance",
        output_dir=tmp_path / "reviewer_material_evidence_fill_guidance" / "status",
    )
    assert status.latest_guidance_id == guidance.guidance_id
    assert status.status == "WARN"
    assert status.workflow_stage == "REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL"
    assert status.health_status == "PASS"
    assert status.row_count == 16
    assert status.reviewer_guidance_row_count == 114
    assert status.checklist_pass_candidate_count == 0
    assert status.remaining_blocked_count == 16
    assert status.clean_review_updates_created is False
    assert status.approval_applied is False

    assert (
        cli.main(
            [
                "reviewer-material-evidence-fill-guidance-index",
                "--root",
                str(tmp_path / "reviewer_material_evidence_fill_guidance"),
                "--output-dir",
                str(tmp_path / "reviewer_material_evidence_fill_guidance_cli" / "index"),
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "reviewer-material-evidence-fill-guidance-health",
                "--root",
                str(tmp_path / "reviewer_material_evidence_fill_guidance"),
                "--output-dir",
                str(tmp_path / "reviewer_material_evidence_fill_guidance_cli" / "health"),
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "reviewer-material-evidence-fill-guidance-status",
                "--root",
                str(tmp_path / "reviewer_material_evidence_fill_guidance"),
                "--output-dir",
                str(tmp_path / "reviewer_material_evidence_fill_guidance_cli" / "status"),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert f"latest_guidance_id: {guidance.guidance_id}" in output
    assert "workflow_stage: REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL" in output
    assert "approval_applied: False" in output


def test_reviewer_material_evidence_fill_guidance_health_fails_for_unsafe_artifacts(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    material_plan = _build_material_gate_closure_plan(tmp_path, inputs)
    guidance = build_reviewer_material_evidence_fill_guidance(
        material_plan=material_plan.artifact_paths["artifact_dir"],
        audit=None,
        completion_plan=tmp_path / "first_batch_reviewer_evidence_completion_plan",
        partial_impact=tmp_path / "first_batch_partial_completion_impact",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=tmp_path / "reviewer_material_evidence_fill_guidance",
    )
    metadata_path = guidance.artifact_paths["metadata"]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["approval_applied"] = True
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    guidance_frame = pd.read_csv(guidance.artifact_paths["guidance_csv"], dtype=str, keep_default_na=False)
    guidance_frame.loc[0, "include_flag"] = "True"
    guidance_frame.loc[0, "valid_for_signal_date"] = "True"
    guidance_frame.loc[0, "first_reviewer_action"] = "APPROVED_FOR_PIT_UNIVERSE"
    guidance_frame.to_csv(guidance.artifact_paths["guidance_csv"], index=False)
    (guidance.artifact_paths["artifact_dir"] / "review_updates.csv").write_text(
        "signal_date,symbol,universe_name\n2024-04-02,000001,stock_core\n",
        encoding="utf-8",
    )

    health = check_reviewer_material_evidence_fill_guidance_health(
        root=tmp_path / "reviewer_material_evidence_fill_guidance",
        output_dir=tmp_path / "reviewer_material_evidence_fill_guidance" / "health",
    )
    issue_codes = set(health.health_frame["issue_code"])
    assert health.status == "FAIL"
    assert "APPROVAL_APPLIED_DETECTED" in issue_codes
    assert "INCLUDE_FLAG_TRUE_DETECTED" in issue_codes
    assert "VALID_FOR_SIGNAL_DATE_TRUE_DETECTED" in issue_codes
    assert "APPROVED_FOR_PIT_UNIVERSE_DETECTED" in issue_codes
    assert "CLEAN_REVIEW_UPDATES_FILE_DETECTED" in issue_codes


def test_research_status_includes_reviewer_material_guidance_and_preserves_paper_priority(
    tmp_path: Path,
    capsys,
) -> None:
    inputs = _write_inputs(tmp_path)
    reports = tmp_path / "reports"
    material_plan = _build_material_gate_closure_plan(reports, inputs)
    guidance = build_reviewer_material_evidence_fill_guidance(
        material_plan=material_plan.artifact_paths["artifact_dir"],
        audit=None,
        completion_plan=reports / "first_batch_reviewer_evidence_completion_plan",
        partial_impact=reports / "first_batch_partial_completion_impact",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=reports / "reviewer_material_evidence_fill_guidance",
    )
    _write_paper_workflow_status(reports)

    dashboard = run_local_research_dashboard(root=reports, output_dir=tmp_path / "dashboard")

    assert dashboard.workflow_stage == "PAPER_WORKFLOW_READY"
    assert dashboard.latest_reviewer_material_evidence_fill_guidance_id == guidance.guidance_id
    assert (
        dashboard.reviewer_material_evidence_fill_guidance_stage
        == "REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL"
    )
    assert dashboard.reviewer_material_evidence_fill_guidance_row_count == 16
    assert dashboard.reviewer_material_evidence_fill_guidance_reviewer_guidance_row_count == 114
    assert dashboard.reviewer_material_evidence_fill_guidance_checklist_pass_candidate_count == 0
    assert dashboard.reviewer_material_evidence_fill_guidance_remaining_blocked_count == 16
    assert dashboard.reviewer_material_evidence_fill_guidance_clean_review_updates_created is False
    assert dashboard.reviewer_material_evidence_fill_guidance_approval_applied is False

    summary = pd.read_csv(dashboard.artifact_paths["local_research_summary"], dtype=str, keep_default_na=False)
    metadata = json.loads(dashboard.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert summary.iloc[0]["latest_reviewer_material_evidence_fill_guidance_id"] == guidance.guidance_id
    assert metadata["latest_reviewer_material_evidence_fill_guidance_id"] == guidance.guidance_id
    assert metadata["reviewer_material_evidence_fill_guidance_remaining_blocked_count"] == 16

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
    assert f"latest_reviewer_material_evidence_fill_guidance_id: {guidance.guidance_id}" in output
    assert (
        "reviewer_material_evidence_fill_guidance_stage: "
        "REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL"
    ) in output
    assert "reviewer_material_evidence_fill_guidance_approval_applied: False" in output


def test_research_status_includes_one_row_material_package_and_preserves_paper_priority(
    tmp_path: Path,
    capsys,
) -> None:
    inputs = _write_inputs(tmp_path)
    reports = tmp_path / "reports"
    material_plan = _build_material_gate_closure_plan(reports, inputs)
    guidance = build_reviewer_material_evidence_fill_guidance(
        material_plan=material_plan.artifact_paths["artifact_dir"],
        audit=None,
        completion_plan=reports / "first_batch_reviewer_evidence_completion_plan",
        partial_impact=reports / "first_batch_partial_completion_impact",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=reports / "reviewer_material_evidence_fill_guidance",
    )
    package = build_one_row_material_evidence_fill_package(
        audit=_write_one_row_material_evidence_fill_package_audit(reports),
        guidance=guidance.artifact_paths["artifact_dir"],
        material_plan=material_plan.artifact_paths["artifact_dir"],
        partial_impact=reports / "first_batch_partial_completion_impact",
        completion_plan=reports / "first_batch_reviewer_evidence_completion_plan",
        validator=inputs["validator"],
        enrichment=inputs["enrichment"],
        reviewer_no_hit_acceptance=None,
        reviewer_no_hit_downstream_impact=inputs["downstream_impact"],
        output_dir=reports / "one_row_material_evidence_fill_package",
    )
    _write_paper_workflow_status(reports)

    dashboard = run_local_research_dashboard(root=reports, output_dir=tmp_path / "dashboard")

    assert dashboard.workflow_stage == "PAPER_WORKFLOW_READY"
    assert dashboard.latest_one_row_material_evidence_fill_package_id == package.package_id
    assert (
        dashboard.one_row_material_evidence_fill_package_stage
        == "ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_CONTEXT_DRAFTED"
    )
    assert dashboard.one_row_material_evidence_fill_package_health_status == "PASS"
    assert dashboard.one_row_material_evidence_fill_package_target_signal_date == "2024-04-02"
    assert dashboard.one_row_material_evidence_fill_package_target_symbol == "000001"
    assert dashboard.one_row_material_evidence_fill_package_target_universe_name == "stock_core"
    assert dashboard.one_row_material_evidence_fill_package_package_row_count == 1
    assert dashboard.one_row_material_evidence_fill_package_context_field_drafted_count == (
        package.context_field_drafted_count
    )
    assert dashboard.one_row_material_evidence_fill_package_material_blocker_closed_count == 0
    assert dashboard.one_row_material_evidence_fill_package_checklist_pass_candidate_count == 0
    assert dashboard.one_row_material_evidence_fill_package_remaining_blocked_count == 16
    assert dashboard.one_row_material_evidence_fill_package_clean_review_updates_created is False
    assert dashboard.one_row_material_evidence_fill_package_approval_applied is False

    summary = pd.read_csv(dashboard.artifact_paths["local_research_summary"], dtype=str, keep_default_na=False)
    metadata = json.loads(dashboard.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert summary.iloc[0]["latest_one_row_material_evidence_fill_package_id"] == package.package_id
    assert summary.iloc[0]["one_row_material_evidence_fill_package_target_symbol"] == "000001"
    assert metadata["latest_one_row_material_evidence_fill_package_id"] == package.package_id
    assert metadata["one_row_material_evidence_fill_package_remaining_blocked_count"] == 16
    assert metadata["one_row_material_evidence_fill_package_approval_applied"] is False

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
    assert f"latest_one_row_material_evidence_fill_package_id: {package.package_id}" in output
    assert (
        "one_row_material_evidence_fill_package_stage: "
        "ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_CONTEXT_DRAFTED"
    ) in output
    assert "one_row_material_evidence_fill_package_target_symbol: 000001" in output
    assert "one_row_material_evidence_fill_package_approval_applied: False" in output


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


def _write_one_row_material_evidence_fill_package_audit(tmp_path: Path) -> Path:
    root = tmp_path / "manual_diagnostics" / "one_row_material_evidence_fill_package_audit"
    root.mkdir(parents=True)
    target = {"signal_date": "2024-04-02", "symbol": "000001", "universe_name": "stock_core"}
    fillable = [
        {
            **target,
            "field": "name",
            "candidate_value": "Ping An Bank context",
            "fillable_now": "yes_context",
            "evidence_basis": "official symbol-level context",
            "evidence_strength": "SUPPORTING_OFFICIAL_SYMBOL_LEVEL",
            "approval_safe": "no",
            "notes": "Identity context only.",
        },
        {
            **target,
            "field": "exchange",
            "candidate_value": "SZSE",
            "fillable_now": "yes_context",
            "evidence_basis": "SZSE 1815 quote context",
            "evidence_strength": "STRONG_OFFICIAL_DATE_SPECIFIC_FOR_QUOTATION",
            "approval_safe": "no",
            "notes": "Quote context only.",
        },
        {
            **target,
            "field": "listed_date",
            "candidate_value": "1991-04-03",
            "fillable_now": "yes_context",
            "evidence_basis": "official listing context",
            "evidence_strength": "SUPPORTING_OFFICIAL_SYMBOL_LEVEL",
            "approval_safe": "no",
            "notes": "Listing context only.",
        },
        {
            **target,
            "field": "industry",
            "candidate_value": "banking_official_context",
            "fillable_now": "yes_context",
            "evidence_basis": "official disclosure context",
            "evidence_strength": "CONTEXT_OR_SUPPORTING_SYMBOL_LEVEL",
            "approval_safe": "no",
            "notes": "Reviewer should normalize taxonomy.",
        },
        {
            **target,
            "field": "min_lot",
            "candidate_value": "100",
            "fillable_now": "yes_rule_context",
            "evidence_basis": "SZSE round-lot rule context",
            "evidence_strength": "RULE_CONTEXT",
            "approval_safe": "no",
            "notes": "Rule context only.",
        },
        {
            **target,
            "field": "t_plus_rule",
            "candidate_value": "T+1_rule_context",
            "fillable_now": "yes_rule_context",
            "evidence_basis": "SZSE trading rule context",
            "evidence_strength": "RULE_CONTEXT",
            "approval_safe": "no",
            "notes": "Rule context only.",
        },
        {
            **target,
            "field": "as_of_date",
            "candidate_value": "2024-04-02",
            "fillable_now": "conditional_context",
            "evidence_basis": "SZSE 1815 same-date quotation",
            "evidence_strength": "STRONG_OFFICIAL_DATE_SPECIFIC_FOR_QUOTATION_ONLY",
            "approval_safe": "no",
            "notes": "Quote-observation date only.",
        },
        {
            **target,
            "field": "revision_id",
            "candidate_value": "one_row_material_evidence_fill_package_v0_1_draft",
            "fillable_now": "yes_diagnostics_only",
            "evidence_basis": "diagnostic lineage",
            "evidence_strength": "DIAGNOSTIC_LINEAGE_ONLY",
            "approval_safe": "no",
            "notes": "Not evidence.",
        },
        {
            **target,
            "field": "source",
            "candidate_value": "SZSE_1815_QUOTATION_DIAGNOSTIC;NO_HIT_NEEDS_REVIEW",
            "fillable_now": "yes_lineage_context",
            "evidence_basis": "diagnostic source lineage",
            "evidence_strength": "LINEAGE_CONTEXT",
            "approval_safe": "no",
            "notes": "Not clean review updates.",
        },
    ]
    pd.DataFrame(fillable).to_csv(root / "fillable_field_assessment.csv", index=False)
    pd.DataFrame(
        [
            {
                **target,
                "blocker": "is_active / active-not-delisted evidence",
                "after_candidate_fill_status": "still_blocked",
                "reason": "Quote context is not accepted active/not-delisted policy by itself.",
            },
            {
                **target,
                "blocker": "is_st / no-ST evidence",
                "after_candidate_fill_status": "still_blocked",
                "reason": "No accepted historical no-ST evidence.",
            },
            {
                **target,
                "blocker": "survivorship-bias resolution",
                "after_candidate_fill_status": "still_blocked",
                "reason": "Reviewer rationale still required.",
            },
        ]
    ).to_csv(root / "remaining_blockers_after_candidate_fill.csv", index=False)
    pd.DataFrame(
        [
            {
                **target,
                "claim_or_field": "is_active=true",
                "risk": "Overclaims active/not-delisted status.",
                "safe_treatment": "Keep as traded context only.",
                "severity": "high",
            },
            {
                **target,
                "claim_or_field": "is_st=false",
                "risk": "No accepted no-ST evidence.",
                "safe_treatment": "Keep blocked.",
                "severity": "high",
            },
            {
                **target,
                "claim_or_field": "survivorship_bias_resolved=true",
                "risk": "Would create approval semantics.",
                "safe_treatment": "Keep false.",
                "severity": "critical",
            },
        ]
    ).to_csv(root / "overclaim_risk_matrix.csv", index=False)
    pd.DataFrame(
        [
            {
                **target,
                "judgment_item": "Accept same-date quote as EOD traded context only",
                "required_reviewer_action": "Document policy and limits.",
                "can_be_auto_filled": "no",
                "supporting_artifacts": "SZSE 1815 diagnostics",
            }
        ]
    ).to_csv(root / "reviewer_judgment_needed.csv", index=False)
    pd.DataFrame(
        [
            {
                **target,
                "needed_evidence": "accepted historical no-ST and not-delisted evidence",
                "why_needed": "stock status and active/not-delisted blockers remain",
                "candidate_source": "SZSE/CNInfo no-hit or stronger official source",
                "current_status": "not accepted",
                "blocks_checklist_pass": "yes",
            }
        ]
    ).to_csv(root / "external_evidence_needed.csv", index=False)
    return root


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
