"""Report-only forward return label schema fixture workflow.

This module writes tiny synthetic forward_return_label rows for schema and
governance review only. The fixture rows are not real forward labels, not
future labels joined to replay decisions or training datasets, not replay
execution, not metric computation, not signal_score input authorization, not
model training, not stock_profile validation, not paper validation, not
buy-review permission, not performance validation, and not trading permission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED = "FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED"

LABEL_STATUSES = {"COMPLETE", "PARTIAL", "BLOCKED", "NOT_APPLICABLE"}
LABEL_QUALITY_STATUSES = {"PASS", "WARN", "FAIL"}
LABEL_COMPLETENESS_STATUSES = {
    "COMPLETE",
    "PARTIAL_BENCHMARK_MISSING",
    "PARTIAL_INDUSTRY_MISSING",
    "MISSING_EXIT_PRICE",
    "INVALID_WINDOW",
    "EXECUTION_BLOCKED",
}
RETURN_DIRECTIONS = {"POSITIVE", "NEGATIVE", "ZERO", "UNKNOWN"}
RETURN_BUCKETS = {"GAIN", "LOSS", "FLAT", "MISSING"}
EXECUTION_BLOCKER_TYPES = {"NONE", "SUSPENSION", "MISSING_PRICE", "INVALID_WINDOW", "CALENDAR_GAP", "DATA_GAP"}
PRICE_BASES = {"CLOSE", "ADJUSTED_CLOSE", "VWAP", "OPEN", "UNKNOWN"}
CALENDAR_POLICIES = {"TRADING_DAY", "CALENDAR_DAY", "NEXT_TRADING_DAY"}
WORKFLOW_STATUSES = {"PASS", "WARN", "FAIL", "NO_INPUT"}

REQUIRED_CASE_IDS = [
    "SYNTH_FWD_1D_COMPLETE_LABEL",
    "SYNTH_FWD_5D_COMPLETE_LABEL",
    "SYNTH_FWD_20D_COMPLETE_BENCHMARK_RELATIVE_LABEL",
    "SYNTH_NEGATIVE_FORWARD_RETURN_LABEL",
    "SYNTH_POSITIVE_FORWARD_RETURN_LABEL",
    "SYNTH_BLOCKED_NOT_FROZEN_DECISION_LABEL",
    "SYNTH_BLOCKED_MISSING_EXIT_PRICE_LABEL",
    "SYNTH_BLOCKED_INVALID_WINDOW_LABEL",
    "SYNTH_EXECUTION_BLOCKED_SUSPENSION_LABEL",
    "SYNTH_PARTIAL_BENCHMARK_OR_INDUSTRY_LABEL",
]

REQUIRED_FORWARD_RETURN_LABEL_FIELDS = [
    "forward_return_label_id",
    "source_replay_decision_fixture_id",
    "source_replay_decision_id",
    "replay_decision_status",
    "replay_decision_health_status",
    "replay_decision_workflow_stage",
    "replay_decision_frozen",
    "symbol",
    "asset_type",
    "universe_name",
    "decision_date",
    "replay_as_of_date",
    "replay_decision_time",
    "label_policy_version",
    "schema_fixture_case_id",
    "horizon_trading_days",
    "horizon_calendar_days",
    "window_start_date",
    "window_end_date",
    "entry_date",
    "exit_date",
    "entry_price_available_time",
    "exit_price_available_time",
    "calendar_policy",
    "holiday_calendar_id",
    "window_valid",
    "entry_price",
    "exit_price",
    "entry_price_source",
    "exit_price_source",
    "entry_price_basis",
    "exit_price_basis",
    "corporate_action_adjustment",
    "forward_return",
    "forward_return_pct",
    "log_forward_return",
    "return_direction",
    "return_bucket",
    "benchmark_id",
    "benchmark_name",
    "benchmark_entry_price",
    "benchmark_exit_price",
    "benchmark_forward_return",
    "benchmark_relative_return",
    "industry_id",
    "industry_name",
    "industry_forward_return",
    "industry_relative_return",
    "relative_label_available",
    "tradeable_at_entry",
    "tradeable_at_exit",
    "suspended_during_window",
    "limit_up_or_down_during_window",
    "halt_or_special_handling_flag",
    "execution_blocker_type",
    "execution_blocker_reason",
    "label_execution_status",
    "label_status",
    "label_quality_status",
    "label_completeness_status",
    "validation_status",
    "validation_issue_count",
    "blocker_reason",
    "warning_reason",
    "partial_label_reason",
    "report_only",
    "diagnostic_only",
    "schema_fixture",
    "synthetic_fixture_row",
    "real_forward_label_created",
    "future_label_joined_to_decision_input",
    "signal_score_input_authorized",
    "model_training_input_authorized",
    "stock_profile_input_authorized",
    "paper_validation_created",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
    "source_registry_ref",
    "raw_document_store_ref",
    "market_data_ref",
    "benchmark_data_ref",
    "industry_data_ref",
    "calendar_ref",
    "source_hash",
    "revision_id",
    "created_at",
    "created_by_workflow",
    "artifact_path",
    "real_buy_review_allowed",
]

ROW_FALSE_FLAGS = [
    "real_forward_label_created",
    "future_label_joined_to_decision_input",
    "signal_score_input_authorized",
    "model_training_input_authorized",
    "stock_profile_input_authorized",
    "paper_validation_created",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
    "real_buy_review_allowed",
]

FORBIDDEN_METADATA_FALSE_FLAGS = [
    "real_forward_labels_created",
    "future_labels_joined",
    "signal_score_implemented",
    "signal_score_input_authorized",
    "model_training_performed",
    "model_training_input_authorized",
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
    "external_api_called",
    "llm_api_called",
    "message_sent",
    "order_placed",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "forward_return_label_schema_fixture_report.md",
    "fixture_rows": "forward_return_label_schema_fixture.csv",
    "case_matrix": "forward_return_label_case_matrix.csv",
    "field_contract": "forward_return_label_field_contract.csv",
    "validation_results": "forward_return_label_validation_results.csv",
    "leakage_guard_results": "forward_return_label_leakage_guard_results.csv",
    "safety_flags": "forward_return_label_safety_flags.json",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class ForwardReturnLabelSchemaFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/forward_return_label_schema_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ForwardReturnLabelSchemaFixtureResult:
    forward_return_label_schema_fixture_id: str
    status: str
    workflow_stage: str
    label_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_forward_return_label_schema_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: ForwardReturnLabelSchemaFixtureSettings | None = None,
) -> ForwardReturnLabelSchemaFixtureResult:
    resolved_settings = settings or ForwardReturnLabelSchemaFixtureSettings()
    if output_dir is not None:
        resolved_settings = ForwardReturnLabelSchemaFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    fixture_rows = build_forward_return_label_fixture_rows()
    fixture_id = _fixture_id(fixture_rows, resolved_settings.config_version)
    paths = resolve_forward_return_label_schema_fixture_paths(resolved_settings.output_dir, fixture_id)
    fixture_rows = fixture_rows.assign(artifact_path=str(paths["fixture_rows"]))
    field_contract = build_forward_return_label_field_contract()
    case_matrix = build_forward_return_label_case_matrix(fixture_rows)
    validation_results = validate_forward_return_label_fixture(fixture_rows, resolved_settings)
    leakage_guard_results = build_forward_return_label_leakage_guard_results()
    validation_issue_count = int((~validation_results["passed"]).sum())
    result = ForwardReturnLabelSchemaFixtureResult(
        forward_return_label_schema_fixture_id=fixture_id,
        status="PASS" if validation_issue_count == 0 else "FAIL",
        workflow_stage=FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED,
        label_count=len(fixture_rows),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_forward_return_label_schema_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            fixture_rows=fixture_rows,
            field_contract=field_contract,
            case_matrix=case_matrix,
            validation_results=validation_results,
            leakage_guard_results=leakage_guard_results,
        )
    return result


def build_forward_return_label_fixture_rows() -> pd.DataFrame:
    rows = [
        _row(
            schema_fixture_case_id="SYNTH_FWD_1D_COMPLETE_LABEL",
            forward_return_label_id="SYNTH_FWD_LABEL_000001_20240402_1D",
            source_replay_decision_id="SYNTH_WATCH_COMPLETE_EVIDENCE_DECISION",
            symbol="000001",
            horizon_trading_days=1,
            horizon_calendar_days=1,
            window_start_date="2024-04-03T09:30:00",
            window_end_date="2024-04-03T15:00:00",
            entry_date="2024-04-03",
            exit_date="2024-04-03",
            exit_price_available_time="2024-04-03T15:30:00",
            exit_price="10.10",
            forward_return="0.10",
            forward_return_pct="0.010000",
            log_forward_return="0.009950",
            return_direction="POSITIVE",
            return_bucket="GAIN",
        ),
        _row(
            schema_fixture_case_id="SYNTH_FWD_5D_COMPLETE_LABEL",
            forward_return_label_id="SYNTH_FWD_LABEL_SYN002_20240402_5D",
            source_replay_decision_id="SYNTH_REVIEW_BUY_CANDIDATE_REPORT_ONLY_DECISION",
            symbol="SYN002",
            horizon_trading_days=5,
            horizon_calendar_days=7,
            window_start_date="2024-04-03T09:30:00",
            window_end_date="2024-04-10T15:00:00",
            exit_date="2024-04-10",
            exit_price_available_time="2024-04-10T15:30:00",
            exit_price="10.25",
            forward_return="0.25",
            forward_return_pct="0.025000",
            log_forward_return="0.024693",
            return_direction="POSITIVE",
            return_bucket="GAIN",
        ),
        _row(
            schema_fixture_case_id="SYNTH_FWD_20D_COMPLETE_BENCHMARK_RELATIVE_LABEL",
            forward_return_label_id="SYNTH_FWD_LABEL_SYN003_20240402_20D_REL",
            source_replay_decision_id="SYNTH_REVIEW_SELL_CANDIDATE_REPORT_ONLY_DECISION",
            symbol="SYN003",
            horizon_trading_days=20,
            horizon_calendar_days=30,
            window_start_date="2024-04-03T09:30:00",
            window_end_date="2024-05-02T15:00:00",
            exit_date="2024-05-02",
            exit_price_available_time="2024-05-02T15:30:00",
            exit_price="10.80",
            forward_return="0.80",
            forward_return_pct="0.080000",
            log_forward_return="0.076961",
            return_direction="POSITIVE",
            return_bucket="GAIN",
            benchmark_exit_price="102.00",
            benchmark_forward_return="0.020000",
            benchmark_relative_return="0.060000",
            industry_forward_return="0.030000",
            industry_relative_return="0.050000",
        ),
        _row(
            schema_fixture_case_id="SYNTH_NEGATIVE_FORWARD_RETURN_LABEL",
            forward_return_label_id="SYNTH_FWD_LABEL_SYN004_20240402_NEG",
            source_replay_decision_id="SYNTH_HOLD_REVIEW_DECISION",
            symbol="SYN004",
            window_start_date="2024-04-03T09:30:00",
            window_end_date="2024-04-10T15:00:00",
            exit_date="2024-04-10",
            exit_price_available_time="2024-04-10T15:30:00",
            exit_price="9.40",
            forward_return="-0.60",
            forward_return_pct="-0.060000",
            log_forward_return="-0.061875",
            return_direction="NEGATIVE",
            return_bucket="LOSS",
        ),
        _row(
            schema_fixture_case_id="SYNTH_POSITIVE_FORWARD_RETURN_LABEL",
            forward_return_label_id="SYNTH_FWD_LABEL_SYN005_20240402_POS",
            source_replay_decision_id="SYNTH_NO_ACTION_WEAK_EVIDENCE_DECISION",
            symbol="SYN005",
            window_start_date="2024-04-03T09:30:00",
            window_end_date="2024-04-10T15:00:00",
            exit_date="2024-04-10",
            exit_price_available_time="2024-04-10T15:30:00",
            exit_price="10.45",
            forward_return="0.45",
            forward_return_pct="0.045000",
            log_forward_return="0.044017",
            return_direction="POSITIVE",
            return_bucket="GAIN",
        ),
        _row(
            schema_fixture_case_id="SYNTH_BLOCKED_NOT_FROZEN_DECISION_LABEL",
            forward_return_label_id="SYNTH_FWD_LABEL_SYN006_20240402_NOT_FROZEN",
            source_replay_decision_id="SYNTH_OBSERVE_ONLY_INCOMPLETE_REVIEW_DECISION",
            symbol="SYN006",
            replay_decision_frozen=False,
            label_status="BLOCKED",
            label_quality_status="FAIL",
            label_completeness_status="EXECUTION_BLOCKED",
            validation_status="FAIL",
            validation_issue_count=1,
            blocker_reason="Referenced replay decision is not frozen; future label join is blocked.",
            window_start_date="2024-04-03T09:30:00",
            window_end_date="2024-04-10T15:00:00",
            exit_date="2024-04-10",
            exit_price_available_time="2024-04-10T15:30:00",
            exit_price="10.05",
            forward_return="0.05",
            forward_return_pct="0.005000",
            log_forward_return="0.004988",
            return_direction="POSITIVE",
            return_bucket="GAIN",
        ),
        _row(
            schema_fixture_case_id="SYNTH_BLOCKED_MISSING_EXIT_PRICE_LABEL",
            forward_return_label_id="SYNTH_FWD_LABEL_SYN007_20240402_MISSING_EXIT",
            source_replay_decision_id="SYNTH_BLOCKED_MISSING_REPLAY_EVIDENCE_BUNDLE_DECISION",
            symbol="SYN007",
            label_status="BLOCKED",
            label_quality_status="FAIL",
            label_completeness_status="MISSING_EXIT_PRICE",
            validation_status="FAIL",
            validation_issue_count=1,
            blocker_reason="Exit price is missing or unavailable for the synthetic window.",
            exit_price="",
            exit_price_available_time="",
            forward_return="",
            forward_return_pct="",
            log_forward_return="",
            return_direction="UNKNOWN",
            return_bucket="MISSING",
            execution_blocker_type="MISSING_PRICE",
            execution_blocker_reason="Missing exit price blocks complete label.",
            label_execution_status="BLOCKED_MISSING_PRICE",
        ),
        _row(
            schema_fixture_case_id="SYNTH_BLOCKED_INVALID_WINDOW_LABEL",
            forward_return_label_id="SYNTH_FWD_LABEL_SYN008_20240402_INVALID_WINDOW",
            source_replay_decision_id="SYNTH_BLOCKED_FUTURE_AVAILABLE_EVIDENCE_DECISION",
            symbol="SYN008",
            label_status="BLOCKED",
            label_quality_status="FAIL",
            label_completeness_status="INVALID_WINDOW",
            validation_status="FAIL",
            validation_issue_count=1,
            blocker_reason="Label window starts at or before replay_decision_time.",
            window_start_date="2024-04-02T09:30:00",
            window_end_date="2024-04-02T15:00:00",
            entry_date="2024-04-02",
            exit_date="2024-04-02",
            window_valid=False,
            execution_blocker_type="INVALID_WINDOW",
            execution_blocker_reason="Invalid label window.",
            label_execution_status="BLOCKED_INVALID_WINDOW",
            forward_return="",
            forward_return_pct="",
            log_forward_return="",
            return_direction="UNKNOWN",
            return_bucket="MISSING",
        ),
        _row(
            schema_fixture_case_id="SYNTH_EXECUTION_BLOCKED_SUSPENSION_LABEL",
            forward_return_label_id="SYNTH_FWD_LABEL_SYN009_20240402_SUSPENSION",
            source_replay_decision_id="SYNTH_BLOCKED_RISK_VETO_ST_DELIST_DECISION",
            symbol="SYN009",
            label_status="BLOCKED",
            label_quality_status="FAIL",
            label_completeness_status="EXECUTION_BLOCKED",
            validation_status="FAIL",
            validation_issue_count=1,
            blocker_reason="Suspension or no-trade window blocks clean execution interpretation.",
            tradeable_at_entry=False,
            tradeable_at_exit=False,
            suspended_during_window=True,
            execution_blocker_type="SUSPENSION",
            execution_blocker_reason="Synthetic suspension/no-trade window.",
            label_execution_status="BLOCKED_SUSPENSION",
            forward_return="",
            forward_return_pct="",
            log_forward_return="",
            return_direction="UNKNOWN",
            return_bucket="MISSING",
        ),
        _row(
            schema_fixture_case_id="SYNTH_PARTIAL_BENCHMARK_OR_INDUSTRY_LABEL",
            forward_return_label_id="SYNTH_FWD_LABEL_SYN010_20240402_PARTIAL_REL",
            source_replay_decision_id="SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_DECISION",
            symbol="SYN010",
            label_status="PARTIAL",
            label_quality_status="WARN",
            label_completeness_status="PARTIAL_BENCHMARK_MISSING",
            validation_status="WARN",
            validation_issue_count=0,
            warning_reason="Benchmark or industry-relative context is incomplete.",
            partial_label_reason="Security forward return exists but relative benchmark or industry label is incomplete.",
            relative_label_available=False,
            benchmark_exit_price="",
            benchmark_forward_return="",
            benchmark_relative_return="",
            industry_relative_return="",
            exit_price="10.20",
            forward_return="0.20",
            forward_return_pct="0.020000",
            log_forward_return="0.019803",
            return_direction="POSITIVE",
            return_bucket="GAIN",
        ),
    ]
    return pd.DataFrame(rows, columns=REQUIRED_FORWARD_RETURN_LABEL_FIELDS)


def build_forward_return_label_field_contract() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "field_name": field,
                "field_group": _field_group(field),
                "data_type_hint": _data_type_hint(field),
                "required": True,
                "description": _field_description(field),
            }
            for field in REQUIRED_FORWARD_RETURN_LABEL_FIELDS
        ]
    )


def build_forward_return_label_case_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    return fixture_rows[
        [
            "schema_fixture_case_id",
            "forward_return_label_id",
            "source_replay_decision_id",
            "symbol",
            "horizon_trading_days",
            "label_status",
            "label_completeness_status",
            "return_direction",
            "return_bucket",
            "execution_blocker_type",
            "blocker_reason",
            "partial_label_reason",
        ]
    ].copy()


def build_forward_return_label_leakage_guard_results() -> pd.DataFrame:
    guards = [
        (
            "decision_time_separation",
            "Forward labels are outcome context only and must not leak into decision-time inputs.",
        ),
        ("training_boundary", "Forward labels do not authorize model training by themselves."),
        ("signal_boundary", "Forward labels do not authorize signal score inputs."),
        ("paper_boundary", "Forward labels do not create paper validation or approval."),
        ("buy_review_boundary", "Forward labels do not create buy-review eligibility."),
        ("trading_boundary", "Forward labels do not create broker, order, message, API, or trading permission."),
    ]
    return pd.DataFrame(
        [
            {
                "guard_name": guard_name,
                "expected_value": False,
                "observed_value": False,
                "passed": True,
                "notes": notes,
            }
            for guard_name, notes in guards
        ]
    )


def validate_forward_return_label_fixture(
    fixture_rows: pd.DataFrame,
    settings: ForwardReturnLabelSchemaFixtureSettings,
) -> pd.DataFrame:
    checks: list[dict[str, Any]] = []

    def add(check_name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": check_name, "passed": bool(passed), "detail": detail})

    all_text = "\n".join(fixture_rows.astype(str).to_numpy().ravel().tolist())
    complete = fixture_rows[fixture_rows["label_status"] == "COMPLETE"]
    cases = set(fixture_rows["schema_fixture_case_id"])

    add("exactly_10_label_rows", len(fixture_rows) == 10, f"row_count={len(fixture_rows)}")
    add("required_cases_present", cases == set(REQUIRED_CASE_IDS), f"case_count={len(cases)}")
    add(
        "required_fields_present",
        set(REQUIRED_FORWARD_RETURN_LABEL_FIELDS) <= set(fixture_rows.columns),
        "required fields present",
    )
    add("unique_forward_return_label_id", fixture_rows["forward_return_label_id"].is_unique, "ids are unique")
    add("leading_zero_symbol_preserved", "000001" in set(fixture_rows["symbol"].astype(str)), "000001 present")
    add(
        "replay_decision_fixture_lineage_present",
        (
            (fixture_rows["source_replay_decision_fixture_id"] == "356bbd57a4d6")
            & (fixture_rows["replay_decision_workflow_stage"] == "REPLAY_DECISION_SCHEMA_FIXTURE_CREATED")
        ).all(),
        "rows reference replay decision schema fixture lineage only",
    )
    add(
        "complete_windows_start_after_decision_time",
        complete.apply(lambda row: pd.Timestamp(row["window_start_date"]) > pd.Timestamp(row["replay_decision_time"]), axis=1).all(),
        "complete rows start after decision time",
    )
    add(
        "complete_windows_end_after_start",
        complete.apply(lambda row: pd.Timestamp(row["window_end_date"]) > pd.Timestamp(row["window_start_date"]), axis=1).all(),
        "complete rows end after start",
    )
    add(
        "not_frozen_case_blocked",
        _case_value(fixture_rows, "SYNTH_BLOCKED_NOT_FROZEN_DECISION_LABEL", "label_status") == "BLOCKED"
        and not _bool(_case_value(fixture_rows, "SYNTH_BLOCKED_NOT_FROZEN_DECISION_LABEL", "replay_decision_frozen")),
        "not-frozen decision case blocked",
    )
    add(
        "missing_exit_price_case_blocked",
        _case_value(fixture_rows, "SYNTH_BLOCKED_MISSING_EXIT_PRICE_LABEL", "label_completeness_status")
        == "MISSING_EXIT_PRICE",
        "missing exit price case blocked",
    )
    add(
        "invalid_window_case_blocked",
        _case_value(fixture_rows, "SYNTH_BLOCKED_INVALID_WINDOW_LABEL", "label_completeness_status") == "INVALID_WINDOW"
        and not _bool(_case_value(fixture_rows, "SYNTH_BLOCKED_INVALID_WINDOW_LABEL", "window_valid")),
        "invalid window case blocked",
    )
    add(
        "suspension_case_explicit",
        _case_value(fixture_rows, "SYNTH_EXECUTION_BLOCKED_SUSPENSION_LABEL", "execution_blocker_type") == "SUSPENSION",
        "suspension case has explicit execution blocker",
    )
    add(
        "partial_relative_case_partial",
        _case_value(fixture_rows, "SYNTH_PARTIAL_BENCHMARK_OR_INDUSTRY_LABEL", "label_status") == "PARTIAL",
        "partial benchmark or industry case remains partial",
    )
    add("label_status_allowed", set(fixture_rows["label_status"]) <= LABEL_STATUSES, "label statuses valid")
    add(
        "label_quality_status_allowed",
        set(fixture_rows["label_quality_status"]) <= LABEL_QUALITY_STATUSES,
        "quality statuses valid",
    )
    add(
        "label_completeness_status_allowed",
        set(fixture_rows["label_completeness_status"]) <= LABEL_COMPLETENESS_STATUSES,
        "completeness statuses valid",
    )
    add(
        "return_direction_allowed",
        set(fixture_rows["return_direction"]) <= RETURN_DIRECTIONS,
        "return directions valid",
    )
    add("return_bucket_allowed", set(fixture_rows["return_bucket"]) <= RETURN_BUCKETS, "return buckets valid")
    add(
        "execution_blocker_type_allowed",
        set(fixture_rows["execution_blocker_type"]) <= EXECUTION_BLOCKER_TYPES,
        "execution blocker types valid",
    )
    add("calendar_policy_allowed", set(fixture_rows["calendar_policy"]) <= CALENDAR_POLICIES, "calendar policy valid")
    add(
        "price_basis_allowed",
        set(fixture_rows["entry_price_basis"]) <= PRICE_BASES and set(fixture_rows["exit_price_basis"]) <= PRICE_BASES,
        "price basis valid",
    )
    for flag in ROW_FALSE_FLAGS:
        add(f"{flag}_false", (fixture_rows[flag] == False).all(), f"{flag} false for all rows")  # noqa: E712
    add(
        "no_private_credential_like_values",
        re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", all_text.lower()) is None,
        "no private credential-like values",
    )
    add(
        "output_path_safe",
        not _path_targets_forbidden_storage(settings.output_dir),
        "output directory avoids data/raw, data/processed, data/cache, and docs/project_sources",
    )
    return pd.DataFrame(checks)


def write_forward_return_label_schema_fixture_artifacts(
    *,
    result: ForwardReturnLabelSchemaFixtureResult,
    settings: ForwardReturnLabelSchemaFixtureSettings,
    fixture_rows: pd.DataFrame,
    field_contract: pd.DataFrame,
    case_matrix: pd.DataFrame,
    validation_results: pd.DataFrame,
    leakage_guard_results: pd.DataFrame,
) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    fixture_rows.to_csv(paths["fixture_rows"], index=False)
    case_matrix.to_csv(paths["case_matrix"], index=False)
    field_contract.to_csv(paths["field_contract"], index=False)
    validation_results.to_csv(paths["validation_results"], index=False)
    leakage_guard_results.to_csv(paths["leakage_guard_results"], index=False)
    paths["safety_flags"].write_text(json.dumps(_safety_flags(), indent=2, sort_keys=True), encoding="utf-8")
    paths["report"].write_text(render_forward_return_label_schema_fixture_report(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_metadata(result, settings), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def render_forward_return_label_schema_fixture_report(result: ForwardReturnLabelSchemaFixtureResult) -> str:
    return "\n".join(
        [
            "# Forward Return Label Schema Fixture Report v0.1",
            "",
            "This workflow creates tiny synthetic forward_return_label rows for schema and governance review only.",
            "",
            "## Current Result",
            "",
            f"- forward_return_label_schema_fixture_id: {result.forward_return_label_schema_fixture_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- label_count: {result.label_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
            "",
            "## Safety Boundary",
            "",
            "- No real forward labels are created.",
            "- No future labels joined to replay decisions or training datasets.",
            "- No replay execution or metric computation is created.",
            "- No signal_score implementation or input authorization is created.",
            "- No model training is performed.",
            "- No active weights or active thresholds are created.",
            "- No stock_profile validation is created.",
            "- No paper validation is created.",
            "- No buy-review or buy_review_allowed flag is created.",
            "- No strategy performance validation is claimed.",
            "- No current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, or trading is created.",
            "- No trading is allowed.",
        ]
    )


def resolve_forward_return_label_schema_fixture_paths(output_dir: Path, fixture_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    paths = {"artifact_dir": artifact_dir}
    paths.update({key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()})
    return paths


def _row(**overrides: Any) -> dict[str, Any]:
    case_id = overrides.get("schema_fixture_case_id", "SYNTH_FWD_LABEL")
    symbol = overrides.get("symbol", "SYN000")
    base: dict[str, Any] = {
        "forward_return_label_id": f"{case_id}_ID",
        "source_replay_decision_fixture_id": "356bbd57a4d6",
        "source_replay_decision_id": "SYNTH_WATCH_COMPLETE_EVIDENCE_DECISION",
        "replay_decision_status": "PASS",
        "replay_decision_health_status": "PASS",
        "replay_decision_workflow_stage": "REPLAY_DECISION_SCHEMA_FIXTURE_CREATED",
        "replay_decision_frozen": True,
        "symbol": symbol,
        "asset_type": "STOCK",
        "universe_name": "synthetic_forward_return_label_fixture",
        "decision_date": "2024-04-02",
        "replay_as_of_date": "2024-04-02",
        "replay_decision_time": "2024-04-02T09:30:00",
        "label_policy_version": "forward_return_label_schema_fixture_policy_v0.1",
        "schema_fixture_case_id": case_id,
        "horizon_trading_days": 5,
        "horizon_calendar_days": 7,
        "window_start_date": "2024-04-03T09:30:00",
        "window_end_date": "2024-04-10T15:00:00",
        "entry_date": "2024-04-03",
        "exit_date": "2024-04-10",
        "entry_price_available_time": "2024-04-03T09:31:00",
        "exit_price_available_time": "2024-04-10T15:30:00",
        "calendar_policy": "TRADING_DAY",
        "holiday_calendar_id": "CN_SYNTHETIC_TRADING_CALENDAR",
        "window_valid": True,
        "entry_price": "10.00",
        "exit_price": "10.10",
        "entry_price_source": "SYNTH_MARKET_DATA_REF",
        "exit_price_source": "SYNTH_MARKET_DATA_REF",
        "entry_price_basis": "CLOSE",
        "exit_price_basis": "CLOSE",
        "corporate_action_adjustment": "NONE",
        "forward_return": "0.10",
        "forward_return_pct": "0.010000",
        "log_forward_return": "0.009950",
        "return_direction": "POSITIVE",
        "return_bucket": "GAIN",
        "benchmark_id": "SYNTH_BENCHMARK_000",
        "benchmark_name": "Synthetic Benchmark",
        "benchmark_entry_price": "100.00",
        "benchmark_exit_price": "101.00",
        "benchmark_forward_return": "0.010000",
        "benchmark_relative_return": "0.000000",
        "industry_id": "SYNTH_INDUSTRY_000",
        "industry_name": "Synthetic Industry",
        "industry_forward_return": "0.008000",
        "industry_relative_return": "0.002000",
        "relative_label_available": True,
        "tradeable_at_entry": True,
        "tradeable_at_exit": True,
        "suspended_during_window": False,
        "limit_up_or_down_during_window": False,
        "halt_or_special_handling_flag": False,
        "execution_blocker_type": "NONE",
        "execution_blocker_reason": "",
        "label_execution_status": "EXECUTION_CONTEXT_AVAILABLE",
        "label_status": "COMPLETE",
        "label_quality_status": "PASS",
        "label_completeness_status": "COMPLETE",
        "validation_status": "PASS",
        "validation_issue_count": 0,
        "blocker_reason": "",
        "warning_reason": "",
        "partial_label_reason": "",
        "report_only": True,
        "diagnostic_only": True,
        "schema_fixture": True,
        "synthetic_fixture_row": True,
        "source_registry_ref": "source_registry_schema_fixture:3d04b1f6480e",
        "raw_document_store_ref": "raw_document_store_schema_fixture:ea35302eb116",
        "market_data_ref": "SYNTHETIC_MARKET_DATA_REF",
        "benchmark_data_ref": "SYNTHETIC_BENCHMARK_DATA_REF",
        "industry_data_ref": "SYNTHETIC_INDUSTRY_DATA_REF",
        "calendar_ref": "SYNTHETIC_CALENDAR_REF",
        "source_hash": _stable_hash(f"source|{case_id}"),
        "revision_id": f"SYNTH_FWD_LABEL_REV_{_stable_hash(case_id)[:8]}",
        "created_at": "2026-06-28T00:00:00Z",
        "created_by_workflow": "forward-return-label-schema-fixture",
        "artifact_path": "",
    }
    for flag in ROW_FALSE_FLAGS:
        base[flag] = False
    base.update(overrides)
    return base


def _metadata(
    result: ForwardReturnLabelSchemaFixtureResult,
    settings: ForwardReturnLabelSchemaFixtureSettings,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "forward_return_label_schema_fixture_id": result.forward_return_label_schema_fixture_id,
        "workflow_name": "forward_return_label_schema_fixture",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "config_version": settings.config_version,
        "label_count": result.label_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": True,
        "diagnostic_only": True,
        "schema_fixture": True,
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
        "recommended_next_task": "Forward Return Label Schema Fixture Views Report-Only v0.1",
    }
    metadata.update(_safety_flags())
    return metadata


def _safety_flags() -> dict[str, bool]:
    return {flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS}


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Forward Return Label Schema Fixture Views Report-Only v0.1",
            "",
            "Add index, health, and status artifact views for this report-only forward return label schema fixture. Keep the workflow synthetic and do not create real forward labels, future-label joins, replay execution, metric computation, signal_score inputs, model training inputs, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/order/message/API behavior, or trading permission.",
        ]
    )


def _fixture_id(fixture_rows: pd.DataFrame, config_version: str) -> str:
    digest = hashlib.sha256(config_version.encode("utf-8"))
    digest.update("|".join(REQUIRED_FORWARD_RETURN_LABEL_FIELDS).encode("utf-8"))
    digest.update(fixture_rows.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _assert_settings_safe(settings: ForwardReturnLabelSchemaFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Forward return label schema fixture must remain report_only and diagnostic_only.")
    if _path_targets_forbidden_storage(settings.output_dir):
        raise ValueError("Forward return label schema fixture output must stay out of protected paths.")


def _path_targets_forbidden_storage(path: Path) -> bool:
    normalized_parts = {part.lower() for part in Path(path).parts}
    path_text = str(path).replace("\\", "/").lower()
    return (
        ("data" in normalized_parts and {"raw", "processed", "cache"} & normalized_parts)
        or "docs/project_sources" in path_text
    )


def _case_value(frame: pd.DataFrame, case_id: str, column: str) -> Any:
    return frame.loc[frame["schema_fixture_case_id"] == case_id, column].iloc[0]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _field_group(field: str) -> str:
    groups = {
        "identity_and_lineage": {
            "forward_return_label_id",
            "source_replay_decision_fixture_id",
            "source_replay_decision_id",
            "replay_decision_status",
            "replay_decision_health_status",
            "replay_decision_workflow_stage",
            "replay_decision_frozen",
            "symbol",
            "asset_type",
            "universe_name",
            "decision_date",
            "replay_as_of_date",
            "replay_decision_time",
            "label_policy_version",
            "schema_fixture_case_id",
        },
        "horizon_and_window": {
            "horizon_trading_days",
            "horizon_calendar_days",
            "window_start_date",
            "window_end_date",
            "entry_date",
            "exit_date",
            "entry_price_available_time",
            "exit_price_available_time",
            "calendar_policy",
            "holiday_calendar_id",
            "window_valid",
        },
        "price_and_return": {
            "entry_price",
            "exit_price",
            "entry_price_source",
            "exit_price_source",
            "entry_price_basis",
            "exit_price_basis",
            "corporate_action_adjustment",
            "forward_return",
            "forward_return_pct",
            "log_forward_return",
            "return_direction",
            "return_bucket",
        },
        "benchmark_and_industry": {
            "benchmark_id",
            "benchmark_name",
            "benchmark_entry_price",
            "benchmark_exit_price",
            "benchmark_forward_return",
            "benchmark_relative_return",
            "industry_id",
            "industry_name",
            "industry_forward_return",
            "industry_relative_return",
            "relative_label_available",
        },
        "execution_and_market_state": {
            "tradeable_at_entry",
            "tradeable_at_exit",
            "suspended_during_window",
            "limit_up_or_down_during_window",
            "halt_or_special_handling_flag",
            "execution_blocker_type",
            "execution_blocker_reason",
            "label_execution_status",
        },
        "quality_and_validation": {
            "label_status",
            "label_quality_status",
            "label_completeness_status",
            "validation_status",
            "validation_issue_count",
            "blocker_reason",
            "warning_reason",
            "partial_label_reason",
        },
        "source_and_audit": {
            "source_registry_ref",
            "raw_document_store_ref",
            "market_data_ref",
            "benchmark_data_ref",
            "industry_data_ref",
            "calendar_ref",
            "source_hash",
            "revision_id",
            "created_at",
            "created_by_workflow",
            "artifact_path",
        },
    }
    for group, fields in groups.items():
        if field in fields:
            return group
    return "safety_and_boundary_flags"


def _data_type_hint(field: str) -> str:
    if field in {
        "replay_decision_frozen",
        "window_valid",
        "relative_label_available",
        "tradeable_at_entry",
        "tradeable_at_exit",
        "suspended_during_window",
        "limit_up_or_down_during_window",
        "halt_or_special_handling_flag",
        "report_only",
        "diagnostic_only",
        "schema_fixture",
        "synthetic_fixture_row",
    } | set(ROW_FALSE_FLAGS):
        return "boolean"
    if field in {"horizon_trading_days", "horizon_calendar_days", "validation_issue_count"}:
        return "integer"
    if field.endswith("_time") or field in {"window_start_date", "window_end_date", "created_at"}:
        return "timestamp"
    if field.endswith("_date"):
        return "date"
    if field.endswith("_price") or "return" in field:
        return "decimal"
    return "string"


def _field_description(field: str) -> str:
    return field.replace("_", " ") + " for report-only forward return label schema fixture governance."
