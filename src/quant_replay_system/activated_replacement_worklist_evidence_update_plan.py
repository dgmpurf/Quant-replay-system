"""Report-only evidence update planning from activated replacement worklists.

This workflow turns activated stock/ETF replacement planning rows into
profile-specific evidence update work packages. It does not approve/reject rows,
export universe files, build snapshots, run current-candidates, compute labels,
mutate cache, call APIs, or perform trading workflows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.point_in_time_universe_evidence_update_ingestion import COMPLETED_UPDATE_COLUMNS
from quant_replay_system.reviewed_replacement_worklist_activation import ACTIVATION_COLUMNS


PROFILE_NAMES = ["stock_core", "etf_core", "mixed_demo_core"]

PLAN_COLUMNS = [
    "plan_id",
    "activation_id",
    "acceptance_id",
    "replacement_plan_id",
    "source_split_plan_id",
    "source_policy_audit_id",
    "source_worklist_id",
    "signal_date",
    "symbol",
    "current_universe_name",
    "future_universe_name",
    "universe_name",
    "resolved_instrument_type",
    "legacy_classification",
    "profile_rule_applied",
    "profile_conflict",
    "conflict_reason",
    "review_status",
    "include_flag",
    "valid_for_signal_date",
    "reviewer",
    "reviewed_at",
    "review_reason",
    "evidence_source",
    "evidence_path",
    "evidence_reference",
    "listed_date",
    "delisted_date",
    "is_active",
    "is_st",
    "is_suspended",
    "listed_date_evidence",
    "delisted_date_evidence",
    "is_active_evidence",
    "survivorship_bias_resolved",
    "as_of_date",
    "name",
    "instrument_type",
    "exchange",
    "industry",
    "min_lot",
    "t_plus_rule",
    "available_time",
    "revision_id",
    "source",
    "hint_fields_authoritative_for_pit",
    "manual_review_required",
    "evidence_update_planning_only",
    "clean_review_updates_created",
    "active_worklist_mutated",
    "no_approval_applied",
    "no_rejection_applied",
    "no_universe_export",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
]

TEMPLATE_COLUMNS = [
    "activation_id",
    "acceptance_id",
    "replacement_plan_id",
    "source_split_plan_id",
    "source_policy_audit_id",
    "source_worklist_id",
    "current_universe_name",
    "future_universe_name",
    "resolved_instrument_type",
    "legacy_classification",
    "profile_rule_applied",
    "profile_conflict",
    "conflict_reason",
    *COMPLETED_UPDATE_COLUMNS,
    "valid_for_signal_date",
    "hint_fields_authoritative_for_pit",
    "manual_review_required",
    "evidence_update_planning_only",
    "clean_review_updates_created",
    "no_approval_applied",
    "no_rejection_applied",
    "no_universe_export",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
]

SAFETY_STATEMENT = (
    "No approval, rejection, active worklist mutation, universe export, data/raw write, "
    "data/processed write, current-candidates generation, snapshot build, forward labels, "
    "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
    "or cache mutation was invoked."
)


@dataclass(frozen=True)
class ActivatedReplacementWorklistEvidenceUpdatePlanSettings:
    output_dir: Path = Path("outputs/reports/activated_replacement_worklist_evidence_update_plan")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    enable_active_worklist_mutation: bool = False
    enable_approval: bool = False
    enable_rejection: bool = False
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
    enable_network_api: bool = False
    enable_llm_api: bool = False


@dataclass(frozen=True)
class ActivatedReplacementWorklistEvidenceUpdatePlanRequest:
    activation: Path


@dataclass(frozen=True)
class ActivatedReplacementWorklistEvidenceUpdatePlanResult:
    plan_id: str
    status: str
    request: ActivatedReplacementWorklistEvidenceUpdatePlanRequest
    activation_id: str
    acceptance_id: str
    replacement_plan_id: str
    source_split_plan_id: str
    source_policy_audit_id: str
    source_worklist_id: str
    row_count: int
    stock_core_row_count: int
    etf_core_row_count: int
    mixed_demo_core_row_count: int
    stock_core_first_batch_row_count: int
    etf_core_first_batch_row_count: int
    include_flag_true_count: int
    valid_for_signal_date_count: int
    approved_count: int
    rejected_count: int
    clean_review_updates_created: bool
    active_worklist_mutated: bool
    plan_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def load_activation_for_evidence_update_plan(activation: str | Path) -> pd.DataFrame:
    path = Path(activation)
    if not path.exists():
        raise FileNotFoundError(f"Activated replacement worklist CSV not found: {path}")
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    missing = sorted(set(ACTIVATION_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Activation artifact is missing required columns: {', '.join(missing)}")
    return frame


def build_activated_replacement_worklist_evidence_update_plan(
    *,
    activation: str | Path,
    output_dir: str | Path | None = None,
    settings: ActivatedReplacementWorklistEvidenceUpdatePlanSettings | None = None,
) -> ActivatedReplacementWorklistEvidenceUpdatePlanResult:
    resolved_settings = settings or ActivatedReplacementWorklistEvidenceUpdatePlanSettings()
    if output_dir is not None:
        resolved_settings = _replace_settings_output_dir(resolved_settings, Path(output_dir))
    _assert_settings_safe(resolved_settings)
    request = ActivatedReplacementWorklistEvidenceUpdatePlanRequest(activation=Path(activation))
    activation_frame = load_activation_for_evidence_update_plan(request.activation)
    acceptance_id = _acceptance_id_from_activation_path(request.activation)
    plan_id = _plan_id(request, activation_frame, resolved_settings)
    plan_frame = _build_plan_frame(activation_frame, plan_id, acceptance_id)
    counts = _counts(plan_frame)
    paths = resolve_activated_replacement_worklist_evidence_update_plan_paths(
        resolved_settings.output_dir,
        plan_id,
    )
    result = ActivatedReplacementWorklistEvidenceUpdatePlanResult(
        plan_id=plan_id,
        status="PASS",
        request=request,
        activation_id=_first_text(plan_frame, "activation_id"),
        acceptance_id=acceptance_id,
        replacement_plan_id=_first_text(plan_frame, "replacement_plan_id"),
        source_split_plan_id=_first_text(plan_frame, "source_split_plan_id"),
        source_policy_audit_id=_first_text(plan_frame, "source_policy_audit_id"),
        source_worklist_id=_first_text(plan_frame, "source_worklist_id"),
        row_count=len(plan_frame),
        stock_core_row_count=counts["stock_core_row_count"],
        etf_core_row_count=counts["etf_core_row_count"],
        mixed_demo_core_row_count=counts["mixed_demo_core_row_count"],
        stock_core_first_batch_row_count=len(_first_batch_frame(plan_frame, "stock_core")),
        etf_core_first_batch_row_count=len(_first_batch_frame(plan_frame, "etf_core")),
        include_flag_true_count=counts["include_flag_true_count"],
        valid_for_signal_date_count=counts["valid_for_signal_date_count"],
        approved_count=counts["approved_count"],
        rejected_count=counts["rejected_count"],
        clean_review_updates_created=False,
        active_worklist_mutated=False,
        plan_frame=plan_frame,
        artifact_paths=paths,
        warnings=[],
        audit_metadata=_audit_metadata(resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_activated_replacement_worklist_evidence_update_plan_artifacts(result)
    return result


def resolve_activated_replacement_worklist_evidence_update_plan_paths(
    output_dir: str | Path,
    plan_id: str,
) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / plan_id
    return {
        "artifact_dir": artifact_dir,
        "plan_csv": artifact_dir / "activated_replacement_worklist_evidence_update_plan.csv",
        "stock_core_evidence_worklist": artifact_dir / "stock_core_evidence_worklist.csv",
        "etf_core_evidence_worklist": artifact_dir / "etf_core_evidence_worklist.csv",
        "mixed_demo_core_evidence_worklist": artifact_dir / "mixed_demo_core_evidence_worklist.csv",
        "stock_core_update_template": artifact_dir / "stock_core_update_template.csv",
        "etf_core_update_template": artifact_dir / "etf_core_update_template.csv",
        "mixed_demo_core_update_template": artifact_dir / "mixed_demo_core_update_template.csv",
        "stock_core_first_batch_package": artifact_dir / "stock_core_first_batch_package.csv",
        "etf_core_first_batch_package": artifact_dir / "etf_core_first_batch_package.csv",
        "evidence_source_checklist": artifact_dir / "evidence_source_checklist.md",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def write_activated_replacement_worklist_evidence_update_plan_artifacts(
    result: ActivatedReplacementWorklistEvidenceUpdatePlanResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.plan_frame.to_csv(paths["plan_csv"], index=False)
    for profile in PROFILE_NAMES:
        profile_frame = _profile_frame(result.plan_frame, profile)
        profile_frame.to_csv(paths[f"{profile}_evidence_worklist"], index=False)
        profile_frame.loc[:, TEMPLATE_COLUMNS].to_csv(paths[f"{profile}_update_template"], index=False)
    _first_batch_frame(result.plan_frame, "stock_core").to_csv(paths["stock_core_first_batch_package"], index=False)
    _first_batch_frame(result.plan_frame, "etf_core").to_csv(paths["etf_core_first_batch_package"], index=False)
    paths["evidence_source_checklist"].write_text(render_evidence_source_checklist(result), encoding="utf-8")
    paths["report"].write_text(render_activated_replacement_worklist_evidence_update_plan_report(result), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_json_safe(build_activated_replacement_worklist_evidence_update_plan_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


def render_evidence_source_checklist(result: ActivatedReplacementWorklistEvidenceUpdatePlanResult) -> str:
    return "\n".join(
        [
            f"# Evidence Source Checklist: {result.plan_id}",
            "",
            SAFETY_STATEMENT,
            "",
            "Use this checklist for later manual evidence discovery only. Do not approve rows from hints.",
            "",
            "- listing date evidence",
            "- delisting or not-delisted evidence",
            "- active status evidence",
            "- ST status evidence",
            "- suspension evidence",
            "- exchange and instrument metadata",
            "- min_lot and t_plus_rule",
            "- PIT-safe as_of_date and available_time",
            "- evidence_source, evidence_path, and evidence_reference",
            "",
            "All evidence must be reviewed before `pit-universe-evidence-update-ingestion` can emit clean review updates.",
        ]
    )


def render_activated_replacement_worklist_evidence_update_plan_report(
    result: ActivatedReplacementWorklistEvidenceUpdatePlanResult,
) -> str:
    return "\n".join(
        [
            f"# Activated Replacement Worklist Evidence Update Plan: {result.plan_id}",
            "",
            SAFETY_STATEMENT,
            "This is evidence-update planning context only. It does not create clean review updates.",
            "",
            "## Summary",
            "",
            f"- activation_id: {result.activation_id}",
            f"- acceptance_id: {result.acceptance_id}",
            f"- replacement_plan_id: {result.replacement_plan_id}",
            f"- source_split_plan_id: {result.source_split_plan_id}",
            f"- source_policy_audit_id: {result.source_policy_audit_id}",
            f"- source_worklist_id: {result.source_worklist_id}",
            f"- row_count: {result.row_count}",
            f"- stock_core_row_count: {result.stock_core_row_count}",
            f"- etf_core_row_count: {result.etf_core_row_count}",
            f"- mixed_demo_core_row_count: {result.mixed_demo_core_row_count}",
            f"- approved_count: {result.approved_count}",
            f"- rejected_count: {result.rejected_count}",
            f"- valid_for_signal_date_count: {result.valid_for_signal_date_count}",
            f"- clean_review_updates_created: {result.clean_review_updates_created}",
            "",
            "## First Batch Selection",
            "",
            "- stock_core: first symbol by activated profile order, all selected signal dates.",
            "- etf_core: first symbol by activated profile order, all selected signal dates.",
            "",
            "## Recommended Next Action",
            "",
            "Fill profile-specific evidence templates manually, then validate completed updates with pit-universe-evidence-update-ingestion.",
            "",
        ]
    )


def build_activated_replacement_worklist_evidence_update_plan_metadata(
    result: ActivatedReplacementWorklistEvidenceUpdatePlanResult,
) -> dict[str, Any]:
    return {
        "plan_id": result.plan_id,
        "status": result.status,
        "created_at": _first_text(result.plan_frame, "activated_at"),
        "activation": str(result.request.activation),
        "activation_id": result.activation_id,
        "acceptance_id": result.acceptance_id,
        "replacement_plan_id": result.replacement_plan_id,
        "source_split_plan_id": result.source_split_plan_id,
        "source_policy_audit_id": result.source_policy_audit_id,
        "source_worklist_id": result.source_worklist_id,
        "row_count": result.row_count,
        "stock_core_row_count": result.stock_core_row_count,
        "etf_core_row_count": result.etf_core_row_count,
        "mixed_demo_core_row_count": result.mixed_demo_core_row_count,
        "stock_core_first_batch_row_count": result.stock_core_first_batch_row_count,
        "etf_core_first_batch_row_count": result.etf_core_first_batch_row_count,
        "include_flag_true_count": result.include_flag_true_count,
        "valid_for_signal_date_count": result.valid_for_signal_date_count,
        "approved_count": result.approved_count,
        "rejected_count": result.rejected_count,
        "clean_review_updates_created": result.clean_review_updates_created,
        "active_worklist_mutated": False,
        "no_approval_applied": True,
        "no_rejection_applied": True,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "evidence_update_planning_only": True,
        "warnings": result.warnings,
        "safety_statement": SAFETY_STATEMENT,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
        "known_limitations": [
            "This workflow creates evidence update packages only under outputs/reports.",
            "It does not create clean review updates.",
            "It does not apply approvals or rejections.",
            "It does not export usable universe files or make current-candidates inputs.",
        ],
    }


def _build_plan_frame(activation_frame: pd.DataFrame, plan_id: str, acceptance_id: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in activation_frame.to_dict("records"):
        future_universe = _text(row.get("future_universe_name"))
        rows.append(
            {
                "plan_id": plan_id,
                "activation_id": _text(row.get("activation_id")),
                "acceptance_id": acceptance_id,
                "replacement_plan_id": _text(row.get("replacement_plan_id")),
                "source_split_plan_id": _text(row.get("source_split_plan_id")),
                "source_policy_audit_id": _text(row.get("source_policy_audit_id")),
                "source_worklist_id": _text(row.get("source_worklist_id")),
                "signal_date": _text(row.get("signal_date")),
                "symbol": normalize_symbol_value(row.get("symbol")),
                "current_universe_name": _text(row.get("current_universe_name")),
                "future_universe_name": future_universe,
                "universe_name": future_universe,
                "resolved_instrument_type": _text(row.get("resolved_instrument_type")),
                "legacy_classification": _text(row.get("legacy_classification")),
                "profile_rule_applied": _text(row.get("profile_rule_applied")),
                "profile_conflict": _to_bool(row.get("profile_conflict")),
                "conflict_reason": _text(row.get("conflict_reason")),
                "review_status": "NEEDS_MANUAL_REVIEW",
                "include_flag": False,
                "valid_for_signal_date": False,
                "reviewer": "",
                "reviewed_at": "",
                "review_reason": "",
                "evidence_source": "",
                "evidence_path": "",
                "evidence_reference": "",
                "listed_date": "",
                "delisted_date": "",
                "is_active": "",
                "is_st": "",
                "is_suspended": "",
                "listed_date_evidence": "",
                "delisted_date_evidence": "",
                "is_active_evidence": "",
                "survivorship_bias_resolved": False,
                "as_of_date": "",
                "name": "",
                "instrument_type": "",
                "exchange": "",
                "industry": "",
                "min_lot": "",
                "t_plus_rule": "",
                "available_time": "",
                "revision_id": "",
                "source": "",
                "hint_fields_authoritative_for_pit": False,
                "manual_review_required": True,
                "evidence_update_planning_only": True,
                "clean_review_updates_created": False,
                "active_worklist_mutated": False,
                "no_approval_applied": True,
                "no_rejection_applied": True,
                "no_universe_export": True,
                "no_data_raw_write": True,
                "no_data_processed_write": True,
                "no_current_candidates_generated": True,
                "no_snapshot_built": True,
                "no_forward_labels": True,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_order_placement": True,
                "no_message_sent": True,
            }
        )
    return pd.DataFrame(rows, columns=PLAN_COLUMNS).sort_values(
        ["future_universe_name", "signal_date", "symbol"],
    ).reset_index(drop=True)


def _first_batch_frame(frame: pd.DataFrame, profile: str) -> pd.DataFrame:
    profile_frame = _profile_frame(frame, profile)
    if profile_frame.empty:
        return profile_frame
    first_symbol = str(profile_frame["symbol"].iloc[0])
    return profile_frame.loc[profile_frame["symbol"].astype(str) == first_symbol].reset_index(drop=True)


def _profile_frame(frame: pd.DataFrame, profile: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PLAN_COLUMNS)
    return frame.loc[frame["future_universe_name"] == profile, PLAN_COLUMNS].reset_index(drop=True)


def _counts(frame: pd.DataFrame) -> dict[str, int]:
    return {
        "stock_core_row_count": _equals_count(frame, "future_universe_name", "stock_core"),
        "etf_core_row_count": _equals_count(frame, "future_universe_name", "etf_core"),
        "mixed_demo_core_row_count": _equals_count(frame, "future_universe_name", "mixed_demo_core"),
        "include_flag_true_count": _true_count(frame, "include_flag"),
        "valid_for_signal_date_count": _true_count(frame, "valid_for_signal_date"),
        "approved_count": _equals_count(frame, "review_status", "APPROVED_FOR_PIT_UNIVERSE"),
        "rejected_count": _equals_count(frame, "review_status", "REJECTED"),
    }


def _acceptance_id_from_activation_path(path: Path) -> str:
    parts = list(path.parts)
    if "reviewed_replacement_worklist_activation" in parts:
        idx = parts.index("reviewed_replacement_worklist_activation")
        if idx + 1 < len(parts):
            activation_id = parts[idx + 1]
            metadata_path = Path(*parts[: idx + 2]) / "metadata.json"
            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                    acceptance_path = _text(metadata.get("acceptance"))
                    if acceptance_path:
                        acceptance_parts = Path(acceptance_path).parts
                        if "reviewed_replacement_worklist_acceptance" in acceptance_parts:
                            acc_idx = acceptance_parts.index("reviewed_replacement_worklist_acceptance")
                            if acc_idx + 1 < len(acceptance_parts):
                                return acceptance_parts[acc_idx + 1]
                except json.JSONDecodeError:
                    return ""
            _ = activation_id
    return ""


def _plan_id(
    request: ActivatedReplacementWorklistEvidenceUpdatePlanRequest,
    activation_frame: pd.DataFrame,
    settings: ActivatedReplacementWorklistEvidenceUpdatePlanSettings,
) -> str:
    payload = {
        "activation": str(request.activation),
        "config_version": settings.config_version,
        "rows": activation_frame[
            [column for column in ["activation_id", "signal_date", "symbol", "future_universe_name"] if column in activation_frame]
        ].to_dict("records"),
    }
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _replace_settings_output_dir(
    settings: ActivatedReplacementWorklistEvidenceUpdatePlanSettings,
    output_dir: Path,
) -> ActivatedReplacementWorklistEvidenceUpdatePlanSettings:
    return ActivatedReplacementWorklistEvidenceUpdatePlanSettings(
        output_dir=output_dir,
        config_version=settings.config_version,
        write_artifacts=settings.write_artifacts,
        enable_active_worklist_mutation=settings.enable_active_worklist_mutation,
        enable_approval=settings.enable_approval,
        enable_rejection=settings.enable_rejection,
        enable_universe_export=settings.enable_universe_export,
        enable_data_raw_write=settings.enable_data_raw_write,
        enable_data_processed_write=settings.enable_data_processed_write,
        enable_current_candidates=settings.enable_current_candidates,
        enable_snapshot_build=settings.enable_snapshot_build,
        enable_forward_labels=settings.enable_forward_labels,
        enable_cache_mutation=settings.enable_cache_mutation,
        enable_live_trading=settings.enable_live_trading,
        enable_broker_api=settings.enable_broker_api,
        enable_order_placement=settings.enable_order_placement,
        enable_message_delivery=settings.enable_message_delivery,
        enable_network_api=settings.enable_network_api,
        enable_llm_api=settings.enable_llm_api,
    )


def _audit_metadata(settings: ActivatedReplacementWorklistEvidenceUpdatePlanSettings) -> dict[str, Any]:
    return {
        "config_version": settings.config_version,
        "active_worklist_mutated": False,
        "no_approval_applied": True,
        "no_rejection_applied": True,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "no_cache_mutation": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "no_network_api": True,
        "no_llm_api": True,
    }


def _assert_settings_safe(settings: ActivatedReplacementWorklistEvidenceUpdatePlanSettings) -> None:
    unsafe = {
        "enable_active_worklist_mutation": settings.enable_active_worklist_mutation,
        "enable_approval": settings.enable_approval,
        "enable_rejection": settings.enable_rejection,
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
        "enable_network_api": settings.enable_network_api,
        "enable_llm_api": settings.enable_llm_api,
    }
    enabled = [name for name, value in unsafe.items() if value]
    if enabled:
        raise ValueError(
            "Activated replacement worklist evidence update plan is report-only; unsafe settings enabled: "
            + ", ".join(enabled)
        )


def _first_text(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame:
        return ""
    values = [_text(value) for value in frame[column].drop_duplicates().tolist() if _text(value)]
    return values[0] if values else ""


def _equals_count(frame: pd.DataFrame, column: str, value: str) -> int:
    if frame.empty or column not in frame:
        return 0
    return int((frame[column].astype(str) == value).sum())


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
