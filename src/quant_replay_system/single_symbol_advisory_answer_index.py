"""Local-only index for single-symbol advisory answer artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import Settings, SingleSymbolAdvisoryAnswerIndexSettings, load_settings


SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_LIMITATIONS = [
    "Scans local question-style single-symbol advisory answer folders only.",
    "Reads artifacts already written by single-symbol-advisory --question-style.",
    "Does not regenerate advisory answers, call LLM APIs, send messages, place orders, or call brokers.",
]

SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_COLUMNS = [
    "artifact_type",
    "answer_run_id",
    "advisory_run_id",
    "symbol",
    "status",
    "advisory_action",
    "question",
    "answer_style",
    "demo_mode",
    "not_strategy_recommendation",
    "requires_manual_confirmation",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "no_message_sent",
    "llm_api_called",
    "answer_markdown_path",
    "answer_json_path",
    "metadata_path",
    "created_at",
]


@dataclass(frozen=True)
class SingleSymbolAdvisoryAnswerIndexPaths:
    artifact_dir: Path
    single_symbol_advisory_answer_index_csv: Path
    single_symbol_advisory_answer_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "single_symbol_advisory_answer_index_csv": self.single_symbol_advisory_answer_index_csv,
            "single_symbol_advisory_answer_index_report": self.single_symbol_advisory_answer_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SingleSymbolAdvisoryAnswerIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_single_symbol_advisory_answer_artifacts(
    root: str | Path | None = None,
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _ = _scan_artifact_rows(
        Path(root) if root is not None else SingleSymbolAdvisoryAnswerIndexSettings().root_dir,
        include_missing_metadata=include_missing_metadata,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def load_single_symbol_advisory_answer_metadata(path: str | Path) -> dict[str, Any]:
    metadata_path = Path(path)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Single-symbol advisory answer metadata not found: {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def build_single_symbol_advisory_answer_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_missing_metadata: bool | None = None,
    settings: Settings | SingleSymbolAdvisoryAnswerIndexSettings | dict[str, Any] | None = None,
) -> SingleSymbolAdvisoryAnswerIndexResult:
    project_settings, index_settings = _resolve_settings(settings)
    if index_settings.enable_live_trading or index_settings.enable_broker_api:
        raise ValueError("Single-symbol advisory answer index cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else index_settings.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else index_settings.output_dir
    effective_include_missing = (
        bool(include_missing_metadata)
        if include_missing_metadata is not None
        else index_settings.include_missing_metadata
    )
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=effective_include_missing)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_single_symbol_advisory_answer_index_paths(effective_output_dir)
    audit_metadata = {
        "root_dir": effective_root,
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(index_frame),
        "config_version": index_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "llm_api_called": False,
        "single_symbol_advisory_answer_artifacts_only": True,
    }
    result = SingleSymbolAdvisoryAnswerIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if index_settings.write_artifacts:
        write_single_symbol_advisory_answer_index(result)
    _ = project_settings
    return result


def resolve_single_symbol_advisory_answer_index_paths(
    output_dir: str | Path,
) -> SingleSymbolAdvisoryAnswerIndexPaths:
    artifact_dir = Path(output_dir)
    return SingleSymbolAdvisoryAnswerIndexPaths(
        artifact_dir=artifact_dir,
        single_symbol_advisory_answer_index_csv=artifact_dir / "single_symbol_advisory_answer_index.csv",
        single_symbol_advisory_answer_index_report=artifact_dir / "single_symbol_advisory_answer_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_single_symbol_advisory_answer_index(result: SingleSymbolAdvisoryAnswerIndexResult) -> dict[str, Path]:
    paths = SingleSymbolAdvisoryAnswerIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.single_symbol_advisory_answer_index_csv, index=False)
    metadata = build_single_symbol_advisory_answer_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.single_symbol_advisory_answer_index_report.write_text(
        render_single_symbol_advisory_answer_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_single_symbol_advisory_answer_index_metadata(
    result: SingleSymbolAdvisoryAnswerIndexResult,
    paths: SingleSymbolAdvisoryAnswerIndexPaths,
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
        "single_symbol_advisory_answer_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, LLM API, or message delivery was invoked.",
    }


def render_single_symbol_advisory_answer_index_report(
    result: SingleSymbolAdvisoryAnswerIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"index_id": _generate_index_id(result.index_frame, result.audit_metadata)}
    lines = [
        "# Single-Symbol Advisory Answer Artifact Index",
        "",
        "No live trading, broker API, order placement, LLM API, or message delivery was invoked. This index scans local answer artifacts only.",
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
        "## Answer Index",
        "",
        _markdown_table(
            result.index_frame,
            [
                "answer_run_id",
                "advisory_run_id",
                "symbol",
                "status",
                "advisory_action",
                "question",
                "answer_style",
                "llm_api_called",
                "answer_markdown_path",
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
        return rows, [f"Single-symbol advisory answer artifact root does not exist: {root}"]
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
            metadata = load_single_symbol_advisory_answer_metadata(metadata_path)
        except (OSError, json.JSONDecodeError) as exc:
            if include_missing_metadata:
                rows.append(_invalid_metadata_row(artifact_dir, metadata_path, exc))
                warnings.append(f"Unreadable metadata included in index: {metadata_path}: {exc}")
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    return _base_row(
        artifact_type="SINGLE_SYMBOL_ADVISORY_ANSWER",
        answer_run_id=_string_or_empty(metadata.get("answer_run_id")) or artifact_dir.name,
        advisory_run_id=_string_or_empty(metadata.get("advisory_run_id")),
        symbol=_string_or_empty(metadata.get("symbol")),
        status=_string_or_empty(metadata.get("status")) or "READY",
        advisory_action=_string_or_empty(metadata.get("advisory_action")),
        question=_string_or_empty(metadata.get("question")),
        answer_style=_string_or_empty(metadata.get("answer_style")),
        demo_mode=_bool_or_blank(metadata.get("demo_mode")),
        not_strategy_recommendation=_bool_or_blank(metadata.get("not_strategy_recommendation")),
        requires_manual_confirmation=_bool_or_blank(metadata.get("requires_manual_confirmation")),
        auto_order_allowed=_bool_or_blank(metadata.get("auto_order_allowed")),
        no_live_trading=_bool_or_blank(metadata.get("no_live_trading")),
        no_broker_api=_bool_or_blank(metadata.get("no_broker_api")),
        no_message_sent=_bool_or_blank(metadata.get("no_message_sent")),
        llm_api_called=_bool_or_blank(metadata.get("llm_api_called")),
        answer_markdown_path=_metadata_path(
            output_files,
            "single_symbol_advisory_answer",
            artifact_dir / "single_symbol_advisory_answer.md",
        ),
        answer_json_path=_metadata_path(
            output_files,
            "single_symbol_advisory_answer_json",
            artifact_dir / "single_symbol_advisory_answer.json",
        ),
        metadata_path=str(metadata_path),
        created_at=_string_or_empty(metadata.get("created_at")),
    )


def _missing_metadata_row(artifact_dir: Path, metadata_path: Path) -> dict[str, Any]:
    return _base_row(
        artifact_type="SINGLE_SYMBOL_ADVISORY_ANSWER",
        answer_run_id=artifact_dir.name,
        status="MISSING_METADATA",
        answer_markdown_path=str(artifact_dir / "single_symbol_advisory_answer.md"),
        answer_json_path=str(artifact_dir / "single_symbol_advisory_answer.json"),
        metadata_path=str(metadata_path),
    )


def _invalid_metadata_row(artifact_dir: Path, metadata_path: Path, exc: Exception) -> dict[str, Any]:
    row = _missing_metadata_row(artifact_dir, metadata_path)
    row["status"] = f"INVALID_METADATA:{exc.__class__.__name__}"
    return row


def _base_row(**values: Any) -> dict[str, Any]:
    row = {column: "" for column in SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_COLUMNS}
    row.update(values)
    return row


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    index = frame.copy(deep=True)
    for column in SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_COLUMNS:
        if column not in index.columns:
            index[column] = ""
    if index.empty:
        return index[SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_COLUMNS]
    return index[SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_COLUMNS].sort_values(
        ["created_at", "answer_run_id", "metadata_path"],
        na_position="last",
    ).reset_index(drop=True)


def _metadata_path(output_files: dict[str, Any], key: str, default: Path) -> str:
    value = output_files.get(key)
    return str(value) if _present(value) else str(default)


def _bool_or_blank(value: Any) -> bool | str:
    if not _present(value):
        return ""
    return _to_bool(value)


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def _present(value: Any) -> bool:
    return _string_or_empty(value).strip() != ""


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _string_or_empty(value).strip().lower() in {"true", "1", "yes", "y"}


def _generate_index_id(frame: pd.DataFrame, audit_metadata: dict[str, Any]) -> str:
    payload = {
        "root_dir": str(audit_metadata.get("root_dir", "")),
        "answer_run_ids": sorted(str(value) for value in frame.get("answer_run_id", pd.Series(dtype="object")).dropna()),
        "artifact_count": len(frame),
        "config_version": audit_metadata.get("config_version", ""),
    }
    return _hash_payload(payload, length=12)


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if frame.empty or "created_at" not in frame.columns:
        return "1970-01-01T00:00:00+00:00"
    values = [value for value in frame["created_at"].astype(str).tolist() if value.strip()]
    return max(values) if values else "1970-01-01T00:00:00+00:00"


def _resolve_settings(
    settings: Settings | SingleSymbolAdvisoryAnswerIndexSettings | dict[str, Any] | None,
) -> tuple[Settings, SingleSymbolAdvisoryAnswerIndexSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.single_symbol_advisory_answer_index
    if isinstance(settings, Settings):
        return settings, settings.single_symbol_advisory_answer_index
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, SingleSymbolAdvisoryAnswerIndexSettings):
        return project.model_copy(update={"single_symbol_advisory_answer_index": settings}), settings
    if isinstance(settings, dict):
        payload = dict(project.single_symbol_advisory_answer_index.model_dump())
        payload.update(settings)
        index_settings = SingleSymbolAdvisoryAnswerIndexSettings(**payload)
        return project.model_copy(update={"single_symbol_advisory_answer_index": index_settings}), index_settings
    raise TypeError("settings must be Settings, SingleSymbolAdvisoryAnswerIndexSettings, dict, or None")


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
