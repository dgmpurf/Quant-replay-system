"""Health checks for report-only active replay input final-review artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_replay_input_final_review import (
    FINAL_REVIEW_ATTESTATION_BLOCKED,
    FINAL_REVIEW_AUTHORITY_BLOCKED,
    FINAL_REVIEW_EVIDENCE_BLOCKED,
    FINAL_REVIEW_LEAKAGE_BLOCKED,
    FINAL_REVIEW_LINEAGE_BLOCKED,
    FINAL_REVIEW_OVERCLAIM_BLOCKED,
    FINAL_REVIEW_PACKAGE_FOUND,
    FINAL_REVIEW_PIT_BLOCKED,
    FINAL_REVIEW_READY_FOR_EMISSION_REVIEW,
    FINAL_REVIEW_REVIEW_BLOCKED,
    FINAL_REVIEW_SIDE_EFFECT_BLOCKED,
    FINAL_REVIEW_SOURCE_BLOCKED,
    FINAL_REVIEW_TAXONOMY_BLOCKED,
    NO_FINAL_REVIEW_PACKAGE,
)
from quant_replay_system.active_replay_input_final_review_index import (
    DEFAULT_ROOT,
    build_active_replay_input_final_review_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"

ALLOWED_STATUSES = {
    NO_FINAL_REVIEW_PACKAGE,
    FINAL_REVIEW_PACKAGE_FOUND,
    FINAL_REVIEW_LINEAGE_BLOCKED,
    FINAL_REVIEW_AUTHORITY_BLOCKED,
    FINAL_REVIEW_ATTESTATION_BLOCKED,
    FINAL_REVIEW_PIT_BLOCKED,
    FINAL_REVIEW_SOURCE_BLOCKED,
    FINAL_REVIEW_EVIDENCE_BLOCKED,
    FINAL_REVIEW_TAXONOMY_BLOCKED,
    FINAL_REVIEW_LEAKAGE_BLOCKED,
    FINAL_REVIEW_SIDE_EFFECT_BLOCKED,
    FINAL_REVIEW_OVERCLAIM_BLOCKED,
    FINAL_REVIEW_REVIEW_BLOCKED,
    FINAL_REVIEW_READY_FOR_EMISSION_REVIEW,
}

HEALTH_COLUMNS = ["final_review_run_id", "severity", "issue_code", "message", "artifact_path"]


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_active_replay_input_final_review_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveReplayInputFinalReviewHealthResult:
    index = build_active_replay_input_final_review_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_FINAL_REVIEW_ARTIFACT_FOUND", "No final-review artifacts found.", root))
    else:
        latest = index.index_frame.sort_values(["generated_at", "final_review_run_id"]).iloc[-1].to_dict()
        issues.extend(_issues_for_latest(latest))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "active_replay_input_final_review_health.csv",
        "health_report": Path(output_dir) / "active_replay_input_final_review_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActiveReplayInputFinalReviewHealthResult(
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


def _issues_for_latest(row: dict[str, Any]) -> list[dict[str, Any]]:
    final_review_run_id = _text(row.get("final_review_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata_path = Path(_text(row.get("metadata_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []

    required_paths = [
        (metadata_path, "MISSING_METADATA"),
        (Path(_text(row.get("final_review_report_path"))), "MISSING_FINAL_REVIEW_REPORT"),
        (artifact_path / "final_review_package_manifest_results.csv", "MISSING_PACKAGE_RESULTS"),
        (artifact_path / "active_ready_lineage_results.csv", "MISSING_LINEAGE_RESULTS"),
        (artifact_path / "final_reviewer_authority_results.csv", "MISSING_AUTHORITY_RESULTS"),
        (artifact_path / "final_reviewer_attestation_results.csv", "MISSING_ATTESTATION_RESULTS"),
        (artifact_path / "pit_source_evidence_attachment_results.csv", "MISSING_PIT_SOURCE_RESULTS"),
        (artifact_path / "taxonomy_attachment_results.csv", "MISSING_TAXONOMY_RESULTS"),
        (artifact_path / "leakage_side_effect_evidence_results.csv", "MISSING_LEAKAGE_SIDE_EFFECT_RESULTS"),
        (artifact_path / "overclaim_guard_results.csv", "MISSING_OVERCLAIM_GUARD_RESULTS"),
        (artifact_path / "emission_readiness_results.csv", "MISSING_EMISSION_READINESS_RESULTS"),
        (artifact_path / "recommended_next_task.md", "MISSING_RECOMMENDED_NEXT_TASK"),
    ]
    for path, code in required_paths:
        if not _text(path) or not path.exists():
            issues.append(_issue(final_review_run_id, "ERROR", code, f"Required final-review artifact missing: {path}", path))

    if status == "ACTIVE_REPLAY_INPUT_READY":
        issues.append(_issue(final_review_run_id, "ERROR", "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED", "ACTIVE_REPLAY_INPUT_READY must not be emitted.", metadata_path))
    elif status not in ALLOWED_STATUSES:
        issues.append(_issue(final_review_run_id, "ERROR", "UNKNOWN_FINAL_REVIEW_STATUS", f"Unknown final-review status: {status}", metadata_path))

    false_expected = [
        ("active_ready_emitted", "ACTIVE_READY_EMITTED_UNEXPECTED"),
        ("active_replay_input_ready", "ACTIVE_REPLAY_INPUT_READY_FLAG_UNEXPECTED"),
        ("active_replay_input", "ACTIVE_REPLAY_INPUT_UNEXPECTED"),
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
            issues.append(_issue(final_review_run_id, "ERROR", code, f"Unsafe false-expected field is true: {field}", metadata_path))

    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(final_review_run_id, "ERROR", "UNSAFE_REPORT_ONLY_FLAGS", f"Safety flag is missing or false: {field}", metadata_path))
    for field in ["no_live_trading", "no_broker_api", "no_order_placement", "no_message_sent"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(final_review_run_id, "ERROR", "UNSAFE_TRADING_FLAGS", f"Trading safety flag is missing or false: {field}", metadata_path))

    if status != NO_FINAL_REVIEW_PACKAGE and (
        _to_int(row.get("overclaim_guard_total_count")) <= 0
        or _to_int(row.get("overclaim_guard_pass_count")) != _to_int(row.get("overclaim_guard_total_count"))
    ):
        issues.append(_issue(final_review_run_id, "ERROR", "OVERCLAIM_GUARD_FAILED", "Overclaim guard counts do not fully pass.", metadata_path))

    if not _safe_diagnostics_path(artifact_path) or _unsafe_path(artifact_path):
        issues.append(_issue(final_review_run_id, "ERROR", "UNSAFE_OUTPUT_PATH", f"Unsafe final-review artifact path: {artifact_path}", artifact_path))
    for value in row.values():
        if isinstance(value, str) and value.strip() and _unsafe_path(Path(value)):
            issues.append(_issue(final_review_run_id, "ERROR", "UNSAFE_OUTPUT_PATH", f"Unsafe path recorded in final-review metadata: {value}", metadata_path))
    return issues


def _write(result: ActiveReplayInputFinalReviewHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Active Replay Input Final-Review Health",
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


def _issue(final_review_run_id: str, severity: str, issue_code: str, message: str, artifact_path: str | Path) -> dict[str, Any]:
    return {
        "final_review_run_id": final_review_run_id,
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
    "ActiveReplayInputFinalReviewHealthResult",
    "check_active_replay_input_final_review_health",
]
