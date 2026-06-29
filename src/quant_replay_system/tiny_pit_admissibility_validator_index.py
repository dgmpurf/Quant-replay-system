"""Index view for synthetic Tiny PIT admissibility validator artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.tiny_pit_admissibility_validator import (
    SAFETY_FALSE_FLAGS,
    TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED,
)


VIEW_DIR_NAMES = {"index", "health", "status"}
NO_TINY_PIT_ADMISSIBILITY_VALIDATOR = "NO_TINY_PIT_ADMISSIBILITY_VALIDATOR"

INDEX_COLUMNS = [
    "validator_run_id",
    "created_at",
    "status",
    "workflow_stage",
    "package_id",
    "package_version",
    "case_count",
    "pass_candidate_count",
    "warning_count",
    "blocker_count",
    "report_only",
    "diagnostic_only",
    "synthetic_only",
    "artifact_path",
    "report_path",
]


@dataclass(frozen=True)
class TinyPitAdmissibilityValidatorIndexResult:
    artifact_count: int
    latest_validator_run_id: str
    latest_status: str
    latest_workflow_stage: str
    latest_case_count: int
    latest_pass_candidate_count: int
    latest_warning_count: int
    latest_blocker_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_tiny_pit_admissibility_validator_index(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_v0_1/index",
) -> TinyPitAdmissibilityValidatorIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    latest = _latest_row(frame)
    paths = _paths(output_dir)
    result = TinyPitAdmissibilityValidatorIndexResult(
        artifact_count=len(frame),
        latest_validator_run_id=_text(latest.get("validator_run_id")),
        latest_status=_text(latest.get("status")) or "NO_INPUT",
        latest_workflow_stage=_text(latest.get("workflow_stage")) or NO_TINY_PIT_ADMISSIBILITY_VALIDATOR,
        latest_case_count=_to_int(latest.get("case_count")),
        latest_pass_candidate_count=_to_int(latest.get("pass_candidate_count")),
        latest_warning_count=_to_int(latest.get("warning_count")),
        latest_blocker_count=_to_int(latest.get("blocker_count")),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
    )
    write_tiny_pit_admissibility_validator_index(result)
    return result


def write_tiny_pit_admissibility_validator_index(result: TinyPitAdmissibilityValidatorIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(result.artifact_paths["index_csv"], index=False)
    metadata = {
        "index_id": _hash_payload(result.index_frame.to_dict("records")),
        "artifact_count": result.artifact_count,
        "latest_validator_run_id": result.latest_validator_run_id,
        "latest_status": result.latest_status,
        "latest_workflow_stage": result.latest_workflow_stage,
        "latest_case_count": result.latest_case_count,
        "latest_pass_candidate_count": result.latest_pass_candidate_count,
        "latest_warning_count": result.latest_warning_count,
        "latest_blocker_count": result.latest_blocker_count,
        "warnings": result.warnings,
        "report_only": True,
        "diagnostic_only": True,
        "synthetic_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
    }
    result.artifact_paths["metadata"].write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Tiny PIT validator root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in _candidate_dirs(root):
        metadata_path = artifact_dir / "metadata.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read tiny PIT validator metadata {metadata_path}: {exc}")
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata))
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
        and (path / "metadata.json").exists()
    )


def _row_from_metadata(artifact_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "validator_run_id": _text(metadata.get("validator_run_id")) or artifact_dir.name,
        "created_at": _text(metadata.get("created_at")),
        "status": _text(metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "package_id": _text(metadata.get("package_id")),
        "package_version": _text(metadata.get("package_version")),
        "case_count": _to_int(metadata.get("case_count")),
        "pass_candidate_count": _to_int(metadata.get("pass_candidate_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "synthetic_only": _to_bool(metadata.get("synthetic_only")),
        "artifact_path": _text(metadata.get("artifact_path")) or str(artifact_dir),
        "report_path": _text(metadata.get("report_path")) or str(artifact_dir / "tiny_pit_admissibility_validator_report.md"),
    }


def _latest_row(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {}
    return frame.sort_values(["created_at", "validator_run_id"]).iloc[-1].to_dict()


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, INDEX_COLUMNS]


def _paths(output_dir: str | Path) -> dict[str, Path]:
    artifact_dir = Path(output_dir)
    return {
        "artifact_dir": artifact_dir,
        "index_csv": artifact_dir / "tiny_pit_admissibility_validator_index.csv",
        "metadata": artifact_dir / "metadata.json",
    }


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


def _text(value: Any) -> str:
    return "" if value is None else str(value)


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
