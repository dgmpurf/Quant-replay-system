"""Index view for tiny PIT admissibility validator contract fixture artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture import (
    SAFETY_FALSE_FLAGS,
    TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED,
)


NO_TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE = "NO_TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE"
TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_INVALID = (
    "TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_INVALID"
)
VIEW_DIR_NAMES = {"index", "health", "status"}

PATH_COLUMNS = [
    "metadata_path",
    "report_path",
    "gate_case_matrix_path",
    "package_section_contract_path",
    "output_status_contract_path",
    "pit_timing_rule_matrix_path",
    "forbidden_interpretation_matrix_path",
    "safety_flags_path",
    "limitations_path",
    "recommended_next_task_path",
]

INDEX_COLUMNS = [
    "tiny_pit_admissibility_validator_contract_fixture_id",
    "created_at",
    "artifact_path",
    "latest_artifact_path",
    "status",
    "workflow_stage",
    "health_status",
    "case_count",
    "package_section_count",
    "gate_group_count",
    "timing_rule_count",
    "validation_issue_count",
    "report_only",
    "diagnostic_only",
    "contract_fixture",
    "forbidden_future_status_present",
    *SAFETY_FALSE_FLAGS,
    *PATH_COLUMNS,
]


@dataclass(frozen=True)
class TinyPitAdmissibilityValidatorContractFixtureIndexResult:
    artifact_count: int
    latest_fixture_id: str
    latest_status: str
    latest_workflow_stage: str
    latest_health_status: str
    latest_artifact_path: str
    latest_case_count: int
    latest_package_section_count: int
    latest_gate_group_count: int
    latest_timing_rule_count: int
    latest_validation_issue_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_tiny_pit_admissibility_validator_contract_fixture_index(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_contract_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_contract_fixture_v0_1/index",
) -> TinyPitAdmissibilityValidatorContractFixtureIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    latest = _latest_row(frame)
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "tiny_pit_admissibility_validator_contract_fixture_index.csv",
        "index_report": Path(output_dir) / "tiny_pit_admissibility_validator_contract_fixture_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = TinyPitAdmissibilityValidatorContractFixtureIndexResult(
        artifact_count=len(frame),
        latest_fixture_id=_text(latest.get("tiny_pit_admissibility_validator_contract_fixture_id")),
        latest_status=_text(latest.get("status")) or "NO_INPUT",
        latest_workflow_stage=_text(latest.get("workflow_stage")) or NO_TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE,
        latest_health_status=_text(latest.get("health_status")) or "PASS",
        latest_artifact_path=_text(latest.get("latest_artifact_path")),
        latest_case_count=_to_int(latest.get("case_count")),
        latest_package_section_count=_to_int(latest.get("package_section_count")),
        latest_gate_group_count=_to_int(latest.get("gate_group_count")),
        latest_timing_rule_count=_to_int(latest.get("timing_rule_count")),
        latest_validation_issue_count=_to_int(latest.get("validation_issue_count")),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_audit_metadata(root, len(frame)),
    )
    write_tiny_pit_admissibility_validator_contract_fixture_index(result)
    return result


def write_tiny_pit_admissibility_validator_contract_fixture_index(
    result: TinyPitAdmissibilityValidatorContractFixtureIndexResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    paths["index_report"].write_text(
        "\n".join(
            [
                "# Tiny PIT Admissibility Validator Contract Fixture Index",
                "",
                "Report-only index view. It does not create real reviewed CSV packages, active reviewed input candidates, PIT validators, replay inputs, evidence bundles, decisions, freezes, forward labels, future-label joins, training datasets, metric computation, signal_score, model training, stock_profile validation, paper validation, buy-review, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, trading, or data writes.",
                "",
                f"- artifact_count: {result.artifact_count}",
                f"- latest_fixture_id: {result.latest_fixture_id}",
                f"- latest_status: {result.latest_status}",
                f"- latest_workflow_stage: {result.latest_workflow_stage}",
                f"- latest_health_status: {result.latest_health_status}",
                f"- latest_case_count: {result.latest_case_count}",
                f"- latest_package_section_count: {result.latest_package_section_count}",
                f"- latest_gate_group_count: {result.latest_gate_group_count}",
                f"- latest_timing_rule_count: {result.latest_timing_rule_count}",
                f"- latest_validation_issue_count: {result.latest_validation_issue_count}",
                f"- latest_artifact_path: {result.latest_artifact_path}",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "index_id": _hash_payload(result.index_frame.to_dict("records")),
        "artifact_count": result.artifact_count,
        "latest_fixture_id": result.latest_fixture_id,
        "latest_status": result.latest_status,
        "latest_workflow_stage": result.latest_workflow_stage,
        "latest_health_status": result.latest_health_status,
        "latest_case_count": result.latest_case_count,
        "latest_package_section_count": result.latest_package_section_count,
        "latest_gate_group_count": result.latest_gate_group_count,
        "latest_timing_rule_count": result.latest_timing_rule_count,
        "latest_validation_issue_count": result.latest_validation_issue_count,
        "latest_artifact_path": result.latest_artifact_path,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Tiny PIT contract fixture root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in _candidate_dirs(root):
        metadata_path = artifact_dir / "metadata.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read tiny PIT fixture metadata {metadata_path}: {exc}")
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


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


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    status = _text(metadata.get("status"))
    health_status = _derived_health_status(metadata, artifact_dir)
    artifact_path = str(artifact_dir)
    return {
        "tiny_pit_admissibility_validator_contract_fixture_id": (
            _text(metadata.get("tiny_pit_admissibility_validator_contract_fixture_id")) or artifact_dir.name
        ),
        "created_at": _artifact_mtime(artifact_dir),
        "artifact_path": artifact_path,
        "latest_artifact_path": artifact_path,
        "status": status if status in {"PASS", "WARN", "FAIL", "NO_INPUT"} else "FAIL",
        "workflow_stage": (
            TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED
            if status == "PASS" and health_status == "PASS"
            else TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_INVALID
        ),
        "health_status": health_status,
        "case_count": _to_int(metadata.get("case_count")),
        "package_section_count": _to_int(metadata.get("package_section_count")),
        "gate_group_count": _to_int(metadata.get("gate_group_count")),
        "timing_rule_count": _to_int(metadata.get("timing_rule_count")),
        "validation_issue_count": _to_int(metadata.get("validation_issue_count")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "contract_fixture": _to_bool(metadata.get("contract_fixture")),
        "forbidden_future_status_present": _forbidden_future_status_present(artifact_dir),
        **{flag: _to_bool(metadata.get(flag)) for flag in SAFETY_FALSE_FLAGS},
        **_artifact_paths(artifact_dir, metadata_path),
    }


def _artifact_paths(artifact_dir: Path, metadata_path: Path) -> dict[str, str]:
    return {
        "metadata_path": str(metadata_path),
        "report_path": str(artifact_dir / "tiny_pit_admissibility_validator_contract_fixture_report.md"),
        "gate_case_matrix_path": str(artifact_dir / "gate_case_matrix.csv"),
        "package_section_contract_path": str(artifact_dir / "package_section_contract.csv"),
        "output_status_contract_path": str(artifact_dir / "output_status_contract.csv"),
        "pit_timing_rule_matrix_path": str(artifact_dir / "pit_timing_rule_matrix.csv"),
        "forbidden_interpretation_matrix_path": str(artifact_dir / "forbidden_interpretation_matrix.csv"),
        "safety_flags_path": str(artifact_dir / "safety_flags.json"),
        "limitations_path": str(artifact_dir / "limitations.md"),
        "recommended_next_task_path": str(artifact_dir / "recommended_next_task.md"),
    }


def _derived_health_status(metadata: dict[str, Any], artifact_dir: Path) -> str:
    if _text(metadata.get("status")) != "PASS":
        return "FAIL"
    if _text(metadata.get("workflow_stage")) != TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED:
        return "FAIL"
    if _to_int(metadata.get("case_count")) != 12:
        return "FAIL"
    if _to_int(metadata.get("package_section_count")) != 12:
        return "FAIL"
    if _to_int(metadata.get("gate_group_count")) != 24:
        return "FAIL"
    if _to_int(metadata.get("timing_rule_count")) != 10:
        return "FAIL"
    if _to_int(metadata.get("validation_issue_count")) != 0:
        return "FAIL"
    if not _to_bool(metadata.get("report_only")) or not _to_bool(metadata.get("diagnostic_only")):
        return "FAIL"
    if not _to_bool(metadata.get("contract_fixture")):
        return "FAIL"
    if any(_to_bool(metadata.get(flag)) for flag in SAFETY_FALSE_FLAGS):
        return "FAIL"
    if _forbidden_future_status_present(artifact_dir):
        return "FAIL"
    return "PASS"


def _forbidden_future_status_present(artifact_dir: Path) -> bool:
    path = artifact_dir / "output_status_contract.csv"
    if not path.exists():
        return False
    try:
        statuses = pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        return True
    forbidden = {
        "ACTIVE_REPLAY_INPUT_READY",
        "REAL_REPLAY_READY",
        "FORWARD_LABEL_READY",
        "TRAINING_READY",
        "STOCK_PROFILE_READY",
        "BUY_REVIEW_READY",
    }
    return bool(forbidden.intersection(set(statuses.get("status_name", []))))


def _latest_row(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {}
    return frame.sort_values(["created_at", "tiny_pit_admissibility_validator_contract_fixture_id"]).iloc[-1].to_dict()


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, INDEX_COLUMNS]


def _artifact_mtime(path: Path) -> str:
    timestamp = path.stat().st_mtime
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def _audit_metadata(root: str | Path, artifact_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "artifact_count": artifact_count,
        "report_only": True,
        "diagnostic_only": True,
        "tiny_pit_admissibility_validator_contract_fixture_index_created": True,
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


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


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_json_safe(inner) for inner in value]
    if isinstance(value, Path):
        return str(value)
    return value
