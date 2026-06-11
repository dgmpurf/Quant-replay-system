"""Status view for report-only replay substrate schema fixture artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.replay_substrate_schema_fixture_health import (
    check_replay_substrate_schema_fixture_health,
)
from quant_replay_system.replay_substrate_schema_fixture_index import (
    build_replay_substrate_schema_fixture_index,
)


NO_REPLAY_SUBSTRATE_SCHEMA_FIXTURE = "NO_REPLAY_SUBSTRATE_SCHEMA_FIXTURE"
REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY = "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY"
REPLAY_SUBSTRATE_SCHEMA_FIXTURE_HEALTH_WARN = "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_HEALTH_WARN"
REPLAY_SUBSTRATE_SCHEMA_FIXTURE_FAILED = "REPLAY_SUBSTRATE_SCHEMA_FIXTURE_FAILED"

SUMMARY_COLUMNS = [
    "latest_fixture_id",
    "status",
    "workflow_stage",
    "health_status",
    "entity_count",
    "validation_issue_count",
    "overclaim_guard_status",
    "overclaim_guard_pass_count",
    "overclaim_guard_total_count",
    "active_replay_input",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
    "report_only",
    "diagnostic_only",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "report_path",
    "next_manual_action",
]


@dataclass(frozen=True)
class ReplaySubstrateSchemaFixtureStatusResult:
    latest_fixture_id: str
    status: str
    workflow_stage: str
    health_status: str
    entity_count: int
    validation_issue_count: int
    overclaim_guard_status: str
    overclaim_guard_pass_count: int
    overclaim_guard_total_count: int
    active_replay_input: bool
    forward_labels_exist: bool
    weights_trained: bool
    active_stock_profile_exists: bool
    real_buy_review_eligible: bool
    report_only: bool
    diagnostic_only: bool
    no_live_trading: bool
    no_broker_api: bool
    no_order_placement: bool
    report_path: str
    next_manual_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_replay_substrate_schema_fixture_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/status",
) -> ReplaySubstrateSchemaFixtureStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_replay_substrate_schema_fixture_index(root=root, output_dir=sibling_root / "index")
    health = check_replay_substrate_schema_fixture_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "fixture_id"]).iloc[-1].to_dict()
        if health.status == "FAIL":
            status = "FAIL"
            stage = REPLAY_SUBSTRATE_SCHEMA_FIXTURE_FAILED
            next_action = "Repair replay-substrate schema fixture artifacts before adding research-status integration."
        elif health.status == "WARN":
            status = "WARN"
            stage = REPLAY_SUBSTRATE_SCHEMA_FIXTURE_HEALTH_WARN
            next_action = "Review fixture warnings; keep this as report-only context."
        else:
            status = "PASS"
            stage = REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY
            next_action = "This is a report-only replay substrate schema fixture. Add index/health/status hardening or research-status integration next; do not run real replay, labels, training, stock-profile validation, or buy-review eligibility."
        result = _result_from_latest(latest, status, stage, health.status, next_action, output_dir, root)
    _write(result)
    return result


def _result_from_latest(
    latest: dict[str, Any],
    status: str,
    stage: str,
    health_status: str,
    next_action: str,
    output_dir: str | Path,
    root: str | Path,
) -> ReplaySubstrateSchemaFixtureStatusResult:
    overclaim_guard_status = (
        "PASS"
        if _to_int(latest.get("overclaim_guard_total_count")) > 0
        and _to_int(latest.get("overclaim_guard_pass_count")) == _to_int(latest.get("overclaim_guard_total_count"))
        else "FAIL"
    )
    summary = {
        "latest_fixture_id": _text(latest.get("fixture_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "entity_count": _to_int(latest.get("entity_count")),
        "validation_issue_count": _to_int(latest.get("validation_issue_count")),
        "overclaim_guard_status": overclaim_guard_status,
        "overclaim_guard_pass_count": _to_int(latest.get("overclaim_guard_pass_count")),
        "overclaim_guard_total_count": _to_int(latest.get("overclaim_guard_total_count")),
        "active_replay_input": False,
        "forward_labels_exist": _to_bool(latest.get("forward_labels_computed")),
        "weights_trained": _to_bool(latest.get("weights_trained")),
        "active_stock_profile_exists": _to_bool(latest.get("active_stock_profile_created")),
        "real_buy_review_eligible": _to_bool(latest.get("real_buy_review_eligible")),
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "report_path": _text(latest.get("report_path")),
        "next_manual_action": next_action,
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ReplaySubstrateSchemaFixtureStatusResult(
        latest_fixture_id=summary["latest_fixture_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        entity_count=summary["entity_count"],
        validation_issue_count=summary["validation_issue_count"],
        overclaim_guard_status=overclaim_guard_status,
        overclaim_guard_pass_count=summary["overclaim_guard_pass_count"],
        overclaim_guard_total_count=summary["overclaim_guard_total_count"],
        active_replay_input=False,
        forward_labels_exist=summary["forward_labels_exist"],
        weights_trained=summary["weights_trained"],
        active_stock_profile_exists=summary["active_stock_profile_exists"],
        real_buy_review_eligible=summary["real_buy_review_eligible"],
        report_only=True,
        diagnostic_only=True,
        no_live_trading=True,
        no_broker_api=True,
        no_order_placement=True,
        report_path=summary["report_path"],
        next_manual_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"Replay substrate schema fixture health is {health_status}."],
        audit_metadata=_audit_metadata(root),
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> ReplaySubstrateSchemaFixtureStatusResult:
    summary = {
        "latest_fixture_id": "",
        "status": "WARN",
        "workflow_stage": NO_REPLAY_SUBSTRATE_SCHEMA_FIXTURE,
        "health_status": "FAIL",
        "entity_count": 0,
        "validation_issue_count": 0,
        "overclaim_guard_status": "MISSING",
        "overclaim_guard_pass_count": 0,
        "overclaim_guard_total_count": 0,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "report_path": "",
        "next_manual_action": "Run replay-substrate-schema-fixture to create report-only schema fixtures.",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return ReplaySubstrateSchemaFixtureStatusResult(
        latest_fixture_id="",
        status="WARN",
        workflow_stage=NO_REPLAY_SUBSTRATE_SCHEMA_FIXTURE,
        health_status="FAIL",
        entity_count=0,
        validation_issue_count=0,
        overclaim_guard_status="MISSING",
        overclaim_guard_pass_count=0,
        overclaim_guard_total_count=0,
        active_replay_input=False,
        forward_labels_exist=False,
        weights_trained=False,
        active_stock_profile_exists=False,
        real_buy_review_eligible=False,
        report_only=True,
        diagnostic_only=True,
        no_live_trading=True,
        no_broker_api=True,
        no_order_placement=True,
        report_path="",
        next_manual_action=summary["next_manual_action"],
        summary_frame=frame,
        artifact_paths=_paths(output_dir),
        warnings=[f"No replay substrate schema fixture artifacts found under {root}."],
        audit_metadata=_audit_metadata(root),
    )


def _write(result: ReplaySubstrateSchemaFixtureStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Replay Substrate Schema Fixture Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_fixture_id: {result.latest_fixture_id}",
                f"- health_status: {result.health_status}",
                f"- entity_count: {result.entity_count}",
                f"- validation_issue_count: {result.validation_issue_count}",
                f"- overclaim_guard_status: {result.overclaim_guard_status}",
                f"- overclaim_guard_pass_count: {result.overclaim_guard_pass_count}",
                f"- overclaim_guard_total_count: {result.overclaim_guard_total_count}",
                f"- active_replay_input: {result.active_replay_input}",
                f"- forward_labels_exist: {result.forward_labels_exist}",
                f"- weights_trained: {result.weights_trained}",
                f"- active_stock_profile_exists: {result.active_stock_profile_exists}",
                f"- real_buy_review_eligible: {result.real_buy_review_eligible}",
                f"- report_only: {result.report_only}",
                f"- diagnostic_only: {result.diagnostic_only}",
                f"- no_live_trading: {result.no_live_trading}",
                f"- no_broker_api: {result.no_broker_api}",
                f"- no_order_placement: {result.no_order_placement}",
                "",
                "This is a report-only replay substrate schema fixture.",
                "It is not real replay.",
                "It is not forward-label computation.",
                "It is not training.",
                "It is not stock-profile validation.",
                "It is not real buy-review eligibility.",
                "",
                f"Next action: {result.next_manual_action}",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "latest_fixture_id": result.latest_fixture_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "health_status": result.health_status,
        "entity_count": result.entity_count,
        "validation_issue_count": result.validation_issue_count,
        "overclaim_guard_status": result.overclaim_guard_status,
        "overclaim_guard_pass_count": result.overclaim_guard_pass_count,
        "overclaim_guard_total_count": result.overclaim_guard_total_count,
        "active_replay_input": result.active_replay_input,
        "forward_labels_exist": result.forward_labels_exist,
        "weights_trained": result.weights_trained,
        "active_stock_profile_exists": result.active_stock_profile_exists,
        "real_buy_review_eligible": result.real_buy_review_eligible,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "no_live_trading": result.no_live_trading,
        "no_broker_api": result.no_broker_api,
        "no_order_placement": result.no_order_placement,
        "report_path": result.report_path,
        "next_manual_action": result.next_manual_action,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _paths(output_dir: str | Path) -> dict[str, Path]:
    artifact_dir = Path(output_dir)
    return {
        "artifact_dir": artifact_dir,
        "status_csv": artifact_dir / "replay_substrate_schema_fixture_status.csv",
        "status_report": artifact_dir / "replay_substrate_schema_fixture_status_report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _audit_metadata(root: str | Path) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_forward_labels_computed": True,
        "no_weights_trained": True,
        "no_active_stock_profile_created": True,
        "real_buy_review_eligible": False,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_data_cache_write": True,
        "no_cache_mutation": True,
    }


def _hash_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(value), sort_keys=True).encode("utf-8")).hexdigest()[:12]


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
