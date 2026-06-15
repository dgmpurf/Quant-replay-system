"""Health checks for report-only real replay execution precheck artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.real_replay_execute import (
    NO_REAL_REPLAY_EXECUTION_INPUT,
    READY_FOR_REAL_REPLAY_EXECUTION_REVIEW,
    REAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED,
    REAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED,
    REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED,
    REAL_REPLAY_EXECUTION_INPUT_FOUND,
    REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED,
    REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED,
    REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED,
    REAL_REPLAY_EXECUTION_PIT_BLOCKED,
    REAL_REPLAY_EXECUTION_REVIEW_BLOCKED,
    REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED,
    REAL_REPLAY_EXECUTION_SOURCE_BLOCKED,
    REAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED,
)
from quant_replay_system.real_replay_execute_index import (
    DEFAULT_ROOT,
    build_real_replay_execute_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"

ALLOWED_STATUSES = {
    NO_REAL_REPLAY_EXECUTION_INPUT,
    REAL_REPLAY_EXECUTION_INPUT_FOUND,
    REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED,
    REAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED,
    REAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED,
    REAL_REPLAY_EXECUTION_PIT_BLOCKED,
    REAL_REPLAY_EXECUTION_SOURCE_BLOCKED,
    REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED,
    REAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED,
    REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED,
    REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED,
    REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED,
    REAL_REPLAY_EXECUTION_REVIEW_BLOCKED,
    READY_FOR_REAL_REPLAY_EXECUTION_REVIEW,
}

HEALTH_COLUMNS = ["real_replay_execution_run_id", "severity", "issue_code", "message", "artifact_path"]

FALSE_EXPECTED_FIELDS = [
    "replay_execution_started",
    "replay_execution_completed",
    "real_replay_executed",
    "replay_execution_allowed",
    "replay_decisions_created",
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


@dataclass(frozen=True)
class RealReplayExecuteHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_real_replay_execute_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> RealReplayExecuteHealthResult:
    index = build_real_replay_execute_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(
            _issue(
                "",
                "ERROR",
                "NO_REAL_REPLAY_EXECUTION_ARTIFACT_FOUND",
                "No real replay execution precheck artifacts found.",
                root,
            )
        )
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "real_replay_execute_health.csv",
        "health_report": Path(output_dir) / "real_replay_execute_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = RealReplayExecuteHealthResult(
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


def _issues_for_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    run_id = _text(row.get("real_replay_execution_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata_path = Path(_text(row.get("metadata_path")))
    precheck_path = Path(_text(row.get("precheck_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []

    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)

    required_paths = [
        (metadata_path, "MISSING_METADATA"),
        (Path(_text(row.get("report_path"))), "MISSING_REPORT"),
        (artifact_path / "real_replay_precondition_results.csv", "MISSING_PRECONDITION_RESULTS"),
        (artifact_path / "real_replay_authority_results.csv", "MISSING_AUTHORITY_RESULTS"),
        (artifact_path / "real_replay_lineage_results.csv", "MISSING_LINEAGE_RESULTS"),
        (artifact_path / "real_replay_attestation_results.csv", "MISSING_ATTESTATION_RESULTS"),
        (artifact_path / "pit_source_evidence_results.csv", "MISSING_PIT_SOURCE_RESULTS"),
        (artifact_path / "taxonomy_evidence_results.csv", "MISSING_TAXONOMY_RESULTS"),
        (artifact_path / "leakage_side_effect_guard_results.csv", "MISSING_LEAKAGE_SIDE_EFFECT_RESULTS"),
        (artifact_path / "overclaim_guard_results.csv", "MISSING_OVERCLAIM_GUARD_RESULTS"),
        (precheck_path, "MISSING_PRECHECK"),
        (artifact_path / "recommended_next_task.md", "MISSING_RECOMMENDED_NEXT_TASK"),
    ]
    for path, code in required_paths:
        if not _text(path) or not path.exists():
            issues.append(_issue(run_id, "ERROR", code, f"Required real replay precheck artifact missing: {path}", path))

    if status == "REAL_REPLAY_EXECUTED":
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "REAL_REPLAY_EXECUTED_UNAUTHORIZED",
                "REAL_REPLAY_EXECUTED is not healthy in this report-only artifact view milestone.",
                metadata_path,
            )
        )
    elif status not in ALLOWED_STATUSES:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "UNKNOWN_REAL_REPLAY_EXECUTION_STATUS",
                f"Unknown real replay execution precheck status: {status}",
                metadata_path,
            )
        )

    if status == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW and not _to_bool(
        row.get("ready_for_real_replay_execution_review")
    ):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "READY_STATUS_WITHOUT_READY_FLAG",
                "READY_FOR_REAL_REPLAY_EXECUTION_REVIEW requires ready_for_real_replay_execution_review true.",
                metadata_path,
            )
        )
    if status != READY_FOR_REAL_REPLAY_EXECUTION_REVIEW and _to_bool(
        row.get("ready_for_real_replay_execution_review")
    ):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "READY_FLAG_OUTSIDE_READY_STATUS",
                "ready_for_real_replay_execution_review can be true only for the review-ready status.",
                metadata_path,
            )
        )

    for field in FALSE_EXPECTED_FIELDS:
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

    if _text(row.get("replay_decision_artifact_path")):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "REPLAY_DECISION_ARTIFACT_PATH_UNEXPECTED",
                "Precheck artifact must not point to replay decision artifacts.",
                precheck_path,
            )
        )

    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "UNSAFE_REPORT_ONLY_FLAGS",
                    f"Safety flag is missing or false: {field}",
                    metadata_path,
                )
            )

    if status != NO_REAL_REPLAY_EXECUTION_INPUT:
        issues.extend(_overclaim_guard_issues(run_id, Path(_text(row.get("overclaim_guard_results_path")))))
    return issues


def _overclaim_guard_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return [
            _issue(
                run_id,
                "ERROR",
                "MISSING_OVERCLAIM_GUARD_RESULTS",
                "Review-ready real replay precheck artifacts require overclaim guard results.",
                path,
            )
        ]
    try:
        frame = pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - pandas parser details are not part of the contract
        return [_issue(run_id, "ERROR", "OVERCLAIM_GUARD_UNREADABLE", str(exc), path)]
    if frame.empty:
        return [
            _issue(
                run_id,
                "ERROR",
                "OVERCLAIM_GUARD_FAILED",
                "Overclaim guard results are empty.",
                path,
            )
        ]
    issues = []
    for row in frame.to_dict("records"):
        if not _to_bool(row.get("passed")) or _text(row.get("status")) != "PASS":
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "OVERCLAIM_GUARD_FAILED",
                    "Overclaim guard rows must all pass for review-ready artifacts.",
                    path,
                )
            )
            break
    return issues


def _ensure_manual_diagnostics_issues(run_id: str, artifact_path: Path, issues: list[dict[str, Any]]) -> None:
    parts = [part.lower() for part in artifact_path.parts]
    try:
        outputs_index = parts.index("outputs")
        reports_index = parts.index("reports")
        diagnostics_index = parts.index("manual_diagnostics")
    except ValueError:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Real replay execution precheck artifacts must stay under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )
        return
    if not (outputs_index < reports_index < diagnostics_index):
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "ARTIFACT_PATH_OUTSIDE_MANUAL_DIAGNOSTICS",
                "Real replay execution precheck artifacts must stay under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: RealReplayExecuteHealthResult) -> None:
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
                "# Real Replay Execution Precheck Health",
                "",
                "Report-only health check. Review-ready artifacts are pre-execution context only and must never imply replay execution, replay decisions, labels, training, stock_profile, buy-review eligibility, broker/order/message/API/cache/data side effects, or trading.",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                result.health_frame.to_markdown(index=False)
                if not result.health_frame.empty
                else "No real replay execution precheck health issues found.",
            ]
        ),
        encoding="utf-8",
    )


def _issue(run_id: str, severity: str, issue_code: str, message: str, artifact_path: str | Path) -> dict[str, Any]:
    return {
        "real_replay_execution_run_id": run_id,
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    for column in HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[HEALTH_COLUMNS]


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
        return value.strip().lower() in {"1", "true", "yes", "y", "pass"}
    return False
