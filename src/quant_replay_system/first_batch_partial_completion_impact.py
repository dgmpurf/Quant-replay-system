"""Report-only first-batch partial reviewer completion impact.

This workflow compares a first-batch reviewer evidence completion plan with an
optional partial reviewer completion fixture. It reports which reviewer metadata
fields were filled and which PIT evidence blockers remain. It never creates
clean review updates, applies approval, runs PIT review/export workflows, writes
universe inputs, runs current-candidates, builds snapshots, computes labels, or
mutates cache.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


REVIEWER_METADATA_FIELDS = [
    "reviewer",
    "reviewed_at",
    "review_reason",
    "evidence_source",
    "evidence_reference",
    "evidence_path",
]

MATERIAL_EVIDENCE_FIELDS = [
    "as_of_date",
    "industry",
    "is_active",
    "is_active_evidence",
    "revision_id",
    "t_plus_rule",
    "is_st",
]

IMPACT_COLUMNS = [
    "impact_id",
    "completion_plan_id",
    "partial_completion_path",
    "signal_date",
    "symbol",
    "universe_name",
    "review_status_before",
    "review_status_after_partial_completion",
    "partial_completion_found",
    "completed_reviewer_metadata",
    "completed_reviewer_metadata_count",
    "completed_material_evidence_fields",
    "completed_material_evidence_field_count",
    "blocker_reduction_class",
    "material_checklist_blocker_reduced",
    "remaining_missing_evidence_fields",
    "remaining_missing_evidence_categories",
    "remaining_checklist_blockers",
    "checklist_pass_before",
    "checklist_pass_after_partial_completion",
    "approval_candidate_after_partial_completion",
    "include_flag_after_partial_completion",
    "valid_for_signal_date_after_partial_completion",
    "survivorship_bias_resolved_after_partial_completion",
    "approved_for_pit_universe_present",
    "clean_review_updates_created",
    "approval_applied",
    "pit_review_run",
    "export_readiness_run",
    "export_staging_run",
    "universe_exported",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "impact_only",
]

SAFETY_STATEMENT = (
    "No approval, rejection, clean review updates, PIT review, export-readiness, "
    "staging, universe export, data/raw write, data/processed write, active worklist "
    "mutation, current-candidates generation, snapshot build, forward labels, live "
    "trading, broker API, orders, messages, API/LLM calls, or cache mutation was invoked."
)


@dataclass(frozen=True)
class FirstBatchPartialCompletionImpactSettings:
    output_dir: Path = Path("outputs/reports/first_batch_partial_completion_impact")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    enable_approval: bool = False
    enable_clean_review_updates: bool = False
    enable_pit_review: bool = False
    enable_export_readiness: bool = False
    enable_export_staging: bool = False
    enable_universe_export: bool = False
    enable_data_raw_write: bool = False
    enable_data_processed_write: bool = False
    enable_current_candidates: bool = False
    enable_snapshot_build: bool = False
    enable_forward_labels: bool = False
    enable_cache_mutation: bool = False
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_order_placement: bool = False
    enable_message_delivery: bool = False


@dataclass(frozen=True)
class FirstBatchPartialCompletionImpactRequest:
    completion_plan: Path
    partial_completion: Path | None = None


@dataclass(frozen=True)
class FirstBatchPartialCompletionImpactResult:
    impact_id: str
    status: str
    request: FirstBatchPartialCompletionImpactRequest
    completion_plan_id: str
    partial_completion_path: str
    row_count: int
    completed_row_count: int
    completed_field_count: int
    blocker_reduced_count: int
    material_blocker_reduced_count: int
    checklist_pass_count: int
    remaining_blocked_count: int
    clean_review_updates_created: bool
    approval_applied: bool
    impact_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]


def build_first_batch_partial_completion_impact(
    *,
    completion_plan: str | Path = "outputs/reports/first_batch_reviewer_evidence_completion_plan/c630522f235a",
    partial_completion: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: FirstBatchPartialCompletionImpactSettings | None = None,
) -> FirstBatchPartialCompletionImpactResult:
    resolved_settings = settings or FirstBatchPartialCompletionImpactSettings()
    if output_dir is not None:
        resolved_settings = FirstBatchPartialCompletionImpactSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)
    request = FirstBatchPartialCompletionImpactRequest(
        completion_plan=Path(completion_plan),
        partial_completion=Path(partial_completion) if partial_completion else None,
    )
    plan_frame, plan_metadata = load_first_batch_completion_plan_for_impact(request.completion_plan)
    partial_frame = load_partial_completion_fixture(request.partial_completion)
    impact_id = _impact_id(request, plan_frame, partial_frame)
    impact_frame = evaluate_first_batch_partial_completion_impact(
        impact_id=impact_id,
        completion_plan_id=str(plan_metadata.get("plan_id") or _first_non_empty(plan_frame, "plan_id")),
        plan_frame=plan_frame,
        partial_frame=partial_frame,
        partial_completion_path=str(request.partial_completion or ""),
    )
    counts = _impact_counts(impact_frame)
    paths = resolve_first_batch_partial_completion_impact_paths(resolved_settings.output_dir, impact_id)
    result = FirstBatchPartialCompletionImpactResult(
        impact_id=impact_id,
        status="WARN" if counts["remaining_blocked_count"] else "PASS",
        request=request,
        completion_plan_id=str(plan_metadata.get("plan_id") or _first_non_empty(plan_frame, "plan_id")),
        partial_completion_path=str(request.partial_completion or ""),
        row_count=len(impact_frame),
        completed_row_count=counts["completed_row_count"],
        completed_field_count=counts["completed_field_count"],
        blocker_reduced_count=counts["blocker_reduced_count"],
        material_blocker_reduced_count=counts["material_blocker_reduced_count"],
        checklist_pass_count=counts["checklist_pass_count"],
        remaining_blocked_count=counts["remaining_blocked_count"],
        clean_review_updates_created=False,
        approval_applied=False,
        impact_frame=impact_frame,
        artifact_paths=paths,
        warnings=[],
    )
    if resolved_settings.write_artifacts:
        write_first_batch_partial_completion_impact_artifacts(result)
    return result


def load_first_batch_completion_plan_for_impact(completion_plan: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = Path(completion_plan)
    if not path.exists():
        raise FileNotFoundError(f"Completion plan path not found: {path}")
    metadata: dict[str, Any] = {}
    if path.is_file():
        plan_csv = path
        metadata_path = path.parent / "metadata.json"
    else:
        plan_csv = path / "first_batch_reviewer_evidence_completion_plan.csv"
        metadata_path = path / "metadata.json"
    if not plan_csv.exists():
        raise FileNotFoundError(f"Completion plan CSV not found: {plan_csv}")
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    frame = read_csv_preserve_symbol_columns(plan_csv, keep_default_na=False)
    return _normalize_identity(frame), metadata


def load_partial_completion_fixture(partial_completion: str | Path | None) -> pd.DataFrame:
    if not partial_completion:
        return pd.DataFrame()
    path = Path(partial_completion)
    if not path.exists():
        raise FileNotFoundError(f"Partial completion fixture not found: {path}")
    return _normalize_identity(read_csv_preserve_symbol_columns(path, keep_default_na=False))


def evaluate_first_batch_partial_completion_impact(
    *,
    impact_id: str,
    completion_plan_id: str,
    plan_frame: pd.DataFrame,
    partial_frame: pd.DataFrame,
    partial_completion_path: str,
) -> pd.DataFrame:
    partial_by_key = _partial_by_identity(partial_frame)
    rows: list[dict[str, Any]] = []
    for row in plan_frame.to_dict("records"):
        key = _identity_key(row)
        partial = partial_by_key.get(key, {})
        completed_reviewer = _completed_fields(partial, REVIEWER_METADATA_FIELDS)
        completed_material = _completed_material_fields(partial, row)
        partial_found = bool(partial)
        material_reduced = bool(completed_material)
        reviewer_reduced = bool(completed_reviewer)
        reduction = (
            "MATERIAL_EVIDENCE_PARTIAL"
            if material_reduced
            else "REVIEWER_METADATA_ONLY"
            if reviewer_reduced
            else "NO_PARTIAL_COMPLETION"
        )
        remaining_fields = _string(row.get("missing_evidence_fields"))
        remaining_categories = _string(row.get("missing_evidence_categories"))
        blocked_before = _bool(row.get("remaining_blocked"), default=True)
        checklist_before = _bool(row.get("checklist_pass"))
        checklist_after = False
        rows.append(
            {
                "impact_id": impact_id,
                "completion_plan_id": completion_plan_id,
                "partial_completion_path": partial_completion_path,
                "signal_date": _string(row.get("signal_date")),
                "symbol": normalize_symbol_value(row.get("symbol")),
                "universe_name": _string(row.get("universe_name")),
                "review_status_before": _string(row.get("review_status")) or "NEEDS_MORE_EVIDENCE",
                "review_status_after_partial_completion": _safe_review_status(partial),
                "partial_completion_found": partial_found,
                "completed_reviewer_metadata": ";".join(completed_reviewer),
                "completed_reviewer_metadata_count": len(completed_reviewer),
                "completed_material_evidence_fields": ";".join(completed_material),
                "completed_material_evidence_field_count": len(completed_material),
                "blocker_reduction_class": reduction,
                "material_checklist_blocker_reduced": material_reduced,
                "remaining_missing_evidence_fields": remaining_fields,
                "remaining_missing_evidence_categories": remaining_categories,
                "remaining_checklist_blockers": _string(row.get("checklist_blockers")),
                "checklist_pass_before": checklist_before,
                "checklist_pass_after_partial_completion": checklist_after,
                "approval_candidate_after_partial_completion": False,
                "include_flag_after_partial_completion": False,
                "valid_for_signal_date_after_partial_completion": False,
                "survivorship_bias_resolved_after_partial_completion": False,
                "approved_for_pit_universe_present": _contains_approval(partial),
                "clean_review_updates_created": False,
                "approval_applied": False,
                "pit_review_run": False,
                "export_readiness_run": False,
                "export_staging_run": False,
                "universe_exported": False,
                "no_data_raw_write": True,
                "no_data_processed_write": True,
                "no_current_candidates_generated": True,
                "no_snapshot_built": True,
                "no_forward_labels": True,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_order_placement": True,
                "no_message_sent": True,
                "impact_only": True,
            }
        )
    return pd.DataFrame(rows, columns=IMPACT_COLUMNS)


def resolve_first_batch_partial_completion_impact_paths(output_dir: str | Path, impact_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / impact_id
    return {
        "artifact_dir": artifact_dir,
        "impact_csv": artifact_dir / "first_batch_partial_completion_impact.csv",
        "completed_field_to_blocker_matrix": artifact_dir / "completed_field_to_blocker_matrix.csv",
        "still_missing_after_partial_completion": artifact_dir / "still_missing_after_partial_completion.csv",
        "checklist_pass_requirements_remaining": artifact_dir / "checklist_pass_requirements_remaining.csv",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def write_first_batch_partial_completion_impact_artifacts(
    result: FirstBatchPartialCompletionImpactResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.impact_frame.to_csv(paths["impact_csv"], index=False)
    _completed_field_matrix(result.impact_frame).to_csv(paths["completed_field_to_blocker_matrix"], index=False)
    _still_missing(result.impact_frame).to_csv(paths["still_missing_after_partial_completion"], index=False)
    _requirements_remaining(result.impact_frame).to_csv(paths["checklist_pass_requirements_remaining"], index=False)
    paths["report"].write_text(render_first_batch_partial_completion_impact_report(result), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_json_safe(build_first_batch_partial_completion_impact_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


def render_first_batch_partial_completion_impact_report(result: FirstBatchPartialCompletionImpactResult) -> str:
    return "\n".join(
        [
            f"# First-Batch Partial Completion Impact: {result.impact_id}",
            "",
            SAFETY_STATEMENT,
            "",
            "This is a blocker-delta report only. It does not create clean review updates or apply PIT approval.",
            "",
            "## Summary",
            "",
            f"- completion_plan_id: {result.completion_plan_id}",
            f"- partial_completion_path: {result.partial_completion_path}",
            f"- row_count: {result.row_count}",
            f"- completed_row_count: {result.completed_row_count}",
            f"- completed_field_count: {result.completed_field_count}",
            f"- blocker_reduced_count: {result.blocker_reduced_count}",
            f"- material_blocker_reduced_count: {result.material_blocker_reduced_count}",
            f"- checklist_pass_count: {result.checklist_pass_count}",
            f"- remaining_blocked_count: {result.remaining_blocked_count}",
            f"- clean_review_updates_created: {result.clean_review_updates_created}",
            f"- approval_applied: {result.approval_applied}",
            "",
            "## Interpretation",
            "",
            "Reviewer metadata can improve audit completeness, but it does not satisfy PIT evidence gates by itself.",
            "Rows remain blocked until required PIT metadata, accepted no-hit support, survivorship rationale, and source evidence checks are complete in later explicit workflows.",
            "",
        ]
    )


def build_first_batch_partial_completion_impact_metadata(
    result: FirstBatchPartialCompletionImpactResult,
) -> dict[str, Any]:
    return {
        "impact_id": result.impact_id,
        "status": result.status,
        "completion_plan_id": result.completion_plan_id,
        "partial_completion_path": result.partial_completion_path,
        "row_count": result.row_count,
        "completed_row_count": result.completed_row_count,
        "completed_field_count": result.completed_field_count,
        "blocker_reduced_count": result.blocker_reduced_count,
        "material_blocker_reduced_count": result.material_blocker_reduced_count,
        "checklist_pass_count": result.checklist_pass_count,
        "remaining_blocked_count": result.remaining_blocked_count,
        "clean_review_updates_created": False,
        "approval_applied": False,
        "pit_review_run": False,
        "export_readiness_run": False,
        "export_staging_run": False,
        "universe_exported": False,
        "active_worklist_mutated": False,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "cache_mutated": False,
        "impact_only": True,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        "safety_statement": SAFETY_STATEMENT,
        "known_limitations": [
            "This workflow only reports blocker deltas and does not create clean review updates.",
            "Reviewer metadata completion does not reduce material PIT evidence blockers by itself.",
            "Rows remain blocked until later explicit review workflows complete PIT evidence gates.",
        ],
    }


def _completed_field_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in frame.to_dict("records"):
        completed = _split_semicolon(_string(row.get("completed_reviewer_metadata")))
        completed += _split_semicolon(_string(row.get("completed_material_evidence_fields")))
        if not completed:
            rows.append(
                {
                    "impact_id": row.get("impact_id", ""),
                    "signal_date": row.get("signal_date", ""),
                    "symbol": row.get("symbol", ""),
                    "universe_name": row.get("universe_name", ""),
                    "completed_field": "",
                    "field_class": "NONE",
                    "blocker_reduced": "False",
                    "material_checklist_blocker_reduced": "False",
                    "notes": "No partial completion field supplied.",
                }
            )
            continue
        for field in completed:
            material = field in MATERIAL_EVIDENCE_FIELDS
            rows.append(
                {
                    "impact_id": row.get("impact_id", ""),
                    "signal_date": row.get("signal_date", ""),
                    "symbol": row.get("symbol", ""),
                    "universe_name": row.get("universe_name", ""),
                    "completed_field": field,
                    "field_class": "MATERIAL_EVIDENCE" if material else "REVIEWER_METADATA",
                    "blocker_reduced": "True" if not material else "Potential",
                    "material_checklist_blocker_reduced": str(material),
                    "notes": (
                        "Reviewer metadata improves audit trail only."
                        if not material
                        else "Material evidence still requires source authority and policy validation."
                    ),
                }
            )
    return pd.DataFrame(rows)


def _still_missing(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "impact_id",
        "signal_date",
        "symbol",
        "universe_name",
        "partial_completion_found",
        "remaining_missing_evidence_fields",
        "remaining_missing_evidence_categories",
        "remaining_checklist_blockers",
        "checklist_pass_after_partial_completion",
        "approval_candidate_after_partial_completion",
    ]
    return frame[columns].copy()


def _requirements_remaining(frame: pd.DataFrame) -> pd.DataFrame:
    row_count = len(frame)
    stock_rows = int((frame["universe_name"].astype(str) == "stock_core").sum()) if not frame.empty else 0
    return pd.DataFrame(
        [
            _requirement("as_of_date", "PIT-safe as-of date at or before signal date", row_count),
            _requirement("industry", "Reviewed PIT-safe industry or accepted blank/mapping policy", row_count),
            _requirement("is_active", "Accepted date-specific active/traded context", row_count),
            _requirement("is_active_evidence", "Authoritative or accepted evidence reference", row_count),
            _requirement("revision_id", "Reviewed source revision lineage", row_count),
            _requirement("t_plus_rule", "Reviewed trading rule metadata", row_count),
            _requirement("is_st", "Stock ST/no-ST evidence or accepted no-hit support", stock_rows),
            _requirement("survivorship_bias_resolution", "Reviewer survivorship rationale and accepted support", row_count),
            _requirement("reviewer_no_hit_acceptance", "Accepted no-hit support by symbol/date/universe/exception_type", row_count),
        ]
    )


def _requirement(requirement: str, pass_condition: str, blocked_row_count: int) -> dict[str, Any]:
    return {
        "requirement": requirement,
        "pass_condition": pass_condition,
        "blocked_row_count_after_partial_completion": blocked_row_count,
        "status_after_partial_completion": "BLOCKED" if blocked_row_count else "CLEAR",
    }


def _impact_counts(frame: pd.DataFrame) -> dict[str, int]:
    completed_rows = int((pd.to_numeric(frame["completed_reviewer_metadata_count"], errors="coerce").fillna(0) > 0).sum())
    completed_fields = int(pd.to_numeric(frame["completed_reviewer_metadata_count"], errors="coerce").fillna(0).sum())
    material = int(
        (pd.to_numeric(frame["completed_material_evidence_field_count"], errors="coerce").fillna(0) > 0).sum()
    )
    return {
        "completed_row_count": completed_rows,
        "completed_field_count": completed_fields,
        "blocker_reduced_count": completed_rows,
        "material_blocker_reduced_count": material,
        "checklist_pass_count": int((frame["checklist_pass_after_partial_completion"].astype(str) == "True").sum()),
        "remaining_blocked_count": len(frame),
    }


def _partial_by_identity(frame: pd.DataFrame) -> dict[tuple[str, str, str], dict[str, Any]]:
    if frame.empty:
        return {}
    return {_identity_key(row): row for row in frame.to_dict("records")}


def _identity_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _string(row.get("signal_date")),
        normalize_symbol_value(row.get("symbol")),
        _string(row.get("universe_name")),
    )


def _completed_fields(row: dict[str, Any], fields: list[str]) -> list[str]:
    if not row:
        return []
    return [field for field in fields if _string(row.get(field))]


def _completed_material_fields(partial: dict[str, Any], plan_row: dict[str, Any]) -> list[str]:
    if not partial:
        return []
    missing = set(_split_semicolon(_string(plan_row.get("missing_evidence_fields")).replace(",", ";")))
    return [field for field in MATERIAL_EVIDENCE_FIELDS if field in missing and _string(partial.get(field))]


def _safe_review_status(partial: dict[str, Any]) -> str:
    status = _string(partial.get("review_status"))
    if not status or status == "APPROVED_FOR_PIT_UNIVERSE":
        return "NEEDS_MORE_EVIDENCE"
    return status


def _contains_approval(row: dict[str, Any]) -> bool:
    if not row:
        return False
    return "APPROVED_FOR_PIT_UNIVERSE" in json.dumps(row, ensure_ascii=False)


def _normalize_identity(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in ["signal_date", "symbol", "universe_name"]:
        if column not in result.columns:
            result[column] = ""
    result["symbol"] = result["symbol"].map(normalize_symbol_value)
    result["signal_date"] = result["signal_date"].astype(str)
    result["universe_name"] = result["universe_name"].astype(str)
    return result


def _impact_id(
    request: FirstBatchPartialCompletionImpactRequest,
    plan_frame: pd.DataFrame,
    partial_frame: pd.DataFrame,
) -> str:
    digest = hashlib.sha256()
    digest.update(str(request.completion_plan).encode("utf-8"))
    digest.update(str(request.partial_completion or "").encode("utf-8"))
    digest.update("|".join(plan_frame.get("symbol", pd.Series(dtype=str)).astype(str).tolist()).encode("utf-8"))
    if not partial_frame.empty:
        digest.update(partial_frame.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _first_non_empty(frame: pd.DataFrame, column: str) -> str:
    if column not in frame.columns:
        return ""
    for value in frame[column].tolist():
        text = _string(value)
        if text:
            return text
    return ""


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def _bool(value: Any, *, default: bool = False) -> bool:
    text = _string(value).lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return default


def _string(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _assert_settings_safe(settings: FirstBatchPartialCompletionImpactSettings) -> None:
    unsafe = {
        "enable_approval": settings.enable_approval,
        "enable_clean_review_updates": settings.enable_clean_review_updates,
        "enable_pit_review": settings.enable_pit_review,
        "enable_export_readiness": settings.enable_export_readiness,
        "enable_export_staging": settings.enable_export_staging,
        "enable_universe_export": settings.enable_universe_export,
        "enable_data_raw_write": settings.enable_data_raw_write,
        "enable_data_processed_write": settings.enable_data_processed_write,
        "enable_current_candidates": settings.enable_current_candidates,
        "enable_snapshot_build": settings.enable_snapshot_build,
        "enable_forward_labels": settings.enable_forward_labels,
        "enable_cache_mutation": settings.enable_cache_mutation,
        "enable_live_trading": settings.enable_live_trading,
        "enable_broker_api": settings.enable_broker_api,
        "enable_order_placement": settings.enable_order_placement,
        "enable_message_delivery": settings.enable_message_delivery,
    }
    enabled = [name for name, value in unsafe.items() if value]
    if enabled:
        raise ValueError(f"Unsafe first-batch partial completion impact settings enabled: {', '.join(enabled)}")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        return value.item()
    return value

