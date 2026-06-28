"""Status view for report-only replay decision schema fixture artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.replay_decision_schema_fixture import FORBIDDEN_METADATA_FALSE_FLAGS
from quant_replay_system.replay_decision_schema_fixture_health import check_replay_decision_schema_fixture_health
from quant_replay_system.replay_decision_schema_fixture_index import (
    CONTEXT_METADATA_FLAGS,
    NO_REPLAY_DECISION_SCHEMA_FIXTURE,
    REPLAY_DECISION_SCHEMA_FIXTURE_CREATED,
    REPLAY_DECISION_SCHEMA_FIXTURE_INVALID,
    build_replay_decision_schema_fixture_index,
)


SUMMARY_COLUMNS = [
    "latest_run_id",
    "status",
    "workflow_stage",
    "health_status",
    "decision_count",
    "validation_issue_count",
    "report_only",
    "diagnostic_only",
    "replay_decision_schema_fixture_created",
    "replay_decision_rows_created",
    *CONTEXT_METADATA_FLAGS,
    *FORBIDDEN_METADATA_FALSE_FLAGS,
    "report_path",
    "next_action",
]

VIEWS_NEXT_ACTION = (
    "Replay Decision Schema Fixture core/views/research-status/checkpoint context is available as "
    "report-only schema-fixture governance. Review the checkpoint and run post-checkpoint governance "
    "audit before any real replay decision, real replay evidence bundle consumption, forward label, "
    "future label join, signal_score input, model training input, active weights, active thresholds, "
    "stock_profile validation, paper validation, buy-review, performance validation, current-candidates, "
    "snapshots, signal_semantics mutation, broker/order/message/API behavior, or trading workflow."
)


@dataclass(frozen=True)
class ReplayDecisionSchemaFixtureStatusResult:
    latest_run_id: str
    status: str
    workflow_stage: str
    health_status: str
    decision_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    replay_decision_schema_fixture_created: bool
    replay_decision_rows_created: bool
    replay_evidence_bundle_schema_fixture_used: bool
    real_replay_decisions_created: bool
    real_replay_evidence_bundle_used: bool
    forward_labels_created: bool
    future_labels_joined: bool
    signal_score_implemented: bool
    signal_score_input_authorized: bool
    model_training_performed: bool
    active_weights_created: bool
    active_thresholds_created: bool
    stock_profile_validation_created: bool
    paper_validation_created: bool
    real_buy_review_eligible: bool
    buy_review_allowed: bool
    strategy_performance_validated: bool
    trading_allowed: bool
    live_trading_enabled: bool
    broker_api_called: bool
    external_api_called: bool
    llm_api_called: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    active_stock_profile_created: bool
    operational_global_approved_for_paper_granted: bool
    report_path: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_replay_decision_schema_fixture_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/replay_decision_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/replay_decision_schema_fixture_v0_1/status",
) -> ReplayDecisionSchemaFixtureStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_replay_decision_schema_fixture_index(root=root, output_dir=sibling_root / "index")
    health = check_replay_decision_schema_fixture_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "replay_decision_schema_fixture_id"]).iloc[-1].to_dict()
        if health.status == "FAIL":
            result = _result_from_latest(
                latest,
                status="FAIL",
                stage=REPLAY_DECISION_SCHEMA_FIXTURE_INVALID,
                health_status=health.status,
                next_action=(
                    "Repair replay decision schema fixture artifacts before relying on view context. "
                    "Fixture rows are not real replay decisions, real replay evidence bundle consumption, "
                    "forward labels, future labels, signal_score inputs, model training inputs, active weights, "
                    "active thresholds, stock_profile validation, buy-review, performance validation, or trading permission."
                ),
                output_dir=output_dir,
                root=root,
            )
        else:
            result = _result_from_latest(
                latest,
                status="PASS",
                stage=REPLAY_DECISION_SCHEMA_FIXTURE_CREATED,
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
) -> ReplayDecisionSchemaFixtureStatusResult:
    summary = {
        "latest_run_id": _text(latest.get("replay_decision_schema_fixture_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "decision_count": _to_int(latest.get("decision_count")),
        "validation_issue_count": _to_int(latest.get("validation_issue_count")),
        "report_only": _to_bool(latest.get("report_only")),
        "diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        "replay_decision_schema_fixture_created": _to_bool(latest.get("replay_decision_schema_fixture_created")),
        "replay_decision_rows_created": _to_bool(latest.get("replay_decision_rows_created")),
        **{flag: _to_bool(latest.get(flag)) for flag in CONTEXT_METADATA_FLAGS},
        **{flag: _to_bool(latest.get(flag)) for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
        "report_path": _text(latest.get("limitations_path")),
        "next_action": next_action,
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ReplayDecisionSchemaFixtureStatusResult(
        latest_run_id=summary["latest_run_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        decision_count=summary["decision_count"],
        validation_issue_count=summary["validation_issue_count"],
        report_only=summary["report_only"],
        diagnostic_only=summary["diagnostic_only"],
        replay_decision_schema_fixture_created=summary["replay_decision_schema_fixture_created"],
        replay_decision_rows_created=summary["replay_decision_rows_created"],
        replay_evidence_bundle_schema_fixture_used=summary["replay_evidence_bundle_schema_fixture_used"],
        report_path=summary["report_path"],
        next_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"Replay decision schema fixture health is {health_status}."],
        audit_metadata=_audit_metadata(root),
        **{flag: summary[flag] for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> ReplayDecisionSchemaFixtureStatusResult:
    summary = {
        "latest_run_id": "",
        "status": "PASS",
        "workflow_stage": NO_REPLAY_DECISION_SCHEMA_FIXTURE,
        "health_status": "PASS",
        "decision_count": 0,
        "validation_issue_count": 0,
        "report_only": True,
        "diagnostic_only": True,
        "replay_decision_schema_fixture_created": False,
        "replay_decision_rows_created": False,
        **{flag: False for flag in CONTEXT_METADATA_FLAGS},
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
        "report_path": "",
        "next_action": "Run replay-decision-schema-fixture to create report-only replay decision schema fixture artifacts.",
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ReplayDecisionSchemaFixtureStatusResult(
        latest_run_id="",
        status="PASS",
        workflow_stage=NO_REPLAY_DECISION_SCHEMA_FIXTURE,
        health_status="PASS",
        decision_count=0,
        validation_issue_count=0,
        report_only=True,
        diagnostic_only=True,
        replay_decision_schema_fixture_created=False,
        replay_decision_rows_created=False,
        replay_evidence_bundle_schema_fixture_used=False,
        report_path="",
        next_action=summary["next_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No replay decision schema fixture artifacts found under {root}."],
        audit_metadata=_audit_metadata(root),
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    )


def _write(result: ReplayDecisionSchemaFixtureStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Replay Decision Schema Fixture Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_run_id: {result.latest_run_id}",
                f"- health_status: {result.health_status}",
                f"- decision_count: {result.decision_count}",
                f"- validation_issue_count: {result.validation_issue_count}",
                "",
                "This is a report-only replay decision schema fixture status view. It does not create real replay decisions, real replay evidence bundle consumption, forward labels, future labels joined, signal_score input authorization, model training inputs, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, broker behavior, API calls, orders, messages, current-candidates, snapshots, signal_semantics mutation, or trading.",
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
        "decision_count": result.decision_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "replay_decision_schema_fixture_created": result.replay_decision_schema_fixture_created,
        "replay_decision_rows_created": result.replay_decision_rows_created,
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
        "status_csv": artifact_dir / "replay_decision_schema_fixture_status.csv",
        "status_report": artifact_dir / "replay_decision_schema_fixture_status_report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _audit_metadata(root: str | Path) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "report_only": True,
        "diagnostic_only": True,
        "replay_decision_schema_fixture_status_created": True,
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
