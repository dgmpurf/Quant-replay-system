"""Index view for manifest-only Tiny PIT real reviewed LOCAL_CSV preflight artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


VIEW_DIR_NAMES = {"index", "health", "status"}
DEFAULT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_v0_1"
)

INDEX_COLUMNS = [
    "run_id",
    "fixture_id",
    "created_at",
    "runtime_status",
    "status",
    "workflow_stage",
    "health_status",
    "report_only",
    "diagnostic_only",
    "synthetic_only",
    "real_manifest_read",
    "csv_read_level",
    "references_followed",
    "local_file_hash_computed",
    "external_source_validated",
    "pit_admissibility_validated",
    "real_csv_consumed",
    "real_reviewed_csv_package_created",
    "real_package_candidate_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "active_replay_ready",
    "active_replay_input_ready_emitted",
    "replay_execution_allowed",
    "trading_allowed",
    "buy_review_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "artifact_path",
    "report_path",
]


@dataclass(frozen=True)
class TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeIndexResult:
    artifact_count: int
    latest_run_id: str
    latest_runtime_status: str
    latest_health_status: str
    latest_workflow_stage: str
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/index",
) -> TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    latest = _latest_row(frame)
    paths = _paths(output_dir)
    result = TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeIndexResult(
        artifact_count=len(frame),
        latest_run_id=_text(latest.get("run_id")),
        latest_runtime_status=_text(latest.get("runtime_status")) or "NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_INPUT",
        latest_health_status=_text(latest.get("health_status")) or "WARN",
        latest_workflow_stage=_text(latest.get("workflow_stage")),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
    )
    _write(result)
    return result


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Tiny PIT manifest-only preflight root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in _candidate_dirs(root):
        metadata_path = artifact_dir / "metadata.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read manifest-only preflight metadata {metadata_path}: {exc}")
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
    run_id = _text(metadata.get("run_id") or metadata.get("fixture_id") or artifact_dir.name)
    return {
        "run_id": run_id,
        "fixture_id": _text(metadata.get("fixture_id") or run_id),
        "created_at": _text(metadata.get("created_at")),
        "runtime_status": _text(metadata.get("runtime_status") or metadata.get("status")),
        "status": _text(metadata.get("status") or metadata.get("runtime_status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "health_status": _text(metadata.get("health_status")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "synthetic_only": _to_bool(metadata.get("synthetic_only")),
        "real_manifest_read": _to_bool(metadata.get("manifest_read")),
        "csv_read_level": _text(metadata.get("csv_read_level")),
        "references_followed": _to_bool(metadata.get("references_followed")),
        "local_file_hash_computed": _to_bool(metadata.get("local_file_hash_computed")),
        "external_source_validated": _to_bool(metadata.get("external_source_validated")),
        "pit_admissibility_validated": _to_bool(metadata.get("pit_admissibility_validated")),
        "real_csv_consumed": _to_bool(metadata.get("real_csv_consumed")),
        "real_reviewed_csv_package_created": _to_bool(metadata.get("real_reviewed_csv_package_created")),
        "real_package_candidate_created": _to_bool(metadata.get("real_package_candidate_created")),
        "active_reviewed_input_candidate_created": _to_bool(metadata.get("active_reviewed_input_candidate_created")),
        "real_replay_input_created": _to_bool(metadata.get("real_replay_input_created")),
        "active_replay_input": _to_bool(metadata.get("active_replay_input")),
        "active_replay_ready": _to_bool(metadata.get("active_replay_ready")),
        "active_replay_input_ready_emitted": _to_bool(metadata.get("active_replay_input_ready_emitted")),
        "replay_execution_allowed": _to_bool(metadata.get("replay_execution_allowed")),
        "trading_allowed": _to_bool(metadata.get("trading_allowed")),
        "buy_review_allowed": _to_bool(metadata.get("buy_review_allowed")),
        "data_raw_written": _to_bool(metadata.get("data_raw_written")),
        "data_processed_written": _to_bool(metadata.get("data_processed_written")),
        "data_cache_written": _to_bool(metadata.get("data_cache_written")),
        "artifact_path": _text(metadata.get("artifact_path") or artifact_dir),
        "report_path": _text(metadata.get("report_path") or artifact_dir / "preflight_prototype_report.md"),
    }


def _write(result: TinyPitRealReviewedLocalCsvPackageCandidateRealPreflightPrototypeIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(result.artifact_paths["index_csv"], index=False)
    metadata = {
        "index_id": _hash_payload(result.index_frame.to_dict("records")),
        "artifact_count": result.artifact_count,
        "latest_run_id": result.latest_run_id,
        "latest_runtime_status": result.latest_runtime_status,
        "latest_health_status": result.latest_health_status,
        "latest_workflow_stage": result.latest_workflow_stage,
        "warnings": result.warnings,
        "report_only": True,
        "diagnostic_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
    }
    result.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _latest_row(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {}
    return frame.sort_values(["created_at", "run_id"]).iloc[-1].to_dict()


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
        "index_csv": artifact_dir / "tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_index.csv",
        "metadata": artifact_dir / "metadata.json",
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)

