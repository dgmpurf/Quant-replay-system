"""Health checks for minimal replay input package fixture smoke artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.historical_replay_input_gate_validator import (
    ACTIVE_REPLAY_INPUT_READY,
    REPLAY_INPUT_GATE_PASS_CANDIDATE,
)
from quant_replay_system.minimal_replay_input_package_fixture_smoke_index import (
    build_minimal_replay_input_package_fixture_smoke_index,
)


HEALTH_COLUMNS = ["smoke_run_id", "severity", "issue_code", "message", "artifact_path"]


@dataclass(frozen=True)
class MinimalReplayInputPackageFixtureSmokeHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_minimal_replay_input_package_fixture_smoke_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/minimal_replay_input_package_fixture_smoke_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/minimal_replay_input_package_fixture_smoke_v0_1/health",
) -> MinimalReplayInputPackageFixtureSmokeHealthResult:
    index = build_minimal_replay_input_package_fixture_smoke_index(
        root=root,
        output_dir=Path(output_dir).parent / "index",
    )
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_SMOKE_ARTIFACT_FOUND", "No smoke artifacts found.", root))
    else:
        latest = index.index_frame.sort_values(["generated_at", "smoke_run_id"]).iloc[-1].to_dict()
        issues.extend(_issues_for_latest(latest))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "minimal_replay_input_package_fixture_smoke_health.csv",
        "health_report": Path(output_dir) / "minimal_replay_input_package_fixture_smoke_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = MinimalReplayInputPackageFixtureSmokeHealthResult(
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
    smoke_run_id = _text(row.get("smoke_run_id"))
    metadata_path = Path(_text(row.get("metadata_path")))
    artifact_path = Path(_text(row.get("artifact_path")))
    input_package_path = Path(_text(row.get("input_package_path")))
    issues: list[dict[str, Any]] = []

    required_paths = [
        (metadata_path, "MISSING_METADATA"),
        (Path(_text(row.get("smoke_report_path"))), "MISSING_SMOKE_REPORT"),
        (Path(_text(row.get("validator_result_ref_path"))), "MISSING_VALIDATOR_RESULT_REF"),
        (Path(_text(row.get("expected_pass_candidate_conditions_path"))), "MISSING_EXPECTED_CONDITIONS"),
        (Path(_text(row.get("safety_flag_report_path"))), "MISSING_SAFETY_FLAG_REPORT"),
        (Path(_text(row.get("recommended_next_task_path"))), "MISSING_RECOMMENDED_NEXT_TASK"),
    ]
    for path, code in required_paths:
        if not _text(path) or not path.exists():
            issues.append(_issue(smoke_run_id, "ERROR", code, f"Required smoke artifact missing: {path}", path))

    if _text(row.get("validator_status")) != REPLAY_INPUT_GATE_PASS_CANDIDATE:
        issues.append(
            _issue(
                smoke_run_id,
                "ERROR",
                "VALIDATOR_NOT_PASS_CANDIDATE",
                "Smoke validator status must be REPLAY_INPUT_GATE_PASS_CANDIDATE.",
                metadata_path,
            )
        )
    if not _to_bool(row.get("pass_candidate")):
        issues.append(_issue(smoke_run_id, "ERROR", "PASS_CANDIDATE_FALSE", "Smoke pass_candidate must be true.", metadata_path))
    if _text(row.get("validator_status")) == ACTIVE_REPLAY_INPUT_READY or _text(row.get("validator_workflow_stage")) == ACTIVE_REPLAY_INPUT_READY:
        issues.append(_issue(smoke_run_id, "ERROR", "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED", "ACTIVE_REPLAY_INPUT_READY must not be emitted.", metadata_path))

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
            issues.append(_issue(smoke_run_id, "ERROR", code, f"Unsafe false-expected field is true: {field}", metadata_path))

    for field in ["report_only", "diagnostic_only"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(smoke_run_id, "ERROR", "UNSAFE_REPORT_ONLY_FLAGS", f"Safety flag is missing or false: {field}", metadata_path))
    for field in ["no_live_trading", "no_broker_api", "no_order_placement", "no_message_sent"]:
        if not _to_bool(row.get(field)):
            issues.append(_issue(smoke_run_id, "ERROR", "UNSAFE_TRADING_FLAGS", f"Trading safety flag is missing or false: {field}", metadata_path))

    if not _safe_diagnostics_path(artifact_path) or _unsafe_path(artifact_path):
        issues.append(_issue(smoke_run_id, "ERROR", "UNSAFE_ARTIFACT_PATH", f"Unsafe smoke artifact path: {artifact_path}", artifact_path))
    if not _safe_diagnostics_path(input_package_path) or _unsafe_path(input_package_path):
        issues.append(_issue(smoke_run_id, "ERROR", "UNSAFE_INPUT_PACKAGE_PATH", f"Unsafe input package path: {input_package_path}", input_package_path))
    if _text(artifact_path) and _text(input_package_path) and not _is_relative_to(input_package_path, artifact_path):
        issues.append(_issue(smoke_run_id, "ERROR", "UNSAFE_INPUT_PACKAGE_PATH", "Input package is not under the smoke artifact folder.", input_package_path))
    return issues


def _write(result: MinimalReplayInputPackageFixtureSmokeHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Minimal Replay Input Package Fixture Smoke Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "Report-only health view. It does not run replay, create active replay input, compute forward labels, train weights, create stock profiles, create buy-review eligibility, integrate research-status, write data stores, call APIs, send messages, use broker integration, place orders, or mutate cache.",
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


def _issue(smoke_run_id: str, severity: str, issue_code: str, message: str, artifact_path: str | Path) -> dict[str, Any]:
    return {
        "smoke_run_id": smoke_run_id,
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


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


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


__all__ = [
    "MinimalReplayInputPackageFixtureSmokeHealthResult",
    "check_minimal_replay_input_package_fixture_smoke_health",
]
