"""Local-only workflow status for single-symbol advisory answer artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import Settings, SingleSymbolAdvisoryAnswerStatusSettings, load_settings
from quant_replay_system.single_symbol_advisory_answer_health import check_single_symbol_advisory_answer_health
from quant_replay_system.single_symbol_advisory_answer_index import scan_single_symbol_advisory_answer_artifacts


SINGLE_SYMBOL_ADVISORY_ANSWER_STATUS_LIMITATIONS = [
    "Scans local question-style answer metadata only.",
    "Does not regenerate answers, call LLM APIs, send messages, place orders, call brokers, or enable live trading.",
    "Stage inference is conservative when artifacts are missing or health checks fail.",
]

STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "symbol",
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
    "latest_answer_run_id",
    "latest_advisory_run_id",
    "latest_symbol",
    "latest_status",
    "latest_advisory_action",
    "latest_question",
    "answer_style",
    "health_status",
    "demo_mode",
    "not_strategy_recommendation",
    "answer_markdown_path",
    "next_manual_action",
]

NO_ARTIFACTS_STAGE = "NO_SINGLE_SYMBOL_ADVISORY_ANSWER_ARTIFACTS"
READY_STAGE = "SINGLE_SYMBOL_ADVISORY_ANSWER_READY_FOR_REVIEW"
NOT_FOUND_STAGE = "SINGLE_SYMBOL_ADVISORY_ANSWER_NOT_FOUND"
HEALTH_WARN_STAGE = "SINGLE_SYMBOL_ADVISORY_ANSWER_HEALTH_WARN"
FAILED_STAGE = "SINGLE_SYMBOL_ADVISORY_ANSWER_FAILED"
DEMO_VALIDATED_STAGE = "DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED"

DEMO_NEXT_ACTION = "Review local question-style answer; do not treat DEMO_ONLY output as a strategy recommendation."
NOT_FOUND_NEXT_ACTION = "Symbol was not found in the provided local artifact; no recommendation was invented."


@dataclass(frozen=True)
class SingleSymbolAdvisoryAnswerStatusPaths:
    artifact_dir: Path
    single_symbol_advisory_answer_status_report: Path
    single_symbol_advisory_answer_status_csv: Path
    single_symbol_advisory_answer_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "single_symbol_advisory_answer_status_report": self.single_symbol_advisory_answer_status_report,
            "single_symbol_advisory_answer_status_csv": self.single_symbol_advisory_answer_status_csv,
            "single_symbol_advisory_answer_status_summary": self.single_symbol_advisory_answer_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SingleSymbolAdvisoryAnswerStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_answer_run_id: str
    latest_advisory_run_id: str
    latest_symbol: str
    latest_advisory_action: str
    health_status: str
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_single_symbol_advisory_answer_status(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: Settings | SingleSymbolAdvisoryAnswerStatusSettings | dict[str, Any] | str | Path | None = None,
) -> SingleSymbolAdvisoryAnswerStatusResult:
    """Scan local question-style answer artifacts and write a status dashboard."""

    project_settings, status_settings = _resolve_settings(config)
    if status_settings.enable_live_trading or status_settings.enable_broker_api:
        raise ValueError("Single-symbol advisory answer status cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else status_settings.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else status_settings.output_dir
    index_frame = scan_single_symbol_advisory_answer_artifacts(effective_root)
    health_settings = project_settings.single_symbol_advisory_answer_health.model_copy(
        update={"root_dir": effective_root, "write_artifacts": False}
    )
    health_result = check_single_symbol_advisory_answer_health(index_df=index_frame, settings=health_settings)
    status_frame = build_single_symbol_advisory_answer_status_frame(index_frame, health_result=health_result)
    summary_frame = summarize_single_symbol_advisory_answer_status(index_frame, health_result=health_result)
    summary = summary_frame.iloc[0].to_dict()
    status_id = generate_single_symbol_advisory_answer_status_id(
        index_frame,
        health_status=health_result.status,
        config_version=status_settings.config_version,
    )
    paths = resolve_single_symbol_advisory_answer_status_paths(effective_output_dir, status_id)
    warnings = _status_warnings(index_frame, health_result, str(summary.get("workflow_stage", "")))
    audit_metadata = {
        "status_id": status_id,
        "root_dir": effective_root,
        "workflow_stage": summary.get("workflow_stage", ""),
        "status": summary.get("status", ""),
        "latest_answer_run_id": summary.get("latest_answer_run_id", ""),
        "latest_advisory_run_id": summary.get("latest_advisory_run_id", ""),
        "latest_symbol": summary.get("latest_symbol", ""),
        "health_status": health_result.status if len(index_frame) else "MISSING",
        "strict": status_settings.strict,
        "config_version": status_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "llm_api_called": False,
        "single_symbol_advisory_answer_artifacts_only": True,
    }
    result = SingleSymbolAdvisoryAnswerStatusResult(
        status_id=status_id,
        status=str(summary.get("status", "WARN")),
        workflow_stage=str(summary.get("workflow_stage", NO_ARTIFACTS_STAGE)),
        latest_answer_run_id=str(summary.get("latest_answer_run_id", "")),
        latest_advisory_run_id=str(summary.get("latest_advisory_run_id", "")),
        latest_symbol=str(summary.get("latest_symbol", "")),
        latest_advisory_action=str(summary.get("latest_advisory_action", "")),
        health_status=str(summary.get("health_status", "")),
        next_manual_action=str(summary.get("next_manual_action", "")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=SINGLE_SYMBOL_ADVISORY_ANSWER_STATUS_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if status_settings.write_artifacts:
        write_single_symbol_advisory_answer_status_artifacts(result)
    return result


def build_single_symbol_advisory_answer_status_frame(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    latest = _latest_answer_row(index_frame)
    if latest is None:
        rows.append(
            _status_row(
                component="SINGLE_SYMBOL_ADVISORY_ANSWER",
                status="MISSING",
                next_action="Run single-symbol-advisory --question-style for a symbol and local artifact.",
                notes="No question-style answer artifacts were found.",
            )
        )
    else:
        rows.append(
            _status_row(
                component="SINGLE_SYMBOL_ADVISORY_ANSWER",
                status=_string_or_empty(latest.get("status")) or "READY",
                latest_artifact_id=_string_or_empty(latest.get("answer_run_id")),
                symbol=_string_or_empty(latest.get("symbol")),
                report_path=_string_or_empty(latest.get("answer_markdown_path")),
                metadata_path=_string_or_empty(latest.get("metadata_path")),
                next_action="Review local question-style answer artifact.",
                notes="Latest local deterministic question-style answer artifact.",
            )
        )
    rows.append(
        _status_row(
            component="SINGLE_SYMBOL_ADVISORY_ANSWER_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("single_symbol_advisory_answer_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=health_result.issue_count,
            warning_count=health_result.warning_count,
            error_count=health_result.error_count,
            next_action=_health_next_action(health_result.status if len(index_frame) else "MISSING"),
            notes="Current in-memory health evaluation for question-style answer artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_single_symbol_advisory_answer_status(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    latest = _latest_answer_row(index_frame)
    if latest is None:
        return pd.DataFrame(
            [
                _summary_row(
                    workflow_stage=NO_ARTIFACTS_STAGE,
                    status="WARN",
                    health_status="MISSING",
                    next_manual_action="Run single-symbol-advisory --question-style for a symbol and local artifact.",
                )
            ]
        )

    health_status = str(health_result.status)
    latest_status = _string_or_empty(latest.get("status")) or "READY"
    action = _string_or_empty(latest.get("advisory_action")).upper()
    demo_mode = _to_bool(latest.get("demo_mode"))
    not_strategy = _to_bool(latest.get("not_strategy_recommendation"))

    if health_status == "FAIL":
        stage = FAILED_STAGE
        status = "FAIL"
        next_action = "Repair question-style answer artifacts before using this response."
    elif health_status == "WARN":
        stage = HEALTH_WARN_STAGE
        status = "WARN"
        next_action = "Review question-style answer health warnings before using this response."
    elif latest_status == "NOT_FOUND":
        stage = NOT_FOUND_STAGE
        status = "WARN"
        next_action = NOT_FOUND_NEXT_ACTION
    elif action == "DEMO_ONLY" or demo_mode or not_strategy:
        stage = DEMO_VALIDATED_STAGE
        status = "WARN"
        next_action = DEMO_NEXT_ACTION
    else:
        stage = READY_STAGE
        status = "PASS"
        next_action = "Review local question-style answer; manual confirmation remains required."

    return pd.DataFrame(
        [
            _summary_row(
                workflow_stage=stage,
                status=status,
                latest_answer_run_id=_string_or_empty(latest.get("answer_run_id")),
                latest_advisory_run_id=_string_or_empty(latest.get("advisory_run_id")),
                latest_symbol=_string_or_empty(latest.get("symbol")),
                latest_status=latest_status,
                latest_advisory_action=action,
                latest_question=_string_or_empty(latest.get("question")),
                answer_style=_string_or_empty(latest.get("answer_style")),
                health_status=health_status,
                demo_mode=demo_mode,
                not_strategy_recommendation=not_strategy,
                answer_markdown_path=_string_or_empty(latest.get("answer_markdown_path")),
                next_manual_action=next_action,
            )
        ]
    )


def resolve_single_symbol_advisory_answer_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> SingleSymbolAdvisoryAnswerStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return SingleSymbolAdvisoryAnswerStatusPaths(
        artifact_dir=artifact_dir,
        single_symbol_advisory_answer_status_report=artifact_dir / "single_symbol_advisory_answer_status_report.md",
        single_symbol_advisory_answer_status_csv=artifact_dir / "single_symbol_advisory_answer_status.csv",
        single_symbol_advisory_answer_status_summary=artifact_dir / "single_symbol_advisory_answer_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_single_symbol_advisory_answer_status_artifacts(
    result: SingleSymbolAdvisoryAnswerStatusResult,
) -> dict[str, Path]:
    paths = SingleSymbolAdvisoryAnswerStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.single_symbol_advisory_answer_status_csv, index=False)
    result.summary_frame.to_csv(paths.single_symbol_advisory_answer_status_summary, index=False)
    metadata = build_single_symbol_advisory_answer_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.single_symbol_advisory_answer_status_report.write_text(
        render_single_symbol_advisory_answer_status_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_single_symbol_advisory_answer_status_metadata(
    result: SingleSymbolAdvisoryAnswerStatusResult,
    paths: SingleSymbolAdvisoryAnswerStatusPaths,
) -> dict[str, Any]:
    return {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_answer_run_id": result.latest_answer_run_id,
        "latest_advisory_run_id": result.latest_advisory_run_id,
        "latest_symbol": result.latest_symbol,
        "latest_advisory_action": result.latest_advisory_action,
        "health_status": result.health_status,
        "next_manual_action": result.next_manual_action,
        "config_summary": {
            "root_dir": str(result.audit_metadata.get("root_dir", "")),
            "strict": bool(result.audit_metadata.get("strict", False)),
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


def render_single_symbol_advisory_answer_status_report(
    result: SingleSymbolAdvisoryAnswerStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    _ = metadata
    lines = [
        f"# Single-Symbol Advisory Answer Status: {result.status_id}",
        "",
        "No live trading, broker API, order placement, LLM API, or message delivery was invoked. This status dashboard summarizes local deterministic question-style answers only.",
        "",
        "## Summary",
        "",
        _markdown_table(result.summary_frame, SUMMARY_COLUMNS),
        "",
        "## Components",
        "",
        _markdown_table(result.status_frame, STATUS_COLUMNS),
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


def generate_single_symbol_advisory_answer_status_id(
    index_frame: pd.DataFrame,
    *,
    health_status: str,
    config_version: str,
) -> str:
    latest = _latest_answer_row(index_frame)
    payload = {
        "latest_answer_run_id": "" if latest is None else _string_or_empty(latest.get("answer_run_id")),
        "artifact_count": len(index_frame),
        "health_status": health_status,
        "config_version": config_version,
    }
    return _hash_payload(payload, length=12)


def _latest_answer_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy(deep=True)
    for column in ["created_at", "answer_run_id"]:
        if column not in frame.columns:
            frame[column] = ""
    frame["_created_sort"] = frame["created_at"].astype(str)
    return frame.sort_values(["_created_sort", "answer_run_id"], na_position="last").iloc[-1].to_dict()


def _health_next_action(status: str) -> str:
    if status == "FAIL":
        return "Repair question-style answer health errors."
    if status == "WARN":
        return "Review question-style answer health warnings."
    if status == "PASS":
        return "Review latest local question-style answer."
    return "Run single-symbol-advisory-answer-health."


def _status_warnings(index_frame: pd.DataFrame, health_result, workflow_stage: str) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No single-symbol advisory answer artifacts were found.")
    if workflow_stage == DEMO_VALIDATED_STAGE:
        warnings.append("Latest question-style answer is DEMO_ONLY; it is workflow validation only and not a strategy recommendation.")
    if workflow_stage == NOT_FOUND_STAGE:
        warnings.append("Latest question-style answer is NOT_FOUND; no recommendation was invented.")
    for warning in getattr(health_result, "warnings", []) or []:
        warnings.append(f"Health warning: {warning}")
    return warnings


def _status_row(**values: Any) -> dict[str, Any]:
    row = {column: "" for column in STATUS_COLUMNS}
    row.update(values)
    return row


def _summary_row(**values: Any) -> dict[str, Any]:
    row = {column: "" for column in SUMMARY_COLUMNS}
    row.update(values)
    return row


def _finalize_status_frame(frame: pd.DataFrame) -> pd.DataFrame:
    status = frame.copy(deep=True)
    for column in STATUS_COLUMNS:
        if column not in status.columns:
            status[column] = ""
    if status.empty:
        return status[STATUS_COLUMNS]
    return status[STATUS_COLUMNS].reset_index(drop=True)


def _resolve_settings(
    config: Settings | SingleSymbolAdvisoryAnswerStatusSettings | dict[str, Any] | str | Path | None,
) -> tuple[Settings, SingleSymbolAdvisoryAnswerStatusSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.single_symbol_advisory_answer_status
    if isinstance(config, Settings):
        return config, config.single_symbol_advisory_answer_status
    if isinstance(config, SingleSymbolAdvisoryAnswerStatusSettings):
        project = load_settings(Path("config/default.yaml"))
        return project.model_copy(update={"single_symbol_advisory_answer_status": config}), config
    if isinstance(config, dict):
        project = load_settings(Path("config/default.yaml"))
        payload = dict(project.single_symbol_advisory_answer_status.model_dump())
        payload.update(config)
        status_settings = SingleSymbolAdvisoryAnswerStatusSettings(**payload)
        return project.model_copy(update={"single_symbol_advisory_answer_status": status_settings}), status_settings
    project = load_settings(Path(config))
    return project, project.single_symbol_advisory_answer_status


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _string_or_empty(value).strip().lower() in {"true", "1", "yes", "y"}


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


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
