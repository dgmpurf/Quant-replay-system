"""Local-only index for calibration-to-signal-semantics proposal artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


CALIBRATION_TO_SEMANTICS_INDEX_LIMITATIONS = [
    "Scans local calibration-to-signal-semantics proposal artifact folders only.",
    "Reads reports already written by calibration-to-signal-semantics.",
    "Does not regenerate calibration, change signal semantics defaults, or write config.",
    "Does not send messages, place orders, call brokers, call APIs, or enable live trading.",
]

CALIBRATION_TO_SEMANTICS_INDEX_COLUMNS = [
    "artifact_type",
    "proposal_run_id",
    "status",
    "calibration_run_count",
    "observed_review_buy_candidate_count",
    "observed_watch_count",
    "observed_blocked_count",
    "defaults_changed",
    "proposal_categories",
    "report_path",
    "summary_csv_path",
    "proposals_csv_path",
    "metadata_path",
    "created_at",
]


@dataclass(frozen=True)
class CalibrationToSemanticsIndexSettings:
    root_dir: Path = Path("outputs/reports/calibration_to_signal_semantics")
    output_dir: Path = Path("outputs/reports/calibration_to_signal_semantics/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: bool = False
    enable_broker_api: bool = False


@dataclass(frozen=True)
class CalibrationToSemanticsIndexPaths:
    artifact_dir: Path
    calibration_to_signal_semantics_index_csv: Path
    calibration_to_signal_semantics_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "calibration_to_signal_semantics_index_csv": self.calibration_to_signal_semantics_index_csv,
            "calibration_to_signal_semantics_index_report": self.calibration_to_signal_semantics_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CalibrationToSemanticsIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_calibration_to_signal_semantics_artifacts(
    root: str | Path | None = None,
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _warnings = _scan_artifact_rows(
        Path(root) if root is not None else CalibrationToSemanticsIndexSettings().root_dir,
        include_missing_metadata=include_missing_metadata,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def build_calibration_to_signal_semantics_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_missing_metadata: bool | None = None,
    settings: CalibrationToSemanticsIndexSettings | dict[str, Any] | None = None,
) -> CalibrationToSemanticsIndexResult:
    resolved = _resolve_settings(settings)
    if resolved.enable_live_trading or resolved.enable_broker_api:
        raise ValueError("Calibration-to-semantics index cannot enable live trading or broker API access")
    effective_root = Path(root) if root is not None else resolved.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else resolved.output_dir
    effective_include_missing = (
        bool(include_missing_metadata)
        if include_missing_metadata is not None
        else resolved.include_missing_metadata
    )
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=effective_include_missing)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_calibration_to_signal_semantics_index_paths(effective_output_dir)
    audit_metadata = {
        "root_dir": effective_root,
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(index_frame),
        "config_version": resolved.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "external_api_called": False,
        "config_mutated": False,
        "proposal_artifacts_only": True,
    }
    result = CalibrationToSemanticsIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=CALIBRATION_TO_SEMANTICS_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if resolved.write_artifacts:
        write_calibration_to_signal_semantics_index(result)
    return result


def resolve_calibration_to_signal_semantics_index_paths(output_dir: str | Path) -> CalibrationToSemanticsIndexPaths:
    artifact_dir = Path(output_dir)
    return CalibrationToSemanticsIndexPaths(
        artifact_dir=artifact_dir,
        calibration_to_signal_semantics_index_csv=artifact_dir / "calibration_to_signal_semantics_index.csv",
        calibration_to_signal_semantics_index_report=artifact_dir / "calibration_to_signal_semantics_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_calibration_to_signal_semantics_index(result: CalibrationToSemanticsIndexResult) -> dict[str, Path]:
    paths = CalibrationToSemanticsIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.calibration_to_signal_semantics_index_csv, index=False)
    metadata = build_calibration_to_signal_semantics_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.calibration_to_signal_semantics_index_report.write_text(
        render_calibration_to_signal_semantics_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_calibration_to_signal_semantics_index_metadata(
    result: CalibrationToSemanticsIndexResult,
    paths: CalibrationToSemanticsIndexPaths,
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
        "external_api_called": False,
        "llm_api_called": False,
        "config_mutated": False,
        "proposal_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.",
    }


def render_calibration_to_signal_semantics_index_report(
    result: CalibrationToSemanticsIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"index_id": _generate_index_id(result.index_frame, result.audit_metadata)}
    lines = [
        "# Calibration-to-Signal Semantics Proposal Artifact Index",
        "",
        "No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked. This index scans local proposal artifacts only.",
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
                "proposal_run_id",
                "status",
                "calibration_run_count",
                "observed_review_buy_candidate_count",
                "observed_watch_count",
                "observed_blocked_count",
                "defaults_changed",
                "proposal_categories",
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
        return rows, [f"Calibration-to-signal-semantics proposal artifact root does not exist: {root}"]
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
            warnings.append(f"Could not read proposal metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        proposal_run_id = str(metadata.get("proposal_run_id") or "").strip()
        if not proposal_run_id:
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    outputs = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    report_path = Path(outputs.get("calibration_to_signal_semantics_report") or artifact_dir / "calibration_to_signal_semantics_report.md")
    summary_path = Path(outputs.get("calibration_to_signal_semantics_summary") or artifact_dir / "calibration_to_signal_semantics_summary.csv")
    proposals_path = Path(outputs.get("calibration_to_signal_semantics_proposals") or artifact_dir / "calibration_to_signal_semantics_proposals.csv")
    summary = _first_csv_record(summary_path)
    categories = _proposal_categories(metadata, proposals_path)
    comparison = metadata.get("comparison") if isinstance(metadata.get("comparison"), dict) else {}
    return {
        "artifact_type": "CALIBRATION_TO_SIGNAL_SEMANTICS_PROPOSAL",
        "proposal_run_id": str(metadata.get("proposal_run_id") or artifact_dir.name),
        "status": str(metadata.get("status") or summary.get("status") or "READY"),
        "calibration_run_count": _to_int(metadata.get("calibration_run_count", summary.get("calibration_run_count"))),
        "observed_review_buy_candidate_count": _to_int(
            comparison.get("observed_review_buy_candidate_count", summary.get("observed_review_buy_candidate_count"))
        ),
        "observed_watch_count": _to_int(comparison.get("observed_watch_count", summary.get("observed_watch_count"))),
        "observed_blocked_count": _to_int(comparison.get("observed_blocked_count", summary.get("observed_blocked_count"))),
        "defaults_changed": _to_bool(metadata.get("defaults_changed", summary.get("defaults_changed", False))),
        "proposal_categories": ";".join(categories),
        "report_path": str(report_path),
        "summary_csv_path": str(summary_path),
        "proposals_csv_path": str(proposals_path),
        "metadata_path": str(metadata_path),
        "created_at": str(metadata.get("created_at") or _artifact_mtime(artifact_dir)),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    return {
        "artifact_type": "CALIBRATION_TO_SIGNAL_SEMANTICS_PROPOSAL",
        "proposal_run_id": artifact_dir.name,
        "status": status,
        "calibration_run_count": 0,
        "observed_review_buy_candidate_count": 0,
        "observed_watch_count": 0,
        "observed_blocked_count": 0,
        "defaults_changed": False,
        "proposal_categories": "",
        "report_path": str(artifact_dir / "calibration_to_signal_semantics_report.md"),
        "summary_csv_path": str(artifact_dir / "calibration_to_signal_semantics_summary.csv"),
        "proposals_csv_path": str(artifact_dir / "calibration_to_signal_semantics_proposals.csv"),
        "metadata_path": str(artifact_dir / "metadata.json"),
        "created_at": _artifact_mtime(artifact_dir),
    }


def _proposal_categories(metadata: dict[str, Any], proposals_path: Path) -> list[str]:
    raw = metadata.get("proposal_categories")
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    if proposals_path.exists():
        try:
            frame = pd.read_csv(proposals_path, keep_default_na=False)
        except Exception:
            return []
        if "category" in frame.columns:
            return [str(item).strip() for item in frame["category"].dropna().astype(str) if str(item).strip()]
    return []


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


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=CALIBRATION_TO_SEMANTICS_INDEX_COLUMNS)
    output = frame.copy()
    for column in CALIBRATION_TO_SEMANTICS_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    output = output[CALIBRATION_TO_SEMANTICS_INDEX_COLUMNS].sort_values(["created_at", "proposal_run_id"]).reset_index(drop=True)
    output["defaults_changed"] = output["defaults_changed"].map(_to_bool).astype(object)
    return output


def _resolve_settings(settings: CalibrationToSemanticsIndexSettings | dict[str, Any] | None) -> CalibrationToSemanticsIndexSettings:
    if settings is None:
        return CalibrationToSemanticsIndexSettings()
    if isinstance(settings, CalibrationToSemanticsIndexSettings):
        return settings
    return CalibrationToSemanticsIndexSettings(**{**CalibrationToSemanticsIndexSettings().__dict__, **settings})


def _generate_index_id(frame: pd.DataFrame, metadata: dict[str, Any]) -> str:
    return _hash_payload({"rows": frame.to_dict("records"), "metadata": _json_safe(metadata)}, length=12)


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
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in frame.loc[:, available].head(max_rows).to_dict("records"):
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
