"""Data quality summaries for processed point-in-time data files."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.calendar import TRADING_CALENDAR_SCHEMA
from quant_replay_system.config import DataQualitySettings, Settings, load_settings
from quant_replay_system.data import CORPORATE_ACTION_SCHEMA, MARKET_DATA_SCHEMA, UNIVERSE_SNAPSHOT_SCHEMA


DATA_QUALITY_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Does not call market data APIs or require API tokens.",
    "Does not connect to brokers, place orders, or automate execution.",
    "Provides summary diagnostics; it does not repair source data.",
]

SUPPORTED_DATASET_TYPES = {"market", "benchmark", "universe", "corporate_actions", "trading_calendar"}

QUALITY_ISSUE_COLUMNS = [
    "dataset_type",
    "severity",
    "issue_code",
    "column",
    "row_count",
    "message",
    "suggested_action",
]

SCHEMA_BY_DATASET = {
    "market": MARKET_DATA_SCHEMA,
    "benchmark": MARKET_DATA_SCHEMA,
    "universe": UNIVERSE_SNAPSHOT_SCHEMA,
    "corporate_actions": CORPORATE_ACTION_SCHEMA,
    "trading_calendar": TRADING_CALENDAR_SCHEMA,
}

DATE_COLUMN_BY_DATASET = {
    "market": "trade_date",
    "benchmark": "trade_date",
    "universe": "as_of_date",
    "corporate_actions": "ex_date",
    "trading_calendar": "trade_date",
}

DUPLICATE_KEYS_BY_DATASET = {
    "market": ["symbol", "trade_date"],
    "benchmark": ["symbol", "trade_date"],
    "universe": ["as_of_date", "symbol"],
    "corporate_actions": ["symbol", "action_type", "ex_date"],
    "trading_calendar": ["trade_date"],
}


@dataclass(frozen=True)
class DataQualityIssue:
    dataset_type: str
    severity: str
    issue_code: str
    column: str
    row_count: int
    message: str
    suggested_action: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_type": self.dataset_type,
            "severity": self.severity,
            "issue_code": self.issue_code,
            "column": self.column,
            "row_count": self.row_count,
            "message": self.message,
            "suggested_action": self.suggested_action,
        }


@dataclass(frozen=True)
class DataQualityArtifactPaths:
    artifact_dir: Path
    data_quality_report: Path
    data_quality_issues: Path
    row_counts: Path
    missingness_summary: Path
    duplicate_summary: Path
    source_revision_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "data_quality_report": self.data_quality_report,
            "data_quality_issues": self.data_quality_issues,
            "row_counts": self.row_counts,
            "missingness_summary": self.missingness_summary,
            "duplicate_summary": self.duplicate_summary,
            "source_revision_summary": self.source_revision_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class DataQualityResult:
    dataset_type: str
    status: str
    row_count: int
    issue_count: int
    warning_count: int
    error_count: int
    row_count_summary: pd.DataFrame
    missingness_summary: pd.DataFrame
    duplicate_summary: pd.DataFrame
    source_revision_summary: pd.DataFrame
    issue_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    known_limitations: list[str]
    quality_run_id: str
    audit_metadata: dict[str, Any]


def run_data_quality_checks(
    data: pd.DataFrame | str | Path,
    dataset_type: str,
    *,
    output_dir: str | Path | None = None,
    settings: Settings | DataQualitySettings | dict[str, Any] | None = None,
) -> DataQualityResult:
    """Run local data quality checks and write optional quality artifacts."""

    project_settings, quality_settings = _resolve_settings(settings)
    if quality_settings.enable_live_trading or quality_settings.enable_broker_api:
        raise ValueError("Data quality checks cannot enable live trading or broker API access")
    normalized_type = _normalize_dataset_type(dataset_type)
    frame = _load_frame(data)
    row_counts = summarize_row_counts(frame, normalized_type)
    missingness = summarize_missingness(frame)
    duplicates = summarize_duplicates(frame, normalized_type, settings=quality_settings)
    source_revision = run_source_revision_summary(frame)
    issue_frame = build_data_quality_report(
        frame,
        normalized_type,
        duplicate_summary=duplicates,
        settings=quality_settings,
    )
    status, issue_count, warning_count, error_count = _status_from_issues(issue_frame)
    quality_run_id = generate_quality_run_id(
        frame,
        normalized_type,
        source_revision,
        settings=quality_settings,
    )
    paths = resolve_data_quality_artifact_paths(
        Path(output_dir) if output_dir is not None else quality_settings.output_dir,
        normalized_type,
        quality_run_id,
    )
    audit_metadata = {
        "dataset_type": normalized_type,
        "row_count": len(frame),
        "status": status,
        "quality_run_id": quality_run_id,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "data_quality_only": True,
        "config_version": quality_settings.config_version,
    }
    result = DataQualityResult(
        dataset_type=normalized_type,
        status=status,
        row_count=len(frame),
        issue_count=issue_count,
        warning_count=warning_count,
        error_count=error_count,
        row_count_summary=row_counts,
        missingness_summary=missingness,
        duplicate_summary=duplicates,
        source_revision_summary=source_revision,
        issue_frame=issue_frame,
        artifact_paths=paths.as_dict(),
        known_limitations=DATA_QUALITY_LIMITATIONS,
        quality_run_id=quality_run_id,
        audit_metadata=audit_metadata,
    )
    if quality_settings.write_artifacts:
        write_data_quality_artifacts(result)
    _ = project_settings
    return result


def summarize_row_counts(data: pd.DataFrame, dataset_type: str) -> pd.DataFrame:
    """Summarize row counts by date and source when those columns exist."""

    normalized_type = _normalize_dataset_type(dataset_type)
    frame = data.copy(deep=True)
    rows: list[dict[str, Any]] = [
        {
            "dataset_type": normalized_type,
            "group_type": "total",
            "group_value": "ALL",
            "row_count": len(frame),
        }
    ]
    date_column = DATE_COLUMN_BY_DATASET[normalized_type]
    if date_column in frame.columns:
        parsed_dates = pd.to_datetime(frame[date_column], errors="coerce").dt.normalize()
        for value, count in parsed_dates.dt.date.astype(str).value_counts(dropna=False).sort_index().items():
            rows.append(
                {
                    "dataset_type": normalized_type,
                    "group_type": date_column,
                    "group_value": value,
                    "row_count": int(count),
                }
            )
    if "source" in frame.columns:
        sources = frame["source"].map(_string_or_empty).replace("", "<missing>")
        for value, count in sources.value_counts(dropna=False).sort_index().items():
            rows.append(
                {
                    "dataset_type": normalized_type,
                    "group_type": "source",
                    "group_value": value,
                    "row_count": int(count),
                }
            )
    return pd.DataFrame(rows)


def summarize_missingness(data: pd.DataFrame) -> pd.DataFrame:
    """Summarize missing values by column."""

    frame = data.copy(deep=True)
    if frame.empty and len(frame.columns) == 0:
        return pd.DataFrame(columns=["column", "missing_count", "missing_pct", "row_count"])
    rows = []
    row_count = len(frame)
    for column in frame.columns:
        missing = _missing_mask(frame[column])
        rows.append(
            {
                "column": column,
                "missing_count": int(missing.sum()),
                "missing_pct": float(missing.mean()) if row_count else 0.0,
                "row_count": row_count,
            }
        )
    return pd.DataFrame(rows).sort_values("column").reset_index(drop=True)


def summarize_duplicates(
    data: pd.DataFrame,
    dataset_type: str,
    *,
    settings: DataQualitySettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Summarize duplicate business keys."""

    normalized_type = _normalize_dataset_type(dataset_type)
    cfg = _coerce_quality_settings(settings)
    keys = DUPLICATE_KEYS_BY_DATASET[normalized_type]
    if any(column not in data.columns for column in keys):
        return pd.DataFrame(
            [
                {
                    "dataset_type": normalized_type,
                    "key_columns": ",".join(keys),
                    "duplicate_row_count": 0,
                    "duplicate_group_count": 0,
                    "severity": "",
                }
            ]
        )
    duplicated = data.duplicated(subset=keys, keep=False)
    duplicate_groups = data.loc[duplicated, keys].drop_duplicates() if duplicated.any() else pd.DataFrame(columns=keys)
    return pd.DataFrame(
        [
            {
                "dataset_type": normalized_type,
                "key_columns": ",".join(keys),
                "duplicate_row_count": int(duplicated.sum()),
                "duplicate_group_count": int(len(duplicate_groups)),
                "severity": _configured_severity(cfg.duplicate_key_severity, cfg) if duplicated.any() else "",
            }
        ]
    )


def run_market_data_sanity_checks(
    data: pd.DataFrame,
    *,
    dataset_type: str = "market",
    settings: DataQualitySettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Run market/benchmark-specific data sanity checks."""

    cfg = _coerce_quality_settings(settings)
    normalized_type = _normalize_dataset_type(dataset_type)
    frame = data.copy(deep=True)
    issues: list[DataQualityIssue] = []
    if normalized_type not in {"market", "benchmark"}:
        return _finalize_issue_frame(pd.DataFrame(columns=QUALITY_ISSUE_COLUMNS))
    if _has_columns(frame, ["open", "high", "low", "close"]):
        numeric = _numeric_frame(frame, ["open", "high", "low", "close"])
        price_problem = (numeric[["open", "high", "low", "close"]] <= 0).any(axis=1)
        if price_problem.any():
            issues.append(
                _issue(
                    normalized_type,
                    "ERROR",
                    "NON_POSITIVE_PRICE",
                    "open,high,low,close",
                    int(price_problem.sum()),
                    "Market data contains negative or zero OHLC prices.",
                    "Correct non-positive prices before replay.",
                )
            )
        ohlc_problem = (
            (numeric["high"] < numeric["low"])
            | (numeric["high"] < numeric["open"])
            | (numeric["high"] < numeric["close"])
            | (numeric["low"] > numeric["open"])
            | (numeric["low"] > numeric["close"])
        )
        if ohlc_problem.any():
            issues.append(
                _issue(
                    normalized_type,
                    "ERROR",
                    "OHLC_INCONSISTENCY",
                    "open,high,low,close",
                    int(ohlc_problem.sum()),
                    "OHLC values are internally inconsistent.",
                    "Verify high/low/open/close fields in the source CSV.",
                )
            )
    if _has_columns(frame, ["volume", "amount"]):
        numeric = _numeric_frame(frame, ["volume", "amount"])
        negative = (numeric[["volume", "amount"]] < 0).any(axis=1)
        if negative.any():
            issues.append(
                _issue(
                    normalized_type,
                    "ERROR",
                    "NEGATIVE_VOLUME_OR_AMOUNT",
                    "volume,amount",
                    int(negative.sum()),
                    "Volume or amount contains negative values.",
                    "Correct negative volume/amount values before replay.",
                )
            )
    if "pre_close" in frame.columns:
        pre_close = pd.to_numeric(frame["pre_close"], errors="coerce")
        bad_pre_close = pre_close.isna() | (pre_close <= 0)
        if bad_pre_close.any():
            issues.append(
                _issue(
                    normalized_type,
                    "ERROR",
                    "BAD_PRE_CLOSE",
                    "pre_close",
                    int(bad_pre_close.sum()),
                    "pre_close is missing or non-positive.",
                    "Provide valid previous close values.",
                )
            )
    issues.extend(_available_time_issues(frame, normalized_type, "trade_date", cfg))
    issues.extend(_source_revision_issues(frame, normalized_type, cfg))
    return _finalize_issue_frame(pd.DataFrame([issue.as_dict() for issue in issues]))


def run_available_time_checks(
    data: pd.DataFrame,
    dataset_type: str,
    *,
    settings: DataQualitySettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Run generic available_time checks for a dataset."""

    cfg = _coerce_quality_settings(settings)
    normalized_type = _normalize_dataset_type(dataset_type)
    date_column = DATE_COLUMN_BY_DATASET[normalized_type]
    issues = _available_time_issues(data, normalized_type, date_column, cfg)
    return _finalize_issue_frame(pd.DataFrame([issue.as_dict() for issue in issues]))


def run_source_revision_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Summarize source/revision coverage."""

    frame = data.copy(deep=True)
    if "source" not in frame.columns and "revision_id" not in frame.columns:
        return pd.DataFrame(columns=["source", "revision_id", "row_count"])
    source = frame["source"].map(_string_or_empty).replace("", "<missing>") if "source" in frame.columns else "<missing>"
    revision = (
        frame["revision_id"].map(_string_or_empty).replace("", "<missing>")
        if "revision_id" in frame.columns
        else "<missing>"
    )
    summary = pd.DataFrame({"source": source, "revision_id": revision})
    return (
        summary.value_counts(["source", "revision_id"], dropna=False)
        .rename("row_count")
        .reset_index()
        .sort_values(["source", "revision_id"])
        .reset_index(drop=True)
    )


def build_data_quality_report(
    data: pd.DataFrame,
    dataset_type: str,
    *,
    duplicate_summary: pd.DataFrame | None = None,
    settings: DataQualitySettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build structured quality issue rows for one dataset."""

    cfg = _coerce_quality_settings(settings)
    normalized_type = _normalize_dataset_type(dataset_type)
    frame = data.copy(deep=True)
    issues: list[DataQualityIssue] = []
    schema = SCHEMA_BY_DATASET[normalized_type]
    missing_required = [column for column in schema if column not in frame.columns]
    for column in missing_required:
        issues.append(
            _issue(
                normalized_type,
                "ERROR",
                "MISSING_REQUIRED_COLUMN",
                column,
                0,
                f"Missing required column: {column}.",
                "Regenerate or repair the canonical processed CSV.",
            )
        )
    if missing_required:
        return _finalize_issue_frame(pd.DataFrame([issue.as_dict() for issue in issues]))

    duplicates = duplicate_summary if duplicate_summary is not None else summarize_duplicates(frame, normalized_type, settings=cfg)
    if not duplicates.empty and int(duplicates.iloc[0]["duplicate_row_count"]) > 0:
        issues.append(
            _issue(
                normalized_type,
                str(duplicates.iloc[0]["severity"]),
                "DUPLICATE_KEY",
                str(duplicates.iloc[0]["key_columns"]),
                int(duplicates.iloc[0]["duplicate_row_count"]),
                "Duplicate business-key rows found.",
                "Deduplicate rows or resolve revisions before replay.",
            )
        )

    if normalized_type in {"market", "benchmark"}:
        market_issues = run_market_data_sanity_checks(frame, dataset_type=normalized_type, settings=cfg)
        issues.extend(_issues_from_frame(market_issues))
    elif normalized_type == "universe":
        issues.extend(_universe_issues(frame, cfg))
    elif normalized_type == "corporate_actions":
        issues.extend(_corporate_action_issues(frame, cfg))
    elif normalized_type == "trading_calendar":
        issues.extend(_trading_calendar_issues(frame))

    return _finalize_issue_frame(pd.DataFrame([issue.as_dict() for issue in issues]))


def write_data_quality_artifacts(result: DataQualityResult) -> dict[str, Path]:
    """Write data quality markdown, CSVs, and metadata."""

    paths = DataQualityArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.issue_frame, paths.data_quality_issues)
    _export_dataframe(result.row_count_summary, paths.row_counts)
    _export_dataframe(result.missingness_summary, paths.missingness_summary)
    _export_dataframe(result.duplicate_summary, paths.duplicate_summary)
    _export_dataframe(result.source_revision_summary, paths.source_revision_summary)
    metadata = build_data_quality_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.data_quality_report.write_text(render_data_quality_report(result, metadata), encoding="utf-8")
    return paths.as_dict()


def resolve_data_quality_artifact_paths(
    output_dir: str | Path,
    dataset_type: str,
    quality_run_id: str,
) -> DataQualityArtifactPaths:
    """Resolve stable data quality artifact paths."""

    artifact_dir = Path(output_dir) / dataset_type / quality_run_id
    return DataQualityArtifactPaths(
        artifact_dir=artifact_dir,
        data_quality_report=artifact_dir / "data_quality_report.md",
        data_quality_issues=artifact_dir / "data_quality_issues.csv",
        row_counts=artifact_dir / "row_counts.csv",
        missingness_summary=artifact_dir / "missingness_summary.csv",
        duplicate_summary=artifact_dir / "duplicate_summary.csv",
        source_revision_summary=artifact_dir / "source_revision_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def build_data_quality_metadata(result: DataQualityResult, paths: DataQualityArtifactPaths) -> dict[str, Any]:
    """Build deterministic metadata for a data quality run."""

    return {
        "quality_run_id": result.quality_run_id,
        "dataset_type": result.dataset_type,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "row_count": result.row_count,
        "issue_count": result.issue_count,
        "warning_count": result.warning_count,
        "error_count": result.error_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "data_quality_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_data_quality_report(result: DataQualityResult, metadata: dict[str, Any] | None = None) -> str:
    """Render a markdown data quality report."""

    _ = metadata
    lines = [
        f"# Data Quality Report: {result.dataset_type}",
        "",
        "No broker or live trading integration was invoked. This report checks local data artifacts only.",
        "",
        "## Summary",
        "",
        _dict_table(
            {
                "quality_run_id": result.quality_run_id,
                "dataset_type": result.dataset_type,
                "status": result.status,
                "row_count": result.row_count,
                "issue_count": result.issue_count,
                "warning_count": result.warning_count,
                "error_count": result.error_count,
            }
        ),
        "",
        "## Issues",
        "",
        _markdown_table(result.issue_frame, QUALITY_ISSUE_COLUMNS, max_rows=100),
        "",
        "## Row Counts",
        "",
        _markdown_table(result.row_count_summary, ["dataset_type", "group_type", "group_value", "row_count"]),
        "",
        "## Missingness",
        "",
        _markdown_table(result.missingness_summary, ["column", "missing_count", "missing_pct", "row_count"]),
        "",
        "## Duplicates",
        "",
        _markdown_table(result.duplicate_summary, ["dataset_type", "key_columns", "duplicate_row_count", "duplicate_group_count", "severity"]),
        "",
        "## Source / Revision Coverage",
        "",
        _markdown_table(result.source_revision_summary, ["source", "revision_id", "row_count"]),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def generate_quality_run_id(
    frame: pd.DataFrame,
    dataset_type: str,
    source_revision_summary: pd.DataFrame,
    *,
    settings: DataQualitySettings,
) -> str:
    """Generate a deterministic quality run id."""

    normalized_type = _normalize_dataset_type(dataset_type)
    date_column = DATE_COLUMN_BY_DATASET[normalized_type]
    parsed_dates = pd.to_datetime(frame[date_column], errors="coerce") if date_column in frame.columns else pd.Series(dtype="datetime64[ns]")
    date_values = parsed_dates.dropna().dt.date.astype(str).tolist() if not parsed_dates.empty else []
    payload = {
        "dataset_type": normalized_type,
        "row_count": len(frame),
        "date_min": min(date_values) if date_values else "",
        "date_max": max(date_values) if date_values else "",
        "source_revision_summary": source_revision_summary.to_dict("records"),
        "duplicate_key_severity": settings.duplicate_key_severity,
        "missing_available_time_severity": settings.missing_available_time_severity,
        "missing_source_revision_severity": settings.missing_source_revision_severity,
        "suspicious_available_time_severity": settings.suspicious_available_time_severity,
        "strict": settings.strict,
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _universe_issues(frame: pd.DataFrame, settings: DataQualitySettings) -> list[DataQualityIssue]:
    issues: list[DataQualityIssue] = []
    for column in ["symbol", "name", "instrument_type", "exchange"]:
        missing = _missing_mask(frame[column])
        if missing.any():
            issues.append(
                _issue(
                    "universe",
                    "ERROR",
                    "MISSING_IDENTITY_FIELD",
                    column,
                    int(missing.sum()),
                    f"{column} is missing.",
                    "Repair core universe identity fields.",
                )
            )
    as_of = pd.to_datetime(frame["as_of_date"], errors="coerce")
    listed = pd.to_datetime(frame["listed_date"], errors="coerce")
    listed_after = listed.notna() & as_of.notna() & (listed > as_of)
    if listed_after.any():
        issues.append(
            _issue("universe", "ERROR", "LISTED_DATE_AFTER_AS_OF_DATE", "listed_date", int(listed_after.sum()), "listed_date is after as_of_date.", "Fix listed_date or snapshot date.")
        )
    delisted = pd.to_datetime(frame["delisted_date"].replace("", pd.NA), errors="coerce")
    delisted_before = delisted.notna() & listed.notna() & (delisted < listed)
    if delisted_before.any():
        issues.append(
            _issue("universe", "ERROR", "DELISTED_DATE_BEFORE_LISTED_DATE", "delisted_date", int(delisted_before.sum()), "delisted_date is before listed_date.", "Fix listed/delisted dates.")
        )
    min_lot = pd.to_numeric(frame["min_lot"], errors="coerce")
    bad_lot = min_lot.isna() | (min_lot <= 0)
    if bad_lot.any():
        issues.append(_issue("universe", "ERROR", "NON_POSITIVE_MIN_LOT", "min_lot", int(bad_lot.sum()), "min_lot is missing or non-positive.", "Provide a positive lot size."))
    issues.extend(_available_time_issues(frame, "universe", "as_of_date", settings))
    issues.extend(_source_revision_issues(frame, "universe", settings))
    return issues


def _corporate_action_issues(frame: pd.DataFrame, settings: DataQualitySettings) -> list[DataQualityIssue]:
    issues: list[DataQualityIssue] = []
    issues.extend(_available_time_issues(frame, "corporate_actions", "ex_date", settings))
    ex_date = pd.to_datetime(frame["ex_date"], errors="coerce")
    bad_ex = ex_date.isna() | (ex_date < pd.Timestamp("1900-01-01"))
    if bad_ex.any():
        issues.append(_issue("corporate_actions", "ERROR", "INVALID_EX_DATE", "ex_date", int(bad_ex.sum()), "ex_date is invalid or implausible.", "Fix corporate action dates."))
    cash = pd.to_numeric(frame["cash_dividend"], errors="coerce")
    negative_cash = cash.notna() & (cash < 0)
    if negative_cash.any():
        issues.append(_issue("corporate_actions", "ERROR", "NEGATIVE_CASH_DIVIDEND", "cash_dividend", int(negative_cash.sum()), "cash_dividend is negative.", "Correct dividend values."))
    split = pd.to_numeric(frame["split_ratio"], errors="coerce")
    bad_split = split.notna() & (split <= 0)
    if bad_split.any():
        issues.append(_issue("corporate_actions", "ERROR", "NON_POSITIVE_SPLIT_RATIO", "split_ratio", int(bad_split.sum()), "split_ratio is non-positive.", "Correct split ratio values."))
    issues.extend(_source_revision_issues(frame, "corporate_actions", settings))
    return issues


def _trading_calendar_issues(frame: pd.DataFrame) -> list[DataQualityIssue]:
    issues: list[DataQualityIssue] = []
    missing_trading_day = _missing_mask(frame["is_trading_day"])
    if missing_trading_day.any():
        issues.append(_issue("trading_calendar", "ERROR", "MISSING_IS_TRADING_DAY", "is_trading_day", int(missing_trading_day.sum()), "is_trading_day is missing.", "Fill true/false trading day flags."))
    is_trading = _parse_bool_loose(frame["is_trading_day"])
    for column in ["session_open", "session_close", "decision_time"]:
        missing = is_trading & _missing_mask(frame[column])
        if missing.any():
            issues.append(_issue("trading_calendar", "ERROR", "TRADING_DAY_MISSING_SESSION_FIELD", column, int(missing.sum()), f"Trading day is missing {column}.", "Fill session and decision times for trading days."))
        unexpected = (~is_trading) & (~_missing_mask(frame[column]))
        if unexpected.any():
            issues.append(_issue("trading_calendar", "WARN", "NON_TRADING_DAY_HAS_SESSION_FIELD", column, int(unexpected.sum()), f"Non-trading day has {column}.", "Clear session fields for non-trading days unless intentional."))
    return issues


def _available_time_issues(
    frame: pd.DataFrame,
    dataset_type: str,
    base_date_column: str,
    settings: DataQualitySettings,
) -> list[DataQualityIssue]:
    issues: list[DataQualityIssue] = []
    if "available_time" not in frame.columns:
        issues.append(_issue(dataset_type, _configured_severity(settings.missing_available_time_severity, settings), "MISSING_AVAILABLE_TIME", "available_time", len(frame), "available_time column is missing.", "Add available_time before replay."))
        return issues
    available_raw = frame["available_time"]
    missing = _missing_mask(available_raw)
    if missing.any():
        issues.append(_issue(dataset_type, _configured_severity(settings.missing_available_time_severity, settings), "MISSING_AVAILABLE_TIME", "available_time", int(missing.sum()), "available_time has missing values.", "Add available_time before replay."))
    if base_date_column in frame.columns:
        available = pd.to_datetime(available_raw, errors="coerce")
        base_dates = pd.to_datetime(frame[base_date_column], errors="coerce").dt.normalize()
        suspicious = available.notna() & base_dates.notna() & (available < base_dates)
        if suspicious.any():
            issues.append(_issue(dataset_type, _configured_severity(settings.suspicious_available_time_severity, settings), "AVAILABLE_TIME_BEFORE_BASE_DATE", "available_time", int(suspicious.sum()), f"available_time is before {base_date_column}.", "Verify publication timing and point-in-time availability."))
    return issues


def _source_revision_issues(
    frame: pd.DataFrame,
    dataset_type: str,
    settings: DataQualitySettings,
) -> list[DataQualityIssue]:
    issues: list[DataQualityIssue] = []
    for column in ["source", "revision_id"]:
        if column not in frame.columns:
            issues.append(_issue(dataset_type, _configured_severity(settings.missing_source_revision_severity, settings), f"MISSING_{column.upper()}_COLUMN", column, len(frame), f"{column} column is missing.", "Add source/revision metadata before replay."))
            continue
        missing = _missing_mask(frame[column])
        if missing.any():
            issues.append(_issue(dataset_type, _configured_severity(settings.missing_source_revision_severity, settings), f"MISSING_{column.upper()}", column, int(missing.sum()), f"{column} has missing values.", "Fill source/revision metadata before replay."))
    return issues


def _issues_from_frame(frame: pd.DataFrame) -> list[DataQualityIssue]:
    return [
        DataQualityIssue(
            dataset_type=str(row["dataset_type"]),
            severity=str(row["severity"]),
            issue_code=str(row["issue_code"]),
            column=str(row["column"]),
            row_count=int(row["row_count"]),
            message=str(row["message"]),
            suggested_action=str(row["suggested_action"]),
        )
        for row in frame.to_dict("records")
    ]


def _status_from_issues(issue_frame: pd.DataFrame) -> tuple[str, int, int, int]:
    frame = _finalize_issue_frame(issue_frame)
    issue_count = len(frame)
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    return status, issue_count, warning_count, error_count


def _issue(dataset_type: str, severity: str, issue_code: str, column: str, row_count: int, message: str, suggested_action: str) -> DataQualityIssue:
    return DataQualityIssue(
        dataset_type=dataset_type,
        severity=str(severity).upper(),
        issue_code=issue_code,
        column=column,
        row_count=int(row_count),
        message=message,
        suggested_action=suggested_action,
    )


def _finalize_issue_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in QUALITY_ISSUE_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    if output.empty:
        return output[QUALITY_ISSUE_COLUMNS]
    return output[QUALITY_ISSUE_COLUMNS].sort_values(["severity", "issue_code", "column"], na_position="last").reset_index(drop=True)


def _load_frame(data: pd.DataFrame | str | Path) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data.copy(deep=True)
    path = Path(data)
    if not path.exists():
        raise FileNotFoundError(f"Data quality input CSV not found: {path}")
    return pd.read_csv(path)


def _normalize_dataset_type(dataset_type: str) -> str:
    normalized = str(dataset_type).strip().lower()
    if normalized not in SUPPORTED_DATASET_TYPES:
        raise ValueError(f"dataset_type must be one of: {', '.join(sorted(SUPPORTED_DATASET_TYPES))}")
    return normalized


def _has_columns(frame: pd.DataFrame, columns: list[str]) -> bool:
    return all(column in frame.columns for column in columns)


def _numeric_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame({column: pd.to_numeric(frame[column], errors="coerce") for column in columns})


def _missing_mask(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype(str).str.strip().eq("")


def _parse_bool_loose(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    return normalized.isin({"true", "1", "yes", "y"})


def _configured_severity(value: str, settings: DataQualitySettings) -> str:
    if settings.strict and str(value).upper() in {"INFO", "WARN"}:
        return "ERROR"
    return str(value).upper()


def _coerce_quality_settings(settings: DataQualitySettings | dict[str, Any] | None) -> DataQualitySettings:
    if settings is None:
        return DataQualitySettings()
    if isinstance(settings, DataQualitySettings):
        return settings
    if isinstance(settings, dict):
        return DataQualitySettings(**settings)
    if hasattr(settings, "model_dump"):
        return DataQualitySettings(**settings.model_dump())
    raise TypeError("settings must be DataQualitySettings, dict, or None")


def _resolve_settings(settings: Settings | DataQualitySettings | dict[str, Any] | None) -> tuple[Settings, DataQualitySettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.data_quality
    if isinstance(settings, Settings):
        return settings, settings.data_quality
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, DataQualitySettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.data_quality.model_dump())
        for key, value in settings.items():
            if key == "data_quality" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, DataQualitySettings(**payload)
    raise TypeError("settings must be Settings, DataQualitySettings, dict, or None")


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    table = frame[available].head(max_rows).copy()
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True).replace("|", "\\|")
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("|", "\\|").replace("\n", " ")


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = _sanitize_dataframe_for_export(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    export = frame.copy(deep=True)
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif export[column].dtype == "object":
            export[column] = export[column].map(_cell_to_export_value)
    return export


def _cell_to_export_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True)
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
