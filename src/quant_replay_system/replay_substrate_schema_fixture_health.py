"""Health checks for report-only replay substrate schema fixture artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.replay_substrate_schema_fixture import REPLAY_SUBSTRATE_ENTITIES
from quant_replay_system.replay_substrate_schema_fixture_index import (
    build_replay_substrate_schema_fixture_index,
)


HEALTH_COLUMNS = ["fixture_id", "status", "severity", "issue_code", "message", "artifact_path"]
REQUIRED_SAFETY_TRUE_FLAGS = [
    "report_only",
    "diagnostic_only",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_forward_labels_computed",
    "no_weights_trained",
    "no_active_stock_profile_created",
]


@dataclass(frozen=True)
class ReplaySubstrateSchemaFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_replay_substrate_schema_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/health",
) -> ReplaySubstrateSchemaFixtureHealthResult:
    index = build_replay_substrate_schema_fixture_index(root=root, output_dir=Path(output_dir).parent / "index")
    issues: list[dict[str, Any]] = []
    if index.index_frame.empty:
        issues.append(_issue("", "ERROR", "NO_FIXTURE_FOUND", "No replay substrate schema fixture artifacts found.", root))
    for row in index.index_frame.to_dict("records"):
        issues.extend(_issues_for_row(row))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "replay_substrate_schema_fixture_health.csv",
        "health_report": Path(output_dir) / "replay_substrate_schema_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ReplaySubstrateSchemaFixtureHealthResult(
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


def _issues_for_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    fixture_id = _text(row.get("fixture_id"))
    issues: list[dict[str, Any]] = []
    artifact_path = Path(_text(row.get("artifact_path")))
    metadata_path = Path(_text(row.get("metadata_path")))
    report_path = Path(_text(row.get("report_path")))
    entity_status_path = Path(_text(row.get("entity_status_path")))
    validation_issues_path = Path(_text(row.get("validation_issues_path")))
    overclaim_path = Path(_text(row.get("overclaim_guards_path")))

    for path, code in [
        (metadata_path, "MISSING_METADATA"),
        (report_path, "MISSING_REPORT"),
        (entity_status_path, "MISSING_ENTITY_STATUS"),
        (validation_issues_path, "MISSING_VALIDATION_ISSUES"),
        (overclaim_path, "MISSING_OVERCLAIM_GUARDS"),
    ]:
        if not _text(path) or not path.exists():
            issues.append(_issue(fixture_id, "ERROR", code, f"Required artifact missing: {path}", path))

    if _text(row.get("status")) != "PASS":
        issues.append(_issue(fixture_id, "ERROR", "VALIDATION_ISSUES_PRESENT", "Fixture status is not PASS.", artifact_path))
    if _to_int(row.get("entity_count")) != len(REPLAY_SUBSTRATE_ENTITIES):
        issues.append(_issue(fixture_id, "ERROR", "VALIDATION_ISSUES_PRESENT", "Entity count is not 14.", entity_status_path))
    if _to_int(row.get("validation_issue_count")) != 0:
        issues.append(_issue(fixture_id, "ERROR", "VALIDATION_ISSUES_PRESENT", "Validation issues are present.", validation_issues_path))
    if _to_int(row.get("overclaim_guard_total_count")) == 0 or _to_int(row.get("overclaim_guard_pass_count")) != _to_int(row.get("overclaim_guard_total_count")):
        issues.append(_issue(fixture_id, "ERROR", "OVERCLAIM_GUARD_FAILED", "Not all overclaim guards passed.", overclaim_path))
    if _to_bool(row.get("forward_labels_computed")):
        issues.append(_issue(fixture_id, "ERROR", "FORWARD_LABELS_COMPUTED_UNEXPECTED", "Forward labels were unexpectedly computed.", metadata_path))
    if _to_bool(row.get("weights_trained")):
        issues.append(_issue(fixture_id, "ERROR", "WEIGHTS_TRAINED_UNEXPECTED", "Weights were unexpectedly trained.", metadata_path))
    if _to_bool(row.get("active_stock_profile_created")):
        issues.append(_issue(fixture_id, "ERROR", "ACTIVE_STOCK_PROFILE_CREATED_UNEXPECTED", "Active stock profile was unexpectedly created.", metadata_path))
    if _to_bool(row.get("real_buy_review_eligible")):
        issues.append(_issue(fixture_id, "ERROR", "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED", "Real buy-review eligibility is unexpectedly true.", metadata_path))
    missing = _text(row.get("missing_safety_flags"))
    if missing:
        issues.append(_issue(fixture_id, "ERROR", "MISSING_SAFETY_FLAGS", f"Missing safety flags: {missing}", metadata_path))
    for flag in REQUIRED_SAFETY_TRUE_FLAGS:
        if not _to_bool(row.get(flag)):
            issues.append(_issue(fixture_id, "ERROR", "MISSING_SAFETY_FLAGS", f"Safety flag is missing or false: {flag}", metadata_path))
    if _unsafe_path(artifact_path):
        issues.append(_issue(fixture_id, "ERROR", "UNSAFE_OUTPUT_PATH", f"Unsafe output path: {artifact_path}", artifact_path))
    return issues


def _unsafe_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if "raw" in parts and "data" in parts:
        return True
    if "processed" in parts and "data" in parts:
        return True
    if "cache" in parts and "data" in parts:
        return True
    return False


def _write(result: ReplaySubstrateSchemaFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Replay Substrate Schema Fixture Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                "This health view is report-only and does not mutate replay, labels, training, stock profiles, data, or cache.",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues.",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _issue(fixture_id: str, severity: str, code: str, message: str, path: str | Path) -> dict[str, Any]:
    return {
        "fixture_id": fixture_id,
        "status": "OPEN",
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, HEALTH_COLUMNS]


def _audit_metadata(root: str | Path, checked_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "checked_artifact_count": checked_count,
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_forward_labels_computed": True,
        "no_weights_trained": True,
        "no_active_stock_profile_created": True,
        "real_buy_review_eligible": False,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_data_cache_write": True,
        "no_cache_mutation": True,
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
