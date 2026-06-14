"""Health checks for report-only active replay input ready-decision artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_replay_input_ready_decision import (
    ACTIVE_REPLAY_INPUT_READY_DECISION_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT_FOUND,
    ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_TAXONOMY_BLOCKED,
    NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT,
    READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION,
)
from quant_replay_system.active_replay_input_ready_decision_index import (
    DEFAULT_ROOT,
    build_active_replay_input_ready_decision_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"

ALLOWED_STATUSES = {
    NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT,
    ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT_FOUND,
    ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_TAXONOMY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED,
    READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION,
}

HEALTH_COLUMNS = ["decision_run_id", "severity", "issue_code", "message", "artifact_path"]


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_active_replay_input_ready_decision_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveReplayInputReadyDecisionHealthResult:
    index = build_active_replay_input_ready_decision_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(
            _issue(
                "",
                "ERROR",
                "NO_READY_DECISION_ARTIFACT_FOUND",
                "No ready-decision artifacts found.",
                root,
            )
        )
    else:
        latest = index.index_frame.sort_values(["generated_at", "decision_run_id"]).iloc[-1].to_dict()
        issues.extend(_issues_for_latest(latest))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "active_replay_input_ready_decision_health.csv",
        "health_report": Path(output_dir) / "active_replay_input_ready_decision_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActiveReplayInputReadyDecisionHealthResult(
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
    decision_run_id = _text(row.get("decision_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata_path = Path(_text(row.get("metadata_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []

    required_paths = [
        (metadata_path, "MISSING_METADATA"),
        (Path(_text(row.get("decision_report_path"))), "MISSING_DECISION_REPORT"),
        (artifact_path / "decision_precondition_results.csv", "MISSING_PRECONDITION_RESULTS"),
        (artifact_path / "decision_authority_results.csv", "MISSING_AUTHORITY_RESULTS"),
        (artifact_path / "emission_lineage_results.csv", "MISSING_LINEAGE_RESULTS"),
        (artifact_path / "decision_attestation_results.csv", "MISSING_ATTESTATION_RESULTS"),
        (artifact_path / "pit_source_evidence_results.csv", "MISSING_PIT_SOURCE_RESULTS"),
        (artifact_path / "taxonomy_evidence_results.csv", "MISSING_TAXONOMY_RESULTS"),
        (artifact_path / "leakage_side_effect_guard_results.csv", "MISSING_LEAKAGE_SIDE_EFFECT_RESULTS"),
        (artifact_path / "overclaim_guard_results.csv", "MISSING_OVERCLAIM_GUARD_RESULTS"),
        (artifact_path / "active_replay_input_ready_candidate.json", "MISSING_READY_CANDIDATE"),
        (artifact_path / "recommended_next_task.md", "MISSING_RECOMMENDED_NEXT_TASK"),
    ]
    for path, code in required_paths:
        if not _text(path) or not path.exists():
            issues.append(
                _issue(decision_run_id, "ERROR", code, f"Required ready-decision artifact missing: {path}", path)
            )

    if status == "ACTIVE_REPLAY_INPUT_READY":
        issues.append(
            _issue(
                decision_run_id,
                "ERROR",
                "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED",
                "ACTIVE_REPLAY_INPUT_READY must not be emitted.",
                metadata_path,
            )
        )
    elif status not in ALLOWED_STATUSES:
        issues.append(
            _issue(
                decision_run_id,
                "ERROR",
                "UNKNOWN_READY_DECISION_STATUS",
                f"Unknown ready-decision status: {status}",
                metadata_path,
            )
        )

    if (
        _to_bool(row.get("ready_for_active_replay_input_ready_decision"))
        and status != READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION
    ):
        issues.append(
            _issue(
                decision_run_id,
                "ERROR",
                "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION_INCONSISTENT",
                "ready_for_active_replay_input_ready_decision is true for a non-ready status.",
                metadata_path,
            )
        )

    false_expected = [
        ("active_replay_input_ready", "ACTIVE_REPLAY_INPUT_READY_FLAG_UNEXPECTED"),
        ("active_replay_input", "ACTIVE_REPLAY_INPUT_UNEXPECTED"),
        ("active_ready_emitted", "ACTIVE_READY_EMITTED_UNEXPECTED"),
        ("replay_execution_allowed", "REPLAY_EXECUTION_ALLOWED_UNEXPECTED"),
        ("forward_labels_allowed", "FORWARD_LABELS_ALLOWED_UNEXPECTED"),
        ("training_allowed", "TRAINING_ALLOWED_UNEXPECTED"),
        ("stock_profile_allowed", "STOCK_PROFILE_ALLOWED_UNEXPECTED"),
        ("buy_review_allowed", "BUY_REVIEW_ALLOWED_UNEXPECTED"),
        ("trading_allowed", "TRADING_ALLOWED_UNEXPECTED"),
        ("replay_decisions_exist", "REPLAY_DECISIONS_EXIST_UNEXPECTED"),
        ("forward_labels_exist", "FORWARD_LABELS_EXIST_UNEXPECTED"),
        ("weights_trained", "WEIGHTS_TRAINED_UNEXPECTED"),
        ("active_stock_profile_exists", "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED"),
        ("real_buy_review_eligible", "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED"),
        ("approval_applied", "APPROVAL_APPLIED_UNEXPECTED"),
        ("order_placed", "ORDER_PLACED_UNEXPECTED"),
        ("message_sent", "MESSAGE_SENT_UNEXPECTED"),
        ("llm_api_called", "LLM_API_CALLED_UNEXPECTED"),
        ("external_api_called", "EXTERNAL_API_CALLED_UNEXPECTED"),
        ("cache_mutated", "CACHE_MUTATED_UNEXPECTED"),
        ("data_raw_written", "DATA_RAW_WRITTEN_UNEXPECTED"),
        ("data_processed_written", "DATA_PROCESSED_WRITTEN_UNEXPECTED"),
        ("data_cache_written", "DATA_CACHE_WRITTEN_UNEXPECTED"),
        ("current_candidates_run", "CURRENT_CANDIDATES_RUN_UNEXPECTED"),
        ("snapshot_built", "SNAPSHOT_BUILT_UNEXPECTED"),
        ("signal_semantics_changed", "SIGNAL_SEMANTICS_CHANGED_UNEXPECTED"),
    ]
    for field, code in false_expected:
        if _to_bool(row.get(field)):
            issues.append(
                _issue(
                    decision_run_id,
                    "ERROR",
                    code,
                    f"Unsafe false-expected field is true: {field}",
                    metadata_path,
                )
            )

    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(
                _issue(
                    decision_run_id,
                    "ERROR",
                    "UNSAFE_REPORT_ONLY_FLAGS",
                    f"Safety flag is missing or false: {field}",
                    metadata_path,
                )
            )
    for field in ["no_live_trading", "no_broker_api", "no_order_placement", "no_message_sent"]:
        if not _to_bool(row.get(field)):
            issues.append(
                _issue(
                    decision_run_id,
                    "ERROR",
                    "UNSAFE_TRADING_FLAGS",
                    f"Trading safety flag is missing or false: {field}",
                    metadata_path,
                )
            )

    if status != NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT and (
        _to_int(row.get("overclaim_guard_total_count")) <= 0
        or _to_int(row.get("overclaim_guard_pass_count")) != _to_int(row.get("overclaim_guard_total_count"))
    ):
        issues.append(
            _issue(
                decision_run_id,
                "ERROR",
                "OVERCLAIM_GUARD_FAILED",
                "Overclaim guard counts do not fully pass.",
                metadata_path,
            )
        )

    if not _safe_diagnostics_path(artifact_path) or _unsafe_path(artifact_path):
        issues.append(
            _issue(
                decision_run_id,
                "ERROR",
                "UNSAFE_OUTPUT_PATH",
                f"Unsafe ready-decision artifact path: {artifact_path}",
                artifact_path,
            )
        )
    for value in row.values():
        if isinstance(value, str) and value.strip() and _unsafe_path(Path(value)):
            issues.append(
                _issue(
                    decision_run_id,
                    "ERROR",
                    "UNSAFE_OUTPUT_PATH",
                    f"Unsafe path recorded in ready-decision metadata: {value}",
                    metadata_path,
                )
            )
    return issues


def _write(result: ActiveReplayInputReadyDecisionHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Active Replay Input Ready Decision Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "Report-only health view. It does not emit ACTIVE_REPLAY_INPUT_READY, create active replay input, run replay, compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, integrate research-status, write data stores, call APIs, send messages, use broker integration, place orders, or mutate cache.",
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


def _issue(
    decision_run_id: str,
    severity: str,
    issue_code: str,
    message: str,
    artifact_path: str | Path,
) -> dict[str, Any]:
    return {
        "decision_run_id": decision_run_id,
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


def _safe_diagnostics_path(path: Path) -> bool:
    return "outputs/reports/manual_diagnostics" in str(path).replace("\\", "/").lower()


def _unsafe_path(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return any(part in normalized for part in ["data/raw", "data/processed", "data/cache"])


def _hash_payload(payload: Any) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "ActiveReplayInputReadyDecisionHealthResult",
    "check_active_replay_input_ready_decision_health",
]
