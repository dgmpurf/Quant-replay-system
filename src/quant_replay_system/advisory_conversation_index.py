"""Local-only index for advisory conversation artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import AdvisoryConversationIndexSettings, Settings, load_settings


ADVISORY_CONVERSATION_INDEX_LIMITATIONS = [
    "Scans local advisory-conversation artifact folders only.",
    "Reads artifacts already written by advisory-conversation.",
    "Does not parse new questions, call LLM/external APIs, send messages, place orders, or call brokers.",
]

ADVISORY_CONVERSATION_INDEX_COLUMNS = [
    "artifact_type",
    "conversation_run_id",
    "original_question",
    "parsed_symbol",
    "parsed_intent",
    "status",
    "advisory_action",
    "parser_type",
    "linked_advisory_run_id",
    "linked_answer_run_id",
    "linked_answer_markdown_path",
    "llm_api_called",
    "external_api_called",
    "no_message_sent",
    "no_live_trading",
    "no_broker_api",
    "auto_order_allowed",
    "report_path",
    "conversation_json_path",
    "metadata_path",
    "created_at",
]


@dataclass(frozen=True)
class AdvisoryConversationIndexPaths:
    artifact_dir: Path
    advisory_conversation_index_csv: Path
    advisory_conversation_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "advisory_conversation_index_csv": self.advisory_conversation_index_csv,
            "advisory_conversation_index_report": self.advisory_conversation_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AdvisoryConversationIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_advisory_conversation_artifacts(
    root: str | Path | None = None,
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _ = _scan_artifact_rows(
        Path(root) if root is not None else AdvisoryConversationIndexSettings().root_dir,
        include_missing_metadata=include_missing_metadata,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def load_advisory_conversation_metadata(path: str | Path) -> dict[str, Any]:
    metadata_path = Path(path)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Advisory conversation metadata not found: {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def build_advisory_conversation_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_missing_metadata: bool | None = None,
    settings: Settings | AdvisoryConversationIndexSettings | dict[str, Any] | None = None,
) -> AdvisoryConversationIndexResult:
    project_settings, index_settings = _resolve_settings(settings)
    if index_settings.enable_live_trading or index_settings.enable_broker_api:
        raise ValueError("Advisory conversation index cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else index_settings.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else index_settings.output_dir
    effective_include_missing = (
        bool(include_missing_metadata)
        if include_missing_metadata is not None
        else index_settings.include_missing_metadata
    )
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=effective_include_missing)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_advisory_conversation_index_paths(effective_output_dir)
    audit_metadata = {
        "root_dir": effective_root,
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(index_frame),
        "config_version": index_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "llm_api_called": False,
        "external_api_called": False,
        "advisory_conversation_artifacts_only": True,
    }
    result = AdvisoryConversationIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=ADVISORY_CONVERSATION_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if index_settings.write_artifacts:
        write_advisory_conversation_index(result)
    _ = project_settings
    return result


def resolve_advisory_conversation_index_paths(output_dir: str | Path) -> AdvisoryConversationIndexPaths:
    artifact_dir = Path(output_dir)
    return AdvisoryConversationIndexPaths(
        artifact_dir=artifact_dir,
        advisory_conversation_index_csv=artifact_dir / "advisory_conversation_index.csv",
        advisory_conversation_index_report=artifact_dir / "advisory_conversation_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_advisory_conversation_index(result: AdvisoryConversationIndexResult) -> dict[str, Path]:
    paths = AdvisoryConversationIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.advisory_conversation_index_csv, index=False)
    metadata = build_advisory_conversation_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.advisory_conversation_index_report.write_text(
        render_advisory_conversation_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_advisory_conversation_index_metadata(
    result: AdvisoryConversationIndexResult,
    paths: AdvisoryConversationIndexPaths,
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
        "llm_api_called": False,
        "external_api_called": False,
        "advisory_conversation_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, LLM/API call, external API call, or message delivery was invoked.",
    }


def render_advisory_conversation_index_report(
    result: AdvisoryConversationIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"index_id": _generate_index_id(result.index_frame, result.audit_metadata)}
    lines = [
        "# Advisory Conversation Artifact Index",
        "",
        "No live trading, broker API, order placement, LLM/API call, external API call, or message delivery was invoked. This index scans local conversation artifacts only.",
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
        "## Conversation Index",
        "",
        _markdown_table(
            result.index_frame,
            [
                "conversation_run_id",
                "original_question",
                "parsed_symbol",
                "parsed_intent",
                "status",
                "advisory_action",
                "parser_type",
                "linked_answer_run_id",
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
        return rows, [f"Advisory conversation artifact root does not exist: {root}"]
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, metadata_path))
                warnings.append(f"Missing metadata included in index: {metadata_path}")
            continue
        try:
            metadata = load_advisory_conversation_metadata(metadata_path)
        except (OSError, json.JSONDecodeError) as exc:
            if include_missing_metadata:
                rows.append(_invalid_metadata_row(artifact_dir, metadata_path, exc))
                warnings.append(f"Unreadable metadata included in index: {metadata_path}: {exc}")
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files", {}) if isinstance(metadata.get("output_files"), dict) else {}
    return {
        "artifact_type": "ADVISORY_CONVERSATION",
        "conversation_run_id": _string_or_empty(metadata.get("conversation_run_id")) or artifact_dir.name,
        "original_question": _string_or_empty(metadata.get("original_question")),
        "parsed_symbol": _string_or_empty(metadata.get("parsed_symbol")),
        "parsed_intent": _string_or_empty(metadata.get("parsed_intent")),
        "status": _string_or_empty(metadata.get("status")),
        "advisory_action": _string_or_empty(metadata.get("advisory_action")),
        "parser_type": _string_or_empty(metadata.get("parser_type")),
        "linked_advisory_run_id": _string_or_empty(metadata.get("linked_advisory_run_id")),
        "linked_answer_run_id": _string_or_empty(metadata.get("linked_answer_run_id")),
        "linked_answer_markdown_path": _string_or_empty(metadata.get("linked_answer_markdown_path")),
        "llm_api_called": _to_bool(metadata.get("llm_api_called")),
        "external_api_called": _to_bool(metadata.get("external_api_called")),
        "no_message_sent": _to_bool(metadata.get("no_message_sent")),
        "no_live_trading": _to_bool(metadata.get("no_live_trading")),
        "no_broker_api": _to_bool(metadata.get("no_broker_api")),
        "auto_order_allowed": _to_bool(metadata.get("auto_order_allowed")),
        "report_path": _string_or_empty(output_files.get("advisory_conversation_report")),
        "conversation_json_path": _string_or_empty(output_files.get("advisory_conversation_json")),
        "metadata_path": str(metadata_path),
        "created_at": _string_or_empty(metadata.get("created_at")) or _mtime_iso(metadata_path),
    }


def _missing_metadata_row(artifact_dir: Path, metadata_path: Path) -> dict[str, Any]:
    return {
        "artifact_type": "ADVISORY_CONVERSATION",
        "conversation_run_id": artifact_dir.name,
        "status": "MISSING_METADATA",
        "metadata_path": str(metadata_path),
        "created_at": _mtime_iso(artifact_dir),
    }


def _invalid_metadata_row(artifact_dir: Path, metadata_path: Path, exc: Exception) -> dict[str, Any]:
    row = _missing_metadata_row(artifact_dir, metadata_path)
    row["status"] = "INVALID_METADATA"
    row["original_question"] = str(exc)
    return row


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    for column in ADVISORY_CONVERSATION_INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = False if column in _BOOL_COLUMNS else ""
    if frame.empty:
        return frame[ADVISORY_CONVERSATION_INDEX_COLUMNS]
    frame = frame[ADVISORY_CONVERSATION_INDEX_COLUMNS].copy()
    for column in _BOOL_COLUMNS:
        frame[column] = frame[column].map(_to_bool)
    frame = frame.sort_values(["created_at", "conversation_run_id"], ascending=[True, True]).reset_index(drop=True)
    return frame


_BOOL_COLUMNS = {
    "llm_api_called",
    "external_api_called",
    "no_message_sent",
    "no_live_trading",
    "no_broker_api",
    "auto_order_allowed",
}


def _resolve_settings(
    settings: Settings | AdvisoryConversationIndexSettings | dict[str, Any] | None,
) -> tuple[Settings, AdvisoryConversationIndexSettings]:
    if settings is None:
        project_settings = load_settings(Path("config/default.yaml"))
        return project_settings, project_settings.advisory_conversation_index
    if isinstance(settings, Settings):
        return settings, settings.advisory_conversation_index
    if isinstance(settings, AdvisoryConversationIndexSettings):
        project_settings = load_settings(Path("config/default.yaml"))
        return project_settings, settings
    project_settings = load_settings(Path("config/default.yaml"))
    return project_settings, AdvisoryConversationIndexSettings(**settings)


def _generate_index_id(frame: pd.DataFrame, audit_metadata: dict[str, Any]) -> str:
    payload = {
        "rows": frame.fillna("").to_dict("records") if not frame.empty else [],
        "root_dir": str(audit_metadata.get("root_dir", "")),
        "config_version": str(audit_metadata.get("config_version", "")),
    }
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if frame.empty or "created_at" not in frame.columns:
        return "1970-01-01T00:00:00+00:00"
    values = [str(value) for value in frame["created_at"].tolist() if str(value).strip()]
    return max(values) if values else "1970-01-01T00:00:00+00:00"


def _mtime_iso(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return ""


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    rows.extend(f"| {key} | {value} |" for key, value in values.items())
    return "\n".join(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str], *, max_rows: int = 50) -> str:
    if frame.empty:
        return "_No rows._"
    visible = frame.head(max_rows).copy()
    for column in columns:
        if column not in visible.columns:
            visible[column] = ""
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in visible[columns].iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    if len(frame) > max_rows:
        rows.append(f"\n_Only first {max_rows} rows shown._")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)
