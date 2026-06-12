"""Health checks for report-only historical replay input gate validator fixtures."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.historical_replay_input_gate_validator_fixture import ACTIVE_REPLAY_INPUT_READY
from quant_replay_system.historical_replay_input_gate_validator_fixture_index import (
    build_historical_replay_input_gate_validator_fixture_index,
)


HEALTH_COLUMNS = ["fixture_run_id", "severity", "issue_code", "message", "artifact_path"]


@dataclass(frozen=True)
class HistoricalReplayInputGateValidatorFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_historical_replay_input_gate_validator_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/health",
) -> HistoricalReplayInputGateValidatorFixtureHealthResult:
    index = build_historical_replay_input_gate_validator_fixture_index(
        root=root, output_dir=Path(output_dir).parent / "index"
    )
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_FIXTURE_FOUND", "No fixture artifacts found.", root))
    else:
        latest = index.index_frame.sort_values(["generated_at", "fixture_run_id"]).iloc[-1].to_dict()
        issues.extend(_issues_for_latest(latest))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "historical_replay_input_gate_validator_fixture_health.csv",
        "health_report": Path(output_dir) / "historical_replay_input_gate_validator_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = HistoricalReplayInputGateValidatorFixtureHealthResult(
        status=status,
        checked_artifact_count=len(index.index_frame),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=index.warnings,
        audit_metadata=_audit_metadata(root, len(index.index_frame)),
    )
    _write(result)
    return result


def _issues_for_latest(row: dict[str, Any]) -> list[dict[str, Any]]:
    fixture_run_id = _text(row.get("fixture_run_id"))
    metadata_path = Path(_text(row.get("metadata_path")))
    artifact_path = Path(_text(row.get("artifact_path")))
    fixture_cases_path = Path(_text(row.get("fixture_cases_path")))
    issues: list[dict[str, Any]] = []

    for path, code in [
        (metadata_path, "MISSING_METADATA"),
        (fixture_cases_path, "MISSING_FIXTURE_CASES"),
        (Path(_text(row.get("blocked_requirements_path"))), "MISSING_BLOCKED_REQUIREMENTS"),
        (Path(_text(row.get("expected_status_matrix_path"))), "MISSING_EXPECTED_STATUS_MATRIX"),
        (Path(_text(row.get("fixture_input_schema_path"))), "MISSING_FIXTURE_INPUT_SCHEMA"),
        (Path(_text(row.get("overclaim_guard_report_path"))), "MISSING_OVERCLAIM_GUARD_REPORT"),
        (Path(_text(row.get("report_path"))), "MISSING_REPORT"),
    ]:
        if not _text(path) or not path.exists():
            issues.append(_issue(fixture_run_id, "ERROR", code, f"Required artifact missing: {path}", path))

    if _text(row.get("status")) != "PASS":
        issues.append(_issue(fixture_run_id, "ERROR", "LATEST_FIXTURE_NOT_PASS", "Latest fixture status is not PASS.", metadata_path))
    if _to_int(row.get("case_count")) != 68:
        issues.append(_issue(fixture_run_id, "ERROR", "CASE_COUNT_MISMATCH", "case_count must be 68.", metadata_path))
    if _to_int(row.get("blocked_case_count")) != 67:
        issues.append(_issue(fixture_run_id, "ERROR", "BLOCKED_CASE_COUNT_MISMATCH", "blocked_case_count must be 67.", metadata_path))
    if _to_int(row.get("pass_candidate_case_count")) != 1:
        issues.append(_issue(fixture_run_id, "ERROR", "PASS_CANDIDATE_COUNT_MISMATCH", "pass_candidate_case_count must be 1.", metadata_path))
    if _to_int(row.get("active_ready_case_count")) != 0:
        issues.append(_issue(fixture_run_id, "ERROR", "ACTIVE_READY_CASE_PRESENT", "active_ready_case_count must be 0.", metadata_path))
    if _to_int(row.get("validation_issue_count")) != 0:
        issues.append(_issue(fixture_run_id, "ERROR", "VALIDATION_ISSUES_PRESENT", "validation_issue_count must be 0.", metadata_path))
    guard_pass = _to_int(row.get("overclaim_guard_pass_count"))
    guard_total = _to_int(row.get("overclaim_guard_total_count"))
    if guard_total <= 0 or guard_pass != guard_total:
        issues.append(_issue(fixture_run_id, "ERROR", "OVERCLAIM_GUARD_FAILED", "Overclaim guards did not all pass.", metadata_path))

    if fixture_cases_path.exists():
        try:
            cases = pd.read_csv(fixture_cases_path, dtype=str)
            if ACTIVE_REPLAY_INPUT_READY in set(cases.get("expected_status", pd.Series(dtype=str))):
                issues.append(
                    _issue(
                        fixture_run_id,
                        "ERROR",
                        "ACTIVE_READY_CASE_PRESENT",
                        "Fixture cases include ACTIVE_REPLAY_INPUT_READY.",
                        fixture_cases_path,
                    )
                )
        except Exception as exc:  # pragma: no cover - defensive parse guard
            issues.append(_issue(fixture_run_id, "ERROR", "MISSING_FIXTURE_CASES", f"Could not parse fixture cases: {exc}", fixture_cases_path))

    false_expected = [
        ("active_replay_input", "ACTIVE_REPLAY_INPUT_UNEXPECTED"),
        ("forward_labels_exist", "FORWARD_LABELS_EXIST_UNEXPECTED"),
        ("weights_trained", "WEIGHTS_TRAINED_UNEXPECTED"),
        ("active_stock_profile_exists", "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED"),
        ("real_buy_review_eligible", "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED"),
        ("llm_api_called", "UNSAFE_ACTIONABILITY_FLAGS"),
        ("external_api_called", "UNSAFE_ACTIONABILITY_FLAGS"),
        ("cache_mutated", "UNSAFE_ACTIONABILITY_FLAGS"),
        ("current_candidates_run", "UNSAFE_ACTIONABILITY_FLAGS"),
        ("snapshot_built", "UNSAFE_ACTIONABILITY_FLAGS"),
        ("signal_semantics_changed", "UNSAFE_ACTIONABILITY_FLAGS"),
        ("validator_implemented", "VALIDATOR_IMPLEMENTED_UNEXPECTED"),
        ("active_ready_status_allowed", "ACTIVE_READY_STATUS_ALLOWED_UNEXPECTED"),
    ]
    for field, code in false_expected:
        if _to_bool(row.get(field)):
            issues.append(_issue(fixture_run_id, "ERROR", code, f"Unsafe false-expected field is true: {field}", metadata_path))

    true_expected = ["report_only", "diagnostic_only", "no_live_trading", "no_broker_api", "no_order_placement", "no_message_sent"]
    for field in true_expected:
        if not _to_bool(row.get(field)):
            issues.append(_issue(fixture_run_id, "ERROR", "UNSAFE_REPORT_ONLY_FLAGS", f"Safety flag is missing or false: {field}", metadata_path))

    for path in [
        artifact_path,
        metadata_path,
        fixture_cases_path,
        Path(_text(row.get("blocked_requirements_path"))),
        Path(_text(row.get("expected_status_matrix_path"))),
        Path(_text(row.get("fixture_input_schema_path"))),
        Path(_text(row.get("overclaim_guard_report_path"))),
        Path(_text(row.get("report_path"))),
    ]:
        if _unsafe_path(path) or not _safe_diagnostics_path(path):
            issues.append(_issue(fixture_run_id, "ERROR", "UNSAFE_OUTPUT_PATH", f"Unsafe output path: {path}", path))
    return issues


def _write(result: HistoricalReplayInputGateValidatorFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Historical Replay Input Gate Validator Fixture Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "Report-only health view. No replay, current-candidates, snapshots, forward labels, training, active stock profiles, real validator, research-status integration, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues.",
            ]
        ),
        encoding="utf-8",
    )
    paths["metadata"].write_text(
        json.dumps(
            {
                "status": result.status,
                "checked_artifact_count": result.checked_artifact_count,
                "issue_count": result.issue_count,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _issue(fixture_run_id: str, severity: str, issue_code: str, message: str, artifact_path: str | Path) -> dict[str, Any]:
    return {
        "fixture_run_id": fixture_run_id,
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS, dtype=object)
    for column in HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[HEALTH_COLUMNS]


def _audit_metadata(root: str | Path, checked_artifact_count: int) -> dict[str, Any]:
    return {
        "root": str(root),
        "checked_artifact_count": checked_artifact_count,
        "report_only": True,
        "diagnostic_only": True,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
    }


def _unsafe_path(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    return ("data" in parts and "raw" in parts) or ("data" in parts and "processed" in parts) or ("data" in parts and "cache" in parts)


def _safe_diagnostics_path(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    for index in range(len(parts) - 2):
        if parts[index : index + 3] == ["outputs", "reports", "manual_diagnostics"]:
            return True
    return False


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


__all__ = [
    "HistoricalReplayInputGateValidatorFixtureHealthResult",
    "check_historical_replay_input_gate_validator_fixture_health",
]
