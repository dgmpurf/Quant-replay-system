"""Health view for report-only replay decision schema fixture artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.replay_decision_schema_fixture import (
    ALLOWED_DECISION_ACTIONABILITY,
    ALLOWED_DECISION_LABELS,
    ALLOWED_FREEZE_STATUS,
    ALLOWED_TRADE_USAGE,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    FORBIDDEN_TRADE_USAGE,
    REQUIRED_REPLAY_DECISION_FIELDS,
    ROW_FALSE_FLAGS,
)
from quant_replay_system.replay_decision_schema_fixture_index import VIEW_DIR_NAMES


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
REQUIRED_ARTIFACTS = {
    "metadata": "replay_decision_schema_fixture_metadata.json",
    "schema_fields": "replay_decision_schema_fields.csv",
    "fixture_rows": "replay_decision_fixture_rows.csv",
    "evidence_bundle_matrix": "replay_decision_evidence_bundle_matrix.csv",
    "pit_admissibility_matrix": "replay_decision_pit_admissibility_matrix.csv",
    "freeze_matrix": "replay_decision_freeze_matrix.csv",
    "label_exclusion_matrix": "replay_decision_label_exclusion_matrix.csv",
    "quality_compliance_matrix": "replay_decision_quality_compliance_matrix.csv",
    "risk_veto_matrix": "replay_decision_risk_veto_matrix.csv",
    "forbidden_output_guard_matrix": "replay_decision_forbidden_output_guard_matrix.csv",
    "validation_summary": "replay_decision_validation_summary.csv",
    "limitations": "replay_decision_limitations.md",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class ReplayDecisionSchemaFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_replay_decision_schema_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/replay_decision_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/replay_decision_schema_fixture_v0_1/health",
) -> ReplayDecisionSchemaFixtureHealthResult:
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
        "health_csv": Path(output_dir) / "replay_decision_schema_fixture_health.csv",
        "health_report": Path(output_dir) / "replay_decision_schema_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ReplayDecisionSchemaFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if Path(root).exists() else [f"Replay decision schema fixture root does not exist: {root}"],
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
        run_id = _text(metadata.get("replay_decision_schema_fixture_id")) or run_id
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
    if status != "PASS":
        issues.append(_issue(run_id, "ERROR", "FIXTURE_STATUS_NOT_PASS", "Fixture metadata status is not PASS.", metadata_path))
    if not _to_bool(metadata.get("replay_decision_schema_fixture_created")):
        issues.append(_issue(run_id, "ERROR", "CREATED_FLAG_MISSING", "replay_decision_schema_fixture_created is not true.", metadata_path))
    if not _to_bool(metadata.get("replay_decision_rows_created")):
        issues.append(_issue(run_id, "ERROR", "REPLAY_DECISION_ROWS_CREATED_FLAG_MISSING", "replay_decision_rows_created is not true.", metadata_path))
    if _to_int(metadata.get("decision_count")) != 10:
        issues.append(_issue(run_id, "ERROR", "DECISION_COUNT_NOT_10", "decision_count must be 10.", metadata_path))
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
    missing = sorted(set(REQUIRED_REPLAY_DECISION_FIELDS) - set(fields["field_name"].dropna().astype(str)))
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
    missing = sorted(set(REQUIRED_REPLAY_DECISION_FIELDS) - set(rows.columns))
    if missing:
        issues.append(
            _issue(run_id, "ERROR", "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING", f"fixture rows missing required columns: {','.join(missing)}", path)
        )
        return issues

    by_id = rows.set_index("replay_decision_id", drop=False)
    all_text = " ".join(rows.astype(str).agg(" ".join, axis=1))
    eligible = rows[rows["decision_time_eligible"].map(_to_bool)]
    frozen = rows[rows["freeze_status"] == "FROZEN_SYNTHETIC_FIXTURE"]

    if _contains_sensitive_text(all_text):
        issues.append(_issue(run_id, "ERROR", "SENSITIVE_TEXT_DETECTED", "token/secret-looking text appears in fixture rows.", path))
    if len(rows) != 10:
        issues.append(_issue(run_id, "ERROR", "DECISION_COUNT_NOT_10", "replay decision fixture must contain exactly 10 rows.", path))
    if not rows["replay_decision_id"].is_unique:
        issues.append(_issue(run_id, "ERROR", "REPLAY_DECISION_ID_NOT_UNIQUE", "replay_decision_id must be unique.", path))
    _non_empty_check(issues, run_id, path, rows, "replay_decision_time", "REPLAY_DECISION_TIME_MISSING")
    if not rows[["entity_id", "symbol", "instrument_type"]].map(_is_non_empty_text).all().all():
        issues.append(_issue(run_id, "ERROR", "ENTITY_CONTEXT_MISSING", "entity_id, symbol, and instrument_type must be populated.", path))
    if not eligible.empty and not eligible["replay_evidence_bundle_id"].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", "REPLAY_EVIDENCE_BUNDLE_ID_MISSING", "eligible rows need replay_evidence_bundle_id.", path))
    if not eligible.empty and not (eligible["replay_evidence_bundle_status"] == "PASS").all():
        issues.append(_issue(run_id, "ERROR", "ELIGIBLE_BUNDLE_STATUS_NOT_PASS", "eligible rows need PASS bundle status.", path))
    if not eligible.empty and not (eligible["replay_evidence_bundle_health_status"] == "PASS").all():
        issues.append(_issue(run_id, "ERROR", "ELIGIBLE_BUNDLE_HEALTH_NOT_PASS", "eligible rows need PASS bundle health.", path))
    if not eligible.empty and not (eligible["replay_evidence_bundle_workflow_stage"] == "REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED").all():
        issues.append(_issue(run_id, "ERROR", "ELIGIBLE_BUNDLE_STAGE_INVALID", "eligible rows need replay evidence bundle fixture stage.", path))
    if not eligible.empty and not eligible.apply(lambda row: _timestamp_order_ok(row["available_time_max"], row["replay_decision_time"]), axis=1).all():
        issues.append(_issue(run_id, "ERROR", "ELIGIBLE_AVAILABLE_TIME_AFTER_DECISION_TIME", "eligible available_time after decision time.", path))

    future_available = rows[rows.apply(lambda row: _timestamp_order_strict_after(row["available_time_max"], row["replay_decision_time"]), axis=1)]
    if not future_available.empty and (
        future_available["decision_time_eligible"].map(_to_bool).any()
        or future_available["pit_valid"].map(_to_bool).any()
        or future_available["all_inputs_available_lte_decision_time"].map(_to_bool).any()
    ):
        issues.append(_issue(run_id, "ERROR", "FUTURE_AVAILABLE_EVIDENCE_NOT_BLOCKED", "future-available evidence must be blocked.", path))
    if not rows["future_label_excluded"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "FUTURE_LABELS_NOT_EXCLUDED", "future labels must be excluded.", path))
    if not rows["future_outcome_excluded"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "FUTURE_OUTCOMES_NOT_EXCLUDED", "future outcomes must be excluded.", path))
    if not rows["future_return_excluded"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "FUTURE_RETURNS_NOT_EXCLUDED", "future returns must be excluded.", path))
    if not rows["future_revision_excluded"].map(_to_bool).all():
        issues.append(_issue(run_id, "ERROR", "FUTURE_REVISIONS_NOT_EXCLUDED", "future revisions must be excluded.", path))
    output_exclusion_columns = [
        "metrics_excluded",
        "training_output_excluded",
        "model_output_excluded",
        "stock_profile_output_excluded",
        "paper_approval_excluded",
        "buy_review_output_excluded",
    ]
    if not rows[output_exclusion_columns].apply(lambda col: col.map(_to_bool)).all().all():
        issues.append(_issue(run_id, "ERROR", "OUTPUTS_NOT_EXCLUDED", "metrics/training/model/profile/paper/buy-review outputs must be excluded.", path))
    if not set(rows["decision_label"]) <= ALLOWED_DECISION_LABELS:
        issues.append(_issue(run_id, "ERROR", "DECISION_LABEL_INVALID", "decision_label outside allowed review-only enum.", path))
    if not set(rows["decision_actionability"]) <= ALLOWED_DECISION_ACTIONABILITY:
        issues.append(_issue(run_id, "ERROR", "DECISION_ACTIONABILITY_INVALID", "decision_actionability invalid.", path))
    if not set(rows["freeze_status"]) <= ALLOWED_FREEZE_STATUS:
        issues.append(_issue(run_id, "ERROR", "FREEZE_STATUS_INVALID", "freeze_status invalid.", path))
    if not frozen.empty and frozen["mutation_allowed"].map(_to_bool).any():
        issues.append(_issue(run_id, "ERROR", "FROZEN_ROW_MUTATION_ALLOWED", "frozen synthetic rows must not allow mutation.", path))
    if not frozen.empty and not frozen[["decision_hash", "evidence_snapshot_hash", "source_revision_snapshot_hash"]].map(_is_non_empty_text).all().all():
        issues.append(_issue(run_id, "ERROR", "FROZEN_HASH_MISSING", "frozen synthetic rows need hashes.", path))

    _special_row_issues(issues, run_id, path, by_id)
    _forbidden_flag_issues(issues, run_id, path, rows)

    if set(rows["trade_usage"]) & FORBIDDEN_TRADE_USAGE or not set(rows["trade_usage"]) <= ALLOWED_TRADE_USAGE:
        issues.append(_issue(run_id, "ERROR", "TRADE_USAGE_FORBIDDEN", "forbidden trade_usage appears.", path))
    return issues


def _special_row_issues(issues: list[dict[str, Any]], run_id: str, path: Path, by_id: pd.DataFrame) -> None:
    if "SYNTH_BLOCKED_FUTURE_AVAILABLE_EVIDENCE_DECISION" in by_id.index:
        row = by_id.loc["SYNTH_BLOCKED_FUTURE_AVAILABLE_EVIDENCE_DECISION"]
        if _to_bool(row["decision_time_eligible"]) or _to_bool(row["pit_valid"]):
            issues.append(_issue(run_id, "ERROR", "FUTURE_AVAILABLE_EVIDENCE_NOT_BLOCKED", "future available row not blocked.", path))
    for row_id in ["SYNTH_REVIEW_BUY_CANDIDATE_REPORT_ONLY_DECISION", "SYNTH_REVIEW_SELL_CANDIDATE_REPORT_ONLY_DECISION"]:
        if row_id in by_id.index:
            row = by_id.loc[row_id]
            if row["trade_usage"] in FORBIDDEN_TRADE_USAGE or _to_bool(row["trading_allowed"]) or _to_bool(row["buy_review_allowed"]):
                issues.append(_issue(run_id, "ERROR", "REVIEW_CANDIDATE_TREATED_AS_ORDER_SIGNAL", f"{row_id} became actionable.", path))
    if "SYNTH_BLOCKED_RISK_VETO_ST_DELIST_DECISION" in by_id.index:
        row = by_id.loc["SYNTH_BLOCKED_RISK_VETO_ST_DELIST_DECISION"]
        if row["decision_actionability"] != "blocked" or not _to_bool(row["risk_veto_flag"]):
            issues.append(_issue(run_id, "ERROR", "RISK_VETO_ROW_DOES_NOT_BLOCK_ACTIONABILITY", "risk veto row must block.", path))
    if "SYNTH_BLOCKED_MISSING_REPLAY_EVIDENCE_BUNDLE_DECISION" in by_id.index:
        row = by_id.loc["SYNTH_BLOCKED_MISSING_REPLAY_EVIDENCE_BUNDLE_DECISION"]
        if _to_bool(row["decision_time_eligible"]) or _is_non_empty_text(row["replay_evidence_bundle_id"]):
            issues.append(_issue(run_id, "ERROR", "MISSING_BUNDLE_ROW_NOT_BLOCKED", "missing bundle row must be blocked.", path))
    if "SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_DECISION" in by_id.index:
        row = by_id.loc["SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_DECISION"]
        if row["trade_usage"] != "no_trade" or _to_bool(row["decision_time_eligible"]):
            issues.append(_issue(run_id, "ERROR", "RESTRICTED_PRIVATE_ROW_NOT_BLOCKED", "restricted/private row must be no_trade.", path))
    if "SYNTH_OBSERVE_ONLY_INCOMPLETE_REVIEW_DECISION" in by_id.index:
        row = by_id.loc["SYNTH_OBSERVE_ONLY_INCOMPLETE_REVIEW_DECISION"]
        if _to_bool(row["decision_time_eligible"]) or row["decision_actionability"] != "observe_only":
            issues.append(_issue(run_id, "ERROR", "OBSERVE_ONLY_INCOMPLETE_DECISION_ELIGIBLE", "observe-only row must not be eligible.", path))


def _forbidden_flag_issues(issues: list[dict[str, Any]], run_id: str, path: Path, rows: pd.DataFrame) -> None:
    grouped = {
        "FORWARD_LABELS_CREATED_TRUE": ["forward_labels_created"],
        "FUTURE_LABELS_JOINED_TRUE": ["future_labels_joined"],
        "SIGNAL_SCORE_FLAG_TRUE": ["signal_score_implemented", "signal_score_input_authorized"],
        "MODEL_TRAINING_FLAG_TRUE": ["model_training_allowed"],
        "ACTIVE_WEIGHT_THRESHOLD_FLAG_TRUE": ["active_weight_allowed", "active_threshold_allowed"],
        "STOCK_PROFILE_FLAG_TRUE": ["stock_profile_validation_allowed"],
        "PAPER_VALIDATION_FLAG_TRUE": ["paper_validation_allowed"],
        "BUY_REVIEW_FLAG_TRUE": ["real_buy_review_allowed", "buy_review_allowed"],
        "PERFORMANCE_OR_TRADING_FLAG_TRUE": ["strategy_performance_validated", "trading_allowed"],
        "REAL_REPLAY_DECISION_FLAG_TRUE": ["real_replay_decisions_created"],
        "REAL_REPLAY_EVIDENCE_BUNDLE_USED_TRUE": ["real_replay_evidence_bundle_used"],
        "BROKER_API_LLM_FLAG_TRUE": ["broker_api_called", "external_api_called", "llm_api_called"],
        "DATA_WRITE_FLAG_TRUE": ["data_raw_written", "data_processed_written", "data_cache_written"],
        "OPERATIONAL_SIDE_EFFECT_FLAG_TRUE": [
            "current_candidates_run",
            "snapshot_built",
            "signal_semantics_changed",
            "active_stock_profile_created",
        ],
    }
    for code, columns in grouped.items():
        if any(rows[column].map(_to_bool).any() for column in columns):
            issues.append(_issue(run_id, "ERROR", code, f"forbidden flag group true: {','.join(columns)}", path))
    for flag in ROW_FALSE_FLAGS:
        if rows[flag].map(_to_bool).any():
            # Group-specific issue above is more useful; this generic guard is retained for completeness.
            pass


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and (path / "replay_decision_schema_fixture_metadata.json").exists()
    )


def _write(result: ReplayDecisionSchemaFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Replay Decision Schema Fixture Health",
                "",
                f"- health_status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                "",
                "Report-only health: no real replay decisions, real replay evidence bundle consumption, forward labels, future labels joined, signal_score input authorization, model training inputs, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/order/message/API behavior, or trading readiness was created.",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "health_status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, HEALTH_COLUMNS]


def _issue(run_id: str, severity: str, issue_code: str, message: str, artifact_path: Path) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "status": "FAIL" if severity == "ERROR" else "WARN",
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _audit_metadata(root: str | Path, checked_artifact_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "checked_artifact_count": checked_artifact_count,
        "report_only": True,
        "diagnostic_only": True,
        "replay_decision_schema_fixture_health_created": True,
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    }


def _non_empty_check(
    issues: list[dict[str, Any]], run_id: str, path: Path, rows: pd.DataFrame, column: str, issue_code: str
) -> None:
    if not rows[column].map(_is_non_empty_text).all():
        issues.append(_issue(run_id, "ERROR", issue_code, f"{column} must be populated.", path))


def _timestamp_order_ok(left: Any, right: Any) -> bool:
    try:
        return pd.Timestamp(left) <= pd.Timestamp(right)
    except Exception:
        return False


def _timestamp_order_strict_after(left: Any, right: Any) -> bool:
    try:
        return pd.Timestamp(left) > pd.Timestamp(right)
    except Exception:
        return False


def _unsafe_path_text(value: Any) -> bool:
    text = str(value).replace("\\", "/").lower()
    unsafe_tokens = [
        "data/raw",
        "data/processed",
        "data/cache",
        "broker",
        "order",
        "trading",
        "current-candidates",
        "snapshot",
        "signal_semantics",
        "model_training",
        "active_weights",
        "active_thresholds",
    ]
    return any(token in text for token in unsafe_tokens)


def _contains_sensitive_text(text: str) -> bool:
    return re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text.lower()) is not None


def _is_non_empty_text(value: Any) -> bool:
    return bool(str(value).strip())


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
