"""Compare cached market bars across local data sources."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketDataComparisonSettings, Settings, load_settings
from quant_replay_system.data import normalize_symbol_series
from quant_replay_system.market_data_cache import MARKET_CACHE_COLUMNS, load_market_cache
from quant_replay_system.market_source_policy import build_market_comparison_policy_hints


MARKET_COMPARISON_TIMESTAMP = "1970-01-01T00:00:00+00:00"

PRICE_COLUMNS = ["open", "high", "low", "close", "pre_close", "adj_factor"]
SIZE_COLUMNS = ["volume", "amount"]
COMPARISON_VALUE_COLUMNS = [*PRICE_COLUMNS, *SIZE_COLUMNS]

MARKET_COMPARISON_COLUMNS = [
    "symbol",
    "trade_date",
    "source_a",
    "source_b",
    "upstream_source_a",
    "upstream_source_b",
    "successful_function_a",
    "successful_function_b",
    "row_match_status",
    "tolerance_status",
    "tolerance_reason",
]

for _column in COMPARISON_VALUE_COLUMNS:
    MARKET_COMPARISON_COLUMNS.extend(
        [
            f"{_column}_a",
            f"{_column}_b",
            f"{_column}_diff",
            f"{_column}_diff_pct",
        ]
    )

MARKET_COMPARISON_DIAGNOSTIC_COLUMNS = [
    "volume_ratio_a_to_b",
    "amount_ratio_a_to_b",
    "close_times_volume_a",
    "close_times_volume_b",
    "amount_to_close_volume_ratio_a",
    "amount_to_close_volume_ratio_b",
    "likely_volume_unit_mismatch",
    "likely_amount_unit_mismatch",
    "likely_adjustment_or_semantic_mismatch",
    "diagnostic_reason",
]

MARKET_COMPARISON_COLUMNS.extend(MARKET_COMPARISON_DIAGNOSTIC_COLUMNS)


MARKET_COMPARISON_SUMMARY_COLUMNS = [
    "comparison_id",
    "status",
    "cache_path",
    "symbol",
    "source_a",
    "source_b",
    "start_date",
    "end_date",
    "matched_row_count",
    "source_a_only_count",
    "source_b_only_count",
    "max_close_diff_pct",
    "max_volume_diff_pct",
    "max_amount_diff_pct",
    "median_volume_ratio",
    "median_amount_ratio",
    "median_amount_to_close_volume_ratio_a",
    "median_amount_to_close_volume_ratio_b",
    "stable_volume_ratio_detected",
    "stable_amount_ratio_detected",
    "suspected_volume_scale_factor",
    "suspected_amount_scale_factor",
    "diagnostic_classification",
    "policy_security_type",
    "source_a_upstream_source",
    "source_b_upstream_source",
    "source_a_field_reliability",
    "source_b_field_reliability",
    "recommended_for_price",
    "recommended_for_volume",
    "recommended_for_amount",
    "amount_sensitive_preferred_source",
    "pre_close_caveat",
    "source_a_policy_notes",
    "source_b_policy_notes",
    "pass_count",
    "warn_count",
    "fail_count",
    "no_live_trading",
    "no_broker_api",
]


MARKET_COMPARISON_LIMITATIONS = [
    "The comparison checks cached local daily bars only.",
    "It does not certify either source as truth.",
    "Differences may reflect adjustment, unit, coverage, delay, or upstream correction semantics.",
    "Compared rows must still pass data-pipeline, data-quality, and snapshot-quality before research use.",
    "No broker API, live trading, or order automation is invoked.",
]


@dataclass(frozen=True)
class MarketDataComparisonArtifactPaths:
    artifact_dir: Path
    market_data_comparison_report: Path
    market_data_comparison_rows: Path
    market_data_comparison_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_data_comparison_report": self.market_data_comparison_report,
            "market_data_comparison_rows": self.market_data_comparison_rows,
            "market_data_comparison_summary": self.market_data_comparison_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketDataComparisonResult:
    comparison_id: str
    status: str
    cache_path: Path
    symbol: str
    source_a: str
    source_b: str
    start_date: str
    end_date: str
    comparison_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def matched_row_count(self) -> int:
        return int((self.comparison_frame["row_match_status"] == "MATCHED").sum()) if not self.comparison_frame.empty else 0

    @property
    def source_a_only_count(self) -> int:
        return int((self.comparison_frame["row_match_status"] == "SOURCE_A_ONLY").sum()) if not self.comparison_frame.empty else 0

    @property
    def source_b_only_count(self) -> int:
        return int((self.comparison_frame["row_match_status"] == "SOURCE_B_ONLY").sum()) if not self.comparison_frame.empty else 0

    @property
    def pass_count(self) -> int:
        return int((self.comparison_frame["tolerance_status"] == "PASS").sum()) if not self.comparison_frame.empty else 0

    @property
    def warn_count(self) -> int:
        return int((self.comparison_frame["tolerance_status"] == "WARN").sum()) if not self.comparison_frame.empty else 0

    @property
    def fail_count(self) -> int:
        return int((self.comparison_frame["tolerance_status"] == "FAIL").sum()) if not self.comparison_frame.empty else 0


def run_market_source_comparison(
    *,
    symbol: str,
    source_a: str,
    source_b: str,
    start_date: str | None = None,
    end_date: str | None = None,
    cache_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    config: Settings | MarketDataComparisonSettings | dict[str, Any] | None = None,
) -> MarketDataComparisonResult:
    """Compare one cached symbol between two data sources and write artifacts."""

    project_settings, comparison_settings = _resolve_settings(config)
    if comparison_settings.enable_live_trading or comparison_settings.enable_broker_api:
        raise ValueError("Market data comparison cannot enable live trading or broker API access")

    path = Path(cache_path) if cache_path is not None else project_settings.market_data_cache.cache_path
    if not path.exists():
        raise FileNotFoundError(f"Market cache file not found: {path}")

    normalized_symbol = _normalize_symbol(symbol)
    normalized_source_a = _normalize_source(source_a)
    normalized_source_b = _normalize_source(source_b)
    cache_frame = load_market_comparison_inputs(
        cache_path=path,
        symbol=normalized_symbol,
        start_date=start_date,
        end_date=end_date,
        config=project_settings,
    )
    comparison_frame = build_market_source_comparison_frame(
        cache_frame,
        symbol=normalized_symbol,
        source_a=normalized_source_a,
        source_b=normalized_source_b,
        settings=comparison_settings,
    )
    comparison_id = generate_market_source_comparison_id(
        symbol=normalized_symbol,
        source_a=normalized_source_a,
        source_b=normalized_source_b,
        start_date=start_date,
        end_date=end_date,
        cache_path=path,
        settings=comparison_settings,
    )
    summary_frame = summarize_market_source_comparison(
        comparison_frame,
        comparison_id=comparison_id,
        cache_path=path,
        symbol=normalized_symbol,
        source_a=normalized_source_a,
        source_b=normalized_source_b,
        start_date=start_date or "",
        end_date=end_date or "",
        settings=comparison_settings,
        policy_config=project_settings,
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    artifact_paths = resolve_market_source_comparison_artifact_paths(
        Path(output_dir) if output_dir is not None else comparison_settings.output_dir,
        comparison_id,
    )
    warnings = _comparison_warnings(comparison_frame)
    result = MarketDataComparisonResult(
        comparison_id=comparison_id,
        status=status,
        cache_path=path,
        symbol=normalized_symbol,
        source_a=normalized_source_a,
        source_b=normalized_source_b,
        start_date=start_date or "",
        end_date=end_date or "",
        comparison_frame=comparison_frame,
        summary_frame=summary_frame,
        artifact_paths=artifact_paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_COMPARISON_LIMITATIONS,
        audit_metadata={
            "comparison_id": comparison_id,
            "operation": "market_source_comparison",
            "cache_path": path,
            "symbol": normalized_symbol,
            "source_a": normalized_source_a,
            "source_b": normalized_source_b,
            "start_date": start_date or "",
            "end_date": end_date or "",
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "market_data_comparison_only": True,
            "network_api_calls_used_in_tests": False,
            "config_version": comparison_settings.config_version,
        },
    )
    if comparison_settings.write_artifacts:
        write_market_source_comparison_artifacts(result)
    return result


def load_market_comparison_inputs(
    *,
    cache_path: str | Path,
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    config: Settings | None = None,
) -> pd.DataFrame:
    """Load and filter cache rows for one symbol/date range."""

    frame = load_market_cache(cache_path, config=config)
    if frame.empty:
        return pd.DataFrame(columns=MARKET_CACHE_COLUMNS)
    normalized_symbol = _normalize_symbol(symbol)
    output = frame.loc[frame["symbol"] == normalized_symbol].copy()
    if start_date:
        start = pd.to_datetime(start_date, errors="raise").normalize()
        output = output.loc[pd.to_datetime(output["trade_date"], errors="coerce") >= start]
    if end_date:
        end = pd.to_datetime(end_date, errors="raise").normalize()
        output = output.loc[pd.to_datetime(output["trade_date"], errors="coerce") <= end]
    return output.reset_index(drop=True)


def build_market_source_comparison_frame(
    cache_frame: pd.DataFrame,
    *,
    symbol: str,
    source_a: str,
    source_b: str,
    settings: MarketDataComparisonSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build a row-level source comparison frame from cached market rows."""

    comparison_settings = _coerce_comparison_settings(settings)
    if cache_frame.empty:
        return pd.DataFrame(columns=MARKET_COMPARISON_COLUMNS)
    normalized_symbol = _normalize_symbol(symbol)
    normalized_source_a = _normalize_source(source_a)
    normalized_source_b = _normalize_source(source_b)
    frame = cache_frame.copy(deep=True)
    frame["symbol"] = normalize_symbol_series(frame["symbol"])
    frame["source"] = frame["source"].map(_normalize_source)
    frame = frame.loc[frame["symbol"] == normalized_symbol].copy()
    left = _comparison_side_frame(frame, source=normalized_source_a, side="a")
    right = _comparison_side_frame(frame, source=normalized_source_b, side="b")
    merged = pd.merge(left, right, on=["symbol", "trade_date"], how="outer")
    if merged.empty:
        return pd.DataFrame(columns=MARKET_COMPARISON_COLUMNS)
    merged["source_a"] = merged.get("source_a", "").fillna("")
    merged["source_b"] = merged.get("source_b", "").fillna("")
    has_a = merged["source_a"].astype(str).str.strip().ne("")
    has_b = merged["source_b"].astype(str).str.strip().ne("")
    merged["row_match_status"] = "MATCHED"
    merged.loc[has_a & ~has_b, "row_match_status"] = "SOURCE_A_ONLY"
    merged.loc[~has_a & has_b, "row_match_status"] = "SOURCE_B_ONLY"
    for column in ["upstream_source_a", "upstream_source_b", "successful_function_a", "successful_function_b"]:
        if column not in merged.columns:
            merged[column] = ""
        merged[column] = merged[column].fillna("")
    for metric in COMPARISON_VALUE_COLUMNS:
        _add_metric_diff_columns(merged, metric)
    _add_unit_diagnostic_columns(merged, comparison_settings)
    statuses = merged.apply(lambda row: _tolerance_status(row, comparison_settings), axis=1)
    merged["tolerance_status"] = [status for status, _reason in statuses]
    merged["tolerance_reason"] = [reason for _status, reason in statuses]
    for column in MARKET_COMPARISON_COLUMNS:
        if column not in merged.columns:
            merged[column] = ""
    return merged[MARKET_COMPARISON_COLUMNS].sort_values(["symbol", "trade_date"]).reset_index(drop=True)


def summarize_market_source_comparison(
    comparison_frame: pd.DataFrame,
    *,
    comparison_id: str,
    cache_path: Path,
    symbol: str,
    source_a: str,
    source_b: str,
    start_date: str,
    end_date: str,
    settings: MarketDataComparisonSettings | dict[str, Any] | None = None,
    policy_config: Settings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    comparison_settings = _coerce_comparison_settings(settings)
    frame = comparison_frame.copy(deep=True)
    if frame.empty:
        matched = source_a_only = source_b_only = pass_count = warn_count = fail_count = 0
        max_close = max_volume = max_amount = 0.0
    else:
        matched = int((frame["row_match_status"] == "MATCHED").sum())
        source_a_only = int((frame["row_match_status"] == "SOURCE_A_ONLY").sum())
        source_b_only = int((frame["row_match_status"] == "SOURCE_B_ONLY").sum())
        pass_count = int((frame["tolerance_status"] == "PASS").sum())
        warn_count = int((frame["tolerance_status"] == "WARN").sum())
        fail_count = int((frame["tolerance_status"] == "FAIL").sum())
        max_close = _max_abs_numeric(frame.get("close_diff_pct", pd.Series(dtype="float64")))
        max_volume = _max_abs_numeric(frame.get("volume_diff_pct", pd.Series(dtype="float64")))
        max_amount = _max_abs_numeric(frame.get("amount_diff_pct", pd.Series(dtype="float64")))
    unit_summary = _summarize_unit_diagnostics(frame, comparison_settings)
    policy_hints = build_market_comparison_policy_hints(
        frame,
        symbol=symbol,
        source_a=source_a,
        source_b=source_b,
        config=policy_config,
    )
    status = "FAIL" if fail_count else "WARN" if warn_count else "PASS"
    return pd.DataFrame(
        [
            {
                "comparison_id": comparison_id,
                "status": status,
                "cache_path": str(cache_path),
                "symbol": symbol,
                "source_a": source_a,
                "source_b": source_b,
                "start_date": start_date,
                "end_date": end_date,
                "matched_row_count": matched,
                "source_a_only_count": source_a_only,
                "source_b_only_count": source_b_only,
                "max_close_diff_pct": max_close,
                "max_volume_diff_pct": max_volume,
                "max_amount_diff_pct": max_amount,
                **unit_summary,
                **policy_hints,
                "pass_count": pass_count,
                "warn_count": warn_count,
                "fail_count": fail_count,
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ],
        columns=MARKET_COMPARISON_SUMMARY_COLUMNS,
    )


def write_market_source_comparison_artifacts(result: MarketDataComparisonResult) -> dict[str, Path]:
    paths = MarketDataComparisonArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.comparison_frame.to_csv(paths.market_data_comparison_rows, index=False)
    result.summary_frame.to_csv(paths.market_data_comparison_summary, index=False)
    paths.market_data_comparison_report.write_text(render_market_source_comparison_report(result), encoding="utf-8")
    metadata = {
        "comparison_id": result.comparison_id,
        "status": result.status,
        "cache_path": str(result.cache_path),
        "symbol": result.symbol,
        "source_a": result.source_a,
        "source_b": result.source_b,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "summary": result.summary_frame.to_dict("records"),
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "policy_hints": result.summary_frame[
            [
                "policy_security_type",
                "source_a_field_reliability",
                "source_b_field_reliability",
                "recommended_for_price",
                "recommended_for_volume",
                "recommended_for_amount",
                "amount_sensitive_preferred_source",
                "pre_close_caveat",
            ]
        ].to_dict("records")
        if not result.summary_frame.empty
        else [],
        "created_at": MARKET_COMPARISON_TIMESTAMP,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths.as_dict()


def render_market_source_comparison_report(result: MarketDataComparisonResult) -> str:
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    lines = [
        "# Market Data Source Comparison",
        "",
        f"- comparison_id: {result.comparison_id}",
        f"- status: {result.status}",
        f"- cache_path: {result.cache_path}",
        f"- symbol: {result.symbol}",
        f"- source_a: {result.source_a}",
        f"- source_b: {result.source_b}",
        f"- matched_row_count: {summary.get('matched_row_count', 0)}",
        f"- source_a_only_count: {summary.get('source_a_only_count', 0)}",
        f"- source_b_only_count: {summary.get('source_b_only_count', 0)}",
        f"- max_close_diff_pct: {summary.get('max_close_diff_pct', 0)}",
        f"- max_volume_diff_pct: {summary.get('max_volume_diff_pct', 0)}",
        f"- max_amount_diff_pct: {summary.get('max_amount_diff_pct', 0)}",
        f"- diagnostic_classification: {summary.get('diagnostic_classification', 'NO_UNIT_MISMATCH')}",
        f"- median_volume_ratio: {summary.get('median_volume_ratio', '')}",
        f"- median_amount_ratio: {summary.get('median_amount_ratio', '')}",
        f"- suspected_volume_scale_factor: {summary.get('suspected_volume_scale_factor', '')}",
        f"- suspected_amount_scale_factor: {summary.get('suspected_amount_scale_factor', '')}",
        f"- policy_security_type: {summary.get('policy_security_type', '')}",
        f"- recommended_for_price: {summary.get('recommended_for_price', '')}",
        f"- recommended_for_volume: {summary.get('recommended_for_volume', '')}",
        f"- recommended_for_amount: {summary.get('recommended_for_amount', '')}",
        f"- amount_sensitive_preferred_source: {summary.get('amount_sensitive_preferred_source', '')}",
        f"- pre_close_caveat: {summary.get('pre_close_caveat', '')}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Summary",
        "",
        result.summary_frame.to_markdown(index=False) if not result.summary_frame.empty else "No comparison rows.",
        "",
        "## Unit And Semantic Diagnostics",
        "",
        "- `volume_ratio_a_to_b` and `amount_ratio_a_to_b` are source A divided by source B.",
        "- Stable ratios far from 1.0 can indicate a possible source-specific unit scale.",
        "- Unstable ratios with matched prices are reported as source semantics differences, not corrected automatically.",
        "- Diagnostics do not choose a trusted source or mutate cached data.",
        "",
        "## Source Field Reliability Policy Hints",
        "",
        f"- security_type: {summary.get('policy_security_type', '')}",
        f"- source_a_upstream_source: {summary.get('source_a_upstream_source', '')}",
        f"- source_b_upstream_source: {summary.get('source_b_upstream_source', '')}",
        f"- source_a_field_reliability: {summary.get('source_a_field_reliability', '')}",
        f"- source_b_field_reliability: {summary.get('source_b_field_reliability', '')}",
        f"- recommended_for_price: {summary.get('recommended_for_price', '')}",
        f"- recommended_for_volume: {summary.get('recommended_for_volume', '')}",
        f"- recommended_for_amount: {summary.get('recommended_for_amount', '')}",
        f"- amount_sensitive_preferred_source: {summary.get('amount_sensitive_preferred_source', '')}",
        f"- pre_close_caveat: {summary.get('pre_close_caveat', '')}",
        f"- source_a_policy_notes: {summary.get('source_a_policy_notes', '')}",
        f"- source_b_policy_notes: {summary.get('source_b_policy_notes', '')}",
        "",
        "Policy hints are field-level research data preparation guidance. They do not override comparison tolerances, data quality, or snapshot quality gates.",
        "",
        _render_top_difference_rows(result.comparison_frame),
        "",
        "## Interpretation Notes",
        "",
        "- Large price differences may indicate adjustment or ex-rights handling differences.",
        "- Large volume or amount differences may indicate unit, source, or upstream semantics differences.",
        "- Source-only rows indicate date coverage gaps and should be reviewed before building snapshots.",
        "- This report compares sources; it does not certify either source as truth.",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def resolve_market_source_comparison_artifact_paths(
    output_dir: str | Path,
    comparison_id: str,
) -> MarketDataComparisonArtifactPaths:
    artifact_dir = Path(output_dir) / comparison_id
    return MarketDataComparisonArtifactPaths(
        artifact_dir=artifact_dir,
        market_data_comparison_report=artifact_dir / "market_data_comparison_report.md",
        market_data_comparison_rows=artifact_dir / "market_data_comparison_rows.csv",
        market_data_comparison_summary=artifact_dir / "market_data_comparison_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def generate_market_source_comparison_id(
    *,
    symbol: str,
    source_a: str,
    source_b: str,
    start_date: str | None,
    end_date: str | None,
    cache_path: str | Path,
    settings: MarketDataComparisonSettings,
) -> str:
    payload = {
        "symbol": symbol,
        "source_a": source_a,
        "source_b": source_b,
        "start_date": start_date or "",
        "end_date": end_date or "",
        "cache_path": str(cache_path),
        "config_version": settings.config_version,
        "price_abs_tolerance": settings.price_abs_tolerance,
        "price_pct_tolerance": settings.price_pct_tolerance,
        "volume_pct_tolerance": settings.volume_pct_tolerance,
        "amount_pct_tolerance": settings.amount_pct_tolerance,
        "unit_ratio_stability_tolerance": settings.unit_ratio_stability_tolerance,
        "unit_ratio_far_from_one_tolerance": settings.unit_ratio_far_from_one_tolerance,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _comparison_side_frame(frame: pd.DataFrame, *, source: str, side: str) -> pd.DataFrame:
    selected = frame.loc[frame["source"] == source].copy()
    columns = ["symbol", "trade_date", f"source_{side}", f"upstream_source_{side}", f"successful_function_{side}"]
    for metric in COMPARISON_VALUE_COLUMNS:
        columns.append(f"{metric}_{side}")
    if selected.empty:
        return pd.DataFrame(columns=columns)
    selected = selected.sort_values(
        ["symbol", "trade_date", "source", "upstream_source", "successful_function", "revision_id", "cache_ingested_at"]
    )
    selected = selected.drop_duplicates(subset=["symbol", "trade_date", "source"], keep="last")
    output = pd.DataFrame(
        {
            "symbol": selected["symbol"],
            "trade_date": selected["trade_date"],
            f"source_{side}": selected["source"],
            f"upstream_source_{side}": selected["upstream_source"],
            f"successful_function_{side}": selected["successful_function"],
        }
    )
    for metric in COMPARISON_VALUE_COLUMNS:
        output[f"{metric}_{side}"] = pd.to_numeric(selected.get(metric, pd.Series(dtype="float64")), errors="coerce")
    return output.reset_index(drop=True)


def _add_metric_diff_columns(frame: pd.DataFrame, metric: str) -> None:
    left = pd.to_numeric(frame.get(f"{metric}_a", pd.Series(index=frame.index, dtype="float64")), errors="coerce")
    right = pd.to_numeric(frame.get(f"{metric}_b", pd.Series(index=frame.index, dtype="float64")), errors="coerce")
    diff = left - right
    frame[f"{metric}_a"] = left
    frame[f"{metric}_b"] = right
    frame[f"{metric}_diff"] = diff
    frame[f"{metric}_diff_pct"] = [_diff_pct(a, b) for a, b in zip(left, right)]


def _add_unit_diagnostic_columns(frame: pd.DataFrame, settings: MarketDataComparisonSettings) -> None:
    volume_a = pd.to_numeric(frame.get("volume_a", pd.Series(index=frame.index, dtype="float64")), errors="coerce")
    volume_b = pd.to_numeric(frame.get("volume_b", pd.Series(index=frame.index, dtype="float64")), errors="coerce")
    amount_a = pd.to_numeric(frame.get("amount_a", pd.Series(index=frame.index, dtype="float64")), errors="coerce")
    amount_b = pd.to_numeric(frame.get("amount_b", pd.Series(index=frame.index, dtype="float64")), errors="coerce")
    close_a = pd.to_numeric(frame.get("close_a", pd.Series(index=frame.index, dtype="float64")), errors="coerce")
    close_b = pd.to_numeric(frame.get("close_b", pd.Series(index=frame.index, dtype="float64")), errors="coerce")

    frame["volume_ratio_a_to_b"] = [_safe_ratio(a, b) for a, b in zip(volume_a, volume_b)]
    frame["amount_ratio_a_to_b"] = [_safe_ratio(a, b) for a, b in zip(amount_a, amount_b)]
    frame["close_times_volume_a"] = close_a * volume_a
    frame["close_times_volume_b"] = close_b * volume_b
    frame["amount_to_close_volume_ratio_a"] = [
        _safe_ratio(amount, close_volume) for amount, close_volume in zip(amount_a, frame["close_times_volume_a"])
    ]
    frame["amount_to_close_volume_ratio_b"] = [
        _safe_ratio(amount, close_volume) for amount, close_volume in zip(amount_b, frame["close_times_volume_b"])
    ]

    diagnostics = frame.apply(lambda row: _row_unit_diagnostics(row, settings), axis=1)
    frame["likely_volume_unit_mismatch"] = [item["likely_volume_unit_mismatch"] for item in diagnostics]
    frame["likely_amount_unit_mismatch"] = [item["likely_amount_unit_mismatch"] for item in diagnostics]
    frame["likely_adjustment_or_semantic_mismatch"] = [
        item["likely_adjustment_or_semantic_mismatch"] for item in diagnostics
    ]
    frame["diagnostic_reason"] = [item["diagnostic_reason"] for item in diagnostics]


def _tolerance_status(row: pd.Series, settings: MarketDataComparisonSettings) -> tuple[str, str]:
    match_status = str(row.get("row_match_status", ""))
    if match_status == "SOURCE_A_ONLY":
        return "WARN", "Date exists only in source A."
    if match_status == "SOURCE_B_ONLY":
        return "WARN", "Date exists only in source B."
    if match_status != "MATCHED":
        return "WARN", "Row match status is unknown."

    price_failures: list[str] = []
    for metric in PRICE_COLUMNS:
        abs_diff = abs(_float_or_zero(row.get(f"{metric}_diff")))
        pct_diff = abs(_float_or_zero(row.get(f"{metric}_diff_pct")))
        if abs_diff > settings.price_abs_tolerance and pct_diff > settings.price_pct_tolerance:
            price_failures.append(metric)
    size_failures: list[str] = []
    volume_pct = abs(_float_or_zero(row.get("volume_diff_pct")))
    amount_pct = abs(_float_or_zero(row.get("amount_diff_pct")))
    if volume_pct > settings.volume_pct_tolerance:
        size_failures.append("volume")
    if amount_pct > settings.amount_pct_tolerance:
        size_failures.append("amount")
    failures = [*price_failures, *size_failures]
    if failures:
        return "FAIL", f"Tolerance exceeded for: {', '.join(failures)}."
    return "PASS", "All compared values are within tolerance."


def _row_unit_diagnostics(row: pd.Series, settings: MarketDataComparisonSettings) -> dict[str, Any]:
    match_status = str(row.get("row_match_status", ""))
    if match_status != "MATCHED":
        return {
            "likely_volume_unit_mismatch": False,
            "likely_amount_unit_mismatch": False,
            "likely_adjustment_or_semantic_mismatch": False,
            "diagnostic_reason": "Source-only row; unit diagnostics require both sources.",
        }

    close_abs_diff = abs(_float_or_zero(row.get("close_diff")))
    close_pct_diff = abs(_float_or_zero(row.get("close_diff_pct")))
    close_matches = close_abs_diff <= settings.price_abs_tolerance or close_pct_diff <= settings.price_pct_tolerance
    volume_ratio = _float_or_nan(row.get("volume_ratio_a_to_b"))
    amount_ratio = _float_or_nan(row.get("amount_ratio_a_to_b"))
    amount_semantic_ratio = _safe_ratio(
        row.get("amount_to_close_volume_ratio_a"),
        row.get("amount_to_close_volume_ratio_b"),
    )
    volume_far = _ratio_far_from_one(volume_ratio, settings)
    amount_far = _ratio_far_from_one(amount_ratio, settings)
    semantic_far = _ratio_far_from_one(amount_semantic_ratio, settings)
    likely_volume = close_matches and volume_far
    likely_amount = close_matches and amount_far
    likely_semantic = (not close_matches and (volume_far or amount_far)) or semantic_far

    reasons: list[str] = []
    if close_matches and (likely_volume or likely_amount):
        reasons.append("Close prices match while size fields differ.")
    if likely_volume:
        reasons.append(f"Volume ratio A/B={_format_diagnostic_float(volume_ratio)} is far from 1.0.")
    if likely_amount:
        reasons.append(f"Amount ratio A/B={_format_diagnostic_float(amount_ratio)} is far from 1.0.")
    if semantic_far:
        reasons.append(
            "Amount divided by close*volume differs between sources "
            f"(ratio A/B={_format_diagnostic_float(amount_semantic_ratio)})."
        )
    if not reasons:
        reasons.append("No unit or semantic mismatch detected.")

    return {
        "likely_volume_unit_mismatch": bool(likely_volume),
        "likely_amount_unit_mismatch": bool(likely_amount),
        "likely_adjustment_or_semantic_mismatch": bool(likely_semantic),
        "diagnostic_reason": " ".join(reasons),
    }


def _summarize_unit_diagnostics(
    frame: pd.DataFrame,
    settings: MarketDataComparisonSettings,
) -> dict[str, Any]:
    defaults = {
        "median_volume_ratio": float("nan"),
        "median_amount_ratio": float("nan"),
        "median_amount_to_close_volume_ratio_a": float("nan"),
        "median_amount_to_close_volume_ratio_b": float("nan"),
        "stable_volume_ratio_detected": False,
        "stable_amount_ratio_detected": False,
        "suspected_volume_scale_factor": float("nan"),
        "suspected_amount_scale_factor": float("nan"),
        "diagnostic_classification": "INSUFFICIENT_OVERLAP",
    }
    if frame.empty or "row_match_status" not in frame.columns:
        return defaults

    matched = frame.loc[frame["row_match_status"] == "MATCHED"].copy()
    if matched.empty:
        return defaults

    median_volume_ratio = _median_finite(matched.get("volume_ratio_a_to_b", pd.Series(dtype="float64")))
    median_amount_ratio = _median_finite(matched.get("amount_ratio_a_to_b", pd.Series(dtype="float64")))
    median_amount_to_close_volume_ratio_a = _median_finite(
        matched.get("amount_to_close_volume_ratio_a", pd.Series(dtype="float64"))
    )
    median_amount_to_close_volume_ratio_b = _median_finite(
        matched.get("amount_to_close_volume_ratio_b", pd.Series(dtype="float64"))
    )
    stable_volume_ratio = _stable_ratio_detected(
        matched.get("volume_ratio_a_to_b", pd.Series(dtype="float64")),
        settings,
    )
    stable_amount_ratio = _stable_ratio_detected(
        matched.get("amount_ratio_a_to_b", pd.Series(dtype="float64")),
        settings,
    )
    volume_far = _ratio_far_from_one(median_volume_ratio, settings)
    amount_far = _ratio_far_from_one(median_amount_ratio, settings)
    usable_volume_scale = stable_volume_ratio and volume_far and _is_positive_finite(median_volume_ratio)
    usable_amount_scale = stable_amount_ratio and amount_far and _is_positive_finite(median_amount_ratio)
    suspected_volume_scale_factor = median_volume_ratio if usable_volume_scale else float("nan")
    suspected_amount_scale_factor = median_amount_ratio if usable_amount_scale else float("nan")
    close_match_share = _share_close_matches(matched, settings)
    volume_mismatch_rows = int(
        matched.get("likely_volume_unit_mismatch", pd.Series(dtype="bool")).fillna(False).astype(bool).sum()
    )
    amount_mismatch_rows = int(
        matched.get("likely_amount_unit_mismatch", pd.Series(dtype="bool")).fillna(False).astype(bool).sum()
    )
    volume_or_amount_mismatch = volume_mismatch_rows > 0 or amount_mismatch_rows > 0

    if not volume_or_amount_mismatch:
        classification = "NO_UNIT_MISMATCH"
    elif close_match_share >= 0.80 and usable_volume_scale and usable_amount_scale:
        classification = "PRICE_MATCH_VOLUME_AMOUNT_MISMATCH"
    elif close_match_share >= 0.80 and usable_volume_scale:
        classification = "VOLUME_UNIT_MISMATCH"
    elif close_match_share >= 0.80 and usable_amount_scale:
        classification = "AMOUNT_UNIT_MISMATCH"
    elif close_match_share >= 0.80:
        classification = "SOURCE_SEMANTICS_DIFFER"
    else:
        classification = "SOURCE_SEMANTICS_DIFFER"

    return {
        "median_volume_ratio": median_volume_ratio,
        "median_amount_ratio": median_amount_ratio,
        "median_amount_to_close_volume_ratio_a": median_amount_to_close_volume_ratio_a,
        "median_amount_to_close_volume_ratio_b": median_amount_to_close_volume_ratio_b,
        "stable_volume_ratio_detected": bool(stable_volume_ratio and volume_far),
        "stable_amount_ratio_detected": bool(stable_amount_ratio and amount_far),
        "suspected_volume_scale_factor": suspected_volume_scale_factor,
        "suspected_amount_scale_factor": suspected_amount_scale_factor,
        "diagnostic_classification": classification,
    }


def _diff_pct(left: Any, right: Any) -> float:
    if pd.isna(left) or pd.isna(right):
        return float("nan")
    a = float(left)
    b = float(right)
    diff = abs(a - b)
    denominator = abs(a) if abs(a) > 0 else abs(b)
    if denominator == 0:
        return 0.0 if diff == 0 else float("inf")
    return diff / denominator


def _safe_ratio(left: Any, right: Any) -> float:
    a = _float_or_nan(left)
    b = _float_or_nan(right)
    if not math.isfinite(a) or not math.isfinite(b):
        return float("nan")
    if b == 0:
        return 1.0 if a == 0 else float("inf")
    return a / b


def _float_or_nan(value: Any) -> float:
    try:
        if pd.isna(value):
            return float("nan")
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _ratio_far_from_one(value: Any, settings: MarketDataComparisonSettings) -> bool:
    ratio = _float_or_nan(value)
    return math.isfinite(ratio) and abs(ratio - 1.0) > settings.unit_ratio_far_from_one_tolerance


def _is_positive_finite(value: Any) -> bool:
    parsed = _float_or_nan(value)
    return math.isfinite(parsed) and parsed > 0


def _median_finite(series: pd.Series) -> float:
    values = _finite_float_values(series)
    if not values:
        return float("nan")
    return float(pd.Series(values, dtype="float64").median())


def _stable_ratio_detected(series: pd.Series, settings: MarketDataComparisonSettings) -> bool:
    values = _finite_float_values(series)
    if len(values) < 2:
        return False
    median = float(pd.Series(values, dtype="float64").median())
    if abs(median) < 1e-12:
        return max(abs(value - median) for value in values) <= settings.unit_ratio_stability_tolerance
    relative_deviations = [abs(value - median) / abs(median) for value in values]
    return max(relative_deviations) <= settings.unit_ratio_stability_tolerance


def _finite_float_values(series: pd.Series) -> list[float]:
    values: list[float] = []
    for value in pd.to_numeric(series, errors="coerce"):
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(parsed):
            values.append(parsed)
    return values


def _share_close_matches(frame: pd.DataFrame, settings: MarketDataComparisonSettings) -> float:
    if frame.empty:
        return 0.0
    matches = []
    for _index, row in frame.iterrows():
        abs_diff = abs(_float_or_zero(row.get("close_diff")))
        pct_diff = abs(_float_or_zero(row.get("close_diff_pct")))
        matches.append(abs_diff <= settings.price_abs_tolerance or pct_diff <= settings.price_pct_tolerance)
    return sum(1 for item in matches if item) / len(matches)


def _format_diagnostic_float(value: Any) -> str:
    parsed = _float_or_nan(value)
    if not math.isfinite(parsed):
        return "n/a"
    return f"{parsed:.6g}"


def _render_top_difference_rows(frame: pd.DataFrame, limit: int = 10) -> str:
    if frame.empty:
        return "No comparison rows."
    matched = frame.loc[frame["row_match_status"] == "MATCHED"].copy()
    if matched.empty:
        return "No matched rows for unit diagnostics."
    matched["_largest_size_diff_pct"] = matched[["volume_diff_pct", "amount_diff_pct"]].apply(
        lambda row: max(
            abs(_float_or_zero(row.get("volume_diff_pct"))),
            abs(_float_or_zero(row.get("amount_diff_pct"))),
        ),
        axis=1,
    )
    columns = [
        "symbol",
        "trade_date",
        "upstream_source_a",
        "upstream_source_b",
        "close_diff_pct",
        "volume_diff_pct",
        "amount_diff_pct",
        "volume_ratio_a_to_b",
        "amount_ratio_a_to_b",
        "diagnostic_reason",
    ]
    rows = matched.sort_values("_largest_size_diff_pct", ascending=False).head(limit)
    return rows[columns].to_markdown(index=False)


def _comparison_warnings(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return ["No comparison rows were produced."]
    warnings: list[str] = []
    source_only = frame[frame["row_match_status"].isin(["SOURCE_A_ONLY", "SOURCE_B_ONLY"])]
    if not source_only.empty:
        warnings.append(f"{len(source_only)} cache rows exist in only one source.")
    failures = frame[frame["tolerance_status"] == "FAIL"]
    if not failures.empty:
        warnings.append(f"{len(failures)} matched rows exceed comparison tolerances.")
    return warnings


def _max_abs_numeric(series: pd.Series) -> float:
    parsed = pd.to_numeric(series, errors="coerce").abs()
    parsed = parsed.replace([float("inf")], pd.NA).dropna()
    if parsed.empty:
        return 0.0
    return float(parsed.max())


def _normalize_symbol(symbol: str) -> str:
    return normalize_symbol_series(pd.Series([symbol])).iloc[0]


def _normalize_source(source: str) -> str:
    return str(source or "").strip().upper()


def _coerce_comparison_settings(
    settings: MarketDataComparisonSettings | dict[str, Any] | None,
) -> MarketDataComparisonSettings:
    if settings is None:
        return load_settings(Path("config/default.yaml")).market_data_comparison
    if isinstance(settings, MarketDataComparisonSettings):
        return settings
    if isinstance(settings, dict):
        base = load_settings(Path("config/default.yaml")).market_data_comparison.model_dump()
        base.update(settings)
        return MarketDataComparisonSettings(**base)
    raise TypeError("settings must be MarketDataComparisonSettings, dict, or None")


def _resolve_settings(
    config: Settings | MarketDataComparisonSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketDataComparisonSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.market_data_comparison
    if isinstance(config, Settings):
        return config, config.market_data_comparison
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, MarketDataComparisonSettings):
        return project, config
    if isinstance(config, dict):
        comparison_payload = dict(project.market_data_comparison.model_dump())
        project_updates: dict[str, Any] = {}
        for key, value in config.items():
            if key == "market_data_comparison" and isinstance(value, dict):
                comparison_payload.update(value)
            elif key == "market_data_cache" and isinstance(value, dict):
                project_updates["market_data_cache"] = project.market_data_cache.model_copy(update=value)
            elif key in comparison_payload:
                comparison_payload[key] = value
        if project_updates:
            project = project.model_copy(update=project_updates)
        return project, MarketDataComparisonSettings(**comparison_payload)
    raise TypeError("config must be Settings, MarketDataComparisonSettings, dict, or None")


def _float_or_zero(value: Any) -> float:
    try:
        if pd.isna(value):
            return 0.0
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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
