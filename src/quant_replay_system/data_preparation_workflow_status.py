"""Local-only data preparation workflow status dashboard."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import DataPreparationWorkflowStatusSettings, Settings, load_settings


DATA_PREP_WORKFLOW_STATUS_LIMITATIONS = [
    "Scans local artifact metadata only.",
    "Does not regenerate missing artifacts or rerun data preparation steps.",
    "Does not fetch real data, call market data APIs, connect to brokers, or place orders.",
    "Stage inference is conservative when artifacts are missing or metadata is incomplete.",
]

STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "dataset_type",
    "snapshot_id",
    "decision_date",
    "universe_name",
    "report_path",
    "metadata_path",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "workflow_stage",
    "status",
    "latest_pipeline_id",
    "latest_snapshot_id",
    "latest_decision_date",
    "data_pipeline_status",
    "data_quality_status",
    "snapshot_quality_status",
    "current_candidate_status",
    "data_prep_index_status",
    "data_prep_health_status",
    "next_manual_action",
]

COMPONENTS = [
    "DATA_PIPELINE",
    "DATA_QUALITY",
    "SNAPSHOT_QUALITY",
    "CURRENT_CANDIDATES",
    "DATA_PREP_INDEX",
    "DATA_PREP_HEALTH",
]


@dataclass(frozen=True)
class DataPreparationWorkflowStatusPaths:
    artifact_dir: Path
    data_preparation_workflow_status_report: Path
    data_preparation_workflow_status_csv: Path
    data_preparation_workflow_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "data_preparation_workflow_status_report": self.data_preparation_workflow_status_report,
            "data_preparation_workflow_status_csv": self.data_preparation_workflow_status_csv,
            "data_preparation_workflow_summary": self.data_preparation_workflow_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class DataPreparationWorkflowStatusResult:
    workflow_status_id: str
    status: str
    latest_pipeline_id: str
    latest_snapshot_id: str
    latest_decision_date: str
    data_pipeline_status: str
    data_quality_status: str
    snapshot_quality_status: str
    current_candidate_status: str
    data_prep_index_status: str
    data_prep_health_status: str
    next_manual_action: str
    workflow_stage: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_data_preparation_workflow_status(
    *,
    root: str | Path | None = None,
    data_pipeline_root: str | Path | None = None,
    data_quality_root: str | Path | None = None,
    snapshot_quality_root: str | Path | None = None,
    current_candidates_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
    config: Settings | DataPreparationWorkflowStatusSettings | dict[str, Any] | str | Path | None = None,
) -> DataPreparationWorkflowStatusResult:
    """Scan local data preparation artifacts and write a status dashboard."""

    project_settings, status_settings = _resolve_settings(config)
    if status_settings.enable_live_trading or status_settings.enable_broker_api:
        raise ValueError("Data preparation workflow status dashboard cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else status_settings.root_dir
    effective_pipeline_root = (
        Path(data_pipeline_root) if data_pipeline_root is not None else status_settings.data_pipeline_root
    )
    effective_quality_root = Path(data_quality_root) if data_quality_root is not None else status_settings.data_quality_root
    effective_snapshot_root = (
        Path(snapshot_quality_root) if snapshot_quality_root is not None else status_settings.snapshot_quality_root
    )
    effective_current_root = (
        Path(current_candidates_root) if current_candidates_root is not None else status_settings.current_candidates_root
    )
    effective_output_dir = Path(output_dir) if output_dir is not None else status_settings.output_dir
    if root is not None:
        if data_pipeline_root is None:
            effective_pipeline_root = effective_root / "data_pipeline"
        if data_quality_root is None:
            effective_quality_root = effective_root / "data_quality"
        if snapshot_quality_root is None:
            effective_snapshot_root = effective_root / "snapshot_quality"
        if current_candidates_root is None:
            effective_current_root = effective_root / "current_candidates"

    scan = scan_data_preparation_workflow_artifacts(
        root=effective_root,
        data_pipeline_root=effective_pipeline_root,
        data_quality_root=effective_quality_root,
        snapshot_quality_root=effective_snapshot_root,
        current_candidates_root=effective_current_root,
        decision_date=decision_date,
        universe_name=universe_name,
    )
    status_frame = build_data_preparation_workflow_status_frame(
        scan,
        decision_date=decision_date,
        universe_name=universe_name,
    )
    workflow_stage = infer_data_preparation_workflow_stage(status_frame)
    next_manual_action = infer_data_preparation_next_action(status_frame, workflow_stage=workflow_stage)
    summary_frame = summarize_data_preparation_workflow_status(
        status_frame,
        workflow_stage=workflow_stage,
        next_manual_action=next_manual_action,
    )
    summary = summary_frame.iloc[0].to_dict()
    workflow_status_id = generate_data_preparation_workflow_status_id(
        status_frame,
        decision_date=decision_date,
        config_version=status_settings.config_version,
    )
    paths = resolve_data_preparation_workflow_status_paths(effective_output_dir, workflow_status_id)
    warnings = _dashboard_warnings(status_frame, workflow_stage)
    audit_metadata = {
        "workflow_status_id": workflow_status_id,
        "root_dir": effective_root,
        "data_pipeline_root": effective_pipeline_root,
        "data_quality_root": effective_quality_root,
        "snapshot_quality_root": effective_snapshot_root,
        "current_candidates_root": effective_current_root,
        "decision_date_filter": _date_string(decision_date),
        "universe_name_filter": _string_or_empty(universe_name),
        "workflow_stage": workflow_stage,
        "strict": status_settings.strict,
        "config_version": status_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "network_api_calls_used_in_tests": False,
        "data_preparation_only": True,
    }
    result = DataPreparationWorkflowStatusResult(
        workflow_status_id=workflow_status_id,
        status=str(summary.get("status", "WARN")),
        latest_pipeline_id=str(summary.get("latest_pipeline_id", "")),
        latest_snapshot_id=str(summary.get("latest_snapshot_id", "")),
        latest_decision_date=str(summary.get("latest_decision_date", "")),
        data_pipeline_status=str(summary.get("data_pipeline_status", "MISSING")),
        data_quality_status=str(summary.get("data_quality_status", "MISSING")),
        snapshot_quality_status=str(summary.get("snapshot_quality_status", "MISSING")),
        current_candidate_status=str(summary.get("current_candidate_status", "MISSING")),
        data_prep_index_status=str(summary.get("data_prep_index_status", "MISSING")),
        data_prep_health_status=str(summary.get("data_prep_health_status", "MISSING")),
        next_manual_action=next_manual_action,
        workflow_stage=workflow_stage,
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=DATA_PREP_WORKFLOW_STATUS_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if status_settings.write_artifacts:
        write_data_preparation_workflow_status_artifacts(result)
    _ = project_settings
    return result


def scan_data_preparation_workflow_artifacts(
    *,
    root: str | Path,
    data_pipeline_root: str | Path,
    data_quality_root: str | Path,
    snapshot_quality_root: str | Path,
    current_candidates_root: str | Path,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
) -> pd.DataFrame:
    """Scan local metadata files for data preparation workflow components."""

    root_path = Path(root)
    pipeline_root = Path(data_pipeline_root)
    quality_root = Path(data_quality_root)
    requested_date = _date_string(decision_date)
    requested_universe = _string_or_empty(universe_name)
    records: list[dict[str, Any]] = []
    records.extend(_scan_data_pipeline(pipeline_root))
    records.extend(_scan_data_quality_roots([quality_root, pipeline_root]))
    records.extend(_scan_snapshot_quality(Path(snapshot_quality_root)))
    records.extend(_scan_current_candidates(Path(current_candidates_root), requested_date, requested_universe))
    records.extend(_scan_data_prep_index(root_path / "data_preparation" / "index"))
    records.extend(_scan_data_prep_health(root_path / "data_preparation" / "health"))
    return _finalize_scan_frame(pd.DataFrame(records))


def build_data_preparation_workflow_status_frame(
    scan_frame: pd.DataFrame,
    *,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
) -> pd.DataFrame:
    """Build one status row per data preparation workflow component."""

    frame = _finalize_scan_frame(scan_frame)
    rows: list[dict[str, Any]] = []
    for component in COMPONENTS:
        component_rows = frame.loc[frame["component"] == component]
        if component_rows.empty:
            rows.append(_missing_status_row(component))
            continue
        latest = _latest_record(component_rows).copy()
        latest["next_action"] = _component_next_action(component, latest.get("status", ""))
        rows.append(latest)
    _ = decision_date, universe_name
    return _finalize_status_frame(pd.DataFrame(rows))


def infer_data_preparation_workflow_stage(status_frame: pd.DataFrame) -> str:
    """Infer the current data preparation workflow stage."""

    statuses = _status_by_component(status_frame)
    rows = {row["component"]: row for row in _finalize_status_frame(status_frame).to_dict("records")}
    if _has_attention_status(status_frame):
        return "DATA_PREP_NEEDS_ATTENTION"
    if statuses["DATA_PIPELINE"] == "MISSING":
        return "NO_DATA_PIPELINE"
    if statuses["DATA_QUALITY"] == "MISSING":
        return "DATA_PIPELINE_READY"
    if statuses["SNAPSHOT_QUALITY"] == "MISSING":
        pipeline_notes = _string_or_empty(rows.get("DATA_PIPELINE", {}).get("notes"))
        if "snapshot_manifest_path=" in pipeline_notes:
            return "SNAPSHOT_READY"
        return "DATA_QUALITY_READY"
    if statuses["CURRENT_CANDIDATES"] == "MISSING":
        return "SNAPSHOT_QUALITY_READY"
    if statuses["DATA_PREP_INDEX"] == "MISSING":
        return "CURRENT_CANDIDATES_READY"
    if statuses["DATA_PREP_HEALTH"] == "MISSING":
        return "DATA_PREP_INDEX_READY"
    if statuses["DATA_PREP_HEALTH"] == "PASS":
        return "DATA_PREP_WORKFLOW_COMPLETE"
    if statuses["DATA_PREP_HEALTH"] == "READY":
        return "DATA_PREP_HEALTH_READY"
    return "DATA_PREP_NEEDS_ATTENTION"


def infer_data_preparation_next_action(
    status_frame: pd.DataFrame,
    *,
    workflow_stage: str | None = None,
) -> str:
    """Infer the next manual action from the data preparation workflow stage."""

    stage = workflow_stage or infer_data_preparation_workflow_stage(status_frame)
    actions = {
        "NO_DATA_PIPELINE": "Run data-pipeline.",
        "DATA_PIPELINE_READY": "Run data-quality.",
        "DATA_QUALITY_READY": "Run snapshot-quality.",
        "SNAPSHOT_READY": "Run snapshot-quality.",
        "SNAPSHOT_QUALITY_READY": "Run current-candidates.",
        "CURRENT_CANDIDATES_READY": "Run data-prep-index.",
        "DATA_PREP_INDEX_READY": "Run data-prep-health.",
        "DATA_PREP_HEALTH_READY": "Proceed to current-to-paper.",
        "DATA_PREP_WORKFLOW_COMPLETE": "Proceed to current-to-paper.",
        "DATA_PREP_NEEDS_ATTENTION": "Review warnings/errors.",
    }
    return actions.get(stage, "Review data preparation artifacts.")


def summarize_data_preparation_workflow_status(
    status_frame: pd.DataFrame,
    *,
    workflow_stage: str,
    next_manual_action: str,
) -> pd.DataFrame:
    """Summarize workflow status into one dashboard row."""

    frame = _finalize_status_frame(status_frame)
    by_component = {row["component"]: row for row in frame.to_dict("records")}
    explicit_statuses = [str(row.get("status", "")).upper() for row in frame.to_dict("records")]
    missing_count = explicit_statuses.count("MISSING")
    error_count = int(pd.to_numeric(frame["error_count"], errors="coerce").fillna(0).sum()) if not frame.empty else 0
    warning_count = int(pd.to_numeric(frame["warning_count"], errors="coerce").fillna(0).sum()) if not frame.empty else 0
    status = "FAIL" if "FAIL" in explicit_statuses or error_count else "WARN" if "WARN" in explicit_statuses or missing_count or warning_count else "PASS"
    row = {
        "workflow_stage": workflow_stage,
        "status": status,
        "latest_pipeline_id": _component_artifact_id(by_component, "DATA_PIPELINE"),
        "latest_snapshot_id": _component_snapshot_id(by_component, "SNAPSHOT_QUALITY"),
        "latest_decision_date": _latest_decision_date(frame),
        "data_pipeline_status": _component_status(by_component, "DATA_PIPELINE"),
        "data_quality_status": _component_status(by_component, "DATA_QUALITY"),
        "snapshot_quality_status": _component_status(by_component, "SNAPSHOT_QUALITY"),
        "current_candidate_status": _component_status(by_component, "CURRENT_CANDIDATES"),
        "data_prep_index_status": _component_status(by_component, "DATA_PREP_INDEX"),
        "data_prep_health_status": _component_status(by_component, "DATA_PREP_HEALTH"),
        "next_manual_action": next_manual_action,
    }
    return pd.DataFrame([row], columns=SUMMARY_COLUMNS)


def resolve_data_preparation_workflow_status_paths(
    output_dir: str | Path,
    workflow_status_id: str,
) -> DataPreparationWorkflowStatusPaths:
    """Resolve deterministic workflow status artifact paths."""

    artifact_dir = Path(output_dir) / workflow_status_id
    return DataPreparationWorkflowStatusPaths(
        artifact_dir=artifact_dir,
        data_preparation_workflow_status_report=artifact_dir / "data_preparation_workflow_status_report.md",
        data_preparation_workflow_status_csv=artifact_dir / "data_preparation_workflow_status.csv",
        data_preparation_workflow_summary=artifact_dir / "data_preparation_workflow_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_data_preparation_workflow_status_artifacts(
    result: DataPreparationWorkflowStatusResult,
) -> dict[str, Path]:
    """Write workflow status report, CSVs, and metadata."""

    paths = DataPreparationWorkflowStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.status_frame, paths.data_preparation_workflow_status_csv)
    _export_dataframe(result.summary_frame, paths.data_preparation_workflow_summary)
    metadata = build_data_preparation_workflow_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.data_preparation_workflow_status_report.write_text(
        render_data_preparation_workflow_status_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_data_preparation_workflow_status_metadata(
    result: DataPreparationWorkflowStatusResult,
    paths: DataPreparationWorkflowStatusPaths,
) -> dict[str, Any]:
    """Build metadata for workflow status artifacts."""

    return {
        "workflow_status_id": result.workflow_status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_pipeline_id": result.latest_pipeline_id,
        "latest_snapshot_id": result.latest_snapshot_id,
        "latest_decision_date": result.latest_decision_date,
        "next_manual_action": result.next_manual_action,
        "component_statuses": result.summary_frame.to_dict("records")[0] if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "network_api_calls_used_in_tests": False,
        "data_preparation_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_data_preparation_workflow_status_report(
    result: DataPreparationWorkflowStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render markdown workflow status dashboard."""

    _ = metadata
    lines = [
        f"# Data Preparation Workflow Status: {result.workflow_status_id}",
        "",
        "No broker or live trading integration was invoked. This dashboard scans local data preparation artifacts only.",
        "",
        "## Workflow Summary",
        "",
        _markdown_table(
            result.summary_frame,
            [
                "workflow_stage",
                "status",
                "latest_pipeline_id",
                "latest_snapshot_id",
                "latest_decision_date",
                "next_manual_action",
            ],
        ),
        "",
        "## Component Status",
        "",
        _markdown_table(
            result.status_frame,
            [
                "component",
                "status",
                "latest_artifact_id",
                "dataset_type",
                "snapshot_id",
                "decision_date",
                "issue_count",
                "warning_count",
                "error_count",
                "next_action",
                "report_path",
            ],
            max_rows=100,
        ),
        "",
        "## Next Manual Action",
        "",
        f"- {result.next_manual_action}",
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def generate_data_preparation_workflow_status_id(
    status_frame: pd.DataFrame,
    *,
    decision_date: str | pd.Timestamp | None,
    config_version: str,
) -> str:
    """Generate deterministic workflow status id."""

    frame = _finalize_status_frame(status_frame)
    payload = {
        "decision_date": _date_string(decision_date),
        "artifacts": [
            {
                "component": row["component"],
                "artifact_id": row["latest_artifact_id"],
                "status": row["status"],
            }
            for row in frame.to_dict("records")
        ],
        "config_version": config_version,
    }
    return _hash_payload(payload, length=12)


def _scan_data_pipeline(root: Path) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json", excluded_parts={"data_quality"}):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("pipeline_id"):
            continue
        output_files = _output_files(metadata)
        dataset_types = _dataset_types(metadata.get("dataset_results"))
        snapshot_manifest_path = _string_or_empty(metadata.get("snapshot_manifest_path"))
        notes = f"dataset_count={_string_or_empty(metadata.get('dataset_count'))}"
        if snapshot_manifest_path:
            notes = f"{notes}; snapshot_manifest_path={snapshot_manifest_path}"
        records.append(
            _record(
                component="DATA_PIPELINE",
                status=_string_or_empty(metadata.get("status")) or "READY",
                latest_artifact_id=_string_or_empty(metadata.get("pipeline_id")) or metadata_path.parent.name,
                dataset_type=", ".join(dataset_types),
                report_path=output_files.get("data_pipeline_report", metadata_path.parent / "data_pipeline_report.md"),
                metadata_path=metadata_path,
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                notes=notes,
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_data_quality_roots(roots: list[Path]) -> list[dict[str, Any]]:
    records = []
    seen: set[Path] = set()
    for root in roots:
        for metadata_path in _metadata_paths(root, "metadata.json"):
            resolved = metadata_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            metadata = _load_json_or_none(metadata_path)
            if metadata is None or not metadata.get("quality_run_id"):
                continue
            output_files = _output_files(metadata)
            records.append(
                _record(
                    component="DATA_QUALITY",
                    status=_string_or_empty(metadata.get("status")) or "READY",
                    latest_artifact_id=_string_or_empty(metadata.get("quality_run_id")) or metadata_path.parent.name,
                    dataset_type=_string_or_empty(metadata.get("dataset_type")) or metadata_path.parent.parent.name,
                    report_path=output_files.get("data_quality_report", metadata_path.parent / "data_quality_report.md"),
                    metadata_path=metadata_path,
                    issue_count=_int_or_zero(metadata.get("issue_count")),
                    warning_count=_int_or_zero(metadata.get("warning_count")),
                    error_count=_int_or_zero(metadata.get("error_count")),
                    notes=f"row_count={_string_or_empty(metadata.get('row_count'))}",
                    created_at=metadata.get("created_at"),
                )
            )
    return records


def _scan_snapshot_quality(root: Path) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("quality_gate_id"):
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                component="SNAPSHOT_QUALITY",
                status=_string_or_empty(metadata.get("status")) or "READY",
                latest_artifact_id=_string_or_empty(metadata.get("quality_gate_id")) or metadata_path.parent.name,
                snapshot_id=_string_or_empty(metadata.get("snapshot_id")),
                report_path=output_files.get("snapshot_quality_gate_report", metadata_path.parent / "snapshot_quality_gate_report.md"),
                metadata_path=metadata_path,
                issue_count=_int_or_zero(metadata.get("issue_count")),
                warning_count=_int_or_zero(metadata.get("warning_count")),
                error_count=_int_or_zero(metadata.get("error_count")),
                notes=f"failed_required={', '.join(metadata.get('failed_required_datasets', [])) if isinstance(metadata.get('failed_required_datasets'), list) else ''}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_current_candidates(root: Path, decision_date: str, universe_name: str) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json", excluded_parts={"index", "health"}):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get("run_id"):
            continue
        metadata_date = _date_string(metadata.get("decision_date"))
        metadata_universe = _string_or_empty(metadata.get("universe_name"))
        if decision_date and metadata_date != decision_date:
            continue
        if universe_name and metadata_universe != universe_name:
            continue
        output_files = _output_files(metadata)
        row_counts = metadata.get("row_counts") if isinstance(metadata.get("row_counts"), dict) else {}
        records.append(
            _record(
                component="CURRENT_CANDIDATES",
                status="READY",
                latest_artifact_id=_string_or_empty(metadata.get("run_id")) or metadata_path.parent.name,
                decision_date=metadata_date,
                universe_name=metadata_universe,
                report_path=output_files.get("current_candidates_report", metadata_path.parent / "current_candidates_report.md"),
                metadata_path=metadata_path,
                warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
                notes=f"candidate_count={_string_or_empty(row_counts.get('candidates'))}",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _scan_data_prep_index(root: Path) -> list[dict[str, Any]]:
    return _single_metadata_record(
        root / "metadata.json",
        component="DATA_PREP_INDEX",
        id_key="index_id",
        default_id="data-prep-index",
        report_key="data_preparation_artifact_index",
        default_report="data_preparation_artifact_index.md",
        status="READY",
    )


def _scan_data_prep_health(root: Path) -> list[dict[str, Any]]:
    return _health_records(
        root,
        component="DATA_PREP_HEALTH",
        id_key="health_check_id",
        report_key="data_preparation_artifact_health_report",
        default_report="data_preparation_artifact_health_report.md",
    )


def _single_metadata_record(
    metadata_path: Path,
    *,
    component: str,
    id_key: str,
    default_id: str,
    report_key: str,
    default_report: str,
    status: str,
) -> list[dict[str, Any]]:
    metadata = _load_json_or_none(metadata_path)
    if metadata is None:
        return []
    output_files = _output_files(metadata)
    return [
        _record(
            component=component,
            status=status,
            latest_artifact_id=_string_or_empty(metadata.get(id_key)) or default_id,
            report_path=output_files.get(report_key, metadata_path.parent / default_report),
            metadata_path=metadata_path,
            issue_count=_int_or_zero(metadata.get("issue_count")),
            warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else _int_or_zero(metadata.get("warning_count")),
            error_count=_int_or_zero(metadata.get("error_count")),
            notes=f"artifact_count={_string_or_empty(metadata.get('artifact_count'))}",
            created_at=metadata.get("created_at"),
        )
    ]


def _health_records(
    root: Path,
    *,
    component: str,
    id_key: str,
    report_key: str,
    default_report: str,
) -> list[dict[str, Any]]:
    records = []
    for metadata_path in _metadata_paths(root, "metadata.json"):
        metadata = _load_json_or_none(metadata_path)
        if metadata is None or not metadata.get(id_key):
            continue
        output_files = _output_files(metadata)
        records.append(
            _record(
                component=component,
                status=_string_or_empty(metadata.get("status")) or "READY",
                latest_artifact_id=_string_or_empty(metadata.get(id_key)) or metadata_path.parent.name,
                report_path=output_files.get(report_key, metadata_path.parent / default_report),
                metadata_path=metadata_path,
                issue_count=_int_or_zero(metadata.get("issue_count")),
                warning_count=_int_or_zero(metadata.get("warning_count")),
                error_count=_int_or_zero(metadata.get("error_count")),
                notes="",
                created_at=metadata.get("created_at"),
            )
        )
    return records


def _record(**values: Any) -> dict[str, Any]:
    row = {
        "component": "",
        "status": "",
        "latest_artifact_id": "",
        "dataset_type": "",
        "snapshot_id": "",
        "decision_date": "",
        "universe_name": "",
        "report_path": "",
        "metadata_path": "",
        "issue_count": 0,
        "warning_count": 0,
        "error_count": 0,
        "next_action": "",
        "notes": "",
        "created_at": "",
    }
    row.update(values)
    row["status"] = _string_or_empty(row["status"]).upper()
    row["decision_date"] = _date_string(row.get("decision_date"))
    row["report_path"] = _string_or_empty(row.get("report_path"))
    row["metadata_path"] = _string_or_empty(row.get("metadata_path"))
    row["latest_artifact_id"] = _string_or_empty(row.get("latest_artifact_id"))
    row["issue_count"] = _int_or_zero(row.get("issue_count"))
    row["warning_count"] = _int_or_zero(row.get("warning_count"))
    row["error_count"] = _int_or_zero(row.get("error_count"))
    return row


def _missing_status_row(component: str) -> dict[str, Any]:
    return _record(
        component=component,
        status="MISSING",
        next_action=_component_next_action(component, "MISSING"),
        notes="No matching local artifact metadata found.",
    )


def _component_next_action(component: str, status: str) -> str:
    if status == "FAIL":
        return "Review warnings/errors."
    if component == "DATA_PIPELINE":
        return "Run data-pipeline." if status == "MISSING" else "Run data-quality."
    if component == "DATA_QUALITY":
        return "Run data-quality." if status == "MISSING" else "Run snapshot-quality."
    if component == "SNAPSHOT_QUALITY":
        return "Run snapshot-quality." if status == "MISSING" else "Run current-candidates."
    if component == "CURRENT_CANDIDATES":
        return "Run current-candidates." if status == "MISSING" else "Run data-prep-index."
    if component == "DATA_PREP_INDEX":
        return "Run data-prep-index." if status == "MISSING" else "Run data-prep-health."
    if component == "DATA_PREP_HEALTH":
        return "Run data-prep-health." if status == "MISSING" else "Proceed to current-to-paper."
    return ""


def _status_by_component(status_frame: pd.DataFrame) -> dict[str, str]:
    frame = _finalize_status_frame(status_frame)
    values = {row["component"]: row["status"] for row in frame.to_dict("records")}
    for component in COMPONENTS:
        values.setdefault(component, "MISSING")
    return values


def _has_attention_status(status_frame: pd.DataFrame) -> bool:
    frame = _finalize_status_frame(status_frame)
    if frame.empty:
        return False
    active = frame.loc[frame["status"] != "MISSING"]
    if active.empty:
        return False
    statuses = set(active["status"].astype(str).str.upper())
    if statuses.intersection({"FAIL", "WARN"}):
        return True
    error_count = int(pd.to_numeric(active["error_count"], errors="coerce").fillna(0).sum())
    return error_count > 0


def _component_status(by_component: dict[str, dict[str, Any]], component: str) -> str:
    row = by_component.get(component, {})
    return _string_or_empty(row.get("status")) or "MISSING"


def _component_artifact_id(by_component: dict[str, dict[str, Any]], component: str) -> str:
    row = by_component.get(component, {})
    return _string_or_empty(row.get("latest_artifact_id"))


def _component_snapshot_id(by_component: dict[str, dict[str, Any]], component: str) -> str:
    row = by_component.get(component, {})
    return _string_or_empty(row.get("snapshot_id"))


def _latest_decision_date(frame: pd.DataFrame) -> str:
    dates = sorted(_date_string(value) for value in frame.get("decision_date", pd.Series(dtype="object")).tolist() if _date_string(value))
    return dates[-1] if dates else ""


def _dashboard_warnings(status_frame: pd.DataFrame, workflow_stage: str) -> list[str]:
    warnings = []
    if workflow_stage != "DATA_PREP_WORKFLOW_COMPLETE":
        warnings.append(f"Workflow stage is {workflow_stage}; manual action is still needed.")
    failing = status_frame.loc[status_frame["status"] == "FAIL"] if not status_frame.empty else pd.DataFrame()
    for row in failing.to_dict("records"):
        warnings.append(f"{row['component']} status is FAIL.")
    return warnings


def _metadata_paths(root: Path, filename: str, excluded_parts: set[str] | None = None) -> list[Path]:
    if not root.exists():
        return []
    excluded = excluded_parts or set()
    paths = []
    for path in root.rglob(filename):
        relative_parts = set(path.relative_to(root).parts[:-1])
        if relative_parts.intersection(excluded):
            continue
        paths.append(path)
    return sorted(paths)


def _load_json_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _output_files(metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files")
    return output_files if isinstance(output_files, dict) else {}


def _dataset_types(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    values = sorted(
        _string_or_empty(item.get("dataset_type"))
        for item in value
        if isinstance(item, dict) and _string_or_empty(item.get("dataset_type"))
    )
    return values


def _latest_record(frame: pd.DataFrame) -> dict[str, Any]:
    sortable = frame.copy(deep=True)
    sortable["_sort_date"] = sortable["decision_date"].map(lambda value: _date_string(value))
    sortable["_sort_created"] = sortable["created_at"].map(_string_or_empty)
    sortable = sortable.sort_values(
        ["_sort_date", "_sort_created", "latest_artifact_id", "metadata_path"],
        na_position="last",
    )
    return sortable.iloc[-1].drop(labels=["_sort_date", "_sort_created"], errors="ignore").to_dict()


def _finalize_scan_frame(frame: pd.DataFrame) -> pd.DataFrame:
    scan = frame.copy(deep=True)
    columns = STATUS_COLUMNS + ["created_at"]
    for column in columns:
        if column not in scan.columns:
            scan[column] = ""
    if scan.empty:
        return scan[columns]
    return scan[columns].sort_values(["component", "decision_date", "created_at", "latest_artifact_id"], na_position="last").reset_index(drop=True)


def _finalize_status_frame(frame: pd.DataFrame) -> pd.DataFrame:
    status = frame.copy(deep=True)
    for column in STATUS_COLUMNS:
        if column not in status.columns:
            status[column] = ""
    if status.empty:
        return status[STATUS_COLUMNS]
    return status[STATUS_COLUMNS].sort_values(["component"], key=lambda series: series.map(_component_order)).reset_index(drop=True)


def _component_order(component: Any) -> int:
    text = _string_or_empty(component)
    return COMPONENTS.index(text) if text in COMPONENTS else len(COMPONENTS)


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = _sanitize_dataframe_for_export(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    export = frame.copy(deep=True)
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif export[column].dtype == "object":
            export[column] = export[column].map(_cell_to_export_value)
    return export


def _cell_to_export_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True)
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    table = frame[available].head(max_rows).copy()
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True).replace("|", "\\|")
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("|", "\\|").replace("\n", " ")


def _resolve_settings(
    config: Settings | DataPreparationWorkflowStatusSettings | dict[str, Any] | str | Path | None,
) -> tuple[Settings, DataPreparationWorkflowStatusSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.data_preparation_workflow_status
    if isinstance(config, Settings):
        return config, config.data_preparation_workflow_status
    if isinstance(config, (str, Path)):
        project = load_settings(Path(config))
        return project, project.data_preparation_workflow_status
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, DataPreparationWorkflowStatusSettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.data_preparation_workflow_status.model_dump())
        for key, value in config.items():
            if key == "data_preparation_workflow_status" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, DataPreparationWorkflowStatusSettings(**payload)
    raise TypeError("config must be Settings, DataPreparationWorkflowStatusSettings, dict, path, or None")


def _date_string(value: Any) -> str:
    if not _present(value):
        return ""
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        return ""
    return str(timestamp.date())


def _int_or_zero(value: Any) -> int:
    if not _present(value):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _present(value: Any) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return str(value).strip() != ""


def _string_or_empty(value: Any) -> str:
    return str(value).strip() if _present(value) else ""


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
