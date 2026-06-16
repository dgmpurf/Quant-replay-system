"""Health checks for report-only replay decision freeze artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.replay_decision_freeze import (
    NO_REPLAY_DECISION_FREEZE_INPUT,
    READY_FOR_REPLAY_DECISION_FREEZE,
    REPLAY_DECISION_FREEZE_ATTESTATION_BLOCKED,
    REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED,
    REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED,
    REPLAY_DECISION_FREEZE_INPUT_FOUND,
    REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED,
    REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED,
    REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED,
    REPLAY_DECISION_FREEZE_PIT_BLOCKED,
    REPLAY_DECISION_FREEZE_REVIEW_BLOCKED,
    REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED,
    REPLAY_DECISION_FREEZE_SOURCE_BLOCKED,
    REPLAY_DECISION_FREEZE_TAXONOMY_BLOCKED,
    REPLAY_DECISION_FROZEN,
)
from quant_replay_system.replay_decision_freeze_index import (
    DEFAULT_ROOT,
    build_replay_decision_freeze_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"

ALLOWED_STATUSES = {
    NO_REPLAY_DECISION_FREEZE_INPUT,
    REPLAY_DECISION_FREEZE_INPUT_FOUND,
    REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED,
    REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED,
    REPLAY_DECISION_FREEZE_ATTESTATION_BLOCKED,
    REPLAY_DECISION_FREEZE_PIT_BLOCKED,
    REPLAY_DECISION_FREEZE_SOURCE_BLOCKED,
    REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED,
    REPLAY_DECISION_FREEZE_TAXONOMY_BLOCKED,
    REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED,
    REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED,
    REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED,
    REPLAY_DECISION_FREEZE_REVIEW_BLOCKED,
    READY_FOR_REPLAY_DECISION_FREEZE,
    REPLAY_DECISION_FROZEN,
}
ALLOWED_DECISION_LABELS = {
    "WATCH",
    "REVIEW_BUY_CANDIDATE",
    "REVIEW_SELL_CANDIDATE",
    "HOLD_REVIEW",
    "NO_ACTION",
    "BLOCKED",
}
HEALTH_COLUMNS = ["replay_decision_freeze_run_id", "severity", "issue_code", "message", "artifact_path"]

UNSAFE_FALSE_FIELDS = [
    "forward_labels_allowed",
    "forward_labels_exist",
    "forward_return_labels_created",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
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
REQUIRED_EVIDENCE_COLUMNS = {"available_time", "source_hash", "revision_id", "taxonomy_layer", "pit_valid"}
FORBIDDEN_COLUMN_TOKENS = {
    "future",
    "forward_return",
    "forward_return_label",
    "training",
    "model_weight",
    "stock_profile",
    "buy_review",
    "approved_for_paper",
    "order",
    "broker",
    "trade_id",
}
OVERCLAIM_PHRASES = [
    "strategy performance validated",
    "paper approval granted",
    "approved_for_paper=true",
    "broker integration enabled",
    "order placed",
    "trading authorized",
]


@dataclass(frozen=True)
class ReplayDecisionFreezeHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_replay_decision_freeze_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ReplayDecisionFreezeHealthResult:
    index = build_replay_decision_freeze_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_REPLAY_DECISION_FREEZE_ARTIFACT_FOUND", "No replay decision freeze artifacts found.", root))
    else:
        for row in index.index_frame.to_dict("records"):
            issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "replay_decision_freeze_health.csv",
        "health_report": Path(output_dir) / "replay_decision_freeze_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ReplayDecisionFreezeHealthResult(
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
    run_id = _text(row.get("replay_decision_freeze_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata_path = Path(_text(row.get("metadata_path")))
    rows_path = Path(_text(row.get("replay_decision_rows_path")))
    evidence_path = Path(_text(row.get("replay_decision_evidence_index_path")))
    status = _text(row.get("status"))
    decision_row_count = _to_int(row.get("decision_row_count"))
    issues: list[dict[str, Any]] = []

    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)
    for path, code in [
        (metadata_path, "MISSING_METADATA"),
        (Path(_text(row.get("report_path"))), "MISSING_REPORT"),
        (rows_path, "MISSING_REPLAY_DECISION_ROWS"),
        (evidence_path, "MISSING_REPLAY_DECISION_EVIDENCE_INDEX"),
        (Path(_text(row.get("safety_flags_path"))), "MISSING_SAFETY_FLAGS"),
        (artifact_path / "replay_decision_precondition_results.csv", "MISSING_PRECONDITION_RESULTS"),
        (artifact_path / "replay_decision_authority_results.csv", "MISSING_AUTHORITY_RESULTS"),
        (artifact_path / "replay_decision_lineage_results.csv", "MISSING_LINEAGE_RESULTS"),
        (artifact_path / "replay_decision_attestation_results.csv", "MISSING_ATTESTATION_RESULTS"),
        (artifact_path / "pit_source_evidence_results.csv", "MISSING_PIT_SOURCE_RESULTS"),
        (artifact_path / "taxonomy_evidence_results.csv", "MISSING_TAXONOMY_RESULTS"),
        (artifact_path / "leakage_side_effect_guard_results.csv", "MISSING_LEAKAGE_SIDE_EFFECT_RESULTS"),
        (artifact_path / "overclaim_guard_results.csv", "MISSING_OVERCLAIM_GUARD_RESULTS"),
        (artifact_path / "recommended_next_task.md", "MISSING_RECOMMENDED_NEXT_TASK"),
    ]:
        if not _text(path) or not path.exists():
            issues.append(_issue(run_id, "ERROR", code, f"Required replay decision freeze artifact missing: {path}", path))

    if status not in ALLOWED_STATUSES:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_REPLAY_DECISION_FREEZE_STATUS", f"Unknown status: {status}", metadata_path))
    if status == REPLAY_DECISION_FROZEN:
        for field in ["replay_decision_frozen", "replay_decisions_created", "replay_decisions_exist", "replay_decision_artifacts_created"]:
            if not _to_bool(row.get(field)):
                issues.append(_issue(run_id, "ERROR", f"{field.upper()}_REQUIRED_FOR_FROZEN", f"{field} must be true for REPLAY_DECISION_FROZEN.", metadata_path))
        if decision_row_count <= 0:
            issues.append(_issue(run_id, "ERROR", "FROZEN_STATUS_WITHOUT_ROWS", "REPLAY_DECISION_FROZEN requires replay_decision_rows.csv rows.", rows_path))
    elif decision_row_count > 0:
        issues.append(_issue(run_id, "ERROR", "ROWS_EXIST_WITHOUT_FROZEN_STATUS", "Replay decision rows can exist only for REPLAY_DECISION_FROZEN.", rows_path))

    for field in UNSAFE_FALSE_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", f"{field.upper()}_UNEXPECTED", f"Unsafe false-expected field is true: {field}", metadata_path))
    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(run_id, "ERROR", "UNSAFE_REPORT_ONLY_FLAGS", f"Missing or false flag: {field}", metadata_path))

    issues.extend(_decision_row_issues(run_id, rows_path))
    issues.extend(_evidence_issues(run_id, evidence_path))
    issues.extend(_report_overclaim_issues(run_id, Path(_text(row.get("report_path")))))
    return issues


def _decision_row_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        frame = pd.read_csv(path, dtype={"symbol": "string"})
    except Exception as exc:  # pragma: no cover
        return [_issue(run_id, "ERROR", "REPLAY_DECISION_ROWS_UNREADABLE", str(exc), path)]
    if frame.empty:
        return []
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in FORBIDDEN_COLUMN_TOKENS)
    ]
    issues: list[dict[str, Any]] = []
    if forbidden:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "REPLAY_DECISION_ROWS_FORBIDDEN_COLUMNS",
                f"Replay decision rows contain forbidden downstream/action columns: {','.join(forbidden)}",
                path,
            )
        )
    if "decision_label" in frame.columns:
        invalid = sorted(set(str(value) for value in frame["decision_label"].dropna()) - ALLOWED_DECISION_LABELS)
        if invalid:
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "REPLAY_DECISION_LABEL_OUTSIDE_REVIEW_ONLY_SET",
                    f"Decision labels outside review-only set: {','.join(invalid)}",
                    path,
                )
            )
    return issues


def _evidence_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        frame = pd.read_csv(path)
    except Exception as exc:  # pragma: no cover
        return [_issue(run_id, "ERROR", "EVIDENCE_INDEX_UNREADABLE", str(exc), path)]
    if frame.empty:
        return []
    missing = sorted(REQUIRED_EVIDENCE_COLUMNS - set(frame.columns))
    if missing:
        return [
            _issue(
                run_id,
                "ERROR",
                "EVIDENCE_INDEX_REQUIRED_COLUMNS_MISSING",
                f"Evidence index is missing required PIT/source/taxonomy columns: {','.join(missing)}",
                path,
            )
        ]
    return []


def _report_overclaim_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").lower()
    for phrase in OVERCLAIM_PHRASES:
        if phrase in text:
            return [_issue(run_id, "ERROR", "REPORT_OVERCLAIM_UNEXPECTED", f"Report contains forbidden overclaim wording: {phrase}", path)]
    return []


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
                "Replay decision freeze artifacts must stay under outputs/reports/manual_diagnostics.",
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
                "Replay decision freeze artifacts must stay under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: ReplayDecisionFreezeHealthResult) -> None:
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
                "# Replay Decision Freeze Health",
                "",
                "Report-only health check. `REPLAY_DECISION_FROZEN` means frozen decision-time review rows only and must never imply forward labels, training, stock_profile, buy-review eligibility, paper approval, broker/order/message/API/cache/data side effects, or trading.",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                result.health_frame.to_markdown(index=False)
                if not result.health_frame.empty
                else "No replay decision freeze health issues found.",
            ]
        ),
        encoding="utf-8",
    )


def _issue(run_id: str, severity: str, issue_code: str, message: str, artifact_path: str | Path) -> dict[str, Any]:
    return {
        "replay_decision_freeze_run_id": run_id,
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


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
