"""Report-only reviewed replacement worklist planning.

This module consumes a universe-profile split-worklist plan and writes future
replacement worklist templates under reports only. It does not mutate active
worklists, approve/reject rows, export universe files, build snapshots, run
current-candidates, compute labels, mutate cache, call APIs, or perform trading
workflows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


PLAN_COLUMNS = [
    "replacement_plan_id",
    "source_split_plan_id",
    "source_worklist_id",
    "source_policy_audit_id",
    "signal_date",
    "symbol",
    "current_universe_name",
    "future_universe_name",
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
    "manual_review_required",
    "replacement_plan_only",
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
    "replacement_plan_id",
    "source_split_plan_id",
    "source_worklist_id",
    "signal_date",
    "symbol",
    "future_universe_name",
    "resolved_instrument_type",
    "review_status",
    "include_flag",
    "valid_for_signal_date",
    "reviewer",
    "reviewed_at",
    "review_reason",
    "evidence_source",
    "evidence_path",
    "evidence_reference",
    "manual_review_required",
]

SAFETY_STATEMENT = (
    "No approval, rejection, active worklist mutation, universe export, data/raw write, "
    "data/processed write, current-candidates generation, snapshot build, forward labels, "
    "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
    "or cache mutation was invoked."
)


@dataclass(frozen=True)
class ReviewedReplacementWorklistPlanSettings:
    output_dir: Path = Path("outputs/reports/reviewed_replacement_worklist_plan")
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
class ReviewedReplacementWorklistPlanRequest:
    split_plan: Path


@dataclass(frozen=True)
class ReviewedReplacementWorklistPlanPaths:
    artifact_dir: Path
    plan_csv: Path
    stock_core_worklist: Path
    etf_core_worklist: Path
    mixed_demo_core_worklist: Path
    stock_core_update_template: Path
    etf_core_update_template: Path
    mixed_demo_core_update_template: Path
    report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "reviewed_replacement_worklist_plan": self.plan_csv,
            "replacement_worklist_stock_core": self.stock_core_worklist,
            "replacement_worklist_etf_core": self.etf_core_worklist,
            "replacement_worklist_mixed_demo_core": self.mixed_demo_core_worklist,
            "replacement_update_template_stock_core": self.stock_core_update_template,
            "replacement_update_template_etf_core": self.etf_core_update_template,
            "replacement_update_template_mixed_demo_core": self.mixed_demo_core_update_template,
            "report": self.report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ReviewedReplacementWorklistPlanResult:
    replacement_plan_id: str
    status: str
    request: ReviewedReplacementWorklistPlanRequest
    row_count: int
    stock_core_row_count: int
    etf_core_row_count: int
    mixed_demo_core_row_count: int
    profile_conflict_count: int
    active_worklist_mutated: bool
    plan_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def load_split_worklist_plan_for_replacement(split_plan: str | Path) -> pd.DataFrame:
    path = Path(split_plan)
    if not path.exists():
        raise FileNotFoundError(f"Universe profile split-worklist plan CSV not found: {path}")
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    required = {"plan_id", "signal_date", "symbol", "recommended_future_universe"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Split-worklist plan is missing required columns: {', '.join(missing)}")
    return frame


def build_reviewed_replacement_worklist_plan(
    *,
    split_plan: str | Path,
    output_dir: str | Path | None = None,
    settings: ReviewedReplacementWorklistPlanSettings | None = None,
) -> ReviewedReplacementWorklistPlanResult:
    resolved_settings = settings or ReviewedReplacementWorklistPlanSettings()
    if output_dir is not None:
        resolved_settings = ReviewedReplacementWorklistPlanSettings(
            output_dir=Path(output_dir),
            config_version=resolved_settings.config_version,
            write_artifacts=resolved_settings.write_artifacts,
            enable_active_worklist_mutation=resolved_settings.enable_active_worklist_mutation,
            enable_approval=resolved_settings.enable_approval,
            enable_rejection=resolved_settings.enable_rejection,
            enable_universe_export=resolved_settings.enable_universe_export,
            enable_data_raw_write=resolved_settings.enable_data_raw_write,
            enable_data_processed_write=resolved_settings.enable_data_processed_write,
            enable_current_candidates=resolved_settings.enable_current_candidates,
            enable_snapshot_build=resolved_settings.enable_snapshot_build,
            enable_forward_labels=resolved_settings.enable_forward_labels,
            enable_cache_mutation=resolved_settings.enable_cache_mutation,
            enable_live_trading=resolved_settings.enable_live_trading,
            enable_broker_api=resolved_settings.enable_broker_api,
            enable_order_placement=resolved_settings.enable_order_placement,
            enable_message_delivery=resolved_settings.enable_message_delivery,
            enable_network_api=resolved_settings.enable_network_api,
            enable_llm_api=resolved_settings.enable_llm_api,
        )
    _assert_settings_safe(resolved_settings)
    request = ReviewedReplacementWorklistPlanRequest(split_plan=Path(split_plan))
    split_frame = load_split_worklist_plan_for_replacement(request.split_plan)
    replacement_plan_id = _replacement_plan_id(request, split_frame, resolved_settings)
    plan_frame = _build_plan_frame(split_frame, replacement_plan_id)
    counts = _counts(plan_frame)
    warnings = _warnings(counts)
    paths = resolve_reviewed_replacement_worklist_plan_paths(resolved_settings.output_dir, replacement_plan_id)
    result = ReviewedReplacementWorklistPlanResult(
        replacement_plan_id=replacement_plan_id,
        status="WARN" if counts["profile_conflict_count"] else "PASS",
        request=request,
        row_count=len(plan_frame),
        stock_core_row_count=counts["stock_core_row_count"],
        etf_core_row_count=counts["etf_core_row_count"],
        mixed_demo_core_row_count=counts["mixed_demo_core_row_count"],
        profile_conflict_count=counts["profile_conflict_count"],
        active_worklist_mutated=False,
        plan_frame=plan_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        audit_metadata=_audit_metadata(resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_reviewed_replacement_worklist_plan_artifacts(result)
    return result


def resolve_reviewed_replacement_worklist_plan_paths(
    output_dir: str | Path,
    replacement_plan_id: str,
) -> ReviewedReplacementWorklistPlanPaths:
    artifact_dir = Path(output_dir) / replacement_plan_id
    return ReviewedReplacementWorklistPlanPaths(
        artifact_dir=artifact_dir,
        plan_csv=artifact_dir / "reviewed_replacement_worklist_plan.csv",
        stock_core_worklist=artifact_dir / "replacement_worklist_stock_core.csv",
        etf_core_worklist=artifact_dir / "replacement_worklist_etf_core.csv",
        mixed_demo_core_worklist=artifact_dir / "replacement_worklist_mixed_demo_core.csv",
        stock_core_update_template=artifact_dir / "replacement_update_template_stock_core.csv",
        etf_core_update_template=artifact_dir / "replacement_update_template_etf_core.csv",
        mixed_demo_core_update_template=artifact_dir / "replacement_update_template_mixed_demo_core.csv",
        report=artifact_dir / "report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_reviewed_replacement_worklist_plan_artifacts(
    result: ReviewedReplacementWorklistPlanResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.plan_frame.to_csv(paths["reviewed_replacement_worklist_plan"], index=False)
    for profile, worklist_path, template_path in [
        ("stock_core", paths["replacement_worklist_stock_core"], paths["replacement_update_template_stock_core"]),
        ("etf_core", paths["replacement_worklist_etf_core"], paths["replacement_update_template_etf_core"]),
        (
            "mixed_demo_core",
            paths["replacement_worklist_mixed_demo_core"],
            paths["replacement_update_template_mixed_demo_core"],
        ),
    ]:
        profile_frame = _profile_frame(result.plan_frame, profile)
        profile_frame.to_csv(worklist_path, index=False)
        profile_frame[TEMPLATE_COLUMNS].to_csv(template_path, index=False)
    paths["report"].write_text(render_reviewed_replacement_worklist_plan_report(result), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_json_safe(build_reviewed_replacement_worklist_plan_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


def render_reviewed_replacement_worklist_plan_report(result: ReviewedReplacementWorklistPlanResult) -> str:
    return "\n".join(
        [
            f"# Reviewed Replacement Worklist Plan: {result.replacement_plan_id}",
            "",
            SAFETY_STATEMENT,
            "This is a future replacement-template plan only. It leaves the active legacy worklist unchanged.",
            "",
            "## Summary",
            "",
            f"- row_count: {result.row_count}",
            f"- stock_core_row_count: {result.stock_core_row_count}",
            f"- etf_core_row_count: {result.etf_core_row_count}",
            f"- mixed_demo_core_row_count: {result.mixed_demo_core_row_count}",
            f"- profile_conflict_count: {result.profile_conflict_count}",
            f"- active_worklist_mutated: {result.active_worklist_mutated}",
            "",
            "## Replacement Plan",
            "",
            result.plan_frame.to_markdown(index=False) if not result.plan_frame.empty else "No rows.",
            "",
            "## Warnings",
            "",
            "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
            "",
            "## Recommended Next Action",
            "",
            "Review replacement templates manually. Do not apply approvals, reject rows, export universe files, or run current-candidates from this plan.",
            "",
        ]
    )


def build_reviewed_replacement_worklist_plan_metadata(result: ReviewedReplacementWorklistPlanResult) -> dict[str, Any]:
    return {
        "replacement_plan_id": result.replacement_plan_id,
        "status": result.status,
        "created_at": "2024-05-30T00:00:00",
        "split_plan": str(result.request.split_plan),
        "source_split_plan_id": _source_split_plan_id(result.plan_frame),
        "row_count": result.row_count,
        "stock_core_row_count": result.stock_core_row_count,
        "etf_core_row_count": result.etf_core_row_count,
        "mixed_demo_core_row_count": result.mixed_demo_core_row_count,
        "profile_conflict_count": result.profile_conflict_count,
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
        "plan_only": True,
        "replacement_plan_only": True,
        "warnings": result.warnings,
        "safety_statement": SAFETY_STATEMENT,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
        "known_limitations": [
            "This workflow creates replacement worklist templates only under outputs/reports.",
            "It does not apply reviewer approvals or rejections.",
            "It does not make rows valid for candidate generation.",
        ],
    }


def _build_plan_frame(split_frame: pd.DataFrame, replacement_plan_id: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in split_frame.to_dict("records"):
        future_universe = _future_universe(row)
        rows.append(
            {
                "replacement_plan_id": replacement_plan_id,
                "source_split_plan_id": _text(row.get("plan_id")),
                "source_worklist_id": _text(row.get("source_worklist_id")),
                "source_policy_audit_id": _text(row.get("source_policy_audit_id")),
                "signal_date": _text(row.get("signal_date")),
                "symbol": normalize_symbol_value(row.get("symbol")),
                "current_universe_name": _text(row.get("current_universe_name")),
                "future_universe_name": future_universe,
                "resolved_instrument_type": _text(row.get("resolved_instrument_type") or row.get("instrument_type")),
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
                "manual_review_required": True,
                "replacement_plan_only": True,
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


def _profile_frame(plan_frame: pd.DataFrame, profile: str) -> pd.DataFrame:
    frame = plan_frame.loc[plan_frame["future_universe_name"] == profile].copy(deep=True)
    return frame.loc[:, PLAN_COLUMNS].reset_index(drop=True)


def _future_universe(row: dict[str, Any]) -> str:
    value = _text(row.get("recommended_future_universe"))
    if value in {"stock_core", "etf_core", "mixed_demo_core"}:
        return value
    resolved = _text(row.get("resolved_instrument_type") or row.get("instrument_type")).upper()
    if resolved == "STOCK":
        return "stock_core"
    if resolved == "ETF":
        return "etf_core"
    return "mixed_demo_core"


def _counts(plan_frame: pd.DataFrame) -> dict[str, int]:
    return {
        "stock_core_row_count": _equals_count(plan_frame, "future_universe_name", "stock_core"),
        "etf_core_row_count": _equals_count(plan_frame, "future_universe_name", "etf_core"),
        "mixed_demo_core_row_count": _equals_count(plan_frame, "future_universe_name", "mixed_demo_core"),
        "profile_conflict_count": _true_count(plan_frame, "profile_conflict"),
    }


def _warnings(counts: dict[str, int]) -> list[str]:
    warnings: list[str] = []
    if counts["profile_conflict_count"]:
        warnings.append("Profile conflicts are carried forward as planning context only.")
    if counts["mixed_demo_core_row_count"]:
        warnings.append("mixed_demo_core rows require explicit manual review before any future use.")
    return warnings


def _replacement_plan_id(
    request: ReviewedReplacementWorklistPlanRequest,
    split_frame: pd.DataFrame,
    settings: ReviewedReplacementWorklistPlanSettings,
) -> str:
    payload = {
        "split_plan": str(request.split_plan),
        "config_version": settings.config_version,
        "rows": split_frame[
            [
                column
                for column in [
                    "plan_id",
                    "source_worklist_id",
                    "signal_date",
                    "symbol",
                    "recommended_future_universe",
                    "resolved_instrument_type",
                ]
                if column in split_frame
            ]
        ].to_dict("records"),
    }
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _audit_metadata(settings: ReviewedReplacementWorklistPlanSettings) -> dict[str, Any]:
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


def _assert_settings_safe(settings: ReviewedReplacementWorklistPlanSettings) -> None:
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
        raise ValueError(f"Reviewed replacement worklist planning is report-only; unsafe settings enabled: {', '.join(enabled)}")


def _source_split_plan_id(frame: pd.DataFrame) -> str:
    if frame.empty or "source_split_plan_id" not in frame:
        return ""
    values = [_text(value) for value in frame["source_split_plan_id"].drop_duplicates().tolist() if _text(value)]
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
