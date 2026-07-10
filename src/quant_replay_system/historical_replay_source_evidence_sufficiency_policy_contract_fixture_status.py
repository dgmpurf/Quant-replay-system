"""Latest status view for source/evidence sufficiency policy fixture runs."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture import (
    RECOMMENDED_NEXT_TASK,
    SAFETY_FALSE_FIELDS,
    _validate_output_root,
)
from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture_health import (
    STATUS_HEALTH_FAIL,
    check_historical_replay_source_evidence_sufficiency_policy_contract_fixture_health,
)
from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture_index import (
    DEFAULT_ROOT,
    _view_dir,
    build_historical_replay_source_evidence_sufficiency_policy_contract_fixture_index,
)


STATUS_CREATED = (
    "SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_STATUS_CREATED_REPORT_ONLY"
)
STATUS_NO_ARTIFACTS = (
    "SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_STATUS_NO_ARTIFACTS"
)
NEXT_TASK = RECOMMENDED_NEXT_TASK
STATUS_COLUMNS = [
    "latest_run_id",
    "latest_status",
    "latest_health_status",
    "latest_workflow_stage",
    "latest_historical_decision_date",
    "latest_legacy_universe_label",
    "latest_artifact_path",
    "latest_report_path",
    "latest_metadata_path",
    "latest_row_count",
    "latest_stock_row_count",
    "latest_etf_row_count",
    "latest_evidence_family_count",
    "latest_row_evidence_family_contract_count",
    "latest_applicable_contract_row_count",
    "latest_instrument_not_applicable_context_row_count",
    "latest_profile_conflict_count",
    "latest_profile_aligned_context_count",
    "latest_unresolved_profile_conflict_count",
    "latest_selected_row_with_blocker_count",
    "latest_sufficiency_candidate_count",
    "latest_evidence_accepted_count",
    "latest_evidence_closed_count",
    "latest_pit_admissible_count",
    "latest_replay_ready_count",
    "latest_safety_true_count",
    "report_only",
    "diagnostic_only",
    "local_only",
    "synthetic_only",
    *[f"latest_{field}" for field in SAFETY_FALSE_FIELDS],
    "recommended_next_task",
]


@dataclass(frozen=True)
class HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureStatusResult:
    status: str
    latest_run_id: str
    latest_status: str
    latest_health_status: str
    latest_workflow_stage: str
    recommended_next_task: str
    summary: dict[str, Any]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def run_historical_replay_source_evidence_sufficiency_policy_contract_fixture_status(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureStatusResult:
    root_path = _validate_output_root(Path(root))
    out_dir = _view_dir(root_path, output_dir, "status")
    sibling_root = out_dir.parent
    index = build_historical_replay_source_evidence_sufficiency_policy_contract_fixture_index(
        root=root_path, output_dir=sibling_root / "index"
    )
    health = check_historical_replay_source_evidence_sufficiency_policy_contract_fixture_health(
        root=root_path, output_dir=sibling_root / "health"
    )
    if index.rows:
        latest = sorted(index.rows, key=lambda row: str(row.get("run_id", "")))[-1]
        summary = _summary_from_latest(latest, health.status)
    else:
        summary = _no_artifact_summary(health.status)
    result = HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureStatusResult(
        status=STATUS_CREATED,
        latest_run_id=str(summary["latest_run_id"]),
        latest_status=str(summary["latest_status"]),
        latest_health_status=str(summary["latest_health_status"]),
        latest_workflow_stage=str(summary["latest_workflow_stage"]),
        recommended_next_task=NEXT_TASK,
        summary=summary,
        artifact_paths=_paths(out_dir),
        warnings=(
            ["Latest fixture health is unsafe."]
            if health.status == STATUS_HEALTH_FAIL
            else list(health.warnings)
        ),
    )
    _write(result)
    return result


def _summary_from_latest(
    latest: dict[str, Any], health_status: str
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "latest_run_id": latest.get("run_id", ""),
        "latest_status": latest.get("runtime_status", ""),
        "latest_health_status": health_status,
        "latest_workflow_stage": latest.get("workflow_stage", ""),
        "latest_historical_decision_date": latest.get("historical_decision_date", ""),
        "latest_legacy_universe_label": latest.get("legacy_universe_label", ""),
        "latest_artifact_path": latest.get("artifact_path", ""),
        "latest_report_path": latest.get("report_path", ""),
        "latest_metadata_path": latest.get("metadata_path", ""),
        "report_only": True,
        "diagnostic_only": True,
        "local_only": True,
        "synthetic_only": True,
        "recommended_next_task": NEXT_TASK,
    }
    for name in [
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
    ]:
        summary[f"latest_{name}"] = latest.get(name, 0)
    for field in SAFETY_FALSE_FIELDS:
        summary[f"latest_{field}"] = _to_bool(latest.get(field))
    return {column: summary.get(column, "") for column in STATUS_COLUMNS}


def _no_artifact_summary(health_status: str) -> dict[str, Any]:
    summary: dict[str, Any] = {column: "" for column in STATUS_COLUMNS}
    summary.update(
        {
            "latest_status": STATUS_NO_ARTIFACTS,
            "latest_health_status": health_status,
            "latest_workflow_stage": STATUS_NO_ARTIFACTS,
            "report_only": True,
            "diagnostic_only": True,
            "local_only": True,
            "synthetic_only": True,
            "recommended_next_task": NEXT_TASK,
        }
    )
    for column in STATUS_COLUMNS:
        if column.startswith("latest_") and column.endswith("_count"):
            summary[column] = 0
    for field in SAFETY_FALSE_FIELDS:
        summary[f"latest_{field}"] = False
    return summary


def _paths(output_dir: Path) -> dict[str, Path]:
    stem = "historical_replay_source_evidence_sufficiency_policy_contract_fixture_status"
    return {
        "artifact_dir": output_dir,
        "status_csv": output_dir / f"{stem}.csv",
        "status_md": output_dir / f"{stem}.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(
    result: HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureStatusResult,
) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    with result.artifact_paths["status_csv"].open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=STATUS_COLUMNS)
        writer.writeheader()
        writer.writerow(result.summary)
    result.artifact_paths["status_md"].write_text(
        _render_markdown(result), encoding="utf-8"
    )
    result.artifact_paths["metadata_json"].write_text(
        json.dumps(
            {
                "status": result.status,
                "latest_run_id": result.latest_run_id,
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


def _render_markdown(
    result: HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureStatusResult,
) -> str:
    return "\n".join(
        [
            "# Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Status",
            "",
            f"- Latest run id: `{result.latest_run_id}`",
            f"- Latest status: `{result.latest_status}`",
            f"- Latest health status: `{result.latest_health_status}`",
            f"- Latest workflow stage: `{result.latest_workflow_stage}`",
            f"- Recommended next task: `{NEXT_TASK}`",
            "- Report-only context only; no evidence sufficiency, acceptance, closure, PIT approval, replay readiness, buy-review, or trading authority is created.",
            "",
        ]
    )


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)
