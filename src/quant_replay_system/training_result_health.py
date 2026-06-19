"""Health checks for report-only actual training_result phase 1 artifacts."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.training_result import (
    DOWNSTREAM_FALSE_FIELDS,
    NO_TRAINING_RESULT_INPUT,
    READY_FOR_TRAINING_RESULT,
    TRAINING_RESULT_CREATED,
)
from quant_replay_system.training_result_index import DEFAULT_ROOT, build_training_result_index
from quant_replay_system.training_result_index import _read_csv, _text, _to_bool


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"
HEALTH_COLUMNS = ["training_result_run_id", "severity", "issue_code", "message", "artifact_path"]

ALLOWED_STATUSES = {
    NO_TRAINING_RESULT_INPUT,
    READY_FOR_TRAINING_RESULT,
    TRAINING_RESULT_CREATED,
    "TRAINING_RESULT_INPUT_FOUND",
    "TRAINING_RESULT_APPROVAL_BLOCKED",
    "TRAINING_RESULT_PLANNING_INPUT_BLOCKED",
    "TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED",
    "TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED",
    "TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED",
    "TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED",
    "TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED",
    "TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED",
    "TRAINING_RESULT_HEALTH_BLOCKED",
    "TRAINING_RESULT_LINEAGE_BLOCKED",
    "TRAINING_RESULT_METRIC_EVIDENCE_BLOCKED",
    "TRAINING_RESULT_LIMITATIONS_BLOCKED",
    "TRAINING_RESULT_OVERFIT_WARNING_BLOCKED",
    "TRAINING_RESULT_REPORT_ONLY_BLOCKED",
    "TRAINING_RESULT_FORBIDDEN_ARTIFACT_BLOCKED",
    "TRAINING_RESULT_LEAKAGE_BLOCKED",
    "TRAINING_RESULT_SIDE_EFFECT_BLOCKED",
    "TRAINING_RESULT_OVERCLAIM_BLOCKED",
}

CREATED_REQUIRED_PATH_CODES = {
    "metadata_path": "MISSING_METADATA",
    "rows_path": "MISSING_ROWS",
    "status_json_path": "MISSING_STATUS",
    "input_index_path": "MISSING_INPUT_INDEX",
    "metric_evidence_reference_path": "MISSING_METRIC_EVIDENCE_REFERENCE",
    "lineage_matrix_path": "MISSING_LINEAGE_MATRIX",
    "limitations_path": "MISSING_LIMITATIONS",
    "overfit_warnings_path": "MISSING_OVERFIT_WARNINGS",
    "safety_flags_path": "MISSING_SAFETY_FLAGS",
}

ALWAYS_REQUIRED_PATH_CODES = {
    "metadata_path": "MISSING_METADATA",
    "report_path": "MISSING_REPORT",
    "status_json_path": "MISSING_STATUS",
    "safety_flags_path": "MISSING_SAFETY_FLAGS",
}

REQUIRED_METRIC_EVIDENCE = {
    "sample_count",
    "label_coverage",
    "average_return",
    "median_return",
    "hit_rate",
    "benchmark_relative_return",
    "industry_relative_return",
}

LINEAGE_REQUIRED_COLUMNS = {
    "source_run_id",
    "available_time_coverage",
    "source_hash_coverage",
    "revision_id_coverage",
    "quality_status_coverage",
}

INPUT_INDEX_REQUIRED_COLUMNS = {"source_run_id", "health_status"}

FORBIDDEN_ROW_TOKENS = {
    "model_weight",
    "model_weights",
    "weights",
    "model_version",
    "parameter_version",
    "threshold",
    "prediction",
    "probability",
    "calibrated_probability",
    "feature_importance",
    "calibration_report",
    "validation_report",
    "performance_validation",
    "stock_profile",
    "buy_review",
    "paper_approval",
    "approved_for_paper",
    "order_id",
    "broker_order_id",
    "trade_id",
}

FORBIDDEN_ARTIFACT_PATTERNS = {
    "model_weight*",
    "model_weights*",
    "weights*",
    "model_version*",
    "parameter_version*",
    "threshold*",
    "prediction*",
    "probability*",
    "calibrated_probability*",
    "feature_importance*",
    "calibration_report*",
    "validation_report*",
    "performance_validation*",
    "stock_profile*",
    "buy_review*",
    "paper_approval*",
    "broker*",
    "order*",
    "trade*",
}

LIMITATION_PHRASES = [
    "report-only actual training_result artifacts",
    "not weights",
    "not model_version",
    "not parameter_version",
    "not thresholds",
    "not predictions/probabilities/feature importance",
    "not stock_profile",
    "not buy-review",
    "not paper approval",
    "not performance validation",
    "not trading",
]

REQUIRED_OVERFIT_WARNINGS = {
    "small sample",
    "class imbalance",
    "single-stock overfit",
    "metric selection bias",
    "lookahead leakage",
}

POSITIVE_OVERCLAIM_PHRASES = [
    "strategy performance validated",
    "strategy validation passed",
    "validates profitability",
    "profitability proof",
    "stock-profile readiness",
    "buy-review readiness",
    "paper approval granted",
    "trading permission",
    "trained weights",
    "created model_version",
    "optimized thresholds",
    "generated predictions",
]


@dataclass(frozen=True)
class TrainingResultHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_training_result_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> TrainingResultHealthResult:
    index = build_training_result_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_TRAINING_RESULT_ARTIFACT_FOUND", "No training_result artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues, dtype=object))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "training_result_health.csv",
        "health_report": Path(output_dir) / "training_result_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = TrainingResultHealthResult(
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
    run_id = _text(row.get("training_result_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []
    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    if status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_TRAINING_RESULT_STATUS", f"Unknown status: {status}", artifact_path))
    for field, code in ALWAYS_REQUIRED_PATH_CODES.items():
        _require_path(run_id, Path(_text(row.get(field))), code, issues)
    _forbidden_artifact_issues(run_id, artifact_path, issues)
    _created_state_issues(row, issues)
    if status == TRAINING_RESULT_CREATED:
        for field, code in CREATED_REQUIRED_PATH_CODES.items():
            _require_path(run_id, Path(_text(row.get(field))), code, issues)
        if _to_int(row.get("training_result_row_count")) <= 0:
            issues.append(_issue(run_id, "ERROR", "TRAINING_RESULT_ROWS_EMPTY", "TRAINING_RESULT_CREATED requires at least one report-only training_result row.", artifact_path))
        if not _to_bool(row.get("limitations_created")):
            issues.append(_issue(run_id, "ERROR", "LIMITATIONS_FLAG_FALSE", "limitations_created must be true for TRAINING_RESULT_CREATED.", artifact_path))
        if not _to_bool(row.get("overfit_warnings_created")):
            issues.append(_issue(run_id, "ERROR", "OVERFIT_WARNINGS_FLAG_FALSE", "overfit_warnings_created must be true for TRAINING_RESULT_CREATED.", artifact_path))
        issues.extend(_metric_evidence_issues(run_id, Path(_text(row.get("metric_evidence_reference_path")))))
        issues.extend(_input_index_issues(run_id, Path(_text(row.get("input_index_path")))))
        issues.extend(_lineage_issues(run_id, Path(_text(row.get("lineage_matrix_path")))))
        issues.extend(_training_result_row_issues(run_id, Path(_text(row.get("rows_path")))))
        issues.extend(_limitations_issues(run_id, Path(_text(row.get("limitations_path")))))
        issues.extend(_overfit_warning_issues(run_id, Path(_text(row.get("overfit_warnings_path")))))
    issues.extend(_report_wording_issues(run_id, Path(_text(row.get("report_path")))))
    for field in DOWNSTREAM_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", artifact_path))
    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "REPORT_ONLY_FLAGS_MISSING", f"Missing or false flag: {field}", artifact_path))
    return issues


def _created_state_issues(row: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    run_id = _text(row.get("training_result_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    status = _text(row.get("status"))
    created = _to_bool(row.get("training_result_created"))
    if status == TRAINING_RESULT_CREATED and not created:
        issues.append(_issue(run_id, "ERROR", "TRAINING_RESULT_CREATED_FLAG_FALSE", "training_result_created must be true for TRAINING_RESULT_CREATED.", artifact_path))
    if status in {NO_TRAINING_RESULT_INPUT, READY_FOR_TRAINING_RESULT} and created:
        issues.append(_issue(run_id, "ERROR", "TRAINING_RESULT_CREATED_UNEXPECTED", "training_result_created must remain false before TRAINING_RESULT_CREATED.", artifact_path))


def _metric_evidence_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    issues: list[dict[str, Any]] = []
    columns = set(rows.columns)
    if "metric_name" not in columns:
        return [_issue(run_id, "ERROR", "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING", "metric evidence requires metric_name.", path)]
    missing = sorted(REQUIRED_METRIC_EVIDENCE - set(rows["metric_name"].dropna().astype(str)))
    if missing:
        issues.append(_issue(run_id, "ERROR", "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING", f"Missing metric evidence: {','.join(missing)}", path))
    if "forbidden_interpretation" not in columns or not ({"accepted_interpretation", "permitted_interpretation"} & columns):
        issues.append(_issue(run_id, "ERROR", "METRIC_EVIDENCE_INTERPRETATION_MISSING", "Metric evidence requires permitted/accepted and forbidden interpretations.", path))
    text = " ".join(rows.astype(str).fillna("").agg(" ".join, axis=1).str.lower())
    if _contains_positive_overclaim(text):
        issues.append(_issue(run_id, "ERROR", "METRIC_EVIDENCE_OVERCLAIM", "Metric evidence contains strategy validation or profitability proof wording.", path))
    return issues


def _input_index_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    missing = INPUT_INDEX_REQUIRED_COLUMNS - set(rows.columns)
    if missing:
        return [_issue(run_id, "ERROR", "INPUT_INDEX_LINEAGE_MISSING", f"Input index missing columns: {','.join(sorted(missing))}", path)]
    if rows["source_run_id"].fillna("").astype(str).str.strip().eq("").any():
        return [_issue(run_id, "ERROR", "INPUT_INDEX_LINEAGE_MISSING", "Input index has blank source_run_id.", path)]
    return []


def _lineage_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    missing = LINEAGE_REQUIRED_COLUMNS - set(rows.columns)
    if missing:
        return [_issue(run_id, "ERROR", "LINEAGE_COVERAGE_MISSING", f"Lineage matrix missing columns: {','.join(sorted(missing))}", path)]
    for column in LINEAGE_REQUIRED_COLUMNS:
        if rows[column].fillna("").astype(str).str.strip().eq("").any():
            return [_issue(run_id, "ERROR", "LINEAGE_COVERAGE_MISSING", f"Lineage matrix has blank values in {column}.", path)]
    return []


def _training_result_row_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty:
        return []
    forbidden_columns = [column for column in rows.columns if _forbidden_row_column(column)]
    if forbidden_columns:
        return [_issue(run_id, "ERROR", "TRAINING_RESULT_ROW_FORBIDDEN_FIELD", f"Training result rows include forbidden fields: {','.join(forbidden_columns)}", path)]
    return []


def _limitations_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").lower()
    missing = [phrase for phrase in LIMITATION_PHRASES if phrase not in text]
    if missing:
        return [_issue(run_id, "ERROR", "LIMITATIONS_WORDING_MISSING", f"Limitations missing phrases: {','.join(missing)}", path)]
    return []


def _overfit_warning_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if rows.empty or "risk_item" not in rows.columns:
        return []
    missing = REQUIRED_OVERFIT_WARNINGS - set(rows["risk_item"].dropna().astype(str))
    if missing:
        return [_issue(run_id, "ERROR", "OVERFIT_WARNING_MISSING", f"Overfit warnings missing: {','.join(sorted(missing))}", path)]
    return []


def _report_wording_issues(run_id: str, report_path: Path) -> list[dict[str, Any]]:
    if not report_path.exists():
        return []
    text = report_path.read_text(encoding="utf-8").lower()
    if _contains_positive_overclaim(text):
        return [_issue(run_id, "ERROR", "REPORT_OVERCLAIM_WORDING", "Report contains model/performance/trading overclaim wording.", report_path)]
    return []


def _contains_positive_overclaim(text: str) -> bool:
    normalized = text.lower()
    for safe_phrase in [
        "not profitability proof",
        "not strategy performance validation",
        "not trading permission",
        "not model weights",
        "not predictions",
        "not weights",
        "not model_version",
        "not parameter_version",
        "not thresholds",
        "not stock_profile",
        "not buy-review",
        "not paper approval",
        "not performance validation",
        "not trading",
    ]:
        normalized = normalized.replace(safe_phrase, "")
    return any(phrase in normalized for phrase in POSITIVE_OVERCLAIM_PHRASES)


def _forbidden_row_column(column: str) -> bool:
    name = column.lower()
    return any(token in name for token in FORBIDDEN_ROW_TOKENS)


def _forbidden_artifact_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    for child in (artifact_path.iterdir() if artifact_path.exists() else []):
        name = child.name.lower()
        if any(fnmatch.fnmatch(name, pattern) for pattern in FORBIDDEN_ARTIFACT_PATTERNS):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_ARTIFACT_PRESENT", f"Forbidden training/model/trading artifact present: {child.name}", child))


def _require_path(run_id: str, path: Path, code: str, issues: list[dict[str, Any]]) -> None:
    if not _text(path) or not path.exists():
        issues.append(_issue(run_id, "ERROR", code, f"Required actual training_result artifact missing: {path}", path))


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = {part.lower() for part in artifact_path.parts}
    if "outputs" not in parts or "reports" not in parts or "manual_diagnostics" not in parts:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Training result artifacts must remain under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: TrainingResultHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "health_id": _hash_payload(result.health_frame.to_dict("records")),
                "status": result.status,
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
                "# Actual Training Result Health",
                "",
                "Report-only health for actual training_result phase 1 artifacts. It fails if outputs imply weights, model_version, parameter_version, thresholds, predictions, calibrated probabilities, feature importance, stock_profile, buy-review, paper approval, performance validation, broker/order/message/API/cache/data side effects, current-candidates, snapshots, signal semantics mutation, or trading.",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues found.",
            ]
        ),
        encoding="utf-8",
    )


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[HEALTH_COLUMNS].copy()


def _issue(run_id: str, severity: str, issue_code: str, message: str, artifact_path: str | Path) -> dict[str, Any]:
    return {
        "training_result_run_id": run_id,
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _to_int(value: Any) -> int:
    try:
        if value is None or value == "" or pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
