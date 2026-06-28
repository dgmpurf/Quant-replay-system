"""Status view for report-only forward return label schema fixture artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.forward_return_label_schema_fixture import FORBIDDEN_METADATA_FALSE_FLAGS
from quant_replay_system.forward_return_label_schema_fixture_health import check_forward_return_label_schema_fixture_health
from quant_replay_system.forward_return_label_schema_fixture_index import (
    FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED,
    FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_INVALID,
    NO_FORWARD_RETURN_LABEL_SCHEMA_FIXTURE,
    ROW_CONTEXT_FLAGS,
    build_forward_return_label_schema_fixture_index,
)


SUMMARY_COLUMNS = [
    "latest_run_id",
    "status",
    "workflow_stage",
    "health_status",
    "label_count",
    "validation_issue_count",
    "report_only",
    "diagnostic_only",
    "schema_fixture",
    *ROW_CONTEXT_FLAGS,
    *FORBIDDEN_METADATA_FALSE_FLAGS,
    "report_path",
    "next_action",
]

VIEWS_NEXT_ACTION = "Forward Return Label Schema Fixture Research-Status and Checkpoint Report-Only v0.1"


@dataclass(frozen=True)
class ForwardReturnLabelSchemaFixtureStatusResult:
    latest_run_id: str
    status: str
    workflow_stage: str
    health_status: str
    label_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    schema_fixture: bool
    future_label_joined_to_decision_input: bool
    real_forward_labels_created: bool
    future_labels_joined: bool
    signal_score_implemented: bool
    signal_score_input_authorized: bool
    model_training_performed: bool
    model_training_input_authorized: bool
    active_weights_created: bool
    active_thresholds_created: bool
    stock_profile_validation_created: bool
    paper_validation_created: bool
    real_buy_review_eligible: bool
    buy_review_allowed: bool
    strategy_performance_validated: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    broker_api_called: bool
    external_api_called: bool
    llm_api_called: bool
    message_sent: bool
    order_placed: bool
    trading_allowed: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    report_path: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_forward_return_label_schema_fixture_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/forward_return_label_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/forward_return_label_schema_fixture_v0_1/status",
) -> ForwardReturnLabelSchemaFixtureStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_forward_return_label_schema_fixture_index(root=root, output_dir=sibling_root / "index")
    health = check_forward_return_label_schema_fixture_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "forward_return_label_schema_fixture_id"]).iloc[-1].to_dict()
        if health.status == "FAIL":
            result = _result_from_latest(
                latest,
                status="FAIL",
                stage=FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_INVALID,
                health_status=health.status,
                next_action=(
                    "Repair forward return label schema fixture artifacts before relying on view context. "
                    "Fixture rows are not real forward labels, future-label joins, signal_score inputs, "
                    "model training inputs, stock_profile validation, buy-review, performance validation, or trading permission."
                ),
                output_dir=output_dir,
                root=root,
            )
        else:
            result = _result_from_latest(
                latest,
                status="PASS",
                stage=FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED,
                health_status=health.status,
                next_action=VIEWS_NEXT_ACTION,
                output_dir=output_dir,
                root=root,
            )
    _write(result)
    return result


def _result_from_latest(
    latest: dict[str, Any],
    *,
    status: str,
    stage: str,
    health_status: str,
    next_action: str,
    output_dir: str | Path,
    root: str | Path,
) -> ForwardReturnLabelSchemaFixtureStatusResult:
    summary = {
        "latest_run_id": _text(latest.get("forward_return_label_schema_fixture_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "label_count": _to_int(latest.get("label_count")),
        "validation_issue_count": _to_int(latest.get("validation_issue_count")),
        "report_only": _to_bool(latest.get("report_only")),
        "diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        "schema_fixture": _to_bool(latest.get("schema_fixture")),
        **{flag: _to_bool(latest.get(flag)) for flag in ROW_CONTEXT_FLAGS},
        **{flag: _to_bool(latest.get(flag)) for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
        "report_path": _text(latest.get("report_path")),
        "next_action": next_action,
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ForwardReturnLabelSchemaFixtureStatusResult(
        latest_run_id=summary["latest_run_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        label_count=summary["label_count"],
        validation_issue_count=summary["validation_issue_count"],
        report_only=summary["report_only"],
        diagnostic_only=summary["diagnostic_only"],
        schema_fixture=summary["schema_fixture"],
        report_path=summary["report_path"],
        next_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"Forward return label schema fixture health is {health_status}."],
        audit_metadata=_audit_metadata(root),
        **{flag: summary[flag] for flag in ROW_CONTEXT_FLAGS},
        **{flag: summary[flag] for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> ForwardReturnLabelSchemaFixtureStatusResult:
    summary = {
        "latest_run_id": "",
        "status": "PASS",
        "workflow_stage": NO_FORWARD_RETURN_LABEL_SCHEMA_FIXTURE,
        "health_status": "PASS",
        "label_count": 0,
        "validation_issue_count": 0,
        "report_only": True,
        "diagnostic_only": True,
        "schema_fixture": False,
        **{flag: False for flag in ROW_CONTEXT_FLAGS},
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
        "report_path": "",
        "next_action": "Run forward-return-label-schema-fixture to create report-only forward return label schema fixture artifacts.",
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ForwardReturnLabelSchemaFixtureStatusResult(
        latest_run_id="",
        status="PASS",
        workflow_stage=NO_FORWARD_RETURN_LABEL_SCHEMA_FIXTURE,
        health_status="PASS",
        label_count=0,
        validation_issue_count=0,
        report_only=True,
        diagnostic_only=True,
        schema_fixture=False,
        report_path="",
        next_action=summary["next_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No forward return label schema fixture artifacts found under {root}."],
        audit_metadata=_audit_metadata(root),
        **{flag: False for flag in ROW_CONTEXT_FLAGS},
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    )


def _write(result: ForwardReturnLabelSchemaFixtureStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Forward Return Label Schema Fixture Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_run_id: {result.latest_run_id}",
                f"- health_status: {result.health_status}",
                f"- label_count: {result.label_count}",
                f"- validation_issue_count: {result.validation_issue_count}",
                "",
                "This is a report-only forward return label schema fixture status view. It does not create real forward labels, future-label joins, replay execution, metric computation, signal_score inputs, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/order/message/API behavior, or trading.",
                "",
                f"Next action: {result.next_action}",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "latest_run_id": result.latest_run_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "health_status": result.health_status,
        "label_count": result.label_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "schema_fixture": result.schema_fixture,
        **{flag: getattr(result, flag) for flag in ROW_CONTEXT_FLAGS},
        **{flag: getattr(result, flag) for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
        "report_path": result.report_path,
        "next_action": result.next_action,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _paths(output_dir: str | Path) -> dict[str, Path]:
    artifact_dir = Path(output_dir)
    return {
        "artifact_dir": artifact_dir,
        "status_csv": artifact_dir / "forward_return_label_schema_fixture_status.csv",
        "status_report": artifact_dir / "forward_return_label_schema_fixture_status_report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _audit_metadata(root: str | Path) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "report_only": True,
        "diagnostic_only": True,
        "forward_return_label_schema_fixture_status_created": True,
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
