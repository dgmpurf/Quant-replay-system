"""Health view for reviewed LOCAL_CSV replay prototype input contract fixture artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture import (
    CONTRACT_FILE_NAMES,
    REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED,
    SAFETY_FALSE_FLAGS,
)
from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture_index import VIEW_DIR_NAMES


HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]

REQUIRED_ARTIFACTS = {
    "metadata": "metadata.json",
    "report": "reviewed_local_csv_replay_prototype_input_contract_fixture_report.md",
    "contract_matrix": "reviewed_local_csv_contract_matrix.csv",
    "field_contract": "reviewed_local_csv_field_contract.csv",
    "pit_rule_matrix": "reviewed_local_csv_pit_rule_matrix.csv",
    "lineage_rule_matrix": "reviewed_local_csv_lineage_rule_matrix.csv",
    "quality_review_rule_matrix": "reviewed_local_csv_quality_review_rule_matrix.csv",
    "forbidden_interpretation_matrix": "reviewed_local_csv_forbidden_interpretation_matrix.csv",
    "safety_flags": "reviewed_local_csv_safety_flags.json",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class ReviewedLocalCsvReplayPrototypeInputContractFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_reviewed_local_csv_replay_prototype_input_contract_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1/health",
) -> ReviewedLocalCsvReplayPrototypeInputContractFixtureHealthResult:
    candidate_dirs = _candidate_dirs(Path(root))
    issues: list[dict[str, Any]] = []
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    frame = _finalize(pd.DataFrame(issues))
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARNING").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    paths = {
        "artifact_dir": Path(output_dir),
        "health_csv": Path(output_dir) / "reviewed_local_csv_replay_prototype_input_contract_fixture_health.csv",
        "health_report": Path(output_dir) / "reviewed_local_csv_replay_prototype_input_contract_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ReviewedLocalCsvReplayPrototypeInputContractFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if Path(root).exists() else [f"Reviewed LOCAL_CSV contract fixture root does not exist: {root}"],
        audit_metadata=_audit_metadata(root, len(candidate_dirs)),
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, Any]]:
    run_id = artifact_dir.name
    issues: list[dict[str, Any]] = []
    paths = {key: artifact_dir / filename for key, filename in REQUIRED_ARTIFACTS.items()}
    for path in paths.values():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Required artifact missing: {path}", path))

    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_issue(run_id, "ERROR", "METADATA_UNREADABLE", f"Metadata cannot be read: {exc}", paths["metadata"]))
    if metadata is not None:
        run_id = _text(metadata.get("reviewed_local_csv_replay_prototype_input_contract_fixture_id")) or run_id
        issues.extend(_metadata_issues(run_id, metadata, paths["metadata"]))
    if paths["contract_matrix"].exists():
        issues.extend(_contract_matrix_issues(run_id, paths["contract_matrix"]))
    if paths["field_contract"].exists():
        issues.extend(_field_contract_issues(run_id, paths["field_contract"]))
    if paths["pit_rule_matrix"].exists():
        issues.extend(_pit_rule_issues(run_id, paths["pit_rule_matrix"]))
    if paths["safety_flags"].exists():
        issues.extend(_safety_flags_issues(run_id, paths["safety_flags"]))
    return issues


def _metadata_issues(run_id: str, metadata: dict[str, Any], metadata_path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    status = _text(metadata.get("status"))
    if status not in {"PASS", "WARN", "FAIL", "NO_INPUT"}:
        issues.append(_issue(run_id, "ERROR", "UNKNOWN_STATUS", f"Unknown fixture status: {status}", metadata_path))
    if status != "PASS":
        issues.append(_issue(run_id, "ERROR", "FIXTURE_STATUS_NOT_PASS", "Fixture metadata status is not PASS.", metadata_path))
    if _text(metadata.get("workflow_stage")) != REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED:
        issues.append(_issue(run_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", metadata_path))
    if _to_int(metadata.get("contract_count")) != 12:
        issues.append(_issue(run_id, "ERROR", "CONTRACT_COUNT_NOT_12", "contract_count must be 12.", metadata_path))
    if _to_int(metadata.get("validation_issue_count")) != 0:
        issues.append(
            _issue(run_id, "ERROR", "VALIDATION_ISSUE_COUNT_NOT_ZERO", "validation_issue_count must be 0.", metadata_path)
        )
    if not _to_bool(metadata.get("report_only")):
        issues.append(_issue(run_id, "ERROR", "METADATA_REPORT_ONLY_NOT_TRUE", "metadata report_only is not true.", metadata_path))
    if not _to_bool(metadata.get("diagnostic_only")):
        issues.append(
            _issue(run_id, "ERROR", "METADATA_DIAGNOSTIC_ONLY_NOT_TRUE", "metadata diagnostic_only is not true.", metadata_path)
        )
    if not _to_bool(metadata.get("schema_fixture")):
        issues.append(
            _issue(run_id, "ERROR", "METADATA_SCHEMA_FIXTURE_NOT_TRUE", "metadata schema_fixture is not true.", metadata_path)
        )
    for flag in SAFETY_FALSE_FLAGS:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{flag} is true.", metadata_path))
    for key, value in (metadata.get("artifact_paths") or {}).items():
        if _unsafe_path_text(value):
            issues.append(_issue(run_id, "ERROR", "UNSAFE_ARTIFACT_PATH", f"Unsafe artifact path for {key}: {value}", metadata_path))
    return issues


def _contract_matrix_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        contracts = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(run_id, "ERROR", "CONTRACT_MATRIX_UNREADABLE", f"contract matrix cannot be read: {exc}", path)]
    issues: list[dict[str, Any]] = []
    if len(contracts) != 12:
        issues.append(_issue(run_id, "ERROR", "CONTRACT_COUNT_NOT_12", "contract matrix must contain 12 rows.", path))
    if set(contracts.get("file_name", [])) != set(CONTRACT_FILE_NAMES):
        issues.append(_issue(run_id, "ERROR", "CONTRACT_FILES_MISMATCH", "contract matrix file_name set is invalid.", path))
    if "current_allowed_status" in contracts and "forward_return_label_reviewed.csv" in set(contracts["file_name"]):
        forward_label = contracts.loc[contracts["file_name"] == "forward_return_label_reviewed.csv"].iloc[0]
        if forward_label["current_allowed_status"] != "FUTURE_ONLY_BLOCKED_AS_DECISION_TIME_INPUT":
            issues.append(
                _issue(
                    run_id,
                    "ERROR",
                    "FORWARD_LABEL_NOT_BLOCKED_AS_DECISION_INPUT",
                    "forward_return_label_reviewed.csv must be future-only and blocked as decision-time input.",
                    path,
                )
            )
    if _contains_sensitive_text(" ".join(contracts.astype(str).to_numpy().ravel().tolist())):
        issues.append(_issue(run_id, "ERROR", "SENSITIVE_TEXT_DETECTED", "credential-looking text appears.", path))
    return issues


def _field_contract_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        fields = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(run_id, "ERROR", "FIELD_CONTRACT_UNREADABLE", f"field contract cannot be read: {exc}", path)]
    required = {"source_hash", "revision_id", "available_time", "reviewer_id", "reviewed_at", "review_status"}
    missing = sorted(required - set(fields.get("field_name", [])))
    if missing:
        return [_issue(run_id, "ERROR", "FIELD_CONTRACT_REQUIRED_FIELDS_MISSING", f"missing fields: {','.join(missing)}", path)]
    return []


def _pit_rule_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        rules = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(run_id, "ERROR", "PIT_RULE_MATRIX_UNREADABLE", f"PIT rules cannot be read: {exc}", path)]
    required = {
        "available_time_cutoff",
        "event_date_not_available_time",
        "period_end_not_available_time",
        "publish_time_not_available_time",
        "fetched_at_not_available_time",
        "reviewed_at_audit_only",
        "future_prices_excluded",
        "future_labels_excluded",
        "source_hash_required",
        "revision_id_required",
        "permission_gate_required",
        "quality_gate_required",
        "reviewer_approval_no_pit_override",
    }
    missing = sorted(required - set(rules.get("rule_id", [])))
    if missing:
        return [_issue(run_id, "ERROR", "PIT_RULES_MISSING", f"missing PIT rules: {','.join(missing)}", path)]
    return []


def _safety_flags_issues(run_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        flags = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [_issue(run_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", f"safety flags cannot be read: {exc}", path)]
    return [
        _issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{flag} is true.", path)
        for flag in SAFETY_FALSE_FLAGS
        if _to_bool(flags.get(flag))
    ]


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and _looks_like_fixture_dir(path)
    )


def _looks_like_fixture_dir(path: Path) -> bool:
    metadata_path = path / "metadata.json"
    if not metadata_path.exists():
        return False
    if (path / "reviewed_local_csv_contract_matrix.csv").exists():
        return True
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return bool(
        metadata.get("reviewed_local_csv_replay_prototype_input_contract_fixture_id")
        or metadata.get("workflow_name") == "reviewed_local_csv_replay_prototype_input_contract_fixture"
    )


def _write(result: ReviewedLocalCsvReplayPrototypeInputContractFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Health",
                "",
                f"- health_status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                "",
                "Report-only health view. It does not create real reviewed input packages, PIT validators, replay inputs, evidence bundles, decisions, freezes, labels, training datasets, metrics, signal_score, models, stock_profile validation, paper validation, buy-review, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, trading, or data writes.",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "health_status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, HEALTH_COLUMNS]


def _issue(run_id: str, severity: str, issue_code: str, message: str, artifact_path: Path) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "status": "FAIL" if severity == "ERROR" else "WARN",
        "severity": severity,
        "issue_code": issue_code,
        "message": message,
        "artifact_path": str(artifact_path),
    }


def _audit_metadata(root: str | Path, checked_artifact_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "checked_artifact_count": checked_artifact_count,
        "report_only": True,
        "diagnostic_only": True,
        "reviewed_local_csv_replay_prototype_input_contract_fixture_health_created": True,
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


def _unsafe_path_text(value: Any) -> bool:
    text = str(value).replace("\\", "/").lower()
    unsafe_tokens = [
        "data/raw",
        "data/processed",
        "data/cache",
        "docs/project_sources",
        "current-candidates",
        "snapshot",
        "signal_semantics",
        "model_training",
        "active_weights",
        "active_thresholds",
        "broker",
        "order",
        "trading",
    ]
    return any(token in text for token in unsafe_tokens)


def _contains_sensitive_text(text: str) -> bool:
    return re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text.lower()) is not None


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

