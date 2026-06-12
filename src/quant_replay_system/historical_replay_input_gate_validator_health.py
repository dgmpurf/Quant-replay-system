"""Health checks for report-only historical replay input gate validator artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.historical_replay_input_gate_validator import ACTIVE_REPLAY_INPUT_READY
from quant_replay_system.historical_replay_input_gate_validator_index import (
    build_historical_replay_input_gate_validator_index,
)


ALLOWED_STATUSES = {
    "NO_INPUT",
    "NON_INPUT_ARTIFACT_REJECTED",
    "PIT_UNIVERSE_BLOCKED",
    "SOURCE_REGISTRY_BLOCKED",
    "RAW_DOCUMENT_BLOCKED",
    "FACTOR_DEFINITION_BLOCKED",
    "FACTOR_OBSERVATION_BLOCKED",
    "EVENT_STRUCTURED_BLOCKED",
    "COMPANY_EXPOSURE_BLOCKED",
    "EVIDENCE_BUNDLE_BLOCKED",
    "FUTURE_LABEL_LEAKAGE_BLOCKED",
    "TRAINING_LEAKAGE_BLOCKED",
    "STOCK_PROFILE_LEAKAGE_BLOCKED",
    "ACTIONABILITY_BLOCKED",
    "REPLAY_INPUT_GATE_PASS_CANDIDATE",
}

HEALTH_COLUMNS = ["validator_run_id", "severity", "issue_code", "message", "artifact_path"]


@dataclass(frozen=True)
class HistoricalReplayInputGateValidatorHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_historical_replay_input_gate_validator_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1/health",
) -> HistoricalReplayInputGateValidatorHealthResult:
    index = build_historical_replay_input_gate_validator_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_VALIDATOR_ARTIFACT_FOUND", "No validator artifacts found.", root))
    else:
        latest = index.index_frame.sort_values(["generated_at", "validator_run_id"]).iloc[-1].to_dict()
        issues.extend(_issues_for_latest(latest))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "historical_replay_input_gate_validator_health.csv",
        "health_report": Path(output_dir) / "historical_replay_input_gate_validator_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = HistoricalReplayInputGateValidatorHealthResult(
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
    validator_run_id = _text(row.get("validator_run_id"))
    metadata_path = Path(_text(row.get("metadata_path")))
    issues: list[dict[str, Any]] = []
    for path, code in [
        (metadata_path, "MISSING_METADATA"),
        (Path(_text(row.get("report_path"))), "MISSING_REPORT"),
        (Path(_text(row.get("input_package_summary_path"))), "MISSING_INPUT_PACKAGE_SUMMARY"),
        (Path(_text(row.get("gate_results_path"))), "MISSING_GATE_RESULTS"),
        (Path(_text(row.get("blocker_matrix_path"))), "MISSING_BLOCKER_MATRIX"),
        (Path(_text(row.get("entity_contract_validation_path"))), "MISSING_ENTITY_CONTRACT_VALIDATION"),
        (Path(_text(row.get("non_input_artifact_rejections_path"))), "MISSING_NON_INPUT_REJECTIONS"),
        (Path(_text(row.get("overclaim_guard_report_path"))), "MISSING_OVERCLAIM_GUARDS"),
    ]:
        if not _text(path) or not path.exists():
            issues.append(_issue(validator_run_id, "ERROR", code, f"Required artifact missing: {path}", path))

    status = _text(row.get("status"))
    if status == ACTIVE_REPLAY_INPUT_READY:
        issues.append(
            _issue(
                validator_run_id,
                "ERROR",
                "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED",
                "ACTIVE_REPLAY_INPUT_READY is not allowed for this report-only validator.",
                metadata_path,
            )
        )
    elif status not in ALLOWED_STATUSES:
        issues.append(_issue(validator_run_id, "ERROR", "UNKNOWN_STATUS", f"Unknown validator status: {status}", metadata_path))

    false_expected = [
        ("active_replay_input_ready", "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED"),
        ("active_replay_input", "ACTIVE_REPLAY_INPUT_UNEXPECTED"),
        ("forward_labels_exist", "FORWARD_LABELS_EXIST_UNEXPECTED"),
        ("weights_trained", "WEIGHTS_TRAINED_UNEXPECTED"),
        ("active_stock_profile_exists", "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED"),
        ("real_buy_review_eligible", "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED"),
        ("approval_applied", "APPROVAL_APPLIED_UNEXPECTED"),
        ("order_placed", "ORDER_PLACED_UNEXPECTED"),
        ("llm_api_called", "LLM_API_CALLED_UNEXPECTED"),
        ("external_api_called", "EXTERNAL_API_CALLED_UNEXPECTED"),
        ("cache_mutated", "CACHE_MUTATED_UNEXPECTED"),
        ("current_candidates_run", "CURRENT_CANDIDATES_RUN_UNEXPECTED"),
        ("snapshot_built", "SNAPSHOT_BUILT_UNEXPECTED"),
        ("signal_semantics_changed", "SIGNAL_SEMANTICS_CHANGED_UNEXPECTED"),
    ]
    for field, code in false_expected:
        if _to_bool(row.get(field)):
            issues.append(_issue(validator_run_id, "ERROR", code, f"Unsafe false-expected field is true: {field}", metadata_path))

    true_expected = ["report_only", "diagnostic_only"]
    for field in true_expected:
        if not _to_bool(row.get(field)):
            issues.append(_issue(validator_run_id, "ERROR", "UNSAFE_REPORT_ONLY_FLAGS", f"Safety flag is missing or false: {field}", metadata_path))
    trading_true_expected = ["no_live_trading", "no_broker_api", "no_order_placement", "no_message_sent"]
    for field in trading_true_expected:
        if not _to_bool(row.get(field)):
            issues.append(_issue(validator_run_id, "ERROR", "UNSAFE_TRADING_FLAGS", f"Trading safety flag is missing or false: {field}", metadata_path))

    guard_pass = _to_int(row.get("overclaim_guard_pass_count"))
    guard_total = _to_int(row.get("overclaim_guard_total_count"))
    if guard_total <= 0 or guard_pass != guard_total:
        issues.append(_issue(validator_run_id, "ERROR", "OVERCLAIM_GUARD_FAILED", "Overclaim guards did not all pass.", metadata_path))
    guard_path = Path(_text(row.get("overclaim_guard_report_path")))
    if guard_path.exists():
        try:
            guards = pd.read_csv(guard_path, dtype=str).fillna("")
            if "passed" not in guards.columns or not guards["passed"].map(_to_bool).all():
                issues.append(_issue(validator_run_id, "ERROR", "OVERCLAIM_GUARD_FAILED", "Overclaim guard report contains failed guards.", guard_path))
        except Exception as exc:  # pragma: no cover - defensive parse guard
            issues.append(_issue(validator_run_id, "ERROR", "OVERCLAIM_GUARD_FAILED", f"Could not parse overclaim guards: {exc}", guard_path))

    for path in [
        Path(_text(row.get("artifact_path"))),
        metadata_path,
        Path(_text(row.get("report_path"))),
        Path(_text(row.get("input_package_summary_path"))),
        Path(_text(row.get("gate_results_path"))),
        Path(_text(row.get("blocker_matrix_path"))),
        Path(_text(row.get("entity_contract_validation_path"))),
        Path(_text(row.get("non_input_artifact_rejections_path"))),
        guard_path,
    ]:
        if _unsafe_path(path) or not _safe_diagnostics_path(path):
            issues.append(_issue(validator_run_id, "ERROR", "UNSAFE_OUTPUT_PATH", f"Unsafe output path: {path}", path))
    return issues


def _write(result: HistoricalReplayInputGateValidatorHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Historical Replay Input Gate Validator Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "Report-only health view. No replay, current-candidates, snapshots, forward labels, training, active stock profiles, research-status integration, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues found.",
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
                "health_id": _hash_payload(result.health_frame.to_dict("records")),
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _issue(validator_run_id: str, severity: str, issue_code: str, message: str, artifact_path: str | Path) -> dict[str, Any]:
    return {
        "validator_run_id": validator_run_id,
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
    return frame[HEALTH_COLUMNS].astype(object)


def _audit_metadata(root: str | Path, checked_artifact_count: int) -> dict[str, Any]:
    return {
        "root": str(root),
        "checked_artifact_count": checked_artifact_count,
        "report_only": True,
        "diagnostic_only": True,
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _safe_diagnostics_path(path: Path) -> bool:
    return "outputs/reports/manual_diagnostics" in str(path).replace("\\", "/").lower()


def _unsafe_path(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return any(part in normalized for part in ["data/raw", "data/processed", "data/cache"])


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int:
    try:
        if _text(value) == "":
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}

