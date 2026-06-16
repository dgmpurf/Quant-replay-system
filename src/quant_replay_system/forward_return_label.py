"""Report-only forward return label core.

This workflow joins forward price outcomes after a frozen replay decision
artifact has been produced. It is deliberately narrow: it writes diagnostics
under manual_diagnostics only and never trains weights, creates stock profiles,
creates buy-review eligibility, validates strategy performance, calls trading
systems, mutates caches, or writes raw/processed data stores.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_FORWARD_RETURN_LABEL_INPUT = "NO_FORWARD_RETURN_LABEL_INPUT"
FORWARD_RETURN_LABEL_INPUT_FOUND = "FORWARD_RETURN_LABEL_INPUT_FOUND"
FORWARD_RETURN_LABEL_LINEAGE_BLOCKED = "FORWARD_RETURN_LABEL_LINEAGE_BLOCKED"
FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED = "FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED"
FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED = "FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED"
FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED = "FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED"
FORWARD_RETURN_LABEL_WINDOW_BLOCKED = "FORWARD_RETURN_LABEL_WINDOW_BLOCKED"
FORWARD_RETURN_LABEL_BENCHMARK_BLOCKED = "FORWARD_RETURN_LABEL_BENCHMARK_BLOCKED"
FORWARD_RETURN_LABEL_INDUSTRY_BLOCKED = "FORWARD_RETURN_LABEL_INDUSTRY_BLOCKED"
FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED = "FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED"
FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED = "FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED"
FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED = "FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED"
FORWARD_RETURN_LABEL_REVIEW_BLOCKED = "FORWARD_RETURN_LABEL_REVIEW_BLOCKED"
READY_FOR_FORWARD_RETURN_LABEL = "READY_FOR_FORWARD_RETURN_LABEL"
FORWARD_RETURN_LABELS_CREATED = "FORWARD_RETURN_LABELS_CREATED"

EXACT_APPROVAL_TEXT = (
    "I explicitly authorize implementation of forward return label core only, "
    "report-only, no training, no stock_profile, no buy-review, no paper approval, "
    "no performance validation, no trading."
)

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/forward_return_label_v0_1")

SUPPORTED_LABELS = {
    "forward_return_1d",
    "forward_return_3d",
    "forward_return_5d",
    "forward_return_10d",
    "forward_return_20d",
    "max_drawdown_5d",
    "max_runup_5d",
    "benchmark_relative_return_5d",
    "industry_relative_return_5d",
}
DEFAULT_LABELS = ["forward_return_5d"]
PRICE_REQUIRED_COLUMNS = [
    "symbol",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "adjustment_factor",
    "suspended_flag",
    "limit_up_flag",
    "limit_down_flag",
    "source_id",
    "source_hash",
    "revision_id",
    "available_time",
    "quality_status",
]
DECISION_REQUIRED_COLUMNS = [
    "replay_decision_id",
    "replay_decision_freeze_run_id",
    "replay_as_of_date",
    "symbol",
]
LABEL_ROW_COLUMNS = [
    "forward_return_label_run_id",
    "replay_decision_id",
    "replay_decision_freeze_run_id",
    "actual_replay_execution_run_id",
    "source_active_input_creation_run_id",
    "source_real_replay_precheck_run_id",
    "symbol",
    "instrument_type",
    "replay_as_of_date",
    "label_name",
    "label_horizon_trading_days",
    "label_start_date",
    "label_end_date",
    "start_price",
    "end_price",
    "forward_return",
    "max_drawdown",
    "max_runup",
    "benchmark_symbol",
    "benchmark_return",
    "benchmark_relative_return",
    "industry_code",
    "industry_name",
    "industry_return",
    "industry_relative_return",
    "suspended_days_count",
    "limit_up_days_count",
    "limit_down_days_count",
    "price_source_id",
    "price_source_hash",
    "price_revision_id",
    "price_available_time",
    "price_quality_status",
    "report_only",
    "diagnostic_only",
]
LEAKAGE_FORBIDDEN_COLUMNS = {
    "forward_return",
    "forward_return_label",
    "training_score",
    "model_weight",
    "stock_profile_status",
    "stock_profile_validated",
    "real_buy_review_eligible",
    "approved_for_paper",
}
OVERCLAIM_FORBIDDEN_COLUMNS = {"strategy_performance_validated"}
SIDE_EFFECT_FORBIDDEN_COLUMNS = {"order_id", "broker_order_id", "trade_id"}
LEAKAGE_TRUE_FIELDS = {
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "real_buy_review_eligible",
}
SIDE_EFFECT_TRUE_FIELDS = {
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
}
OVERCLAIM_TRUE_FIELDS = {
    "buy_review_allowed",
    "trading_allowed",
    "approved_for_paper",
    "strategy_performance_validated",
}
OVERCLAIM_REQUIRED_TRUE_FIELDS = {
    "forward_labels_not_training_permission",
    "forward_labels_not_stock_profile_permission",
    "forward_labels_not_buy_review_eligibility",
    "forward_labels_not_paper_approval",
    "forward_labels_not_performance_validation",
    "forward_labels_not_trading_authorization",
}
DOWNSTREAM_FALSE_FIELDS = [
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
    "strategy_performance_validated",
    "trading_allowed",
    "order_placed",
    "broker_api_called",
]


@dataclass(frozen=True)
class ForwardReturnLabelSettings:
    replay_decision_freeze_artifact_path: Path | None = None
    replay_decision_freeze_status_artifact_path: Path | None = None
    replay_decision_freeze_health_artifact_path: Path | None = None
    replay_decision_metadata_path: Path | None = None
    replay_decision_rows_path: Path | None = None
    replay_decision_evidence_index_path: Path | None = None
    replay_decision_safety_flags_path: Path | None = None
    approval_manifest_path: Path | None = None
    forward_label_request_manifest_path: Path | None = None
    price_input_csv_path: Path | None = None
    benchmark_input_csv_path: Path | None = None
    industry_input_csv_path: Path | None = None
    benchmark_mapping_csv_path: Path | None = None
    industry_mapping_csv_path: Path | None = None
    label_window_rules_csv_path: Path | None = None
    leakage_side_effect_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_forward_return_label: bool = False
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ForwardReturnLabelGateResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str
    observed_value: str = ""


@dataclass(frozen=True)
class ForwardReturnLabelResult:
    forward_return_label_run_id: str
    status: str
    workflow_stage: str
    ready_for_forward_return_label: bool
    forward_return_label_executed: bool
    forward_return_label_artifacts_created: bool
    forward_return_label_artifact_path: str
    forward_labels_allowed: bool
    forward_labels_exist: bool
    forward_return_labels_created: bool
    labels_joined_after_freeze: bool
    labels_excluded_from_decision_rows: bool
    source_replay_decision_freeze_run_id: str
    source_actual_replay_execution_run_id: str
    source_active_input_creation_run_id: str
    source_real_replay_precheck_run_id: str
    replay_decision_frozen: bool
    replay_decisions_exist: bool
    replay_decision_row_count: int
    label_row_count: int
    blocker_count: int
    warning_count: int
    next_action: str
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]
    precondition_results: list[ForwardReturnLabelGateResult]
    lineage_results: list[ForwardReturnLabelGateResult]
    authority_results: list[ForwardReturnLabelGateResult]
    frozen_replay_decision_results: list[ForwardReturnLabelGateResult]
    price_input_results: list[ForwardReturnLabelGateResult]
    label_window_results: list[ForwardReturnLabelGateResult]
    benchmark_industry_results: list[ForwardReturnLabelGateResult]
    leakage_side_effect_guard_results: list[ForwardReturnLabelGateResult]
    overclaim_guard_results: list[ForwardReturnLabelGateResult]
    training_allowed: bool = False
    weights_trained: bool = False
    training_result_created: bool = False
    stock_profile_allowed: bool = False
    active_stock_profile_exists: bool = False
    stock_profile_created: bool = False
    buy_review_allowed: bool = False
    real_buy_review_eligible: bool = False
    approved_for_paper: bool = False
    strategy_performance_validated: bool = False
    trading_allowed: bool = False
    order_placed: bool = False
    broker_api_called: bool = False
    message_sent: bool = False
    llm_api_called: bool = False
    external_api_called: bool = False
    cache_mutated: bool = False
    data_raw_written: bool = False
    data_processed_written: bool = False
    data_cache_written: bool = False
    current_candidates_run: bool = False
    snapshot_built: bool = False
    signal_semantics_changed: bool = False


def run_forward_return_label(settings: ForwardReturnLabelSettings | None = None) -> ForwardReturnLabelResult:
    settings = settings or ForwardReturnLabelSettings()
    output_dir = Path(settings.output_dir)
    _assert_manual_diagnostics_output(output_dir)
    run_id = _build_run_id(settings)
    artifact_dir = output_dir / run_id
    paths = _artifact_paths(artifact_dir)

    precondition_results: list[ForwardReturnLabelGateResult] = []
    lineage_results: list[ForwardReturnLabelGateResult] = []
    authority_results: list[ForwardReturnLabelGateResult] = []
    frozen_results: list[ForwardReturnLabelGateResult] = []
    price_results: list[ForwardReturnLabelGateResult] = []
    window_results: list[ForwardReturnLabelGateResult] = []
    benchmark_industry_results: list[ForwardReturnLabelGateResult] = []
    leakage_results: list[ForwardReturnLabelGateResult] = []
    overclaim_results: list[ForwardReturnLabelGateResult] = []

    supplied_paths = [
        settings.replay_decision_metadata_path,
        settings.replay_decision_rows_path,
        settings.approval_manifest_path,
        settings.price_input_csv_path,
    ]
    has_input = any(path is not None and Path(path).exists() for path in supplied_paths)
    if not has_input:
        precondition_results.append(
            _gate("precondition", "input_present", NO_FORWARD_RETURN_LABEL_INPUT, False, "No forward label input paths found", "")
        )
        result = _build_result(
            run_id=run_id,
            status=NO_FORWARD_RETURN_LABEL_INPUT,
            workflow_stage="FORWARD_RETURN_LABEL_NO_INPUT",
            ready=False,
            executed=False,
            artifacts_created=False,
            paths=paths,
            settings=settings,
            metadata={},
            decision_rows=pd.DataFrame(columns=DECISION_REQUIRED_COLUMNS),
            label_rows=pd.DataFrame(columns=LABEL_ROW_COLUMNS),
            precondition_results=precondition_results,
            lineage_results=lineage_results,
            authority_results=authority_results,
            frozen_results=frozen_results,
            price_results=price_results,
            window_results=window_results,
            benchmark_industry_results=benchmark_industry_results,
            leakage_results=leakage_results,
            overclaim_results=overclaim_results,
            next_action="Provide frozen replay decisions, approval, price inputs, and report-only guard evidence.",
        )
        if settings.write_artifacts:
            write_forward_return_label_artifacts(result, pd.DataFrame(columns=LABEL_ROW_COLUMNS))
        return result

    metadata = _read_json_or_empty(settings.replay_decision_metadata_path)
    safety = _read_json_or_empty(settings.replay_decision_safety_flags_path)
    approval = _read_json_or_empty(settings.approval_manifest_path)
    request = _read_json_or_empty(settings.forward_label_request_manifest_path)
    leakage_bundle = _read_json_or_empty(settings.leakage_side_effect_evidence_bundle_path)
    overclaim_bundle = _read_json_or_empty(settings.overclaim_evidence_bundle_path)

    decision_rows = _read_csv_or_empty(settings.replay_decision_rows_path)
    evidence_index = _read_csv_or_empty(settings.replay_decision_evidence_index_path)
    price_rows = _read_csv_or_empty(settings.price_input_csv_path)
    benchmark_rows = _read_csv_or_empty(settings.benchmark_input_csv_path)
    industry_rows = _read_csv_or_empty(settings.industry_input_csv_path)
    benchmark_mapping = _read_csv_or_empty(settings.benchmark_mapping_csv_path)
    industry_mapping = _read_csv_or_empty(settings.industry_mapping_csv_path)
    window_rules = _read_csv_or_empty(settings.label_window_rules_csv_path)

    precondition_results.append(_gate("precondition", "input_present", FORWARD_RETURN_LABEL_INPUT_FOUND, True, "", "inputs found"))
    authority_results.extend(_evaluate_authority(settings.approval_manifest_path, approval))
    frozen_results.extend(_evaluate_frozen_decisions(settings, metadata, decision_rows, evidence_index, safety))
    leakage_results.extend(_evaluate_forbidden_decision_columns(decision_rows))
    leakage_results.extend(_evaluate_safety_payloads(safety, leakage_bundle, metadata))
    overclaim_results.extend(_evaluate_overclaim_payload(overclaim_bundle, metadata))
    price_results.extend(_evaluate_price_inputs(settings.price_input_csv_path, price_rows, decision_rows))
    requested_labels = _requested_labels(request)
    window_results.extend(_evaluate_label_windows(settings.label_window_rules_csv_path, window_rules, requested_labels))
    benchmark_industry_results.extend(
        _evaluate_benchmark_industry(settings, requested_labels, benchmark_mapping, industry_mapping)
    )
    lineage_results.extend(_evaluate_lineage(metadata, decision_rows))

    status = _resolve_status(
        authority_results=authority_results,
        frozen_results=frozen_results,
        lineage_results=lineage_results,
        leakage_results=leakage_results,
        overclaim_results=overclaim_results,
        price_results=price_results,
        window_results=window_results,
        benchmark_industry_results=benchmark_industry_results,
    )
    label_rows = pd.DataFrame(columns=LABEL_ROW_COLUMNS)
    ready = status == READY_FOR_FORWARD_RETURN_LABEL
    executed = False
    artifacts_created = False
    workflow_stage = status
    next_action = "Resolve blocker gates before creating report-only forward return labels."
    if ready and settings.allow_forward_return_label:
        label_rows = _build_label_rows(
            run_id,
            decision_rows,
            price_rows,
            benchmark_rows,
            industry_rows,
            benchmark_mapping,
            industry_mapping,
            window_rules,
            requested_labels,
            settings,
        )
        if label_rows.empty:
            status = FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED
            workflow_stage = status
            ready = False
            next_action = "Resolve missing start/end price coverage before creating labels."
            price_results.append(
                _gate("price_input", "label_rows_created", status, False, "No label rows could be built", "")
            )
        else:
            status = FORWARD_RETURN_LABELS_CREATED
            workflow_stage = status
            executed = True
            artifacts_created = True
            next_action = "Review report-only forward return labels; do not train weights or create stock profiles."
    elif ready:
        next_action = "Review gates, then rerun with explicit --allow-forward-return-label if report-only labels are intended."

    result = _build_result(
        run_id=run_id,
        status=status,
        workflow_stage=workflow_stage,
        ready=ready,
        executed=executed,
        artifacts_created=artifacts_created,
        paths=paths,
        settings=settings,
        metadata=metadata,
        decision_rows=decision_rows,
        label_rows=label_rows,
        precondition_results=precondition_results,
        lineage_results=lineage_results,
        authority_results=authority_results,
        frozen_results=frozen_results,
        price_results=price_results,
        window_results=window_results,
        benchmark_industry_results=benchmark_industry_results,
        leakage_results=leakage_results,
        overclaim_results=overclaim_results,
        next_action=next_action,
    )
    if settings.write_artifacts:
        write_forward_return_label_artifacts(result, label_rows)
    return result


def write_forward_return_label_artifacts(result: ForwardReturnLabelResult, label_rows: pd.DataFrame) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_json(paths["metadata"], _metadata(result))
    _write_json(paths["safety_flags"], _safety_flags(result))
    _write_csv(paths["forward_return_label_rows"], label_rows.reindex(columns=LABEL_ROW_COLUMNS))
    _write_csv(paths["forward_return_label_price_input_index"], _index_frame(result, "price_input"))
    _write_csv(paths["forward_return_label_benchmark_index"], _index_frame(result, "benchmark"))
    _write_csv(paths["forward_return_label_industry_index"], _index_frame(result, "industry"))
    _write_gate_csv(paths["precondition_results"], result.precondition_results)
    _write_gate_csv(paths["lineage_results"], result.lineage_results)
    _write_gate_csv(paths["authority_results"], result.authority_results)
    _write_gate_csv(paths["frozen_replay_decision_results"], result.frozen_replay_decision_results)
    _write_gate_csv(paths["price_input_results"], result.price_input_results)
    _write_gate_csv(paths["label_window_results"], result.label_window_results)
    _write_gate_csv(paths["benchmark_industry_results"], result.benchmark_industry_results)
    _write_gate_csv(paths["leakage_side_effect_guard_results"], result.leakage_side_effect_guard_results)
    _write_gate_csv(paths["overclaim_guard_results"], result.overclaim_guard_results)
    paths["report"].write_text(render_forward_return_label_report(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")


def render_forward_return_label_report(result: ForwardReturnLabelResult) -> str:
    lines = [
        "# Forward Return Label Core Report-Only",
        "",
        f"- forward_return_label_run_id: {result.forward_return_label_run_id}",
        f"- status: {result.status}",
        f"- workflow_stage: {result.workflow_stage}",
        f"- ready_for_forward_return_label: {result.ready_for_forward_return_label}",
        f"- forward_return_label_executed: {result.forward_return_label_executed}",
        f"- forward_return_label_artifacts_created: {result.forward_return_label_artifacts_created}",
        f"- label_row_count: {result.label_row_count}",
        f"- source_replay_decision_freeze_run_id: {result.source_replay_decision_freeze_run_id}",
        "",
        "Safety interpretation: labels are joined after replay decision freeze and are excluded from decision-time rows.",
        "This is not training, not stock_profile creation, not buy-review eligibility, not paper approval, not performance validation, and not trading.",
        "",
        "Downstream flags remain false:",
    ]
    for field in DOWNSTREAM_FALSE_FIELDS:
        lines.append(f"- {field}: {getattr(result, field)}")
    lines.extend(["", f"Next action: {result.next_action}", ""])
    return "\n".join(lines)


def _build_result(
    *,
    run_id: str,
    status: str,
    workflow_stage: str,
    ready: bool,
    executed: bool,
    artifacts_created: bool,
    paths: dict[str, Path],
    settings: ForwardReturnLabelSettings,
    metadata: dict[str, Any],
    decision_rows: pd.DataFrame,
    label_rows: pd.DataFrame,
    precondition_results: list[ForwardReturnLabelGateResult],
    lineage_results: list[ForwardReturnLabelGateResult],
    authority_results: list[ForwardReturnLabelGateResult],
    frozen_results: list[ForwardReturnLabelGateResult],
    price_results: list[ForwardReturnLabelGateResult],
    window_results: list[ForwardReturnLabelGateResult],
    benchmark_industry_results: list[ForwardReturnLabelGateResult],
    leakage_results: list[ForwardReturnLabelGateResult],
    overclaim_results: list[ForwardReturnLabelGateResult],
    next_action: str,
) -> ForwardReturnLabelResult:
    blocker_count = sum(
        1
        for result in (
            precondition_results
            + lineage_results
            + authority_results
            + frozen_results
            + price_results
            + window_results
            + benchmark_industry_results
            + leakage_results
            + overclaim_results
        )
        if not result.passed
    )
    freeze_id = _first_non_empty(
        metadata.get("replay_decision_freeze_run_id"),
        _first_value(decision_rows, "replay_decision_freeze_run_id"),
    )
    actual_id = _first_non_empty(
        metadata.get("source_actual_replay_execution_run_id"),
        _first_value(decision_rows, "actual_replay_execution_run_id"),
    )
    active_id = _first_non_empty(
        metadata.get("source_active_input_creation_run_id"),
        _first_value(decision_rows, "source_active_input_creation_run_id"),
    )
    precheck_id = _first_non_empty(
        metadata.get("source_real_replay_precheck_run_id"),
        _first_value(decision_rows, "source_real_replay_precheck_run_id"),
    )
    labels_created = status == FORWARD_RETURN_LABELS_CREATED and not label_rows.empty
    return ForwardReturnLabelResult(
        forward_return_label_run_id=run_id,
        status=status,
        workflow_stage=workflow_stage,
        ready_for_forward_return_label=ready,
        forward_return_label_executed=executed,
        forward_return_label_artifacts_created=artifacts_created,
        forward_return_label_artifact_path=str(paths["forward_return_label_rows"]) if labels_created else "",
        forward_labels_allowed=labels_created,
        forward_labels_exist=labels_created,
        forward_return_labels_created=labels_created,
        labels_joined_after_freeze=labels_created,
        labels_excluded_from_decision_rows=True,
        source_replay_decision_freeze_run_id=freeze_id,
        source_actual_replay_execution_run_id=actual_id,
        source_active_input_creation_run_id=active_id,
        source_real_replay_precheck_run_id=precheck_id,
        replay_decision_frozen=bool(metadata.get("replay_decision_frozen", False)),
        replay_decisions_exist=bool(metadata.get("replay_decisions_exist", False)) or not decision_rows.empty,
        replay_decision_row_count=int(len(decision_rows)),
        label_row_count=int(len(label_rows)),
        blocker_count=blocker_count,
        warning_count=0,
        next_action=next_action,
        report_only=settings.report_only,
        diagnostic_only=settings.diagnostic_only,
        artifact_paths=paths,
        precondition_results=precondition_results,
        lineage_results=lineage_results,
        authority_results=authority_results,
        frozen_replay_decision_results=frozen_results,
        price_input_results=price_results,
        label_window_results=window_results,
        benchmark_industry_results=benchmark_industry_results,
        leakage_side_effect_guard_results=leakage_results,
        overclaim_guard_results=overclaim_results,
    )


def _evaluate_authority(path: Path | None, approval: dict[str, Any]) -> list[ForwardReturnLabelGateResult]:
    if path is None or not Path(path).exists():
        return [_gate("authority", "approval_manifest", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED, False, "Missing approval manifest", _path_text(path))]
    text = str(approval.get("approval_text", "")).strip()
    if text != EXACT_APPROVAL_TEXT:
        return [
            _gate(
                "authority",
                "exact_approval_text",
                FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED,
                False,
                "Approval text must be exact and must not authorize training, stock_profile, buy-review, paper approval, performance validation, or trading",
                _path_text(path),
                text,
            )
        ]
    return [_gate("authority", "exact_approval_text", "PASS", True, "", _path_text(path), text)]


def _evaluate_frozen_decisions(
    settings: ForwardReturnLabelSettings,
    metadata: dict[str, Any],
    decision_rows: pd.DataFrame,
    evidence_index: pd.DataFrame,
    safety: dict[str, Any],
) -> list[ForwardReturnLabelGateResult]:
    results: list[ForwardReturnLabelGateResult] = []
    for name, path in [
        ("replay_decision_metadata", settings.replay_decision_metadata_path),
        ("replay_decision_rows", settings.replay_decision_rows_path),
        ("replay_decision_evidence_index", settings.replay_decision_evidence_index_path),
        ("replay_decision_safety_flags", settings.replay_decision_safety_flags_path),
    ]:
        passed = path is not None and Path(path).exists()
        results.append(
            _gate(
                "frozen_replay_decision",
                name,
                "PASS" if passed else FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED,
                passed,
                "" if passed else f"Missing {name}",
                _path_text(path),
            )
        )
    frozen = metadata.get("execution_status") == "REPLAY_DECISION_FROZEN" and metadata.get("replay_decision_frozen") is True
    healthy = metadata.get("health_status", "PASS") == "PASS"
    decisions_exist = metadata.get("replay_decisions_exist") is True and not decision_rows.empty
    results.append(
        _gate(
            "frozen_replay_decision",
            "frozen_status",
            "PASS" if frozen else FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED,
            frozen,
            "" if frozen else "Replay decision artifact is not frozen",
            _path_text(settings.replay_decision_metadata_path),
            str(metadata.get("execution_status", "")),
        )
    )
    results.append(
        _gate(
            "frozen_replay_decision",
            "health_status",
            "PASS" if healthy else FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED,
            healthy,
            "" if healthy else "Replay decision freeze health is not PASS",
            _path_text(settings.replay_decision_metadata_path),
            str(metadata.get("health_status", "")),
        )
    )
    results.append(
        _gate(
            "frozen_replay_decision",
            "decision_rows_exist",
            "PASS" if decisions_exist else FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED,
            decisions_exist,
            "" if decisions_exist else "Frozen replay decision rows are missing or empty",
            _path_text(settings.replay_decision_rows_path),
            str(len(decision_rows)),
        )
    )
    required_cols_present = all(col in decision_rows.columns for col in DECISION_REQUIRED_COLUMNS)
    results.append(
        _gate(
            "frozen_replay_decision",
            "decision_required_columns",
            "PASS" if required_cols_present else FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED,
            required_cols_present,
            "" if required_cols_present else "Frozen replay decision rows are missing required columns",
            _path_text(settings.replay_decision_rows_path),
            ",".join(decision_rows.columns),
        )
    )
    evidence_ok = not evidence_index.empty and {"source_hash", "revision_id", "available_time"}.issubset(evidence_index.columns)
    results.append(
        _gate(
            "frozen_replay_decision",
            "decision_evidence_index",
            "PASS" if evidence_ok else FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED,
            evidence_ok,
            "" if evidence_ok else "Evidence index must contain source_hash, revision_id, and available_time",
            _path_text(settings.replay_decision_evidence_index_path),
        )
    )
    safety_ok = bool(safety)
    results.append(
        _gate(
            "frozen_replay_decision",
            "decision_safety_flags",
            "PASS" if safety_ok else FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED,
            safety_ok,
            "" if safety_ok else "Replay decision safety flags are missing",
            _path_text(settings.replay_decision_safety_flags_path),
        )
    )
    return results


def _evaluate_forbidden_decision_columns(decision_rows: pd.DataFrame) -> list[ForwardReturnLabelGateResult]:
    results: list[ForwardReturnLabelGateResult] = []
    columns = set(decision_rows.columns)
    for forbidden, status, group in [
        (LEAKAGE_FORBIDDEN_COLUMNS, FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED, "leakage_guard"),
        (OVERCLAIM_FORBIDDEN_COLUMNS, FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED, "overclaim_guard"),
        (SIDE_EFFECT_FORBIDDEN_COLUMNS, FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED, "side_effect_guard"),
    ]:
        overlap = sorted(columns & forbidden)
        results.append(
            _gate(
                group,
                "forbidden_decision_columns",
                "PASS" if not overlap else status,
                not overlap,
                "" if not overlap else f"Frozen decision rows contain forbidden columns: {','.join(overlap)}",
                "",
                ",".join(overlap),
            )
        )
    return results


def _evaluate_safety_payloads(*payloads: dict[str, Any]) -> list[ForwardReturnLabelGateResult]:
    results: list[ForwardReturnLabelGateResult] = []
    for field in sorted(LEAKAGE_TRUE_FIELDS):
        value = any(_truthy(payload.get(field)) for payload in payloads if payload)
        results.append(
            _gate(
                "leakage_guard",
                field,
                "PASS" if not value else FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED,
                not value,
                "" if not value else f"{field} must remain false",
                "",
                str(value),
            )
        )
    for field in sorted(SIDE_EFFECT_TRUE_FIELDS):
        value = any(_truthy(payload.get(field)) for payload in payloads if payload)
        results.append(
            _gate(
                "side_effect_guard",
                field,
                "PASS" if not value else FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED,
                not value,
                "" if not value else f"{field} must remain false",
                "",
                str(value),
            )
        )
    return results


def _evaluate_overclaim_payload(overclaim: dict[str, Any], metadata: dict[str, Any]) -> list[ForwardReturnLabelGateResult]:
    results: list[ForwardReturnLabelGateResult] = []
    for field in sorted(OVERCLAIM_TRUE_FIELDS):
        value = _truthy(overclaim.get(field)) or _truthy(metadata.get(field))
        results.append(
            _gate(
                "overclaim_guard",
                field,
                "PASS" if not value else FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED,
                not value,
                "" if not value else f"{field} must remain false",
                "",
                str(value),
            )
        )
    for field in sorted(OVERCLAIM_REQUIRED_TRUE_FIELDS):
        value = overclaim.get(field)
        passed = value is True
        results.append(
            _gate(
                "overclaim_guard",
                field,
                "PASS" if passed else FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED,
                passed,
                "" if passed else f"{field} must explicitly be true",
                "",
                str(value),
            )
        )
    return results


def _evaluate_price_inputs(path: Path | None, price_rows: pd.DataFrame, decision_rows: pd.DataFrame) -> list[ForwardReturnLabelGateResult]:
    results: list[ForwardReturnLabelGateResult] = []
    exists = path is not None and Path(path).exists()
    results.append(
        _gate("price_input", "price_input_exists", "PASS" if exists else FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED, exists, "" if exists else "Missing price input CSV", _path_text(path))
    )
    missing = [col for col in PRICE_REQUIRED_COLUMNS if col not in price_rows.columns]
    results.append(
        _gate(
            "price_input",
            "required_columns",
            "PASS" if not missing else FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED,
            not missing,
            "" if not missing else f"Missing price columns: {','.join(missing)}",
            _path_text(path),
        )
    )
    if missing or decision_rows.empty:
        return results
    required_blank = price_rows[["source_hash", "revision_id", "available_time", "quality_status"]].isna().any().any()
    results.append(
        _gate(
            "price_input",
            "lineage_columns_populated",
            "PASS" if not required_blank else FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED,
            not required_blank,
            "" if not required_blank else "Price lineage fields must be populated",
            _path_text(path),
        )
    )
    for _, decision in decision_rows.iterrows():
        symbol = str(decision.get("symbol", "")).zfill(6)
        as_of = str(decision.get("replay_as_of_date", ""))
        symbol_prices = price_rows.loc[price_rows["symbol"].astype(str).str.zfill(6) == symbol].sort_values("trade_date")
        start = symbol_prices.loc[symbol_prices["trade_date"].astype(str) == as_of]
        enough_future = len(symbol_prices.loc[symbol_prices["trade_date"].astype(str) >= as_of]) >= 6
        start_close = _numeric(start["close"].iloc[0]) if not start.empty else None
        passed = bool(start_close and enough_future)
        results.append(
            _gate(
                "price_input",
                "start_end_price_coverage",
                "PASS" if passed else FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED,
                passed,
                "" if passed else "Start or forward end price coverage is missing",
                _path_text(path),
                f"{symbol}:{as_of}",
            )
        )
    return results


def _evaluate_label_windows(path: Path | None, window_rules: pd.DataFrame, requested_labels: list[str]) -> list[ForwardReturnLabelGateResult]:
    exists = path is not None and Path(path).exists()
    results = [
        _gate("label_window", "label_window_rules_exists", "PASS" if exists else FORWARD_RETURN_LABEL_WINDOW_BLOCKED, exists, "" if exists else "Missing label window rules", _path_text(path))
    ]
    unsupported = [label for label in requested_labels if label not in SUPPORTED_LABELS]
    results.append(
        _gate(
            "label_window",
            "requested_label_supported",
            "PASS" if not unsupported else FORWARD_RETURN_LABEL_WINDOW_BLOCKED,
            not unsupported,
            "" if not unsupported else f"Unsupported labels: {','.join(unsupported)}",
            _path_text(path),
        )
    )
    if window_rules.empty or "label_name" not in window_rules.columns or "horizon_trading_days" not in window_rules.columns:
        results.append(
            _gate("label_window", "window_rule_columns", FORWARD_RETURN_LABEL_WINDOW_BLOCKED, False, "Window rules need label_name and horizon_trading_days", _path_text(path))
        )
    else:
        available = set(window_rules["label_name"].astype(str))
        missing = [label for label in requested_labels if label not in available]
        results.append(
            _gate(
                "label_window",
                "requested_label_windows_present",
                "PASS" if not missing else FORWARD_RETURN_LABEL_WINDOW_BLOCKED,
                not missing,
                "" if not missing else f"Missing label windows: {','.join(missing)}",
                _path_text(path),
            )
        )
    return results


def _evaluate_benchmark_industry(
    settings: ForwardReturnLabelSettings,
    requested_labels: list[str],
    benchmark_mapping: pd.DataFrame,
    industry_mapping: pd.DataFrame,
) -> list[ForwardReturnLabelGateResult]:
    results: list[ForwardReturnLabelGateResult] = []
    needs_benchmark = any(label.startswith("benchmark_relative") for label in requested_labels)
    needs_industry = any(label.startswith("industry_relative") for label in requested_labels)
    bench_pass = (not needs_benchmark) or (
        settings.benchmark_mapping_csv_path is not None
        and Path(settings.benchmark_mapping_csv_path).exists()
        and not benchmark_mapping.empty
        and {"symbol", "benchmark_symbol"}.issubset(benchmark_mapping.columns)
    )
    ind_pass = (not needs_industry) or (
        settings.industry_mapping_csv_path is not None
        and Path(settings.industry_mapping_csv_path).exists()
        and not industry_mapping.empty
        and {"symbol", "industry_code"}.issubset(industry_mapping.columns)
    )
    results.append(
        _gate(
            "benchmark_industry",
            "benchmark_mapping",
            "PASS" if bench_pass else FORWARD_RETURN_LABEL_BENCHMARK_BLOCKED,
            bench_pass,
            "" if bench_pass else "Benchmark-relative labels require benchmark mapping",
            _path_text(settings.benchmark_mapping_csv_path),
        )
    )
    results.append(
        _gate(
            "benchmark_industry",
            "industry_mapping",
            "PASS" if ind_pass else FORWARD_RETURN_LABEL_INDUSTRY_BLOCKED,
            ind_pass,
            "" if ind_pass else "Industry-relative labels require industry mapping",
            _path_text(settings.industry_mapping_csv_path),
        )
    )
    return results


def _evaluate_lineage(metadata: dict[str, Any], decision_rows: pd.DataFrame) -> list[ForwardReturnLabelGateResult]:
    required = [
        ("replay_decision_freeze_run_id", _first_non_empty(metadata.get("replay_decision_freeze_run_id"), _first_value(decision_rows, "replay_decision_freeze_run_id"))),
        ("source_actual_replay_execution_run_id", _first_non_empty(metadata.get("source_actual_replay_execution_run_id"), _first_value(decision_rows, "actual_replay_execution_run_id"))),
        ("source_active_input_creation_run_id", _first_non_empty(metadata.get("source_active_input_creation_run_id"), _first_value(decision_rows, "source_active_input_creation_run_id"))),
    ]
    return [
        _gate(
            "lineage",
            name,
            "PASS" if bool(value) else FORWARD_RETURN_LABEL_LINEAGE_BLOCKED,
            bool(value),
            "" if value else f"Missing {name}",
            "",
            str(value),
        )
        for name, value in required
    ]


def _resolve_status(
    *,
    authority_results: list[ForwardReturnLabelGateResult],
    frozen_results: list[ForwardReturnLabelGateResult],
    lineage_results: list[ForwardReturnLabelGateResult],
    leakage_results: list[ForwardReturnLabelGateResult],
    overclaim_results: list[ForwardReturnLabelGateResult],
    price_results: list[ForwardReturnLabelGateResult],
    window_results: list[ForwardReturnLabelGateResult],
    benchmark_industry_results: list[ForwardReturnLabelGateResult],
) -> str:
    ordered = [
        (authority_results, FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        (frozen_results, FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED),
        (lineage_results, FORWARD_RETURN_LABEL_LINEAGE_BLOCKED),
        (leakage_results, FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        (leakage_results, FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED),
        (leakage_results, FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED),
        (overclaim_results, FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED),
        (price_results, FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED),
        (window_results, FORWARD_RETURN_LABEL_WINDOW_BLOCKED),
        (benchmark_industry_results, FORWARD_RETURN_LABEL_BENCHMARK_BLOCKED),
        (benchmark_industry_results, FORWARD_RETURN_LABEL_INDUSTRY_BLOCKED),
    ]
    for results, status in ordered:
        if any(not item.passed and item.status == status for item in results):
            return status
    if any(not item.passed for item in authority_results + frozen_results + lineage_results + leakage_results + overclaim_results + price_results + window_results + benchmark_industry_results):
        return FORWARD_RETURN_LABEL_REVIEW_BLOCKED
    return READY_FOR_FORWARD_RETURN_LABEL


def _build_label_rows(
    run_id: str,
    decisions: pd.DataFrame,
    prices: pd.DataFrame,
    benchmarks: pd.DataFrame,
    industries: pd.DataFrame,
    benchmark_mapping: pd.DataFrame,
    industry_mapping: pd.DataFrame,
    window_rules: pd.DataFrame,
    requested_labels: list[str],
    settings: ForwardReturnLabelSettings,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if decisions.empty or prices.empty:
        return pd.DataFrame(columns=LABEL_ROW_COLUMNS)
    window_lookup = {
        str(row["label_name"]): int(row["horizon_trading_days"])
        for _, row in window_rules.iterrows()
        if "label_name" in row and "horizon_trading_days" in row
    }
    for _, decision in decisions.iterrows():
        symbol = str(decision.get("symbol", "")).zfill(6)
        as_of = str(decision.get("replay_as_of_date", ""))
        symbol_prices = prices.loc[prices["symbol"].astype(str).str.zfill(6) == symbol].sort_values("trade_date").reset_index(drop=True)
        if symbol_prices.empty:
            continue
        start_matches = symbol_prices.loc[symbol_prices["trade_date"].astype(str) == as_of]
        if start_matches.empty:
            continue
        start_index = int(start_matches.index[0])
        for label in requested_labels:
            horizon = int(window_lookup.get(label, _horizon_from_label(label)))
            end_index = start_index + horizon
            if end_index >= len(symbol_prices):
                continue
            window = symbol_prices.iloc[start_index : end_index + 1]
            start_row = symbol_prices.iloc[start_index]
            end_row = symbol_prices.iloc[end_index]
            start_price = _numeric(start_row.get("close"))
            end_price = _numeric(end_row.get("close"))
            if start_price is None or end_price is None or start_price == 0:
                continue
            forward_return = end_price / start_price - 1
            base = _label_base(run_id, decision, label, horizon, start_row, end_row, start_price, end_price, forward_return, window, settings)
            _add_benchmark(base, symbol, as_of, str(end_row.get("trade_date", "")), forward_return, benchmarks, benchmark_mapping)
            _add_industry(base, symbol, as_of, str(end_row.get("trade_date", "")), forward_return, industries, industry_mapping)
            if label == "max_drawdown_5d":
                base["max_drawdown"] = min(_numeric(value) for value in window["low"] if _numeric(value) is not None) / start_price - 1
            if label == "max_runup_5d":
                base["max_runup"] = max(_numeric(value) for value in window["high"] if _numeric(value) is not None) / start_price - 1
            rows.append(base)
    return pd.DataFrame(rows, columns=LABEL_ROW_COLUMNS)


def _label_base(
    run_id: str,
    decision: pd.Series,
    label: str,
    horizon: int,
    start_row: pd.Series,
    end_row: pd.Series,
    start_price: float,
    end_price: float,
    forward_return: float,
    window: pd.DataFrame,
    settings: ForwardReturnLabelSettings,
) -> dict[str, Any]:
    symbol = str(decision.get("symbol", "")).zfill(6)
    return {
        "forward_return_label_run_id": run_id,
        "replay_decision_id": decision.get("replay_decision_id", ""),
        "replay_decision_freeze_run_id": decision.get("replay_decision_freeze_run_id", ""),
        "actual_replay_execution_run_id": decision.get("actual_replay_execution_run_id", ""),
        "source_active_input_creation_run_id": decision.get("source_active_input_creation_run_id", ""),
        "source_real_replay_precheck_run_id": decision.get("source_real_replay_precheck_run_id", ""),
        "symbol": symbol,
        "instrument_type": decision.get("instrument_type", ""),
        "replay_as_of_date": decision.get("replay_as_of_date", ""),
        "label_name": label,
        "label_horizon_trading_days": horizon,
        "label_start_date": start_row.get("trade_date", ""),
        "label_end_date": end_row.get("trade_date", ""),
        "start_price": start_price,
        "end_price": end_price,
        "forward_return": forward_return,
        "max_drawdown": "",
        "max_runup": "",
        "benchmark_symbol": "",
        "benchmark_return": "",
        "benchmark_relative_return": "",
        "industry_code": "",
        "industry_name": "",
        "industry_return": "",
        "industry_relative_return": "",
        "suspended_days_count": int(window["suspended_flag"].map(_truthy).sum()),
        "limit_up_days_count": int(window["limit_up_flag"].map(_truthy).sum()),
        "limit_down_days_count": int(window["limit_down_flag"].map(_truthy).sum()),
        "price_source_id": end_row.get("source_id", ""),
        "price_source_hash": end_row.get("source_hash", ""),
        "price_revision_id": end_row.get("revision_id", ""),
        "price_available_time": end_row.get("available_time", ""),
        "price_quality_status": end_row.get("quality_status", ""),
        "report_only": settings.report_only,
        "diagnostic_only": settings.diagnostic_only,
    }


def _add_benchmark(base: dict[str, Any], symbol: str, start_date: str, end_date: str, forward_return: float, benchmarks: pd.DataFrame, mapping: pd.DataFrame) -> None:
    if mapping.empty or benchmarks.empty:
        return
    mapped = mapping.loc[mapping["symbol"].astype(str).str.zfill(6) == symbol]
    if mapped.empty:
        return
    benchmark_symbol = str(mapped.iloc[0].get("benchmark_symbol", ""))
    subset = benchmarks.loc[benchmarks["benchmark_symbol"].astype(str).str.zfill(6) == benchmark_symbol.zfill(6)]
    start = subset.loc[subset["trade_date"].astype(str) == start_date]
    end = subset.loc[subset["trade_date"].astype(str) == end_date]
    if start.empty or end.empty:
        return
    start_price = _numeric(start.iloc[0].get("close"))
    end_price = _numeric(end.iloc[0].get("close"))
    if start_price is None or end_price is None or start_price == 0:
        return
    bench_return = end_price / start_price - 1
    base["benchmark_symbol"] = benchmark_symbol
    base["benchmark_return"] = bench_return
    base["benchmark_relative_return"] = forward_return - bench_return


def _add_industry(base: dict[str, Any], symbol: str, start_date: str, end_date: str, forward_return: float, industries: pd.DataFrame, mapping: pd.DataFrame) -> None:
    if mapping.empty or industries.empty:
        return
    mapped = mapping.loc[mapping["symbol"].astype(str).str.zfill(6) == symbol]
    if mapped.empty:
        return
    industry_code = str(mapped.iloc[0].get("industry_code", ""))
    subset = industries.loc[industries["industry_code"].astype(str) == industry_code]
    start = subset.loc[subset["trade_date"].astype(str) == start_date]
    end = subset.loc[subset["trade_date"].astype(str) == end_date]
    if start.empty or end.empty:
        return
    start_price = _numeric(start.iloc[0].get("close"))
    end_price = _numeric(end.iloc[0].get("close"))
    if start_price is None or end_price is None or start_price == 0:
        return
    industry_return = end_price / start_price - 1
    base["industry_code"] = industry_code
    base["industry_name"] = mapped.iloc[0].get("industry_name", "")
    base["industry_return"] = industry_return
    base["industry_relative_return"] = forward_return - industry_return


def _metadata(result: ForwardReturnLabelResult) -> dict[str, Any]:
    payload = asdict(result)
    payload.pop("artifact_paths", None)
    for key in [
        "precondition_results",
        "lineage_results",
        "authority_results",
        "frozen_replay_decision_results",
        "price_input_results",
        "label_window_results",
        "benchmark_industry_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
    ]:
        payload[key] = [asdict(item) for item in getattr(result, key)]
    payload["artifact_paths"] = {key: str(value) for key, value in result.artifact_paths.items()}
    payload["execution_status"] = result.status
    payload["created_at"] = _now_iso()
    return payload


def _safety_flags(result: ForwardReturnLabelResult) -> dict[str, Any]:
    return {
        "forward_labels_allowed": result.forward_labels_allowed,
        "forward_labels_exist": result.forward_labels_exist,
        "forward_return_labels_created": result.forward_return_labels_created,
        "forward_return_label_executed": result.forward_return_label_executed,
        "forward_return_label_artifacts_created": result.forward_return_label_artifacts_created,
        **{field: getattr(result, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "message_sent": result.message_sent,
        "llm_api_called": result.llm_api_called,
        "external_api_called": result.external_api_called,
        "cache_mutated": result.cache_mutated,
        "data_raw_written": result.data_raw_written,
        "data_processed_written": result.data_processed_written,
        "data_cache_written": result.data_cache_written,
        "current_candidates_run": result.current_candidates_run,
        "snapshot_built": result.snapshot_built,
        "signal_semantics_changed": result.signal_semantics_changed,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
    }


def _artifact_paths(artifact_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "metadata.json",
        "report": artifact_dir / "forward_return_label_report.md",
        "forward_return_label_rows": artifact_dir / "forward_return_label_rows.csv",
        "forward_return_label_price_input_index": artifact_dir / "forward_return_label_price_input_index.csv",
        "forward_return_label_benchmark_index": artifact_dir / "forward_return_label_benchmark_index.csv",
        "forward_return_label_industry_index": artifact_dir / "forward_return_label_industry_index.csv",
        "safety_flags": artifact_dir / "safety_flags.json",
        "precondition_results": artifact_dir / "precondition_results.csv",
        "lineage_results": artifact_dir / "lineage_results.csv",
        "authority_results": artifact_dir / "authority_results.csv",
        "frozen_replay_decision_results": artifact_dir / "frozen_replay_decision_results.csv",
        "price_input_results": artifact_dir / "price_input_results.csv",
        "label_window_results": artifact_dir / "label_window_results.csv",
        "benchmark_industry_results": artifact_dir / "benchmark_industry_results.csv",
        "leakage_side_effect_guard_results": artifact_dir / "leakage_side_effect_guard_results.csv",
        "overclaim_guard_results": artifact_dir / "overclaim_guard_results.csv",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def _index_frame(result: ForwardReturnLabelResult, input_type: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "forward_return_label_run_id": result.forward_return_label_run_id,
                "input_type": input_type,
                "status": result.status,
                "row_count": result.replay_decision_row_count,
                "report_only": result.report_only,
                "diagnostic_only": result.diagnostic_only,
            }
        ]
    )


def _recommended_next_task(result: ForwardReturnLabelResult) -> str:
    if result.status == FORWARD_RETURN_LABELS_CREATED:
        return (
            "# Recommended Next Task\n\n"
            "Add Forward Return Label artifact views report-only, with index/health/status only after validating these diagnostics.\n"
        )
    return "# Recommended Next Task\n\nResolve blocker gates before rerunning report-only forward return label core.\n"


def _requested_labels(request: dict[str, Any]) -> list[str]:
    raw = request.get("label_names")
    if not raw:
        return DEFAULT_LABELS
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [part.strip() for part in str(raw).replace(",", ";").split(";") if part.strip()]


def _horizon_from_label(label: str) -> int:
    for part in label.split("_"):
        if part.endswith("d") and part[:-1].isdigit():
            return int(part[:-1])
    return 5


def _read_json_or_empty(path: Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _read_csv_or_empty(path: Path | None) -> pd.DataFrame:
    if path is None or not Path(path).exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype={"symbol": "string"})
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _write_gate_csv(path: Path, rows: list[ForwardReturnLabelGateResult]) -> None:
    _write_csv(path, pd.DataFrame([asdict(row) for row in rows]))


def _gate(
    gate_group: str,
    gate_name: str,
    status: str,
    passed: bool,
    blocker_reason: str,
    evidence_path: str,
    observed_value: str = "",
) -> ForwardReturnLabelGateResult:
    return ForwardReturnLabelGateResult(
        gate_group=gate_group,
        gate_name=gate_name,
        status=status,
        passed=passed,
        blocker_reason=blocker_reason,
        evidence_path=evidence_path,
        observed_value=observed_value,
    )


def _build_run_id(settings: ForwardReturnLabelSettings) -> str:
    payload = {
        "metadata": _path_text(settings.replay_decision_metadata_path),
        "rows": _path_text(settings.replay_decision_rows_path),
        "price": _path_text(settings.price_input_csv_path),
        "allow": settings.allow_forward_return_label,
        "time": _now_iso(),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _assert_manual_diagnostics_output(output_dir: Path) -> None:
    parts = {part.lower() for part in output_dir.parts}
    if "manual_diagnostics" not in parts:
        raise ValueError("Forward return label core may only write under outputs/reports/manual_diagnostics")


def _first_value(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    value = frame[column].iloc[0]
    if pd.isna(value):
        return ""
    return str(value)


def _first_non_empty(*values: object) -> str:
    for value in values:
        if value is not None and str(value):
            return str(value)
    return ""


def _numeric(value: object) -> float | None:
    try:
        if pd.isna(value):
            return None
        text = str(value).strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _path_text(path: Path | None) -> str:
    return "" if path is None else str(path)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
