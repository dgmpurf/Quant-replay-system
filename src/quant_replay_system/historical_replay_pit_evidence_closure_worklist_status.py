"""Status view for historical replay PIT evidence closure worklist artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_pit_evidence_closure_worklist import SAFETY_FALSE_FIELDS
from quant_replay_system.historical_replay_pit_evidence_closure_worklist_health import (
    check_historical_replay_pit_evidence_closure_worklist_health,
)
from quant_replay_system.historical_replay_pit_evidence_closure_worklist_index import (
    DEFAULT_ROOT,
    build_historical_replay_pit_evidence_closure_worklist_index,
)


STATUS_CREATED = "PIT_EVIDENCE_CLOSURE_WORKLIST_STATUS_CREATED_REPORT_ONLY"
STATUS_NO_ARTIFACTS = "PIT_EVIDENCE_CLOSURE_WORKLIST_STATUS_NO_ARTIFACTS"
NEXT_TASK = "Historical Replay PIT Evidence Closure Worklist CLI Report-Only v0.1"

STATUS_COLUMNS = [
    "latest_worklist_run_id",
    "latest_status",
    "latest_health_status",
    "latest_workflow_stage",
    "latest_signal_date",
    "latest_universe_name",
    "latest_artifact_path",
    "latest_report_path",
    "latest_metadata_path",
    "latest_row_count",
    "latest_blocked_count",
    "latest_missing_evidence_count",
    "latest_needs_manual_review_count",
    "latest_no_hit_review_needed_count",
    "latest_closure_ready_not_pit_approved_count",
    "latest_profile_conflict_count",
    "latest_survivorship_warning_count",
    "report_only",
    "diagnostic_only",
    *[f"latest_{field}" for field in SAFETY_FALSE_FIELDS],
    "recommended_next_task",
]


@dataclass(frozen=True)
class HistoricalReplayPitEvidenceClosureWorklistStatusResult:
    latest_worklist_run_id: str
    latest_status: str
    latest_health_status: str
    latest_workflow_stage: str
    recommended_next_task: str
    summary: dict[str, Any]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def run_historical_replay_pit_evidence_closure_worklist_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplayPitEvidenceClosureWorklistStatusResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "status"
    sibling_root = out_dir.parent
    index = build_historical_replay_pit_evidence_closure_worklist_index(root=root_path, output_dir=sibling_root / "index")
    health = check_historical_replay_pit_evidence_closure_worklist_health(root=root_path, output_dir=sibling_root / "health")
    if index.rows:
        latest = sorted(index.rows, key=lambda row: str(row.get("worklist_run_id", "")))[-1]
        summary = _summary_from_latest(latest, health.status)
    else:
        summary = _no_artifact_summary(health.status)
    paths = _paths(out_dir)
    result = HistoricalReplayPitEvidenceClosureWorklistStatusResult(
        latest_worklist_run_id=str(summary.get("latest_worklist_run_id", "")),
        latest_status=str(summary.get("latest_status", "")),
        latest_health_status=str(summary.get("latest_health_status", "")),
        latest_workflow_stage=str(summary.get("latest_workflow_stage", "")),
        recommended_next_task=NEXT_TASK,
        summary=summary,
        artifact_paths=paths,
        warnings=[] if health.status.endswith("PASS_REPORT_ONLY") else [f"Historical replay PIT worklist health is {health.status}."],
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "latest_worklist_run_id": latest.get("worklist_run_id", ""),
        "latest_status": latest.get("status", ""),
        "latest_health_status": health_status,
        "latest_workflow_stage": latest.get("workflow_stage", ""),
        "latest_signal_date": latest.get("signal_date", ""),
        "latest_universe_name": latest.get("universe_name", ""),
        "latest_artifact_path": latest.get("artifact_path", ""),
        "latest_report_path": latest.get("report_path", ""),
        "latest_metadata_path": latest.get("metadata_path", ""),
        "latest_row_count": latest.get("row_count", 0),
        "latest_blocked_count": latest.get("blocked_count", 0),
        "latest_missing_evidence_count": latest.get("missing_evidence_count", 0),
        "latest_needs_manual_review_count": latest.get("needs_manual_review_count", 0),
        "latest_no_hit_review_needed_count": latest.get("no_hit_review_needed_count", 0),
        "latest_closure_ready_not_pit_approved_count": latest.get("closure_ready_not_pit_approved_count", 0),
        "latest_profile_conflict_count": latest.get("profile_conflict_count", 0),
        "latest_survivorship_warning_count": latest.get("survivorship_warning_count", 0),
        "report_only": True,
        "diagnostic_only": True,
        "recommended_next_task": NEXT_TASK,
    }
    for field in SAFETY_FALSE_FIELDS:
        summary[f"latest_{field}"] = _to_bool(latest.get(field))
    return {column: summary.get(column, "") for column in STATUS_COLUMNS}


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    summary = {column: "" for column in STATUS_COLUMNS}
    summary.update(
        {
            "latest_status": STATUS_NO_ARTIFACTS,
            "latest_health_status": health_status,
            "latest_workflow_stage": STATUS_NO_ARTIFACTS,
            "report_only": True,
            "diagnostic_only": True,
            "recommended_next_task": NEXT_TASK,
        }
    )
    for field in SAFETY_FALSE_FIELDS:
        summary[f"latest_{field}"] = False
    return summary


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "status_csv": output_dir / "historical_replay_pit_evidence_closure_worklist_status.csv",
        "status_md": output_dir / "historical_replay_pit_evidence_closure_worklist_status.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: HistoricalReplayPitEvidenceClosureWorklistStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    with result.artifact_paths["status_csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=STATUS_COLUMNS)
        writer.writeheader()
        writer.writerow(result.summary)
    result.artifact_paths["status_md"].write_text(_render_markdown(result), encoding="utf-8")
    result.artifact_paths["metadata_json"].write_text(
        json.dumps(
            {
                "status": STATUS_CREATED,
                "latest_worklist_run_id": result.latest_worklist_run_id,
                "latest_status": result.latest_status,
                "latest_health_status": result.latest_health_status,
                "latest_workflow_stage": result.latest_workflow_stage,
                "summary": result.summary,
                "recommended_next_task": result.recommended_next_task,
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


def _render_markdown(result: HistoricalReplayPitEvidenceClosureWorklistStatusResult) -> str:
    return "\n".join(
        [
            "# Historical Replay PIT Evidence Closure Worklist Status",
            "",
            f"- Latest run id: `{result.latest_worklist_run_id}`",
            f"- Latest status: `{result.latest_status}`",
            f"- Latest health status: `{result.latest_health_status}`",
            f"- Latest workflow stage: `{result.latest_workflow_stage}`",
            f"- Recommended next task: `{NEXT_TASK}`",
            "- Report-only status; no PIT evidence closure, replay, labels, training, model, buy-review, trading, or protected data-write behavior is authorized.",
            "",
        ]
    )


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)
