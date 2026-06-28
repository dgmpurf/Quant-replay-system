"""Index view for reviewed LOCAL_CSV replay prototype input contract fixture artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture import (
    REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED,
    SAFETY_FALSE_FLAGS,
)


NO_REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE = (
    "NO_REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE"
)
REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_INVALID = (
    "REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_INVALID"
)
VIEW_DIR_NAMES = {"index", "health", "status"}

PATH_COLUMNS = [
    "metadata_path",
    "report_path",
    "contract_matrix_path",
    "field_contract_path",
    "pit_rule_matrix_path",
    "lineage_rule_matrix_path",
    "quality_review_rule_matrix_path",
    "forbidden_interpretation_matrix_path",
    "safety_flags_path",
    "recommended_next_task_path",
]

INDEX_COLUMNS = [
    "reviewed_local_csv_replay_prototype_input_contract_fixture_id",
    "created_at",
    "artifact_path",
    "latest_artifact_path",
    "status",
    "workflow_stage",
    "health_status",
    "expected_artifacts",
    "contract_count",
    "validation_issue_count",
    "report_only",
    "diagnostic_only",
    "schema_fixture",
    *SAFETY_FALSE_FLAGS,
    *PATH_COLUMNS,
]


@dataclass(frozen=True)
class ReviewedLocalCsvReplayPrototypeInputContractFixtureIndexResult:
    artifact_count: int
    latest_run_id: str
    latest_status: str
    latest_workflow_stage: str
    latest_health_status: str
    latest_artifact_path: str
    latest_contract_count: int
    latest_validation_issue_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_reviewed_local_csv_replay_prototype_input_contract_fixture_index(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1/index",
) -> ReviewedLocalCsvReplayPrototypeInputContractFixtureIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    latest = _latest_row(frame)
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "reviewed_local_csv_replay_prototype_input_contract_fixture_index.csv",
        "index_report": Path(output_dir) / "reviewed_local_csv_replay_prototype_input_contract_fixture_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ReviewedLocalCsvReplayPrototypeInputContractFixtureIndexResult(
        artifact_count=len(frame),
        latest_run_id=_text(latest.get("reviewed_local_csv_replay_prototype_input_contract_fixture_id")),
        latest_status=_text(latest.get("status")) or "NO_INPUT",
        latest_workflow_stage=(
            _text(latest.get("workflow_stage"))
            or NO_REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE
        ),
        latest_health_status=_text(latest.get("health_status")) or "PASS",
        latest_artifact_path=_text(latest.get("latest_artifact_path")),
        latest_contract_count=_to_int(latest.get("contract_count")),
        latest_validation_issue_count=_to_int(latest.get("validation_issue_count")),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_audit_metadata(root, len(frame)),
    )
    write_reviewed_local_csv_replay_prototype_input_contract_fixture_index(result)
    return result


def write_reviewed_local_csv_replay_prototype_input_contract_fixture_index(
    result: ReviewedLocalCsvReplayPrototypeInputContractFixtureIndexResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    paths["index_report"].write_text(
        "\n".join(
            [
                "# Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Index",
                "",
                "Report-only index view. It does not create real reviewed input packages, PIT validators, replay inputs, replay evidence bundles, replay decisions, replay freezes, forward labels, future-label joins, training datasets, metric computation, signal_score, model training, stock_profile validation, paper validation, buy-review, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, trading, or data writes.",
                "",
                f"- artifact_count: {result.artifact_count}",
                f"- latest_run_id: {result.latest_run_id}",
                f"- latest_status: {result.latest_status}",
                f"- latest_workflow_stage: {result.latest_workflow_stage}",
                f"- latest_health_status: {result.latest_health_status}",
                f"- latest_contract_count: {result.latest_contract_count}",
                f"- latest_validation_issue_count: {result.latest_validation_issue_count}",
                f"- latest_artifact_path: {result.latest_artifact_path}",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "index_id": _hash_payload(result.index_frame.to_dict("records")),
        "artifact_count": result.artifact_count,
        "latest_run_id": result.latest_run_id,
        "latest_status": result.latest_status,
        "latest_workflow_stage": result.latest_workflow_stage,
        "latest_health_status": result.latest_health_status,
        "latest_contract_count": result.latest_contract_count,
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
        return [], [f"Reviewed LOCAL_CSV contract fixture root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in _candidate_dirs(root):
        metadata_path = artifact_dir / "metadata.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read reviewed LOCAL_CSV fixture metadata {metadata_path}: {exc}")
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


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    status = _text(metadata.get("status"))
    health_status = _derived_health_status(metadata)
    artifact_path = str(artifact_dir)
    return {
        "reviewed_local_csv_replay_prototype_input_contract_fixture_id": (
            _text(metadata.get("reviewed_local_csv_replay_prototype_input_contract_fixture_id")) or artifact_dir.name
        ),
        "created_at": _artifact_mtime(artifact_dir),
        "artifact_path": artifact_path,
        "latest_artifact_path": artifact_path,
        "status": status if status in {"PASS", "WARN", "FAIL", "NO_INPUT"} else "FAIL",
        "workflow_stage": (
            REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED
            if status == "PASS" and health_status == "PASS"
            else REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_INVALID
        ),
        "health_status": health_status,
        "expected_artifacts": 10,
        "contract_count": _to_int(metadata.get("contract_count")),
        "validation_issue_count": _to_int(metadata.get("validation_issue_count")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "schema_fixture": _to_bool(metadata.get("schema_fixture")),
        **{flag: _to_bool(metadata.get(flag)) for flag in SAFETY_FALSE_FLAGS},
        **_artifact_paths(artifact_dir, metadata_path),
    }


def _artifact_paths(artifact_dir: Path, metadata_path: Path) -> dict[str, str]:
    return {
        "metadata_path": str(metadata_path),
        "report_path": str(artifact_dir / "reviewed_local_csv_replay_prototype_input_contract_fixture_report.md"),
        "contract_matrix_path": str(artifact_dir / "reviewed_local_csv_contract_matrix.csv"),
        "field_contract_path": str(artifact_dir / "reviewed_local_csv_field_contract.csv"),
        "pit_rule_matrix_path": str(artifact_dir / "reviewed_local_csv_pit_rule_matrix.csv"),
        "lineage_rule_matrix_path": str(artifact_dir / "reviewed_local_csv_lineage_rule_matrix.csv"),
        "quality_review_rule_matrix_path": str(artifact_dir / "reviewed_local_csv_quality_review_rule_matrix.csv"),
        "forbidden_interpretation_matrix_path": str(
            artifact_dir / "reviewed_local_csv_forbidden_interpretation_matrix.csv"
        ),
        "safety_flags_path": str(artifact_dir / "reviewed_local_csv_safety_flags.json"),
        "recommended_next_task_path": str(artifact_dir / "recommended_next_task.md"),
    }


def _derived_health_status(metadata: dict[str, Any]) -> str:
    if _text(metadata.get("status")) != "PASS":
        return "FAIL"
    if _to_int(metadata.get("contract_count")) != 12:
        return "FAIL"
    if _to_int(metadata.get("validation_issue_count")) != 0:
        return "FAIL"
    if not _to_bool(metadata.get("report_only")) or not _to_bool(metadata.get("diagnostic_only")):
        return "FAIL"
    if not _to_bool(metadata.get("schema_fixture")):
        return "FAIL"
    if any(_to_bool(metadata.get(flag)) for flag in SAFETY_FALSE_FLAGS):
        return "FAIL"
    return "PASS"


def _latest_row(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {}
    return frame.sort_values(["created_at", "reviewed_local_csv_replay_prototype_input_contract_fixture_id"]).iloc[-1].to_dict()


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS, dtype=object)
    for column in INDEX_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, INDEX_COLUMNS].astype(object)


def _audit_metadata(root: str | Path, artifact_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "artifact_count": artifact_count,
        "report_only": True,
        "diagnostic_only": True,
        "reviewed_local_csv_replay_prototype_input_contract_fixture_views_created": True,
        **{flag: False for flag in SAFETY_FALSE_FLAGS},
    }


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _hash_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(value), sort_keys=True).encode("utf-8")).hexdigest()[:12]


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

