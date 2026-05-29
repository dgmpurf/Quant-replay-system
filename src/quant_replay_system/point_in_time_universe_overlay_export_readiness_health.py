"""Health checks for PIT universe overlay export-readiness artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.point_in_time_universe_overlay_export_readiness import READINESS_OUTPUT_COLUMNS
from quant_replay_system.point_in_time_universe_overlay_export_readiness_index import (
    PIT_UNIVERSE_OVERLAY_EXPORT_READINESS_INDEX_COLUMNS,
    scan_pit_universe_overlay_export_readiness_artifacts,
)


HEALTH_COLUMNS = [
    "artifact_type",
    "export_readiness_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

HEALTH_LIMITATIONS = [
    "Checks local PIT universe overlay export-readiness artifacts only.",
    "Does not export universe files, write data/raw or data/processed, run current-candidates, build snapshots, or compute forward labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class PitUniverseOverlayExportReadinessHealthPaths:
    artifact_dir: Path
    pit_universe_overlay_export_readiness_health_report: Path
    pit_universe_overlay_export_readiness_health_issues: Path
    pit_universe_overlay_export_readiness_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_overlay_export_readiness_health_report": self.pit_universe_overlay_export_readiness_health_report,
            "pit_universe_overlay_export_readiness_health_issues": self.pit_universe_overlay_export_readiness_health_issues,
            "pit_universe_overlay_export_readiness_health_summary": self.pit_universe_overlay_export_readiness_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseOverlayExportReadinessHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    health_check_id: str
    audit_metadata: dict[str, Any]


def check_pit_universe_overlay_export_readiness_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path = "outputs/reports/point_in_time_universe_overlay_export_readiness",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_overlay_export_readiness/health",
) -> PitUniverseOverlayExportReadinessHealthResult:
    index_frame, index_source, load_issues = _load_index(index_df=index_df, index_path=index_path, root=root)
    health_frame = build_pit_universe_overlay_export_readiness_health_frame(index_frame)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_pit_universe_overlay_export_readiness_health(
        health_frame,
        checked_artifact_count=len(index_frame),
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = _hash_payload({"rows": index_frame.to_dict("records"), "status": status}, length=12)
    paths = resolve_pit_universe_overlay_export_readiness_health_paths(output_dir, health_check_id)
    result = PitUniverseOverlayExportReadinessHealthResult(
        status=status,
        checked_artifact_count=len(index_frame),
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=[],
        known_limitations=HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata={
            "index_source": index_source,
            "checked_artifact_count": len(index_frame),
            "universe_exported": False,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "pit_universe_overlay_export_readiness_artifacts_only": True,
        },
    )
    write_pit_universe_overlay_export_readiness_health_artifacts(result)
    return result


def build_pit_universe_overlay_export_readiness_health_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    index_frame = _prepare_index_frame(index_df)
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        metadata = _check_metadata(row, Path(_string_or_empty(row.get("metadata_path"))), issues)
        readiness = _check_csv(
            row,
            Path(_string_or_empty(row.get("readiness_csv_path"))),
            issues,
            path_field="readiness_csv_path",
            missing_code="MISSING_READINESS_CSV",
            required_columns=READINESS_OUTPUT_COLUMNS,
        )
        _check_report(row, Path(_string_or_empty(row.get("report_path"))), issues)
        if metadata is not None and readiness is not None:
            _check_export_readiness_contract(row, metadata, readiness, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_pit_universe_overlay_export_readiness_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    frame = _finalize_health_frame(health_frame)
    issue_count = len(frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    rows = [
        {
            "status": status,
            "checked_artifact_count": checked_artifact_count,
            "issue_count": issue_count,
            "error_count": error_count,
            "warning_count": warning_count,
        }
    ]
    if not frame.empty:
        for issue_code, group in frame.groupby("issue_code", dropna=False):
            rows.append(
                {
                    "status": status,
                    "checked_artifact_count": checked_artifact_count,
                    "issue_count": len(group),
                    "error_count": int((group["severity"] == "ERROR").sum()),
                    "warning_count": int((group["severity"] == "WARN").sum()),
                    "issue_code": issue_code,
                }
            )
    return pd.DataFrame(rows)


def resolve_pit_universe_overlay_export_readiness_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> PitUniverseOverlayExportReadinessHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return PitUniverseOverlayExportReadinessHealthPaths(
        artifact_dir=artifact_dir,
        pit_universe_overlay_export_readiness_health_report=artifact_dir
        / "pit_universe_overlay_export_readiness_health_report.md",
        pit_universe_overlay_export_readiness_health_issues=artifact_dir
        / "pit_universe_overlay_export_readiness_health_issues.csv",
        pit_universe_overlay_export_readiness_health_summary=artifact_dir
        / "pit_universe_overlay_export_readiness_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_overlay_export_readiness_health_artifacts(
    result: PitUniverseOverlayExportReadinessHealthResult,
) -> dict[str, Path]:
    paths = PitUniverseOverlayExportReadinessHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.pit_universe_overlay_export_readiness_health_issues, index=False)
    result.summary_frame.to_csv(paths.pit_universe_overlay_export_readiness_health_summary, index=False)
    metadata = build_pit_universe_overlay_export_readiness_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_overlay_export_readiness_health_report.write_text(
        render_pit_universe_overlay_export_readiness_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_pit_universe_overlay_export_readiness_health_metadata(
    result: PitUniverseOverlayExportReadinessHealthResult,
    paths: PitUniverseOverlayExportReadinessHealthPaths,
) -> dict[str, Any]:
    return {
        "health_check_id": result.health_check_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, "
            "forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, "
            "or cache mutation was invoked."
        ),
    }


def render_pit_universe_overlay_export_readiness_health_report(
    result: PitUniverseOverlayExportReadinessHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "# PIT Universe Overlay Export Readiness Health",
            "",
            "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked. This health check reads local export-readiness artifacts only.",
            "",
            "## Summary",
            "",
            _dict_table(
                {
                    "health_check_id": result.health_check_id,
                    "status": result.status,
                    "checked_artifact_count": result.checked_artifact_count,
                    "issue_count": result.issue_count,
                    "error_count": result.error_count,
                    "warning_count": result.warning_count,
                }
            ),
            "",
            "## Issues",
            "",
            _markdown_table(
                result.health_frame,
                ["export_readiness_id", "severity", "issue_code", "path_field", "issue_message", "suggested_action"],
            ),
            "",
        ]
    )


def _load_index(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path,
) -> tuple[pd.DataFrame, str, list[dict[str, Any]]]:
    if index_df is not None:
        return _prepare_index_frame(index_df), "in_memory", []
    if index_path is not None:
        path = Path(index_path)
        if not path.exists():
            issue = _issue(
                {},
                "metadata_path",
                path,
                "ERROR",
                "MISSING_METADATA",
                f"Index CSV not found: {path}",
                "Run pit-universe-overlay-export-readiness-index.",
            )
            return _prepare_index_frame(pd.DataFrame()), str(path), [issue]
        return _prepare_index_frame(pd.read_csv(path, keep_default_na=False)), str(path), []
    frame = scan_pit_universe_overlay_export_readiness_artifacts(root)
    return _prepare_index_frame(frame), str(root), []


def _check_metadata(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(
            _issue(
                row,
                "metadata_path",
                path,
                "ERROR",
                "MISSING_METADATA",
                "metadata.json is missing.",
                "Regenerate the PIT universe overlay export-readiness artifact.",
            )
        )
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(
            _issue(
                row,
                "metadata_path",
                path,
                "ERROR",
                "MISSING_METADATA",
                f"metadata.json is unreadable: {exc}",
                "Regenerate the PIT universe overlay export-readiness artifact.",
            )
        )
        return None
    return metadata if isinstance(metadata, dict) else {}


def _check_csv(
    row: dict[str, Any],
    path: Path,
    issues: list[dict[str, Any]],
    *,
    path_field: str,
    missing_code: str,
    required_columns: list[str],
) -> pd.DataFrame | None:
    if not path.exists():
        issues.append(
            _issue(
                row,
                path_field,
                path,
                "ERROR",
                missing_code,
                f"{path_field} is missing.",
                "Regenerate the PIT universe overlay export-readiness artifact.",
            )
        )
        return None
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(
            _issue(
                row,
                path_field,
                path,
                "ERROR",
                missing_code,
                f"{path_field} is unreadable: {exc}",
                "Regenerate the PIT universe overlay export-readiness artifact.",
            )
        )
        return None
    _check_required_columns(row, frame, issues, path_field=path_field, required_columns=required_columns)
    return frame


def _check_required_columns(
    row: dict[str, Any],
    frame: pd.DataFrame,
    issues: list[dict[str, Any]],
    *,
    path_field: str,
    required_columns: list[str],
) -> None:
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        issues.append(
            _issue(
                row,
                path_field,
                row.get(path_field),
                "ERROR",
                "MISSING_REQUIRED_COLUMNS",
                f"Missing required columns: {', '.join(missing)}",
                "Regenerate the PIT universe overlay export-readiness artifact with the current schema.",
            )
        )


def _check_report(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(
            _issue(
                row,
                "report_path",
                path,
                "ERROR",
                "MISSING_REPORT",
                "PIT universe overlay export-readiness report is missing.",
                "Regenerate the PIT universe overlay export-readiness artifact.",
            )
        )


def _check_export_readiness_contract(
    row: dict[str, Any],
    metadata: dict[str, Any],
    readiness: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    _check_no_export_or_execution(row, metadata, issues)
    _check_safety_flags(row, metadata, readiness, issues)
    _check_export_ready_rows(row, readiness, issues)


def _check_no_export_or_execution(row: dict[str, Any], metadata: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    false_flags = {
        "would_write_data_raw": "DATA_RAW_WRITE_DETECTED",
        "would_write_data_processed": "DATA_PROCESSED_WRITE_DETECTED",
        "universe_exported": "UNIVERSE_EXPORT_DETECTED",
        "current_candidates_executed": "CURRENT_CANDIDATES_GENERATED",
        "snapshot_manifest_built": "SNAPSHOT_BUILT",
        "snapshot_manifests_built": "SNAPSHOT_BUILT",
        "forward_returns_computed": "FORWARD_LABELS_COMPUTED",
        "cache_mutated": "CACHE_MUTATION_DETECTED",
        "network_api_called": "NETWORK_OR_API_DETECTED",
        "external_api_called": "NETWORK_OR_API_DETECTED",
        "llm_api_called": "NETWORK_OR_API_DETECTED",
    }
    for flag, code in false_flags.items():
        if _to_bool(metadata.get(flag)):
            issues.append(
                _issue(
                    row,
                    "metadata_path",
                    row.get("metadata_path"),
                    "ERROR",
                    code,
                    f"{flag}=true detected.",
                    "Regenerate export-readiness artifacts as report-only artifacts.",
                )
            )
    true_flags = {
        "no_current_candidates_generated": "CURRENT_CANDIDATES_GENERATED",
        "no_snapshot_built": "SNAPSHOT_BUILT",
        "no_forward_labels": "FORWARD_LABELS_COMPUTED",
    }
    for flag, code in true_flags.items():
        if not _to_bool(metadata.get(flag, False)):
            issues.append(
                _issue(
                    row,
                    "metadata_path",
                    row.get("metadata_path"),
                    "ERROR",
                    code,
                    f"{flag}=true is missing from metadata.",
                    "Regenerate export-readiness artifacts with report-only safety metadata.",
                )
            )


def _check_safety_flags(
    row: dict[str, Any],
    metadata: dict[str, Any],
    readiness: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    checks = [
        ("no_live_trading", "LIVE_TRADING_DETECTED"),
        ("no_broker_api", "BROKER_DETECTED"),
        ("no_order_placement", "ORDER_PLACEMENT_DETECTED"),
        ("no_message_sent", "MESSAGE_DELIVERY_DETECTED"),
    ]
    for field, code in checks:
        if not _to_bool(metadata.get(field, False)):
            issues.append(
                _issue(
                    row,
                    "metadata_path",
                    row.get("metadata_path"),
                    "ERROR",
                    code,
                    f"{field}=true is missing from metadata.",
                    "Regenerate export-readiness artifacts with safety metadata.",
                )
            )
        if field in readiness.columns and (~readiness[field].map(_to_bool)).any():
            issues.append(
                _issue(
                    row,
                    "readiness_csv_path",
                    row.get("readiness_csv_path"),
                    "ERROR",
                    code,
                    f"A row does not have {field}=true.",
                    "Regenerate export-readiness artifacts with safety row fields.",
                )
            )
    unsafe_flags = {
        "live_trading_enabled": "LIVE_TRADING_DETECTED",
        "broker_api_invoked": "BROKER_DETECTED",
        "order_placement_enabled": "ORDER_PLACEMENT_DETECTED",
        "message_delivery_enabled": "MESSAGE_DELIVERY_DETECTED",
        "message_sent": "MESSAGE_DELIVERY_DETECTED",
    }
    for flag, code in unsafe_flags.items():
        if _to_bool(metadata.get(flag)):
            issues.append(
                _issue(
                    row,
                    "metadata_path",
                    row.get("metadata_path"),
                    "ERROR",
                    code,
                    f"{flag}=true detected.",
                    "Regenerate local-only export-readiness artifacts.",
                )
            )


def _check_export_ready_rows(row: dict[str, Any], readiness: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if readiness.empty or "export_ready" not in readiness.columns:
        return
    ready = readiness["export_ready"].map(_to_bool)
    if not ready.any():
        return
    ready_frame = readiness.loc[ready].copy()
    missing_counts = ready_frame.get("required_column_missing_count", pd.Series([0] * len(ready_frame))).map(_to_int)
    missing_text = ready_frame.get("missing_required_columns", pd.Series([""] * len(ready_frame))).map(_string_or_empty)
    if (missing_counts > 0).any() or missing_text.ne("").any():
        issues.append(
            _issue(
                row,
                "readiness_csv_path",
                row.get("readiness_csv_path"),
                "ERROR",
                "EXPORT_READY_MISSING_REQUIRED_COLUMNS",
                "An export_ready row still has missing required universe columns.",
                "Keep the row blocked until required universe columns are complete or explicitly mappable.",
            )
        )


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PIT_UNIVERSE_OVERLAY_EXPORT_READINESS_INDEX_COLUMNS)
    output = frame.copy()
    for column in PIT_UNIVERSE_OVERLAY_EXPORT_READINESS_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[PIT_UNIVERSE_OVERLAY_EXPORT_READINESS_INDEX_COLUMNS].reset_index(drop=True)


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    output = frame.copy()
    for column in HEALTH_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[HEALTH_COLUMNS].reset_index(drop=True)


def _issue(
    row: dict[str, Any],
    path_field: str,
    path_value: Any,
    severity: str,
    issue_code: str,
    issue_message: str,
    suggested_action: str,
) -> dict[str, Any]:
    return {
        "artifact_type": "PIT_UNIVERSE_OVERLAY_EXPORT_READINESS",
        "export_readiness_id": _string_or_empty(row.get("export_readiness_id")),
        "path_field": path_field,
        "path_value": str(path_value or ""),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _to_int(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
    except (TypeError, ValueError):
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "nat", "none", "null"} else text


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item") and value.__class__.__module__.startswith("numpy"):
        return _json_safe(value.item())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _dict_table(values: dict[str, Any]) -> str:
    return "\n".join(f"- {key}: {value}" for key, value in values.items())


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 200) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "No rows."
    return frame[available].head(max_rows).to_markdown(index=False)
