"""Index view for historical replay PIT evidence closure worklist artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_pit_evidence_closure_worklist import OUTPUT_FILES, SAFETY_FALSE_FIELDS


DEFAULT_ROOT = Path("outputs/reports/manual_diagnostics/historical_replay_pit_evidence_closure_worklist_v0_1")
VIEW_DIR_NAMES = {"index", "health", "status"}
STATUS_INDEX_CREATED = "PIT_EVIDENCE_CLOSURE_WORKLIST_INDEX_CREATED_REPORT_ONLY"

INDEX_COLUMNS = [
    "worklist_run_id",
    "signal_date",
    "universe_name",
    "status",
    "health_status",
    "workflow_stage",
    "artifact_path",
    "metadata_path",
    "report_path",
    "worklist_path",
    "summary_path",
    "blocker_summary_path",
    "safety_flags_path",
    "row_count",
    "blocked_count",
    "missing_evidence_count",
    "context_only_count",
    "needs_manual_review_count",
    "no_hit_review_needed_count",
    "no_hit_accepted_context_count",
    "closure_ready_not_pit_approved_count",
    "profile_conflict_count",
    "survivorship_warning_count",
    "symbols_preview",
    "source_artifact_families_seen",
    "recommended_next_task",
    *SAFETY_FALSE_FIELDS,
]


@dataclass(frozen=True)
class HistoricalReplayPitEvidenceClosureWorklistIndexResult:
    artifact_count: int
    rows: list[dict[str, Any]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_historical_replay_pit_evidence_closure_worklist_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplayPitEvidenceClosureWorklistIndexResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "index"
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root_path.exists():
        warnings.append(f"Artifact root does not exist: {root_path}")
    else:
        for artifact_dir in _candidate_dirs(root_path):
            row = _row_from_artifact_dir(artifact_dir)
            if row is not None:
                rows.append(row)
    rows = sorted(rows, key=lambda row: (_text(row.get("worklist_run_id")), _text(row.get("artifact_path"))))
    paths = _paths(out_dir)
    result = HistoricalReplayPitEvidenceClosureWorklistIndexResult(
        artifact_count=len(rows),
        rows=rows,
        artifact_paths=paths,
        warnings=warnings,
    )
    _write(result)
    return result


def _candidate_dirs(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for metadata_path in root.rglob(OUTPUT_FILES["metadata"]):
        artifact_dir = metadata_path.parent
        try:
            relative_parts = artifact_dir.relative_to(root).parts
        except ValueError:
            continue
        if any(part in VIEW_DIR_NAMES or part.startswith("_") for part in relative_parts):
            continue
        candidates.append(artifact_dir)
    return sorted(set(candidates))


def _row_from_artifact_dir(artifact_dir: Path) -> dict[str, Any] | None:
    metadata_path = artifact_dir / OUTPUT_FILES["metadata"]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict):
        return None
    summary = _read_summary(artifact_dir / OUTPUT_FILES["summary"])
    row = {
        "worklist_run_id": _text(metadata.get("worklist_run_id") or artifact_dir.name),
        "signal_date": _text(metadata.get("signal_date") or summary.get("signal_date")),
        "universe_name": _text(metadata.get("universe_name") or summary.get("universe_name")),
        "status": _text(metadata.get("status") or summary.get("status")),
        "health_status": _text(metadata.get("health_status") or summary.get("health_status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "artifact_path": str(artifact_dir),
        "metadata_path": str(metadata_path),
        "report_path": str(artifact_dir / OUTPUT_FILES["report"]),
        "worklist_path": str(artifact_dir / OUTPUT_FILES["worklist"]),
        "summary_path": str(artifact_dir / OUTPUT_FILES["summary"]),
        "blocker_summary_path": str(artifact_dir / OUTPUT_FILES["blocker_summary"]),
        "safety_flags_path": str(artifact_dir / OUTPUT_FILES["safety_flags"]),
        "row_count": _value(metadata.get("row_count"), summary.get("row_count"), 0),
        "blocked_count": _value(metadata.get("blocked_count"), summary.get("blocked_count"), 0),
        "missing_evidence_count": _value(metadata.get("missing_evidence_count"), summary.get("missing_evidence_count"), 0),
        "context_only_count": _value(metadata.get("context_only_count"), summary.get("context_only_count"), 0),
        "needs_manual_review_count": _value(
            metadata.get("needs_manual_review_count"), summary.get("needs_manual_review_count"), 0
        ),
        "no_hit_review_needed_count": _value(metadata.get("no_hit_review_needed_count"), 0),
        "no_hit_accepted_context_count": _value(metadata.get("no_hit_accepted_context_count"), 0),
        "closure_ready_not_pit_approved_count": _value(
            metadata.get("closure_ready_not_pit_approved_count"),
            summary.get("closure_ready_not_pit_approved_count"),
            0,
        ),
        "profile_conflict_count": _value(metadata.get("profile_conflict_count"), summary.get("profile_conflict_count"), 0),
        "survivorship_warning_count": _value(
            metadata.get("survivorship_warning_count"), summary.get("survivorship_warning_count"), 0
        ),
        "symbols_preview": _symbols_preview(artifact_dir / OUTPUT_FILES["worklist"]),
        "source_artifact_families_seen": ";".join(metadata.get("source_artifact_families_seen", []) or []),
        "recommended_next_task": _text(metadata.get("recommended_next_task")),
    }
    row.update({field: _to_bool(metadata.get(field)) for field in SAFETY_FALSE_FIELDS})
    return {column: row.get(column, "") for column in INDEX_COLUMNS}


def _read_summary(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError:
        return {}
    return rows[0] if rows else {}


def _symbols_preview(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            symbols = [_text(row.get("symbol")) for row in csv.DictReader(handle) if _text(row.get("symbol"))]
    except OSError:
        return ""
    return ";".join(symbols[:20])


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "index_csv": output_dir / "historical_replay_pit_evidence_closure_worklist_index.csv",
        "index_md": output_dir / "historical_replay_pit_evidence_closure_worklist_index.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: HistoricalReplayPitEvidenceClosureWorklistIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_csv(result.artifact_paths["index_csv"], INDEX_COLUMNS, result.rows)
    result.artifact_paths["index_md"].write_text(_render_markdown(result), encoding="utf-8")
    result.artifact_paths["metadata_json"].write_text(
        json.dumps(
            {
                "status": STATUS_INDEX_CREATED,
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


def _render_markdown(result: HistoricalReplayPitEvidenceClosureWorklistIndexResult) -> str:
    lines = [
        "# Historical Replay PIT Evidence Closure Worklist Index",
        "",
        f"- Artifact count: `{result.artifact_count}`",
        "- Report-only index; no PIT evidence closure, replay, labels, training, model, buy-review, or trading behavior is created.",
        "",
        "| run_id | status | health_status | row_count | symbols |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result.rows:
        lines.append(
            "| {worklist_run_id} | {status} | {health_status} | {row_count} | {symbols_preview} |".format(
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
