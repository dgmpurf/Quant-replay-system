"""Health view for tiny PIT admissibility validator contract fixture artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture import (
    REQUIRED_CASES,
    REQUIRED_GATE_GROUPS,
    REQUIRED_PACKAGE_SECTIONS,
    SAFETY_FALSE_FLAGS,
    TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED,
)
from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture_index import VIEW_DIR_NAMES


HEALTH_COLUMNS = ["fixture_id", "status", "severity", "issue_code", "message", "artifact_path"]

REQUIRED_ARTIFACTS = {
    "metadata": "metadata.json",
    "report": "tiny_pit_admissibility_validator_contract_fixture_report.md",
    "gate_case_matrix": "gate_case_matrix.csv",
    "package_section_contract": "package_section_contract.csv",
    "output_status_contract": "output_status_contract.csv",
    "pit_timing_rule_matrix": "pit_timing_rule_matrix.csv",
    "forbidden_interpretation_matrix": "forbidden_interpretation_matrix.csv",
    "safety_flags": "safety_flags.json",
    "limitations": "limitations.md",
    "recommended_next_task": "recommended_next_task.md",
}

FORBIDDEN_FUTURE_STATUSES = {
    "ACTIVE_REPLAY_INPUT_READY",
    "REAL_REPLAY_READY",
    "FORWARD_LABEL_READY",
    "TRAINING_READY",
    "STOCK_PROFILE_READY",
    "BUY_REVIEW_READY",
}


@dataclass(frozen=True)
class TinyPitAdmissibilityValidatorContractFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_tiny_pit_admissibility_validator_contract_fixture_health(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_contract_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_contract_fixture_v0_1/health",
) -> TinyPitAdmissibilityValidatorContractFixtureHealthResult:
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
        "health_csv": Path(output_dir) / "tiny_pit_admissibility_validator_contract_fixture_health.csv",
        "health_report": Path(output_dir) / "tiny_pit_admissibility_validator_contract_fixture_health_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = TinyPitAdmissibilityValidatorContractFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=frame,
        artifact_paths=paths,
        warnings=[] if Path(root).exists() else [f"Tiny PIT contract fixture root does not exist: {root}"],
        audit_metadata=_audit_metadata(root, len(candidate_dirs)),
    )
    _write(result)
    return result


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, Any]]:
    fixture_id = artifact_dir.name
    issues: list[dict[str, Any]] = []
    paths = {key: artifact_dir / filename for key, filename in REQUIRED_ARTIFACTS.items()}
    for path in paths.values():
        if not path.exists():
            issues.append(_issue(fixture_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Required artifact missing: {path}", path))

    metadata: dict[str, Any] | None = None
    if paths["metadata"].exists():
        try:
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_issue(fixture_id, "ERROR", "METADATA_UNREADABLE", f"Metadata cannot be read: {exc}", paths["metadata"]))
    if metadata is not None:
        fixture_id = _text(metadata.get("tiny_pit_admissibility_validator_contract_fixture_id")) or fixture_id
        issues.extend(_metadata_issues(fixture_id, metadata, paths["metadata"]))
    if paths["gate_case_matrix"].exists():
        issues.extend(_gate_case_issues(fixture_id, paths["gate_case_matrix"]))
    if paths["package_section_contract"].exists():
        issues.extend(_package_section_issues(fixture_id, paths["package_section_contract"]))
    if paths["output_status_contract"].exists():
        issues.extend(_output_status_issues(fixture_id, paths["output_status_contract"]))
    if paths["pit_timing_rule_matrix"].exists():
        issues.extend(_pit_timing_rule_issues(fixture_id, paths["pit_timing_rule_matrix"]))
    if paths["safety_flags"].exists():
        issues.extend(_safety_flags_issues(fixture_id, paths["safety_flags"]))
    return issues


def _metadata_issues(fixture_id: str, metadata: dict[str, Any], metadata_path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    status = _text(metadata.get("status"))
    if status not in {"PASS", "WARN", "FAIL", "NO_INPUT"}:
        issues.append(_issue(fixture_id, "ERROR", "UNKNOWN_STATUS", f"Unknown fixture status: {status}", metadata_path))
    if status != "PASS":
        issues.append(_issue(fixture_id, "ERROR", "FIXTURE_STATUS_NOT_PASS", "Fixture metadata status is not PASS.", metadata_path))
    if _text(metadata.get("workflow_stage")) != TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED:
        issues.append(_issue(fixture_id, "ERROR", "WORKFLOW_STAGE_INVALID", "workflow_stage is invalid.", metadata_path))
    if _to_int(metadata.get("case_count")) != 12:
        issues.append(_issue(fixture_id, "ERROR", "CASE_COUNT_NOT_12", "case_count must be 12.", metadata_path))
    if _to_int(metadata.get("package_section_count")) != 12:
        issues.append(_issue(fixture_id, "ERROR", "PACKAGE_SECTION_COUNT_NOT_12", "package_section_count must be 12.", metadata_path))
    if _to_int(metadata.get("gate_group_count")) != 24:
        issues.append(_issue(fixture_id, "ERROR", "GATE_GROUP_COUNT_NOT_24", "gate_group_count must be 24.", metadata_path))
    if _to_int(metadata.get("timing_rule_count")) != 10:
        issues.append(_issue(fixture_id, "ERROR", "TIMING_RULE_COUNT_NOT_10", "timing_rule_count must be 10.", metadata_path))
    if _to_int(metadata.get("validation_issue_count")) != 0:
        issues.append(_issue(fixture_id, "ERROR", "VALIDATION_ISSUE_COUNT_NOT_ZERO", "validation_issue_count must be 0.", metadata_path))
    if not _to_bool(metadata.get("report_only")):
        issues.append(_issue(fixture_id, "ERROR", "METADATA_REPORT_ONLY_NOT_TRUE", "metadata report_only is not true.", metadata_path))
    if not _to_bool(metadata.get("diagnostic_only")):
        issues.append(_issue(fixture_id, "ERROR", "METADATA_DIAGNOSTIC_ONLY_NOT_TRUE", "metadata diagnostic_only is not true.", metadata_path))
    if not _to_bool(metadata.get("contract_fixture")):
        issues.append(_issue(fixture_id, "ERROR", "METADATA_CONTRACT_FIXTURE_NOT_TRUE", "metadata contract_fixture is not true.", metadata_path))
    for flag in SAFETY_FALSE_FLAGS:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(fixture_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{flag} is true.", metadata_path))
    for key, value in (metadata.get("artifact_paths") or {}).items():
        if _unsafe_path_text(value):
            issues.append(_issue(fixture_id, "ERROR", "UNSAFE_ARTIFACT_PATH", f"Unsafe artifact path for {key}: {value}", metadata_path))
    return issues


def _gate_case_issues(fixture_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        cases = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(fixture_id, "ERROR", "GATE_CASE_MATRIX_UNREADABLE", f"gate case matrix cannot be read: {exc}", path)]
    issues: list[dict[str, Any]] = []
    if set(cases.get("case_name", [])) != set(REQUIRED_CASES):
        issues.append(_issue(fixture_id, "ERROR", "GATE_CASES_MISMATCH", "gate case set is invalid.", path))
    observed_gate_groups = {
        part.strip()
        for value in cases.get("gate_groups", [])
        for part in str(value).split(";")
        if part.strip()
    }
    if observed_gate_groups != set(REQUIRED_GATE_GROUPS):
        issues.append(_issue(fixture_id, "ERROR", "GATE_GROUPS_MISMATCH", "gate group set is invalid.", path))
    if _contains_sensitive_text(" ".join(cases.astype(str).to_numpy().ravel().tolist())):
        issues.append(_issue(fixture_id, "ERROR", "SENSITIVE_TEXT_DETECTED", "credential-looking text appears.", path))
    return issues


def _package_section_issues(fixture_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        sections = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(fixture_id, "ERROR", "PACKAGE_SECTION_CONTRACT_UNREADABLE", f"package section contract cannot be read: {exc}", path)]
    if set(sections.get("section_name", [])) != set(REQUIRED_PACKAGE_SECTIONS):
        return [_issue(fixture_id, "ERROR", "PACKAGE_SECTIONS_MISMATCH", "package section set is invalid.", path)]
    return []


def _output_status_issues(fixture_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        statuses = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(fixture_id, "ERROR", "OUTPUT_STATUS_CONTRACT_UNREADABLE", f"output status contract cannot be read: {exc}", path)]
    issues: list[dict[str, Any]] = []
    forbidden_present = FORBIDDEN_FUTURE_STATUSES.intersection(set(statuses.get("status_name", [])))
    if forbidden_present:
        issues.append(
            _issue(
                fixture_id,
                "ERROR",
                "FORBIDDEN_FUTURE_STATUS_PRESENT",
                f"Forbidden future statuses present: {','.join(sorted(forbidden_present))}",
                path,
            )
        )
    for column in [
        "active_replay_input_allowed",
        "labels_allowed",
        "training_allowed",
        "stock_profile_allowed",
        "buy_review_allowed",
        "trading_allowed",
    ]:
        if column in statuses and any(_to_bool(value) for value in statuses[column]):
            issues.append(_issue(fixture_id, "ERROR", "FORBIDDEN_STATUS_PERMISSION_TRUE", f"{column} contains true.", path))
    return issues


def _pit_timing_rule_issues(fixture_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        rules = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        return [_issue(fixture_id, "ERROR", "PIT_TIMING_RULE_MATRIX_UNREADABLE", f"PIT timing rules cannot be read: {exc}", path)]
    if len(rules) != 10:
        return [_issue(fixture_id, "ERROR", "TIMING_RULE_COUNT_NOT_10", "PIT timing rule matrix must contain 10 rows.", path)]
    return []


def _safety_flags_issues(fixture_id: str, path: Path) -> list[dict[str, Any]]:
    try:
        flags = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [_issue(fixture_id, "ERROR", "SAFETY_FLAGS_UNREADABLE", f"safety flags cannot be read: {exc}", path)]
    return [
        _issue(fixture_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{flag} is true.", path)
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
    if (path / "gate_case_matrix.csv").exists():
        return True
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return bool(
        metadata.get("tiny_pit_admissibility_validator_contract_fixture_id")
        or metadata.get("workflow_name") == "tiny_pit_admissibility_validator_contract_fixture"
    )


def _write(result: TinyPitAdmissibilityValidatorContractFixtureHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["health_csv"], index=False)
    paths["health_report"].write_text(
        "\n".join(
            [
                "# Tiny PIT Admissibility Validator Contract Fixture Health",
                "",
                f"- health_status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                "",
                "Report-only health view. It does not create real reviewed CSV packages, active reviewed input candidates, PIT validators, replay inputs, evidence bundles, decisions, freezes, labels, training datasets, metrics, signal_score, models, stock_profile validation, paper validation, buy-review, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, trading, or data writes.",
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


def _issue(fixture_id: str, severity: str, issue_code: str, message: str, artifact_path: Path) -> dict[str, Any]:
    return {
        "fixture_id": fixture_id,
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
        "tiny_pit_admissibility_validator_contract_fixture_health_created": True,
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


def _unsafe_path_text(value: Any) -> bool:
    text = str(value).replace("\\", "/").lower()
    unsafe_tokens = [
        "data/raw",
        "data/processed",
        "data/cache",
        "docs/project_sources",
    ]
    return any(token in text for token in unsafe_tokens)


def _contains_sensitive_text(text: str) -> bool:
    return bool(re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text.lower()))


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_json_safe(inner) for inner in value]
    if isinstance(value, Path):
        return str(value)
    return value
