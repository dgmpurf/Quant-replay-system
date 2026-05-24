"""Reviewed offline market update batch handoff to local snapshot validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketUpdateHandoffSettings, Settings, load_settings
from quant_replay_system.current_candidates import CurrentCandidateResult, generate_current_candidates
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.data_pipeline import (
    DataPipelineResult,
    load_data_pipeline_manifest,
    run_data_source_ingestion_pipeline,
)
from quant_replay_system.market_daily_update import (
    MarketDailyUpdateManifestResult,
    run_market_daily_update_manifest,
)
from quant_replay_system.snapshot_quality_gate import SnapshotQualityGateResult, run_snapshot_quality_gate


MARKET_UPDATE_HANDOFF_TIMESTAMP = "1970-01-01T00:00:00+00:00"

MARKET_UPDATE_HANDOFF_LIMITATIONS = [
    "The market update handoff is local-only and manually invoked.",
    "It does not mutate the market cache.",
    "It does not fetch real data, schedule jobs, call broker APIs, place orders, or automate execution.",
    "WARN_ACCEPT rows are included by default so provisional reviewed sources can be smoke-tested.",
    "The generated snapshot still must pass data-pipeline, data-quality, snapshot-quality, and downstream review.",
]

HANDOFF_ROW_COLUMNS = [
    "manifest_row",
    "symbol",
    "source",
    "dataset_type",
    "start_date",
    "end_date",
    "source_row_status",
    "preflight_status",
    "included",
    "handoff_status",
    "inclusion_reason",
    "raw_data_path",
    "metadata_path",
    "preflight_row_count",
    "batch_row_count",
    "cache_write_occurred",
    "no_live_trading",
    "no_broker_api",
]


@dataclass(frozen=True)
class LoadedMarketDailyUpdateResults:
    update_id: str
    status: str
    artifact_dir: Path
    symbol_results_frame: pd.DataFrame
    metadata: dict[str, Any]


@dataclass(frozen=True)
class MarketUpdateHandoffIssue:
    category: str
    severity: str
    symbol: str
    message: str
    no_live_trading: bool = True
    no_broker_api: bool = True

    def as_row(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "symbol": self.symbol,
            "message": self.message,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
        }


@dataclass(frozen=True)
class MarketUpdateHandoffArtifactPaths:
    artifact_dir: Path
    market_update_handoff_report: Path
    market_update_handoff_rows: Path
    generated_pipeline_manifest: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_update_handoff_report": self.market_update_handoff_report,
            "market_update_handoff_rows": self.market_update_handoff_rows,
            "generated_pipeline_manifest": self.generated_pipeline_manifest,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketUpdateHandoffResult:
    handoff_id: str
    status: str
    symbol_manifest_path: Path | None
    market_daily_update_dir: Path | None
    market_daily_update_result: MarketDailyUpdateManifestResult | LoadedMarketDailyUpdateResults | None
    handoff_rows_frame: pd.DataFrame
    batch_market_csv_path: Path | None
    pipeline_manifest_path: Path | None
    pipeline_result: DataPipelineResult | None
    snapshot_quality_result: SnapshotQualityGateResult | None
    current_candidate_result: CurrentCandidateResult | None
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def included_row_count(self) -> int:
        if self.handoff_rows_frame.empty:
            return 0
        return int(self.handoff_rows_frame["included"].map(_coerce_bool).sum())

    @property
    def candidate_count(self) -> int:
        if self.current_candidate_result is None:
            return 0
        return int(self.current_candidate_result.candidate_count)


def run_market_update_snapshot_handoff(
    *,
    symbol_manifest: str | Path | None = None,
    market_daily_update_dir: str | Path | None = None,
    universe: str | Path,
    trading_calendar: str | Path,
    decision_date: str,
    universe_name: str,
    selection_profile: str = "demo",
    top_n: int | None = None,
    strict_accept_only: bool = False,
    dry_run: bool = True,
    run_validation: bool | None = None,
    output_dir: str | Path | None = None,
    config: Settings | MarketUpdateHandoffSettings | dict[str, Any] | None = None,
) -> MarketUpdateHandoffResult:
    """Convert accepted reviewed update rows into a local snapshot dry-run."""

    project_settings, handoff_settings = _resolve_settings(config)
    if handoff_settings.enable_live_trading or handoff_settings.enable_broker_api:
        raise ValueError("Market update handoff cannot enable live trading or broker API access")
    if symbol_manifest is None and market_daily_update_dir is None:
        raise ValueError("market-update-handoff requires --symbol-manifest or --market-daily-update-dir")

    effective_run_validation = (
        handoff_settings.run_pipeline_validation if run_validation is None else bool(run_validation)
    )
    handoff_id = generate_market_update_handoff_id(
        symbol_manifest=Path(symbol_manifest) if symbol_manifest is not None else None,
        market_daily_update_dir=Path(market_daily_update_dir) if market_daily_update_dir is not None else None,
        universe=Path(universe),
        trading_calendar=Path(trading_calendar),
        decision_date=decision_date,
        universe_name=universe_name,
        selection_profile=selection_profile,
        strict_accept_only=strict_accept_only,
        settings=handoff_settings,
    )
    paths = resolve_market_update_handoff_artifact_paths(
        Path(output_dir) if output_dir is not None else handoff_settings.output_dir,
        handoff_id,
    )

    update_result: MarketDailyUpdateManifestResult | LoadedMarketDailyUpdateResults | None
    if market_daily_update_dir is not None:
        update_result = load_market_daily_update_results(market_daily_update_dir)
    else:
        update_result = run_market_daily_update_manifest(
            symbol_manifest,
            allow_real_data=False,
            dry_run=True,
            accept_cache_write=False,
            output_dir=paths.artifact_dir / "market_daily_update",
            config=project_settings,
        )

    handoff_rows = collect_accepted_update_rows(
        update_result.symbol_results_frame,
        strict_accept_only=strict_accept_only,
    )
    batch_market_csv_path: Path | None = None
    pipeline_manifest_path: Path | None = None
    pipeline_result: DataPipelineResult | None = None
    snapshot_result: SnapshotQualityGateResult | None = None
    current_result: CurrentCandidateResult | None = None
    warnings: list[str] = []

    if handoff_rows.empty or not handoff_rows["included"].map(_coerce_bool).any():
        warnings.append("No accepted or warn-accepted market update rows were available for handoff.")
        status = "FAIL"
    else:
        batch_path = handoff_settings.batch_output_dir / handoff_id / "market_raw_data.csv"
        batch_market_csv_path, batch_counts = build_batch_market_csv(handoff_rows, batch_path)
        handoff_rows = _attach_batch_counts(handoff_rows, batch_counts)
        if batch_counts and sum(batch_counts.values()) == 0:
            warnings.append("Accepted market update rows produced an empty batch market CSV.")
            status = "FAIL"
        else:
            pipeline_manifest_path = build_cache_backed_pipeline_manifest(
                market_path=batch_market_csv_path,
                universe_path=universe,
                trading_calendar_path=trading_calendar,
                output_path=handoff_settings.manifest_output_dir / f"market_update_handoff_{handoff_id}.json",
            )
            status = "PASS"

    if status != "FAIL" and effective_run_validation and pipeline_manifest_path is not None:
        pipeline_result, snapshot_result, current_result = _run_validation_chain(
            pipeline_manifest_path=pipeline_manifest_path,
            decision_date=decision_date,
            universe_name=universe_name,
            selection_profile=selection_profile,
            top_n=top_n if top_n is not None else handoff_settings.default_top_n,
            settings=project_settings,
        )
        warnings.extend(_validation_warnings(pipeline_result, snapshot_result, current_result))
        status = _handoff_status(
            handoff_rows,
            update_result=update_result,
            pipeline_result=pipeline_result,
            snapshot_result=snapshot_result,
            current_result=current_result,
            warnings=warnings,
        )
    elif status != "FAIL":
        status = _handoff_status(
            handoff_rows,
            update_result=update_result,
            pipeline_result=None,
            snapshot_result=None,
            current_result=None,
            warnings=warnings,
        )

    result = MarketUpdateHandoffResult(
        handoff_id=handoff_id,
        status=status,
        symbol_manifest_path=Path(symbol_manifest) if symbol_manifest is not None else None,
        market_daily_update_dir=Path(market_daily_update_dir) if market_daily_update_dir is not None else None,
        market_daily_update_result=update_result,
        handoff_rows_frame=handoff_rows,
        batch_market_csv_path=batch_market_csv_path,
        pipeline_manifest_path=pipeline_manifest_path,
        pipeline_result=pipeline_result,
        snapshot_quality_result=snapshot_result,
        current_candidate_result=current_result,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_UPDATE_HANDOFF_LIMITATIONS,
        audit_metadata={
            "handoff_id": handoff_id,
            "operation": "market_update_handoff",
            "dry_run": bool(dry_run),
            "strict_accept_only": bool(strict_accept_only),
            "run_pipeline_validation": bool(effective_run_validation),
            "symbol_manifest": Path(symbol_manifest) if symbol_manifest is not None else None,
            "market_daily_update_dir": Path(market_daily_update_dir) if market_daily_update_dir is not None else None,
            "universe": Path(universe),
            "trading_calendar": Path(trading_calendar),
            "decision_date": decision_date,
            "universe_name": universe_name,
            "selection_profile": selection_profile,
            "included_row_count": int(handoff_rows["included"].map(_coerce_bool).sum())
            if not handoff_rows.empty
            else 0,
            "batch_market_csv_path": batch_market_csv_path,
            "generated_pipeline_manifest_path": pipeline_manifest_path,
            "pipeline_id": pipeline_result.pipeline_id if pipeline_result is not None else "",
            "snapshot_quality_status": snapshot_result.status if snapshot_result is not None else "",
            "current_candidate_run_id": current_result.run_id if current_result is not None else "",
            "candidate_count": current_result.candidate_count if current_result is not None else 0,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "cache_mutated": False,
            "network_api_calls_used_in_tests": False,
            "market_update_handoff_only": True,
            "config_version": handoff_settings.config_version,
        },
    )
    if handoff_settings.write_artifacts:
        write_market_update_handoff_artifacts(result)
    return result


def load_market_daily_update_results(path: str | Path) -> LoadedMarketDailyUpdateResults:
    """Load a prior market-daily-update artifact directory."""

    artifact_dir = Path(path)
    symbol_results_path = artifact_dir / "market_daily_update_symbol_results.csv"
    metadata_path = artifact_dir / "metadata.json"
    if not symbol_results_path.exists():
        raise FileNotFoundError(f"Market daily update symbol results not found: {symbol_results_path}")
    metadata = _load_json(metadata_path) if metadata_path.exists() else {}
    frame = read_csv_preserve_symbol_columns(symbol_results_path, keep_default_na=False)
    return LoadedMarketDailyUpdateResults(
        update_id=str(metadata.get("update_id") or artifact_dir.name),
        status=str(metadata.get("status") or metadata.get("audit_metadata", {}).get("status") or ""),
        artifact_dir=artifact_dir,
        symbol_results_frame=frame,
        metadata=metadata,
    )


def collect_accepted_update_rows(
    symbol_results: pd.DataFrame,
    *,
    strict_accept_only: bool = False,
) -> pd.DataFrame:
    """Return handoff rows with accepted rows marked for inclusion."""

    rows: list[dict[str, Any]] = []
    for raw_row in symbol_results.to_dict("records"):
        preflight_status = str(raw_row.get("preflight_status") or "").strip().upper()
        row_status = str(raw_row.get("status") or "").strip().upper()
        raw_data_path = str(raw_row.get("raw_data_path") or "").strip()
        included = False
        handoff_status = "EXCLUDED"
        reason = _exclusion_reason(row_status, preflight_status, raw_data_path, strict_accept_only)
        if row_status in {"PASS", "WARN"} and raw_data_path:
            if preflight_status == "ACCEPT":
                included = True
                handoff_status = "INCLUDED_ACCEPT"
                reason = "Preflight ACCEPT row included."
            elif preflight_status == "WARN_ACCEPT" and not strict_accept_only:
                included = True
                handoff_status = "INCLUDED_WARN_ACCEPT"
                reason = "Preflight WARN_ACCEPT row included because strict_accept_only is false."
        rows.append(
            {
                "manifest_row": raw_row.get("manifest_row", ""),
                "symbol": normalize_symbol_value(raw_row.get("symbol")),
                "source": str(raw_row.get("source") or "").strip().upper(),
                "dataset_type": str(raw_row.get("dataset_type") or "").strip().lower(),
                "start_date": str(raw_row.get("start_date") or "").strip(),
                "end_date": str(raw_row.get("end_date") or "").strip(),
                "source_row_status": row_status,
                "preflight_status": preflight_status,
                "included": included,
                "handoff_status": handoff_status,
                "inclusion_reason": reason,
                "raw_data_path": raw_data_path,
                "metadata_path": str(raw_row.get("metadata_path") or "").strip(),
                "preflight_row_count": int(float(raw_row.get("row_count") or 0)),
                "batch_row_count": 0,
                "cache_write_occurred": _coerce_bool(raw_row.get("cache_write_occurred")),
                "no_live_trading": True,
                "no_broker_api": True,
            }
        )
    return pd.DataFrame(rows, columns=HANDOFF_ROW_COLUMNS)


def build_batch_market_csv(
    handoff_rows: pd.DataFrame,
    output_path: str | Path,
) -> tuple[Path, dict[str, int]]:
    """Merge included raw market CSVs into one local batch market CSV."""

    path = Path(output_path)
    frames: list[pd.DataFrame] = []
    batch_counts: dict[str, int] = {}
    for row in handoff_rows.loc[handoff_rows["included"].map(_coerce_bool)].to_dict("records"):
        raw_path = Path(str(row.get("raw_data_path") or ""))
        frame = read_csv_preserve_symbol_columns(raw_path, keep_default_na=False)
        frame = _filter_raw_market_frame(
            frame,
            symbol=str(row.get("symbol") or ""),
            start_date=str(row.get("start_date") or ""),
            end_date=str(row.get("end_date") or ""),
        )
        metadata = _load_json(Path(row["metadata_path"])) if str(row.get("metadata_path") or "").strip() else {}
        frame = _enrich_batch_frame(
            frame,
            source=str(row.get("source") or ""),
            metadata=metadata,
        )
        key = _row_key(row)
        batch_counts[key] = len(frame)
        frames.append(frame)

    batch = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    if not batch.empty:
        batch = _sort_batch_frame(batch)
    path.parent.mkdir(parents=True, exist_ok=True)
    batch.to_csv(path, index=False)
    return path, batch_counts


def build_cache_backed_pipeline_manifest(
    *,
    market_path: str | Path,
    universe_path: str | Path,
    trading_calendar_path: str | Path,
    output_path: str | Path,
) -> Path:
    """Write a LOCAL_CSV data-pipeline manifest for the handoff batch."""

    manifest_path = Path(output_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "datasets": [
            {"dataset_type": "market", "source": "LOCAL_CSV", "input_path": str(market_path)},
            {"dataset_type": "universe", "source": "LOCAL_CSV", "input_path": str(universe_path)},
            {"dataset_type": "trading_calendar", "source": "LOCAL_CSV", "input_path": str(trading_calendar_path)},
        ]
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def summarize_market_update_handoff(result: MarketUpdateHandoffResult) -> pd.DataFrame:
    """Build a one-row summary for reports and metadata."""

    current = result.current_candidate_result
    pipeline = result.pipeline_result
    snapshot = result.snapshot_quality_result
    return pd.DataFrame(
        [
            {
                "handoff_id": result.handoff_id,
                "status": result.status,
                "included_row_count": result.included_row_count,
                "batch_market_csv_path": str(result.batch_market_csv_path or ""),
                "generated_pipeline_manifest_path": str(result.pipeline_manifest_path or ""),
                "pipeline_id": pipeline.pipeline_id if pipeline is not None else "",
                "pipeline_status": pipeline.status if pipeline is not None else "",
                "snapshot_quality_status": snapshot.status if snapshot is not None else "",
                "current_candidate_run_id": current.run_id if current is not None else "",
                "factor_dataset_rows": current.factor_dataset_row_count if current is not None else 0,
                "scored_dataset_rows": current.scored_dataset_row_count if current is not None else 0,
                "candidate_count": current.candidate_count if current is not None else 0,
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ]
    )


def write_market_update_handoff_artifacts(result: MarketUpdateHandoffResult) -> dict[str, Path]:
    """Write handoff report, row CSV, manifest copy, and metadata."""

    paths = MarketUpdateHandoffArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.handoff_rows_frame.to_csv(paths.market_update_handoff_rows, index=False)
    if result.pipeline_manifest_path is not None and result.pipeline_manifest_path.exists():
        paths.generated_pipeline_manifest.write_text(
            result.pipeline_manifest_path.read_text(encoding="utf-8-sig"),
            encoding="utf-8",
        )
    else:
        paths.generated_pipeline_manifest.write_text("{}\n", encoding="utf-8")
    metadata = build_market_update_handoff_metadata(result)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.market_update_handoff_report.write_text(render_market_update_handoff_report(result), encoding="utf-8")
    return paths.as_dict()


def build_market_update_handoff_metadata(result: MarketUpdateHandoffResult) -> dict[str, Any]:
    """Build metadata.json content for one handoff run."""

    current = result.current_candidate_result
    pipeline = result.pipeline_result
    snapshot = result.snapshot_quality_result
    return {
        "handoff_id": result.handoff_id,
        "status": result.status,
        "created_at": MARKET_UPDATE_HANDOFF_TIMESTAMP,
        "summary": summarize_market_update_handoff(result).to_dict("records"),
        "symbol_manifest_path": str(result.symbol_manifest_path or ""),
        "market_daily_update_dir": str(result.market_daily_update_dir or ""),
        "batch_market_csv_path": str(result.batch_market_csv_path or ""),
        "generated_pipeline_manifest_path": str(result.pipeline_manifest_path or ""),
        "pipeline_id": pipeline.pipeline_id if pipeline is not None else "",
        "pipeline_status": pipeline.status if pipeline is not None else "",
        "snapshot_quality_status": snapshot.status if snapshot is not None else "",
        "snapshot_quality_report_path": str(snapshot.artifact_paths["snapshot_quality_gate_report"])
        if snapshot is not None
        else "",
        "current_candidate_run_id": current.run_id if current is not None else "",
        "factor_dataset_shape": list(current.factor_dataset.shape) if current is not None else [0, 0],
        "scored_dataset_shape": list(current.scored_dataset.shape) if current is not None else [0, 0],
        "candidates_shape": list(current.candidates.shape) if current is not None else [0, 0],
        "candidate_count": current.candidate_count if current is not None else 0,
        "current_candidate_warnings": current.warnings if current is not None else [],
        "handoff_rows": result.handoff_rows_frame.to_dict("records"),
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


def render_market_update_handoff_report(result: MarketUpdateHandoffResult) -> str:
    """Render a markdown report for the handoff."""

    current = result.current_candidate_result
    pipeline = result.pipeline_result
    snapshot = result.snapshot_quality_result
    lines = [
        "# Reviewed Offline Update Batch To Snapshot Handoff",
        "",
        f"- handoff_id: {result.handoff_id}",
        f"- status: {result.status}",
        f"- symbol_manifest_path: {result.symbol_manifest_path or ''}",
        f"- market_daily_update_dir: {result.market_daily_update_dir or ''}",
        f"- included_row_count: {result.included_row_count}",
        f"- batch_market_csv_path: {result.batch_market_csv_path or ''}",
        f"- generated_pipeline_manifest_path: {result.pipeline_manifest_path or ''}",
        f"- pipeline_id: {pipeline.pipeline_id if pipeline is not None else ''}",
        f"- pipeline_status: {pipeline.status if pipeline is not None else ''}",
        f"- snapshot_quality_status: {snapshot.status if snapshot is not None else ''}",
        f"- current_candidate_run_id: {current.run_id if current is not None else ''}",
        f"- factor_dataset_shape: {tuple(current.factor_dataset.shape) if current is not None else (0, 0)}",
        f"- scored_dataset_shape: {tuple(current.scored_dataset.shape) if current is not None else (0, 0)}",
        f"- candidates_shape: {tuple(current.candidates.shape) if current is not None else (0, 0)}",
        f"- candidate_count: {current.candidate_count if current is not None else 0}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Handoff Rows",
        "",
        result.handoff_rows_frame.to_markdown(index=False) if not result.handoff_rows_frame.empty else "No rows.",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    if current is not None and current.warnings:
        lines.extend(["", "## Current Candidate Warnings", ""])
        lines.extend(f"- {warning}" for warning in current.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def resolve_market_update_handoff_artifact_paths(
    output_dir: str | Path,
    handoff_id: str,
) -> MarketUpdateHandoffArtifactPaths:
    artifact_dir = Path(output_dir) / handoff_id
    return MarketUpdateHandoffArtifactPaths(
        artifact_dir=artifact_dir,
        market_update_handoff_report=artifact_dir / "market_update_handoff_report.md",
        market_update_handoff_rows=artifact_dir / "market_update_handoff_rows.csv",
        generated_pipeline_manifest=artifact_dir / "generated_pipeline_manifest.json",
        metadata=artifact_dir / "metadata.json",
    )


def generate_market_update_handoff_id(
    *,
    symbol_manifest: Path | None,
    market_daily_update_dir: Path | None,
    universe: Path,
    trading_calendar: Path,
    decision_date: str,
    universe_name: str,
    selection_profile: str,
    strict_accept_only: bool,
    settings: MarketUpdateHandoffSettings,
) -> str:
    payload = {
        "symbol_manifest": str(symbol_manifest) if symbol_manifest is not None else "",
        "market_daily_update_dir": str(market_daily_update_dir) if market_daily_update_dir is not None else "",
        "universe": str(universe),
        "trading_calendar": str(trading_calendar),
        "decision_date": decision_date,
        "universe_name": universe_name,
        "selection_profile": selection_profile,
        "strict_accept_only": strict_accept_only,
        "config_version": settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _run_validation_chain(
    *,
    pipeline_manifest_path: Path,
    decision_date: str,
    universe_name: str,
    selection_profile: str,
    top_n: int,
    settings: Settings,
) -> tuple[DataPipelineResult, SnapshotQualityGateResult | None, CurrentCandidateResult | None]:
    pipeline_result = run_data_source_ingestion_pipeline(
        load_data_pipeline_manifest(pipeline_manifest_path),
        config=settings,
    )
    snapshot_result = None
    current_result = None
    if pipeline_result.snapshot_manifest_path is not None:
        snapshot_result = run_snapshot_quality_gate(pipeline_result.snapshot_manifest_path, settings=settings)
        if snapshot_result.status != "FAIL":
            current_result = generate_current_candidates(
                decision_date,
                universe_name=universe_name,
                top_n=top_n,
                config=settings,
                snapshot_manifest_path=pipeline_result.snapshot_manifest_path,
                selection_profile=selection_profile,
            )
    return pipeline_result, snapshot_result, current_result


def _validation_warnings(
    pipeline_result: DataPipelineResult | None,
    snapshot_result: SnapshotQualityGateResult | None,
    current_result: CurrentCandidateResult | None,
) -> list[str]:
    warnings: list[str] = []
    if pipeline_result is not None:
        warnings.extend(f"data-pipeline: {warning}" for warning in pipeline_result.warnings)
    if snapshot_result is not None:
        warnings.extend(f"snapshot-quality: {warning}" for warning in snapshot_result.warnings)
    if current_result is not None:
        warnings.extend(f"current-candidates: {warning}" for warning in current_result.warnings)
    return warnings


def _handoff_status(
    handoff_rows: pd.DataFrame,
    *,
    update_result: MarketDailyUpdateManifestResult | LoadedMarketDailyUpdateResults | None,
    pipeline_result: DataPipelineResult | None,
    snapshot_result: SnapshotQualityGateResult | None,
    current_result: CurrentCandidateResult | None,
    warnings: list[str],
) -> str:
    if handoff_rows.empty or not handoff_rows["included"].map(_coerce_bool).any():
        return "FAIL"
    if pipeline_result is not None and pipeline_result.status == "FAIL":
        return "FAIL"
    if snapshot_result is not None and snapshot_result.status == "FAIL":
        return "FAIL"
    excluded_count = int((~handoff_rows["included"].map(_coerce_bool)).sum())
    warn_included = bool((handoff_rows["handoff_status"] == "INCLUDED_WARN_ACCEPT").any())
    update_warn = update_result is not None and str(update_result.status).upper() in {"WARN", "FAIL"}
    downstream_warn = (
        (pipeline_result is not None and pipeline_result.status == "WARN")
        or (snapshot_result is not None and snapshot_result.status == "WARN")
        or bool(warnings)
    )
    if excluded_count or warn_included or update_warn or downstream_warn:
        return "WARN"
    if current_result is not None and current_result.candidate_count == 0:
        return "WARN"
    return "PASS"


def _attach_batch_counts(handoff_rows: pd.DataFrame, batch_counts: dict[str, int]) -> pd.DataFrame:
    output = handoff_rows.copy(deep=True)
    output["batch_row_count"] = [
        batch_counts.get(_row_key(row), int(row.get("batch_row_count") or 0))
        for row in output.to_dict("records")
    ]
    return output[HANDOFF_ROW_COLUMNS]


def _filter_raw_market_frame(
    frame: pd.DataFrame,
    *,
    symbol: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    output = frame.copy(deep=True)
    if "symbol" in output.columns and symbol:
        output["symbol"] = output["symbol"].map(normalize_symbol_value)
        output = output.loc[output["symbol"] == normalize_symbol_value(symbol)]
    if "trade_date" in output.columns:
        parsed = pd.to_datetime(output["trade_date"], errors="coerce").dt.normalize()
        if start_date:
            output = output.loc[parsed >= pd.Timestamp(start_date).normalize()]
            parsed = pd.to_datetime(output["trade_date"], errors="coerce").dt.normalize()
        if end_date:
            output = output.loc[parsed <= pd.Timestamp(end_date).normalize()]
    return output.reset_index(drop=True)


def _enrich_batch_frame(frame: pd.DataFrame, *, source: str, metadata: dict[str, Any]) -> pd.DataFrame:
    output = frame.copy(deep=True)
    metadata_source = _metadata_source(metadata) or source
    if metadata_source and ("source" not in output.columns or output["source"].astype(str).str.strip().eq("").all()):
        output["source"] = metadata_source
    if "upstream_source" not in output.columns:
        output["upstream_source"] = _metadata_upstream_source(metadata)
    if "successful_function" not in output.columns:
        output["successful_function"] = _metadata_successful_function(metadata)
    return output


def _sort_batch_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    sort_columns = [column for column in ["symbol", "trade_date", "available_time", "revision_id"] if column in output.columns]
    if sort_columns:
        output = output.sort_values(sort_columns)
    return output.reset_index(drop=True)


def _exclusion_reason(
    row_status: str,
    preflight_status: str,
    raw_data_path: str,
    strict_accept_only: bool,
) -> str:
    if row_status not in {"PASS", "WARN"}:
        return f"Source row status {row_status or 'UNKNOWN'} is not eligible for handoff."
    if not raw_data_path:
        return "Source row has no raw_data_path."
    if preflight_status == "WARN_ACCEPT" and strict_accept_only:
        return "Preflight WARN_ACCEPT excluded because strict_accept_only is true."
    if preflight_status not in {"ACCEPT", "WARN_ACCEPT"}:
        return f"Preflight status {preflight_status or 'UNKNOWN'} is not eligible for handoff."
    return "Row excluded."


def _row_key(row: dict[str, Any]) -> str:
    return f"{row.get('manifest_row', '')}|{row.get('symbol', '')}|{row.get('raw_data_path', '')}"


def _metadata_source(metadata: dict[str, Any]) -> str:
    adapter_metadata = metadata.get("audit_metadata", {}).get("adapter_metadata", {})
    return str(metadata.get("source") or adapter_metadata.get("source") or adapter_metadata.get("adapter") or "").strip().upper()


def _metadata_upstream_source(metadata: dict[str, Any]) -> str:
    adapter_metadata = metadata.get("audit_metadata", {}).get("adapter_metadata", {})
    return str(metadata.get("upstream_source") or adapter_metadata.get("upstream_source") or "").strip().upper()


def _metadata_successful_function(metadata: dict[str, Any]) -> str:
    adapter_metadata = metadata.get("audit_metadata", {}).get("adapter_metadata", {})
    return str(metadata.get("successful_function") or adapter_metadata.get("successful_function") or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", ""}:
        return False
    return False


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


def _resolve_settings(
    config: Settings | MarketUpdateHandoffSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketUpdateHandoffSettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.market_update_handoff
    if isinstance(config, Settings):
        return config, config.market_update_handoff
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, MarketUpdateHandoffSettings):
        return project, config
    if isinstance(config, dict):
        handoff_payload = dict(project.market_update_handoff.model_dump())
        project_updates: dict[str, Any] = {}
        for key, value in config.items():
            if key == "market_update_handoff" and isinstance(value, dict):
                handoff_payload.update(value)
            elif key == "market_daily_update" and isinstance(value, dict):
                project_updates["market_daily_update"] = project.market_daily_update.model_copy(update=value)
            elif key == "market_cache_preflight" and isinstance(value, dict):
                project_updates["market_cache_preflight"] = project.market_cache_preflight.model_copy(update=value)
            elif key == "data_pipeline" and isinstance(value, dict):
                project_updates["data_pipeline"] = project.data_pipeline.model_copy(update=value)
            elif key == "snapshot_quality_gate" and isinstance(value, dict):
                project_updates["snapshot_quality_gate"] = project.snapshot_quality_gate.model_copy(update=value)
            elif key == "current_candidates" and isinstance(value, dict):
                project_updates["current_candidates"] = project.current_candidates.model_copy(update=value)
            elif key in handoff_payload:
                handoff_payload[key] = value
        if project_updates:
            project = project.model_copy(update=project_updates)
        return project, MarketUpdateHandoffSettings(**handoff_payload)
    raise TypeError("config must be Settings, MarketUpdateHandoffSettings, dict, or None")
