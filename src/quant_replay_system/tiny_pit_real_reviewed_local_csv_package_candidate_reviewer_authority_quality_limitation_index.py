"""Index view for Reviewer Authority / Quality / Limitation artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation import (
    ARTIFACT_FILENAMES,
    REQUIRED_FALSE_FLAGS,
)


DEFAULT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_"
    "quality_limitation_v0_1"
)
VIEW_DIR_NAMES = {"index", "health", "status"}
INDEX_COLUMNS = [
    "run_id",
    "runtime_status",
    "health_status",
    "workflow_stage",
    "artifact_path",
    "metadata_path",
    "report_path",
    "summary_path",
    "limitations_path",
    "issues_path",
    "forbidden_downstream_flags_path",
    "report_only",
    "diagnostic_only",
    "reviewer_authority_level",
    "quality_status_level",
    "limitation_review_level",
    "permission_review_level",
    "package_promotion_level",
    "reviewer_metadata_present",
    "reviewer_id_recorded",
    "reviewer_id_preview",
    "reviewer_role",
    "reviewer_role_supported",
    "reviewer_type",
    "reviewer_attestation_present",
    "reviewer_authority_scope_declared",
    "reviewer_authority_validated",
    "quality_status_present",
    "quality_status_declared",
    "quality_status_validated",
    "quality_issue_count",
    "quality_warning_count",
    "quality_blocker_count",
    "limitations_present",
    "limitation_count",
    "limitation_severity_max",
    "limitation_categories",
    "unresolved_limitation_count",
    "blocking_limitation_count",
    "limitations_overridden_by_reviewer",
    "limitations_overridden_by_quality",
    "permission_class_present",
    "permission_class",
    "legality_flag",
    "permission_class_validated",
    "restricted_use_blocked",
    "private_source_blocked",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "issue_count",
    "warning_count",
    *REQUIRED_FALSE_FLAGS,
    "recommended_next_task",
]


@dataclass(frozen=True)
class ReviewerAuthorityQualityLimitationIndexResult:
    artifact_count: int
    rows: list[dict[str, Any]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_reviewer_authority_quality_limitation_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/index",
) -> ReviewerAuthorityQualityLimitationIndexResult:
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
    result = ReviewerAuthorityQualityLimitationIndexResult(
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
        with metadata_path.open("r", encoding="utf-8") as handle:
            metadata = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict):
        return None
    row = {
        "run_id": _text(metadata.get("run_id") or artifact_dir.name),
        "runtime_status": _text(metadata.get("runtime_status") or metadata.get("status")),
        "health_status": _text(metadata.get("health_status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "artifact_path": str(artifact_dir),
        "metadata_path": str(metadata_path),
        "report_path": str(artifact_dir / ARTIFACT_FILENAMES["report"]),
        "summary_path": str(artifact_dir / ARTIFACT_FILENAMES["summary"]),
        "limitations_path": str(artifact_dir / ARTIFACT_FILENAMES["limitations"]),
        "issues_path": str(artifact_dir / ARTIFACT_FILENAMES["issues"]),
        "forbidden_downstream_flags_path": str(
            artifact_dir / ARTIFACT_FILENAMES["forbidden_downstream_flags"]
        ),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "reviewer_authority_level": _text(metadata.get("reviewer_authority_level")),
        "quality_status_level": _text(metadata.get("quality_status_level")),
        "limitation_review_level": _text(metadata.get("limitation_review_level")),
        "permission_review_level": _text(metadata.get("permission_review_level")),
        "package_promotion_level": _text(metadata.get("package_promotion_level")),
        "reviewer_metadata_present": _to_bool(metadata.get("reviewer_metadata_present")),
        "reviewer_id_recorded": _to_bool(metadata.get("reviewer_id_recorded")),
        "reviewer_id_preview": _preview(metadata.get("reviewer_id_preview")),
        "reviewer_role": _text(metadata.get("reviewer_role")),
        "reviewer_role_supported": _to_bool(metadata.get("reviewer_role_supported")),
        "reviewer_type": _text(metadata.get("reviewer_type")),
        "reviewer_attestation_present": _to_bool(metadata.get("reviewer_attestation_present")),
        "reviewer_authority_scope_declared": _to_bool(
            metadata.get("reviewer_authority_scope_declared")
        ),
        "reviewer_authority_validated": _to_bool(metadata.get("reviewer_authority_validated")),
        "quality_status_present": _to_bool(metadata.get("quality_status_present")),
        "quality_status_declared": _to_bool(metadata.get("quality_status_declared")),
        "quality_status_validated": _to_bool(metadata.get("quality_status_validated")),
        "quality_issue_count": _value(metadata.get("quality_issue_count")),
        "quality_warning_count": _value(metadata.get("quality_warning_count")),
        "quality_blocker_count": _value(metadata.get("quality_blocker_count")),
        "limitations_present": _to_bool(metadata.get("limitations_present")),
        "limitation_count": _value(metadata.get("limitation_count")),
        "limitation_severity_max": _text(metadata.get("limitation_severity_max")),
        "limitation_categories": _list_value(metadata.get("limitation_categories")),
        "unresolved_limitation_count": _value(metadata.get("unresolved_limitation_count")),
        "blocking_limitation_count": _value(metadata.get("blocking_limitation_count")),
        "limitations_overridden_by_reviewer": _to_bool(
            metadata.get("limitations_overridden_by_reviewer")
        ),
        "limitations_overridden_by_quality": _to_bool(
            metadata.get("limitations_overridden_by_quality")
        ),
        "permission_class_present": _to_bool(metadata.get("permission_class_present")),
        "permission_class": _text(metadata.get("permission_class")),
        "legality_flag": _text(metadata.get("legality_flag")),
        "permission_class_validated": _to_bool(metadata.get("permission_class_validated")),
        "restricted_use_blocked": _to_bool(metadata.get("restricted_use_blocked")),
        "private_source_blocked": _to_bool(metadata.get("private_source_blocked")),
        "source_hash_validated": _to_bool(metadata.get("source_hash_validated")),
        "revision_id_validated": _to_bool(metadata.get("revision_id_validated")),
        "available_time_validated": _to_bool(metadata.get("available_time_validated")),
        "pit_admissibility_validated": _to_bool(metadata.get("pit_admissibility_validated")),
        "source_reliability_scored": _to_bool(metadata.get("source_reliability_scored")),
        "issue_count": _value(metadata.get("issue_count")),
        "warning_count": _value(metadata.get("warning_count")),
        "recommended_next_task": _text(metadata.get("recommended_next_task")),
    }
    row.update({flag: _to_bool(metadata.get(flag)) for flag in REQUIRED_FALSE_FLAGS})
    return row


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
        "index_csv": root / "reviewer_quality_limitation_index.csv",
        "index_md": root / "reviewer_quality_limitation_index.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: ReviewerAuthorityQualityLimitationIndexResult) -> None:
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


def _index_markdown(result: ReviewerAuthorityQualityLimitationIndexResult) -> str:
    lines = [
        "# Reviewer Authority Quality Limitation Index",
        "",
        f"- Artifact count: `{result.artifact_count}`",
        "- This index exposes reviewer/quality/limitation metadata context and safety flags only.",
        "- It does not expose full reviewer identity, source content, target CSV text, full hashes, or readiness claims.",
        "",
        "| Run id | Status | Health | Reviewer | Quality declared | Limitation severity | Permission |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in result.rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _text(row.get("run_id")),
                    _text(row.get("runtime_status")),
                    _text(row.get("health_status")),
                    _text(row.get("reviewer_id_preview")),
                    str(_to_bool(row.get("quality_status_declared"))).lower(),
                    _text(row.get("limitation_severity_max")),
                    _text(row.get("permission_class")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def _preview(value: Any) -> str:
    return _text(value)[:16]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _value(value: Any) -> Any:
    if value is None:
        return ""
    return value


def _list_value(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)
