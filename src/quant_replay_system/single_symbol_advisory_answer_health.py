"""Local-only health checks for single-symbol advisory answer artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import Settings, SingleSymbolAdvisoryAnswerHealthSettings, load_settings
from quant_replay_system.data import normalize_symbol_value
from quant_replay_system.single_symbol_advisory_answer_index import (
    SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_COLUMNS,
    scan_single_symbol_advisory_answer_artifacts,
)


SINGLE_SYMBOL_ADVISORY_ANSWER_HEALTH_LIMITATIONS = [
    "Checks local question-style answer artifacts referenced by the answer index only.",
    "Does not regenerate advisory answers or alert previews.",
    "Does not call LLM APIs, send messages, place orders, call brokers, or enable live trading.",
    "Does not validate strategy quality or approve demo outputs as recommendations.",
]

HEALTH_COLUMNS = [
    "artifact_type",
    "answer_run_id",
    "advisory_run_id",
    "symbol",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

ISSUE_CODES = {
    "MISSING_METADATA",
    "MISSING_ANSWER_MARKDOWN",
    "MISSING_ANSWER_JSON",
    "MISSING_REQUIRED_FIELDS",
    "SYMBOL_FORMAT_ERROR",
    "AUTO_ORDER_ALLOWED",
    "MISSING_MANUAL_CONFIRMATION",
    "DEMO_ANSWER_UNSAFE",
    "NOT_FOUND_WITH_RECOMMENDATION",
    "LLM_API_CALLED",
    "MESSAGE_DELIVERY_DETECTED",
    "MISSING_NO_LIVE_TRADING_STATEMENT",
    "STALE_OR_PARTIAL_ANSWER",
}

REQUIRED_PATH_FIELDS = ["metadata_path", "answer_markdown_path", "answer_json_path"]

REQUIRED_ANSWER_FIELDS = [
    "answer_run_id",
    "advisory_run_id",
    "symbol",
    "status",
    "advisory_action",
    "question",
    "answer_style",
    "short_answer",
    "requires_manual_confirmation",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "no_message_sent",
]

DEMO_SAFE_ACTIONS = {"DEMO_ONLY", "WATCH", "BLOCKED", "NO_ACTION"}
NOT_FOUND_SAFE_ACTIONS = {"NO_ACTION", ""}
UNSAFE_RECOMMENDATION_ACTIONS = {"REVIEW_BUY_CANDIDATE", "REVIEW_SELL_CANDIDATE", "BUY", "SELL"}
UNSAFE_ANSWER_PHRASES = [
    "buy now",
    "sell now",
    "buy this stock now",
    "sell this stock now",
    "you should buy",
    "you should sell",
    "must buy",
    "must sell",
    "execute buy",
    "execute sell",
    "place order",
    "place a buy order",
    "place a sell order",
]


@dataclass(frozen=True)
class SingleSymbolAdvisoryAnswerHealthPaths:
    artifact_dir: Path
    single_symbol_advisory_answer_health_report: Path
    single_symbol_advisory_answer_health_issues: Path
    single_symbol_advisory_answer_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "single_symbol_advisory_answer_health_report": self.single_symbol_advisory_answer_health_report,
            "single_symbol_advisory_answer_health_issues": self.single_symbol_advisory_answer_health_issues,
            "single_symbol_advisory_answer_health_summary": self.single_symbol_advisory_answer_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SingleSymbolAdvisoryAnswerHealthResult:
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


def check_single_symbol_advisory_answer_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | SingleSymbolAdvisoryAnswerHealthSettings | dict[str, Any] | None = None,
) -> SingleSymbolAdvisoryAnswerHealthResult:
    """Check indexed question-style answer artifacts for safety and file health."""

    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Single-symbol advisory answer health cannot enable live trading or broker API access")

    index_frame, index_source, base_dir, load_warnings, load_issues = _load_index_for_health(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
    )
    checked_count = len(index_frame)
    health_frame = build_single_symbol_advisory_answer_health_frame(
        index_frame,
        base_dir=base_dir,
        settings=health_settings,
    )
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_single_symbol_advisory_answer_health(health_frame, checked_artifact_count=checked_count)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_single_symbol_advisory_answer_health_check_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_single_symbol_advisory_answer_health_paths(
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
        "single_symbol_advisory_answer_artifacts_only": True,
    }
    result = SingleSymbolAdvisoryAnswerHealthResult(
        status=status,
        checked_artifact_count=checked_count,
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=SINGLE_SYMBOL_ADVISORY_ANSWER_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_single_symbol_advisory_answer_health_artifacts(result)
    _ = project_settings
    return result


def build_single_symbol_advisory_answer_health_frame(
    index_df: pd.DataFrame,
    *,
    base_dir: str | Path | None = None,
    settings: SingleSymbolAdvisoryAnswerHealthSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    cfg = _coerce_health_settings(settings)
    index_frame = _prepare_index_frame(index_df)
    base_path = Path(base_dir) if base_dir is not None else None
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        if _string_or_empty(row.get("artifact_type")).upper() != "SINGLE_SYMBOL_ADVISORY_ANSWER":
            continue
        resolved_paths = {field: _resolve_artifact_path(row.get(field), base_path) for field in REQUIRED_PATH_FIELDS}
        metadata = _check_metadata(row, resolved_paths["metadata_path"], issues)
        answer_json = _check_answer_json(row, resolved_paths["answer_json_path"], issues)
        markdown_text = _check_answer_markdown(row, resolved_paths["answer_markdown_path"], issues, cfg)
        if metadata is not None and answer_json is not None:
            _check_answer_contract(row, metadata, answer_json, markdown_text, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_single_symbol_advisory_answer_health(
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


def resolve_single_symbol_advisory_answer_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> SingleSymbolAdvisoryAnswerHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return SingleSymbolAdvisoryAnswerHealthPaths(
        artifact_dir=artifact_dir,
        single_symbol_advisory_answer_health_report=artifact_dir / "single_symbol_advisory_answer_health_report.md",
        single_symbol_advisory_answer_health_issues=artifact_dir / "single_symbol_advisory_answer_health_issues.csv",
        single_symbol_advisory_answer_health_summary=artifact_dir / "single_symbol_advisory_answer_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_single_symbol_advisory_answer_health_artifacts(
    result: SingleSymbolAdvisoryAnswerHealthResult,
) -> dict[str, Path]:
    paths = SingleSymbolAdvisoryAnswerHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.single_symbol_advisory_answer_health_issues, index=False)
    result.summary_frame.to_csv(paths.single_symbol_advisory_answer_health_summary, index=False)
    metadata = build_single_symbol_advisory_answer_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.single_symbol_advisory_answer_health_report.write_text(
        render_single_symbol_advisory_answer_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_single_symbol_advisory_answer_health_metadata(
    result: SingleSymbolAdvisoryAnswerHealthResult,
    paths: SingleSymbolAdvisoryAnswerHealthPaths,
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
        "single_symbol_advisory_answer_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, LLM API, or message delivery was invoked.",
    }


def render_single_symbol_advisory_answer_health_report(
    result: SingleSymbolAdvisoryAnswerHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    _ = metadata
    lines = [
        f"# Single-Symbol Advisory Answer Health Check: {result.health_check_id}",
        "",
        "No live trading, broker API, order placement, LLM API, or message delivery was invoked. This health check validates local question-style answer artifacts only.",
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
            ["artifact_type", "answer_run_id", "symbol", "path_field", "severity", "issue_code", "issue_message", "suggested_action"],
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


def generate_single_symbol_advisory_answer_health_check_id(
    index_frame: pd.DataFrame,
    *,
    index_source: str,
    settings: SingleSymbolAdvisoryAnswerHealthSettings,
) -> str:
    frame = _prepare_index_frame(index_frame)
    payload = {
        "index_source": index_source,
        "answer_run_ids": sorted(str(value) for value in frame.get("answer_run_id", pd.Series(dtype="object")).dropna()),
        "strict": settings.strict,
        "config_version": settings.config_version,
    }
    return _hash_payload(payload, length=12)


def _load_index_for_health(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path | None,
    settings: SingleSymbolAdvisoryAnswerHealthSettings,
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    issues: list[dict[str, Any]] = []
    if index_df is not None:
        return _prepare_index_frame(index_df), "dataframe", None, warnings, issues
    if index_path is not None:
        return _load_index_path(Path(index_path), warnings, issues)
    if root is not None:
        root_path = Path(root)
        return scan_single_symbol_advisory_answer_artifacts(root_path), str(root_path), None, warnings, issues
    if settings.index_path.exists():
        return _load_index_path(settings.index_path, warnings, issues)
    warnings.append(f"Index path not found; scanning root instead: {settings.index_path}")
    return scan_single_symbol_advisory_answer_artifacts(settings.root_dir), str(settings.root_dir), None, warnings, issues


def _load_index_path(
    path: Path,
    warnings: list[str],
    issues: list[dict[str, Any]],
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    try:
        frame = pd.read_csv(path, dtype={"answer_run_id": str, "advisory_run_id": str, "symbol": str})
    except Exception as exc:
        issues.append(
            _issue(
                {"artifact_type": "", "answer_run_id": "", "advisory_run_id": "", "symbol": ""},
                path_field="index_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_METADATA",
                issue_message=f"Could not read single-symbol advisory answer index CSV: {exc}",
                suggested_action="Regenerate single-symbol-advisory-answer-index.",
            )
        )
        return _prepare_index_frame(pd.DataFrame()), str(path), path.parent, warnings, issues
    return _prepare_index_frame(frame), str(path), path.parent, warnings, issues


def _check_metadata(row: dict[str, Any], path: Path | None, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if path is None or not path.exists():
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_METADATA",
                issue_message="Question-style answer metadata.json is missing.",
                suggested_action="Rerun single-symbol-advisory --question-style.",
            )
        )
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_METADATA",
                issue_message=f"Question-style answer metadata.json is unreadable: {exc}",
                suggested_action="Regenerate the answer artifact.",
            )
        )
        return None


def _check_answer_json(row: dict[str, Any], path: Path | None, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if path is None or not path.exists():
        issues.append(
            _issue(
                row,
                path_field="answer_json_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_ANSWER_JSON",
                issue_message="single_symbol_advisory_answer.json is missing.",
                suggested_action="Rerun single-symbol-advisory --question-style.",
            )
        )
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(
            _issue(
                row,
                path_field="answer_json_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_ANSWER_JSON",
                issue_message=f"single_symbol_advisory_answer.json is unreadable: {exc}",
                suggested_action="Regenerate the answer artifact.",
            )
        )
        return None


def _check_answer_markdown(
    row: dict[str, Any],
    path: Path | None,
    issues: list[dict[str, Any]],
    cfg: SingleSymbolAdvisoryAnswerHealthSettings,
) -> str:
    if path is None or not path.exists():
        issues.append(
            _issue(
                row,
                path_field="answer_markdown_path",
                path_value=path,
                severity=_severity("ERROR", cfg),
                issue_code="MISSING_ANSWER_MARKDOWN",
                issue_message="single_symbol_advisory_answer.md is missing.",
                suggested_action="Rerun single-symbol-advisory --question-style.",
            )
        )
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(
            _issue(
                row,
                path_field="answer_markdown_path",
                path_value=path,
                severity=_severity("ERROR", cfg),
                issue_code="MISSING_ANSWER_MARKDOWN",
                issue_message=f"single_symbol_advisory_answer.md is unreadable: {exc}",
                suggested_action="Regenerate the answer artifact.",
            )
        )
        return ""


def _check_answer_contract(
    row: dict[str, Any],
    metadata: dict[str, Any],
    answer_json: dict[str, Any],
    markdown_text: str,
    issues: list[dict[str, Any]],
) -> None:
    missing = [field for field in REQUIRED_ANSWER_FIELDS if not _present(_coalesced(field, metadata, answer_json))]
    if missing:
        issues.append(
            _issue(
                row,
                path_field="answer_json_path",
                severity="ERROR",
                issue_code="MISSING_REQUIRED_FIELDS",
                issue_message=f"Question-style answer artifact is missing required fields: {', '.join(missing)}",
                suggested_action="Regenerate answer artifacts with the current contract.",
            )
        )
    _check_symbol_integrity(row, metadata, answer_json, issues)
    _check_safety_flags(row, metadata, answer_json, issues)
    _check_demo_safety(row, metadata, answer_json, markdown_text, issues)
    _check_not_found_safety(row, metadata, answer_json, markdown_text, issues)


def _check_symbol_integrity(
    row: dict[str, Any],
    metadata: dict[str, Any],
    answer_json: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    symbol = _string_or_empty(_coalesced("symbol", metadata, answer_json) or row.get("symbol"))
    normalized = normalize_symbol_value(symbol)
    if symbol.strip() != normalized and normalized.isdigit() and len(normalized) == 6:
        issues.append(
            _issue(
                row,
                path_field="answer_json_path",
                severity="ERROR",
                issue_code="SYMBOL_FORMAT_ERROR",
                issue_message=f"Answer symbol appears to have lost leading-zero formatting: {symbol!r}.",
                suggested_action="Regenerate answer artifacts preserving symbol values as strings.",
            )
        )


def _check_safety_flags(
    row: dict[str, Any],
    metadata: dict[str, Any],
    answer_json: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    if _any_bool_true("auto_order_allowed", metadata, answer_json):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="AUTO_ORDER_ALLOWED",
                issue_message="Question-style answer allows automatic order placement.",
                suggested_action="Regenerate the answer with auto_order_allowed=false.",
            )
        )
    if not _all_bool_true("requires_manual_confirmation", metadata, answer_json, default=True):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="MISSING_MANUAL_CONFIRMATION",
                issue_message="Question-style answer does not require manual confirmation.",
                suggested_action="Regenerate the answer with requires_manual_confirmation=true.",
            )
        )
    if not _all_bool_true("no_live_trading", metadata, answer_json) or not _all_bool_true("no_broker_api", metadata, answer_json):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="MISSING_NO_LIVE_TRADING_STATEMENT",
                issue_message="Answer is missing no_live_trading=true or no_broker_api=true.",
                suggested_action="Regenerate the answer with explicit local-only safety flags.",
            )
        )
    if not _all_bool_true("no_message_sent", metadata, answer_json):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="MESSAGE_DELIVERY_DETECTED",
                issue_message="Answer does not assert no_message_sent=true.",
                suggested_action="Regenerate the answer as local preview only.",
            )
        )
    if any(_to_bool(_coalesced(key, metadata, answer_json)) for key in ["message_sent", "message_delivery_enabled", "alert_delivery_enabled"]):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="MESSAGE_DELIVERY_DETECTED",
                issue_message="Answer metadata indicates message delivery or sending.",
                suggested_action="Do not use this artifact as local-only evidence; investigate delivery state.",
            )
        )
    if any(_to_bool(_coalesced(key, metadata, answer_json)) for key in ["llm_api_called", "external_api_called"]):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="LLM_API_CALLED",
                issue_message="Answer metadata indicates an LLM or external API call.",
                suggested_action="Regenerate v0.1 answers with deterministic local rendering only.",
            )
        )


def _check_demo_safety(
    row: dict[str, Any],
    metadata: dict[str, Any],
    answer_json: dict[str, Any],
    markdown_text: str,
    issues: list[dict[str, Any]],
) -> None:
    demo = _to_bool(_coalesced("demo_mode", metadata, answer_json))
    not_strategy = _to_bool(_coalesced("not_strategy_recommendation", metadata, answer_json))
    action = _string_or_empty(_coalesced("advisory_action", metadata, answer_json)).upper()
    if not (demo or not_strategy or action == "DEMO_ONLY"):
        return
    text = _answer_text(metadata, answer_json, markdown_text)
    if action not in DEMO_SAFE_ACTIONS or _contains_unsafe_instruction(text):
        issues.append(
            _issue(
                row,
                path_field="answer_markdown_path",
                severity="ERROR",
                issue_code="DEMO_ANSWER_UNSAFE",
                issue_message="Demo/not-strategy question-style answer contains unsafe action guidance.",
                suggested_action="Regenerate demo answers as DEMO_ONLY/WATCH/BLOCKED/NO_ACTION without real BUY/SELL instructions.",
            )
        )
    if demo and not not_strategy:
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="DEMO_ANSWER_UNSAFE",
                issue_message="Demo question-style answer is missing not_strategy_recommendation=true.",
                suggested_action="Regenerate demo answer with not_strategy_recommendation=true.",
            )
        )


def _check_not_found_safety(
    row: dict[str, Any],
    metadata: dict[str, Any],
    answer_json: dict[str, Any],
    markdown_text: str,
    issues: list[dict[str, Any]],
) -> None:
    status = _string_or_empty(_coalesced("status", metadata, answer_json)).upper()
    action = _string_or_empty(_coalesced("advisory_action", metadata, answer_json)).upper()
    if status != "NOT_FOUND":
        return
    text = _answer_text(metadata, answer_json, markdown_text)
    if action not in NOT_FOUND_SAFE_ACTIONS or action in UNSAFE_RECOMMENDATION_ACTIONS or _contains_unsafe_instruction(text):
        issues.append(
            _issue(
                row,
                path_field="answer_markdown_path",
                severity="ERROR",
                issue_code="NOT_FOUND_WITH_RECOMMENDATION",
                issue_message="NOT_FOUND question-style answer invented recommendation-like guidance.",
                suggested_action="Regenerate missing-symbol answer as NOT_FOUND with NO_ACTION and no invented recommendation.",
            )
        )


def _answer_text(metadata: dict[str, Any], answer_json: dict[str, Any], markdown_text: str) -> str:
    return "\n".join(
        [
            _string_or_empty(metadata.get("short_answer")),
            _string_or_empty(answer_json.get("short_answer")),
            _string_or_empty(answer_json.get("answer_body")),
            markdown_text,
        ]
    ).lower()


def _contains_unsafe_instruction(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in UNSAFE_ANSWER_PHRASES)


def _coalesced(field: str, metadata: dict[str, Any], answer_json: dict[str, Any]) -> Any:
    for payload in [
        metadata,
        answer_json,
        answer_json.get("audit_metadata") if isinstance(answer_json.get("audit_metadata"), dict) else {},
        metadata.get("audit_metadata") if isinstance(metadata.get("audit_metadata"), dict) else {},
        answer_json.get("advisory_record") if isinstance(answer_json.get("advisory_record"), dict) else {},
    ]:
        value = payload.get(field) if isinstance(payload, dict) else None
        if _present(value):
            return value
    return ""


def _any_bool_true(field: str, metadata: dict[str, Any], answer_json: dict[str, Any]) -> bool:
    return any(_to_bool(payload.get(field)) for payload in _payloads(metadata, answer_json) if isinstance(payload, dict))


def _all_bool_true(
    field: str,
    metadata: dict[str, Any],
    answer_json: dict[str, Any],
    *,
    default: bool = False,
) -> bool:
    values = [payload.get(field) for payload in _payloads(metadata, answer_json) if isinstance(payload, dict) and _present(payload.get(field))]
    if not values:
        return default
    return all(_to_bool(value) for value in values)


def _payloads(metadata: dict[str, Any], answer_json: dict[str, Any]) -> list[dict[str, Any]]:
    payloads = [metadata, answer_json]
    for payload in [metadata.get("audit_metadata"), answer_json.get("audit_metadata"), answer_json.get("advisory_record")]:
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _resolve_artifact_path(value: Any, base_dir: Path | None) -> Path | None:
    if not _present(value):
        return None
    path = Path(str(value))
    if path.exists() or path.is_absolute() or base_dir is None:
        return path
    candidate = base_dir / path
    if candidate.exists():
        return candidate
    return path


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    index = frame.copy(deep=True)
    for column in SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_COLUMNS:
        if column not in index.columns:
            index[column] = ""
    if index.empty:
        return index[SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_COLUMNS]
    return index[SINGLE_SYMBOL_ADVISORY_ANSWER_INDEX_COLUMNS].reset_index(drop=True)


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    issues = frame.copy(deep=True)
    for column in HEALTH_COLUMNS:
        if column not in issues.columns:
            issues[column] = ""
    if issues.empty:
        return issues[HEALTH_COLUMNS]
    return issues[HEALTH_COLUMNS].sort_values(["severity", "issue_code", "answer_run_id"], na_position="last").reset_index(drop=True)


def _issue(
    row: dict[str, Any],
    *,
    path_field: str,
    severity: str,
    issue_code: str,
    issue_message: str,
    suggested_action: str,
    path_value: Any = None,
) -> dict[str, Any]:
    if issue_code not in ISSUE_CODES:
        raise ValueError(f"Unsupported single-symbol advisory answer health issue_code: {issue_code}")
    return {
        "artifact_type": _string_or_empty(row.get("artifact_type", "SINGLE_SYMBOL_ADVISORY_ANSWER")) or "SINGLE_SYMBOL_ADVISORY_ANSWER",
        "answer_run_id": _string_or_empty(row.get("answer_run_id", "")),
        "advisory_run_id": _string_or_empty(row.get("advisory_run_id", "")),
        "symbol": _string_or_empty(row.get("symbol", "")),
        "path_field": path_field,
        "path_value": _string_or_empty(path_value if path_value is not None else row.get(path_field, "")),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _severity(value: str, cfg: SingleSymbolAdvisoryAnswerHealthSettings) -> str:
    severity = str(value).upper()
    if cfg.strict and severity == "WARN":
        return "ERROR"
    return severity


def _coerce_health_settings(
    settings: SingleSymbolAdvisoryAnswerHealthSettings | dict[str, Any] | None,
) -> SingleSymbolAdvisoryAnswerHealthSettings:
    if settings is None:
        return SingleSymbolAdvisoryAnswerHealthSettings()
    if isinstance(settings, SingleSymbolAdvisoryAnswerHealthSettings):
        return settings
    if isinstance(settings, dict):
        return SingleSymbolAdvisoryAnswerHealthSettings(**settings)
    if hasattr(settings, "model_dump"):
        return SingleSymbolAdvisoryAnswerHealthSettings(**settings.model_dump())
    raise TypeError("settings must be SingleSymbolAdvisoryAnswerHealthSettings, dict, or None")


def _resolve_settings(
    settings: Settings | SingleSymbolAdvisoryAnswerHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, SingleSymbolAdvisoryAnswerHealthSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.single_symbol_advisory_answer_health
    if isinstance(settings, Settings):
        return settings, settings.single_symbol_advisory_answer_health
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, SingleSymbolAdvisoryAnswerHealthSettings):
        return project.model_copy(update={"single_symbol_advisory_answer_health": settings}), settings
    if isinstance(settings, dict):
        payload = dict(project.single_symbol_advisory_answer_health.model_dump())
        payload.update(settings)
        health_settings = SingleSymbolAdvisoryAnswerHealthSettings(**payload)
        return project.model_copy(update={"single_symbol_advisory_answer_health": health_settings}), health_settings
    raise TypeError("settings must be Settings, SingleSymbolAdvisoryAnswerHealthSettings, dict, or None")


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


def _present(value: Any) -> bool:
    return _string_or_empty(value).strip() != ""


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
