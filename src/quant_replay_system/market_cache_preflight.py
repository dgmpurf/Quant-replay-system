"""Source-policy-aware preflight checks before market cache ingestion."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketCachePreflightSettings, Settings, load_settings
from quant_replay_system.data import normalize_symbol_series, read_csv_preserve_symbol_columns
from quant_replay_system.market_data_cache import (
    CACHE_TIMESTAMP,
    INPUT_REQUIRED_COLUMNS,
    MARKET_CACHE_COLUMNS,
    load_market_cache,
)
from quant_replay_system.market_data_comparison import (
    build_market_source_comparison_frame,
    generate_market_source_comparison_id,
    summarize_market_source_comparison,
)
from quant_replay_system.market_source_policy import (
    MarketFieldReliability,
    get_market_field_reliability,
    infer_market_security_type,
)


MARKET_CACHE_PREFLIGHT_TIMESTAMP = "1970-01-01T00:00:00+00:00"

MARKET_CACHE_PREFLIGHT_LIMITATIONS = [
    "The preflight checks candidate local market rows before cache ingestion.",
    "The preflight does not mutate data/cache or ingest rows.",
    "ACCEPT or WARN_ACCEPT is not strategy data certification.",
    "Accepted rows must still pass data-pipeline, data-quality, and snapshot-quality before research use.",
    "No broker API, live trading, or order automation is invoked.",
]

PREFLIGHT_ISSUE_COLUMNS = [
    "category",
    "severity",
    "field",
    "symbol",
    "trade_date",
    "message",
    "decision_impact",
    "no_live_trading",
    "no_broker_api",
]

PREFLIGHT_SUMMARY_COLUMNS = [
    "preflight_id",
    "status",
    "input_path",
    "metadata_path",
    "source",
    "upstream_source",
    "successful_function",
    "security_type",
    "symbol",
    "start_date",
    "end_date",
    "row_count",
    "required_fields",
    "reference_source",
    "comparison_status",
    "comparison_id",
    "issue_count",
    "warning_count",
    "error_count",
    "known_caveat_count",
    "no_live_trading",
    "no_broker_api",
]


class MarketCachePreflightDecision(str, Enum):
    ACCEPT = "ACCEPT"
    WARN_ACCEPT = "WARN_ACCEPT"
    REJECT = "REJECT"


@dataclass(frozen=True)
class MarketCachePreflightIssue:
    category: str
    severity: str
    field: str
    symbol: str
    trade_date: str
    message: str
    decision_impact: str
    no_live_trading: bool = True
    no_broker_api: bool = True

    def as_row(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "field": self.field,
            "symbol": self.symbol,
            "trade_date": self.trade_date,
            "message": self.message,
            "decision_impact": self.decision_impact,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
        }


@dataclass(frozen=True)
class MarketCachePreflightArtifactPaths:
    artifact_dir: Path
    market_cache_preflight_report: Path
    market_cache_preflight_issues: Path
    market_cache_preflight_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_cache_preflight_report": self.market_cache_preflight_report,
            "market_cache_preflight_issues": self.market_cache_preflight_issues,
            "market_cache_preflight_summary": self.market_cache_preflight_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketCachePreflightResult:
    preflight_id: str
    status: str
    input_path: Path
    metadata_path: Path | None
    candidate_frame: pd.DataFrame
    issues_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    comparison_frame: pd.DataFrame
    comparison_summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def row_count(self) -> int:
        return len(self.candidate_frame)

    @property
    def issue_count(self) -> int:
        return len(self.issues_frame)

    @property
    def warning_count(self) -> int:
        if self.issues_frame.empty:
            return 0
        return int((self.issues_frame["severity"] == "WARN").sum())

    @property
    def error_count(self) -> int:
        if self.issues_frame.empty:
            return 0
        return int((self.issues_frame["severity"] == "ERROR").sum())


def run_market_cache_preflight(
    input_path: str | Path,
    *,
    metadata_path: str | Path | None = None,
    health_metadata_path: str | Path | None = None,
    reference_source: str | None = None,
    cache_path: str | Path | None = None,
    required_fields: list[str] | str | None = None,
    symbol: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    output_dir: str | Path | None = None,
    strict_provisional: bool | None = None,
    config: Settings | MarketCachePreflightSettings | dict[str, Any] | None = None,
) -> MarketCachePreflightResult:
    """Run local-only acceptance preflight before market-cache-ingest."""

    project_settings, preflight_settings = _resolve_settings(config)
    if preflight_settings.enable_live_trading or preflight_settings.enable_broker_api:
        raise ValueError("Market cache preflight cannot enable live trading or broker API access")

    source_path = Path(input_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Market cache preflight input CSV not found: {source_path}")
    metadata_file = Path(metadata_path) if metadata_path is not None else None
    health_metadata_file = Path(health_metadata_path) if health_metadata_path is not None else None
    metadata = _load_optional_metadata(metadata_file)
    health_metadata = _load_optional_metadata(health_metadata_file)
    raw = read_csv_preserve_symbol_columns(source_path, keep_default_na=False)
    fields = _normalize_required_fields(required_fields, preflight_settings)
    strict = preflight_settings.strict_provisional if strict_provisional is None else bool(strict_provisional)

    candidate_frame, issues = validate_candidate_market_cache_rows(
        raw,
        settings=preflight_settings,
    )
    if not candidate_frame.empty:
        candidate_frame = _enrich_candidate_rows(candidate_frame, metadata=metadata)
        candidate_frame = _filter_candidate_rows(
            candidate_frame,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
    if candidate_frame.empty and not _has_error(issues):
        issues.append(
            _issue(
                "SCHEMA_ERROR",
                "ERROR",
                "symbol",
                "",
                "",
                "Candidate market CSV has no rows after optional symbol/date filters.",
                "REJECT",
            )
        )

    source = _first_non_empty(candidate_frame.get("source", pd.Series(dtype="object"))) if not candidate_frame.empty else _metadata_source(metadata)
    upstream_source = (
        _first_non_empty(candidate_frame.get("upstream_source", pd.Series(dtype="object")))
        if not candidate_frame.empty
        else _metadata_upstream_source(metadata)
    )
    successful_function = (
        _first_non_empty(candidate_frame.get("successful_function", pd.Series(dtype="object")))
        if not candidate_frame.empty
        else _metadata_successful_function(metadata)
    )
    selected_symbol = _first_non_empty(candidate_frame.get("symbol", pd.Series(dtype="object"))) if not candidate_frame.empty else ""
    security_type = infer_market_security_type(selected_symbol) if selected_symbol else "UNKNOWN"

    if not candidate_frame.empty:
        issues.extend(
            evaluate_market_source_policy_for_cache(
                candidate_frame,
                source=source,
                upstream_source=upstream_source,
                required_fields=fields,
                strict_provisional=strict,
                settings=preflight_settings,
                config=project_settings,
            )
        )
        issues.extend(_evaluate_optional_health_metadata(health_metadata))

    comparison_frame = pd.DataFrame()
    comparison_summary_frame = pd.DataFrame()
    if reference_source and not candidate_frame.empty:
        comparison_frame, comparison_summary_frame, comparison_issues = evaluate_optional_source_comparison(
            candidate_frame,
            reference_source=reference_source,
            cache_path=cache_path or project_settings.market_data_cache.cache_path,
            start_date=start_date,
            end_date=end_date,
            settings=project_settings,
            preflight_settings=preflight_settings,
        )
        issues.extend(comparison_issues)

    issue_frame = build_market_cache_preflight_issue_frame(issues)
    status = _decision_status(issue_frame)
    preflight_id = generate_market_cache_preflight_id(
        input_path=source_path,
        metadata_path=metadata_file,
        reference_source=reference_source or "",
        required_fields=fields,
        symbol=symbol or "",
        start_date=start_date or "",
        end_date=end_date or "",
        settings=preflight_settings,
    )
    summary_frame = summarize_market_cache_preflight(
        candidate_frame,
        issue_frame,
        preflight_id=preflight_id,
        status=status,
        input_path=source_path,
        metadata_path=metadata_file,
        source=source,
        upstream_source=upstream_source,
        successful_function=successful_function,
        security_type=security_type,
        required_fields=fields,
        reference_source=reference_source or "",
        comparison_summary_frame=comparison_summary_frame,
    )
    artifact_paths = resolve_market_cache_preflight_artifact_paths(
        Path(output_dir) if output_dir is not None else preflight_settings.output_dir,
        preflight_id,
    )
    result = MarketCachePreflightResult(
        preflight_id=preflight_id,
        status=status,
        input_path=source_path,
        metadata_path=metadata_file,
        candidate_frame=candidate_frame,
        issues_frame=issue_frame,
        summary_frame=summary_frame,
        comparison_frame=comparison_frame,
        comparison_summary_frame=comparison_summary_frame,
        artifact_paths=artifact_paths.as_dict(),
        warnings=_preflight_warnings(issue_frame),
        known_limitations=MARKET_CACHE_PREFLIGHT_LIMITATIONS,
        audit_metadata={
            "preflight_id": preflight_id,
            "operation": "market_cache_preflight",
            "input_path": source_path,
            "metadata_path": metadata_file,
            "health_metadata_path": health_metadata_file,
            "reference_source": reference_source or "",
            "cache_path": cache_path or project_settings.market_data_cache.cache_path,
            "required_fields": fields,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "cache_mutated": False,
            "market_cache_preflight_only": True,
            "config_version": preflight_settings.config_version,
        },
    )
    if preflight_settings.write_artifacts:
        write_market_cache_preflight_artifacts(result)
    return result


def validate_candidate_market_cache_rows(
    frame: pd.DataFrame,
    *,
    settings: MarketCachePreflightSettings | dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, list[MarketCachePreflightIssue]]:
    """Validate canonical market rows without mutating the cache."""

    preflight_settings = _coerce_preflight_settings(settings)
    output = frame.copy(deep=True)
    issues: list[MarketCachePreflightIssue] = []
    missing = [column for column in INPUT_REQUIRED_COLUMNS if column not in output.columns]
    if missing:
        return (
            pd.DataFrame(columns=MARKET_CACHE_COLUMNS),
            [
                _issue(
                    "SCHEMA_ERROR",
                    "ERROR",
                    "",
                    "",
                    "",
                    f"Candidate market CSV missing required columns: {', '.join(missing)}.",
                    "REJECT",
                )
            ],
        )

    output["symbol"] = normalize_symbol_series(output["symbol"])
    missing_symbol = output["symbol"].map(_is_missing_token)
    if missing_symbol.any():
        issues.append(
            _issue(
                "SYMBOL_FORMAT_ERROR",
                "ERROR",
                "symbol",
                "",
                "",
                "Candidate market CSV contains missing symbol values.",
                "REJECT",
            )
        )

    output["trade_date"] = _parse_required_date(output["trade_date"], "trade_date", issues)
    if preflight_settings.require_available_time:
        output["available_time"] = _parse_required_timestamp(output["available_time"], "available_time", issues)
    else:
        output["available_time"] = _parse_optional_timestamp(output["available_time"], "available_time", issues)

    for column in ["event_time", "publish_time", "ingest_time"]:
        output[column] = _parse_optional_timestamp(output[column], column, issues)

    for column in ["open", "high", "low", "close", "volume", "amount"]:
        output[column] = _parse_required_numeric(output[column], column, issues)
        parsed = pd.to_numeric(output[column], errors="coerce")
        if parsed.notna().any() and (parsed < 0).any():
            issues.append(
                _issue(
                    "OHLC_SANITY_ERROR",
                    "ERROR",
                    column,
                    "",
                    "",
                    f"{column} contains negative values.",
                    "REJECT",
                )
            )
    for column in ["pre_close", "adj_factor", "limit_up", "limit_down"]:
        output[column] = _parse_optional_numeric(output[column], column, issues)
        parsed = pd.to_numeric(output[column], errors="coerce")
        non_missing = output[column].map(lambda value: not _is_missing_token(value))
        if (parsed[non_missing] < 0).any():
            issues.append(
                _issue(
                    "OHLC_SANITY_ERROR",
                    "ERROR",
                    column,
                    "",
                    "",
                    f"{column} contains negative values.",
                    "REJECT",
                )
            )

    high = pd.to_numeric(output["high"], errors="coerce")
    low = pd.to_numeric(output["low"], errors="coerce")
    bad_ohlc = high.notna() & low.notna() & (high < low)
    if bad_ohlc.any():
        first_bad = output.loc[bad_ohlc].iloc[0]
        issues.append(
            _issue(
                "OHLC_SANITY_ERROR",
                "ERROR",
                "high,low",
                str(first_bad.get("symbol", "")),
                str(first_bad.get("trade_date", "")),
                "Candidate market CSV violates OHLC sanity: high is less than low.",
                "REJECT",
            )
        )

    if _has_error(issues):
        return pd.DataFrame(columns=MARKET_CACHE_COLUMNS), issues

    for column in MARKET_CACHE_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    output["is_suspended"] = output["is_suspended"].map(_normalize_bool_text)
    output["revision_id"] = output["revision_id"].map(_string_or_empty)
    output["source"] = output["source"].map(_normalize_key)
    output["cache_ingested_at"] = ""
    return output[MARKET_CACHE_COLUMNS].reset_index(drop=True), issues


def evaluate_market_source_policy_for_cache(
    frame: pd.DataFrame,
    *,
    source: str,
    upstream_source: str,
    required_fields: list[str],
    strict_provisional: bool,
    settings: MarketCachePreflightSettings | dict[str, Any] | None = None,
    config: Settings | dict[str, Any] | None = None,
) -> list[MarketCachePreflightIssue]:
    """Evaluate required fields against the source reliability policy."""

    preflight_settings = _coerce_preflight_settings(settings)
    issues: list[MarketCachePreflightIssue] = []
    securities = sorted({infer_market_security_type(symbol) for symbol in frame["symbol"].dropna().astype(str)})
    for security_type in securities or ["UNKNOWN"]:
        for field in required_fields:
            reliability = get_market_field_reliability(
                source=source,
                upstream_source=upstream_source,
                security_type=security_type,
                field=field,
                config=config,
            )
            if reliability == MarketFieldReliability.RELIABLE:
                continue
            if reliability == MarketFieldReliability.CAVEAT_FIRST_WINDOW_ROW:
                issues.append(
                    _issue(
                        "KNOWN_CAVEAT",
                        "INFO",
                        field,
                        "",
                        "",
                        f"{source}/{upstream_source}/{security_type} {field} has known reliability caveat: {reliability.value}.",
                        "ACCEPT_WITH_CAVEAT",
                    )
                )
            elif reliability == MarketFieldReliability.PROVISIONAL:
                severity = "ERROR" if strict_provisional else "WARN"
                issues.append(
                    _issue(
                        "SOURCE_POLICY_PROVISIONAL",
                        severity,
                        field,
                        "",
                        "",
                        f"{source}/{upstream_source}/{security_type} {field} is PROVISIONAL.",
                        "REJECT" if severity == "ERROR" else "WARN_ACCEPT",
                    )
                )
            elif reliability in {MarketFieldReliability.UNAVAILABLE, MarketFieldReliability.DO_NOT_USE}:
                issues.append(
                    _issue(
                        "SOURCE_POLICY_UNAVAILABLE_FIELD",
                        "ERROR",
                        field,
                        "",
                        "",
                        f"{source}/{upstream_source}/{security_type} {field} is {reliability.value}.",
                        "REJECT",
                    )
                )
            elif reliability == MarketFieldReliability.UNSTABLE:
                severity = "ERROR" if preflight_settings.unstable_policy_action == "REJECT" else "WARN"
                issues.append(
                    _issue(
                        "SOURCE_POLICY_UNRELIABLE",
                        severity,
                        field,
                        "",
                        "",
                        f"{source}/{upstream_source}/{security_type} {field} is UNSTABLE.",
                        "REJECT" if severity == "ERROR" else "WARN_ACCEPT",
                    )
                )
            else:
                issues.append(
                    _issue(
                        "SOURCE_POLICY_UNRELIABLE",
                        "WARN",
                        field,
                        "",
                        "",
                        f"{source}/{upstream_source}/{security_type} {field} has UNKNOWN reliability.",
                        "WARN_ACCEPT",
                    )
                )
    return issues


def evaluate_optional_source_comparison(
    candidate_frame: pd.DataFrame,
    *,
    reference_source: str,
    cache_path: str | Path,
    start_date: str | None,
    end_date: str | None,
    settings: Settings,
    preflight_settings: MarketCachePreflightSettings,
) -> tuple[pd.DataFrame, pd.DataFrame, list[MarketCachePreflightIssue]]:
    """Compare candidate rows against a reference source already present in cache."""

    issues: list[MarketCachePreflightIssue] = []
    source = _first_non_empty(candidate_frame.get("source", pd.Series(dtype="object")))
    reference = _normalize_key(reference_source)
    if not source or source == reference:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            [
                _issue(
                    "COMPARISON_WARN",
                    "WARN",
                    "",
                    "",
                    "",
                    "Reference source is missing or equal to candidate source; comparison was skipped.",
                    "WARN_ACCEPT",
                )
            ],
        )

    symbol = _first_non_empty(candidate_frame["symbol"])
    cache = load_market_cache(cache_path, config=settings)
    if cache.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            [
                _issue(
                    "COMPARISON_WARN",
                    "WARN",
                    "",
                    symbol,
                    "",
                    f"Reference cache is empty or unavailable at {cache_path}.",
                    "WARN_ACCEPT",
                )
            ],
        )
    cache["source"] = cache["source"].map(_normalize_key)
    reference_rows = cache.loc[(cache["symbol"] == symbol) & (cache["source"] == reference)].copy()
    if start_date:
        start = pd.to_datetime(start_date, errors="raise").normalize()
        reference_rows = reference_rows.loc[pd.to_datetime(reference_rows["trade_date"], errors="coerce") >= start]
    if end_date:
        end = pd.to_datetime(end_date, errors="raise").normalize()
        reference_rows = reference_rows.loc[pd.to_datetime(reference_rows["trade_date"], errors="coerce") <= end]
    if reference_rows.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            [
                _issue(
                    "COMPARISON_WARN",
                    "WARN",
                    "",
                    symbol,
                    "",
                    f"No cached reference rows found for source={reference}, symbol={symbol}.",
                    "WARN_ACCEPT",
                )
            ],
        )

    combined = pd.concat([candidate_frame[MARKET_CACHE_COLUMNS], reference_rows[MARKET_CACHE_COLUMNS]], ignore_index=True)
    comparison_frame = build_market_source_comparison_frame(
        combined,
        symbol=symbol,
        source_a=source,
        source_b=reference,
        settings=settings.market_data_comparison,
    )
    comparison_id = generate_market_source_comparison_id(
        symbol=symbol,
        source_a=source,
        source_b=reference,
        start_date=start_date or "",
        end_date=end_date or "",
        cache_path=cache_path,
        settings=settings.market_data_comparison,
    )
    comparison_summary = summarize_market_source_comparison(
        comparison_frame,
        comparison_id=comparison_id,
        cache_path=Path(cache_path),
        symbol=symbol,
        source_a=source,
        source_b=reference,
        start_date=start_date or "",
        end_date=end_date or "",
        settings=settings.market_data_comparison,
        policy_config=settings,
    )
    comparison_status = str(comparison_summary.iloc[0]["status"]) if not comparison_summary.empty else "PASS"
    if comparison_status == "PASS":
        return comparison_frame, comparison_summary, []
    if comparison_status == "WARN":
        issues.append(
            _issue(
                "COMPARISON_WARN",
                "WARN",
                "",
                symbol,
                "",
                "Optional source comparison returned WARN.",
                "WARN_ACCEPT",
            )
        )
    elif _comparison_failures_are_known_caveats(comparison_frame, comparison_summary, preflight_settings):
        issues.append(
            _issue(
                "KNOWN_CAVEAT",
                "WARN",
                "pre_close",
                symbol,
                str(_first_failure_date(comparison_frame)),
                "Optional source comparison failed only on first-window pre_close caveat.",
                "WARN_ACCEPT",
            )
        )
    else:
        severity = "ERROR" if preflight_settings.reject_on_comparison_fail else "WARN"
        issues.append(
            _issue(
                "COMPARISON_FAIL",
                severity,
                "",
                symbol,
                "",
                "Optional source comparison returned FAIL.",
                "REJECT" if severity == "ERROR" else "WARN_ACCEPT",
            )
        )
    return comparison_frame, comparison_summary, issues


def summarize_market_cache_preflight(
    candidate_frame: pd.DataFrame,
    issues_frame: pd.DataFrame,
    *,
    preflight_id: str,
    status: str,
    input_path: Path,
    metadata_path: Path | None,
    source: str,
    upstream_source: str,
    successful_function: str,
    security_type: str,
    required_fields: list[str],
    reference_source: str,
    comparison_summary_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Build one CSV-friendly preflight summary row."""

    if candidate_frame.empty:
        symbol = ""
        start_date = ""
        end_date = ""
    else:
        symbol = ",".join(sorted(candidate_frame["symbol"].astype(str).unique()))
        start_date = str(candidate_frame["trade_date"].min())
        end_date = str(candidate_frame["trade_date"].max())
    if comparison_summary_frame.empty:
        comparison_status = ""
        comparison_id = ""
    else:
        comparison_status = str(comparison_summary_frame.iloc[0].get("status", ""))
        comparison_id = str(comparison_summary_frame.iloc[0].get("comparison_id", ""))
    warning_count = int((issues_frame["severity"] == "WARN").sum()) if not issues_frame.empty else 0
    error_count = int((issues_frame["severity"] == "ERROR").sum()) if not issues_frame.empty else 0
    known_caveat_count = int((issues_frame["category"] == "KNOWN_CAVEAT").sum()) if not issues_frame.empty else 0
    return pd.DataFrame(
        [
            {
                "preflight_id": preflight_id,
                "status": status,
                "input_path": str(input_path),
                "metadata_path": str(metadata_path) if metadata_path is not None else "",
                "source": source,
                "upstream_source": upstream_source,
                "successful_function": successful_function,
                "security_type": security_type,
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "row_count": int(len(candidate_frame)),
                "required_fields": ",".join(required_fields),
                "reference_source": reference_source,
                "comparison_status": comparison_status,
                "comparison_id": comparison_id,
                "issue_count": int(len(issues_frame)),
                "warning_count": warning_count,
                "error_count": error_count,
                "known_caveat_count": known_caveat_count,
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ],
        columns=PREFLIGHT_SUMMARY_COLUMNS,
    )


def build_market_cache_preflight_issue_frame(
    issues: list[MarketCachePreflightIssue] | pd.DataFrame,
) -> pd.DataFrame:
    if isinstance(issues, pd.DataFrame):
        frame = issues.copy(deep=True)
    else:
        frame = pd.DataFrame([issue.as_row() for issue in issues])
    for column in PREFLIGHT_ISSUE_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[PREFLIGHT_ISSUE_COLUMNS].fillna("")


def write_market_cache_preflight_artifacts(result: MarketCachePreflightResult) -> dict[str, Path]:
    paths = MarketCachePreflightArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.issues_frame.to_csv(paths.market_cache_preflight_issues, index=False)
    result.summary_frame.to_csv(paths.market_cache_preflight_summary, index=False)
    paths.market_cache_preflight_report.write_text(render_market_cache_preflight_report(result), encoding="utf-8")
    metadata = {
        "preflight_id": result.preflight_id,
        "status": result.status,
        "input_path": str(result.input_path),
        "metadata_path": str(result.metadata_path) if result.metadata_path is not None else "",
        "row_count": int(result.row_count),
        "issue_count": int(result.issue_count),
        "warning_count": int(result.warning_count),
        "error_count": int(result.error_count),
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "summary": result.summary_frame.to_dict("records"),
        "issues": result.issues_frame.to_dict("records"),
        "comparison_summary": result.comparison_summary_frame.to_dict("records")
        if not result.comparison_summary_frame.empty
        else [],
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "created_at": MARKET_CACHE_PREFLIGHT_TIMESTAMP,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "cache_mutated": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths.as_dict()


def render_market_cache_preflight_report(result: MarketCachePreflightResult) -> str:
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    lines = [
        "# Market Cache Acceptance Preflight",
        "",
        f"- preflight_id: {result.preflight_id}",
        f"- status: {result.status}",
        f"- input_path: {result.input_path}",
        f"- metadata_path: {result.metadata_path or ''}",
        f"- source: {summary.get('source', '')}",
        f"- upstream_source: {summary.get('upstream_source', '')}",
        f"- security_type: {summary.get('security_type', '')}",
        f"- symbol: {summary.get('symbol', '')}",
        f"- row_count: {summary.get('row_count', 0)}",
        f"- required_fields: {summary.get('required_fields', '')}",
        f"- reference_source: {summary.get('reference_source', '')}",
        f"- comparison_status: {summary.get('comparison_status', '')}",
        f"- issue_count: {summary.get('issue_count', 0)}",
        f"- warning_count: {summary.get('warning_count', 0)}",
        f"- error_count: {summary.get('error_count', 0)}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Summary",
        "",
        result.summary_frame.to_markdown(index=False) if not result.summary_frame.empty else "No summary row.",
        "",
        "## Issues",
        "",
        result.issues_frame.to_markdown(index=False) if not result.issues_frame.empty else "No issues.",
    ]
    if not result.comparison_summary_frame.empty:
        lines.extend(
            [
                "",
                "## Optional Source Comparison",
                "",
                result.comparison_summary_frame.to_markdown(index=False),
            ]
        )
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def resolve_market_cache_preflight_artifact_paths(
    output_dir: str | Path,
    preflight_id: str,
) -> MarketCachePreflightArtifactPaths:
    artifact_dir = Path(output_dir) / preflight_id
    return MarketCachePreflightArtifactPaths(
        artifact_dir=artifact_dir,
        market_cache_preflight_report=artifact_dir / "market_cache_preflight_report.md",
        market_cache_preflight_issues=artifact_dir / "market_cache_preflight_issues.csv",
        market_cache_preflight_summary=artifact_dir / "market_cache_preflight_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def generate_market_cache_preflight_id(
    *,
    input_path: Path,
    metadata_path: Path | None,
    reference_source: str,
    required_fields: list[str],
    symbol: str,
    start_date: str,
    end_date: str,
    settings: MarketCachePreflightSettings,
) -> str:
    payload = {
        "input_path": str(input_path),
        "metadata_path": str(metadata_path) if metadata_path is not None else "",
        "reference_source": reference_source,
        "required_fields": required_fields,
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "strict_provisional": settings.strict_provisional,
        "unstable_policy_action": settings.unstable_policy_action,
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _enrich_candidate_rows(frame: pd.DataFrame, *, metadata: dict[str, Any]) -> pd.DataFrame:
    output = frame.copy(deep=True)
    metadata_fields = {
        "upstream_source": _metadata_upstream_source(metadata),
        "successful_function": _metadata_successful_function(metadata),
        "fetched_at": _string_or_empty(metadata.get("created_at") or metadata.get("fetched_at") or CACHE_TIMESTAMP),
    }
    metadata_source = _metadata_source(metadata)
    if metadata_source and ("source" not in output.columns or output["source"].map(_is_missing_token).all()):
        output["source"] = metadata_source
    for column, value in metadata_fields.items():
        if column not in output.columns:
            output[column] = value
        elif value:
            output[column] = output[column].map(lambda item: value if _is_missing_token(item) else item)
    output["upstream_source"] = output["upstream_source"].map(_normalize_key)
    output["successful_function"] = output["successful_function"].map(_string_or_empty)
    output["fetched_at"] = output["fetched_at"].map(_string_or_empty)
    output["cache_ingested_at"] = ""
    for column in MARKET_CACHE_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[MARKET_CACHE_COLUMNS]


def _filter_candidate_rows(
    frame: pd.DataFrame,
    *,
    symbol: str | None,
    start_date: str | None,
    end_date: str | None,
) -> pd.DataFrame:
    output = frame.copy(deep=True)
    if symbol:
        normalized_symbol = normalize_symbol_series(pd.Series([symbol])).iloc[0]
        output = output.loc[output["symbol"] == normalized_symbol]
    if start_date:
        start = pd.to_datetime(start_date, errors="raise").normalize()
        output = output.loc[pd.to_datetime(output["trade_date"], errors="coerce") >= start]
    if end_date:
        end = pd.to_datetime(end_date, errors="raise").normalize()
        output = output.loc[pd.to_datetime(output["trade_date"], errors="coerce") <= end]
    return output.reset_index(drop=True)


def _evaluate_optional_health_metadata(metadata: dict[str, Any]) -> list[MarketCachePreflightIssue]:
    if not metadata:
        return []
    status = _normalize_key(metadata.get("status") or metadata.get("adapter_status"))
    if status == "FAIL":
        return [
            _issue(
                "HEALTH_FAIL",
                "ERROR",
                "",
                "",
                "",
                "Linked data-source health metadata reports FAIL.",
                "REJECT",
            )
        ]
    if status == "WARN":
        return [
            _issue(
                "HEALTH_WARN",
                "WARN",
                "",
                "",
                "",
                "Linked data-source health metadata reports WARN.",
                "WARN_ACCEPT",
            )
        ]
    return []


def _comparison_failures_are_known_caveats(
    comparison_frame: pd.DataFrame,
    summary_frame: pd.DataFrame,
    settings: MarketCachePreflightSettings,
) -> bool:
    if not settings.allow_first_window_pre_close_caveat or comparison_frame.empty or summary_frame.empty:
        return False
    summary = summary_frame.iloc[0]
    if str(summary.get("pre_close_caveat", "")) != "CAVEAT_FIRST_WINDOW_ROW":
        return False
    failures = comparison_frame.loc[comparison_frame["tolerance_status"] == "FAIL"].copy()
    if failures.empty:
        return False
    matched = comparison_frame.loc[comparison_frame["row_match_status"] == "MATCHED"].copy()
    if matched.empty:
        return False
    first_date = str(matched["trade_date"].min())
    for _index, row in failures.iterrows():
        if str(row.get("trade_date", "")) != first_date:
            return False
        if set(_failure_fields_from_reason(str(row.get("tolerance_reason", "")))) != {"pre_close"}:
            return False
    return True


def _failure_fields_from_reason(reason: str) -> list[str]:
    match = re.search(r"Tolerance exceeded for:\s*(.*?)\.", reason)
    if not match:
        return []
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def _first_failure_date(comparison_frame: pd.DataFrame) -> str:
    failures = comparison_frame.loc[comparison_frame["tolerance_status"] == "FAIL"]
    if failures.empty:
        return ""
    return str(failures.iloc[0].get("trade_date", ""))


def _decision_status(issue_frame: pd.DataFrame) -> str:
    if issue_frame.empty:
        return MarketCachePreflightDecision.ACCEPT.value
    if (issue_frame["severity"] == "ERROR").any():
        return MarketCachePreflightDecision.REJECT.value
    if (issue_frame["severity"] == "WARN").any():
        return MarketCachePreflightDecision.WARN_ACCEPT.value
    return MarketCachePreflightDecision.ACCEPT.value


def _preflight_warnings(issue_frame: pd.DataFrame) -> list[str]:
    if issue_frame.empty:
        return []
    return [
        f"{row['category']}: {row['message']}"
        for row in issue_frame.to_dict("records")
        if str(row.get("severity", "")) in {"WARN", "ERROR"}
    ]


def _normalize_required_fields(
    value: list[str] | str | None,
    settings: MarketCachePreflightSettings,
) -> list[str]:
    if value is None:
        raw_values = settings.default_required_fields
    elif isinstance(value, str):
        raw_values = value.split(",")
    else:
        raw_values = value
    fields: list[str] = []
    for item in raw_values:
        field = str(item).strip().lower()
        if field and field not in fields:
            fields.append(field)
    return fields or list(settings.default_required_fields)


def _parse_required_date(
    series: pd.Series,
    column: str,
    issues: list[MarketCachePreflightIssue],
) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce").dt.normalize()
    invalid = parsed.isna()
    if invalid.any():
        issues.append(
            _issue(
                "DATE_PARSE_ERROR",
                "ERROR",
                column,
                "",
                "",
                f"{column} contains missing or invalid dates.",
                "REJECT",
            )
        )
    return parsed.dt.strftime("%Y-%m-%d").fillna("")


def _parse_required_timestamp(
    series: pd.Series,
    column: str,
    issues: list[MarketCachePreflightIssue],
) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    invalid = parsed.isna()
    if invalid.any():
        issues.append(
            _issue(
                "AVAILABLE_TIME_ERROR",
                "ERROR",
                column,
                "",
                "",
                f"{column} contains missing or invalid timestamps.",
                "REJECT",
            )
        )
    return parsed.dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")


def _parse_optional_timestamp(
    series: pd.Series,
    column: str,
    issues: list[MarketCachePreflightIssue],
) -> pd.Series:
    text = series.map(_string_or_empty)
    missing = text.map(_is_missing_token)
    parsed = pd.to_datetime(text.mask(missing, ""), errors="coerce")
    invalid = parsed.isna() & ~missing
    if invalid.any():
        issues.append(
            _issue(
                "DATE_PARSE_ERROR",
                "ERROR",
                column,
                "",
                "",
                f"{column} contains invalid non-empty timestamps.",
                "REJECT",
            )
        )
    return parsed.dt.strftime("%Y-%m-%d %H:%M:%S").mask(missing, "").fillna("")


def _parse_required_numeric(
    series: pd.Series,
    column: str,
    issues: list[MarketCachePreflightIssue],
) -> pd.Series:
    parsed = pd.to_numeric(series, errors="coerce")
    if parsed.isna().any():
        issues.append(
            _issue(
                "OHLC_SANITY_ERROR",
                "ERROR",
                column,
                "",
                "",
                f"{column} contains missing or invalid numeric values.",
                "REJECT",
            )
        )
    return parsed


def _parse_optional_numeric(
    series: pd.Series,
    column: str,
    issues: list[MarketCachePreflightIssue],
) -> pd.Series:
    text = series.map(_string_or_empty)
    missing = text.map(_is_missing_token)
    parsed = pd.to_numeric(text.mask(missing, ""), errors="coerce")
    invalid = parsed.isna() & ~missing
    if invalid.any():
        issues.append(
            _issue(
                "OHLC_SANITY_ERROR",
                "ERROR",
                column,
                "",
                "",
                f"{column} contains invalid non-empty numeric values.",
                "REJECT",
            )
        )
    return parsed


def _issue(
    category: str,
    severity: str,
    field: str,
    symbol: str,
    trade_date: str,
    message: str,
    decision_impact: str,
) -> MarketCachePreflightIssue:
    return MarketCachePreflightIssue(
        category=category,
        severity=severity,
        field=field,
        symbol=symbol,
        trade_date=trade_date,
        message=message,
        decision_impact=decision_impact,
    )


def _load_optional_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"Market cache preflight metadata JSON not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Market cache preflight metadata JSON is unreadable: {path}") from exc


def _metadata_source(metadata: dict[str, Any]) -> str:
    adapter_metadata = metadata.get("audit_metadata", {}).get("adapter_metadata", {})
    return _normalize_key(metadata.get("source") or adapter_metadata.get("source") or adapter_metadata.get("adapter"))


def _metadata_upstream_source(metadata: dict[str, Any]) -> str:
    adapter_metadata = metadata.get("audit_metadata", {}).get("adapter_metadata", {})
    return _normalize_key(metadata.get("upstream_source") or adapter_metadata.get("upstream_source"))


def _metadata_successful_function(metadata: dict[str, Any]) -> str:
    adapter_metadata = metadata.get("audit_metadata", {}).get("adapter_metadata", {})
    return _string_or_empty(metadata.get("successful_function") or adapter_metadata.get("successful_function"))


def _normalize_bool_text(value: Any) -> str:
    text = _string_or_empty(value).lower()
    if text in {"true", "1", "yes", "y"}:
        return "true"
    if text in {"false", "0", "no", "n", ""}:
        return "false"
    raise ValueError("is_suspended contains invalid boolean values")


def _first_non_empty(series: pd.Series) -> str:
    for value in series.dropna().astype(str):
        text = value.strip()
        if text:
            return text.upper()
    return ""


def _has_error(issues: list[MarketCachePreflightIssue]) -> bool:
    return any(issue.severity == "ERROR" for issue in issues)


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


def _is_missing_token(value: Any) -> bool:
    return _string_or_empty(value).strip().lower() in {"", "nan", "nat", "none", "null", "-", "--"}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _coerce_preflight_settings(
    settings: MarketCachePreflightSettings | dict[str, Any] | None,
) -> MarketCachePreflightSettings:
    if settings is None:
        return load_settings(Path("config/default.yaml")).market_cache_preflight
    if isinstance(settings, MarketCachePreflightSettings):
        return settings
    if isinstance(settings, dict):
        base = load_settings(Path("config/default.yaml")).market_cache_preflight.model_dump()
        base.update(settings)
        return MarketCachePreflightSettings(**base)
    raise TypeError("settings must be MarketCachePreflightSettings, dict, or None")


def _resolve_settings(
    config: Settings | MarketCachePreflightSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketCachePreflightSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.market_cache_preflight
    if isinstance(config, Settings):
        return config, config.market_cache_preflight
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, MarketCachePreflightSettings):
        return project, config
    if isinstance(config, dict):
        preflight_payload = dict(project.market_cache_preflight.model_dump())
        project_updates: dict[str, Any] = {}
        for key, value in config.items():
            if key == "market_cache_preflight" and isinstance(value, dict):
                preflight_payload.update(value)
            elif key == "market_data_cache" and isinstance(value, dict):
                project_updates["market_data_cache"] = project.market_data_cache.model_copy(update=value)
            elif key == "market_data_comparison" and isinstance(value, dict):
                project_updates["market_data_comparison"] = project.market_data_comparison.model_copy(update=value)
            elif key == "market_source_policy" and isinstance(value, dict):
                project_updates["market_source_policy"] = project.market_source_policy.model_copy(update=value)
            elif key in preflight_payload:
                preflight_payload[key] = value
        if project_updates:
            project = project.model_copy(update=project_updates)
        return project, MarketCachePreflightSettings(**preflight_payload)
    raise TypeError("config must be Settings, MarketCachePreflightSettings, dict, or None")
