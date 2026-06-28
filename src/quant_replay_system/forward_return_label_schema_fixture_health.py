"""Health view for report-only forward return label schema fixture artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.forward_return_label_schema_fixture import (
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REQUIRED_FORWARD_RETURN_LABEL_FIELDS,
    ROW_FALSE_FLAGS,
)
from quant_replay_system.forward_return_label_schema_fixture_index import VIEW_DIR_NAMES


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]

REQUIRED_ARTIFACTS = {
    "metadata": "metadata.json",
    "report": "forward_return_label_schema_fixture_report.md",
    "fixture_rows": "forward_return_label_schema_fixture.csv",
    "case_matrix": "forward_return_label_case_matrix.csv",
    "field_contract": "forward_return_label_field_contract.csv",
    "validation_results": "forward_return_label_validation_results.csv",
    "leakage_guard_results": "forward_return_label_leakage_guard_results.csv",
    "safety_flags": "forward_return_label_safety_flags.json",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class ForwardReturnLabelSchemaFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_forward_return_label_schema_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/forward_return_label_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/forward_return_label_schema_fixture_v0_1/health",
) -> ForwardReturnLabelSchemaFixtureHealthResult:
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
        "health_csv": Path(output_dir) / "forward_return_label_schema_fixture_health.csv",
        "health_report": Path(output_dir) / "forward_return_label_schema_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ForwardReturnLabelSchemaFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if Path(root).exists() else [f"Forward return label schema fixture root does not exist: {root}"],
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
        run_id = _text(metadata.get("forward_return_label_schema_fixture_id")) or run_id
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
    if paths["field_contract"].exists():
        issues.extend(_field_contract_issues(run_id, paths["field_contract"]))
    if paths["fixture_rows"].exists():
        issues.extend(_fixture_row_issues(run_id, paths["fixture_rows"]))
    if paths["safety_flags"].exists():
        issues.extend(_safety_flags_issues(run_id, paths["safety_flags"]))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], metadata_path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    status = _text(metadata.get("status"))
    if status not in {"PASS", "WARN", "FAIL", "NO_INPUT"}:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_STATUS", f"Unknown fixture status: {status}", metadata_path))
    if status != "PASS":
        issues.append(_issue(run_id, "ERROR", "FIXTURE_STATUS_NOT_PASS", "Fixture metadata status is not PASS.", metadata_path))
    if _text(metadata.get("workflow_stage")) != "FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED":
        issues.append(_issue(run_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", metadata_path))
    if _to_int(metadata.get("label_count")) != 10:
        issues.append(_issue(run_id, "ERROR", "LABEL_COUNT_NOT_10", "label_count must be 10.", metadata_path))
    if _to_int(metadata.get("validation_issue_count")) != 0:
        issues.append(_issue(run_id, "ERROR", "VALIDATION_ISSUE_COUNT_NOT_ZERO", "validation_issue_count must be 0.", metadata_path))
    if not _to_bool(metadata.get("report_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_REPORT_ONLY_NOT_TRUE", "metadata report_only is not true.", metadata_path))
    if not _to_bool(metadata.get("diagnostic_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_DIAGNOSTIC_ONLY_NOT_TRUE", "metadata diagnostic_only is not true.", metadata_path))
    if not _to_bool(metadata.get("schema_fixture")):
        issues.append(_issue(run_id, "ERROR", "METADATA_SCHEMA_FIXTURE_NOT_TRUE", "metadata schema_fixture is not true.", metadata_path))
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{flag} is true.", metadata_path))
    for key, value in (metadata.get("artifact_paths") or {}).items():
        if _unsafe_path_text(value):
            issues.append(_issue(run_id, "ERROR", "UNSAFE_ARTIFACT_PATH", f"Unsafe artifact path for {key}: {value}", metadata_path))
    return issues


def _field_contract_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        fields = pd.read_csv(path, dtype=str)
    except Exception as exc:
        return [_issue(run_id, "ERROR", "FIELD_CONTRACT_UNREADABLE", f"Field contract cannot be read: {exc}", path)]
    if "field_name" not in fields.columns:
        return [_issue(run_id, "ERROR", "FIELD_CONTRACT_REQUIRED_FIELDS_MISSING", "field contract missing field_name column.", path)]
    missing = sorted(set(REQUIRED_FORWARD_RETURN_LABEL_FIELDS) - set(fields["field_name"].dropna().astype(str)))
    if missing:
        return [
            _issue(
                run_id,
                "ERROR",
                "FIELD_CONTRACT_REQUIRED_FIELDS_MISSING",
                f"field contract missing required field names: {','.join(missing)}",
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
    missing = sorted(set(REQUIRED_FORWARD_RETURN_LABEL_FIELDS) - set(rows.columns))
    if missing:
        issues.append(
            _issue(run_id, "ERROR", "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING", f"fixture rows missing required columns: {','.join(missing)}", path)
        )
        return issues

    all_text = " ".join(rows.astype(str).agg(" ".join, axis=1))
    complete = rows[rows["label_status"] == "COMPLETE"]
    if _contains_sensitive_text(all_text):
        issues.append(_issue(run_id, "ERROR", "SENSITIVE_TEXT_DETECTED", "token/secret-looking text appears in fixture rows.", path))
    if len(rows) != 10:
        issues.append(_issue(run_id, "ERROR", "LABEL_COUNT_NOT_10", "forward return label fixture must contain exactly 10 rows.", path))
    if not rows["forward_return_label_id"].is_unique:
        issues.append(_issue(run_id, "ERROR", "FORWARD_RETURN_LABEL_ID_NOT_UNIQUE", "forward_return_label_id must be unique.", path))
    if "000001" not in set(rows["symbol"].astype(str)):
        issues.append(_issue(run_id, "ERROR", "LEADING_ZERO_SYMBOL_MISSING", "leading-zero synthetic symbol 000001 must be preserved.", path))
    if not (rows["replay_decision_workflow_stage"] == "REPLAY_DECISION_SCHEMA_FIXTURE_CREATED").all():
        issues.append(_issue(run_id, "ERROR", "REPLAY_DECISION_STAGE_INVALID", "replay decision fixture lineage stage invalid.", path))
    if not complete.empty and not complete.apply(lambda row: _timestamp_strict_after(row["window_start_date"], row["replay_decision_time"]), axis=1).all():
        issues.append(_issue(run_id, "ERROR", "COMPLETE_WINDOW_START_NOT_AFTER_DECISION_TIME", "complete label windows must start after replay decision time.", path))
    if not complete.empty and not complete.apply(lambda row: _timestamp_strict_after(row["window_end_date"], row["window_start_date"]), axis=1).all():
        issues.append(_issue(run_id, "ERROR", "COMPLETE_WINDOW_END_NOT_AFTER_START", "complete label windows must end after start.", path))
    _special_case_issues(issues, run_id, path, rows.set_index("schema_fixture_case_id", drop=False))
    _forbidden_flag_issues(issues, run_id, path, rows)
    return issues


def _special_case_issues(issues: list[dict[str, Any]], run_id: str, path: Path, by_case: pd.DataFrame) -> None:
    if "SYNTH_BLOCKED_NOT_FROZEN_DECISION_LABEL" in by_case.index:
        row = by_case.loc["SYNTH_BLOCKED_NOT_FROZEN_DECISION_LABEL"]
        if row["label_status"] != "BLOCKED" or _to_bool(row["replay_decision_frozen"]):
            issues.append(_issue(run_id, "ERROR", "NOT_FROZEN_CASE_NOT_BLOCKED", "not-frozen decision case must be blocked.", path))
    if "SYNTH_BLOCKED_MISSING_EXIT_PRICE_LABEL" in by_case.index:
        row = by_case.loc["SYNTH_BLOCKED_MISSING_EXIT_PRICE_LABEL"]
        if row["label_completeness_status"] != "MISSING_EXIT_PRICE" or row["exit_price"]:
            issues.append(_issue(run_id, "ERROR", "MISSING_EXIT_PRICE_CASE_NOT_BLOCKED", "missing exit price case must be blocked.", path))
    if "SYNTH_BLOCKED_INVALID_WINDOW_LABEL" in by_case.index:
        row = by_case.loc["SYNTH_BLOCKED_INVALID_WINDOW_LABEL"]
        if row["label_completeness_status"] != "INVALID_WINDOW" or _to_bool(row["window_valid"]):
            issues.append(_issue(run_id, "ERROR", "INVALID_WINDOW_CASE_NOT_BLOCKED", "invalid window case must be blocked.", path))
    if "SYNTH_EXECUTION_BLOCKED_SUSPENSION_LABEL" in by_case.index:
        row = by_case.loc["SYNTH_EXECUTION_BLOCKED_SUSPENSION_LABEL"]
        if row["execution_blocker_type"] != "SUSPENSION" or not _to_bool(row["suspended_during_window"]):
            issues.append(_issue(run_id, "ERROR", "SUSPENSION_CASE_MISSING_BLOCKER", "suspension case must have blocker.", path))
    if "SYNTH_PARTIAL_BENCHMARK_OR_INDUSTRY_LABEL" in by_case.index:
        row = by_case.loc["SYNTH_PARTIAL_BENCHMARK_OR_INDUSTRY_LABEL"]
        if row["label_status"] != "PARTIAL" or _to_bool(row["relative_label_available"]):
            issues.append(_issue(run_id, "ERROR", "PARTIAL_RELATIVE_CASE_NOT_PARTIAL", "partial relative case must remain partial.", path))


def _forbidden_flag_issues(issues: list[dict[str, Any]], run_id: str, path: Path, rows: pd.DataFrame) -> None:
    grouped = {
        "REAL_FORWARD_LABEL_FLAG_TRUE": ["real_forward_label_created"],
        "FUTURE_LABEL_JOIN_FLAG_TRUE": ["future_label_joined_to_decision_input"],
        "SIGNAL_SCORE_FLAG_TRUE": ["signal_score_input_authorized"],
        "MODEL_TRAINING_FLAG_TRUE": ["model_training_input_authorized"],
        "STOCK_PROFILE_FLAG_TRUE": ["stock_profile_input_authorized"],
        "PAPER_VALIDATION_FLAG_TRUE": ["paper_validation_created"],
        "BUY_REVIEW_FLAG_TRUE": ["buy_review_allowed", "real_buy_review_allowed"],
        "PERFORMANCE_OR_TRADING_FLAG_TRUE": ["strategy_performance_validated", "trading_allowed"],
    }
    for code, columns in grouped.items():
        if any(rows[column].map(_to_bool).any() for column in columns):
            issues.append(_issue(run_id, "ERROR", code, f"forbidden flag group true: {','.join(columns)}", path))
    for flag in ROW_FALSE_FLAGS:
        if rows[flag].map(_to_bool).any() and not any(flag in columns for columns in grouped.values()):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_ROW_FLAG_TRUE", f"{flag} is true.", path))


def _safety_flags_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        flags = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [_issue(run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", f"safety flags cannot be read: {exc}", path)]
    return [
        _issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{flag} is true.", path)
        for flag in FORBIDDEN_METADATA_FALSE_FLAGS
        if _to_bool(flags.get(flag))
    ]


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and _looks_like_fixture_dir(path)
    )


def _looks_like_fixture_dir(path: Path) -> bool:
    metadata_path = path / "metadata.json"
    if not metadata_path.exists():
        return False
    if (path / "forward_return_label_schema_fixture.csv").exists():
        return True
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return bool(
        metadata.get("forward_return_label_schema_fixture_id")
        or metadata.get("workflow_name") == "forward_return_label_schema_fixture"
    )


def _write(result: ForwardReturnLabelSchemaFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Forward Return Label Schema Fixture Health",
                "",
                f"- health_status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                "",
                "Report-only health: no real forward labels, future-label joins, signal_score inputs, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/order/message/API behavior, or trading readiness was created.",
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
        "forward_return_label_schema_fixture_health_created": True,
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    }


def _timestamp_strict_after(left: Any, right: Any) -> bool:
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
        "docs/project_sources",
        "current-candidates",
        "snapshot",
        "signal_semantics",
        "model_training",
        "active_weights",
        "active_thresholds",
        "broker",
        "order",
        "trading",
    ]
    return any(token in text for token in unsafe_tokens)


def _contains_sensitive_text(text: str) -> bool:
    return re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text.lower()) is not None


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
