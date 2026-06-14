"""Health checks for report-only ACTIVE_REPLAY_INPUT_READY emission-decision artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_replay_input_ready_emission import (
    ACTIVE_REPLAY_INPUT_READY_EMISSION_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT_FOUND,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_TAXONOMY_BLOCKED,
    NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT,
    READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION,
)
from quant_replay_system.active_replay_input_ready_emission_index import (
    DEFAULT_ROOT,
    build_active_replay_input_ready_emission_index,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "health"

ALLOWED_STATUSES = {
    NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT_FOUND,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_TAXONOMY_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW_BLOCKED,
    READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION,
}

HEALTH_COLUMNS = ["active_ready_emission_run_id", "severity", "issue_code", "message", "artifact_path"]


@dataclass(frozen=True)
class ActiveReplayInputReadyEmissionHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_active_replay_input_ready_emission_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveReplayInputReadyEmissionHealthResult:
    index = build_active_replay_input_ready_emission_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(
            _issue(
                "",
                "ERROR",
                "NO_ACTIVE_READY_EMISSION_ARTIFACT_FOUND",
                "No ACTIVE_REPLAY_INPUT_READY emission-decision artifacts found.",
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
        "health_csv": Path(output_dir) / "active_replay_input_ready_emission_health.csv",
        "health_report": Path(output_dir) / "active_replay_input_ready_emission_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActiveReplayInputReadyEmissionHealthResult(
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
    emission_run_id = _text(row.get("active_ready_emission_run_id"))
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata_path = Path(_text(row.get("metadata_path")))
    status = _text(row.get("status"))
    issues: list[dict[str, Any]] = []

    required_paths = [
        (metadata_path, "MISSING_METADATA"),
        (Path(_text(row.get("emission_report_path"))), "MISSING_EMISSION_REPORT"),
        (artifact_path / "final_emission_precondition_results.csv", "MISSING_PRECONDITION_RESULTS"),
        (artifact_path / "final_emission_authority_results.csv", "MISSING_AUTHORITY_RESULTS"),
        (artifact_path / "ready_to_emit_lineage_results.csv", "MISSING_LINEAGE_RESULTS"),
        (artifact_path / "final_emission_attestation_results.csv", "MISSING_ATTESTATION_RESULTS"),
        (artifact_path / "pit_source_evidence_results.csv", "MISSING_PIT_SOURCE_RESULTS"),
        (artifact_path / "taxonomy_evidence_results.csv", "MISSING_TAXONOMY_RESULTS"),
        (artifact_path / "leakage_side_effect_guard_results.csv", "MISSING_LEAKAGE_SIDE_EFFECT_RESULTS"),
        (artifact_path / "overclaim_guard_results.csv", "MISSING_OVERCLAIM_GUARD_RESULTS"),
        (artifact_path / "active_replay_input_ready_emission_candidate.json", "MISSING_EMISSION_CANDIDATE"),
        (artifact_path / "recommended_next_task.md", "MISSING_RECOMMENDED_NEXT_TASK"),
    ]
    for path, code in required_paths:
        if not _text(path) or not path.exists():
            issues.append(
                _issue(emission_run_id, "ERROR", code, f"Required emission-decision artifact missing: {path}", path)
            )

    for path, code in required_paths[2:10]:
        if path.exists():
            issues.extend(_csv_column_issues(emission_run_id, path, code.replace("MISSING", "INVALID")))

    if status == "ACTIVE_REPLAY_INPUT_READY":
        issues.append(
            _issue(
                emission_run_id,
                "ERROR",
                "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED",
                "ACTIVE_REPLAY_INPUT_READY must not be emitted by this workflow.",
                metadata_path,
            )
        )
    elif status not in ALLOWED_STATUSES:
        issues.append(
            _issue(
                emission_run_id,
                "ERROR",
                "UNKNOWN_ACTIVE_READY_EMISSION_STATUS",
                f"Unknown ACTIVE_REPLAY_INPUT_READY emission-decision status: {status}",
                metadata_path,
            )
        )

    if (
        _to_bool(row.get("ready_for_active_replay_input_ready_emission_decision"))
        and status != READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION
    ):
        issues.append(
            _issue(
                emission_run_id,
                "ERROR",
                "READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_INCONSISTENT",
                "ready_for_active_replay_input_ready_emission_decision is true for a non-ready status.",
                metadata_path,
            )
        )

    false_expected = [
        ("active_replay_input_ready", "ACTIVE_REPLAY_INPUT_READY_FLAG_UNEXPECTED"),
        ("active_replay_input", "ACTIVE_REPLAY_INPUT_UNEXPECTED"),
        ("active_ready_emitted", "ACTIVE_READY_EMITTED_UNEXPECTED"),
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
    for field, code in false_expected:
        if _to_bool(row.get(field)):
            issues.append(
                _issue(
                    emission_run_id,
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
                    emission_run_id,
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
                    emission_run_id,
                    "ERROR",
                    "UNSAFE_TRADING_FLAGS",
                    f"Trading safety flag is missing or false: {field}",
                    metadata_path,
                )
            )

    if status != NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT and (
        _to_int(row.get("overclaim_guard_total_count")) <= 0
        or _to_int(row.get("overclaim_guard_pass_count")) != _to_int(row.get("overclaim_guard_total_count"))
    ):
        issues.append(
            _issue(
                emission_run_id,
                "ERROR",
                "OVERCLAIM_GUARD_FAILED",
                "Overclaim guard counts do not fully pass.",
                metadata_path,
            )
        )

    if not _safe_diagnostics_path(artifact_path) or _unsafe_path(artifact_path):
        issues.append(
            _issue(
                emission_run_id,
                "ERROR",
                "UNSAFE_OUTPUT_PATH",
                f"Unsafe emission-decision artifact path: {artifact_path}",
                artifact_path,
            )
        )
    for value in row.values():
        if isinstance(value, str) and value.strip() and _unsafe_path(Path(value)):
            issues.append(
                _issue(
                    emission_run_id,
                    "ERROR",
                    "UNSAFE_OUTPUT_PATH",
                    f"Unsafe path recorded in emission-decision metadata: {value}",
                    metadata_path,
                )
            )
    return issues


def _csv_column_issues(emission_run_id: str, path: Path, issue_code: str) -> list[dict[str, Any]]:
    try:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception as exc:  # pragma: no cover - pandas exception type varies by malformed input
        return [_issue(emission_run_id, "ERROR", issue_code, f"Could not read CSV artifact {path}: {exc}", path)]
    required = {"gate_group", "gate_name", "status", "passed", "blocker_reason", "evidence_path"}
    missing = sorted(required - set(frame.columns))
    if missing:
        return [
            _issue(
                emission_run_id,
                "ERROR",
                issue_code,
                f"CSV artifact is missing required columns {missing}: {path}",
                path,
            )
        ]
    return []


def _write(result: ActiveReplayInputReadyEmissionHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# ACTIVE_REPLAY_INPUT_READY Emission Decision Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "Report-only health view. It does not emit ACTIVE_REPLAY_INPUT_READY, create active replay input, run replay, create replay decisions, compute labels, train weights, create stock_profile artifacts, create real buy-review eligibility, integrate research-status, write data stores, call APIs, send messages, use broker integration, place orders, or mutate cache.",
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
    emission_run_id: str,
    severity: str,
    issue_code: str,
    message: str,
    artifact_path: str | Path,
) -> dict[str, Any]:
    return {
        "active_ready_emission_run_id": emission_run_id,
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
    "ActiveReplayInputReadyEmissionHealthResult",
    "check_active_replay_input_ready_emission_health",
]
