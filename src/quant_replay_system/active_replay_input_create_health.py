"""Health checks for report-only active replay input creation artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_replay_input_create import (
    ACTIVE_REPLAY_INPUT_CREATED,
    ACTIVE_REPLAY_INPUT_CREATION_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_INPUT_FOUND,
    ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_TAXONOMY_BLOCKED,
    NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT,
    READY_FOR_ACTIVE_REPLAY_INPUT_CREATION,
)
from quant_replay_system.active_replay_input_create_index import (
    DEFAULT_ROOT,
    build_active_replay_input_create_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"

ALLOWED_STATUSES = {
    NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT,
    ACTIVE_REPLAY_INPUT_CREATION_INPUT_FOUND,
    ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_TAXONOMY_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED,
    READY_FOR_ACTIVE_REPLAY_INPUT_CREATION,
    ACTIVE_REPLAY_INPUT_CREATED,
}

HEALTH_COLUMNS = ["active_input_creation_run_id", "severity", "issue_code", "message", "artifact_path"]

FALSE_EXPECTED_FIELDS = [
    ("replay_execution_allowed", "REPLAY_EXECUTION_ALLOWED_UNEXPECTED"),
    ("replay_decisions_exist", "REPLAY_DECISIONS_EXIST_UNEXPECTED"),
    ("forward_labels_allowed", "FORWARD_LABELS_ALLOWED_UNEXPECTED"),
    ("forward_labels_exist", "FORWARD_LABELS_EXIST_UNEXPECTED"),
    ("training_allowed", "TRAINING_ALLOWED_UNEXPECTED"),
    ("weights_trained", "WEIGHTS_TRAINED_UNEXPECTED"),
    ("stock_profile_allowed", "STOCK_PROFILE_ALLOWED_UNEXPECTED"),
    ("active_stock_profile_exists", "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED"),
    ("buy_review_allowed", "BUY_REVIEW_ALLOWED_UNEXPECTED"),
    ("real_buy_review_eligible", "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED"),
    ("trading_allowed", "TRADING_ALLOWED_UNEXPECTED"),
    ("order_placed", "ORDER_PLACED_UNEXPECTED"),
    ("broker_api_called", "BROKER_API_CALLED_UNEXPECTED"),
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


@dataclass(frozen=True)
class ActiveReplayInputCreateHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_active_replay_input_create_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveReplayInputCreateHealthResult:
    index = build_active_replay_input_create_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(
            _issue(
                "",
                "ERROR",
                "NO_ACTIVE_REPLAY_INPUT_CREATION_ARTIFACT_FOUND",
                "No active replay input creation artifacts found.",
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
        "health_csv": Path(output_dir) / "active_replay_input_create_health.csv",
        "health_report": Path(output_dir) / "active_replay_input_create_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActiveReplayInputCreateHealthResult(
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
    run_id = _text(row.get("active_input_creation_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata_path = Path(_text(row.get("metadata_path")))
    active_input_path = Path(_text(row.get("active_replay_input_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []

    _ensure_manual_diagnostics_issues(run_id, artifact_path, issues)

    required_paths = [
        (metadata_path, "MISSING_METADATA"),
        (Path(_text(row.get("report_path"))), "MISSING_REPORT"),
        (artifact_path / "active_input_precondition_results.csv", "MISSING_PRECONDITION_RESULTS"),
        (artifact_path / "active_input_authority_results.csv", "MISSING_AUTHORITY_RESULTS"),
        (artifact_path / "active_input_lineage_results.csv", "MISSING_LINEAGE_RESULTS"),
        (artifact_path / "active_input_attestation_results.csv", "MISSING_ATTESTATION_RESULTS"),
        (artifact_path / "pit_source_evidence_results.csv", "MISSING_PIT_SOURCE_RESULTS"),
        (artifact_path / "taxonomy_evidence_results.csv", "MISSING_TAXONOMY_RESULTS"),
        (artifact_path / "leakage_side_effect_guard_results.csv", "MISSING_LEAKAGE_SIDE_EFFECT_RESULTS"),
        (artifact_path / "overclaim_guard_results.csv", "MISSING_OVERCLAIM_GUARD_RESULTS"),
        (artifact_path / "recommended_next_task.md", "MISSING_RECOMMENDED_NEXT_TASK"),
    ]
    for path, code in required_paths:
        if not _text(path) or not path.exists():
            issues.append(_issue(run_id, "ERROR", code, f"Required active-input artifact missing: {path}", path))

    if status not in ALLOWED_STATUSES:
        issues.append(
            _issue(
                run_id,
                "ERROR",
                "UNKNOWN_ACTIVE_REPLAY_INPUT_CREATION_STATUS",
                f"Unknown active replay input creation status: {status}",
                metadata_path,
            )
        )

    if status == ACTIVE_REPLAY_INPUT_CREATED:
        if not _to_bool(row.get("active_replay_input_file_exists")) or not active_input_path.exists():
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "MISSING_ACTIVE_REPLAY_INPUT_FILE",
                    "Created status requires active_replay_input.json.",
                    active_input_path,
                )
            )
        if not _to_bool(row.get("active_replay_input_created")):
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "CREATED_STATUS_WITHOUT_CREATED_FLAG",
                    "ACTIVE_REPLAY_INPUT_CREATED requires active_replay_input_created true.",
                    metadata_path,
                )
            )
        if not _to_bool(row.get("active_replay_input")):
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "CREATED_STATUS_WITHOUT_ACTIVE_INPUT_FLAG",
                    "ACTIVE_REPLAY_INPUT_CREATED requires active_replay_input true.",
                    metadata_path,
                )
            )
    else:
        if _to_bool(row.get("active_replay_input")):
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "ACTIVE_INPUT_TRUE_OUTSIDE_CREATED_STATUS",
                    "active_replay_input can be true only for ACTIVE_REPLAY_INPUT_CREATED.",
                    metadata_path,
                )
            )
        if _to_bool(row.get("active_replay_input_created")):
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "ACTIVE_INPUT_CREATED_TRUE_OUTSIDE_CREATED_STATUS",
                    "active_replay_input_created can be true only for ACTIVE_REPLAY_INPUT_CREATED.",
                    metadata_path,
                )
            )

    for field, code in FALSE_EXPECTED_FIELDS:
        if _to_bool(row.get(field)):
            issues.append(
                _issue(run_id, "ERROR", code, f"Unsafe false-expected field is true: {field}", metadata_path)
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

    if status not in {NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT} and (
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
                "Active input creation artifacts must stay under outputs/reports/manual_diagnostics.",
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
                "Active input creation artifacts must stay under outputs/reports/manual_diagnostics.",
                artifact_path,
            )
        )


def _write(result: ActiveReplayInputCreateHealthResult) -> None:
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
                "# Active Replay Input Creation Health",
                "",
                "Report-only health check. Created active replay input artifacts are allowed only as diagnostics and never imply replay, replay decisions, labels, training, stock_profile, buy-review, API/cache/data side effects, or trading.",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                result.health_frame.to_markdown(index=False)
                if not result.health_frame.empty
                else "No active replay input creation health issues found.",
            ]
        ),
        encoding="utf-8",
    )


def _issue(run_id: str, severity: str, issue_code: str, message: str, artifact_path: str | Path) -> dict[str, Any]:
    return {
        "active_input_creation_run_id": run_id,
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
