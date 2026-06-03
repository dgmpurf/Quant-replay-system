"""Report-only universe profile policy audit workflow.

This module classifies local universe artifacts by instrument mix and universe
profile naming. It writes governance/audit artifacts only; it does not approve
or reject rows, export universe files, run current-candidates, build snapshots,
compute labels, mutate cache, or perform trading workflows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


AUDIT_OUTPUT_COLUMNS = [
    "audit_id",
    "source_artifact_type",
    "source_artifact_id",
    "universe_name",
    "symbol",
    "instrument_type",
    "suggested_instrument_type",
    "resolved_instrument_type",
    "profile_policy_classification",
    "policy_issue",
    "recommended_future_universe",
    "legacy_universe_classification",
    "should_approve",
    "should_reject",
    "review_status_recommendation",
    "review_reason_recommendation",
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
    "audit_only",
]

SUMMARY_COLUMNS = [
    "audit_id",
    "universe_name",
    "profile_policy_classification",
    "policy_issue",
    "row_count",
    "symbol_count",
    "stock_row_count",
    "etf_row_count",
    "unknown_row_count",
    "recommended_stock_core_count",
    "recommended_etf_core_count",
    "recommended_mixed_demo_core_count",
    "legacy_universe_classification",
]

SPLIT_GUIDANCE_COLUMNS = [
    "audit_id",
    "universe_name",
    "resolved_instrument_type",
    "recommended_future_universe",
    "row_count",
    "symbol_count",
    "symbols",
    "guidance",
]

SAFETY_STATEMENT = (
    "No approval, rejection, universe export, data/raw write, data/processed write, "
    "current-candidates generation, snapshot build, forward labels, live trading, broker API, "
    "order placement, message delivery, network/API, LLM/API, or cache mutation was invoked."
)

PROFILE_CLASSIFICATIONS = {
    "legacy_mixed_demo_universe",
    "etf_only_universe",
    "stock_only_universe",
    "mixed_demo_universe",
    "unknown_universe_profile",
}


@dataclass(frozen=True)
class UniverseProfilePolicyAuditSettings:
    output_dir: Path = Path("outputs/reports/universe_profile_policy_audit")
    config_version: str = "v0.1"
    write_artifacts: bool = True
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
class UniverseProfilePolicyAuditRequest:
    worklist: Path | None = None
    review: Path | None = None


@dataclass(frozen=True)
class UniverseProfilePolicyAuditRow:
    values: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {column: self.values.get(column, "") for column in AUDIT_OUTPUT_COLUMNS}


@dataclass(frozen=True)
class UniverseProfilePolicyAuditArtifactPaths:
    artifact_dir: Path
    audit_csv: Path
    summary_csv: Path
    split_guidance_csv: Path
    report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "audit_csv": self.audit_csv,
            "summary_csv": self.summary_csv,
            "split_guidance_csv": self.split_guidance_csv,
            "report": self.report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class UniverseProfilePolicyAuditResult:
    audit_id: str
    status: str
    request: UniverseProfilePolicyAuditRequest
    row_count: int
    universe_count: int
    mixed_universe_count: int
    ambiguous_policy_count: int
    stock_row_count: int
    etf_row_count: int
    recommended_stock_core_count: int
    recommended_etf_core_count: int
    recommended_mixed_demo_core_count: int
    audit_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    split_guidance_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def load_universe_profile_policy_input(
    *,
    worklist: str | Path | None = None,
    review: str | Path | None = None,
) -> pd.DataFrame:
    """Load one or more local universe artifacts while preserving symbols."""

    frames: list[pd.DataFrame] = []
    if worklist is not None:
        frames.append(_load_source_frame(Path(worklist), "worklist"))
    if review is not None:
        frames.append(_load_source_frame(Path(review), "review"))
    if not frames:
        raise ValueError("At least one of worklist or review must be provided.")
    return _dedupe_policy_input(pd.concat(frames, ignore_index=True, sort=False))


def classify_universe_profile_policy(universe_name: str, instrument_types: set[str]) -> tuple[str, str, str]:
    """Classify a universe name by its observed instrument mix."""

    resolved = {value for value in instrument_types if value and value != "UNKNOWN"}
    normalized_universe = universe_name.strip().lower()
    if normalized_universe == "etf_core" and {"STOCK", "ETF"}.issubset(resolved):
        return (
            "legacy_mixed_demo_universe",
            "POLICY_AMBIGUOUS_DEMO_MIXED_UNIVERSE",
            "legacy_mixed_demo_universe",
        )
    if normalized_universe == "mixed_demo_core" or {"STOCK", "ETF"}.issubset(resolved):
        return ("mixed_demo_universe", "MIXED_DEMO_CORE_RECOMMENDED", "")
    if resolved == {"ETF"}:
        return ("etf_only_universe", "", "")
    if resolved == {"STOCK"}:
        return ("stock_only_universe", "", "")
    return ("unknown_universe_profile", "UNKNOWN_OR_MISSING_INSTRUMENT_TYPE", "")


def build_universe_profile_policy_audit(
    *,
    worklist: str | Path | None = None,
    review: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: UniverseProfilePolicyAuditSettings | None = None,
) -> UniverseProfilePolicyAuditResult:
    """Build report-only universe profile policy audit artifacts."""

    resolved_settings = settings or UniverseProfilePolicyAuditSettings()
    if output_dir is not None:
        resolved_settings = UniverseProfilePolicyAuditSettings(
            output_dir=Path(output_dir),
            config_version=resolved_settings.config_version,
            write_artifacts=resolved_settings.write_artifacts,
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

    request = UniverseProfilePolicyAuditRequest(
        worklist=Path(worklist) if worklist is not None else None,
        review=Path(review) if review is not None else None,
    )
    input_frame = load_universe_profile_policy_input(worklist=request.worklist, review=request.review)
    audit_id = generate_universe_profile_policy_audit_id(request, input_frame, resolved_settings)
    audit_frame = _build_audit_frame(input_frame, audit_id)
    summary_frame = _build_summary_frame(audit_frame, audit_id)
    split_guidance_frame = _build_split_guidance_frame(audit_frame, audit_id)
    counts = _build_counts(audit_frame)
    paths = resolve_universe_profile_policy_audit_paths(resolved_settings.output_dir, audit_id)
    result = UniverseProfilePolicyAuditResult(
        audit_id=audit_id,
        status="WARN" if counts["ambiguous_policy_count"] else "PASS",
        request=request,
        row_count=len(audit_frame),
        universe_count=int(audit_frame["universe_name"].nunique()) if not audit_frame.empty else 0,
        mixed_universe_count=counts["mixed_universe_count"],
        ambiguous_policy_count=counts["ambiguous_policy_count"],
        stock_row_count=counts["stock_row_count"],
        etf_row_count=counts["etf_row_count"],
        recommended_stock_core_count=counts["recommended_stock_core_count"],
        recommended_etf_core_count=counts["recommended_etf_core_count"],
        recommended_mixed_demo_core_count=counts["recommended_mixed_demo_core_count"],
        audit_frame=audit_frame,
        summary_frame=summary_frame,
        split_guidance_frame=split_guidance_frame,
        warnings=_build_warnings(counts),
        artifact_paths=paths.as_dict(),
        audit_metadata=_audit_metadata(request, resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_universe_profile_policy_audit_artifacts(result)
    return result


def render_universe_profile_policy_audit_report(result: UniverseProfilePolicyAuditResult) -> str:
    """Render a human-readable universe profile policy audit report."""

    lines = [
        f"# Universe Profile Policy Audit: {result.audit_id}",
        "",
        SAFETY_STATEMENT,
        "This is a governance/report-only artifact. It does not mutate active worklists or classify rows as approved/rejected.",
        "",
        "## Summary",
        "",
        _dict_table(_summary_dict(result)),
        "",
        "## Universe Summary",
        "",
        _markdown_table(result.summary_frame, SUMMARY_COLUMNS),
        "",
        "## Future Split Guidance",
        "",
        _markdown_table(result.split_guidance_frame, SPLIT_GUIDANCE_COLUMNS),
        "",
        "## Audit Rows",
        "",
        _markdown_table(result.audit_frame, AUDIT_OUTPUT_COLUMNS),
        "",
        "## Warnings",
        "",
        "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
        "",
        "## Recommended Next Action",
        "",
        (
            "Leave existing mixed `etf_core` artifacts as legacy audit context; generate future worklists with "
            "`stock_core`, `etf_core`, or `mixed_demo_core` according to explicit instrument-type policy."
        ),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def write_universe_profile_policy_audit_artifacts(result: UniverseProfilePolicyAuditResult) -> dict[str, Path]:
    """Write audit CSVs, metadata, and report under outputs/reports."""

    paths = UniverseProfilePolicyAuditArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.audit_frame.to_csv(paths.audit_csv, index=False)
    result.summary_frame.to_csv(paths.summary_csv, index=False)
    result.split_guidance_frame.to_csv(paths.split_guidance_csv, index=False)
    paths.metadata.write_text(
        json.dumps(_json_safe(build_universe_profile_policy_audit_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    paths.report.write_text(render_universe_profile_policy_audit_report(result), encoding="utf-8")
    return paths.as_dict()


def build_universe_profile_policy_audit_metadata(result: UniverseProfilePolicyAuditResult) -> dict[str, Any]:
    """Build metadata for a universe profile policy audit run."""

    return {
        "audit_id": result.audit_id,
        "status": result.status,
        "created_at": "2024-05-29T00:00:00",
        "worklist": str(result.request.worklist) if result.request.worklist else "",
        "review": str(result.request.review) if result.request.review else "",
        "row_count": result.row_count,
        "universe_count": result.universe_count,
        "mixed_universe_count": result.mixed_universe_count,
        "ambiguous_policy_count": result.ambiguous_policy_count,
        "stock_row_count": result.stock_row_count,
        "etf_row_count": result.etf_row_count,
        "recommended_stock_core_count": result.recommended_stock_core_count,
        "recommended_etf_core_count": result.recommended_etf_core_count,
        "recommended_mixed_demo_core_count": result.recommended_mixed_demo_core_count,
        "warnings": result.warnings,
        "safety_statement": SAFETY_STATEMENT,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
        **result.audit_metadata,
        "known_limitations": [
            "This workflow reports naming/profile policy only and does not approve or reject rows.",
            "Legacy mixed etf_core artifacts remain visible as audit context.",
            "The audit does not validate PIT evidence, strategy performance, or trading readiness.",
        ],
    }


def generate_universe_profile_policy_audit_id(
    request: UniverseProfilePolicyAuditRequest,
    input_frame: pd.DataFrame,
    settings: UniverseProfilePolicyAuditSettings,
) -> str:
    payload = {
        "worklist": str(request.worklist) if request.worklist else "",
        "review": str(request.review) if request.review else "",
        "config_version": settings.config_version,
        "rows": input_frame[
            [
                column
                for column in [
                    "source_artifact_type",
                    "source_artifact_id",
                    "universe_name",
                    "symbol",
                    "instrument_type",
                    "suggested_instrument_type",
                ]
                if column in input_frame
            ]
        ].to_dict("records"),
    }
    digest = hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]


def resolve_universe_profile_policy_audit_paths(
    output_dir: str | Path,
    audit_id: str,
) -> UniverseProfilePolicyAuditArtifactPaths:
    artifact_dir = Path(output_dir) / audit_id
    return UniverseProfilePolicyAuditArtifactPaths(
        artifact_dir=artifact_dir,
        audit_csv=artifact_dir / "universe_profile_policy_audit.csv",
        summary_csv=artifact_dir / "universe_profile_policy_summary.csv",
        split_guidance_csv=artifact_dir / "universe_profile_policy_split_guidance.csv",
        report=artifact_dir / "universe_profile_policy_audit_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def _load_source_frame(path: Path, source_artifact_type: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Universe profile policy source not found: {path}")
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    output = frame.copy(deep=True)
    for column in ["symbol", "universe_name"]:
        if column not in output.columns:
            output[column] = ""
    if "signal_date" not in output.columns:
        output["signal_date"] = ""
    if "instrument_type" not in output.columns:
        output["instrument_type"] = ""
    if "suggested_instrument_type" not in output.columns:
        output["suggested_instrument_type"] = ""
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    output["universe_name"] = output["universe_name"].map(_text)
    output["instrument_type"] = output["instrument_type"].map(_instrument_type)
    output["suggested_instrument_type"] = output["suggested_instrument_type"].map(_instrument_type)
    output["source_artifact_type"] = source_artifact_type
    output["source_artifact_id"] = _source_artifact_id(path)
    return output


def _dedupe_policy_input(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    output = frame.copy(deep=True)
    for column in ["signal_date", "symbol", "universe_name"]:
        if column not in output.columns:
            output[column] = ""
    priority = {"worklist": 0, "review": 1}
    output["_source_priority"] = output["source_artifact_type"].map(lambda value: priority.get(str(value), 9))
    output["_identity"] = output.apply(
        lambda row: "|".join(
            [
                _text(row.get("signal_date")),
                normalize_symbol_value(row.get("symbol")),
                _text(row.get("universe_name")),
            ]
        ),
        axis=1,
    )
    output = output.sort_values(["_identity", "_source_priority"]).drop_duplicates("_identity", keep="first")
    return output.drop(columns=["_source_priority", "_identity"]).reset_index(drop=True)


def _build_audit_frame(input_frame: pd.DataFrame, audit_id: str) -> pd.DataFrame:
    output = input_frame.copy(deep=True)
    output["resolved_instrument_type"] = output.apply(
        lambda row: _resolve_instrument_type(row.get("instrument_type"), row.get("suggested_instrument_type")),
        axis=1,
    )
    classifications: dict[str, tuple[str, str, str]] = {}
    for universe_name, group in output.groupby("universe_name", dropna=False):
        classifications[str(universe_name)] = classify_universe_profile_policy(
            str(universe_name),
            set(group["resolved_instrument_type"].astype(str)),
        )
    rows = []
    for _, row in output.iterrows():
        universe_name = _text(row.get("universe_name"))
        classification, policy_issue, legacy_classification = classifications.get(
            universe_name,
            ("unknown_universe_profile", "UNKNOWN_OR_MISSING_INSTRUMENT_TYPE", ""),
        )
        resolved_instrument_type = _instrument_type(row.get("resolved_instrument_type"))
        recommended_future_universe = _recommended_future_universe(
            universe_name,
            resolved_instrument_type,
            classification,
        )
        rows.append(
            UniverseProfilePolicyAuditRow(
                {
                    "audit_id": audit_id,
                    "source_artifact_type": _text(row.get("source_artifact_type")),
                    "source_artifact_id": _text(row.get("source_artifact_id")),
                    "universe_name": universe_name,
                    "symbol": normalize_symbol_value(row.get("symbol")),
                    "instrument_type": _instrument_type(row.get("instrument_type")),
                    "suggested_instrument_type": _instrument_type(row.get("suggested_instrument_type")),
                    "resolved_instrument_type": resolved_instrument_type,
                    "profile_policy_classification": classification,
                    "policy_issue": policy_issue,
                    "recommended_future_universe": recommended_future_universe,
                    "legacy_universe_classification": legacy_classification,
                    "should_approve": False,
                    "should_reject": False,
                    "review_status_recommendation": "NO_AUTOMATIC_REVIEW_STATUS_CHANGE",
                    "review_reason_recommendation": _review_reason_recommendation(
                        universe_name,
                        resolved_instrument_type,
                        classification,
                        policy_issue,
                    ),
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
                    "audit_only": True,
                }
            ).as_dict()
        )
    return pd.DataFrame(rows, columns=AUDIT_OUTPUT_COLUMNS)


def _build_summary_frame(audit_frame: pd.DataFrame, audit_id: str) -> pd.DataFrame:
    rows = []
    for universe_name, group in audit_frame.groupby("universe_name", dropna=False):
        row_count = len(group)
        rows.append(
            {
                "audit_id": audit_id,
                "universe_name": universe_name,
                "profile_policy_classification": _first_text(group, "profile_policy_classification"),
                "policy_issue": _first_text(group, "policy_issue"),
                "row_count": row_count,
                "symbol_count": int(group["symbol"].nunique()),
                "stock_row_count": int((group["resolved_instrument_type"] == "STOCK").sum()),
                "etf_row_count": int((group["resolved_instrument_type"] == "ETF").sum()),
                "unknown_row_count": int((group["resolved_instrument_type"] == "UNKNOWN").sum()),
                "recommended_stock_core_count": int((group["recommended_future_universe"] == "stock_core").sum()),
                "recommended_etf_core_count": int((group["recommended_future_universe"] == "etf_core").sum()),
                "recommended_mixed_demo_core_count": int((group["recommended_future_universe"] == "mixed_demo_core").sum()),
                "legacy_universe_classification": _first_text(group, "legacy_universe_classification"),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def _build_split_guidance_frame(audit_frame: pd.DataFrame, audit_id: str) -> pd.DataFrame:
    if audit_frame.empty:
        return pd.DataFrame(columns=SPLIT_GUIDANCE_COLUMNS)
    rows = []
    for (universe_name, resolved_type, recommended), group in audit_frame.groupby(
        ["universe_name", "resolved_instrument_type", "recommended_future_universe"],
        dropna=False,
    ):
        symbols = sorted({normalize_symbol_value(value) for value in group["symbol"].tolist() if _text(value)})
        rows.append(
            {
                "audit_id": audit_id,
                "universe_name": universe_name,
                "resolved_instrument_type": resolved_type,
                "recommended_future_universe": recommended,
                "row_count": len(group),
                "symbol_count": len(symbols),
                "symbols": ",".join(symbols),
                "guidance": _split_guidance_text(resolved_type, recommended),
            }
        )
    return pd.DataFrame(rows, columns=SPLIT_GUIDANCE_COLUMNS)


def _build_counts(audit_frame: pd.DataFrame) -> dict[str, int]:
    if audit_frame.empty:
        return {
            "mixed_universe_count": 0,
            "ambiguous_policy_count": 0,
            "stock_row_count": 0,
            "etf_row_count": 0,
            "recommended_stock_core_count": 0,
            "recommended_etf_core_count": 0,
            "recommended_mixed_demo_core_count": 0,
        }
    universe_classifications = audit_frame[["universe_name", "profile_policy_classification"]].drop_duplicates()
    return {
        "mixed_universe_count": int(
            universe_classifications["profile_policy_classification"].isin(
                ["legacy_mixed_demo_universe", "mixed_demo_universe"]
            ).sum()
        ),
        "ambiguous_policy_count": int((audit_frame["policy_issue"] == "POLICY_AMBIGUOUS_DEMO_MIXED_UNIVERSE").sum()),
        "stock_row_count": int((audit_frame["resolved_instrument_type"] == "STOCK").sum()),
        "etf_row_count": int((audit_frame["resolved_instrument_type"] == "ETF").sum()),
        "recommended_stock_core_count": int((audit_frame["recommended_future_universe"] == "stock_core").sum()),
        "recommended_etf_core_count": int((audit_frame["recommended_future_universe"] == "etf_core").sum()),
        "recommended_mixed_demo_core_count": int((audit_frame["recommended_future_universe"] == "mixed_demo_core").sum()),
    }


def _audit_metadata(
    request: UniverseProfilePolicyAuditRequest,
    settings: UniverseProfilePolicyAuditSettings,
) -> dict[str, Any]:
    return {
        "config_version": settings.config_version,
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
        "audit_only": True,
    }


def _assert_settings_safe(settings: UniverseProfilePolicyAuditSettings) -> None:
    unsafe_flags = {
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
        raise ValueError(f"Universe profile policy audit is report-only; unsafe flags enabled: {', '.join(enabled)}")


def _recommended_future_universe(
    universe_name: str,
    resolved_instrument_type: str,
    classification: str,
) -> str:
    if resolved_instrument_type == "STOCK":
        return "stock_core"
    if resolved_instrument_type == "ETF":
        return "etf_core"
    if universe_name.strip().lower() == "mixed_demo_core":
        return "mixed_demo_core"
    return "unknown"


def _review_reason_recommendation(
    universe_name: str,
    resolved_instrument_type: str,
    classification: str,
    policy_issue: str,
) -> str:
    if policy_issue == "POLICY_AMBIGUOUS_DEMO_MIXED_UNIVERSE":
        return (
            f"{universe_name} contains mixed STOCK/ETF rows and should be treated as legacy mixed demo context; "
            "do not approve or reject automatically."
        )
    if classification == "etf_only_universe" and resolved_instrument_type != "ETF":
        return "Future ETF-only profiles should block non-ETF rows before approval/export."
    if classification == "stock_only_universe" and resolved_instrument_type != "STOCK":
        return "Future stock-only profiles should block non-STOCK rows before approval/export."
    return "No automatic review status change; use this row only as universe profile policy context."


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


def _build_warnings(counts: dict[str, int]) -> list[str]:
    warnings: list[str] = []
    if counts["ambiguous_policy_count"]:
        warnings.append(
            "Mixed STOCK/ETF rows were found under a legacy etf_core label; treat as demo/mixed policy context only."
        )
    if counts["mixed_universe_count"]:
        warnings.append("Future worklists should use stock_core, etf_core, or mixed_demo_core explicitly.")
    return warnings


def _summary_dict(result: UniverseProfilePolicyAuditResult) -> dict[str, Any]:
    return {
        "audit_id": result.audit_id,
        "status": result.status,
        "row_count": result.row_count,
        "universe_count": result.universe_count,
        "mixed_universe_count": result.mixed_universe_count,
        "ambiguous_policy_count": result.ambiguous_policy_count,
        "stock_row_count": result.stock_row_count,
        "etf_row_count": result.etf_row_count,
        "recommended_stock_core_count": result.recommended_stock_core_count,
        "recommended_etf_core_count": result.recommended_etf_core_count,
        "recommended_mixed_demo_core_count": result.recommended_mixed_demo_core_count,
        "audit_csv": result.artifact_paths.get("audit_csv", ""),
        "report": result.artifact_paths.get("report", ""),
    }


def _split_guidance_text(resolved_type: str, recommended: str) -> str:
    if recommended == "stock_core":
        return "Use stock_core for reviewed stock-only PIT worklists."
    if recommended == "etf_core":
        return "Use etf_core for reviewed ETF-only PIT worklists."
    if recommended == "mixed_demo_core":
        return "Use mixed_demo_core for demo/mixed workflows; do not treat as non-demo approval."
    return f"Resolve instrument type {resolved_type} before future profile assignment."


def _first_text(frame: pd.DataFrame, column: str) -> str:
    values = [_text(value) for value in frame[column].tolist() if _text(value)]
    return values[0] if values else ""


def _dict_table(values: dict[str, Any]) -> str:
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        lines.append(f"| {key} | {_markdown_escape(value)} |")
    return "\n".join(lines)


def _markdown_table(frame: pd.DataFrame, columns: list[str], *, max_rows: int = 40) -> str:
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
        lines.append(f"| ... | {len(frame) - max_rows} additional rows omitted |")
    return "\n".join(lines)


def _markdown_escape(value: Any) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


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


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()
