"""Local-only health checks for advisory conversation artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.advisory_conversation_index import (
    ADVISORY_CONVERSATION_INDEX_COLUMNS,
    scan_advisory_conversation_artifacts,
)
from quant_replay_system.config import AdvisoryConversationHealthSettings, Settings, load_settings


ADVISORY_CONVERSATION_HEALTH_LIMITATIONS = [
    "Checks local advisory-conversation artifacts referenced by the conversation index only.",
    "Does not parse new questions, regenerate answers, call LLM/external APIs, send messages, place orders, or call brokers.",
    "Does not validate strategy quality or approve demo outputs as recommendations.",
]

HEALTH_COLUMNS = [
    "artifact_type",
    "conversation_run_id",
    "parsed_symbol",
    "parsed_intent",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

ISSUE_CODES = {
    "MISSING_METADATA",
    "MISSING_CONVERSATION_JSON",
    "MISSING_REPORT",
    "MISSING_REQUIRED_FIELDS",
    "SYMBOL_FORMAT_ERROR",
    "LLM_API_CALLED",
    "MESSAGE_DELIVERY_DETECTED",
    "AUTO_ORDER_ALLOWED",
    "MISSING_NO_LIVE_TRADING_STATEMENT",
    "PARSE_FAILED_WITH_RECOMMENDATION",
    "NOT_FOUND_WITH_RECOMMENDATION",
    "DEMO_CONVERSATION_ACTION_UNSAFE",
    "MISSING_LINKED_ANSWER",
    "STALE_OR_PARTIAL_CONVERSATION",
}

REQUIRED_PATH_FIELDS = ["metadata_path", "conversation_json_path", "report_path"]

REQUIRED_CONVERSATION_FIELDS = [
    "conversation_run_id",
    "status",
    "original_question",
    "parsed_symbol",
    "parsed_intent",
    "parser_type",
    "advisory_action",
    "answer_summary",
    "requires_manual_confirmation",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "no_message_sent",
    "llm_api_called",
    "external_api_called",
]

DEMO_SAFE_ACTIONS = {"DEMO_ONLY", "WATCH", "BLOCKED", "NO_ACTION"}
NO_RECOMMENDATION_ACTIONS = {"NO_ACTION", ""}
UNSAFE_RECOMMENDATION_ACTIONS = {"REVIEW_BUY_CANDIDATE", "REVIEW_SELL_CANDIDATE", "BUY", "SELL"}
UNSAFE_PHRASES = [
    "buy now",
    "sell now",
    "you should buy",
    "you should sell",
    "must buy",
    "must sell",
    "execute buy",
    "execute sell",
    "place a buy order",
    "place a sell order",
]


@dataclass(frozen=True)
class AdvisoryConversationHealthPaths:
    artifact_dir: Path
    advisory_conversation_health_report: Path
    advisory_conversation_health_issues: Path
    advisory_conversation_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "advisory_conversation_health_report": self.advisory_conversation_health_report,
            "advisory_conversation_health_issues": self.advisory_conversation_health_issues,
            "advisory_conversation_health_summary": self.advisory_conversation_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AdvisoryConversationHealthResult:
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


def check_advisory_conversation_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | AdvisoryConversationHealthSettings | dict[str, Any] | None = None,
) -> AdvisoryConversationHealthResult:
    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Advisory conversation health cannot enable live trading or broker API access")

    index_frame, index_source, base_dir, load_warnings, load_issues = _load_index_for_health(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
    )
    checked_count = len(index_frame)
    health_frame = build_advisory_conversation_health_frame(index_frame, base_dir=base_dir)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_advisory_conversation_health(health_frame, checked_artifact_count=checked_count)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_advisory_conversation_health_check_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_advisory_conversation_health_paths(
        Path(output_dir) if output_dir is not None else health_settings.output_dir,
        health_check_id,
    )
    audit_metadata = {
        "health_check_id": health_check_id,
        "index_source": index_source,
        "checked_artifact_count": checked_count,
        "strict": health_settings.strict,
        "config_version": health_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "llm_api_called": False,
        "external_api_called": False,
        "advisory_conversation_artifacts_only": True,
    }
    result = AdvisoryConversationHealthResult(
        status=status,
        checked_artifact_count=checked_count,
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=ADVISORY_CONVERSATION_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_advisory_conversation_health_artifacts(result)
    _ = project_settings
    return result


def build_advisory_conversation_health_frame(
    index_df: pd.DataFrame,
    *,
    base_dir: str | Path | None = None,
) -> pd.DataFrame:
    index_frame = _prepare_index_frame(index_df)
    base_path = Path(base_dir) if base_dir is not None else None
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        if _string_or_empty(row.get("artifact_type")).upper() != "ADVISORY_CONVERSATION":
            continue
        resolved_paths = {field: _resolve_artifact_path(row.get(field), base_path) for field in REQUIRED_PATH_FIELDS}
        metadata = _check_metadata(row, resolved_paths["metadata_path"], issues)
        conversation_json = _check_conversation_json(row, resolved_paths["conversation_json_path"], issues)
        report_text = _check_report(row, resolved_paths["report_path"], issues)
        if metadata is not None and conversation_json is not None:
            _check_conversation_contract(row, metadata, conversation_json, report_text, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_advisory_conversation_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    frame = _finalize_health_frame(health_frame)
    issue_count = len(frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    info_count = int((frame["severity"] == "INFO").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    rows = [
        {
            "status": status,
            "checked_artifact_count": checked_artifact_count,
            "issue_count": issue_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
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
                    "info_count": int((group["severity"] == "INFO").sum()),
                    "issue_code": issue_code,
                }
            )
    return pd.DataFrame(rows)


def resolve_advisory_conversation_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> AdvisoryConversationHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return AdvisoryConversationHealthPaths(
        artifact_dir=artifact_dir,
        advisory_conversation_health_report=artifact_dir / "advisory_conversation_health_report.md",
        advisory_conversation_health_issues=artifact_dir / "advisory_conversation_health_issues.csv",
        advisory_conversation_health_summary=artifact_dir / "advisory_conversation_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_advisory_conversation_health_artifacts(result: AdvisoryConversationHealthResult) -> dict[str, Path]:
    paths = AdvisoryConversationHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.advisory_conversation_health_issues, index=False)
    result.summary_frame.to_csv(paths.advisory_conversation_health_summary, index=False)
    metadata = build_advisory_conversation_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.advisory_conversation_health_report.write_text(
        render_advisory_conversation_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_advisory_conversation_health_metadata(
    result: AdvisoryConversationHealthResult,
    paths: AdvisoryConversationHealthPaths,
) -> dict[str, Any]:
    return {
        "health_check_id": result.health_check_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "config_summary": {
            "index_source": result.audit_metadata.get("index_source", ""),
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
        "external_api_called": False,
        "advisory_conversation_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, LLM/API call, external API call, or message delivery was invoked.",
    }


def render_advisory_conversation_health_report(
    result: AdvisoryConversationHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    _ = metadata
    lines = [
        f"# Advisory Conversation Health Check: {result.health_check_id}",
        "",
        "No live trading, broker API, order placement, LLM/API call, external API call, or message delivery was invoked. This health check validates local conversation artifacts only.",
        "",
        "## Health Summary",
        "",
        _markdown_table(
            result.summary_frame,
            ["status", "checked_artifact_count", "issue_count", "error_count", "warning_count", "info_count", "issue_code"],
        ),
        "",
        "## Issues",
        "",
        _markdown_table(
            result.health_frame,
            [
                "artifact_type",
                "conversation_run_id",
                "parsed_symbol",
                "parsed_intent",
                "path_field",
                "severity",
                "issue_code",
                "issue_message",
                "suggested_action",
            ],
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


def generate_advisory_conversation_health_check_id(
    index_frame: pd.DataFrame,
    *,
    index_source: str,
    settings: AdvisoryConversationHealthSettings,
) -> str:
    payload = {
        "index_source": index_source,
        "rows": index_frame.fillna("").to_dict("records") if not index_frame.empty else [],
        "strict": settings.strict,
        "config_version": settings.config_version,
    }
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _load_index_for_health(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path | None,
    settings: AdvisoryConversationHealthSettings,
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    load_issues: list[dict[str, Any]] = []
    if index_df is not None:
        return _prepare_index_frame(index_df), "provided_dataframe", None, warnings, load_issues
    if index_path:
        path = Path(index_path)
        if not path.exists():
            load_issues.append(_load_issue("MISSING_METADATA", "index", str(path), f"Index CSV not found: {path}"))
            return _prepare_index_frame(pd.DataFrame()), str(path), path.parent, warnings, load_issues
        frame = pd.read_csv(path, dtype=str)
        return _prepare_index_frame(frame), str(path), path.parent, warnings, load_issues
    effective_root = Path(root) if root is not None else settings.root_dir
    frame = scan_advisory_conversation_artifacts(effective_root)
    return _prepare_index_frame(frame), str(effective_root), None, warnings, load_issues


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    for column in ADVISORY_CONVERSATION_INDEX_COLUMNS:
        if column not in prepared.columns:
            prepared[column] = False if column in _BOOL_COLUMNS else ""
    return prepared[ADVISORY_CONVERSATION_INDEX_COLUMNS]


def _check_metadata(row: dict[str, Any], path: Path | None, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if path is None or not path.exists():
        _add_issue(row, issues, "metadata_path", path, "ERROR", "MISSING_METADATA", "metadata.json is missing.")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _add_issue(row, issues, "metadata_path", path, "ERROR", "MISSING_METADATA", f"metadata.json is unreadable: {exc}")
        return None


def _check_conversation_json(row: dict[str, Any], path: Path | None, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if path is None or not path.exists():
        _add_issue(row, issues, "conversation_json_path", path, "ERROR", "MISSING_CONVERSATION_JSON", "Conversation JSON is missing.")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _add_issue(row, issues, "conversation_json_path", path, "ERROR", "MISSING_CONVERSATION_JSON", f"Conversation JSON is unreadable: {exc}")
        return None


def _check_report(row: dict[str, Any], path: Path | None, issues: list[dict[str, Any]]) -> str:
    if path is None or not path.exists():
        _add_issue(row, issues, "report_path", path, "ERROR", "MISSING_REPORT", "Conversation report is missing.")
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        _add_issue(row, issues, "report_path", path, "ERROR", "MISSING_REPORT", f"Conversation report is unreadable: {exc}")
        return ""


def _check_conversation_contract(
    row: dict[str, Any],
    metadata: dict[str, Any],
    conversation_json: dict[str, Any],
    report_text: str,
    issues: list[dict[str, Any]],
) -> None:
    merged = {**conversation_json, **metadata}
    missing = [field for field in REQUIRED_CONVERSATION_FIELDS if field not in merged]
    if missing:
        _add_issue(
            row,
            issues,
            "metadata_path",
            row.get("metadata_path"),
            "ERROR",
            "MISSING_REQUIRED_FIELDS",
            f"Missing required fields: {', '.join(missing)}",
        )
    status = _string_or_empty(merged.get("status")).upper()
    action = _string_or_empty(merged.get("advisory_action")).upper()
    parsed_symbol = _string_or_empty(merged.get("parsed_symbol"))
    answer_summary = _string_or_empty(merged.get("answer_summary"))
    text_blob = " ".join([answer_summary, report_text, json.dumps(_json_safe(conversation_json), ensure_ascii=False)]).lower()
    is_demo = _to_bool(merged.get("demo_mode")) or _to_bool(merged.get("not_strategy_recommendation")) or action == "DEMO_ONLY"

    if parsed_symbol and (not re.fullmatch(r"\d{6}", parsed_symbol)):
        _add_issue(row, issues, "parsed_symbol", parsed_symbol, "ERROR", "SYMBOL_FORMAT_ERROR", "Parsed symbol must stay a six-digit string.")
    if _to_bool(merged.get("llm_api_called")) or _to_bool(merged.get("external_api_called")):
        _add_issue(row, issues, "llm_api_called", "", "ERROR", "LLM_API_CALLED", "Conversation artifact indicates an LLM or external API call.")
    if (
        _to_bool(merged.get("message_sent"))
        or _to_bool(merged.get("message_delivery_enabled"))
        or not _to_bool(merged.get("no_message_sent"))
    ):
        _add_issue(row, issues, "no_message_sent", "", "ERROR", "MESSAGE_DELIVERY_DETECTED", "Conversation artifact indicates message delivery.")
    if _to_bool(merged.get("auto_order_allowed")):
        _add_issue(row, issues, "auto_order_allowed", "", "ERROR", "AUTO_ORDER_ALLOWED", "auto_order_allowed must remain false.")
    if (
        not _to_bool(merged.get("no_live_trading"))
        or not _to_bool(merged.get("no_broker_api"))
        or _to_bool(merged.get("live_trading_enabled"))
        or _to_bool(merged.get("broker_api_invoked"))
    ):
        _add_issue(row, issues, "no_live_trading", "", "ERROR", "MISSING_NO_LIVE_TRADING_STATEMENT", "No-live/no-broker safety flags are missing or false.")
    if status == "PARSE_FAILED":
        if parsed_symbol or action not in NO_RECOMMENDATION_ACTIONS or _contains_unsafe_phrase(text_blob):
            _add_issue(row, issues, "status", status, "ERROR", "PARSE_FAILED_WITH_RECOMMENDATION", "PARSE_FAILED must not invent a symbol or recommendation.")
    if status == "NOT_FOUND":
        if action not in NO_RECOMMENDATION_ACTIONS or _contains_unsafe_phrase(text_blob):
            _add_issue(row, issues, "status", status, "ERROR", "NOT_FOUND_WITH_RECOMMENDATION", "NOT_FOUND must not invent a recommendation.")
    if is_demo and (action not in DEMO_SAFE_ACTIONS or _contains_unsafe_phrase(text_blob) or (action == "DEMO_ONLY" and "real trading recommendation" not in text_blob)):
        _add_issue(row, issues, "advisory_action", action, "ERROR", "DEMO_CONVERSATION_ACTION_UNSAFE", "DEMO_ONLY conversation must remain workflow validation only.")
    linked_answer_path = _string_or_empty(merged.get("linked_answer_markdown_path"))
    if status == "READY" and not linked_answer_path:
        _add_issue(row, issues, "linked_answer_markdown_path", "", "ERROR", "MISSING_LINKED_ANSWER", "READY conversation must link to an answer markdown artifact.")
    elif linked_answer_path and not _resolve_artifact_path(linked_answer_path, None).exists():
        _add_issue(row, issues, "linked_answer_markdown_path", linked_answer_path, "ERROR", "MISSING_LINKED_ANSWER", "Linked answer markdown path does not exist.")


def _resolve_artifact_path(value: Any, base_dir: Path | None) -> Path | None:
    text = _string_or_empty(value)
    if not text:
        return None
    path = Path(text)
    if path.is_absolute() or base_dir is None:
        return path
    candidate = base_dir / path
    return candidate if candidate.exists() else path


def _load_issue(issue_code: str, field: str, value: str, message: str) -> dict[str, Any]:
    return {
        "artifact_type": "ADVISORY_CONVERSATION",
        "conversation_run_id": "",
        "parsed_symbol": "",
        "parsed_intent": "",
        "path_field": field,
        "path_value": value,
        "severity": "ERROR",
        "issue_code": issue_code,
        "issue_message": message,
        "suggested_action": _suggested_action(issue_code),
    }


def _add_issue(
    row: dict[str, Any],
    issues: list[dict[str, Any]],
    path_field: str,
    path_value: Any,
    severity: str,
    issue_code: str,
    issue_message: str,
) -> None:
    issues.append(
        {
            "artifact_type": "ADVISORY_CONVERSATION",
            "conversation_run_id": _string_or_empty(row.get("conversation_run_id")),
            "parsed_symbol": _string_or_empty(row.get("parsed_symbol")),
            "parsed_intent": _string_or_empty(row.get("parsed_intent")),
            "path_field": path_field,
            "path_value": _string_or_empty(path_value),
            "severity": severity,
            "issue_code": issue_code,
            "issue_message": issue_message,
            "suggested_action": _suggested_action(issue_code),
        }
    )


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    for column in HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    if frame.empty:
        return frame[HEALTH_COLUMNS]
    return frame[HEALTH_COLUMNS].copy().sort_values(["severity", "issue_code", "conversation_run_id"]).reset_index(drop=True)


def _resolve_settings(
    settings: Settings | AdvisoryConversationHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, AdvisoryConversationHealthSettings]:
    if settings is None:
        project_settings = load_settings(Path("config/default.yaml"))
        return project_settings, project_settings.advisory_conversation_health
    if isinstance(settings, Settings):
        return settings, settings.advisory_conversation_health
    if isinstance(settings, AdvisoryConversationHealthSettings):
        project_settings = load_settings(Path("config/default.yaml"))
        return project_settings, settings
    project_settings = load_settings(Path("config/default.yaml"))
    return project_settings, AdvisoryConversationHealthSettings(**settings)


_BOOL_COLUMNS = {
    "llm_api_called",
    "external_api_called",
    "no_message_sent",
    "no_live_trading",
    "no_broker_api",
    "auto_order_allowed",
}


def _contains_unsafe_phrase(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in UNSAFE_PHRASES)


def _suggested_action(issue_code: str) -> str:
    actions = {
        "MISSING_METADATA": "Regenerate the advisory conversation artifact or remove partial diagnostics from active review.",
        "MISSING_CONVERSATION_JSON": "Regenerate the advisory conversation artifact.",
        "MISSING_REPORT": "Regenerate the advisory conversation report.",
        "MISSING_REQUIRED_FIELDS": "Repair metadata/JSON schema before using conversation artifacts.",
        "SYMBOL_FORMAT_ERROR": "Preserve parsed symbols as six-digit strings.",
        "LLM_API_CALLED": "Keep advisory-conversation v0.1 local and deterministic.",
        "MESSAGE_DELIVERY_DETECTED": "Remove delivery metadata; use preview-only artifacts.",
        "AUTO_ORDER_ALLOWED": "Keep auto_order_allowed=false.",
        "MISSING_NO_LIVE_TRADING_STATEMENT": "Restore no-live/no-broker safety flags.",
        "PARSE_FAILED_WITH_RECOMMENDATION": "Ensure parse failures do not invent symbols or advice.",
        "NOT_FOUND_WITH_RECOMMENDATION": "Ensure missing symbols do not invent recommendations.",
        "DEMO_CONVERSATION_ACTION_UNSAFE": "Keep demo conversations review-only and non-recommendational.",
        "MISSING_LINKED_ANSWER": "Regenerate linked single-symbol answer artifacts.",
    }
    return actions.get(issue_code, "Review and repair the advisory conversation artifact.")


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
