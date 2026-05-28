"""Local-only index for advisory profile calibration artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import AdvisoryProfileCalibrationIndexSettings, Settings, load_settings
from quant_replay_system.data import read_csv_preserve_symbol_columns


ADVISORY_PROFILE_CALIBRATION_INDEX_LIMITATIONS = [
    "Scans local advisory profile calibration artifact folders only.",
    "Reads artifacts already written by advisory-profile-calibration.",
    "Does not regenerate candidates, thresholds, labels, or quality reports.",
    "Does not send messages, place orders, call brokers, or enable live trading.",
]

ADVISORY_PROFILE_CALIBRATION_INDEX_COLUMNS = [
    "artifact_type",
    "calibration_run_id",
    "status",
    "profile",
    "input_type",
    "row_count",
    "review_buy_candidate_count",
    "watch_count",
    "no_action_count",
    "blocked_count",
    "demo_only_count",
    "issue_count",
    "data_quality_status",
    "snapshot_quality_status",
    "requires_manual_confirmation",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "no_message_sent",
    "report_path",
    "calibration_csv_path",
    "summary_csv_path",
    "issues_csv_path",
    "metadata_path",
    "input_path",
    "created_at",
]


@dataclass(frozen=True)
class AdvisoryProfileCalibrationIndexPaths:
    artifact_dir: Path
    advisory_profile_calibration_index_csv: Path
    advisory_profile_calibration_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "advisory_profile_calibration_index_csv": self.advisory_profile_calibration_index_csv,
            "advisory_profile_calibration_index_report": self.advisory_profile_calibration_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AdvisoryProfileCalibrationIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_advisory_profile_calibration_artifacts(
    root: str | Path | None = None,
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    """Scan local advisory profile calibration artifact folders."""

    rows, _warnings = _scan_artifact_rows(
        Path(root) if root is not None else AdvisoryProfileCalibrationIndexSettings().root_dir,
        include_missing_metadata=include_missing_metadata,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def build_advisory_profile_calibration_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_missing_metadata: bool | None = None,
    settings: Settings | AdvisoryProfileCalibrationIndexSettings | dict[str, Any] | None = None,
) -> AdvisoryProfileCalibrationIndexResult:
    """Build and optionally write an advisory profile calibration artifact index."""

    project_settings, index_settings = _resolve_settings(settings)
    if index_settings.enable_live_trading or index_settings.enable_broker_api:
        raise ValueError("Advisory profile calibration index cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else index_settings.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else index_settings.output_dir
    effective_include_missing = (
        bool(include_missing_metadata)
        if include_missing_metadata is not None
        else index_settings.include_missing_metadata
    )
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=effective_include_missing)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_advisory_profile_calibration_index_paths(effective_output_dir)
    audit_metadata = {
        "root_dir": effective_root,
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(index_frame),
        "config_version": index_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "advisory_profile_calibration_artifacts_only": True,
    }
    result = AdvisoryProfileCalibrationIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=ADVISORY_PROFILE_CALIBRATION_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if index_settings.write_artifacts:
        write_advisory_profile_calibration_index(result)
    _ = project_settings
    return result


def resolve_advisory_profile_calibration_index_paths(output_dir: str | Path) -> AdvisoryProfileCalibrationIndexPaths:
    artifact_dir = Path(output_dir)
    return AdvisoryProfileCalibrationIndexPaths(
        artifact_dir=artifact_dir,
        advisory_profile_calibration_index_csv=artifact_dir / "advisory_profile_calibration_index.csv",
        advisory_profile_calibration_index_report=artifact_dir / "advisory_profile_calibration_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_advisory_profile_calibration_index(result: AdvisoryProfileCalibrationIndexResult) -> dict[str, Path]:
    paths = AdvisoryProfileCalibrationIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.advisory_profile_calibration_index_csv, index=False)
    metadata = build_advisory_profile_calibration_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.advisory_profile_calibration_index_report.write_text(
        render_advisory_profile_calibration_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_advisory_profile_calibration_index_metadata(
    result: AdvisoryProfileCalibrationIndexResult,
    paths: AdvisoryProfileCalibrationIndexPaths,
) -> dict[str, Any]:
    return {
        "index_id": _generate_index_id(result.index_frame, result.audit_metadata),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "config_summary": {
            "root_dir": str(result.audit_metadata.get("root_dir", "")),
            "include_missing_metadata": bool(result.audit_metadata.get("include_missing_metadata", False)),
            "config_version": result.audit_metadata.get("config_version", ""),
        },
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "advisory_profile_calibration_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, or message delivery was invoked.",
    }


def render_advisory_profile_calibration_index_report(
    result: AdvisoryProfileCalibrationIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"index_id": _generate_index_id(result.index_frame, result.audit_metadata)}
    lines = [
        "# Advisory Profile Calibration Artifact Index",
        "",
        "No live trading, broker API, order placement, or message delivery was invoked. This index scans local calibration artifacts only.",
        "",
        "## Index Metadata",
        "",
        _dict_table(
            {
                "index_id": meta.get("index_id", ""),
                "root_dir": result.audit_metadata.get("root_dir", ""),
                "artifact_count": result.artifact_count,
                "include_missing_metadata": result.audit_metadata.get("include_missing_metadata", False),
            }
        ),
        "",
        "## Artifact Index",
        "",
        _markdown_table(
            result.index_frame,
            [
                "calibration_run_id",
                "status",
                "profile",
                "row_count",
                "review_buy_candidate_count",
                "watch_count",
                "no_action_count",
                "blocked_count",
                "demo_only_count",
                "issue_count",
                "report_path",
            ],
            max_rows=100,
        ),
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


def _scan_artifact_rows(root: Path, *, include_missing_metadata: bool) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root.exists():
        return rows, [f"Advisory profile calibration artifact root does not exist: {root}"]
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir))
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read advisory profile calibration metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        calibration_run_id = str(metadata.get("calibration_run_id") or "").strip()
        if not calibration_run_id:
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    outputs = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    if not outputs:
        outputs = metadata.get("outputs") if isinstance(metadata.get("outputs"), dict) else {}
    calibration_csv_path = Path(outputs.get("advisory_profile_calibration") or artifact_dir / "advisory_profile_calibration.csv")
    summary_csv_path = Path(outputs.get("advisory_profile_calibration_summary") or artifact_dir / "advisory_profile_calibration_summary.csv")
    issues_csv_path = Path(outputs.get("advisory_profile_calibration_issues") or artifact_dir / "advisory_profile_calibration_issues.csv")
    report_path = Path(outputs.get("advisory_profile_calibration_report") or artifact_dir / "advisory_profile_calibration_report.md")
    summary = _first_csv_record(summary_csv_path)
    label_counts = _label_counts(metadata, summary)
    csv_statuses = _csv_statuses(calibration_csv_path)
    return {
        "artifact_type": "ADVISORY_PROFILE_CALIBRATION",
        "calibration_run_id": str(metadata.get("calibration_run_id") or artifact_dir.name),
        "status": str(metadata.get("status") or summary.get("status") or "READY"),
        "profile": str(metadata.get("profile") or summary.get("profile") or ""),
        "input_type": str(metadata.get("input_type") or summary.get("input_type") or ""),
        "row_count": _to_int(metadata.get("row_count", summary.get("row_count"))),
        "review_buy_candidate_count": _to_int(label_counts.get("REVIEW_BUY_CANDIDATE")),
        "watch_count": _to_int(label_counts.get("WATCH")),
        "no_action_count": _to_int(label_counts.get("NO_ACTION")),
        "blocked_count": _to_int(label_counts.get("BLOCKED")),
        "demo_only_count": _to_int(label_counts.get("DEMO_ONLY")),
        "issue_count": _to_int(metadata.get("issue_count", summary.get("issue_count"))),
        "data_quality_status": str(metadata.get("data_quality_status") or csv_statuses.get("data_quality_status", "")),
        "snapshot_quality_status": str(
            metadata.get("snapshot_quality_status") or csv_statuses.get("snapshot_quality_status", "")
        ),
        "requires_manual_confirmation": _to_bool(metadata.get("requires_manual_confirmation", summary.get("requires_manual_confirmation", False))),
        "auto_order_allowed": _to_bool(metadata.get("auto_order_allowed", summary.get("auto_order_allowed", False))),
        "no_live_trading": _to_bool(metadata.get("no_live_trading", summary.get("no_live_trading", False))),
        "no_broker_api": _to_bool(metadata.get("no_broker_api", summary.get("no_broker_api", False))),
        "no_message_sent": _to_bool(metadata.get("no_message_sent", summary.get("no_message_sent", False))),
        "report_path": str(report_path),
        "calibration_csv_path": str(calibration_csv_path),
        "summary_csv_path": str(summary_csv_path),
        "issues_csv_path": str(issues_csv_path),
        "metadata_path": str(metadata_path),
        "input_path": str(metadata.get("input_path") or summary.get("input_path") or ""),
        "created_at": str(metadata.get("created_at") or _artifact_mtime(artifact_dir)),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    return {
        "artifact_type": "ADVISORY_PROFILE_CALIBRATION",
        "calibration_run_id": artifact_dir.name,
        "status": status,
        "profile": "",
        "input_type": "",
        "row_count": 0,
        "review_buy_candidate_count": 0,
        "watch_count": 0,
        "no_action_count": 0,
        "blocked_count": 0,
        "demo_only_count": 0,
        "issue_count": 1,
        "data_quality_status": "",
        "snapshot_quality_status": "",
        "requires_manual_confirmation": False,
        "auto_order_allowed": False,
        "no_live_trading": False,
        "no_broker_api": False,
        "no_message_sent": False,
        "report_path": str(artifact_dir / "advisory_profile_calibration_report.md"),
        "calibration_csv_path": str(artifact_dir / "advisory_profile_calibration.csv"),
        "summary_csv_path": str(artifact_dir / "advisory_profile_calibration_summary.csv"),
        "issues_csv_path": str(artifact_dir / "advisory_profile_calibration_issues.csv"),
        "metadata_path": str(artifact_dir / "metadata.json"),
        "input_path": "",
        "created_at": _artifact_mtime(artifact_dir),
    }


def _label_counts(metadata: dict[str, Any], summary: dict[str, Any]) -> dict[str, int]:
    counts = metadata.get("label_counts")
    if isinstance(counts, dict):
        return {str(key): _to_int(value) for key, value in counts.items()}
    return {
        "REVIEW_BUY_CANDIDATE": _to_int(summary.get("review_buy_candidate_count")),
        "WATCH": _to_int(summary.get("watch_count")),
        "NO_ACTION": _to_int(summary.get("no_action_count")),
        "BLOCKED": _to_int(summary.get("blocked_count")),
        "DEMO_ONLY": _to_int(summary.get("demo_only_count")),
    }


def _first_csv_record(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        frame = pd.read_csv(path, keep_default_na=False)
    except Exception:
        return {}
    if frame.empty:
        return {}
    return frame.iloc[0].to_dict()


def _csv_statuses(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception:
        return {}
    return {
        "data_quality_status": _first_non_empty(frame, "data_quality_status"),
        "snapshot_quality_status": _first_non_empty(frame, "snapshot_quality_status"),
    }


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=ADVISORY_PROFILE_CALIBRATION_INDEX_COLUMNS)
    output = frame.copy()
    for column in ADVISORY_PROFILE_CALIBRATION_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return (
        output[ADVISORY_PROFILE_CALIBRATION_INDEX_COLUMNS]
        .sort_values(["created_at", "calibration_run_id"])
        .reset_index(drop=True)
    )


def _resolve_settings(
    settings: Settings | AdvisoryProfileCalibrationIndexSettings | dict[str, Any] | None,
) -> tuple[Settings, AdvisoryProfileCalibrationIndexSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.advisory_profile_calibration_index
    if isinstance(settings, Settings):
        return settings, settings.advisory_profile_calibration_index
    if isinstance(settings, AdvisoryProfileCalibrationIndexSettings):
        project = load_settings(Path("config/default.yaml"))
        return project.model_copy(update={"advisory_profile_calibration_index": settings}), settings
    project = load_settings(Path("config/default.yaml"))
    updated = project.advisory_profile_calibration_index.model_copy(update=settings)
    return project.model_copy(update={"advisory_profile_calibration_index": updated}), updated


def _generate_index_id(frame: pd.DataFrame, metadata: dict[str, Any]) -> str:
    payload = {"rows": frame.to_dict("records"), "metadata": _json_safe(metadata)}
    return _hash_payload(payload, length=12)


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if frame.empty or "created_at" not in frame.columns:
        return "1970-01-01T00:00:00+00:00"
    values = [str(value) for value in frame["created_at"].dropna().tolist() if str(value).strip()]
    return max(values) if values else "1970-01-01T00:00:00+00:00"


def _artifact_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return ""


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _first_non_empty(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    for value in frame[column].dropna().astype(str):
        if value.strip():
            return value.strip()
    return ""


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
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


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
    if value is None:
        return ""
    return str(value).replace("\n", " ").replace("|", "\\|")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
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
