"""Report-only universe profile registry and split-worklist planning.

This module reads local policy-audit/worklist artifacts and a local universe
profile registry, then writes future split guidance under reports only. It does
not mutate active worklists, approve/reject rows, export universe files, build
snapshots, run current-candidates, compute labels, mutate cache, or perform
trading workflows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


REGISTRY_SNAPSHOT_COLUMNS = [
    "profile_name",
    "allowed_instrument_types",
    "profile_type",
    "mixed_allowed",
    "demo_only",
    "description",
]

PLAN_COLUMNS = [
    "plan_id",
    "source_worklist_id",
    "source_policy_audit_id",
    "signal_date",
    "current_universe_name",
    "symbol",
    "instrument_type",
    "resolved_instrument_type",
    "current_profile_classification",
    "recommended_future_universe",
    "profile_rule_applied",
    "profile_conflict",
    "conflict_reason",
    "legacy_classification",
    "should_mutate_active_worklist",
    "should_approve",
    "should_reject",
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
    "plan_only",
]

SUMMARY_COLUMNS = [
    "plan_id",
    "source_worklist_id",
    "source_policy_audit_id",
    "row_count",
    "stock_row_count",
    "etf_row_count",
    "unknown_instrument_type_count",
    "legacy_mixed_demo_row_count",
    "recommended_stock_core_count",
    "recommended_etf_core_count",
    "recommended_mixed_demo_core_count",
    "profile_conflict_count",
    "active_worklist_mutated",
    "next_manual_action",
]

SAFETY_STATEMENT = (
    "No approval, rejection, active worklist mutation, universe export, data/raw write, "
    "data/processed write, current-candidates generation, snapshot build, forward labels, "
    "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
    "or cache mutation was invoked."
)


@dataclass(frozen=True)
class UniverseProfileRegistrySettings:
    profiles_path: Path = Path("config/universe_profiles.yaml")
    config_version: str = "v0.1"


@dataclass(frozen=True)
class UniverseProfileDefinition:
    profile_name: str
    allowed_instrument_types: tuple[str, ...]
    profile_type: str
    mixed_allowed: bool
    demo_only: bool
    description: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_name": self.profile_name,
            "allowed_instrument_types": ",".join(self.allowed_instrument_types),
            "profile_type": self.profile_type,
            "mixed_allowed": self.mixed_allowed,
            "demo_only": self.demo_only,
            "description": self.description,
        }


@dataclass(frozen=True)
class UniverseProfileSplitWorklistPlanSettings:
    output_dir: Path = Path("outputs/reports/universe_profile_split_worklist_plan")
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
class UniverseProfileSplitWorklistPlanRequest:
    worklist: Path | None
    policy_audit: Path | None
    profiles: Path


@dataclass(frozen=True)
class UniverseProfileSplitWorklistPlanRow:
    values: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {column: self.values.get(column, "") for column in PLAN_COLUMNS}


@dataclass(frozen=True)
class UniverseProfileSplitWorklistPlanArtifactPaths:
    artifact_dir: Path
    registry_snapshot: Path
    plan_csv: Path
    summary_csv: Path
    stock_core_guidance: Path
    etf_core_guidance: Path
    mixed_demo_core_guidance: Path
    report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "registry_snapshot": self.registry_snapshot,
            "plan_csv": self.plan_csv,
            "summary_csv": self.summary_csv,
            "stock_core_guidance": self.stock_core_guidance,
            "etf_core_guidance": self.etf_core_guidance,
            "mixed_demo_core_guidance": self.mixed_demo_core_guidance,
            "report": self.report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class UniverseProfileSplitWorklistPlanResult:
    plan_id: str
    status: str
    request: UniverseProfileSplitWorklistPlanRequest
    row_count: int
    stock_row_count: int
    etf_row_count: int
    unknown_instrument_type_count: int
    legacy_mixed_demo_row_count: int
    recommended_stock_core_count: int
    recommended_etf_core_count: int
    recommended_mixed_demo_core_count: int
    profile_conflict_count: int
    registry: dict[str, UniverseProfileDefinition]
    registry_frame: pd.DataFrame
    plan_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def load_universe_profile_registry(
    path: str | Path = "config/universe_profiles.yaml",
) -> dict[str, UniverseProfileDefinition]:
    """Load local universe profile definitions."""

    profiles_path = Path(path)
    if not profiles_path.exists():
        raise FileNotFoundError(f"Universe profile registry not found: {profiles_path}")
    raw = yaml.safe_load(profiles_path.read_text(encoding="utf-8")) or {}
    profiles = raw.get("profiles", raw)
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("Universe profile registry must contain a non-empty profiles mapping.")
    registry: dict[str, UniverseProfileDefinition] = {}
    for name, values in profiles.items():
        if not isinstance(values, dict):
            raise ValueError(f"Universe profile {name} must be a mapping.")
        allowed = tuple(_instrument_type(value) for value in values.get("allowed_instrument_types", []))
        allowed = tuple(value for value in allowed if value != "UNKNOWN")
        if not allowed:
            raise ValueError(f"Universe profile {name} must define allowed_instrument_types.")
        registry[str(name)] = UniverseProfileDefinition(
            profile_name=str(name),
            allowed_instrument_types=allowed,
            profile_type=_text(values.get("profile_type")),
            mixed_allowed=_to_bool(values.get("mixed_allowed")),
            demo_only=_to_bool(values.get("demo_only")),
            description=_text(values.get("description")),
        )
    return registry


def load_universe_profile_split_worklist_inputs(
    *,
    worklist: str | Path | None = None,
    policy_audit: str | Path | None = None,
) -> pd.DataFrame:
    """Load worklist and/or policy-audit rows while preserving symbols."""

    if worklist is None and policy_audit is None:
        raise ValueError("At least one of worklist or policy_audit must be provided.")
    if worklist is not None and policy_audit is not None:
        return _enrich_worklist_with_policy_audit(
            _load_worklist_frame(Path(worklist)),
            _load_policy_audit_frame(Path(policy_audit)),
        )
    if policy_audit is not None:
        return _load_policy_audit_frame(Path(policy_audit))
    return _load_worklist_frame(Path(worklist))


def classify_universe_profile_split_target(
    row: dict[str, Any],
    registry: dict[str, UniverseProfileDefinition],
) -> dict[str, Any]:
    """Classify one row against future profile rules."""

    current_universe = _text(row.get("current_universe_name") or row.get("universe_name"))
    resolved_type = _instrument_type(row.get("resolved_instrument_type") or row.get("instrument_type") or row.get("suggested_instrument_type"))
    current_classification = _text(row.get("current_profile_classification") or row.get("profile_policy_classification"))
    legacy_classification = _text(row.get("legacy_classification") or row.get("legacy_universe_classification"))
    if current_universe.lower() == "etf_core" and current_classification == "legacy_mixed_demo_universe":
        legacy_classification = legacy_classification or "legacy_mixed_demo_universe"
    recommended = _recommended_future_universe(resolved_type, current_classification, current_universe)
    profile = registry.get(recommended)
    profile_conflict = False
    conflict_reason = ""
    if current_universe in registry and current_universe != recommended:
        current_profile = registry[current_universe]
        if resolved_type not in set(current_profile.allowed_instrument_types):
            profile_conflict = True
            conflict_reason = (
                f"{resolved_type} is not allowed in current future profile {current_universe}; "
                f"plan-only split target is {recommended}."
            )
    if profile is None:
        profile_conflict = True
        conflict_reason = conflict_reason or f"Recommended future universe {recommended} is not in registry."
    elif resolved_type not in set(profile.allowed_instrument_types):
        profile_conflict = True
        conflict_reason = conflict_reason or f"{resolved_type} is not allowed in recommended profile {recommended}."
    rule = (
        "LEGACY_ETF_CORE_SPLIT_BY_INSTRUMENT_TYPE"
        if legacy_classification == "legacy_mixed_demo_universe" or current_classification == "legacy_mixed_demo_universe"
        else "PROFILE_REGISTRY_ALLOWED_INSTRUMENT_TYPE"
    )
    return {
        "resolved_instrument_type": resolved_type,
        "current_profile_classification": current_classification,
        "recommended_future_universe": recommended,
        "profile_rule_applied": rule,
        "profile_conflict": profile_conflict,
        "conflict_reason": conflict_reason,
        "legacy_classification": legacy_classification,
    }


def build_universe_profile_split_worklist_plan(
    *,
    worklist: str | Path | None = None,
    policy_audit: str | Path | None = None,
    profiles: str | Path = "config/universe_profiles.yaml",
    output_dir: str | Path | None = None,
    settings: UniverseProfileSplitWorklistPlanSettings | None = None,
) -> UniverseProfileSplitWorklistPlanResult:
    """Build report-only split-worklist planning artifacts."""

    resolved_settings = settings or UniverseProfileSplitWorklistPlanSettings()
    if output_dir is not None:
        resolved_settings = UniverseProfileSplitWorklistPlanSettings(
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
    registry = load_universe_profile_registry(profiles)
    request = UniverseProfileSplitWorklistPlanRequest(
        worklist=Path(worklist) if worklist else None,
        policy_audit=Path(policy_audit) if policy_audit else None,
        profiles=Path(profiles),
    )
    input_frame = load_universe_profile_split_worklist_inputs(worklist=request.worklist, policy_audit=request.policy_audit)
    plan_id = generate_universe_profile_split_worklist_plan_id(request, input_frame, registry, resolved_settings)
    plan_frame = _build_plan_frame(input_frame, registry, plan_id)
    counts = _counts(plan_frame)
    summary_frame = _build_summary_frame(plan_id, input_frame, plan_frame, counts)
    registry_frame = _registry_frame(registry)
    paths = resolve_universe_profile_split_worklist_plan_paths(resolved_settings.output_dir, plan_id)
    result = UniverseProfileSplitWorklistPlanResult(
        plan_id=plan_id,
        status="WARN" if counts["profile_conflict_count"] or counts["legacy_mixed_demo_row_count"] else "PASS",
        request=request,
        row_count=len(plan_frame),
        stock_row_count=counts["stock_row_count"],
        etf_row_count=counts["etf_row_count"],
        unknown_instrument_type_count=counts["unknown_instrument_type_count"],
        legacy_mixed_demo_row_count=counts["legacy_mixed_demo_row_count"],
        recommended_stock_core_count=counts["recommended_stock_core_count"],
        recommended_etf_core_count=counts["recommended_etf_core_count"],
        recommended_mixed_demo_core_count=counts["recommended_mixed_demo_core_count"],
        profile_conflict_count=counts["profile_conflict_count"],
        registry=registry,
        registry_frame=registry_frame,
        plan_frame=plan_frame,
        summary_frame=summary_frame,
        warnings=_warnings(counts),
        artifact_paths=paths.as_dict(),
        audit_metadata=_audit_metadata(request, resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_universe_profile_split_worklist_plan_artifacts(result)
    return result


def render_universe_profile_split_worklist_plan_report(result: UniverseProfileSplitWorklistPlanResult) -> str:
    """Render the split-worklist plan report."""

    return "\n".join(
        [
            f"# Universe Profile Split Worklist Plan: {result.plan_id}",
            "",
            SAFETY_STATEMENT,
            "This is a planning/preview artifact only. It does not regenerate active worklists or apply review decisions.",
            "",
            "## Summary",
            "",
            _markdown_table(result.summary_frame, SUMMARY_COLUMNS),
            "",
            "## Registry Snapshot",
            "",
            _markdown_table(result.registry_frame, REGISTRY_SNAPSHOT_COLUMNS),
            "",
            "## Split Guidance",
            "",
            _markdown_table(result.plan_frame, PLAN_COLUMNS),
            "",
            "## Warnings",
            "",
            "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
            "",
            "## Recommended Next Action",
            "",
            "Review split guidance manually. Leave the current active worklist unchanged until a separate explicit split-worklist workflow is approved.",
            "",
        ]
    )


def write_universe_profile_split_worklist_plan_artifacts(
    result: UniverseProfileSplitWorklistPlanResult,
) -> dict[str, Path]:
    """Write split-plan artifacts under outputs/reports."""

    paths = UniverseProfileSplitWorklistPlanArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    paths.registry_snapshot.write_text(_registry_yaml(result.registry), encoding="utf-8")
    result.plan_frame.to_csv(paths.plan_csv, index=False)
    result.summary_frame.to_csv(paths.summary_csv, index=False)
    _guidance_frame(result.plan_frame, "stock_core").to_csv(paths.stock_core_guidance, index=False)
    _guidance_frame(result.plan_frame, "etf_core").to_csv(paths.etf_core_guidance, index=False)
    _guidance_frame(result.plan_frame, "mixed_demo_core").to_csv(paths.mixed_demo_core_guidance, index=False)
    paths.metadata.write_text(
        json.dumps(_json_safe(build_universe_profile_split_worklist_plan_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    paths.report.write_text(render_universe_profile_split_worklist_plan_report(result), encoding="utf-8")
    return paths.as_dict()


def build_universe_profile_split_worklist_plan_metadata(
    result: UniverseProfileSplitWorklistPlanResult,
) -> dict[str, Any]:
    """Build split-plan metadata."""

    return {
        "plan_id": result.plan_id,
        "status": result.status,
        "created_at": "2024-05-29T00:00:00",
        "worklist": str(result.request.worklist) if result.request.worklist else "",
        "policy_audit": str(result.request.policy_audit) if result.request.policy_audit else "",
        "profiles": str(result.request.profiles),
        "row_count": result.row_count,
        "stock_row_count": result.stock_row_count,
        "etf_row_count": result.etf_row_count,
        "unknown_instrument_type_count": result.unknown_instrument_type_count,
        "legacy_mixed_demo_row_count": result.legacy_mixed_demo_row_count,
        "recommended_stock_core_count": result.recommended_stock_core_count,
        "recommended_etf_core_count": result.recommended_etf_core_count,
        "recommended_mixed_demo_core_count": result.recommended_mixed_demo_core_count,
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
        "plan_only": True,
        "warnings": result.warnings,
        "safety_statement": SAFETY_STATEMENT,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
        "known_limitations": [
            "This workflow plans future split worklists only and does not create active worklists.",
            "Legacy mixed etf_core rows remain active-workflow context until a separate explicit migration is approved.",
            "The plan does not validate PIT evidence, strategy performance, or trading readiness.",
        ],
    }


def generate_universe_profile_split_worklist_plan_id(
    request: UniverseProfileSplitWorklistPlanRequest,
    input_frame: pd.DataFrame,
    registry: dict[str, UniverseProfileDefinition],
    settings: UniverseProfileSplitWorklistPlanSettings,
) -> str:
    payload = {
        "worklist": str(request.worklist) if request.worklist else "",
        "policy_audit": str(request.policy_audit) if request.policy_audit else "",
        "profiles": str(request.profiles),
        "config_version": settings.config_version,
        "registry": {key: value.as_dict() for key, value in sorted(registry.items())},
        "rows": input_frame[
            [
                column
                for column in [
                    "signal_date",
                    "symbol",
                    "current_universe_name",
                    "instrument_type",
                    "suggested_instrument_type",
                    "resolved_instrument_type",
                    "current_profile_classification",
                ]
                if column in input_frame
            ]
        ].to_dict("records"),
    }
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def resolve_universe_profile_split_worklist_plan_paths(
    output_dir: str | Path,
    plan_id: str,
) -> UniverseProfileSplitWorklistPlanArtifactPaths:
    artifact_dir = Path(output_dir) / plan_id
    return UniverseProfileSplitWorklistPlanArtifactPaths(
        artifact_dir=artifact_dir,
        registry_snapshot=artifact_dir / "universe_profile_registry_snapshot.yaml",
        plan_csv=artifact_dir / "universe_profile_split_worklist_plan.csv",
        summary_csv=artifact_dir / "universe_profile_split_summary.csv",
        stock_core_guidance=artifact_dir / "universe_profile_split_guidance_stock_core.csv",
        etf_core_guidance=artifact_dir / "universe_profile_split_guidance_etf_core.csv",
        mixed_demo_core_guidance=artifact_dir / "universe_profile_split_guidance_mixed_demo_core.csv",
        report=artifact_dir / "universe_profile_split_worklist_plan_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def _load_policy_audit_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Universe profile policy audit CSV not found: {path}")
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    output = pd.DataFrame()
    output["signal_date"] = frame.get("signal_date", "")
    output["symbol"] = frame.get("symbol", "").map(normalize_symbol_value)
    output["current_universe_name"] = frame.get("universe_name", "").map(_text)
    output["instrument_type"] = frame.get("instrument_type", "").map(_instrument_type)
    output["suggested_instrument_type"] = frame.get("suggested_instrument_type", "").map(_instrument_type)
    output["resolved_instrument_type"] = frame.get("resolved_instrument_type", "").map(_instrument_type)
    output["current_profile_classification"] = frame.get("profile_policy_classification", "").map(_text)
    output["policy_issue"] = frame.get("policy_issue", "").map(_text)
    output["recommended_future_universe"] = frame.get("recommended_future_universe", "").map(_text)
    output["legacy_classification"] = frame.get("legacy_universe_classification", "").map(_text)
    output["source_policy_audit_id"] = _source_artifact_id(path)
    output["source_worklist_id"] = ""
    output["source_priority"] = 0
    return output


def _load_worklist_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"PIT universe evidence worklist CSV not found: {path}")
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    output = pd.DataFrame()
    output["signal_date"] = frame.get("signal_date", "").map(_text)
    output["symbol"] = frame.get("symbol", "").map(normalize_symbol_value)
    output["current_universe_name"] = frame.get("universe_name", "").map(_text)
    output["instrument_type"] = frame.get("instrument_type", "").map(_instrument_type) if "instrument_type" in frame else "UNKNOWN"
    output["suggested_instrument_type"] = frame.get("suggested_instrument_type", "").map(_instrument_type)
    output["resolved_instrument_type"] = output.apply(
        lambda row: _resolve_instrument_type(row.get("instrument_type"), row.get("suggested_instrument_type")),
        axis=1,
    )
    output["current_profile_classification"] = ""
    output["policy_issue"] = ""
    output["recommended_future_universe"] = ""
    output["legacy_classification"] = ""
    output["source_policy_audit_id"] = ""
    output["source_worklist_id"] = _source_artifact_id(path)
    output["source_priority"] = 1
    return output


def _merge_input_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    merged = pd.concat(frames, ignore_index=True, sort=False)
    for column in ["signal_date", "symbol", "current_universe_name"]:
        if column not in merged:
            merged[column] = ""
    merged["_identity"] = merged.apply(
        lambda row: "|".join(
            [
                _text(row.get("signal_date")),
                normalize_symbol_value(row.get("symbol")),
                _text(row.get("current_universe_name")),
            ]
        ),
        axis=1,
    )
    merged = merged.sort_values(["_identity", "source_priority"]).drop_duplicates("_identity", keep="first")
    return merged.drop(columns=["_identity", "source_priority"]).reset_index(drop=True)


def _enrich_worklist_with_policy_audit(worklist_frame: pd.DataFrame, policy_frame: pd.DataFrame) -> pd.DataFrame:
    worklist = worklist_frame.copy(deep=True)
    policy = policy_frame.copy(deep=True)
    if worklist.empty:
        return worklist
    if policy.empty:
        return worklist
    for frame in [worklist, policy]:
        frame["_join_symbol"] = frame["symbol"].map(normalize_symbol_value)
        frame["_join_universe"] = frame["current_universe_name"].map(_text)
    policy_columns = [
        "_join_symbol",
        "_join_universe",
        "source_policy_audit_id",
        "current_profile_classification",
        "policy_issue",
        "recommended_future_universe",
        "legacy_classification",
    ]
    policy_lookup = (
        policy.loc[:, [column for column in policy_columns if column in policy.columns]]
        .drop_duplicates(["_join_symbol", "_join_universe"], keep="first")
    )
    merged = worklist.merge(policy_lookup, on=["_join_symbol", "_join_universe"], how="left", suffixes=("", "_policy"))
    for column in [
        "source_policy_audit_id",
        "current_profile_classification",
        "policy_issue",
        "recommended_future_universe",
        "legacy_classification",
    ]:
        policy_column = f"{column}_policy"
        if policy_column in merged.columns:
            merged[column] = merged[policy_column].where(merged[policy_column].map(_text) != "", merged.get(column, ""))
            merged = merged.drop(columns=[policy_column])
    return merged.drop(columns=["_join_symbol", "_join_universe"]).reset_index(drop=True)


def _build_plan_frame(
    input_frame: pd.DataFrame,
    registry: dict[str, UniverseProfileDefinition],
    plan_id: str,
) -> pd.DataFrame:
    rows = []
    for _, input_row in input_frame.iterrows():
        row = input_row.to_dict()
        classification = classify_universe_profile_split_target(row, registry)
        resolved_type = classification["resolved_instrument_type"]
        rows.append(
            UniverseProfileSplitWorklistPlanRow(
                {
                    "plan_id": plan_id,
                    "source_worklist_id": _text(row.get("source_worklist_id")),
                    "source_policy_audit_id": _text(row.get("source_policy_audit_id")),
                    "signal_date": _text(row.get("signal_date")),
                    "current_universe_name": _text(row.get("current_universe_name")),
                    "symbol": normalize_symbol_value(row.get("symbol")),
                    "instrument_type": _instrument_type(row.get("instrument_type")),
                    "resolved_instrument_type": resolved_type,
                    "current_profile_classification": classification["current_profile_classification"],
                    "recommended_future_universe": classification["recommended_future_universe"],
                    "profile_rule_applied": classification["profile_rule_applied"],
                    "profile_conflict": classification["profile_conflict"],
                    "conflict_reason": classification["conflict_reason"],
                    "legacy_classification": classification["legacy_classification"],
                    "should_mutate_active_worklist": False,
                    "should_approve": False,
                    "should_reject": False,
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
                }
            ).as_dict()
        )
    return _finalize_frame(pd.DataFrame(rows), PLAN_COLUMNS)


def _build_summary_frame(
    plan_id: str,
    input_frame: pd.DataFrame,
    plan_frame: pd.DataFrame,
    counts: dict[str, int],
) -> pd.DataFrame:
    row = {column: "" for column in SUMMARY_COLUMNS}
    row.update(
        {
            "plan_id": plan_id,
            "source_worklist_id": _first_text(input_frame, "source_worklist_id"),
            "source_policy_audit_id": _first_text(input_frame, "source_policy_audit_id"),
            "row_count": len(plan_frame),
            "stock_row_count": counts["stock_row_count"],
            "etf_row_count": counts["etf_row_count"],
            "unknown_instrument_type_count": counts["unknown_instrument_type_count"],
            "legacy_mixed_demo_row_count": counts["legacy_mixed_demo_row_count"],
            "recommended_stock_core_count": counts["recommended_stock_core_count"],
            "recommended_etf_core_count": counts["recommended_etf_core_count"],
            "recommended_mixed_demo_core_count": counts["recommended_mixed_demo_core_count"],
            "profile_conflict_count": counts["profile_conflict_count"],
            "active_worklist_mutated": False,
            "next_manual_action": (
                "Review split guidance manually; leave active worklist unchanged until an explicit split workflow is approved."
            ),
        }
    )
    return pd.DataFrame([row], columns=SUMMARY_COLUMNS)


def _registry_frame(registry: dict[str, UniverseProfileDefinition]) -> pd.DataFrame:
    return pd.DataFrame([definition.as_dict() for _, definition in sorted(registry.items())], columns=REGISTRY_SNAPSHOT_COLUMNS)


def _counts(frame: pd.DataFrame) -> dict[str, int]:
    if frame.empty:
        return {
            "stock_row_count": 0,
            "etf_row_count": 0,
            "unknown_instrument_type_count": 0,
            "legacy_mixed_demo_row_count": 0,
            "recommended_stock_core_count": 0,
            "recommended_etf_core_count": 0,
            "recommended_mixed_demo_core_count": 0,
            "profile_conflict_count": 0,
        }
    return {
        "stock_row_count": int((frame["resolved_instrument_type"] == "STOCK").sum()),
        "etf_row_count": int((frame["resolved_instrument_type"] == "ETF").sum()),
        "unknown_instrument_type_count": int((frame["resolved_instrument_type"] == "UNKNOWN").sum()),
        "legacy_mixed_demo_row_count": int((frame["legacy_classification"] == "legacy_mixed_demo_universe").sum()),
        "recommended_stock_core_count": int((frame["recommended_future_universe"] == "stock_core").sum()),
        "recommended_etf_core_count": int((frame["recommended_future_universe"] == "etf_core").sum()),
        "recommended_mixed_demo_core_count": int((frame["recommended_future_universe"] == "mixed_demo_core").sum()),
        "profile_conflict_count": int(frame["profile_conflict"].map(_to_bool).sum()),
    }


def _audit_metadata(
    request: UniverseProfileSplitWorklistPlanRequest,
    settings: UniverseProfileSplitWorklistPlanSettings,
) -> dict[str, Any]:
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
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "no_network_api": True,
        "no_llm_api": True,
        "no_cache_mutation": True,
        "plan_only": True,
    }


def _assert_settings_safe(settings: UniverseProfileSplitWorklistPlanSettings) -> None:
    unsafe_flags = {
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
    enabled = [name for name, value in unsafe_flags.items() if value]
    if enabled:
        raise ValueError(f"Universe profile split-worklist plan is report-only; unsafe flags enabled: {', '.join(enabled)}")


def _warnings(counts: dict[str, int]) -> list[str]:
    warnings: list[str] = []
    if counts["legacy_mixed_demo_row_count"]:
        warnings.append("Legacy mixed etf_core rows remain active-workflow context and were not mutated.")
    if counts["profile_conflict_count"]:
        warnings.append("Rows conflict with future profile rules and should be reviewed before split worklists are generated.")
    return warnings


def _recommended_future_universe(
    resolved_instrument_type: str,
    current_classification: str,
    current_universe_name: str,
) -> str:
    if resolved_instrument_type == "STOCK":
        return "stock_core"
    if resolved_instrument_type == "ETF":
        return "etf_core"
    if current_universe_name.strip().lower() == "mixed_demo_core" or current_classification == "mixed_demo_universe":
        return "mixed_demo_core"
    return "unknown"


def _guidance_frame(frame: pd.DataFrame, profile_name: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PLAN_COLUMNS)
    return frame.loc[frame["recommended_future_universe"] == profile_name, PLAN_COLUMNS].reset_index(drop=True)


def _registry_yaml(registry: dict[str, UniverseProfileDefinition]) -> str:
    payload = {
        "profiles": {
            name: {
                "allowed_instrument_types": list(definition.allowed_instrument_types),
                "profile_type": definition.profile_type,
                "mixed_allowed": definition.mixed_allowed,
                "demo_only": definition.demo_only,
                "description": definition.description,
            }
            for name, definition in sorted(registry.items())
        }
    }
    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=True)


def _resolve_instrument_type(instrument_type: Any, suggested_instrument_type: Any) -> str:
    explicit = _instrument_type(instrument_type)
    if explicit != "UNKNOWN":
        return explicit
    suggested = _instrument_type(suggested_instrument_type)
    return suggested if suggested != "UNKNOWN" else "UNKNOWN"


def _instrument_type(value: Any) -> str:
    text = _text(value).upper()
    if text in {"STOCK", "ETF"}:
        return text
    return "UNKNOWN" if not text else text


def _source_artifact_id(path: Path) -> str:
    parent = path.parent.name
    if parent and parent not in {".", ""}:
        return parent
    return path.stem


def _first_text(frame: pd.DataFrame, column: str) -> str:
    if column not in frame:
        return ""
    for value in frame[column].tolist():
        text = _text(value)
        if text:
            return text
    return ""


def _finalize_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=columns)
    output = frame.copy()
    for column in columns:
        if column not in output.columns:
            output[column] = ""
    return output[columns].reset_index(drop=True)


def _markdown_table(frame: pd.DataFrame, columns: list[str], *, max_rows: int = 60) -> str:
    if frame.empty:
        return "_No rows._"
    visible = frame.loc[:, [column for column in columns if column in frame.columns]].head(max_rows)
    lines = [
        "| " + " | ".join(visible.columns) + " |",
        "| " + " | ".join("---" for _ in visible.columns) + " |",
    ]
    for _, row in visible.iterrows():
        lines.append("| " + " | ".join(_markdown_escape(row[column]) for column in visible.columns) + " |")
    if len(frame) > max_rows:
        lines.append(f"| ... | showing first {max_rows} of {len(frame)} rows |")
    return "\n".join(lines)


def _markdown_escape(value: Any) -> str:
    return _text(value).replace("|", "\\|").replace("\n", " ")


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "nat", "none", "null"} else text


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value
