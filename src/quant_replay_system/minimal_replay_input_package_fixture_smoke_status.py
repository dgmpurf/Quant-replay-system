"""Status summary for minimal replay input package fixture smoke artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.historical_replay_input_gate_validator import REPLAY_INPUT_GATE_PASS_CANDIDATE
from quant_replay_system.minimal_replay_input_package_fixture_smoke_health import (
    check_minimal_replay_input_package_fixture_smoke_health,
)
from quant_replay_system.minimal_replay_input_package_fixture_smoke_index import (
    build_minimal_replay_input_package_fixture_smoke_index,
)


NO_SMOKE_ARTIFACT_FOUND = "NO_SMOKE_ARTIFACT_FOUND"
SMOKE_PASS_CANDIDATE_READY = "SMOKE_PASS_CANDIDATE_READY"
SMOKE_BLOCKED = "SMOKE_BLOCKED"
SMOKE_HEALTH_FAILED = "SMOKE_HEALTH_FAILED"

SUMMARY_COLUMNS = [
    "latest_smoke_run_id",
    "latest_validator_run_id",
    "validator_status",
    "health_status",
    "workflow_stage",
    "pass_candidate",
    "active_replay_input_ready",
    "active_replay_input",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
    "blocker_count",
    "warning_count",
    "report_path",
    "safety_statement",
    "next_action",
]


@dataclass(frozen=True)
class MinimalReplayInputPackageFixtureSmokeStatusResult:
    latest_smoke_run_id: str
    latest_validator_run_id: str
    validator_status: str
    health_status: str
    workflow_stage: str
    pass_candidate: bool
    active_replay_input_ready: bool
    active_replay_input: bool
    forward_labels_exist: bool
    weights_trained: bool
    active_stock_profile_exists: bool
    real_buy_review_eligible: bool
    blocker_count: int
    warning_count: int
    report_path: str
    safety_statement: str
    next_action: str
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_minimal_replay_input_package_fixture_smoke_status(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/minimal_replay_input_package_fixture_smoke_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/minimal_replay_input_package_fixture_smoke_v0_1/status",
) -> MinimalReplayInputPackageFixtureSmokeStatusResult:
    sibling_root = Path(output_dir).parent
    index = build_minimal_replay_input_package_fixture_smoke_index(root=root, output_dir=sibling_root / "index")
    health = check_minimal_replay_input_package_fixture_smoke_health(root=root, output_dir=sibling_root / "health")
    if index.index_frame.empty:
        result = _no_artifact_result(output_dir, root, health.status, health.error_count, health.warning_count)
    else:
        latest = index.index_frame.sort_values(["generated_at", "smoke_run_id"]).iloc[-1].to_dict()
        result = _result_from_latest(latest, health.status, health.error_count, health.warning_count, output_dir, root)
    _write(result)
    return result


def _result_from_latest(
    latest: dict[str, Any],
    health_status: str,
    error_count: int,
    warning_count: int,
    output_dir: str | Path,
    root: str | Path,
) -> MinimalReplayInputPackageFixtureSmokeStatusResult:
    validator_status = _text(latest.get("validator_status"))
    stage = _stage_for_latest(latest, health_status)
    summary = {
        "latest_smoke_run_id": _text(latest.get("smoke_run_id")),
        "latest_validator_run_id": _text(latest.get("validator_run_id")),
        "validator_status": validator_status,
        "health_status": health_status,
        "workflow_stage": stage,
        "pass_candidate": _to_bool(latest.get("pass_candidate")),
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "blocker_count": error_count,
        "warning_count": warning_count,
        "report_path": _text(latest.get("smoke_report_path")),
        "safety_statement": _safety_statement(),
        "next_action": _next_action(stage),
    }
    return _result(summary, output_dir, root, [])


def _no_artifact_result(
    output_dir: str | Path,
    root: str | Path,
    health_status: str,
    error_count: int,
    warning_count: int,
) -> MinimalReplayInputPackageFixtureSmokeStatusResult:
    summary = {
        "latest_smoke_run_id": "",
        "latest_validator_run_id": "",
        "validator_status": "MISSING",
        "health_status": health_status,
        "workflow_stage": NO_SMOKE_ARTIFACT_FOUND,
        "pass_candidate": False,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "blocker_count": error_count,
        "warning_count": warning_count,
        "report_path": "",
        "safety_statement": _safety_statement(),
        "next_action": "Run minimal-replay-input-package-fixture-smoke before artifact views.",
    }
    return _result(summary, output_dir, root, [f"No smoke artifacts found under {root}"])


def _result(
    summary: dict[str, Any],
    output_dir: str | Path,
    root: str | Path,
    warnings: list[str],
) -> MinimalReplayInputPackageFixtureSmokeStatusResult:
    paths = {
        "artifact_dir": Path(output_dir),
        "status_csv": Path(output_dir) / "minimal_replay_input_package_fixture_smoke_status.csv",
        "status_report": Path(output_dir) / "minimal_replay_input_package_fixture_smoke_status_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    frame = pd.DataFrame([summary], columns=SUMMARY_COLUMNS)
    return MinimalReplayInputPackageFixtureSmokeStatusResult(
        latest_smoke_run_id=str(summary["latest_smoke_run_id"]),
        latest_validator_run_id=str(summary["latest_validator_run_id"]),
        validator_status=str(summary["validator_status"]),
        health_status=str(summary["health_status"]),
        workflow_stage=str(summary["workflow_stage"]),
        pass_candidate=bool(summary["pass_candidate"]),
        active_replay_input_ready=False,
        active_replay_input=False,
        forward_labels_exist=False,
        weights_trained=False,
        active_stock_profile_exists=False,
        real_buy_review_eligible=False,
        blocker_count=int(summary["blocker_count"]),
        warning_count=int(summary["warning_count"]),
        report_path=str(summary["report_path"]),
        safety_statement=str(summary["safety_statement"]),
        next_action=str(summary["next_action"]),
        summary_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={"root": str(root), "report_only": True, "diagnostic_only": True},
    )


def _write(result: MinimalReplayInputPackageFixtureSmokeStatusResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.summary_frame.to_csv(paths["status_csv"], index=False)
    paths["status_report"].write_text(
        "\n".join(
            [
                "# Minimal Replay Input Package Fixture Smoke Status",
                "",
                f"- validator_status: {result.validator_status}",
                f"- health_status: {result.health_status}",
                f"- workflow_stage: {result.workflow_stage}",
                f"- latest_smoke_run_id: {result.latest_smoke_run_id}",
                f"- latest_validator_run_id: {result.latest_validator_run_id}",
                f"- pass_candidate: {result.pass_candidate}",
                f"- active_replay_input_ready: {result.active_replay_input_ready}",
                f"- active_replay_input: {result.active_replay_input}",
                f"- blocker_count: {result.blocker_count}",
                "",
                result.safety_statement,
                "",
                f"Next action: {result.next_action}",
            ]
        ),
        encoding="utf-8",
    )
    paths["metadata"].write_text(
        json.dumps(
            {
                "latest_smoke_run_id": result.latest_smoke_run_id,
                "latest_validator_run_id": result.latest_validator_run_id,
                "validator_status": result.validator_status,
                "health_status": result.health_status,
                "workflow_stage": result.workflow_stage,
                "pass_candidate": result.pass_candidate,
                "active_replay_input_ready": False,
                "active_replay_input": False,
                "forward_labels_exist": False,
                "weights_trained": False,
                "active_stock_profile_exists": False,
                "real_buy_review_eligible": False,
                "blocker_count": result.blocker_count,
                "warning_count": result.warning_count,
                "report_path": result.report_path,
                "next_action": result.next_action,
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _stage_for_latest(latest: dict[str, Any], health_status: str) -> str:
    if health_status == "FAIL":
        return SMOKE_HEALTH_FAILED
    if _text(latest.get("validator_status")) == REPLAY_INPUT_GATE_PASS_CANDIDATE and _to_bool(latest.get("pass_candidate")):
        return SMOKE_PASS_CANDIDATE_READY
    return SMOKE_BLOCKED


def _next_action(stage: str) -> str:
    if stage == SMOKE_PASS_CANDIDATE_READY:
        return "Review smoke pass-candidate diagnostics; do not treat as active replay input."
    if stage == NO_SMOKE_ARTIFACT_FOUND:
        return "Run minimal-replay-input-package-fixture-smoke before artifact views."
    if stage == SMOKE_HEALTH_FAILED:
        return "Resolve smoke health blockers before using this as validator smoke evidence."
    return "Resolve smoke blockers; do not run replay or downstream workflows."


def _safety_statement() -> str:
    return (
        "This smoke workflow is report-only. It only proves the validator can produce "
        "REPLAY_INPUT_GATE_PASS_CANDIDATE. It is not active replay input. It is not "
        "ACTIVE_REPLAY_INPUT_READY. It does not run replay. It does not compute forward labels. "
        "It does not train weights. It does not create active stock profiles. It does not create "
        "real buy-review eligibility. It does not authorize trading."
    )


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


__all__ = [
    "NO_SMOKE_ARTIFACT_FOUND",
    "SMOKE_BLOCKED",
    "SMOKE_HEALTH_FAILED",
    "SMOKE_PASS_CANDIDATE_READY",
    "MinimalReplayInputPackageFixtureSmokeStatusResult",
    "run_minimal_replay_input_package_fixture_smoke_status",
]
