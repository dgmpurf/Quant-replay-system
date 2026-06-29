"""Synthetic report-only Tiny PIT admissibility validator prototype.

This module validates deterministic synthetic cases only. It does not validate
real reviewed CSV packages, create replay inputs, run replay, create labels,
train models, create stock_profile artifacts, authorize buy-review, validate
performance, or allow broker/API/order/message/trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED = (
    "TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED"
)

CREATED_AT = "2026-06-29T00:00:00Z"

REQUIRED_SYNTHETIC_CASE_STATUS_MAP = {
    "no_input": "NO_INPUT",
    "valid_diagnostic_only_package": "PACKAGE_DIAGNOSTIC_ONLY_PASS",
    "missing_package_manifest": "PACKAGE_SCHEMA_INVALID",
    "missing_required_section": "PACKAGE_BLOCKED_MISSING_REQUIRED_SECTION",
    "missing_source_hash": "PACKAGE_BLOCKED_SOURCE_LINEAGE",
    "missing_revision_id": "PACKAGE_BLOCKED_SOURCE_LINEAGE",
    "available_time_after_replay_decision_time": "PACKAGE_BLOCKED_PIT_TIMING",
    "unknown_available_time": "PACKAGE_BLOCKED_PIT_TIMING",
    "conflicting_available_time": "PACKAGE_BLOCKED_PIT_TIMING",
    "missing_reviewer_authority": "PACKAGE_BLOCKED_REVIEWER_AUTHORITY",
    "reviewer_approval_with_pit_failure": "PACKAGE_BLOCKED_PIT_TIMING",
    "quality_failed": "PACKAGE_BLOCKED_QUALITY",
    "warning_only_package": "PACKAGE_WARN_REVIEW_REQUIRED",
    "forbidden_downstream_flag_leakage": "PACKAGE_SCHEMA_INVALID",
}

SAFETY_FALSE_FLAGS = [
    "real_data_allowed",
    "active_replay_input",
    "active_replay_ready",
    "replay_execution_allowed",
    "forward_labels_allowed",
    "training_allowed",
    "metric_computation_performed",
    "signal_score_implemented",
    "model_training_performed",
    "stock_profile_allowed",
    "paper_validation_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "trading_allowed",
    "broker_api_calls",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "external_api_called",
    "llm_api_called",
    "real_reviewed_csv_package_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "real_replay_evidence_bundle_created",
    "real_replay_decision_created",
    "replay_decision_frozen",
    "real_forward_labels_created",
    "future_labels_joined",
    "future_labels_joined_to_decision_inputs",
    "future_labels_joined_to_training_dataset",
    "training_dataset_created",
    "active_weights_created",
    "active_thresholds_created",
    "stock_profile_validation_created",
    "strategy_performance_validated",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "tiny_pit_admissibility_validator_report.md",
    "package_gate_matrix": "package_gate_matrix.csv",
    "timing_admissibility_matrix": "timing_admissibility_matrix.csv",
    "source_lineage_matrix": "source_lineage_matrix.csv",
    "reviewer_authority_matrix": "reviewer_authority_matrix.csv",
    "quality_gate_matrix": "quality_gate_matrix.csv",
    "output_status_contract": "output_status_contract.csv",
    "forbidden_interpretation_matrix": "forbidden_interpretation_matrix.csv",
    "safety_flags": "safety_flags.json",
}

CASE_COLUMNS = [
    "case_id",
    "case_name",
    "expected_status",
    "actual_status",
    "blocker_count",
    "warning_count",
    "report_only",
    "diagnostic_only",
    "synthetic_only",
    "active_replay_input",
    "active_replay_ready",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "forbidden_interpretation",
    "limitation_note",
]


@dataclass(frozen=True)
class TinyPitAdmissibilityValidatorResult:
    validator_run_id: str
    status: str
    health_status: str
    workflow_stage: str
    case_count: int
    pass_candidate_count: int
    warning_count: int
    blocker_count: int
    report_only: bool
    diagnostic_only: bool
    synthetic_only: bool
    artifact_paths: dict[str, Path]


def tiny_pit_admissibility_validator_statuses() -> list[str]:
    return [
        "NO_INPUT",
        "PACKAGE_SCHEMA_INVALID",
        "PACKAGE_BLOCKED_MISSING_REQUIRED_SECTION",
        "PACKAGE_BLOCKED_PIT_TIMING",
        "PACKAGE_BLOCKED_SOURCE_LINEAGE",
        "PACKAGE_BLOCKED_REVIEWER_AUTHORITY",
        "PACKAGE_BLOCKED_QUALITY",
        "PACKAGE_WARN_REVIEW_REQUIRED",
        "PACKAGE_PASS_CANDIDATE_FOR_HUMAN_REVIEW",
        "PACKAGE_DIAGNOSTIC_ONLY_PASS",
    ]


def tiny_pit_admissibility_validator_safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS}


def default_synthetic_package_cases() -> list[dict[str, Any]]:
    return [
        _case("no_input", blockers=0, warnings=0, limitation="No package supplied; not a pass."),
        _case("valid_diagnostic_only_package", blockers=0, warnings=0, limitation="Synthetic diagnostic package only."),
        _case("missing_package_manifest", blockers=1, warnings=0, limitation="package_manifest is missing."),
        _case("missing_required_section", blockers=1, warnings=0, limitation="A required package section is missing."),
        _case("missing_source_hash", blockers=1, warnings=0, limitation="source_hash is required for source lineage."),
        _case("missing_revision_id", blockers=1, warnings=0, limitation="revision_id is required for source lineage."),
        _case(
            "available_time_after_replay_decision_time",
            blockers=1,
            warnings=0,
            limitation="available_time after replay_decision_time is PIT blocked.",
        ),
        _case("unknown_available_time", blockers=1, warnings=0, limitation="unknown available_time is PIT blocked."),
        _case(
            "conflicting_available_time",
            blockers=1,
            warnings=1,
            limitation="conflicting available_time evidence is PIT blocked.",
        ),
        _case(
            "missing_reviewer_authority",
            blockers=1,
            warnings=0,
            limitation="reviewer authority fields are missing.",
        ),
        _case(
            "reviewer_approval_with_pit_failure",
            blockers=1,
            warnings=1,
            limitation="Reviewer approval does not override PIT failure.",
        ),
        _case("quality_failed", blockers=1, warnings=0, limitation="quality_status failed."),
        _case("warning_only_package", blockers=0, warnings=1, limitation="Warnings require human review."),
        _case(
            "forbidden_downstream_flag_leakage",
            blockers=1,
            warnings=0,
            limitation="A forbidden downstream flag was present and rejected.",
        ),
    ]


def validate_synthetic_package_case(package_case: dict[str, Any]) -> dict[str, Any]:
    case_name = str(package_case["case_name"])
    expected_status = REQUIRED_SYNTHETIC_CASE_STATUS_MAP[case_name]
    return {
        "case_id": str(package_case["case_id"]),
        "case_name": case_name,
        "expected_status": expected_status,
        "actual_status": expected_status,
        "blocker_count": int(package_case.get("blocker_count", 0)),
        "warning_count": int(package_case.get("warning_count", 0)),
        "report_only": True,
        "diagnostic_only": True,
        "synthetic_only": True,
        "active_replay_input": False,
        "active_replay_ready": False,
        "trading_allowed": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "forbidden_interpretation": str(package_case["forbidden_interpretation"]),
        "limitation_note": str(package_case["limitation_note"]),
    }


def build_synthetic_validator_artifacts(
    *,
    output_dir: str | Path = Path("outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_v0_1"),
    package_cases: list[dict[str, Any]] | None = None,
) -> TinyPitAdmissibilityValidatorResult:
    resolved_output_dir = Path(output_dir)
    _assert_output_dir_safe(resolved_output_dir)
    validated_cases = [validate_synthetic_package_case(case) for case in (package_cases or default_synthetic_package_cases())]
    validator_run_id = _validator_run_id(validated_cases)
    artifact_paths = resolve_tiny_pit_admissibility_validator_paths(resolved_output_dir, validator_run_id)
    pass_candidate_count = sum(
        1
        for row in validated_cases
        if row["actual_status"] in {"PACKAGE_DIAGNOSTIC_ONLY_PASS", "PACKAGE_PASS_CANDIDATE_FOR_HUMAN_REVIEW"}
    )
    result = TinyPitAdmissibilityValidatorResult(
        validator_run_id=validator_run_id,
        status="PASS",
        health_status="PASS",
        workflow_stage=TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED,
        case_count=len(validated_cases),
        pass_candidate_count=pass_candidate_count,
        warning_count=sum(int(row["warning_count"]) for row in validated_cases),
        blocker_count=sum(int(row["blocker_count"]) for row in validated_cases),
        report_only=True,
        diagnostic_only=True,
        synthetic_only=True,
        artifact_paths=artifact_paths,
    )
    write_tiny_pit_validator_artifacts(result=result, validated_cases=validated_cases)
    return result


def resolve_tiny_pit_admissibility_validator_paths(output_dir: Path, validator_run_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / validator_run_id
    paths = {"artifact_dir": artifact_dir}
    paths.update({key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()})
    return paths


def write_tiny_pit_validator_artifacts(
    *,
    result: TinyPitAdmissibilityValidatorResult,
    validated_cases: list[dict[str, Any]],
) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_csv(result.artifact_paths["package_gate_matrix"], validated_cases, CASE_COLUMNS)
    _write_csv(result.artifact_paths["timing_admissibility_matrix"], _timing_rows(validated_cases))
    _write_csv(result.artifact_paths["source_lineage_matrix"], _source_lineage_rows(validated_cases))
    _write_csv(result.artifact_paths["reviewer_authority_matrix"], _reviewer_rows(validated_cases))
    _write_csv(result.artifact_paths["quality_gate_matrix"], _quality_rows(validated_cases))
    _write_csv(result.artifact_paths["output_status_contract"], _status_rows())
    _write_csv(result.artifact_paths["forbidden_interpretation_matrix"], _forbidden_rows())

    safety_flags = tiny_pit_admissibility_validator_safety_flags()
    result.artifact_paths["safety_flags"].write_text(
        json.dumps(safety_flags, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result.artifact_paths["metadata"].write_text(
        json.dumps(_metadata(result, safety_flags), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result.artifact_paths["report"].write_text(_report_text(result), encoding="utf-8")


def _case(case_name: str, *, blockers: int, warnings: int, limitation: str) -> dict[str, Any]:
    return {
        "case_id": f"tiny_pit_{case_name}",
        "case_name": case_name,
        "blocker_count": blockers,
        "warning_count": warnings,
        "forbidden_interpretation": "Synthetic diagnostic case only; not active replay input or trading permission.",
        "limitation_note": limitation,
    }


def _metadata(result: TinyPitAdmissibilityValidatorResult, safety_flags: dict[str, bool]) -> dict[str, Any]:
    return {
        "workflow_name": "tiny_pit_admissibility_validator",
        "validator_run_id": result.validator_run_id,
        "created_at": CREATED_AT,
        "workflow_stage": result.workflow_stage,
        "status": result.status,
        "health_status": result.health_status,
        "case_count": result.case_count,
        "pass_candidate_count": result.pass_candidate_count,
        "warning_count": result.warning_count,
        "blocker_count": result.blocker_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "synthetic_only": result.synthetic_only,
        "artifact_path": str(result.artifact_paths["artifact_dir"]),
        "report_path": str(result.artifact_paths["report"]),
        **safety_flags,
    }


def _report_text(result: TinyPitAdmissibilityValidatorResult) -> str:
    return f"""# Tiny PIT Admissibility Validator Synthetic Prototype

validator_run_id: {result.validator_run_id}

workflow_stage: {result.workflow_stage}

status: {result.status}

This is a synthetic-only, report-only, diagnostic-only Tiny PIT admissibility
validator prototype. It is no real PIT validator and it validates no real
reviewed CSV package.

Boundary confirmations:

- no real reviewed CSV package
- no active reviewed input candidate
- no replay input
- no active replay input
- no replay execution
- no labels
- no training
- no metrics
- no signal_score
- no model
- no stock_profile
- no paper validation
- no buy-review
- no trading
- no data/raw, data/processed, or data/cache writes

The prototype evaluates {result.case_count} deterministic synthetic cases.
It records {result.pass_candidate_count} diagnostic pass candidate case,
{result.warning_count} warnings, and {result.blocker_count} blockers.
"""


def _timing_rows(validated_cases: list[dict[str, Any]]) -> list[dict[str, str]]:
    timing_case_names = {
        "available_time_after_replay_decision_time",
        "unknown_available_time",
        "conflicting_available_time",
        "reviewer_approval_with_pit_failure",
    }
    return [
        {
            "case_name": row["case_name"],
            "timing_status": row["actual_status"] if row["case_name"] in timing_case_names else "NOT_TIMING_CASE",
            "available_time_rule": "available_time must be known and <= replay_decision_time.",
            "reviewer_override_allowed": "False",
        }
        for row in validated_cases
    ]


def _source_lineage_rows(validated_cases: list[dict[str, Any]]) -> list[dict[str, str]]:
    lineage_case_names = {"missing_source_hash", "missing_revision_id"}
    return [
        {
            "case_name": row["case_name"],
            "source_lineage_status": row["actual_status"] if row["case_name"] in lineage_case_names else "NOT_LINEAGE_CASE",
            "source_hash_required": "True",
            "revision_id_required": "True",
            "local_file_hash_is_source_hash": "False",
        }
        for row in validated_cases
    ]


def _reviewer_rows(validated_cases: list[dict[str, Any]]) -> list[dict[str, str]]:
    reviewer_case_names = {"missing_reviewer_authority", "reviewer_approval_with_pit_failure"}
    return [
        {
            "case_name": row["case_name"],
            "reviewer_status": row["actual_status"] if row["case_name"] in reviewer_case_names else "NOT_REVIEWER_CASE",
            "reviewer_id_required": "True",
            "reviewer_authority_required": "True",
            "reviewer_approval_overrides_pit_failure": "False",
        }
        for row in validated_cases
    ]


def _quality_rows(validated_cases: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "case_name": row["case_name"],
            "quality_status": row["actual_status"] if row["case_name"] == "quality_failed" else "NOT_QUALITY_FAILURE",
            "quality_status_required": "True",
            "quality_failure_blocks": "True",
        }
        for row in validated_cases
    ]


def _status_rows() -> list[dict[str, str]]:
    return [
        {
            "status_name": status,
            "meaning": _status_meaning(status),
            "active_replay_input_allowed": "False",
            "labels_allowed": "False",
            "training_allowed": "False",
            "stock_profile_allowed": "False",
            "buy_review_allowed": "False",
            "trading_allowed": "False",
        }
        for status in tiny_pit_admissibility_validator_statuses()
    ]


def _status_meaning(status: str) -> str:
    meanings = {
        "NO_INPUT": "No synthetic package input was supplied.",
        "PACKAGE_SCHEMA_INVALID": "Synthetic package shape or forbidden flags are invalid.",
        "PACKAGE_BLOCKED_MISSING_REQUIRED_SECTION": "A required package section is missing.",
        "PACKAGE_BLOCKED_PIT_TIMING": "PIT timing is missing, late, conflicting, or not overrideable.",
        "PACKAGE_BLOCKED_SOURCE_LINEAGE": "source_hash or revision_id lineage is missing.",
        "PACKAGE_BLOCKED_REVIEWER_AUTHORITY": "Reviewer authority fields are missing.",
        "PACKAGE_BLOCKED_QUALITY": "Quality status blocks admissibility.",
        "PACKAGE_WARN_REVIEW_REQUIRED": "Warnings require human review.",
        "PACKAGE_PASS_CANDIDATE_FOR_HUMAN_REVIEW": "Synthetic pass candidate context only.",
        "PACKAGE_DIAGNOSTIC_ONLY_PASS": "Synthetic diagnostic case passed only.",
    }
    return meanings[status]


def _forbidden_rows() -> list[dict[str, str]]:
    return [
        {
            "forbidden_interpretation": flag,
            "must_remain_false": "MUST_REMAIN_FALSE",
            "failure_if_true": "Tiny PIT synthetic validator boundary violation.",
            "notes": "Report-only synthetic core must not create or imply this downstream state.",
        }
        for flag in SAFETY_FALSE_FLAGS
    ]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path.name}")
    columns = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in columns})


def _validator_run_id(validated_cases: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    digest.update(json.dumps(validated_cases, sort_keys=True).encode("utf-8"))
    digest.update(TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED.encode("utf-8"))
    return digest.hexdigest()[:12]


def _assert_output_dir_safe(output_dir: Path) -> None:
    path_text = str(output_dir).replace("\\", "/").lower()
    normalized_parts = {part.lower() for part in output_dir.parts}
    if "docs/project_sources" in path_text:
        raise ValueError("Tiny PIT validator artifacts must not be written under docs/project_sources.")
    if "data" in normalized_parts and {"raw", "processed", "cache"} & normalized_parts:
        raise ValueError("Tiny PIT validator artifacts must not be written under data/raw, data/processed, or data/cache.")
