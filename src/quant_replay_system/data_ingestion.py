"""Local CSV ingestion and processed snapshot helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.calendar import TRADING_CALENDAR_SCHEMA
from quant_replay_system.config import DataIngestionSettings, Settings, load_settings
from quant_replay_system.data import (
    CORPORATE_ACTION_SCHEMA,
    MARKET_DATA_SCHEMA,
    UNIVERSE_SNAPSHOT_SCHEMA,
)


INGESTION_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Does not call market data APIs or require API tokens.",
    "Does not connect to brokers, place orders, or automate execution.",
    "Writes naive local exchange timestamps for MVP compatibility with replay loaders.",
]

VALIDATION_COLUMNS = [
    "dataset_type",
    "severity",
    "issue_code",
    "column",
    "row_count",
    "message",
    "suggested_action",
]

INGESTION_CATEGORIES = {
    "market": "market",
    "benchmark": "benchmark",
    "universe": "universe",
    "corporate_actions": "corporate_actions",
    "trading_calendar": "trading_calendar",
}


@dataclass(frozen=True)
class SchemaValidationResult:
    valid: bool
    error_count: int
    warning_count: int
    validation_report: pd.DataFrame


@dataclass(frozen=True)
class IngestionArtifactPaths:
    artifact_dir: Path
    cleaned_csv: Path
    validation_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "cleaned_csv": self.cleaned_csv,
            "validation_report": self.validation_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class IngestionResult:
    dataset_type: str
    input_path: Path
    row_count: int
    cleaned_data: pd.DataFrame
    validation: SchemaValidationResult
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


@dataclass(frozen=True)
class SnapshotBuildResult:
    snapshot_id: str
    snapshot_name: str
    manifest_path: Path
    processed_files: dict[str, Path]
    row_counts: dict[str, int]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def ingest_market_data_csv(
    path: str | Path,
    *,
    output_dir: str | Path | None = None,
    settings: Settings | DataIngestionSettings | dict[str, Any] | None = None,
) -> IngestionResult:
    """Ingest a local market daily CSV into the canonical point-in-time schema."""

    return _ingest_csv(
        path,
        dataset_type="market",
        schema=MARKET_DATA_SCHEMA,
        date_columns=["trade_date"],
        datetime_columns=["event_time", "publish_time", "ingest_time", "available_time"],
        bool_columns=["is_suspended"],
        numeric_columns=["open", "high", "low", "close", "volume", "amount", "pre_close", "adj_factor", "limit_up", "limit_down"],
        duplicate_keys=["symbol", "trade_date"],
        default_time_base_column="trade_date",
        default_time_text="15:30",
        output_dir=output_dir,
        settings=settings,
    )


def ingest_benchmark_data_csv(
    path: str | Path,
    *,
    output_dir: str | Path | None = None,
    settings: Settings | DataIngestionSettings | dict[str, Any] | None = None,
) -> IngestionResult:
    """Ingest a local benchmark daily CSV using the market-data schema."""

    return _ingest_csv(
        path,
        dataset_type="benchmark",
        schema=MARKET_DATA_SCHEMA,
        date_columns=["trade_date"],
        datetime_columns=["event_time", "publish_time", "ingest_time", "available_time"],
        bool_columns=["is_suspended"],
        numeric_columns=["open", "high", "low", "close", "volume", "amount", "pre_close", "adj_factor", "limit_up", "limit_down"],
        duplicate_keys=["symbol", "trade_date"],
        default_time_base_column="trade_date",
        default_time_text="15:30",
        output_dir=output_dir,
        settings=settings,
    )


def ingest_universe_snapshot_csv(
    path: str | Path,
    *,
    output_dir: str | Path | None = None,
    settings: Settings | DataIngestionSettings | dict[str, Any] | None = None,
) -> IngestionResult:
    """Ingest a local universe snapshot CSV into the canonical schema."""

    return _ingest_csv(
        path,
        dataset_type="universe",
        schema=UNIVERSE_SNAPSHOT_SCHEMA,
        date_columns=["as_of_date", "listed_date", "delisted_date"],
        datetime_columns=["available_time"],
        bool_columns=["is_active", "is_st", "is_suspended"],
        numeric_columns=["min_lot"],
        duplicate_keys=["as_of_date", "symbol"],
        default_time_base_column="as_of_date",
        default_time_text="08:00",
        output_dir=output_dir,
        settings=settings,
        nullable_date_columns=["delisted_date"],
    )


def ingest_corporate_actions_csv(
    path: str | Path,
    *,
    output_dir: str | Path | None = None,
    settings: Settings | DataIngestionSettings | dict[str, Any] | None = None,
) -> IngestionResult:
    """Ingest a local corporate actions CSV into the canonical schema."""

    return _ingest_csv(
        path,
        dataset_type="corporate_actions",
        schema=CORPORATE_ACTION_SCHEMA,
        date_columns=["ex_date", "record_date"],
        datetime_columns=["event_time", "publish_time", "ingest_time", "available_time"],
        bool_columns=["rights_issue"],
        numeric_columns=["cash_dividend", "split_ratio"],
        duplicate_keys=["symbol", "action_type", "ex_date", "record_date"],
        default_time_base_column="ex_date",
        default_time_text="08:00",
        output_dir=output_dir,
        settings=settings,
        corporate_actions=True,
    )


def ingest_trading_calendar_csv(
    path: str | Path,
    *,
    output_dir: str | Path | None = None,
    settings: Settings | DataIngestionSettings | dict[str, Any] | None = None,
) -> IngestionResult:
    """Ingest a local trading calendar CSV into the canonical calendar schema."""

    return _ingest_csv(
        path,
        dataset_type="trading_calendar",
        schema=TRADING_CALENDAR_SCHEMA,
        date_columns=["trade_date"],
        datetime_columns=[],
        bool_columns=["is_trading_day"],
        numeric_columns=[],
        duplicate_keys=["trade_date"],
        default_time_base_column=None,
        default_time_text=None,
        output_dir=output_dir,
        settings=settings,
        add_source_revision=False,
        uses_available_time=False,
    )


def validate_required_columns(
    frame: pd.DataFrame,
    required_columns: list[str],
    *,
    dataset_type: str = "",
) -> SchemaValidationResult:
    """Validate required columns and return a structured validation report."""

    missing = [column for column in required_columns if column not in frame.columns]
    issues = [
        _validation_issue(
            dataset_type=dataset_type,
            severity="ERROR",
            issue_code="MISSING_REQUIRED_COLUMN",
            column=column,
            row_count=0,
            message=f"Missing required column: {column}",
            suggested_action="Add the missing column to the source CSV or configure an allowed default.",
        )
        for column in missing
    ]
    return _validation_result(issues)


def normalize_symbol_column(frame: pd.DataFrame, column: str = "symbol") -> pd.DataFrame:
    """Normalize symbol strings without mutating the input frame."""

    output = frame.copy(deep=True)
    if column in output.columns:
        output[column] = output[column].astype(str).str.strip().str.upper()
    return output


def normalize_date_columns(
    frame: pd.DataFrame,
    date_columns: list[str],
    *,
    nullable_date_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Parse date columns as normalized pandas timestamps."""

    output = frame.copy(deep=True)
    nullable = set(nullable_date_columns or [])
    for column in date_columns:
        if column not in output.columns:
            continue
        parsed = pd.to_datetime(output[column], errors="coerce")
        if column in nullable:
            output[column] = parsed.dt.normalize()
        else:
            output[column] = parsed.dt.normalize()
    return output


def assign_default_available_time(
    frame: pd.DataFrame,
    *,
    base_date_column: str,
    default_time_text: str,
    dataset_type: str,
) -> pd.Series:
    """Build default available_time values from a date column and local exchange time."""

    if base_date_column not in frame.columns:
        raise ValueError(f"{dataset_type}: cannot default available_time without {base_date_column}")
    dates = pd.to_datetime(frame[base_date_column], errors="coerce").dt.normalize()
    if dates.isna().any():
        raise ValueError(f"{dataset_type}: cannot default available_time from invalid {base_date_column}")
    return dates + _time_delta(default_time_text)


def build_processed_snapshot(
    snapshot_name: str,
    processed_files: dict[str, str | Path | IngestionResult],
    *,
    output_dir: str | Path | None = None,
    settings: Settings | DataIngestionSettings | dict[str, Any] | None = None,
) -> SnapshotBuildResult:
    """Build a deterministic manifest for a set of processed ingestion outputs."""

    _, ingestion_settings = _resolve_settings(settings)
    if ingestion_settings.enable_live_trading or ingestion_settings.enable_broker_api:
        raise ValueError("Data ingestion cannot enable live trading or broker API access")

    resolved_files = {
        str(dataset_type): _processed_path_from_value(value)
        for dataset_type, value in sorted(processed_files.items())
    }
    row_counts: dict[str, int] = {}
    warnings: list[str] = []
    for dataset_type, file_path in resolved_files.items():
        if not file_path.exists():
            warnings.append(f"Processed file is missing for {dataset_type}: {file_path}")
            row_counts[dataset_type] = 0
            continue
        try:
            row_counts[dataset_type] = int(len(pd.read_csv(file_path)))
        except Exception as exc:
            warnings.append(f"Could not read processed file for {dataset_type}: {file_path}: {exc}")
            row_counts[dataset_type] = 0

    snapshot_id = _hash_payload(
        {
            "snapshot_name": snapshot_name,
            "processed_files": {key: str(value) for key, value in resolved_files.items()},
            "row_counts": row_counts,
            "config_version": ingestion_settings.config_version,
        },
        length=12,
    )
    snapshot_dir = Path(output_dir) if output_dir is not None else ingestion_settings.snapshot_dir
    manifest_path = snapshot_dir / f"{snapshot_name}_{snapshot_id}_snapshot_manifest.json"
    audit_metadata = {
        "snapshot_id": snapshot_id,
        "snapshot_name": snapshot_name,
        "processed_files": resolved_files,
        "row_counts": row_counts,
        "warnings": warnings,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "data_ingestion_only": True,
        "config_version": ingestion_settings.config_version,
    }
    result = SnapshotBuildResult(
        snapshot_id=snapshot_id,
        snapshot_name=snapshot_name,
        manifest_path=manifest_path,
        processed_files=resolved_files,
        row_counts=row_counts,
        warnings=warnings,
        known_limitations=INGESTION_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if ingestion_settings.write_artifacts:
        write_snapshot_manifest(result)
    return result


def write_ingestion_artifacts(result: IngestionResult) -> dict[str, Path]:
    """Write cleaned CSV, validation report, and metadata for an ingestion run."""

    paths = IngestionArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.cleaned_data, paths.cleaned_csv)
    _export_dataframe(result.validation.validation_report, paths.validation_report)
    metadata = build_ingestion_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths.as_dict()


def build_ingestion_metadata(result: IngestionResult, paths: IngestionArtifactPaths) -> dict[str, Any]:
    """Build deterministic metadata for one ingestion run."""

    return {
        "dataset_type": result.dataset_type,
        "input_path": str(result.input_path),
        "row_count": result.row_count,
        "validation": {
            "valid": result.validation.valid,
            "error_count": result.validation.error_count,
            "warning_count": result.validation.warning_count,
        },
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "created_at": "1970-01-01T00:00:00+00:00",
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "data_ingestion_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def write_snapshot_manifest(result: SnapshotBuildResult) -> Path:
    """Write the processed snapshot manifest."""

    result.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "snapshot_id": result.snapshot_id,
        "snapshot_name": result.snapshot_name,
        "created_at": "1970-01-01T00:00:00+00:00",
        "processed_files": {key: str(value) for key, value in result.processed_files.items()},
        "row_counts": result.row_counts,
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "data_ingestion_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }
    result.manifest_path.write_text(json.dumps(_json_safe(manifest), indent=2, sort_keys=True), encoding="utf-8")
    return result.manifest_path


def _ingest_csv(
    path: str | Path,
    *,
    dataset_type: str,
    schema: list[str],
    date_columns: list[str],
    datetime_columns: list[str],
    bool_columns: list[str],
    numeric_columns: list[str],
    duplicate_keys: list[str],
    default_time_base_column: str | None,
    default_time_text: str | None,
    output_dir: str | Path | None,
    settings: Settings | DataIngestionSettings | dict[str, Any] | None,
    nullable_date_columns: list[str] | None = None,
    corporate_actions: bool = False,
    add_source_revision: bool = True,
    uses_available_time: bool = True,
) -> IngestionResult:
    project_settings, ingestion_settings = _resolve_settings(settings)
    if ingestion_settings.enable_live_trading or ingestion_settings.enable_broker_api:
        raise ValueError("Data ingestion cannot enable live trading or broker API access")

    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")
    raw = pd.read_csv(input_path, keep_default_na=False)
    prepared, validation = _prepare_frame(
        raw,
        dataset_type=dataset_type,
        schema=schema,
        date_columns=date_columns,
        datetime_columns=datetime_columns,
        bool_columns=bool_columns,
        numeric_columns=numeric_columns,
        duplicate_keys=duplicate_keys,
        default_time_base_column=default_time_base_column,
        default_time_text=default_time_text,
        settings=ingestion_settings,
        nullable_date_columns=nullable_date_columns or [],
        corporate_actions=corporate_actions,
        add_source_revision=add_source_revision,
        uses_available_time=uses_available_time,
    )
    _raise_for_validation_errors(dataset_type, validation.validation_report)
    sorted_frame = _sort_frame(prepared[schema], duplicate_keys)
    paths = resolve_ingestion_artifact_paths(
        _effective_output_dir(output_dir, ingestion_settings, dataset_type),
        input_path,
    )
    result = IngestionResult(
        dataset_type=dataset_type,
        input_path=input_path,
        row_count=len(sorted_frame),
        cleaned_data=sorted_frame,
        validation=validation,
        artifact_paths=paths.as_dict(),
        warnings=_warnings_from_report(validation.validation_report),
        known_limitations=INGESTION_LIMITATIONS,
        audit_metadata={
            "dataset_type": dataset_type,
            "input_path": input_path,
            "row_count": len(sorted_frame),
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "data_ingestion_only": True,
            "config_version": ingestion_settings.config_version,
        },
    )
    if ingestion_settings.write_artifacts:
        write_ingestion_artifacts(result)
    _ = project_settings
    return result


def resolve_ingestion_artifact_paths(output_dir: str | Path, input_path: str | Path) -> IngestionArtifactPaths:
    """Resolve deterministic artifact paths for one input CSV."""

    artifact_dir = Path(output_dir)
    stem = Path(input_path).stem
    return IngestionArtifactPaths(
        artifact_dir=artifact_dir,
        cleaned_csv=artifact_dir / f"{stem}_cleaned.csv",
        validation_report=artifact_dir / f"{stem}_validation_report.csv",
        metadata=artifact_dir / f"{stem}_metadata.json",
    )


def _prepare_frame(
    raw: pd.DataFrame,
    *,
    dataset_type: str,
    schema: list[str],
    date_columns: list[str],
    datetime_columns: list[str],
    bool_columns: list[str],
    numeric_columns: list[str],
    duplicate_keys: list[str],
    default_time_base_column: str | None,
    default_time_text: str | None,
    settings: DataIngestionSettings,
    nullable_date_columns: list[str],
    corporate_actions: bool,
    add_source_revision: bool,
    uses_available_time: bool,
) -> tuple[pd.DataFrame, SchemaValidationResult]:
    frame = raw.copy(deep=True)
    issues: list[dict[str, Any]] = []

    if add_source_revision:
        if "source" not in frame.columns:
            frame["source"] = settings.default_source
        if "revision_id" not in frame.columns:
            frame["revision_id"] = settings.default_revision_id

    if uses_available_time:
        frame, available_issues = _ensure_available_time(
            frame,
            dataset_type=dataset_type,
            default_time_base_column=default_time_base_column,
            default_time_text=default_time_text,
            settings=settings,
            corporate_actions=corporate_actions,
        )
        issues.extend(available_issues)

    required_validation = validate_required_columns(frame, schema, dataset_type=dataset_type)
    issues.extend(required_validation.validation_report.to_dict("records"))
    if any(issue["severity"] == "ERROR" for issue in issues):
        return frame, _validation_result(issues)

    if "symbol" in frame.columns:
        frame = normalize_symbol_column(frame)

    nullable = set(nullable_date_columns)
    for column in date_columns:
        parsed = pd.to_datetime(frame[column].replace("", pd.NA), errors="coerce")
        invalid = parsed.isna() & ~(column in nullable and frame[column].astype(str).str.strip().eq(""))
        if invalid.any():
            issues.append(
                _validation_issue(
                    dataset_type=dataset_type,
                    severity="ERROR",
                    issue_code="INVALID_DATE",
                    column=column,
                    row_count=int(invalid.sum()),
                    message=f"{column} contains invalid dates.",
                    suggested_action="Fix date values before ingestion.",
                )
            )
        frame[column] = parsed.dt.normalize()

    for column in datetime_columns:
        if column not in frame.columns:
            continue
        parsed = pd.to_datetime(frame[column].replace("", pd.NA), errors="coerce")
        invalid = parsed.isna()
        if invalid.any():
            issues.append(
                _validation_issue(
                    dataset_type=dataset_type,
                    severity="ERROR",
                    issue_code="INVALID_TIMESTAMP",
                    column=column,
                    row_count=int(invalid.sum()),
                    message=f"{column} contains invalid timestamps.",
                    suggested_action="Fix timestamp values before ingestion.",
                )
            )
        frame[column] = _drop_timezone(parsed)

    for column in bool_columns:
        frame, bool_issues = _parse_bool_column(frame, column, dataset_type)
        issues.extend(bool_issues)

    for column in numeric_columns:
        frame, numeric_issues = _parse_numeric_column(frame, column, dataset_type)
        issues.extend(numeric_issues)

    issues.extend(_duplicate_issues(frame, duplicate_keys, dataset_type, settings.duplicate_key_severity))
    return frame, _validation_result(issues)


def _ensure_available_time(
    frame: pd.DataFrame,
    *,
    dataset_type: str,
    default_time_base_column: str | None,
    default_time_text: str | None,
    settings: DataIngestionSettings,
    corporate_actions: bool,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    output = frame.copy(deep=True)
    issues: list[dict[str, Any]] = []
    missing_column = "available_time" not in output.columns
    if missing_column:
        output["available_time"] = ""
    raw_available = output["available_time"]
    blank_available = raw_available.astype(str).str.strip().eq("") | raw_available.isna()
    parsed = pd.to_datetime(raw_available.replace("", pd.NA), errors="coerce")
    invalid_existing = parsed.isna() & ~blank_available
    if invalid_existing.any():
        issues.append(
            _validation_issue(
                dataset_type=dataset_type,
                severity="ERROR",
                issue_code="INVALID_TIMESTAMP",
                column="available_time",
                row_count=int(invalid_existing.sum()),
                message="available_time contains invalid timestamps.",
                suggested_action="Fix available_time values before ingestion.",
            )
        )
    missing = parsed.isna() & blank_available
    if missing.any():
        allow_default = settings.allow_default_available_time and (
            not corporate_actions or settings.allow_default_corporate_action_available_time
        )
        if not allow_default:
            issues.append(
                _validation_issue(
                    dataset_type=dataset_type,
                    severity="ERROR",
                    issue_code="MISSING_AVAILABLE_TIME",
                    column="available_time",
                    row_count=int(missing.sum()),
                    message="available_time is missing and defaulting is disabled.",
                    suggested_action="Provide available_time or enable the relevant defaulting setting.",
                )
            )
            output["available_time"] = _drop_timezone(parsed)
            return output, issues
        if default_time_base_column is None or default_time_text is None:
            issues.append(
                _validation_issue(
                    dataset_type=dataset_type,
                    severity="ERROR",
                    issue_code="MISSING_AVAILABLE_TIME",
                    column="available_time",
                    row_count=int(missing.sum()),
                    message="available_time cannot be defaulted for this dataset type.",
                    suggested_action="Provide available_time in the source CSV.",
                )
            )
            output["available_time"] = _drop_timezone(parsed)
            return output, issues
        defaults = assign_default_available_time(
            output,
            base_date_column=default_time_base_column,
            default_time_text=default_time_text,
            dataset_type=dataset_type,
        )
        parsed.loc[missing] = defaults.loc[missing]
        issues.append(
            _validation_issue(
                dataset_type=dataset_type,
                severity="WARN",
                issue_code="DEFAULT_AVAILABLE_TIME_ASSIGNED",
                column="available_time",
                row_count=int(missing.sum()),
                message=f"Default available_time assigned using {default_time_base_column} {default_time_text}.",
                suggested_action="Provide explicit available_time when exact publication timing is known.",
            )
        )
    output["available_time"] = _drop_timezone(parsed)
    return output, issues


def _parse_bool_column(
    frame: pd.DataFrame,
    column: str,
    dataset_type: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    output = frame.copy(deep=True)
    normalized = output[column].astype(str).str.strip().str.lower()
    true_values = {"true", "1", "yes", "y"}
    false_values = {"false", "0", "no", "n"}
    valid = true_values | false_values
    invalid = ~normalized.isin(valid)
    issues = []
    if invalid.any():
        issues.append(
            _validation_issue(
                dataset_type=dataset_type,
                severity="ERROR",
                issue_code="INVALID_BOOLEAN",
                column=column,
                row_count=int(invalid.sum()),
                message=f"{column} contains invalid boolean values.",
                suggested_action="Use true/false, 1/0, yes/no, or y/n.",
            )
        )
    output[column] = normalized.isin(true_values)
    return output, issues


def _parse_numeric_column(
    frame: pd.DataFrame,
    column: str,
    dataset_type: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    output = frame.copy(deep=True)
    numeric = pd.to_numeric(output[column], errors="coerce")
    issues: list[dict[str, Any]] = []
    if numeric.isna().any():
        issues.append(
            _validation_issue(
                dataset_type=dataset_type,
                severity="ERROR",
                issue_code="INVALID_NUMERIC",
                column=column,
                row_count=int(numeric.isna().sum()),
                message=f"{column} contains missing or invalid numeric values.",
                suggested_action="Fix numeric values before ingestion.",
            )
        )
    if (numeric < 0).any():
        issue_code = "NEGATIVE_VOLUME_OR_AMOUNT" if column in {"volume", "amount"} else "NEGATIVE_PRICE"
        issues.append(
            _validation_issue(
                dataset_type=dataset_type,
                severity="ERROR",
                issue_code=issue_code,
                column=column,
                row_count=int((numeric < 0).sum()),
                message=f"{column} contains negative values.",
                suggested_action="Correct negative market data values before ingestion.",
            )
        )
    output[column] = numeric
    return output, issues


def _duplicate_issues(
    frame: pd.DataFrame,
    keys: list[str],
    dataset_type: str,
    severity: str,
) -> list[dict[str, Any]]:
    if not keys or any(column not in frame.columns for column in keys) or frame.empty:
        return []
    duplicates = frame.duplicated(subset=keys, keep=False)
    if not duplicates.any():
        return []
    return [
        _validation_issue(
            dataset_type=dataset_type,
            severity=severity,
            issue_code="DUPLICATE_KEY",
            column=",".join(keys),
            row_count=int(duplicates.sum()),
            message=f"Duplicate rows found for key: {', '.join(keys)}.",
            suggested_action="Deduplicate source rows or set duplicate_key_severity=ERROR to fail ingestion.",
        )
    ]


def _raise_for_validation_errors(dataset_type: str, report: pd.DataFrame) -> None:
    if report.empty:
        return
    errors = report.loc[report["severity"] == "ERROR"]
    if errors.empty:
        return
    first = errors.iloc[0]
    raise ValueError(f"{dataset_type} ingestion validation failed: {first['issue_code']} - {first['message']}")


def _validation_result(issues: list[dict[str, Any]]) -> SchemaValidationResult:
    report = _finalize_validation_report(pd.DataFrame(issues))
    error_count = int((report["severity"] == "ERROR").sum()) if not report.empty else 0
    warning_count = int((report["severity"] == "WARN").sum()) if not report.empty else 0
    return SchemaValidationResult(
        valid=error_count == 0,
        error_count=error_count,
        warning_count=warning_count,
        validation_report=report,
    )


def _validation_issue(
    *,
    dataset_type: str,
    severity: str,
    issue_code: str,
    column: str,
    row_count: int,
    message: str,
    suggested_action: str,
) -> dict[str, Any]:
    return {
        "dataset_type": dataset_type,
        "severity": severity,
        "issue_code": issue_code,
        "column": column,
        "row_count": int(row_count),
        "message": message,
        "suggested_action": suggested_action,
    }


def _finalize_validation_report(frame: pd.DataFrame) -> pd.DataFrame:
    report = frame.copy(deep=True)
    for column in VALIDATION_COLUMNS:
        if column not in report.columns:
            report[column] = ""
    if report.empty:
        return report[VALIDATION_COLUMNS]
    return report[VALIDATION_COLUMNS].sort_values(["severity", "issue_code", "column"]).reset_index(drop=True)


def _warnings_from_report(report: pd.DataFrame) -> list[str]:
    if report.empty:
        return []
    warnings = report.loc[report["severity"] == "WARN"]
    return [f"{row['issue_code']}: {row['message']}" for row in warnings.to_dict("records")]


def _sort_frame(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    sort_columns = [column for column in [*keys, "available_time", "revision_id"] if column in frame.columns]
    if not sort_columns:
        return frame.reset_index(drop=True)
    return frame.sort_values(sort_columns, na_position="last").reset_index(drop=True)


def _effective_output_dir(
    output_dir: str | Path | None,
    settings: DataIngestionSettings,
    dataset_type: str,
) -> Path:
    if output_dir is not None:
        return Path(output_dir)
    return settings.output_dir / INGESTION_CATEGORIES[dataset_type]


def _processed_path_from_value(value: str | Path | IngestionResult) -> Path:
    if isinstance(value, IngestionResult):
        return value.artifact_paths["cleaned_csv"]
    return Path(value)


def _time_delta(time_text: str) -> pd.Timedelta:
    parts = str(time_text).split(":")
    if len(parts) < 2:
        raise ValueError(f"Invalid default time: {time_text}")
    return pd.Timedelta(hours=int(parts[0]), minutes=int(parts[1]))


def _drop_timezone(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if hasattr(parsed.dt, "tz") and parsed.dt.tz is not None:
        parsed = parsed.dt.tz_localize(None)
    return parsed


def _resolve_settings(
    settings: Settings | DataIngestionSettings | dict[str, Any] | None,
) -> tuple[Settings, DataIngestionSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.data_ingestion
    if isinstance(settings, Settings):
        return settings, settings.data_ingestion
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, DataIngestionSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.data_ingestion.model_dump())
        for key, value in settings.items():
            if key == "data_ingestion" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, DataIngestionSettings(**payload)
    raise TypeError("settings must be Settings, DataIngestionSettings, dict, or None")


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


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
