"""Health checks for report-only forward return label artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.forward_return_label import (
    FORWARD_RETURN_LABELS_CREATED,
    FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED,
    FORWARD_RETURN_LABEL_BENCHMARK_BLOCKED,
    FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED,
    FORWARD_RETURN_LABEL_INDUSTRY_BLOCKED,
    FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED,
    FORWARD_RETURN_LABEL_LINEAGE_BLOCKED,
    FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED,
    FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED,
    FORWARD_RETURN_LABEL_REVIEW_BLOCKED,
    FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED,
    FORWARD_RETURN_LABEL_WINDOW_BLOCKED,
    NO_FORWARD_RETURN_LABEL_INPUT,
    READY_FOR_FORWARD_RETURN_LABEL,
)
from quant_replay_system.forward_return_label_index import DEFAULT_ROOT, build_forward_return_label_index


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["forward_return_label_run_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_FORWARD_RETURN_LABEL_INPUT,
    FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED,
    FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED,
    FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED,
    FORWARD_RETURN_LABEL_WINDOW_BLOCKED,
    FORWARD_RETURN_LABEL_BENCHMARK_BLOCKED,
    FORWARD_RETURN_LABEL_INDUSTRY_BLOCKED,
    FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED,
    FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED,
    FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED,
    FORWARD_RETURN_LABEL_LINEAGE_BLOCKED,
    FORWARD_RETURN_LABEL_REVIEW_BLOCKED,
    READY_FOR_FORWARD_RETURN_LABEL,
    FORWARD_RETURN_LABELS_CREATED,
}
ALLOWED_LABEL_NAMES = {
    "forward_return_1d",
    "forward_return_3d",
    "forward_return_5d",
    "forward_return_10d",
    "forward_return_20d",
    "max_drawdown_5d",
    "max_drawdown_20d",
    "max_runup_5d",
    "max_runup_20d",
    "benchmark_relative_return_5d",
    "industry_relative_return_5d",
}
REQUIRED_LABEL_COLUMNS = {
    "forward_return_label_run_id",
    "replay_decision_id",
    "replay_decision_freeze_run_id",
    "actual_replay_execution_run_id",
    "source_active_input_creation_run_id",
    "source_real_replay_precheck_run_id",
    "symbol",
    "replay_as_of_date",
    "label_name",
    "label_start_date",
    "label_end_date",
    "price_source_id",
    "price_source_hash",
    "price_revision_id",
    "price_available_time",
    "price_quality_status",
}
FORBIDDEN_COLUMN_GROUPS = [
    ("LABEL_ROWS_FORBIDDEN_TRAINING_COLUMNS", {"training", "feature_importance", "threshold_optimized"}),
    ("LABEL_ROWS_FORBIDDEN_MODEL_COLUMNS", {"model_weight", "model_version"}),
    ("LABEL_ROWS_FORBIDDEN_STOCK_PROFILE_COLUMNS", {"stock_profile"}),
    ("LABEL_ROWS_FORBIDDEN_BUY_REVIEW_COLUMNS", {"buy_review", "real_buy_review_eligible"}),
    ("LABEL_ROWS_FORBIDDEN_PAPER_APPROVAL_COLUMNS", {"approved_for_paper"}),
    ("LABEL_ROWS_FORBIDDEN_PERFORMANCE_COLUMNS", {"strategy_performance_validated", "performance_validation"}),
    ("LABEL_ROWS_FORBIDDEN_TRADING_COLUMNS", {"order", "broker", "trade_id"}),
]
UNSAFE_FALSE_FIELDS = [
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
    "strategy_performance_validated",
    "trading_allowed",
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
]


@dataclass(frozen=True)
class ForwardReturnLabelHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_forward_return_label_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ForwardReturnLabelHealthResult:
    index = build_forward_return_label_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_FORWARD_RETURN_LABEL_ARTIFACT_FOUND", "No forward return label artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "forward_return_label_health.csv",
        "health_report": Path(output_dir) / "forward_return_label_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ForwardReturnLabelHealthResult(
        status=status,
        checked_artifact_count=len(index.index_frame),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=index.warnings,
        audit_metadata={"root": str(root), "checked_artifact_count": len(index.index_frame), "report_only": True, "diagnostic_only": True},
    )
    _write(result)
    return result


def _issues_for_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    run_id = _text(row.get("forward_return_label_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata_path = Path(_text(row.get("metadata_path")))
    rows_path = Path(_text(row.get("forward_return_label_rows_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []

    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    for path, code in [
        (metadata_path, "MISSING_METADATA"),
        (Path(_text(row.get("report_path"))), "MISSING_REPORT"),
        (Path(_text(row.get("safety_flags_path"))), "MISSING_SAFETY_FLAGS"),
        (Path(_text(row.get("forward_return_label_price_input_index_path"))), "MISSING_PRICE_INPUT_INDEX"),
        (Path(_text(row.get("forward_return_label_benchmark_index_path"))), "MISSING_BENCHMARK_INDEX"),
        (Path(_text(row.get("forward_return_label_industry_index_path"))), "MISSING_INDUSTRY_INDEX"),
    ]:
        if not _text(path) or not path.exists():
            issues.append(_issue(run_id, "ERROR", code, f"Required forward return label artifact missing: {path}", path))

    if status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_FORWARD_RETURN_LABEL_STATUS", f"Unknown status: {status}", metadata_path))

    rows_exist = rows_path.exists()
    rows = _read_csv(rows_path) if rows_exist else pd.DataFrame()
    if status == FORWARD_RETURN_LABELS_CREATED:
        if not rows_exist or rows.empty:
            issues.append(_issue(run_id, "ERROR", "LABELS_CREATED_WITHOUT_ROWS", "FORWARD_RETURN_LABELS_CREATED requires non-empty forward_return_label_rows.csv.", rows_path))
    elif rows_exist and not rows.empty:
        issues.append(_issue(run_id, "ERROR", "ROWS_EXIST_WITHOUT_LABELS_CREATED_STATUS", "Forward label rows can exist only with FORWARD_RETURN_LABELS_CREATED status.", rows_path))

    if rows_exist and not rows.empty:
        issues.extend(_label_row_issues(run_id, rows_path, rows))

    for field in UNSAFE_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", metadata_path))
    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "UNSAFE_REPORT_ONLY_FLAGS", f"Missing or false flag: {field}", metadata_path))
    return issues


def _label_row_issues(run_id: str, path: Path, frame: pd.DataFrame) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    missing = sorted(REQUIRED_LABEL_COLUMNS - set(frame.columns))
    if missing:
        issues.append(_issue(run_id, "ERROR", "LABEL_ROWS_REQUIRED_COLUMNS_MISSING", f"Label rows missing required columns: {','.join(missing)}", path))
    if "label_name" in frame.columns:
        invalid = sorted(set(str(value) for value in frame["label_name"].dropna()) - ALLOWED_LABEL_NAMES)
        if invalid:
            issues.append(_issue(run_id, "ERROR", "LABEL_NAME_OUTSIDE_ALLOWED_SET", f"Label names outside allowed set: {','.join(invalid)}", path))
    lower_columns = {column.lower() for column in frame.columns}
    for code, tokens in FORBIDDEN_COLUMN_GROUPS:
        matched = sorted(column for column in lower_columns if any(token in column for token in tokens))
        if matched:
            issues.append(_issue(run_id, "ERROR", code, f"Forbidden columns in label rows: {','.join(matched)}", path))
    return issues


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Forward return label artifacts must remain under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype={"symbol": "string"})
    except Exception:
        return pd.DataFrame()


def _issue(run_id: str, severity: str, code: str, message: str, path: str | Path) -> dict[str, Any]:
    return {
        "forward_return_label_run_id": run_id,
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[HEALTH_COLUMNS]


def _write(result: ForwardReturnLabelHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "health_id": _hash_payload(result.health_frame.to_dict("records")),
                "status": result.status,
                "checked_artifact_count": result.checked_artifact_count,
                "issue_count": result.issue_count,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "warnings": result.warnings,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Forward Return Label Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "Health keeps forward labels report-only and fails if artifacts imply training, training_result, stock_profile, buy-review, paper approval, performance validation, broker/order/message/API/cache/data side effects, snapshots, current-candidates, signal semantics mutation, or trading.",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No health issues found.",
            ]
        ),
        encoding="utf-8",
    )


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
