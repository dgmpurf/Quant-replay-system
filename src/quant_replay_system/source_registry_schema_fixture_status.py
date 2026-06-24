"""Status view for report-only source registry schema fixture artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.source_registry_schema_fixture import FORBIDDEN_SIDE_EFFECT_FLAGS
from quant_replay_system.source_registry_schema_fixture_health import check_source_registry_schema_fixture_health
from quant_replay_system.source_registry_schema_fixture_index import (
    NO_SOURCE_REGISTRY_SCHEMA_FIXTURE,
    SOURCE_REGISTRY_SCHEMA_FIXTURE_CREATED,
    SOURCE_REGISTRY_SCHEMA_FIXTURE_INVALID,
    build_source_registry_schema_fixture_index,
)


SUMMARY_COLUMNS = [
    "latest_run_id",
    "status",
    "workflow_stage",
    "health_status",
    "source_count",
    "validation_issue_count",
    "report_only",
    "diagnostic_only",
    "source_registry_schema_fixture_created",
    *FORBIDDEN_SIDE_EFFECT_FLAGS,
    "report_path",
    "next_action",
]

POST_CHECKPOINT_NEXT_ACTION = (
    "Source Registry Schema Fixture core/views/research-status/checkpoint context is available as "
    "report-only schema-fixture governance. Review the checkpoint and run post-checkpoint governance "
    "audit before any raw document store, real source registry, production source permission, replay "
    "input, buy-review, performance validation, or trading workflow."
)


@dataclass(frozen=True)
class SourceRegistrySchemaFixtureStatusResult:
    latest_run_id: str
    status: str
    workflow_stage: str
    health_status: str
    source_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    source_registry_schema_fixture_created: bool
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
    real_buy_review_eligible: bool
    buy_review_allowed: bool
    strategy_performance_validated: bool
    trading_allowed: bool
    operational_global_approved_for_paper_granted: bool
    report_path: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_source_registry_schema_fixture_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/source_registry_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/source_registry_schema_fixture_v0_1/status",
) -> SourceRegistrySchemaFixtureStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_source_registry_schema_fixture_index(root=root, output_dir=sibling_root / "index")
    health = check_source_registry_schema_fixture_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "source_registry_schema_fixture_id"]).iloc[-1].to_dict()
        if health.status == "FAIL":
            result = _result_from_latest(
                latest,
                status="FAIL",
                stage=SOURCE_REGISTRY_SCHEMA_FIXTURE_INVALID,
                health_status=health.status,
                next_action=(
                    "Repair source registry schema fixture artifacts, then review the checkpoint and run "
                    "post-checkpoint governance audit before any raw document store, real source registry, "
                    "production source permission, replay input, buy-review, performance validation, or "
                    "trading workflow. Fixture rows are not production sources."
                ),
                output_dir=output_dir,
                root=root,
            )
        else:
            result = _result_from_latest(
                latest,
                status="PASS",
                stage=SOURCE_REGISTRY_SCHEMA_FIXTURE_CREATED,
                health_status=health.status,
                next_action=POST_CHECKPOINT_NEXT_ACTION,
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
) -> SourceRegistrySchemaFixtureStatusResult:
    summary = {
        "latest_run_id": _text(latest.get("source_registry_schema_fixture_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "source_count": _to_int(latest.get("source_count")),
        "validation_issue_count": _to_int(latest.get("validation_issue_count")),
        "report_only": _to_bool(latest.get("report_only")),
        "diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        "source_registry_schema_fixture_created": _to_bool(latest.get("source_registry_schema_fixture_created")),
        **{flag: _to_bool(latest.get(flag)) for flag in FORBIDDEN_SIDE_EFFECT_FLAGS},
        "report_path": _text(latest.get("limitations_path")),
        "next_action": next_action,
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return SourceRegistrySchemaFixtureStatusResult(
        latest_run_id=summary["latest_run_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        source_count=summary["source_count"],
        validation_issue_count=summary["validation_issue_count"],
        report_only=summary["report_only"],
        diagnostic_only=summary["diagnostic_only"],
        source_registry_schema_fixture_created=summary["source_registry_schema_fixture_created"],
        report_path=summary["report_path"],
        next_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"Source registry schema fixture health is {health_status}."],
        audit_metadata=_audit_metadata(root),
        **{flag: summary[flag] for flag in FORBIDDEN_SIDE_EFFECT_FLAGS},
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> SourceRegistrySchemaFixtureStatusResult:
    summary = {
        "latest_run_id": "",
        "status": "PASS",
        "workflow_stage": NO_SOURCE_REGISTRY_SCHEMA_FIXTURE,
        "health_status": "PASS",
        "source_count": 0,
        "validation_issue_count": 0,
        "report_only": True,
        "diagnostic_only": True,
        "source_registry_schema_fixture_created": False,
        **{flag: False for flag in FORBIDDEN_SIDE_EFFECT_FLAGS},
        "report_path": "",
        "next_action": "Run source-registry-schema-fixture to create report-only source registry fixture artifacts.",
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return SourceRegistrySchemaFixtureStatusResult(
        latest_run_id="",
        status="PASS",
        workflow_stage=NO_SOURCE_REGISTRY_SCHEMA_FIXTURE,
        health_status="PASS",
        source_count=0,
        validation_issue_count=0,
        report_only=True,
        diagnostic_only=True,
        source_registry_schema_fixture_created=False,
        report_path="",
        next_action=summary["next_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No source registry schema fixture artifacts found under {root}."],
        audit_metadata=_audit_metadata(root),
        **{flag: False for flag in FORBIDDEN_SIDE_EFFECT_FLAGS},
    )


def _write(result: SourceRegistrySchemaFixtureStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Source Registry Schema Fixture Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_run_id: {result.latest_run_id}",
                f"- health_status: {result.health_status}",
                f"- source_count: {result.source_count}",
                f"- validation_issue_count: {result.validation_issue_count}",
                f"- report_only: {result.report_only}",
                f"- diagnostic_only: {result.diagnostic_only}",
                f"- source_registry_schema_fixture_created: {result.source_registry_schema_fixture_created}",
                "",
                "This is a report-only source registry schema fixture status view.",
                "It does not grant real source permission.",
                "It does not create production source readiness.",
                "It does not create buy-review eligibility, performance validation, broker behavior, API calls, orders, messages, or trading.",
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
        "source_count": result.source_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "source_registry_schema_fixture_created": result.source_registry_schema_fixture_created,
        **{flag: getattr(result, flag) for flag in FORBIDDEN_SIDE_EFFECT_FLAGS},
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
        "status_csv": artifact_dir / "source_registry_schema_fixture_status.csv",
        "status_report": artifact_dir / "source_registry_schema_fixture_status_report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _audit_metadata(root: str | Path) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "report_only": True,
        "diagnostic_only": True,
        "source_registry_schema_fixture_status_created": True,
        **{flag: False for flag in FORBIDDEN_SIDE_EFFECT_FLAGS},
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
