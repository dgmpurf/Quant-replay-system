"""Local-only index for signal semantics artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import Settings, SignalSemanticsIndexSettings, load_settings
from quant_replay_system.data import read_csv_preserve_symbol_columns


SIGNAL_SEMANTICS_INDEX_LIMITATIONS = [
    "Scans local signal semantics artifact folders only.",
    "Reads artifacts already written by signal-semantics.",
    "Does not regenerate candidates, semantics decisions, or quality reports.",
    "Does not send messages, place orders, call brokers, or enable live trading.",
]

SIGNAL_SEMANTICS_INDEX_COLUMNS = [
    "artifact_type",
    "semantics_run_id",
    "status",
    "row_count",
    "demo_only_count",
    "watch_count",
    "review_buy_candidate_count",
    "review_sell_candidate_count",
    "hold_review_count",
    "no_action_count",
    "blocked_count",
    "issue_count",
    "input_path",
    "input_type",
    "profile",
    "data_quality_status",
    "snapshot_quality_status",
    "no_live_trading",
    "no_broker_api",
    "auto_order_allowed",
    "report_path",
    "semantics_csv_path",
    "issues_csv_path",
    "metadata_path",
    "created_at",
]


@dataclass(frozen=True)
class SignalSemanticsIndexPaths:
    artifact_dir: Path
    signal_semantics_index_csv: Path
    signal_semantics_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "signal_semantics_index_csv": self.signal_semantics_index_csv,
            "signal_semantics_index_report": self.signal_semantics_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SignalSemanticsIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_signal_semantics_artifacts(
    root: str | Path | None = None,
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    """Scan local signal semantics artifact folders and return an index frame."""

    rows, _warnings = _scan_artifact_rows(
        Path(root) if root is not None else SignalSemanticsIndexSettings().root_dir,
        include_missing_metadata=include_missing_metadata,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def build_signal_semantics_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_missing_metadata: bool | None = None,
    settings: Settings | SignalSemanticsIndexSettings | dict[str, Any] | None = None,
) -> SignalSemanticsIndexResult:
    """Build and optionally write a signal semantics artifact index."""

    project_settings, index_settings = _resolve_settings(settings)
    if index_settings.enable_live_trading or index_settings.enable_broker_api:
        raise ValueError("Signal semantics index cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else index_settings.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else index_settings.output_dir
    effective_include_missing = (
        bool(include_missing_metadata)
        if include_missing_metadata is not None
        else index_settings.include_missing_metadata
    )
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=effective_include_missing)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_signal_semantics_index_paths(effective_output_dir)
    audit_metadata = {
        "root_dir": effective_root,
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(index_frame),
        "config_version": index_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "signal_semantics_artifacts_only": True,
    }
    result = SignalSemanticsIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=SIGNAL_SEMANTICS_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if index_settings.write_artifacts:
        write_signal_semantics_index(result)
    _ = project_settings
    return result


def resolve_signal_semantics_index_paths(output_dir: str | Path) -> SignalSemanticsIndexPaths:
    """Resolve stable signal semantics index artifact paths."""

    artifact_dir = Path(output_dir)
    return SignalSemanticsIndexPaths(
        artifact_dir=artifact_dir,
        signal_semantics_index_csv=artifact_dir / "signal_semantics_index.csv",
        signal_semantics_index_report=artifact_dir / "signal_semantics_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_signal_semantics_index(result: SignalSemanticsIndexResult) -> dict[str, Path]:
    """Write signal semantics index CSV, report, and metadata."""

    paths = SignalSemanticsIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.signal_semantics_index_csv, index=False)
    metadata = build_signal_semantics_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.signal_semantics_index_report.write_text(
        render_signal_semantics_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_signal_semantics_index_metadata(
    result: SignalSemanticsIndexResult,
    paths: SignalSemanticsIndexPaths,
) -> dict[str, Any]:
    """Build metadata for signal semantics index output."""

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
        "signal_semantics_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, or message delivery was invoked.",
    }


def render_signal_semantics_index_report(
    result: SignalSemanticsIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render the markdown signal semantics index report."""

    meta = metadata or {"index_id": _generate_index_id(result.index_frame, result.audit_metadata)}
    lines = [
        "# Signal Semantics Artifact Index",
        "",
        "No live trading, broker API, order placement, or message delivery was invoked. This index scans local signal semantics artifacts only.",
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
                "semantics_run_id",
                "status",
                "row_count",
                "demo_only_count",
                "watch_count",
                "review_buy_candidate_count",
                "review_sell_candidate_count",
                "blocked_count",
                "issue_count",
                "profile",
                "input_type",
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
        return rows, [f"Signal semantics artifact root does not exist: {root}"]
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata and artifact_dir.name not in {"index", "health", "status"}:
                rows.append(_missing_metadata_row(artifact_dir))
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read signal semantics metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        semantics_run_id = str(metadata.get("semantics_run_id") or "").strip()
        if not semantics_run_id:
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    outputs = metadata.get("outputs") if isinstance(metadata.get("outputs"), dict) else {}
    audit = metadata.get("audit_metadata") if isinstance(metadata.get("audit_metadata"), dict) else {}
    semantics_csv_path = Path(outputs.get("signal_semantics") or artifact_dir / "signal_semantics.csv")
    issues_csv_path = Path(outputs.get("signal_semantics_issues") or artifact_dir / "signal_semantics_issues.csv")
    report_path = Path(outputs.get("signal_semantics_report") or artifact_dir / "signal_semantics_report.md")
    action_counts = _action_counts(metadata)
    csv_statuses = _csv_statuses(semantics_csv_path)
    return {
        "artifact_type": "SIGNAL_SEMANTICS",
        "semantics_run_id": str(metadata.get("semantics_run_id") or artifact_dir.name),
        "status": str(metadata.get("status") or "READY"),
        "row_count": _to_int(metadata.get("row_count")),
        "demo_only_count": _to_int(metadata.get("demo_only_count") or action_counts.get("DEMO_ONLY")),
        "watch_count": _to_int(metadata.get("watch_count") or action_counts.get("WATCH")),
        "review_buy_candidate_count": _to_int(
            metadata.get("review_buy_candidate_count") or action_counts.get("REVIEW_BUY_CANDIDATE")
        ),
        "review_sell_candidate_count": _to_int(
            metadata.get("review_sell_candidate_count") or action_counts.get("REVIEW_SELL_CANDIDATE")
        ),
        "hold_review_count": _to_int(metadata.get("hold_review_count") or action_counts.get("HOLD_REVIEW")),
        "no_action_count": _to_int(metadata.get("no_action_count") or action_counts.get("NO_ACTION")),
        "blocked_count": _to_int(metadata.get("blocked_count") or action_counts.get("BLOCKED")),
        "issue_count": _to_int(metadata.get("issue_count")),
        "input_path": str(metadata.get("input_path") or audit.get("input_path") or ""),
        "input_type": str(metadata.get("input_type") or audit.get("input_type") or ""),
        "profile": str(metadata.get("profile") or audit.get("profile") or ""),
        "data_quality_status": str(metadata.get("data_quality_status") or csv_statuses.get("data_quality_status", "")),
        "snapshot_quality_status": str(
            metadata.get("snapshot_quality_status") or csv_statuses.get("snapshot_quality_status", "")
        ),
        "no_live_trading": _to_bool(metadata.get("no_live_trading", audit.get("no_live_trading", False))),
        "no_broker_api": _to_bool(metadata.get("no_broker_api", audit.get("no_broker_api", False))),
        "auto_order_allowed": _to_bool(metadata.get("auto_order_allowed", audit.get("auto_order_allowed", False))),
        "report_path": str(report_path),
        "semantics_csv_path": str(semantics_csv_path),
        "issues_csv_path": str(issues_csv_path),
        "metadata_path": str(metadata_path),
        "created_at": str(metadata.get("created_at") or ""),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    return {
        "artifact_type": "SIGNAL_SEMANTICS",
        "semantics_run_id": artifact_dir.name,
        "status": status,
        "row_count": 0,
        "demo_only_count": 0,
        "watch_count": 0,
        "review_buy_candidate_count": 0,
        "review_sell_candidate_count": 0,
        "hold_review_count": 0,
        "no_action_count": 0,
        "blocked_count": 0,
        "issue_count": 1,
        "input_path": "",
        "input_type": "",
        "profile": "",
        "data_quality_status": "",
        "snapshot_quality_status": "",
        "no_live_trading": False,
        "no_broker_api": False,
        "auto_order_allowed": False,
        "report_path": str(artifact_dir / "signal_semantics_report.md"),
        "semantics_csv_path": str(artifact_dir / "signal_semantics.csv"),
        "issues_csv_path": str(artifact_dir / "signal_semantics_issues.csv"),
        "metadata_path": str(artifact_dir / "metadata.json"),
        "created_at": "",
    }


def _action_counts(metadata: dict[str, Any]) -> dict[str, int]:
    counts = metadata.get("action_counts")
    if not isinstance(counts, dict):
        audit = metadata.get("audit_metadata") if isinstance(metadata.get("audit_metadata"), dict) else {}
        counts = audit.get("action_counts")
    if not isinstance(counts, dict):
        return {}
    return {str(key): _to_int(value) for key, value in counts.items()}


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
        return pd.DataFrame(columns=SIGNAL_SEMANTICS_INDEX_COLUMNS)
    output = frame.copy()
    for column in SIGNAL_SEMANTICS_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[SIGNAL_SEMANTICS_INDEX_COLUMNS].sort_values(["created_at", "semantics_run_id"]).reset_index(drop=True)


def _resolve_settings(
    settings: Settings | SignalSemanticsIndexSettings | dict[str, Any] | None,
) -> tuple[Settings, SignalSemanticsIndexSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.signal_semantics_index
    if isinstance(settings, Settings):
        return settings, settings.signal_semantics_index
    if isinstance(settings, SignalSemanticsIndexSettings):
        project = load_settings(Path("config/default.yaml"))
        return project.model_copy(update={"signal_semantics_index": settings}), settings
    project = load_settings(Path("config/default.yaml"))
    updated = project.signal_semantics_index.model_copy(update=settings)
    return project.model_copy(update={"signal_semantics_index": updated}), updated


def _generate_index_id(frame: pd.DataFrame, metadata: dict[str, Any]) -> str:
    payload = {"rows": frame.to_dict("records"), "metadata": _json_safe(metadata)}
    return _hash_payload(payload, length=12)


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if frame.empty or "created_at" not in frame.columns:
        return "1970-01-01T00:00:00+00:00"
    values = [str(value) for value in frame["created_at"].dropna().tolist() if str(value).strip()]
    return max(values) if values else "1970-01-01T00:00:00+00:00"


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
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return text


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
