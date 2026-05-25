"""Policy-aware planning for reviewed market cache exports."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketCacheExportPolicySettings, Settings, load_settings
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.market_data_cache import load_market_cache
from quant_replay_system.market_source_policy import (
    MarketFieldReliability,
    get_market_source_policy,
    infer_market_security_type,
)


MARKET_CACHE_EXPORT_POLICY_TIMESTAMP = "1970-01-01T00:00:00+00:00"

POLICY_EXPORT_REQUEST_REQUIRED_COLUMNS = [
    "symbol",
    "start_date",
    "end_date",
    "required_fields",
    "enabled",
]

POLICY_EXPORT_RECOMMENDATION_COLUMNS = [
    "manifest_row",
    "symbol",
    "start_date",
    "end_date",
    "security_type",
    "required_fields",
    "status",
    "recommended_source",
    "recommended_upstream_source",
    "row_count",
    "min_trade_date",
    "max_trade_date",
    "candidate_count",
    "policy_statuses",
    "warnings",
    "reason",
    "notes",
    "no_live_trading",
    "no_broker_api",
]

POLICY_EXPORT_ISSUE_COLUMNS = [
    "category",
    "severity",
    "manifest_row",
    "symbol",
    "source",
    "upstream_source",
    "message",
    "suggested_action",
    "no_live_trading",
    "no_broker_api",
]

RECOMMENDED_MANIFEST_COLUMNS = [
    "symbol",
    "start_date",
    "end_date",
    "source",
    "upstream_source",
    "enabled",
    "security_type",
    "require_fields",
    "notes",
]

ACCEPTABLE_POLICY_STATUSES = {"RECOMMENDED", "RECOMMENDED_WITH_WARNINGS"}

POLICY_SCORE_RANK = {
    MarketFieldReliability.RELIABLE: 4,
    MarketFieldReliability.CAVEAT_FIRST_WINDOW_ROW: 3,
    MarketFieldReliability.PROVISIONAL: 2,
    MarketFieldReliability.UNKNOWN: 1,
    MarketFieldReliability.UNSTABLE: 0,
    MarketFieldReliability.UNAVAILABLE: 0,
    MarketFieldReliability.DO_NOT_USE: 0,
}

MARKET_CACHE_EXPORT_POLICY_LIMITATIONS = [
    "The policy-aware export planner only recommends reviewed source/upstream selections.",
    "It does not run market-cache-export automatically by default.",
    "It never mutates the market cache.",
    "PROVISIONAL recommendations remain warnings and require human review.",
    "Generated reviewed manifests must still pass market-cache-export, data-pipeline, data-quality, and snapshot-quality.",
    "No broker API, live trading, order automation, scheduler, or real network call is invoked.",
]


@dataclass(frozen=True)
class MarketCacheExportPolicyRequest:
    manifest_row: int
    symbol: str
    start_date: str
    end_date: str
    required_fields: list[str]
    enabled: bool
    security_type: str = ""
    preferred_source: str = ""
    preferred_upstream_source: str = ""
    reference_source: str = ""
    notes: str = ""


@dataclass(frozen=True)
class MarketCacheSourceCandidate:
    symbol: str
    source: str
    upstream_source: str
    row_count: int
    min_trade_date: str
    max_trade_date: str


@dataclass(frozen=True)
class MarketCacheExportPolicyRecommendation:
    manifest_row: int
    symbol: str
    start_date: str
    end_date: str
    security_type: str
    required_fields: list[str]
    status: str
    recommended_source: str = ""
    recommended_upstream_source: str = ""
    row_count: int = 0
    min_trade_date: str = ""
    max_trade_date: str = ""
    candidate_count: int = 0
    policy_statuses: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    reason: str = ""
    notes: str = ""

    def as_row(self) -> dict[str, Any]:
        return {
            "manifest_row": self.manifest_row,
            "symbol": self.symbol,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "security_type": self.security_type,
            "required_fields": ",".join(self.required_fields),
            "status": self.status,
            "recommended_source": self.recommended_source,
            "recommended_upstream_source": self.recommended_upstream_source,
            "row_count": int(self.row_count),
            "min_trade_date": self.min_trade_date,
            "max_trade_date": self.max_trade_date,
            "candidate_count": int(self.candidate_count),
            "policy_statuses": json.dumps(self.policy_statuses, sort_keys=True),
            "warnings": " | ".join(self.warnings),
            "reason": self.reason,
            "notes": self.notes,
            "no_live_trading": True,
            "no_broker_api": True,
        }

    def as_reviewed_manifest_row(self) -> dict[str, Any]:
        enabled = self.status in ACCEPTABLE_POLICY_STATUSES
        notes = self.notes
        if self.warnings:
            notes = f"{notes} | {' | '.join(self.warnings)}" if notes else " | ".join(self.warnings)
        if self.reason:
            notes = f"{notes} | {self.reason}" if notes else self.reason
        return {
            "symbol": self.symbol,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "source": self.recommended_source if enabled else "",
            "upstream_source": self.recommended_upstream_source if enabled else "",
            "enabled": bool(enabled),
            "security_type": self.security_type,
            "require_fields": ",".join(self.required_fields),
            "notes": notes,
        }


@dataclass(frozen=True)
class MarketCacheExportPolicyIssue:
    category: str
    severity: str
    message: str
    manifest_row: int | str = ""
    symbol: str = ""
    source: str = ""
    upstream_source: str = ""
    suggested_action: str = ""
    no_live_trading: bool = True
    no_broker_api: bool = True

    def as_row(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "manifest_row": self.manifest_row,
            "symbol": self.symbol,
            "source": self.source,
            "upstream_source": self.upstream_source,
            "message": self.message,
            "suggested_action": self.suggested_action,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
        }


@dataclass(frozen=True)
class MarketCacheExportPolicyArtifactPaths:
    artifact_dir: Path
    market_cache_export_policy_report: Path
    market_cache_export_policy_recommendations: Path
    market_cache_export_policy_issues: Path
    metadata: Path
    recommended_manifest: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_cache_export_policy_report": self.market_cache_export_policy_report,
            "market_cache_export_policy_recommendations": self.market_cache_export_policy_recommendations,
            "market_cache_export_policy_issues": self.market_cache_export_policy_issues,
            "metadata": self.metadata,
            "recommended_manifest": self.recommended_manifest,
        }


@dataclass(frozen=True)
class MarketCacheExportPolicyResult:
    plan_id: str
    status: str
    manifest_path: Path
    request_rows: list[MarketCacheExportPolicyRequest]
    recommendations_frame: pd.DataFrame
    issues_frame: pd.DataFrame
    recommended_manifest_frame: pd.DataFrame
    recommended_manifest_path: Path
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def recommendation_count(self) -> int:
        return int(self.recommendations_frame["status"].isin(ACCEPTABLE_POLICY_STATUSES).sum()) if not self.recommendations_frame.empty else 0

    @property
    def issue_count(self) -> int:
        return len(self.issues_frame)


def load_policy_export_request(
    path: str | Path,
    *,
    settings: MarketCacheExportPolicySettings | None = None,
) -> list[MarketCacheExportPolicyRequest]:
    """Load a policy-aware cache export request manifest while preserving symbols."""

    policy_settings = settings or load_settings(Path("config/default.yaml")).market_cache_export_policy
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Market cache export policy request manifest not found: {manifest_path}")
    frame = read_csv_preserve_symbol_columns(manifest_path, keep_default_na=False)
    missing = [column for column in POLICY_EXPORT_REQUEST_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Market cache export policy request manifest missing columns: {', '.join(missing)}")

    rows: list[MarketCacheExportPolicyRequest] = []
    for index, raw_row in frame.iterrows():
        symbol = normalize_symbol_value(raw_row.get("symbol"))
        security_type = _normalize_key(raw_row.get("security_type"))
        if not security_type:
            security_type = infer_market_security_type(symbol)
        rows.append(
            MarketCacheExportPolicyRequest(
                manifest_row=int(index) + 2,
                symbol=symbol,
                start_date=_string_or_empty(raw_row.get("start_date")),
                end_date=_string_or_empty(raw_row.get("end_date")),
                required_fields=_normalize_required_fields(raw_row.get("required_fields"), policy_settings),
                enabled=_coerce_bool(raw_row.get("enabled")),
                security_type=security_type,
                preferred_source=_normalize_key(raw_row.get("preferred_source")),
                preferred_upstream_source=_normalize_key(raw_row.get("preferred_upstream_source")),
                reference_source=_normalize_key(raw_row.get("reference_source")),
                notes=_string_or_empty(raw_row.get("notes")),
            )
        )
    return rows


def find_available_cache_sources_for_symbol(
    request: MarketCacheExportPolicyRequest,
    *,
    cache_path: str | Path | None = None,
    config: Settings | dict[str, Any] | None = None,
) -> list[MarketCacheSourceCandidate]:
    """Return source/upstream combinations with cached rows for one request row."""

    project_settings = _resolve_project_settings(config)
    frame = load_market_cache(cache_path, config=project_settings)
    if frame.empty:
        return []
    start = pd.to_datetime(request.start_date, errors="raise").normalize() if request.start_date else None
    end = pd.to_datetime(request.end_date, errors="raise").normalize() if request.end_date else None
    dates = pd.to_datetime(frame["trade_date"], errors="coerce")
    mask = frame["symbol"].astype(str).map(normalize_symbol_value).eq(request.symbol)
    if start is not None:
        mask &= dates >= start
    if end is not None:
        mask &= dates <= end
    selected = frame.loc[mask].copy()
    if selected.empty:
        return []
    selected["source"] = selected["source"].astype(str).str.strip().str.upper()
    selected["upstream_source"] = selected["upstream_source"].fillna("").astype(str).str.strip().str.upper()
    selected = selected.loc[selected["source"].ne("") & selected["upstream_source"].ne("")]
    candidates: list[MarketCacheSourceCandidate] = []
    for (source, upstream_source), group in selected.groupby(["source", "upstream_source"], dropna=False):
        candidates.append(
            MarketCacheSourceCandidate(
                symbol=request.symbol,
                source=str(source),
                upstream_source=str(upstream_source),
                row_count=int(len(group)),
                min_trade_date=str(group["trade_date"].min()),
                max_trade_date=str(group["trade_date"].max()),
            )
        )
    return sorted(candidates, key=lambda item: (item.source, item.upstream_source))


def score_source_candidates_by_policy(
    request: MarketCacheExportPolicyRequest,
    candidates: list[MarketCacheSourceCandidate],
    *,
    strict_reliable: bool = False,
    config: Settings | dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Score available source candidates using field reliability policy and preference order."""

    project_settings = _resolve_project_settings(config)
    preference = _source_preference_for(request, project_settings.market_cache_export_policy)
    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        policy = get_market_source_policy(
            source=candidate.source,
            upstream_source=candidate.upstream_source,
            security_type=request.security_type,
            config=project_settings,
        )
        statuses = {field: policy.reliability_for(field) for field in request.required_fields}
        status_values = {field: value.value for field, value in statuses.items()}
        rejected_statuses = {
            MarketFieldReliability.UNAVAILABLE,
            MarketFieldReliability.UNSTABLE,
            MarketFieldReliability.DO_NOT_USE,
        }
        warnings: list[str] = []
        rejected = any(status in rejected_statuses for status in statuses.values())
        if strict_reliable and any(status != MarketFieldReliability.RELIABLE for status in statuses.values()):
            rejected = True
            warnings.append("strict_reliable requires every required field to be RELIABLE.")
        else:
            if any(status == MarketFieldReliability.PROVISIONAL for status in statuses.values()):
                warnings.append("One or more required fields are PROVISIONAL and require review.")
            if any(status == MarketFieldReliability.UNKNOWN for status in statuses.values()):
                warnings.append("One or more required fields have UNKNOWN reliability.")
            if any(status == MarketFieldReliability.CAVEAT_FIRST_WINDOW_ROW for status in statuses.values()):
                warnings.append("One or more required fields have first-window-row caveats.")
        if any(status in rejected_statuses for status in statuses.values()):
            warnings.append("One or more required fields are unavailable, unstable, or marked do-not-use.")
        min_rank = min((POLICY_SCORE_RANK.get(status, 0) for status in statuses.values()), default=0)
        pref_index = _preference_index(candidate.source, candidate.upstream_source, preference)
        preferred_override = _preferred_override_rank(request, candidate)
        scored.append(
            {
                "candidate": candidate,
                "policy_statuses": status_values,
                "warnings": warnings,
                "rejected": rejected,
                "score": min_rank,
                "preference_index": pref_index,
                "preferred_override": preferred_override,
            }
        )
    return sorted(
        scored,
        key=lambda item: (
            bool(item["rejected"]),
            -int(item["preferred_override"]),
            -int(item["score"]),
            int(item["preference_index"]),
            -int(item["candidate"].row_count),
            item["candidate"].source,
            item["candidate"].upstream_source,
        ),
    )


def build_policy_export_recommendations(
    requests: list[MarketCacheExportPolicyRequest],
    *,
    cache_path: str | Path | None = None,
    strict_reliable: bool = False,
    fail_fast: bool = False,
    config: Settings | dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build recommendation rows, reviewed manifest rows, and issues."""

    recommendations: list[MarketCacheExportPolicyRecommendation] = []
    issues: list[MarketCacheExportPolicyIssue] = []

    for request in requests:
        if not request.enabled:
            recommendations.append(
                MarketCacheExportPolicyRecommendation(
                    manifest_row=request.manifest_row,
                    symbol=request.symbol,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    security_type=request.security_type,
                    required_fields=request.required_fields,
                    status="DISABLED",
                    reason="Request row is disabled.",
                    notes=request.notes,
                )
            )
            continue

        candidates = find_available_cache_sources_for_symbol(request, cache_path=cache_path, config=config)
        if not candidates:
            issue = MarketCacheExportPolicyIssue(
                category="NO_CACHE_ROWS",
                severity="ERROR",
                manifest_row=request.manifest_row,
                symbol=request.symbol,
                message="No cached rows are available for this symbol/date request.",
                suggested_action="Backfill or ingest reviewed rows before planning a cache export.",
            )
            issues.append(issue)
            recommendations.append(
                _recommendation_from_issue(request, "NO_CACHE_ROWS", issue.message)
            )
            if fail_fast:
                break
            continue

        scored = score_source_candidates_by_policy(
            request,
            candidates,
            strict_reliable=strict_reliable,
            config=config,
        )
        accepted = [item for item in scored if not item["rejected"] and int(item["score"]) > 0]
        if not accepted:
            issue = MarketCacheExportPolicyIssue(
                category="NO_RELIABLE_SOURCE",
                severity="ERROR",
                manifest_row=request.manifest_row,
                symbol=request.symbol,
                message="No available source/upstream satisfies the required field policy.",
                suggested_action="Review source policy, relax strict mode, or ingest a better source.",
            )
            issues.append(issue)
            best = scored[0] if scored else {}
            candidate = best.get("candidate")
            recommendations.append(
                MarketCacheExportPolicyRecommendation(
                    manifest_row=request.manifest_row,
                    symbol=request.symbol,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    security_type=request.security_type,
                    required_fields=request.required_fields,
                    status="NO_RELIABLE_SOURCE",
                    recommended_source=getattr(candidate, "source", ""),
                    recommended_upstream_source=getattr(candidate, "upstream_source", ""),
                    row_count=getattr(candidate, "row_count", 0),
                    min_trade_date=getattr(candidate, "min_trade_date", ""),
                    max_trade_date=getattr(candidate, "max_trade_date", ""),
                    candidate_count=len(candidates),
                    policy_statuses=best.get("policy_statuses", {}),
                    warnings=list(best.get("warnings", [])),
                    reason=issue.message,
                    notes=request.notes,
                )
            )
            if fail_fast:
                break
            continue

        best = accepted[0]
        candidate = best["candidate"]
        warnings = list(best["warnings"])
        status = "RECOMMENDED_WITH_WARNINGS" if warnings else "RECOMMENDED"
        if warnings:
            issues.append(
                MarketCacheExportPolicyIssue(
                    category="POLICY_WARNING",
                    severity="WARN",
                    manifest_row=request.manifest_row,
                    symbol=request.symbol,
                    source=candidate.source,
                    upstream_source=candidate.upstream_source,
                    message=" | ".join(warnings),
                    suggested_action="Review the generated manifest notes before running market-cache-export.",
                )
            )
        recommendations.append(
            MarketCacheExportPolicyRecommendation(
                manifest_row=request.manifest_row,
                symbol=request.symbol,
                start_date=request.start_date,
                end_date=request.end_date,
                security_type=request.security_type,
                required_fields=request.required_fields,
                status=status,
                recommended_source=candidate.source,
                recommended_upstream_source=candidate.upstream_source,
                row_count=candidate.row_count,
                min_trade_date=candidate.min_trade_date,
                max_trade_date=candidate.max_trade_date,
                candidate_count=len(candidates),
                policy_statuses=best["policy_statuses"],
                warnings=warnings,
                reason=_recommendation_reason(candidate, best),
                notes=request.notes,
            )
        )

    recommendation_frame = _finalize_recommendations(
        pd.DataFrame([recommendation.as_row() for recommendation in recommendations])
    )
    manifest_frame = _finalize_recommended_manifest(
        pd.DataFrame([recommendation.as_reviewed_manifest_row() for recommendation in recommendations])
    )
    issue_frame = _finalize_issues(pd.DataFrame([issue.as_row() for issue in issues]))
    return recommendation_frame, manifest_frame, issue_frame


def run_market_cache_export_policy_plan(
    manifest: str | Path,
    *,
    cache_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    manifest_output_dir: str | Path | None = None,
    strict_reliable: bool | None = None,
    fail_fast: bool | None = None,
    config: Settings | MarketCacheExportPolicySettings | dict[str, Any] | None = None,
) -> MarketCacheExportPolicyResult:
    """Run the policy-aware reviewed cache export planning workflow."""

    project_settings, policy_settings = _resolve_settings(config)
    if policy_settings.enable_live_trading or policy_settings.enable_broker_api:
        raise ValueError("Market cache export policy planning cannot enable live trading or broker API access")
    if output_dir is not None:
        policy_settings = policy_settings.model_copy(update={"output_dir": Path(output_dir)})
    if manifest_output_dir is not None:
        policy_settings = policy_settings.model_copy(update={"manifest_output_dir": Path(manifest_output_dir)})
    effective_strict = policy_settings.strict_reliable if strict_reliable is None else bool(strict_reliable)
    effective_fail_fast = policy_settings.fail_fast if fail_fast is None else bool(fail_fast)

    manifest_path = Path(manifest)
    requests = load_policy_export_request(manifest_path, settings=policy_settings)
    plan_id = generate_market_cache_export_policy_plan_id(
        manifest_path=manifest_path,
        cache_path=cache_path or project_settings.market_data_cache.cache_path,
        requests=requests,
        strict_reliable=effective_strict,
        settings=policy_settings,
    )
    paths = resolve_market_cache_export_policy_artifact_paths(
        policy_settings.output_dir,
        policy_settings.manifest_output_dir,
        plan_id,
    )
    recommendations, recommended_manifest, issues = build_policy_export_recommendations(
        requests,
        cache_path=cache_path,
        strict_reliable=effective_strict,
        fail_fast=effective_fail_fast,
        config=project_settings,
    )
    status = _status_from_frames(recommendations, issues)
    warnings = _warnings_from_issues(issues)
    result = MarketCacheExportPolicyResult(
        plan_id=plan_id,
        status=status,
        manifest_path=manifest_path,
        request_rows=requests,
        recommendations_frame=recommendations,
        issues_frame=issues,
        recommended_manifest_frame=recommended_manifest,
        recommended_manifest_path=paths.recommended_manifest,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_CACHE_EXPORT_POLICY_LIMITATIONS,
        audit_metadata={
            "plan_id": plan_id,
            "operation": "market_cache_export_policy_plan",
            "manifest_path": manifest_path,
            "cache_path": cache_path or project_settings.market_data_cache.cache_path,
            "recommendation_count": int(recommendations["status"].isin(ACCEPTABLE_POLICY_STATUSES).sum())
            if not recommendations.empty
            else 0,
            "issue_count": len(issues),
            "strict_reliable": effective_strict,
            "generated_reviewed_manifest_path": paths.recommended_manifest,
            "cache_mutated": False,
            "market_cache_export_run": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "network_api_calls_used_in_tests": False,
            "config_version": policy_settings.config_version,
        },
    )
    if policy_settings.write_artifacts:
        write_policy_export_recommendation_artifacts(result)
    return result


def write_policy_export_recommendation_artifacts(result: MarketCacheExportPolicyResult) -> dict[str, Path]:
    """Write policy planning artifacts and the generated reviewed export manifest."""

    paths = MarketCacheExportPolicyArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    paths.recommended_manifest.parent.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.recommendations_frame, paths.market_cache_export_policy_recommendations)
    _export_dataframe(result.issues_frame, paths.market_cache_export_policy_issues)
    _export_dataframe(result.recommended_manifest_frame, paths.recommended_manifest)
    metadata = build_policy_export_recommendation_metadata(result)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.market_cache_export_policy_report.write_text(render_policy_export_recommendation_report(result), encoding="utf-8")
    return paths.as_dict()


def build_policy_export_recommendation_metadata(result: MarketCacheExportPolicyResult) -> dict[str, Any]:
    return {
        "plan_id": result.plan_id,
        "status": result.status,
        "created_at": MARKET_CACHE_EXPORT_POLICY_TIMESTAMP,
        "manifest_path": str(result.manifest_path),
        "generated_reviewed_manifest_path": str(result.recommended_manifest_path),
        "recommendation_count": result.recommendation_count,
        "issue_count": result.issue_count,
        "status_counts": _status_counts(result.recommendations_frame),
        "recommendations": result.recommendations_frame.to_dict("records"),
        "issues": result.issues_frame.to_dict("records"),
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "audit_metadata": result.audit_metadata,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "cache_mutated": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }


def render_policy_export_recommendation_report(result: MarketCacheExportPolicyResult) -> str:
    lines = [
        "# Policy-aware Reviewed Cache Export Plan",
        "",
        f"- plan_id: {result.plan_id}",
        f"- status: {result.status}",
        f"- manifest_path: {result.manifest_path}",
        f"- generated_reviewed_manifest_path: {result.recommended_manifest_path}",
        f"- recommendation_count: {result.recommendation_count}",
        f"- issue_count: {result.issue_count}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Recommendations",
        "",
        result.recommendations_frame.to_markdown(index=False) if not result.recommendations_frame.empty else "No recommendations.",
        "",
        "## Issues",
        "",
        result.issues_frame.to_markdown(index=False) if not result.issues_frame.empty else "No issues.",
        "",
        "## Interpretation",
        "",
        "- This command recommends reviewed source/upstream selections from existing local cache rows.",
        "- It does not run market-cache-export automatically by default.",
        "- The generated reviewed manifest should be inspected before use.",
        "- PROVISIONAL source policy recommendations remain warnings.",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def resolve_market_cache_export_policy_artifact_paths(
    output_dir: str | Path,
    manifest_output_dir: str | Path,
    plan_id: str,
) -> MarketCacheExportPolicyArtifactPaths:
    artifact_dir = Path(output_dir) / plan_id
    return MarketCacheExportPolicyArtifactPaths(
        artifact_dir=artifact_dir,
        market_cache_export_policy_report=artifact_dir / "market_cache_export_policy_report.md",
        market_cache_export_policy_recommendations=artifact_dir / "market_cache_export_policy_recommendations.csv",
        market_cache_export_policy_issues=artifact_dir / "market_cache_export_policy_issues.csv",
        metadata=artifact_dir / "metadata.json",
        recommended_manifest=Path(manifest_output_dir) / f"market_cache_export_recommended_{plan_id}.csv",
    )


def generate_market_cache_export_policy_plan_id(
    *,
    manifest_path: Path,
    cache_path: str | Path,
    requests: list[MarketCacheExportPolicyRequest],
    strict_reliable: bool,
    settings: MarketCacheExportPolicySettings,
) -> str:
    payload = {
        "manifest_path": str(manifest_path),
        "cache_path": str(cache_path),
        "strict_reliable": bool(strict_reliable),
        "requests": [
            {
                "manifest_row": row.manifest_row,
                "symbol": row.symbol,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "required_fields": row.required_fields,
                "enabled": row.enabled,
                "security_type": row.security_type,
                "preferred_source": row.preferred_source,
                "preferred_upstream_source": row.preferred_upstream_source,
            }
            for row in requests
        ],
        "source_preference": settings.source_preference,
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _recommendation_from_issue(
    request: MarketCacheExportPolicyRequest,
    status: str,
    message: str,
) -> MarketCacheExportPolicyRecommendation:
    return MarketCacheExportPolicyRecommendation(
        manifest_row=request.manifest_row,
        symbol=request.symbol,
        start_date=request.start_date,
        end_date=request.end_date,
        security_type=request.security_type,
        required_fields=request.required_fields,
        status=status,
        reason=message,
        notes=request.notes,
    )


def _recommendation_reason(candidate: MarketCacheSourceCandidate, scored: dict[str, Any]) -> str:
    statuses = scored.get("policy_statuses", {})
    return (
        f"Selected {candidate.source}/{candidate.upstream_source} from local cache with "
        f"{candidate.row_count} rows; required field policy statuses: {json.dumps(statuses, sort_keys=True)}."
    )


def _source_preference_for(
    request: MarketCacheExportPolicyRequest,
    settings: MarketCacheExportPolicySettings,
) -> list[list[str]]:
    if request.preferred_source and request.preferred_upstream_source:
        preferred = [[request.preferred_source, request.preferred_upstream_source]]
    else:
        preferred = []
    configured = settings.source_preference.get(request.security_type.upper(), [])
    return preferred + configured


def _preference_index(source: str, upstream_source: str, preference: list[list[str]]) -> int:
    pair = [source, upstream_source]
    for index, preferred in enumerate(preference):
        normalized = [_normalize_key(item) for item in preferred]
        if normalized == pair:
            return index
    return len(preference) + 100


def _preferred_override_rank(request: MarketCacheExportPolicyRequest, candidate: MarketCacheSourceCandidate) -> int:
    if not request.preferred_source or not request.preferred_upstream_source:
        return 0
    return int(candidate.source == request.preferred_source and candidate.upstream_source == request.preferred_upstream_source)


def _status_from_frames(recommendations: pd.DataFrame, issues: pd.DataFrame) -> str:
    if not issues.empty and "ERROR" in set(issues["severity"].astype(str).str.upper()):
        if recommendations.empty or not recommendations["status"].isin(ACCEPTABLE_POLICY_STATUSES).any():
            return "FAIL"
        return "WARN"
    if not issues.empty and "WARN" in set(issues["severity"].astype(str).str.upper()):
        return "WARN"
    if recommendations.empty:
        return "FAIL"
    if recommendations["status"].eq("RECOMMENDED_WITH_WARNINGS").any():
        return "WARN"
    if recommendations["status"].isin(ACCEPTABLE_POLICY_STATUSES).any():
        return "PASS"
    return "WARN"


def _warnings_from_issues(issues: pd.DataFrame) -> list[str]:
    if issues.empty:
        return []
    return [
        f"{row.get('severity')} {row.get('category')}: {row.get('message')}"
        for row in issues.to_dict("records")
        if str(row.get("severity", "")).upper() in {"WARN", "ERROR"}
    ]


def _status_counts(frame: pd.DataFrame) -> dict[str, int]:
    if frame.empty or "status" not in frame.columns:
        return {}
    return {str(key): int(value) for key, value in frame["status"].value_counts().sort_index().items()}


def _finalize_recommendations(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in POLICY_EXPORT_RECOMMENDATION_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    if output.empty:
        return output[POLICY_EXPORT_RECOMMENDATION_COLUMNS]
    return output[POLICY_EXPORT_RECOMMENDATION_COLUMNS].sort_values(["manifest_row", "symbol"]).reset_index(drop=True)


def _finalize_recommended_manifest(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in RECOMMENDED_MANIFEST_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    if output.empty:
        return output[RECOMMENDED_MANIFEST_COLUMNS]
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    return output[RECOMMENDED_MANIFEST_COLUMNS].sort_values(["symbol", "start_date", "end_date"]).reset_index(drop=True)


def _finalize_issues(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in POLICY_EXPORT_ISSUE_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    if output.empty:
        return output[POLICY_EXPORT_ISSUE_COLUMNS]
    return output[POLICY_EXPORT_ISSUE_COLUMNS].sort_values(["severity", "category", "manifest_row"]).reset_index(drop=True)


def _normalize_required_fields(value: Any, settings: MarketCacheExportPolicySettings) -> list[str]:
    text = _string_or_empty(value)
    raw_values = text.split(",") if text else settings.default_required_fields
    fields: list[str] = []
    for raw in raw_values:
        field = str(raw or "").strip().lower()
        if field and field not in fields:
            fields.append(field)
    return fields


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes", "y", "enabled"}:
        return True
    if text in {"false", "0", "no", "n", "disabled", ""}:
        return False
    raise ValueError(f"Invalid boolean value in market cache export policy manifest: {value}")


def _normalize_key(value: Any) -> str:
    return str(value or "").strip().upper()


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = frame.copy(deep=True)
    if "symbol" in export.columns:
        export["symbol"] = export["symbol"].map(normalize_symbol_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _resolve_project_settings(config: Settings | dict[str, Any] | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    if isinstance(config, dict):
        project = load_settings(Path("config/default.yaml"))
        updates: dict[str, Any] = {}
        if "market_data_cache" in config and isinstance(config["market_data_cache"], dict):
            updates["market_data_cache"] = project.market_data_cache.model_copy(update=config["market_data_cache"])
        if "market_cache_export_policy" in config and isinstance(config["market_cache_export_policy"], dict):
            updates["market_cache_export_policy"] = project.market_cache_export_policy.model_copy(
                update=config["market_cache_export_policy"]
            )
        return project.model_copy(update=updates) if updates else project
    raise TypeError("config must be Settings, dict, or None")


def _resolve_settings(
    config: Settings | MarketCacheExportPolicySettings | dict[str, Any] | None,
) -> tuple[Settings, MarketCacheExportPolicySettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.market_cache_export_policy
    if isinstance(config, Settings):
        return config, config.market_cache_export_policy
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, MarketCacheExportPolicySettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.market_cache_export_policy.model_dump())
        project_updates: dict[str, Any] = {}
        for key, value in config.items():
            if key == "market_cache_export_policy" and isinstance(value, dict):
                payload.update(value)
            elif key == "market_data_cache" and isinstance(value, dict):
                project_updates["market_data_cache"] = project.market_data_cache.model_copy(update=value)
            elif key in payload:
                payload[key] = value
        if project_updates:
            project = project.model_copy(update=project_updates)
        return project, MarketCacheExportPolicySettings(**payload)
    raise TypeError("config must be Settings, MarketCacheExportPolicySettings, dict, or None")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
