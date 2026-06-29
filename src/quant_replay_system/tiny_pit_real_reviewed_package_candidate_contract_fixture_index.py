"""Index view for Tiny PIT real reviewed package candidate contract fixture artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


VIEW_DIR_NAMES = {"index", "health", "status"}
DEFAULT_ROOT = "outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_package_candidate_contract_fixture_v0_1"
NO_TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE = (
    "NO_TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE"
)

INDEX_COLUMNS = [
    "fixture_id",
    "run_id",
    "created_at",
    "status",
    "health_status",
    "workflow_stage",
    "case_count",
    "pass_candidate_count",
    "warn_count",
    "fail_count",
    "blocker_count",
    "warning_count",
    "report_only",
    "diagnostic_only",
    "synthetic_only",
    "artifact_path",
    "report_path",
    "real_reviewed_csv_package_created",
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
]


@dataclass(frozen=True)
class TinyPitRealReviewedPackageCandidateContractFixtureIndexResult:
    artifact_count: int
    latest_fixture_id: str
    latest_status: str
    latest_health_status: str
    latest_workflow_stage: str
    latest_case_count: int
    latest_pass_candidate_count: int
    latest_blocker_count: int
    latest_warning_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_tiny_pit_real_reviewed_package_candidate_contract_fixture_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/index",
) -> TinyPitRealReviewedPackageCandidateContractFixtureIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    latest = _latest_row(frame)
    paths = _paths(output_dir)
    result = TinyPitRealReviewedPackageCandidateContractFixtureIndexResult(
        artifact_count=len(frame),
        latest_fixture_id=_text(latest.get("fixture_id")),
        latest_status=_text(latest.get("status")) or "NO_REAL_REVIEWED_PACKAGE_CANDIDATE",
        latest_health_status=_text(latest.get("health_status")) or "WARN",
        latest_workflow_stage=(
            _text(latest.get("workflow_stage"))
            or NO_TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE
        ),
        latest_case_count=_to_int(latest.get("case_count")),
        latest_pass_candidate_count=_to_int(latest.get("pass_candidate_count")),
        latest_blocker_count=_to_int(latest.get("blocker_count")),
        latest_warning_count=_to_int(latest.get("warning_count")),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
    )
    _write(result)
    return result


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Tiny PIT real reviewed package candidate contract fixture root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in _candidate_dirs(root):
        metadata_path = artifact_dir / "metadata.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(
                "Could not read Tiny PIT real reviewed package candidate contract fixture "
                f"metadata {metadata_path}: {exc}"
            )
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
    fixture_id = _text(metadata.get("fixture_id")) or artifact_dir.name
    return {
        "fixture_id": fixture_id,
        "run_id": fixture_id,
        "created_at": _text(metadata.get("created_at")),
        "status": _text(metadata.get("status")),
        "health_status": _text(metadata.get("health_status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "case_count": _to_int(metadata.get("case_count")),
        "pass_candidate_count": _to_int(metadata.get("pass_candidate_count") or metadata.get("pass_count")),
        "warn_count": _to_int(metadata.get("warn_count")),
        "fail_count": _to_int(metadata.get("fail_count")),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "synthetic_only": _to_bool(metadata.get("synthetic_only")),
        "artifact_path": _text(metadata.get("artifact_path")) or str(artifact_dir),
        "report_path": _text(metadata.get("report_path"))
        or str(artifact_dir / "real_reviewed_package_candidate_contract_fixture_report.md"),
        "real_reviewed_csv_package_created": _to_bool(metadata.get("real_reviewed_csv_package_created")),
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
    }


def _write(result: TinyPitRealReviewedPackageCandidateContractFixtureIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(result.artifact_paths["index_csv"], index=False)
    metadata = {
        "index_id": _hash_payload(result.index_frame.to_dict("records")),
        "artifact_count": result.artifact_count,
        "latest_fixture_id": result.latest_fixture_id,
        "latest_status": result.latest_status,
        "latest_health_status": result.latest_health_status,
        "latest_workflow_stage": result.latest_workflow_stage,
        "latest_case_count": result.latest_case_count,
        "latest_pass_candidate_count": result.latest_pass_candidate_count,
        "latest_blocker_count": result.latest_blocker_count,
        "latest_warning_count": result.latest_warning_count,
        "warnings": result.warnings,
        "report_only": True,
        "diagnostic_only": True,
        "synthetic_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
    }
    result.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _latest_row(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {}
    return frame.sort_values(["created_at", "fixture_id"]).iloc[-1].to_dict()


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
        "index_csv": artifact_dir / "tiny_pit_real_reviewed_package_candidate_contract_fixture_index.csv",
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


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
