"""Report-only Operational Global APPROVED_FOR_PAPER planning workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT = "NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT"
READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW = "READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW"
OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED = (
    "OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED"
)
BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER = "BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER"
INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT = "INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT"

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/operational_global_approved_for_paper_v0_1")

ARTIFACT_FILES = {
    "operational_global_approved_for_paper_metadata": "operational_global_approved_for_paper_metadata.json",
    "operational_global_approved_for_paper_manifest_review": "operational_global_approved_for_paper_manifest_review.csv",
    "operational_global_approved_for_paper_lineage_matrix": "operational_global_approved_for_paper_lineage_matrix.csv",
    "operational_global_approved_for_paper_health_gate_results": "operational_global_approved_for_paper_health_gate_results.csv",
    "operational_global_approved_for_paper_forbidden_output_guard": "operational_global_approved_for_paper_forbidden_output_guard.csv",
    "operational_global_approved_for_paper_side_effect_guard": "operational_global_approved_for_paper_side_effect_guard.csv",
    "operational_global_approved_for_paper_overclaim_guard": "operational_global_approved_for_paper_overclaim_guard.csv",
    "operational_global_approved_for_paper_limitations": "operational_global_approved_for_paper_limitations.md",
    "operational_global_approved_for_paper_revocation_plan": "operational_global_approved_for_paper_revocation_plan.md",
    "recommended_next_task": "recommended_next_task.md",
}

REQUIRED_FIELDS = [
    "exact_user_approval_id",
    "approval_scope",
    "approval_timestamp",
    "approver_placeholder_id",
    "reviewer_placeholder_id",
    "upstream_artifact_ids",
    "upstream_artifact_paths",
    "upstream_health_statuses",
    "immutable_lineage_hashes",
    "source_hashes",
    "revision_ids",
    "available_time_summary",
    "limitations_acknowledged",
    "overfit_warnings_acknowledged",
    "metric_limitations_acknowledged",
    "paper_workflow_limitations_acknowledged",
    "stock_profile_limitations_acknowledged",
    "forbidden_outputs_checked",
    "side_effects_checked",
    "operational_global_approved_for_paper_requested",
    "real_buy_review_requested",
    "trading_requested",
    "buy_review_allowed_requested",
    "strategy_performance_validation_requested",
    "approval_expiry",
    "review_cadence",
    "revocation_path",
    "audit_report_path",
    "created_by_workflow",
    "report_only_until_promoted",
]

TRUE_REQUIRED_FIELDS = [
    "limitations_acknowledged",
    "overfit_warnings_acknowledged",
    "metric_limitations_acknowledged",
    "paper_workflow_limitations_acknowledged",
    "stock_profile_limitations_acknowledged",
    "forbidden_outputs_checked",
    "side_effects_checked",
    "operational_global_approved_for_paper_requested",
    "report_only_until_promoted",
]

FALSE_REQUIRED_FIELDS = [
    "real_buy_review_requested",
    "trading_requested",
    "buy_review_allowed_requested",
    "strategy_performance_validation_requested",
]

DOWNSTREAM_FALSE_FIELDS = [
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "active_stock_profile_created",
    "promoted_model_created",
    "production_model_created",
    "active_thresholds_created",
    "advisory_predictions_created",
    "active_probabilities_created",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

FORBIDDEN_PATH_TOKENS = [
    "data/raw",
    "data/processed",
    "data/cache",
    "current_candidates",
    "current-candidates",
    "snapshot",
    "signal_semantics",
    "signal-semantics",
    "broker",
    "order",
    "trading",
]


@dataclass(frozen=True)
class OperationalGlobalApprovedForPaperSettings:
    manifest_path: str | Path | None = None
    output_dir: str | Path = DEFAULT_OUTPUT_DIR
    allow_operational_global_approved_for_paper_planning: bool = False
    write_artifacts: bool = True
    research_governed: bool = True
    diagnostic_output: bool = True


@dataclass(frozen=True)
class OperationalGlobalApprovedForPaperGateResult:
    gate: str
    status: str
    message: str


@dataclass(frozen=True)
class OperationalGlobalApprovedForPaperResult:
    operational_global_approved_for_paper_id: str
    status: str
    workflow_stage: str
    ready_for_operational_global_approved_for_paper_review: bool
    operational_global_approved_for_paper_executed: bool
    operational_global_approved_for_paper_planning_artifacts_created: bool
    operational_global_approved_for_paper_metadata_created: bool
    operational_global_approved_for_paper_manifest_review_created: bool
    operational_global_approved_for_paper_lineage_matrix_created: bool
    operational_global_approved_for_paper_health_gate_results_created: bool
    operational_global_approved_for_paper_forbidden_output_guard_created: bool
    operational_global_approved_for_paper_side_effect_guard_created: bool
    operational_global_approved_for_paper_overclaim_guard_created: bool
    operational_global_approved_for_paper_limitations_created: bool
    operational_global_approved_for_paper_revocation_plan_created: bool
    operational_global_approved_for_paper_granted: bool
    global_approved_for_paper: bool
    real_buy_review_eligible: bool
    buy_review_allowed: bool
    strategy_performance_validated: bool
    trading_allowed: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    active_stock_profile_created: bool
    promoted_model_created: bool
    production_model_created: bool
    active_thresholds_created: bool
    advisory_predictions_created: bool
    active_probabilities_created: bool
    broker_api_called: bool
    order_placed: bool
    message_sent: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    report_only: bool
    research_governed: bool
    diagnostic_output: bool
    artifact_path: str
    artifact_paths: dict[str, Path]
    gate_results: list[OperationalGlobalApprovedForPaperGateResult]
    approval_manifest_exact_user_approval_id: str = ""


def run_operational_global_approved_for_paper(
    settings: OperationalGlobalApprovedForPaperSettings | None = None,
) -> OperationalGlobalApprovedForPaperResult:
    settings = settings or OperationalGlobalApprovedForPaperSettings()
    manifest = _read_manifest(settings.manifest_path) if settings.manifest_path else {}
    run_id = _run_id(settings, manifest)
    artifact_dir = Path(settings.output_dir) / run_id
    artifact_paths = {key: artifact_dir / filename for key, filename in ARTIFACT_FILES.items()}
    gates: list[OperationalGlobalApprovedForPaperGateResult] = []

    if not settings.manifest_path:
        result = _build_result(
            settings,
            artifact_paths,
            run_id,
            NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
            "OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_NO_INPUT",
            gates,
            {},
        )
        return write_operational_global_approved_for_paper_artifacts(result, settings, manifest)

    if not manifest:
        _append(gates, "manifest_read", INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT, "Manifest is missing or unreadable.")
        result = _build_result(
            settings,
            artifact_paths,
            run_id,
            INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
            INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
            gates,
            {},
        )
        return write_operational_global_approved_for_paper_artifacts(result, settings, manifest)

    status = _validate_manifest(settings, manifest, gates)
    if status == READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW and settings.allow_operational_global_approved_for_paper_planning:
        status = OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED
        _append(gates, "report_only_planning_allow", status, "Exact report-only planning allow flag is present.")
    result = _build_result(settings, artifact_paths, run_id, status, status, gates, manifest)
    return write_operational_global_approved_for_paper_artifacts(result, settings, manifest)


def write_operational_global_approved_for_paper_artifacts(
    result: OperationalGlobalApprovedForPaperResult,
    settings: OperationalGlobalApprovedForPaperSettings,
    manifest: dict[str, Any],
) -> OperationalGlobalApprovedForPaperResult:
    if not settings.write_artifacts:
        return result
    artifact_dir = Path(result.artifact_path)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    _write_json(result.artifact_paths["operational_global_approved_for_paper_metadata"], _metadata(result, manifest))
    _write_gate_csv(
        result.artifact_paths["operational_global_approved_for_paper_health_gate_results"],
        result.gate_results or [_gate("no_input", result.status, result.workflow_stage)],
    )
    _write_gate_csv(
        result.artifact_paths["operational_global_approved_for_paper_forbidden_output_guard"],
        [gate for gate in result.gate_results if "forbidden" in gate.gate]
        or [_gate("forbidden_output_guard", result.status, "No forbidden output was requested or created.")],
    )
    _write_gate_csv(
        result.artifact_paths["operational_global_approved_for_paper_side_effect_guard"],
        [gate for gate in result.gate_results if "side_effect" in gate.gate or "path" in gate.gate]
        or [_gate("side_effect_guard", result.status, "No side-effect path was requested or created.")],
    )
    _write_gate_csv(
        result.artifact_paths["operational_global_approved_for_paper_overclaim_guard"],
        [gate for gate in result.gate_results if "overclaim" in gate.gate or "request" in gate.gate]
        or [_gate("overclaim_guard", result.status, "No operational approval overclaim was created.")],
    )
    result.artifact_paths["recommended_next_task"].write_text(_recommended_next_task(result), encoding="utf-8")

    if result.operational_global_approved_for_paper_planning_artifacts_created:
        _write_manifest_review(result.artifact_paths["operational_global_approved_for_paper_manifest_review"], manifest)
        _write_lineage_matrix(result.artifact_paths["operational_global_approved_for_paper_lineage_matrix"], result, manifest)
        result.artifact_paths["operational_global_approved_for_paper_limitations"].write_text(
            _limitations_text(), encoding="utf-8"
        )
        result.artifact_paths["operational_global_approved_for_paper_revocation_plan"].write_text(
            _revocation_plan_text(manifest), encoding="utf-8"
        )
    return result


def _validate_manifest(
    settings: OperationalGlobalApprovedForPaperSettings,
    manifest: dict[str, Any],
    gates: list[OperationalGlobalApprovedForPaperGateResult],
) -> str:
    if not _output_under_manual_diagnostics(settings.output_dir):
        return _block(gates, "side_effect_output_boundary", "Output must remain under manual diagnostics.")

    missing = [field for field in REQUIRED_FIELDS if _is_missing(manifest.get(field))]
    if missing:
        return _invalid(gates, "manifest_required_fields", f"Missing required fields: {', '.join(missing)}")

    for field in TRUE_REQUIRED_FIELDS:
        if not _to_bool(manifest.get(field)):
            return _block(gates, f"required_true_{field}", f"{field} must be true for report-only planning.")

    for field in FALSE_REQUIRED_FIELDS:
        if _to_bool(manifest.get(field)):
            return _block(gates, f"forbidden_request_{field}", f"{field} must remain false.")

    for field in ["approver_placeholder_id", "reviewer_placeholder_id"]:
        if "placeholder" not in _text(manifest.get(field)).lower():
            return _invalid(gates, f"placeholder_identity_{field}", f"{field} must use placeholder identity.")

    health_statuses = _as_list(manifest.get("upstream_health_statuses"))
    if not health_statuses or any(_text(status).upper() != "PASS" for status in health_statuses):
        return _block(gates, "upstream_health_statuses", "All upstream health statuses must be PASS.")

    unsafe_paths = [path for path in _as_list(manifest.get("upstream_artifact_paths")) if _has_forbidden_path(path)]
    if unsafe_paths:
        return _block(gates, "forbidden_upstream_artifact_path", f"Forbidden upstream path: {unsafe_paths[0]}")

    _append(gates, "manifest_contract", READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW, "Manifest contract is valid.")
    _append(gates, "side_effect_guard", READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW, "No side-effect request is present.")
    _append(gates, "overclaim_guard", READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW, "No buy-review, trading, or performance claim is present.")
    return READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW


def _build_result(
    settings: OperationalGlobalApprovedForPaperSettings,
    artifact_paths: dict[str, Path],
    run_id: str,
    status: str,
    stage: str,
    gates: list[OperationalGlobalApprovedForPaperGateResult],
    manifest: dict[str, Any],
) -> OperationalGlobalApprovedForPaperResult:
    created = status == OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED
    ready = status in {
        READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW,
        OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED,
    }
    return OperationalGlobalApprovedForPaperResult(
        operational_global_approved_for_paper_id=run_id,
        status=status,
        workflow_stage=stage,
        ready_for_operational_global_approved_for_paper_review=ready,
        operational_global_approved_for_paper_executed=created,
        operational_global_approved_for_paper_planning_artifacts_created=created,
        operational_global_approved_for_paper_metadata_created=True,
        operational_global_approved_for_paper_manifest_review_created=created,
        operational_global_approved_for_paper_lineage_matrix_created=created,
        operational_global_approved_for_paper_health_gate_results_created=True,
        operational_global_approved_for_paper_forbidden_output_guard_created=True,
        operational_global_approved_for_paper_side_effect_guard_created=True,
        operational_global_approved_for_paper_overclaim_guard_created=True,
        operational_global_approved_for_paper_limitations_created=created,
        operational_global_approved_for_paper_revocation_plan_created=created,
        operational_global_approved_for_paper_granted=False,
        global_approved_for_paper=False,
        real_buy_review_eligible=False,
        buy_review_allowed=False,
        strategy_performance_validated=False,
        trading_allowed=False,
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        report_only=True,
        research_governed=settings.research_governed,
        diagnostic_output=settings.diagnostic_output,
        artifact_path=str(Path(settings.output_dir) / run_id),
        artifact_paths=artifact_paths,
        gate_results=gates,
        approval_manifest_exact_user_approval_id=_text(manifest.get("exact_user_approval_id")),
    )


def _metadata(result: OperationalGlobalApprovedForPaperResult, manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "operational_global_approved_for_paper_id": result.operational_global_approved_for_paper_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "ready_for_operational_global_approved_for_paper_review": result.ready_for_operational_global_approved_for_paper_review,
        "operational_global_approved_for_paper_executed": result.operational_global_approved_for_paper_executed,
        "operational_global_approved_for_paper_planning_artifacts_created": result.operational_global_approved_for_paper_planning_artifacts_created,
        "approval_manifest_exact_user_approval_id": result.approval_manifest_exact_user_approval_id,
        "approval_scope": _text(manifest.get("approval_scope")),
        "approval_expiry": _text(manifest.get("approval_expiry")),
        "revocation_path": _text(manifest.get("revocation_path")),
        "report_only": result.report_only,
        "research_governed": result.research_governed,
        "diagnostic_output": result.diagnostic_output,
        **{field: getattr(result, field) for field in _metadata_false_fields()},
        "artifact_path": result.artifact_path,
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
    }


def _write_manifest_review(path: Path, manifest: dict[str, Any]) -> None:
    rows = []
    for field in REQUIRED_FIELDS:
        value = manifest.get(field)
        rows.append(
            {
                "field_name": field,
                "present": not _is_missing(value),
                "value_preview": _preview(value),
                "report_only_planning_field": True,
            }
        )
    _write_frame(path, rows)


def _write_lineage_matrix(path: Path, result: OperationalGlobalApprovedForPaperResult, manifest: dict[str, Any]) -> None:
    ids = _as_list(manifest.get("upstream_artifact_ids"))
    paths = _as_list(manifest.get("upstream_artifact_paths"))
    statuses = _as_list(manifest.get("upstream_health_statuses"))
    lineage_hashes = _as_list(manifest.get("immutable_lineage_hashes"))
    source_hashes = _as_list(manifest.get("source_hashes"))
    revision_ids = _as_list(manifest.get("revision_ids"))
    rows = []
    for index, upstream_id in enumerate(ids):
        rows.append(
            {
                "operational_global_approved_for_paper_id": result.operational_global_approved_for_paper_id,
                "upstream_artifact_id": _text(upstream_id),
                "upstream_artifact_path": _item(paths, index),
                "upstream_health_status": _item(statuses, index),
                "immutable_lineage_hash": _item(lineage_hashes, index),
                "source_hash": _item(source_hashes, index),
                "revision_id": _item(revision_ids, index),
                "available_time_summary": _text(manifest.get("available_time_summary")),
                "report_only": True,
                "diagnostic_output": True,
            }
        )
    _write_frame(path, rows)


def _limitations_text() -> str:
    return "\n".join(
        [
            "# Operational Global APPROVED_FOR_PAPER Planning Limitations",
            "",
            "This is report-only planning.",
            "It does not grant operational global approved_for_paper.",
            "It creates no real buy-review eligibility.",
            "It creates no buy_review_allowed.",
            "It is no strategy performance validation.",
            "It creates no current-candidates integration.",
            "It creates no snapshot integration.",
            "It creates no signal_semantics mutation.",
            "It creates no active stock_profile.",
            "It creates no promoted model.",
            "It creates no production model.",
            "It creates no active thresholds.",
            "It creates no advisory predictions.",
            "It creates no active probabilities.",
            "It creates no broker/order/message/API/trading.",
            "",
        ]
    )


def _revocation_plan_text(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Operational Global APPROVED_FOR_PAPER Revocation Plan",
            "",
            f"Approval expiry: {_text(manifest.get('approval_expiry'))}",
            f"Review cadence: {_text(manifest.get('review_cadence'))}",
            f"Revocation path: {_text(manifest.get('revocation_path'))}",
            "",
            "This revocation plan is planning context only and does not grant operational global approval.",
            "",
        ]
    )


def _recommended_next_task(result: OperationalGlobalApprovedForPaperResult) -> str:
    if result.status == OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED:
        task = "Operational Global APPROVED_FOR_PAPER Artifact Views Report-Only v0.1"
    elif result.status == READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW:
        task = "Review exact report-only planning allow flag before creating planning artifacts."
    else:
        task = "Resolve Operational Global APPROVED_FOR_PAPER planning blockers before artifact views."
    return f"# Recommended Next Task\n\n{task}\n"


def _read_manifest(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    manifest_path = Path(path)
    if not manifest_path.exists():
        return {}
    try:
        if manifest_path.suffix.lower() == ".csv":
            frame = pd.read_csv(manifest_path, dtype=str)
            return frame.iloc[0].dropna().to_dict() if not frame.empty else {}
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, pd.errors.ParserError):
        return {}


def _run_id(settings: OperationalGlobalApprovedForPaperSettings, manifest: dict[str, Any]) -> str:
    payload = {
        "manifest_path": str(settings.manifest_path or ""),
        "manifest": manifest,
        "allow": settings.allow_operational_global_approved_for_paper_planning,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_gate_csv(path: Path, gates: list[OperationalGlobalApprovedForPaperGateResult]) -> None:
    _write_frame(path, [{"gate": gate.gate, "status": gate.status, "message": gate.message} for gate in gates])


def _write_frame(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, dtype=object).to_csv(path, index=False)


def _append(gates: list[OperationalGlobalApprovedForPaperGateResult], gate: str, status: str, message: str) -> None:
    gates.append(_gate(gate, status, message))


def _gate(gate: str, status: str, message: str) -> OperationalGlobalApprovedForPaperGateResult:
    return OperationalGlobalApprovedForPaperGateResult(gate=gate, status=status, message=message)


def _block(gates: list[OperationalGlobalApprovedForPaperGateResult], gate: str, message: str) -> str:
    _append(gates, gate, BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER, message)
    return BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER


def _invalid(gates: list[OperationalGlobalApprovedForPaperGateResult], gate: str, message: str) -> str:
    _append(gates, gate, INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT, message)
    return INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).strip().lower() in {"1", "true", "yes", "y"}


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return [part.strip() for part in stripped.split(";") if part.strip()]
    return [value]


def _has_forbidden_path(value: Any) -> bool:
    text = _text(value).replace("\\", "/").lower()
    return any(token in text for token in FORBIDDEN_PATH_TOKENS)


def _output_under_manual_diagnostics(path: str | Path) -> bool:
    text = Path(path).as_posix().lower()
    return "outputs/reports/manual_diagnostics" in text


def _preview(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ";".join(_text(item) for item in value)
    return _text(value)


def _item(values: list[Any], index: int) -> str:
    return _text(values[index]) if index < len(values) else ""


def _metadata_false_fields() -> list[str]:
    return [
        "operational_global_approved_for_paper_granted",
        "global_approved_for_paper",
        "real_buy_review_eligible",
        "buy_review_allowed",
        "strategy_performance_validated",
        "trading_allowed",
        *DOWNSTREAM_FALSE_FIELDS,
    ]
