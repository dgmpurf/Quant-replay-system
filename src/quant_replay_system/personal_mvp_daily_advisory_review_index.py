"""Index view for Personal MVP daily advisory review report-only artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.personal_mvp_daily_advisory_review import OUTPUT_FILES, REQUIRED_FALSE_SAFETY_FIELDS


DEFAULT_ROOT = Path("outputs/reports/personal_mvp_daily_advisory_review")
VIEW_DIR_NAMES = {"index", "health", "status"}
INDEX_COLUMNS = [
    "daily_review_run_id",
    "status",
    "health_status",
    "workflow_stage",
    "artifact_path",
    "metadata_path",
    "report_path",
    "rows_path",
    "summary_path",
    "drilldown_path",
    "checklist_path",
    "safety_flags_path",
    "review_date",
    "generated_at",
    "row_count",
    "watch_count",
    "review_buy_candidate_count",
    "review_sell_candidate_count",
    "hold_review_count",
    "no_action_count",
    "blocked_count",
    "demo_count",
    "not_found_count",
    "stale_artifact_count",
    "missing_artifact_count",
    "warning_count",
    "symbols_preview",
    "report_only",
    "diagnostic_only",
    "local_only",
    "manual_confirmation_required",
    *REQUIRED_FALSE_SAFETY_FIELDS,
    "recommended_next_manual_action",
]


@dataclass(frozen=True)
class PersonalMvpDailyAdvisoryReviewIndexResult:
    artifact_count: int
    rows: list[dict[str, Any]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_personal_mvp_daily_advisory_review_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> PersonalMvpDailyAdvisoryReviewIndexResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "index"
    _validate_output_dir(out_dir)
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    if not root_path.exists():
        warnings.append(f"Artifact root does not exist: {root_path}")
    else:
        for artifact_dir in _candidate_dirs(root_path):
            row = _row_from_artifact_dir(artifact_dir)
            if row is not None:
                rows.append(row)
    rows = sorted(rows, key=lambda row: (_text(row.get("generated_at")), _text(row.get("daily_review_run_id"))))
    paths = _paths(out_dir)
    result = PersonalMvpDailyAdvisoryReviewIndexResult(
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
        if any(part in VIEW_DIR_NAMES or part.startswith("_") for part in artifact_dir.relative_to(root).parts):
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
    summary = _read_summary(artifact_dir / OUTPUT_FILES["daily_advisory_review_summary"])
    row = {
        "daily_review_run_id": _text(metadata.get("daily_review_run_id") or artifact_dir.name),
        "status": _text(metadata.get("status")),
        "health_status": _text(metadata.get("health_status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "artifact_path": str(artifact_dir),
        "metadata_path": str(metadata_path),
        "report_path": str(artifact_dir / OUTPUT_FILES["daily_advisory_review_report"]),
        "rows_path": str(artifact_dir / OUTPUT_FILES["daily_advisory_review_rows"]),
        "summary_path": str(artifact_dir / OUTPUT_FILES["daily_advisory_review_summary"]),
        "drilldown_path": str(artifact_dir / OUTPUT_FILES["single_symbol_drilldown_index"]),
        "checklist_path": str(artifact_dir / OUTPUT_FILES["manual_review_checklist"]),
        "safety_flags_path": str(artifact_dir / OUTPUT_FILES["safety_flags"]),
        "review_date": _text(metadata.get("review_date") or summary.get("review_date")),
        "generated_at": _text(metadata.get("generated_at")),
        "row_count": _value(metadata.get("row_count"), summary.get("row_count")),
        "watch_count": _value(summary.get("watch_count"), 0),
        "review_buy_candidate_count": _value(summary.get("review_buy_candidate_count"), 0),
        "review_sell_candidate_count": _value(summary.get("review_sell_candidate_count"), 0),
        "hold_review_count": _value(summary.get("hold_review_count"), 0),
        "no_action_count": _value(summary.get("no_action_count"), 0),
        "blocked_count": _value(summary.get("blocked_count"), 0),
        "demo_count": _value(summary.get("demo_count"), 0),
        "not_found_count": _value(summary.get("not_found_count"), 0),
        "stale_artifact_count": _value(summary.get("stale_artifact_count"), 0),
        "missing_artifact_count": _value(summary.get("missing_artifact_count"), 0),
        "warning_count": _value(metadata.get("warning_count"), summary.get("warning_count")),
        "symbols_preview": _symbols_preview(artifact_dir / OUTPUT_FILES["daily_advisory_review_rows"]),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "local_only": _to_bool(metadata.get("local_only")),
        "manual_confirmation_required": _to_bool(metadata.get("manual_confirmation_required")),
        "recommended_next_manual_action": _text(
            metadata.get("recommended_next_manual_action") or summary.get("recommended_next_manual_action")
        ),
    }
    row.update({field: _to_bool(metadata.get(field)) for field in REQUIRED_FALSE_SAFETY_FIELDS})
    return _finalize_row(row)


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
            reader = csv.DictReader(handle)
            symbols = [_text(row.get("symbol")) for row in reader if _text(row.get("symbol"))]
    except OSError:
        return ""
    return ";".join(symbols[:20])


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "index_csv": output_dir / "personal_mvp_daily_advisory_review_index.csv",
        "index_md": output_dir / "personal_mvp_daily_advisory_review_index.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: PersonalMvpDailyAdvisoryReviewIndexResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_rows(result.artifact_paths["index_csv"], INDEX_COLUMNS, result.rows)
    result.artifact_paths["index_md"].write_text(_render_markdown(result), encoding="utf-8")
    result.artifact_paths["metadata_json"].write_text(
        json.dumps(
            {
                "status": "PASS",
                "artifact_count": result.artifact_count,
                "index_csv": str(result.artifact_paths["index_csv"]),
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


def _render_markdown(result: PersonalMvpDailyAdvisoryReviewIndexResult) -> str:
    lines = [
        "# Personal MVP Daily Advisory Review Index",
        "",
        f"- Artifact count: `{result.artifact_count}`",
        "- Report-only local advisory review artifacts only.",
        "- No buy-review, broker, order, message, trading, replay, labels, training, model, stock_profile, or protected data-write behavior is created.",
        "",
        "| run_id | status | health_status | row_count | symbols |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result.rows:
        lines.append(
            "| {daily_review_run_id} | {status} | {health_status} | {row_count} | {symbols_preview} |".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _finalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {column: row.get(column, "") for column in INDEX_COLUMNS}


def _validate_output_dir(path: Path) -> None:
    resolved = path.resolve()
    cwd = Path.cwd().resolve()
    for protected in [
        cwd / "data" / "raw",
        cwd / "data" / "processed",
        cwd / "data" / "cache",
        cwd / "docs" / "project_sources",
    ]:
        if resolved == protected or _is_relative_to(resolved, protected):
            raise ValueError(f"Refusing protected output path: {path}")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ")[:240]


def _value(primary: Any, fallback: Any = "") -> Any:
    return fallback if primary in {None, ""} else primary


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)
