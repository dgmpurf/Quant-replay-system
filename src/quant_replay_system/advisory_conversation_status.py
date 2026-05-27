"""Local-only workflow status for advisory conversation artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.advisory_conversation_health import check_advisory_conversation_health
from quant_replay_system.advisory_conversation_index import scan_advisory_conversation_artifacts
from quant_replay_system.config import AdvisoryConversationStatusSettings, Settings, load_settings
from quant_replay_system.signal_semantics import (
    SIGNAL_SEMANTICS_PROVENANCE_FIELDS,
    signal_semantics_provenance_present,
)


ADVISORY_CONVERSATION_STATUS_LIMITATIONS = [
    "Scans local advisory conversation metadata only.",
    "Does not parse new questions, regenerate answers, call LLM/external APIs, send messages, place orders, call brokers, or enable live trading.",
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
    "latest_conversation_run_id",
    "latest_original_question",
    "latest_parsed_symbol",
    "latest_parsed_intent",
    "latest_advisory_action",
    "parser_type",
    "health_status",
    "llm_api_called",
    "no_message_sent",
    "no_live_trading",
    "no_broker_api",
    "auto_order_allowed",
    *SIGNAL_SEMANTICS_PROVENANCE_FIELDS,
    "semantics_provenance_present",
    "semantics_missing_provenance_legacy_warning_only",
    "linked_answer_markdown_path",
    "next_manual_action",
]

NO_ARTIFACTS_STAGE = "NO_ADVISORY_CONVERSATION_ARTIFACTS"
READY_STAGE = "ADVISORY_CONVERSATION_READY_FOR_REVIEW"
PARSE_FAILED_STAGE = "ADVISORY_CONVERSATION_PARSE_FAILED"
NOT_FOUND_STAGE = "ADVISORY_CONVERSATION_NOT_FOUND"
HEALTH_WARN_STAGE = "ADVISORY_CONVERSATION_HEALTH_WARN"
FAILED_STAGE = "ADVISORY_CONVERSATION_FAILED"
DEMO_VALIDATED_STAGE = "DEMO_ADVISORY_CONVERSATION_VALIDATED"

DEMO_NEXT_ACTION = "Review local conversational advisory answer; do not treat DEMO_ONLY output as a strategy recommendation."
NOT_FOUND_NEXT_ACTION = "Parsed symbol was not found in the provided local artifact; no recommendation was invented."
PARSE_FAILED_NEXT_ACTION = "Provide a six-digit local symbol in the question; no symbol or recommendation was invented."


@dataclass(frozen=True)
class AdvisoryConversationStatusPaths:
    artifact_dir: Path
    advisory_conversation_status_report: Path
    advisory_conversation_status_csv: Path
    advisory_conversation_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "advisory_conversation_status_report": self.advisory_conversation_status_report,
            "advisory_conversation_status_csv": self.advisory_conversation_status_csv,
            "advisory_conversation_status_summary": self.advisory_conversation_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AdvisoryConversationStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_conversation_run_id: str
    latest_original_question: str
    latest_parsed_symbol: str
    latest_parsed_intent: str
    latest_advisory_action: str
    health_status: str
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_advisory_conversation_status(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: Settings | AdvisoryConversationStatusSettings | dict[str, Any] | str | Path | None = None,
) -> AdvisoryConversationStatusResult:
    project_settings, status_settings = _resolve_settings(config)
    if status_settings.enable_live_trading or status_settings.enable_broker_api:
        raise ValueError("Advisory conversation status cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else status_settings.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else status_settings.output_dir
    index_frame = scan_advisory_conversation_artifacts(effective_root)
    health_settings = project_settings.advisory_conversation_health.model_copy(
        update={"root_dir": effective_root, "write_artifacts": False}
    )
    health_result = check_advisory_conversation_health(index_df=index_frame, settings=health_settings)
    status_frame = build_advisory_conversation_status_frame(index_frame, health_result=health_result)
    summary_frame = summarize_advisory_conversation_status(index_frame, health_result=health_result)
    summary = summary_frame.iloc[0].to_dict()
    status_id = generate_advisory_conversation_status_id(
        index_frame,
        health_status=health_result.status,
        config_version=status_settings.config_version,
    )
    paths = resolve_advisory_conversation_status_paths(effective_output_dir, status_id)
    warnings = _status_warnings(index_frame, health_result, str(summary.get("workflow_stage", "")))
    audit_metadata = {
        "status_id": status_id,
        "root_dir": effective_root,
        "workflow_stage": summary.get("workflow_stage", ""),
        "status": summary.get("status", ""),
        "latest_conversation_run_id": summary.get("latest_conversation_run_id", ""),
        "latest_parsed_symbol": summary.get("latest_parsed_symbol", ""),
        "health_status": health_result.status if len(index_frame) else "MISSING",
        "strict": status_settings.strict,
        "config_version": status_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "llm_api_called": False,
        "external_api_called": False,
        "advisory_conversation_artifacts_only": True,
    }
    result = AdvisoryConversationStatusResult(
        status_id=status_id,
        status=str(summary.get("status", "WARN")),
        workflow_stage=str(summary.get("workflow_stage", NO_ARTIFACTS_STAGE)),
        latest_conversation_run_id=str(summary.get("latest_conversation_run_id", "")),
        latest_original_question=str(summary.get("latest_original_question", "")),
        latest_parsed_symbol=str(summary.get("latest_parsed_symbol", "")),
        latest_parsed_intent=str(summary.get("latest_parsed_intent", "")),
        latest_advisory_action=str(summary.get("latest_advisory_action", "")),
        health_status=str(summary.get("health_status", "")),
        next_manual_action=str(summary.get("next_manual_action", "")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=ADVISORY_CONVERSATION_STATUS_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if status_settings.write_artifacts:
        write_advisory_conversation_status_artifacts(result)
    return result


def build_advisory_conversation_status_frame(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    latest = _latest_conversation_row(index_frame)
    if latest is None:
        rows.append(
            _status_row(
                component="ADVISORY_CONVERSATION",
                status="MISSING",
                next_action="Run advisory-conversation with a local candidates/scored/signals artifact.",
                notes="No advisory conversation artifacts were found.",
            )
        )
    else:
        rows.append(
            _status_row(
                component="ADVISORY_CONVERSATION",
                status=_string_or_empty(latest.get("status")) or "READY",
                latest_artifact_id=_string_or_empty(latest.get("conversation_run_id")),
                symbol=_string_or_empty(latest.get("parsed_symbol")),
                report_path=_string_or_empty(latest.get("report_path")),
                metadata_path=_string_or_empty(latest.get("metadata_path")),
                next_action="Review local conversational advisory artifact.",
                notes=f"intent={_string_or_empty(latest.get('parsed_intent'))}; parser={_string_or_empty(latest.get('parser_type'))}",
            )
        )
    rows.append(
        _status_row(
            component="ADVISORY_CONVERSATION_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("advisory_conversation_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=health_result.issue_count,
            warning_count=health_result.warning_count,
            error_count=health_result.error_count,
            next_action=_health_next_action(health_result.status if len(index_frame) else "MISSING"),
            notes="Current in-memory health evaluation for advisory conversation artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_advisory_conversation_status(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    latest = _latest_conversation_row(index_frame)
    if latest is None:
        return pd.DataFrame(
            [
                _summary_row(
                    workflow_stage=NO_ARTIFACTS_STAGE,
                    status="WARN",
                    health_status="MISSING",
                    next_manual_action="Run advisory-conversation with a local candidates/scored/signals artifact.",
                )
            ]
        )

    health_status = str(health_result.status)
    latest_status = _string_or_empty(latest.get("status")).upper() or "READY"
    action = _string_or_empty(latest.get("advisory_action")).upper()
    if health_status == "FAIL":
        stage = FAILED_STAGE
        status = "FAIL"
        next_action = "Repair advisory conversation artifacts before using local conversational answers."
    elif health_status == "WARN":
        stage = HEALTH_WARN_STAGE
        status = "WARN"
        next_action = "Review advisory conversation health warnings before using local conversational answers."
    elif latest_status == "PARSE_FAILED":
        stage = PARSE_FAILED_STAGE
        status = "WARN"
        next_action = PARSE_FAILED_NEXT_ACTION
    elif latest_status == "NOT_FOUND":
        stage = NOT_FOUND_STAGE
        status = "WARN"
        next_action = NOT_FOUND_NEXT_ACTION
    elif action == "DEMO_ONLY":
        stage = DEMO_VALIDATED_STAGE
        status = "WARN"
        next_action = DEMO_NEXT_ACTION
    else:
        stage = READY_STAGE
        status = "PASS"
        next_action = "Review local conversational advisory answer; manual confirmation remains required."

    return pd.DataFrame(
        [
            _summary_row(
                workflow_stage=stage,
                status=status,
                latest_conversation_run_id=_string_or_empty(latest.get("conversation_run_id")),
                latest_original_question=_string_or_empty(latest.get("original_question")),
                latest_parsed_symbol=_string_or_empty(latest.get("parsed_symbol")),
                latest_parsed_intent=_string_or_empty(latest.get("parsed_intent")),
                latest_advisory_action=action,
                parser_type=_string_or_empty(latest.get("parser_type")),
                health_status=health_status,
                llm_api_called=_to_bool(latest.get("llm_api_called")),
                no_message_sent=_to_bool(latest.get("no_message_sent")),
                no_live_trading=_to_bool(latest.get("no_live_trading")),
                no_broker_api=_to_bool(latest.get("no_broker_api")),
                auto_order_allowed=_to_bool(latest.get("auto_order_allowed")),
                **_provenance_summary(latest),
                linked_answer_markdown_path=_string_or_empty(latest.get("linked_answer_markdown_path")),
                next_manual_action=next_action,
            )
        ]
    )


def resolve_advisory_conversation_status_paths(output_dir: str | Path, status_id: str) -> AdvisoryConversationStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return AdvisoryConversationStatusPaths(
        artifact_dir=artifact_dir,
        advisory_conversation_status_report=artifact_dir / "advisory_conversation_status_report.md",
        advisory_conversation_status_csv=artifact_dir / "advisory_conversation_status.csv",
        advisory_conversation_status_summary=artifact_dir / "advisory_conversation_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_advisory_conversation_status_artifacts(result: AdvisoryConversationStatusResult) -> dict[str, Path]:
    paths = AdvisoryConversationStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.advisory_conversation_status_csv, index=False)
    result.summary_frame.to_csv(paths.advisory_conversation_status_summary, index=False)
    metadata = build_advisory_conversation_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.advisory_conversation_status_report.write_text(
        render_advisory_conversation_status_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_advisory_conversation_status_metadata(
    result: AdvisoryConversationStatusResult,
    paths: AdvisoryConversationStatusPaths,
) -> dict[str, Any]:
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    return {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_conversation_run_id": result.latest_conversation_run_id,
        "latest_original_question": result.latest_original_question,
        "latest_parsed_symbol": result.latest_parsed_symbol,
        "latest_parsed_intent": result.latest_parsed_intent,
        "latest_advisory_action": result.latest_advisory_action,
        "health_status": result.health_status,
        "next_manual_action": result.next_manual_action,
        **_metadata_provenance(summary),
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


def render_advisory_conversation_status_report(
    result: AdvisoryConversationStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    _ = metadata
    lines = [
        f"# Advisory Conversation Status: {result.status_id}",
        "",
        "No live trading, broker API, order placement, LLM/API call, external API call, or message delivery was invoked.",
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


def generate_advisory_conversation_status_id(
    index_frame: pd.DataFrame,
    *,
    health_status: str,
    config_version: str,
) -> str:
    payload = {
        "rows": index_frame.fillna("").to_dict("records") if not index_frame.empty else [],
        "health_status": health_status,
        "config_version": config_version,
    }
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _latest_conversation_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    if "created_at" not in frame.columns:
        frame["created_at"] = ""
    frame = frame.sort_values(["created_at", "conversation_run_id"], ascending=[True, True]).reset_index(drop=True)
    return frame.iloc[-1].to_dict()


def _status_warnings(index_frame: pd.DataFrame, health_result, stage: str) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No advisory conversation artifacts were found.")
    if health_result.status == "WARN":
        warnings.append("Advisory conversation health has warnings.")
    if health_result.status == "FAIL":
        warnings.append("Advisory conversation health failed.")
    if stage == DEMO_VALIDATED_STAGE:
        warnings.append("Latest advisory conversation is DEMO_ONLY; it is workflow validation only and not a strategy recommendation.")
    if stage == PARSE_FAILED_STAGE:
        warnings.append("Latest advisory conversation could not parse a symbol; no recommendation was invented.")
    if stage == NOT_FOUND_STAGE:
        warnings.append("Latest advisory conversation parsed a missing symbol; no recommendation was invented.")
    return warnings


def _status_row(
    *,
    component: str,
    status: str,
    latest_artifact_id: str = "",
    symbol: str = "",
    report_path: str = "",
    metadata_path: str = "",
    issue_count: int = 0,
    warning_count: int = 0,
    error_count: int = 0,
    next_action: str = "",
    notes: str = "",
) -> dict[str, Any]:
    return {
        "component": component,
        "status": status,
        "latest_artifact_id": latest_artifact_id,
        "symbol": symbol,
        "report_path": report_path,
        "metadata_path": metadata_path,
        "issue_count": issue_count,
        "warning_count": warning_count,
        "error_count": error_count,
        "next_action": next_action,
        "notes": notes,
    }


def _summary_row(**overrides: Any) -> dict[str, Any]:
    row = {column: "" for column in SUMMARY_COLUMNS}
    row.update(overrides)
    return row


def _provenance_summary(row: dict[str, Any]) -> dict[str, Any]:
    present = _to_bool(row.get("semantics_provenance_present")) or signal_semantics_provenance_present(row)
    legacy_warning_only = _to_bool(row.get("semantics_missing_provenance_legacy_warning_only")) if not present else False
    return {
        **{field: _string_or_empty(row.get(field)) for field in SIGNAL_SEMANTICS_PROVENANCE_FIELDS},
        "semantics_provenance_present": present,
        "semantics_missing_provenance_legacy_warning_only": legacy_warning_only,
    }


def _metadata_provenance(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        **{field: summary.get(field, "") for field in SIGNAL_SEMANTICS_PROVENANCE_FIELDS},
        "semantics_provenance_present": summary.get("semantics_provenance_present", ""),
        "semantics_missing_provenance_legacy_warning_only": summary.get(
            "semantics_missing_provenance_legacy_warning_only",
            "",
        ),
    }


def _health_next_action(status: str) -> str:
    if status == "PASS":
        return "Review local advisory conversation answer manually."
    if status == "WARN":
        return "Review advisory conversation health warnings."
    if status == "FAIL":
        return "Repair advisory conversation artifacts before using local conversation output."
    return "Run advisory-conversation-health after conversation artifacts exist."


def _finalize_status_frame(frame: pd.DataFrame) -> pd.DataFrame:
    for column in STATUS_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[STATUS_COLUMNS].copy()


def _resolve_settings(
    config: Settings | AdvisoryConversationStatusSettings | dict[str, Any] | str | Path | None,
) -> tuple[Settings, AdvisoryConversationStatusSettings]:
    if config is None:
        project_settings = load_settings(Path("config/default.yaml"))
        return project_settings, project_settings.advisory_conversation_status
    if isinstance(config, Settings):
        return config, config.advisory_conversation_status
    if isinstance(config, AdvisoryConversationStatusSettings):
        project_settings = load_settings(Path("config/default.yaml"))
        return project_settings, config
    if isinstance(config, dict):
        project_settings = load_settings(Path("config/default.yaml"))
        return project_settings, AdvisoryConversationStatusSettings(**config)
    project_settings = load_settings(config)
    return project_settings, project_settings.advisory_conversation_status


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "_No rows._"
    visible = frame.copy()
    for column in columns:
        if column not in visible.columns:
            visible[column] = ""
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in visible[columns].iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


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
