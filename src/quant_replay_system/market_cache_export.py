"""Reviewed market cache export workflow for pipeline-ready local market CSVs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketCacheExportSettings, Settings, load_settings
from quant_replay_system.data import MARKET_DATA_SCHEMA, normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.market_data_cache import (
    MARKET_CACHE_COLUMNS,
    query_market_cache,
    validate_market_cache_frame,
)


MARKET_CACHE_EXPORT_TIMESTAMP = "1970-01-01T00:00:00+00:00"

MARKET_CACHE_EXPORT_REQUIRED_COLUMNS = [
    "symbol",
    "start_date",
    "end_date",
    "source",
    "upstream_source",
    "enabled",
]

MARKET_CACHE_EXPORT_ROW_COLUMNS = [
    "manifest_row",
    "symbol",
    "start_date",
    "end_date",
    "source",
    "upstream_source",
    "enabled",
    "security_type",
    "require_fields",
    "status",
    "row_count",
    "min_trade_date",
    "max_trade_date",
    "message",
    "notes",
    "no_live_trading",
    "no_broker_api",
]

MARKET_CACHE_EXPORT_ISSUE_COLUMNS = [
    "category",
    "severity",
    "manifest_row",
    "symbol",
    "source",
    "upstream_source",
    "row_count",
    "message",
    "suggested_action",
    "no_live_trading",
    "no_broker_api",
]

MARKET_CACHE_EXPORT_LIMITATIONS = [
    "The reviewed cache export is local-only and never mutates the market cache.",
    "It requires explicit source and upstream_source selections by default.",
    "It rejects duplicate symbol/trade_date rows before data-pipeline use.",
    "It does not certify source truth, change scoring formulas, call broker APIs, place orders, or automate execution.",
    "Exported rows must still pass data-pipeline, data-quality, and snapshot-quality before research use.",
]


@dataclass(frozen=True)
class MarketCacheExportManifestRow:
    manifest_row: int
    symbol: str
    start_date: str
    end_date: str
    source: str
    upstream_source: str
    enabled: bool
    security_type: str = ""
    required_fields: list[str] = field(default_factory=list)
    notes: str = ""

    def as_result_row(
        self,
        *,
        status: str,
        row_count: int = 0,
        min_trade_date: str = "",
        max_trade_date: str = "",
        message: str = "",
    ) -> dict[str, Any]:
        return {
            "manifest_row": self.manifest_row,
            "symbol": self.symbol,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "source": self.source,
            "upstream_source": self.upstream_source,
            "enabled": self.enabled,
            "security_type": self.security_type,
            "require_fields": ",".join(self.required_fields),
            "status": status,
            "row_count": int(row_count),
            "min_trade_date": min_trade_date,
            "max_trade_date": max_trade_date,
            "message": message,
            "notes": self.notes,
            "no_live_trading": True,
            "no_broker_api": True,
        }


@dataclass(frozen=True)
class MarketCacheExportIssue:
    category: str
    severity: str
    message: str
    manifest_row: int | str = ""
    symbol: str = ""
    source: str = ""
    upstream_source: str = ""
    row_count: int = 0
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
            "row_count": int(self.row_count),
            "message": self.message,
            "suggested_action": self.suggested_action,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
        }


@dataclass(frozen=True)
class MarketCacheExportArtifactPaths:
    artifact_dir: Path
    market_cache_export_report: Path
    market_cache_export_rows: Path
    market_cache_export_issues: Path
    metadata: Path
    exported_market_csv: Path
    generated_pipeline_manifest: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_cache_export_report": self.market_cache_export_report,
            "market_cache_export_rows": self.market_cache_export_rows,
            "market_cache_export_issues": self.market_cache_export_issues,
            "metadata": self.metadata,
            "exported_market_csv": self.exported_market_csv,
            "generated_pipeline_manifest": self.generated_pipeline_manifest,
        }


@dataclass(frozen=True)
class MarketCacheExportResult:
    export_id: str
    status: str
    manifest_path: Path
    manifest_rows: list[MarketCacheExportManifestRow]
    export_rows_frame: pd.DataFrame
    issues_frame: pd.DataFrame
    exported_market_frame: pd.DataFrame
    exported_market_csv_path: Path
    pipeline_manifest_path: Path | None
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def row_count(self) -> int:
        return len(self.exported_market_frame)

    @property
    def issue_count(self) -> int:
        return len(self.issues_frame)

    @property
    def duplicate_key_count(self) -> int:
        if self.exported_market_frame.empty or not {"symbol", "trade_date"}.issubset(self.exported_market_frame.columns):
            return 0
        return int(self.exported_market_frame.duplicated(["symbol", "trade_date"]).sum())


def load_market_cache_export_manifest(
    path: str | Path,
    *,
    settings: MarketCacheExportSettings | None = None,
) -> list[MarketCacheExportManifestRow]:
    """Load a reviewed cache-export manifest while preserving symbol strings."""

    export_settings = settings or load_settings(Path("config/default.yaml")).market_cache_export
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Market cache export manifest not found: {manifest_path}")
    frame = read_csv_preserve_symbol_columns(manifest_path, keep_default_na=False)
    missing = [column for column in MARKET_CACHE_EXPORT_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Market cache export manifest missing columns: {', '.join(missing)}")

    rows: list[MarketCacheExportManifestRow] = []
    for index, raw_row in frame.iterrows():
        rows.append(
            MarketCacheExportManifestRow(
                manifest_row=int(index) + 2,
                symbol=normalize_symbol_value(raw_row.get("symbol")),
                start_date=_string_or_empty(raw_row.get("start_date")),
                end_date=_string_or_empty(raw_row.get("end_date")),
                source=_normalize_source(raw_row.get("source")),
                upstream_source=_normalize_source(raw_row.get("upstream_source")),
                enabled=_coerce_bool(raw_row.get("enabled")),
                security_type=_normalize_source(raw_row.get("security_type")),
                required_fields=_normalize_required_fields(raw_row.get("require_fields"), export_settings),
                notes=_string_or_empty(raw_row.get("notes")),
            )
        )
    return rows


def build_market_cache_export_frame(
    rows: list[MarketCacheExportManifestRow],
    *,
    cache_path: str | Path | None = None,
    fail_fast: bool = False,
    config: Settings | MarketCacheExportSettings | dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Query selected cache rows and return export rows, candidate market rows, and issues."""

    project_settings, export_settings = _resolve_settings(config)
    selected_frames: list[pd.DataFrame] = []
    result_rows: list[dict[str, Any]] = []
    issues: list[MarketCacheExportIssue] = []

    for row in rows:
        if not row.enabled:
            result_rows.append(row.as_result_row(status="SKIPPED_DISABLED", message="Manifest row is disabled."))
            continue
        if export_settings.require_explicit_source and (not row.source or not row.upstream_source):
            issue = MarketCacheExportIssue(
                category="SOURCE_SELECTION_MISSING",
                severity="ERROR",
                manifest_row=row.manifest_row,
                symbol=row.symbol,
                source=row.source,
                upstream_source=row.upstream_source,
                message="Manifest row must provide source and upstream_source.",
                suggested_action="Review the manifest and select one explicit source/upstream pair.",
            )
            issues.append(issue)
            result_rows.append(row.as_result_row(status="FAIL", message=issue.message))
            if fail_fast:
                break
            continue

        result = query_market_cache(
            symbol=row.symbol,
            start_date=row.start_date,
            end_date=row.end_date,
            source=row.source,
            upstream_source=row.upstream_source,
            cache_path=cache_path,
            config=project_settings,
        )
        frame = result.result_frame.copy(deep=True)
        if frame.empty:
            issue = MarketCacheExportIssue(
                category="MISSING_ROWS",
                severity="ERROR",
                manifest_row=row.manifest_row,
                symbol=row.symbol,
                source=row.source,
                upstream_source=row.upstream_source,
                message="No cached rows matched this reviewed export selection.",
                suggested_action="Check cache coverage or adjust the reviewed source/upstream/date selection.",
            )
            issues.append(issue)
            result_rows.append(row.as_result_row(status="FAIL", message=issue.message))
            if fail_fast:
                break
            continue

        selected_frames.append(frame)
        result_rows.append(
            row.as_result_row(
                status="PASS",
                row_count=len(frame),
                min_trade_date=str(frame["trade_date"].min()),
                max_trade_date=str(frame["trade_date"].max()),
                message="Reviewed cache rows selected.",
            )
        )

    market_frame = pd.concat(selected_frames, ignore_index=True, sort=False) if selected_frames else pd.DataFrame(columns=MARKET_CACHE_COLUMNS)
    export_rows = _finalize_export_rows(pd.DataFrame(result_rows))
    issue_frame = _finalize_issues(pd.DataFrame([issue.as_row() for issue in issues]))
    return export_rows, market_frame, issue_frame


def validate_market_cache_export_frame(
    frame: pd.DataFrame,
    *,
    required_fields: list[str] | None = None,
    settings: MarketCacheExportSettings | dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate and normalize a reviewed cache export frame before writing it."""

    cfg = _coerce_export_settings(settings)
    issues: list[MarketCacheExportIssue] = []
    required_columns = list(MARKET_DATA_SCHEMA)
    missing_columns = [column for column in required_columns if column not in frame.columns]
    if missing_columns:
        issues.append(
            MarketCacheExportIssue(
                category="SCHEMA_ERROR",
                severity="ERROR",
                message=f"Exported market frame missing required columns: {', '.join(missing_columns)}",
                suggested_action="Regenerate the export from canonical market cache rows.",
            )
        )
        return frame.copy(deep=True), _finalize_issues(pd.DataFrame([issue.as_row() for issue in issues]))

    try:
        normalized = validate_market_cache_frame(frame)
    except Exception as exc:
        issues.append(
            MarketCacheExportIssue(
                category="SCHEMA_ERROR",
                severity="ERROR",
                message=f"Exported market frame failed canonical validation: {exc}",
                suggested_action="Inspect selected cache rows before data-pipeline use.",
            )
        )
        return frame.copy(deep=True), _finalize_issues(pd.DataFrame([issue.as_row() for issue in issues]))

    if normalized.empty:
        issues.append(
            MarketCacheExportIssue(
                category="EMPTY_EXPORT",
                severity="ERROR",
                message="Reviewed cache export produced no market rows.",
                suggested_action="Enable at least one manifest row with matching cache coverage.",
            )
        )

    if cfg.reject_duplicate_business_keys and not normalized.empty:
        duplicated = normalized.duplicated(["symbol", "trade_date"], keep=False)
        if duplicated.any():
            duplicate_rows = int(duplicated.sum())
            issues.append(
                MarketCacheExportIssue(
                    category="DUPLICATE_BUSINESS_KEY",
                    severity="ERROR",
                    row_count=duplicate_rows,
                    message="Exported rows contain duplicate symbol/trade_date keys.",
                    suggested_action="Review manifest ranges so only one source/upstream row exists per symbol/date.",
                )
            )

    for field in required_fields or []:
        if field not in normalized.columns:
            issues.append(
                MarketCacheExportIssue(
                    category="SCHEMA_ERROR",
                    severity="ERROR",
                    message=f"Required field is not present in exported rows: {field}",
                    suggested_action="Review required_fields or source coverage.",
                )
            )
            continue
        if normalized[field].map(_is_missing_token).any():
            issues.append(
                MarketCacheExportIssue(
                    category="REQUIRED_FIELD_MISSING",
                    severity="ERROR",
                    row_count=int(normalized[field].map(_is_missing_token).sum()),
                    message=f"Required field contains missing values: {field}",
                    suggested_action="Select a source/upstream with complete required field coverage.",
                )
            )

    return normalized, _finalize_issues(pd.DataFrame([issue.as_row() for issue in issues]))


def run_market_cache_export(
    manifest: str | Path,
    *,
    cache_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    export_output_dir: str | Path | None = None,
    manifest_output_dir: str | Path | None = None,
    build_pipeline_manifest: bool = False,
    universe: str | Path | None = None,
    trading_calendar: str | Path | None = None,
    fail_fast: bool | None = None,
    config: Settings | MarketCacheExportSettings | dict[str, Any] | None = None,
) -> MarketCacheExportResult:
    """Run the reviewed market cache export workflow."""

    project_settings, export_settings = _resolve_settings(config)
    if export_settings.enable_live_trading or export_settings.enable_broker_api:
        raise ValueError("Market cache export cannot enable live trading or broker API access")
    if export_output_dir is not None:
        export_settings = export_settings.model_copy(update={"export_output_dir": Path(export_output_dir)})
    if manifest_output_dir is not None:
        export_settings = export_settings.model_copy(update={"manifest_output_dir": Path(manifest_output_dir)})
    if output_dir is not None:
        export_settings = export_settings.model_copy(update={"output_dir": Path(output_dir)})
    effective_fail_fast = export_settings.fail_fast if fail_fast is None else bool(fail_fast)
    manifest_path = Path(manifest)
    rows = load_market_cache_export_manifest(manifest_path, settings=export_settings)
    export_id = generate_market_cache_export_id(
        manifest_path=manifest_path,
        cache_path=cache_path or project_settings.market_data_cache.cache_path,
        rows=rows,
        build_pipeline_manifest=build_pipeline_manifest,
        universe=universe,
        trading_calendar=trading_calendar,
        settings=export_settings,
    )
    paths = resolve_market_cache_export_artifact_paths(
        export_settings.output_dir,
        export_settings.export_output_dir,
        export_settings.manifest_output_dir,
        export_id,
    )

    row_results, candidate_frame, query_issues = build_market_cache_export_frame(
        rows,
        cache_path=cache_path,
        fail_fast=effective_fail_fast,
        config=project_settings,
    )
    required_fields = _combined_required_fields(rows)
    normalized_frame, validation_issues = validate_market_cache_export_frame(
        candidate_frame,
        required_fields=required_fields,
        settings=export_settings,
    )
    issues_frame = _finalize_issues(pd.concat([query_issues, validation_issues], ignore_index=True, sort=False))
    status = _status_from_issues(issues_frame)
    warnings = _warnings_from_issues(issues_frame)

    pipeline_manifest_path = None
    if build_pipeline_manifest:
        if universe is None or trading_calendar is None:
            issue = MarketCacheExportIssue(
                category="PIPELINE_MANIFEST_INPUT_MISSING",
                severity="ERROR",
                message="--build-pipeline-manifest requires --universe and --trading-calendar.",
                suggested_action="Provide reviewed universe and trading calendar CSV paths.",
            )
            issues_frame = _finalize_issues(pd.concat([issues_frame, pd.DataFrame([issue.as_row()])], ignore_index=True))
            status = _status_from_issues(issues_frame)
            warnings = _warnings_from_issues(issues_frame)
        else:
            pipeline_manifest_path = build_cache_export_pipeline_manifest(
                market_path=paths.exported_market_csv,
                universe_path=universe,
                trading_calendar_path=trading_calendar,
                output_path=paths.generated_pipeline_manifest,
            )

    result = MarketCacheExportResult(
        export_id=export_id,
        status=status,
        manifest_path=manifest_path,
        manifest_rows=rows,
        export_rows_frame=row_results,
        issues_frame=issues_frame,
        exported_market_frame=normalized_frame,
        exported_market_csv_path=paths.exported_market_csv,
        pipeline_manifest_path=pipeline_manifest_path,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_CACHE_EXPORT_LIMITATIONS,
        audit_metadata={
            "export_id": export_id,
            "operation": "market_cache_export",
            "manifest_path": manifest_path,
            "cache_path": cache_path or project_settings.market_data_cache.cache_path,
            "row_count": len(normalized_frame),
            "issue_count": len(issues_frame),
            "duplicate_key_count": _duplicate_key_count(normalized_frame),
            "build_pipeline_manifest": bool(build_pipeline_manifest),
            "generated_pipeline_manifest_path": pipeline_manifest_path,
            "exported_market_csv_path": paths.exported_market_csv,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "cache_mutated": False,
            "network_api_calls_used_in_tests": False,
            "market_cache_export_only": True,
            "config_version": export_settings.config_version,
        },
    )
    if export_settings.write_artifacts:
        write_market_cache_export_artifacts(result)
    return result


def build_cache_export_pipeline_manifest(
    *,
    market_path: str | Path,
    universe_path: str | Path,
    trading_calendar_path: str | Path,
    output_path: str | Path,
) -> Path:
    """Write a LOCAL_CSV data-pipeline manifest for a reviewed cache export."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "datasets": [
            {"dataset_type": "market", "source": "LOCAL_CSV", "input_path": str(market_path)},
            {"dataset_type": "universe", "source": "LOCAL_CSV", "input_path": str(universe_path)},
            {"dataset_type": "trading_calendar", "source": "LOCAL_CSV", "input_path": str(trading_calendar_path)},
        ]
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_market_cache_export_artifacts(result: MarketCacheExportResult) -> dict[str, Path]:
    """Write reviewed cache export artifacts and the pipeline-ready market CSV."""

    paths = MarketCacheExportArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    paths.exported_market_csv.parent.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.export_rows_frame, paths.market_cache_export_rows)
    _export_dataframe(result.issues_frame, paths.market_cache_export_issues)
    _export_dataframe(result.exported_market_frame, paths.exported_market_csv)
    metadata = build_market_cache_export_metadata(result)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.market_cache_export_report.write_text(render_market_cache_export_report(result), encoding="utf-8")
    if result.pipeline_manifest_path is None and not paths.generated_pipeline_manifest.exists():
        paths.generated_pipeline_manifest.parent.mkdir(parents=True, exist_ok=True)
        paths.generated_pipeline_manifest.write_text("{}\n", encoding="utf-8")
    return paths.as_dict()


def build_market_cache_export_metadata(result: MarketCacheExportResult) -> dict[str, Any]:
    """Build deterministic metadata for one reviewed cache export."""

    return {
        "export_id": result.export_id,
        "status": result.status,
        "created_at": MARKET_CACHE_EXPORT_TIMESTAMP,
        "manifest_path": str(result.manifest_path),
        "exported_market_csv_path": str(result.exported_market_csv_path),
        "generated_pipeline_manifest_path": str(result.pipeline_manifest_path or ""),
        "row_count": result.row_count,
        "issue_count": result.issue_count,
        "duplicate_key_count": result.duplicate_key_count,
        "export_rows": result.export_rows_frame.to_dict("records"),
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


def render_market_cache_export_report(result: MarketCacheExportResult) -> str:
    """Render a markdown report for the reviewed cache export."""

    lines = [
        "# Reviewed Market Cache Export",
        "",
        f"- export_id: {result.export_id}",
        f"- status: {result.status}",
        f"- manifest_path: {result.manifest_path}",
        f"- exported_market_csv_path: {result.exported_market_csv_path}",
        f"- row_count: {result.row_count}",
        f"- duplicate_key_count: {result.duplicate_key_count}",
        f"- issue_count: {result.issue_count}",
        f"- generated_pipeline_manifest_path: {result.pipeline_manifest_path or ''}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Reviewed Rows",
        "",
        result.export_rows_frame.to_markdown(index=False) if not result.export_rows_frame.empty else "No manifest rows.",
        "",
        "## Issues",
        "",
        result.issues_frame.to_markdown(index=False) if not result.issues_frame.empty else "No issues.",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Interpretation", ""])
    lines.extend(
        [
            "- The local market cache may contain multiple source variants for the same symbol/date.",
            "- This export requires reviewed source/upstream selection before data-pipeline use.",
            "- Data quality duplicate-key checks remain unchanged.",
        ]
    )
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def resolve_market_cache_export_artifact_paths(
    output_dir: str | Path,
    export_output_dir: str | Path,
    manifest_output_dir: str | Path,
    export_id: str,
) -> MarketCacheExportArtifactPaths:
    artifact_dir = Path(output_dir) / export_id
    return MarketCacheExportArtifactPaths(
        artifact_dir=artifact_dir,
        market_cache_export_report=artifact_dir / "market_cache_export_report.md",
        market_cache_export_rows=artifact_dir / "market_cache_export_rows.csv",
        market_cache_export_issues=artifact_dir / "market_cache_export_issues.csv",
        metadata=artifact_dir / "metadata.json",
        exported_market_csv=Path(export_output_dir) / export_id / "market_raw_data.csv",
        generated_pipeline_manifest=Path(manifest_output_dir) / f"market_cache_export_{export_id}.json",
    )


def generate_market_cache_export_id(
    *,
    manifest_path: Path,
    cache_path: str | Path,
    rows: list[MarketCacheExportManifestRow],
    build_pipeline_manifest: bool,
    universe: str | Path | None,
    trading_calendar: str | Path | None,
    settings: MarketCacheExportSettings,
) -> str:
    payload = {
        "manifest_path": str(manifest_path),
        "cache_path": str(cache_path),
        "rows": [
            {
                "manifest_row": row.manifest_row,
                "symbol": row.symbol,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "source": row.source,
                "upstream_source": row.upstream_source,
                "enabled": row.enabled,
                "security_type": row.security_type,
                "required_fields": row.required_fields,
            }
            for row in rows
        ],
        "build_pipeline_manifest": bool(build_pipeline_manifest),
        "universe": str(universe) if universe is not None else "",
        "trading_calendar": str(trading_calendar) if trading_calendar is not None else "",
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _combined_required_fields(rows: list[MarketCacheExportManifestRow]) -> list[str]:
    fields: list[str] = []
    for row in rows:
        if not row.enabled:
            continue
        for field in row.required_fields:
            if field and field not in fields:
                fields.append(field)
    return fields


def _status_from_issues(issues_frame: pd.DataFrame) -> str:
    if issues_frame.empty:
        return "PASS"
    severities = set(issues_frame["severity"].astype(str).str.upper())
    if "ERROR" in severities:
        return "FAIL"
    if "WARN" in severities:
        return "WARN"
    return "PASS"


def _warnings_from_issues(issues_frame: pd.DataFrame) -> list[str]:
    if issues_frame.empty:
        return []
    return [
        f"{row.get('severity')} {row.get('category')}: {row.get('message')}"
        for row in issues_frame.to_dict("records")
        if str(row.get("severity", "")).upper() in {"WARN", "ERROR"}
    ]


def _duplicate_key_count(frame: pd.DataFrame) -> int:
    if frame.empty or not {"symbol", "trade_date"}.issubset(frame.columns):
        return 0
    return int(frame.duplicated(["symbol", "trade_date"]).sum())


def _finalize_export_rows(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in MARKET_CACHE_EXPORT_ROW_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    if output.empty:
        return output[MARKET_CACHE_EXPORT_ROW_COLUMNS]
    return output[MARKET_CACHE_EXPORT_ROW_COLUMNS].sort_values(["manifest_row", "symbol"]).reset_index(drop=True)


def _finalize_issues(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in MARKET_CACHE_EXPORT_ISSUE_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    if output.empty:
        return output[MARKET_CACHE_EXPORT_ISSUE_COLUMNS]
    return output[MARKET_CACHE_EXPORT_ISSUE_COLUMNS].sort_values(["severity", "category", "manifest_row"]).reset_index(drop=True)


def _normalize_required_fields(value: Any, settings: MarketCacheExportSettings) -> list[str]:
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
    raise ValueError(f"Invalid boolean value in market cache export manifest: {value}")


def _normalize_source(value: Any) -> str:
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


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = frame.copy(deep=True)
    if "symbol" in export.columns:
        export["symbol"] = export["symbol"].map(normalize_symbol_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
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


def _coerce_export_settings(settings: MarketCacheExportSettings | dict[str, Any] | None) -> MarketCacheExportSettings:
    if settings is None:
        return load_settings(Path("config/default.yaml")).market_cache_export
    if isinstance(settings, MarketCacheExportSettings):
        return settings
    if isinstance(settings, dict):
        base = load_settings(Path("config/default.yaml")).market_cache_export.model_dump()
        base.update(settings)
        return MarketCacheExportSettings(**base)
    if hasattr(settings, "model_dump"):
        return MarketCacheExportSettings(**settings.model_dump())
    raise TypeError("settings must be MarketCacheExportSettings, dict, or None")


def _resolve_settings(
    config: Settings | MarketCacheExportSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketCacheExportSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.market_cache_export
    if isinstance(config, Settings):
        return config, config.market_cache_export
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, MarketCacheExportSettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.market_cache_export.model_dump())
        project_updates: dict[str, Any] = {}
        for key, value in config.items():
            if key == "market_cache_export" and isinstance(value, dict):
                payload.update(value)
            elif key == "market_data_cache" and isinstance(value, dict):
                project_updates["market_data_cache"] = project.market_data_cache.model_copy(update=value)
            elif key in payload:
                payload[key] = value
        if project_updates:
            project = project.model_copy(update=project_updates)
        return project, MarketCacheExportSettings(**payload)
    raise TypeError("config must be Settings, MarketCacheExportSettings, dict, or None")
