"""Snapshot-level quality gate for processed local data snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import (
    DataQualitySettings,
    Settings,
    SnapshotQualityGateSettings,
    load_settings,
)
from quant_replay_system.data_quality import DataQualityResult, run_data_quality_checks


SNAPSHOT_QUALITY_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Does not call market data APIs or require API tokens.",
    "Does not connect to brokers, place orders, or automate execution.",
    "Runs quality checks and reports gate status; it does not repair data.",
    "Not yet wired into replay orchestration as a hard preflight.",
]

GATE_SUMMARY_COLUMNS = [
    "dataset_type",
    "required",
    "present",
    "path",
    "status",
    "row_count",
    "issue_count",
    "warning_count",
    "error_count",
    "gate_effect",
    "reason",
]

DATASET_QUALITY_COLUMNS = [
    "dataset_type",
    "required",
    "path",
    "quality_status",
    "quality_run_id",
    "row_count",
    "issue_count",
    "warning_count",
    "error_count",
]

DATASET_ISSUE_COUNT_COLUMNS = [
    "dataset_type",
    "required",
    "status",
    "issue_count",
    "warning_count",
    "error_count",
]


@dataclass(frozen=True)
class SnapshotDatasetQualityResult:
    dataset_type: str
    required: bool
    path: Path | None
    status: str
    row_count: int
    issue_count: int
    warning_count: int
    error_count: int
    gate_effect: str
    reason: str
    quality_result: DataQualityResult | None


@dataclass(frozen=True)
class SnapshotQualityGateArtifactPaths:
    artifact_dir: Path
    snapshot_quality_gate_report: Path
    snapshot_quality_summary: Path
    dataset_quality_results: Path
    dataset_issue_counts: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "snapshot_quality_gate_report": self.snapshot_quality_gate_report,
            "snapshot_quality_summary": self.snapshot_quality_summary,
            "dataset_quality_results": self.dataset_quality_results,
            "dataset_issue_counts": self.dataset_issue_counts,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SnapshotQualityGateResult:
    snapshot_id: str
    status: str
    dataset_results: list[SnapshotDatasetQualityResult]
    required_dataset_count: int
    optional_dataset_count: int
    failed_required_datasets: list[str]
    failed_optional_datasets: list[str]
    warning_count: int
    error_count: int
    gate_summary_frame: pd.DataFrame
    dataset_quality_results_frame: pd.DataFrame
    dataset_issue_counts_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    quality_gate_id: str
    audit_metadata: dict[str, Any]


def load_snapshot_manifest(path: str | Path) -> dict[str, Any]:
    """Load and normalize a local snapshot manifest."""

    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Snapshot manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_paths: dict[str, str] = {}
    if isinstance(payload.get("processed_files"), dict):
        dataset_paths.update({str(key): str(value) for key, value in payload["processed_files"].items()})
    for dataset_type in ["market", "universe", "trading_calendar", "benchmark", "corporate_actions"]:
        field = f"{dataset_type}_path"
        if field in payload and _present(payload.get(field)):
            dataset_paths[dataset_type] = str(payload[field])
    snapshot_id = _string_or_empty(payload.get("snapshot_id")) or manifest_path.stem
    return {
        "snapshot_id": snapshot_id,
        "created_at": _string_or_empty(payload.get("created_at")),
        "source": _string_or_empty(payload.get("source")),
        "revision_id": _string_or_empty(payload.get("revision_id")),
        "notes": _string_or_empty(payload.get("notes")),
        "dataset_paths": dataset_paths,
        "manifest_path": manifest_path,
        "raw_manifest": payload,
    }


def run_snapshot_quality_gate(
    snapshot_manifest_path: str | Path,
    *,
    settings: Settings | SnapshotQualityGateSettings | dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
) -> SnapshotQualityGateResult:
    """Run snapshot-level quality checks across all manifest datasets."""

    project_settings, gate_settings = _resolve_settings(settings)
    if gate_settings.enable_live_trading or gate_settings.enable_broker_api:
        raise ValueError("Snapshot quality gate cannot enable live trading or broker API access")
    manifest = load_snapshot_manifest(snapshot_manifest_path)
    manifest_path = Path(manifest["manifest_path"])
    data_quality_settings = _data_quality_settings(project_settings)
    dataset_results = _run_dataset_quality(manifest, gate_settings, data_quality_settings)
    status, warnings, failed_required, failed_optional = evaluate_snapshot_gate_status(dataset_results, gate_settings)
    gate_summary = build_snapshot_quality_summary(dataset_results)
    dataset_quality = _dataset_quality_results_frame(dataset_results)
    dataset_issue_counts = _dataset_issue_counts_frame(dataset_results)
    required_count = len(gate_settings.required_datasets)
    optional_count = len(gate_settings.optional_datasets)
    warning_count = int(sum(result.warning_count for result in dataset_results) + sum(1 for result in dataset_results if result.gate_effect == "WARN"))
    error_count = int(sum(result.error_count for result in dataset_results) + sum(1 for result in dataset_results if result.gate_effect == "FAIL"))
    quality_gate_id = generate_quality_gate_id(
        snapshot_id=str(manifest["snapshot_id"]),
        dataset_results=dataset_results,
        settings=gate_settings,
    )
    paths = resolve_snapshot_quality_gate_paths(
        Path(output_dir) if output_dir is not None else gate_settings.output_dir,
        str(manifest["snapshot_id"]),
        quality_gate_id,
    )
    audit_metadata = {
        "snapshot_id": manifest["snapshot_id"],
        "manifest_path": manifest_path,
        "quality_gate_id": quality_gate_id,
        "status": status,
        "block_replay_on_fail": gate_settings.block_replay_on_fail,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "snapshot_quality_only": True,
        "config_version": gate_settings.config_version,
    }
    result = SnapshotQualityGateResult(
        snapshot_id=str(manifest["snapshot_id"]),
        status=status,
        dataset_results=dataset_results,
        required_dataset_count=required_count,
        optional_dataset_count=optional_count,
        failed_required_datasets=failed_required,
        failed_optional_datasets=failed_optional,
        warning_count=warning_count,
        error_count=error_count,
        gate_summary_frame=gate_summary,
        dataset_quality_results_frame=dataset_quality,
        dataset_issue_counts_frame=dataset_issue_counts,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=SNAPSHOT_QUALITY_LIMITATIONS,
        quality_gate_id=quality_gate_id,
        audit_metadata=audit_metadata,
    )
    if gate_settings.write_artifacts:
        write_snapshot_quality_gate_artifacts(result)
    return result


def evaluate_snapshot_gate_status(
    dataset_results: list[SnapshotDatasetQualityResult],
    settings: SnapshotQualityGateSettings | dict[str, Any] | None = None,
) -> tuple[str, list[str], list[str], list[str]]:
    """Evaluate PASS/WARN/FAIL for a set of dataset quality results."""

    gate_settings = _coerce_gate_settings(settings)
    warnings: list[str] = []
    failed_required = [
        result.dataset_type
        for result in dataset_results
        if result.required and result.gate_effect == "FAIL"
    ]
    failed_optional = [
        result.dataset_type
        for result in dataset_results
        if not result.required and result.status == "FAIL"
    ]
    if failed_required:
        warnings.append(f"Required dataset gate failure: {', '.join(failed_required)}")
        return "FAIL", warnings, failed_required, failed_optional
    if gate_settings.fail_on_optional_dataset_fail and failed_optional:
        warnings.append(f"Optional dataset failure escalated: {', '.join(failed_optional)}")
        return "FAIL", warnings, failed_required, failed_optional
    has_warning = any(result.gate_effect == "WARN" or result.warning_count > 0 for result in dataset_results)
    if failed_optional:
        warnings.append(f"Optional dataset quality failure: {', '.join(failed_optional)}")
        has_warning = True
    if has_warning:
        return "WARN", warnings, failed_required, failed_optional
    return "PASS", warnings, failed_required, failed_optional


def build_snapshot_quality_summary(dataset_results: list[SnapshotDatasetQualityResult]) -> pd.DataFrame:
    """Build one-row-per-dataset gate summary."""

    rows = [
        {
            "dataset_type": result.dataset_type,
            "required": result.required,
            "present": result.path is not None and result.path.exists(),
            "path": str(result.path) if result.path is not None else "",
            "status": result.status,
            "row_count": result.row_count,
            "issue_count": result.issue_count,
            "warning_count": result.warning_count,
            "error_count": result.error_count,
            "gate_effect": result.gate_effect,
            "reason": result.reason,
        }
        for result in dataset_results
    ]
    return _finalize_frame(pd.DataFrame(rows), GATE_SUMMARY_COLUMNS, ["required", "dataset_type"])


def assert_snapshot_quality_passed(result: SnapshotQualityGateResult) -> None:
    """Raise if the snapshot quality gate failed."""

    if result.status == "FAIL":
        failed = ", ".join(result.failed_required_datasets) or "unknown required dataset"
        raise ValueError(
            f"Snapshot quality gate failed for snapshot {result.snapshot_id}. "
            f"Failed required datasets: {failed}. See {result.artifact_paths.get('snapshot_quality_gate_report')}."
        )


def resolve_snapshot_quality_gate_paths(
    output_dir: str | Path,
    snapshot_id: str,
    quality_gate_id: str,
) -> SnapshotQualityGateArtifactPaths:
    """Resolve stable snapshot quality gate artifact paths."""

    artifact_dir = Path(output_dir) / f"{snapshot_id}_{quality_gate_id}"
    return SnapshotQualityGateArtifactPaths(
        artifact_dir=artifact_dir,
        snapshot_quality_gate_report=artifact_dir / "snapshot_quality_gate_report.md",
        snapshot_quality_summary=artifact_dir / "snapshot_quality_summary.csv",
        dataset_quality_results=artifact_dir / "dataset_quality_results.csv",
        dataset_issue_counts=artifact_dir / "dataset_issue_counts.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_snapshot_quality_gate_artifacts(result: SnapshotQualityGateResult) -> dict[str, Path]:
    """Write snapshot quality gate markdown, CSVs, and metadata."""

    paths = SnapshotQualityGateArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.gate_summary_frame, paths.snapshot_quality_summary)
    _export_dataframe(result.dataset_quality_results_frame, paths.dataset_quality_results)
    _export_dataframe(result.dataset_issue_counts_frame, paths.dataset_issue_counts)
    metadata = build_snapshot_quality_gate_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.snapshot_quality_gate_report.write_text(render_snapshot_quality_gate_report(result, metadata), encoding="utf-8")
    return paths.as_dict()


def build_snapshot_quality_gate_metadata(
    result: SnapshotQualityGateResult,
    paths: SnapshotQualityGateArtifactPaths,
) -> dict[str, Any]:
    """Build deterministic metadata for a snapshot quality gate run."""

    return {
        "snapshot_id": result.snapshot_id,
        "quality_gate_id": result.quality_gate_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "required_dataset_count": result.required_dataset_count,
        "optional_dataset_count": result.optional_dataset_count,
        "failed_required_datasets": result.failed_required_datasets,
        "failed_optional_datasets": result.failed_optional_datasets,
        "warning_count": result.warning_count,
        "error_count": result.error_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "snapshot_quality_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_snapshot_quality_gate_report(
    result: SnapshotQualityGateResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render the markdown snapshot quality gate report."""

    _ = metadata
    lines = [
        f"# Snapshot Quality Gate: {result.snapshot_id}",
        "",
        "No broker or live trading integration was invoked. This report checks local snapshot files only.",
        "",
        "## Gate Summary",
        "",
        _dict_table(
            {
                "snapshot_id": result.snapshot_id,
                "quality_gate_id": result.quality_gate_id,
                "status": result.status,
                "required_dataset_count": result.required_dataset_count,
                "optional_dataset_count": result.optional_dataset_count,
                "failed_required_datasets": ", ".join(result.failed_required_datasets),
                "failed_optional_datasets": ", ".join(result.failed_optional_datasets),
                "warning_count": result.warning_count,
                "error_count": result.error_count,
            }
        ),
        "",
        "## Dataset Gate Results",
        "",
        _markdown_table(result.gate_summary_frame, GATE_SUMMARY_COLUMNS),
        "",
        "## Dataset Quality Results",
        "",
        _markdown_table(result.dataset_quality_results_frame, DATASET_QUALITY_COLUMNS),
        "",
        "## Dataset Issue Counts",
        "",
        _markdown_table(result.dataset_issue_counts_frame, DATASET_ISSUE_COUNT_COLUMNS),
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


def generate_quality_gate_id(
    *,
    snapshot_id: str,
    dataset_results: list[SnapshotDatasetQualityResult],
    settings: SnapshotQualityGateSettings,
) -> str:
    """Generate a deterministic quality gate id."""

    payload = {
        "snapshot_id": snapshot_id,
        "dataset_results": [
            {
                "dataset_type": result.dataset_type,
                "required": result.required,
                "path": str(result.path) if result.path is not None else "",
                "status": result.status,
                "row_count": result.row_count,
                "issue_count": result.issue_count,
                "warning_count": result.warning_count,
                "error_count": result.error_count,
                "gate_effect": result.gate_effect,
            }
            for result in sorted(dataset_results, key=lambda item: item.dataset_type)
        ],
        "settings": {
            "required_datasets": list(settings.required_datasets),
            "optional_datasets": list(settings.optional_datasets),
            "fail_on_required_dataset_warn": settings.fail_on_required_dataset_warn,
            "fail_on_optional_dataset_fail": settings.fail_on_optional_dataset_fail,
            "allow_missing_optional_datasets": settings.allow_missing_optional_datasets,
            "missing_optional_dataset_severity": settings.missing_optional_dataset_severity,
            "block_replay_on_fail": settings.block_replay_on_fail,
            "config_version": settings.config_version,
        },
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _run_dataset_quality(
    manifest: dict[str, Any],
    gate_settings: SnapshotQualityGateSettings,
    data_quality_settings: DataQualitySettings,
) -> list[SnapshotDatasetQualityResult]:
    dataset_paths = manifest["dataset_paths"]
    manifest_path = Path(manifest["manifest_path"])
    results: list[SnapshotDatasetQualityResult] = []
    ordered_datasets = list(gate_settings.required_datasets) + [
        dataset for dataset in gate_settings.optional_datasets if dataset not in gate_settings.required_datasets
    ]
    for dataset_type in ordered_datasets:
        required = dataset_type in gate_settings.required_datasets
        raw_path = dataset_paths.get(dataset_type)
        if not _present(raw_path):
            results.append(_missing_dataset_result(dataset_type, required, gate_settings))
            continue
        path = _resolve_dataset_path(raw_path, manifest_path.parent)
        if not path.exists():
            results.append(_missing_file_result(dataset_type, required, path, gate_settings))
            continue
        quality = run_data_quality_checks(path, dataset_type, settings=data_quality_settings)
        gate_effect, reason = _gate_effect_for_quality(quality.status, required, gate_settings)
        results.append(
            SnapshotDatasetQualityResult(
                dataset_type=dataset_type,
                required=required,
                path=path,
                status=quality.status,
                row_count=quality.row_count,
                issue_count=quality.issue_count,
                warning_count=quality.warning_count,
                error_count=quality.error_count,
                gate_effect=gate_effect,
                reason=reason,
                quality_result=quality,
            )
        )
    return results


def _missing_dataset_result(
    dataset_type: str,
    required: bool,
    settings: SnapshotQualityGateSettings,
) -> SnapshotDatasetQualityResult:
    if required:
        status, effect, reason = "FAIL", "FAIL", "Missing required dataset path."
    elif settings.allow_missing_optional_datasets:
        severity = settings.missing_optional_dataset_severity
        status = "WARN" if severity == "WARN" else "INFO"
        effect = "WARN" if severity == "WARN" else "INFO"
        reason = "Missing optional dataset path."
    else:
        status, effect, reason = "FAIL", "FAIL", "Missing optional dataset path is not allowed."
    return SnapshotDatasetQualityResult(
        dataset_type=dataset_type,
        required=required,
        path=None,
        status=status,
        row_count=0,
        issue_count=1,
        warning_count=1 if effect == "WARN" else 0,
        error_count=1 if effect == "FAIL" else 0,
        gate_effect=effect,
        reason=reason,
        quality_result=None,
    )


def _missing_file_result(
    dataset_type: str,
    required: bool,
    path: Path,
    settings: SnapshotQualityGateSettings,
) -> SnapshotDatasetQualityResult:
    if required or not settings.allow_missing_optional_datasets:
        status, effect, reason = "FAIL", "FAIL", "Dataset file does not exist."
    else:
        severity = settings.missing_optional_dataset_severity
        status = "WARN" if severity == "WARN" else "INFO"
        effect = "WARN" if severity == "WARN" else "INFO"
        reason = "Optional dataset file does not exist."
    return SnapshotDatasetQualityResult(
        dataset_type=dataset_type,
        required=required,
        path=path,
        status=status,
        row_count=0,
        issue_count=1,
        warning_count=1 if effect == "WARN" else 0,
        error_count=1 if effect == "FAIL" else 0,
        gate_effect=effect,
        reason=reason,
        quality_result=None,
    )


def _gate_effect_for_quality(
    quality_status: str,
    required: bool,
    settings: SnapshotQualityGateSettings,
) -> tuple[str, str]:
    if required and quality_status == "FAIL":
        return "FAIL", "Required dataset failed data quality checks."
    if required and quality_status == "WARN" and settings.fail_on_required_dataset_warn:
        return "FAIL", "Required dataset warning escalated by gate settings."
    if required and quality_status == "WARN":
        return "WARN", "Required dataset has data quality warnings."
    if required:
        return "PASS", "Required dataset passed data quality checks."
    if quality_status == "FAIL" and settings.fail_on_optional_dataset_fail:
        return "FAIL", "Optional dataset failure escalated by gate settings."
    if quality_status == "FAIL":
        return "WARN", "Optional dataset failed data quality checks."
    if quality_status == "WARN":
        return "WARN", "Optional dataset has data quality warnings."
    return "PASS", "Optional dataset passed data quality checks."


def _data_quality_settings(project_settings: Settings) -> DataQualitySettings:
    return project_settings.data_quality.model_copy(update={"write_artifacts": False})


def _dataset_quality_results_frame(dataset_results: list[SnapshotDatasetQualityResult]) -> pd.DataFrame:
    rows = [
        {
            "dataset_type": result.dataset_type,
            "required": result.required,
            "path": str(result.path) if result.path is not None else "",
            "quality_status": result.status,
            "quality_run_id": result.quality_result.quality_run_id if result.quality_result is not None else "",
            "row_count": result.row_count,
            "issue_count": result.issue_count,
            "warning_count": result.warning_count,
            "error_count": result.error_count,
        }
        for result in dataset_results
    ]
    return _finalize_frame(pd.DataFrame(rows), DATASET_QUALITY_COLUMNS, ["required", "dataset_type"])


def _dataset_issue_counts_frame(dataset_results: list[SnapshotDatasetQualityResult]) -> pd.DataFrame:
    rows = [
        {
            "dataset_type": result.dataset_type,
            "required": result.required,
            "status": result.status,
            "issue_count": result.issue_count,
            "warning_count": result.warning_count,
            "error_count": result.error_count,
        }
        for result in dataset_results
    ]
    return _finalize_frame(pd.DataFrame(rows), DATASET_ISSUE_COUNT_COLUMNS, ["required", "dataset_type"])


def _resolve_dataset_path(value: str | Path, base_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.exists():
        return path
    return base_dir / path


def _finalize_frame(frame: pd.DataFrame, columns: list[str], sort_columns: list[str]) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in columns:
        if column not in output.columns:
            output[column] = ""
    if output.empty:
        return output[columns]
    available_sort = [column for column in sort_columns if column in output.columns]
    if available_sort:
        output = output.sort_values(available_sort, ascending=[False if column == "required" else True for column in available_sort])
    return output[columns].reset_index(drop=True)


def _coerce_gate_settings(settings: SnapshotQualityGateSettings | dict[str, Any] | None) -> SnapshotQualityGateSettings:
    if settings is None:
        return SnapshotQualityGateSettings()
    if isinstance(settings, SnapshotQualityGateSettings):
        return settings
    if isinstance(settings, dict):
        return SnapshotQualityGateSettings(**settings)
    if hasattr(settings, "model_dump"):
        return SnapshotQualityGateSettings(**settings.model_dump())
    raise TypeError("settings must be SnapshotQualityGateSettings, dict, or None")


def _resolve_settings(
    settings: Settings | SnapshotQualityGateSettings | dict[str, Any] | None,
) -> tuple[Settings, SnapshotQualityGateSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.snapshot_quality_gate
    if isinstance(settings, Settings):
        return settings, settings.snapshot_quality_gate
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, SnapshotQualityGateSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.snapshot_quality_gate.model_dump())
        for key, value in settings.items():
            if key == "snapshot_quality_gate" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, SnapshotQualityGateSettings(**payload)
    raise TypeError("settings must be Settings, SnapshotQualityGateSettings, dict, or None")


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


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


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
