"""Plan-only multi-date current-candidates backfill from local cache coverage."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


PLAN_COLUMNS = [
    "plan_id",
    "signal_date",
    "universe",
    "selection_profile",
    "eligible_symbol_count",
    "total_symbol_count",
    "min_required_symbol_count",
    "max_forward_horizon",
    "warmup_trading_days",
    "warmup_available",
    "earliest_required_warmup_date",
    "first_available_market_date",
    "warmup_start_date",
    "warmup_reason",
    "forward_1d_available",
    "forward_3d_available",
    "forward_5d_available",
    "forward_10d_available",
    "latest_required_forward_date",
    "cache_start_date",
    "cache_end_date",
    "source_policy",
    "recommended_source_filter",
    "recommended_upstream_filter",
    "status",
    "reason",
    "candidate_generation_feasible",
    "candidate_generation_blocker",
    "symbols",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
]

REQUIRED_CACHE_COLUMNS = [
    "symbol",
    "trade_date",
    "source",
    "upstream_source",
]

SAFETY_STATEMENT = "No live trading, broker API, order placement, message delivery, or network/API call was invoked."


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanSettings:
    output_dir: Path = Path("outputs/reports/current_candidates_backfill_plan")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_message_delivery: bool = False
    auto_order_allowed: bool = False


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanRequest:
    cache_path: Path
    start_date: str
    end_date: str
    universe: str
    selection_profile: str
    horizons: tuple[int, ...]
    max_dates: int | None
    warmup_trading_days: int
    min_symbol_coverage: int
    source_policy: str


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanRow:
    plan_id: str
    signal_date: str
    universe: str
    selection_profile: str
    eligible_symbol_count: int
    total_symbol_count: int
    min_required_symbol_count: int
    max_forward_horizon: int
    warmup_trading_days: int
    warmup_available: bool
    earliest_required_warmup_date: str
    first_available_market_date: str
    warmup_start_date: str
    warmup_reason: str
    forward_1d_available: bool
    forward_3d_available: bool
    forward_5d_available: bool
    forward_10d_available: bool
    latest_required_forward_date: str
    cache_start_date: str
    cache_end_date: str
    source_policy: str
    recommended_source_filter: str
    recommended_upstream_filter: str
    status: str
    reason: str
    candidate_generation_feasible: bool
    candidate_generation_blocker: str
    symbols: str
    no_live_trading: bool = True
    no_broker_api: bool = True
    no_order_placement: bool = True
    no_message_sent: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "signal_date": self.signal_date,
            "universe": self.universe,
            "selection_profile": self.selection_profile,
            "eligible_symbol_count": self.eligible_symbol_count,
            "total_symbol_count": self.total_symbol_count,
            "min_required_symbol_count": self.min_required_symbol_count,
            "max_forward_horizon": self.max_forward_horizon,
            "warmup_trading_days": self.warmup_trading_days,
            "warmup_available": self.warmup_available,
            "earliest_required_warmup_date": self.earliest_required_warmup_date,
            "first_available_market_date": self.first_available_market_date,
            "warmup_start_date": self.warmup_start_date,
            "warmup_reason": self.warmup_reason,
            "forward_1d_available": self.forward_1d_available,
            "forward_3d_available": self.forward_3d_available,
            "forward_5d_available": self.forward_5d_available,
            "forward_10d_available": self.forward_10d_available,
            "latest_required_forward_date": self.latest_required_forward_date,
            "cache_start_date": self.cache_start_date,
            "cache_end_date": self.cache_end_date,
            "source_policy": self.source_policy,
            "recommended_source_filter": self.recommended_source_filter,
            "recommended_upstream_filter": self.recommended_upstream_filter,
            "status": self.status,
            "reason": self.reason,
            "candidate_generation_feasible": self.candidate_generation_feasible,
            "candidate_generation_blocker": self.candidate_generation_blocker,
            "symbols": self.symbols,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
            "no_order_placement": self.no_order_placement,
            "no_message_sent": self.no_message_sent,
        }


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanArtifactPaths:
    artifact_dir: Path
    plan_csv: Path
    report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "plan_csv": self.plan_csv,
            "report": self.report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanResult:
    plan_id: str
    status: str
    request: CurrentCandidatesBackfillPlanRequest
    selected_date_count: int
    first_signal_date: str
    last_signal_date: str
    horizon_feasibility_counts: dict[str, int]
    warmup_feasibility_counts: dict[str, int]
    plan_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def build_current_candidates_backfill_plan(
    *,
    cache_path: str | Path = "data/cache/market/daily_bars.csv",
    start_date: str,
    end_date: str,
    universe: str,
    selection_profile: str = "demo",
    horizons: list[int] | tuple[int, ...] = (1, 3, 5, 10),
    max_dates: int | None = None,
    warmup_trading_days: int = 60,
    min_symbol_coverage: int = 4,
    source_policy: str = "reviewed_local_v0",
    output_dir: str | Path | None = None,
    settings: CurrentCandidatesBackfillPlanSettings | None = None,
) -> CurrentCandidatesBackfillPlanResult:
    """Build a plan-only current-candidates backfill artifact from local cache coverage."""

    resolved_settings = settings or CurrentCandidatesBackfillPlanSettings()
    if output_dir is not None:
        resolved_settings = CurrentCandidatesBackfillPlanSettings(
            output_dir=Path(output_dir),
            config_version=resolved_settings.config_version,
            write_artifacts=resolved_settings.write_artifacts,
            enable_live_trading=resolved_settings.enable_live_trading,
            enable_broker_api=resolved_settings.enable_broker_api,
            enable_message_delivery=resolved_settings.enable_message_delivery,
            auto_order_allowed=resolved_settings.auto_order_allowed,
        )
    _assert_settings_safe(resolved_settings)

    request = CurrentCandidatesBackfillPlanRequest(
        cache_path=Path(cache_path),
        start_date=_date_text(start_date),
        end_date=_date_text(end_date),
        universe=str(universe),
        selection_profile=_normalize_selection_profile(selection_profile),
        horizons=_normalize_horizons(horizons),
        max_dates=max_dates if max_dates is None else int(max_dates),
        warmup_trading_days=_normalize_warmup_trading_days(warmup_trading_days),
        min_symbol_coverage=int(min_symbol_coverage),
        source_policy=str(source_policy or "reviewed_local_v0"),
    )
    cache_frame = _load_cache_frame(request.cache_path)
    scoped = _scope_cache_frame(cache_frame, request.start_date, request.end_date)
    plan_id = generate_current_candidates_backfill_plan_id(request, scoped, resolved_settings)
    rows = _build_plan_rows(plan_id, request, scoped)
    plan_frame = build_current_candidates_backfill_plan_table([row.as_dict() for row in rows])
    status = "PASS" if rows else "WARN"
    warnings = _build_warnings(request, rows, scoped)
    paths = resolve_current_candidates_backfill_plan_artifact_paths(resolved_settings.output_dir, plan_id)
    result = CurrentCandidatesBackfillPlanResult(
        plan_id=plan_id,
        status=status,
        request=request,
        selected_date_count=len(rows),
        first_signal_date=_first_value(plan_frame, "signal_date"),
        last_signal_date=_last_value(plan_frame, "signal_date"),
        horizon_feasibility_counts=_horizon_feasibility_counts(plan_frame, request.horizons),
        warmup_feasibility_counts=_warmup_feasibility_counts(plan_frame),
        plan_frame=plan_frame,
        warnings=warnings,
        artifact_paths=paths.as_dict(),
        audit_metadata=_audit_metadata(request, scoped, resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_current_candidates_backfill_plan_artifacts(result)
    return result


def select_candidate_signal_dates(
    trading_dates: list[pd.Timestamp],
    *,
    horizons: list[int] | tuple[int, ...],
    warmup_trading_days: int = 60,
    max_dates: int | None = None,
) -> list[pd.Timestamp]:
    """Select signal dates that have enough warmup history and future trading dates."""

    normalized_horizons = _normalize_horizons(horizons)
    max_horizon = max(normalized_horizons)
    warmup_days = _normalize_warmup_trading_days(warmup_trading_days)
    feasible = [
        date
        for index, date in enumerate(trading_dates)
        if _warmup_available_at_index(index, warmup_days) and index + max_horizon < len(trading_dates)
    ]
    if max_dates is None or max_dates <= 0 or len(feasible) <= max_dates:
        return feasible
    if max_dates == 1:
        return [feasible[0]]
    step = (len(feasible) - 1) / float(max_dates - 1)
    selected_indices = sorted({round(index * step) for index in range(max_dates)})
    return [feasible[index] for index in selected_indices]


def evaluate_forward_horizon_feasibility(
    signal_date: pd.Timestamp,
    trading_dates: list[pd.Timestamp],
    horizons: list[int] | tuple[int, ...],
) -> dict[int, bool]:
    """Return whether each forward horizon is available for one signal date."""

    normalized = [pd.Timestamp(date).normalize() for date in trading_dates]
    date = pd.Timestamp(signal_date).normalize()
    if date not in normalized:
        return {horizon: False for horizon in _normalize_horizons(horizons)}
    index = normalized.index(date)
    return {horizon: index + horizon < len(normalized) for horizon in _normalize_horizons(horizons)}


def evaluate_warmup_feasibility(
    signal_date: pd.Timestamp,
    trading_dates: list[pd.Timestamp],
    warmup_trading_days: int,
) -> dict[str, Any]:
    """Return warmup feasibility details for one signal date."""

    normalized = [pd.Timestamp(date).normalize() for date in trading_dates]
    date = pd.Timestamp(signal_date).normalize()
    warmup_days = _normalize_warmup_trading_days(warmup_trading_days)
    first_available = _date_text(normalized[0]) if normalized else ""
    if date not in normalized:
        return {
            "warmup_available": False,
            "earliest_required_warmup_date": "",
            "first_available_market_date": first_available,
            "warmup_start_date": first_available,
            "warmup_reason": "signal date is not present in local market cache trading dates",
        }
    index = normalized.index(date)
    available = _warmup_available_at_index(index, warmup_days)
    start_index = index - warmup_days + 1 if available else 0
    warmup_start = _date_text(normalized[start_index]) if normalized else ""
    return {
        "warmup_available": available,
        "earliest_required_warmup_date": warmup_start if available else "",
        "first_available_market_date": first_available,
        "warmup_start_date": warmup_start,
        "warmup_reason": _warmup_reason(index=index, warmup_days=warmup_days, available=available),
    }


def build_current_candidates_backfill_plan_table(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=PLAN_COLUMNS)


def write_current_candidates_backfill_plan_artifacts(result: CurrentCandidatesBackfillPlanResult) -> dict[str, Path]:
    """Write plan CSV, markdown report, and metadata."""

    paths = CurrentCandidatesBackfillPlanArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.plan_frame, paths.plan_csv)
    paths.metadata.write_text(
        json.dumps(_json_safe(build_current_candidates_backfill_plan_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    paths.report.write_text(render_current_candidates_backfill_plan_report(result), encoding="utf-8")
    return paths.as_dict()


def render_current_candidates_backfill_plan_report(result: CurrentCandidatesBackfillPlanResult) -> str:
    lines = [
        f"# Current-Candidates Backfill Plan: {result.plan_id}",
        "",
        SAFETY_STATEMENT,
        "This is a plan-only artifact. It does not run current-candidates, data-pipeline, cache export, or forward-label computation.",
        "",
        "## Summary",
        "",
        _dict_table(_summary_dict(result)),
        "",
        "## Source Policy Guidance",
        "",
        _dict_table(
            {
                "source_policy": result.request.source_policy,
                "recommended_source_filter": _recommended_source_filter(result.request.source_policy),
                "recommended_upstream_filter": _recommended_upstream_filter(result.request.source_policy),
                "notes": "Use explicit reviewed source/upstream selections before executing candidate generation.",
            }
        ),
        "",
        "## Planned Signal Dates",
        "",
        _markdown_table(result.plan_frame, PLAN_COLUMNS),
        "",
        "## Warnings",
        "",
        "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
        "",
    ]
    return "\n".join(str(line) for line in lines)


def build_current_candidates_backfill_plan_metadata(result: CurrentCandidatesBackfillPlanResult) -> dict[str, Any]:
    return {
        "plan_id": result.plan_id,
        "status": result.status,
        "created_at": "",
        "cache_path": str(result.request.cache_path),
        "start_date": result.request.start_date,
        "end_date": result.request.end_date,
        "universe": result.request.universe,
        "selection_profile": result.request.selection_profile,
        "horizons": list(result.request.horizons),
        "max_dates": result.request.max_dates,
        "warmup_trading_days": result.request.warmup_trading_days,
        "min_symbol_coverage": result.request.min_symbol_coverage,
        "source_policy": result.request.source_policy,
        "selected_date_count": result.selected_date_count,
        "first_signal_date": result.first_signal_date,
        "last_signal_date": result.last_signal_date,
        "horizon_feasibility_counts": result.horizon_feasibility_counts,
        "warmup_feasibility_counts": result.warmup_feasibility_counts,
        "warnings": result.warnings,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
        **result.audit_metadata,
        "known_limitations": [
            "This is a plan-only artifact and does not generate current-candidates.",
            "Universe snapshot point-in-time compatibility must be checked before execution.",
            "Forward returns are not computed by this planner.",
            "The planner does not validate strategy performance.",
        ],
    }


def generate_current_candidates_backfill_plan_id(
    request: CurrentCandidatesBackfillPlanRequest,
    frame: pd.DataFrame,
    settings: CurrentCandidatesBackfillPlanSettings,
) -> str:
    payload = {
        "cache_path": str(request.cache_path),
        "start_date": request.start_date,
        "end_date": request.end_date,
        "universe": request.universe,
        "selection_profile": request.selection_profile,
        "horizons": list(request.horizons),
        "max_dates": request.max_dates,
        "warmup_trading_days": request.warmup_trading_days,
        "min_symbol_coverage": request.min_symbol_coverage,
        "source_policy": request.source_policy,
        "frame_digest": _frame_digest(frame),
        "config_version": settings.config_version,
    }
    return _hash_payload(payload, length=12)


def resolve_current_candidates_backfill_plan_artifact_paths(
    output_dir: str | Path,
    plan_id: str,
) -> CurrentCandidatesBackfillPlanArtifactPaths:
    artifact_dir = Path(output_dir) / plan_id
    return CurrentCandidatesBackfillPlanArtifactPaths(
        artifact_dir=artifact_dir,
        plan_csv=artifact_dir / "current_candidates_backfill_plan.csv",
        report=artifact_dir / "current_candidates_backfill_plan_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def _build_plan_rows(
    plan_id: str,
    request: CurrentCandidatesBackfillPlanRequest,
    frame: pd.DataFrame,
) -> list[CurrentCandidatesBackfillPlanRow]:
    if frame.empty:
        return []
    trading_dates = _trading_dates(frame)
    selected_dates = select_candidate_signal_dates(
        trading_dates,
        horizons=request.horizons,
        warmup_trading_days=request.warmup_trading_days,
        max_dates=request.max_dates,
    )
    total_symbol_count = _symbol_count(frame)
    cache_start = _date_text(frame["trade_date"].min())
    cache_end = _date_text(frame["trade_date"].max())
    rows: list[CurrentCandidatesBackfillPlanRow] = []
    for signal_date in selected_dates:
        signal_text = _date_text(signal_date)
        date_frame = frame.loc[frame["trade_date"] == signal_date].copy()
        symbols = sorted({normalize_symbol_value(value) for value in date_frame["symbol"].tolist() if normalize_symbol_value(value)})
        eligible_symbol_count = len(symbols)
        feasibility = evaluate_forward_horizon_feasibility(signal_date, trading_dates, request.horizons)
        warmup = evaluate_warmup_feasibility(signal_date, trading_dates, request.warmup_trading_days)
        max_forward_date = _forward_date_text(signal_date, trading_dates, max(request.horizons))
        all_requested = all(feasibility.values())
        warmup_available = bool(warmup["warmup_available"])
        coverage_ok = eligible_symbol_count >= request.min_symbol_coverage
        candidate_generation_feasible = all_requested and warmup_available and coverage_ok
        blocker = _candidate_generation_blocker(
            all_requested=all_requested,
            warmup_available=warmup_available,
            coverage_ok=coverage_ok,
            eligible_symbol_count=eligible_symbol_count,
            request=request,
        )
        status = "READY" if candidate_generation_feasible else "BLOCKED"
        reason = _row_reason(candidate_generation_feasible=candidate_generation_feasible, blocker=blocker)
        rows.append(
            CurrentCandidatesBackfillPlanRow(
                plan_id=plan_id,
                signal_date=signal_text,
                universe=request.universe,
                selection_profile=request.selection_profile,
                eligible_symbol_count=eligible_symbol_count,
                total_symbol_count=total_symbol_count,
                min_required_symbol_count=request.min_symbol_coverage,
                max_forward_horizon=max(request.horizons),
                warmup_trading_days=request.warmup_trading_days,
                warmup_available=warmup_available,
                earliest_required_warmup_date=str(warmup["earliest_required_warmup_date"]),
                first_available_market_date=str(warmup["first_available_market_date"]),
                warmup_start_date=str(warmup["warmup_start_date"]),
                warmup_reason=str(warmup["warmup_reason"]),
                forward_1d_available=bool(feasibility.get(1, False)),
                forward_3d_available=bool(feasibility.get(3, False)),
                forward_5d_available=bool(feasibility.get(5, False)),
                forward_10d_available=bool(feasibility.get(10, False)),
                latest_required_forward_date=max_forward_date,
                cache_start_date=cache_start,
                cache_end_date=cache_end,
                source_policy=request.source_policy,
                recommended_source_filter=_recommended_source_filter(request.source_policy),
                recommended_upstream_filter=_recommended_upstream_filter(request.source_policy),
                status=status,
                reason=reason,
                candidate_generation_feasible=candidate_generation_feasible,
                candidate_generation_blocker=blocker,
                symbols=";".join(symbols),
            )
        )
    return rows


def _load_cache_frame(cache_path: Path) -> pd.DataFrame:
    if not cache_path.exists():
        raise FileNotFoundError(f"Market cache CSV not found: {cache_path}")
    frame = read_csv_preserve_symbol_columns(cache_path, keep_default_na=False)
    missing = sorted(set(REQUIRED_CACHE_COLUMNS).difference(frame.columns))
    if missing:
        raise ValueError(f"Market cache missing required columns: {', '.join(missing)}")
    output = frame.copy(deep=True)
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    output["trade_date"] = pd.to_datetime(output["trade_date"], errors="coerce").dt.normalize()
    if output["trade_date"].isna().any():
        raise ValueError("Market cache contains invalid trade_date values.")
    return output


def _scope_cache_frame(frame: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    start = pd.Timestamp(start_date).normalize()
    end = pd.Timestamp(end_date).normalize()
    if start > end:
        raise ValueError("start_date cannot be later than end_date.")
    scoped = frame.loc[(frame["trade_date"] >= start) & (frame["trade_date"] <= end)].copy()
    return scoped.sort_values(["trade_date", "symbol", "source", "upstream_source"]).reset_index(drop=True)


def _trading_dates(frame: pd.DataFrame) -> list[pd.Timestamp]:
    if frame.empty:
        return []
    return [pd.Timestamp(value).normalize() for value in sorted(frame["trade_date"].dropna().unique())]


def _forward_date_text(signal_date: pd.Timestamp, trading_dates: list[pd.Timestamp], horizon: int) -> str:
    normalized = [pd.Timestamp(date).normalize() for date in trading_dates]
    date = pd.Timestamp(signal_date).normalize()
    if date not in normalized:
        return ""
    index = normalized.index(date)
    if index + horizon >= len(normalized):
        return ""
    return _date_text(normalized[index + horizon])


def _row_reason(
    *,
    candidate_generation_feasible: bool,
    blocker: str,
) -> str:
    if candidate_generation_feasible:
        return "Plan row has required warmup, forward horizons, and symbol coverage; execution still requires reviewed snapshot inputs."
    return blocker


def _candidate_generation_blocker(
    *,
    all_requested: bool,
    warmup_available: bool,
    coverage_ok: bool,
    eligible_symbol_count: int,
    request: CurrentCandidatesBackfillPlanRequest,
) -> str:
    reasons = []
    if not warmup_available:
        reasons.append(f"missing {request.warmup_trading_days} trading-day warmup coverage")
    if not all_requested:
        reasons.append("missing requested forward horizon coverage")
    if not coverage_ok:
        reasons.append(
            f"eligible_symbol_count={eligible_symbol_count} is below min_required_symbol_count={request.min_symbol_coverage}"
        )
    return "; ".join(reasons)


def _build_warnings(
    request: CurrentCandidatesBackfillPlanRequest,
    rows: list[CurrentCandidatesBackfillPlanRow],
    frame: pd.DataFrame,
) -> list[str]:
    warnings = [
        "Plan-only artifact: current-candidates were not generated.",
        "Source/upstream selections must be reviewed before execution.",
        "Forward returns are not computed by this planner.",
    ]
    if not rows:
        warnings.append("No signal dates met the requested warmup, forward-horizon, and symbol-coverage constraints.")
    if not frame.empty:
        duplicate_count = int(frame.duplicated(["symbol", "trade_date"]).sum())
        if duplicate_count:
            warnings.append(
                f"Cache contains {duplicate_count} duplicate symbol/trade_date rows in scope; counts use distinct symbols only."
            )
    if request.selection_profile == "demo":
        warnings.append("Demo selection profile is for local workflow validation only and is not a strategy recommendation.")
    return warnings


def _audit_metadata(
    request: CurrentCandidatesBackfillPlanRequest,
    frame: pd.DataFrame,
    settings: CurrentCandidatesBackfillPlanSettings,
) -> dict[str, Any]:
    return {
        "cache_row_count_in_scope": int(len(frame)),
        "cache_symbol_count_in_scope": _symbol_count(frame),
        "cache_start_date_in_scope": _date_text(frame["trade_date"].min()) if not frame.empty else "",
        "cache_end_date_in_scope": _date_text(frame["trade_date"].max()) if not frame.empty else "",
        "recommended_source_filter": _recommended_source_filter(request.source_policy),
        "recommended_upstream_filter": _recommended_upstream_filter(request.source_policy),
        "plan_only": True,
        "current_candidates_executed": False,
        "data_pipeline_executed": False,
        "cache_mutated": False,
        "network_api_called": False,
        "external_api_called": False,
        "llm_api_called": False,
        "requires_manual_review": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "auto_order_allowed": False,
        "approved_for_paper_applied": False,
        "output_dir": str(settings.output_dir),
        "config_version": settings.config_version,
    }


def _summary_dict(result: CurrentCandidatesBackfillPlanResult) -> dict[str, Any]:
    return {
        "plan_id": result.plan_id,
        "status": result.status,
        "cache_path": result.request.cache_path,
        "date_range": f"{result.request.start_date} to {result.request.end_date}",
        "universe": result.request.universe,
        "selection_profile": result.request.selection_profile,
        "horizons": ",".join(str(value) for value in result.request.horizons),
        "warmup_trading_days": result.request.warmup_trading_days,
        "selected_date_count": result.selected_date_count,
        "first_signal_date": result.first_signal_date,
        "last_signal_date": result.last_signal_date,
        "min_symbol_coverage": result.request.min_symbol_coverage,
        "source_policy": result.request.source_policy,
        "plan_csv": result.artifact_paths["plan_csv"],
    }


def _horizon_feasibility_counts(frame: pd.DataFrame, horizons: tuple[int, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for horizon in horizons:
        column = f"forward_{horizon}d_available"
        counts[column] = int(frame[column].sum()) if column in frame else 0
    return counts


def _warmup_feasibility_counts(frame: pd.DataFrame) -> dict[str, int]:
    return {
        "warmup_available": int(frame["warmup_available"].sum()) if "warmup_available" in frame else 0,
        "candidate_generation_feasible": int(frame["candidate_generation_feasible"].sum())
        if "candidate_generation_feasible" in frame
        else 0,
    }


def _warmup_available_at_index(index: int, warmup_trading_days: int) -> bool:
    return index + 1 >= _normalize_warmup_trading_days(warmup_trading_days)


def _warmup_reason(*, index: int, warmup_days: int, available: bool) -> str:
    available_count = index + 1
    if available:
        return f"Warmup window has {warmup_days} trading-day coverage through signal date."
    return f"Warmup requires {warmup_days} trading days through signal date; only {available_count} available in scoped cache."


def _recommended_source_filter(source_policy: str) -> str:
    if str(source_policy).strip().lower() == "reviewed_local_v0":
        return "AKSHARE_OPTIONAL"
    return ""


def _recommended_upstream_filter(source_policy: str) -> str:
    if str(source_policy).strip().lower() == "reviewed_local_v0":
        return "TENCENT_FOR_STOCKS;SINA_FOR_ETFS"
    return ""


def _normalize_horizons(values: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    horizons = sorted({int(value) for value in values if int(value) > 0})
    if not horizons:
        raise ValueError("At least one positive horizon is required.")
    return tuple(horizons)


def _normalize_warmup_trading_days(value: int) -> int:
    warmup = int(value)
    if warmup <= 0:
        raise ValueError("warmup_trading_days must be a positive integer.")
    return warmup


def _normalize_selection_profile(value: str) -> str:
    normalized = str(value or "demo").strip().lower()
    if normalized not in {"default", "demo"}:
        raise ValueError(f"Unsupported selection_profile: {value}")
    return normalized


def _assert_settings_safe(settings: CurrentCandidatesBackfillPlanSettings) -> None:
    if settings.enable_live_trading:
        raise ValueError("Current-candidates backfill planning cannot enable live trading.")
    if settings.enable_broker_api:
        raise ValueError("Current-candidates backfill planning cannot enable broker API access.")
    if settings.enable_message_delivery:
        raise ValueError("Current-candidates backfill planning cannot enable message delivery.")
    if settings.auto_order_allowed:
        raise ValueError("Current-candidates backfill planning cannot allow auto-order.")


def _symbol_count(frame: pd.DataFrame) -> int:
    if frame.empty or "symbol" not in frame:
        return 0
    return int(frame["symbol"].fillna("").astype(str).loc[lambda series: series != ""].nunique())


def _first_value(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame:
        return ""
    return str(frame[column].iloc[0])


def _last_value(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame:
        return ""
    return str(frame[column].iloc[-1])


def _date_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(pd.Timestamp(value).normalize().date())


def _frame_digest(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "empty"
    columns = [column for column in ["symbol", "trade_date", "source", "upstream_source"] if column in frame.columns]
    digest_frame = frame[columns].copy()
    if "trade_date" in digest_frame:
        digest_frame["trade_date"] = digest_frame["trade_date"].map(_date_text)
    encoded = digest_frame.sort_values(columns).to_csv(index=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _hash_payload(payload: dict[str, Any], *, length: int = 12) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _dict_table(values: dict[str, Any]) -> str:
    if not values:
        return "No data."
    return "\n".join(f"- {key}: {value}" for key, value in values.items())


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No rows."
    available = [column for column in columns if column in frame.columns]
    if not available:
        return "No columns."
    return frame[available].to_markdown(index=False)
