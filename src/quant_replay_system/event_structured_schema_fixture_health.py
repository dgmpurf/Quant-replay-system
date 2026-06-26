"""Health view for report-only event structured schema fixture artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.event_structured_schema_fixture import (
    ALLOWED_TRADE_USAGE,
    DIRECTION_FOR_AFFECTED_ENTITY,
    DIRECTION_RULE_TYPES,
    EVENT_SCOPES,
    EVENT_STATUSES,
    EVENT_TYPES,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    FORBIDDEN_TRADE_USAGE,
    MANUAL_REVIEW_STATUSES,
    QUALITY_STATUSES,
    REQUIRED_EVENT_STRUCTURED_FIELDS,
    SOURCE_TIERS,
)
from quant_replay_system.event_structured_schema_fixture_index import VIEW_DIR_NAMES


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
REQUIRED_ARTIFACTS = {
    "metadata": "event_structured_schema_fixture_metadata.json",
    "schema_fields": "event_structured_schema_fields.csv",
    "fixture_rows": "event_structured_fixture_rows.csv",
    "type_matrix": "event_structured_type_matrix.csv",
    "direction_matrix": "event_structured_direction_matrix.csv",
    "pit_lineage_matrix": "event_structured_pit_lineage_matrix.csv",
    "source_quality_matrix": "event_structured_source_quality_matrix.csv",
    "validation_summary": "event_structured_validation_summary.csv",
    "limitations": "event_structured_limitations.md",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class EventStructuredSchemaFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_event_structured_schema_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/event_structured_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/event_structured_schema_fixture_v0_1/health",
) -> EventStructuredSchemaFixtureHealthResult:
    candidate_dirs = _candidate_dirs(Path(root))
    issues: list[dict[str, Any]] = []
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "event_structured_schema_fixture_health.csv",
        "health_report": Path(output_dir) / "event_structured_schema_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = EventStructuredSchemaFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if Path(root).exists() else [f"Event structured schema fixture root does not exist: {root}"],
        audit_metadata=_audit_metadata(root, len(candidate_dirs)),
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, Any]]:
    run_id = artifact_dir.name
    issues: list[dict[str, Any]] = []
    paths = {key: artifact_dir / filename for key, filename in REQUIRED_ARTIFACTS.items()}
    for path in paths.values():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Required artifact missing: {path}", path))

    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_issue(run_id, "ERROR", "METADATA_UNREADABLE", f"Metadata cannot be read: {exc}", paths["metadata"]))

    if metadata is not None:
        run_id = _text(metadata.get("event_structured_schema_fixture_id")) or run_id
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
    if paths["schema_fields"].exists():
        issues.extend(_schema_field_issues(run_id, paths["schema_fields"]))
    if paths["fixture_rows"].exists():
        issues.extend(_fixture_row_issues(run_id, paths["fixture_rows"]))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], metadata_path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    status = _text(metadata.get("status"))
    if status not in {"PASS", "WARN", "FAIL"}:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_STATUS", f"Unknown fixture status: {status}", metadata_path))
    if status == "FAIL":
        issues.append(_issue(run_id, "ERROR", "FIXTURE_STATUS_NOT_PASS", "Fixture metadata status is FAIL.", metadata_path))
    if not _to_bool(metadata.get("event_structured_schema_fixture_created")):
        issues.append(_issue(run_id, "ERROR", "CREATED_FLAG_MISSING", "event_structured_schema_fixture_created is not true.", metadata_path))
    if not _to_bool(metadata.get("event_structured_rows_created")):
        issues.append(_issue(run_id, "ERROR", "EVENT_STRUCTURED_ROWS_CREATED_FLAG_MISSING", "event_structured_rows_created is not true.", metadata_path))
    if _to_int(metadata.get("event_count")) != 10:
        issues.append(_issue(run_id, "ERROR", "EVENT_COUNT_NOT_10", "event_count must be 10.", metadata_path))
    if _to_int(metadata.get("validation_issue_count")) != 0:
        issues.append(_issue(run_id, "ERROR", "VALIDATION_ISSUE_COUNT_NOT_ZERO", "validation_issue_count must be 0.", metadata_path))
    if not _to_bool(metadata.get("report_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_REPORT_ONLY_NOT_TRUE", "metadata report_only is not true.", metadata_path))
    if not _to_bool(metadata.get("diagnostic_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_DIAGNOSTIC_ONLY_NOT_TRUE", "metadata diagnostic_only is not true.", metadata_path))
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{flag} is true.", metadata_path))
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    for key, value in artifact_paths.items():
        if _unsafe_path_text(value):
            issues.append(_issue(run_id, "ERROR", "UNSAFE_ARTIFACT_PATH", f"Unsafe artifact path for {key}: {value}", metadata_path))
    return issues


def _schema_field_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        fields = pd.read_csv(path, dtype=str)
    except Exception as exc:
        return [_issue(run_id, "ERROR", "SCHEMA_FIELDS_UNREADABLE", f"Schema fields cannot be read: {exc}", path)]
    if "field_name" not in fields.columns:
        return [_issue(run_id, "ERROR", "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING", "schema fields missing field_name column.", path)]
    missing = sorted(set(REQUIRED_EVENT_STRUCTURED_FIELDS) - set(fields["field_name"].dropna().astype(str)))
    if missing:
        return [
            _issue(
                run_id,
                "ERROR",
                "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING",
                f"schema fields missing required field names: {','.join(missing)}",
                path,
            )
        ]
    return []


def _fixture_row_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        rows = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(run_id, "ERROR", "FIXTURE_ROWS_UNREADABLE", f"fixture rows cannot be read: {exc}", path)]
    issues: list[dict[str, Any]] = []
    missing = sorted(set(REQUIRED_EVENT_STRUCTURED_FIELDS) - set(rows.columns))
    if missing:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING",
                f"fixture rows missing required columns: {','.join(missing)}",
                path,
            )
        )
        return issues

    row_text = " ".join(rows.astype(str).agg(" ".join, axis=1))
    column_text = " ".join(str(column) for column in rows.columns)
    lower_text = row_text.lower()
    by_id = rows.set_index("event_structured_id", drop=False)

    if _contains_secret_like(f"{column_text} {row_text}"):
        issues.append(_issue(run_id, "ERROR", "SENSITIVE_TEXT_DETECTED", "token/secret-looking text appears in fixture rows.", path))
    if len(rows) != 10:
        issues.append(_issue(run_id, "ERROR", "EVENT_COUNT_NOT_10", "event structured fixture must contain exactly 10 rows.", path))
    if not rows["event_structured_id"].is_unique:
        issues.append(_issue(run_id, "ERROR", "EVENT_STRUCTURED_ID_NOT_UNIQUE", "event_structured_id must be unique.", path))
    if not rows["event_version"].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", "EVENT_VERSION_MISSING", "event_version must be populated.", path))
    separated = rows[(rows["event_time"] != rows["publish_time"]) & (rows["publish_time"] != rows["available_time"])]
    if len(separated) < 6:
        issues.append(_issue(run_id, "ERROR", "TIMING_SEPARATION_INSUFFICIENT", "event_time, publish_time, and available_time must be separated in at least 6 examples.", path))

    for column, code in [
        ("available_time", "AVAILABLE_TIME_MISSING"),
        ("source_id", "SOURCE_ID_MISSING"),
        ("revision_id", "REVISION_ID_MISSING"),
        ("parser_version", "PARSER_VERSION_MISSING"),
        ("extractor_version", "EXTRACTOR_VERSION_MISSING"),
    ]:
        if not rows[column].map(_is_non_empty_text).all():
            issues.append(_issue(run_id, "ERROR", code, f"{column} must be populated.", path))
    if not rows["document_id"].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", "DOCUMENT_ID_MISSING_FOR_EVIDENCE_BACKED", "evidence-backed rows need document_id.", path))
    if not rows["document_version_id"].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", "DOCUMENT_VERSION_ID_MISSING_FOR_EVIDENCE_BACKED", "evidence-backed rows need document_version_id.", path))
    if not rows.apply(lambda row: bool(_text(row["source_hash"])) or bool(_text(row["content_hash"])), axis=1).all():
        issues.append(_issue(run_id, "ERROR", "HASH_OR_CONTENT_HASH_MISSING", "evidence-backed rows need source_hash or content_hash.", path))
    if not rows.apply(lambda row: _timestamp_to_date_order_ok(row["available_time"], row["as_of_date"]), axis=1).all():
        issues.append(_issue(run_id, "ERROR", "AVAILABLE_TIME_AFTER_AS_OF_DATE", "available_time must not be after as_of_date under fixture contract.", path))
    if not rows.apply(lambda row: _timestamp_order_ok(row["available_time"], row["stale_after"]), axis=1).all():
        issues.append(_issue(run_id, "ERROR", "STALE_AFTER_BEFORE_AVAILABLE_TIME", "stale_after must not be before available_time.", path))

    _enum_check(issues, run_id, path, rows, "event_type", EVENT_TYPES, "EVENT_TYPE_INVALID")
    _enum_check(issues, run_id, path, rows, "event_scope", EVENT_SCOPES, "EVENT_SCOPE_INVALID")
    _enum_check(issues, run_id, path, rows, "source_tier", SOURCE_TIERS, "SOURCE_TIER_INVALID")
    _enum_check(issues, run_id, path, rows, "direction_rule_type", DIRECTION_RULE_TYPES, "DIRECTION_RULE_TYPE_INVALID")
    _enum_check(issues, run_id, path, rows, "direction_for_affected_entity", DIRECTION_FOR_AFFECTED_ENTITY, "DIRECTION_FOR_AFFECTED_ENTITY_INVALID")
    _enum_check(issues, run_id, path, rows, "event_status", EVENT_STATUSES, "EVENT_STATUS_INVALID")
    _enum_check(issues, run_id, path, rows, "quality_status", QUALITY_STATUSES, "QUALITY_STATUS_INVALID")
    _enum_check(issues, run_id, path, rows, "manual_review_status", MANUAL_REVIEW_STATUSES, "MANUAL_REVIEW_STATUS_INVALID")

    mixed_or_conditional = rows[
        rows["direction_rule_type"].isin(["CONDITIONAL", "MIXED_BY_EXPOSURE", "MIXED_BY_REGIME"])
        | rows["direction_for_affected_entity"].isin(["CONDITIONAL", "MIXED"])
    ]
    if not mixed_or_conditional.empty and not mixed_or_conditional["direction_rule_detail"].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", "MIXED_OR_CONDITIONAL_DIRECTION_DETAIL_MISSING", "mixed/conditional direction rows need direction_rule_detail.", path))
    if "SYNTH_IRON_ORE_PRICE_SHOCK_PUBLIC" in by_id.index:
        iron = _first_row(by_id.loc["SYNTH_IRON_ORE_PRICE_SHOCK_PUBLIC"])
        detail = _text(iron["direction_rule_detail"]).lower()
        if not (
            iron["direction_rule_type"] == "MIXED_BY_EXPOSURE"
            and iron["direction_for_affected_entity"] == "MIXED"
            and _is_non_empty_text(iron["company_exposure_id_refs"])
            and "steel buyer" in detail
            and "resource producer" in detail
        ):
            issues.append(_issue(run_id, "ERROR", "COMMODITY_POLICY_DIRECTION_CONTEXT_MISSING", "commodity/policy event needs company-exposure-based directional context.", path))
    else:
        issues.append(_issue(run_id, "ERROR", "COMMODITY_POLICY_DIRECTION_CONTEXT_MISSING", "commodity direction sample row is missing.", path))
    if "SYNTH_OFFICIAL_STEEL_CAPACITY_RESTRICTION" in by_id.index:
        policy = _first_row(by_id.loc["SYNTH_OFFICIAL_STEEL_CAPACITY_RESTRICTION"])
        if not (
            policy["direction_rule_type"] == "CONDITIONAL"
            and policy["direction_for_affected_entity"] == "CONDITIONAL"
            and _is_non_empty_text(policy["company_exposure_id_refs"])
            and _is_non_empty_text(policy["direction_rule_detail"])
        ):
            issues.append(_issue(run_id, "ERROR", "COMMODITY_POLICY_DIRECTION_CONTEXT_MISSING", "policy row needs company-exposure-based directional context.", path))
    else:
        issues.append(_issue(run_id, "ERROR", "COMMODITY_POLICY_DIRECTION_CONTEXT_MISSING", "policy direction sample row is missing.", path))
    if "SYNTH_ST_DELIST_RISK_VETO_EVENT" in by_id.index:
        risk = _first_row(by_id.loc["SYNTH_ST_DELIST_RISK_VETO_EVENT"])
        risk_detail = _text(risk["direction_rule_detail"]).lower()
        if not (
            risk["direction_rule_type"] == "RISK_VETO_ONLY"
            and risk["direction_for_affected_entity"] == "RISK_VETO_ONLY"
            and not _to_bool(risk["is_alpha_claim"])
            and not _to_bool(risk["real_buy_review_allowed"])
            and not _to_bool(risk["trading_allowed"])
            and "creates positive alpha" not in risk_detail
            and "buy permission" not in risk_detail
            and "buy signal" not in risk_detail
        ):
            issues.append(_issue(run_id, "ERROR", "RISK_VETO_IMPLIES_POSITIVE_ALPHA_OR_BUY", "risk veto row must not imply positive alpha or buy permission.", path))
    if "SYNTH_BLOCKED_UNVERIFIED_RUMOR_EVENT" in by_id.index:
        blocked = _first_row(by_id.loc["SYNTH_BLOCKED_UNVERIFIED_RUMOR_EVENT"])
        if blocked["trade_usage"] != "no_trade":
            issues.append(_issue(run_id, "ERROR", "BLOCKED_RUMOR_NOT_NO_TRADE", "blocked rumor row must be no_trade.", path))
        if _to_bool(blocked["pit_valid"]) or _to_bool(blocked["decision_time_eligible"]):
            issues.append(_issue(run_id, "ERROR", "BLOCKED_RUMOR_PIT_OR_DECISION_ELIGIBLE", "blocked rumor row cannot be PIT-valid or decision-time eligible.", path))
    if "SYNTH_INDEX_REBALANCE_CONTEXT" in by_id.index:
        etf = _first_row(by_id.loc["SYNTH_INDEX_REBALANCE_CONTEXT"])
        etf_text = f"{etf.get('validation_notes', '')} {etf.get('direction_rule_detail', '')}".lower()
        if ("real/current holdings" in etf_text or "real or current holdings ingestion" in etf_text) and "does not claim" not in etf_text:
            issues.append(_issue(run_id, "ERROR", "ETF_INDEX_ROW_CLAIMS_REAL_CURRENT_HOLDINGS", "ETF/index row cannot claim real/current holdings ingestion.", path))

    extraction_confidence = pd.to_numeric(rows["extraction_confidence"], errors="coerce")
    if extraction_confidence.isna().any() or not extraction_confidence.between(0, 1).all():
        issues.append(_issue(run_id, "ERROR", "EXTRACTION_CONFIDENCE_OUT_OF_BOUNDS", "extraction_confidence must be numeric and within [0, 1].", path))
    event_confidence = pd.to_numeric(rows["event_confidence"], errors="coerce")
    if event_confidence.isna().any() or not event_confidence.between(0, 1).all():
        issues.append(_issue(run_id, "ERROR", "EVENT_CONFIDENCE_OUT_OF_BOUNDS", "event_confidence must be numeric and within [0, 1].", path))
    if _confidence_claims_probability(lower_text):
        issues.append(_issue(run_id, "ERROR", "CONFIDENCE_TREATED_AS_RETURN_PROBABILITY", "confidence fields must not be encoded as return probability.", path))
    if rows["trade_usage"].isin(FORBIDDEN_TRADE_USAGE).any():
        issues.append(_issue(run_id, "ERROR", "TRADE_USAGE_FORBIDDEN", "trade_usage contains buy/sell/trading usage.", path))
    elif not rows["trade_usage"].isin(ALLOWED_TRADE_USAGE).all():
        issues.append(_issue(run_id, "ERROR", "TRADE_USAGE_INVALID", "trade_usage contains invalid values.", path))

    row_checks = [
        ("report_only", True, "ROW_REPORT_ONLY_NOT_TRUE"),
        ("diagnostic_only", True, "ROW_DIAGNOSTIC_ONLY_NOT_TRUE"),
        ("is_live_signal", False, "ROW_IS_LIVE_SIGNAL_TRUE"),
        ("is_alpha_claim", False, "ROW_IS_ALPHA_CLAIM_TRUE"),
        ("signal_score_implemented", False, "ROW_SIGNAL_SCORE_IMPLEMENTED_TRUE"),
        ("model_training_allowed", False, "ROW_MODEL_TRAINING_ALLOWED_TRUE"),
        ("active_weight_allowed", False, "ROW_ACTIVE_WEIGHT_ALLOWED_TRUE"),
        ("active_threshold_allowed", False, "ROW_ACTIVE_THRESHOLD_ALLOWED_TRUE"),
        ("stock_profile_validation_allowed", False, "ROW_STOCK_PROFILE_VALIDATION_ALLOWED_TRUE"),
        ("real_buy_review_allowed", False, "ROW_REAL_BUY_REVIEW_ALLOWED_TRUE"),
        ("trading_allowed", False, "ROW_TRADING_ALLOWED_TRUE"),
    ]
    for column, expected, code in row_checks:
        actual = rows[column].map(_to_bool)
        failed = not actual.all() if expected else actual.any()
        if failed:
            issues.append(_issue(run_id, "ERROR", code, f"{column} must be {expected} for every fixture row.", path))
    return issues


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and any((path / filename).exists() for filename in REQUIRED_ARTIFACTS.values())
    )


def _write(result: EventStructuredSchemaFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Event Structured Schema Fixture Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "This health view is report-only. It does not create production event ingestion, active event libraries, real raw document ingestion, real source adapters, crawlers, LLM extraction runtime, factor observations, production company exposure mappings, replay evidence bundles, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, API calls, broker behavior, orders, messages, or trading.",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues.",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _enum_check(
    issues: list[dict[str, Any]],
    run_id: str,
    path: Path,
    rows: pd.DataFrame,
    column: str,
    allowed: set[str],
    code: str,
) -> None:
    if not rows[column].isin(allowed).all():
        issues.append(_issue(run_id, "ERROR", code, f"{column} contains invalid values.", path))


def _issue(run_id: str, severity: str, code: str, message: str, path: str | Path) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "status": "OPEN",
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, HEALTH_COLUMNS]


def _audit_metadata(root: str | Path, checked_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "checked_artifact_count": checked_count,
        "report_only": True,
        "diagnostic_only": True,
        "event_structured_schema_fixture_health_created": True,
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    }


def _unsafe_path_text(value: Any) -> bool:
    text = _text(value).replace("\\", "/").lower()
    unsafe_fragments = [
        "data/raw",
        "data/processed",
        "data/cache",
        "broker",
        "order",
        "trading",
        "current-candidates",
        "current_candidates",
        "snapshot",
        "signal_semantics",
        "model_training",
        "active_weights",
        "active_thresholds",
    ]
    return any(fragment in text for fragment in unsafe_fragments)


def _confidence_claims_probability(text: str) -> bool:
    unsafe_patterns = [
        "confidence is return probability",
        "confidence as return probability",
        "confidence = return probability",
        "extraction_confidence is return probability",
        "event_confidence is return probability",
        "return_probability",
    ]
    return any(pattern in text for pattern in unsafe_patterns)


def _first_row(value: pd.Series | pd.DataFrame) -> pd.Series:
    if isinstance(value, pd.DataFrame):
        return value.iloc[0]
    return value


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _contains_secret_like(text: str) -> bool:
    return bool(re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text.lower()))


def _timestamp_order_ok(first: Any, second: Any) -> bool:
    first_text = _text(first)
    second_text = _text(second)
    if not first_text or not second_text:
        return False
    first_ts = pd.to_datetime(first_text, errors="coerce")
    second_ts = pd.to_datetime(second_text, errors="coerce")
    if pd.isna(first_ts) or pd.isna(second_ts):
        return False
    return bool(first_ts <= second_ts)


def _timestamp_to_date_order_ok(timestamp_value: Any, date_value: Any) -> bool:
    timestamp_text = _text(timestamp_value)
    date_text = _text(date_value)
    if not timestamp_text or not date_text:
        return False
    timestamp = pd.to_datetime(timestamp_text, errors="coerce")
    date = pd.to_datetime(date_text, errors="coerce")
    if pd.isna(timestamp) or pd.isna(date):
        return False
    return bool(timestamp.normalize() <= date.normalize())


def _is_non_empty_text(value: Any) -> bool:
    return bool(_text(value))


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
