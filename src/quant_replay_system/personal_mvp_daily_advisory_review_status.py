"""Status view for Personal MVP daily advisory review report-only artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.personal_mvp_daily_advisory_review import REQUIRED_FALSE_SAFETY_FIELDS
from quant_replay_system.personal_mvp_daily_advisory_review_health import check_personal_mvp_daily_advisory_review_health
from quant_replay_system.personal_mvp_daily_advisory_review_index import (
    DEFAULT_ROOT,
    build_personal_mvp_daily_advisory_review_index,
)


NO_ARTIFACT_STATUS = "DAILY_ADVISORY_REVIEW_NO_ARTIFACT"
NEXT_TASK = "Personal MVP Daily Advisory Review Surface Research-Status Integration Planning Report-Only v0.1"
STATUS_COLUMNS = [
    "latest_daily_review_run_id",
    "latest_status",
    "latest_health_status",
    "latest_workflow_stage",
    "latest_artifact_path",
    "latest_report_path",
    "latest_metadata_path",
    "latest_review_date",
    "latest_row_count",
    "latest_watch_count",
    "latest_review_buy_candidate_count",
    "latest_review_sell_candidate_count",
    "latest_hold_review_count",
    "latest_no_action_count",
    "latest_blocked_count",
    "latest_demo_count",
    "latest_not_found_count",
    "latest_stale_artifact_count",
    "latest_missing_artifact_count",
    "latest_warning_count",
    "report_only",
    "diagnostic_only",
    "local_only",
    "manual_confirmation_required",
    *[f"latest_{field}" for field in REQUIRED_FALSE_SAFETY_FIELDS],
    "recommended_next_task",
]


@dataclass(frozen=True)
class PersonalMvpDailyAdvisoryReviewStatusResult:
    latest_daily_review_run_id: str
    latest_status: str
    latest_health_status: str
    latest_workflow_stage: str
    recommended_next_task: str
    summary: dict[str, Any]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def run_personal_mvp_daily_advisory_review_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> PersonalMvpDailyAdvisoryReviewStatusResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "status"
    sibling_root = out_dir.parent
    index = build_personal_mvp_daily_advisory_review_index(root=root_path, output_dir=sibling_root / "index")
    health = check_personal_mvp_daily_advisory_review_health(root=root_path, output_dir=sibling_root / "health")
    if index.rows:
        latest = sorted(index.rows, key=lambda row: (_text(row.get("generated_at")), _text(row.get("daily_review_run_id"))))[-1]
        summary = _summary_from_latest(latest, health.status)
    else:
        summary = _no_artifact_summary(health.status)
    paths = _paths(out_dir)
    result = PersonalMvpDailyAdvisoryReviewStatusResult(
        latest_daily_review_run_id=_text(summary.get("latest_daily_review_run_id")),
        latest_status=_text(summary.get("latest_status")),
        latest_health_status=_text(summary.get("latest_health_status")),
        latest_workflow_stage=_text(summary.get("latest_workflow_stage")),
        recommended_next_task=NEXT_TASK,
        summary=summary,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Personal MVP daily advisory review health is {health.status}."],
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    summary = {
        "latest_daily_review_run_id": _text(latest.get("daily_review_run_id")),
        "latest_status": _text(latest.get("status")),
        "latest_health_status": health_status,
        "latest_workflow_stage": _text(latest.get("workflow_stage")),
        "latest_artifact_path": _text(latest.get("artifact_path")),
        "latest_report_path": _text(latest.get("report_path")),
        "latest_metadata_path": _text(latest.get("metadata_path")),
        "latest_review_date": _text(latest.get("review_date")),
        "latest_row_count": _value(latest.get("row_count")),
        "latest_watch_count": _value(latest.get("watch_count")),
        "latest_review_buy_candidate_count": _value(latest.get("review_buy_candidate_count")),
        "latest_review_sell_candidate_count": _value(latest.get("review_sell_candidate_count")),
        "latest_hold_review_count": _value(latest.get("hold_review_count")),
        "latest_no_action_count": _value(latest.get("no_action_count")),
        "latest_blocked_count": _value(latest.get("blocked_count")),
        "latest_demo_count": _value(latest.get("demo_count")),
        "latest_not_found_count": _value(latest.get("not_found_count")),
        "latest_stale_artifact_count": _value(latest.get("stale_artifact_count")),
        "latest_missing_artifact_count": _value(latest.get("missing_artifact_count")),
        "latest_warning_count": _value(latest.get("warning_count")),
        "report_only": True,
        "diagnostic_only": True,
        "local_only": True,
        "manual_confirmation_required": True,
        "recommended_next_task": NEXT_TASK,
    }
    for field in REQUIRED_FALSE_SAFETY_FIELDS:
        summary[f"latest_{field}"] = _to_bool(latest.get(field))
    return {column: summary.get(column, "") for column in STATUS_COLUMNS}


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    summary = {column: "" for column in STATUS_COLUMNS}
    summary.update(
        {
            "latest_status": NO_ARTIFACT_STATUS,
            "latest_health_status": health_status,
            "latest_workflow_stage": NO_ARTIFACT_STATUS,
            "report_only": True,
            "diagnostic_only": True,
            "local_only": True,
            "manual_confirmation_required": True,
            "recommended_next_task": NEXT_TASK,
        }
    )
    for field in REQUIRED_FALSE_SAFETY_FIELDS:
        summary[f"latest_{field}"] = False
    return summary


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "status_csv": output_dir / "personal_mvp_daily_advisory_review_status.csv",
        "status_md": output_dir / "personal_mvp_daily_advisory_review_status.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: PersonalMvpDailyAdvisoryReviewStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    with result.artifact_paths["status_csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=STATUS_COLUMNS)
        writer.writeheader()
        writer.writerow(result.summary)
    result.artifact_paths["status_md"].write_text(_render_markdown(result), encoding="utf-8")
    result.artifact_paths["metadata_json"].write_text(
        json.dumps(
            {
                "latest_daily_review_run_id": result.latest_daily_review_run_id,
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


def _render_markdown(result: PersonalMvpDailyAdvisoryReviewStatusResult) -> str:
    return "\n".join(
        [
            "# Personal MVP Daily Advisory Review Status",
            "",
            f"- Latest run id: `{result.latest_daily_review_run_id}`",
            f"- Latest status: `{result.latest_status}`",
            f"- Latest health status: `{result.latest_health_status}`",
            f"- Latest workflow stage: `{result.latest_workflow_stage}`",
            f"- Recommended next task: `{NEXT_TASK}`",
            "- Report-only local advisory review status only.",
            "- No real buy-review, broker, order, message, trading, replay, labels, training, model, stock_profile, paper expansion, or protected data-write behavior is authorized.",
            "",
        ]
    )


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ")[:240]


def _value(value: Any) -> Any:
    return "" if value is None else value


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)
