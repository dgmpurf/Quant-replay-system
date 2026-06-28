"""Tiny report-only PIT admissibility validator contract fixture.

This module writes deterministic synthetic contract artifacts for a future PIT
admissibility validator. It does not implement the validator, does not create
real reviewed CSV packages, and does not authorize replay, labels, training,
stock_profile, paper validation, buy-review, performance validation, current
candidates, snapshots, broker/API/order/message behavior, or trading.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED = (
    "TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED"
)

RECOMMENDED_NEXT_TASK = "Tiny PIT Admissibility Validator Contract Fixture Views Report-Only v0.1"

REQUIRED_CASES = [
    "NO_INPUT",
    "PACKAGE_READ_FAILED",
    "PACKAGE_SCHEMA_INVALID",
    "PACKAGE_PIT_BLOCKED_AVAILABLE_TIME",
    "PACKAGE_PIT_BLOCKED_MISSING_SOURCE_HASH",
    "PACKAGE_PIT_BLOCKED_MISSING_REVISION_ID",
    "PACKAGE_PIT_BLOCKED_REVIEW_STATUS",
    "PACKAGE_PIT_BLOCKED_SOURCE_PERMISSION",
    "PACKAGE_PIT_BLOCKED_QUALITY_STATUS",
    "PACKAGE_PIT_BLOCKED_FORWARD_LABEL_LEAKAGE",
    "PACKAGE_REVIEW_REQUIRED",
    "PIT_ADMISSIBILITY_PASS_CANDIDATE",
]

REQUIRED_PACKAGE_SECTIONS = [
    "source_registry_reviewed.csv",
    "raw_document_store_reviewed.csv",
    "factor_definition_reviewed.csv",
    "company_exposure_reviewed.csv",
    "event_structured_reviewed.csv",
    "factor_observation_reviewed.csv",
    "replay_evidence_bundle_reviewed.csv",
    "replay_decision_reviewed.csv",
    "forward_return_label_reviewed.csv",
    "market_data_reviewed.csv",
    "benchmark_data_reviewed.csv",
    "trading_calendar_reviewed.csv",
]

REQUIRED_GATE_GROUPS = [
    "package identity gate",
    "file presence gate",
    "required column gate",
    "source registry reference gate",
    "raw document/reference gate",
    "available_time gate",
    "source_hash gate",
    "revision_id gate",
    "reviewer authority / review status gate",
    "source permission gate",
    "quality status gate",
    "factor definition reference gate",
    "company exposure reference gate",
    "event timing gate",
    "factor observation PIT gate",
    "replay evidence bundle lineage gate",
    "replay decision exclusion gate",
    "forward-label exclusion gate",
    "market data date-window gate",
    "benchmark data date-window gate",
    "trading calendar gate",
    "future leakage gate",
    "forbidden interpretation gate",
    "side-effect safety gate",
]

TIMING_RULES = [
    (
        "replay_decision_time_central_cutoff",
        "replay_decision_time is the future central cutoff.",
        "Package cannot be PIT-admissible without a declared replay_decision_time.",
    ),
    (
        "available_time_lte_replay_decision_time",
        "Every decision-time input must satisfy available_time <= replay_decision_time.",
        "Rows with available_time after replay_decision_time are PIT blocked.",
    ),
    (
        "event_date_not_available_time",
        "event_date is not available_time.",
        "Event dating alone cannot prove the information was decision-time available.",
    ),
    (
        "period_end_not_available_time",
        "period_end is not available_time.",
        "Financial period coverage alone cannot prove historical availability.",
    ),
    (
        "publish_time_not_always_available_time",
        "publish_time is not always available_time.",
        "Publish timestamp needs source-specific availability interpretation.",
    ),
    (
        "fetched_at_after_replay_requires_historical_availability",
        "fetched_at can be after replay date only if historical availability is proven.",
        "Late fetch metadata cannot substitute for point-in-time availability proof.",
    ),
    (
        "reviewed_at_audit_metadata_only",
        "reviewed_at is audit metadata, not historical availability.",
        "Reviewer timestamp cannot backdate information into the replay decision.",
    ),
    (
        "reviewer_approval_no_pit_override",
        "Reviewer approval does not override PIT failure.",
        "A reviewed row remains blocked when availability, lineage, or leakage gates fail.",
    ),
    (
        "future_forward_labels_excluded_from_decision_inputs",
        "Future forward labels cannot be decision-time inputs.",
        "Forward labels are blocked from decision-time package sections.",
    ),
    (
        "future_labels_not_joined_to_decision_or_training",
        "Future labels must not be joined to decision inputs or training datasets at this stage.",
        "Any label join is out of scope for this contract fixture.",
    ),
]

SAFETY_FALSE_FLAGS = [
    "real_reviewed_csv_package_created",
    "active_reviewed_input_candidate_created",
    "pit_admissibility_validator_implemented",
    "real_replay_input_created",
    "real_replay_evidence_bundle_created",
    "real_replay_decision_created",
    "replay_decision_frozen",
    "real_forward_labels_created",
    "future_labels_joined",
    "future_labels_joined_to_decision_inputs",
    "future_labels_joined_to_training_dataset",
    "training_dataset_created",
    "metric_computation_performed",
    "signal_score_implemented",
    "signal_score_input_authorized",
    "model_training_performed",
    "active_weights_created",
    "active_thresholds_created",
    "stock_profile_validation_created",
    "paper_validation_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "tiny_pit_admissibility_validator_contract_fixture_report.md",
    "gate_case_matrix": "gate_case_matrix.csv",
    "package_section_contract": "package_section_contract.csv",
    "output_status_contract": "output_status_contract.csv",
    "pit_timing_rule_matrix": "pit_timing_rule_matrix.csv",
    "forbidden_interpretation_matrix": "forbidden_interpretation_matrix.csv",
    "safety_flags": "safety_flags.json",
    "limitations": "limitations.md",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class TinyPitAdmissibilityValidatorContractFixtureSettings:
    output_dir: Path = Path(
        "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_contract_fixture_v0_1"
    )
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class TinyPitAdmissibilityValidatorContractFixtureResult:
    tiny_pit_admissibility_validator_contract_fixture_id: str
    status: str
    workflow_stage: str
    case_count: int
    package_section_count: int
    gate_group_count: int
    timing_rule_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_tiny_pit_admissibility_validator_contract_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: TinyPitAdmissibilityValidatorContractFixtureSettings | None = None,
) -> TinyPitAdmissibilityValidatorContractFixtureResult:
    resolved_settings = settings or TinyPitAdmissibilityValidatorContractFixtureSettings()
    if output_dir is not None:
        resolved_settings = TinyPitAdmissibilityValidatorContractFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    gate_case_matrix = build_gate_case_matrix()
    package_section_contract = build_package_section_contract()
    output_status_contract = build_output_status_contract()
    pit_timing_rule_matrix = build_pit_timing_rule_matrix()
    forbidden_interpretation_matrix = build_forbidden_interpretation_matrix()
    validation_issue_count = validate_tiny_pit_contract_fixture(
        gate_case_matrix=gate_case_matrix,
        package_section_contract=package_section_contract,
        output_status_contract=output_status_contract,
        pit_timing_rule_matrix=pit_timing_rule_matrix,
        forbidden_interpretation_matrix=forbidden_interpretation_matrix,
        settings=resolved_settings,
    )
    fixture_id = _fixture_id(
        gate_case_matrix=gate_case_matrix,
        package_section_contract=package_section_contract,
        output_status_contract=output_status_contract,
        config_version=resolved_settings.config_version,
    )
    paths = resolve_tiny_pit_admissibility_validator_contract_fixture_paths(
        resolved_settings.output_dir,
        fixture_id,
    )
    result = TinyPitAdmissibilityValidatorContractFixtureResult(
        tiny_pit_admissibility_validator_contract_fixture_id=fixture_id,
        status="PASS" if validation_issue_count == 0 else "FAIL",
        workflow_stage=TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED,
        case_count=len(gate_case_matrix),
        package_section_count=len(package_section_contract),
        gate_group_count=len(REQUIRED_GATE_GROUPS),
        timing_rule_count=len(pit_timing_rule_matrix),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_tiny_pit_admissibility_validator_contract_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            gate_case_matrix=gate_case_matrix,
            package_section_contract=package_section_contract,
            output_status_contract=output_status_contract,
            pit_timing_rule_matrix=pit_timing_rule_matrix,
            forbidden_interpretation_matrix=forbidden_interpretation_matrix,
        )
    return result


def build_gate_case_matrix() -> pd.DataFrame:
    gate_groups_by_case = {
        "NO_INPUT": ["package identity gate", "file presence gate"],
        "PACKAGE_READ_FAILED": ["file presence gate", "required column gate"],
        "PACKAGE_SCHEMA_INVALID": ["required column gate", "source registry reference gate"],
        "PACKAGE_PIT_BLOCKED_AVAILABLE_TIME": ["available_time gate", "event timing gate"],
        "PACKAGE_PIT_BLOCKED_MISSING_SOURCE_HASH": ["source_hash gate", "raw document/reference gate"],
        "PACKAGE_PIT_BLOCKED_MISSING_REVISION_ID": ["revision_id gate", "factor definition reference gate"],
        "PACKAGE_PIT_BLOCKED_REVIEW_STATUS": ["reviewer authority / review status gate"],
        "PACKAGE_PIT_BLOCKED_SOURCE_PERMISSION": ["source permission gate"],
        "PACKAGE_PIT_BLOCKED_QUALITY_STATUS": ["quality status gate"],
        "PACKAGE_PIT_BLOCKED_FORWARD_LABEL_LEAKAGE": [
            "forward-label exclusion gate",
            "future leakage gate",
        ],
        "PACKAGE_REVIEW_REQUIRED": [
            "company exposure reference gate",
            "factor observation PIT gate",
            "replay evidence bundle lineage gate",
            "replay decision exclusion gate",
            "market data date-window gate",
            "benchmark data date-window gate",
            "trading calendar gate",
            "forbidden interpretation gate",
            "side-effect safety gate",
        ],
        "PIT_ADMISSIBILITY_PASS_CANDIDATE": [
            "package identity gate",
            "file presence gate",
            "required column gate",
            "source registry reference gate",
            "raw document/reference gate",
            "available_time gate",
            "source_hash gate",
            "revision_id gate",
            "reviewer authority / review status gate",
            "source permission gate",
            "quality status gate",
            "factor definition reference gate",
            "company exposure reference gate",
            "event timing gate",
            "factor observation PIT gate",
            "replay evidence bundle lineage gate",
            "replay decision exclusion gate",
            "forward-label exclusion gate",
            "market data date-window gate",
            "benchmark data date-window gate",
            "trading calendar gate",
            "future leakage gate",
            "forbidden interpretation gate",
            "side-effect safety gate",
        ],
    }
    rows = []
    for case_name in REQUIRED_CASES:
        is_pass_candidate = case_name == "PIT_ADMISSIBILITY_PASS_CANDIDATE"
        rows.append(
            {
                "case_name": case_name,
                "expected_runtime_status": "PASS_CANDIDATE" if is_pass_candidate else "BLOCKED_OR_REVIEW_REQUIRED",
                "gate_groups": ";".join(gate_groups_by_case[case_name]),
                "pass_candidate_allowed": str(is_pass_candidate),
                "active_ready_allowed": "False",
                "blocker_reason": "None for synthetic pass-candidate contract." if is_pass_candidate else case_name,
                "notes": "Synthetic contract case only; no package is read and no validator is implemented.",
            }
        )
    return pd.DataFrame(rows)


def build_package_section_contract() -> pd.DataFrame:
    decision_time_inputs = {
        "source_registry_reviewed.csv",
        "raw_document_store_reviewed.csv",
        "factor_definition_reviewed.csv",
        "company_exposure_reviewed.csv",
        "event_structured_reviewed.csv",
        "factor_observation_reviewed.csv",
        "replay_evidence_bundle_reviewed.csv",
        "replay_decision_reviewed.csv",
        "market_data_reviewed.csv",
        "benchmark_data_reviewed.csv",
        "trading_calendar_reviewed.csv",
    }
    rows = []
    for section_name in REQUIRED_PACKAGE_SECTIONS:
        is_forward_label = section_name == "forward_return_label_reviewed.csv"
        rows.append(
            {
                "section_name": section_name,
                "required_for_future_package": "True",
                "decision_time_input": str(section_name in decision_time_inputs and not is_forward_label),
                "must_satisfy_pit": "True",
                "required_lineage_fields": "source_hash;revision_id;available_time;review_status;quality_status",
                "forbidden_interpretation": (
                    "Future label context only; blocked as decision-time input."
                    if is_forward_label
                    else "Contract section only; not a real reviewed CSV package."
                ),
                "notes": "Synthetic schema contract row; no real CSV is created or read.",
            }
        )
    return pd.DataFrame(rows)


def build_output_status_contract() -> pd.DataFrame:
    statuses = [
        ("NO_INPUT", "No reviewed input package reference was supplied."),
        ("PACKAGE_READ_FAILED", "A future package could not be read."),
        ("PACKAGE_SCHEMA_INVALID", "A future package is missing required structure."),
        ("PACKAGE_PIT_BLOCKED", "A future package violates PIT or lineage gates."),
        ("PACKAGE_REVIEW_REQUIRED", "A future package needs reviewer confirmation."),
        ("PIT_ADMISSIBILITY_PASS_CANDIDATE", "A future package appears reviewable as a pass-candidate only."),
    ]
    return pd.DataFrame(
        [
            {
                "status_name": status_name,
                "meaning": meaning,
                "runtime_status": "PASS" if status_name == "PIT_ADMISSIBILITY_PASS_CANDIDATE" else "WARN",
                "active_replay_input_allowed": "False",
                "labels_allowed": "False",
                "training_allowed": "False",
                "stock_profile_allowed": "False",
                "buy_review_allowed": "False",
                "trading_allowed": "False",
                "notes": "Future status contract only; this fixture emits PASS for artifact creation.",
            }
            for status_name, meaning in statuses
        ]
    )


def build_pit_timing_rule_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timing_rule_id": rule_id,
                "required": "True",
                "rule_text": rule_text,
                "blocker_if_violated": blocker,
                "notes": "Contract rule only; no real temporal validation is executed.",
            }
            for rule_id, rule_text, blocker in TIMING_RULES
        ]
    )


def build_forbidden_interpretation_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "forbidden_interpretation": flag,
                "must_remain_false": "True",
                "failure_if_true": "Fixture boundary violation.",
                "notes": "This contract fixture must not claim this side effect or downstream readiness.",
            }
            for flag in SAFETY_FALSE_FLAGS
        ]
    )


def validate_tiny_pit_contract_fixture(
    *,
    gate_case_matrix: pd.DataFrame,
    package_section_contract: pd.DataFrame,
    output_status_contract: pd.DataFrame,
    pit_timing_rule_matrix: pd.DataFrame,
    forbidden_interpretation_matrix: pd.DataFrame,
    settings: TinyPitAdmissibilityValidatorContractFixtureSettings,
) -> int:
    issues = 0
    if not settings.report_only or not settings.diagnostic_only:
        issues += 1
    if set(gate_case_matrix["case_name"]) != set(REQUIRED_CASES):
        issues += 1
    observed_gate_groups = {
        part.strip()
        for value in gate_case_matrix["gate_groups"]
        for part in str(value).split(";")
        if part.strip()
    }
    if observed_gate_groups != set(REQUIRED_GATE_GROUPS):
        issues += 1
    if set(package_section_contract["section_name"]) != set(REQUIRED_PACKAGE_SECTIONS):
        issues += 1
    if len(pit_timing_rule_matrix) != len(TIMING_RULES):
        issues += 1
    if set(forbidden_interpretation_matrix["forbidden_interpretation"]) != set(SAFETY_FALSE_FLAGS):
        issues += 1
    forbidden_statuses = {
        "ACTIVE_REPLAY_INPUT_READY",
        "REAL_REPLAY_READY",
        "FORWARD_LABEL_READY",
        "TRAINING_READY",
        "STOCK_PROFILE_READY",
        "BUY_REVIEW_READY",
    }
    if forbidden_statuses.intersection(set(output_status_contract["status_name"])):
        issues += 1
    return issues


def resolve_tiny_pit_admissibility_validator_contract_fixture_paths(
    output_dir: str | Path,
    fixture_id: str,
) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / fixture_id
    paths = {"artifact_dir": artifact_dir}
    paths.update({key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()})
    return paths


def write_tiny_pit_admissibility_validator_contract_fixture_artifacts(
    *,
    result: TinyPitAdmissibilityValidatorContractFixtureResult,
    settings: TinyPitAdmissibilityValidatorContractFixtureSettings,
    gate_case_matrix: pd.DataFrame,
    package_section_contract: pd.DataFrame,
    output_status_contract: pd.DataFrame,
    pit_timing_rule_matrix: pd.DataFrame,
    forbidden_interpretation_matrix: pd.DataFrame,
) -> None:
    del settings
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    gate_case_matrix.to_csv(result.artifact_paths["gate_case_matrix"], index=False)
    package_section_contract.to_csv(result.artifact_paths["package_section_contract"], index=False)
    output_status_contract.to_csv(result.artifact_paths["output_status_contract"], index=False)
    pit_timing_rule_matrix.to_csv(result.artifact_paths["pit_timing_rule_matrix"], index=False)
    forbidden_interpretation_matrix.to_csv(result.artifact_paths["forbidden_interpretation_matrix"], index=False)
    safety_flags = {flag: False for flag in SAFETY_FALSE_FLAGS}
    result.artifact_paths["safety_flags"].write_text(
        json.dumps(safety_flags, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result.artifact_paths["metadata"].write_text(
        json.dumps(
            _metadata_payload(result=result, safety_flags=safety_flags),
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    result.artifact_paths["report"].write_text(_report_text(result), encoding="utf-8")
    result.artifact_paths["limitations"].write_text(_limitations_text(), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(
        f"# Recommended Next Task\n\n{RECOMMENDED_NEXT_TASK}\n",
        encoding="utf-8",
    )


def _metadata_payload(
    *,
    result: TinyPitAdmissibilityValidatorContractFixtureResult,
    safety_flags: dict[str, bool],
) -> dict[str, Any]:
    return {
        "workflow_name": "tiny_pit_admissibility_validator_contract_fixture",
        "tiny_pit_admissibility_validator_contract_fixture_id": (
            result.tiny_pit_admissibility_validator_contract_fixture_id
        ),
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "case_count": result.case_count,
        "package_section_count": result.package_section_count,
        "gate_group_count": result.gate_group_count,
        "timing_rule_count": result.timing_rule_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "contract_fixture": True,
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        **safety_flags,
    }


def _report_text(result: TinyPitAdmissibilityValidatorContractFixtureResult) -> str:
    return f"""# Tiny PIT Admissibility Validator Contract Fixture

status: {result.status}

workflow_stage: {result.workflow_stage}

fixture_id: {result.tiny_pit_admissibility_validator_contract_fixture_id}

This diagnostics-only fixture defines a tiny synthetic contract for a future PIT
admissibility validator. No real reviewed CSV package is created.
No PIT admissibility validator is implemented. No active reviewed input candidate,
replay input, evidence bundle, replay decision, freeze, forward labels, training
dataset, metric computation, signal_score, model training, active weights,
active thresholds, stock_profile validation, paper validation, buy-review,
strategy performance validation, current-candidates, snapshots, signal_semantics
changes, broker/API/order/message behavior, trading, or data/raw,
data/processed, or data/cache writes are created.

The fixture records {result.case_count} synthetic gate cases,
{result.package_section_count} package sections, {result.gate_group_count} gate
groups, and {result.timing_rule_count} PIT timing rules.
"""


def _limitations_text() -> str:
    return """# Limitations

This is a contract fixture only. It does not read a reviewed package and does
not validate any real package rows.

replay_decision_time is only documented as a future central cutoff.

event_date is not available_time.

period_end is not available_time.

publish_time is not always available_time.

fetched_at can be after the replay date only if historical availability is
separately proven.

reviewed_at is audit metadata, not historical availability.

reviewer approval does not override PIT failure.

Future forward labels cannot be decision-time inputs and must not be joined to
decision inputs or training datasets at this stage.
"""


def _fixture_id(
    *,
    gate_case_matrix: pd.DataFrame,
    package_section_contract: pd.DataFrame,
    output_status_contract: pd.DataFrame,
    config_version: str,
) -> str:
    payload = {
        "config_version": config_version,
        "cases": gate_case_matrix.to_dict(orient="records"),
        "sections": package_section_contract.to_dict(orient="records"),
        "statuses": output_status_contract.to_dict(orient="records"),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]


def _assert_settings_safe(settings: TinyPitAdmissibilityValidatorContractFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Tiny PIT admissibility validator contract fixture must remain report-only diagnostics.")
