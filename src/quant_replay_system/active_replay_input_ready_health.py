"""Health checks for report-only ACTIVE_REPLAY_INPUT_READY core artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_replay_input_ready import (
    ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT_FOUND,
    ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED,
    NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT,
    READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY,
)
from quant_replay_system.active_replay_input_ready_index import (
    DEFAULT_ROOT,
    build_active_replay_input_ready_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"

ALLOWED_STATUSES = {
    NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT,
    ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT_FOUND,
    ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED,
    READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY,
}

HEALTH_COLUMNS = ["active_ready_run_id", "severity", "issue_code", "message", "artifact_path"]


@dataclass(frozen=True)
class ActiveReplayInputReadyHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_active_replay_input_ready_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveReplayInputReadyHealthResult:
    index = build_active_replay_input_ready_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_ACTIVE_READY_ARTIFACT_FOUND", "No active-ready artifacts found.", root))
    else:
        latest = index.index_frame.sort_values(["generated_at", "active_ready_run_id"]).iloc[-1].to_dict()
        issues.extend(_issues_for_latest(latest))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "active_replay_input_ready_health.csv",
        "health_report": Path(output_dir) / "active_replay_input_ready_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActiveReplayInputReadyHealthResult(
        status=status,
        checked_artifact_count=len(index.index_frame),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=index.warnings,
        audit_metadata={
            "root": str(root),
            "checked_artifact_count": len(index.index_frame),
            "report_only": True,
            "diagnostic_only": True,
        },
    )
    _write(result)
    return result


def _issues_for_latest(row: dict[str, Any]) -> list[dict[str, Any]]:
    run_id = _text(row.get("active_ready_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata_path = Path(_text(row.get("metadata_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []
    required_paths = [
        (metadata_path, "MISSING_METADATA"),
        (Path(_text(row.get("active_ready_report_path"))), "MISSING_ACTIVE_READY_REPORT"),
        (artifact_path / "active_ready_precondition_results.csv", "MISSING_PRECONDITION_RESULTS"),
        (artifact_path / "active_ready_authority_results.csv", "MISSING_AUTHORITY_RESULTS"),
        (artifact_path / "ready_decision_lineage_results.csv", "MISSING_LINEAGE_RESULTS"),
        (artifact_path / "active_ready_attestation_results.csv", "MISSING_ATTESTATION_RESULTS"),
        (artifact_path / "pit_source_evidence_results.csv", "MISSING_PIT_SOURCE_RESULTS"),
        (artifact_path / "taxonomy_evidence_results.csv", "MISSING_TAXONOMY_RESULTS"),
        (artifact_path / "leakage_side_effect_guard_results.csv", "MISSING_LEAKAGE_SIDE_EFFECT_RESULTS"),
        (artifact_path / "overclaim_guard_results.csv", "MISSING_OVERCLAIM_GUARD_RESULTS"),
        (artifact_path / "active_replay_input_ready_candidate.json", "MISSING_READY_CANDIDATE"),
        (artifact_path / "recommended_next_task.md", "MISSING_RECOMMENDED_NEXT_TASK"),
    ]
    for path, code in required_paths:
        if not _text(path) or not path.exists():
            issues.append(_issue(run_id, "ERROR", code, f"Required active-ready artifact missing: {path}", path))
    if status == "ACTIVE_REPLAY_INPUT_READY":
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED",
                "ACTIVE_REPLAY_INPUT_READY must not be emitted.",
                metadata_path,
            )
        )
    elif status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_ACTIVE_READY_STATUS", f"Unknown status: {status}", metadata_path))
    false_expected = [
        "active_replay_input_ready",
        "active_replay_input",
        "active_ready_emitted",
        "replay_execution_allowed",
        "replay_decisions_exist",
        "forward_labels_allowed",
        "forward_labels_exist",
        "training_allowed",
        "weights_trained",
        "stock_profile_allowed",
        "active_stock_profile_exists",
        "buy_review_allowed",
        "real_buy_review_eligible",
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
    for field in false_expected:
        if _to_bool(row.get(field)):
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    f"{field.upper()}_UNEXPECTED",
                    f"Unsafe false-expected field is true: {field}",
                    metadata_path,
                )
            )
    for field in ["report_only", "diagnostic_only", "no_live_trading", "no_broker_api", "no_order_placement", "no_message_sent"]:
        if not _to_bool(row.get(field)):
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "UNSAFE_REPORT_ONLY_OR_TRADING_FLAGS",
                    f"Safety flag is missing or false: {field}",
                    metadata_path,
                )
            )
    if status != NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT and (
        _to_int(row.get("overclaim_guard_total_count")) <= 0
        or _to_int(row.get("overclaim_guard_pass_count")) != _to_int(row.get("overclaim_guard_total_count"))
    ):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "OVERCLAIM_GUARD_FAILED",
                "Overclaim guard counts do not fully pass.",
                metadata_path,
            )
        )
    if not _safe_diagnostics_path(artifact_path) or _unsafe_path(artifact_path):
        issues.append(_issue(run_id, "ERROR", "UNSAFE_OUTPUT_PATH", f"Unsafe artifact path: {artifact_path}", artifact_path))
    return issues


def _write(result: ActiveReplayInputReadyHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# ACTIVE_REPLAY_INPUT_READY Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                _safety_statement(),
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


def _issue(run_id: str, severity: str, code: str, message: str, artifact_path: str | Path) -> dict[str, Any]:
    return {
        "active_ready_run_id": run_id,
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[HEALTH_COLUMNS].reset_index(drop=True)


def _safe_diagnostics_path(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    return "outputs" in parts and "reports" in parts and "manual_diagnostics" in parts


def _unsafe_path(path: Path) -> bool:
    text = str(path).replace("\\", "/").lower()
    return any(token in text for token in ["/data/raw", "/data/processed", "/data/cache", "/.env", "/secrets"])


def _safety_statement() -> str:
    return (
        "Report-only health view. READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY is not ACTIVE_REPLAY_INPUT_READY; "
        "ACTIVE_REPLAY_INPUT_READY is not emitted; active replay input is not created; replay is not run; "
        "replay decisions are not created; labels are not computed; training is not run; stock_profile is not "
        "created; buy-review eligibility is not created; trading is not authorized."
    )


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass", "accepted"}
    return False


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
