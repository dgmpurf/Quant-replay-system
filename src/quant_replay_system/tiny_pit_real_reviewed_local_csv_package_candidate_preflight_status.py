"""Status view for Tiny PIT reviewed LOCAL_CSV preflight artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight import (
    NEGATIVE_FALSE_FIELDS,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_health import (
    check_real_reviewed_local_csv_package_candidate_preflight_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_index import (
    CAPABILITY_LEVEL_FIELDS,
    COUNT_FIELDS,
    DEFAULT_ROOT,
    build_real_reviewed_local_csv_package_candidate_preflight_index,
)


NO_ARTIFACT_STAGE = "NO_TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Research-Status "
    "Planning Report-Only v0.1"
)
STATUS_COLUMNS = [
    "latest_run_id",
    "latest_runtime_status",
    "latest_health_status",
    "latest_workflow_stage",
    "latest_artifact_path",
    "latest_report_path",
    "latest_metadata_path",
    "latest_summary_path",
    "latest_preflight_id",
    "latest_declared_package_id",
    *[f"latest_{field}" for field in CAPABILITY_LEVEL_FIELDS],
    *[f"latest_{field}" for field in COUNT_FIELDS],
    *[f"latest_{field}" for field in NEGATIVE_FALSE_FIELDS],
    "report_only",
    "diagnostic_only",
    "recommended_next_task",
]


@dataclass(frozen=True)
class RealReviewedLocalCsvPreflightStatusResult:
    latest_run_id: str
    latest_runtime_status: str
    latest_health_status: str
    latest_workflow_stage: str
    latest_artifact_path: str
    latest_report_path: str
    latest_metadata_path: str
    latest_summary_path: str
    latest_preflight_id: str
    latest_declared_package_id: str
    latest_required_reference_present_count: int
    latest_missing_required_reference_count: int
    latest_missing_optional_reference_count: int
    latest_real_package_candidate_created: bool
    latest_active_replay_input: bool
    latest_buy_review_allowed: bool
    latest_trading_allowed: bool
    recommended_next_task: str
    summary: dict[str, Any]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def run_real_reviewed_local_csv_package_candidate_preflight_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = f"{DEFAULT_ROOT}/status",
) -> RealReviewedLocalCsvPreflightStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_real_reviewed_local_csv_package_candidate_preflight_index(
        root=root,
        output_dir=sibling_root / "index",
    )
    health = check_real_reviewed_local_csv_package_candidate_preflight_health(
        root=root,
        output_dir=sibling_root / "health",
    )
    if not index.rows:
        summary = _no_artifact_summary(health.status)
    else:
        latest = sorted(index.rows, key=lambda row: str(row.get("run_id") or ""))[-1]
        summary = _summary_from_latest(latest, health.status)
    paths = _paths(output_dir)
    result = RealReviewedLocalCsvPreflightStatusResult(
        latest_run_id=str(summary["latest_run_id"]),
        latest_runtime_status=str(summary["latest_runtime_status"]),
        latest_health_status=str(summary["latest_health_status"]),
        latest_workflow_stage=str(summary["latest_workflow_stage"]),
        latest_artifact_path=str(summary["latest_artifact_path"]),
        latest_report_path=str(summary["latest_report_path"]),
        latest_metadata_path=str(summary["latest_metadata_path"]),
        latest_summary_path=str(summary["latest_summary_path"]),
        latest_preflight_id=str(summary["latest_preflight_id"]),
        latest_declared_package_id=str(summary["latest_declared_package_id"]),
        latest_required_reference_present_count=_to_int(
            summary["latest_required_reference_present_count"]
        ),
        latest_missing_required_reference_count=_to_int(
            summary["latest_missing_required_reference_count"]
        ),
        latest_missing_optional_reference_count=_to_int(
            summary["latest_missing_optional_reference_count"]
        ),
        latest_real_package_candidate_created=_to_bool(
            summary["latest_real_package_candidate_created"]
        ),
        latest_active_replay_input=_to_bool(summary["latest_active_replay_input"]),
        latest_buy_review_allowed=_to_bool(summary["latest_buy_review_allowed"]),
        latest_trading_allowed=_to_bool(summary["latest_trading_allowed"]),
        recommended_next_task=NEXT_TASK,
        summary=summary,
        artifact_paths=paths,
        warnings=[] if health.status == "PASS" else [f"Preflight artifact health is {health.status}."],
    )
    _write(result)
    return result


def _summary_from_latest(latest: dict[str, Any], health_status: str) -> dict[str, Any]:
    summary = {
        "latest_run_id": _text(latest.get("run_id")),
        "latest_runtime_status": _text(latest.get("runtime_status")),
        "latest_health_status": health_status,
        "latest_workflow_stage": _text(latest.get("workflow_stage")),
        "latest_artifact_path": _text(latest.get("artifact_path")),
        "latest_report_path": _text(latest.get("report_path")),
        "latest_metadata_path": _text(latest.get("metadata_path")),
        "latest_summary_path": _text(latest.get("summary_path")),
        "latest_preflight_id": _text(latest.get("preflight_id")),
        "latest_declared_package_id": _text(latest.get("declared_package_id")),
        "report_only": True,
        "diagnostic_only": True,
        "recommended_next_task": NEXT_TASK,
    }
    for field in CAPABILITY_LEVEL_FIELDS:
        summary[f"latest_{field}"] = _text(latest.get(field))
    for field in COUNT_FIELDS:
        summary[f"latest_{field}"] = _to_int(latest.get(field))
    for field in NEGATIVE_FALSE_FIELDS:
        summary[f"latest_{field}"] = _to_bool(latest.get(field))
        summary[field] = _to_bool(latest.get(field))
    return _finalize_summary(summary)


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "latest_run_id": "",
        "latest_runtime_status": "NO_PREFLIGHT_ARTIFACT",
        "latest_health_status": health_status,
        "latest_workflow_stage": NO_ARTIFACT_STAGE,
        "latest_artifact_path": "",
        "latest_report_path": "",
        "latest_metadata_path": "",
        "latest_summary_path": "",
        "latest_preflight_id": "",
        "latest_declared_package_id": "",
        "report_only": True,
        "diagnostic_only": True,
        "recommended_next_task": NEXT_TASK,
    }
    for field in CAPABILITY_LEVEL_FIELDS:
        summary[f"latest_{field}"] = ""
    for field in COUNT_FIELDS:
        summary[f"latest_{field}"] = 0
    for field in NEGATIVE_FALSE_FIELDS:
        summary[f"latest_{field}"] = False
        summary[field] = False
    return _finalize_summary(summary)


def _finalize_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {column: summary.get(column, "") for column in STATUS_COLUMNS}


def _paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "artifact_dir": root,
        "status_csv": root / "real_reviewed_local_csv_package_candidate_preflight_status.csv",
        "status_md": root / "real_reviewed_local_csv_package_candidate_preflight_status.md",
        "metadata_json": root / "metadata.json",
    }


def _write(result: RealReviewedLocalCsvPreflightStatusResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_rows(result.artifact_paths["status_csv"], STATUS_COLUMNS, [result.summary])
    _write_text(result.artifact_paths["status_md"], _status_markdown(result))
    _write_json(
        result.artifact_paths["metadata_json"],
        {
            "latest_run_id": result.latest_run_id,
            "latest_runtime_status": result.latest_runtime_status,
            "latest_health_status": result.latest_health_status,
            "latest_workflow_stage": result.latest_workflow_stage,
            "latest_preflight_id": result.latest_preflight_id,
            "latest_declared_package_id": result.latest_declared_package_id,
            "report_only": True,
            "diagnostic_only": True,
            "recommended_next_task": NEXT_TASK,
        },
    )


def _status_markdown(result: RealReviewedLocalCsvPreflightStatusResult) -> str:
    return "\n".join(
        [
            "# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Status",
            "",
            f"- latest_run_id: {result.latest_run_id}",
            f"- latest_runtime_status: {result.latest_runtime_status}",
            f"- latest_health_status: {result.latest_health_status}",
            f"- latest_preflight_id: {result.latest_preflight_id}",
            "- declared_package_id: metadata only",
            "- report_only: true",
            "- diagnostic_only: true",
            f"- recommended_next_task: {NEXT_TASK}",
            "- package_candidate_created: false",
            "- replay_or_trading_ready: false",
            "",
        ]
    )


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
