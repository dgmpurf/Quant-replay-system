"""Status view for report-only factor definition schema fixture artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.factor_definition_schema_fixture import FORBIDDEN_METADATA_FALSE_FLAGS
from quant_replay_system.factor_definition_schema_fixture_health import check_factor_definition_schema_fixture_health
from quant_replay_system.factor_definition_schema_fixture_index import (
    FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED,
    FACTOR_DEFINITION_SCHEMA_FIXTURE_INVALID,
    NO_FACTOR_DEFINITION_SCHEMA_FIXTURE,
    build_factor_definition_schema_fixture_index,
)


SUMMARY_COLUMNS = [
    "latest_run_id",
    "status",
    "workflow_stage",
    "health_status",
    "factor_count",
    "taxonomy_layer_count",
    "validation_issue_count",
    "report_only",
    "diagnostic_only",
    "factor_definition_schema_fixture_created",
    "factor_definition_rows_created",
    "taxonomy_primary_classification",
    "legacy_12_factor_tags_checklist_only",
    *FORBIDDEN_METADATA_FALSE_FLAGS,
    "report_path",
    "next_action",
]

VIEWS_NEXT_ACTION = (
    "Factor Definition Schema Fixture core/views/research-status/checkpoint context is available "
    "as report-only schema-fixture governance. Run the post-checkpoint governance audit before "
    "any real factor observations, event ingestion, company exposure mappings, replay evidence "
    "bundles, signal_score implementation, model training, active weights, active thresholds, "
    "stock_profile validation, paper validation, buy-review, performance validation, current-candidates, "
    "snapshots, signal_semantics mutation, advisory predictions/probabilities, broker/order/message/API, "
    "or trading workflow. Do not treat fixture rows as live signals, factor observations, active "
    "factor library, model training inputs, active weights, active thresholds, stock_profile validation, "
    "buy-review, performance validation, or trading permission."
)


@dataclass(frozen=True)
class FactorDefinitionSchemaFixtureStatusResult:
    latest_run_id: str
    status: str
    workflow_stage: str
    health_status: str
    factor_count: int
    taxonomy_layer_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    factor_definition_schema_fixture_created: bool
    factor_definition_rows_created: bool
    taxonomy_primary_classification: bool
    legacy_12_factor_tags_checklist_only: bool
    signal_score_formula_active: bool
    signal_score_implemented: bool
    live_signals_created: bool
    signal_semantics_changed: bool
    factor_observations_created: bool
    event_ingestion_created: bool
    company_exposure_created: bool
    replay_evidence_bundle_created: bool
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
    active_stock_profile_created: bool
    operational_global_approved_for_paper_granted: bool
    report_path: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_factor_definition_schema_fixture_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/factor_definition_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/factor_definition_schema_fixture_v0_1/status",
) -> FactorDefinitionSchemaFixtureStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_factor_definition_schema_fixture_index(root=root, output_dir=sibling_root / "index")
    health = check_factor_definition_schema_fixture_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root)
    else:
        latest = index.index_frame.sort_values(["created_at", "factor_definition_schema_fixture_id"]).iloc[-1].to_dict()
        if health.status == "FAIL":
            result = _result_from_latest(
                latest,
                status="FAIL",
                stage=FACTOR_DEFINITION_SCHEMA_FIXTURE_INVALID,
                health_status=health.status,
                next_action=(
                    "Repair factor definition schema fixture artifacts before relying on view context. "
                    "Fixture rows are not live signals, factor observations, active factor library, model "
                    "training inputs, active weights, active thresholds, stock_profile validation, buy-review, "
                    "performance validation, or trading permission."
                ),
                output_dir=output_dir,
                root=root,
            )
        else:
            result = _result_from_latest(
                latest,
                status="PASS",
                stage=FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED,
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
) -> FactorDefinitionSchemaFixtureStatusResult:
    summary = {
        "latest_run_id": _text(latest.get("factor_definition_schema_fixture_id")),
        "status": status,
        "workflow_stage": stage,
        "health_status": health_status,
        "factor_count": _to_int(latest.get("factor_count")),
        "taxonomy_layer_count": _to_int(latest.get("taxonomy_layer_count")),
        "validation_issue_count": _to_int(latest.get("validation_issue_count")),
        "report_only": _to_bool(latest.get("report_only")),
        "diagnostic_only": _to_bool(latest.get("diagnostic_only")),
        "factor_definition_schema_fixture_created": _to_bool(latest.get("factor_definition_schema_fixture_created")),
        "factor_definition_rows_created": _to_bool(latest.get("factor_definition_rows_created")),
        "taxonomy_primary_classification": _to_bool(latest.get("taxonomy_primary_classification")),
        "legacy_12_factor_tags_checklist_only": _to_bool(latest.get("legacy_12_factor_tags_checklist_only")),
        **{flag: _to_bool(latest.get(flag)) for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
        "report_path": _text(latest.get("limitations_path")),
        "next_action": next_action,
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return FactorDefinitionSchemaFixtureStatusResult(
        latest_run_id=summary["latest_run_id"],
        status=status,
        workflow_stage=stage,
        health_status=health_status,
        factor_count=summary["factor_count"],
        taxonomy_layer_count=summary["taxonomy_layer_count"],
        validation_issue_count=summary["validation_issue_count"],
        report_only=summary["report_only"],
        diagnostic_only=summary["diagnostic_only"],
        factor_definition_schema_fixture_created=summary["factor_definition_schema_fixture_created"],
        factor_definition_rows_created=summary["factor_definition_rows_created"],
        taxonomy_primary_classification=summary["taxonomy_primary_classification"],
        legacy_12_factor_tags_checklist_only=summary["legacy_12_factor_tags_checklist_only"],
        report_path=summary["report_path"],
        next_action=next_action,
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[] if health_status == "PASS" else [f"Factor definition schema fixture health is {health_status}."],
        audit_metadata=_audit_metadata(root),
        **{flag: summary[flag] for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    )


def _no_artifact_result(output_dir: str | Path, root: str | Path) -> FactorDefinitionSchemaFixtureStatusResult:
    summary = {
        "latest_run_id": "",
        "status": "PASS",
        "workflow_stage": NO_FACTOR_DEFINITION_SCHEMA_FIXTURE,
        "health_status": "PASS",
        "factor_count": 0,
        "taxonomy_layer_count": 0,
        "validation_issue_count": 0,
        "report_only": True,
        "diagnostic_only": True,
        "factor_definition_schema_fixture_created": False,
        "factor_definition_rows_created": False,
        "taxonomy_primary_classification": False,
        "legacy_12_factor_tags_checklist_only": False,
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
        "report_path": "",
        "next_action": "Run factor-definition-schema-fixture to create report-only factor definition schema fixture artifacts.",
    }
    paths = _paths(output_dir)
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return FactorDefinitionSchemaFixtureStatusResult(
        latest_run_id="",
        status="PASS",
        workflow_stage=NO_FACTOR_DEFINITION_SCHEMA_FIXTURE,
        health_status="PASS",
        factor_count=0,
        taxonomy_layer_count=0,
        validation_issue_count=0,
        report_only=True,
        diagnostic_only=True,
        factor_definition_schema_fixture_created=False,
        factor_definition_rows_created=False,
        taxonomy_primary_classification=False,
        legacy_12_factor_tags_checklist_only=False,
        report_path="",
        next_action=summary["next_action"],
        summary_frame=frame,
        artifact_paths=paths,
        warnings=[f"No factor definition schema fixture artifacts found under {root}."],
        audit_metadata=_audit_metadata(root),
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    )


def _write(result: FactorDefinitionSchemaFixtureStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Factor Definition Schema Fixture Status",
                "",
                f"- status: {result.status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_run_id: {result.latest_run_id}",
                f"- health_status: {result.health_status}",
                f"- factor_count: {result.factor_count}",
                f"- taxonomy_layer_count: {result.taxonomy_layer_count}",
                f"- validation_issue_count: {result.validation_issue_count}",
                f"- report_only: {result.report_only}",
                f"- diagnostic_only: {result.diagnostic_only}",
                f"- factor_definition_schema_fixture_created: {result.factor_definition_schema_fixture_created}",
                "",
                "This is a report-only factor definition schema fixture status view.",
                "It does not create factor observations, event ingestion, company exposure mappings, replay evidence bundles, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, broker behavior, API calls, orders, messages, advisory predictions, probabilities, or trading.",
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
        "factor_count": result.factor_count,
        "taxonomy_layer_count": result.taxonomy_layer_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "factor_definition_schema_fixture_created": result.factor_definition_schema_fixture_created,
        "factor_definition_rows_created": result.factor_definition_rows_created,
        "taxonomy_primary_classification": result.taxonomy_primary_classification,
        "legacy_12_factor_tags_checklist_only": result.legacy_12_factor_tags_checklist_only,
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
        "status_csv": artifact_dir / "factor_definition_schema_fixture_status.csv",
        "status_report": artifact_dir / "factor_definition_schema_fixture_status_report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _audit_metadata(root: str | Path) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "report_only": True,
        "diagnostic_only": True,
        "factor_definition_schema_fixture_status_created": True,
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
