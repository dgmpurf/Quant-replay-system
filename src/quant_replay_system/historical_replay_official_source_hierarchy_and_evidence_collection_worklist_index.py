"""Index view for official source hierarchy worklist artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_official_source_hierarchy_and_evidence_collection_worklist import (
    DEFAULT_OUTPUT_ROOT,
    OUTPUT_FILES,
    SAFETY_FALSE_FIELDS,
)


DEFAULT_ROOT = DEFAULT_OUTPUT_ROOT
VIEW_DIR_NAMES = {"index", "health", "status"}
STATUS_INDEX_CREATED = "OFFICIAL_SOURCE_HIERARCHY_WORKLIST_INDEX_CREATED_REPORT_ONLY"
NEXT_TASK = (
    "Historical Replay Official Manual Evidence Collection Template Design Report-Only v0.1"
)

INDEX_COLUMNS = [
    "run_id",
    "artifact_path",
    "metadata_path",
    "report_path",
    "runtime_status",
    "health_status",
    "workflow_stage",
    "historical_decision_date",
    "universe_name",
    "row_count",
    "stock_row_count",
    "etf_row_count",
    "source_class_count",
    "evidence_family_count",
    "evidence_collection_worklist_row_count",
    "no_hit_handoff_row_count",
    "blocked_count",
    "profile_conflict_count",
    "survivorship_warning_count",
    "safety_true_count",
    "symbols_preview",
    "recommended_next_task",
    *SAFETY_FALSE_FIELDS,
]


@dataclass(frozen=True)
class HistoricalReplayOfficialSourceHierarchyWorklistIndexResult:
    status: str
    artifact_count: int
    rows: list[dict[str, Any]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplayOfficialSourceHierarchyWorklistIndexResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "index"
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []

    if not root_path.exists():
        warnings.append(f"Artifact root does not exist: {root_path}")
    else:
        for artifact_dir in _candidate_dirs(root_path):
            row = _row_from_artifact_dir(artifact_dir)
            if row is not None:
                rows.append(row)

    rows = sorted(rows, key=lambda row: (_text(row.get("run_id")), _text(row.get("artifact_path"))))
    paths = _paths(out_dir)
    result = HistoricalReplayOfficialSourceHierarchyWorklistIndexResult(
        status=STATUS_INDEX_CREATED,
        artifact_count=len(rows),
        rows=rows,
        artifact_paths=paths,
        warnings=warnings,
    )
    _write(result)
    return result


def _candidate_dirs(root: Path) -> list[Path]:
    candidates: set[Path] = set()
    for metadata_path in root.rglob(OUTPUT_FILES["metadata"]):
        artifact_dir = metadata_path.parent
        try:
            relative_parts = artifact_dir.relative_to(root).parts
        except ValueError:
            continue
        if any(part in VIEW_DIR_NAMES or part.startswith("_") for part in relative_parts):
            continue
        candidates.add(artifact_dir)
    return sorted(candidates)


def _row_from_artifact_dir(artifact_dir: Path) -> dict[str, Any] | None:
    metadata_path = artifact_dir / OUTPUT_FILES["metadata"]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict):
        return None

    row: dict[str, Any] = {
        "run_id": _text(metadata.get("run_id") or artifact_dir.name),
        "artifact_path": str(artifact_dir),
        "metadata_path": str(metadata_path),
        "report_path": _text(metadata.get("report_path")) or str(artifact_dir / OUTPUT_FILES["report"]),
        "runtime_status": _text(metadata.get("runtime_status")),
        "health_status": _text(metadata.get("health_status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "historical_decision_date": _text(metadata.get("historical_decision_date")),
        "universe_name": _text(metadata.get("universe_name")),
        "symbols_preview": _symbols_preview(artifact_dir / OUTPUT_FILES["worklist"]),
        "recommended_next_task": NEXT_TASK,
    }
    for field in INDEX_COLUMNS:
        if field not in row and field not in SAFETY_FALSE_FIELDS:
            row[field] = _value(metadata.get(field), 0)
    row.update({field: _to_bool(metadata.get(field)) for field in SAFETY_FALSE_FIELDS})
    row["safety_true_count"] = sum(1 for field in SAFETY_FALSE_FIELDS if _to_bool(metadata.get(field)))
    return {column: row.get(column, "") for column in INDEX_COLUMNS}


def _symbols_preview(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            symbols = [_text(row.get("symbol")) for row in csv.DictReader(handle) if _text(row.get("symbol"))]
    except OSError:
        return ""
    return ";".join(list(dict.fromkeys(symbols))[:20])


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "index_csv": output_dir
        / "historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index.csv",
        "index_md": output_dir
        / "historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: HistoricalReplayOfficialSourceHierarchyWorklistIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_csv(result.artifact_paths["index_csv"], INDEX_COLUMNS, result.rows)
    result.artifact_paths["index_md"].write_text(_render_markdown(result), encoding="utf-8")
    result.artifact_paths["metadata_json"].write_text(
        json.dumps(
            {
                "status": result.status,
                "artifact_count": result.artifact_count,
                "warnings": result.warnings,
                "report_only": True,
                "diagnostic_only": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _render_markdown(result: HistoricalReplayOfficialSourceHierarchyWorklistIndexResult) -> str:
    lines = [
        "# Historical Replay Official Source Hierarchy and Evidence Collection Worklist Index",
        "",
        f"- Status: `{result.status}`",
        f"- Artifact count: `{result.artifact_count}`",
        "- Report-only index; no official evidence collection, evidence closure, PIT approval, replay, labels, training, model, buy-review, or trading behavior is created.",
        "",
        "| run_id | status | health_status | collection_rows | symbols |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result.rows:
        lines.append(
            "| {run_id} | {runtime_status} | {health_status} | {evidence_collection_worklist_row_count} | {symbols_preview} |".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ")[:240]


def _value(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return ""


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)
