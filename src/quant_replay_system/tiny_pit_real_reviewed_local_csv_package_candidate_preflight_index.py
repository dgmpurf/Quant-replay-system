"""Index view for Tiny PIT reviewed LOCAL_CSV preflight artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight import (
    ACTIVE_INPUT_NONE,
    AVAILABLE_TIME_VALIDATION_NONE,
    ARTIFACT_FILENAMES,
    LIMITATION_REVIEW_NONE,
    NEGATIVE_FALSE_FIELDS,
    OPTIONAL_REFERENCE_NAMES,
    PERMISSION_REVIEW_NONE,
    PIT_ADMISSIBILITY_NONE,
    QUALITY_STATUS_NONE,
    REPLAY_READINESS_NONE,
    REQUIRED_REFERENCE_NAMES,
    REVIEWER_AUTHORITY_NONE,
    REVISION_ID_VALIDATION_NONE,
    SOURCE_HASH_VALIDATION_NONE,
    SOURCE_RELIABILITY_NONE,
)


DEFAULT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_preflight_v0_1"
)
VIEW_DIR_NAMES = {"index", "health", "status"}
CAPABILITY_LEVEL_FIELDS = [
    "preflight_level",
    "package_creation_level",
    "csv_read_level",
    "source_hash_validation_level",
    "revision_id_validation_level",
    "available_time_validation_level",
    "pit_admissibility_level",
    "reviewer_authority_level",
    "quality_status_level",
    "limitation_review_level",
    "permission_review_level",
    "source_reliability_level",
    "active_input_level",
    "replay_readiness_level",
]
CAPABILITY_DEFAULTS = {
    "source_hash_validation_level": SOURCE_HASH_VALIDATION_NONE,
    "revision_id_validation_level": REVISION_ID_VALIDATION_NONE,
    "available_time_validation_level": AVAILABLE_TIME_VALIDATION_NONE,
    "pit_admissibility_level": PIT_ADMISSIBILITY_NONE,
    "reviewer_authority_level": REVIEWER_AUTHORITY_NONE,
    "quality_status_level": QUALITY_STATUS_NONE,
    "limitation_review_level": LIMITATION_REVIEW_NONE,
    "permission_review_level": PERMISSION_REVIEW_NONE,
    "source_reliability_level": SOURCE_RELIABILITY_NONE,
    "active_input_level": ACTIVE_INPUT_NONE,
    "replay_readiness_level": REPLAY_READINESS_NONE,
}
COUNT_FIELDS = [
    "evidence_reference_count",
    "required_reference_count",
    "required_reference_present_count",
    "missing_required_reference_count",
    "optional_reference_count",
    "missing_optional_reference_count",
    "unvalidated_capability_count",
    "promotion_blocker_count",
    "warning_count",
    "issue_count",
]
REFERENCE_PRESENT_FIELDS = [
    f"{name}_present" for name in [*REQUIRED_REFERENCE_NAMES, *OPTIONAL_REFERENCE_NAMES]
]
INDEX_COLUMNS = [
    "run_id",
    "runtime_status",
    "health_status",
    "workflow_stage",
    "artifact_path",
    "metadata_path",
    "report_path",
    "summary_path",
    "issues_path",
    "limitations_path",
    "evidence_reference_matrix_path",
    "forbidden_downstream_flags_path",
    "preflight_id",
    "declared_package_id",
    "report_only",
    "diagnostic_only",
    *CAPABILITY_LEVEL_FIELDS,
    *COUNT_FIELDS,
    *REFERENCE_PRESENT_FIELDS,
    *NEGATIVE_FALSE_FIELDS,
    "recommended_next_task",
]


@dataclass(frozen=True)
class RealReviewedLocalCsvPreflightIndexResult:
    artifact_count: int
    rows: list[dict[str, Any]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_real_reviewed_local_csv_package_candidate_preflight_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/index",
) -> RealReviewedLocalCsvPreflightIndexResult:
    root_path = Path(root)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root_path.exists():
        warnings.append(f"Artifact root does not exist: {root_path}")
    else:
        for artifact_dir in _candidate_dirs(root_path):
            row = _row_from_artifact_dir(artifact_dir)
            if row is not None:
                rows.append(row)
    rows = [_finalize_row(row) for row in rows]
    paths = _paths(output_dir)
    result = RealReviewedLocalCsvPreflightIndexResult(
        artifact_count=len(rows),
        rows=rows,
        artifact_paths=paths,
        warnings=warnings,
    )
    _write(result)
    return result


def _row_from_artifact_dir(artifact_dir: Path) -> dict[str, Any] | None:
    metadata_path = artifact_dir / ARTIFACT_FILENAMES["metadata"]
    try:
        loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(loaded, dict):
        return None
    row: dict[str, Any] = {
        "run_id": _text(loaded.get("run_id") or artifact_dir.name),
        "runtime_status": _text(loaded.get("runtime_status") or loaded.get("status")),
        "health_status": _text(loaded.get("health_status")),
        "workflow_stage": _text(loaded.get("workflow_stage")),
        "artifact_path": str(artifact_dir),
        "metadata_path": str(metadata_path),
        "report_path": str(artifact_dir / ARTIFACT_FILENAMES["report"]),
        "summary_path": str(artifact_dir / ARTIFACT_FILENAMES["summary"]),
        "issues_path": str(artifact_dir / ARTIFACT_FILENAMES["issues"]),
        "limitations_path": str(artifact_dir / ARTIFACT_FILENAMES["limitations"]),
        "evidence_reference_matrix_path": str(
            artifact_dir / ARTIFACT_FILENAMES["evidence_reference_matrix"]
        ),
        "forbidden_downstream_flags_path": str(
            artifact_dir / ARTIFACT_FILENAMES["forbidden_downstream_flags"]
        ),
        "preflight_id": _text(loaded.get("preflight_id")),
        "declared_package_id": _text(loaded.get("declared_package_id")),
        "report_only": _to_bool(loaded.get("report_only")),
        "diagnostic_only": _to_bool(loaded.get("diagnostic_only")),
        "recommended_next_task": _text(loaded.get("recommended_next_task")),
    }
    row.update(
        {field: _text(loaded.get(field) or CAPABILITY_DEFAULTS.get(field, "")) for field in CAPABILITY_LEVEL_FIELDS}
    )
    row.update({field: _to_int(loaded.get(field)) for field in COUNT_FIELDS})
    row.update({field: _to_bool(loaded.get(field)) for field in NEGATIVE_FALSE_FIELDS})
    row.update(_reference_presence(artifact_dir / ARTIFACT_FILENAMES["evidence_reference_matrix"]))
    return row


def _reference_presence(matrix_path: Path) -> dict[str, bool]:
    presence = {field: False for field in REFERENCE_PRESENT_FIELDS}
    try:
        with matrix_path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                reference_name = row.get("reference_name", "")
                field = f"{reference_name}_present"
                if field in presence:
                    presence[field] = _to_bool(row.get("reference_present"))
    except OSError:
        return presence
    return presence


def _candidate_dirs(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and (path / ARTIFACT_FILENAMES["metadata"]).exists()
    )


def _finalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {column: row.get(column, "") for column in INDEX_COLUMNS}


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "index_csv": root / "real_reviewed_local_csv_package_candidate_preflight_index.csv",
        "index_md": root / "real_reviewed_local_csv_package_candidate_preflight_index.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: RealReviewedLocalCsvPreflightIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_rows(result.artifact_paths["index_csv"], INDEX_COLUMNS, result.rows)
    _write_text(result.artifact_paths["index_md"], _index_markdown(result))
    _write_json(
        result.artifact_paths["metadata_json"],
        {
            "artifact_count": result.artifact_count,
            "status": "PASS",
            "warnings": result.warnings,
            "index_csv": str(result.artifact_paths["index_csv"]),
        },
    )


def _index_markdown(result: RealReviewedLocalCsvPreflightIndexResult) -> str:
    lines = [
        "# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Index",
        "",
        f"- artifact_count: {result.artifact_count}",
        "- report_only: true",
        "- diagnostic_only: true",
        "- scope: generated preflight artifacts only",
        "",
    ]
    for row in result.rows:
        lines.extend(
            [
                f"## {row['run_id']}",
                f"- runtime_status: {row['runtime_status']}",
                f"- health_status: {row['health_status']}",
                f"- preflight_id: {row['preflight_id']}",
                "- declared_package_id: metadata only",
                "",
            ]
        )
    return "\n".join(lines)


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows([{column: row.get(column, "") for column in columns} for row in rows])


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
