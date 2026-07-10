"""Safe index view for source/evidence sufficiency policy fixture runs."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture import (
    DEFAULT_OUTPUT_ROOT,
    OUTPUT_FILES,
    RECOMMENDED_NEXT_TASK,
    SAFETY_FALSE_FIELDS,
    STATUS_CREATED as CORE_STATUS_CREATED,
    WORKFLOW_STAGE,
    _validate_output_root,
)


DEFAULT_ROOT = DEFAULT_OUTPUT_ROOT
VIEW_DIR_NAMES = {"index", "health", "status"}
STATUS_INDEX_CREATED = (
    "SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_INDEX_CREATED_REPORT_ONLY"
)
NEXT_TASK = RECOMMENDED_NEXT_TASK

INDEX_COLUMNS = [
    "run_id",
    "artifact_path",
    "metadata_path",
    "report_path",
    "runtime_status",
    "health_status",
    "workflow_stage",
    "historical_decision_date",
    "legacy_universe_label",
    "row_count",
    "stock_row_count",
    "etf_row_count",
    "evidence_family_count",
    "row_evidence_family_contract_count",
    "applicable_contract_row_count",
    "instrument_not_applicable_context_row_count",
    "profile_conflict_count",
    "profile_aligned_context_count",
    "unresolved_profile_conflict_count",
    "selected_row_with_blocker_count",
    "sufficiency_candidate_count",
    "evidence_accepted_count",
    "evidence_closed_count",
    "pit_admissible_count",
    "replay_ready_count",
    "safety_true_count",
    "symbols_preview",
    "report_only",
    "diagnostic_only",
    "local_only",
    "synthetic_only",
    *SAFETY_FALSE_FIELDS,
    "recommended_next_task",
]


@dataclass(frozen=True)
class HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureIndexResult:
    status: str
    artifact_count: int
    rows: list[dict[str, Any]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_historical_replay_source_evidence_sufficiency_policy_contract_fixture_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureIndexResult:
    root_path = _validate_output_root(Path(root))
    out_dir = _view_dir(root_path, output_dir, "index")
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    if not root_path.exists():
        warnings.append("Fixture artifact root does not exist.")
    else:
        for artifact_dir in _candidate_dirs(root_path):
            row = _row_from_artifact_dir(root_path, artifact_dir)
            if row is not None:
                rows.append(row)
    rows.sort(key=lambda row: (str(row["run_id"]), str(row["artifact_path"])))
    result = HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureIndexResult(
        status=STATUS_INDEX_CREATED,
        artifact_count=len(rows),
        rows=rows,
        artifact_paths=_paths(out_dir),
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


def _row_from_artifact_dir(root: Path, artifact_dir: Path) -> dict[str, Any] | None:
    metadata_path = artifact_dir / OUTPUT_FILES["metadata"]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict):
        return None
    if metadata.get("runtime_status") != CORE_STATUS_CREATED:
        return None
    if metadata.get("workflow_stage") != WORKFLOW_STAGE:
        return None
    relative_dir = artifact_dir.relative_to(root).as_posix()
    row: dict[str, Any] = {
        "run_id": _text(metadata.get("run_id") or artifact_dir.name),
        "artifact_path": relative_dir,
        "metadata_path": f"{relative_dir}/{OUTPUT_FILES['metadata']}",
        "report_path": f"{relative_dir}/{OUTPUT_FILES['report']}",
        "runtime_status": _text(metadata.get("runtime_status")),
        "health_status": _text(metadata.get("health_status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "historical_decision_date": _text(metadata.get("historical_decision_date")),
        "legacy_universe_label": _text(metadata.get("legacy_universe_label")),
        "symbols_preview": _text(metadata.get("symbols_preview")),
        "recommended_next_task": NEXT_TASK,
    }
    for column in INDEX_COLUMNS:
        if column in row:
            continue
        if column in SAFETY_FALSE_FIELDS:
            row[column] = _to_bool(metadata.get(column))
        elif column in {"report_only", "diagnostic_only", "local_only", "synthetic_only"}:
            row[column] = _to_bool(metadata.get(column))
        else:
            row[column] = metadata.get(column, 0)
    row["safety_true_count"] = sum(
        1 for field in SAFETY_FALSE_FIELDS if _to_bool(metadata.get(field))
    )
    return {column: row.get(column, "") for column in INDEX_COLUMNS}


def _view_dir(root: Path, output_dir: str | Path | None, name: str) -> Path:
    out_dir = (Path(output_dir).resolve() if output_dir is not None else root / name)
    _validate_output_root(out_dir)
    try:
        out_dir.relative_to(root)
    except ValueError as exc:
        raise ValueError("view output directory must remain under the requested root") from exc
    return out_dir


def _paths(output_dir: Path) -> dict[str, Path]:
    stem = "historical_replay_source_evidence_sufficiency_policy_contract_fixture_index"
    return {
        "artifact_dir": output_dir,
        "index_csv": output_dir / f"{stem}.csv",
        "index_md": output_dir / f"{stem}.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(
    result: HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureIndexResult,
) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    with result.artifact_paths["index_csv"].open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_COLUMNS)
        writer.writeheader()
        writer.writerows(result.rows)
    result.artifact_paths["index_md"].write_text(
        _render_markdown(result), encoding="utf-8"
    )
    result.artifact_paths["metadata_json"].write_text(
        json.dumps(
            {
                "status": result.status,
                "artifact_count": result.artifact_count,
                "warnings": result.warnings,
                "report_only": True,
                "diagnostic_only": True,
                "recommended_next_task": NEXT_TASK,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _render_markdown(
    result: HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureIndexResult,
) -> str:
    lines = [
        "# Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Index",
        "",
        f"- Status: `{result.status}`",
        f"- Artifact count: `{result.artifact_count}`",
        "- Relative report-only references only; artifact existence is not evidence sufficiency, acceptance, closure, PIT approval, or replay readiness.",
        "",
        "| run_id | status | health | rows | STOCK | ETF | families | contracts | applicable | N/A | blockers | safety true |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result.rows:
        lines.append(
            "| {run_id} | {runtime_status} | {health_status} | {row_count} | {stock_row_count} | {etf_row_count} | {evidence_family_count} | {row_evidence_family_contract_count} | {applicable_contract_row_count} | {instrument_not_applicable_context_row_count} | {selected_row_with_blocker_count} | {safety_true_count} |".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ")[:240]


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)
